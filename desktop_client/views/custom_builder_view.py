"""Custom Itinerary Builder View matching Web App 3-view state machine (form -> browse -> timeline).

Directly ports the architecture from Project/src/app/features/itinerary/custom-builder/:
- View 0 ('form'): Questionnaire for trip title, destination, dates, budget presets, preferences.
- View 1 ('browse'): Top segmented switcher, target day selector, place cards with stateful [+ Add] / [✓ Added].
- View 2 ('timeline'): Top switcher + [✓ Save], editable settings, day capsule bar, [🕒 Auto-Schedule],
  embedded ItineraryRouteMap, ordered stop cards with inter-stop leg commute badges, Edit Stop modal with
  Move to Day dropdown, and geofenced Off-Grid Custom Venue modal.
"""

from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta
from typing import Callable, Optional
import uuid
import flet as ft

from desktop_client.components.date_range_dialog import show_date_range_dialog
from desktop_client.components.destination_picker import DestinationPicker
from desktop_client.components.dialogs import show_place_detail_dialog
from desktop_client.components.itinerary_route_map import ItineraryRouteMap
from desktop_client.components.stop_card import StopCard
from desktop_client.config.settings import BUDGET_PRESETS, CANONICAL_CATEGORIES, ThemeColors
from desktop_client.core.commute_guide import get_leg_commute_info
from desktop_client.models.itinerary import (
    Itinerary,
    ItineraryCreatePayload,
    ItineraryDay,
    ItineraryItem,
)
from desktop_client.models.place import Place
from desktop_client.services.itinerary_service import get_itinerary_service
from desktop_client.services.place_service import get_place_service


class CustomBuilderView(ft.Container):
    """Custom itinerary builder matching the 3-view Web App flow."""

    def __init__(
        self,
        on_navigate: Optional[Callable[..., None]] = None,
        pre_added_place: Optional[Place] = None,
        existing_itinerary: Optional[Itinerary] = None,
        is_draft_from_wizard: bool = False,
    ):
        super().__init__()
        self.on_navigate = on_navigate
        self.place_service = get_place_service()
        self.itinerary_service = get_itinerary_service()
        self.pre_added_place = pre_added_place
        self.existing_itinerary = existing_itinerary

        self.expand = True
        self.padding = ft.Padding.symmetric(horizontal=24, vertical=16)
        self.bgcolor = ThemeColors.BG_LIGHT

        # Itinerary Draft State
        today = date.today()
        self.active_day_index = 0

        # Check active draft if passed from wizard
        draft = self.itinerary_service.get_active_draft_itinerary() if is_draft_from_wizard else None
        source_itin = existing_itinerary or draft

        if source_itin:
            self.trip_title = source_itin.title or "My Custom Trip"
            self.destination = source_itin.destination or "Nueva Ecija"
            self.start_date_str = source_itin.start_date or (today + timedelta(days=5)).strftime("%Y-%m-%d")
            self.end_date_str = source_itin.end_date or (today + timedelta(days=6)).strftime("%Y-%m-%d")
            self.daily_budget = source_itin.daily_budget or 2500.0
            self.preferences = list(source_itin.preferences) if source_itin.preferences else ["Nature & Parks", "Food Trip"]
            self.days: list[ItineraryDay] = list(source_itin.days) if source_itin.days else []
            self.active_view = "timeline"
        else:
            self.trip_title = "My Nueva Ecija Journey"
            self.destination = "Nueva Ecija"
            self.start_date_str = (today + timedelta(days=5)).strftime("%Y-%m-%d")
            self.end_date_str = (today + timedelta(days=6)).strftime("%Y-%m-%d")
            self.daily_budget = 2500.0
            self.preferences = ["Nature & Parks", "Food Trip"]
            self.days = []
            self.sync_days_with_date_range()
            # If pre_added_place passed from Home/Map, skip form and start in timeline
            if pre_added_place:
                self.active_view = "timeline"
            else:
                self.active_view = "form"

        # Pre-load place into Day 1 if passed
        if pre_added_place and len(self.days) > 0:
            if not any(item.place_id == pre_added_place.id for item in self.days[0].items):
                item = ItineraryItem(
                    id=str(uuid.uuid4()),
                    day_id=self.days[0].id,
                    place_id=pre_added_place.id,
                    place=pre_added_place,
                    custom_title=pre_added_place.name,
                    sort_order=1,
                    planned_time="09:00 AM",
                    duration_minutes=120,
                    estimated_cost_max=pre_added_place.estimated_cost_max or 0.0,
                    estimated_cost_min=pre_added_place.estimated_cost_min or 0.0,
                )
                self.days[0].items.insert(0, item)

        self.active_day_index = 0

        # Browse View State
        self.browse_search = ""
        self.browse_category = "all"
        self.browse_places: list[Place] = []
        self.browse_loading = False

        self.feedback_message: Optional[str] = None
        self.is_dirty: bool = bool(pre_added_place or existing_itinerary)

        self._build_content()
        self._load_browse_places()

    def has_unsaved_changes(self) -> bool:
        """Returns True if user has unsaved modifications in draft."""
        return getattr(self, "is_dirty", False)

    @property
    def total_stops_count(self) -> int:
        return sum(len(d.items) for d in self.days)

    def sync_days_with_date_range(self) -> None:
        """Aligns self.days with start_date_str and end_date_str."""
        try:
            start_d = datetime.strptime(self.start_date_str, "%Y-%m-%d").date()
            end_d = datetime.strptime(self.end_date_str, "%Y-%m-%d").date()
            if end_d < start_d:
                end_d = start_d
            diff = (end_d - start_d).days + 1
        except Exception:
            diff = 2

        new_days: list[ItineraryDay] = []
        for i in range(diff):
            current_date = (start_d + timedelta(days=i)).strftime("%Y-%m-%d")
            if i < len(self.days):
                day = self.days[i]
                day.day_number = i + 1
                day.travel_date = current_date
                new_days.append(day)
            else:
                new_days.append(
                    ItineraryDay(
                        id=str(uuid.uuid4()),
                        itinerary_id="",
                        day_number=i + 1,
                        travel_date=current_date,
                        title=f"Day {i + 1}",
                        items=[],
                    )
                )
        self.days = new_days
        self.active_day_index = min(getattr(self, "active_day_index", 0), max(0, len(self.days) - 1))

    def _auto_schedule_active_day(self, _=None) -> None:
        """Sequential planned_time recalculation starting at 09:00 AM with Haversine buffers."""
        if not self.days or self.active_day_index >= len(self.days):
            return
        day = self.days[self.active_day_index]
        if not day.items:
            return

        self.is_dirty = True
        current_minutes = 9 * 60  # 09:00 AM
        for idx, item in enumerate(day.items):
            hrs = (current_minutes // 60) % 24
            mins = current_minutes % 60
            ampm = "AM" if hrs < 12 else "PM"
            display_hrs = hrs if hrs <= 12 else hrs - 12
            if display_hrs == 0:
                display_hrs = 12
            item.planned_time = f"{display_hrs:02d}:{mins:02d} {ampm}"
            item.sort_order = idx + 1
            dur = item.duration_minutes or 90
            current_minutes += dur + 30
            # Midday dining anchor adjustment
            if 11 * 60 <= current_minutes < 12 * 60 and idx < len(day.items) - 1:
                current_minutes = 13 * 60

        self._build_content()
        self._safe_update()

    def _delete_active_day(self, _=None) -> None:
        """Deletes active day if more than 1 day exists."""
        if len(self.days) <= 1:
            return
        del self.days[self.active_day_index]
        for i, d in enumerate(self.days):
            d.day_number = i + 1
        self.is_dirty = True
        self.active_day_index = max(0, min(self.active_day_index, len(self.days) - 1))
        self._build_content()
        self._safe_update()

    def _add_new_day(self, _=None) -> None:
        """Appends a new day to the custom itinerary."""
        last_date = self.days[-1].travel_date if self.days else self.end_date_str
        try:
            next_date = (datetime.strptime(last_date, "%Y-%m-%d").date() + timedelta(days=1)).strftime("%Y-%m-%d")
        except Exception:
            next_date = self.end_date_str

        self.end_date_str = next_date
        new_day = ItineraryDay(
            id=str(uuid.uuid4()),
            itinerary_id="",
            day_number=len(self.days) + 1,
            travel_date=next_date,
            title=f"Day {len(self.days) + 1}",
            items=[],
        )
        self.days.append(new_day)
        self.active_day_index = len(self.days) - 1
        self.is_dirty = True
        self._build_content()
        self._safe_update()

    def _build_content(self) -> None:
        if self.active_view == "form":
            self.content = self._build_form_view()
        elif self.active_view == "browse":
            self.content = self._build_browse_view()
        else:
            self.content = self._build_timeline_view()

    # =========================================================================
    # VIEW 0: QUESTIONNAIRE FORM ('form')
    # =========================================================================
    def _build_form_view(self) -> ft.Control:
        title_block = ft.Column(
            controls=[
                ft.Text("Custom Itinerary Builder", size=24, weight=ft.FontWeight.W_800, color=ThemeColors.TEXT_BLACK),
                ft.Text("Tell us your travel details to start crafting your personalized schedule.", size=13, color=ThemeColors.TEXT_MUTED_LIGHT),
            ],
            spacing=4,
        )

        title_input = ft.TextField(
            label="Trip Title",
            value=self.trip_title,
            border_radius=12,
            dense=True,
            on_change=lambda e: setattr(self, "trip_title", e.control.value),
        )

        dest_picker = DestinationPicker(
            value=self.destination,
            on_change=lambda val: setattr(self, "destination", val),
        )

        date_summary = ft.Text(f"{self.start_date_str}  →  {self.end_date_str}", size=13, weight=ft.FontWeight.BOLD)
        date_btn = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.CALENDAR_MONTH, color=ThemeColors.PRIMARY_BLUE, size=18),
                    date_summary,
                ],
                spacing=8,
            ),
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
            border_radius=12,
            padding=ft.Padding.symmetric(horizontal=16, vertical=12),
            ink=True,
            on_click=lambda _: self._open_date_picker(date_summary),
        )

        budget_input = ft.TextField(
            label="Daily Budget (PHP)",
            value=str(int(self.daily_budget)),
            prefix=ft.Text("₱ "),
            border_radius=12,
            dense=True,
            on_change=lambda e: self._on_budget_change(e.control.value),
        )

        budget_pills = ft.Row(
            controls=[
                ft.Container(
                    content=ft.Text(
                        f"₱{p['amount'] if isinstance(p, dict) else float(p):,.0f}",
                        size=11,
                        weight=ft.FontWeight.BOLD,
                        color=ThemeColors.PRIMARY_BLUE,
                    ),
                    bgcolor=ThemeColors.AZURE_SOFT,
                    border_radius=8,
                    padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                    ink=True,
                    on_click=lambda _, b=(p["amount"] if isinstance(p, dict) else float(p)): self._set_budget_preset(b, budget_input),
                )
                for p in BUDGET_PRESETS
            ],
            spacing=8,
        )

        def _start_building(_):
            self.sync_days_with_date_range()
            self.active_view = "browse"
            self._build_content()
            self._safe_update()

        start_btn = ft.FilledButton(
            content=ft.Row(
                controls=[
                    ft.Text("Start Building Itinerary →", size=14, weight=ft.FontWeight.BOLD),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            style=ft.ButtonStyle(
                bgcolor=ThemeColors.PRIMARY_BLUE,
                color=ft.Colors.WHITE,
                padding=ft.Padding.symmetric(vertical=16),
                shape=ft.RoundedRectangleBorder(radius=12),
            ),
            width=float("inf"),
            on_click=_start_building,
        )

        form_card = ft.Container(
            content=ft.Column(
                controls=[
                    title_input,
                    ft.Container(height=4),
                    dest_picker,
                    ft.Container(height=4),
                    ft.Text("Travel Dates", size=12, weight=ft.FontWeight.W_600, color=ThemeColors.TEXT_MUTED_LIGHT),
                    date_btn,
                    ft.Container(height=4),
                    budget_input,
                    budget_pills,
                    ft.Container(height=16),
                    start_btn,
                ],
                spacing=12,
            ),
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
            border_radius=16,
            padding=24,
            width=580,
            shadow=ft.BoxShadow(blur_radius=12, color=ft.Colors.with_opacity(0.06, "#000000"), offset=ft.Offset(0, 4)),
        )

        return ft.Column(
            controls=[
                title_block,
                ft.Container(height=16),
                form_card,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            spacing=0,
            expand=True,
        )

    # =========================================================================
    # VIEW 1: BROWSE & ADD PLACES ('browse')
    # =========================================================================
    def _build_browse_view(self) -> ft.Control:
        # Segmented view switcher matching Web App
        top_switcher = self._build_segmented_switcher(active="browse")

        # Target Day Selector Bar
        day_chips: list[ft.Control] = []
        for idx, day in enumerate(self.days):
            is_sel = idx == self.active_day_index
            day_chips.append(
                ft.Container(
                    content=ft.Text(
                        f"Day {day.day_number} ({len(day.items)})",
                        size=11,
                        weight=ft.FontWeight.BOLD if is_sel else ft.FontWeight.NORMAL,
                        color=ft.Colors.WHITE if is_sel else ThemeColors.PRIMARY_BLUE,
                    ),
                    bgcolor=ThemeColors.PRIMARY_BLUE if is_sel else ThemeColors.AZURE_SOFT,
                    border_radius=10,
                    padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                    ink=True,
                    on_click=lambda _, i=idx: self._set_target_day(i),
                )
            )
        day_chips.append(
            ft.IconButton(
                icon=ft.Icons.ADD_CIRCLE_OUTLINE,
                icon_size=20,
                icon_color=ThemeColors.PRIMARY_BLUE,
                tooltip="Add another day",
                on_click=self._add_new_day,
            )
        )

        target_day_bar = ft.Row(
            controls=[
                ft.Text("Scheduling for:", size=12, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_MUTED_LIGHT),
                ft.Row(controls=day_chips, spacing=6),
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Search & Category Filters
        search_field = ft.TextField(
            hint_text="Search attractions, restaurants, resorts...",
            prefix_icon=ft.Icons.SEARCH,
            value=self.browse_search,
            border_radius=10,
            dense=True,
            expand=True,
            on_submit=lambda e: self._on_browse_search(e.control.value),
        )

        cat_chips: list[ft.Control] = []
        cats = [("all", "All"), ("nature_park", "Nature"), ("restaurant", "Food"), ("museum_cultural", "Culture"), ("resort_swimming", "Resorts"), ("shopping_market", "Shopping")]
        for c_key, c_label in cats:
            is_act = self.browse_category == c_key
            cat_chips.append(
                ft.Container(
                    content=ft.Text(c_label, size=11, weight=ft.FontWeight.BOLD if is_act else ft.FontWeight.NORMAL, color=ft.Colors.WHITE if is_act else ThemeColors.TEXT_MAIN_LIGHT),
                    bgcolor=ThemeColors.PRIMARY_BLUE if is_act else ThemeColors.SURFACE_LIGHT,
                    border=ft.Border.all(1, ThemeColors.PRIMARY_BLUE if is_act else ThemeColors.BORDER_LIGHT),
                    border_radius=12,
                    padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                    ink=True,
                    on_click=lambda _, k=c_key: self._on_browse_cat_change(k),
                )
            )

        # Place Cards Grid
        place_cards: list[ft.Control] = []
        active_day = self.days[self.active_day_index] if self.days else None
        added_place_ids = {it.place_id for it in active_day.items} if active_day else set()

        if self.browse_loading:
            place_cards.append(ft.Container(content=ft.ProgressRing(), alignment=ft.Alignment(0, 0), padding=40))
        elif not self.browse_places:
            place_cards.append(ft.Container(content=ft.Text("No places found for this filter.", size=13, color=ThemeColors.TEXT_MUTED_LIGHT), padding=40))
        else:
            for p in self.browse_places:
                is_added = p.id in added_place_ids
                place_cards.append(self._build_browse_place_card(p, is_added))

        # Bottom Bar: View Itinerary CTA
        bottom_bar = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(f"{self.total_stops_count} total places scheduled across {len(self.days)} days", size=13, weight=ft.FontWeight.W_600),
                    ft.FilledButton(
                        content=f"View my Itinerary ({self.total_stops_count} places) →",
                        style=ft.ButtonStyle(bgcolor=ThemeColors.PRIMARY_BLUE, color=ft.Colors.WHITE),
                        on_click=lambda _: self._switch_view("timeline"),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
            border_radius=12,
            padding=ft.Padding.symmetric(horizontal=20, vertical=12),
        )

        return ft.Column(
            controls=[
                top_switcher,
                ft.Container(height=8),
                target_day_bar,
                ft.Container(height=10),
                search_field,
                ft.Row(controls=cat_chips, spacing=6),
                ft.Container(height=12),
                ft.Column(controls=place_cards, spacing=8, scroll=ft.ScrollMode.AUTO, expand=True),
                ft.Container(height=8),
                bottom_bar,
            ],
            spacing=0,
            expand=True,
        )

    def _build_browse_place_card(self, place: Place, is_added: bool) -> ft.Control:
        action_btn = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.CHECK if is_added else ft.Icons.ADD, size=14, color=ft.Colors.WHITE if is_added else ThemeColors.PRIMARY_BLUE),
                    ft.Text("Added" if is_added else "Add", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE if is_added else ThemeColors.PRIMARY_BLUE),
                ],
                spacing=4,
                tight=True,
            ),
            bgcolor=ThemeColors.SUCCESS if is_added else ThemeColors.AZURE_SOFT,
            border=ft.Border.all(1, ThemeColors.SUCCESS if is_added else ThemeColors.PRIMARY_BLUE),
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=12, vertical=6),
            ink=True,
            on_click=lambda _: self._toggle_place_in_active_day(place),
        )

        details_btn = ft.TextButton(
            "Details",
            icon=ft.Icons.INFO_OUTLINE,
            on_click=lambda _: show_place_detail_dialog(self.page, place),
            style=ft.ButtonStyle(padding=ft.Padding.symmetric(horizontal=8, vertical=4)),
        )

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Image(
                        src=place.resolved_image_path,
                        width=80,
                        height=64,
                        fit=ft.BoxFit.COVER,
                        border_radius=8,
                        error_content=ft.Icon(ft.Icons.LANDSCAPE, size=24, color=ThemeColors.PRIMARY_BLUE),
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(place.name, size=13, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_BLACK),
                            ft.Text(f"{place.municipality_name or 'Nueva Ecija'} • {place.formatted_category}", size=11, color=ThemeColors.TEXT_MUTED_LIGHT),
                            ft.Text(place.formatted_cost, size=11, weight=ft.FontWeight.BOLD, color=ThemeColors.EMERALD_PRIMARY),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    ft.Row(controls=[details_btn, action_btn], spacing=6),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
            border_radius=10,
            padding=8,
        )

    # =========================================================================
    # VIEW 2: TIMELINE ITINERARY ('timeline')
    # =========================================================================
    def _build_timeline_view(self) -> ft.Control:
        top_switcher = self._build_segmented_switcher(active="timeline")

        # Active Day
        active_day = self.days[self.active_day_index] if self.days else None

        # Day capsule bar
        day_buttons: list[ft.Control] = []
        for idx, day in enumerate(self.days):
            is_act = idx == self.active_day_index
            day_buttons.append(
                ft.Container(
                    content=ft.Text(
                        f"Day {day.day_number} ({len(day.items)})",
                        size=11,
                        weight=ft.FontWeight.BOLD if is_act else ft.FontWeight.NORMAL,
                        color=ft.Colors.WHITE if is_act else ThemeColors.TEXT_MAIN_LIGHT,
                    ),
                    bgcolor=ThemeColors.PRIMARY_BLUE if is_act else ThemeColors.SURFACE_LIGHT,
                    border=ft.Border.all(1, ThemeColors.PRIMARY_BLUE if is_act else ThemeColors.BORDER_LIGHT),
                    border_radius=10,
                    padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                    ink=True,
                    on_click=lambda _, i=idx: self._set_target_day(i),
                )
            )
        day_buttons.append(
            ft.IconButton(icon=ft.Icons.ADD_CIRCLE_OUTLINE, icon_size=18, icon_color=ThemeColors.PRIMARY_BLUE, tooltip="Add Day", on_click=self._add_new_day)
        )

        day_bar = ft.Row(controls=day_buttons, spacing=6)

        # Active Day Header Actions
        active_day_header = ft.Row(
            controls=[
                ft.Text(f"Day {active_day.day_number if active_day else 1} — {active_day.travel_date if active_day else ''}", size=16, weight=ft.FontWeight.BOLD),
                ft.Row(
                    controls=[
                        ft.FilledButton(
                            content="🕒 Auto-Schedule",
                            style=ft.ButtonStyle(bgcolor=ThemeColors.AZURE_SOFT, color=ThemeColors.PRIMARY_BLUE),
                            on_click=self._auto_schedule_active_day,
                        ),
                        ft.OutlinedButton(
                            content="🗑 Delete Day",
                            style=ft.ButtonStyle(color=ThemeColors.ERROR),
                            on_click=self._delete_active_day,
                            disabled=len(self.days) <= 1,
                        ),
                    ],
                    spacing=8,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        # Embedded Route Map
        route_map = ItineraryRouteMap(
            day=active_day,
            on_view_full_map=lambda: self._open_full_map_draft(),
            height_expanded=240,
        )

        # Timeline Items with Commute Badges
        timeline_items: list[ft.Control] = []
        if active_day and active_day.items:
            for idx, item in enumerate(active_day.items):
                if idx > 0:
                    prev_item = active_day.items[idx - 1]
                    leg_info = get_leg_commute_info(prev_item, item)
                    timeline_items.append(
                        ft.Container(
                            content=ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.DIRECTIONS_CAR, size=13, color=ThemeColors.PRIMARY_BLUE),
                                    ft.Text(leg_info.display_text, size=11, weight=ft.FontWeight.W_600, color=ThemeColors.PRIMARY_BLUE),
                                ],
                                spacing=6,
                            ),
                            bgcolor=ThemeColors.AZURE_SOFT,
                            border_radius=8,
                            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                            margin=ft.Margin.only(left=24, top=2, bottom=2),
                        )
                    )
                timeline_items.append(
                    StopCard(
                        item=item,
                        editable=True,
                        on_move_up=lambda it=item: self._move_stop(it, -1),
                        on_move_down=lambda it=item: self._move_stop(it, 1),
                        on_edit=lambda it=item: self._open_edit_stop_dialog(it),
                        on_delete=lambda it=item: self._remove_stop(it),
                    )
                )
        else:
            timeline_items.append(
                ft.Container(
                    content=ft.Text("No stops scheduled yet for this day. Click '+ Browse & Add Places' below.", size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                    padding=20,
                )
            )

        # Bottom Add Buttons
        bottom_add_row = ft.Row(
            controls=[
                ft.FilledButton(
                    content="+ Browse & Add Places to Day",
                    style=ft.ButtonStyle(bgcolor=ThemeColors.PRIMARY_BLUE, color=ft.Colors.WHITE),
                    on_click=lambda _: self._switch_view("browse"),
                ),
                ft.OutlinedButton(
                    content="+ Add Off-Grid Custom Venue",
                    on_click=lambda _: self._open_custom_venue_dialog(),
                ),
            ],
            spacing=10,
        )

        # Save CTA Footer
        footer_cta = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(f"Total: {self.total_stops_count} places • ~₱{sum(d.total_day_cost for d in self.days):,.0f} estimated cost", size=13, weight=ft.FontWeight.BOLD),
                    ft.FilledButton(
                        content="💾 Save Custom Itinerary",
                        style=ft.ButtonStyle(bgcolor=ThemeColors.SUCCESS, color=ft.Colors.WHITE),
                        on_click=lambda _: self._save_custom_itinerary(),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
            border_radius=12,
            padding=ft.Padding.symmetric(horizontal=20, vertical=12),
        )

        return ft.Column(
            controls=[
                top_switcher,
                ft.Container(height=8),
                day_bar,
                ft.Container(height=10),
                active_day_header,
                ft.Container(height=8),
                route_map,
                ft.Container(height=10),
                ft.Column(controls=timeline_items, spacing=4),
                ft.Container(height=12),
                bottom_add_row,
                ft.Container(height=14),
                footer_cta,
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=0,
            expand=True,
        )

    def _build_segmented_switcher(self, active: str) -> ft.Control:
        is_browse = active == "browse"
        return ft.Row(
            controls=[
                ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Text(
                                "+ Add Places",
                                size=12,
                                weight=ft.FontWeight.BOLD if is_browse else ft.FontWeight.NORMAL,
                                color=ft.Colors.WHITE if is_browse else ThemeColors.TEXT_MAIN_LIGHT,
                            ),
                            bgcolor=ThemeColors.PRIMARY_BLUE if is_browse else ThemeColors.SURFACE_LIGHT,
                            border_radius=8,
                            padding=ft.Padding.symmetric(horizontal=16, vertical=8),
                            ink=True,
                            on_click=lambda _: self._switch_view("browse"),
                        ),
                        ft.Container(
                            content=ft.Text(
                                f"📅 Your Itinerary ({self.total_stops_count})",
                                size=12,
                                weight=ft.FontWeight.BOLD if not is_browse else ft.FontWeight.NORMAL,
                                color=ft.Colors.WHITE if not is_browse else ThemeColors.TEXT_MAIN_LIGHT,
                            ),
                            bgcolor=ThemeColors.PRIMARY_BLUE if not is_browse else ThemeColors.SURFACE_LIGHT,
                            border_radius=8,
                            padding=ft.Padding.symmetric(horizontal=16, vertical=8),
                            ink=True,
                            on_click=lambda _: self._switch_view("timeline"),
                        ),
                    ],
                    spacing=0,
                ),
                ft.FilledButton(
                    content="✓ Save",
                    style=ft.ButtonStyle(bgcolor=ThemeColors.PRIMARY_BLUE, color=ft.Colors.WHITE),
                    on_click=lambda _: self._save_custom_itinerary(),
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

    # =========================================================================
    # ACTIONS & HANDLERS
    # =========================================================================
    def _switch_view(self, view_name: str) -> None:
        self.active_view = view_name
        self._build_content()
        self._safe_update()

    def _set_target_day(self, idx: int) -> None:
        self.active_day_index = idx
        self._build_content()
        self._safe_update()

    def _toggle_place_in_active_day(self, place: Place) -> None:
        if not self.days or self.active_day_index >= len(self.days):
            return
        day = self.days[self.active_day_index]
        existing_idx = next((i for i, it in enumerate(day.items) if it.place_id == place.id), None)
        self.is_dirty = True

        if existing_idx is not None:
            del day.items[existing_idx]
        else:
            time_str = self._calc_next_time(day)
            item = ItineraryItem(
                id=str(uuid.uuid4()),
                day_id=day.id,
                place_id=place.id,
                place=place,
                custom_title=place.name,
                sort_order=len(day.items) + 1,
                planned_time=time_str,
                duration_minutes=90,
                estimated_cost_max=place.estimated_cost_max or 0.0,
                estimated_cost_min=place.estimated_cost_min or 0.0,
            )
            day.items.append(item)

        self._build_content()
        self._safe_update()

    def _calc_next_time(self, day: ItineraryDay) -> str:
        if not day.items:
            return "09:00 AM"
        dur = day.items[-1].duration_minutes or 90
        try:
            t = datetime.strptime(day.items[-1].planned_time or "09:00 AM", "%I:%M %p")
            nxt = t + timedelta(minutes=dur + 30)
            return nxt.strftime("%I:%M %p")
        except Exception:
            return "11:00 AM"

    def _move_stop(self, item: ItineraryItem, delta: int) -> None:
        day = self.days[self.active_day_index]
        idx = day.items.index(item)
        new_idx = idx + delta
        if 0 <= new_idx < len(day.items):
            day.items[idx], day.items[new_idx] = day.items[new_idx], day.items[idx]
            for i, itm in enumerate(day.items):
                itm.sort_order = i + 1
            self.is_dirty = True
            self._build_content()
            self._safe_update()

    def _remove_stop(self, item: ItineraryItem) -> None:
        day = self.days[self.active_day_index]
        if item in day.items:
            day.items.remove(item)
            for i, itm in enumerate(day.items):
                itm.sort_order = i + 1
            self.is_dirty = True
            self._build_content()
            self._safe_update()

    def _open_edit_stop_dialog(self, item: ItineraryItem) -> None:
        """Edit stop modal with Move to Day dropdown support."""
        time_field = ft.TextField(label="Planned Time", value=item.planned_time or "09:00 AM", dense=True)
        dur_field = ft.TextField(label="Duration (mins)", value=str(item.duration_minutes or 90), dense=True)
        notes_field = ft.TextField(label="Notes", value=item.notes or "", dense=True, multiline=True)

        day_options = [ft.dropdown.Option(str(d.day_number), f"Day {d.day_number}") for d in self.days]
        day_dropdown = ft.Dropdown(
            label="Move to Day",
            options=day_options,
            value=str(self.days[self.active_day_index].day_number),
            dense=True,
        )

        def _save_edit(_):
            item.planned_time = time_field.value.strip()
            try:
                item.duration_minutes = int(dur_field.value.strip())
            except ValueError:
                pass
            item.notes = notes_field.value.strip()

            target_day_num = int(day_dropdown.value)
            current_day_num = self.days[self.active_day_index].day_number
            if target_day_num != current_day_num:
                self.days[self.active_day_index].items.remove(item)
                target_day = next(d for d in self.days if d.day_number == target_day_num)
                item.sort_order = len(target_day.items) + 1
                target_day.items.append(item)

            self.is_dirty = True
            dlg.open = False
            self.page.update()
            self._build_content()
            self._safe_update()

        dlg = ft.AlertDialog(
            title=ft.Text(f"Edit Stop: {item.custom_title or (item.place.name if item.place else 'Stop')}"),
            content=ft.Column(controls=[day_dropdown, time_field, dur_field, notes_field], tight=True, spacing=10),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: setattr(dlg, "open", False) or self.page.update()),
                ft.FilledButton("Save", on_click=_save_edit),
            ],
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def _open_custom_venue_dialog(self) -> None:
        """Adds off-grid custom venue geofenced to Nueva Ecija (Lat 15.15-16.15, Lng 120.70-121.40)."""
        name_field = ft.TextField(label="Venue Name *", dense=True)
        muni_field = ft.TextField(label="Municipality / Location", dense=True)
        lat_field = ft.TextField(label="Latitude (15.15 – 16.15)", dense=True, value="15.5800")
        lng_field = ft.TextField(label="Longitude (120.70 – 121.40)", dense=True, value="121.0000")
        err_text = ft.Text("", size=11, color=ThemeColors.ERROR)

        def _add_venue(_):
            name = name_field.value.strip()
            if not name:
                err_text.value = "Venue Name is required."
                dlg.update()
                return
            try:
                lat = float(lat_field.value.strip())
                lng = float(lng_field.value.strip())
                if not (15.10 <= lat <= 16.25 and 120.65 <= lng <= 121.50):
                    err_text.value = "Coordinates outside Nueva Ecija (Lat 15.15–16.15, Lng 120.70–121.40)."
                    dlg.update()
                    return
            except ValueError:
                err_text.value = "Please enter valid numeric coordinates."
                dlg.update()
                return

            active_day = self.days[self.active_day_index]
            new_item = ItineraryItem(
                id=str(uuid.uuid4()),
                day_id=active_day.id,
                custom_title=name,
                sort_order=len(active_day.items) + 1,
                planned_time=self._calc_next_time(active_day),
                duration_minutes=90,
                latitude=lat,
                longitude=lng,
                custom_lat=lat,
                custom_lng=lng,
            )
            active_day.items.append(new_item)
            self.is_dirty = True
            dlg.open = False
            self.page.update()
            self._build_content()
            self._safe_update()

        dlg = ft.AlertDialog(
            title=ft.Text("Add Off-Grid Custom Venue"),
            content=ft.Column(controls=[name_field, muni_field, ft.Row(controls=[lat_field, lng_field], spacing=8), err_text], tight=True, spacing=8),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: setattr(dlg, "open", False) or self.page.update()),
                ft.FilledButton("Add Venue", on_click=_add_venue),
            ],
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def _open_full_map_draft(self) -> None:
        """Handoff draft custom itinerary to MapView Follow-Route mode."""
        draft_itin = Itinerary(
            id="draft",
            title=self.trip_title,
            destination=self.destination,
            start_date=self.start_date_str,
            end_date=self.end_date_str,
            daily_budget=self.daily_budget,
            preferences=self.preferences,
            days=self.days,
        )
        self.itinerary_service.set_active_draft_itinerary(draft_itin)
        day_num = self.active_day_index + 1
        if self.on_navigate:
            self.on_navigate(f"/map?itineraryId=draft&day={day_num}")

    def _save_custom_itinerary(self) -> None:
        if self.total_stops_count == 0:
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text("Please add at least 1 stop before saving!"), open=True)
                self.page.update()
            return

        async def _do_save():
            days_payload = []
            for d in self.days:
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
                title=self.trip_title,
                destination=self.destination,
                start_date=self.start_date_str,
                end_date=self.end_date_str,
                daily_budget=self.daily_budget,
                preferences=self.preferences,
                type="custom",
                days=days_payload,
            )
            saved = await self.itinerary_service.create_itinerary(payload)
            self.is_dirty = False
            self.itinerary_service.set_active_draft_itinerary(None)
            if self.on_navigate:
                self.on_navigate(f"/trips/{saved.id}", trip_data=saved)

        p = self.safe_page
        if p:
            p.run_task(_do_save)
        else:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(_do_save())
            except RuntimeError:
                pass

    def _open_date_picker(self, summary_label: ft.Text) -> None:
        def _on_dates(s: str, e: str):
            self.start_date_str = s
            self.end_date_str = e
            summary_label.value = f"{s}  →  {e}"
            self.sync_days_with_date_range()
            self.is_dirty = True
            self._safe_update()

        show_date_range_dialog(
            self.page,
            initial_start=self.start_date_str,
            initial_end=self.end_date_str,
            on_apply=_on_dates,
        )

    def _set_budget_preset(self, val: float, field_ctrl: ft.TextField) -> None:
        self.daily_budget = val
        field_ctrl.value = str(int(val))
        self.is_dirty = True
        self._safe_update()

    def _on_budget_change(self, val: str) -> None:
        try:
            self.daily_budget = float(val.replace(",", "").strip())
            self.is_dirty = True
        except ValueError:
            pass

    def _on_browse_search(self, query: str) -> None:
        self.browse_search = query.strip()
        self._load_browse_places()

    def _on_browse_cat_change(self, cat: str) -> None:
        self.browse_category = cat
        self._load_browse_places()

    def _load_browse_places(self) -> None:
        self.browse_loading = True
        self._build_content()
        self._safe_update()

        async def _worker():
            try:
                cat = None if self.browse_category == "all" else self.browse_category
                q = self.browse_search if self.browse_search else None
                res = await self.place_service.get_places(page=1, page_size=60, category=cat, search=q)
                self.browse_places = res.items
            except Exception:
                from desktop_client.core.offline_data import get_all_offline_places
                raw = get_all_offline_places()
                self.browse_places = [Place.from_dict(p) for p in raw[:60]]
            finally:
                self.browse_loading = False
                self._build_content()
                self._safe_update()

        p = self.safe_page
        if p:
            p.run_task(_worker)
        else:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(_worker())
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
