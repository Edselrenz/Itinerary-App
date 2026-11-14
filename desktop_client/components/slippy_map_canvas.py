"""Pure-Flet 1.1.2 Web-Mercator Slippy Map with OSM tiles, spatial marker clustering, and OSRM road routing.

Directly ports the Leaflet mapping architecture from Project/src/app/tabs/map/map.page.ts
and Project/src/app/shared/components/itinerary-route-map/itinerary-route-map.component.ts into pure Flet.
"""

from __future__ import annotations

from dataclasses import dataclass
import concurrent.futures
import math
import os
from pathlib import Path
import time
from typing import Callable, Optional
import urllib.request
import flet as ft
import flet.canvas as cv
import httpx

from desktop_client.config.settings import get_settings
from desktop_client.core.polyline import decode_polyline, generate_geodesic_arc
from desktop_client.models.place import Place

# Global background tile fetcher
_TILE_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=6)
_QUEUED_TILES: set[str] = set()
_TILE_PATH_CACHE: dict[str, str] = {}


def _resolve_tile_source(
    zoom: int,
    x: int,
    y: int,
    on_tile_cached: Optional[Callable[[str, str], None]] = None,
) -> str:
    """Returns local path to clean OSM tile (bundled or cached) or downloads in background with clean ESRI fallback."""
    tile_key = f"{zoom}_{x}_{y}"
    cached_src = _TILE_PATH_CACHE.get(tile_key)
    if cached_src:
        return cached_src

    settings = get_settings()

    # 1. Bundled assets (Zooms 8-11 pre-downloaded in desktop_client/assets/tiles)
    direct_cand = settings.assets_dir / "tiles" / f"{zoom}_{x}_{y}.png"
    if direct_cand.is_file():
        cand_str = str(direct_cand)
        _TILE_PATH_CACHE[tile_key] = cand_str
        return cand_str

    # 2. Local disk cache
    cache_dir = settings.storage_dir / "tile_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"{zoom}_{x}_{y}.png"
    if cache_file.is_file() and cache_file.stat().st_size > 500:
        c_str = str(cache_file)
        _TILE_PATH_CACHE[tile_key] = c_str
        return c_str

    # 3. Schedule background download from tile.openstreetmap.org with compliant User-Agent
    if tile_key not in _QUEUED_TILES:
        _QUEUED_TILES.add(tile_key)

        def _fetch():
            url = f"https://tile.openstreetmap.org/{zoom}/{x}/{y}.png"
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "NuevaEcijaTravel/1.0 (+https://edselrenz.github.io/Itinerary-App; contact: edselrenz0@gmail.com)"},
            )
            try:
                with urllib.request.urlopen(req, timeout=5) as resp:
                    if resp.status == 200:
                        data = resp.read()
                        if len(data) > 500:
                            with open(cache_file, "wb") as f:
                                f.write(data)
                            c_path = str(cache_file)
                            _TILE_PATH_CACHE[tile_key] = c_path
                            if on_tile_cached:
                                on_tile_cached(tile_key, c_path)
            except Exception:
                pass
            finally:
                _QUEUED_TILES.discard(tile_key)

        _TILE_EXECUTOR.submit(_fetch)

    # 4. Clean fallback while downloading: ESRI World Street Map (clean, zero watermark, never blocked by Flutter)
    return f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{zoom}/{y}/{x}"


# Category Pin Palette matching Project/src/app/tabs/map/map.page.scss (.pin-cat-*)
CATEGORY_PIN_STYLE: dict[str, tuple[str, ft.IconData]] = {
    "tourist_attraction": ("#10b981", ft.Icons.LANDSCAPE_ROUNDED),
    "nature_park": ("#10b981", ft.Icons.PARK_ROUNDED),
    "attraction": ("#10b981", ft.Icons.PHOTO_CAMERA_ROUNDED),
    "restaurant": ("#f97316", ft.Icons.RESTAURANT_ROUNDED),
    "cafe": ("#f97316", ft.Icons.LOCAL_CAFE_ROUNDED),
    "fast_food": ("#f97316", ft.Icons.FASTFOOD_ROUNDED),
    "church_religious": ("#8b5cf6", ft.Icons.ACCOUNT_BALANCE_ROUNDED),
    "museum_cultural": ("#8b5cf6", ft.Icons.MUSEUM_ROUNDED),
    "shopping_market": ("#ec4899", ft.Icons.SHOPPING_BAG_ROUNDED),
    "supermarket": ("#ec4899", ft.Icons.SHOPPING_CART_ROUNDED),
    "convenience_store": ("#ec4899", ft.Icons.STOREFRONT_ROUNDED),
    "resort_swimming": ("#06b6d4", ft.Icons.POOL_ROUNDED),
    "hotel_accommodation": ("#06b6d4", ft.Icons.HOTEL_ROUNDED),
    "fuel_station": ("#64748b", ft.Icons.LOCAL_GAS_STATION_ROUNDED),
    "gas_station": ("#64748b", ft.Icons.LOCAL_GAS_STATION_ROUNDED),
    "transport_terminal": ("#64748b", ft.Icons.DIRECTIONS_BUS_ROUNDED),
    "hospital_clinic": ("#ef4444", ft.Icons.LOCAL_HOSPITAL_ROUNDED),
    "pharmacy": ("#ef4444", ft.Icons.MEDICATION_ROUNDED),
    "bank_atm": ("#0284c7", ft.Icons.LOCAL_ATM_ROUNDED),
    "public_facility": ("#0284c7", ft.Icons.ACCOUNT_BALANCE_ROUNDED),
}


@dataclass
class RouteStopPin:
    """Represents a numbered itinerary stop on the route map."""

    index: int          # 0-based index (displayed as index + 1)
    title: str
    lat: float
    lng: float
    planned_time: str = ""
    category: str = "attraction"
    place: Optional[Place] = None


def latlon_to_world_px(lat: float, lon: float, zoom: int) -> tuple[float, float]:
    """Project (lat, lon) in degrees to global Web-Mercator pixel coordinates at integer zoom."""
    lat = max(-85.05112878, min(85.05112878, float(lat)))
    lon = float(lon)
    scale = 256.0 * (2 ** zoom)
    x = (lon + 180.0) / 360.0 * scale
    sin_lat = math.sin(math.radians(lat))
    y = (0.5 - math.log((1.0 + sin_lat) / (1.0 - sin_lat)) / (4.0 * math.pi)) * scale
    return x, y


def world_px_to_latlon(wx: float, wy: float, zoom: int) -> tuple[float, float]:
    """Inverse project global Web-Mercator pixel coordinates (wx, wy) back to (lat, lon)."""
    scale = 256.0 * (2 ** zoom)
    lon = (wx / scale) * 360.0 - 180.0
    n = math.pi - 2.0 * math.pi * (wy / scale)
    lat = math.degrees(math.atan(0.5 * (math.exp(n) - math.exp(-n))))
    return lat, lon


def fetch_osrm_road_geometry(coords: list[tuple[float, float]], timeout: float = 3.0) -> list[tuple[float, float]]:
    """Fetch road-following geometry from public OSRM API for a sequence of (lat, lng) stops.
    Falls back to smooth 24-point geodesic arcs if offline or OSRM times out.
    """
    valid = [(float(lat), float(lng)) for lat, lng in coords if lat and lng]
    if len(valid) < 2:
        return valid

    coord_str = ";".join(f"{lng:.6f},{lat:.6f}" for lat, lng in valid)
    url = f"https://router.project-osrm.org/route/v1/driving/{coord_str}?overview=full&geometries=polyline"
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                routes = data.get("routes") or []
                if routes and routes[0].get("geometry"):
                    decoded = decode_polyline(routes[0]["geometry"])
                    if len(decoded) >= 2:
                        return decoded
    except Exception:
        pass

    # Offline / fallback: stitch smooth geodesic splines between consecutive stops
    fallback_pts: list[tuple[float, float]] = []
    for i in range(len(valid) - 1):
        arc = generate_geodesic_arc(valid[i], valid[i + 1], num_points=24)
        if i > 0 and arc:
            arc = arc[1:]
        fallback_pts.extend(arc)
    return fallback_pts


class SlippyMapCanvas(ft.Container):
    """Interactive OpenStreetMap slippy map with marker clustering, category pins, and OSRM road polylines."""

    def __init__(
        self,
        width: int = 860,
        height: int = 520,
        center_lat: float = 15.58,
        center_lng: float = 121.00,
        zoom: int = 10,
        places: Optional[list[Place]] = None,
        route_stops: Optional[list[RouteStopPin]] = None,
        route_polyline_points: Optional[list[tuple[float, float]]] = None,
        route_coords: Optional[list[tuple[float, float]]] = None,
        active_stop_index: Optional[int] = None,
        user_location: Optional[tuple[float, float]] = None,
        on_place_click: Optional[Callable[[Place], None]] = None,
        on_stop_click: Optional[Callable[[int, RouteStopPin], None]] = None,
        border_radius: int = 16,
    ) -> None:
        super().__init__()
        self._map_w = max(320, int(width))
        self._map_h = max(220, int(height))
        self.width = self._map_w
        self.height = self._map_h
        self.border_radius = border_radius
        self.clip_behavior = ft.ClipBehavior.HARD_EDGE
        self.bgcolor = "#e2e8f0"
        self.border = ft.Border.all(1, "#cbd5e1")

        self.center_lat = float(center_lat)
        self.center_lng = float(center_lng)
        self.zoom = max(8, min(18, int(zoom)))

        if route_coords and not route_stops:
            route_stops = [
                RouteStopPin(index=i, title=f"Stop {i+1}", lat=c[0], lng=c[1])
                for i, c in enumerate(route_coords)
            ]
            if not route_polyline_points:
                route_polyline_points = route_coords

        self._places: list[Place] = list(places or [])
        self._route_stops: list[RouteStopPin] = list(route_stops or [])
        self._route_pts: list[tuple[float, float]] = list(route_polyline_points or [])
        self._active_stop_index = active_stop_index
        self._user_location = user_location
        self._on_place_click = on_place_click
        self._on_stop_click = on_stop_click
        self._last_pan_redraw: float = 0.0
        self._last_scroll_zoom: float = 0.0
        self._active_tile_images: dict[str, ft.Image] = {}

        self._tile_stack = ft.Stack(width=self._map_w, height=self._map_h)
        self._vector_canvas = cv.Canvas(width=self._map_w, height=self._map_h, shapes=[])
        self._marker_stack = ft.Stack(width=self._map_w, height=self._map_h)

        # Attribution & Zoom Controls (positioned bottom-right, clear of top bar and floating buttons)
        self._zoom_label = ft.Text(f"Z{self.zoom}", size=10, weight=ft.FontWeight.W_700, color="#334155")
        controls_overlay = ft.Container(
            right=12,
            bottom=24,
            bgcolor=ft.Colors.with_opacity(0.95, "#ffffff"),
            border_radius=10,
            border=ft.Border.all(1, "#cbd5e1"),
            padding=ft.Padding.symmetric(horizontal=4, vertical=4),
            shadow=ft.BoxShadow(blur_radius=8, color=ft.Colors.with_opacity(0.12, "#0f172a")),
            content=ft.Column(
                spacing=2,
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.ADD_ROUNDED,
                        icon_size=16,
                        icon_color="#0f172a",
                        tooltip="Zoom in",
                        on_click=lambda _: self.set_zoom(self.zoom + 1),
                        style=ft.ButtonStyle(padding=ft.Padding.all(4)),
                    ),
                    self._zoom_label,
                    ft.IconButton(
                        icon=ft.Icons.REMOVE_ROUNDED,
                        icon_size=16,
                        icon_color="#0f172a",
                        tooltip="Zoom out",
                        on_click=lambda _: self.set_zoom(self.zoom - 1),
                        style=ft.ButtonStyle(padding=ft.Padding.all(4)),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.FIT_SCREEN_ROUNDED,
                        icon_size=15,
                        icon_color="#0284c7",
                        tooltip="Fit markers / route",
                        on_click=lambda _: self.fit_to_content(),
                        style=ft.ButtonStyle(padding=ft.Padding.all(4)),
                    ),
                ],
            ),
        )

        attribution_badge = ft.Container(
            left=8,
            bottom=6,
            bgcolor=ft.Colors.with_opacity(0.82, "#ffffff"),
            border_radius=6,
            padding=ft.Padding.symmetric(horizontal=6, vertical=2),
            content=ft.Text("© OpenStreetMap contributors • OSRM", size=9, color="#475569"),
        )

        # Dedicated hit-testable gesture plane placed ABOVE tiles/vectors and BELOW interactive markers
        gesture_surface = ft.GestureDetector(
            on_pan_update=self._handle_pan_update,
            on_pan_end=self._handle_pan_end,
            on_scroll=self._handle_scroll,
            on_double_tap=lambda _: self.set_zoom(self.zoom + 1),
            drag_interval=32,
            content=ft.Container(
                width=self._map_w,
                height=self._map_h,
                bgcolor="#01000000",
            ),
        )
        self._gesture_surface = gesture_surface

        self.content = ft.Stack(
            width=self._map_w,
            height=self._map_h,
            controls=[
                self._tile_stack,
                self._vector_canvas,
                gesture_surface,
                self._marker_stack,
                controls_overlay,
                attribution_badge,
            ],
        )
        self._canvas_stack = self.content

        if self._route_stops:
            self.set_route(
                self._route_stops,
                polyline_points=route_polyline_points,
                active_stop_index=active_stop_index,
                auto_fit=True,
            )
        else:
            self.redraw()

    @property
    def route_coords(self) -> list[tuple[float, float]]:
        if self._route_pts:
            return list(self._route_pts)
        return [(s.lat, s.lng) for s in self._route_stops if s.lat and s.lng]

    def get_viewport_bounds(self) -> tuple[float, float, float, float]:
        """Returns (min_lat, min_lng, max_lat, max_lng) for the currently visible map viewport."""
        cx, cy = latlon_to_world_px(self.center_lat, self.center_lng, self.zoom)
        nw_lat, nw_lng = world_px_to_latlon(cx - self._map_w / 2.0, cy - self._map_h / 2.0, self.zoom)
        se_lat, se_lng = world_px_to_latlon(cx + self._map_w / 2.0, cy + self._map_h / 2.0, self.zoom)
        return (min(nw_lat, se_lat), min(nw_lng, se_lng), max(nw_lat, se_lat), max(nw_lng, se_lng))

    def set_places(self, places: list[Place], auto_fit: bool = False) -> None:
        self._places = list(places or [])
        if auto_fit and self._places:
            self.fit_bounds([(p.latitude, p.longitude) for p in self._places if p.latitude and p.longitude])
        else:
            self.redraw()

    def set_route(
        self,
        stops: list[RouteStopPin],
        polyline_points: Optional[list[tuple[float, float]]] = None,
        active_stop_index: Optional[int] = None,
        auto_fit: bool = True,
    ) -> None:
        self._route_stops = list(stops or [])
        self._active_stop_index = active_stop_index
        if polyline_points is not None and len(polyline_points) >= 2:
            self._route_pts = list(polyline_points)
        elif len(self._route_stops) >= 2:
            coords = [(s.lat, s.lng) for s in self._route_stops if s.lat and s.lng]
            # Immediate smooth geodesic arc so UI never freezes
            arc_pts: list[tuple[float, float]] = []
            for i in range(len(coords) - 1):
                seg = generate_geodesic_arc(coords[i], coords[i + 1])
                if arc_pts:
                    arc_pts.extend(seg[1:])
                else:
                    arc_pts.extend(seg)
            self._route_pts = arc_pts or coords

            def _async_osrm():
                try:
                    pts = fetch_osrm_road_geometry(coords)
                    if pts and len(pts) >= 2:
                        self._route_pts = pts
                        self._render_route_vectors()
                        if self.page:
                            self._vector_canvas.update()
                except Exception:
                    pass

            _TILE_EXECUTOR.submit(_async_osrm)
        else:
            self._route_pts = []

        if auto_fit and self._route_stops:
            self.fit_bounds([(s.lat, s.lng) for s in self._route_stops if s.lat and s.lng])
        else:
            self.redraw()

    def set_center_and_zoom(self, lat: float, lng: float, zoom: Optional[int] = None) -> None:
        self.center_lat = float(lat)
        self.center_lng = float(lng)
        if zoom is not None:
            self.zoom = max(8, min(18, int(zoom)))
        self.redraw()

    def recenter_province(self) -> None:
        """Recenters to default Nueva Ecija provincial coordinates (15.58, 121.00, zoom 10)."""
        self.set_center_and_zoom(15.58, 121.00, 10)

    def set_zoom(self, new_zoom: int) -> None:
        clamped = max(8, min(18, int(new_zoom)))
        if clamped != self.zoom:
            self.zoom = clamped
            self.redraw()

    def fit_to_content(self) -> None:
        if self._route_stops:
            self.fit_bounds([(s.lat, s.lng) for s in self._route_stops if s.lat and s.lng])
        elif self._places:
            self.fit_bounds([(p.latitude, p.longitude) for p in self._places if p.latitude and p.longitude])
        else:
            self.set_center_and_zoom(15.58, 121.00, 10)

    def fit_bounds(self, coords: list[tuple[float, float]], padding_px: int = 56) -> None:
        valid = [(lat, lng) for lat, lng in coords if lat and lng and -90 <= lat <= 90 and -180 <= lng <= 180]
        if not valid:
            self.redraw()
            return
        if len(valid) == 1:
            self.center_lat, self.center_lng = valid[0]
            self.zoom = 14
            self.redraw()
            return

        min_lat = min(c[0] for c in valid)
        max_lat = max(c[0] for c in valid)
        min_lng = min(c[1] for c in valid)
        max_lng = max(c[1] for c in valid)

        self.center_lat = (min_lat + max_lat) / 2.0
        self.center_lng = (min_lng + max_lng) / 2.0

        usable_w = max(120, self._map_w - 2 * padding_px)
        usable_h = max(120, self._map_h - 2 * padding_px)

        best_z = 10
        for z in range(16, 8, -1):
            x1, y1 = latlon_to_world_px(max_lat, min_lng, z)
            x2, y2 = latlon_to_world_px(min_lat, max_lng, z)
            if abs(x2 - x1) <= usable_w and abs(y2 - y1) <= usable_h:
                best_z = z
                break
        self.zoom = best_z
        self.redraw()

    def _handle_pan_update(self, e: ft.DragUpdateEvent) -> None:
        dx = float(getattr(e, "delta_x", 0.0) or 0.0)
        dy = float(getattr(e, "delta_y", 0.0) or 0.0)
        cx, cy = latlon_to_world_px(self.center_lat, self.center_lng, self.zoom)
        self.center_lat, self.center_lng = world_px_to_latlon(cx - dx, cy - dy, self.zoom)
        now = time.monotonic()
        if now - self._last_pan_redraw >= 0.045:
            self._last_pan_redraw = now
            self.redraw()

    def _handle_pan_end(self, e: ft.DragEndEvent) -> None:
        self.redraw()

    def _handle_scroll(self, e: Any) -> None:
        now = time.monotonic()
        if now - self._last_scroll_zoom < 0.12:
            return
        dy = float(getattr(e, "scroll_delta_y", 0.0) or 0.0)
        if dy < -1.0:
            self._last_scroll_zoom = now
            self.set_zoom(self.zoom + 1)
        elif dy > 1.0:
            self._last_scroll_zoom = now
            self.set_zoom(self.zoom - 1)

    def _latlon_to_viewport(self, lat: float, lng: float) -> tuple[float, float]:
        cx, cy = latlon_to_world_px(self.center_lat, self.center_lng, self.zoom)
        px, py = latlon_to_world_px(lat, lng, self.zoom)
        return (self._map_w / 2.0) + (px - cx), (self._map_h / 2.0) + (py - cy)

    def _on_single_tile_cached(self, tile_key: str, local_path: str) -> None:
        """Thread-safe callback updating only the specific ft.Image control when a background tile finishes downloading."""
        img = self._active_tile_images.get(tile_key)
        if img and self.page:
            try:
                img.src = local_path
                img.update()
            except Exception:
                pass

    def redraw(self) -> None:
        self._zoom_label.value = f"Z{self.zoom}"
        self._render_tiles()
        self._render_route_vectors()
        self._render_markers_and_clusters()
        try:
            if self.page:
                self.update()
        except Exception:
            pass

    def _render_tiles(self) -> None:
        cx, cy = latlon_to_world_px(self.center_lat, self.center_lng, self.zoom)
        top_left_wx = cx - (self._map_w / 2.0)
        top_left_wy = cy - (self._map_h / 2.0)

        min_tx = int(math.floor(top_left_wx / 256.0))
        max_tx = int(math.floor((top_left_wx + self._map_w) / 256.0))
        min_ty = int(math.floor(top_left_wy / 256.0))
        max_ty = int(math.floor((top_left_wy + self._map_h) / 256.0))

        num_tiles = 2 ** self.zoom
        tiles: list[ft.Control] = []
        active_imgs: dict[str, ft.Image] = {}
        for tx in range(min_tx, max_tx + 1):
            for ty in range(min_ty, max_ty + 1):
                if ty < 0 or ty >= num_tiles:
                    continue
                wrapped_tx = tx % num_tiles
                left_px = (tx * 256.0) - top_left_wx
                top_px = (ty * 256.0) - top_left_wy
                tile_key = f"{self.zoom}_{wrapped_tx}_{ty}"
                tile_src = _resolve_tile_source(
                    self.zoom,
                    wrapped_tx,
                    ty,
                    on_tile_cached=self._on_single_tile_cached,
                )
                img_ctrl = ft.Image(
                    src=tile_src,
                    width=256,
                    height=256,
                    fit=ft.BoxFit.COVER,
                    gapless_playback=True,
                )
                active_imgs[tile_key] = img_ctrl
                tiles.append(
                    ft.Container(
                        left=left_px,
                        top=top_px,
                        width=256,
                        height=256,
                        content=img_ctrl,
                    )
                )
        self._active_tile_images = active_imgs
        self._tile_stack.controls = tiles

    def _render_route_vectors(self) -> None:
        shapes: list[cv.Shape] = []
        if len(self._route_pts) >= 2:
            screen_pts = [self._latlon_to_viewport(lat, lng) for lat, lng in self._route_pts]
            path_elements: list[cv.PathElement] = [cv.Path.MoveTo(screen_pts[0][0], screen_pts[0][1])]
            for vx, vy in screen_pts[1:]:
                path_elements.append(cv.Path.LineTo(vx, vy))

            # Outer white route casing
            shapes.append(
                cv.Path(
                    elements=path_elements,
                    paint=ft.Paint(
                        color="#ffffff",
                        stroke_width=8,
                        style=ft.PaintingStyle.STROKE,
                        stroke_cap=ft.StrokeCap.ROUND,
                        stroke_join=ft.StrokeJoin.ROUND,
                    ),
                )
            )
            # Inner primary road line (#0284c7 / #2563eb matching Web App)
            shapes.append(
                cv.Path(
                    elements=path_elements,
                    paint=ft.Paint(
                        color="#0284c7",
                        stroke_width=5,
                        style=ft.PaintingStyle.STROKE,
                        stroke_cap=ft.StrokeCap.ROUND,
                        stroke_join=ft.StrokeJoin.ROUND,
                    ),
                )
            )
        self._vector_canvas.shapes = shapes

    def _render_markers_and_clusters(self) -> None:
        controls: list[ft.Control] = []

        # 1. User GPS / Cabanatuan Anchor Dot (if present)
        if self._user_location:
            ux, uy = self._latlon_to_viewport(self._user_location[0], self._user_location[1])
            if -20 <= ux <= self._map_w + 20 and -20 <= uy <= self._map_h + 20:
                controls.append(
                    ft.Container(
                        left=ux - 10,
                        top=uy - 10,
                        width=20,
                        height=20,
                        bgcolor="#3b82f6",
                        border=ft.Border.all(3, "#ffffff"),
                        border_radius=10,
                        tooltip="Your Location",
                        shadow=ft.BoxShadow(blur_radius=8, color=ft.Colors.with_opacity(0.4, "#3b82f6")),
                    )
                )

        # 2. Discovery Place Markers (with fast degree bounding-box pre-filter and marker clustering)
        lat_span = (360.0 / (2 ** self.zoom)) * (self._map_h / 256.0) * 0.75
        lng_span = (360.0 / (2 ** self.zoom)) * (self._map_w / 256.0) * 0.75
        visible_places: list[tuple[Place, float, float]] = []
        for p in self._places:
            if not p.latitude or not p.longitude:
                continue
            if abs(p.latitude - self.center_lat) > lat_span or abs(p.longitude - self.center_lng) > lng_span:
                continue
            px, py = self._latlon_to_viewport(p.latitude, p.longitude)
            if -32 <= px <= self._map_w + 32 and -32 <= py <= self._map_h + 32:
                visible_places.append((p, px, py))

        if self.zoom < 14 and len(visible_places) > 18:
            # Grid spatial clustering (cell size 58px) matching Leaflet.markercluster (.marker-cluster)
            grid: dict[tuple[int, int], list[tuple[Place, float, float]]] = {}
            cell_size = 58.0
            for item in visible_places:
                gx = int(item[1] // cell_size)
                gy = int(item[2] // cell_size)
                grid.setdefault((gx, gy), []).append(item)

            for bucket in grid.values():
                if len(bucket) == 1:
                    p, px, py = bucket[0]
                    controls.append(self._build_place_pin(p, px, py))
                else:
                    avg_x = sum(b[1] for b in bucket) / len(bucket)
                    avg_y = sum(b[2] for b in bucket) / len(bucket)
                    avg_lat = sum(b[0].latitude for b in bucket) / len(bucket)
                    avg_lng = sum(b[0].longitude for b in bucket) / len(bucket)
                    count = len(bucket)
                    controls.append(self._build_cluster_pin(count, avg_x, avg_y, avg_lat, avg_lng))
        else:
            for p, px, py in visible_places[:250]:
                controls.append(self._build_place_pin(p, px, py))

        # 3. Numbered Itinerary Route Stop Badges (1..N) on top of everything
        for stop in self._route_stops:
            if not stop.lat or not stop.lng:
                continue
            sx, sy = self._latlon_to_viewport(stop.lat, stop.lng)
            if -40 <= sx <= self._map_w + 40 and -40 <= sy <= self._map_h + 40:
                controls.append(self._build_route_stop_badge(stop, sx, sy))

        self._marker_stack.controls = controls

    def _build_cluster_pin(
        self, count: int, px: float, py: float, center_lat: float, center_lng: float
    ) -> ft.Control:
        """Web-App-identical blue marker cluster circle (`.marker-cluster` in `map.page.scss`)."""
        size = 38 if count < 25 else (44 if count < 100 else 50)
        return ft.Container(
            left=px - size / 2,
            top=py - size / 2,
            width=size,
            height=size,
            border_radius=size / 2,
            bgcolor=ft.Colors.with_opacity(0.28, "#0084ff"),
            padding=ft.Padding.all(4),
            tooltip=f"{count} places in this area — Click to zoom in",
            ink=True,
            on_click=lambda _: self.set_center_and_zoom(center_lat, center_lng, min(17, self.zoom + 2)),
            content=ft.Container(
                alignment=ft.Alignment(0, 0),
                border_radius=(size - 8) / 2,
                bgcolor="#0084ff",
                border=ft.Border.all(2, "#ffffff"),
                content=ft.Text(
                    str(count),
                    size=12,
                    weight=ft.FontWeight.W_800,
                    color="#ffffff",
                ),
            ),
        )

    def _build_place_pin(self, place: Place, px: float, py: float) -> ft.Control:
        """Category-colored circular marker pin that opens PlaceDetailSheet on click."""
        color_hex, icon_data = CATEGORY_PIN_STYLE.get(
            place.category, ("#2563eb", ft.Icons.LOCATION_ON_ROUNDED)
        )
        return ft.Container(
            left=px - 15,
            top=py - 15,
            width=30,
            height=30,
            bgcolor=color_hex,
            border=ft.Border.all(2, "#ffffff"),
            border_radius=15,
            alignment=ft.Alignment(0, 0),
            tooltip=f"{place.name} ({place.municipality_name or 'Nueva Ecija'})",
            shadow=ft.BoxShadow(blur_radius=6, color=ft.Colors.with_opacity(0.28, "#0f172a")),
            ink=True,
            on_click=lambda _, p=place: self._on_place_click(p) if self._on_place_click else None,
            content=ft.Icon(icon_data, size=15, color="#ffffff"),
        )

    def _build_route_stop_badge(self, stop: RouteStopPin, sx: float, sy: float) -> ft.Control:
        """Numbered circular stop badge (`1`, `2`, `3`...) with floating stop name pill."""
        is_active = self._active_stop_index == stop.index
        badge_bg = "#f97316" if is_active else "#2563eb"
        badge_size = 34 if is_active else 30

        return ft.Container(
            left=sx - badge_size / 2,
            top=sy - badge_size / 2,
            ink=True,
            on_click=lambda _, s=stop: self._on_stop_click(s.index, s) if self._on_stop_click else None,
            tooltip=f"Stop {stop.index + 1}: {stop.title} ({stop.planned_time or 'Scheduled'})",
            content=ft.Row(
                spacing=4,
                tight=True,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        width=badge_size,
                        height=badge_size,
                        bgcolor=badge_bg,
                        border=ft.Border.all(2.5, "#ffffff"),
                        border_radius=badge_size / 2,
                        alignment=ft.Alignment(0, 0),
                        shadow=ft.BoxShadow(
                            blur_radius=8,
                            color=ft.Colors.with_opacity(0.35, "#0f172a"),
                            offset=ft.Offset(0, 2),
                        ),
                        content=ft.Text(
                            str(stop.index + 1),
                            size=13,
                            weight=ft.FontWeight.W_800,
                            color="#ffffff",
                        ),
                    ),
                    ft.Container(
                        bgcolor=ft.Colors.with_opacity(0.95, "#ffffff"),
                        border=ft.Border.all(1, "#cbd5e1"),
                        border_radius=8,
                        padding=ft.Padding.symmetric(horizontal=7, vertical=3),
                        shadow=ft.BoxShadow(blur_radius=4, color=ft.Colors.with_opacity(0.12, "#0f172a")),
                        content=ft.Text(
                            stop.title[:22] + ("…" if len(stop.title) > 22 else ""),
                            size=10,
                            weight=ft.FontWeight.W_700,
                            color="#0f172a",
                        ),
                    ),
                ],
            ),
        )
