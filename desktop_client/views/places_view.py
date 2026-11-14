"""Places Explorer and Destination Catalog View mirroring Ionic tabs/map."""

import asyncio
from typing import Callable, Optional
import flet as ft

from desktop_client.components.dialogs import show_place_detail_dialog
from desktop_client.components.place_card import PlaceCard
from desktop_client.components.slippy_map_canvas import RouteStopPin, SlippyMapCanvas
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
    - Advanced Multi-Select Filter Modal (Price Tiers, LGUs, Categories).
    - Dual mode: Responsive Catalog Grid & Interactive Map Explorer.
    - Direct "+ Add to Trip" routing into Custom Itinerary Builder.
    """

    def __init__(self, on_navigate: Optional[Callable[..., None]] = None):
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
        self.selected_price_tier = "all"  # all, free, budget, mid, luxury
        self.search_query = ""
        self.sort_by = ""
        self.view_mode = "map"  # Default to GIS Map mode matching /map tab
        self.interactive_map: Optional[InteractiveProvinceMap] = None

        # Map Explorer State
        self.map_zoom = 1.0
        self.selected_map_place: Optional[Place] = None

        self.paginated_data: Optional[PaginatedPlaces] = None
        self.all_places_cache: list[Place] = []
        self.municipalities: list[Municipality] = []
        self.is_loading = True

        self._build_content()
        self._load_municipalities()
        self._fetch_places()

    def _build_content(self) -> None:
        # Search Box
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

        filter_btn = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.TUNE, size=16, color=ThemeColors.PRIMARY_BLUE),
                    ft.Text("Filters", size=13, weight=ft.FontWeight.BOLD, color=ThemeColors.PRIMARY_BLUE),
                ],
                spacing=6,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            border=ft.Border.all(1.2, ThemeColors.CUSTOM_CARD_BORDER),
            bgcolor=ThemeColors.AZURE_SOFT,
            border_radius=12,
            height=48,
            padding=ft.Padding.symmetric(horizontal=14),
            ink=True,
            on_click=lambda _: self._open_filter_modal(),
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

        # View Mode Toggle (Grid vs Map)
        grid_mode_btn = ft.Container(
            content=ft.Icon(
                ft.Icons.GRID_VIEW_ROUNDED,
                size=18,
                color=ft.Colors.WHITE if self.view_mode == "grid" else ThemeColors.TEXT_MAIN_LIGHT,
            ),
            bgcolor=ThemeColors.PRIMARY_BLUE if self.view_mode == "grid" else ThemeColors.SURFACE_LIGHT,
            border_radius=8,
            padding=8,
            tooltip="Catalog Grid View",
            ink=True,
            on_click=lambda _: self._set_view_mode("grid"),
        )

        map_mode_btn = ft.Container(
            content=ft.Icon(
                ft.Icons.MAP_ROUNDED,
                size=18,
                color=ft.Colors.WHITE if self.view_mode == "map" else ThemeColors.TEXT_MAIN_LIGHT,
            ),
            bgcolor=ThemeColors.PRIMARY_BLUE if self.view_mode == "map" else ThemeColors.SURFACE_LIGHT,
            border_radius=8,
            padding=8,
            tooltip="Interactive Map Explorer",
            ink=True,
            on_click=lambda _: self._set_view_mode("map"),
        )

        mode_switcher = ft.Container(
            content=ft.Row(controls=[grid_mode_btn, map_mode_btn], spacing=4),
            border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
            border_radius=10,
            padding=2,
            bgcolor=ThemeColors.SURFACE_LIGHT,
        )

        search_row = ft.Row(
            controls=[
                self.search_input,
                search_btn,
                filter_btn,
                reset_btn,
                mode_switcher,
            ],
            spacing=8,
        )

        # Quick Category Filter Pills
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

        # LGU Dropdown & Sort
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

        # Active Price Tier Badge
        price_tier_label = {
            "all": "All Budgets",
            "free": "Free Admission (₱0)",
            "budget": "Budget (≤ ₱500)",
            "mid": "Mid-tier (≤ ₱1,500)",
            "luxury": "Luxury (> ₱1,500)",
        }.get(self.selected_price_tier, "All Budgets")

        tier_badge = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.PAYMENTS_OUTLINED, size=14, color=ThemeColors.BUDGET_GREEN),
                    ft.Text(price_tier_label, size=11, weight=ft.FontWeight.BOLD, color=ThemeColors.BUDGET_GREEN),
                ],
                spacing=4,
            ),
            bgcolor=ThemeColors.SUCCESS_BG,
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=10, vertical=6),
            visible=self.selected_price_tier != "all",
        )

        filter_row = ft.Row(
            controls=[
                self.lgu_dropdown,
                self.sort_dropdown,
                tier_badge,
            ],
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Main Body: Grid vs Map Explorer
        if self.view_mode == "map":
            main_body = self._build_map_explorer()
        else:
            main_body = self._build_catalog_grid()

        self.content = ft.Column(
            controls=[
                search_row,
                ft.Container(height=8),
                category_track,
                ft.Container(height=8),
                filter_row,
                ft.Divider(color=ThemeColors.BORDER_LIGHT, height=1),
                ft.Container(height=6),
                main_body,
            ],
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def _build_catalog_grid(self) -> ft.Control:
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
                    on_add_to_day=lambda p: self._add_to_trip(p),
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

        return ft.Column(
            controls=[
                results_info,
                ft.Container(height=12),
                places_content,
                ft.Container(height=20),
                pagination_row,
                ft.Container(height=24),
            ],
            spacing=0,
        )

    def recenter_map(self) -> None:
        """Recenter camera to province center."""
        if self.interactive_map:
            self.interactive_map.set_center_and_zoom(15.58, 121.00, 10)

    def _build_map_explorer(self) -> ft.Control:
        """Interactive Provincial GIS Map plotting Nueva Ecija destinations and OSM POIs."""
        from desktop_client.core.offline_data import get_all_offline_places

        all_raw = get_all_offline_places()
        places_to_plot: list[Place] = []
        for raw in all_raw:
            try:
                places_to_plot.append(Place.from_dict(raw))
            except Exception:
                continue

        if self.selected_category != "all":
            places_to_plot = [p for p in places_to_plot if p.category == self.selected_category]
        if self.selected_municipality != "all":
            places_to_plot = [p for p in places_to_plot if p.municipality_name == self.selected_municipality or p.municipality_id == self.selected_municipality]
        if self.search_query:
            sq = self.search_query.lower().strip()
            places_to_plot = [p for p in places_to_plot if sq in p.name.lower() or sq in (p.municipality_name or "").lower()]

        self.interactive_map = SlippyMapCanvas(
            width=920,
            height=520,
            center_lat=15.58,
            center_lng=121.00,
            zoom=10,
            places=places_to_plot,
            on_place_click=lambda p: self._select_map_place(p),
            border_radius=16,
        )

        map_canvas = ft.Container(
            content=self.interactive_map,
            height=520,
            border=ft.Border.all(1.5, ThemeColors.BORDER_LIGHT),
            border_radius=16,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )

        header_row = ft.Row(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.MAP, size=18, color=ThemeColors.PRIMARY_BLUE),
                        ft.Text(f"Nueva Ecija GIS Map Explorer ({len(places_to_plot)} Places Plotted)", size=13, weight=ft.FontWeight.BOLD),
                    ],
                    spacing=6,
                ),
                ft.Container(
                    content=ft.Text(
                        "Click any cluster to zoom in • Click pin to inspect",
                        size=11,
                        color=ThemeColors.TEXT_MUTED_LIGHT,
                    ),
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        # Selected Map Place Preview Card
        preview_control = ft.Container()
        if self.selected_map_place:
            p = self.selected_map_place
            preview_control = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Image(
                            src=p.resolved_image_path,
                            width=90,
                            height=70,
                            fit=ft.BoxFit.COVER,
                            border_radius=10,
                            error_content=ft.Icon(ft.Icons.LANDSCAPE, size=30, color=ThemeColors.PRIMARY_BLUE),
                        ),
                        ft.Column(
                            controls=[
                                ft.Text(p.name, size=13, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_BLACK),
                                ft.Text(f"{p.municipality_name or 'Nueva Ecija'} • {p.formatted_category}", size=11, color=ThemeColors.TEXT_MUTED_LIGHT),
                                ft.Text(p.formatted_cost, size=11, weight=ft.FontWeight.BOLD, color=ThemeColors.EMERALD_PRIMARY),
                            ],
                            spacing=3,
                            expand=True,
                        ),
                        ft.Row(
                            controls=[
                                ft.OutlinedButton(
                                    content="View Details",
                                    icon=ft.Icons.VISIBILITY,
                                    on_click=lambda _: self._show_place_details(p),
                                ),
                                ft.FilledButton(
                                    content="+ Add to Trip",
                                    icon=ft.Icons.ADD,
                                    style=ft.ButtonStyle(bgcolor=ThemeColors.PRIMARY_BLUE, color=ft.Colors.WHITE),
                                    on_click=lambda _: self._add_to_trip(p),
                                ),
                            ],
                            spacing=8,
                        ),
                    ],
                    spacing=14,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                bgcolor=ThemeColors.SURFACE_LIGHT,
                border=ft.Border.all(1.5, ThemeColors.CUSTOM_CARD_BORDER),
                border_radius=14,
                padding=12,
                margin=ft.Margin.only(top=10),
            )

        return ft.Column(
            controls=[
                header_row,
                ft.Container(height=4),
                map_canvas,
                preview_control,
            ],
            spacing=4,
        )

    def _select_map_place(self, place: Place) -> None:
        self.selected_map_place = place
        p = self.safe_page
        if p:
            show_place_detail_dialog(
                p,
                place,
                on_add_to_trip=lambda pl: self.on_navigate("/builder", pre_added_place=pl) if self.on_navigate else None,
            )
        self._build_content()
        self._safe_update()

    def _zoom_map(self, delta: float) -> None:
        self.map_zoom = max(0.8, min(2.0, self.map_zoom + delta))
        self._build_content()
        self._safe_update()

    def _set_view_mode(self, mode: str) -> None:
        self.view_mode = mode
        self._build_content()
        self._safe_update()

    def _open_filter_modal(self) -> None:
        """Opens Figma Multi-Select Filter Modal."""
        if not self.safe_page:
            return

        # Category Chips
        cat_chips: list[ft.Control] = []
        temp_category = self.selected_category
        temp_municipality = self.selected_municipality
        temp_price_tier = self.selected_price_tier

        # Price Tiers
        price_tiers = [
            ("all", "All Prices"),
            ("free", "Free Admission (₱0)"),
            ("budget", "Budget (≤ ₱500)"),
            ("mid", "Mid (≤ ₱1,500)"),
            ("luxury", "Luxury (> ₱1,500)"),
        ]

        def update_dialog_ui():
            try:
                dlg.update()
            except Exception:
                pass

        def set_tier(tier: str):
            nonlocal temp_price_tier
            temp_price_tier = tier
            for c in tier_row.controls:
                is_sel = getattr(c, "data", None) == tier
                c.bgcolor = ThemeColors.PRIMARY_BLUE if is_sel else ThemeColors.SURFACE_LIGHT
                c.content.color = ft.Colors.WHITE if is_sel else ThemeColors.TEXT_MAIN_LIGHT
            update_dialog_ui()

        tier_buttons = []
        for t_key, t_label in price_tiers:
            is_sel = t_key == temp_price_tier
            btn = ft.Container(
                content=ft.Text(t_label, size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE if is_sel else ThemeColors.TEXT_MAIN_LIGHT),
                bgcolor=ThemeColors.PRIMARY_BLUE if is_sel else ThemeColors.SURFACE_LIGHT,
                border=ft.Border.all(1, ThemeColors.PRIMARY_BLUE if is_sel else ThemeColors.BORDER_LIGHT),
                border_radius=14,
                padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                ink=True,
                data=t_key,
                on_click=lambda _, tk=t_key: set_tier(tk),
            )
            tier_buttons.append(btn)

        tier_row = ft.Row(controls=tier_buttons, wrap=True, spacing=6)

        # Municipality Dropdown in Modal
        lgu_opts = [ft.dropdown.Option("all", "All 32 Municipalities")]
        for m in self.municipalities:
            lgu_opts.append(ft.dropdown.Option(m.id, m.name))
        if not self.municipalities:
            for lgu in NUEVA_ECIJA_LGUS:
                lgu_opts.append(ft.dropdown.Option(lgu, lgu))

        lgu_select = ft.Dropdown(
            label="Select Municipality",
            options=lgu_opts,
            value=temp_municipality,
            dense=True,
        )

        def apply_filters(_):
            self.selected_price_tier = temp_price_tier
            self.selected_municipality = lgu_select.value or "all"
            self.current_page = 1
            dlg.open = False
            self.safe_page.update()
            self._fetch_places()

        def reset_in_modal(_):
            self.selected_price_tier = "all"
            self.selected_municipality = "all"
            self.selected_category = "all"
            dlg.open = False
            self.safe_page.update()
            self._reset_filters()

        dlg = ft.AlertDialog(
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.TUNE, color=ThemeColors.PRIMARY_BLUE, size=22),
                    ft.Text("Destination Filter & Pricing", size=16, weight=ft.FontWeight.BOLD),
                ],
                spacing=8,
            ),
            content=ft.Column(
                controls=[
                    ft.Text("Price Tier Filter", size=13, weight=ft.FontWeight.BOLD),
                    tier_row,
                    ft.Container(height=6),
                    ft.Text("Municipality Location", size=13, weight=ft.FontWeight.BOLD),
                    lgu_select,
                ],
                spacing=10,
                width=450,
                tight=True,
            ),
            actions=[
                ft.TextButton("Reset Filters", on_click=reset_in_modal),
                ft.FilledButton(
                    content="Apply Filters",
                    style=ft.ButtonStyle(bgcolor=ThemeColors.PRIMARY_BLUE, color=ft.Colors.WHITE),
                    on_click=apply_filters,
                ),
            ],
        )
        self.safe_page.overlay.append(dlg)
        dlg.open = True
        self.safe_page.update()

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
        self.selected_price_tier = "all"
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
        show_place_detail_dialog(
            self.page,
            place,
            on_add_to_day=lambda p: self._add_to_trip(p),
            on_navigate=self.on_navigate,
        )

    def _add_to_trip(self, place: Place) -> None:
        if self.on_navigate:
            self.on_navigate("/builder", pre_added_place=place)

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
                res = await self.place_service.get_places(
                    page=self.current_page,
                    page_size=self.page_size,
                    category=cat,
                    municipality_id=muni,
                    search=search,
                    sort=sort,
                )
                items = res.items
                # Apply price tier filter locally if active
                if self.selected_price_tier == "free":
                    items = [p for p in items if (p.estimated_cost_max or 0.0) == 0.0]
                elif self.selected_price_tier == "budget":
                    items = [p for p in items if (p.estimated_cost_max or 0.0) <= 500.0]
                elif self.selected_price_tier == "mid":
                    items = [p for p in items if 0.0 < (p.estimated_cost_max or 0.0) <= 1500.0]
                elif self.selected_price_tier == "luxury":
                    items = [p for p in items if (p.estimated_cost_min or 0.0) > 1500.0]

                self.paginated_data = PaginatedPlaces(
                    items=items,
                    total=len(items) if self.selected_price_tier != "all" else res.total,
                    page=self.current_page,
                    page_size=self.page_size,
                )
                self.all_places_cache = res.items
            except Exception:
                # Offline fallback to canonical curated destinations
                from desktop_client.views.dashboard_view import DashboardView
                fallback_places = DashboardView()._get_fallback_popular_places()
                if cat:
                    fallback_places = [p for p in fallback_places if p.category == cat]
                if search:
                    s_lower = search.lower()
                    fallback_places = [p for p in fallback_places if s_lower in p.name.lower() or s_lower in (p.municipality_name or "").lower()]
                if self.selected_price_tier == "free":
                    fallback_places = [p for p in fallback_places if (p.estimated_cost_max or 0.0) == 0.0]
                elif self.selected_price_tier == "budget":
                    fallback_places = [p for p in fallback_places if (p.estimated_cost_max or 0.0) <= 500.0]
                elif self.selected_price_tier == "mid":
                    fallback_places = [p for p in fallback_places if 0.0 < (p.estimated_cost_max or 0.0) <= 1500.0]
                elif self.selected_price_tier == "luxury":
                    fallback_places = [p for p in fallback_places if (p.estimated_cost_min or 0.0) > 1500.0]

                self.paginated_data = PaginatedPlaces(
                    items=fallback_places,
                    total=len(fallback_places),
                    page=1,
                    page_size=self.page_size,
                )
                self.all_places_cache = fallback_places
            finally:
                self.is_loading = False
                self._build_content()
                self._safe_update()

        if self.safe_page:
            self.safe_page.run_task(_worker)
        else:
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

        if self.safe_page:
            self.safe_page.run_task(_worker)
        else:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(_worker())
            except RuntimeError:
                pass

    @property
    def safe_page(self) -> Optional[ft.Page]:
        try:
            return self.page
        except Exception:
            return None

    def _navigate(self, route: str) -> None:
        if self.on_navigate:
            self.on_navigate(route)
