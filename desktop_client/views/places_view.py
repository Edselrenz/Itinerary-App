"""Places Explorer and Destination Catalog View mirroring Ionic tabs/map."""

import asyncio
from typing import Callable, Optional
import flet as ft

from desktop_client.components.dialogs import show_place_detail_dialog
from desktop_client.components.place_card import PlaceCard
from desktop_client.config.settings import (
    CANONICAL_CATEGORIES,
    NUEVA_ECIJA_LGUS,
    ThemeColors,
)
from desktop_client.models.place import Municipality, PaginatedPlaces, Place
from desktop_client.services.place_service import get_place_service


class PlacesView(ft.Container):
    """Destination catalog matching Ionic tabs/map:

    - Search bar with clear button.
    - Category filter pills row with active highlighting.
    - 32-LGU municipality selector and sort options.
    - Responsive destination cards grid with honest pricing and details dialog.
    """

    def __init__(self, on_navigate: Optional[Callable[[str], None]] = None):
        super().__init__()
        self.on_navigate = on_navigate
        self.place_service = get_place_service()

        self.expand = True
        self.padding = ft.Padding.symmetric(horizontal=28, vertical=20)
        self.bgcolor = ThemeColors.BG_LIGHT

        # Search & Filter State
        self.current_page = 1
        self.page_size = 18
        self.selected_category = "all"
        self.selected_municipality = "all"
        self.search_query = ""
        self.sort_by = ""

        self.paginated_data: Optional[PaginatedPlaces] = None
        self.municipalities: list[Municipality] = []
        self.is_loading = True

        self._build_content()
        self._load_municipalities()
        self._fetch_places()

    def _build_content(self) -> None:
        # Search Box (matching .map-search-box)
        self.search_input = ft.TextField(
            hint_text="Search places in Nueva Ecija (e.g. Minalungao, Farm Bistro, Dam)...",
            hint_style=ft.TextStyle(size=13, color=ThemeColors.TEXT_FAINT_LIGHT),
            prefix_icon=ft.Icons.SEARCH_ROUNDED,
            value=self.search_query,
            border_radius=12,
            border_color=ThemeColors.BORDER_LIGHT,
            focused_border_color=ThemeColors.PRIMARY_BLUE,
            expand=True,
            on_submit=lambda _: self._on_search_submit(),
        )

        search_btn = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.SEARCH, size=16, color=ft.Colors.WHITE),
                    ft.Text("Search", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ],
                spacing=6,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            bgcolor=ThemeColors.PRIMARY_BLUE,
            border_radius=12,
            height=48,
            padding=ft.Padding.symmetric(horizontal=18),
            ink=True,
            on_click=lambda _: self._on_search_submit(),
        )

        reset_btn = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.CLEAR_ALL, size=16, color=ThemeColors.TEXT_MUTED_LIGHT),
                    ft.Text("Reset", size=13, color=ThemeColors.TEXT_MUTED_LIGHT),
                ],
                spacing=6,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            border=ft.Border.all(1.2, ThemeColors.BORDER_LIGHT),
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border_radius=12,
            height=48,
            padding=ft.Padding.symmetric(horizontal=14),
            ink=True,
            on_click=lambda _: self._reset_filters(),
        )

        search_row = ft.Row(
            controls=[
                self.search_input,
                search_btn,
                reset_btn,
            ],
            spacing=10,
        )

        # LGU Dropdown Options
        lgu_options = [ft.dropdown.Option("all", "All 32 Municipalities")]
        for m in self.municipalities:
            lgu_options.append(ft.dropdown.Option(m.id, f"{m.name} ({m.place_count or 0})"))
        if not self.municipalities:
            for lgu in NUEVA_ECIJA_LGUS:
                lgu_options.append(ft.dropdown.Option(lgu, lgu))

        self.lgu_dropdown = ft.Dropdown(
            label="Filter by Municipality",
            options=lgu_options,
            value=self.selected_municipality,
            width=260,
            border_radius=10,
            border_color=ThemeColors.BORDER_LIGHT,
            focused_border_color=ThemeColors.PRIMARY_BLUE,
            on_select=lambda e: self._on_municipality_change(e.control.value),
        )

        self.sort_dropdown = ft.Dropdown(
            label="Sort By",
            options=[
                ft.dropdown.Option("", "Relevance / Curated"),
                ft.dropdown.Option("name", "Name (A-Z)"),
                ft.dropdown.Option("cost_asc", "Price: Low to High"),
                ft.dropdown.Option("cost_desc", "Price: High to Low"),
                ft.dropdown.Option("rating", "Top Rated"),
            ],
            value=self.sort_by,
            width=200,
            border_radius=10,
            border_color=ThemeColors.BORDER_LIGHT,
            focused_border_color=ThemeColors.PRIMARY_BLUE,
            on_select=lambda e: self._on_sort_change(e.control.value),
        )

        filter_row = ft.Row(
            controls=[
                self.lgu_dropdown,
                self.sort_dropdown,
            ],
            spacing=12,
        )

        # Quick Category Filter Pills (matching .filter-scroll-track)
        category_chips: list[ft.Control] = [
            self._create_category_pill("all", "All", ft.Icons.TRAVEL_EXPLORE, self.selected_category == "all")
        ]
        for cat in CANONICAL_CATEGORIES:
            is_active = self.selected_category == cat["key"]
            category_chips.append(
                self._create_category_pill(cat["key"], cat["label"], ft.Icons.PLACE, is_active)
            )

        category_track = ft.Row(
            controls=category_chips,
            scroll=ft.ScrollMode.AUTO,
            spacing=8,
        )

        # Results summary header
        total_count = self.paginated_data.total if self.paginated_data else 0
        total_pages = self.paginated_data.total_pages if self.paginated_data else 1

        results_info = ft.Row(
            controls=[
                ft.Text(
                    f"Showing {total_count} destinations in Nueva Ecija",
                    size=13,
                    weight=ft.FontWeight.BOLD,
                    color=ThemeColors.TEXT_BLACK,
                ),
                ft.Text(
                    f"Page {self.current_page} of {max(total_pages, 1)}",
                    size=12,
                    color=ThemeColors.TEXT_MUTED_LIGHT,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        # Places Grid / Results
        places_content: ft.Control
        if self.is_loading:
            places_content = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.ProgressRing(width=24, height=24, stroke_width=2),
                        ft.Text("Fetching places from backend registry...", size=13, color=ThemeColors.TEXT_MUTED_LIGHT),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=12,
                ),
                padding=60,
                alignment=ft.Alignment(0, 0),
            )
        elif self.paginated_data and self.paginated_data.items:
            cards = [
                PlaceCard(
                    place=p,
                    on_view_details=self._show_place_details,
                    on_add_to_day=lambda p: self._navigate("/builder"),
                    width=float("inf"),
                )
                for p in self.paginated_data.items
            ]
            places_content = ft.ResponsiveRow(
                controls=[ft.Container(content=c, col={"sm": 12, "md": 6, "lg": 4}) for c in cards],
                spacing=16,
                run_spacing=16,
            )
        else:
            places_content = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.SEARCH_OFF, size=52, color=ThemeColors.TEXT_FAINT_LIGHT),
                        ft.Text("No destinations found matching your filters.", size=15, weight=ft.FontWeight.BOLD),
                        ft.Text("Try broadening your category or selecting 'All Municipalities'.", size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                        ft.Container(height=8),
                        ft.FilledButton(
                            content="Reset All Filters",
                            style=ft.ButtonStyle(bgcolor=ThemeColors.PRIMARY_BLUE, color=ft.Colors.WHITE),
                            on_click=lambda _: self._reset_filters(),
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=6,
                ),
                padding=60,
                alignment=ft.Alignment(0, 0),
            )

        # Pagination Controls
        prev_btn = ft.OutlinedButton(
            content="← Previous",
            disabled=self.current_page <= 1 or self.is_loading,
            on_click=lambda _: self._change_page(self.current_page - 1),
        )

        next_btn = ft.FilledButton(
            content="Next →",
            style=ft.ButtonStyle(bgcolor=ThemeColors.PRIMARY_BLUE, color=ft.Colors.WHITE),
            disabled=self.current_page >= total_pages or self.is_loading,
            on_click=lambda _: self._change_page(self.current_page + 1),
        )

        pagination_row = ft.Row(
            controls=[prev_btn, next_btn],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=16,
        )

        self.content = ft.Column(
            controls=[
                search_row,
                ft.Container(height=8),
                category_track,
                ft.Container(height=8),
                filter_row,
                ft.Divider(color=ThemeColors.BORDER_LIGHT, height=1),
                ft.Container(height=6),
                results_info,
                ft.Container(height=12),
                places_content,
                ft.Container(height=20),
                pagination_row,
                ft.Container(height=24),
            ],
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def _create_category_pill(self, key: str, label: str, icon: str, is_active: bool) -> ft.Control:
        bg = ThemeColors.PRIMARY_BLUE if is_active else ThemeColors.SURFACE_LIGHT
        color = ft.Colors.WHITE if is_active else ThemeColors.TEXT_MAIN_LIGHT
        border_color = ThemeColors.PRIMARY_BLUE if is_active else ThemeColors.BORDER_LIGHT

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(icon, size=14, color=color),
                    ft.Text(label, size=12, weight=ft.FontWeight.W_700 if is_active else ft.FontWeight.W_500, color=color),
                ],
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=bg,
            border=ft.Border.all(1.2, border_color),
            border_radius=20,
            padding=ft.Padding.symmetric(horizontal=12, vertical=8),
            ink=True,
            on_click=lambda _: self._on_category_select(key),
        )

    def _on_category_select(self, key: str) -> None:
        if self.selected_category == key:
            return
        self.selected_category = key
        self.current_page = 1
        self._fetch_places()

    def _on_municipality_change(self, val: str) -> None:
        self.selected_municipality = val or "all"
        self.current_page = 1
        self._fetch_places()

    def _on_sort_change(self, val: str) -> None:
        self.sort_by = val or ""
        self.current_page = 1
        self._fetch_places()

    def _on_search_submit(self) -> None:
        self.search_query = (self.search_input.value or "").strip()
        self.current_page = 1
        self._fetch_places()

    def _reset_filters(self) -> None:
        self.selected_category = "all"
        self.selected_municipality = "all"
        self.search_query = ""
        self.sort_by = ""
        self.current_page = 1
        self.search_input.value = ""
        self._fetch_places()

    def _change_page(self, new_page: int) -> None:
        self.current_page = new_page
        self._fetch_places()

    def _safe_update(self) -> None:
        try:
            self.update()
        except Exception:
            pass

    def _show_place_details(self, place: Place) -> None:
        show_place_detail_dialog(self.page, place, on_add_to_day=lambda p: self._navigate("/builder"))

    def _fetch_places(self) -> None:
        self.is_loading = True
        self._build_content()
        self._safe_update()

        async def _worker():
            cat = None if self.selected_category == "all" else self.selected_category
            muni = None if self.selected_municipality == "all" else self.selected_municipality
            search = self.search_query if self.search_query else None
            sort = self.sort_by if self.sort_by else None

            try:
                self.paginated_data = await self.place_service.get_places(
                    page=self.current_page,
                    page_size=self.page_size,
                    category=cat,
                    municipality=muni,
                    search=search,
                    sort_by=sort,
                )
            except Exception:
                self.paginated_data = None
            finally:
                self.is_loading = False
                self._build_content()
                self._safe_update()

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_worker())
        except RuntimeError:
            pass

    def _load_municipalities(self) -> None:
        async def _worker():
            try:
                self.municipalities = await self.place_service.get_municipalities()
                self._build_content()
                self._safe_update()
            except Exception:
                pass

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_worker())
        except RuntimeError:
            pass

    def _navigate(self, route: str) -> None:
        if self.on_navigate:
            self.on_navigate(route)
