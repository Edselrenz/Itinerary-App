"""Full-Bleed Map Explorer and Destination Catalog View mirroring Ionic tabs/map.

Directly ports the architecture from Project/src/app/tabs/map/:
- 100% Full-Bleed interactive SlippyMapCanvas (expand=True)
- Floating Top Search & 17 Category Filter Pills Bar (.map-top-bar) with in-place live filtering
- Floating Right Action Buttons: [✨ Live OSM], [🎯 Locate Me (GPS)], [🧭 Reset Province View]
- Floating Bottom-Center "List View (N)" Pill opening Collapsible POI List Drawer (without full-screen pointer blocking)
- Focused Follow-Route Mode (activated via /map?itineraryId=...&day=...) with Day Switcher,
  [Show Nearby POIs] toggle, and Bottom Active Route Stops Carousel with Google Maps Navigation.
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Optional
import urllib.parse
import flet as ft

from desktop_client.components.dialogs import show_place_detail_dialog
from desktop_client.components.place_card import PlaceCard
from desktop_client.components.slippy_map_canvas import RouteStopPin, SlippyMapCanvas
from desktop_client.config.settings import CANONICAL_CATEGORIES, NUEVA_ECIJA_LGUS, ThemeColors
from desktop_client.core.commute_guide import get_multi_stop_google_maps_url
from desktop_client.models.itinerary import Itinerary, ItineraryDay
from desktop_client.models.place import Municipality, Place
from desktop_client.services.itinerary_service import get_itinerary_service
from desktop_client.services.place_service import get_place_service

CATEGORY_ICONS: dict[str, ft.IconData] = {
    "all": ft.Icons.LAYERS_OUTLINED,
    "tourist_attraction": ft.Icons.AUTO_AWESOME_OUTLINED,
    "nature_park": ft.Icons.FOREST_OUTLINED,
    "resort_swimming": ft.Icons.POOL_OUTLINED,
    "hotel_accommodation": ft.Icons.BED_OUTLINED,
    "restaurant": ft.Icons.RESTAURANT_OUTLINED,
    "cafe": ft.Icons.LOCAL_CAFE_OUTLINED,
    "church_religious": ft.Icons.CHURCH_OUTLINED,
    "museum_cultural": ft.Icons.MUSEUM_OUTLINED,
    "shopping_market": ft.Icons.SHOPPING_BAG_OUTLINED,
    "transport_terminal": ft.Icons.DIRECTIONS_BUS_OUTLINED,
    "convenience_store": ft.Icons.STOREFRONT_OUTLINED,
    "hospital_clinic": ft.Icons.LOCAL_HOSPITAL_OUTLINED,
    "pharmacy": ft.Icons.MEDICATION_OUTLINED,
    "bank_atm": ft.Icons.CREDIT_CARD_OUTLINED,
    "fuel_station": ft.Icons.LOCAL_GAS_STATION_OUTLINED,
    "viewpoint": ft.Icons.VISIBILITY_OUTLINED,
}


class PlacesView(ft.Container):
    """Full-bleed Map Tab matching the canonical Web Client (Project/src/app/tabs/map/)."""

    def __init__(
        self,
        on_navigate: Optional[Callable[..., None]] = None,
        route_query: Optional[str] = None,
        active_trip: Optional[Itinerary] = None,
    ):
        super().__init__()
        self.on_navigate = on_navigate
        self.route_query = route_query or ""
        self.active_trip = active_trip
        self.place_service = get_place_service()
        self.itinerary_service = get_itinerary_service()

        self.expand = True
        self.padding = 0
        self.margin = 0
        self.bgcolor = "#e2e8f0"

        # Search & Multi-Category Filter State
        self.search_query = ""
        self.selected_categories: set[str] = set()
        self.selected_category = "all"
        self.selected_municipality = "all"
        self.selected_price_tier = "all"  # all, free, budget, mid, luxury
        self.is_drawer_open = False
        self.is_live_refreshing = False

        # Route / Follow-Route Mode State
        self.is_follow_route_mode = False
        self.show_nearby_pois_in_route = False
        self.active_day_number = 1
        self.route_itinerary: Optional[Itinerary] = None

        self._check_and_init_route_mode()

        self.all_places: list[Place] = self.place_service.get_loaded_places()
        self.filtered_places: list[Place] = list(self.all_places)

        self.map_component: Optional[SlippyMapCanvas] = None
        self._build_content()
        self._async_bootstrap()

    @property
    def safe_page(self) -> Optional[ft.Page]:
        if hasattr(self, "_test_page") and self._test_page is not None:
            return self._test_page
        try:
            return self.page
        except Exception:
            return None

    def _check_and_init_route_mode(self) -> None:
        """Determines if /map was launched with an itinerary route parameter."""
        parsed = urllib.parse.urlparse(self.route_query)
        params = urllib.parse.parse_qs(parsed.query)

        itin_id = params.get("itineraryId", [None])[0]
        follow_param = params.get("followRoute", ["false"])[0].lower() == "true"
        day_param = params.get("day", ["1"])[0]
        try:
            self.active_day_number = int(day_param)
        except ValueError:
            self.active_day_number = 1

        if itin_id or follow_param:
            self.is_follow_route_mode = True
            if itin_id:
                if self.active_trip and (self.active_trip.id == itin_id or itin_id == "draft"):
                    self.route_itinerary = self.active_trip
                else:
                    self.route_itinerary = self.itinerary_service.get_itinerary_or_draft(itin_id)
            else:
                self.route_itinerary = self.active_trip
        else:
            self.is_follow_route_mode = False
            self.route_itinerary = None

    def _async_bootstrap(self) -> None:
        async def _load():
            try:
                res = await self.place_service.get_places(page=1, page_size=250)
                if res.items:
                    self.place_service.merge_places_into_cache(res.items)
                    self.all_places = self.place_service.get_loaded_places()
                    self._apply_filters()
                    self._update_in_place(reset_viewport=False)
            except Exception:
                pass

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_load())
        except RuntimeError:
            pass

    def _apply_filters(self) -> None:
        """Filters self.all_places based on search, category, municipality, and price tier."""
        results = self.all_places

        if self.selected_categories:
            results = [p for p in results if p.category in self.selected_categories]
        elif self.selected_category != "all":
            results = [p for p in results if p.category == self.selected_category]

        if self.selected_municipality != "all":
            m_low = self.selected_municipality.lower()
            results = [
                p for p in results
                if m_low in (p.municipality_name or "").lower() or m_low in (p.municipality_id or "").lower()
            ]

        if self.selected_price_tier != "all":
            if self.selected_price_tier == "free":
                results = [
                    p for p in results
                    if p.estimated_cost_min == 0 and (p.estimated_cost_max is None or p.estimated_cost_max == 0)
                ]
            elif self.selected_price_tier == "budget":
                results = [
                    p for p in results
                    if (p.estimated_cost_max is not None and p.estimated_cost_max <= 500)
                    or (p.estimated_cost_min == 0 and p.estimated_cost_max is None)
                ]
            elif self.selected_price_tier == "mid":
                results = [
                    p for p in results
                    if (p.estimated_cost_max is not None and p.estimated_cost_max > 500)
                    or (p.estimated_cost_min is not None and p.estimated_cost_min > 500)
                ]
            elif self.selected_price_tier == "luxury":
                results = [
                    p for p in results
                    if (p.estimated_cost_min is not None and p.estimated_cost_min > 2000)
                    or (p.estimated_cost_max is not None and p.estimated_cost_max > 2000)
                ]

        if self.search_query.strip():
            q = self.search_query.strip().lower()
            results = [
                p for p in results
                if q in p.name.lower()
                or q in (p.municipality_name or "").lower()
                or q in (p.description or "").lower()
                or any(q in t.lower() for t in p.tags)
            ]

        self.filtered_places = results

    @property
    def _active_filters_count(self) -> int:
        return (
            len(self.selected_categories)
            + (1 if self.selected_municipality != "all" else 0)
            + (1 if self.selected_price_tier != "all" else 0)
        )

    def _safe_update(self) -> None:
        try:
            if self.safe_page:
                self.update()
        except Exception:
            pass

    def _update_in_place(self, reset_viewport: bool = False) -> None:
        """Updates markers, counts, badges, and drawer in-place preserving text field focus and map."""
        if hasattr(self, "_clear_btn"):
            self._clear_btn.visible = bool(self.search_query)
        if hasattr(self, "_filter_badge_text"):
            filter_count = self._active_filters_count
            self._filter_badge_text.value = str(filter_count)
            self._filter_badge.visible = filter_count > 0
        if hasattr(self, "_cat_row"):
            self._cat_row.controls = self._build_category_pills()
        if hasattr(self, "_drawer_pill_label"):
            count = len(self.filtered_places)
            self._drawer_pill_label.value = f"List View ({count})" if not self.is_drawer_open else "Close List View"
        if hasattr(self, "_drawer_pill_icon"):
            self._drawer_pill_icon.name = (
                ft.Icons.KEYBOARD_ARROW_DOWN_ROUNDED if self.is_drawer_open else ft.Icons.LIST_ROUNDED
            )
        if hasattr(self, "_drawer_container"):
            self._drawer_container.visible = self.is_drawer_open
            self._drawer_container.content = self._build_drawer_content()

        if self.map_component:
            if self.is_follow_route_mode and not self.show_nearby_pois_in_route:
                self.map_component.set_places([])
            else:
                self.map_component.set_places(self.filtered_places, auto_fit=reset_viewport)

        self._safe_update()

    def recenter_map(self) -> None:
        """Resets filters and recenters discovery map to provincial view."""
        self.is_follow_route_mode = False
        self.route_itinerary = None
        self.search_query = ""
        if hasattr(self, "_search_field"):
            self._search_field.value = ""
        self.selected_categories.clear()
        self.selected_category = "all"
        self.selected_municipality = "all"
        self.selected_price_tier = "all"
        self.is_drawer_open = False
        self._apply_filters()
        if self.map_component:
            self.map_component.recenter_province()
        self._build_content()
        self._safe_update()

    def _build_content(self) -> None:
        # 1. Base Map Component
        route_stops: list[RouteStopPin] = []
        if self.is_follow_route_mode and self.route_itinerary and self.route_itinerary.days:
            target_day: Optional[ItineraryDay] = None
            for d in self.route_itinerary.days:
                if d.day_number == self.active_day_number:
                    target_day = d
                    break
            if not target_day:
                target_day = self.route_itinerary.days[0]
                self.active_day_number = target_day.day_number

            for idx, itm in enumerate(target_day.items):
                p = itm.place
                lat = (p.latitude if p and p.latitude else None) or itm.custom_lat
                lng = (p.longitude if p and p.longitude else None) or itm.custom_lng
                title = itm.custom_title or (p.name if p else f"Stop {idx + 1}")
                cat = p.category if p and p.category else "attraction"
                if lat and lng:
                    route_stops.append(
                        RouteStopPin(
                            index=idx,
                            title=title,
                            lat=float(lat),
                            lng=float(lng),
                            planned_time=itm.planned_time or "",
                            category=cat,
                            place=p,
                        )
                    )

        places_to_show = []
        if not self.is_follow_route_mode or self.show_nearby_pois_in_route:
            places_to_show = self.filtered_places

        self.map_component = SlippyMapCanvas(
            width=1366,
            height=768,
            places=places_to_show,
            route_stops=route_stops,
            on_place_click=self._handle_place_pin_click,
            on_stop_click=self._handle_stop_pin_click,
            border_radius=0,
        )

        map_wrapper = ft.Container(
            content=self.map_component,
            expand=True,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )

        stack_layers: list[ft.Control] = [map_wrapper]

        if self.is_follow_route_mode:
            stack_layers.append(self._build_follow_route_top_bar())
            stack_layers.append(self._build_follow_route_bottom_carousel())
        else:
            stack_layers.append(self._build_discovery_top_bar())
            stack_layers.append(self._build_floating_action_buttons())
            stack_layers.append(self._build_drawer_toggle_pill())
            stack_layers.append(self._build_poi_drawer())

        self.content = ft.Stack(
            controls=stack_layers,
            expand=True,
        )

    # =========================================================================
    # DISCOVERY MODE CONTROLS
    # =========================================================================

    def _build_category_pills(self) -> list[ft.Control]:
        cat_pills: list[ft.Control] = []
        all_active = len(self.selected_categories) == 0
        cat_pills.append(
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(CATEGORY_ICONS["all"], size=13, color=ft.Colors.WHITE if all_active else ThemeColors.PRIMARY_BLUE),
                        ft.Text("All Places", size=11, weight=ft.FontWeight.BOLD if all_active else ft.FontWeight.W_500, color=ft.Colors.WHITE if all_active else ThemeColors.TEXT_BLACK),
                    ],
                    spacing=5,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    tight=True,
                ),
                bgcolor=ThemeColors.PRIMARY_BLUE if all_active else ft.Colors.WHITE,
                border=ft.Border.all(1, ThemeColors.PRIMARY_BLUE if all_active else ThemeColors.BORDER_LIGHT),
                border_radius=16,
                padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                ink=True,
                on_click=lambda _: self._select_category("all"),
            )
        )

        for cat in CANONICAL_CATEGORIES:
            c_key = cat["key"]
            c_label = cat["label"]
            c_icon = CATEGORY_ICONS.get(c_key, ft.Icons.LOCATION_ON_OUTLINED)
            is_active = c_key in self.selected_categories
            cat_pills.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(c_icon, size=13, color=ft.Colors.WHITE if is_active else ThemeColors.PRIMARY_BLUE),
                            ft.Text(c_label, size=11, weight=ft.FontWeight.W_600 if is_active else ft.FontWeight.W_500, color=ft.Colors.WHITE if is_active else ThemeColors.TEXT_BLACK),
                        ],
                        spacing=5,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        tight=True,
                    ),
                    bgcolor=ThemeColors.PRIMARY_BLUE if is_active else ft.Colors.WHITE,
                    border=ft.Border.all(1, ThemeColors.PRIMARY_BLUE if is_active else ThemeColors.BORDER_LIGHT),
                    border_radius=16,
                    padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                    ink=True,
                    on_click=lambda _, k=c_key: self._select_category(k),
                )
            )
        return cat_pills

    def _build_discovery_top_bar(self) -> ft.Control:
        """Floating Top Search & 17 Category Filter Pills Bar."""
        self._search_field = ft.TextField(
            hint_text="Search places in Nueva Ecija...",
            hint_style=ft.TextStyle(size=13, color=ThemeColors.TEXT_MUTED_LIGHT),
            value=self.search_query,
            dense=True,
            content_padding=ft.Padding.symmetric(horizontal=12, vertical=8),
            border_radius=10,
            border_color=ThemeColors.BORDER_LIGHT,
            focused_border_color=ThemeColors.PRIMARY_BLUE,
            expand=True,
            prefix_icon=ft.Icons.SEARCH_ROUNDED,
            on_change=lambda e: self._on_search_change(e.control.value),
        )

        self._clear_btn = ft.IconButton(
            icon=ft.Icons.CLEAR_ROUNDED,
            icon_size=16,
            icon_color=ThemeColors.TEXT_MUTED_LIGHT,
            tooltip="Clear Search",
            visible=bool(self.search_query),
            on_click=lambda _: self._clear_search(),
        )

        filter_count = self._active_filters_count
        self._filter_badge_text = ft.Text(str(filter_count), size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
        self._filter_badge = ft.Container(
            content=self._filter_badge_text,
            bgcolor=ThemeColors.PRIMARY_BLUE,
            border_radius=10,
            padding=ft.Padding.symmetric(horizontal=5, vertical=1),
            visible=filter_count > 0,
        )

        filter_btn = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.TUNE_ROUNDED, size=15, color=ThemeColors.PRIMARY_BLUE),
                    ft.Text("Filters", size=12, weight=ft.FontWeight.BOLD, color=ThemeColors.PRIMARY_BLUE),
                    self._filter_badge,
                ],
                spacing=4,
            ),
            bgcolor=ThemeColors.AZURE_SOFT,
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=10, vertical=8),
            ink=True,
            on_click=lambda _: self._open_filter_modal(),
        )
        self._filter_sheet_btn = filter_btn

        self._cat_row = ft.Row(
            controls=self._build_category_pills(),
            spacing=6,
            scroll=ft.ScrollMode.HIDDEN,
        )

        card_content = ft.Column(
            controls=[
                ft.Row(controls=[self._search_field, self._clear_btn, filter_btn], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                self._cat_row,
            ],
            spacing=8,
            tight=True,
        )

        return ft.Container(
            content=card_content,
            top=14,
            left=16,
            right=16,
            bgcolor=ft.Colors.with_opacity(0.96, "#ffffff"),
            border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
            border_radius=14,
            padding=ft.Padding.symmetric(horizontal=14, vertical=10),
            shadow=ft.BoxShadow(blur_radius=12, color=ft.Colors.with_opacity(0.12, "#0f172a"), offset=ft.Offset(0, 4)),
        )

    def _build_floating_action_buttons(self) -> ft.Control:
        """Right-hand floating control buttons: [✨ Live OSM], [🎯 Locate Me], [🧭 Reset Province]."""
        def _btn(icon, tip, on_click):
            return ft.Container(
                content=ft.Icon(icon, size=18, color=ThemeColors.TEXT_BLACK),
                width=38,
                height=38,
                bgcolor=ft.Colors.WHITE,
                border_radius=10,
                border=ft.Border.all(1, "#cbd5e1"),
                alignment=ft.Alignment(0, 0),
                shadow=ft.BoxShadow(blur_radius=8, color=ft.Colors.with_opacity(0.15, "#0f172a"), offset=ft.Offset(0, 2)),
                ink=True,
                tooltip=tip,
                on_click=on_click,
            )

        col = ft.Column(
            controls=[
                _btn(ft.Icons.AUTO_AWESOME_ROUNDED, "Live OSM Discovery (Current Viewport)", lambda _: self._refresh_live_places()),
                _btn(ft.Icons.MY_LOCATION_ROUNDED, "Locate Me (Cabanatuan Hub GPS)", lambda _: self._locate_user()),
                _btn(ft.Icons.EXPLORE_ROUNDED, "Reset Province Center", lambda _: self._recenter_province()),
            ],
            spacing=8,
            tight=True,
        )

        # Positioned comfortably at bottom=185, well above SlippyMapCanvas zoom controls at bottom=24
        self._action_buttons = ft.Container(
            right=12,
            bottom=185,
            content=col,
        )
        return self._action_buttons

    def _build_drawer_toggle_pill(self) -> ft.Control:
        """Bottom-center floating pill that opens/closes the POI List Drawer (MAP-01 fixed: no full-screen blocking container)."""
        count = len(self.filtered_places)
        self._drawer_pill_label = ft.Text(
            f"List View ({count})" if not self.is_drawer_open else "Close List View",
            size=12,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.WHITE,
        )
        self._drawer_pill_icon = ft.Icon(
            ft.Icons.KEYBOARD_ARROW_DOWN_ROUNDED if self.is_drawer_open else ft.Icons.LIST_ROUNDED,
            size=18,
            color=ft.Colors.WHITE,
        )

        self._toggle_pill_btn = ft.Container(
            bottom=18,
            left=530,
            content=ft.Container(
                content=ft.Row(
                    controls=[
                        self._drawer_pill_icon,
                        self._drawer_pill_label,
                    ],
                    spacing=6,
                    tight=True,
                ),
                bgcolor=ThemeColors.TEXT_BLACK,
                border_radius=20,
                padding=ft.Padding.symmetric(horizontal=18, vertical=10),
                shadow=ft.BoxShadow(blur_radius=12, color=ft.Colors.with_opacity(0.3, "#000000"), offset=ft.Offset(0, 4)),
                ink=True,
                on_click=lambda _: self._toggle_drawer(),
            ),
        )
        return self._toggle_pill_btn

    @property
    def _route_mode(self) -> bool:
        return self.is_follow_route_mode

    @property
    def current_search(self) -> str:
        return self.search_query

    @property
    def selected_price(self) -> str:
        return self.selected_price_tier

    @property
    def _active_filters_count(self) -> int:
        return len(self.selected_categories) + (1 if self.selected_municipality != "all" else 0) + (1 if self.selected_price_tier != "all" else 0)

    def handle_back(self) -> bool:
        """Handles back button: closes list drawer if open, else delegates to shell."""
        if self.is_drawer_open:
            self.is_drawer_open = False
            self._build_content()
            self._safe_update()
            return True
        return False

    def _toggle_category_filter(self, cat_key: str) -> None:
        if cat_key in self.selected_categories:
            self.selected_categories.remove(cat_key)
        else:
            self.selected_categories.add(cat_key)
        self._apply_filters()
        self._update_in_place(reset_viewport=False)

    def _on_price_change(self, price: str) -> None:
        self.selected_price_tier = price
        self._apply_filters()
        self._update_in_place(reset_viewport=False)

    def _reset_all_filters(self) -> None:
        self._reset_discovery_filters()

    def _build_drawer_content(self) -> ft.Control:
        """Builds vertical scrollable list of destinations with empty-state reset (MAP-10)."""
        if not self.filtered_places:
            return ft.Column(
                controls=[
                    ft.Container(
                        alignment=ft.Alignment(1, 0),
                        content=ft.IconButton(
                            icon=ft.Icons.CLOSE_ROUNDED,
                            icon_size=16,
                            on_click=lambda _: self._toggle_drawer(),
                        ),
                    ),
                    ft.Icon(ft.Icons.SEARCH_OFF_ROUNDED, size=40, color=ThemeColors.TEXT_MUTED_LIGHT),
                    ft.Text("No destinations match your filters", size=13, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_BLACK),
                    ft.Text("Try resetting your filters or search terms", size=11, color=ThemeColors.TEXT_MUTED_LIGHT),
                    ft.Container(height=6),
                    ft.FilledButton(
                        "Reset All Filters",
                        icon=ft.Icons.REFRESH_ROUNDED,
                        on_click=lambda _: self._reset_all_filters(),
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
            )

        cards: list[ft.Control] = []
        for p in self.filtered_places[:80]:
            cards.append(
                ft.Container(
                    content=PlaceCard(
                        place=p,
                        compact=True,
                        on_click=lambda pl: self._focus_place_and_open_dialog(pl),
                    ),
                )
            )

        track = ft.ListView(
            controls=cards,
            spacing=8,
            expand=True,
        )

        return ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text(f"Destinations in View ({len(self.filtered_places):,})", size=13, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_BLACK),
                        ft.IconButton(
                            icon=ft.Icons.CLOSE_ROUNDED,
                            icon_size=16,
                            on_click=lambda _: self._toggle_drawer(),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                track,
            ],
            spacing=6,
            expand=True,
        )

    def _build_poi_drawer(self) -> ft.Control:
        """Collapsible vertical destinations sheet over bottom of map (MAP-10)."""
        self._drawer_container = ft.Container(
            visible=self.is_drawer_open,
            bottom=64,
            left=16,
            width=420,
            height=360,
            bgcolor=ft.Colors.with_opacity(0.97, "#ffffff"),
            border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
            border_radius=16,
            padding=ft.Padding.all(12),
            shadow=ft.BoxShadow(blur_radius=16, color=ft.Colors.with_opacity(0.2, "#0f172a"), offset=ft.Offset(0, -4)),
            content=self._build_drawer_content(),
        )
        return self._drawer_container

    # =========================================================================
    # FOLLOW-ROUTE MODE CONTROLS
    # =========================================================================

    def _build_follow_route_top_bar(self) -> ft.Control:
        """Floating active route header bar with day switcher and [Show Nearby POIs] toggle."""
        itin = self.route_itinerary
        title = itin.title if itin else "Itinerary Route"

        day_chips: list[ft.Control] = []
        for d in (itin.days if itin else []):
            is_active = d.day_number == self.active_day_number
            day_chips.append(
                ft.Container(
                    content=ft.Text(f"Day {d.day_number}", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE if is_active else ThemeColors.PRIMARY_BLUE),
                    bgcolor=ThemeColors.PRIMARY_BLUE if is_active else ThemeColors.AZURE_SOFT,
                    border_radius=8,
                    padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                    ink=True,
                    on_click=lambda _, num=d.day_number: self._switch_route_day(num),
                )
            )

        nearby_btn = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(
                        ft.Icons.VISIBILITY if not self.show_nearby_pois_in_route else ft.Icons.VISIBILITY_OFF,
                        size=14,
                        color=ThemeColors.AZURE_DEEP,
                    ),
                    ft.Text(
                        "Nearby POIs" if not self.show_nearby_pois_in_route else "Hide POIs",
                        size=11,
                        weight=ft.FontWeight.BOLD,
                        color=ThemeColors.AZURE_DEEP,
                    ),
                ],
                spacing=4,
                tight=True,
            ),
            bgcolor=ThemeColors.AZURE_SOFT,
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=10, vertical=6),
            ink=True,
            on_click=lambda _: self._toggle_nearby_pois_in_route(),
        )

        back_btn = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.ARROW_BACK_ROUNDED, size=15, color=ThemeColors.PRIMARY_BLUE),
                    ft.Text("Back to Plan", size=12, weight=ft.FontWeight.BOLD, color=ThemeColors.PRIMARY_BLUE),
                ],
                spacing=4,
            ),
            bgcolor=ThemeColors.AZURE_SOFT,
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=10, vertical=6),
            ink=True,
            on_click=lambda _: self._exit_follow_route_to_plan(),
        )

        browse_btn = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.MAP_ROUNDED, size=14, color=ThemeColors.TEXT_MUTED_LIGHT),
                    ft.Text("Browse Map", size=11, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_MUTED_LIGHT),
                ],
                spacing=4,
            ),
            bgcolor="#f1f5f9",
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=8, vertical=6),
            ink=True,
            on_click=lambda _: self._exit_follow_route_mode_cleanly(),
        )

        return ft.Container(
            top=14,
            left=16,
            right=16,
            bgcolor=ft.Colors.with_opacity(0.96, "#ffffff"),
            border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
            border_radius=14,
            padding=ft.Padding.symmetric(horizontal=14, vertical=10),
            shadow=ft.BoxShadow(blur_radius=12, color=ft.Colors.with_opacity(0.15, "#0f172a"), offset=ft.Offset(0, 4)),
            content=ft.Row(
                controls=[
                    ft.Row(controls=[back_btn, browse_btn], spacing=8),
                    ft.Text(title, size=13, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_BLACK),
                    ft.Row(controls=day_chips + [nearby_btn], spacing=6),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def _build_follow_route_bottom_carousel(self) -> ft.Control:
        """Bottom stop carousel with Google Maps navigation launcher and clickable stop cards."""
        itin = self.route_itinerary
        target_day: Optional[ItineraryDay] = None
        if itin and itin.days:
            for d in itin.days:
                if d.day_number == self.active_day_number:
                    target_day = d
                    break
            if not target_day:
                target_day = itin.days[0]

        items = target_day.items if target_day else []
        cards: list[ft.Control] = []

        coords_for_gmaps: list[tuple[float, float]] = []
        for itm in items:
            p = itm.place
            lat = (p.latitude if p and p.latitude else None) or itm.custom_lat
            lng = (p.longitude if p and p.longitude else None) or itm.custom_lng
            if lat and lng:
                coords_for_gmaps.append((float(lat), float(lng)))

        for idx, itm in enumerate(items):
            p = itm.place
            title = itm.custom_title or (p.name if p else f"Stop {idx + 1}")
            time_str = itm.planned_time or "Scheduled"
            cat = p.category if p and p.category else "attraction"
            lat = (p.latitude if p and p.latitude else None) or itm.custom_lat
            lng = (p.longitude if p and p.longitude else None) or itm.custom_lng

            cards.append(
                ft.Container(
                    width=210,
                    bgcolor=ft.Colors.WHITE,
                    border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
                    border_radius=12,
                    padding=ft.Padding.all(10),
                    shadow=ft.BoxShadow(blur_radius=6, color=ft.Colors.with_opacity(0.1, "#0f172a")),
                    ink=True,
                    on_click=lambda _, lt=lat, lg=lng, pl=p: self._pan_to_stop(lt, lg, pl),
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Container(
                                        content=ft.Text(str(idx + 1), size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                        bgcolor=ThemeColors.PRIMARY_BLUE,
                                        width=22,
                                        height=22,
                                        border_radius=11,
                                        alignment=ft.Alignment(0, 0),
                                    ),
                                    ft.Text(f"Stop {idx + 1} of {len(items)}", size=11, color=ThemeColors.TEXT_MUTED_LIGHT),
                                ],
                                spacing=6,
                            ),
                            ft.Text(title, size=12, weight=ft.FontWeight.BOLD, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                            ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.ACCESS_TIME_ROUNDED, size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                                    ft.Text(time_str, size=10, color=ThemeColors.TEXT_MUTED_LIGHT),
                                ],
                                spacing=4,
                            ),
                        ],
                        spacing=4,
                        tight=True,
                    ),
                )
            )

        gmaps_url = get_multi_stop_google_maps_url(coords_for_gmaps) if coords_for_gmaps else None

        nav_header_controls: list[ft.Control] = [
            ft.Text(f"Day {self.active_day_number} Route Stops ({len(items)})", size=12, weight=ft.FontWeight.BOLD),
        ]
        if gmaps_url:
            nav_header_controls.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.NAVIGATION_ROUNDED, size=13, color=ft.Colors.WHITE),
                            ft.Text("Start Google Maps Navigation", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ],
                        spacing=4,
                        tight=True,
                    ),
                    bgcolor="#10b981",
                    border_radius=8,
                    padding=ft.Padding.symmetric(horizontal=10, vertical=5),
                    ink=True,
                    on_click=lambda _: self.safe_page.launch_url(gmaps_url) if self.safe_page else None,
                )
            )

        return ft.Container(
            bottom=24,
            left=16,
            right=16,
            bgcolor=ft.Colors.with_opacity(0.96, "#ffffff"),
            border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
            border_radius=16,
            padding=ft.Padding.all(12),
            shadow=ft.BoxShadow(blur_radius=14, color=ft.Colors.with_opacity(0.18, "#0f172a"), offset=ft.Offset(0, -4)),
            content=ft.Column(
                controls=[
                    ft.Row(controls=nav_header_controls, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row(controls=cards, spacing=10, scroll=ft.ScrollMode.AUTO),
                ],
                spacing=8,
                tight=True,
            ),
        )

    # =========================================================================
    # EVENT HANDLERS & IN-PLACE INTERACTIONS
    # =========================================================================

    def _handle_place_pin_click(self, place: Place) -> None:
        if self.safe_page:
            show_place_detail_dialog(
                self.safe_page,
                place,
                on_navigate=self.on_navigate,
                on_add_to_day=lambda pl: self._prompt_add_place_to_trip(pl),
            )

    def _handle_stop_pin_click(self, idx: int, stop: RouteStopPin) -> None:
        if stop.place and self.safe_page:
            show_place_detail_dialog(
                self.safe_page,
                stop.place,
                on_navigate=self.on_navigate,
            )

    def _focus_place_and_open_dialog(self, place: Place) -> None:
        if place.latitude and place.longitude and self.map_component:
            self.map_component.set_center_and_zoom(place.latitude, place.longitude, 15)
        self._handle_place_pin_click(place)

    def _prompt_add_place_to_trip(self, place: Place) -> None:
        if self.on_navigate:
            self.on_navigate("/builder", place)

    def _pan_to_stop(self, lat: Optional[float], lng: Optional[float], place: Optional[Place]) -> None:
        if lat and lng and self.map_component:
            self.map_component.set_center_and_zoom(float(lat), float(lng), 15)
        if place and self.safe_page:
            self._handle_place_pin_click(place)

    def _on_search_change(self, val: str) -> None:
        self.search_query = val
        self._apply_filters()
        self._update_in_place(reset_viewport=False)

    def _clear_search(self) -> None:
        self.search_query = ""
        if hasattr(self, "_search_field"):
            self._search_field.value = ""
        self._apply_filters()
        self._update_in_place(reset_viewport=False)

    def _select_category(self, cat_key: str) -> None:
        if cat_key == "all" or cat_key in self.selected_categories:
            self.selected_categories.clear()
            self.selected_category = "all"
        else:
            self.selected_categories = {cat_key}
            self.selected_category = cat_key

        self._apply_filters()
        self._update_in_place(reset_viewport=False)

    def _toggle_drawer(self) -> None:
        self.is_drawer_open = not self.is_drawer_open
        self._update_in_place(reset_viewport=False)

    def _reset_all_filters(self) -> None:
        self.search_query = ""
        if hasattr(self, "_search_field"):
            self._search_field.value = ""
        self.selected_categories.clear()
        self.selected_category = "all"
        self.selected_municipality = "all"
        self.selected_price_tier = "all"
        self._apply_filters()
        self._update_in_place(reset_viewport=False)

    def _refresh_live_places(self) -> None:
        self.is_live_refreshing = True
        self._safe_update()

        async def _do():
            try:
                min_lat, max_lat, min_lng, max_lng = (15.1, 16.15, 120.7, 121.4)
                if self.map_component:
                    min_lat, max_lat, min_lng, max_lng = self.map_component.get_viewport_bounds()

                discovered = await self.place_service.fetch_live_osm_places(
                    min_lat=min_lat,
                    max_lat=max_lat,
                    min_lng=min_lng,
                    max_lng=max_lng,
                )
                self.all_places = self.place_service.get_loaded_places()
                self._apply_filters()
                self._update_in_place(reset_viewport=False)

                if self.safe_page:
                    count = len(self.all_places)
                    self.safe_page.snack_bar = ft.SnackBar(
                        content=ft.Text(f"✨ Live OSM: {count:,} places indexed across Nueva Ecija"),
                        bgcolor=ThemeColors.PRIMARY_BLUE,
                        duration=3000,
                    )
                    self.safe_page.snack_bar.open = True
                    self.safe_page.update()
            except Exception:
                if self.safe_page:
                    self.safe_page.snack_bar = ft.SnackBar(
                        content=ft.Text(f"Notice: Live refresh completed with {len(self.all_places):,} places cached"),
                        duration=2500,
                    )
                    self.safe_page.snack_bar.open = True
                    self.safe_page.update()
            finally:
                self.is_live_refreshing = False
                self._safe_update()

        if self.safe_page:
            self.safe_page.run_task(_do)

    def _locate_user(self) -> None:
        """Simulates GPS location lock onto Cabanatuan hub."""
        if self.map_component:
            self.map_component._user_location = (15.4865, 120.9674)
            self.map_component.set_center_and_zoom(15.4865, 120.9674, 14)

    def _recenter_province(self) -> None:
        """Recenters to geographic center of Nueva Ecija."""
        if self.map_component:
            self.map_component.set_center_and_zoom(15.58, 121.00, 10)

    def _switch_route_day(self, day_num: int) -> None:
        self.active_day_number = day_num
        self._build_content()
        self._safe_update()

    def _toggle_nearby_pois_in_route(self) -> None:
        self.show_nearby_pois_in_route = not self.show_nearby_pois_in_route
        self._build_content()
        self._safe_update()

    def _exit_follow_route_to_plan(self) -> None:
        """Navigates back to the source planning view preserving drafts."""
        if not self.on_navigate:
            return
        parsed_q = urllib.parse.parse_qs(urllib.parse.urlparse(self.route_query).query)
        source_param = parsed_q.get("source", [None])[0]
        if source_param == "builder":
            self.on_navigate("/builder?draft=true", self.route_itinerary)
        elif self.route_query.startswith("/map?itineraryId=draft") or ("draft" in self.route_query):
            self.on_navigate("/suggested?restore=draft", self.route_itinerary)
        elif self.route_itinerary:
            self.on_navigate(f"/trips/{self.route_itinerary.id}", self.route_itinerary)
        else:
            self.on_navigate("/home")

    def _exit_follow_route_mode_cleanly(self) -> None:
        """Disables follow route mode and switches to full province discovery mode."""
        self.is_follow_route_mode = False
        self.route_itinerary = None
        self._build_content()
        self._safe_update()

    def _open_filter_modal(self) -> None:
        """Opens the Web-identical 'Filter Destinations' modal (Multi-Category Chips, Municipality Chips, 4 Price Range Pills)."""
        if not self.safe_page:
            return

        modal_selected_cats = set(self.selected_categories)
        modal_muni = [self.selected_municipality]
        modal_tier = [self.selected_price_tier]

        cat_grid = ft.Row(wrap=True, spacing=6, run_spacing=6)
        muni_row = ft.Row(spacing=6, scroll=ft.ScrollMode.AUTO)
        muni_hint_text = ft.Text(
            "All Nueva Ecija" if modal_muni[0] == "all" else modal_muni[0],
            size=11,
            color=ThemeColors.PRIMARY_BLUE,
            weight=ft.FontWeight.W_600,
        )
        tier_row = ft.Row(wrap=True, spacing=8)

        def _rebuild_cat_chips():
            pills: list[ft.Control] = []
            for c in CANONICAL_CATEGORIES:
                k = c["key"]
                lbl = c["label"]
                ic = CATEGORY_ICONS.get(k, ft.Icons.LOCATION_ON_OUTLINED)
                is_c = k in modal_selected_cats

                def _toggle_cat(_, cat_k=k):
                    if cat_k in modal_selected_cats:
                        modal_selected_cats.remove(cat_k)
                    else:
                        modal_selected_cats.add(cat_k)
                    _rebuild_cat_chips()
                    try:
                        cat_grid.update()
                    except Exception:
                        pass

                row_ctrls: list[ft.Control] = [
                    ft.Icon(ic, size=13, color=ft.Colors.WHITE if is_c else ThemeColors.PRIMARY_BLUE),
                    ft.Text(
                        lbl,
                        size=11,
                        weight=ft.FontWeight.BOLD if is_c else ft.FontWeight.W_500,
                        color=ft.Colors.WHITE if is_c else ThemeColors.TEXT_MAIN_LIGHT,
                    ),
                ]
                if is_c:
                    row_ctrls.append(ft.Icon(ft.Icons.CHECK, size=13, color=ft.Colors.WHITE))

                pills.append(
                    ft.Container(
                        content=ft.Row(controls=row_ctrls, spacing=5, tight=True),
                        bgcolor=ThemeColors.PRIMARY_BLUE if is_c else ThemeColors.SURFACE_LIGHT,
                        border=ft.Border.all(1, ThemeColors.PRIMARY_BLUE if is_c else ThemeColors.BORDER_LIGHT),
                        border_radius=16,
                        padding=ft.Padding.symmetric(horizontal=12, vertical=7),
                        ink=True,
                        on_click=_toggle_cat,
                    )
                )
            cat_grid.controls = pills

        def _rebuild_muni_chips():
            chips: list[ft.Control] = []
            all_munis = [("all", "All Municipalities")] + [(m, m) for m in sorted(NUEVA_ECIJA_LGUS)]
            for m_key, m_lbl in all_munis:
                is_m = modal_muni[0] == m_key

                def _pick_muni(_, mk=m_key):
                    modal_muni[0] = "all" if (modal_muni[0] == mk and mk != "all") else mk
                    muni_hint_text.value = "All Nueva Ecija" if modal_muni[0] == "all" else modal_muni[0]
                    _rebuild_muni_chips()
                    try:
                        muni_hint_text.update()
                        muni_row.update()
                    except Exception:
                        pass

                chips.append(
                    ft.Container(
                        content=ft.Text(
                            m_lbl,
                            size=11,
                            weight=ft.FontWeight.BOLD if is_m else ft.FontWeight.W_500,
                            color=ft.Colors.WHITE if is_m else ThemeColors.TEXT_MAIN_LIGHT,
                        ),
                        bgcolor=ThemeColors.PRIMARY_BLUE if is_m else ThemeColors.SURFACE_LIGHT,
                        border=ft.Border.all(1, ThemeColors.PRIMARY_BLUE if is_m else ThemeColors.BORDER_LIGHT),
                        border_radius=16,
                        padding=ft.Padding.symmetric(horizontal=12, vertical=7),
                        ink=True,
                        on_click=_pick_muni,
                    )
                )
            muni_row.controls = chips

        def _rebuild_tier_pills():
            tiers = [
                ("all", "All Prices"),
                ("free", "Free (₱0)"),
                ("budget", "Budget (≤ ₱500)"),
                ("mid", "Mid-Range (> ₱500)"),
            ]
            btns: list[ft.Control] = []
            for t_key, t_lbl in tiers:
                is_t = modal_tier[0] == t_key

                def _pick_tier(_, tk=t_key):
                    modal_tier[0] = tk
                    _rebuild_tier_pills()
                    try:
                        tier_row.update()
                    except Exception:
                        pass

                btns.append(
                    ft.Container(
                        content=ft.Text(
                            t_lbl,
                            size=11,
                            weight=ft.FontWeight.BOLD if is_t else ft.FontWeight.W_500,
                            color=ft.Colors.WHITE if is_t else ThemeColors.TEXT_MAIN_LIGHT,
                        ),
                        bgcolor=ThemeColors.PRIMARY_BLUE if is_t else ThemeColors.SURFACE_LIGHT,
                        border=ft.Border.all(1, ThemeColors.PRIMARY_BLUE if is_t else ThemeColors.BORDER_LIGHT),
                        border_radius=14,
                        padding=ft.Padding.symmetric(horizontal=14, vertical=8),
                        ink=True,
                        on_click=_pick_tier,
                    )
                )
            tier_row.controls = btns

        _rebuild_cat_chips()
        _rebuild_muni_chips()
        _rebuild_tier_pills()

        def _close_dlg(_=None):
            dlg.open = False
            if self.safe_page:
                self.safe_page.update()

        def _do_reset(_):
            modal_selected_cats.clear()
            modal_muni[0] = "all"
            modal_tier[0] = "all"
            self.selected_categories.clear()
            self.selected_category = "all"
            self.selected_municipality = "all"
            self.selected_price_tier = "all"
            _close_dlg()
            self._apply_filters()
            self._update_in_place(reset_viewport=False)

        def _do_apply(_):
            self.selected_categories = set(modal_selected_cats)
            self.selected_category = next(iter(modal_selected_cats)) if len(modal_selected_cats) == 1 else "all"
            self.selected_municipality = modal_muni[0]
            self.selected_price_tier = modal_tier[0]
            _close_dlg()
            self._apply_filters()
            should_fit = self.selected_municipality != "all" and len(self.filtered_places) > 0
            self._update_in_place(reset_viewport=should_fit)

        dlg = ft.AlertDialog(
            title=ft.Row(
                controls=[
                    ft.Text("Filter Destinations", size=18, weight=ft.FontWeight.W_800, color=ThemeColors.TEXT_BLACK),
                    ft.IconButton(icon=ft.Icons.CLOSE_ROUNDED, icon_size=18, on_click=_close_dlg),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            content=ft.Container(
                width=560,
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text("Categories", size=13, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_BLACK),
                                ft.Text("Select multiple", size=11, color=ThemeColors.TEXT_MUTED_LIGHT),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        cat_grid,
                        ft.Divider(height=12, color=ThemeColors.BORDER_LIGHT),
                        ft.Row(
                            controls=[
                                ft.Text("Municipality / City", size=13, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_BLACK),
                                muni_hint_text,
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        muni_row,
                        ft.Divider(height=12, color=ThemeColors.BORDER_LIGHT),
                        ft.Text("Price Range", size=13, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_BLACK),
                        tier_row,
                    ],
                    tight=True,
                    spacing=8,
                    scroll=ft.ScrollMode.AUTO,
                ),
            ),
            actions=[
                ft.TextButton("Reset", on_click=_do_reset),
                ft.FilledButton(
                    content="Apply Filters",
                    style=ft.ButtonStyle(bgcolor=ThemeColors.PRIMARY_BLUE, color=ft.Colors.WHITE),
                    on_click=_do_apply,
                ),
            ],
        )
        self.safe_page.overlay.append(dlg)
        dlg.open = True
        self.safe_page.update()
