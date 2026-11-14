"""Custom Itinerary Builder View mirroring Web App CustomBuilderPage and UC-C01-UC-C14.

State Machine & Views:
- View 0 ('form'): Questionnaire for trip title, destination, dates, budget presets, preferences.
- View 1 ('browse'): "Add the places you want to visit", target day selector, category filter pills with Other,
  place cards grid with [+ Add] / [✓ Added], empty state with Reset Filters, and bottom View Itinerary CTA.
- View 2 ('timeline'): Dismissible Pre-Loaded Place banner, 2-row .trip-settings-card, separate .verified-budget-card,
  2-line day capsule bar, Day X header with conditional Auto-Schedule and Delete Day (with confirmation),
  Stop Cards with Reorder / Edit (Move to Day reindexing both days) / Remove (with confirmation),
  empty day card with CTA, 2-tab Off-Grid modal (Browse Places with duplicate guard + Off-Grid Venue with
  collapsible 15.15-16.15 / 120.70-121.40 coordinates), and "💾 View Full Itinerary / Save Trip" CTA.
"""

from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta
from typing import Callable, Optional
import uuid
import flet as ft

from desktop_client.components.destination_picker import DestinationPicker
from desktop_client.components.dialogs import show_date_range_dialog, show_place_detail_dialog
from desktop_client.components.itinerary_route_map import ItineraryRouteMap
from desktop_client.components.stop_card import StopCard
from desktop_client.config.settings import ThemeColors, get_settings
from desktop_client.core.commute_guide import get_leg_commute_info
from desktop_client.core.polyline import haversine_distance_meters
from desktop_client.core.session import get_session_manager
from desktop_client.models.itinerary import (
    Itinerary,
    ItineraryDay,
    ItineraryItem,
)
from desktop_client.models.place import Place
from desktop_client.services.itinerary_service import get_itinerary_service
from desktop_client.services.place_service import get_place_service


class CustomBuilderView(ft.Container):
    """Custom itinerary builder matching the 3-view Web App flow and UC-C01 through UC-C14."""

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
        self.settings = get_settings()
        self.pre_added_place = pre_added_place
        self.existing_itinerary = existing_itinerary
        self.is_draft_from_wizard = is_draft_from_wizard

        self.expand = True
        self.padding = ft.Padding.symmetric(horizontal=24, vertical=16)
        self.bgcolor = ThemeColors.BG_LIGHT

        # Itinerary Draft State
        today = date.today()
        self.active_day_index = 0
        self.is_dirty = False
        self.is_saving = False
        self.banner_dismissed = False

        # Check active draft if passed from wizard
        draft = self.itinerary_service.get_active_draft_itinerary() if is_draft_from_wizard else None
        source_itin = existing_itinerary or draft

        user = get_session_manager().current_user
        default_b = float(user.default_daily_budget) if (user and user.default_daily_budget) else 3000.0

        if source_itin:
            self.trip_title = source_itin.title or "Nueva Ecija Getaway"
            self.destination = source_itin.destination or "Nueva Ecija"
            self.start_date_str = source_itin.start_date or today.strftime("%Y-%m-%d")
            self.end_date_str = source_itin.end_date or (today + timedelta(days=1)).strftime("%Y-%m-%d")
            self.daily_budget = source_itin.daily_budget or default_b
            self.preferences = list(source_itin.preferences) if source_itin.preferences else []
            self.days: list[ItineraryDay] = list(source_itin.days) if source_itin.days else []
            self.active_view = "timeline"
        else:
            self.trip_title = "Nueva Ecija Getaway"
            self.destination = "Nueva Ecija"
            self.start_date_str = today.strftime("%Y-%m-%d")
            self.end_date_str = (today + timedelta(days=1)).strftime("%Y-%m-%d")
            self.daily_budget = default_b
            self.preferences = []
            self.days = []
            self.sync_days_with_date_range()
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
                self.is_dirty = True

        self.active_day_index = 0

        # Browse View State
        self.browse_search = ""
        self.browse_category = "all"

        self._build_content()

    @property
    def total_stops_count(self) -> int:
        return sum(len(d.items) for d in self.days)

    def handle_back(self) -> bool:
        """Handles back button stepping through state machine with unsaved changes guard (UC-C14)."""
        if self.is_dirty:
            self._prompt_discard_changes()
            return True

        if self.active_view == "browse":
            self.active_view = "timeline" if self.total_stops_count > 0 else "form"
            self._build_content()
            self._safe_update()
            return True
        elif self.active_view == "timeline":
            if self.total_stops_count == 0:
                self.active_view = "form"
                self._build_content()
                self._safe_update()
                return True
            self._navigate("/home")
            return True

        return False

    def _prompt_discard_changes(self) -> None:
        def _do_discard(_):
            self.is_dirty = False
            dlg.open = False
            if self.safe_page:
                self.safe_page.update()
            self._navigate("/home")

        def _keep_editing(_):
            dlg.open = False
            if self.safe_page:
                self.safe_page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Discard Changes?", size=18, weight=ft.FontWeight.BOLD),
            content=ft.Text("You have unsaved changes in your itinerary. Leaving will discard them.", size=13),
            actions=[
                ft.TextButton("Keep Editing", on_click=_keep_editing),
                ft.FilledButton("Discard", style=ft.ButtonStyle(bgcolor=ThemeColors.ERROR, color=ft.Colors.WHITE), on_click=_do_discard),
            ],
        )
        if self.safe_page:
            self.safe_page.overlay.append(dlg)
            dlg.open = True
            self.safe_page.update()

    def sync_days_with_date_range(self) -> None:
        """Aligns self.days with start_date_str and end_date_str."""
        try:
            s_d = datetime.strptime(self.start_date_str, "%Y-%m-%d").date()
            e_d = datetime.strptime(self.end_date_str, "%Y-%m-%d").date()
            if e_d < s_d:
                e_d = s_d
                self.end_date_str = self.start_date_str
            num_days = max(1, (e_d - s_d).days + 1)
        except Exception:
            num_days = 2
            s_d = date.today()

        new_days: list[ItineraryDay] = []
        for i in range(num_days):
            cur_date = (s_d + timedelta(days=i)).strftime("%Y-%m-%d")
            if i < len(self.days):
                d = self.days[i]
                d.day_number = i + 1
                d.travel_date = cur_date
                new_days.append(d)
            else:
                new_days.append(
                    ItineraryDay(
                        id=str(uuid.uuid4()),
                        itinerary_id="",
                        day_number=i + 1,
                        travel_date=cur_date,
                        title=f"Day {i + 1}",
                        items=[],
                    )
                )
        self.days = new_days
        self.active_day_index = max(0, min(self.active_day_index, len(self.days) - 1))

    def _auto_schedule_active_day(self, _=None) -> None:
        """Sequentially spaces scheduled times starting from 09:00 AM."""
        if not self.days or self.active_day_index >= len(self.days):
            return
        day = self.days[self.active_day_index]
        if not day.items:
            return

        current_minutes = 9 * 60  # 09:00 AM
        for idx, item in enumerate(day.items):
            if idx > 0:
                prev = day.items[idx - 1]
                p1_lat = getattr(prev, "custom_lat", None) or (prev.place.latitude if prev.place else None)
                p1_lng = getattr(prev, "custom_lng", None) or (prev.place.longitude if prev.place else None)
                p2_lat = getattr(item, "custom_lat", None) or (item.place.latitude if item.place else None)
                p2_lng = getattr(item, "custom_lng", None) or (item.place.longitude if item.place else None)
                if p1_lat and p1_lng and p2_lat and p2_lng:
                    dist_km = haversine_distance_meters(float(p1_lat), float(p1_lng), float(p2_lat), float(p2_lng)) / 1000.0
                    transit_mins = max(15, min(120, int((dist_km / 40.0) * 60 + 10)))
                else:
                    transit_mins = 30
                current_minutes += transit_mins

            hrs = (current_minutes // 60) % 24
            mins = current_minutes % 60
            ampm = "AM" if hrs < 12 else "PM"
            display_hrs = hrs if hrs <= 12 else hrs - 12
            if display_hrs == 0:
                display_hrs = 12
            item.planned_time = f"{display_hrs:02d}:{mins:02d} {ampm}"
            item.sort_order = idx + 1
            dur = item.duration_minutes or 90
            current_minutes += dur
            if 11 * 60 <= current_minutes < 12 * 60 and idx < len(day.items) - 1:
                current_minutes = 13 * 60

        self.is_dirty = True
        self._build_content()
        self._safe_update()

    def _delete_active_day(self, _=None) -> None:
        """Prompts confirmation dialog before deleting active day (UC-C09)."""
        if len(self.days) <= 1:
            return
        cur_day = self.days[self.active_day_index]

        def _confirm_delete(_):
            dlg.open = False
            if self.safe_page:
                self.safe_page.update()
            del self.days[self.active_day_index]
            for i, d in enumerate(self.days):
                d.day_number = i + 1
            self.is_dirty = True
            self.active_day_index = max(0, min(self.active_day_index, len(self.days) - 1))
            self._build_content()
            self._safe_update()

        def _cancel(_):
            dlg.open = False
            if self.safe_page:
                self.safe_page.update()

        dlg = ft.AlertDialog(
            title=ft.Text(f"Delete Day {cur_day.day_number}?", size=18, weight=ft.FontWeight.BOLD),
            content=ft.Text("All stops scheduled for this day will be removed.", size=13),
            actions=[
                ft.TextButton("Cancel", on_click=_cancel),
                ft.FilledButton("Delete Day", style=ft.ButtonStyle(bgcolor=ThemeColors.ERROR, color=ft.Colors.WHITE), on_click=_confirm_delete),
            ],
        )
        if self.safe_page:
            self.safe_page.overlay.append(dlg)
            dlg.open = True
            self.safe_page.update()

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

    def _format_date_range_display(self, start_iso: str, end_iso: str) -> tuple[str, str]:
        try:
            s_d = datetime.strptime(start_iso, "%Y-%m-%d").date()
            e_d = datetime.strptime(end_iso, "%Y-%m-%d").date()
            days = (e_d - s_d).days + 1
            nights = max(0, days - 1)
            night_str = f", {nights} {'night' if nights == 1 else 'nights'}" if nights > 0 else ""
            date_str = f"{s_d.strftime('%b %d')} – {e_d.strftime('%b %d, %Y')}"
            subtitle = f"{date_str} ({days} {'day' if days == 1 else 'days'}{night_str})"
            return date_str, subtitle
        except Exception:
            return f"{start_iso} → {end_iso}", f"{start_iso} → {end_iso}"

    # =========================================================================
    # HEADER BAR & 2-TAB VIEW SWITCHER (UC-C01)
    # =========================================================================
    def _build_header_bar(self) -> ft.Control:
        is_timeline = self.active_view == "timeline"
        title_text = "Your Custom Itinerary" if is_timeline else "Custom Itinerary"

        save_btn = ft.Container()
        if self.active_view != "form":
            can_save = self.total_stops_count > 0 and not self.is_saving
            save_btn = ft.FilledButton(
                content="✓ Save",
                style=ft.ButtonStyle(
                    bgcolor=ThemeColors.PRIMARY_BLUE if can_save else "#94a3b8",
                    color=ft.Colors.WHITE,
                ),
                disabled=not can_save,
                on_click=lambda _: self._save_custom_itinerary(),
            )

        top_row = ft.Container(
            content=ft.Row(
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        icon_color=ThemeColors.PRIMARY_BLUE,
                        icon_size=22,
                        tooltip="Back",
                        on_click=lambda _: self.handle_back(),
                    ),
                    ft.Text(title_text, size=20, weight=ft.FontWeight.W_800, color=ThemeColors.TEXT_BLACK),
                    save_btn,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border=ft.Border.only(bottom=ft.BorderSide(1, ThemeColors.BORDER_LIGHT)),
            padding=ft.Padding.symmetric(horizontal=16, vertical=8),
        )

        if self.active_view == "form":
            return ft.Column(controls=[top_row], spacing=0)

        # 2-Tab View Mode Bar (+ Add Places | 📅 Your Itinerary (N))
        is_browse = self.active_view == "browse"
        view_tabs = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Text(
                            "+ Add Places",
                            size=13,
                            weight=ft.FontWeight.BOLD if is_browse else ft.FontWeight.W_500,
                            color=ft.Colors.WHITE if is_browse else ThemeColors.TEXT_MAIN_LIGHT,
                        ),
                        bgcolor=ThemeColors.PRIMARY_BLUE if is_browse else ThemeColors.SURFACE_LIGHT,
                        border_radius=8,
                        padding=ft.Padding.symmetric(horizontal=18, vertical=8),
                        ink=True,
                        on_click=lambda _: self._switch_view("browse"),
                    ),
                    ft.Container(
                        content=ft.Text(
                            f"📅 Your Itinerary ({self.total_stops_count})",
                            size=13,
                            weight=ft.FontWeight.BOLD if not is_browse else ft.FontWeight.W_500,
                            color=ft.Colors.WHITE if not is_browse else ThemeColors.TEXT_MAIN_LIGHT,
                        ),
                        bgcolor=ThemeColors.PRIMARY_BLUE if not is_browse else ThemeColors.SURFACE_LIGHT,
                        border_radius=8,
                        padding=ft.Padding.symmetric(horizontal=18, vertical=8),
                        ink=True,
                        on_click=lambda _: self._switch_view("timeline"),
                    ),
                ],
                spacing=4,
            ),
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border=ft.Border.only(bottom=ft.BorderSide(1, ThemeColors.BORDER_LIGHT)),
            padding=ft.Padding.symmetric(horizontal=16, vertical=6),
            margin=ft.Margin.only(bottom=10),
        )

        return ft.Column(controls=[top_row, view_tabs], spacing=0)

    def _build_content(self) -> None:
        header = self._build_header_bar()
        if self.active_view == "form":
            body = self._build_form_view()
        elif self.active_view == "browse":
            body = self._build_browse_view()
        else:
            body = self._build_timeline_view()

        self.content = ft.Column(
            controls=[header, ft.Container(content=body, expand=True)],
            spacing=0,
            expand=True,
        )

    # =========================================================================
    # VIEW 0: QUESTIONNAIRE FORM ('form' — UC-C02)
    # =========================================================================
    def _build_form_view(self) -> ft.Control:
        heading = ft.Text(
            "Tell us your travel details",
            size=22,
            weight=ft.FontWeight.W_800,
            color=ThemeColors.TEXT_BLACK,
        )

        title_input = ft.TextField(
            label="Trip Title",
            value=self.trip_title,
            border_radius=10,
            border_color="#cbd5e1",
            focused_border_color=ThemeColors.PRIMARY_BLUE,
            filled=True,
            bgcolor=ft.Colors.WHITE,
            dense=True,
            content_padding=ft.Padding.symmetric(horizontal=12, vertical=10),
            on_change=lambda e: setattr(self, "trip_title", e.control.value),
        )

        dest_picker = DestinationPicker(
            value=self.destination,
            on_change=lambda val: setattr(self, "destination", val),
        )

        date_range_str, date_sub_str = self._format_date_range_display(self.start_date_str, self.end_date_str)
        date_btn = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.CALENDAR_MONTH, color=ThemeColors.PRIMARY_BLUE, size=20),
                    ft.Text(date_range_str, size=13, weight=ft.FontWeight.W_600, color=ThemeColors.TEXT_BLACK),
                ],
                spacing=10,
            ),
            bgcolor=ft.Colors.WHITE,
            border=ft.Border.all(1, "#cbd5e1"),
            border_radius=10,
            padding=ft.Padding.symmetric(horizontal=14, vertical=12),
            ink=True,
            on_click=lambda _: self._open_date_picker(),
        )
        date_helper = ft.Text(date_sub_str, size=11, color=ThemeColors.TEXT_FAINT_LIGHT)

        budget_input = ft.TextField(
            label="Daily Budget (₱)",
            value=str(int(self.daily_budget)),
            prefix=ft.Text("₱ "),
            border_radius=10,
            border_color="#cbd5e1",
            focused_border_color=ThemeColors.PRIMARY_BLUE,
            filled=True,
            bgcolor=ft.Colors.WHITE,
            dense=True,
            content_padding=ft.Padding.symmetric(horizontal=12, vertical=10),
            on_change=lambda e: self._on_budget_change(e.control.value),
        )

        budget_presets = [1500, 2500, 4000, 6000]
        budget_chips = [
            ft.Container(
                content=ft.Text(f"₱{b:,}", size=11, weight=ft.FontWeight.BOLD if int(self.daily_budget) == b else ft.FontWeight.W_500, color=ft.Colors.WHITE if int(self.daily_budget) == b else ThemeColors.TEXT_MAIN_LIGHT),
                bgcolor=ThemeColors.PRIMARY_BLUE if int(self.daily_budget) == b else ThemeColors.SURFACE_LIGHT,
                border=ft.Border.all(1, ThemeColors.PRIMARY_BLUE if int(self.daily_budget) == b else ThemeColors.BORDER_LIGHT),
                border_radius=14,
                padding=ft.Padding.symmetric(horizontal=14, vertical=6),
                ink=True,
                on_click=lambda _, val=b: self._set_budget_preset(val, budget_input),
            )
            for b in budget_presets
        ]

        pref_options = [
            ("nature", "Nature & Parks"),
            ("food", "Food Trip"),
            ("culture", "Culture & History"),
            ("shopping", "Shopping"),
            ("resort", "Resort"),
        ]
        pref_chips = []
        for p_key, p_lbl in pref_options:
            is_p = p_key in self.preferences
            pref_chips.append(
                ft.Container(
                    content=ft.Text(p_lbl, size=11, weight=ft.FontWeight.BOLD if is_p else ft.FontWeight.W_500, color=ft.Colors.WHITE if is_p else ThemeColors.TEXT_MAIN_LIGHT),
                    bgcolor=ThemeColors.PRIMARY_BLUE if is_p else ThemeColors.SURFACE_LIGHT,
                    border=ft.Border.all(1, ThemeColors.PRIMARY_BLUE if is_p else ThemeColors.BORDER_LIGHT),
                    border_radius=14,
                    padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                    ink=True,
                    on_click=lambda _, pk=p_key: self._toggle_pref(pk),
                )
            )

        start_btn = ft.Container(
            content=ft.Text("Start Building Itinerary →", size=15, weight=ft.FontWeight.W_700, color=ft.Colors.WHITE),
            bgcolor=ThemeColors.PRIMARY_BLUE,
            border_radius=10,
            height=48,
            alignment=ft.Alignment(0, 0),
            ink=True,
            on_click=lambda _: self._start_building(),
        )

        form_card = ft.Container(
            width=640,
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
            border_radius=18,
            padding=24,
            content=ft.Column(
                controls=[
                    heading,
                    ft.Container(height=8),
                    title_input,
                    dest_picker,
                    ft.Column(controls=[ft.Text("Travel Dates", size=12, weight=ft.FontWeight.BOLD), date_btn, date_helper], spacing=4),
                    ft.Column(controls=[budget_input, ft.Row(controls=budget_chips, spacing=8)], spacing=6),
                    ft.Column(controls=[ft.Text("Preferences (optional)", size=12, weight=ft.FontWeight.BOLD), ft.Row(controls=pref_chips, wrap=True, spacing=6)], spacing=6),
                    ft.Container(height=6),
                    start_btn,
                ],
                spacing=12,
            ),
        )

        return ft.Column(
            controls=[form_card],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def _start_building(self) -> None:
        self.sync_days_with_date_range()
        self.active_view = "browse"
        self._build_content()
        self._safe_update()

    def _open_date_picker(self) -> None:
        def _apply(s: str, e: str):
            try:
                s_d = datetime.strptime(s, "%Y-%m-%d").date()
                e_d = datetime.strptime(e, "%Y-%m-%d").date()
                new_days_count = max(1, (e_d - s_d).days + 1)
            except Exception:
                new_days_count = len(self.days)

            # UC-C03: Shortening Date Range Guard
            if new_days_count < len(self.days):
                lost_stops = sum(len(d.items) for d in self.days[new_days_count:])
                if lost_stops > 0:
                    def _confirm_shorten(_):
                        dlg.open = False
                        if self.safe_page:
                            self.safe_page.update()
                        self.start_date_str = s
                        self.end_date_str = e
                        self.sync_days_with_date_range()
                        self.is_dirty = True
                        self._build_content()
                        self._safe_update()

                    def _cancel_shorten(_):
                        dlg.open = False
                        if self.safe_page:
                            self.safe_page.update()

                    dlg = ft.AlertDialog(
                        title=ft.Text("Shorten Trip Duration?", size=18, weight=ft.FontWeight.BOLD),
                        content=ft.Text(f"Reducing to {new_days_count} days will discard {lost_stops} scheduled stop(s) on trailing days.", size=13),
                        actions=[
                            ft.TextButton("Cancel", on_click=_cancel_shorten),
                            ft.FilledButton("Discard & Shorten", style=ft.ButtonStyle(bgcolor=ThemeColors.ERROR, color=ft.Colors.WHITE), on_click=_confirm_shorten),
                        ],
                    )
                    if self.safe_page:
                        self.safe_page.overlay.append(dlg)
                        dlg.open = True
                        self.safe_page.update()
                    return

            self.start_date_str = s
            self.end_date_str = e
            self.sync_days_with_date_range()
            self.is_dirty = True
            self._build_content()
            self._safe_update()

        if self.safe_page:
            show_date_range_dialog(
                self.safe_page,
                initial_start=self.start_date_str,
                initial_end=self.end_date_str,
                on_apply=_apply,
            )

    # =========================================================================
    # VIEW 1: BROWSE & ADD PLACES ('browse' — UC-C04 to UC-C06)
    # =========================================================================
    def _build_browse_view(self) -> ft.Control:
        heading = ft.Text(
            "Add the places you want to visit",
            size=18,
            weight=ft.FontWeight.W_800,
            color=ThemeColors.TEXT_BLACK,
        )

        # Target Day Selector Bar
        day_chips: list[ft.Control] = []
        for idx, day in enumerate(self.days):
            is_sel = idx == self.active_day_index
            day_chips.append(
                ft.Container(
                    content=ft.Text(
                        f"Day {day.day_number} ({len(day.items)})",
                        size=11,
                        weight=ft.FontWeight.BOLD if is_sel else ft.FontWeight.W_500,
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
                ft.Row(controls=day_chips, spacing=6, scroll=ft.ScrollMode.AUTO),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        search_field = ft.TextField(
            hint_text="Search attractions, restaurants, resorts...",
            prefix_icon=ft.Icons.SEARCH,
            value=self.browse_search,
            border_radius=10,
            dense=True,
            expand=True,
            on_change=lambda e: self._on_browse_search_live(e.control.value),
        )

        # Category Filter Pills with "Other" (UC-C05)
        cats = [("all", "All")]
        if self.preferences:
            cats.append(("recommended", "✨ Recommended for You"))
        cats.extend([
            ("tourist_spots", "Tourist Spots"),
            ("food", "Food"),
            ("resorts_stays", "Resorts & Stays"),
            ("culture_heritage", "Culture & Heritage"),
            ("shopping", "Shopping"),
            ("transit_essentials", "Transit & Essentials"),
            ("other", "Other"),
        ])

        cat_chips = []
        for c_key, c_label in cats:
            is_act = self.browse_category == c_key
            cat_chips.append(
                ft.Container(
                    content=ft.Text(
                        c_label,
                        size=11,
                        weight=ft.FontWeight.BOLD if is_act else ft.FontWeight.W_500,
                        color=ft.Colors.WHITE if is_act else ThemeColors.TEXT_MAIN_LIGHT,
                    ),
                    bgcolor=ThemeColors.PRIMARY_BLUE if is_act else ThemeColors.SURFACE_LIGHT,
                    border=ft.Border.all(1, ThemeColors.PRIMARY_BLUE if is_act else ThemeColors.BORDER_LIGHT),
                    border_radius=12,
                    padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                    ink=True,
                    on_click=lambda _, k=c_key: self._on_browse_cat_change(k),
                )
            )

        cards_grid = self._build_browse_cards_grid()
        self._browse_results_col = cards_grid

        bottom_bar = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(f"{self.total_stops_count} total places scheduled across {len(self.days)} days", size=12, weight=ft.FontWeight.W_600),
                    ft.FilledButton(
                        content=f"View my Itinerary ({self.total_stops_count} {'place' if self.total_stops_count == 1 else 'places'}) →",
                        style=ft.ButtonStyle(bgcolor=ThemeColors.PRIMARY_BLUE, color=ft.Colors.WHITE),
                        on_click=lambda _: self._switch_view("timeline"),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
            border_radius=12,
            padding=ft.Padding.symmetric(horizontal=20, vertical=10),
            margin=ft.Margin.only(top=10),
        )

        return ft.Column(
            controls=[
                heading,
                ft.Container(height=6),
                target_day_bar,
                ft.Container(height=8),
                search_field,
                ft.Container(height=4),
                ft.Row(controls=cat_chips, spacing=6, scroll=ft.ScrollMode.AUTO),
                ft.Container(height=10),
                cards_grid,
                bottom_bar,
            ],
            spacing=0,
            expand=True,
        )

    def _build_browse_cards_grid(self) -> ft.Control:
        active_day = self.days[self.active_day_index] if self.days else None
        added_place_ids = {it.place_id for it in active_day.items} if active_day else set()

        all_places = self.place_service.get_loaded_places()
        if not all_places:
            from desktop_client.core.offline_data import get_all_offline_places
            all_places = [Place.from_dict(p) for p in get_all_offline_places()]

        q = (self.browse_search or "").strip().lower()
        cat = self.browse_category or "all"

        CATEGORY_GROUPS = {
            "tourist_spots": {"tourist_attraction", "nature_park", "historical_landmark", "park", "viewpoint", "attraction"},
            "food": {"restaurant", "cafe", "fast_food", "bakery", "food_court", "dining"},
            "resorts_stays": {"resort_swimming", "hotel_lodging", "stay", "resort", "hotel", "hotel_accommodation"},
            "culture_heritage": {"museum_cultural", "church_religious", "historical_landmark", "monument", "culture"},
            "shopping": {"shopping_market", "convenience_store", "market", "gift_shop", "mall", "supermarket"},
            "transit_essentials": {"gas_station", "bus_station", "transport_terminal", "hospital_clinic", "bank_atm", "transit", "emergency", "pharmacy", "fuel_station", "public_facility"},
        }
        all_known_cats = set().union(*CATEGORY_GROUPS.values())

        matched: list[Place] = []
        for p in all_places:
            if q:
                if not (q in (p.name or "").lower() or q in (p.municipality_name or "").lower() or q in (p.category or "").lower() or q in (p.description or "").lower()):
                    continue

            p_cat = (p.category or "").lower()
            if cat == "all":
                pass
            elif cat == "recommended":
                pref_set = set(self.preferences)
                if not any(pref in p_cat for pref in pref_set):
                    continue
            elif cat == "other":
                if p_cat in all_known_cats or any(k in p_cat for k in all_known_cats):
                    continue
            elif cat in CATEGORY_GROUPS:
                allowed = CATEGORY_GROUPS[cat]
                if p_cat not in allowed and not any(a in p_cat for a in allowed):
                    continue
            matched.append(p)

        if not matched:
            return ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.SEARCH_OFF, size=38, color=ThemeColors.TEXT_MUTED_LIGHT),
                        ft.Text("No destinations found", size=14, weight=ft.FontWeight.BOLD),
                        ft.FilledButton("Reset Filters", on_click=lambda _: self._reset_browse_filters()),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                ),
                padding=40,
                alignment=ft.Alignment(0, 0),
            )

        cards = [self._build_place_grid_card(p, p.id in added_place_ids) for p in matched[:60]]
        return ft.Container(
            content=ft.ResponsiveRow(
                controls=[ft.Container(content=c, col={"sm": 12, "md": 6, "lg": 4}) for c in cards],
                spacing=12,
                run_spacing=12,
            ),
            expand=True,
        )

    def _build_place_grid_card(self, place: Place, is_added: bool) -> ft.Control:
        action_btn = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.CHECK if is_added else ft.Icons.ADD, size=13, color=ft.Colors.WHITE if is_added else ThemeColors.PRIMARY_BLUE),
                    ft.Text("Added" if is_added else "Add", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE if is_added else ThemeColors.PRIMARY_BLUE),
                ],
                spacing=3,
                tight=True,
            ),
            bgcolor=ThemeColors.SUCCESS if is_added else ThemeColors.AZURE_SOFT,
            border=ft.Border.all(1, ThemeColors.SUCCESS if is_added else ThemeColors.PRIMARY_BLUE),
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=10, vertical=5),
            ink=True,
            on_click=lambda _: self._toggle_place_in_active_day(place),
        )

        return ft.Container(
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
            border_radius=12,
            padding=10,
            ink=True,
            on_click=lambda _: show_place_detail_dialog(
                self.safe_page,
                place,
                on_navigate=self.on_navigate,
                on_add_to_day=lambda pl: self._toggle_place_in_active_day(pl),
            ) if self.safe_page else None,
            content=ft.Row(
                controls=[
                    ft.Image(
                        src=place.resolved_image_path,
                        width=74,
                        height=64,
                        fit=ft.BoxFit.COVER,
                        border_radius=8,
                        error_content=ft.Icon(ft.Icons.LANDSCAPE, size=24, color=ThemeColors.PRIMARY_BLUE),
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(place.name, size=13, weight=ft.FontWeight.W_700, color=ThemeColors.TEXT_BLACK, max_lines=1),
                            ft.Text(f"{place.municipality_name or 'Nueva Ecija'}, Nueva Ecija", size=11, color=ThemeColors.TEXT_MUTED_LIGHT),
                            ft.Row(
                                controls=[
                                    ft.Text(place.formatted_cost, size=11, weight=ft.FontWeight.BOLD, color=ThemeColors.EMERALD_PRIMARY),
                                    ft.Container(expand=True),
                                    action_btn,
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                ],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def _reset_browse_filters(self) -> None:
        self.browse_search = ""
        self.browse_category = "all"
        self._build_content()
        self._safe_update()

    def _clear_browse_search(self) -> None:
        self.browse_search = ""
        self._build_content()
        self._safe_update()

    def _on_browse_search_live(self, val: str) -> None:
        self.browse_search = val
        self._build_content()
        self._safe_update()

    def _on_browse_cat_change(self, cat: str) -> None:
        self.browse_category = cat
        self._build_content()
        self._safe_update()

    # =========================================================================
    # VIEW 2: TIMELINE VIEW ('timeline' — UC-C07 to UC-C13)
    # =========================================================================
    def _build_timeline_view(self) -> ft.Control:
        active_day = self.days[self.active_day_index] if self.days else None
        num_days = len(self.days) if self.days else 1

        # UC-C07: Pre-Arrival Dismissible Banner
        pre_loaded_banner = ft.Container()
        if self.pre_added_place and not self.banner_dismissed:
            pre_loaded_banner = ft.Container(
                bgcolor=ThemeColors.AZURE_SOFT,
                border=ft.Border.all(1, ThemeColors.CUSTOM_CARD_BORDER),
                border_radius=10,
                padding=ft.Padding.symmetric(horizontal=12, vertical=8),
                margin=ft.Margin.only(bottom=10),
                content=ft.Row(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text("✨", size=14),
                                ft.Text(
                                    f"Place Pre-Loaded — {self.pre_added_place.name} was automatically added to Day 1 of your trip.",
                                    size=12,
                                    weight=ft.FontWeight.W_600,
                                    color=ThemeColors.PRIMARY_BLUE,
                                ),
                            ],
                            spacing=6,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.CLOSE,
                            icon_size=16,
                            icon_color=ThemeColors.PRIMARY_BLUE,
                            on_click=lambda _: self._dismiss_pre_loaded_banner(),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            )

        # UC-C08: 2-Row .trip-settings-card
        title_tf = ft.TextField(
            value=self.trip_title,
            label="Trip Title",
            dense=True,
            border_radius=8,
            expand=True,
            on_change=lambda e: setattr(self, "trip_title", e.control.value),
        )
        budget_tf = ft.TextField(
            value=str(int(self.daily_budget)),
            label="Daily Budget (₱)",
            prefix=ft.Text("₱ "),
            dense=True,
            border_radius=8,
            width=160,
            on_change=lambda e: self._on_budget_change(e.control.value),
        )

        date_range_str, _ = self._format_date_range_display(self.start_date_str, self.end_date_str)
        date_chip = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.CALENDAR_MONTH, size=14, color=ThemeColors.PRIMARY_BLUE),
                    ft.Text(date_range_str, size=11, weight=ft.FontWeight.BOLD),
                ],
                spacing=4,
            ),
            bgcolor=ThemeColors.AZURE_SOFT,
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=10, vertical=8),
            ink=True,
            on_click=lambda _: self._open_date_picker(),
        )
        dest_chip = DestinationPicker(value=self.destination, on_change=lambda val: setattr(self, "destination", val))

        settings_card = ft.Container(
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
            border_radius=12,
            padding=12,
            margin=ft.Margin.only(bottom=8),
            content=ft.Column(
                controls=[
                    ft.Row(controls=[title_tf, budget_tf], spacing=10),
                    ft.Row(controls=[date_chip, dest_chip], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ],
                spacing=8,
            ),
        )

        # UC-C08: Verified Estimated Costs Card
        itin_temp = Itinerary(
            id="draft",
            title=self.trip_title,
            destination=self.destination,
            start_date=self.start_date_str,
            end_date=self.end_date_str,
            daily_budget=self.daily_budget,
            days=self.days,
        )
        budget_summary = self.itinerary_service.calculate_budget_summary(itin_temp)
        unpriced = budget_summary.get("unpriced_count", 0)

        verified_costs_card = ft.Container(
            bgcolor="#f0fdf4",
            border=ft.Border.all(1, "#bbf7d0"),
            border_radius=12,
            padding=12,
            margin=ft.Margin.only(bottom=10),
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text("🛡️ Verified Estimated Costs", size=12, weight=ft.FontWeight.BOLD, color="#166534"),
                            ft.Text(f"Budget: ₱{self.daily_budget:,.0f}/day (₱{self.daily_budget * num_days:,.0f} total for {num_days} days)", size=11, color="#166534"),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Text(budget_summary.get("display_text", "Free Admission"), size=16, weight=ft.FontWeight.W_800, color="#15803d"),
                    ft.Text(f"* {unpriced} stop(s) do not list verified pricing in open public records." if unpriced > 0 else "All stops have verified open pricing.", size=10, color="#166534", italic=True),
                ],
                spacing=4,
            ),
        )

        # UC-C09: 2-Line Day Tabs Bar
        day_buttons: list[ft.Control] = []
        for idx, day in enumerate(self.days):
            is_act = idx == self.active_day_index
            muni_name = "Nueva Ecija"
            if day.items and day.items[0].place and day.items[0].place.municipality_name:
                muni_name = day.items[0].place.municipality_name
            day_buttons.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text(f"Day {day.day_number}", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE if is_act else ThemeColors.TEXT_BLACK),
                            ft.Text(muni_name, size=9, color=ft.Colors.WHITE if is_act else ThemeColors.TEXT_MUTED_LIGHT),
                        ],
                        spacing=1,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    bgcolor=ThemeColors.PRIMARY_BLUE if is_act else ft.Colors.WHITE,
                    border=ft.Border.all(1, ThemeColors.PRIMARY_BLUE if is_act else ThemeColors.BORDER_LIGHT),
                    border_radius=10,
                    padding=ft.Padding.symmetric(horizontal=14, vertical=6),
                    ink=True,
                    on_click=lambda _, i=idx: self._set_target_day(i),
                )
            )
        day_buttons.append(
            ft.IconButton(icon=ft.Icons.ADD_CIRCLE_OUTLINE, icon_size=18, icon_color=ThemeColors.PRIMARY_BLUE, tooltip="Add Day", on_click=self._add_new_day)
        )
        day_bar = ft.Row(controls=day_buttons, spacing=6, scroll=ft.ScrollMode.AUTO)

        # UC-C09: Active Day Header Actions
        active_day_muni = "Nueva Ecija"
        if active_day and active_day.items and active_day.items[0].place and active_day.items[0].place.municipality_name:
            active_day_muni = active_day.items[0].place.municipality_name

        header_actions = []
        if active_day and len(active_day.items) > 1:
            header_actions.append(
                ft.FilledButton(
                    content="🕒 Auto-Schedule",
                    style=ft.ButtonStyle(bgcolor=ThemeColors.AZURE_SOFT, color=ThemeColors.PRIMARY_BLUE),
                    on_click=self._auto_schedule_active_day,
                )
            )
        if len(self.days) > 1:
            header_actions.append(
                ft.OutlinedButton(
                    content="🗑 Delete Day",
                    style=ft.ButtonStyle(color=ThemeColors.ERROR),
                    on_click=self._delete_active_day,
                )
            )

        active_day_header = ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text(f"Day {active_day.day_number if active_day else 1} - {active_day_muni}", size=16, weight=ft.FontWeight.W_800, color=ThemeColors.TEXT_BLACK),
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.CALENDAR_TODAY, size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                                ft.Text(f"{active_day.travel_date if active_day else ''} ({len(active_day.items) if active_day else 0} stops)", size=11, color=ThemeColors.TEXT_MUTED_LIGHT),
                            ],
                            spacing=4,
                        ),
                    ],
                    spacing=2,
                ),
                ft.Row(controls=header_actions, spacing=6),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        route_map = ItineraryRouteMap(day=active_day, on_view_full_map=lambda: self._open_full_map_draft(), height_expanded=220)

        # UC-C10 & UC-C11: Stop Cards or Empty Day Box
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
                        is_first=(idx == 0),
                        is_last=(idx == len(active_day.items) - 1),
                        editable=True,
                        on_move_up=lambda it=item: self._move_stop(it, -1),
                        on_move_down=lambda it=item: self._move_stop(it, 1),
                        on_edit=lambda it=item: self._open_edit_stop_dialog(it),
                        on_delete=lambda it=item: self._confirm_remove_stop(it),
                        on_click=lambda itm: show_place_detail_dialog(self.safe_page, itm.place, on_navigate=self.on_navigate) if (itm.place and self.safe_page) else None,
                    )
                )
        else:
            # UC-C11: .day-empty-stops-box
            timeline_items.append(
                ft.Container(
                    bgcolor=ft.Colors.WHITE,
                    border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
                    border_radius=12,
                    padding=24,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.SCHEDULE, size=32, color=ThemeColors.PRIMARY_BLUE),
                            ft.Text("No stops scheduled yet", size=14, weight=ft.FontWeight.BOLD),
                            ft.Text("Add places from the destination catalog or add your own off-grid custom venue.", size=12, color=ThemeColors.TEXT_MUTED_LIGHT, text_align=ft.TextAlign.CENTER),
                            ft.FilledButton(
                                f"+ Browse & Add Places to Day {active_day.day_number if active_day else 1}",
                                style=ft.ButtonStyle(bgcolor=ThemeColors.PRIMARY_BLUE, color=ft.Colors.WHITE),
                                on_click=lambda _: self._switch_view("browse"),
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                    ),
                )
            )

        bottom_add_row = ft.Row(
            controls=[
                ft.FilledButton(
                    content=f"+ Browse & Add Places to Day {active_day.day_number if active_day else 1}",
                    style=ft.ButtonStyle(bgcolor=ThemeColors.PRIMARY_BLUE, color=ft.Colors.WHITE),
                    on_click=lambda _: self._switch_view("browse"),
                ),
                ft.OutlinedButton(
                    content="🏢 Add Off-Grid Custom Venue",
                    on_click=lambda _: self._open_custom_venue_dialog(),
                ),
            ],
            spacing=10,
        )

        # UC-C13: Save Footer CTA
        can_save = self.total_stops_count > 0 and not self.is_saving
        footer_cta = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(f"Total: {self.total_stops_count} places • ~₱{sum(d.total_day_cost for d in self.days):,.0f} estimated cost", size=12, weight=ft.FontWeight.BOLD),
                    ft.FilledButton(
                        content="💾 View Full Itinerary / Save Trip",
                        style=ft.ButtonStyle(bgcolor=ThemeColors.SUCCESS if can_save else "#94a3b8", color=ft.Colors.WHITE),
                        disabled=not can_save,
                        on_click=lambda _: self._save_custom_itinerary(),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
            border_radius=12,
            padding=ft.Padding.symmetric(horizontal=16, vertical=10),
            margin=ft.Margin.only(top=10),
        )

        return ft.Column(
            controls=[
                pre_loaded_banner,
                settings_card,
                verified_costs_card,
                day_bar,
                ft.Container(height=8),
                active_day_header,
                ft.Container(height=6),
                route_map,
                ft.Container(height=8),
                ft.Column(controls=timeline_items, spacing=4),
                ft.Container(height=10),
                bottom_add_row,
                footer_cta,
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=0,
            expand=True,
        )

    def _dismiss_pre_loaded_banner(self) -> None:
        self.banner_dismissed = True
        self._build_content()
        self._safe_update()

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
        existing_item = next((it for it in day.items if it.place_id == place.id), None)

        if existing_item is not None:
            # UC-C06: prompt confirmation when removing via [✓ Added]
            self._confirm_remove_stop(existing_item)
        else:
            time_str = self._calc_next_time(day, next_place=place)
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
            self.is_dirty = True
            self._build_content()
            self._safe_update()

    def _calc_next_time(self, day: ItineraryDay, next_place: Optional[Place] = None) -> str:
        if not day.items:
            return "09:00 AM"

        last_item = day.items[-1]
        raw_time = (last_item.planned_time or "09:00 AM").strip()
        end_dt = datetime.strptime("10:30 AM", "%I:%M %p")
        if " - " in raw_time:
            end_str = raw_time.split(" - ")[-1].strip()
            for fmt in ("%I:%M %p", "%H:%M", "%I:%M%p"):
                try:
                    end_dt = datetime.strptime(end_str, fmt)
                    break
                except Exception:
                    pass
        next_start = end_dt + timedelta(minutes=30)
        return next_start.strftime("%I:%M %p")

    def _move_stop(self, item: ItineraryItem, delta: int) -> None:
        day = self.days[self.active_day_index]
        idx = day.items.index(item)
        new_idx = idx + delta
        if 0 <= new_idx < len(day.items):
            day.items[idx], day.items[new_idx] = day.items[new_idx], day.items[idx]
            for i, itm in enumerate(day.items):
                itm.sort_order = i + 1
            self.is_dirty = True
            self._auto_schedule_active_day()

    def _confirm_remove_stop(self, item: ItineraryItem) -> None:
        """Prompts Remove Stop? confirmation dialog (UC-C10)."""
        day = self.days[self.active_day_index]
        stop_name = item.custom_title or (item.place.name if item.place else "Stop")

        def _do_remove(_):
            dlg.open = False
            if self.safe_page:
                self.safe_page.update()
            if item in day.items:
                day.items.remove(item)
                for i, itm in enumerate(day.items):
                    itm.sort_order = i + 1
                self.is_dirty = True
                self._build_content()
                self._safe_update()

        def _cancel(_):
            dlg.open = False
            if self.safe_page:
                self.safe_page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Remove Stop?", size=18, weight=ft.FontWeight.BOLD),
            content=ft.Text(f'Are you sure you want to remove "{stop_name}" from Day {day.day_number}?', size=13),
            actions=[
                ft.TextButton("Cancel", on_click=_cancel),
                ft.FilledButton("Remove", style=ft.ButtonStyle(bgcolor=ThemeColors.ERROR, color=ft.Colors.WHITE), on_click=_do_remove),
            ],
        )
        if self.safe_page:
            self.safe_page.overlay.append(dlg)
            dlg.open = True
            self.safe_page.update()

    def _open_edit_stop_dialog(self, item: ItineraryItem) -> None:
        """Edit stop modal with Move to Day dropdown reindexing both source and target days (UC-C10)."""
        time_field = ft.TextField(label="Planned Time", value=item.planned_time or "09:00 AM", dense=True)
        dur_field = ft.TextField(label="Duration (mins)", value=str(item.duration_minutes or 90), dense=True)
        notes_field = ft.TextField(label="Personal Travel Notes", value=item.notes or "", dense=True, multiline=True)
        cost_min_field = ft.TextField(
            label="Est. Min Cost (₱)",
            value=str(int(item.estimated_cost_min)) if item.estimated_cost_min is not None else "",
            dense=True,
            prefix=ft.Text("₱ "),
        )
        cost_max_field = ft.TextField(
            label="Est. Max Cost (₱)",
            value=str(int(item.estimated_cost_max)) if item.estimated_cost_max is not None else "",
            dense=True,
            prefix=ft.Text("₱ "),
        )

        day_options = [ft.dropdown.Option(str(d.day_number), f"Day {d.day_number} — {d.travel_date} (Day {d.day_number})") for d in self.days]
        source_day = self.days[self.active_day_index]
        day_dropdown = ft.Dropdown(
            label="Scheduled Day (Move Stop)",
            options=day_options,
            value=str(source_day.day_number),
            dense=True,
        )

        def _close_dlg(_=None):
            dlg.open = False
            if self.safe_page:
                self.safe_page.update()

        def _save_edit(_):
            c_min = None
            c_max = None
            try:
                if cost_min_field.value.strip():
                    c_min = float(cost_min_field.value.strip())
                if cost_max_field.value.strip():
                    c_max = float(cost_max_field.value.strip())
            except ValueError:
                return

            item.planned_time = time_field.value.strip()
            try:
                item.duration_minutes = int(dur_field.value.strip())
            except ValueError:
                pass
            item.notes = notes_field.value.strip()
            item.estimated_cost_min = c_min
            item.estimated_cost_max = c_max

            target_day_num = int(day_dropdown.value)
            if target_day_num != source_day.day_number:
                source_day.items.remove(item)
                for i, itm in enumerate(source_day.items):
                    itm.sort_order = i + 1
                target_day = next(d for d in self.days if d.day_number == target_day_num)
                item.sort_order = len(target_day.items) + 1
                target_day.items.append(item)
                target_idx = self.days.index(target_day)
                self.active_day_index = target_idx

            self.is_dirty = True
            _close_dlg()
            self._build_content()
            self._safe_update()

        dlg = ft.AlertDialog(
            title=ft.Text(f"Edit Scheduled Stop: {item.custom_title or (item.place.name if item.place else 'Stop')}"),
            content=ft.Column(
                controls=[day_dropdown, time_field, dur_field, ft.Row(controls=[cost_min_field, cost_max_field], spacing=8), notes_field],
                tight=True,
                spacing=8,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=_close_dlg),
                ft.FilledButton("Save Changes", on_click=_save_edit),
            ],
        )
        if self.safe_page:
            self.safe_page.overlay.append(dlg)
            dlg.open = True
            self.safe_page.update()

    # UC-C12: 2-Tab Place Picker & Off-Grid Venue Modal with Duplicate Guard & Collapsible Coordinates
    def _open_custom_venue_dialog(self) -> None:
        active_tab = ["browse"]  # 'browse' | 'offgrid'
        dlg_holder: list[Optional[ft.AlertDialog]] = [None]
        active_day = self.days[self.active_day_index]

        def _update_dlg_content():
            if dlg_holder[0] is not None and getattr(dlg_holder[0], "content", None):
                try:
                    dlg_holder[0].content.update()
                except Exception:
                    pass

        # Tab 1: Browse Places with Duplicate Guard
        b_search = ft.TextField(hint_text="Search destinations...", dense=True, prefix_icon=ft.Icons.SEARCH)
        places_list_col = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO, height=260)

        def _refresh_browse_list():
            q = (b_search.value or "").strip().lower()
            all_p = self.place_service.get_loaded_places()
            if not all_p:
                from desktop_client.core.offline_data import get_all_offline_places
                all_p = [Place.from_dict(p) for p in get_all_offline_places()]
            matching = [p for p in all_p if not q or q in p.name.lower() or q in (p.municipality_name or "").lower()][:30]

            items = []
            for pl in matching:
                def _pick_place(_, p_target=pl):
                    # Duplicate check
                    if any(it.place_id == p_target.id for it in active_day.items):
                        def _confirm_dup(_):
                            dup_dlg.open = False
                            if self.safe_page:
                                self.safe_page.update()
                            self._add_place_direct(p_target)
                            _close_main()

                        def _cancel_dup(_):
                            dup_dlg.open = False
                            if self.safe_page:
                                self.safe_page.update()

                        dup_dlg = ft.AlertDialog(
                            title=ft.Text("Duplicate Destination", size=18, weight=ft.FontWeight.BOLD),
                            content=ft.Text(f'"{p_target.name}" is already scheduled for Day {active_day.day_number}. Would you still like to add another stop here?', size=13),
                            actions=[
                                ft.TextButton("Cancel", on_click=_cancel_dup),
                                ft.FilledButton("Add Stop", on_click=_confirm_dup),
                            ],
                        )
                        if self.safe_page:
                            self.safe_page.overlay.append(dup_dlg)
                            dup_dlg.open = True
                            self.safe_page.update()
                        return

                    self._add_place_direct(p_target)
                    _close_main()

                items.append(
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Column(
                                    controls=[
                                        ft.Text(pl.name, size=13, weight=ft.FontWeight.BOLD),
                                        ft.Text(f"{pl.municipality_name or 'Nueva Ecija'} • {pl.formatted_category}", size=11, color=ThemeColors.TEXT_MUTED_LIGHT),
                                    ],
                                    spacing=1,
                                    expand=True,
                                ),
                                ft.FilledButton("Add", on_click=_pick_place),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        bgcolor="#f8fafc",
                        border_radius=8,
                        padding=8,
                    )
                )
            places_list_col.controls = items
            try:
                places_list_col.update()
            except Exception:
                pass

        b_search.on_change = lambda _: _refresh_browse_list()

        # Tab 2: Off-Grid Custom Venue
        name_field = ft.TextField(label="Place or Venue Name *", dense=True)
        muni_field = ft.TextField(label="Municipality or Address", dense=True)
        cost_min_field = ft.TextField(label="Est. Min Cost (₱)", prefix=ft.Text("₱ "), dense=True)
        cost_max_field = ft.TextField(label="Est. Max Cost (₱)", prefix=ft.Text("₱ "), dense=True)
        time_field = ft.TextField(label="Planned Time", value=self._calc_next_time(active_day), dense=True)
        dur_field = ft.TextField(label="Duration (mins)", value="90", dense=True)
        notes_field = ft.TextField(label="Personal Travel Notes", multiline=True, dense=True)

        coords_expanded = [False]
        lat_field = ft.TextField(label="Latitude (15.15 - 16.15)", hint_text="15.58", dense=True)
        lng_field = ft.TextField(label="Longitude (120.70 - 121.40)", hint_text="121.00", dense=True)
        coords_col = ft.Column(controls=[ft.Row(controls=[lat_field, lng_field], spacing=8)], visible=False)

        def _toggle_coords(_):
            coords_expanded[0] = not coords_expanded[0]
            coords_col.visible = coords_expanded[0]
            coords_toggle_btn.text = "Hide Coordinates ▲" if coords_expanded[0] else "Pin Coordinates (Lat / Lng) — Optional ▼"
            _update_dlg_content()

        coords_toggle_btn = ft.TextButton("Pin Coordinates (Lat / Lng) — Optional ▼", on_click=_toggle_coords)
        err_text = ft.Text("", size=11, color=ThemeColors.ERROR, visible=False)

        tab_body = ft.Container()

        def _switch_tab(t_name: str):
            active_tab[0] = t_name
            t1_btn.bgcolor = ThemeColors.PRIMARY_BLUE if t_name == "browse" else ThemeColors.SURFACE_LIGHT
            t1_btn.content.color = ft.Colors.WHITE if t_name == "browse" else ThemeColors.TEXT_MAIN_LIGHT
            t2_btn.bgcolor = ThemeColors.PRIMARY_BLUE if t_name == "offgrid" else ThemeColors.SURFACE_LIGHT
            t2_btn.content.color = ft.Colors.WHITE if t_name == "offgrid" else ThemeColors.TEXT_MAIN_LIGHT

            if t_name == "browse":
                _refresh_browse_list()
                tab_body.content = ft.Column(controls=[b_search, places_list_col], spacing=8)
            else:
                tab_body.content = ft.Column(
                    controls=[
                        name_field,
                        muni_field,
                        ft.Row(controls=[cost_min_field, cost_max_field], spacing=8),
                        ft.Row(controls=[time_field, dur_field], spacing=8),
                        coords_toggle_btn,
                        coords_col,
                        notes_field,
                        err_text,
                    ],
                    spacing=8,
                )
            _update_dlg_content()

        t1_btn = ft.Container(
            content=ft.Text("🔍 Browse Places", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            bgcolor=ThemeColors.PRIMARY_BLUE,
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=14, vertical=6),
            ink=True,
            on_click=lambda _: _switch_tab("browse"),
        )
        t2_btn = ft.Container(
            content=ft.Text("✏️ Off-Grid Venue", size=12, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_MAIN_LIGHT),
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=14, vertical=6),
            ink=True,
            on_click=lambda _: _switch_tab("offgrid"),
        )

        def _close_main(_=None):
            dlg.open = False
            if self.safe_page:
                self.safe_page.update()

        def _save_offgrid(_):
            name = name_field.value.strip()
            if not name:
                err_text.value = "Place or Venue Name is required."
                err_text.visible = True
                _update_dlg_content()
                return

            c_min = None
            c_max = None
            try:
                if cost_min_field.value.strip():
                    c_min = float(cost_min_field.value.strip())
                if cost_max_field.value.strip():
                    c_max = float(cost_max_field.value.strip())
            except ValueError:
                err_text.value = "Costs must be valid numbers."
                err_text.visible = True
                _update_dlg_content()
                return

            lat = None
            lng = None
            if lat_field.value.strip() or lng_field.value.strip():
                try:
                    lat = float(lat_field.value.strip())
                    lng = float(lng_field.value.strip())
                    if not (15.15 <= lat <= 16.15 and 120.70 <= lng <= 121.40):
                        err_text.value = "Coordinates outside Nueva Ecija (Lat 15.15–16.15, Lng 120.70–121.40)."
                        err_text.visible = True
                        _update_dlg_content()
                        return
                except ValueError:
                    err_text.value = "Please enter valid numeric coordinates."
                    err_text.visible = True
                    _update_dlg_content()
                    return

            try:
                dur = int(dur_field.value.strip())
            except ValueError:
                dur = 90

            item = ItineraryItem(
                id=str(uuid.uuid4()),
                day_id=active_day.id,
                custom_title=name,
                sort_order=len(active_day.items) + 1,
                planned_time=time_field.value.strip() or self._calc_next_time(active_day),
                duration_minutes=dur,
                estimated_cost_min=c_min,
                estimated_cost_max=c_max,
                notes=notes_field.value.strip() or None,
                custom_lat=lat,
                custom_lng=lng,
            )
            active_day.items.append(item)
            self.is_dirty = True
            _close_main()
            self._build_content()
            self._safe_update()

        _switch_tab("browse")

        dlg = ft.AlertDialog(
            title=ft.Row(
                controls=[
                    ft.Text("Add Destination / Venue", size=18, weight=ft.FontWeight.BOLD),
                    ft.IconButton(icon=ft.Icons.CLOSE, on_click=_close_main),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            content=ft.Container(
                width=500,
                content=ft.Column(
                    controls=[
                        ft.Row(controls=[t1_btn, t2_btn], spacing=8),
                        ft.Divider(height=1),
                        tab_body,
                    ],
                    spacing=8,
                    tight=True,
                ),
            ),
            actions=[
                ft.TextButton("Cancel", on_click=_close_main),
                ft.FilledButton("+ Add to Day", on_click=lambda _: _save_offgrid(None) if active_tab[0] == "offgrid" else None),
            ],
        )
        dlg_holder[0] = dlg
        if self.safe_page:
            self.safe_page.overlay.append(dlg)
            dlg.open = True
            self.safe_page.update()

    def _add_place_direct(self, place: Place) -> None:
        day = self.days[self.active_day_index]
        item = ItineraryItem(
            id=str(uuid.uuid4()),
            day_id=day.id,
            place_id=place.id,
            place=place,
            custom_title=place.name,
            sort_order=len(day.items) + 1,
            planned_time=self._calc_next_time(day, next_place=place),
            duration_minutes=90,
            estimated_cost_max=place.estimated_cost_max or 0.0,
            estimated_cost_min=place.estimated_cost_min or 0.0,
        )
        day.items.append(item)
        self.is_dirty = True
        self._build_content()
        self._safe_update()

    def _open_full_map_draft(self) -> None:
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
        self._navigate(f"/map?itineraryId=draft&day={day_num}&source=builder")

    def _save_custom_itinerary(self) -> None:
        if self.total_stops_count == 0:
            if self.safe_page:
                self.safe_page.snack_bar = ft.SnackBar(ft.Text("Please add at least 1 stop before saving!"), open=True)
                self.safe_page.update()
            return

        self.is_saving = True
        self._build_content()
        self._safe_update()

        async def _do_save():
            try:
                itin_to_save = Itinerary(
                    id=self.existing_itinerary.id if (self.existing_itinerary and not self.is_draft_from_wizard and self.existing_itinerary.id != "draft") else "draft",
                    title=self.trip_title,
                    destination=self.destination,
                    start_date=self.start_date_str,
                    end_date=self.end_date_str,
                    daily_budget=self.daily_budget,
                    preferences=self.preferences,
                    type="custom",
                    days=self.days,
                )
                payload = itin_to_save.to_create_payload()
                if self.existing_itinerary and not self.is_draft_from_wizard and self.existing_itinerary.id != "draft":
                    self.existing_itinerary.title = self.trip_title
                    self.existing_itinerary.destination = self.destination
                    self.existing_itinerary.start_date = self.start_date_str
                    self.existing_itinerary.end_date = self.end_date_str
                    self.existing_itinerary.daily_budget = self.daily_budget
                    self.existing_itinerary.preferences = self.preferences
                    self.existing_itinerary.days = self.days
                    saved = await self.itinerary_service.update_itinerary(self.existing_itinerary)
                else:
                    saved = await self.itinerary_service.create_itinerary(payload)

                self.is_dirty = False
                self.itinerary_service.clear_active_draft_itinerary()
                self._navigate(f"/trips/{saved.id}")
            except Exception as e:
                if self.safe_page:
                    self.safe_page.snack_bar = ft.SnackBar(ft.Text(f"Failed to save itinerary: {e}"), open=True)
                    self.safe_page.update()
            finally:
                self.is_saving = False
                self._build_content()
                self._safe_update()

        if self.safe_page:
            self.safe_page.run_task(_do_save)
        else:
            try:
                asyncio.get_running_loop().create_task(_do_save())
            except RuntimeError:
                pass

    def _toggle_pref(self, pref: str) -> None:
        if pref in self.preferences:
            self.preferences.remove(pref)
        else:
            self.preferences.append(pref)
        self.is_dirty = True
        self._build_content()
        self._safe_update()

    def _set_budget_preset(self, val: float, field_ctrl: ft.TextField) -> None:
        self.daily_budget = val
        field_ctrl.value = str(int(val))
        self.is_dirty = True
        self._safe_update()

    def _on_budget_change(self, val: str) -> None:
        try:
            cleaned = "".join(c for c in val if c.isdigit())
            if cleaned:
                self.daily_budget = float(cleaned)
                self.is_dirty = True
        except ValueError:
            pass

    def _safe_update(self) -> None:
        try:
            self.update()
        except Exception:
            pass

    @property
    def safe_page(self) -> Optional[ft.Page]:
        if hasattr(self, "_test_page") and self._test_page is not None:
            return self._test_page
        try:
            return self.page
        except Exception:
            return None

    def _navigate(self, route: str) -> None:
        if self.on_navigate:
            self.on_navigate(route)
