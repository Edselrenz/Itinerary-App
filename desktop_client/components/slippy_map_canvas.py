"""Interactive Slippy Map Canvas for Flet Desktop (1:1 Web Leaflet Parity).

Provides:
- Zero '403 Access blocked' tiles: Python-only tile fetching with PNG header validation,
  ocean/rural small-tile support (>= 67 bytes), automatic ESRI RGB cache cleanup, and
  live UI swap via `on_tile_cached`.
- 60 FPS GPU-smooth drag translation via a dedicated `_viewport_mover` container.
- Cursor-centered mouse wheel zooming (Leaflet `zoomAround` parity).
- Spatial grid clustering up to Zoom 15 (`disableClusteringAtZoom: 16` parity).
- Smooth animated `fly_to(lat, lng, zoom)` and OSRM route polyline rendering.
- Full backward compatibility with existing test suites and view models.
"""
from __future__ import annotations

import base64
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import inspect
import json
import math
from pathlib import Path
import struct
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import urllib.request
import zlib

import flet as ft
import flet.canvas as cv
import httpx

from desktop_client.config.settings import get_settings
from desktop_client.core.polyline import decode_polyline, generate_geodesic_arc
from desktop_client.models.place import Place

# Provincial bounds matching Project/src/app/tabs/map/map.page.ts with breathing room
NUEVA_ECIJA_MIN_LAT = 15.05
NUEVA_ECIJA_MAX_LAT = 16.25
NUEVA_ECIJA_MIN_LNG = 120.55
NUEVA_ECIJA_MAX_LNG = 121.55

# Thread pool for non-blocking background tile caching
_TILE_EXECUTOR = ThreadPoolExecutor(max_workers=8, thread_name_prefix="osm_tile_fetcher")
_IN_FLIGHT_TILES: set[str] = set()
_FAILED_TILES_COOLDOWN: Dict[str, float] = {}
_TILE_LOCK = threading.Lock()
_TILE_PATH_CACHE: Dict[str, str] = {}

_ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
_BUNDLED_TILES_DIR = _ASSETS_DIR / "tiles"
_CACHE_TILES_DIR = _ASSETS_DIR / "tiles_cache"
_CACHE_TILES_DIR.mkdir(parents=True, exist_ok=True)

# Known SHA/size signatures of OSM 403 block tiles or stale ESRI RGB tiles or Carto watermark
_OSM_BLOCKED_SIGNATURES = (
    b"http://osm.wiki/Blocked",
    b"Access blocked",
    b"carto.com",
    b"API KEY REQUIRED",
    b"basemaps/apikey",
    b"CartoDB",
    b"cartocdn",
)


def _extract_scroll_delta_y(e: Any) -> float:
    """Extract vertical scroll delta from diverse Flet scroll event formats."""
    # 1. Direct offset object attribute
    offset = getattr(e, "scroll_delta", None)
    if offset is not None:
        y = getattr(offset, "y", None)
        if y is not None:
            return float(y)
    # 2. Flat attribute
    if hasattr(e, "scroll_delta_y") and e.scroll_delta_y is not None:
        return float(e.scroll_delta_y)
    if hasattr(e, "delta_y") and e.delta_y is not None:
        return float(e.delta_y)
    # 3. JSON data payload
    data_str = getattr(e, "data", None)
    if data_str and isinstance(data_str, str):
        try:
            d = json.loads(data_str)
            if isinstance(d, dict):
                if "dy" in d:
                    return float(d["dy"])
                if "y" in d:
                    return float(d["y"])
                if "scroll_delta_y" in d:
                    return float(d["scroll_delta_y"])
        except Exception:
            pass
    return 0.0


def _extract_pan_delta(e: Any) -> Tuple[float, float]:
    """Extract (dx, dy) pan delta from diverse Flet pan update event formats."""
    # 1. local_delta or delta object with .x and .y
    for attr in ("local_delta", "delta"):
        obj = getattr(e, attr, None)
        if obj is not None and hasattr(obj, "x") and hasattr(obj, "y"):
            return float(obj.x), float(obj.y)
    # 2. Direct dx, dy attributes
    dx = getattr(e, "delta_x", None) or getattr(e, "dx", None)
    dy = getattr(e, "delta_y", None) or getattr(e, "dy", None)
    if dx is not None and dy is not None:
        return float(dx), float(dy)
    # 3. JSON data payload
    data_str = getattr(e, "data", None)
    if data_str and isinstance(data_str, str):
        try:
            d = json.loads(data_str)
            if isinstance(d, dict):
                return float(d.get("dx", 0.0)), float(d.get("dy", 0.0))
        except Exception:
            pass
    return 0.0, 0.0


def _purge_stale_cached_tiles_once() -> None:
    """Remove any leftover ESRI RGB tiles, Carto watermarked tiles, or corrupt/blocked files from assets/tiles_cache/."""
    try:
        for f in _CACHE_TILES_DIR.glob("*.png"):
            try:
                data = f.read_bytes()
                if not _is_valid_osm_png(data):
                    f.unlink(missing_ok=True)
                    continue
                # Byte 25 of PNG is IHDR color_type:
                # Leftover ESRI World Street Map tiles are color_type == 2 (RGB) and > 2500 bytes.
                if data[25] == 2 and len(data) > 2500:
                    f.unlink(missing_ok=True)
                    continue
            except Exception:
                pass
    except Exception:
        pass


def _is_valid_osm_png(data: bytes) -> bool:
    """Validate that bytes represent a genuine map PNG tile (including 103-byte ocean tiles)
    and NOT an OpenStreetMap 403 'Access blocked' image, Carto 'API KEY REQUIRED' watermark, or HTML error."""
    if not data or len(data) < 67:
        return False
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return False
    if len(data) in (2048, 2049, 21645, 21644, 15403):
        return False
    # Carto "API KEY REQUIRED" watermark tiles are exactly 2048-2049 bytes
    if 2040 <= len(data) <= 2060:
        return False
    for sig in _OSM_BLOCKED_SIGNATURES:
        if sig in data:
            return False
    return True


_purge_stale_cached_tiles_once()


def _make_placeholder_svg_data_uri(zoom: int, x: int, y: int) -> str:
    """Return an instant, seamless SVG placeholder (ocean blue east of Aurora, warm land inland)."""
    # At Z10, x >= 858 (and equivalent scaled x at higher zooms) is the Philippine Sea
    scale = 1 << max(0, zoom - 10)
    is_ocean = (x >= 858 * scale and y >= 464 * scale)
    bg = "#aad3df" if is_ocean else "#f2efe9"
    grid = "#9bc6d3" if is_ocean else "#e6e1d6"
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">'
        f'<rect width="256" height="256" fill="{bg}"/>'
        f'<path d="M 256 0 L 0 0 0 256" fill="none" stroke="{grid}" stroke-width="0.6"/>'
        f'</svg>'
    )
    b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"


def _resolve_tile_source(
    zoom: int,
    x: int,
    y: int,
    on_tile_cached: Optional[Callable[[str, str], None]] = None,
) -> str:
    """Resolve a tile to a local Flet asset path (`/tiles/...` or `/tiles_cache/...`),
    triggering an asynchronous Python download if not yet cached on disk.
    NEVER returns a remote `https://` URL to `ft.Image` so Flutter's Dart HttpClient
    never triggers OpenStreetMap 403 blocks."""
    tile_key = f"{zoom}_{x}_{y}"

    # 1. Check pre-bundled offline tiles (accept any valid PNG >= 67 bytes)
    direct_cand = _BUNDLED_TILES_DIR / f"{tile_key}.png"
    if direct_cand.exists():
        try:
            if direct_cand.stat().st_size >= 67:
                return f"/tiles/{tile_key}.png"
        except OSError:
            pass

    nested_cand = _BUNDLED_TILES_DIR / str(zoom) / str(x) / f"{y}.png"
    if nested_cand.exists():
        try:
            if nested_cand.stat().st_size >= 67:
                return f"/tiles/{zoom}/{x}/{y}.png"
        except OSError:
            pass

    # 2. Check local disk cache
    cache_file = _CACHE_TILES_DIR / f"{tile_key}.png"
    if cache_file.exists():
        try:
            if cache_file.stat().st_size >= 67:
                return f"/tiles_cache/{tile_key}.png"
        except OSError:
            pass

    # 3. Download asynchronously in Python with compliant headers & multi-CDN fallback
    now = time.monotonic()
    with _TILE_LOCK:
        cooldown_until = _FAILED_TILES_COOLDOWN.get(tile_key, 0.0)
        should_fetch = (tile_key not in _IN_FLIGHT_TILES) and (now >= cooldown_until)
        if should_fetch:
            _IN_FLIGHT_TILES.add(tile_key)

    if should_fetch:
        sub = ("a", "b", "c")[(x + y) % 3]
        candidate_urls = [
            (
                f"https://{sub}.tile.openstreetmap.org/{zoom}/{x}/{y}.png",
                {
                    "User-Agent": "TripMoTripKoNuevaEcijaDesktop/2.5 (+https://edselrenz.github.io/Itinerary-App/; contact: edselrenz0@gmail.com)",
                    "Referer": "https://edselrenz.github.io/Itinerary-App/",
                    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                },
            ),
            (
                f"https://{sub}.tile.openstreetmap.fr/osmfr/{zoom}/{x}/{y}.png",
                {
                    "User-Agent": "TripMoTripKoNuevaEcijaDesktop/2.5 (+https://edselrenz.github.io/Itinerary-App/)",
                    "Referer": "https://edselrenz.github.io/Itinerary-App/",
                    "Accept": "image/png,image/*;q=0.8",
                },
            ),
            (
                f"https://{sub}.tile.openstreetmap.de/{zoom}/{x}/{y}.png",
                {
                    "User-Agent": "TripMoTripKoNuevaEcijaDesktop/2.5 (+https://edselrenz.github.io/Itinerary-App/)",
                    "Referer": "https://edselrenz.github.io/Itinerary-App/",
                    "Accept": "image/png,image/*;q=0.8",
                },
            ),
        ]

        def _fetch() -> None:
            saved_asset_path: Optional[str] = None
            try:
                for url, headers in candidate_urls:
                    try:
                        req = urllib.request.Request(url, headers=headers)
                        with urllib.request.urlopen(req, timeout=6) as resp:
                            if resp.status == 200:
                                data = resp.read()
                                if _is_valid_osm_png(data):
                                    tmp_file = _CACHE_TILES_DIR / f"{tile_key}.tmp"
                                    tmp_file.write_bytes(data)
                                    tmp_file.replace(cache_file)
                                    saved_asset_path = f"/tiles_cache/{tile_key}.png"
                                    break
                    except Exception:
                        continue
            finally:
                with _TILE_LOCK:
                    _IN_FLIGHT_TILES.discard(tile_key)
                    if not saved_asset_path:
                        _FAILED_TILES_COOLDOWN[tile_key] = time.monotonic() + 10.0

            if saved_asset_path and on_tile_cached:
                try:
                    on_tile_cached(tile_key, saved_asset_path)
                except Exception:
                    pass

        _TILE_EXECUTOR.submit(_fetch)

    return _make_placeholder_svg_data_uri(zoom, x, y)


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


CATEGORY_MARKER_STYLES: Dict[str, Tuple[str, str]] = {
    "nature": ("#16a34a", "PARK"),
    "attraction": ("#2563eb", "ATTRACTIONS"),
    "museum": ("#7c3aed", "MUSEUM"),
    "church": ("#d97706", "CHURCH"),
    "resort": ("#0891b2", "POOL"),
    "restaurant": ("#ea580c", "RESTAURANT"),
    "cafe": ("#92400e", "LOCAL_CAFE"),
    "hotel": ("#4f46e5", "HOTEL"),
    "market": ("#db2777", "STOREFRONT"),
    "transport": ("#0284c7", "DIRECTIONS_BUS"),
    "hospital": ("#dc2626", "LOCAL_HOSPITAL"),
    "pharmacy": ("#059669", "LOCAL_PHARMACY"),
    "bank": ("#0d9488", "ACCOUNT_BALANCE"),
    "fuel": ("#ca8a04", "LOCAL_GAS_STATION"),
    "convenience": ("#6366f1", "LOCAL_CONVENIENCE_STORE"),
    "public": ("#475569", "LOCATION_CITY"),
}

CATEGORY_PIN_STYLE = {
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


def latlng_to_world_px(lat: float, lng: float, zoom: int) -> Tuple[float, float]:
    """Project (lat, lng) in degrees to global Web-Mercator pixel coordinates at integer zoom."""
    lat_clamped = max(-85.05112878, min(85.05112878, float(lat)))
    n = float(1 << zoom) * 256.0
    wx = (float(lng) + 180.0) / 360.0 * n
    lat_rad = math.radians(lat_clamped)
    wy = (1.0 - math.log(math.tan(lat_rad) + (1.0 / math.cos(lat_rad))) / math.pi) / 2.0 * n
    return wx, wy


latlon_to_world_px = latlng_to_world_px


def world_px_to_latlng(wx: float, wy: float, zoom: int) -> Tuple[float, float]:
    """Inverse project global Web-Mercator pixel coordinates (wx, wy) back to (lat, lng)."""
    n = float(1 << zoom) * 256.0
    lng = (wx / n) * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1.0 - 2.0 * (wy / n))))
    lat = math.degrees(lat_rad)
    return lat, lng


world_px_to_latlon = world_px_to_latlng


def fetch_osrm_road_geometry(coords: list[tuple[float, float]], timeout: float = 3.0) -> list[tuple[float, float]]:
    """Fetch road-following geometry from public OSRM API for a sequence of (lat, lng) stops."""
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

    fallback_pts: list[tuple[float, float]] = []
    for i in range(len(valid) - 1):
        arc = generate_geodesic_arc(valid[i], valid[i + 1], num_points=24)
        if i > 0 and arc:
            arc = arc[1:]
        fallback_pts.extend(arc)
    return fallback_pts


class SlippyMapCanvas(ft.Container):
    """Smooth interactive slippy map canvas matching Web Leaflet behavior 1:1."""

    TILE_SIZE = 256
    MIN_ZOOM = 9
    MAX_ZOOM = 18

    # Matches Web map.page.ts NUEVA_ECIJA_BOUNDS with breathing room for widescreen viewports
    NUEVA_ECIJA_MIN_LAT = NUEVA_ECIJA_MIN_LAT
    NUEVA_ECIJA_MAX_LAT = NUEVA_ECIJA_MAX_LAT
    NUEVA_ECIJA_MIN_LNG = NUEVA_ECIJA_MIN_LNG
    NUEVA_ECIJA_MAX_LNG = NUEVA_ECIJA_MAX_LNG

    def __init__(
        self,
        page: Optional[ft.Page] = None,
        center_lat: float = 15.58,
        center_lng: float = 121.00,
        zoom: int = 10,
        width: int = 860,
        height: int = 580,
        places: Optional[Union[List[Place], List[Dict[str, Any]]]] = None,
        route_stops: Optional[Union[List[RouteStopPin], List[Dict[str, Any]]]] = None,
        route_geometry: Optional[List[Tuple[float, float]]] = None,
        route_polyline_points: Optional[List[Tuple[float, float]]] = None,
        route_coords: Optional[List[Tuple[float, float]]] = None,
        active_stop_index: Optional[int] = None,
        user_location: Optional[Tuple[float, float]] = None,
        selected_place_id: Optional[str] = None,
        on_place_click: Optional[Callable[[Any], None]] = None,
        on_stop_click: Optional[Callable[..., None]] = None,
        on_map_background_click: Optional[Callable[[], None]] = None,
        on_start_trip_here: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_add_to_trip: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_viewport_changed: Optional[Callable[[float, float, int], None]] = None,
        show_zoom_controls: bool = True,
        dark_mode: bool = False,
        border_radius: int = 0,
        **kwargs: Any,
    ) -> None:
        self._page_ref = page
        self.center_lat = float(center_lat)
        self.center_lng = float(center_lng)
        self.zoom = max(self.MIN_ZOOM, min(self.MAX_ZOOM, int(zoom)))
        self._map_w = max(320, int(width))
        self._map_h = max(240, int(height))

        # Backward-compatible route stops from route_coords
        self.route_coords = route_coords
        if route_coords and not route_stops:
            route_stops = [
                RouteStopPin(index=i, title=f"Stop {i+1}", lat=c[0], lng=c[1])
                for i, c in enumerate(route_coords)
            ]
            if not route_geometry and not route_polyline_points:
                route_geometry = route_coords
            min_c_lat = min(float(c[0]) for c in route_coords)
            max_c_lat = max(float(c[0]) for c in route_coords)
            min_c_lng = min(float(c[1]) for c in route_coords)
            max_c_lng = max(float(c[1]) for c in route_coords)
            self.center_lat = (min_c_lat + max_c_lat) / 2.0
            self.center_lng = (min_c_lng + max_c_lng) / 2.0

        self.places = places if places is not None else []
        self._places = self.places
        self.route_stops = route_stops if route_stops is not None else []
        self._route_stops = self.route_stops
        self.route_geometry = route_geometry or route_polyline_points or []
        self._route_pts = self.route_geometry
        self.active_stop_index = active_stop_index
        self._active_stop_index = active_stop_index
        self.user_location = user_location
        self._user_location = user_location
        self.selected_place_id = selected_place_id

        self.on_place_click = on_place_click
        self._on_place_click = on_place_click
        self.on_stop_click = on_stop_click
        self._on_stop_click = on_stop_click
        self.on_map_background_click = on_map_background_click
        self.on_start_trip_here = on_start_trip_here
        self.on_add_to_trip = on_add_to_trip
        self.on_viewport_changed = on_viewport_changed
        self.show_zoom_controls = show_zoom_controls
        self.dark_mode = dark_mode

        # Drag state & 60 FPS throttling
        self._drag_dx: float = 0.0
        self._drag_dy: float = 0.0
        self._last_pan_ui_ts: float = 0.0
        self._last_scroll_zoom: float = 0.0
        self._active_tile_images: Dict[str, ft.Image] = {}
        self._tile_pool: Dict[str, ft.Container] = {}
        self._fly_lock = threading.Lock()
        self._fly_generation = 0

        # Pre-computed spatial index cache
        self._parsed_places: List[Tuple[float, float, str, Any]] = []
        self._cached_cluster_zoom: Optional[int] = None
        self._cached_world_clusters: List[Dict[str, Any]] = []
        self._rebuild_spatial_index()

        # Layers
        self._tile_stack = ft.Stack(controls=[], width=self._map_w, height=self._map_h, clip_behavior=ft.ClipBehavior.NONE)
        self._vector_canvas = cv.Canvas(shapes=[], width=self._map_w, height=self._map_h)
        self._marker_stack = ft.Stack(controls=[], width=self._map_w, height=self._map_h, clip_behavior=ft.ClipBehavior.NONE)

        self._pan_layer = ft.Stack(
            controls=[self._tile_stack, self._vector_canvas],
            width=self._map_w,
            height=self._map_h,
            clip_behavior=ft.ClipBehavior.NONE,
        )
        self._viewport_mover = self._pan_layer

        self._zoom_label = ft.Text(
            f"Z{self.zoom}",
            size=10,
            weight=ft.FontWeight.W_700,
            color="#f8fafc" if self.dark_mode else "#334155",
            text_align=ft.TextAlign.CENTER,
        )

        # Gesture surface for pan, wheel zoom, double-click zoom, and background click
        self._gesture_surface = ft.GestureDetector(
            mouse_cursor=ft.MouseCursor.GRAB,
            drag_interval=14,
            on_pan_start=self._handle_pan_start,
            on_pan_update=self._handle_pan_update,
            on_pan_end=self._handle_pan_end,
            on_scroll=self._handle_scroll,
            on_double_tap=self._handle_double_tap,
            on_tap=self._handle_background_tap,
            content=ft.Container(
                width=self._map_w,
                height=self._map_h,
                bgcolor="#01000000",
            ),
        )
        self._gesture_layer = self._gesture_surface

        stack_children: List[ft.Control] = [
            self._pan_layer,
            self._gesture_surface,
            self._marker_stack,
            self._build_attribution_badge(),
        ]
        if self.show_zoom_controls:
            stack_children.append(self._build_zoom_controls())

        self._canvas_stack = ft.Stack(
            controls=stack_children,
            width=self._map_w,
            height=self._map_h,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )

        super().__init__(
            width=self._map_w,
            height=self._map_h,
            bgcolor="#0f172a" if self.dark_mode else "#e6e1d6",
            border_radius=border_radius,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            content=self._canvas_stack,
            **kwargs,
        )

        self._rebuild_layers(notify=False)

    # ------------------------------------------------------------------
    # Coordinate & Web Mercator Projections
    # ------------------------------------------------------------------
    @classmethod
    def latlng_to_world_px(cls, lat: float, lng: float, zoom: int) -> Tuple[float, float]:
        return latlng_to_world_px(lat, lng, zoom)

    @classmethod
    def world_px_to_latlng(cls, wx: float, wy: float, zoom: int) -> Tuple[float, float]:
        return world_px_to_latlng(wx, wy, zoom)

    def _clamp_center(self, lat: float, lng: float) -> Tuple[float, float]:
        c_lat = max(NUEVA_ECIJA_MIN_LAT, min(NUEVA_ECIJA_MAX_LAT, float(lat)))
        c_lng = max(NUEVA_ECIJA_MIN_LNG, min(NUEVA_ECIJA_MAX_LNG, float(lng)))
        return c_lat, c_lng

    def latlng_to_screen(self, lat: float, lng: float) -> Tuple[float, float]:
        cx, cy = self.latlng_to_world_px(self.center_lat, self.center_lng, self.zoom)
        px, py = self.latlng_to_world_px(lat, lng, self.zoom)
        sx = (self._map_w / 2.0) + (px - cx)
        sy = (self._map_h / 2.0) + (py - cy)
        return sx, sy

    def _latlon_to_viewport(self, lat: float, lng: float) -> Tuple[float, float]:
        return self.latlng_to_screen(lat, lng)

    def get_viewport_bounds(self) -> Tuple[float, float, float, float]:
        """Returns (min_lat, min_lng, max_lat, max_lng) for the currently visible map viewport."""
        cx, cy = self.latlng_to_world_px(self.center_lat, self.center_lng, self.zoom)
        nw_lat, nw_lng = self.world_px_to_latlng(cx - self._map_w / 2.0, cy - self._map_h / 2.0, self.zoom)
        se_lat, se_lng = self.world_px_to_latlng(cx + self._map_w / 2.0, cy + self._map_h / 2.0, self.zoom)
        return (min(nw_lat, se_lat), min(nw_lng, se_lng), max(nw_lat, se_lat), max(nw_lng, se_lng))

    # ------------------------------------------------------------------
    # Spatial Index & Clustering
    # ------------------------------------------------------------------
    def _rebuild_spatial_index(self) -> None:
        parsed: List[Tuple[float, float, str, Any]] = []
        for p in self.places:
            if isinstance(p, dict):
                lat = p.get("latitude") or p.get("lat")
                lng = p.get("longitude") or p.get("lng")
                pid = str(p.get("id") or p.get("place_id") or "")
            else:
                lat = getattr(p, "latitude", None)
                lng = getattr(p, "longitude", None)
                pid = str(getattr(p, "id", "") or "")
            if lat is None or lng is None:
                continue
            try:
                f_lat, f_lng = float(lat), float(lng)
            except (ValueError, TypeError):
                continue
            parsed.append((f_lat, f_lng, pid, p))
        self._parsed_places = parsed
        self._cached_cluster_zoom = None
        self._cached_world_clusters = []

    def _ensure_world_clusters(self) -> None:
        if self._cached_cluster_zoom == self.zoom:
            return
        self._cached_cluster_zoom = self.zoom

        # Match Web map.page.ts `disableClusteringAtZoom: 16`
        if self.zoom >= 16:
            self._cached_world_clusters = [
                {
                    "wx": self.latlng_to_world_px(f_lat, f_lng, self.zoom)[0],
                    "wy": self.latlng_to_world_px(f_lat, f_lng, self.zoom)[1],
                    "lat": f_lat,
                    "lng": f_lng,
                    "count": 1,
                    "place": p,
                    "pid": pid,
                }
                for (f_lat, f_lng, pid, p) in self._parsed_places
            ]
            return

        # Tighter cluster radius at Z14-Z15 so towns break apart cleanly as you zoom in
        cell_size = 76.0 if self.zoom <= 13 else 48.0
        grid: Dict[Tuple[int, int], List[Tuple[float, float, float, float, str, Any]]] = {}
        for f_lat, f_lng, pid, p in self._parsed_places:
            wx, wy = self.latlng_to_world_px(f_lat, f_lng, self.zoom)
            gx = int(wx // cell_size)
            gy = int(wy // cell_size)
            grid.setdefault((gx, gy), []).append((wx, wy, f_lat, f_lng, pid, p))

        clusters: List[Dict[str, Any]] = []
        for items in grid.values():
            cnt = len(items)
            if cnt == 1:
                wx, wy, f_lat, f_lng, pid, p = items[0]
                clusters.append(
                    {
                        "wx": wx,
                        "wy": wy,
                        "lat": f_lat,
                        "lng": f_lng,
                        "count": 1,
                        "place": p,
                        "pid": pid,
                    }
                )
            else:
                avg_wx = sum(x[0] for x in items) / cnt
                avg_wy = sum(x[1] for x in items) / cnt
                avg_lat = sum(x[2] for x in items) / cnt
                avg_lng = sum(x[3] for x in items) / cnt
                lats = [x[2] for x in items]
                lngs = [x[3] for x in items]
                clusters.append(
                    {
                        "wx": avg_wx,
                        "wy": avg_wy,
                        "lat": avg_lat,
                        "lng": avg_lng,
                        "count": cnt,
                        "place": items[0][5],
                        "pid": "",
                        "bounds": (min(lats), min(lngs), max(lats), max(lngs)),
                    }
                )
        self._cached_world_clusters = clusters

    # ------------------------------------------------------------------
    # Public API & Backward Compatibility
    # ------------------------------------------------------------------
    def resize_canvas(self, width: int, height: int) -> None:
        new_w = max(320, int(width))
        new_h = max(240, int(height))
        if abs(new_w - self._map_w) < 4 and abs(new_h - self._map_h) < 4:
            return
        self._map_w = new_w
        self._map_h = new_h
        self.width = new_w
        self.height = new_h
        self._canvas_stack.width = new_w
        self._canvas_stack.height = new_h
        self._tile_stack.width = new_w
        self._tile_stack.height = new_h
        self._vector_canvas.width = new_w
        self._vector_canvas.height = new_h
        self._pan_layer.width = new_w
        self._pan_layer.height = new_h
        self._marker_stack.width = new_w
        self._marker_stack.height = new_h
        self._viewport_mover.width = new_w
        self._viewport_mover.height = new_h
        if hasattr(self, "_gesture_surface") and isinstance(self._gesture_surface.content, ft.Container):
            self._gesture_surface.content.width = new_w
            self._gesture_surface.content.height = new_h
        self._rebuild_layers(notify=True)
        try:
            self.update()
            if getattr(self, "page", None):
                self.page.update()
        except Exception:
            pass

    resize_viewport = resize_canvas

    def set_view(self, lat: float, lng: float, zoom: Optional[int] = None) -> None:
        self.center_lat, self.center_lng = self._clamp_center(lat, lng)
        if zoom is not None:
            self.zoom = max(self.MIN_ZOOM, min(self.MAX_ZOOM, int(zoom)))
        self._drag_dx = 0.0
        self._drag_dy = 0.0
        self._pan_layer.left = 0
        self._pan_layer.top = 0
        self._marker_stack.left = 0
        self._marker_stack.top = 0
        self._rebuild_layers(notify=True)

    set_center_and_zoom = set_view

    def recenter_province(self) -> None:
        """Recenters to default Nueva Ecija provincial coordinates (15.58, 121.00, zoom 10)."""
        self.set_view(15.58, 121.00, 10)

    def fly_to(self, lat: float, lng: float, zoom: Optional[int] = None, animated: bool = True) -> None:
        """Smoothly animate camera pan/zoom to target coordinates (Leaflet flyTo parity)."""
        target_lat, target_lng = self._clamp_center(lat, lng)
        target_zoom = max(self.MIN_ZOOM, min(self.MAX_ZOOM, int(zoom))) if zoom is not None else self.zoom

        if not animated or (
            abs(target_lat - self.center_lat) < 0.0005
            and abs(target_lng - self.center_lng) < 0.0005
            and target_zoom == self.zoom
        ):
            self.set_view(target_lat, target_lng, target_zoom)
            return

        with self._fly_lock:
            self._fly_generation += 1
            my_gen = self._fly_generation

        start_lat, start_lng, start_zoom = self.center_lat, self.center_lng, self.zoom
        steps = 6 if target_zoom == start_zoom else 4

        def _animate() -> None:
            for step in range(1, steps + 1):
                with self._fly_lock:
                    if my_gen != self._fly_generation:
                        return
                t = step / float(steps)
                ease = 1.0 - pow(1.0 - t, 3)
                cur_lat = start_lat + (target_lat - start_lat) * ease
                cur_lng = start_lng + (target_lng - start_lng) * ease
                cur_zoom = target_zoom if step == steps else start_zoom
                self.center_lat, self.center_lng = self._clamp_center(cur_lat, cur_lng)
                self.zoom = cur_zoom
                self._drag_dx = 0.0
                self._drag_dy = 0.0
                self._viewport_mover.left = 0
                self._viewport_mover.top = 0
                self._rebuild_layers(notify=(step == steps))
                if step < steps:
                    time.sleep(0.022)

        threading.Thread(target=_animate, daemon=True).start()

    def set_zoom(self, new_zoom: int, focal_screen_xy: Optional[Tuple[float, float]] = None, notify: bool = True) -> None:
        clamped = max(self.MIN_ZOOM, min(self.MAX_ZOOM, int(new_zoom)))
        if clamped == self.zoom:
            return

        if focal_screen_xy is not None:
            # Keep geographic point under cursor stationary at the new zoom level (zoomAround)
            fx, fy = focal_screen_xy
            cx, cy = self.latlng_to_world_px(self.center_lat, self.center_lng, self.zoom)
            focus_wx = cx + (fx - self._map_w / 2.0)
            focus_wy = cy + (fy - self._map_h / 2.0)
            focus_lat, focus_lng = self.world_px_to_latlng(focus_wx, focus_wy, self.zoom)

            self.zoom = clamped
            new_focus_wx, new_focus_wy = self.latlng_to_world_px(focus_lat, focus_lng, self.zoom)
            new_cx = new_focus_wx - (fx - self._map_w / 2.0)
            new_cy = new_focus_wy - (fy - self._map_h / 2.0)
            new_lat, new_lng = self.world_px_to_latlng(new_cx, new_cy, self.zoom)
            self.center_lat, self.center_lng = self._clamp_center(new_lat, new_lng)
        else:
            self.zoom = clamped

        self._drag_dx = 0.0
        self._drag_dy = 0.0
        self._pan_layer.left = 0
        self._pan_layer.top = 0
        self._marker_stack.left = 0
        self._marker_stack.top = 0
        self._rebuild_layers(notify=notify)

    def set_places(self, places: Any, auto_fit: bool = False) -> None:
        self.places = list(places or [])
        self._places = self.places
        self._rebuild_spatial_index()
        if auto_fit and self._parsed_places:
            coords = [(p[0], p[1]) for p in self._parsed_places]
            self.fit_bounds(coords)
        else:
            self._rebuild_layers(notify=False)

    update_places = set_places

    def set_selected_place_id(self, place_id: Optional[str], pan_to: bool = False) -> None:
        self.selected_place_id = place_id
        if pan_to and place_id:
            for f_lat, f_lng, pid, _ in self._parsed_places:
                if pid == str(place_id):
                    lat_offset = -0.008 * pow(2, max(0, 13 - self.zoom)) if self.zoom >= 12 else 0.0
                    self.fly_to(f_lat + lat_offset, f_lng, animated=True)
                    return
        self._render_markers()
        try:
            if self.page:
                self._marker_stack.update()
        except Exception:
            pass

    def set_route(
        self,
        stops: Any,
        polyline_points: Optional[List[Tuple[float, float]]] = None,
        active_stop_index: Optional[int] = None,
        auto_fit: bool = True,
    ) -> None:
        self.route_stops = list(stops or [])
        self._route_stops = self.route_stops
        self.active_stop_index = active_stop_index
        self._active_stop_index = active_stop_index
        if polyline_points is not None and len(polyline_points) >= 2:
            self.route_geometry = list(polyline_points)
            self._route_pts = self.route_geometry
        elif len(self.route_stops) >= 2:
            coords: List[Tuple[float, float]] = []
            for s in self.route_stops:
                lat = s.get("lat") or s.get("latitude") if isinstance(s, dict) else getattr(s, "lat", None)
                lng = s.get("lng") or s.get("longitude") if isinstance(s, dict) else getattr(s, "lng", None)
                if lat and lng:
                    coords.append((float(lat), float(lng)))
            if coords:
                arc_pts: List[Tuple[float, float]] = []
                for i in range(len(coords) - 1):
                    seg = generate_geodesic_arc(coords[i], coords[i + 1])
                    if arc_pts:
                        arc_pts.extend(seg[1:])
                    else:
                        arc_pts.extend(seg)
                self.route_geometry = arc_pts or coords
                self._route_pts = self.route_geometry

                def _async_osrm():
                    try:
                        pts = fetch_osrm_road_geometry(coords)
                        if pts and len(pts) >= 2:
                            self.route_geometry = pts
                            self._route_pts = pts
                            self._render_route_vectors()
                            p = self.page or self._page_ref
                            if p is not None:
                                async def _apply_vectors():
                                    try:
                                        self._vector_canvas.update()
                                    except Exception:
                                        pass
                                p.run_task(_apply_vectors)
                    except Exception:
                        pass
                _TILE_EXECUTOR.submit(_async_osrm)
        else:
            self.route_geometry = []
            self._route_pts = []

        if auto_fit and (self.route_stops or self.route_geometry):
            self.fit_to_route(notify=False)
        self._rebuild_layers(notify=True)

    update_route = set_route

    def fit_to_route(self, notify: bool = True) -> None:
        coords: List[Tuple[float, float]] = []
        for s in self.route_stops:
            lat = s.get("latitude") or s.get("lat") if isinstance(s, dict) else getattr(s, "lat", None)
            lng = s.get("longitude") or s.get("lng") if isinstance(s, dict) else getattr(s, "lng", None)
            if lat is not None and lng is not None:
                try:
                    coords.append((float(lat), float(lng)))
                except (ValueError, TypeError):
                    pass
        for pt in self.route_geometry:
            if len(pt) >= 2:
                coords.append((float(pt[0]), float(pt[1])))
        if not coords and self._parsed_places:
            coords = [(x[0], x[1]) for x in self._parsed_places]
        if not coords:
            return
        self.fit_bounds(coords, notify=notify)

    fit_to_content = fit_to_route

    def fit_bounds(
        self,
        min_lat_or_coords: Any,
        min_lng: Optional[float] = None,
        max_lat: Optional[float] = None,
        max_lng: Optional[float] = None,
        notify: bool = True,
        padding_px: int = 48,
    ) -> None:
        if isinstance(min_lat_or_coords, (list, tuple)) and (min_lng is None or isinstance(min_lat_or_coords[0], (list, tuple))):
            coords = [c for c in min_lat_or_coords if len(c) >= 2 and c[0] is not None and c[1] is not None]
            if not coords:
                return
            min_lat = min(float(c[0]) for c in coords)
            min_lng = min(float(c[1]) for c in coords)
            max_lat = max(float(c[0]) for c in coords)
            max_lng = max(float(c[1]) for c in coords)
        else:
            min_lat = float(min_lat_or_coords)
            min_lng = float(min_lng)
            max_lat = float(max_lat)
            max_lng = float(max_lng)

        self.center_lat, self.center_lng = self._clamp_center(
            (min_lat + max_lat) / 2.0,
            (min_lng + max_lng) / 2.0,
        )
        usable_w = max(120, self._map_w - 2 * padding_px)
        usable_h = max(120, self._map_h - 2 * padding_px)
        best_z = 15
        for z in range(self.MAX_ZOOM, self.MIN_ZOOM - 1, -1):
            wx1, wy1 = self.latlng_to_world_px(max_lat, min_lng, z)
            wx2, wy2 = self.latlng_to_world_px(min_lat, max_lng, z)
            if abs(wx2 - wx1) <= usable_w and abs(wy2 - wy1) <= usable_h:
                best_z = z
                break
        self.zoom = max(self.MIN_ZOOM, min(16, best_z))
        self._drag_dx = 0.0
        self._drag_dy = 0.0
        self._viewport_mover.left = 0
        self._viewport_mover.top = 0
        self._rebuild_layers(notify=notify)

    def redraw(self) -> None:
        self._rebuild_layers(notify=True)

    # ------------------------------------------------------------------
    # 60 FPS Gesture Handlers
    # ------------------------------------------------------------------
    def _handle_pan_start(self, e: Any = None) -> None:
        with self._fly_lock:
            self._fly_generation += 1
        self._drag_dx = 0.0
        self._drag_dy = 0.0
        self._gesture_surface.mouse_cursor = ft.MouseCursor.GRABBING

    def _handle_pan_update(self, e: Any) -> None:
        pdx, pdy = _extract_pan_delta(e)
        raw_dx = self._drag_dx + pdx
        raw_dy = self._drag_dy + pdy

        # Clamp prospective center DURING drag so the map never overshoots and snaps back
        cx, cy = self.latlng_to_world_px(self.center_lat, self.center_lng, self.zoom)
        prospective_lat, prospective_lng = self.world_px_to_latlng(cx - raw_dx, cy - raw_dy, self.zoom)
        clamped_lat, clamped_lng = self._clamp_center(prospective_lat, prospective_lng)
        clamped_wx, clamped_wy = self.latlng_to_world_px(clamped_lat, clamped_lng, self.zoom)

        self.center_lat = clamped_lat
        self.center_lng = clamped_lng

        self._drag_dx = cx - clamped_wx
        self._drag_dy = cy - clamped_wy

        # Seamless mid-drag rebase when pan exceeds 220px (well inside our 2-tile / 512px buffer)
        if abs(self._drag_dx) >= 220 or abs(self._drag_dy) >= 220:
            self._drag_dx = 0.0
            self._drag_dy = 0.0
            self._pan_layer.left = 0
            self._pan_layer.top = 0
            self._marker_stack.left = 0
            self._marker_stack.top = 0
            self._last_pan_ui_ts = time.monotonic()
            self._rebuild_layers(notify=False)
            return

        now = time.monotonic()
        if now - self._last_pan_ui_ts < 0.015:  # ~60 FPS cap
            return
        self._last_pan_ui_ts = now

        # Update lightweight layer containers
        self._pan_layer.left = round(self._drag_dx, 1)
        self._pan_layer.top = round(self._drag_dy, 1)
        self._marker_stack.left = round(self._drag_dx, 1)
        self._marker_stack.top = round(self._drag_dy, 1)
        try:
            if self.page:
                self._pan_layer.update()
                self._marker_stack.update()
        except Exception:
            pass

    def _handle_pan_end(self, e: Any = None) -> None:
        self._gesture_surface.mouse_cursor = ft.MouseCursor.GRAB
        if abs(self._drag_dx) < 1.5 and abs(self._drag_dy) < 1.5:
            self._drag_dx = 0.0
            self._drag_dy = 0.0
            self._pan_layer.left = 0
            self._pan_layer.top = 0
            self._marker_stack.left = 0
            self._marker_stack.top = 0
            return

        cx, cy = self.latlng_to_world_px(self.center_lat, self.center_lng, self.zoom)
        new_lat, new_lng = self.world_px_to_latlng(cx - self._drag_dx, cy - self._drag_dy, self.zoom)
        self.center_lat, self.center_lng = self._clamp_center(new_lat, new_lng)
        self._drag_dx = 0.0
        self._drag_dy = 0.0
        self._pan_layer.left = 0
        self._pan_layer.top = 0
        self._marker_stack.left = 0
        self._marker_stack.top = 0
        self._rebuild_layers(notify=True)

    def _handle_scroll(self, e: Any) -> None:
        dy = _extract_scroll_delta_y(e)
        if abs(dy) < 0.5:
            return
        now = time.monotonic()
        if now - getattr(self, "_last_scroll_zoom", 0.0) < 0.1:
            return
        self._last_scroll_zoom = now

        focal: Optional[Tuple[float, float]] = None
        if getattr(e, "local_position", None) is not None:
            try:
                focal = (float(e.local_position.x), float(e.local_position.y))
            except Exception:
                focal = None
        if dy < 0:
            self.set_zoom(self.zoom + 1, focal_screen_xy=focal)
        elif dy > 0:
            self.set_zoom(self.zoom - 1, focal_screen_xy=focal)

    def _handle_double_tap(self, e: ft.TapEvent) -> None:
        focal: Optional[Tuple[float, float]] = None
        if getattr(e, "local_position", None) is not None:
            try:
                focal = (float(e.local_position.x), float(e.local_position.y))
            except Exception:
                focal = None
        self.set_zoom(self.zoom + 1, focal_screen_xy=focal)

    def _handle_background_tap(self, e: ft.TapEvent) -> None:
        if self.on_map_background_click:
            self.on_map_background_click()

    # ------------------------------------------------------------------
    # Tile, Route Vector & Marker Rendering
    # ------------------------------------------------------------------
    def _on_tile_cached_live(self, tile_key: str, asset_path: str) -> None:
        """Swap in a freshly cached local PNG tile onto the active ft.Image control on screen."""
        img_ctrl = self._active_tile_images.get(tile_key)
        if img_ctrl is None:
            return
        img_ctrl.src = asset_path
        try:
            p = getattr(img_ctrl, "page", None) or getattr(self, "page", None)
            if p:
                img_ctrl.update()
        except Exception:
            pass

    def _rebuild_layers(self, notify: bool = True) -> None:
        self._zoom_label.value = f"Z{self.zoom}"
        self._zoom_label.color = "#f8fafc" if self.dark_mode else "#334155"
        self.bgcolor = "#0f172a" if self.dark_mode else "#e6e1d6"

        self._render_tiles()
        self._render_route_vectors()
        self._render_markers()

        try:
            if self.page:
                self.update()
        except Exception:
            pass

        if notify and self.on_viewport_changed:
            try:
                self.on_viewport_changed(self.center_lat, self.center_lng, self.zoom)
            except Exception:
                pass

    def _render_tiles(self) -> None:
        cx, cy = self.latlng_to_world_px(self.center_lat, self.center_lng, self.zoom)
        top_left_wx = cx - (self._map_w / 2.0)
        top_left_wy = cy - (self._map_h / 2.0)

        # 2-tile outer buffer on all sides so 220px mid-drag panning never exposes blank edges
        min_tx = int(math.floor(top_left_wx / self.TILE_SIZE)) - 2
        max_tx = int(math.floor((top_left_wx + self._map_w) / self.TILE_SIZE)) + 2
        min_ty = int(math.floor(top_left_wy / self.TILE_SIZE)) - 2
        max_ty = int(math.floor((top_left_wy + self._map_h) / self.TILE_SIZE)) + 2

        max_tile_idx = (1 << self.zoom) - 1
        tile_controls: List[ft.Control] = []
        self._active_tile_images.clear()
        self._tile_pool.clear()

        for tx in range(min_tx, max_tx + 1):
            for ty in range(min_ty, max_ty + 1):
                if ty < 0 or ty > max_tile_idx:
                    continue
                wrapped_tx = tx % (1 << self.zoom)
                screen_x = round(tx * self.TILE_SIZE - top_left_wx)
                screen_y = round(ty * self.TILE_SIZE - top_left_wy)

                tile_key = f"{self.zoom}_{wrapped_tx}_{ty}"
                tile_src = _resolve_tile_source(
                    self.zoom,
                    wrapped_tx,
                    ty,
                    on_tile_cached=self._on_tile_cached_live,
                )

                img_ctrl = ft.Image(
                    src=tile_src,
                    width=self.TILE_SIZE + 1,  # +1px prevents subpixel hairline seams
                    height=self.TILE_SIZE + 1,
                    fit=ft.BoxFit.FILL,
                    gapless_playback=True,
                    color="#475569" if self.dark_mode else None,
                    color_blend_mode=ft.BlendMode.MODULATE if self.dark_mode else None,
                )
                self._active_tile_images[tile_key] = img_ctrl

                tile_cont = ft.Container(
                    left=screen_x,
                    top=screen_y,
                    width=self.TILE_SIZE + 1,
                    height=self.TILE_SIZE + 1,
                    content=img_ctrl,
                )
                self._tile_pool[tile_key] = tile_cont
                tile_controls.append(tile_cont)

        self._tile_stack.controls = tile_controls

    def _render_route_vectors(self) -> None:
        shapes: List[Any] = []
        path_coords: List[Tuple[float, float]] = []

        if self.route_geometry and len(self.route_geometry) >= 2:
            path_coords = [(float(pt[0]), float(pt[1])) for pt in self.route_geometry]
        elif len(self.route_stops) >= 2:
            for s in self.route_stops:
                lat = s.get("latitude") or s.get("lat") if isinstance(s, dict) else getattr(s, "lat", None)
                lng = s.get("longitude") or s.get("lng") if isinstance(s, dict) else getattr(s, "lng", None)
                if lat is not None and lng is not None:
                    try:
                        path_coords.append((float(lat), float(lng)))
                    except (ValueError, TypeError):
                        pass

        if len(path_coords) >= 2:
            screen_pts = [self.latlng_to_screen(lat, lng) for lat, lng in path_coords]
            path_elements = [cv.Path.MoveTo(screen_pts[0][0], screen_pts[0][1])]
            for sx, sy in screen_pts[1:]:
                path_elements.append(cv.Path.LineTo(sx, sy))

            # Outer white casing + inner primary blue route line (matches Web L.polyline)
            shapes.append(
                cv.Path(
                    elements=path_elements,
                    paint=ft.Paint(
                        color="#ffffff" if not self.dark_mode else "#0f172a",
                        stroke_width=8,
                        style=ft.PaintingStyle.STROKE,
                        stroke_cap=ft.StrokeCap.ROUND,
                        stroke_join=ft.StrokeJoin.ROUND,
                    ),
                )
            )
            shapes.append(
                cv.Path(
                    elements=path_elements,
                    paint=ft.Paint(
                        color="#2563eb",
                        stroke_width=5,
                        style=ft.PaintingStyle.STROKE,
                        stroke_cap=ft.StrokeCap.ROUND,
                        stroke_join=ft.StrokeJoin.ROUND,
                    ),
                )
            )

        self._vector_canvas.shapes = shapes

    def _render_markers(self) -> None:
        controls: List[ft.Control] = []

        # 1. User location blue pulse dot
        if self.user_location or self._user_location:
            ulat, ulng = self.user_location or self._user_location
            ux, uy = self.latlng_to_screen(ulat, ulng)
            if -40 <= ux <= self._map_w + 40 and -40 <= uy <= self._map_h + 40:
                controls.append(
                    ft.Container(
                        left=ux - 14,
                        top=uy - 14,
                        width=28,
                        height=28,
                        border_radius=14,
                        bgcolor=ft.Colors.with_opacity(0.24, "#0284c7"),
                        alignment=ft.Alignment.CENTER,
                        content=ft.Container(
                            width=14,
                            height=14,
                            border_radius=7,
                            bgcolor="#0284c7",
                            border=ft.Border.all(2.5, "#ffffff"),
                        ),
                        tooltip="Your Location",
                    )
                )

        # 2. Clustered / Individual POI Markers
        if self._parsed_places:
            self._ensure_world_clusters()
            cx, cy = self.latlng_to_world_px(self.center_lat, self.center_lng, self.zoom)
            half_w = self._map_w / 2.0
            half_h = self._map_h / 2.0

            rendered_count = 0
            max_markers = 160 if self.zoom >= 16 else 96
            for item in self._cached_world_clusters:
                sx = half_w + (item["wx"] - cx)
                sy = half_h + (item["wy"] - cy)
                if not (-48 <= sx <= self._map_w + 48 and -48 <= sy <= self._map_h + 48):
                    continue
                if rendered_count >= max_markers:
                    break
                rendered_count += 1

                if item["count"] == 1:
                    controls.append(self._build_single_place_marker(item["place"], sx, sy))
                else:
                    controls.append(
                        self._build_cluster_marker(
                            item["count"],
                            item["lat"],
                            item["lng"],
                            sx,
                            sy,
                            bounds=item.get("bounds"),
                        )
                    )

        # 3. Numbered Itinerary Route Stop Pins (Always rendered on top)
        for idx, stop in enumerate(self.route_stops):
            if isinstance(stop, dict):
                lat = stop.get("latitude") or stop.get("lat")
                lng = stop.get("longitude") or stop.get("lng")
            else:
                lat = getattr(stop, "lat", None)
                lng = getattr(stop, "lng", None)
            if lat is None or lng is None:
                continue
            try:
                sx, sy = self.latlng_to_screen(float(lat), float(lng))
            except (ValueError, TypeError):
                continue
            if -50 <= sx <= self._map_w + 50 and -50 <= sy <= self._map_h + 50:
                controls.append(self._build_route_stop_marker(idx + 1, stop, sx, sy))

        self._marker_stack.controls = controls

    def _build_cluster_marker(
        self,
        count: int,
        lat: float,
        lng: float,
        sx: float,
        sy: float,
        bounds: Optional[Tuple[float, float, float, float]] = None,
    ) -> ft.Control:
        size = 36 if count < 15 else (42 if count < 60 else 48)
        bg = "#2563eb" if count < 60 else "#1d4ed8"

        def _zoom_cluster(_: ft.ControlEvent) -> None:
            if bounds and (bounds[2] - bounds[0] > 0.002 or bounds[3] - bounds[1] > 0.002):
                self.fit_bounds(bounds[0], bounds[1], bounds[2], bounds[3], notify=True)
            else:
                self.fly_to(lat, lng, min(self.MAX_ZOOM, self.zoom + 2), animated=True)

        return ft.Container(
            left=sx - (size / 2.0),
            top=sy - (size / 2.0),
            width=size,
            height=size,
            border_radius=size / 2.0,
            bgcolor=ft.Colors.with_opacity(0.22, bg),
            alignment=ft.Alignment.CENTER,
            on_click=_zoom_cluster,
            tooltip=f"{count} places in this area — click to zoom in",
            content=ft.Container(
                width=size - 6,
                height=size - 6,
                border_radius=(size - 6) / 2.0,
                bgcolor=bg,
                border=ft.Border.all(2, "#ffffff"),
                alignment=ft.Alignment.CENTER,
                shadow=ft.BoxShadow(
                    blur_radius=8,
                    color=ft.Colors.with_opacity(0.28, "#0f172a"),
                    offset=ft.Offset(0, 2),
                ),
                content=ft.Text(
                    str(count),
                    size=11 if count < 100 else 10,
                    weight=ft.FontWeight.W_800,
                    color="#ffffff",
                ),
            ),
        )

    def _build_single_place_marker(self, place: Any, sx: float, sy: float) -> ft.Control:
        if isinstance(place, dict):
            cat_raw = str(place.get("category") or "attraction").lower()
            pid = str(place.get("id") or place.get("place_id") or "")
            name = place.get("name") or "Destination"
            mun = place.get("municipality") or place.get("municipality_name") or "Nueva Ecija"
        else:
            cat_raw = str(getattr(place, "category", "attraction")).lower()
            pid = str(getattr(place, "id", "") or "")
            name = getattr(place, "name", "Destination")
            mun = getattr(place, "municipality_name", "Nueva Ecija")

        bg_color, icon_name = "#2563eb", "PLACE"
        for key, (col, icn) in CATEGORY_MARKER_STYLES.items():
            if key in cat_raw:
                bg_color, icon_name = col, icn
                break

        is_selected = bool(self.selected_place_id and pid == str(self.selected_place_id))
        size = 36 if is_selected else 28

        def _click_place(_: ft.ControlEvent, p: Any = place, p_id: str = pid) -> None:
            self.selected_place_id = p_id
            if self.on_place_click:
                self.on_place_click(p)

        return ft.Container(
            left=sx - (size / 2.0),
            top=sy - (size / 2.0),
            width=size,
            height=size,
            border_radius=size / 2.0,
            bgcolor="#1d4ed8" if is_selected else bg_color,
            border=ft.Border.all(3 if is_selected else 2, "#ffffff"),
            alignment=ft.Alignment.CENTER,
            shadow=ft.BoxShadow(
                blur_radius=10 if is_selected else 6,
                color=ft.Colors.with_opacity(0.38 if is_selected else 0.25, "#0f172a"),
                offset=ft.Offset(0, 2),
            ),
            on_click=_click_place,
            tooltip=f"{name} ({mun})",
            content=ft.Icon(
                getattr(ft.Icons, icon_name, ft.Icons.PLACE),
                size=17 if is_selected else 14,
                color="#ffffff",
            ),
        )

    def _build_route_stop_marker(self, stop_num: int, stop: Any, sx: float, sy: float) -> ft.Control:
        if isinstance(stop, dict):
            name = stop.get("name") or stop.get("title") or f"Stop {stop_num}"
            stop_idx = stop.get("index", stop_num - 1)
        else:
            name = getattr(stop, "title", f"Stop {stop_num}")
            stop_idx = getattr(stop, "index", stop_num - 1)

        is_active = (self.active_stop_index == stop_idx) or (self._active_stop_index == stop_idx)
        bg = "#f97316" if is_active else "#1d4ed8"

        def _click_stop(_: ft.ControlEvent, s: Any = stop) -> None:
            if self.on_stop_click:
                try:
                    sig = inspect.signature(self.on_stop_click)
                    if len(sig.parameters) >= 2:
                        self.on_stop_click(stop_idx, s)
                    else:
                        self.on_stop_click(s)
                except Exception:
                    self.on_stop_click(s)
            elif self.on_place_click:
                self.on_place_click(s)

        return ft.Container(
            left=sx - 16,
            top=sy - 16,
            width=32,
            height=32,
            border_radius=16,
            bgcolor=bg,
            border=ft.Border.all(2.5, "#ffffff"),
            alignment=ft.Alignment.CENTER,
            shadow=ft.BoxShadow(
                blur_radius=8,
                color=ft.Colors.with_opacity(0.32, "#0f172a"),
                offset=ft.Offset(0, 2),
            ),
            on_click=_click_stop,
            tooltip=f"Stop {stop_num}: {name}",
            content=ft.Text(
                str(stop_num),
                size=12,
                weight=ft.FontWeight.W_800,
                color="#ffffff",
            ),
        )

    def _build_zoom_controls(self) -> ft.Control:
        card_bg = ft.Colors.with_opacity(0.95, "#1e293b" if self.dark_mode else "#ffffff")
        icon_col = "#f8fafc" if self.dark_mode else "#0f172a"
        border_col = "#334155" if self.dark_mode else "#e2e8f0"

        return ft.Container(
            right=16,
            bottom=24,
            bgcolor=card_bg,
            border_radius=14,
            border=ft.Border.all(1, border_col),
            padding=ft.Padding.symmetric(horizontal=4, vertical=4),
            shadow=ft.BoxShadow(
                blur_radius=12,
                color=ft.Colors.with_opacity(0.14, "#0f172a"),
                offset=ft.Offset(0, 4),
            ),
            content=ft.Column(
                spacing=2,
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.ADD,
                        icon_size=16,
                        icon_color=icon_col,
                        tooltip="Zoom In",
                        on_click=lambda _: self.set_zoom(self.zoom + 1),
                        style=ft.ButtonStyle(padding=4),
                    ),
                    self._zoom_label,
                    ft.IconButton(
                        icon=ft.Icons.REMOVE,
                        icon_size=16,
                        icon_color=icon_col,
                        tooltip="Zoom Out",
                        on_click=lambda _: self.set_zoom(self.zoom - 1),
                        style=ft.ButtonStyle(padding=4),
                    ),
                    ft.Divider(height=1, color=border_col),
                    ft.IconButton(
                        icon=ft.Icons.CENTER_FOCUS_STRONG,
                        icon_size=15,
                        icon_color="#2563eb",
                        tooltip="Fit All Visible Markers",
                        on_click=lambda _: self.fit_to_route(),
                        style=ft.ButtonStyle(padding=4),
                    ),
                ],
            ),
        )

    def _build_attribution_badge(self) -> ft.Control:
        return ft.Container(
            left=10,
            bottom=8,
            bgcolor=ft.Colors.with_opacity(0.84, "#0f172a" if self.dark_mode else "#ffffff"),
            border_radius=6,
            padding=ft.Padding.symmetric(horizontal=6, vertical=2),
            content=ft.Text(
                "© OpenStreetMap contributors • OSRM",
                size=9,
                color="#cbd5e1" if self.dark_mode else "#475569",
            ),
        )
