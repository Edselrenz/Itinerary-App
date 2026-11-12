"""Itinerary Detail and Inspection View."""

from typing import Callable, Optional
import flet as ft

from desktop_client.components.dialogs import show_export_dialog
from desktop_client.components.stop_card import StopCard
from desktop_client.config.settings import ThemeColors
from desktop_client.models.itinerary import Itinerary


class TripDetailView(ft.Container):
    """Timeline inspector displaying day schedules, honest pricing, and export actions."""

    def __init__(
        self,
        itinerary: Itinerary,
        on_back: Optional[Callable[[], None]] = None,
    ):
        super().__init__()
        self.itinerary = itinerary
        self.on_back = on_back
        self.active_day_index = 0

        self.expand = True
        self.padding = ft.padding.all(24)
        self.bgcolor = ThemeColors.BG_LIGHT

        self._build_content()

    def _build_content(self) -> None:
        itin = self.itinerary

        # Top navigation / Back bar
        back_btn = ft.TextButton(
            content="← Back to Saved Trips",
            icon=ft.Icons.ARROW_BACK,
            on_click=lambda _: self.on_back() if self.on_back else None,
        )

        export_btn = ft.FilledButton(
            content="Export Itinerary",
            icon=ft.Icons.DOWNLOAD,
            style=ft.ButtonStyle(bgcolor=ThemeColors.AZURE_PRIMARY, color=ft.Colors.WHITE),
            on_click=lambda _: self._open_export(),
        )

        top_nav = ft.Row(
            controls=[back_btn, export_btn],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        # Overview Card
        source_badge = "Local Guest Storage" if itin.is_guest else "Cloud Account"
        badge_bg = ThemeColors.AMBER_LIGHT if itin.is_guest else ThemeColors.SUCCESS_BG
        badge_col = ThemeColors.WARM_GOLD if itin.is_guest else ThemeColors.SUCCESS

        overview_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(itin.title, size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                            ft.Container(
                                content=ft.Text(source_badge, size=10, weight=ft.FontWeight.W_600, color=badge_col),
                                bgcolor=badge_bg,
                                border_radius=6,
                                padding=ft.padding.symmetric(horizontal=8, vertical=2),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Text(
                        f"Destination: {itin.destination} • {itin.date_range_display} • {len(itin.days)} Days • {itin.total_stops} Total Stops",
                        size=13,
                        color=ThemeColors.EMERALD_MINT,
                    ),
                    ft.Text(
                        f"Total Estimated Cost: ₱{itin.total_estimated_cost:,.2f} (~₱{itin.daily_budget:,.2f} / day target budget)",
                        size=12,
                        weight=ft.FontWeight.W_600,
                        color=ThemeColors.AMBER_LIGHT,
                    ),
                ],
                spacing=4,
            ),
            bgcolor=ThemeColors.EMERALD_DARK,
            border_radius=14,
            padding=20,
            margin=ft.margin.only(bottom=16),
        )

        # Day Switcher Tabs
        day_buttons: list[ft.Control] = []
        for idx, day in enumerate(itin.days):
            is_active = idx == self.active_day_index
            day_buttons.append(
                ft.Container(
                    content=ft.Text(
                        f"Day {day.day_number} ({len(day.items)} stops)",
                        size=12,
                        weight=ft.FontWeight.W_600 if is_active else ft.FontWeight.NORMAL,
                        color=ft.Colors.WHITE if is_active else ThemeColors.TEXT_MAIN_LIGHT,
                    ),
                    bgcolor=ThemeColors.EMERALD_PRIMARY if is_active else ThemeColors.SURFACE_LIGHT,
                    border=ft.Border.all(1, ThemeColors.EMERALD_PRIMARY if is_active else ThemeColors.BORDER_LIGHT),
                    border_radius=8,
                    padding=ft.padding.symmetric(horizontal=14, vertical=8),
                    ink=True,
                    on_click=lambda _, day_idx=idx: self._select_day(day_idx),
                )
            )

        day_tabs_row = ft.Row(
            controls=day_buttons,
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
        )

        # Active Day Timeline Stops
        active_day = itin.days[self.active_day_index] if itin.days else None
        timeline_items: list[ft.Control] = []

        if active_day and active_day.items:
            for item in active_day.items:
                timeline_items.append(
                    StopCard(
                        item=item,
                        editable=False,
                    )
                )
        else:
            timeline_items.append(
                ft.Container(
                    content=ft.Text("No stops recorded for this day.", size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                    padding=30,
                )
            )

        day_header = ft.Row(
            controls=[
                ft.Text(
                    f"{active_day.display_title if active_day else 'Day'} — {active_day.travel_date if active_day else ''}",
                    size=16,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    f"Day Estimated Cost: ~₱{active_day.total_day_cost:,.2f}" if active_day else "",
                    size=12,
                    weight=ft.FontWeight.W_600,
                    color=ThemeColors.EMERALD_PRIMARY,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        self.content = ft.Column(
            controls=[
                top_nav,
                ft.Container(height=8),
                overview_card,
                day_tabs_row,
                ft.Container(height=12),
                day_header,
                ft.Container(height=8),
                ft.Column(controls=timeline_items, spacing=6),
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=0,
        )

    def _select_day(self, day_idx: int) -> None:
        self.active_day_index = day_idx
        self._build_content()
        self.update()

    def _open_export(self) -> None:
        if self.page:
            show_export_dialog(self.page, self.itinerary)
