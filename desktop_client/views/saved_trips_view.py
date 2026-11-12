"""Saved Trips Management View."""

import asyncio
from typing import Callable, Optional
import flet as ft

from desktop_client.components.dialogs import show_confirm_dialog, show_export_dialog
from desktop_client.config.settings import ThemeColors
from desktop_client.models.itinerary import Itinerary
from desktop_client.services.itinerary_service import get_itinerary_service


class SavedTripsView(ft.Container):
    """Catalog of saved travel itineraries across cloud sync and local guest persistence."""

    def __init__(self, on_navigate: Optional[Callable[[str], None]] = None, on_select_trip: Optional[Callable[[Itinerary], None]] = None):
        super().__init__()
        self.on_navigate = on_navigate
        self.on_select_trip = on_select_trip
        self.itinerary_service = get_itinerary_service()

        self.expand = True
        self.padding = ft.padding.all(24)
        self.bgcolor = ThemeColors.BG_LIGHT

        self.itineraries: list[Itinerary] = []
        self.is_loading = True
        self.feedback_message: Optional[str] = None

        self._build_content()
        self._load_trips()

    def _build_content(self) -> None:
        header_row = ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text("Saved Itineraries", size=22, weight=ft.FontWeight.BOLD),
                        ft.Text("Access, export, and review your multi-day Nueva Ecija travel plans.", size=13, color=ThemeColors.TEXT_MUTED_LIGHT),
                    ],
                    spacing=2,
                ),
                ft.Row(
                    controls=[
                        ft.FilledButton(
                            content="+ Custom Builder",
                            icon=ft.Icons.ADD,
                            style=ft.ButtonStyle(bgcolor=ThemeColors.AZURE_PRIMARY, color=ft.Colors.WHITE),
                            on_click=lambda _: self._navigate("/builder"),
                        ),
                        ft.FilledButton(
                            content="+ AI Wizard",
                            icon=ft.Icons.AUTO_AWESOME,
                            style=ft.ButtonStyle(bgcolor=ThemeColors.EMERALD_PRIMARY, color=ft.Colors.WHITE),
                            on_click=lambda _: self._navigate("/suggested"),
                        ),
                    ],
                    spacing=8,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        content_section: ft.Control
        if self.is_loading:
            content_section = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.ProgressRing(width=24, height=24, stroke_width=3),
                        ft.Text("Loading saved trips...", size=13, color=ThemeColors.TEXT_MUTED_LIGHT),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=10,
                ),
                padding=60,
                alignment=ft.Alignment(0, 0),
            )
        elif not self.itineraries:
            content_section = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.MAP_OUTLINED, size=56, color=ThemeColors.TEXT_MUTED_LIGHT),
                        ft.Text("No saved itineraries yet.", size=16, weight=ft.FontWeight.BOLD),
                        ft.Text("Generate an optimized route with the AI Wizard or assemble your own custom stops.", size=13, color=ThemeColors.TEXT_MUTED_LIGHT),
                        ft.Container(height=12),
                        ft.Row(
                            controls=[
                                ft.FilledButton(
                                    content="Launch AI Wizard",
                                    icon=ft.Icons.AUTO_AWESOME,
                                    style=ft.ButtonStyle(bgcolor=ThemeColors.EMERALD_PRIMARY, color=ft.Colors.WHITE),
                                    on_click=lambda _: self._navigate("/suggested"),
                                ),
                                ft.OutlinedButton(
                                    content="Open Custom Builder",
                                    icon=ft.Icons.EDIT_CALENDAR,
                                    on_click=lambda _: self._navigate("/builder"),
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=12,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=6,
                ),
                padding=60,
                alignment=ft.Alignment(0, 0),
            )
        else:
            cards = [self._create_trip_card(itin) for itin in self.itineraries]
            content_section = ft.Column(
                controls=cards,
                spacing=12,
            )

        self.content = ft.Column(
            controls=[
                header_row,
                ft.Divider(height=24, color=ThemeColors.BORDER_LIGHT),
                content_section,
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=0,
        )

    def _create_trip_card(self, itin: Itinerary) -> ft.Control:
        source_badge = "Local Guest Trip" if itin.is_guest else "Cloud Synced"
        badge_bg = ThemeColors.AMBER_LIGHT if itin.is_guest else ThemeColors.SUCCESS_BG
        badge_color = ThemeColors.WARM_GOLD if itin.is_guest else ThemeColors.SUCCESS

        total_days = len(itin.days)
        total_stops = itin.total_stops
        est_cost = itin.total_estimated_cost

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Icon(ft.Icons.ROUTE_ROUNDED, size=28, color=ThemeColors.EMERALD_PRIMARY),
                        bgcolor=ThemeColors.EMERALD_MINT,
                        border_radius=12,
                        padding=14,
                    ),
                    ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(itin.title, size=15, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_MAIN_LIGHT),
                                    ft.Container(
                                        content=ft.Text(source_badge, size=10, weight=ft.FontWeight.W_600, color=badge_color),
                                        bgcolor=badge_bg,
                                        border_radius=6,
                                        padding=ft.padding.symmetric(horizontal=8, vertical=2),
                                    ),
                                ],
                                spacing=8,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Text(
                                f"{itin.date_range_display} • {total_days} Days • {total_stops} Scheduled Stops",
                                size=12,
                                color=ThemeColors.TEXT_MUTED_LIGHT,
                            ),
                            ft.Text(
                                f"Estimated Cost: ₱{est_cost:,.2f} (~₱{itin.daily_budget:,.0f} / day budget)",
                                size=11,
                                weight=ft.FontWeight.W_500,
                                color=ThemeColors.EMERALD_PRIMARY,
                            ),
                        ],
                        spacing=3,
                        expand=True,
                    ),
                    ft.Row(
                        controls=[
                            ft.FilledButton(
                                content="View Timeline",
                                icon=ft.Icons.VISIBILITY,
                                style=ft.ButtonStyle(bgcolor=ThemeColors.EMERALD_PRIMARY, color=ft.Colors.WHITE),
                                on_click=lambda _, it=itin: self._view_trip_detail(it),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DOWNLOAD,
                                tooltip="Export Itinerary",
                                on_click=lambda _, it=itin: self._open_export(it),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DELETE_OUTLINE,
                                icon_color=ThemeColors.ERROR,
                                tooltip="Delete Itinerary",
                                on_click=lambda _, it=itin: self._confirm_delete(it),
                            ),
                        ],
                        spacing=4,
                    ),
                ],
                spacing=16,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border_radius=12,
            border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
            padding=16,
        )

    def _load_trips(self) -> None:
        async def _fetch():
            try:
                trips = await self.itinerary_service.list_itineraries()
                self.itineraries = trips
            except Exception:
                self.itineraries = []
            finally:
                self.is_loading = False
                self._build_content()
                try:
                    self.update()
                except Exception:
                    pass

        asyncio.create_task(_fetch())

    def _view_trip_detail(self, itin: Itinerary) -> None:
        if self.on_select_trip:
            self.on_select_trip(itin)
        elif self.on_navigate:
            self.on_navigate(f"/trips/{itin.id}")

    def _open_export(self, itin: Itinerary) -> None:
        if self.page:
            show_export_dialog(self.page, itin)

    def _confirm_delete(self, itin: Itinerary) -> None:
        if not self.page:
            return

        def do_delete():
            async def _exec():
                await self.itinerary_service.delete_itinerary(itin.id, is_guest=itin.is_guest)
                self._load_trips()
            asyncio.create_task(_exec())

        show_confirm_dialog(
            self.page,
            title="Delete Itinerary?",
            message=f"Are you sure you want to delete '{itin.title}'? This will remove all day schedules permanently.",
            on_confirm=do_delete,
        )

    def _navigate(self, route: str) -> None:
        if self.on_navigate:
            self.on_navigate(route)
