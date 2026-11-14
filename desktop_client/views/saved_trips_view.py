"""Saved Trips Management View mirroring Ionic tabs/history and image_2d1020.png."""

from __future__ import annotations

import asyncio
from datetime import date
from typing import Callable, Optional
import flet as ft

from desktop_client.components.dialogs import show_confirm_dialog
from desktop_client.config.settings import ThemeColors
from desktop_client.models.itinerary import Itinerary
from desktop_client.services.itinerary_service import get_itinerary_service


class SavedTripsView(ft.Container):
    """Saved itineraries view matching Ionic tabs/history and image_2d1020.png."""

    def __init__(
        self,
        on_navigate: Optional[Callable[[str], None]] = None,
        on_select_trip: Optional[Callable[[Itinerary], None]] = None,
    ):
        super().__init__()
        self.on_navigate = on_navigate
        self.on_select_trip = on_select_trip
        self.itinerary_service = get_itinerary_service()

        self.expand = True
        self.padding = 0
        self.bgcolor = ThemeColors.BG_LIGHT

        self.active_segment = "all"  # all, upcoming, past, suggested, custom
        self.search_term = ""

        self.itineraries: list[Itinerary] = []
        self.is_loading = True

        self._build_content()
        self._load_trips()

    def _build_content(self) -> None:
        # Top Header Bar matching .history-toolbar in image_2d1020.png
        top_toolbar = ft.Container(
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border=ft.Border.only(bottom=ft.BorderSide(1, ThemeColors.BORDER_LIGHT)),
            padding=ft.Padding.symmetric(horizontal=20, vertical=10),
            content=ft.Row(
                controls=[
                    ft.Text("Saved Itineraries", size=18, weight=ft.FontWeight.W_800, color=ThemeColors.TEXT_BLACK),
                    ft.IconButton(
                        icon=ft.Icons.ADD,
                        icon_size=24,
                        icon_color=ThemeColors.PRIMARY_BLUE,
                        tooltip="New Itinerary",
                        on_click=lambda _: self._navigate("/builder"),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        if self.is_loading:
            body = ft.Container(
                expand=True,
                alignment=ft.Alignment(0, 0),
                content=ft.Row(
                    controls=[
                        ft.ProgressRing(width=24, height=24, stroke_width=2),
                        ft.Text("Loading saved trips...", size=13, color=ThemeColors.TEXT_MUTED_LIGHT),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=12,
                ),
            )
            self.content = ft.Column(controls=[top_toolbar, body], spacing=0, expand=True)
            return

        # Empty State (len(self.itineraries) == 0) — Exact match to image_2d1020.png
        if len(self.itineraries) == 0:
            clock_circle = ft.Container(
                width=72,
                height=72,
                border_radius=36,
                bgcolor="#e0f2fe",
                alignment=ft.Alignment(0, 0),
                content=ft.Icon(ft.Icons.ACCESS_TIME_ROUNDED, size=34, color=ThemeColors.PRIMARY_BLUE),
            )

            suggested_btn = ft.Container(
                width=360,
                height=46,
                bgcolor="#0f172a",
                border_radius=10,
                alignment=ft.Alignment(0, 0),
                ink=True,
                on_click=lambda _: self._navigate("/suggested"),
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.AUTO_AWESOME, size=18, color=ft.Colors.WHITE),
                        ft.Text("Suggested Itinerary", size=14, weight=ft.FontWeight.W_700, color=ft.Colors.WHITE),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=8,
                ),
            )

            custom_btn = ft.Container(
                width=360,
                height=46,
                bgcolor=ThemeColors.PRIMARY_BLUE,
                border_radius=10,
                alignment=ft.Alignment(0, 0),
                ink=True,
                on_click=lambda _: self._navigate("/builder"),
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.ADD, size=18, color=ft.Colors.WHITE),
                        ft.Text("Custom Itinerary", size=14, weight=ft.FontWeight.W_700, color=ft.Colors.WHITE),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=8,
                ),
            )

            empty_body = ft.Container(
                expand=True,
                alignment=ft.Alignment(0, 0),
                content=ft.Column(
                    controls=[
                        clock_circle,
                        ft.Container(height=10),
                        ft.Text("No Saved Itineraries Yet", size=22, weight=ft.FontWeight.W_800, color=ThemeColors.TEXT_BLACK),
                        ft.Container(
                            width=420,
                            content=ft.Text(
                                "Your saved trips will appear here. Choose how you would like to plan your Nueva Ecija travel experience:",
                                size=13,
                                color=ThemeColors.TEXT_FAINT_LIGHT,
                                text_align=ft.TextAlign.CENTER,
                            ),
                        ),
                        ft.Container(height=14),
                        suggested_btn,
                        ft.Container(height=4),
                        custom_btn,
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=4,
                ),
            )
            self.content = ft.Column(controls=[top_toolbar, empty_body], spacing=0, expand=True)
            return

        # Non-empty state (savedItineraries.length > 0)
        body_controls: list[ft.Control] = []

        # Search & Segment Filter Header (only shown when savedItineraries.length > 2, matching history.page.html:8)
        if len(self.itineraries) > 2:
            self.search_field = ft.TextField(
                hint_text="Search saved trips or municipalities...",
                hint_style=ft.TextStyle(size=12, color=ThemeColors.TEXT_FAINT_LIGHT),
                prefix_icon=ft.Icons.SEARCH_ROUNDED,
                value=self.search_term,
                border_radius=12,
                border_color=ThemeColors.BORDER_LIGHT,
                focused_border_color=ThemeColors.PRIMARY_BLUE,
                dense=True,
                on_change=lambda e: self._on_search_change(e.control.value),
            )
            segments = [
                ("all", f"All ({len(self.itineraries)})"),
                ("upcoming", "Upcoming"),
                ("past", "Past"),
                ("suggested", "Suggested"),
                ("custom", "Custom"),
            ]
            segments_row = ft.Row(
                controls=[
                    self._create_segment_pill(seg_key, seg_label, self.active_segment == seg_key)
                    for seg_key, seg_label in segments
                ],
                spacing=8,
                scroll=ft.ScrollMode.AUTO,
            )
            body_controls.extend([self.search_field, ft.Container(height=8), segments_row, ft.Container(height=12)])

        muni_dest = self.itineraries[0].destination if self.itineraries else "Nueva Ecija"
        trip_count_text = f"{len(self.itineraries)} {'Trip' if len(self.itineraries) == 1 else 'Trips'} Planned in {muni_dest}"

        headline_block = ft.Column(
            controls=[
                ft.Text("Your Saved Trips", size=20, weight=ft.FontWeight.W_800, color=ThemeColors.TEXT_BLACK),
                ft.Text(trip_count_text, size=13, color=ThemeColors.TEXT_MUTED_LIGHT),
            ],
            spacing=2,
        )
        body_controls.extend([headline_block, ft.Container(height=14)])

        filtered_trips = self._get_filtered_trips()
        if filtered_trips:
            cards = [self._create_trip_card(it) for it in filtered_trips]
            grid = ft.ResponsiveRow(
                controls=[ft.Container(content=c, col={"sm": 12, "md": 6, "lg": 4}) for c in cards],
                spacing=16,
                run_spacing=16,
            )
            body_controls.append(grid)
        else:
            body_controls.append(
                ft.Container(
                    padding=40,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.FILTER_ALT_OUTLINED, size=36, color=ThemeColors.PRIMARY_BLUE),
                            ft.Text("No Matching Itineraries", size=16, weight=ft.FontWeight.BOLD),
                            ft.Text(
                                f'No saved trips found for "{self.search_term or self.active_segment}". Try clearing your search or switching filter tabs.',
                                size=12,
                                color=ThemeColors.TEXT_MUTED_LIGHT,
                            ),
                            ft.FilledButton(
                                content=f"Show All Trips ({len(self.itineraries)})",
                                style=ft.ButtonStyle(bgcolor=ThemeColors.PRIMARY_BLUE, color=ft.Colors.WHITE),
                                on_click=lambda _: self._reset_filters(),
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                    ),
                )
            )

        scroll_area = ft.Container(
            expand=True,
            padding=ft.Padding.symmetric(horizontal=28, vertical=20),
            content=ft.Column(controls=body_controls, spacing=0, scroll=ft.ScrollMode.AUTO, expand=True),
        )
        self.content = ft.Column(controls=[top_toolbar, scroll_area], spacing=0, expand=True)

    def _create_segment_pill(self, key: str, label: str, is_active: bool) -> ft.Control:
        return ft.Container(
            content=ft.Text(
                label,
                size=12,
                weight=ft.FontWeight.W_700 if is_active else ft.FontWeight.W_500,
                color=ft.Colors.WHITE if is_active else ThemeColors.TEXT_MAIN_LIGHT,
            ),
            bgcolor=ThemeColors.PRIMARY_BLUE if is_active else ThemeColors.SURFACE_LIGHT,
            border=ft.Border.all(1.2, ThemeColors.PRIMARY_BLUE if is_active else ThemeColors.BORDER_LIGHT),
            border_radius=20,
            padding=ft.Padding.symmetric(horizontal=14, vertical=8),
            ink=True,
            on_click=lambda _: self._on_segment_select(key),
        )

    def _get_days_nights_label(self, itin: Itinerary) -> str:
        days = len(itin.days) if itin.days else 1
        nights = max(0, days - 1)
        return f"{days} Days - {nights} {'Night' if nights == 1 else 'Nights'}" if nights > 0 else f"{days} Day"

    def _create_trip_card(self, itin: Itinerary) -> ft.Control:
        is_suggested = itin.type == "suggested"
        badge_bg = ThemeColors.SUGGESTED_BADGE_BG if is_suggested else ThemeColors.CUSTOM_BADGE_BG
        badge_color = ThemeColors.SUGGESTED_BADGE_TEXT if is_suggested else ThemeColors.CUSTOM_BADGE_TEXT
        badge_label = "Suggested Plan" if is_suggested else "Custom Plan"

        return ft.Container(
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border=ft.Border.all(1.2, ThemeColors.BORDER_LIGHT),
            border_radius=16,
            padding=16,
            ink=True,
            on_click=lambda _: self._open_trip(itin),
            shadow=ft.BoxShadow(blur_radius=8, color=ft.Colors.with_opacity(0.04, "#000000")),
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Container(
                                content=ft.Text(badge_label, size=10, weight=ft.FontWeight.BOLD, color=badge_color),
                                bgcolor=badge_bg,
                                border_radius=6,
                                padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                            ),
                            ft.Row(
                                spacing=4,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Text(
                                        f"₱{int(itin.daily_budget):,}/day" if itin.daily_budget else "₱0/day",
                                        size=12,
                                        weight=ft.FontWeight.BOLD,
                                        color=ThemeColors.BUDGET_GREEN,
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.DELETE,
                                        icon_size=18,
                                        icon_color=ThemeColors.ERROR,
                                        tooltip="Delete itinerary",
                                        on_click=lambda _: self._delete_trip(itin),
                                    ),
                                ],
                            ),
                        ],
                    ),
                    ft.Text(itin.title, size=16, weight=ft.FontWeight.W_800, color=ThemeColors.TEXT_BLACK, max_lines=1),
                    ft.Row(
                        spacing=4,
                        controls=[
                            ft.Icon(ft.Icons.LOCATION_ON, size=14, color=ThemeColors.PRIMARY_BLUE),
                            ft.Text(itin.destination or "Nueva Ecija", size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                        ],
                    ),
                    ft.Divider(color="#f1f5f9", height=1),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Row(
                                spacing=4,
                                controls=[
                                    ft.Icon(ft.Icons.CALENDAR_TODAY, size=13, color=ThemeColors.PRIMARY_BLUE),
                                    ft.Text(f"{itin.start_date} → {itin.end_date}", size=11, color=ThemeColors.TEXT_MUTED_LIGHT),
                                ],
                            ),
                            ft.Container(
                                content=ft.Text(self._get_days_nights_label(itin), size=10, weight=ft.FontWeight.BOLD, color=ThemeColors.PRIMARY_BLUE),
                                bgcolor=ThemeColors.AZURE_SOFT,
                                border_radius=10,
                                padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                            ),
                        ],
                    ),
                ],
            ),
        )

    def _get_filtered_trips(self) -> list[Itinerary]:
        results = self.itineraries
        today = date.today().strftime("%Y-%m-%d")
        if self.active_segment == "suggested":
            results = [it for it in results if it.type == "suggested"]
        elif self.active_segment == "custom":
            results = [it for it in results if it.type != "suggested"]
        elif self.active_segment == "upcoming":
            results = [it for it in results if (it.end_date or "") >= today]
        elif self.active_segment == "past":
            results = [it for it in results if (it.end_date or "") < today]

        if self.search_term.strip():
            q = self.search_term.strip().lower()
            results = [
                it for it in results
                if q in (it.title or "").lower() or q in (it.destination or "").lower()
            ]
        return results

    def _reset_filters(self) -> None:
        self.search_term = ""
        self.active_segment = "all"
        self._build_content()
        self._safe_update()

    def _safe_update(self) -> None:
        try:
            self.update()
        except Exception:
            pass

    def _on_segment_select(self, seg_key: str) -> None:
        self.active_segment = seg_key
        self._build_content()
        self._safe_update()

    def _on_search_change(self, query: str) -> None:
        self.search_term = query
        self._build_content()
        self._safe_update()

    def _open_trip(self, itin: Itinerary) -> None:
        if self.on_select_trip:
            self.on_select_trip(itin)

    @property
    def safe_page(self) -> Optional[ft.Page]:
        try:
            return self.page
        except Exception:
            return None

    def _delete_trip(self, itin: Itinerary) -> None:
        def confirm():
            async def _worker():
                await self.itinerary_service.delete_itinerary(itin.id)
                await self._load_trips_async()
            if self.safe_page:
                self.safe_page.run_task(_worker)
            else:
                try:
                    asyncio.get_running_loop().create_task(_worker())
                except RuntimeError:
                    pass

        if self.safe_page:
            show_confirm_dialog(
                self.safe_page,
                title="Delete Itinerary?",
                message=f'Are you sure you want to delete "{itin.title}"? This action cannot be undone.',
                on_confirm=confirm,
            )

    def _load_trips(self) -> None:
        if self.safe_page:
            self.safe_page.run_task(self._load_trips_async)
        else:
            try:
                asyncio.get_running_loop().create_task(self._load_trips_async())
            except RuntimeError:
                pass

    async def _load_trips_async(self) -> None:
        self.is_loading = True
        self._build_content()
        self._safe_update()
        try:
            self.itineraries = await self.itinerary_service.list_itineraries()
        except Exception:
            self.itineraries = []
        finally:
            self.is_loading = False
            self._build_content()
            self._safe_update()

    def _navigate(self, route: str) -> None:
        if self.on_navigate:
            self.on_navigate(route)
