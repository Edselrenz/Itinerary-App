"""Nueva Ecija Travel — Interactive GIS Province Map Component.

Supports dual-engine mapping:
1. Primary Engine: flet_map (Map, TileLayer, MarkerLayer, PolylineLayer) with OSM raster tiles.
2. Fallback Engine: Vector ft.canvas.Canvas rendering when tiles are unreachable or offline.

Features:
- 16 category-colored destination pins
- Numbered route stop badges (1..N) with stop detail invocation
- Encoded polyline route drawing and geodesic arc generation
- Camera controls: Zoom In/Out, Recenter Province, Locate Hub, Follow-Route
"""

import asyncio
import math
from typing import Any, Callable, Optional
import flet as ft
import flet_map as fm

from desktop_client.config.settings import ThemeColors
from desktop_client.core.polyline import (
    decode_polyline,
    generate_geodesic_arc,
    haversine_distance_meters,
)
from desktop_client.models.place import Place

# Nueva Ecija Geographic Bounds & Center
NUEVA_ECIJA_CENTER_LAT = 15.5800
NUEVA_ECIJA_CENTER_LNG = 121.0500
CABANATUAN_HUB_LAT = 15.4859
CABANATUAN_HUB_LNG = 120.9671

PROVINCE_BOUNDS = {
    "min_lat": 15.10,
    "max_lat": 16.15,
    "min_lng": 120.65,
    "max_lng": 121.45,
}

CATEGORY_COLOR_MAP: dict[str, str] = {
    "nature_park": "#10b981",
    "tourist_attraction": "#0284c7",
    "museum_cultural": "#8b5cf6",
    "church_religious": "#a855f7",
    "resort_swimming": "#06b6d4",
    "restaurant": "#f97316",
    "cafe": "#d97706",
    "hotel_accommodation": "#ec4899",
    "shopping_market": "#14b8a6",
    "transport_terminal": "#64748b",
    "hospital_clinic": "#ef4444",
    "pharmacy": "#f43f5e",
    "bank_atm": "#15803d",
    "fuel_station": "#eab308",
    "convenience_store": "#3b82f6",
    "public_facility": "#6b7280",
}

CATEGORY_ICON_MAP: dict[str, str] = {
    "nature_park": ft.Icons.PARK,
    "tourist_attraction": ft.Icons.ATTRACTIONS,
    "museum_cultural": ft.Icons.MUSEUM,
    "church_religious": ft.Icons.CHURCH,
    "resort_swimming": ft.Icons.POOL,
    "restaurant": ft.Icons.RESTAURANT,
    "cafe": ft.Icons.LOCAL_CAFE,
    "hotel_accommodation": ft.Icons.HOTEL,
    "shopping_market": ft.Icons.SHOPPING_BAG,
    "transport_terminal": ft.Icons.DIRECTIONS_BUS,
    "hospital_clinic": ft.Icons.LOCAL_HOSPITAL,
    "pharmacy": ft.Icons.MEDICATION,
    "bank_atm": ft.Icons.ATM,
    "fuel_station": ft.Icons.LOCAL_GAS_STATION,
    "convenience_store": ft.Icons.STORE,
    "public_facility": ft.Icons.LOCATION_CITY,
}


class InteractiveProvinceMap(ft.Container):
    """Full-featured interactive GIS map supporting raster tiles and vector canvas fallback."""

    def __init__(
        self,
        places: Optional[list[Place]] = None,
        route_stops: Optional[list[dict]] = None,
        encoded_polyline: Optional[str] = None,
        selected_place: Optional[Place] = None,
        initial_center: tuple[float, float] = (NUEVA_ECIJA_CENTER_LAT, NUEVA_ECIJA_CENTER_LNG),
        initial_zoom: float = 10.0,
        on_marker_click: Optional[Callable[[Place], None]] = None,
        on_stop_click: Optional[Callable[[int], None]] = None,
        force_canvas_mode: bool = False,
    ):
        super().__init__()
        self.places = places or []
        self.route_stops = route_stops or []
        self.encoded_polyline = encoded_polyline
        self.selected_place = selected_place
        self.center_lat, self.center_lng = initial_center
        self.zoom = initial_zoom
        self.on_marker_click = on_marker_click
        self.on_stop_click = on_stop_click
        self.use_canvas_fallback = force_canvas_mode

        self.expand = True
        self.bgcolor = "#e2e8f0"
        self.border_radius = 12
        self.clip_behavior = ft.ClipBehavior.HARD_EDGE

        self.map_control: Optional[fm.Map] = None
        self._build_content()

    @property
    def safe_page(self) -> Optional[ft.Page]:
        try:
            return self.page
        except Exception:
            return None

    def set_places(self, places: list[Place]) -> None:
        """Updates places plotted on the map."""
        self.places = places
        self._build_content()
        try:
            self.update()
        except Exception:
            pass

    def set_route(
        self,
        route_stops: list[dict],
        encoded_polyline: Optional[str] = None,
        auto_fit: bool = True,
    ) -> None:
        """Updates active itinerary route stops and decoded polyline."""
        self.route_stops = route_stops
        self.encoded_polyline = encoded_polyline
        if auto_fit and route_stops and self.map_control:
            lats = [s.get("latitude") or (s["place"].latitude if isinstance(s.get("place"), Place) else s["place"].get("latitude", 0)) for s in route_stops if s.get("latitude") or s.get("place")]
            lngs = [s.get("longitude") or (s["place"].longitude if isinstance(s.get("place"), Place) else s["place"].get("longitude", 0)) for s in route_stops if s.get("longitude") or s.get("place")]
            valid_pts = [(lat, lng) for lat, lng in zip(lats, lngs) if lat and lng]
            if valid_pts:
                avg_lat = sum(p[0] for p in valid_pts) / len(valid_pts)
                avg_lng = sum(p[1] for p in valid_pts) / len(valid_pts)
                self.center_lat = avg_lat
                self.center_lng = avg_lng
                self._run_map_action(self.map_control.move_to, fm.MapLatitudeLongitude(avg_lat, avg_lng), zoom=11.5)

        self._build_content()
        try:
            self.update()
        except Exception:
            pass

    def _run_map_action(self, coro_func, *args, **kwargs) -> None:
        """Executes map coroutines safely inside or outside an active event loop."""
        if not coro_func or not self.safe_page:
            return

        async def _execute():
            try:
                await coro_func(*args, **kwargs)
            except Exception:
                pass

        self.safe_page.run_task(_execute)

    def select_place(self, place: Optional[Place], center_on: bool = True) -> None:
        """Highlights a selected destination and centers the map."""
        self.selected_place = place
        if place and center_on and self.map_control and place.latitude and place.longitude:
            self._run_map_action(
                self.map_control.move_to,
                fm.MapLatitudeLongitude(place.latitude, place.longitude),
                zoom=13.0,
            )
        self._build_content()
        try:
            self.update()
        except Exception:
            pass

    def recenter(self) -> None:
        """Resets view to province center."""
        self.center_lat = NUEVA_ECIJA_CENTER_LAT
        self.center_lng = NUEVA_ECIJA_CENTER_LNG
        self.zoom = 10.0
        if self.map_control:
            self._run_map_action(
                self.map_control.move_to,
                fm.MapLatitudeLongitude(self.center_lat, self.center_lng),
                zoom=self.zoom,
            )

    def center_on_hub(self) -> None:
        """Centers camera on Cabanatuan central transit hub."""
        if self.map_control:
            self._run_map_action(
                self.map_control.move_to,
                fm.MapLatitudeLongitude(CABANATUAN_HUB_LAT, CABANATUAN_HUB_LNG),
                zoom=12.5,
            )

    def zoom_in(self) -> None:
        if self.map_control:
            self._run_map_action(self.map_control.zoom_in)

    def zoom_out(self) -> None:
        if self.map_control:
            self._run_map_action(self.map_control.zoom_out)

    def toggle_canvas_mode(self) -> None:
        self.use_canvas_fallback = not self.use_canvas_fallback
        self._build_content()
        try:
            self.update()
        except Exception:
            pass

    def _build_content(self) -> None:
        if self.use_canvas_fallback:
            map_view = self._build_canvas_fallback_view()
        else:
            map_view = self._build_flet_map_view()

        floating_controls = self._build_floating_controls()

        self.content = ft.Stack(
            controls=[
                map_view,
                floating_controls,
            ],
            expand=True,
        )

    def _build_floating_controls(self) -> ft.Control:
        """Top-right floating action buttons (Zoom, Recenter, Locate, Engine Switch)."""
        def _btn(icon, tip, on_click):
            return ft.Container(
                content=ft.Icon(icon, size=18, color=ThemeColors.TEXT_BLACK),
                width=36,
                height=36,
                bgcolor=ft.Colors.WHITE,
                border_radius=8,
                alignment=ft.Alignment(0, 0),
                shadow=ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=6,
                    color=ft.Colors.with_opacity(0.18, "#000000"),
                    offset=ft.Offset(0, 2),
                ),
                ink=True,
                tooltip=tip,
                on_click=on_click,
            )

        controls_column = ft.Column(
            controls=[
                _btn(ft.Icons.ADD, "Zoom In", lambda _: self.zoom_in()),
                _btn(ft.Icons.REMOVE, "Zoom Out", lambda _: self.zoom_out()),
                ft.Container(height=4),
                _btn(ft.Icons.CENTER_FOCUS_STRONG, "Recenter Nueva Ecija", lambda _: self.recenter()),
                _btn(ft.Icons.NEAR_ME, "Cabanatuan Hub", lambda _: self.center_on_hub()),
                ft.Container(height=4),
                _btn(
                    ft.Icons.BRUSH if not self.use_canvas_fallback else ft.Icons.MAP,
                    "Switch to Vector Canvas" if not self.use_canvas_fallback else "Switch to Raster OSM Tiles",
                    lambda _: self.toggle_canvas_mode(),
                ),
            ],
            spacing=6,
            alignment=ft.MainAxisAlignment.START,
        )

        return ft.Container(
            content=controls_column,
            top=16,
            right=16,
        )

    def _build_flet_map_view(self) -> ft.Control:
        """Constructs fm.Map with TileLayer, PolylineLayer, and MarkerLayer."""
        layers: list[fm.MapLayer] = []

        # 1. Raster OSM TileLayer
        tile_layer = fm.TileLayer(
            url_template="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
            user_agent_package_name="com.nuevaecijatravel.desktop",
            subdomains=["a", "b", "c"],
            fallback_url="https://a.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png",
        )
        layers.append(tile_layer)

        # 2. Route Polyline Layer
        polyline_coords: list[fm.MapLatitudeLongitude] = []
        if self.encoded_polyline:
            decoded = decode_polyline(self.encoded_polyline)
            for lat, lng in decoded:
                polyline_coords.append(fm.MapLatitudeLongitude(lat, lng))
        elif self.route_stops and len(self.route_stops) >= 2:
            # Generate geodesic spline arcs between route stops
            coords_list: list[tuple[float, float]] = []
            for s in self.route_stops:
                lat = s.get("latitude") or (s["place"].latitude if isinstance(s.get("place"), Place) else s["place"].get("latitude", 0))
                lng = s.get("longitude") or (s["place"].longitude if isinstance(s.get("place"), Place) else s["place"].get("longitude", 0))
                if lat and lng:
                    coords_list.append((float(lat), float(lng)))

            for i in range(len(coords_list) - 1):
                p1 = coords_list[i]
                p2 = coords_list[i + 1]
                arc = generate_geodesic_arc(p1, p2, num_points=8)
                for lat, lng in arc:
                    polyline_coords.append(fm.MapLatitudeLongitude(lat, lng))

        if polyline_coords:
            polyline_marker = fm.PolylineMarker(
                coordinates=polyline_coords,
                color=ThemeColors.PRIMARY_BLUE,
                stroke_width=4.5,
            )
            layers.append(fm.PolylineLayer(polylines=[polyline_marker]))

        # 3. Markers Layer (Route stops take priority, then destination places)
        markers: list[fm.Marker] = []

        # Add route stop markers
        if self.route_stops:
            for s in self.route_stops:
                order = s.get("order", 1)
                place_obj = s.get("place")
                lat = s.get("latitude") or (place_obj.latitude if isinstance(place_obj, Place) else place_obj.get("latitude", 0))
                lng = s.get("longitude") or (place_obj.longitude if isinstance(place_obj, Place) else place_obj.get("longitude", 0))
                name = s.get("title") or (place_obj.name if isinstance(place_obj, Place) else place_obj.get("name", f"Stop {order}"))

                if not lat or not lng:
                    continue

                stop_ctrl = ft.Container(
                    content=ft.Text(
                        str(order),
                        color=ft.Colors.WHITE,
                        size=13,
                        weight=ft.FontWeight.W_800,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    width=32,
                    height=32,
                    border_radius=16,
                    bgcolor=ThemeColors.PRIMARY_BLUE,
                    border=ft.Border.all(2, ft.Colors.WHITE),
                    alignment=ft.Alignment(0, 0),
                    shadow=ft.BoxShadow(
                        spread_radius=1,
                        blur_radius=6,
                        color=ft.Colors.with_opacity(0.35, "#000000"),
                        offset=ft.Offset(0, 3),
                    ),
                    tooltip=f"{order}. {name}",
                    ink=True,
                    on_click=lambda _, ord_num=order, p=place_obj: (
                        self.on_marker_click(p) if (self.on_marker_click and isinstance(p, Place))
                        else (self.on_stop_click(ord_num) if self.on_stop_click else None)
                    ),
                )

                markers.append(
                    fm.Marker(
                        coordinates=fm.MapLatitudeLongitude(float(lat), float(lng)),
                        content=stop_ctrl,
                        width=32,
                        height=32,
                    )
                )

        # Add POI markers (up to 150 visible to keep 60 FPS)
        for place in self.places[:150]:
            if not place.latitude or not place.longitude:
                continue

            is_selected = (self.selected_place and self.selected_place.id == place.id)
            cat_color = CATEGORY_COLOR_MAP.get(place.category, ThemeColors.PRIMARY_BLUE)
            cat_icon = CATEGORY_ICON_MAP.get(place.category, ft.Icons.LOCATION_ON)

            pin_size = 32 if is_selected else 26
            pin_ctrl = ft.Container(
                content=ft.Icon(cat_icon, size=15 if is_selected else 13, color=ft.Colors.WHITE),
                width=pin_size,
                height=pin_size,
                border_radius=pin_size / 2,
                bgcolor=cat_color,
                border=ft.Border.all(2.5 if is_selected else 1.5, ft.Colors.WHITE),
                alignment=ft.Alignment(0, 0),
                shadow=ft.BoxShadow(
                    spread_radius=2 if is_selected else 1,
                    blur_radius=8 if is_selected else 4,
                    color=ft.Colors.with_opacity(0.3, "#000000"),
                    offset=ft.Offset(0, 2),
                ),
                tooltip=f"{place.name} ({place.municipality_name or 'Nueva Ecija'})",
                ink=True,
                on_click=lambda _, p=place: self.on_marker_click(p) if self.on_marker_click else None,
            )

            markers.append(
                fm.Marker(
                    coordinates=fm.MapLatitudeLongitude(place.latitude, place.longitude),
                    content=pin_ctrl,
                    width=pin_size,
                    height=pin_size,
                )
            )

        if markers:
            layers.append(fm.MarkerLayer(markers=markers))

        self.map_control = fm.Map(
            layers=layers,
            initial_center=fm.MapLatitudeLongitude(self.center_lat, self.center_lng),
            initial_zoom=self.zoom,
            min_zoom=7.0,
            max_zoom=18.0,
            expand=True,
            bgcolor="#cbd5e1",
        )

        return self.map_control

    def _build_canvas_fallback_view(self) -> ft.Control:
        """Vector Canvas Fallback for disconnected / offline scenarios."""
        # Simple projection from GPS coordinates to 2D canvas space
        def _to_canvas(lat: float, lng: float, w: float, h: float) -> tuple[float, float]:
            min_lat, max_lat = PROVINCE_BOUNDS["min_lat"], PROVINCE_BOUNDS["max_lat"]
            min_lng, max_lng = PROVINCE_BOUNDS["min_lng"], PROVINCE_BOUNDS["max_lng"]
            nx = (lng - min_lng) / (max_lng - min_lng)
            ny = (max_lat - lat) / (max_lat - min_lat)
            x = max(10, min(w - 10, nx * w))
            y = max(10, min(h - 10, ny * h))
            return x, y

        # Build interactive Stack on top of styled vector canvas
        pins_list: list[ft.Control] = []

        # Background grid with province title
        backdrop = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.MAP_OUTLINED, color="#94a3b8", size=20),
                            ft.Text("Vector Province Canvas (Offline Mode)", size=12, color="#64748b", weight=ft.FontWeight.W_600),
                        ],
                        spacing=8,
                    ),
                    ft.Text("32 LGUs • Nueva Ecija Hub", size=10, color="#94a3b8"),
                ],
                spacing=2,
            ),
            padding=ft.Padding.all(16),
            alignment=ft.Alignment(-1, -1),
        )

        # Plot up to 40 places on vector canvas
        for place in self.places[:40]:
            if not place.latitude or not place.longitude:
                continue
            cat_color = CATEGORY_COLOR_MAP.get(place.category, ThemeColors.PRIMARY_BLUE)
            pin = ft.Container(
                content=ft.Container(
                    width=14,
                    height=14,
                    border_radius=7,
                    bgcolor=cat_color,
                    border=ft.Border.all(1.5, ft.Colors.WHITE),
                    tooltip=f"{place.name} ({place.municipality_name})",
                    ink=True,
                    on_click=lambda _, p=place: self.on_marker_click(p) if self.on_marker_click else None,
                ),
                # Relative positioning
                left=100 + ((place.longitude - 120.65) / 0.8) * 400,
                top=50 + ((16.15 - place.latitude) / 1.05) * 350,
            )
            pins_list.append(pin)

        return ft.Container(
            content=ft.Stack(
                controls=[backdrop] + pins_list,
                expand=True,
            ),
            bgcolor="#f8fafc",
            border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
            border_radius=12,
            expand=True,
        )
