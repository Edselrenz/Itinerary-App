"""Full-Bleed Map Explorer and Destination Catalog View mirroring Ionic tabs/map.

Directly ports the architecture from Project/src/app/tabs/map/:
- 100% Full-Bleed interactive SlippyMapCanvas (expand=True)
- Floating Top Search & 17 Category Filter Pills Bar (.map-top-bar)
- Floating Right Action Buttons: [✨ Live OSM], [🎯 Locate Me (GPS)], [🧭 Reset Province View]
- Floating Bottom-Center "List View (N)" Pill opening Collapsible POI List Drawer
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
from desktop_client.config.settings import CANONICAL_CATEGORIES, ThemeColors
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

        # Search & Filter State
        self.search_query = ""
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
        return getattr(self, "page", None)

    def _check_and_init_route_mode(self) -> None:
        """Determines if /map was launched with an itinerary route parameter."""
        parsed = urllib.parse.urlparse(self.route_query)
        params = urllib.parse.parse_qs(parsed.query)

        itin_id = params.get("itineraryId", [None])[0]
        day_param = params.get("day", ["1"])[0]
        try:
            self.active_day_number = int(day_param)
        except ValueError:
            self.active_day_number = 1

        if itin_id:
            self.is_follow_route_mode = True
            if self.active_trip and (self.active_trip.id == itin_id or itin_id == "draft"):
                self.route_itinerary = self.active_trip
            else:
                self.route_itinerary = self.itinerary_service.get_itinerary_or_draft(itin_id)
        elif self.active_trip:
            self.is_follow_route_mode = True
            self.route_itinerary = self.active_trip

    def _async_bootstrap(self) -> None:
        async def _load():
            try:
                # Refresh places from service / backend if available
                res = await self.place_service.get_places(page=1, page_size=250)
                if res.items:
                    self.place_service.merge_places_into_cache(res.items)
                    self.all_places = self.place_service.get_loaded_places()
                    self._apply_filters()
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

        if self.selected_category != "all":
            results = [p for p in results if p.category == self.selected_category]

        if self.selected_municipality != "all":
            m_low = self.selected_municipality.lower()
            results = [
                p for p in results
                if m_low in (p.municipality_name or "").lower() or m_low in (p.municipality_id or "").lower()
            ]

        if self.selected_price_tier != "all":
            if self.selected_price_tier == "free":
                results = [p for p in results if p.estimated_cost_min == 0 and (p.estimated_cost_max or 0) == 0]
            elif self.selected_price_tier == "budget":
                results = [p for p in results if (p.estimated_cost_min or 0) <= 500]
            elif self.selected_price_tier == "mid":
                results = [p for p in results if (p.estimated_cost_min or 0) > 500]

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
        if self.map_component:
            if self.is_follow_route_mode and not self.show_nearby_pois_in_route:
                self.map_component.set_places([])
            else:
                self.map_component.set_places(self.filtered_places)
        self._safe_update()

    def _safe_update(self) -> None:
        try:
            if self.safe_page:
                self.update()
        except Exception:
            pass

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
            width=1240,
            height=740,
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

        # 2. Top Controls
        if self.is_follow_route_mode:
            stack_layers.append(self._build_follow_route_top_bar())
            stack_layers.append(self._build_follow_route_bottom_carousel())
        else:
            stack_layers.append(self._build_discovery_top_bar())
            stack_layers.append(self._build_floating_action_buttons())
            stack_layers.append(self._build_drawer_toggle_pill())
            if self.is_drawer_open:
                stack_layers.append(self._build_poi_drawer())

        self.content = ft.Stack(
            controls=stack_layers,
            expand=True,
        )

    # =========================================================================
    # DISCOVERY MODE CONTROLS
    # =========================================================================

    def _build_discovery_top_bar(self) -> ft.Control:
        """Floating Top Search & 17 Category Filter Pills Bar."""
        search_field = ft.TextField(
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

        clear_btn = ft.IconButton(
            icon=ft.Icons.CLEAR_ROUNDED,
            icon_size=16,
            icon_color=ThemeColors.TEXT_MUTED_LIGHT,
            tooltip="Clear Search",
            visible=bool(self.search_query),
            on_click=lambda _: self._clear_search(),
        )

        filter_btn = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.TUNE_ROUNDED, size=15, color=ThemeColors.PRIMARY_BLUE),
                    ft.Text("Filters", size=12, weight=ft.FontWeight.BOLD, color=ThemeColors.PRIMARY_BLUE),
                ],
                spacing=4,
            ),
            bgcolor=ThemeColors.AZURE_SOFT,
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=10, vertical=8),
            ink=True,
            on_click=lambda _: self._open_filter_modal(),
        )

        # 17 Category Filter Pills matching Web App (.quick-category-pills)
        cat_pills: list[ft.Control] = []
        all_active = self.selected_category == "all"
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
            is_active = self.selected_category == c_key
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

        cat_row = ft.Row(
            controls=cat_pills,
            spacing=6,
            scroll=ft.ScrollMode.HIDDEN,
        )

        card_content = ft.Column(
            controls=[
                ft.Row(controls=[search_field, clear_btn, filter_btn], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                cat_row,
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
                _btn(ft.Icons.AUTO_AWESOME_ROUNDED, "Live OSM Discovery (Refresh POIs)", lambda _: self._refresh_live_places()),
                _btn(ft.Icons.MY_LOCATION_ROUNDED, "Locate Me (Cabanatuan Hub GPS)", lambda _: self._locate_user()),
                _btn(ft.Icons.EXPLORE_ROUNDED, "Reset Province Center", lambda _: self._recenter_province()),
            ],
            spacing=8,
            tight=True,
        )

        return ft.Container(
            right=16,
            bottom=90,
            content=col,
        )

    def _build_drawer_toggle_pill(self) -> ft.Control:
        """Bottom-center floating pill that opens/closes the POI List Drawer."""
        count = len(self.filtered_places)
        return ft.Container(
            bottom=18,
            left=0,
            right=0,
            alignment=ft.Alignment(0, 1),
            content=ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(
                            ft.Icons.KEYBOARD_ARROW_DOWN_ROUNDED if self.is_drawer_open else ft.Icons.LIST_ROUNDED,
                            size=18,
                            color=ft.Colors.WHITE,
                        ),
                        ft.Text(
                            f"List View ({count})" if not self.is_drawer_open else "Close List View",
                            size=12,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE,
                        ),
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

    def _build_poi_drawer(self) -> ft.Control:
        """Collapsible horizontal destinations carousel drawer over bottom of map."""
        cards: list[ft.Control] = []
        for p in self.filtered_places[:60]:
            cards.append(
                ft.Container(
                    width=240,
                    height=200,
                    content=PlaceCard(
                        place=p,
                        compact=True,
                        on_click=lambda pl: self._focus_place_and_open_dialog(pl),
                    ),
                )
            )

        track = ft.Row(
            controls=cards,
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
        )

        return ft.Container(
            bottom=64,
            left=16,
            right=16,
            height=220,
            bgcolor=ft.Colors.with_opacity(0.96, "#ffffff"),
            border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
            border_radius=16,
            padding=ft.Padding.all(12),
            shadow=ft.BoxShadow(blur_radius=16, color=ft.Colors.with_opacity(0.18, "#0f172a"), offset=ft.Offset(0, -4)),
            content=ft.Column(
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
            ),
        )

    # =========================================================================
    # FOLLOW-ROUTE MODE CONTROLS
    # =========================================================================

    def _build_follow_route_top_bar(self) -> ft.Control:
        """Floating active route header bar with day switcher and [Show Nearby POIs] toggle."""
        itin = self.route_itinerary
        title = itin.title if itin else "Itinerary Route"
        num_days = len(itin.days) if itin and itin.days else 1

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
        items = target_day.items if target_day else []
        gmaps_url = get_multi_stop_google_maps_url(items)

        cards: list[ft.Control] = []
        for idx, it in enumerate(items):
            p = it.place
            title = it.custom_title or (p.name if p else f"Stop {idx + 1}")
            time_str = it.planned_time or ""
            lat = (p.latitude if p and p.latitude else None) or it.custom_lat
            lng = (p.longitude if p and p.longitude else None) or it.custom_lng

            cards.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Text(str(idx + 1), size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                bgcolor=ThemeColors.PRIMARY_BLUE,
                                border_radius=12,
                                width=24,
                                height=24,
                                alignment=ft.Alignment(0, 0),
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text(title, size=12, weight=ft.FontWeight.BOLD, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                    ft.Text(time_str or f"{it.duration_minutes} mins", size=10, color=ThemeColors.TEXT_MUTED_LIGHT),
                                ],
                                spacing=1,
                                tight=True,
                            ),
                        ],
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    bgcolor=ft.Colors.WHITE,
                    border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
                    border_radius=10,
                    padding=ft.Padding.symmetric(horizontal=12, vertical=8),
                    shadow=ft.BoxShadow(blur_radius=6, color=ft.Colors.with_opacity(0.08, "#000000")),
                    ink=True,
                    on_click=lambda _, lt=lat, lg=lng, p_obj=p: self._pan_to_stop(lt, lg, p_obj),
                )
            )

        gmaps_btn = ft.FilledButton(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.DIRECTIONS_ROUNDED, size=15),
                    ft.Text("Google Maps Navigation", size=11, weight=ft.FontWeight.BOLD),
                ],
                spacing=4,
                tight=True,
            ),
            url=gmaps_url if gmaps_url else None,
            style=ft.ButtonStyle(
                bgcolor=ThemeColors.PRIMARY_BLUE,
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=10),
            ),
        )

        return ft.Container(
            bottom=14,
            left=16,
            right=16,
            bgcolor=ft.Colors.with_opacity(0.96, "#ffffff"),
            border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
            border_radius=14,
            padding=ft.Padding.symmetric(horizontal=14, vertical=10),
            shadow=ft.BoxShadow(blur_radius=12, color=ft.Colors.with_opacity(0.15, "#0f172a"), offset=ft.Offset(0, -3)),
            content=ft.Row(
                controls=[
                    ft.Row(controls=cards, spacing=8, scroll=ft.ScrollMode.AUTO, expand=True),
                    gmaps_btn,
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    # =========================================================================
    # ACTIONS & EVENT HANDLERS
    # =========================================================================

    def _handle_place_pin_click(self, place: Place) -> None:
        """Opens place detail dialog on marker pin click without TypeError."""
        if self.safe_page:
            show_place_detail_dialog(
                self.safe_page,
                place,
                on_add_to_day=lambda pl: self.on_navigate("/builder", pre_added_place=pl) if self.on_navigate else None,
                on_navigate=self.on_navigate,
            )

    def _handle_stop_pin_click(self, idx: int, stop: RouteStopPin) -> None:
        if stop.place and self.safe_page:
            show_place_detail_dialog(
                self.safe_page,
                stop.place,
                on_add_to_day=lambda pl: self.on_navigate("/builder", pre_added_place=pl) if self.on_navigate else None,
                on_navigate=self.on_navigate,
            )

    def _focus_place_and_open_dialog(self, place: Place) -> None:
        if self.map_component and place.latitude and place.longitude:
            self.map_component.set_center_and_zoom(place.latitude, place.longitude, 15)
        self._handle_place_pin_click(place)

    def _pan_to_stop(self, lat: Optional[float], lng: Optional[float], place: Optional[Place]) -> None:
        if lat and lng and self.map_component:
            self.map_component.set_center_and_zoom(float(lat), float(lng), 15)
        if place and self.safe_page:
            self._handle_place_pin_click(place)

    def _on_search_change(self, val: str) -> None:
        self.search_query = val
        self._apply_filters()

    def _clear_search(self) -> None:
        self.search_query = ""
        self._apply_filters()

    def _select_category(self, cat_key: str) -> None:
        self.selected_category = cat_key
        self._apply_filters()

    def _toggle_drawer(self) -> None:
        self.is_drawer_open = not self.is_drawer_open
        self._build_content()
        self._safe_update()

    def _refresh_live_places(self) -> None:
        self.is_live_refreshing = True

        async def _do():
            try:
                res = await self.place_service.get_places(page=1, page_size=250)
                if res.items:
                    self.place_service.merge_places_into_cache(res.items)
                    self.all_places = self.place_service.get_loaded_places()
                    self._apply_filters()
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
        if self.route_query.startswith("/map?itineraryId=draft") or ("draft" in self.route_query):
            self.on_navigate("/suggested")
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
        """Opens advanced multi-select filter modal."""
        if not self.safe_page:
            return

        cat_chips: list[ft.Control] = []
        for cat in CANONICAL_CATEGORIES:
            ck = cat["key"]
            is_c = (self.selected_category == ck)
            cat_chips.append(
                ft.FilterChip(
                    label=ft.Text(cat["label"], size=11),
                    selected=is_c,
                    on_select=lambda e, k=ck: self._set_modal_cat(k),
                )
            )

        tier_options = [
            ft.dropdown.Option("all", "All Prices"),
            ft.dropdown.Option("free", "Free Admission (₱0)"),
            ft.dropdown.Option("budget", "Budget (≤ ₱500)"),
            ft.dropdown.Option("mid", "Mid-Range (> ₱500)"),
        ]
        tier_dropdown = ft.Dropdown(
            label="Price Tier",
            options=tier_options,
            value=self.selected_price_tier,
            dense=True,
            on_change=lambda e: setattr(self, "selected_price_tier", e.control.value),
        )

        dlg = ft.AlertDialog(
            title=ft.Text("Filters & Regional Settings"),
            content=ft.Column(
                controls=[
                    ft.Text("Categories", size=12, weight=ft.FontWeight.BOLD),
                    ft.Row(controls=cat_chips, wrap=True, spacing=6),
                    ft.Container(height=8),
                    tier_dropdown,
                ],
                tight=True,
                spacing=8,
                scroll=ft.ScrollMode.AUTO,
            ),
            actions=[
                ft.TextButton("Reset Filters", on_click=lambda _: self._reset_filters_and_close(dlg)),
                ft.FilledButton("Apply Filters", on_click=lambda _: self._apply_filters_and_close(dlg)),
            ],
        )
        self.safe_page.pop_dialog()
        self.safe_page.dialog = dlg
        dlg.open = True
        self.safe_page.update()

    def _set_modal_cat(self, cat_key: str) -> None:
        self.selected_category = cat_key

    def _reset_filters_and_close(self, dlg: ft.AlertDialog) -> None:
        self.selected_category = "all"
        self.selected_municipality = "all"
        self.selected_price_tier = "all"
        dlg.open = False
        if self.safe_page:
            self.safe_page.update()
        self._apply_filters()
        self._build_content()
        self._safe_update()

    def _apply_filters_and_close(self, dlg: ft.AlertDialog) -> None:
        dlg.open = False
        if self.safe_page:
            self.safe_page.update()
        self._apply_filters()
        self._build_content()
        self._safe_update()
