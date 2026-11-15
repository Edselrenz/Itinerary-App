"""Itinerary Detail, Multi-Stop Route Navigation, and In-Place Editor View."""

import asyncio
from datetime import datetime
from typing import Callable, Optional
import urllib.parse
import uuid
import flet as ft

from desktop_client.components.dialogs import (
    show_custom_venue_dialog,
    show_edit_stop_dialog,
    show_export_dialog,
    show_place_detail_dialog,
    show_toast,
)
from desktop_client.components.itinerary_route_map import ItineraryRouteMap
from desktop_client.components.stop_card import StopCard
from desktop_client.config.settings import ThemeColors
from desktop_client.core.commute_guide import get_leg_commute_info
from desktop_client.models.itinerary import Itinerary, ItineraryDay, ItineraryItem
from desktop_client.models.place import Place
from desktop_client.services.itinerary_service import get_itinerary_service
from desktop_client.services.place_service import get_place_service


class TripDetailView(ft.Container):
    """Timeline inspector displaying day schedules, honest pricing, multi-stop Google Maps routes,
    and full in-place editing parity with the web client.
    """

    def __init__(
        self,
        itinerary: Itinerary,
        on_back: Optional[Callable[[], None]] = None,
        on_navigate: Optional[Callable[..., None]] = None,
    ):
        super().__init__()
        self.itinerary = itinerary
        self.on_back = on_back
        self.on_navigate = on_navigate
        self.itinerary_service = get_itinerary_service()
        self.place_service = get_place_service()
        self.active_day_index = 0
        self.view_mode = "detail"  # "detail" or "nearby"
        self.nearby_category = "restaurant"  # "restaurant", "hospital_clinic", "convenience_store"

        # In-Place Edit State
        self.is_edit_mode = False
        self.is_dirty = False
        self.feedback_message: Optional[str] = None
        self.feedback_is_error = False
        self.is_assumptions_expanded = False

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
        elif self.view_mode == "nearby":
            self.content = self._build_nearby_view()
        else:
            self.content = self._build_view_mode()

    def _build_view_mode(self) -> ft.Control:
        itin = self.itinerary

        # Top navigation / Back bar (Matches Web itinerary-detail.page.html)
        back_btn = ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            icon_size=20,
            tooltip="Back to previous screen",
            on_click=lambda _: self.on_back() if self.on_back else None,
        )
        title_text = ft.Text(itin.title, size=18, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_BLACK)

        share_btn = ft.IconButton(
            icon=ft.Icons.SHARE_OUTLINED,
            tooltip="Share or Export Trip",
            on_click=lambda _: self._open_export(),
        )

        edit_btn = ft.FilledButton(
            content="Edit",
            style=ft.ButtonStyle(
                bgcolor=ThemeColors.PRIMARY_BLUE,
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
            on_click=lambda _: self._enter_edit_mode(),
        )

        top_nav = ft.Row(
            controls=[
                ft.Row(controls=[back_btn, title_text], spacing=6),
                ft.Row(controls=[share_btn, edit_btn], spacing=8),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        # Overview Card: Clean White Card matching Web trip-details-card
        plan_badge_label = "Suggested Plan" if itin.type == "suggested" else "Custom Plan"
        plan_badge_bg = ThemeColors.SUGGESTED_BADGE_BG if itin.type == "suggested" else ThemeColors.CUSTOM_BADGE_BG
        plan_badge_col = ThemeColors.SUGGESTED_BADGE_TEXT if itin.type == "suggested" else ThemeColors.CUSTOM_BADGE_TEXT

        overview_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Trip Details", size=16, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_BLACK),
                    ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Text(plan_badge_label, size=10, weight=ft.FontWeight.BOLD, color=plan_badge_col),
                                bgcolor=plan_badge_bg,
                                border_radius=6,
                                padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                            ),
                            ft.Text(f"₱{itin.daily_budget:,.0f}/day", size=13, weight=ft.FontWeight.W_600, color=ThemeColors.TEXT_MUTED_LIGHT),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.LOCATION_ON, size=16, color=ThemeColors.PRIMARY_BLUE),
                            ft.Text(itin.destination, size=14, weight=ft.FontWeight.W_600, color=ThemeColors.TEXT_BLACK),
                        ],
                        spacing=6,
                    ),
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.CALENDAR_TODAY, size=14, color=ThemeColors.TEXT_MUTED_LIGHT),
                            ft.Text(itin.date_range_display, size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                        ],
                        spacing=6,
                    ),
                    ft.Container(
                        content=ft.Text(
                            f"{len(itin.days)} Days & {max(0, len(itin.days) - 1)} Nights • {itin.total_stops} Total Stops",
                            size=11,
                            weight=ft.FontWeight.W_600,
                            color=ThemeColors.PRIMARY_BLUE,
                        ),
                        bgcolor=ThemeColors.PRIMARY_LIGHT,
                        border_radius=6,
                        padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                    ),
                ],
                spacing=8,
            ),
            bgcolor=ft.Colors.WHITE,
            border=ft.Border.all(1.2, ThemeColors.BORDER_LIGHT),
            border_radius=16,
            padding=18,
            margin=ft.Margin.only(bottom=10),
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.06, "#000000")),
        )

        # Verified Estimated Costs Badge
        summary = self.itinerary_service.calculate_budget_summary(itin)
        verified_costs_card = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.PAYMENTS_OUTLINED, size=15, color=ThemeColors.BUDGET_GREEN),
                    ft.Text(f"Verified Place Costs: {summary['display_text']}", size=11, weight=ft.FontWeight.BOLD, color=ThemeColors.BUDGET_GREEN),
                ],
                spacing=6,
            ),
            bgcolor=ThemeColors.SUCCESS_BG,
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=12, vertical=8),
            margin=ft.Margin.only(bottom=10),
        )

        # Expandable Assumptions Info Box
        assumptions_items = itin.assumptions or [
            f"Daily target budget: ₱{itin.daily_budget:,.0f} / day",
            "Lunch scheduled between 12:00 PM – 1:00 PM",
            "Transit durations estimated based on standard provincial road conditions",
        ]
        assumptions_controls: list[ft.Control] = [
            ft.Row(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.LIGHTBULB_OUTLINE, size=16, color=ThemeColors.PRIMARY_BLUE),
                            ft.Text("Trip Assumptions & Corridor Notes", size=11, weight=ft.FontWeight.BOLD, color=ThemeColors.PRIMARY_BLUE),
                        ],
                        spacing=6,
                    ),
                    ft.Icon(
                        ft.Icons.KEYBOARD_ARROW_UP if self.is_assumptions_expanded else ft.Icons.KEYBOARD_ARROW_DOWN,
                        size=16,
                        color=ThemeColors.PRIMARY_BLUE,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )
        ]
        if self.is_assumptions_expanded:
            for asm in assumptions_items:
                assumptions_controls.append(
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.CHECK_SMALL, size=14, color=ThemeColors.PRIMARY_BLUE),
                            ft.Text(asm, size=11, color=ThemeColors.TEXT_MUTED_LIGHT),
                        ],
                        spacing=4,
                    )
                )

        assumptions_box = ft.Container(
            content=ft.Column(controls=assumptions_controls, spacing=4),
            bgcolor=ThemeColors.AZURE_SOFT,
            border_radius=8,
            padding=10,
            margin=ft.Margin.only(bottom=12),
            ink=True,
            on_click=lambda _: self._toggle_assumptions(),
        )

        # Day Switcher Tabs
        day_buttons: list[ft.Control] = []
        for idx, day in enumerate(itin.days):
            is_active = idx == self.active_day_index
            muni_suffix = f" • {day.title.split(': ')[1]}" if (day.title and ": " in day.title) else f" ({len(day.items)} stops)"
            day_buttons.append(
                ft.Container(
                    content=ft.Text(
                        f"Day {day.day_number}{muni_suffix}",
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
                        on_click=lambda itm: show_place_detail_dialog(
                            self.safe_page,
                            itm.place,
                            on_navigate=self.on_navigate,
                            show_add_actions=False,
                        ) if (itm.place and self.safe_page) else None,
                    )
                )

            route_banner = ItineraryRouteMap(
                day=active_day,
                initial_expanded=(len(active_day.items) >= 2),
                height_expanded=190,
                on_view_full_map=lambda: self._open_full_map(),
            )
        else:
            route_banner = ft.Container()
            timeline_items.append(
                ft.Container(
                    content=ft.Text("No stops recorded for this day.", size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                    padding=30,
                )
            )

        # Active Day Header Actions: In-App Nav and Google Maps
        in_app_nav_btn = ft.FilledButton(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.NEAR_ME, size=14, color=ft.Colors.WHITE),
                    ft.Text("In-App Nav", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ],
                spacing=4,
            ),
            style=ft.ButtonStyle(bgcolor=ThemeColors.PRIMARY_BLUE, shape=ft.RoundedRectangleBorder(radius=8)),
            on_click=lambda _: self._launch_in_app_nav(active_day),
        )

        gmaps_btn = ft.OutlinedButton(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.OPEN_IN_NEW, size=14, color=ThemeColors.PRIMARY_BLUE),
                    ft.Text("Google Maps", size=11, weight=ft.FontWeight.BOLD, color=ThemeColors.PRIMARY_BLUE),
                ],
                spacing=4,
            ),
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
            url=gmaps_url,
        )

        day_header = ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text(f"Day {active_day.day_number if active_day else 1}", size=18, weight=ft.FontWeight.BOLD),
                        ft.Text(f"{active_day.travel_date if active_day else ''}", size=11, color=ThemeColors.TEXT_MUTED_LIGHT),
                    ],
                    spacing=2,
                ),
                ft.Row(controls=[in_app_nav_btn, gmaps_btn], spacing=8),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        # Explore Nearby Places Quick-Add Banner
        nearby_banner = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Icon(ft.Icons.STOREFRONT_OUTLINED, size=20, color=ThemeColors.PRIMARY_BLUE),
                        bgcolor=ThemeColors.PRIMARY_LIGHT,
                        border_radius=8,
                        padding=8,
                    ),
                    ft.Column(
                        controls=[
                            ft.Text("Explore Nearby Places", size=13, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_BLACK),
                            ft.Text("Add local dining, clinics, or convenience stores", size=11, color=ThemeColors.TEXT_MUTED_LIGHT),
                        ],
                        spacing=1,
                        expand=True,
                    ),
                    ft.Icon(ft.Icons.ARROW_FORWARD_IOS, size=14, color=ThemeColors.TEXT_MUTED_LIGHT),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border=ft.Border.all(1.2, ThemeColors.BORDER_LIGHT),
            border_radius=12,
            padding=ft.Padding.symmetric(horizontal=14, vertical=12),
            margin=ft.Margin.only(top=10, bottom=10),
            ink=True,
            on_click=lambda _: self._open_nearby_view(),
        )

        # Estimated activity expenses footer card
        total_activity_expenses = sum(
            float(itm.estimated_cost or 0.0)
            for d in itin.days
            for itm in d.items
        )
        expenses_text = f"₱{total_activity_expenses:,.2f}" if total_activity_expenses > 0 else "Flexible / Unpriced"

        expenses_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text("Estimated activity expenses", size=13, weight=ft.FontWeight.BOLD),
                            ft.Text(expenses_text, size=14, weight=ft.FontWeight.BOLD, color=ThemeColors.PRIMARY_BLUE),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Text("Verified fees from listed destinations. Estimates are editable.", size=11, color=ThemeColors.TEXT_MUTED_LIGHT),
                ],
                spacing=4,
            ),
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
            border_radius=12,
            padding=14,
            margin=ft.Margin.only(bottom=16),
        )

        return ft.Column(
            controls=[
                top_nav,
                ft.Container(height=8),
                overview_card,
                verified_costs_card,
                assumptions_box,
                day_tabs_row,
                ft.Container(height=10),
                route_banner,
                day_header,
                ft.Container(height=8),
                ft.Column(controls=timeline_items, spacing=6),
                nearby_banner,
                expenses_card,
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=0,
        )

    def _toggle_assumptions(self) -> None:
        self.is_assumptions_expanded = not self.is_assumptions_expanded
        self._build_content()
        self._safe_update()

    def _open_in_builder(self) -> None:
        if self.on_navigate:
            self.on_navigate("/builder", trip_data=self.itinerary)

    def _launch_in_app_nav(self, day: Optional[ItineraryDay]) -> None:
        if self.on_navigate and self.itinerary:
            day_num = day.day_number if day else 1
            self.on_navigate(f"/map?itineraryId={self.itinerary.id}&day={day_num}&followRoute=true")

    def _open_nearby_view(self) -> None:
        self.view_mode = "nearby"
        self._build_content()
        self._safe_update()

    def _close_nearby_view(self) -> None:
        self.view_mode = "detail"
        self._build_content()
        self._safe_update()

    def _set_nearby_category(self, cat: str) -> None:
        self.nearby_category = cat
        self._build_content()
        self._safe_update()

    def _add_nearby_to_active_day(self, place: Place) -> None:
        active_day = self.itinerary.days[self.active_day_index] if self.itinerary.days else None
        if not active_day:
            return
        new_stop = ItineraryItem(
            place_id=place.id,
            place=place,
            day_number=active_day.day_number,
            order_index=len(active_day.items),
            duration_minutes=60,
            travel_mode=self.itinerary.travel_mode or "driving",
        )
        active_day.items.append(new_stop)
        self.itinerary.total_stops = sum(len(d.items) for d in self.itinerary.days)
        self.is_dirty = True
        if self.safe_page:
            show_toast(self.safe_page, f"Added {place.name} to Day {active_day.day_number}!", bgcolor=ThemeColors.SUCCESS)
        self._close_nearby_view()

    def _build_nearby_view(self) -> ft.Control:
        active_day = self.itinerary.days[self.active_day_index] if self.itinerary.days else None
        day_loc = active_day.display_title if active_day else self.itinerary.destination

        back_nav = ft.Row(
            controls=[
                ft.TextButton(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.ARROW_BACK, size=16, color=ThemeColors.PRIMARY_BLUE),
                            ft.Text("Back to Itinerary", size=13, weight=ft.FontWeight.BOLD, color=ThemeColors.PRIMARY_BLUE),
                        ],
                        spacing=4,
                    ),
                    on_click=lambda _: self._close_nearby_view(),
                ),
                ft.Text(f"Nearby Places in {day_loc}", size=16, weight=ft.FontWeight.BOLD),
            ],
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        categories = [
            ("restaurant", "Restaurants"),
            ("hospital_clinic", "Hospitals & Clinics"),
            ("convenience_store", "Convenience Stores"),
        ]

        cat_chips = []
        for c_key, c_label in categories:
            is_act = (self.nearby_category == c_key)
            cat_chips.append(
                ft.Container(
                    content=ft.Text(
                        c_label,
                        size=12,
                        weight=ft.FontWeight.BOLD if is_act else ft.FontWeight.NORMAL,
                        color=ft.Colors.WHITE if is_act else ThemeColors.TEXT_MAIN_LIGHT,
                    ),
                    bgcolor=ThemeColors.PRIMARY_BLUE if is_act else ThemeColors.SURFACE_LIGHT,
                    border=ft.Border.all(1, ThemeColors.PRIMARY_BLUE if is_act else ThemeColors.BORDER_LIGHT),
                    border_radius=12,
                    padding=ft.Padding.symmetric(horizontal=14, vertical=6),
                    ink=True,
                    on_click=lambda _, k=c_key: self._set_nearby_category(k),
                )
            )

        tabs_row = ft.Row(controls=cat_chips, spacing=8)

        # Places in nearby category
        all_loaded = self.place_service.get_loaded_places()
        matching = [p for p in all_loaded if p.category == self.nearby_category]
        if not matching:
            matching = [p for p in all_loaded if self.nearby_category in (p.category or "").lower()][:10]

        place_cards = []
        for p in matching[:15]:
            place_cards.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text(p.name, size=13, weight=ft.FontWeight.BOLD),
                                    ft.Text(f"{p.municipality_name or 'Nueva Ecija'} • {p.opening_hours or 'Open Daily'}", size=11, color=ThemeColors.TEXT_MUTED_LIGHT),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.NEAR_ME_OUTLINED,
                                icon_size=18,
                                icon_color=ThemeColors.PRIMARY_BLUE,
                                tooltip="View in Google Maps",
                                url=p.directions_url or f"https://www.google.com/maps/search/?api=1&query={p.latitude},{p.longitude}",
                            ),
                            ft.IconButton(
                                icon=ft.Icons.ADD_CIRCLE_OUTLINE,
                                icon_size=20,
                                icon_color=ThemeColors.PRIMARY_BLUE,
                                tooltip=f"Add to Day {active_day.day_number if active_day else 1}",
                                on_click=lambda _, pl=p: self._add_nearby_to_active_day(pl),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    bgcolor=ft.Colors.WHITE,
                    border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
                    border_radius=12,
                    padding=12,
                )
            )

        if not place_cards:
            place_cards.append(
                ft.Container(
                    content=ft.Text("No nearby venues found in this category.", size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                    padding=20,
                )
            )

        return ft.Column(
            controls=[
                back_nav,
                ft.Container(height=8),
                tabs_row,
                ft.Container(height=12),
                ft.Column(controls=place_cards, spacing=8),
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

        avail_days = [d.day_number for d in self.itinerary.days]
        current_day_num = self.itinerary.days[self.active_day_index].day_number if self.itinerary.days else 1

        def handle_save(data: dict):
            item.planned_time = data.get("planned_time")
            item.duration_minutes = data.get("duration_minutes", 90)
            item.notes = data.get("notes")
            item.estimated_cost_min = data.get("estimated_cost_min")
            item.estimated_cost_max = data.get("estimated_cost_max")

            target_day_num = data.get("target_day", current_day_num)
            if target_day_num != current_day_num:
                # Remove from current day
                cur_day = self.itinerary.days[self.active_day_index]
                cur_day.items = [i for i in cur_day.items if i.id != item.id]
                for idx, itm in enumerate(cur_day.items, 1):
                    itm.sort_order = idx

                # Move to target day
                target_day = next((d for d in self.itinerary.days if d.day_number == target_day_num), None)
                if target_day:
                    item.day_id = target_day.id
                    item.sort_order = len(target_day.items) + 1
                    target_day.items.append(item)

            self.is_dirty = True
            self._build_content()
            self._safe_update()

        show_edit_stop_dialog(
            self.safe_page,
            item,
            handle_save,
            available_days=avail_days,
            current_day=current_day_num,
        )

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
                custom_lat=venue_data.get("latitude"),
                custom_lng=venue_data.get("longitude"),
                sort_order=len(active_day.items) + 1,
            )
            active_day.items.append(new_item)
            self.is_dirty = True
            self._build_content()
            self._safe_update()

        show_custom_venue_dialog(self.safe_page, handle_custom)

    def _open_full_map(self) -> None:
        if self.on_navigate:
            day_num = self.itinerary.days[self.active_day_index].day_number if self.itinerary.days else 1
            self.on_navigate(f"/map?itineraryId={self.itinerary.id}&day={day_num}", self.itinerary)

    def _save_changes(self) -> None:
        async def _do_save():
            try:
                updated = await self.itinerary_service.update_itinerary(self.itinerary)
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

