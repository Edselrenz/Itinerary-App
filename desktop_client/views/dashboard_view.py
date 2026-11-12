"""Home / Dashboard Hub View mirroring the Ionic Angular Web Client (tabs/home)."""

import asyncio
from typing import Callable, Optional
import flet as ft

from desktop_client.components.dialogs import show_place_detail_dialog
from desktop_client.config.settings import ThemeColors
from desktop_client.core.session import get_session_manager
from desktop_client.models.itinerary import Itinerary
from desktop_client.models.place import Place
from desktop_client.services.itinerary_service import get_itinerary_service
from desktop_client.services.place_service import get_place_service


class DashboardView(ft.Container):
    """Home view matching Ionic tabs/home exactly:

    - Large bold 'Where are you going next?' headline + notification bell.
    - Pill destination search input.
    - Two Planner Action Cards (Dark Navy Suggested Card + Sky Blue bordered Custom Card).
    - Popular Destinations horizontal scrolling track.
    - Saved Itineraries preview cards with plan badges and daily budgets.
    """

    def __init__(self, on_navigate: Optional[Callable[[str], None]] = None):
        super().__init__()
        self.on_navigate = on_navigate
        self.session_manager = get_session_manager()
        self.place_service = get_place_service()
        self.itinerary_service = get_itinerary_service()

        self.expand = True
        self.padding = ft.Padding.symmetric(horizontal=32, vertical=20)
        self.bgcolor = ThemeColors.BG_LIGHT

        # Data State
        self.destinations: list[Place] = []
        self.saved_itineraries: list[Itinerary] = []
        self.search_results: list[Place] = []
        self.is_searching = False
        self.search_loading = False
        self.search_query = ""
        self.unread_notifications = 1

        self._build_content()
        self._load_data()

    def _build_content(self) -> None:
        # Top Header matching .home-header
        header_title = ft.Text(
            "Where are you\ngoing next?",
            size=28,
            weight=ft.FontWeight.W_800,
            color=ThemeColors.TEXT_BLACK,
        )

        bell_icon = ft.Container(
            content=ft.Stack(
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.NOTIFICATIONS,
                        icon_size=26,
                        icon_color=ThemeColors.PRIMARY_BLUE,
                        tooltip="Travel notifications",
                        on_click=lambda _: self._on_bell_clicked(),
                    ),
                    ft.Container(
                        content=ft.Text(
                            str(self.unread_notifications),
                            size=10,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE,
                        ),
                        bgcolor=ThemeColors.ERROR,
                        border_radius=9,
                        width=18,
                        height=18,
                        alignment=ft.Alignment(0, 0),
                        margin=ft.Margin.only(top=4, left=24),
                        visible=self.unread_notifications > 0,
                    ),
                ]
            )
        )

        top_header_row = ft.Row(
            controls=[header_title, bell_icon],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

        # Search Container matching .search-container
        self.search_input = ft.TextField(
            hint_text="Search destination (e.g. Cabanatuan, Gapan, etc.)",
            hint_style=ft.TextStyle(size=13, color=ThemeColors.TEXT_FAINT_LIGHT),
            value=self.search_query,
            border=ft.NoInputBorder(),
            filled=False,
            expand=True,
            on_change=lambda e: self._on_search_change(e.control.value),
            on_submit=lambda e: self._on_search_submit(e.control.value),
        )

        self.search_trailing_btn = ft.IconButton(
            icon=ft.Icons.SEARCH_ROUNDED,
            icon_size=22,
            icon_color=ThemeColors.TEXT_BLACK,
            on_click=lambda _: self._on_search_submit(self.search_input.value or ""),
        )

        search_container = ft.Container(
            content=ft.Row(
                controls=[
                    self.search_input,
                    self.search_trailing_btn,
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border=ft.Border.all(1.2, ThemeColors.BORDER_LIGHT),
            border_radius=12,
            height=48,
            padding=ft.Padding.symmetric(horizontal=16),
        )

        # Dynamic Content (Search Results vs Standard Home Layout)
        if self.is_searching:
            dynamic_section = self._build_search_results_section()
        else:
            dynamic_section = self._build_standard_home_layout()

        main_column = ft.Column(
            controls=[
                top_header_row,
                ft.Container(height=12),
                search_container,
                ft.Container(height=16),
                dynamic_section,
            ],
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        self.content = main_column

    def _build_standard_home_layout(self) -> ft.Control:
        # Planner Cards Grid (2-column layout matching .planner-cards-grid)
        suggested_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        ft.Icons.AUTO_AWESOME,
                        size=28,
                        color=ThemeColors.PRIMARY_BLUE,
                    ),
                    ft.Container(height=8),
                    ft.Text(
                        "Suggested\nItinerary",
                        size=18,
                        weight=ft.FontWeight.W_800,
                        color=ft.Colors.WHITE,
                    ),
                    ft.Container(height=4),
                    ft.Text(
                        "Let us plan your trip based on your preferences.",
                        size=12,
                        color=ThemeColors.TEXT_MUTED_DARK,
                    ),
                ],
                spacing=0,
                alignment=ft.MainAxisAlignment.START,
            ),
            gradient=ft.LinearGradient(
                begin=ft.Alignment(0, -1),
                end=ft.Alignment(0, 1),
                colors=[ThemeColors.NAVY_GRADIENT_START, ThemeColors.NAVY_GRADIENT_END],
            ),
            border_radius=18,
            padding=ft.Padding.all(20),
            height=195,
            expand=True,
            ink=True,
            on_click=lambda _: self._navigate("/suggested"),
        )

        custom_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        ft.Icons.EDIT_CALENDAR_ROUNDED,
                        size=28,
                        color=ThemeColors.PRIMARY_BLUE,
                    ),
                    ft.Container(height=8),
                    ft.Text(
                        "Custom\nItinerary",
                        size=18,
                        weight=ft.FontWeight.W_800,
                        color=ThemeColors.TEXT_BLACK,
                    ),
                    ft.Container(height=4),
                    ft.Text(
                        "Pick your own places and we will organize the best route for you.",
                        size=12,
                        color=ThemeColors.TEXT_MUTED_LIGHT,
                    ),
                ],
                spacing=0,
                alignment=ft.MainAxisAlignment.START,
            ),
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border=ft.Border.all(1.5, ThemeColors.CUSTOM_CARD_BORDER),
            border_radius=18,
            padding=ft.Padding.all(20),
            height=195,
            expand=True,
            ink=True,
            on_click=lambda _: self._navigate("/builder"),
        )

        planner_grid = ft.Row(
            controls=[suggested_card, custom_card],
            spacing=16,
        )

        # Popular Destinations Section
        popular_header = ft.Row(
            controls=[
                ft.Text("Popular Destinations", size=18, weight=ft.FontWeight.W_800, color=ThemeColors.TEXT_BLACK),
                ft.TextButton(
                    content="See all",
                    style=ft.ButtonStyle(color=ThemeColors.PRIMARY_BLUE),
                    on_click=lambda _: self._navigate("/places"),
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        destinations_cards: list[ft.Control] = []
        if not self.destinations:
            destinations_cards.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.ProgressRing(width=20, height=20, stroke_width=2),
                            ft.Text("Loading popular destinations...", size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                        ],
                        spacing=10,
                    ),
                    padding=20,
                )
            )
        else:
            for place in self.destinations:
                destinations_cards.append(self._create_popular_card(place))

        popular_track = ft.Row(
            controls=destinations_cards,
            spacing=14,
            scroll=ft.ScrollMode.AUTO,
        )

        # Saved Itineraries Section
        saved_header = ft.Row(
            controls=[
                ft.Text("Saved Itineraries", size=18, weight=ft.FontWeight.W_800, color=ThemeColors.TEXT_BLACK),
                ft.TextButton(
                    content="See all",
                    style=ft.ButtonStyle(color=ThemeColors.PRIMARY_BLUE),
                    on_click=lambda _: self._navigate("/trips"),
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        saved_cards: list[ft.Control] = []
        if not self.saved_itineraries:
            saved_cards.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.CALENDAR_MONTH, size=24, color=ThemeColors.PRIMARY_BLUE),
                            ft.Column(
                                controls=[
                                    ft.Text("No saved itineraries yet.", size=13, weight=ft.FontWeight.BOLD),
                                    ft.Text("Start by picking places with the Custom Builder or AI Wizard.", size=11, color=ThemeColors.TEXT_MUTED_LIGHT),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.FilledButton(
                                content="Plan a Trip",
                                style=ft.ButtonStyle(bgcolor=ThemeColors.PRIMARY_BLUE, color=ft.Colors.WHITE),
                                on_click=lambda _: self._navigate("/builder"),
                            ),
                        ],
                        spacing=12,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    bgcolor=ThemeColors.SURFACE_LIGHT,
                    border=ft.Border.all(1.2, ThemeColors.BORDER_LIGHT),
                    border_radius=16,
                    padding=ft.Padding.all(16),
                )
            )
        else:
            for itin in self.saved_itineraries[:4]:
                saved_cards.append(self._create_itinerary_card(itin))

        saved_column = ft.Column(
            controls=saved_cards,
            spacing=12,
        )

        return ft.Column(
            controls=[
                planner_grid,
                ft.Container(height=24),
                popular_header,
                ft.Container(height=6),
                popular_track,
                ft.Container(height=24),
                saved_header,
                ft.Container(height=6),
                saved_column,
                ft.Container(height=20),
            ],
            spacing=0,
        )

    def _build_search_results_section(self) -> ft.Control:
        header_row = ft.Row(
            controls=[
                ft.Text("Search Results", size=18, weight=ft.FontWeight.W_800, color=ThemeColors.TEXT_BLACK),
                ft.Row(
                    controls=[
                        ft.Text(f"{len(self.search_results)} places found", size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                        ft.TextButton(content="Clear Search", on_click=lambda _: self._clear_search()),
                    ],
                    spacing=8,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        if self.search_loading:
            content = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.ProgressRing(width=22, height=22, stroke_width=2),
                        ft.Text(f"Searching for '{self.search_query}'...", size=13, color=ThemeColors.TEXT_MUTED_LIGHT),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=12,
                ),
                padding=40,
            )
        elif self.search_results:
            cards = [self._create_search_result_card(p) for p in self.search_results]
            content = ft.ResponsiveRow(
                controls=[ft.Container(content=c, col={"sm": 12, "md": 6, "lg": 4}) for c in cards],
                spacing=12,
                run_spacing=12,
            )
        else:
            content = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.SEARCH_OFF_ROUNDED, size=48, color=ThemeColors.TEXT_FAINT_LIGHT),
                        ft.Text("No destinations found", size=16, weight=ft.FontWeight.BOLD),
                        ft.Text(f"No places matching '{self.search_query}'. Try another municipality or keyword.", size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                        ft.Container(height=6),
                        ft.FilledButton(
                            content="Reset Search",
                            style=ft.ButtonStyle(bgcolor=ThemeColors.PRIMARY_BLUE, color=ft.Colors.WHITE),
                            on_click=lambda _: self._clear_search(),
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                ),
                padding=50,
                alignment=ft.Alignment(0, 0),
            )

        return ft.Column(
            controls=[
                header_row,
                ft.Container(height=12),
                content,
            ],
            spacing=0,
        )

    def _create_popular_card(self, place: Place) -> ft.Control:
        # Overlaid Category Badge
        cat_badge = ft.Container(
            content=ft.Text(
                place.formatted_category,
                size=9,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.WHITE,
            ),
            bgcolor=ft.Colors.with_opacity(0.85, ThemeColors.TEXT_MAIN_LIGHT),
            border_radius=4,
            padding=ft.Padding.symmetric(horizontal=6, vertical=2),
            margin=ft.Margin.only(top=6, left=6),
        )

        img_ctrl: ft.Control
        if place.image_url and place.image_url.startswith("http"):
            img_ctrl = ft.Image(src=place.image_url, width=170, height=120, fit=ft.BoxFit.COVER)
        else:
            img_ctrl = ft.Container(
                content=ft.Icon(ft.Icons.LANDSCAPE, size=32, color=ThemeColors.PRIMARY_BLUE),
                bgcolor=ThemeColors.PRIMARY_LIGHT,
                width=170,
                height=120,
                alignment=ft.Alignment(0, 0),
            )

        img_wrapper = ft.Container(
            content=ft.Stack(controls=[img_ctrl, cat_badge]),
            border_radius=14,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            margin=ft.Margin.only(bottom=6),
        )

        title = ft.Text(
            place.name,
            size=12,
            weight=ft.FontWeight.BOLD,
            color=ThemeColors.TEXT_BLACK,
            max_lines=2,
            overflow=ft.TextOverflow.ELLIPSIS,
        )

        muni = ft.Row(
            controls=[
                ft.Icon(ft.Icons.LOCATION_ON, size=11, color=ThemeColors.PRIMARY_BLUE),
                ft.Text(place.municipality_name or "Nueva Ecija", size=10, color=ThemeColors.TEXT_MUTED_LIGHT),
            ],
            spacing=2,
        )

        cost = ft.Text(
            place.formatted_cost,
            size=11,
            weight=ft.FontWeight.BOLD,
            color=ThemeColors.BUDGET_GREEN,
        )

        return ft.Container(
            content=ft.Column(
                controls=[img_wrapper, title, muni, cost],
                spacing=2,
            ),
            width=170,
            ink=True,
            on_click=lambda _: show_place_detail_dialog(self.page, place),
        )

    def _create_search_result_card(self, place: Place) -> ft.Control:
        cat_badge = ft.Container(
            content=ft.Text(place.formatted_category, size=9, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            bgcolor=ft.Colors.with_opacity(0.85, ThemeColors.TEXT_MAIN_LIGHT),
            border_radius=4,
            padding=ft.Padding.symmetric(horizontal=6, vertical=2),
            margin=ft.Margin.only(top=6, left=6),
        )

        img_ctrl = ft.Image(src=place.image_url, width=120, height=100, fit=ft.BoxFit.COVER) if place.image_url and place.image_url.startswith("http") else ft.Container(
            content=ft.Icon(ft.Icons.LANDSCAPE, size=28, color=ThemeColors.PRIMARY_BLUE),
            bgcolor=ThemeColors.PRIMARY_LIGHT,
            width=120,
            height=100,
            alignment=ft.Alignment(0, 0),
        )

        img_wrapper = ft.Container(
            content=ft.Stack(controls=[img_ctrl, cat_badge]),
            border_radius=10,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )

        info = ft.Column(
            controls=[
                ft.Text(place.name, size=13, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_BLACK, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.LOCATION_ON, size=12, color=ThemeColors.PRIMARY_BLUE),
                        ft.Text(place.municipality_name or "Nueva Ecija", size=11, color=ThemeColors.PRIMARY_BLUE, weight=ft.FontWeight.W_600),
                    ],
                    spacing=2,
                ),
                ft.Text(place.formatted_cost, size=11, color=ThemeColors.BUDGET_GREEN, weight=ft.FontWeight.BOLD),
            ],
            spacing=4,
            expand=True,
        )

        return ft.Container(
            content=ft.Row(
                controls=[img_wrapper, info],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border=ft.Border.all(1.2, ThemeColors.BORDER_LIGHT),
            border_radius=14,
            padding=10,
            ink=True,
            on_click=lambda _: show_place_detail_dialog(self.page, place),
        )

    def _create_itinerary_card(self, itin: Itinerary) -> ft.Control:
        is_suggested = itin.type == "suggested"
        badge_bg = ThemeColors.SUGGESTED_BADGE_BG if is_suggested else ThemeColors.CUSTOM_BADGE_BG
        badge_color = ThemeColors.SUGGESTED_BADGE_TEXT if is_suggested else ThemeColors.CUSTOM_BADGE_TEXT
        badge_label = "Suggested Plan" if is_suggested else "Custom Plan"

        badge = ft.Container(
            content=ft.Text(badge_label, size=10, weight=ft.FontWeight.BOLD, color=badge_color),
            bgcolor=badge_bg,
            border_radius=6,
            padding=ft.Padding.symmetric(horizontal=8, vertical=3),
        )

        budget = ft.Text(
            f"₱{int(itin.daily_budget):,}/day" if itin.daily_budget else "Flexible",
            size=11,
            weight=ft.FontWeight.BOLD,
            color=ThemeColors.BUDGET_GREEN,
        )

        header_row = ft.Row(
            controls=[badge, budget],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        title = ft.Text(itin.title, size=14, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_BLACK)

        dest = ft.Row(
            controls=[
                ft.Icon(ft.Icons.LOCATION_ON, size=13, color=ThemeColors.PRIMARY_BLUE),
                ft.Text(itin.destination or "Nueva Ecija", size=11, color=ThemeColors.TEXT_MUTED_LIGHT),
            ],
            spacing=4,
        )

        dates = ft.Row(
            controls=[
                ft.Icon(ft.Icons.CALENDAR_TODAY, size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                ft.Text(f"{itin.start_date} → {itin.end_date}", size=11, color=ThemeColors.TEXT_MUTED_LIGHT),
            ],
            spacing=4,
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    header_row,
                    title,
                    dest,
                    dates,
                ],
                spacing=4,
            ),
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border=ft.Border.all(1.2, ThemeColors.BORDER_LIGHT),
            border_radius=16,
            padding=14,
            ink=True,
            on_click=lambda _: self._navigate(f"/trips/{itin.id}"),
        )

    def _on_search_change(self, val: str) -> None:
        self.search_query = val
        if not val.strip():
            self._clear_search()

    def _on_search_submit(self, val: str) -> None:
        query = val.strip()
        if not query:
            self._clear_search()
            return

        self.is_searching = True
        self.search_loading = True
        self._build_content()
        self._safe_update()

        async def _do_search():
            try:
                res = await self.place_service.get_places(page=1, page_size=12, search=query)
                self.search_results = res.items
            except Exception:
                self.search_results = []
            finally:
                self.search_loading = False
                self._build_content()
                self._safe_update()

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_do_search())
        except RuntimeError:
            try:
                asyncio.run(_do_search())
            except Exception:
                pass

    def _safe_update(self) -> None:
        try:
            self.update()
        except Exception:
            pass

    def _clear_search(self) -> None:
        self.is_searching = False
        self.search_query = ""
        self.search_results = []
        self._build_content()
        self._safe_update()

    def _on_bell_clicked(self) -> None:
        self.unread_notifications = 0
        self._build_content()
        self._safe_update()

    def _load_data(self) -> None:
        async def _fetch():
            try:
                places_res = await self.place_service.get_places(page=1, page_size=8)
                self.destinations = places_res.items
            except Exception:
                self.destinations = []

            try:
                self.saved_itineraries = await self.itinerary_service.list_itineraries()
            except Exception:
                self.saved_itineraries = []

            self._build_content()
            self._safe_update()

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_fetch())
        except RuntimeError:
            pass

    def _navigate(self, route: str) -> None:
        if self.on_navigate:
            self.on_navigate(route)
