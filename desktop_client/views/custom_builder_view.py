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

    def __init__(self, on_navigate: Optional[Callable[[str], None]] = None):
        super().__init__()
        self.on_navigate = on_navigate
        self.place_service = get_place_service()
        self.itinerary_service = get_itinerary_service()

        self.expand = True
        self.padding = ft.padding.all(20)
        self.bgcolor = ThemeColors.BG_LIGHT

        # Itinerary Draft State
        today = date.today()
        self.trip_title = "My Nueva Ecija Journey"
        self.destination = "Nueva Ecija"
        self.start_date_str = (today + timedelta(days=5)).strftime("%Y-%m-%d")
        self.end_date_str = (today + timedelta(days=6)).strftime("%Y-%m-%d")
        self.daily_budget = 2500.0

        # Draft Days
        day1_id = str(uuid.uuid4())
        day2_id = str(uuid.uuid4())
        self.days: list[ItineraryDay] = [
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
        self.active_day_index = 0

        # Catalog Pane State
        self.catalog_search = ""
        self.catalog_category = "all"
        self.catalog_places: list[Place] = []
        self.catalog_loading = False

        # Feedback state
        self.feedback_message: Optional[str] = None
        self.feedback_is_error: bool = False

        self._build_content()
        self._load_catalog()

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
            on_change=lambda e: self._on_catalog_cat_change(e.control.value),
        )

        add_custom_btn = ft.FilledButton(
            content="+ Add Off-Grid Venue",
            icon=ft.Icons.ADD_LOCATION_ALT,
            style=ft.ButtonStyle(
                bgcolor=ThemeColors.SURFACE_DARK_HOVER,
                color=ft.Colors.WHITE,
                padding=ft.padding.symmetric(vertical=10),
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
            padding=ft.padding.all(12),
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border_radius=12,
            border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
        )

    def _create_catalog_item(self, place: Place) -> ft.Control:
        muni_text = place.municipality_name or "Nueva Ecija"
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Icon(ft.Icons.LOCATION_ON, size=18, color=ThemeColors.EMERALD_PRIMARY),
                        bgcolor=ThemeColors.EMERALD_MINT,
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
                                weight=ft.FontWeight.W_600,
                                color=ThemeColors.EMERALD_PRIMARY,
                            ),
                        ],
                        spacing=1,
                        expand=True,
                    ),
                    ft.FilledButton(
                        content="+ Add",
                        style=ft.ButtonStyle(
                            bgcolor=ThemeColors.EMERALD_PRIMARY,
                            color=ft.Colors.WHITE,
                            padding=ft.padding.symmetric(horizontal=8, vertical=4),
                        ),
                        on_click=lambda _, p=place: self._add_place_to_active_day(p),
                    ),
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
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                ),
                ft.Container(
                    content=ft.Text(f"{total_stops} Stops", size=11, weight=ft.FontWeight.W_600, color=ThemeColors.EMERALD_PRIMARY),
                    bgcolor=ThemeColors.EMERALD_MINT,
                    border_radius=6,
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                ),
                ft.Container(
                    content=ft.Text(f"Est. ₱{total_cost:,.0f}", size=11, weight=ft.FontWeight.W_600, color=ThemeColors.WARM_GOLD),
                    bgcolor=ThemeColors.AMBER_LIGHT,
                    border_radius=6,
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
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
                    bgcolor=ThemeColors.EMERALD_PRIMARY if is_active else ThemeColors.SURFACE_LIGHT,
                    border_radius=8,
                    padding=ft.padding.symmetric(horizontal=12, vertical=8),
                    border=ft.Border.all(1, ThemeColors.EMERALD_PRIMARY if is_active else ThemeColors.BORDER_LIGHT),
                    ink=True,
                    on_click=lambda _, i=idx: self._select_day(i),
                )
            )

        add_day_btn = ft.OutlinedButton(
            content="+ Add Day",
            icon=ft.Icons.ADD,
            style=ft.ButtonStyle(padding=ft.padding.symmetric(horizontal=10, vertical=6)),
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

        # Save and Export Actions
        save_btn = ft.FilledButton(
            content="Save Itinerary",
            icon=ft.Icons.SAVE,
            style=ft.ButtonStyle(bgcolor=ThemeColors.EMERALD_PRIMARY, color=ft.Colors.WHITE),
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

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(controls=[title_field, stats_pills], spacing=12),
                    ft.Container(height=4),
                    day_tabs_row,
                    ft.Divider(height=1, color=ThemeColors.BORDER_LIGHT),
                    feedback_row,
                    timeline_listview,
                    ft.Divider(height=1, color=ThemeColors.BORDER_LIGHT),
                    actions_bar,
                ],
                spacing=10,
                expand=True,
            ),
            expand=True,
            padding=ft.padding.all(16),
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border_radius=12,
            border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
        )

    def _select_day(self, day_idx: int) -> None:
        self.active_day_index = day_idx
        self.feedback_message = None
        self._build_content()
        self.update()

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
        self.active_day_index = len(self.days) - 1
        self._build_content()
        self.update()

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
        self.feedback_message = f"Added '{place.name}' to Day {active_day.day_number}."
        self.feedback_is_error = False
        self._build_content()
        self.update()

    def _open_custom_venue_dialog(self) -> None:
        if not self.page:
            return

        def handle_custom_save(venue_data: dict):
            active_day = self.days[self.active_day_index]
            new_order = len(active_day.items) + 1
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
            )
            active_day.items.append(new_item)
            self.feedback_message = f"Added off-grid venue '{new_item.custom_title}' to Day {active_day.day_number}."
            self.feedback_is_error = False
            self._build_content()
            self.update()

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
            self._build_content()
            self.update()

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
            self._build_content()
            self.update()

    def _edit_stop(self, item: ItineraryItem) -> None:
        if not self.page:
            return

        def handle_edit_save(data: dict):
            item.planned_time = data.get("planned_time")
            item.duration_minutes = data.get("duration_minutes", 90)
            item.notes = data.get("notes")
            item.estimated_cost_min = data.get("estimated_cost_min")
            item.estimated_cost_max = data.get("estimated_cost_max")
            self._build_content()
            self.update()

        show_edit_stop_dialog(self.page, item, handle_edit_save)

    def _delete_stop(self, item: ItineraryItem) -> None:
        active_day = self.days[self.active_day_index]
        active_day.items = [i for i in active_day.items if i.id != item.id]
        for idx, itm in enumerate(active_day.items, 1):
            itm.sort_order = idx
        self.feedback_message = f"Removed stop from Day {active_day.day_number}."
        self.feedback_is_error = False
        self._build_content()
        self.update()

    def _confirm_reset(self) -> None:
        if not self.page:
            return

        def do_reset():
            for d in self.days:
                d.items = []
            self.feedback_message = "All scheduled stops cleared."
            self.feedback_is_error = False
            self._build_content()
            self.update()

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
            self.update()
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

        asyncio.create_task(_do_save())

    def _export_draft(self) -> None:
        total_stops = sum(len(d.items) for d in self.days)
        if total_stops == 0:
            self.feedback_message = "Cannot export an empty itinerary. Add at least 1 stop."
            self.feedback_is_error = True
            self._build_content()
            self.update()
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
                self.catalog_places = []
            finally:
                self.catalog_loading = False
                self._build_content()
                try:
                    self.update()
                except Exception:
                    pass

        asyncio.create_task(_query())
