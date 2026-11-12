"""Saved Trips Management View mirroring Ionic tabs/history."""

import asyncio
from datetime import date
from typing import Callable, Optional
import flet as ft

from desktop_client.components.dialogs import show_confirm_dialog, show_export_dialog
from desktop_client.config.settings import ThemeColors
from desktop_client.models.itinerary import Itinerary
from desktop_client.services.itinerary_service import get_itinerary_service


class SavedTripsView(ft.Container):
    """Saved itineraries view matching Ionic tabs/history:

    - Search input pill + Segment tabs capsule bar (All, Upcoming, Past, Suggested, Custom).
    - 'Your Saved Trips' headline with count badge.
    - Plan cards with Suggested/Custom badges, daily budget, and export/delete options.
    """

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
        self.padding = ft.Padding.symmetric(horizontal=28, vertical=20)
        self.bgcolor = ThemeColors.BG_LIGHT

        # Filter state
        self.active_segment = "all"  # all, upcoming, past, suggested, custom
        self.search_term = ""

        self.itineraries: list[Itinerary] = []
        self.is_loading = True

        self._build_content()
        self._load_trips()

    def _build_content(self) -> None:
        # Header Row matching .history-toolbar
        title_block = ft.Column(
            controls=[
                ft.Text("Saved Itineraries", size=24, weight=ft.FontWeight.W_800, color=ThemeColors.TEXT_BLACK),
                ft.Text("Manage, export, and review your multi-day schedules.", size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
            ],
            spacing=2,
        )

        new_trip_btn = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.ADD, size=16, color=ft.Colors.WHITE),
                    ft.Text("New Itinerary", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ],
                spacing=6,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            bgcolor=ThemeColors.PRIMARY_BLUE,
            border_radius=12,
            height=44,
            padding=ft.Padding.symmetric(horizontal=16),
            ink=True,
            on_click=lambda _: self._navigate("/builder"),
        )

        header_row = ft.Row(
            controls=[title_block, new_trip_btn],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        # Search Bar matching .search-input-pill
        self.search_field = ft.TextField(
            hint_text="Search saved trips or municipalities...",
            hint_style=ft.TextStyle(size=12, color=ThemeColors.TEXT_FAINT_LIGHT),
            prefix_icon=ft.Icons.SEARCH_ROUNDED,
            value=self.search_term,
            border_radius=12,
            border_color=ThemeColors.BORDER_LIGHT,
            focused_border_color=ThemeColors.PRIMARY_BLUE,
            expand=True,
            on_change=lambda e: self._on_search_change(e.control.value),
        )

        # Segment Tabs Capsule Bar matching .history-segments-scroll
        segments = [
            ("all", f"All ({len(self.itineraries)})"),
            ("upcoming", "Upcoming"),
            ("past", "Past"),
            ("suggested", "Suggested"),
            ("custom", "Custom"),
        ]

        segment_buttons = [
            self._create_segment_pill(seg_key, seg_label, self.active_segment == seg_key)
            for seg_key, seg_label in segments
        ]

        segments_row = ft.Row(
            controls=segment_buttons,
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
        )

        # Filter the trips
        filtered_trips = self._get_filtered_trips()

        # Section Headline Block matching .saved-trips-heading-block
        muni_dest = filtered_trips[0].destination if filtered_trips else "Nueva Ecija"
        trip_count_text = f"{len(filtered_trips)} {'Trip' if len(filtered_trips) == 1 else 'Trips'} Planned in {muni_dest}"

        headline_block = ft.Column(
            controls=[
                ft.Text("Your Saved Trips", size=18, weight=ft.FontWeight.W_800, color=ThemeColors.TEXT_BLACK),
                ft.Text(trip_count_text, size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
            ],
            spacing=2,
        )

        # Content List / Empty State
        content_section: ft.Control
        if self.is_loading:
            content_section = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.ProgressRing(width=24, height=24, stroke_width=2),
                        ft.Text("Loading saved trips...", size=13, color=ThemeColors.TEXT_MUTED_LIGHT),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=12,
                ),
                padding=60,
                alignment=ft.Alignment(0, 0),
            )
        elif not filtered_trips:
            content_section = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.BOOKMARK_BORDER, size=52, color=ThemeColors.TEXT_FAINT_LIGHT),
                        ft.Text("No matching saved itineraries.", size=16, weight=ft.FontWeight.BOLD),
                        ft.Text("Plan your journey with the AI Suggested Wizard or Custom Builder.", size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                        ft.Container(height=8),
                        ft.Row(
                            controls=[
                                ft.FilledButton(
                                    content="AI Wizard",
                                    icon=ft.Icons.AUTO_AWESOME,
                                    style=ft.ButtonStyle(bgcolor=ThemeColors.PRIMARY_BLUE, color=ft.Colors.WHITE),
                                    on_click=lambda _: self._navigate("/suggested"),
                                ),
                                ft.OutlinedButton(
                                    content="Custom Builder",
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
            cards = [self._create_trip_card(it) for it in filtered_trips]
            content_section = ft.ResponsiveRow(
                controls=[ft.Container(content=c, col={"sm": 12, "md": 6, "lg": 4}) for c in cards],
                spacing=16,
                run_spacing=16,
            )

        self.content = ft.Column(
            controls=[
                header_row,
                ft.Container(height=14),
                self.search_field,
                ft.Container(height=8),
                segments_row,
                ft.Divider(color=ThemeColors.BORDER_LIGHT, height=1),
                ft.Container(height=8),
                headline_block,
                ft.Container(height=12),
                content_section,
                ft.Container(height=24),
            ],
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def _create_segment_pill(self, key: str, label: str, is_active: bool) -> ft.Control:
        bg = ThemeColors.PRIMARY_BLUE if is_active else ThemeColors.SURFACE_LIGHT
        color = ft.Colors.WHITE if is_active else ThemeColors.TEXT_MAIN_LIGHT
        border_color = ThemeColors.PRIMARY_BLUE if is_active else ThemeColors.BORDER_LIGHT

        return ft.Container(
            content=ft.Text(label, size=12, weight=ft.FontWeight.W_700 if is_active else ft.FontWeight.W_500, color=color),
            bgcolor=bg,
            border=ft.Border.all(1.2, border_color),
            border_radius=20,
            padding=ft.Padding.symmetric(horizontal=14, vertical=8),
            ink=True,
            on_click=lambda _: self._on_segment_select(key),
        )

    def _create_trip_card(self, itin: Itinerary) -> ft.Control:
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

        delete_btn = ft.IconButton(
            icon=ft.Icons.DELETE_OUTLINE,
            icon_size=18,
            icon_color=ThemeColors.ERROR,
            tooltip="Delete Itinerary",
            on_click=lambda _: self._delete_trip(itin),
        )

        top_row = ft.Row(
            controls=[
                badge,
                ft.Row(controls=[budget, delete_btn], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        title = ft.Text(
            itin.title,
            size=15,
            weight=ft.FontWeight.BOLD,
            color=ThemeColors.TEXT_BLACK,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
        )

        dest = ft.Row(
            controls=[
                ft.Icon(ft.Icons.LOCATION_ON, size=14, color=ThemeColors.PRIMARY_BLUE),
                ft.Text(itin.destination or "Nueva Ecija", size=12, color=ThemeColors.PRIMARY_BLUE, weight=ft.FontWeight.W_600),
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

        # Metrics chip row
        metrics_row = ft.Row(
            controls=[
                ft.Container(
                    content=ft.Text(f"{itin.total_days} Days", size=10, weight=ft.FontWeight.W_600, color=ThemeColors.TEXT_MUTED_LIGHT),
                    bgcolor=ThemeColors.BG_LIGHT,
                    border_radius=4,
                    padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                ),
                ft.Container(
                    content=ft.Text(f"{itin.total_stops} Stops", size=10, weight=ft.FontWeight.W_600, color=ThemeColors.TEXT_MUTED_LIGHT),
                    bgcolor=ThemeColors.BG_LIGHT,
                    border_radius=4,
                    padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                ),
            ],
            spacing=6,
        )

        # Action Buttons
        actions_row = ft.Row(
            controls=[
                ft.TextButton(
                    content="Export (.ics / .md)",
                    icon=ft.Icons.FILE_DOWNLOAD_OUTLINED,
                    style=ft.ButtonStyle(color=ThemeColors.TEXT_MUTED_LIGHT),
                    on_click=lambda _: show_export_dialog(self.page, itin),
                ),
                ft.FilledButton(
                    content="View Details →",
                    style=ft.ButtonStyle(
                        bgcolor=ThemeColors.PRIMARY_BLUE,
                        color=ft.Colors.WHITE,
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                    on_click=lambda _: self._open_trip(itin),
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    top_row,
                    title,
                    dest,
                    dates,
                    metrics_row,
                    ft.Divider(color=ThemeColors.BORDER_LIGHT, height=1),
                    actions_row,
                ],
                spacing=8,
            ),
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border=ft.Border.all(1.2, ThemeColors.BORDER_LIGHT),
            border_radius=16,
            padding=14,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=8,
                color=ft.Colors.with_opacity(0.04, "#000000"),
            ),
        )

    def _get_filtered_trips(self) -> list[Itinerary]:
        results = self.itineraries
        today = date.today().strftime("%Y-%m-%d")

        # Apply Segment filter
        if self.active_segment == "suggested":
            results = [it for it in results if it.type == "suggested"]
        elif self.active_segment == "custom":
            results = [it for it in results if it.type != "suggested"]
        elif self.active_segment == "upcoming":
            results = [it for it in results if (it.end_date or "") >= today]
        elif self.active_segment == "past":
            results = [it for it in results if (it.end_date or "") < today]

        # Apply Search filter
        if self.search_term.strip():
            query = self.search_term.strip().lower()
            results = [
                it for it in results
                if query in (it.title or "").lower() or query in (it.destination or "").lower()
            ]

        return results

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

    def _delete_trip(self, itin: Itinerary) -> None:
        def confirm():
            async def _worker():
                await self.itinerary_service.delete_itinerary(itin.id)
                await self._load_trips_async()
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(_worker())
            except RuntimeError:
                asyncio.run(_worker())

        show_confirm_dialog(
            self.page,
            title="Delete Itinerary?",
            message=f"Are you sure you want to delete '{itin.title}'? This cannot be undone.",
            on_confirm=confirm,
        )

    def _load_trips(self) -> None:
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._load_trips_async())
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
