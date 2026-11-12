"""Places Explorer and Destination Catalog View."""

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
    """Destination catalog with 16-category filters, 32-LGU dropdown,

    free-text search, and pagination.
    """

    def __init__(self, on_navigate: Optional[Callable[[str], None]] = None):
        super().__init__()
        self.on_navigate = on_navigate
        self.place_service = get_place_service()

        self.expand = True
        self.padding = ft.padding.all(24)
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
        # Search Bar
        self.search_field = ft.TextField(
            hint_text="Search places, landmarks, dishes, or farm resorts...",
            prefix_icon=ft.Icons.SEARCH,
            value=self.search_query,
            expand=True,
            on_submit=lambda _: self._on_search_submit(),
        )

        search_btn = ft.FilledButton(
            content="Search",
            style=ft.ButtonStyle(bgcolor=ThemeColors.EMERALD_PRIMARY, color=ft.Colors.WHITE),
            on_click=lambda _: self._on_search_submit(),
        )

        reset_btn = ft.OutlinedButton(
            content="Reset",
            icon=ft.Icons.CLEAR_ALL,
            on_click=lambda _: self._reset_filters(),
        )

        search_row = ft.Row(
            controls=[
                self.search_field,
                search_btn,
                reset_btn,
            ],
            spacing=8,
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
            on_change=lambda e: self._on_municipality_change(e.control.value),
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
            on_change=lambda e: self._on_sort_change(e.control.value),
        )

        filter_row = ft.Row(
            controls=[
                self.lgu_dropdown,
                self.sort_dropdown,
            ],
            spacing=12,
        )

        # 16 Canonical Category Filter Chips
        category_chips: list[ft.Control] = [
            self._create_category_chip("all", "All Categories", self.selected_category == "all")
        ]
        for cat in CANONICAL_CATEGORIES:
            is_active = self.selected_category == cat["key"]
            category_chips.append(
                self._create_category_chip(cat["key"], cat["label"], is_active)
            )

        category_bar = ft.Row(
            controls=category_chips,
            scroll=ft.ScrollMode.AUTO,
            spacing=8,
        )

        # Results header & pagination count
        total_count = self.paginated_data.total if self.paginated_data else 0
        total_pages = self.paginated_data.total_pages if self.paginated_data else 1
        
        results_info = ft.Row(
            controls=[
                ft.Text(
                    f"Showing {total_count} destinations in Nueva Ecija",
                    size=13,
                    weight=ft.FontWeight.W_600,
                    color=ThemeColors.TEXT_MAIN_LIGHT,
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
                        ft.ProgressRing(width=28, height=28, stroke_width=3),
                        ft.Text("Querying Nueva Ecija places...", size=14, color=ThemeColors.TEXT_MUTED_LIGHT),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=12,
                ),
                padding=60,
                alignment=ft.Alignment(0, 0),
            )
        elif not self.paginated_data or not self.paginated_data.items:
            places_content = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.SEARCH_OFF, size=48, color=ThemeColors.TEXT_MUTED_LIGHT),
                        ft.Text("No destinations found matching your filters.", size=15, weight=ft.FontWeight.W_600),
                        ft.Text("Try adjusting your keywords, selecting 'All Municipalities', or resetting filters.", size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                        ft.Container(height=8),
                        ft.FilledButton(
                            content="Reset All Filters",
                            style=ft.ButtonStyle(bgcolor=ThemeColors.EMERALD_PRIMARY, color=ft.Colors.WHITE),
                            on_click=lambda _: self._reset_filters(),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=6,
                ),
                padding=40,
                alignment=ft.Alignment(0, 0),
            )
        else:
            cards = [
                PlaceCard(
                    place=p,
                    on_view_details=self._show_place_details,
                    on_add_to_day=lambda p: self._navigate_to_builder(p),
                    width=290,
                )
                for p in self.paginated_data.items
            ]
            places_content = ft.Row(
                controls=cards,
                wrap=True,
                spacing=16,
                run_spacing=16,
            )

        # Pagination Buttons
        prev_btn = ft.OutlinedButton(
            content="← Previous",
            disabled=self.current_page <= 1 or self.is_loading,
            on_click=lambda _: self._change_page(self.current_page - 1),
        )
        next_btn = ft.FilledButton(
            content="Next →",
            disabled=self.current_page >= total_pages or self.is_loading,
            style=ft.ButtonStyle(bgcolor=ThemeColors.EMERALD_PRIMARY, color=ft.Colors.WHITE),
            on_click=lambda _: self._change_page(self.current_page + 1),
        )

        pagination_bar = ft.Row(
            controls=[prev_btn, next_btn],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=16,
        )

        self.content = ft.Column(
            controls=[
                search_row,
                ft.Container(height=4),
                filter_row,
                ft.Container(height=8),
                category_bar,
                ft.Container(height=12),
                ft.Divider(height=1, color=ThemeColors.BORDER_LIGHT),
                ft.Container(height=8),
                results_info,
                ft.Container(height=12),
                places_content,
                ft.Container(height=24),
                pagination_bar if total_pages > 1 else ft.Container(),
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=0,
        )

    def _create_category_chip(self, key: str, label: str, is_active: bool) -> ft.Control:
        bg = ThemeColors.EMERALD_PRIMARY if is_active else ThemeColors.SURFACE_LIGHT
        text_color = ft.Colors.WHITE if is_active else ThemeColors.TEXT_MAIN_LIGHT
        border_color = ThemeColors.EMERALD_PRIMARY if is_active else ThemeColors.BORDER_LIGHT

        return ft.Container(
            content=ft.Text(label, size=11, weight=ft.FontWeight.W_600 if is_active else ft.FontWeight.NORMAL, color=text_color),
            bgcolor=bg,
            border=ft.Border.all(1, border_color),
            border_radius=16,
            padding=ft.padding.symmetric(horizontal=12, vertical=6),
            ink=True,
            on_click=lambda _: self._on_category_click(key),
        )

    def _on_category_click(self, key: str) -> None:
        self.selected_category = key
        self.current_page = 1
        self._fetch_places()

    def _on_municipality_change(self, val: str) -> None:
        self.selected_municipality = val
        self.current_page = 1
        self._fetch_places()

    def _on_sort_change(self, val: str) -> None:
        self.sort_by = val
        self.current_page = 1
        self._fetch_places()

    def _on_search_submit(self) -> None:
        self.search_query = (self.search_field.value or "").strip()
        self.current_page = 1
        self._fetch_places()

    def _reset_filters(self) -> None:
        self.search_query = ""
        self.search_field.value = ""
        self.selected_category = "all"
        self.selected_municipality = "all"
        self.sort_by = ""
        self.current_page = 1
        self._fetch_places()

    def _change_page(self, page_num: int) -> None:
        self.current_page = page_num
        self._fetch_places()

    def _load_municipalities(self) -> None:
        async def _fetch_munis():
            try:
                data = await self.place_service.get_municipalities()
                self.municipalities = data
                self._build_content()
                try:
                    self.update()
                except Exception:
                    pass
            except Exception:
                pass

        asyncio.create_task(_fetch_munis())

    def _fetch_places(self) -> None:
        self.is_loading = True
        self._build_content()
        try:
            self.update()
        except Exception:
            pass

        async def _do_query():
            try:
                paginated = await self.place_service.get_places(
                    page=self.current_page,
                    page_size=self.page_size,
                    search=self.search_query or None,
                    category=self.selected_category if self.selected_category != "all" else None,
                    municipality_id=self.selected_municipality if self.selected_municipality != "all" else None,
                    sort=self.sort_by or None,
                )
                self.paginated_data = paginated
            except Exception:
                self.paginated_data = None
            finally:
                self.is_loading = False
                self._build_content()
                try:
                    self.update()
                except Exception:
                    pass

        asyncio.create_task(_do_query())

    def _show_place_details(self, place: Place) -> None:
        if self.page:
            show_place_detail_dialog(
                self.page,
                place,
                on_add_to_day=lambda p: self._navigate_to_builder(p),
            )

    def _navigate_to_builder(self, place: Place) -> None:
        if self.on_navigate:
            self.on_navigate("/builder")
