"""Dashboard Hub View."""

import asyncio
from typing import Callable, Optional
import flet as ft

from desktop_client.components.dialogs import show_place_detail_dialog
from desktop_client.components.place_card import PlaceCard
from desktop_client.config.settings import ThemeColors
from desktop_client.core.session import get_session_manager
from desktop_client.models.place import Place
from desktop_client.services.itinerary_service import get_itinerary_service
from desktop_client.services.place_service import get_place_service


class DashboardView(ft.Container):
    """Main dashboard hub providing quick stats, itinerary action cards,

    and featured destinations.
    """

    def __init__(self, on_navigate: Optional[Callable[[str], None]] = None):
        super().__init__()
        self.on_navigate = on_navigate
        self.session_manager = get_session_manager()
        self.place_service = get_place_service()
        self.itinerary_service = get_itinerary_service()

        self.expand = True
        self.padding = ft.padding.all(24)
        self.bgcolor = ThemeColors.BG_LIGHT

        self.featured_places: list[Place] = []
        self.saved_trips_count: int = 0
        self.is_loading = True

        self._build_content()
        self._load_data()

    def _build_content(self) -> None:
        user_name = self.session_manager.display_name
        is_guest = self.session_manager.is_guest or not self.session_manager.is_authenticated

        # Welcome Hero Banner
        hero_banner = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Text(
                                f"Mabuhay, {user_name}!",
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.WHITE,
                            ),
                            ft.Text(
                                "Plan your journey across Nueva Ecija's 32 municipalities — from Sierra Madre "
                                "mountain heights and Pantabangan lake waters to heritage churches and farm bistros.",
                                size=13,
                                color=ThemeColors.EMERALD_MINT,
                                max_lines=2,
                            ),
                        ],
                        spacing=4,
                        expand=True,
                    ),
                    ft.Container(
                        content=ft.FilledButton(
                            content="Explore All 2,670+ POIs",
                            icon=ft.Icons.TRAVEL_EXPLORE,
                            style=ft.ButtonStyle(
                                bgcolor=ThemeColors.AZURE_PRIMARY,
                                color=ft.Colors.WHITE,
                            ),
                            on_click=lambda _: self._navigate("/places"),
                        ),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=ThemeColors.EMERALD_DARK,
            border_radius=16,
            padding=24,
            margin=ft.margin.only(bottom=20),
        )

        # Quick Stats Cards
        stats_cards = ft.Row(
            controls=[
                self._create_stat_card("2,673", "Registered POIs", ft.Icons.PLACE, ThemeColors.AZURE_PRIMARY),
                self._create_stat_card("32", "Municipalities & Cities", ft.Icons.LOCATION_CITY, ThemeColors.EMERALD_PRIMARY),
                self._create_stat_card(
                    str(self.saved_trips_count),
                    "Saved Itineraries",
                    ft.Icons.BOOKMARK_BORDER,
                    ThemeColors.WARM_GOLD,
                    on_click=lambda: self._navigate("/trips"),
                ),
            ],
            spacing=16,
        )

        # Action Cards
        action_cards = ft.Row(
            controls=[
                self._create_action_card(
                    title="AI Suggested Itinerary Wizard",
                    subtitle="Fast, clustered travel planning",
                    description="Answer 4 quick questions (destination, dates, budget, pacing) to generate an optimized multi-day travel schedule.",
                    icon=ft.Icons.AUTO_AWESOME,
                    badge_text="Automated Clustering",
                    color=ThemeColors.EMERALD_PRIMARY,
                    route="/suggested",
                ),
                self._create_action_card(
                    title="Custom Itinerary Builder",
                    subtitle="Stop-by-stop interactive timeline",
                    description="Craft your own journey with dual-pane catalog search, off-grid venue support, and drag-and-drop reordering.",
                    icon=ft.Icons.EDIT_CALENDAR,
                    badge_text="Full Creative Control",
                    color=ThemeColors.AZURE_PRIMARY,
                    route="/builder",
                ),
            ],
            spacing=16,
        )

        # Featured Section
        self.featured_row = ft.Row(
            controls=[],
            scroll=ft.ScrollMode.AUTO,
            spacing=16,
        )

        if self.is_loading:
            self.featured_row.controls = [
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.ProgressRing(width=20, height=20, stroke_width=2),
                            ft.Text("Loading featured destinations...", size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                        ],
                        spacing=10,
                    ),
                    padding=20,
                )
            ]
        elif self.featured_places:
            self.featured_row.controls = [
                PlaceCard(
                    place=p,
                    on_view_details=self._show_place_details,
                    on_add_to_day=lambda p: self._navigate("/builder"),
                    width=290,
                )
                for p in self.featured_places
            ]
        else:
            self.featured_row.controls = [
                ft.Text("No featured destinations found.", size=12, color=ThemeColors.TEXT_MUTED_LIGHT)
            ]

        featured_header = ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text("Featured Destinations", size=16, weight=ft.FontWeight.BOLD),
                        ft.Text("Handpicked highlights from across the province", size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                    ],
                    spacing=1,
                ),
                ft.TextButton(
                    content="View All Places →",
                    on_click=lambda _: self._navigate("/places"),
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        self.content = ft.Column(
            controls=[
                hero_banner,
                stats_cards,
                ft.Container(height=16),
                action_cards,
                ft.Container(height=24),
                featured_header,
                ft.Container(height=8),
                self.featured_row,
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=0,
        )

    def _create_stat_card(
        self,
        value: str,
        label: str,
        icon: str,
        color: str,
        on_click: Optional[Callable[[], None]] = None,
    ) -> ft.Control:
        card = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Icon(icon, size=24, color=color),
                        bgcolor=f"{color}1A",  # 10% opacity
                        border_radius=10,
                        padding=12,
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(value, size=20, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_MAIN_LIGHT),
                            ft.Text(label, size=11, color=ThemeColors.TEXT_MUTED_LIGHT),
                        ],
                        spacing=2,
                    ),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border_radius=12,
            border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
            padding=16,
            expand=True,
            ink=bool(on_click),
            on_click=lambda _: on_click() if on_click else None,
        )
        return card

    def _create_action_card(
        self,
        title: str,
        subtitle: str,
        description: str,
        icon: str,
        badge_text: str,
        color: str,
        route: str,
    ) -> ft.Control:
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Icon(icon, size=24, color=ft.Colors.WHITE),
                                bgcolor=color,
                                border_radius=10,
                                padding=10,
                            ),
                            ft.Container(
                                content=ft.Text(badge_text, size=10, weight=ft.FontWeight.W_600, color=color),
                                bgcolor=f"{color}1A",
                                border_radius=6,
                                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Container(height=4),
                    ft.Text(title, size=16, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_MAIN_LIGHT),
                    ft.Text(subtitle, size=12, weight=ft.FontWeight.W_500, color=color),
                    ft.Text(description, size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                    ft.Container(height=8),
                    ft.Row(
                        controls=[
                            ft.Text("Launch Planner", size=12, weight=ft.FontWeight.W_600, color=color),
                            ft.Icon(ft.Icons.ARROW_FORWARD, size=14, color=color),
                        ],
                        spacing=4,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                spacing=6,
            ),
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border_radius=14,
            border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
            padding=20,
            expand=True,
            ink=True,
            on_click=lambda _: self._navigate(route),
        )

    def _load_data(self) -> None:
        async def _fetch():
            try:
                places = await self.place_service.get_featured_places(limit=6)
                trips = await self.itinerary_service.list_itineraries()
                self.featured_places = places
                self.saved_trips_count = len(trips)
            except Exception:
                pass
            finally:
                self.is_loading = False
                self._build_content()
                try:
                    self.update()
                except Exception:
                    pass

        asyncio.create_task(_fetch())

    def _show_place_details(self, place: Place) -> None:
        if self.page:
            show_place_detail_dialog(
                self.page,
                place,
                on_add_to_day=lambda p: self._navigate("/builder"),
            )

    def _navigate(self, route: str) -> None:
        if self.on_navigate:
            self.on_navigate(route)
