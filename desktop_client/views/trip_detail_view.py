"""Itinerary Detail, Multi-Stop Route Navigation, and In-Place Editor View."""

from datetime import datetime
from typing import Callable, Optional
import urllib.parse
import uuid
import flet as ft

from desktop_client.components.dialogs import (
    show_custom_venue_dialog,
    show_edit_stop_dialog,
    show_export_dialog,
)
from desktop_client.components.stop_card import StopCard
from desktop_client.config.settings import ThemeColors
from desktop_client.core.commute_guide import get_leg_commute_info
from desktop_client.models.itinerary import Itinerary, ItineraryDay, ItineraryItem
from desktop_client.models.place import Place
from desktop_client.services.itinerary_service import get_itinerary_service


class TripDetailView(ft.Container):
    """Timeline inspector displaying day schedules, honest pricing, multi-stop Google Maps routes,
    and full in-place editing parity with the web client.
    """

    def __init__(
        self,
        itinerary: Itinerary,
        on_back: Optional[Callable[[], None]] = None,
    ):
        super().__init__()
        self.itinerary = itinerary
        self.on_back = on_back
        self.itinerary_service = get_itinerary_service()
        self.active_day_index = 0

        # In-Place Edit State
        self.is_edit_mode = False
        self.is_dirty = False
        self.feedback_message: Optional[str] = None
        self.feedback_is_error = False

        self.expand = True
        self.padding = ft.Padding.all(24)
        self.bgcolor = ThemeColors.BG_LIGHT

        self._build_content()

    def has_unsaved_changes(self) -> bool:
        """Pending changes guard check."""
        return self.is_edit_mode and self.is_dirty

    def _build_content(self) -> None:
        if self.is_edit_mode:
            self.content = self._build_edit_mode()
        else:
            self.content = self._build_view_mode()

    def _build_view_mode(self) -> ft.Control:
        itin = self.itinerary

        # Top navigation / Back bar
        back_btn = ft.TextButton(
            content="← Back to Saved Trips",
            icon=ft.Icons.ARROW_BACK,
            on_click=lambda _: self.on_back() if self.on_back else None,
        )

        edit_btn = ft.FilledButton(
            content="✏️ Edit Itinerary",
            style=ft.ButtonStyle(
                bgcolor=ThemeColors.PRIMARY_BLUE,
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
            on_click=lambda _: self._enter_edit_mode(),
        )

        export_btn = ft.OutlinedButton(
            content="Export Dossier",
            icon=ft.Icons.DOWNLOAD,
            on_click=lambda _: self._open_export(),
        )

        top_nav = ft.Row(
            controls=[
                back_btn,
                ft.Row(controls=[edit_btn, export_btn], spacing=8),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        # Overview Card with Dark Navy Gradient matching Figma Action Cards
        source_badge = "Local Guest Storage" if itin.is_guest else "Cloud Account"
        badge_bg = ThemeColors.AMBER_LIGHT if itin.is_guest else ThemeColors.SUCCESS_BG
        badge_col = ThemeColors.WARM_GOLD if itin.is_guest else ThemeColors.SUCCESS

        plan_badge_label = "Suggested Plan" if itin.type == "suggested" else "Custom Plan"
        plan_badge_bg = ThemeColors.SUGGESTED_BADGE_BG if itin.type == "suggested" else ThemeColors.CUSTOM_BADGE_BG
        plan_badge_col = ThemeColors.SUGGESTED_BADGE_TEXT if itin.type == "suggested" else ThemeColors.CUSTOM_BADGE_TEXT

        overview_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(itin.title, size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                            ft.Row(
                                controls=[
                                    ft.Container(
                                        content=ft.Text(plan_badge_label, size=10, weight=ft.FontWeight.BOLD, color=plan_badge_col),
                                        bgcolor=plan_badge_bg,
                                        border_radius=6,
                                        padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                                    ),
                                    ft.Container(
                                        content=ft.Text(source_badge, size=10, weight=ft.FontWeight.W_600, color=badge_col),
                                        bgcolor=badge_bg,
                                        border_radius=6,
                                        padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                                    ),
                                ],
                                spacing=6,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Text(
                        f"Destination: {itin.destination} • {itin.date_range_display} • {len(itin.days)} Days • {itin.total_stops} Total Stops",
                        size=13,
                        color=ThemeColors.PRIMARY_LIGHT,
                    ),
                    ft.Text(
                        f"Total Estimated Cost: ₱{itin.total_estimated_cost:,.2f} (~₱{itin.daily_budget:,.2f} / day target budget)",
                        size=12,
                        weight=ft.FontWeight.W_600,
                        color=ThemeColors.CUSTOM_CARD_BORDER,
                    ),
                ],
                spacing=4,
            ),
            gradient=ft.LinearGradient(
                begin=ft.Alignment(0, -1),
                end=ft.Alignment(0, 1),
                colors=[ThemeColors.NAVY_GRADIENT_START, ThemeColors.NAVY_GRADIENT_END],
            ),
            border_radius=16,
            padding=20,
            margin=ft.Margin.only(bottom=14),
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
                        weight=ft.FontWeight.W_700 if is_active else ft.FontWeight.NORMAL,
                        color=ft.Colors.WHITE if is_active else ThemeColors.TEXT_MAIN_LIGHT,
                    ),
                    bgcolor=ThemeColors.PRIMARY_BLUE if is_active else ThemeColors.SURFACE_LIGHT,
                    border=ft.Border.all(1, ThemeColors.PRIMARY_BLUE if is_active else ThemeColors.BORDER_LIGHT),
                    border_radius=8,
                    padding=ft.Padding.symmetric(horizontal=14, vertical=8),
                    ink=True,
                    on_click=lambda _, day_idx=idx: self._select_day(day_idx),
                )
            )

        day_tabs_row = ft.Row(
            controls=day_buttons,
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
        )

        active_day = itin.days[self.active_day_index] if itin.days else None

        # Route Metrics & Multi-Stop Google Maps Route Link
        route_banner = ft.Container()
        gmaps_url = self._compute_gmaps_route_url(active_day)
        total_day_dist = 0.0
        total_day_mins = 0

        timeline_items: list[ft.Control] = []
        if active_day and active_day.items:
            for idx, item in enumerate(active_day.items):
                if idx > 0:
                    prev_item = active_day.items[idx - 1]
                    leg_info = get_leg_commute_info(prev_item, item)
                    total_day_dist += leg_info.distance_km
                    total_day_mins += leg_info.duration_mins
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

            # Route Metrics Banner
            hrs = total_day_mins // 60
            rem_mins = total_day_mins % 60
            time_display = f"{hrs}h {rem_mins}m" if hrs > 0 else f"{rem_mins} mins"

            map_link_btn = ft.Container()
            if gmaps_url:
                map_link_btn = ft.FilledButton(
                    content="🗺️ Open Route in Google Maps",
                    url=gmaps_url,
                    style=ft.ButtonStyle(
                        bgcolor=ThemeColors.PRIMARY_BLUE,
                        color=ft.Colors.WHITE,
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                )

            route_banner = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.ROUTE, color=ThemeColors.PRIMARY_BLUE, size=18),
                                ft.Text(
                                    f"Day {active_day.day_number} Route: ~{total_day_dist:.1f} km • ~{time_display} drive • {len(active_day.items)} stops",
                                    size=12,
                                    weight=ft.FontWeight.BOLD,
                                    color=ThemeColors.TEXT_BLACK,
                                ),
                            ],
                            spacing=6,
                        ),
                        map_link_btn,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                bgcolor=ThemeColors.AZURE_SOFT,
                border=ft.Border.all(1, ThemeColors.CUSTOM_CARD_BORDER),
                border_radius=12,
                padding=ft.Padding.symmetric(horizontal=14, vertical=10),
                margin=ft.Margin.only(bottom=10),
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

        return ft.Column(
            controls=[
                top_nav,
                ft.Container(height=8),
                overview_card,
                day_tabs_row,
                ft.Container(height=10),
                route_banner,
                day_header,
                ft.Container(height=8),
                ft.Column(controls=timeline_items, spacing=6),
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=0,
        )

    def _build_edit_mode(self) -> ft.Control:
        itin = self.itinerary

        title_input = ft.TextField(
            label="Trip Title",
            value=itin.title,
            dense=True,
            expand=True,
            on_change=lambda e: self._on_field_change("title", e.control.value),
        )

        dest_input = ft.TextField(
            label="Destination",
            value=itin.destination,
            dense=True,
            width=200,
            on_change=lambda e: self._on_field_change("destination", e.control.value),
        )

        budget_input = ft.TextField(
            label="Daily Budget (₱)",
            value=str(itin.daily_budget or 2500.0),
            dense=True,
            width=160,
            on_change=lambda e: self._on_field_change("budget", e.control.value),
        )

        top_fields = ft.Row(controls=[title_input, dest_input, budget_input], spacing=10)

        # Save & Cancel Actions
        save_btn = ft.FilledButton(
            content="💾 Save Changes",
            style=ft.ButtonStyle(
                bgcolor=ThemeColors.EMERALD_PRIMARY,
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
            on_click=lambda _: self._save_changes(),
        )

        cancel_btn = ft.OutlinedButton(
            content="Cancel",
            on_click=lambda _: self._exit_edit_mode(),
        )

        edit_header = ft.Row(
            controls=[
                ft.Text("Editing Itinerary Stops & Schedule", size=16, weight=ft.FontWeight.BOLD),
                ft.Row(controls=[cancel_btn, save_btn], spacing=8),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        # Day Tabs Row in Edit Mode
        day_buttons: list[ft.Control] = []
        for idx, day in enumerate(itin.days):
            is_active = idx == self.active_day_index
            day_buttons.append(
                ft.Container(
                    content=ft.Text(
                        f"Day {day.day_number} ({len(day.items)})",
                        size=12,
                        weight=ft.FontWeight.W_700 if is_active else ft.FontWeight.NORMAL,
                        color=ft.Colors.WHITE if is_active else ThemeColors.TEXT_MAIN_LIGHT,
                    ),
                    bgcolor=ThemeColors.PRIMARY_BLUE if is_active else ThemeColors.SURFACE_LIGHT,
                    border=ft.Border.all(1, ThemeColors.PRIMARY_BLUE if is_active else ThemeColors.BORDER_LIGHT),
                    border_radius=8,
                    padding=ft.Padding.symmetric(horizontal=12, vertical=8),
                    ink=True,
                    on_click=lambda _, day_idx=idx: self._select_day(day_idx),
                )
            )

        add_day_btn = ft.OutlinedButton(
            content="+ Add Day",
            on_click=lambda _: self._add_day(),
        )

        day_bar = ft.Row(
            controls=[*day_buttons, add_day_btn],
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
        )

        active_day = itin.days[self.active_day_index] if itin.days else None

        # Add Off-Grid Venue Button
        add_custom_btn = ft.OutlinedButton(
            content="+ Add Custom Stop",
            icon=ft.Icons.ADD_LOCATION_ALT,
            on_click=lambda _: self._open_add_custom_stop(),
        )

        delete_day_btn = ft.TextButton(
            content="🗑 Delete Day",
            style=ft.ButtonStyle(color=ThemeColors.ERROR),
            visible=len(itin.days) > 1,
            on_click=lambda _: self._delete_day(),
        )

        day_action_row = ft.Row(
            controls=[
                ft.Text(f"Day {active_day.day_number if active_day else ''} Schedule", size=14, weight=ft.FontWeight.BOLD),
                ft.Row(controls=[add_custom_btn, delete_day_btn], spacing=8),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        timeline_items: list[ft.Control] = []
        if active_day and active_day.items:
            for idx, item in enumerate(active_day.items):
                timeline_items.append(
                    StopCard(
                        item=item,
                        is_first=(idx == 0),
                        is_last=(idx == len(active_day.items) - 1),
                        editable=True,
                        on_move_up=self._move_stop_up,
                        on_move_down=self._move_stop_down,
                        on_edit=self._edit_stop,
                        on_delete=self._delete_stop,
                    )
                )
        else:
            timeline_items.append(
                ft.Container(
                    content=ft.Text("No stops in this day. Click '+ Add Custom Stop' to add one.", size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                    padding=30,
                )
            )

        return ft.Column(
            controls=[
                edit_header,
                ft.Container(height=10),
                top_fields,
                ft.Container(height=10),
                day_bar,
                ft.Container(height=8),
                day_action_row,
                ft.Divider(height=1, color=ThemeColors.BORDER_LIGHT),
                ft.Column(controls=timeline_items, spacing=6),
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=0,
        )

    def _enter_edit_mode(self) -> None:
        self.is_edit_mode = True
        self._build_content()
        self._safe_update()

    def _exit_edit_mode(self) -> None:
        self.is_edit_mode = False
        self.is_dirty = False
        self._build_content()
        self._safe_update()

    def _on_field_change(self, field: str, value: str) -> None:
        self.is_dirty = True
        if field == "title":
            self.itinerary.title = value
        elif field == "destination":
            self.itinerary.destination = value
        elif field == "budget":
            try:
                self.itinerary.daily_budget = float(value)
            except ValueError:
                pass

    def _move_stop_up(self, item: ItineraryItem) -> None:
        active_day = self.itinerary.days[self.active_day_index]
        idx = next((i for i, itm in enumerate(active_day.items) if itm.id == item.id), -1)
        if idx > 0:
            active_day.items[idx], active_day.items[idx - 1] = active_day.items[idx - 1], active_day.items[idx]
            for i, itm in enumerate(active_day.items, 1):
                itm.sort_order = i
            self.is_dirty = True
            self._build_content()
            self._safe_update()

    def _move_stop_down(self, item: ItineraryItem) -> None:
        active_day = self.itinerary.days[self.active_day_index]
        idx = next((i for i, itm in enumerate(active_day.items) if itm.id == item.id), -1)
        if idx != -1 and idx < len(active_day.items) - 1:
            active_day.items[idx], active_day.items[idx + 1] = active_day.items[idx + 1], active_day.items[idx]
            for i, itm in enumerate(active_day.items, 1):
                itm.sort_order = i
            self.is_dirty = True
            self._build_content()
            self._safe_update()

    def _edit_stop(self, item: ItineraryItem) -> None:
        if not self.safe_page:
            return

        def handle_save(data: dict):
            item.planned_time = data.get("planned_time")
            item.duration_minutes = data.get("duration_minutes", 90)
            item.notes = data.get("notes")
            item.estimated_cost_min = data.get("estimated_cost_min")
            item.estimated_cost_max = data.get("estimated_cost_max")
            self.is_dirty = True
            self._build_content()
            self._safe_update()

        show_edit_stop_dialog(self.safe_page, item, handle_save)

    def _delete_stop(self, item: ItineraryItem) -> None:
        active_day = self.itinerary.days[self.active_day_index]
        active_day.items = [i for i in active_day.items if i.id != item.id]
        for idx, itm in enumerate(active_day.items, 1):
            itm.sort_order = idx
        self.is_dirty = True
        self._build_content()
        self._safe_update()

    def _add_day(self) -> None:
        new_day_num = len(self.itinerary.days) + 1
        new_day = ItineraryDay(
            id=str(uuid.uuid4()),
            itinerary_id=self.itinerary.id,
            day_number=new_day_num,
            travel_date="",
            title=f"Day {new_day_num} Highlights",
            items=[],
        )
        self.itinerary.days.append(new_day)
        self.active_day_index = len(self.itinerary.days) - 1
        self.is_dirty = True
        self._build_content()
        self._safe_update()

    def _delete_day(self) -> None:
        if len(self.itinerary.days) <= 1:
            return
        del self.itinerary.days[self.active_day_index]
        for i, d in enumerate(self.itinerary.days, 1):
            d.day_number = i
        self.active_day_index = max(0, min(self.active_day_index, len(self.itinerary.days) - 1))
        self.is_dirty = True
        self._build_content()
        self._safe_update()

    def _open_add_custom_stop(self) -> None:
        if not self.safe_page:
            return

        def handle_custom(venue_data: dict):
            active_day = self.itinerary.days[self.active_day_index]
            new_item = ItineraryItem(
                id=str(uuid.uuid4()),
                day_id=active_day.id,
                custom_title=venue_data["custom_title"],
                notes=venue_data.get("notes"),
                planned_time=venue_data.get("planned_time"),
                duration_minutes=venue_data.get("duration_minutes", 90),
                estimated_cost_min=venue_data.get("estimated_cost_min"),
                estimated_cost_max=venue_data.get("estimated_cost_max"),
                sort_order=len(active_day.items) + 1,
            )
            active_day.items.append(new_item)
            self.is_dirty = True
            self._build_content()
            self._safe_update()

        show_custom_venue_dialog(self.safe_page, handle_custom)

    def _save_changes(self) -> None:
        async def _do_save():
            try:
                from desktop_client.models.itinerary import ItineraryUpdatePayload
                days_payload = []
                for d in self.itinerary.days:
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

                payload = ItineraryUpdatePayload(
                    title=self.itinerary.title,
                    destination=self.itinerary.destination,
                    start_date=self.itinerary.start_date,
                    end_date=self.itinerary.end_date,
                    daily_budget=self.itinerary.daily_budget,
                    days=days_payload,
                )
                updated = await self.itinerary_service.update_itinerary(self.itinerary.id, payload)
                self.itinerary = updated
                self.is_dirty = False
                self.is_edit_mode = False
            except Exception:
                self.is_dirty = False
                self.is_edit_mode = False
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

    def _compute_gmaps_route_url(self, day: Optional[ItineraryDay]) -> Optional[str]:
        if not day or len(day.items) < 2:
            return None
        valid_items = [i for i in day.items if i.place and i.place.latitude and i.place.longitude]
        if len(valid_items) < 2:
            return None

        origin = f"{valid_items[0].place.latitude},{valid_items[0].place.longitude}"
        destination = f"{valid_items[-1].place.latitude},{valid_items[-1].place.longitude}"

        if len(valid_items) > 2:
            waypoints = "|".join(f"{i.place.latitude},{i.place.longitude}" for i in valid_items[1:-1])
            params = urllib.parse.urlencode({
                "api": "1",
                "origin": origin,
                "destination": destination,
                "waypoints": waypoints,
                "travelmode": "driving",
            })
        else:
            params = urllib.parse.urlencode({
                "api": "1",
                "origin": origin,
                "destination": destination,
                "travelmode": "driving",
            })
        return f"https://www.google.com/maps/dir/?{params}"

    def _safe_update(self) -> None:
        try:
            self.update()
        except Exception:
            pass

    def _select_day(self, day_idx: int) -> None:
        self.active_day_index = day_idx
        self._build_content()
        self._safe_update()

    @property
    def safe_page(self) -> Optional[ft.Page]:
        try:
            return self.page
        except Exception:
            return None

    def _open_export(self) -> None:
        if self.safe_page:
            show_export_dialog(self.safe_page, self.itinerary)

