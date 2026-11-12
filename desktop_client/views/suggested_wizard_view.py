"""AI Suggested Itinerary Wizard View."""

import asyncio
from datetime import date, datetime, timedelta
from typing import Callable, Optional
import flet as ft

from desktop_client.components.dialogs import (
    show_export_dialog,
    show_place_detail_dialog,
)
from desktop_client.components.stop_card import StopCard
from desktop_client.config.settings import (
    BUDGET_PRESETS,
    CANONICAL_CATEGORIES,
    PACING_OPTIONS,
    ThemeColors,
)
from desktop_client.core.api_client import ApiClientError
from desktop_client.models.itinerary import (
    Itinerary,
    ItineraryDay,
    SuggestedItineraryRequest,
)
from desktop_client.services.itinerary_service import get_itinerary_service


class SuggestedWizardView(ft.Container):
    """Step-by-step wizard generating automated, geographically clustered itineraries."""

    def __init__(self, on_navigate: Optional[Callable[[str], None]] = None):
        super().__init__()
        self.on_navigate = on_navigate
        self.itinerary_service = get_itinerary_service()

        self.expand = True
        self.padding = ft.Padding.all(24)
        self.bgcolor = ThemeColors.BG_LIGHT

        # Wizard State
        today = date.today()
        self.title_val = "Suggested Nueva Ecija Itinerary"
        self.destination_val = "Nueva Ecija"
        self.start_date_val = (today + timedelta(days=7)).strftime("%Y-%m-%d")
        self.end_date_val = (today + timedelta(days=9)).strftime("%Y-%m-%d")
        self.budget_val = 2500.0
        self.pacing_val = "moderate"
        self.selected_categories: set[str] = {
            "nature_park",
            "tourist_attraction",
            "restaurant",
            "museum_cultural",
        }

        # Execution & Result State
        self.is_generating = False
        self.error_message: Optional[str] = None
        self.generated_itinerary: Optional[Itinerary] = None
        self.active_day_index = 0

        self._build_content()

    def _build_content(self) -> None:
        if self.is_generating:
            self.content = self._build_generating_view()
        elif self.generated_itinerary:
            self.content = self._build_result_view()
        else:
            self.content = self._build_wizard_form()

    def _build_wizard_form(self) -> ft.Control:
        # Title and Destination Row
        title_field = ft.TextField(
            label="Trip Title",
            value=self.title_val,
            expand=True,
            on_change=lambda e: setattr(self, "title_val", e.control.value),
        )

        dest_field = ft.TextField(
            label="Destination",
            value=self.destination_val,
            read_only=True,
            width=220,
        )

        row_header = ft.Row(controls=[title_field, dest_field], spacing=16)

        # Dates & Duration
        start_field = ft.TextField(
            label="Start Date (YYYY-MM-DD)",
            value=self.start_date_val,
            width=200,
            on_change=lambda e: setattr(self, "start_date_val", e.control.value),
        )

        end_field = ft.TextField(
            label="End Date (YYYY-MM-DD)",
            value=self.end_date_val,
            width=200,
            on_change=lambda e: setattr(self, "end_date_val", e.control.value),
        )

        dates_row = ft.Row(
            controls=[
                start_field,
                end_field,
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.CALENDAR_MONTH, size=16, color=ThemeColors.TEXT_MUTED_LIGHT),
                            ft.Text("Multi-day trips automatically cluster nearby LGUs.", size=11, color=ThemeColors.TEXT_MUTED_LIGHT),
                        ],
                        spacing=6,
                    ),
                    padding=ft.Padding.only(left=8),
                ),
            ],
            spacing=16,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Budget Presets Cards
        budget_cards: list[ft.Control] = []
        for b in BUDGET_PRESETS:
            is_sel = abs(self.budget_val - b["amount"]) < 1.0
            border_col = ThemeColors.PRIMARY_BLUE if is_sel else ThemeColors.BORDER_LIGHT
            bg_col = ThemeColors.PRIMARY_LIGHT if is_sel else ThemeColors.SURFACE_LIGHT

            budget_cards.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text(b["label"].split(" (")[0], size=13, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_MAIN_LIGHT),
                            ft.Text(f"₱{b['amount']:,.0f} / day", size=12, weight=ft.FontWeight.W_700, color=ThemeColors.BUDGET_GREEN),
                        ],
                        spacing=2,
                    ),
                    bgcolor=bg_col,
                    border=ft.Border.all(2 if is_sel else 1, border_col),
                    border_radius=12,
                    padding=14,
                    expand=True,
                    ink=True,
                    on_click=lambda _, amt=b["amount"]: self._set_budget(amt),
                )
            )

        budget_row = ft.Row(controls=budget_cards, spacing=12)

        # Pacing Options
        pacing_cards: list[ft.Control] = []
        for p in PACING_OPTIONS:
            is_sel = self.pacing_val == p["key"]
            border_col = ThemeColors.AZURE_PRIMARY if is_sel else ThemeColors.BORDER_LIGHT
            bg_col = ThemeColors.AZURE_SOFT if is_sel else ThemeColors.SURFACE_LIGHT

            pacing_cards.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text(p["label"], size=13, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_MAIN_LIGHT),
                            ft.Text(p["desc"], size=11, color=ThemeColors.TEXT_MUTED_LIGHT),
                        ],
                        spacing=2,
                    ),
                    bgcolor=bg_col,
                    border=ft.Border.all(2 if is_sel else 1, border_col),
                    border_radius=10,
                    padding=14,
                    expand=True,
                    ink=True,
                    on_click=lambda _, key=p["key"]: self._set_pacing(key),
                )
            )

        pacing_row = ft.Row(controls=pacing_cards, spacing=12)

        # Category Preferences Chips (Multi-Select)
        category_chips: list[ft.Control] = []
        for cat in CANONICAL_CATEGORIES:
            is_active = cat["key"] in self.selected_categories
            bg = ThemeColors.EMERALD_PRIMARY if is_active else ThemeColors.SURFACE_LIGHT
            text_col = ft.Colors.WHITE if is_active else ThemeColors.TEXT_MAIN_LIGHT
            border_col = ThemeColors.EMERALD_PRIMARY if is_active else ThemeColors.BORDER_LIGHT

            category_chips.append(
                ft.Container(
                    content=ft.Text(cat["label"], size=11, weight=ft.FontWeight.W_600 if is_active else ft.FontWeight.NORMAL, color=text_col),
                    bgcolor=bg,
                    border=ft.Border.all(1, border_col),
                    border_radius=16,
                    padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                    ink=True,
                    on_click=lambda _, k=cat["key"]: self._toggle_category(k),
                )
            )

        categories_wrap = ft.Row(
            controls=category_chips,
            wrap=True,
            spacing=8,
            run_spacing=8,
        )

        # Error display
        error_container = ft.Container()
        if self.error_message:
            error_container = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.ERROR_OUTLINE, color=ThemeColors.ERROR, size=18),
                        ft.Text(self.error_message, color=ThemeColors.ERROR, size=12),
                    ],
                    spacing=8,
                ),
                bgcolor=ThemeColors.ERROR_BG,
                border_radius=8,
                padding=10,
            )

        # Generate Action Button matching .figma-solid-blue-btn
        submit_btn = ft.FilledButton(
            content="Generate Clustered Itinerary",
            icon=ft.Icons.AUTO_AWESOME,
            style=ft.ButtonStyle(
                bgcolor=ThemeColors.PRIMARY_BLUE,
                color=ft.Colors.WHITE,
                padding=ft.Padding.symmetric(horizontal=32, vertical=16),
                shape=ft.RoundedRectangleBorder(radius=12),
            ),
            on_click=lambda _: self._start_generation(),
        )

        form_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Step 1: Trip Name & Destination", size=14, weight=ft.FontWeight.BOLD),
                    row_header,
                    ft.Container(height=8),
                    ft.Text("Step 2: Travel Dates", size=14, weight=ft.FontWeight.BOLD),
                    dates_row,
                    ft.Container(height=8),
                    ft.Text("Step 3: Daily Budget Preset", size=14, weight=ft.FontWeight.BOLD),
                    budget_row,
                    ft.Container(height=8),
                    ft.Text("Step 4: Pacing & Intensity", size=14, weight=ft.FontWeight.BOLD),
                    pacing_row,
                    ft.Container(height=8),
                    ft.Text("Step 5: Traveler Preferences & Interests", size=14, weight=ft.FontWeight.BOLD),
                    categories_wrap,
                    ft.Container(height=16),
                    error_container,
                    ft.Row(controls=[submit_btn], alignment=ft.MainAxisAlignment.CENTER),
                ],
                spacing=12,
            ),
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border_radius=16,
            border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
            padding=28,
            width=900,
        )

        return ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Text("AI Suggested Itinerary Wizard", size=22, weight=ft.FontWeight.BOLD),
                                ft.Text("Our clustering algorithm pairs nearby destinations across Nueva Ecija to save travel time.", size=13, color=ThemeColors.TEXT_MUTED_LIGHT),
                            ],
                            spacing=2,
                        ),
                    ],
                ),
                ft.Container(height=16),
                ft.Row(controls=[form_card], alignment=ft.MainAxisAlignment.CENTER),
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=0,
        )

    def _build_generating_view(self) -> ft.Control:
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.ProgressRing(width=60, height=60, stroke_width=4, color=ThemeColors.PRIMARY_BLUE),
                    ft.Container(height=16),
                    ft.Text("Generating Clustered Itinerary...", size=20, weight=ft.FontWeight.BOLD),
                    ft.Text("Analyzing 2,670+ registered destinations in Nueva Ecija", size=13, color=ThemeColors.TEXT_MUTED_LIGHT),
                    ft.Container(height=8),
                    ft.Container(
                        content=ft.Text(
                            "💡 Travel Tip: Our algorithm groups venues in the same municipality "
                            "(e.g., Pantabangan lakeside resorts vs. Cabanatuan food spots) to minimize road time.",
                            size=12,
                            italic=True,
                            color=ThemeColors.PRIMARY_BLUE,
                        ),
                        bgcolor=ThemeColors.PRIMARY_LIGHT,
                        border_radius=8,
                        padding=12,
                        width=500,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            expand=True,
            alignment=ft.Alignment(0, 0),
        )

    def _build_result_view(self) -> ft.Control:
        itin = self.generated_itinerary
        if not itin:
            return ft.Container()

        # Overview banner matching Suggested Card gradient
        overview_card = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Container(
                                content=ft.Text("Suggested Plan", size=10, weight=ft.FontWeight.BOLD, color=ThemeColors.SUGGESTED_BADGE_TEXT),
                                bgcolor=ThemeColors.SUGGESTED_BADGE_BG,
                                border_radius=6,
                                padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                            ),
                            ft.Text(itin.title, size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                            ft.Text(f"{itin.date_range_display} • {len(itin.days)} Days • {itin.total_stops} Total Stops", size=12, color=ThemeColors.PRIMARY_LIGHT),
                            ft.Text(f"Estimated Trip Cost: ₱{itin.total_estimated_cost:,.2f} (~₱{itin.daily_budget:,.2f} / day budget)", size=12, color=ThemeColors.CUSTOM_CARD_BORDER),
                        ],
                        spacing=4,
                        expand=True,
                    ),
                    ft.Row(
                        controls=[
                            ft.FilledButton(
                                content="Export Trip",
                                icon=ft.Icons.SHARE,
                                style=ft.ButtonStyle(
                                    bgcolor=ThemeColors.PRIMARY_BLUE,
                                    color=ft.Colors.WHITE,
                                    shape=ft.RoundedRectangleBorder(radius=10),
                                ),
                                on_click=lambda _: self._open_export_dialog(),
                            ),
                            ft.OutlinedButton(
                                content="Plan Another",
                                icon=ft.Icons.REFRESH,
                                style=ft.ButtonStyle(color=ft.Colors.WHITE),
                                on_click=lambda _: self._reset_wizard(),
                            ),
                        ],
                        spacing=8,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            gradient=ft.LinearGradient(
                begin=ft.Alignment(0, -1),
                end=ft.Alignment(0, 1),
                colors=[ThemeColors.NAVY_GRADIENT_START, ThemeColors.NAVY_GRADIENT_END],
            ),
            border_radius=16,
            padding=20,
            margin=ft.Margin.only(bottom=16),
        )

        # Day Switcher Tabs
        day_buttons: list[ft.Control] = []
        for idx, day in enumerate(itin.days):
            is_active = idx == self.active_day_index
            bg = ThemeColors.PRIMARY_BLUE if is_active else ThemeColors.SURFACE_LIGHT
            text_col = ft.Colors.WHITE if is_active else ThemeColors.TEXT_MAIN_LIGHT
            day_buttons.append(
                ft.Container(
                    content=ft.Text(
                        f"Day {day.day_number} ({len(day.items)} stops)",
                        size=12,
                        weight=ft.FontWeight.W_700 if is_active else ft.FontWeight.NORMAL,
                        color=text_col,
                    ),
                    bgcolor=bg,
                    border=ft.Border.all(1, ThemeColors.PRIMARY_BLUE if is_active else ThemeColors.BORDER_LIGHT),
                    border_radius=10,
                    padding=ft.Padding.symmetric(horizontal=14, vertical=8),
                    ink=True,
                    on_click=lambda _, day_idx=idx: self._select_day(day_idx),
                )
            )

        day_bar = ft.Row(controls=day_buttons, spacing=8)

        # Active Day Timeline
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
                    content=ft.Text("No stops scheduled for this day.", size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                    padding=20,
                )
            )

        active_day_header = ft.Row(
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

        return ft.Column(
            controls=[
                overview_card,
                day_bar,
                ft.Container(height=12),
                active_day_header,
                ft.Container(height=8),
                ft.Column(controls=timeline_items, spacing=8),
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=0,
        )

    def _set_budget(self, amount: float) -> None:
        self.budget_val = amount
        self._build_content()
        self.update()

    def _set_pacing(self, key: str) -> None:
        self.pacing_val = key
        self._build_content()
        self.update()

    def _toggle_category(self, key: str) -> None:
        if key in self.selected_categories:
            if len(self.selected_categories) > 1:
                self.selected_categories.remove(key)
        else:
            self.selected_categories.add(key)
        self._build_content()
        self.update()

    def _select_day(self, day_idx: int) -> None:
        self.active_day_index = day_idx
        self._build_content()
        self.update()

    def _reset_wizard(self) -> None:
        self.generated_itinerary = None
        self.is_generating = False
        self.error_message = None
        self._build_content()
        self.update()

    def _open_export_dialog(self) -> None:
        if self.page and self.generated_itinerary:
            show_export_dialog(self.page, self.generated_itinerary)

    def _start_generation(self) -> None:
        self.error_message = None
        
        # Date validation
        try:
            start_d = datetime.strptime(self.start_date_val, "%Y-%m-%d").date()
            end_d = datetime.strptime(self.end_date_val, "%Y-%m-%d").date()
            if end_d < start_d:
                self.error_message = "End date cannot be earlier than start date."
                self._build_content()
                self.update()
                return
        except ValueError:
            self.error_message = "Please enter valid dates in YYYY-MM-DD format."
            self._build_content()
            self.update()
            return

        self.is_generating = True
        self._build_content()
        self.update()

        async def _do_gen():
            try:
                req = SuggestedItineraryRequest(
                    title=self.title_val,
                    destination=self.destination_val,
                    start_date=self.start_date_val,
                    end_date=self.end_date_val,
                    daily_budget=self.budget_val,
                    preferences=list(self.selected_categories),
                    pacing=self.pacing_val,
                    travel_mode="DRIVE",
                    save_immediately=True,
                )
                itin = await self.itinerary_service.generate_suggested_itinerary(req)
                self.generated_itinerary = itin
                self.active_day_index = 0
            except ApiClientError as err:
                self.error_message = f"Generation failed: {err.message}"
            except Exception as err:
                self.error_message = f"An unexpected error occurred: {str(err)}"
            finally:
                self.is_generating = False
                self._build_content()
                try:
                    self.update()
                except Exception:
                    pass

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_do_gen())
        except RuntimeError:
            asyncio.run(_do_gen())
