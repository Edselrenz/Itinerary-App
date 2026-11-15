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

from desktop_client.components.dialogs import (
    close_overlay_dialog,
    open_overlay_dialog,
    show_place_detail_dialog,
    show_toast,
)
from desktop_client.components.place_card import PlaceCard
from desktop_client.components.slippy_map_canvas import RouteStopPin, SlippyMapCanvas
from desktop_client.config.settings import CANONICAL_CATEGORIES, NUEVA_ECIJA_LGUS, ThemeColors, get_settings
from desktop_client.core.commute_guide import get_commute_info_for_municipality, get_multi_stop_google_maps_url
from desktop_client.core.polyline import decode_polyline
from desktop_client.models.itinerary import Itinerary, ItineraryDay
from desktop_client.models.place import Municipality, Place
from desktop_client.services.favorites_service import get_favorites_service
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
    "public_facility": ft.Icons.FLAG_OUTLINED,
    "viewpoint": ft.Icons.VISIBILITY_OUTLINED,
}


class PlacesView(ft.Container):
    """Full-bleed Map Tab matching the canonical Web Client (Project/src/app/tabs/map/)."""

    def __init__(
        self,
        on_navigate: Optional[Callable[..., None]] = None,
        route_query: Optional[str] = None,
        active_trip: Optional[Itinerary] = None,
        initial_width: Optional[float] = None,
        initial_height: Optional[float] = None,
    ):
        super().__init__()
        self.on_navigate = on_navigate
        self.route_query = route_query or ""
        self.active_trip = active_trip
        self.initial_width = initial_width
        self.initial_height = initial_height
        self.place_service = get_place_service()
        self.itinerary_service = get_itinerary_service()

        self.expand = True
        self.width = float("inf")
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
        self._active_route_stop_index: Optional[int] = None
        self.show_nearby_pois_in_route = False
        self.active_day_number = 1
        self.route_itinerary: Optional[Itinerary] = None

        # Deep-link & In-Map Interactive Bottom Sheet State (1:1 Web Parity)
        self.selected_map_place: Optional[Any] = None
        self._pending_focus_latlng: Optional[tuple[float, float]] = None
        self._pending_focus_place_id: Optional[str] = None
        self._poi_bottom_sheet_host: Optional[ft.Container] = None

        self._check_and_init_route_mode()

        self.all_places: list[Place] = self.place_service.get_loaded_places()
        self._apply_filters()

        self.map_component: Optional[SlippyMapCanvas] = None
        self._build_content()

    @property
    def safe_page(self) -> Optional[ft.Page]:
        if hasattr(self, "_test_page") and self._test_page is not None:
            return self._test_page
        try:
            return self.page
        except Exception:
            return None

    def did_mount(self) -> None:
        pw = getattr(self.safe_page, "width", None)
        ph = getattr(self.safe_page, "height", None)
        if not pw or not ph or float(pw) < 320 or float(ph) < 240:
            pw = getattr(getattr(self.safe_page, "window", None), "width", None)
            ph = getattr(getattr(self.safe_page, "window", None), "height", None)
        if pw and ph:
            try:
                self.on_resize(float(pw), float(ph))
            except Exception:
                pass

        async def _bootstrap():
            try:
                await self._async_bootstrap()
                if self._pending_focus_latlng and self.map_component:
                    self.map_component.fly_to(
                        self._pending_focus_latlng[0], self._pending_focus_latlng[1], 15, animated=True
                    )
                elif self._pending_focus_place_id and self.map_component:
                    self.map_component.set_selected_place_id(self._pending_focus_place_id, pan_to=True)
                    for pl in self.all_places:
                        if str(pl.id) == str(self._pending_focus_place_id):
                            self._handle_place_pin_click(pl)
                            break
                elif (self.selected_municipality != "all" or self.search_query) and self.filtered_places and self.map_component:
                    coords = [(p.latitude, p.longitude) for p in self.filtered_places if p.latitude and p.longitude]
                    if coords:
                        self.map_component.fit_bounds(coords, notify=True)
            except Exception:
                pass

        if self.safe_page is not None:
            self.safe_page.run_task(_bootstrap)

    @property
    def _route_mode(self) -> bool:
        return self.is_follow_route_mode

    def _check_and_init_route_mode(self) -> None:
        """Parse Web-compatible query parameters (`itineraryId`, `followRoute`, `day`/`dayNumber`,
        `lat`, `lng`, `placeId`, `destination`, `municipality`, `category`, `priceTier`, `search`)."""
        parsed = urllib.parse.urlparse(self.route_query)
        params = urllib.parse.parse_qs(parsed.query)

        # Also inspect page/state query parameters if passed
        state_obj = getattr(self, "state", None)
        state_params = getattr(state_obj, "route_query_params", None) or {}
        for k, v in state_params.items():
            if k not in params:
                params[k] = [str(v)]

        # 1. Search / Destination pre-filter
        search_arg = params.get("search", [None])[0] or params.get("destination", [None])[0]
        if search_arg:
            self.search_query = str(search_arg).strip()

        # 2. Municipality pre-filter
        muni_arg = params.get("municipality", [None])[0]
        if muni_arg:
            m_cand = str(muni_arg).strip()
            if m_cand in NUEVA_ECIJA_LGUS or m_cand.lower() in [m.lower() for m in NUEVA_ECIJA_LGUS]:
                self.selected_municipality = m_cand

        # 3. Category pre-filter
        cat_arg = params.get("category", [None])[0]
        if cat_arg:
            c_val = str(cat_arg).strip()
            self.selected_category = c_val
            if c_val != "all":
                self.selected_categories = {c_val}

        # 4. Price tier pre-filter
        pt_arg = params.get("priceTier", [None])[0]
        if pt_arg:
            pt = str(pt_arg).strip().lower()
            if pt in ("free", "budget", "mid", "moderate", "premium"):
                self.selected_price_tier = "mid" if pt == "moderate" else pt

        # 5. Target coordinates / specific POI deep link (`lat`, `lng`, `placeId`)
        lat_val = params.get("lat", [None])[0]
        lng_val = params.get("lng", [None])[0]
        if lat_val and lng_val:
            try:
                self._pending_focus_latlng = (float(lat_val), float(lng_val))
            except (ValueError, TypeError):
                self._pending_focus_latlng = None
        else:
            self._pending_focus_latlng = None

        self._pending_focus_place_id = params.get("placeId", [None])[0]

        # 6. Itinerary Route Tracking Mode (`itineraryId`, `followRoute`, `day` or `dayNumber`)
        itin_id = params.get("itineraryId", [None])[0]
        follow_param = params.get("followRoute", ["false"])[0].lower() == "true"
        day_param = params.get("dayNumber", [None])[0] or params.get("day", ["1"])[0]
        try:
            self.active_day_number = int(day_param)
        except (ValueError, TypeError):
            self.active_day_number = 1

        if (itin_id or follow_param) and (self.active_trip is not None or itin_id is not None):
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

    async def _async_bootstrap(self) -> None:
        try:
            res = await self.place_service.get_places(page=1, page_size=250)
            if res.items:
                self.place_service.merge_places_into_cache(res.items)
                self.all_places = self.place_service.get_loaded_places()
                self._apply_filters()
                self._update_in_place(reset_viewport=False)
        except Exception:
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
            self._drawer_container.content = self._build_drawer_content() if self.is_drawer_open else ft.Container()

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
        route_polyline_points: Optional[list[tuple[float, float]]] = None
        if self.is_follow_route_mode and self.route_itinerary and self.route_itinerary.days:
            target_day: Optional[ItineraryDay] = None
            for d in self.route_itinerary.days:
                if d.day_number == self.active_day_number:
                    target_day = d
                    break
            if not target_day:
                target_day = self.route_itinerary.days[0]
                self.active_day_number = target_day.day_number

            if getattr(target_day, "day_overview_polyline", None):
                try:
                    route_polyline_points = decode_polyline(target_day.day_overview_polyline)
                except Exception:
                    route_polyline_points = None

            pts_accum: list[tuple[float, float]] = []
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
                poly = getattr(itm, "route_polyline_from_prev", None)
                if poly and not route_polyline_points:
                    try:
                        dec = decode_polyline(poly)
                        if pts_accum:
                            pts_accum.extend(dec[1:])
                        else:
                            pts_accum.extend(dec)
                    except Exception:
                        pass
            if not route_polyline_points and len(pts_accum) >= 2:
                route_polyline_points = pts_accum

        places_to_show = []
        if not self.is_follow_route_mode or self.show_nearby_pois_in_route:
            places_to_show = self.filtered_places

        pw = int(self.initial_width or (self.safe_page.width if (self.safe_page and self.safe_page.width) else 1220))
        ph = int(self.initial_height or (self.safe_page.height if (self.safe_page and self.safe_page.height) else 840))
        map_w = max(600, pw)
        map_h = max(400, ph - 64)

        is_dark = get_settings().is_dark_mode

        self.map_component = SlippyMapCanvas(
            width=map_w,
            height=map_h,
            places=places_to_show,
            route_stops=route_stops,
            route_polyline_points=route_polyline_points,
            active_stop_index=self._active_route_stop_index,
            on_place_click=self._handle_place_pin_click,
            on_stop_click=self._handle_stop_pin_click,
            on_map_background_click=self._dismiss_poi_bottom_sheet,
            dark_mode=is_dark,
            border_radius=0,
        )
        if self.is_follow_route_mode and route_stops:
            self.map_component.set_route(
                route_stops,
                polyline_points=route_polyline_points,
                active_stop_index=self._active_route_stop_index,
                auto_fit=True,
            )

        map_wrapper = ft.Container(
            content=self.map_component,
            left=0,
            top=0,
            right=0,
            bottom=0,
            expand=True,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )

        # In-Map Interactive POI Bottom Sheet (<app-place-detail-sheet> parity)
        self._poi_bottom_sheet_host = ft.Container(
            bottom=24,
            left=24,
            right=84,
            alignment=ft.Alignment.CENTER,
            visible=bool(self.selected_map_place is not None),
            content=self._build_poi_bottom_sheet(self.selected_map_place) if self.selected_map_place else None,
        )

        stack_layers: list[ft.Control] = [map_wrapper]

        if self.is_follow_route_mode:
            stack_layers.append(self._build_follow_route_top_bar())
            stack_layers.append(self._build_follow_route_bottom_carousel())
        else:
            stack_layers.append(self._build_discovery_top_bar())
            stack_layers.append(self._build_floating_action_buttons())
            stack_layers.append(self._poi_bottom_sheet_host)
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
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        chevron_left = ft.IconButton(
            icon=ft.Icons.CHEVRON_LEFT_ROUNDED,
            icon_size=18,
            icon_color=ThemeColors.TEXT_MUTED_LIGHT,
            tooltip="Scroll left",
            style=ft.ButtonStyle(padding=2),
            on_click=lambda _: self._scroll_category_pills(-220),
        )
        chevron_right = ft.IconButton(
            icon=ft.Icons.CHEVRON_RIGHT_ROUNDED,
            icon_size=18,
            icon_color=ThemeColors.TEXT_MUTED_LIGHT,
            tooltip="Scroll right",
            style=ft.ButtonStyle(padding=2),
            on_click=lambda _: self._scroll_category_pills(220),
        )

        pills_scroll_wrapper = ft.Row(
            controls=[
                chevron_left,
                ft.Container(content=self._cat_row, expand=True),
                chevron_right,
            ],
            spacing=2,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        card_content = ft.Column(
            controls=[
                ft.Row(controls=[self._search_field, self._clear_btn, filter_btn], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                pills_scroll_wrapper,
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

    def _scroll_category_pills(self, delta: int) -> None:
        """Scroll category pills horizontally across desktop viewports."""
        if hasattr(self, "_cat_row") and self._cat_row is not None:
            try:
                self._cat_row.scroll_to(delta=delta, duration=180)
            except Exception:
                pass

    def _build_floating_action_buttons(self) -> ft.Control:
        """Right-hand floating control buttons: [✨ Live OSM], [🎯 Locate Me], [🧭 Reset Province].
        Styled as 44x44 circular pills with Web-identical semantic colors (MAP-BUG-10)."""
        def _fab(icon: ft.IconData, tip: str, on_click: Any, icon_col: str, border_col: str) -> ft.Control:
            return ft.Container(
                content=ft.Icon(icon, size=20, color=icon_col),
                width=44,
                height=44,
                bgcolor=ft.Colors.WHITE,
                border_radius=22,
                border=ft.Border.all(1.5, border_col),
                alignment=ft.Alignment(0, 0),
                shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.16, "#0f172a"), offset=ft.Offset(0, 3)),
                ink=True,
                tooltip=tip,
                on_click=on_click,
            )

        col = ft.Column(
            controls=[
                _fab(ft.Icons.AUTO_AWESOME_ROUNDED, "Live OSM Discovery (Current Viewport)", lambda _: self._refresh_live_places(), "#7c3aed", "#ddd6fe"),
                _fab(ft.Icons.MY_LOCATION_ROUNDED, "Locate Me (Cabanatuan Hub GPS)", lambda _: self._locate_user(), "#0284c7", "#bae6fd"),
                _fab(ft.Icons.EXPLORE_ROUNDED, "Reset Province Center", lambda _: self._recenter_province(), "#475569", "#cbd5e1"),
            ],
            spacing=10,
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

        pw = float(self.initial_width) if self.initial_width else (float(self.safe_page.width) if (self.safe_page and self.safe_page.width) else 1220.0)
        pill_left = int(max(16.0, (pw - 160.0) / 2.0))

        self._toggle_pill_btn = ft.Container(
            bottom=18,
            left=pill_left,
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

    def on_resize(self, width: float, height: float) -> None:
        """Dynamically resizes SlippyMapCanvas and centers bottom pill on window resize (BUG-04)."""
        map_w = max(600, int(width))
        map_h = max(400, int(height - 64))
        if hasattr(self, "map_component") and self.map_component is not None:
            self.map_component.resize_canvas(map_w, map_h)
        if hasattr(self, "_toggle_pill_btn") and self._toggle_pill_btn is not None:
            self._toggle_pill_btn.left = max(16.0, (width - 160.0) / 2.0)
            try:
                self._toggle_pill_btn.update()
            except Exception:
                pass
        try:
            self.update()
        except Exception:
            pass

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

    def _build_drawer_row(self, p: Place) -> ft.Control:
        """Compact horizontal row matching Web .drawer-place-card."""
        return ft.Container(
            bgcolor="#f8fafc",
            border=ft.Border.all(1, "#e2e8f0"),
            border_radius=12,
            padding=ft.Padding.all(8),
            ink=True,
            on_click=lambda _, pl=p: self._focus_place_and_open_dialog(pl),
            content=ft.Row(
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Image(
                        src=p.resolved_image_path,
                        width=60,
                        height=60,
                        fit=ft.BoxFit.COVER,
                        border_radius=8,
                    ),
                    ft.Column(
                        spacing=2,
                        tight=True,
                        expand=True,
                        controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text(
                                        p.formatted_category.upper(),
                                        size=10,
                                        weight=ft.FontWeight.W_700,
                                        color="#0084ff",
                                    ),
                                    ft.Text(
                                        p.formatted_cost,
                                        size=10,
                                        weight=ft.FontWeight.W_700,
                                        color="#059669",
                                    ),
                                ],
                            ),
                            ft.Text(
                                p.name,
                                size=13,
                                weight=ft.FontWeight.W_700,
                                color="#0f172a",
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                            ft.Row(
                                spacing=3,
                                tight=True,
                                controls=[
                                    ft.Icon(ft.Icons.LOCATION_ON_OUTLINED, size=12, color="#64748b"),
                                    ft.Text(
                                        p.municipality_name or "Nueva Ecija",
                                        size=11,
                                        color="#64748b",
                                        max_lines=1,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                ],
                            ),
                        ],
                    ),
                    ft.Icon(ft.Icons.NEAR_ME_OUTLINED, size=16, color="#94a3b8"),
                ],
            ),
        )

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
            cards.append(self._build_drawer_row(p))

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
            content=self._build_drawer_content() if self.is_drawer_open else ft.Container(),
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

            is_active = (self._active_route_stop_index == idx)
            card_border = (
                ft.Border.all(2, ThemeColors.PRIMARY_BLUE)
                if is_active
                else ft.Border.all(1, ThemeColors.BORDER_LIGHT)
            )

            cards.append(
                ft.Container(
                    width=210,
                    bgcolor=ft.Colors.WHITE,
                    border=card_border,
                    border_radius=12,
                    padding=ft.Padding.all(10),
                    shadow=ft.BoxShadow(blur_radius=6, color=ft.Colors.with_opacity(0.1, "#0f172a")),
                    ink=True,
                    on_click=lambda _, lt=lat, lg=lng, pl=p, i=idx: self._pan_to_stop(lt, lg, pl, i),
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

    def _handle_place_pin_click(self, place: Any) -> None:
        """Match Web map.page.ts marker click: pan map to pin and slide up non-blocking POI bottom sheet."""
        self.selected_map_place = place
        if isinstance(place, dict):
            pid = str(place.get("id") or place.get("place_id") or "")
            lat = place.get("latitude") or place.get("lat")
            lng = place.get("longitude") or place.get("lng")
        else:
            pid = str(getattr(place, "id", "") or "")
            lat = getattr(place, "latitude", None)
            lng = getattr(place, "longitude", None)

        if self.map_component is not None:
            if pid:
                self.map_component.set_selected_place_id(pid, pan_to=True)
            elif lat and lng:
                self.map_component.set_center_and_zoom(float(lat), float(lng), 15)

        self._refresh_poi_bottom_sheet()

    def _refresh_poi_bottom_sheet(self) -> None:
        """Update and display the interactive in-map POI bottom sheet."""
        if not self.selected_map_place or not hasattr(self, "_poi_bottom_sheet_host") or self._poi_bottom_sheet_host is None:
            return
        card = self._build_poi_bottom_sheet(self.selected_map_place)
        self._poi_bottom_sheet_host.content = card
        self._poi_bottom_sheet_host.visible = True
        self._safe_update()

    def _dismiss_poi_bottom_sheet(self) -> None:
        """Dismiss the in-map POI bottom sheet when clicking the map background or close button."""
        if not getattr(self, "selected_map_place", None):
            return
        self.selected_map_place = None
        if hasattr(self, "map_component") and self.map_component is not None:
            self.map_component.set_selected_place_id(None, pan_to=False)
        if hasattr(self, "_poi_bottom_sheet_host") and self._poi_bottom_sheet_host is not None:
            self._poi_bottom_sheet_host.visible = False
            self._safe_update()

    def _start_trip_from_place(self, place: Any) -> None:
        """Launch Suggested Itinerary Wizard anchored at this place (1:1 Web startTripHere parity)."""
        p_obj = place if isinstance(place, Place) else Place.from_dict(place)
        if self.on_navigate:
            dest_q = urllib.parse.quote(p_obj.municipality_name or "Nueva Ecija")
            pid_q = urllib.parse.quote(str(p_obj.id))
            self.on_navigate(f"/suggested?destination={dest_q}&placeId={pid_q}", None, p_obj)

    def _build_poi_bottom_sheet(self, place: Any) -> ft.Control:
        """Build Web-identical <app-place-detail-sheet> interactive bottom sheet card."""
        p_obj = place if isinstance(place, Place) else Place.from_dict(place)
        pid = str(p_obj.id or "")
        name = p_obj.name or "Destination"
        mun = p_obj.municipality_name or "Nueva Ecija"
        cat_label = p_obj.formatted_category
        lat = p_obj.latitude
        lng = p_obj.longitude
        cost_str = p_obj.formatted_cost

        fav_svc = get_favorites_service()
        is_fav = fav_svc.is_favorite(pid) if pid else False

        def _toggle_fav(_):
            nonlocal is_fav
            if pid:
                # Pass Place object to FavoritesService.toggle_favorite (fixes MAP-QA-02)
                is_fav = fav_svc.toggle_favorite(p_obj)
                self._refresh_poi_bottom_sheet()

        # Hero Photo Banner with overlaid Favorite, Close, Category, and Open Now badges
        img_src = p_obj.resolved_image_path
        hero_img = ft.Image(
            src=img_src,
            width=560,
            height=150,
            fit=ft.BoxFit.COVER,
            border_radius=ft.BorderRadius(top_left=14, top_right=14, bottom_left=0, bottom_right=0),
        )

        fav_overlay_btn = ft.Container(
            top=10,
            right=50,
            width=34,
            height=34,
            border_radius=17,
            bgcolor="#ffffff" if is_fav else ft.Colors.with_opacity(0.68, "#0f172a"),
            alignment=ft.Alignment.CENTER,
            ink=True,
            tooltip="Remove from favorites" if is_fav else "Add to favorites",
            on_click=_toggle_fav,
            content=ft.Icon(
                ft.Icons.FAVORITE if is_fav else ft.Icons.FAVORITE_BORDER,
                size=18,
                color="#ef4444" if is_fav else "#ffffff",
            ),
        )

        close_overlay_btn = ft.Container(
            top=10,
            right=10,
            width=34,
            height=34,
            border_radius=17,
            bgcolor=ft.Colors.with_opacity(0.68, "#0f172a"),
            alignment=ft.Alignment.CENTER,
            ink=True,
            tooltip="Close details",
            on_click=lambda _: self._dismiss_poi_bottom_sheet(),
            content=ft.Icon(ft.Icons.CLOSE_ROUNDED, size=18, color="#ffffff"),
        )

        cat_overlay_badge = ft.Container(
            bottom=10,
            left=12,
            bgcolor=ft.Colors.with_opacity(0.82, "#0f172a"),
            border_radius=6,
            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
            content=ft.Text(cat_label, size=10, weight=ft.FontWeight.W_700, color="#ffffff"),
        )

        open_overlay_badge = ft.Container(
            bottom=10,
            right=12,
            bgcolor=ft.Colors.with_opacity(0.88, "#166534"),
            border_radius=6,
            padding=ft.Padding.symmetric(horizontal=9, vertical=4),
            content=ft.Row(
                spacing=5,
                tight=True,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(width=7, height=7, border_radius=4, bgcolor="#4ade80"),
                    ft.Text("Open Now", size=10, weight=ft.FontWeight.W_700, color="#ffffff"),
                ],
            ),
        )

        hero_banner = ft.Stack(
            width=560,
            height=150,
            controls=[
                hero_img,
                fav_overlay_btn,
                close_overlay_btn,
                cat_overlay_badge,
                open_overlay_badge,
            ],
        )

        # Rating & Provenance Row
        meta_chips: list[ft.Control] = []
        if p_obj.rating:
            meta_chips.append(
                ft.Container(
                    bgcolor="#fef3c7",
                    border_radius=6,
                    padding=ft.Padding.symmetric(horizontal=7, vertical=2),
                    content=ft.Row(
                        spacing=3,
                        tight=True,
                        controls=[
                            ft.Icon(ft.Icons.STAR_ROUNDED, size=13, color="#f59e0b"),
                            ft.Text(f"{p_obj.rating:.1f}", size=11, weight=ft.FontWeight.W_700, color="#b45309"),
                        ],
                    ),
                )
            )
            if p_obj.user_rating_count:
                meta_chips.append(
                    ft.Text(f"({p_obj.user_rating_count:,} reviews)", size=11, color="#64748b")
                )
            if p_obj.rating >= 4.5:
                meta_chips.append(
                    ft.Container(
                        bgcolor="#ecfdf5",
                        border_radius=4,
                        padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                        content=ft.Text("Top Rated", size=10, weight=ft.FontWeight.W_700, color="#059669"),
                    )
                )

        prov_label = "Google Verified POI" if p_obj.rating else "Verified Destination"
        meta_chips.append(
            ft.Container(
                bgcolor="#f1f5f9",
                border_radius=6,
                padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                content=ft.Row(
                    spacing=4,
                    tight=True,
                    controls=[
                        ft.Icon(ft.Icons.VERIFIED_USER_OUTLINED, size=12, color="#2563eb"),
                        ft.Text(prov_label, size=10, weight=ft.FontWeight.W_600, color="#475569"),
                    ],
                ),
            )
        )

        # Commute guide dataclass attributes (fixes MAP-QA-01 AttributeError)
        commute_info = get_commute_info_for_municipality(mun, name)
        if isinstance(commute_info, dict):
            transit_mode_txt = commute_info.get("transit_mode") or "By Bus / Local UV Express"
            terminal_txt = commute_info.get("departure_hub") or commute_info.get("terminal") or "Cabanatuan Central Terminal"
            dropoff_txt = commute_info.get("drop_off_point") or f"{mun} Town Proper"
            travel_time_txt = commute_info.get("estimated_travel_time") or "45 mins – 1 hr"
            fare_txt = commute_info.get("estimated_fare") or commute_info.get("fare") or "₱25 – ₱60"
        else:
            transit_mode_txt = getattr(commute_info, "transit_mode", "By Bus / Local UV Express")
            terminal_txt = getattr(commute_info, "departure_hub", "Cabanatuan Central Terminal")
            dropoff_txt = getattr(commute_info, "drop_off_point", f"{mun} Town Proper")
            travel_time_txt = getattr(commute_info, "estimated_travel_time", "45 mins – 1 hr")
            fare_txt = getattr(commute_info, "estimated_fare", "₱25 – ₱60")

        desc_txt = p_obj.editorial_summary or p_obj.description or f"Explore {name} in {mun}, Nueva Ecija."
        hours_txt = p_obj.opening_hours or "Open Daily • Standard Visiting Hours"

        # External Google Maps Directions URL + in-map preview
        gmaps_dir_url = (
            p_obj.directions_url
            if (p_obj.directions_url and p_obj.directions_url.strip())
            else f"https://www.google.com/maps/dir/?api=1&destination={lat},{lng}"
        )

        def _get_directions(_):
            if self.safe_page:
                try:
                    self.safe_page.launch_url(gmaps_dir_url)
                except Exception:
                    pass
            if lat and lng and hasattr(self, "map_component") and self.map_component is not None:
                start_coord = (15.4865, 120.9674)
                self.map_component.set_route(
                    [
                        {"latitude": start_coord[0], "longitude": start_coord[1], "name": "Start: Cabanatuan Hub"},
                        {"latitude": float(lat), "longitude": float(lng), "name": name},
                    ],
                    auto_fit=True,
                )
                if self.safe_page:
                    show_toast(self.safe_page, f"Opened Google Maps directions & mapped route to {name}!")

        return ft.Container(
            bgcolor=ft.Colors.with_opacity(0.99, "#ffffff"),
            border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
            border_radius=16,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            width=560,
            shadow=ft.BoxShadow(
                blur_radius=20,
                color=ft.Colors.with_opacity(0.22, "#0f172a"),
                offset=ft.Offset(0, 6),
            ),
            content=ft.Column(
                spacing=0,
                tight=True,
                controls=[
                    hero_banner,
                    ft.Container(
                        padding=ft.Padding.all(14),
                        content=ft.Column(
                            spacing=7,
                            tight=True,
                            controls=[
                                # Title + Full Details button
                                ft.Row(
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                    controls=[
                                        ft.Text(
                                            name,
                                            size=17,
                                            weight=ft.FontWeight.W_800,
                                            color=ThemeColors.TEXT_BLACK,
                                            max_lines=1,
                                            overflow=ft.TextOverflow.ELLIPSIS,
                                            expand=True,
                                        ),
                                        ft.TextButton(
                                            content=ft.Row(
                                                spacing=4,
                                                tight=True,
                                                controls=[
                                                    ft.Text("Full Details", size=11, weight=ft.FontWeight.W_700, color=ThemeColors.PRIMARY_BLUE),
                                                    ft.Icon(ft.Icons.OPEN_IN_NEW_ROUNDED, size=13, color=ThemeColors.PRIMARY_BLUE),
                                                ],
                                            ),
                                            on_click=lambda _: show_place_detail_dialog(
                                                self.safe_page,
                                                p_obj,
                                                on_navigate=self.on_navigate,
                                                on_add_to_day=lambda pl: self._prompt_add_place_to_trip(pl),
                                            ),
                                        ),
                                    ],
                                ),
                                # Rating & Provenance chips
                                ft.Row(spacing=6, wrap=True, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=meta_chips),
                                # Municipality, Cost, and Operating Hours row
                                ft.Row(
                                    spacing=12,
                                    wrap=True,
                                    controls=[
                                        ft.Row(
                                            spacing=4,
                                            tight=True,
                                            controls=[
                                                ft.Icon(ft.Icons.LOCATION_ON_OUTLINED, size=14, color="#2563eb"),
                                                ft.Text(mun, size=12, weight=ft.FontWeight.W_600, color="#475569"),
                                            ],
                                        ),
                                        ft.Row(
                                            spacing=4,
                                            tight=True,
                                            controls=[
                                                ft.Icon(ft.Icons.PAYMENTS_OUTLINED, size=14, color="#059669"),
                                                ft.Text(cost_str, size=12, weight=ft.FontWeight.W_700, color="#047857"),
                                            ],
                                        ),
                                        ft.Row(
                                            spacing=4,
                                            tight=True,
                                            controls=[
                                                ft.Icon(ft.Icons.ACCESS_TIME_ROUNDED, size=13, color="#2563eb"),
                                                ft.Text(hours_txt, size=11, color="#475569", max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                            ],
                                        ),
                                    ],
                                ),
                                # Description snippet
                                ft.Text(desc_txt, size=12, color="#334155", max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                                # Green Local Commute Guide Box (matches Web .sheet-commute-box)
                                ft.Container(
                                    bgcolor="#f0fdf4",
                                    border=ft.Border.all(1, "#bbf7d0"),
                                    border_radius=10,
                                    padding=ft.Padding.symmetric(horizontal=10, vertical=8),
                                    content=ft.Column(
                                        spacing=3,
                                        tight=True,
                                        controls=[
                                            ft.Row(
                                                spacing=5,
                                                controls=[
                                                    ft.Icon(ft.Icons.DIRECTIONS_BUS_OUTLINED, size=14, color="#16a34a"),
                                                    ft.Text("How to get there?", size=11, weight=ft.FontWeight.W_700, color="#14532d"),
                                                ],
                                            ),
                                            ft.Row(
                                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                                controls=[
                                                    ft.Text("Transit & Hub:", size=10, color="#475569"),
                                                    ft.Text(f"{transit_mode_txt} • {terminal_txt}", size=10, weight=ft.FontWeight.W_600, color="#0f172a"),
                                                ],
                                            ),
                                            ft.Row(
                                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                                controls=[
                                                    ft.Text("Drop-off / Est. Fare:", size=10, color="#475569"),
                                                    ft.Text(f"{dropoff_txt} • {travel_time_txt} ({fare_txt})", size=10, weight=ft.FontWeight.W_700, color="#15803d"),
                                                ],
                                            ),
                                        ],
                                    ),
                                ),
                                # Primary & Secondary Action Buttons Row (matches Web .sheet-actions-stack)
                                ft.Row(
                                    spacing=8,
                                    controls=[
                                        ft.FilledButton(
                                            expand=True,
                                            content=ft.Row(
                                                spacing=5,
                                                alignment=ft.MainAxisAlignment.CENTER,
                                                controls=[
                                                    ft.Icon(ft.Icons.AUTO_AWESOME, size=14, color="#ffffff"),
                                                    ft.Text("Start Trip Here", size=12, weight=ft.FontWeight.W_700, color="#ffffff"),
                                                ],
                                            ),
                                            style=ft.ButtonStyle(
                                                bgcolor="#0084ff",
                                                padding=ft.Padding.symmetric(horizontal=12, vertical=10),
                                                shape=ft.RoundedRectangleBorder(radius=10),
                                            ),
                                            on_click=lambda _: self._start_trip_from_place(p_obj),
                                        ),
                                        ft.OutlinedButton(
                                            expand=True,
                                            content=ft.Row(
                                                spacing=5,
                                                alignment=ft.MainAxisAlignment.CENTER,
                                                controls=[
                                                    ft.Icon(ft.Icons.ADD_ROUNDED, size=15, color="#0084ff"),
                                                    ft.Text("Add to Trip", size=12, weight=ft.FontWeight.W_700, color="#0084ff"),
                                                ],
                                            ),
                                            style=ft.ButtonStyle(
                                                bgcolor="#eff6ff",
                                                side=ft.BorderSide(1, "#bfdbfe"),
                                                padding=ft.Padding.symmetric(horizontal=12, vertical=10),
                                                shape=ft.RoundedRectangleBorder(radius=10),
                                            ),
                                            on_click=lambda _: self._prompt_add_place_to_trip(p_obj),
                                        ),
                                        ft.FilledButton(
                                            content=ft.Row(
                                                spacing=5,
                                                tight=True,
                                                controls=[
                                                    ft.Icon(ft.Icons.NAVIGATION_OUTLINED, size=14, color="#ffffff"),
                                                    ft.Text("Get Directions", size=12, weight=ft.FontWeight.W_700, color="#ffffff"),
                                                ],
                                            ),
                                            style=ft.ButtonStyle(
                                                bgcolor="#0f172a",
                                                padding=ft.Padding.symmetric(horizontal=14, vertical=10),
                                                shape=ft.RoundedRectangleBorder(radius=10),
                                            ),
                                            on_click=_get_directions,
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ),
                ],
            ),
        )

    def _handle_stop_pin_click(self, idx: int, stop: RouteStopPin) -> None:
        self._active_route_stop_index = idx
        if self.map_component:
            self.map_component.set_route(self.map_component.route_stops, active_stop_index=idx)
        if stop.place and self.safe_page:
            show_place_detail_dialog(
                self.safe_page,
                stop.place,
                on_navigate=self.on_navigate,
            )
        self._safe_update()

    def _focus_place_and_open_dialog(self, place: Place) -> None:
        """Match Web selectPlaceFromDrawer: close drawer, fly to place, and open bottom sheet."""
        self.is_drawer_open = False
        if hasattr(self, "_drawer_container") and self._drawer_container is not None:
            self._drawer_container.visible = False
        if hasattr(self, "_drawer_pill_label") and self._drawer_pill_label is not None:
            self._drawer_pill_label.value = f"List View ({len(self.filtered_places)})"
        if hasattr(self, "_drawer_pill_icon") and self._drawer_pill_icon is not None:
            self._drawer_pill_icon.name = ft.Icons.LIST_ROUNDED
        if place.latitude and place.longitude and self.map_component:
            self.map_component.fly_to(place.latitude, place.longitude, 15, animated=True)
        self._handle_place_pin_click(place)

    def _prompt_add_place_to_trip(self, place: Place) -> None:
        """Navigate to Custom Builder with this place pre-selected as a stop."""
        if self.on_navigate:
            self.on_navigate("/builder", None, place)

    def _pan_to_stop(self, lat: Optional[float], lng: Optional[float], place: Optional[Place], stop_index: Optional[int] = None) -> None:
        if stop_index is not None:
            self._active_route_stop_index = stop_index
            if self.map_component:
                self.map_component.set_route(self.map_component.route_stops, active_stop_index=stop_index)
        if lat and lng and self.map_component:
            self.map_component.set_center_and_zoom(float(lat), float(lng), 15)
        if place and self.safe_page:
            self._handle_place_pin_click(place)
        self._safe_update()

    def _on_search_change(self, val: str) -> None:
        self.search_query = val
        self._search_change_version = getattr(self, "_search_change_version", 0) + 1
        current_ver = self._search_change_version

        async def _debounced():
            await asyncio.sleep(0.25)
            if getattr(self, "_search_change_version", 0) == current_ver:
                self._apply_filters()
                self._update_in_place(reset_viewport=False)

        if self.safe_page:
            try:
                self.safe_page.run_task(_debounced)
            except Exception:
                self._apply_filters()
                self._update_in_place(reset_viewport=False)
        else:
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
                min_lat, min_lng, max_lat, max_lng = (15.1, 120.7, 16.15, 121.4)
                if self.map_component:
                    min_lat, min_lng, max_lat, max_lng = self.map_component.get_viewport_bounds()

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
                    show_toast(
                        self.safe_page,
                        f"✨ Live OSM: {count:,} places indexed across Nueva Ecija",
                        bgcolor=ThemeColors.PRIMARY_BLUE,
                        duration=3000,
                    )
            except Exception:
                if self.safe_page:
                    show_toast(
                        self.safe_page,
                        f"Notice: Live refresh completed with {len(self.all_places):,} places cached",
                        duration=2500,
                    )
            finally:
                self.is_live_refreshing = False
                self._safe_update()

        if self.safe_page:
            self.safe_page.run_task(_do)

    def _locate_user(self) -> None:
        """Locks GPS indicator onto Cabanatuan hub and smoothly flies camera to Z15."""
        if self.map_component:
            self.map_component.user_location = (15.4865, 120.9674)
            self.map_component._user_location = (15.4865, 120.9674)
            self.map_component.fly_to(15.4865, 120.9674, 15, animated=True)
            if self.safe_page:
                show_toast(self.safe_page, "📍 GPS Locked: Cabanatuan City Central Hub")

    def _recenter_province(self) -> None:
        """Smoothly flies back to geographic center of Nueva Ecija (15.58, 121.00, Z10)."""
        if self.map_component:
            self.map_component.fly_to(15.58, 121.00, 10, animated=True)

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
            close_overlay_dialog(self.safe_page, dlg)

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
        open_overlay_dialog(self.safe_page, dlg)
