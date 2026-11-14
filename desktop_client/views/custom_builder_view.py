"""Custom Itinerary Builder View (Desktop Dual-Pane Layout)."""

import asyncio
from datetime import date, datetime, timedelta
from typing import Callable, Optional
import uuid
import flet as ft

from desktop_client.components.dialogs import (
    show_confirm_dialog,
    show_custom_venue_dialog,
    show_edit_stop_dialog,
    show_export_dialog,
    show_place_detail_dialog,
)
from desktop_client.components.itinerary_route_map import ItineraryRouteMap
from desktop_client.components.stop_card import StopCard
from desktop_client.config.settings import CANONICAL_CATEGORIES, ThemeColors
from desktop_client.models.itinerary import (
    Itinerary,
    ItineraryCreatePayload,
    ItineraryDay,
    ItineraryItem,
    ItineraryItemCreatePayload,
)
from desktop_client.models.place import PaginatedPlaces, Place
from desktop_client.services.itinerary_service import get_itinerary_service
from desktop_client.services.place_service import get_place_service


class CustomBuilderView(ft.Container):
    """Dual-pane custom itinerary builder with catalog search, timeline drag/reorder,

    off-grid custom venues, and zero-stop guard validation.
    """

    def __init__(
        self,
        on_navigate: Optional[Callable[[str], None]] = None,
        pre_added_place: Optional[Place] = None,
        existing_itinerary: Optional[Itinerary] = None,
    ):
        super().__init__()
        self.on_navigate = on_navigate
        self.place_service = get_place_service()
        self.itinerary_service = get_itinerary_service()
        self.pre_added_place = pre_added_place
        self.existing_itinerary = existing_itinerary

        self.expand = True
        self.padding = ft.Padding.all(20)
        self.bgcolor = ThemeColors.BG_LIGHT

        # Itinerary Draft State
        today = date.today()
        if existing_itinerary:
            self.trip_title = existing_itinerary.title or "My Custom Trip"
            self.destination = existing_itinerary.destination or "Nueva Ecija"
            self.start_date_str = existing_itinerary.start_date or (today + timedelta(days=5)).strftime("%Y-%m-%d")
            self.end_date_str = existing_itinerary.end_date or (today + timedelta(days=6)).strftime("%Y-%m-%d")
            self.daily_budget = existing_itinerary.daily_budget or 2500.0
            self.days = list(existing_itinerary.days) if existing_itinerary.days else []
        else:
            self.trip_title = "My Nueva Ecija Journey"
            self.destination = "Nueva Ecija"
            self.start_date_str = (today + timedelta(days=5)).strftime("%Y-%m-%d")
            self.end_date_str = (today + timedelta(days=6)).strftime("%Y-%m-%d")
            self.daily_budget = 2500.0
            day1_id = str(uuid.uuid4())
            day2_id = str(uuid.uuid4())
            self.days = [
                ItineraryDay(
                    id=day1_id,
                    itinerary_id="",
                    day_number=1,
                    travel_date=self.start_date_str,
                    title="Arrival & Exploration",
                    items=[],
                ),
                ItineraryDay(
                    id=day2_id,
                    itinerary_id="",
                    day_number=2,
                    travel_date=self.end_date_str,
                    title="Scenic Trails & Dining",
                    items=[],
                ),
            ]

        # Pre-load place into Day 1 if passed (BUG-08)
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

        # Catalog Pane State
        self.catalog_search = ""
        self.catalog_category = "all"
        self.catalog_places: list[Place] = []
        self.catalog_loading = False

        # Feedback state
        self.feedback_message: Optional[str] = None
        self.feedback_is_error: bool = False
        self.is_dirty: bool = bool(pre_added_place)

        self._build_content()
        self._load_catalog()

    def has_unsaved_changes(self) -> bool:
        """Returns True if user has unsaved modifications in draft."""
        return getattr(self, "is_dirty", False)

    def _dismiss_pre_loaded_banner(self) -> None:
        self.pre_added_place = None
        self._build_content()
        self._safe_update()

    def _auto_schedule_active_day(self, _=None) -> None:
        """Calculates sequential planned_time strings starting at 09:00 AM with transit buffers."""
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

    def _build_content(self) -> None:
        left_pane = self._build_left_pane()
        right_pane = self._build_right_pane()

        self.content = ft.Row(
            controls=[
                left_pane,
                ft.VerticalDivider(width=1, color=ThemeColors.BORDER_LIGHT),
                right_pane,
            ],
            expand=True,
            spacing=16,
        )

    def _build_left_pane(self) -> ft.Control:
        """Left Catalog Pane: Search and Place Selection."""
        search_field = ft.TextField(
            hint_text="Search POIs to add...",
            prefix_icon=ft.Icons.SEARCH,
            value=self.catalog_search,
            expand=True,
            dense=True,
            on_submit=lambda e: self._on_catalog_search(e.control.value),
        )

        category_options = [ft.dropdown.Option("all", "All Categories")]
        for c in CANONICAL_CATEGORIES:
            category_options.append(ft.dropdown.Option(c["key"], c["label"]))

        category_dropdown = ft.Dropdown(
            options=category_options,
            value=self.catalog_category,
            dense=True,
            width=180,
            on_select=lambda e: self._on_catalog_cat_change(e.control.value),
        )

        add_custom_btn = ft.FilledButton(
            content="+ Add Off-Grid Venue",
            icon=ft.Icons.ADD_LOCATION_ALT,
            style=ft.ButtonStyle(
                bgcolor=ThemeColors.SURFACE_DARK_HOVER,
                color=ft.Colors.WHITE,
                padding=ft.Padding.symmetric(vertical=10),
            ),
            width=float("inf"),
            on_click=lambda _: self._open_custom_venue_dialog(),
        )

        # Place items list
        place_controls: list[ft.Control] = []
        if self.catalog_loading:
            place_controls.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.ProgressRing(width=18, height=18, stroke_width=2),
                            ft.Text("Searching destinations...", size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    padding=20,
                )
            )
        elif not self.catalog_places:
            place_controls.append(
                ft.Container(
                    content=ft.Text("No venues found. Try different keywords.", size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                    padding=20,
                    alignment=ft.Alignment(0, 0),
                )
            )
        else:
            for p in self.catalog_places:
                place_controls.append(self._create_catalog_item(p))

        places_listview = ft.ListView(
            controls=place_controls,
            spacing=8,
            expand=True,
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Destination Catalog", size=15, weight=ft.FontWeight.BOLD),
                    ft.Text("Click '+ Add' to place venue into your active day.", size=11, color=ThemeColors.TEXT_MUTED_LIGHT),
                    ft.Row(controls=[search_field, category_dropdown], spacing=8),
                    add_custom_btn,
                    ft.Divider(height=1, color=ThemeColors.BORDER_LIGHT),
                    places_listview,
                ],
                spacing=10,
                expand=True,
            ),
            width=420,
            padding=ft.Padding.all(12),
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border_radius=12,
            border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
        )

    def _create_catalog_item(self, place: Place) -> ft.Control:
        muni_text = place.municipality_name or "Nueva Ecija"
        active_day = self.days[self.active_day_index] if self.days else None
        is_already_added = False
        if active_day:
            is_already_added = any(itm.place_id == place.id for itm in active_day.items)

        if is_already_added:
            action_btn = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.CHECK, size=13, color=ThemeColors.EMERALD_PRIMARY),
                        ft.Text("Added", size=11, weight=ft.FontWeight.BOLD, color=ThemeColors.EMERALD_PRIMARY),
                    ],
                    spacing=3,
                ),
                bgcolor=ThemeColors.EMERALD_MINT,
                border=ft.Border.all(1, ThemeColors.EMERALD_PRIMARY),
                border_radius=6,
                padding=ft.Padding.symmetric(horizontal=8, vertical=5),
            )
        else:
            action_btn = ft.FilledButton(
                content="+ Add",
                style=ft.ButtonStyle(
                    bgcolor=ThemeColors.PRIMARY_BLUE,
                    color=ft.Colors.WHITE,
                    padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                    shape=ft.RoundedRectangleBorder(radius=6),
                ),
                on_click=lambda _, p=place: self._add_place_to_active_day(p),
            )

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Icon(ft.Icons.LOCATION_ON, size=18, color=ThemeColors.PRIMARY_BLUE),
                        bgcolor=ThemeColors.PRIMARY_LIGHT,
                        border_radius=6,
                        padding=8,
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(
                                place.name,
                                size=12,
                                weight=ft.FontWeight.BOLD,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                            ft.Text(
                                f"{place.formatted_category} • {muni_text}",
                                size=10,
                                color=ThemeColors.TEXT_MUTED_LIGHT,
                            ),
                            ft.Text(
                                place.formatted_cost,
                                size=10,
                                weight=ft.FontWeight.W_700,
                                color=ThemeColors.BUDGET_GREEN,
                            ),
                        ],
                        spacing=1,
                        expand=True,
                    ),
                    action_btn,
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=ThemeColors.BG_LIGHT,
            border_radius=8,
            padding=8,
            border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
        )

    def _build_right_pane(self) -> ft.Control:
        """Right Schedule Pane: Multi-day timeline, stop reorder, and save actions."""
        # Top metadata bar
        title_field = ft.TextField(
            label="Itinerary Title",
            value=self.trip_title,
            dense=True,
            expand=True,
            on_change=lambda e: setattr(self, "trip_title", e.control.value),
        )

        total_stops = sum(len(d.items) for d in self.days)
        total_cost = sum(d.total_day_cost for d in self.days)

        stats_pills = ft.Row(
            controls=[
                ft.Container(
                    content=ft.Text(f"{len(self.days)} Days", size=11, weight=ft.FontWeight.W_600, color=ThemeColors.AZURE_DEEP),
                    bgcolor=ThemeColors.AZURE_SOFT,
                    border_radius=6,
                    padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                ),
                ft.Container(
                    content=ft.Text(f"{total_stops} Stops", size=11, weight=ft.FontWeight.W_600, color=ThemeColors.EMERALD_PRIMARY),
                    bgcolor=ThemeColors.EMERALD_MINT,
                    border_radius=6,
                    padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                ),
                ft.Container(
                    content=ft.Text(f"Est. ₱{total_cost:,.0f}", size=11, weight=ft.FontWeight.W_600, color=ThemeColors.WARM_GOLD),
                    bgcolor=ThemeColors.AMBER_LIGHT,
                    border_radius=6,
                    padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                ),
            ],
            spacing=6,
        )

        # Day Switcher Tabs
        day_tabs: list[ft.Control] = []
        for idx, d in enumerate(self.days):
            is_active = idx == self.active_day_index
            day_tabs.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Text(f"Day {d.day_number}", size=12, weight=ft.FontWeight.W_600 if is_active else ft.FontWeight.NORMAL),
                            ft.Text(f"({len(d.items)})", size=10, color=ThemeColors.TEXT_MUTED_LIGHT),
                        ],
                        spacing=4,
                    ),
                    bgcolor=ThemeColors.PRIMARY_BLUE if is_active else ThemeColors.SURFACE_LIGHT,
                    border=ft.Border.all(1, ThemeColors.PRIMARY_BLUE if is_active else ThemeColors.BORDER_LIGHT),
                    border_radius=8,
                    padding=ft.Padding.symmetric(horizontal=12, vertical=8),
                    ink=True,
                    on_click=lambda _, i=idx: self._select_day(i),
                )
            )

        add_day_btn = ft.OutlinedButton(
            content="+ Add Day",
            icon=ft.Icons.ADD,
            style=ft.ButtonStyle(padding=ft.Padding.symmetric(horizontal=10, vertical=6)),
            on_click=lambda _: self._add_new_day(),
        )

        day_tabs_row = ft.Row(
            controls=[*day_tabs, add_day_btn],
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
        )

        # Active Day Timeline
        active_day = self.days[self.active_day_index] if self.days else None
        timeline_controls: list[ft.Control] = []

        if active_day and active_day.items:
            for idx, item in enumerate(active_day.items):
                timeline_controls.append(
                    StopCard(
                        item=item,
                        is_first=(idx == 0),
                        is_last=(idx == len(active_day.items) - 1),
                        on_move_up=self._move_stop_up,
                        on_move_down=self._move_stop_down,
                        on_edit=self._edit_stop,
                        on_delete=self._delete_stop,
                        editable=True,
                    )
                )
        else:
            timeline_controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.ADD_LOCATION_ALT_OUTLINED, size=40, color=ThemeColors.TEXT_MUTED_LIGHT),
                            ft.Text("No stops scheduled for this day yet.", size=13, weight=ft.FontWeight.W_600),
                            ft.Text("Search the catalog on the left and click '+ Add' to schedule stops.", size=11, color=ThemeColors.TEXT_MUTED_LIGHT),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=6,
                    ),
                    padding=40,
                    alignment=ft.Alignment(0, 0),
                )
            )

        timeline_listview = ft.ListView(
            controls=timeline_controls,
            spacing=4,
            expand=True,
        )

        # Feedback Banner
        feedback_row = ft.Container()
        if self.feedback_message:
            col = ThemeColors.ERROR if self.feedback_is_error else ThemeColors.SUCCESS
            bg = ThemeColors.ERROR_BG if self.feedback_is_error else ThemeColors.SUCCESS_BG
            feedback_row = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.INFO_OUTLINE, color=col, size=16),
                        ft.Text(self.feedback_message, color=col, size=12, weight=ft.FontWeight.W_500),
                    ],
                    spacing=8,
                ),
                bgcolor=bg,
                border_radius=8,
                padding=8,
            )

        # Save and Export Actions matching Figma
        save_btn = ft.FilledButton(
            content="Save Itinerary",
            icon=ft.Icons.SAVE,
            style=ft.ButtonStyle(
                bgcolor=ThemeColors.PRIMARY_BLUE,
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=10),
            ),
            on_click=lambda _: self._save_itinerary(),
        )

        export_btn = ft.OutlinedButton(
            content="Export (.ics / text)",
            icon=ft.Icons.DOWNLOAD,
            on_click=lambda _: self._export_draft(),
        )

        clear_btn = ft.TextButton(
            content="Reset Schedule",
            icon=ft.Icons.DELETE_SWEEP,
            on_click=lambda _: self._confirm_reset(),
        )

        actions_bar = ft.Row(
            controls=[
                ft.Row(controls=[save_btn, export_btn], spacing=8),
                clear_btn,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        # Pre-loaded place banner if present
        pre_loaded_ctrl = ft.Container()
        if self.pre_added_place:
            pre_loaded_ctrl = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.AUTO_AWESOME, size=16, color=ThemeColors.PRIMARY_BLUE),
                        ft.Text(f"Pre-loaded '{self.pre_added_place.name}' into Day 1 schedule.", size=12, weight=ft.FontWeight.W_600, color=ThemeColors.PRIMARY_BLUE, expand=True),
                        ft.IconButton(
                            icon=ft.Icons.CLOSE,
                            icon_size=16,
                            icon_color=ThemeColors.TEXT_MUTED_LIGHT,
                            tooltip="Dismiss banner",
                            on_click=lambda _: self._dismiss_pre_loaded_banner(),
                        ),
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                bgcolor=ThemeColors.AZURE_SOFT,
                border=ft.Border.all(1, ThemeColors.CUSTOM_CARD_BORDER),
                border_radius=8,
                padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                margin=ft.Margin.only(bottom=4),
            )

        active_day_bar = ft.Row(
            controls=[
                ft.Text(
                    f"{active_day.display_title if active_day else 'Day'} — {active_day.travel_date if active_day else ''}",
                    size=13,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Row(
                    controls=[
                        ft.TextButton(
                            content="🕒 Auto-Schedule",
                            on_click=lambda _: self._auto_schedule_active_day(),
                        ),
                        ft.TextButton(
                            content="🗑 Delete Day",
                            style=ft.ButtonStyle(color=ThemeColors.ERROR),
                            visible=len(self.days) > 1,
                            on_click=lambda _: self._delete_active_day(),
                        ),
                    ],
                    spacing=4,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        active_day = self.days[self.active_day_index] if self.days else None
        route_map = ItineraryRouteMap(
            day=active_day,
            on_view_full_map=lambda: self.on_navigate("/map") if self.on_navigate else None,
            initial_expanded=(len(active_day.items) >= 2 if active_day else False),
            height_expanded=180,
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    pre_loaded_ctrl,
                    ft.Row(controls=[title_field, stats_pills], spacing=12),
                    ft.Container(height=4),
                    day_tabs_row,
                    active_day_bar,
                    ft.Divider(height=1, color=ThemeColors.BORDER_LIGHT),
                    feedback_row,
                    route_map,
                    timeline_listview,
                    ft.Divider(height=1, color=ThemeColors.BORDER_LIGHT),
                    actions_bar,
                ],
                spacing=10,
                expand=True,
            ),
            expand=True,
            padding=ft.Padding.all(16),
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border_radius=12,
            border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
        )

    def _safe_update(self) -> None:
        try:
            self.update()
        except Exception:
            pass

    def _select_day(self, day_idx: int) -> None:
        self.active_day_index = day_idx
        self.feedback_message = None
        self._build_content()
        self._safe_update()

    def _add_new_day(self) -> None:
        new_day_num = len(self.days) + 1
        new_date = (date.today() + timedelta(days=4 + new_day_num)).strftime("%Y-%m-%d")
        new_day = ItineraryDay(
            id=str(uuid.uuid4()),
            itinerary_id="",
            day_number=new_day_num,
            travel_date=new_date,
            title=f"Day {new_day_num} Highlights",
            items=[],
        )
        self.days.append(new_day)
        self.is_dirty = True
        self.active_day_index = len(self.days) - 1
        self._build_content()
        self._safe_update()

    def _add_place_to_active_day(self, place: Place) -> None:
        if not self.days:
            return
        active_day = self.days[self.active_day_index]
        new_order = len(active_day.items) + 1

        new_item = ItineraryItem(
            id=str(uuid.uuid4()),
            day_id=active_day.id,
            place_id=place.id,
            sort_order=new_order,
            planned_time=f"{9 + ((new_order - 1) * 2):02d}:00",
            duration_minutes=90,
            estimated_cost_min=place.estimated_cost_min,
            estimated_cost_max=place.estimated_cost_max,
            place=place,
        )
        active_day.items.append(new_item)
        self.is_dirty = True
        self.feedback_message = f"Added '{place.name}' to Day {active_day.day_number}."
        self.feedback_is_error = False
        self._build_content()
        self._safe_update()

    def _open_custom_venue_dialog(self) -> None:
        if not self.page:
            return

        def handle_custom_save(venue_data: dict):
            active_day = self.days[self.active_day_index]
            new_order = len(active_day.items) + 1
            lat = venue_data.get("latitude")
            lng = venue_data.get("longitude")
            place_obj = None
            if lat and lng:
                place_obj = Place(
                    id=f"custom-{uuid.uuid4()}",
                    name=venue_data["custom_title"],
                    category="custom_venue",
                    latitude=lat,
                    longitude=lng,
                    municipality_name="Nueva Ecija",
                )

            new_item = ItineraryItem(
                id=str(uuid.uuid4()),
                day_id=active_day.id,
                custom_title=venue_data["custom_title"],
                notes=venue_data.get("notes"),
                planned_time=venue_data.get("planned_time"),
                duration_minutes=venue_data.get("duration_minutes", 90),
                estimated_cost_min=venue_data.get("estimated_cost_min"),
                estimated_cost_max=venue_data.get("estimated_cost_max"),
                sort_order=new_order,
                place=place_obj,
            )
            active_day.items.append(new_item)
            self.is_dirty = True
            self.feedback_message = f"Added off-grid venue '{new_item.custom_title}' to Day {active_day.day_number}."
            self.feedback_is_error = False
            self._build_content()
            self._safe_update()

        show_custom_venue_dialog(self.page, handle_custom_save)

    def _move_stop_up(self, item: ItineraryItem) -> None:
        active_day = self.days[self.active_day_index]
        idx = next((i for i, itm in enumerate(active_day.items) if itm.id == item.id), -1)
        if idx > 0:
            active_day.items[idx], active_day.items[idx - 1] = (
                active_day.items[idx - 1],
                active_day.items[idx],
            )
            for i, itm in enumerate(active_day.items, 1):
                itm.sort_order = i
            self.is_dirty = True
            self._build_content()
            self._safe_update()

    def _move_stop_down(self, item: ItineraryItem) -> None:
        active_day = self.days[self.active_day_index]
        idx = next((i for i, itm in enumerate(active_day.items) if itm.id == item.id), -1)
        if idx != -1 and idx < len(active_day.items) - 1:
            active_day.items[idx], active_day.items[idx + 1] = (
                active_day.items[idx + 1],
                active_day.items[idx],
            )
            for i, itm in enumerate(active_day.items, 1):
                itm.sort_order = i
            self.is_dirty = True
            self._build_content()
            self._safe_update()

    def _edit_stop(self, item: ItineraryItem) -> None:
        if not self.page:
            return

        active_day = self.days[self.active_day_index]

        def handle_edit_save(data: dict):
            item.planned_time = data.get("planned_time")
            item.duration_minutes = data.get("duration_minutes", 90)
            item.notes = data.get("notes")
            item.estimated_cost_min = data.get("estimated_cost_min")
            item.estimated_cost_max = data.get("estimated_cost_max")

            target_day_num = data.get("target_day")
            if target_day_num and target_day_num != active_day.day_number:
                target_day = next((d for d in self.days if d.day_number == target_day_num), None)
                if target_day:
                    active_day.items = [i for i in active_day.items if i.id != item.id]
                    target_day.items.append(item)
                    for i, itm in enumerate(target_day.items, 1):
                        itm.sort_order = i

            self.is_dirty = True
            self._build_content()
            self._safe_update()

        show_edit_stop_dialog(
            self.page,
            item,
            handle_edit_save,
            available_days=[d.day_number for d in self.days],
            current_day=active_day.day_number,
        )

    def _delete_stop(self, item: ItineraryItem) -> None:
        active_day = self.days[self.active_day_index]
        active_day.items = [i for i in active_day.items if i.id != item.id]
        for idx, itm in enumerate(active_day.items, 1):
            itm.sort_order = idx
        self.is_dirty = True
        self.feedback_message = f"Removed stop from Day {active_day.day_number}."
        self.feedback_is_error = False
        self._build_content()
        self._safe_update()

    def _confirm_reset(self) -> None:
        if not self.page:
            return

        def do_reset():
            for d in self.days:
                d.items = []
            self.is_dirty = True
            self.feedback_message = "All scheduled stops cleared."
            self.feedback_is_error = False
            self._build_content()
            self._safe_update()

        show_confirm_dialog(
            self.page,
            title="Reset Itinerary Schedule?",
            message="This will remove all scheduled stops across all days in this draft. This action cannot be undone.",
            on_confirm=do_reset,
        )

    def _save_itinerary(self) -> None:
        """Zero-Stop Guard Validation & Save execution."""
        total_stops = sum(len(d.items) for d in self.days)
        if total_stops == 0:
            self.feedback_message = "Cannot save an empty itinerary. Please add at least 1 destination stop."
            self.feedback_is_error = True
            self._build_content()
            self._safe_update()
            return

        async def _do_save():
            try:
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
                    start_date=self.days[0].travel_date,
                    end_date=self.days[-1].travel_date,
                    daily_budget=self.daily_budget,
                    preferences=[],
                    type="custom",
                    days=days_payload,
                )

                saved_itin = await self.itinerary_service.create_itinerary(payload)
                self.is_dirty = False
                self.feedback_message = f"Itinerary '{saved_itin.title}' successfully saved!"
                self.feedback_is_error = False
                self._build_content()
                try:
                    self.update()
                except Exception:
                    pass
            except Exception as err:
                self.feedback_message = f"Failed to save itinerary: {str(err)}"
                self.feedback_is_error = True
                self._build_content()
                try:
                    self.update()
                except Exception:
                    pass

        if self.safe_page:
            self.safe_page.run_task(_do_save)
        else:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(_do_save())
            except RuntimeError:
                pass

    def _export_draft(self) -> None:
        total_stops = sum(len(d.items) for d in self.days)
        if total_stops == 0:
            self.feedback_message = "Cannot export an empty itinerary. Add at least 1 stop."
            self.feedback_is_error = True
            self._build_content()
            self._safe_update()
            return

        draft_itin = Itinerary(
            id=str(uuid.uuid4()),
            title=self.trip_title,
            destination=self.destination,
            start_date=self.days[0].travel_date,
            end_date=self.days[-1].travel_date,
            daily_budget=self.daily_budget,
            days=self.days,
        )
        if self.page:
            show_export_dialog(self.page, draft_itin)

    def _on_catalog_search(self, query: str) -> None:
        self.catalog_search = query.strip()
        self._load_catalog()

    def _on_catalog_cat_change(self, cat: str) -> None:
        self.catalog_category = cat
        self._load_catalog()

    def _load_catalog(self) -> None:
        self.catalog_loading = True
        self._build_content()
        try:
            self.update()
        except Exception:
            pass

        async def _query():
            try:
                res = await self.place_service.get_places(
                    page=1,
                    page_size=25,
                    search=self.catalog_search or None,
                    category=self.catalog_category if self.catalog_category != "all" else None,
                )
                self.catalog_places = res.items
            except Exception:
                from desktop_client.views.dashboard_view import DashboardView
                fallback = DashboardView()._get_fallback_popular_places()
                if self.catalog_category and self.catalog_category != "all":
                    fallback = [p for p in fallback if p.category == self.catalog_category]
                if self.catalog_search:
                    s_low = self.catalog_search.lower()
                    fallback = [p for p in fallback if s_low in p.name.lower() or s_low in (p.municipality_name or "").lower()]
                self.catalog_places = fallback
            finally:
                self.catalog_loading = False
                self._build_content()
                try:
                    self.update()
                except Exception:
                    pass

        if self.safe_page:
            self.safe_page.run_task(_query)
        else:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(_query())
            except RuntimeError:
                pass

    @property
    def safe_page(self) -> Optional[ft.Page]:
        try:
            return self.page
        except Exception:
            return None
