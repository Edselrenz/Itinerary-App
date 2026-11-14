"""AI Suggested Itinerary Wizard View conforming to Figma & Web client design."""

import asyncio
from datetime import date, datetime, timedelta
from typing import Callable, Optional
import uuid
import flet as ft

from desktop_client.components.date_range_dialog import show_date_range_dialog
from desktop_client.components.destination_picker import DestinationPicker
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
from desktop_client.core.commute_guide import get_leg_commute_info
from desktop_client.models.itinerary import (
    Itinerary,
    ItineraryDay,
    ItineraryItem,
    SuggestedItineraryRequest,
)
from desktop_client.models.place import Place
from desktop_client.services.itinerary_service import get_itinerary_service
from desktop_client.services.place_service import get_place_service


class SuggestedWizardView(ft.Container):
    """Step-by-step wizard generating automated, geographically clustered itineraries:

    - 3-view state machine ('form', 'itinerary', 'nearby').
    - Destination picker with quick chips and 32-LGU explorer.
    - Figma date range picker with live duration summary.
    - Travel mode and pacing parameters.
    - Inter-stop leg commute badges with distance, travel time, and transit fare.
    - Nearby amenities discovery and one-click injection.
    """

    def __init__(self, on_navigate: Optional[Callable[..., None]] = None):
        super().__init__()
        self.on_navigate = on_navigate
        self.itinerary_service = get_itinerary_service()
        self.place_service = get_place_service()

        self.expand = True
        self.padding = ft.Padding.all(24)
        self.bgcolor = ThemeColors.BG_LIGHT

        # State Machine: 'form', 'itinerary', 'nearby'
        self.view_mode = "form"

        # Wizard Form State
        today = date.today()
        self.title_val = "Suggested Nueva Ecija Itinerary"
        self.destination_val = "Nueva Ecija"
        self.start_date_val = (today + timedelta(days=7)).strftime("%Y-%m-%d")
        self.end_date_val = (today + timedelta(days=9)).strftime("%Y-%m-%d")
        self.budget_val = 2500.0
        self.pacing_val = "moderate"
        self.travel_mode_val = "drive"  # 'drive', 'motorcycle', 'transit'
        self.min_rating_val = 0.0
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
        self.save_feedback: Optional[str] = None

        # Nearby Amenities State
        self.nearby_category = "restaurant"
        self.nearby_amenities: list[Place] = []
        self.nearby_loading = False

        self._build_content()

    def _build_content(self) -> None:
        if self.is_generating:
            self.content = self._build_generating_view()
        elif self.view_mode == "nearby":
            self.content = self._build_nearby_view()
        elif self.generated_itinerary and self.view_mode == "itinerary":
            self.content = self._build_result_view()
        else:
            self.content = self._build_wizard_form()

    def _build_wizard_form(self) -> ft.Control:
        # Trip Title
        title_field = ft.TextField(
            label="Trip Title",
            value=self.title_val,
            border_radius=10,
            expand=True,
            dense=True,
            on_change=lambda e: setattr(self, "title_val", e.control.value),
        )

        # Destination Picker Component
        dest_picker = DestinationPicker(
            value=self.destination_val,
            on_change=lambda val: setattr(self, "destination_val", val),
        )

        # Dates Selector Card
        def open_dates(_):
            if self.page:
                show_date_range_dialog(
                    self.page,
                    self.start_date_val,
                    self.end_date_val,
                    lambda s, e: self._on_dates_picked(s, e),
                )

        try:
            s_d = datetime.strptime(self.start_date_val, "%Y-%m-%d").date()
            e_d = datetime.strptime(self.end_date_val, "%Y-%m-%d").date()
            num_days = (e_d - s_d).days + 1
            num_nights = (e_d - s_d).days
            duration_label = f"{num_days} Days ({num_nights} Nights) • {self.start_date_val} → {self.end_date_val}"
        except Exception:
            duration_label = f"{self.start_date_val} → {self.end_date_val}"

        dates_button = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.CALENDAR_MONTH, color=ThemeColors.PRIMARY_BLUE, size=20),
                    ft.Column(
                        controls=[
                            ft.Text("Travel Dates & Duration", size=11, color=ThemeColors.TEXT_MUTED_LIGHT),
                            ft.Text(duration_label, size=13, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_BLACK),
                        ],
                        spacing=1,
                        expand=True,
                    ),
                    ft.Text("Change Dates", size=12, weight=ft.FontWeight.BOLD, color=ThemeColors.PRIMARY_BLUE),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border=ft.Border.all(1.2, ThemeColors.BORDER_LIGHT),
            border_radius=12,
            padding=ft.Padding.symmetric(horizontal=16, vertical=12),
            ink=True,
            on_click=open_dates,
        )

        # Travel Mode Selector (Drive, Motorcycle, Transit)
        modes = [
            ("drive", "Drive / Private Car", ft.Icons.DIRECTIONS_CAR),
            ("motorcycle", "Motorcycle / Tricycle", ft.Icons.TWO_WHEELER),
            ("transit", "Commute / Bus / Jeep", ft.Icons.DIRECTIONS_BUS),
        ]
        mode_cards = []
        for m_key, m_label, m_icon in modes:
            is_sel = self.travel_mode_val == m_key
            card = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(m_icon, size=16, color=ThemeColors.PRIMARY_BLUE if is_sel else ThemeColors.TEXT_MUTED_LIGHT),
                        ft.Text(
                            m_label,
                            size=12,
                            weight=ft.FontWeight.BOLD if is_sel else ft.FontWeight.NORMAL,
                            color=ThemeColors.PRIMARY_BLUE if is_sel else ThemeColors.TEXT_MAIN_LIGHT,
                        ),
                    ],
                    spacing=6,
                ),
                bgcolor=ThemeColors.AZURE_SOFT if is_sel else ThemeColors.SURFACE_LIGHT,
                border=ft.Border.all(1.5 if is_sel else 1.0, ThemeColors.PRIMARY_BLUE if is_sel else ThemeColors.BORDER_LIGHT),
                border_radius=10,
                padding=ft.Padding.symmetric(horizontal=12, vertical=10),
                expand=True,
                ink=True,
                on_click=lambda _, mk=m_key: self._set_travel_mode(mk),
            )
            mode_cards.append(card)

        travel_mode_row = ft.Row(controls=mode_cards, spacing=10)

        # Budget Presets Cards
        budget_cards: list[ft.Control] = []
        for b in BUDGET_PRESETS:
            is_sel = abs(self.budget_val - b["amount"]) < 1.0
            border_col = ThemeColors.PRIMARY_BLUE if is_sel else ThemeColors.BORDER_LIGHT
            bg_col = ThemeColors.AZURE_SOFT if is_sel else ThemeColors.SURFACE_LIGHT

            budget_cards.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text(b["label"].split(" (")[0], size=13, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_MAIN_LIGHT),
                            ft.Text(f"₱{b['amount']:,.0f} / day", size=12, weight=ft.FontWeight.W_700, color=ThemeColors.EMERALD_PRIMARY),
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
            border_col = ThemeColors.PRIMARY_BLUE if is_sel else ThemeColors.BORDER_LIGHT
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
            bg = ThemeColors.PRIMARY_BLUE if is_active else ThemeColors.SURFACE_LIGHT
            text_col = ft.Colors.WHITE if is_active else ThemeColors.TEXT_MAIN_LIGHT
            border_col = ThemeColors.PRIMARY_BLUE if is_active else ThemeColors.BORDER_LIGHT

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

        submit_btn = ft.FilledButton(
            content="Generate Clustered Itinerary",
            icon=ft.Icons.AUTO_AWESOME,
            style=ft.ButtonStyle(
                bgcolor=ThemeColors.PRIMARY_BLUE,
                color=ft.Colors.WHITE,
                padding=ft.Padding.symmetric(horizontal=36, vertical=16),
                shape=ft.RoundedRectangleBorder(radius=12),
            ),
            on_click=lambda _: self._start_generation(),
        )

        form_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Step 1: Trip Name & Destination", size=14, weight=ft.FontWeight.BOLD),
                    title_field,
                    dest_picker,
                    ft.Container(height=6),
                    ft.Text("Step 2: Travel Dates & Duration", size=14, weight=ft.FontWeight.BOLD),
                    dates_button,
                    ft.Container(height=6),
                    ft.Text("Step 3: Travel Mode", size=14, weight=ft.FontWeight.BOLD),
                    travel_mode_row,
                    ft.Container(height=6),
                    ft.Text("Step 4: Daily Budget Target", size=14, weight=ft.FontWeight.BOLD),
                    budget_row,
                    ft.Container(height=6),
                    ft.Text("Step 5: Pacing & Intensity", size=14, weight=ft.FontWeight.BOLD),
                    pacing_row,
                    ft.Container(height=6),
                    ft.Text("Step 6: Traveler Preferences & Interests", size=14, weight=ft.FontWeight.BOLD),
                    categories_wrap,
                    ft.Container(height=14),
                    error_container,
                    ft.Row(controls=[submit_btn], alignment=ft.MainAxisAlignment.CENTER),
                ],
                spacing=10,
            ),
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border_radius=16,
            border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
            padding=26,
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
                    ft.Text(f"Clustering stops around {self.destination_val} across Nueva Ecija", size=13, color=ThemeColors.TEXT_MUTED_LIGHT),
                    ft.Container(height=8),
                    ft.Container(
                        content=ft.Text(
                            "💡 Travel Tip: Our algorithm groups venues within close geographic proximity "
                            "to minimize transit time and tricycle/fuel expenses.",
                            size=12,
                            italic=True,
                            color=ThemeColors.PRIMARY_BLUE,
                        ),
                        bgcolor=ThemeColors.AZURE_SOFT,
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

        # Overview banner with Dark Navy Gradient
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
                            ft.Text(f"Estimated Trip Cost: ₱{itin.total_estimated_cost:,.2f} (~₱{itin.daily_budget:,.2f} / day target)", size=12, color=ThemeColors.CUSTOM_CARD_BORDER),
                        ],
                        spacing=4,
                        expand=True,
                    ),
                    ft.Row(
                        controls=[
                            ft.FilledButton(
                                content="💾 Save Trip",
                                style=ft.ButtonStyle(
                                    bgcolor=ThemeColors.PRIMARY_BLUE,
                                    color=ft.Colors.WHITE,
                                    shape=ft.RoundedRectangleBorder(radius=10),
                                ),
                                on_click=lambda _: self._save_generated_itinerary(),
                            ),
                            ft.OutlinedButton(
                                content="✏️ Edit in Builder",
                                style=ft.ButtonStyle(color=ft.Colors.WHITE),
                                on_click=lambda _: self._customize_in_builder(),
                            ),
                            ft.OutlinedButton(
                                content="📍 Nearby Amenities",
                                style=ft.ButtonStyle(color=ft.Colors.WHITE),
                                on_click=lambda _: self._open_nearby_view(),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.SHARE,
                                icon_color=ft.Colors.WHITE,
                                tooltip="Export dossier",
                                on_click=lambda _: self._open_export_dialog(),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.REFRESH,
                                icon_color=ft.Colors.WHITE,
                                tooltip="Plan another trip",
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
            margin=ft.Margin.only(bottom=12),
        )

        # Assumptions Info Box
        assumptions_box = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.LIGHTBULB_OUTLINE, size=16, color=ThemeColors.PRIMARY_BLUE),
                    ft.Text(
                        f"Assumptions: Pacing: {self.pacing_val.title()} • Travel Mode: {self.travel_mode_val.title()} • "
                        "Lunch scheduled between 12:00 PM – 1:00 PM • Nearby stops clustered within same municipal corridors.",
                        size=11,
                        color=ThemeColors.TEXT_MUTED_LIGHT,
                    ),
                ],
                spacing=8,
            ),
            bgcolor=ThemeColors.AZURE_SOFT,
            border_radius=8,
            padding=10,
            margin=ft.Margin.only(bottom=12),
        )

        # Save Feedback Banner
        feedback_banner = ft.Container()
        if self.save_feedback:
            feedback_banner = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.CHECK_CIRCLE, color=ThemeColors.EMERALD_PRIMARY, size=18),
                        ft.Text(self.save_feedback, color=ThemeColors.EMERALD_PRIMARY, size=12, weight=ft.FontWeight.BOLD),
                    ],
                    spacing=8,
                ),
                bgcolor=ThemeColors.SUCCESS_BG,
                border_radius=8,
                padding=10,
                margin=ft.Margin.only(bottom=10),
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

        # Active Day Timeline with Inter-Stop Leg Commute Badges
        active_day = itin.days[self.active_day_index] if itin.days else None
        timeline_items: list[ft.Control] = []

        if active_day and active_day.items:
            for idx, item in enumerate(active_day.items):
                # Inter-stop leg commute badge between consecutive stops
                if idx > 0:
                    prev_item = active_day.items[idx - 1]
                    leg_info = get_leg_commute_info(prev_item, item)
                    timeline_items.append(
                        ft.Container(
                            content=ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.DIRECTIONS_CAR, size=14, color=ThemeColors.PRIMARY_BLUE),
                                    ft.Text(leg_info.display_text, size=11, weight=ft.FontWeight.W_600, color=ThemeColors.PRIMARY_BLUE),
                                ],
                                spacing=6,
                            ),
                            bgcolor=ThemeColors.AZURE_SOFT,
                            border=ft.Border.all(0.8, ThemeColors.CUSTOM_CARD_BORDER),
                            border_radius=8,
                            padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                            margin=ft.Margin.only(left=28, top=2, bottom=2),
                        )
                    )

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
                feedback_banner,
                assumptions_box,
                day_bar,
                ft.Container(height=12),
                active_day_header,
                ft.Container(height=8),
                ft.Column(controls=timeline_items, spacing=6),
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=0,
        )

    def _build_nearby_view(self) -> ft.Control:
        """Nearby amenities discovery around active day stops."""
        active_day = self.generated_itinerary.days[self.active_day_index] if self.generated_itinerary else None
        day_num = active_day.day_number if active_day else 1

        top_bar = ft.Row(
            controls=[
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color=ThemeColors.TEXT_BLACK,
                    tooltip="Back to Itinerary",
                    on_click=lambda _: self._return_to_itinerary(),
                ),
                ft.Text(f"Nearby Amenities & Support (Day {day_num})", size=18, weight=ft.FontWeight.BOLD),
            ],
            spacing=8,
        )

        # Segmented Tabs (Restaurants, Pharmacies/Hospitals, Stores)
        tabs = [
            ("restaurant", "Restaurants & Dining", ft.Icons.RESTAURANT),
            ("hospital", "Hospitals & Pharmacies", ft.Icons.LOCAL_HOSPITAL),
            ("store", "Stores & Fuel", ft.Icons.LOCAL_GAS_STATION),
        ]

        tab_controls = []
        for t_key, t_label, t_icon in tabs:
            is_sel = self.nearby_category == t_key
            tab = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(t_icon, size=16, color=ft.Colors.WHITE if is_sel else ThemeColors.TEXT_MAIN_LIGHT),
                        ft.Text(t_label, size=12, weight=ft.FontWeight.BOLD if is_sel else ft.FontWeight.NORMAL, color=ft.Colors.WHITE if is_sel else ThemeColors.TEXT_MAIN_LIGHT),
                    ],
                    spacing=6,
                ),
                bgcolor=ThemeColors.PRIMARY_BLUE if is_sel else ThemeColors.SURFACE_LIGHT,
                border=ft.Border.all(1, ThemeColors.PRIMARY_BLUE if is_sel else ThemeColors.BORDER_LIGHT),
                border_radius=16,
                padding=ft.Padding.symmetric(horizontal=14, vertical=8),
                ink=True,
                on_click=lambda _, tk=t_key: self._set_nearby_category(tk),
            )
            tab_controls.append(tab)

        tabs_row = ft.Row(controls=tab_controls, spacing=8)

        # Nearby Place Cards
        cards_column = ft.Column(spacing=10)
        if self.nearby_loading:
            cards_column.controls = [
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.ProgressRing(width=20, height=20, stroke_width=2),
                            ft.Text("Locating nearby amenities...", size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                        ],
                        spacing=10,
                    ),
                    padding=20,
                )
            ]
        elif self.nearby_amenities:
            for p in self.nearby_amenities:
                cards_column.controls.append(
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Image(
                                    src=p.resolved_image_path,
                                    width=75,
                                    height=65,
                                    fit=ft.BoxFit.COVER,
                                    border_radius=8,
                                    error_content=ft.Icon(ft.Icons.STORE, size=24, color=ThemeColors.PRIMARY_BLUE),
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text(p.name, size=13, weight=ft.FontWeight.BOLD),
                                        ft.Text(f"{p.municipality_name or 'Nueva Ecija'} • {p.formatted_category}", size=11, color=ThemeColors.TEXT_MUTED_LIGHT),
                                        ft.Text(p.formatted_cost, size=11, weight=ft.FontWeight.BOLD, color=ThemeColors.EMERALD_PRIMARY),
                                    ],
                                    spacing=2,
                                    expand=True,
                                ),
                                ft.FilledButton(
                                    content=f"+ Add to Day {day_num}",
                                    style=ft.ButtonStyle(bgcolor=ThemeColors.PRIMARY_BLUE, color=ft.Colors.WHITE),
                                    on_click=lambda _, place=p: self._inject_nearby_to_day(place),
                                ),
                            ],
                            spacing=12,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        bgcolor=ThemeColors.SURFACE_LIGHT,
                        border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
                        border_radius=12,
                        padding=10,
                    )
                )
        else:
            cards_column.controls = [
                ft.Container(
                    content=ft.Text("No amenities found in this category.", size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                    padding=20,
                )
            ]

        return ft.Column(
            controls=[
                top_bar,
                ft.Container(height=8),
                tabs_row,
                ft.Container(height=12),
                cards_column,
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=0,
        )

    def _open_nearby_view(self) -> None:
        self.view_mode = "nearby"
        self._load_nearby_amenities()

    def _return_to_itinerary(self) -> None:
        self.view_mode = "itinerary"
        self._build_content()
        self._safe_update()

    def _set_nearby_category(self, cat: str) -> None:
        self.nearby_category = cat
        self._load_nearby_amenities()

    def _load_nearby_amenities(self) -> None:
        self.nearby_loading = True
        self._build_content()
        self._safe_update()

        async def _query():
            try:
                cat_arg = "restaurant" if self.nearby_category == "restaurant" else None
                res = await self.place_service.get_places(page=1, page_size=8, category=cat_arg)
                self.nearby_amenities = res.items
            except Exception:
                from desktop_client.views.dashboard_view import DashboardView
                fallback = DashboardView()._get_fallback_popular_places()
                self.nearby_amenities = fallback[:5]
            finally:
                self.nearby_loading = False
                self._build_content()
                self._safe_update()

        if self.safe_page:
            self.safe_page.run_task(_query)
        else:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(_query())
            except RuntimeError:
                pass

    def _inject_nearby_to_day(self, place: Place) -> None:
        if not self.generated_itinerary or not self.generated_itinerary.days:
            return
        active_day = self.generated_itinerary.days[self.active_day_index]
        new_order = len(active_day.items) + 1
        new_item = ItineraryItem(
            id=str(uuid.uuid4()),
            day_id=active_day.id,
            place_id=place.id,
            place=place,
            custom_title=place.name,
            sort_order=new_order,
            planned_time="01:30 PM",
            duration_minutes=60,
            estimated_cost_min=place.estimated_cost_min,
            estimated_cost_max=place.estimated_cost_max,
        )
        active_day.items.append(new_item)
        self.save_feedback = f"Added '{place.name}' to Day {active_day.day_number}."
        self.view_mode = "itinerary"
        self._build_content()
        self._safe_update()

    def _customize_in_builder(self) -> None:
        if self.on_navigate and self.generated_itinerary:
            self.on_navigate("/builder", trip_data=self.generated_itinerary)

    def _save_generated_itinerary(self) -> None:
        if not self.generated_itinerary:
            return

        async def _do_save():
            try:
                # Save into cloud account or guest local storage
                from desktop_client.models.itinerary import ItineraryCreatePayload
                days_payload = []
                for d in self.generated_itinerary.days:
                    items_payload = []
                    for itm in d.items:
                        items_payload.append({
                            "place_id": itm.place_id,
                            "custom_title": itm.custom_title,
                            "sort_order": itm.sort_order,
                            "planned_time": itm.planned_time,
                            "duration_minutes": itm.duration_minutes,
                            "notes": itm.notes,
                            "estimated_cost_min": itm.estimated_cost_min,
                            "estimated_cost_max": itm.estimated_cost_max,
                            "place": itm.place.to_dict() if itm.place else None,
                        })
                    days_payload.append({
                        "day_number": d.day_number,
                        "travel_date": d.travel_date,
                        "title": d.title,
                        "items": items_payload,
                    })

                payload = ItineraryCreatePayload(
                    title=self.generated_itinerary.title,
                    destination=self.generated_itinerary.destination,
                    start_date=self.generated_itinerary.start_date,
                    end_date=self.generated_itinerary.end_date,
                    daily_budget=self.generated_itinerary.daily_budget,
                    preferences=self.generated_itinerary.preferences,
                    type="suggested",
                    days=days_payload,
                )
                saved = await self.itinerary_service.create_itinerary(payload)
                self.save_feedback = f"Trip '{saved.title}' saved to your itineraries!"
            except Exception as ex:
                self.save_feedback = f"Saved locally in itinerary draft ({str(ex)})."
            finally:
                self._build_content()
                self._safe_update()

        if self.safe_page:
            self.safe_page.run_task(_do_save)
        else:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(_do_save())
            except RuntimeError:
                pass

    def _on_dates_picked(self, start_d: str, end_d: str) -> None:
        self.start_date_val = start_d
        self.end_date_val = end_d
        self._build_content()
        self._safe_update()

    def _set_travel_mode(self, mode: str) -> None:
        self.travel_mode_val = mode
        self._build_content()
        self._safe_update()

    def _set_budget(self, amount: float) -> None:
        self.budget_val = amount
        self._build_content()
        self._safe_update()

    def _set_pacing(self, key: str) -> None:
        self.pacing_val = key
        self._build_content()
        self._safe_update()

    def _toggle_category(self, key: str) -> None:
        if key in self.selected_categories:
            if len(self.selected_categories) > 1:
                self.selected_categories.remove(key)
        else:
            self.selected_categories.add(key)
        self._build_content()
        self._safe_update()

    def _select_day(self, day_idx: int) -> None:
        self.active_day_index = day_idx
        self._build_content()
        self._safe_update()

    def _reset_wizard(self) -> None:
        self.generated_itinerary = None
        self.is_generating = False
        self.error_message = None
        self.view_mode = "form"
        self._build_content()
        self._safe_update()

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
                self._safe_update()
                return
        except ValueError:
            self.error_message = "Please enter valid dates in YYYY-MM-DD format."
            self._build_content()
            self._safe_update()
            return

        self.is_generating = True
        self._build_content()
        self._safe_update()

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
                    travel_mode=self.travel_mode_val.upper(),
                    save_immediately=False,
                )
                itin = await self.itinerary_service.generate_suggested_itinerary(req)
                self.generated_itinerary = itin
                self.active_day_index = 0
                self.view_mode = "itinerary"
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

        if self.safe_page:
            self.safe_page.run_task(_do_gen)
        else:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(_do_gen())
            except RuntimeError:
                pass

    def _safe_update(self) -> None:
        try:
            self.update()
        except Exception:
            pass

    @property
    def safe_page(self) -> Optional[ft.Page]:
        try:
            return self.page
        except Exception:
            return None

