# Antigravity Remediation Plan (v2 — Post-Session 53 Re-QA): Map Tab, Suggested Itinerary & Custom Itinerary Parity

This specification documents the post-Session 53 (`v0.52.0`) QA audit comparing the updated Desktop Application (`desktop_client/`) against the live Web Application at [Trip mo, trip ko — Nueva Ecija](https://edselrenz.github.io/Itinerary-App/#/welcome) (`Project/src/app/`).

While Session 53 resolved the backend/API client headers, `PlaceCard` compact kwargs, and `to_backend_iso_time()` serialization, **20 critical runtime, layout, gesture, and state-machine defects** remain across the **Map Tab (`PlacesView` / `SlippyMapCanvas`)**, **Suggested Itinerary Wizard (`SuggestedWizardView` / `ItineraryService`)**, and **Custom Itinerary Builder (`CustomBuilderView` / `TripDetailView`)**.

Execute **Phases 1 through 5** in order, then run the verification suite in **Phase 6**.

---

## Executive Defect Matrix (Post-Session 53 Re-QA vs. Live Webpage)

| ID | Subsystem | File & Lines | Exact Root Cause in `v0.52.0` | Live Web App Behavior (`https://edselrenz.github.io/Itinerary-App/`) |
| :--- | :--- | :--- | :--- | :--- |
| **`MAP-01`** | Map Tab Pointer Block | `desktop_client/views/places_view.py:407–440` | `_build_drawer_toggle_pill()` returns an outer `ft.Container(bottom=18, left=0, right=0, alignment=ft.Alignment(0, 1))` with no `height`/`width` inside `ft.Stack(expand=True)`. In Flutter, `Container(alignment=...)` creates an `Align` widget that expands to fill the parent `Stack`, forming an invisible full-screen overlay above `SlippyMapCanvas` that intercepts mouse clicks and drags. | Floating `List View (2673)` pill (`map.page.html:187–197`) only occupies its own compact button bounds at bottom-center without blocking map clicks or drags. |
| **`MAP-02`** | Map Gestures & Pin Clicks | `desktop_client/components/slippy_map_canvas.py:285–298` | `ft.GestureDetector` wraps `ft.Stack([self._tile_stack, self._vector_canvas, self._marker_stack])` without a hit-testable background surface and puts `_marker_stack` inside `GestureDetector`, causing pan gestures and marker `on_click` handlers to collide in Flutter's gesture arena. Also lacks `on_scroll` (mouse-wheel zoom) and `on_double_tap` (double-click zoom). | Smooth drag panning everywhere, scroll-wheel zoom, double-click zoom, and instant click handling on cluster bubbles and pins (`map.page.ts:449–535`). |
| **`MAP-03`** | Missing Route Polylines & Auto-Fit | `desktop_client/components/slippy_map_canvas.py:220–221, 310` | `SlippyMapCanvas.__init__()` sets `self._route_pts = list(route_polyline_points or [])` (`[]`) and calls `self.redraw()` without calling `self.set_route()`. Because `PlacesView` (`places_view.py:221`) and `ItineraryRouteMap` (`itinerary_route_map.py:235`) pass `route_stops` to `__init__` without calling `set_route()`, **zero road polylines are ever drawn** and the map stays stuck at provincial Zoom 10 instead of fitting the stops. | Every route map (`ItineraryRouteMapComponent` & Follow-Route Map) computes road geometry and fits bounds to the day's stops on mount. |
| **`MAP-04`** | Stuck in Follow-Route Mode | `desktop_client/main.py:263–267` & `views/places_view.py:110–119` | `main.py` passes `active_trip=selected_trip` to `PlacesView` on `/map`. `PlacesView._check_and_init_route_mode()` sets `self.is_follow_route_mode = True` whenever `self.active_trip` is truthy—even when the route is plain `/map` with no `itineraryId` query param! Once any trip is viewed or created, clicking the **Map** tab hides all 2,673 markers, search bar, and category pills. Also, `main.py:84` calls `recenter_map()`, which does not exist on `PlacesView`. | [Map Tab](https://edselrenz.github.io/Itinerary-App/#/tabs/map) only enters Follow-Route mode when `?followRoute=true` or `?itineraryId=...` is in the URL (`map.page.ts:330, 347–356`). |
| **`MAP-05`** | Search Input Loses Focus & Resets Map | `desktop_client/views/places_view.py:716–737` | `_on_search_change()`, `_clear_search()`, `_select_category()`, and `_toggle_drawer()` call `self._build_content()`, which destroys the `ft.TextField` (losing keyboard focus after typing 1 character!) and instantiates a brand-new `SlippyMapCanvas` at `zoom=10, (15.58, 121.00)`, wiping out the user's pan/zoom state. | Typing in the search bar or clicking category pills updates markers and counts in-place without losing input focus or resetting the map (`map.page.ts:310–318, 854–871`). |
| **`MAP-06`** | Thread-Unsafe Redraws in `_TILE_EXECUTOR` | `desktop_client/components/slippy_map_canvas.py:71–92, 342–353, 466` | Up to 6 `ThreadPoolExecutor` worker threads download tiles and call `on_ready=self.redraw` (`self.update()`) concurrently from non-asyncio threads, mutating `_tile_stack.controls` and `_marker_stack.controls` simultaneously. Also runs 7 `cand.is_file()` checks per missing tile via `settings.get_asset_path()`. | Tile loading and route updates occur asynchronously without mutating the UI tree from background threads. |
| **`MAP-07`** | Missing `import httpx` in `PlaceService` | `desktop_client/services/place_service.py:319` | `fetch_live_osm_places()` calls `httpx.AsyncClient(timeout=10.0)`, raising `NameError: name 'httpx' is not defined` whenever `[✨ Live OSM]` is clicked. Also, `PlacesView._refresh_live_places()` ignores current map viewport bounds. | Clicking `[✨]` queries Overpass API for the current map viewport bounding box (`map.page.ts:678–736`). |
| **`MAP-08`** | Overlapping Map Buttons & Clipping | `desktop_client/views/places_view.py:221–223, 401–405` & `main.py:65–71` | `main.py` never sets `page.window.width`/`height`. `PlacesView` hardcodes `SlippyMapCanvas(width=1240, height=740)`, clipping the bottom 50px, and places `_build_floating_action_buttons()` at `right=16, bottom=90` directly on top of `SlippyMapCanvas` zoom controls (`right=12, bottom=28`). | Floating action buttons and zoom controls are cleanly separated with zero overlap or viewport clipping. |
| **`MAP-09`** | Single-Select Filter Modal & Price Bug | `desktop_client/views/places_view.py:142–159, 815–921` | Filter modal only allows single-category selection instead of multi-select (`selectedCategories: Set<string>`), lacks the active filter count badge on the `Filters` button, and treats `estimated_cost_min=None` as `0 <= 500` in the `budget` price tier filter. | [Map Tab Filters Modal](https://edselrenz.github.io/Itinerary-App/#/tabs/map) supports multi-category selection, active filter badge (`Filters [1]`), and accurate price tier filtering (`map.page.ts:748–766, 883–957`). |
| **`MAP-10`** | Cramped Horizontal POI Drawer | `desktop_client/views/places_view.py:442–491` | `_build_poi_drawer()` renders a horizontal row of tall `PlaceCard`s that overflow vertically inside the `220px` drawer and lacks an empty state + `"Reset All Filters"` button when 0 places match. | Opens a clean vertical scrollable sheet of compact destination rows with an empty-state reset button (`map.page.html:240–315`). |
| **`SUG-01`** | Preference Keys Sent as Labels | `desktop_client/views/suggested_wizard_view.py:91–95, 324–330` | Stores and sends human-readable labels (`"Nature & Parks"`, `"Food Trip"`, `"Culture & History"`) in `SuggestedItineraryRequest.preferences`. Backend `resolve_preference_categories()` (`backend/app/algorithms/itinerary_generator.py:26–68`) expects canonical keys (`"nature"`, `"food"`, `"culture"`, `"shopping"`, `"resort"`), so online generation matches 0 preferred categories. | [Suggested Wizard](https://edselrenz.github.io/Itinerary-App/#/suggested-wizard) uses canonical keys `['nature', 'food', 'culture', 'shopping', 'resort']` with `['food', 'culture', 'resort']` pre-selected (`suggested-wizard.page.ts:113–121`). |
| **`SUG-02`** | Double `"Day 1: Day 1: ..."` Heading | `desktop_client/models/itinerary.py:182–185` | `ItineraryDay.display_title` prepends `f"Day {self.day_number}: "` even when `self.title` already begins with `"Day 1: ..."`, rendering `"Day 1: Day 1: Cabanatuan City"`. | Displays `"Day 1 - Cabanatuan City"` (`suggested-wizard.page.html:319`). |
| **`SUG-03`** | Pacing `"packed"` vs `"fast"` & Unrated OSM Scoring | `desktop_client/services/itinerary_service.py:105, 152–285` | `settings.py:141` defines key `"packed"`, but `itinerary_service.py:105` checks `pacing == "fast"`, so `"Packed"` only schedules 3 stops instead of 4. Also, `score_place()` gives unrated raw OSM places `4.5 * 2.0 = 9.0` (outscoring 4.3-rated curated attractions!), fails to exclude utility categories (`bank_atm`, `fuel_station`, `hospital_clinic`, `pharmacy`, `convenience_store`, `transport_terminal`, `public_facility`), and does not cluster stops within a 25km radius of each day's anchor or run 2-Opt route ordering. | Curated attractions are prioritized, utility POIs are excluded from tourist slots, stops are clustered around the day anchor with 2-Opt ordering, and pacing rules are respected (`itinerary.service.ts:897–1220`). |
| **`SUG-04`** | Missing Bottom CTAs, Nearby Banner & Maps Button | `desktop_client/views/suggested_wizard_view.py:480–860` | Result view lacks the bottom `"Nearby Places in {Municipality}"` banner card and bottom `"✓ Accept & Save Itinerary"` / `"✏️ Customize in Builder"` buttons; Nearby view cards lack the `"Maps"` button and operating hours pill, and `_inject_nearby_to_day()` hardcodes `"01:30 PM"` instead of calculating sequential time. | Includes bottom Nearby banner, bottom Save/Customize CTAs, and Nearby cards with operating hours, `Maps` link, and `+ Add to Day X` (`suggested-wizard.page.html:384–486`). |
| **`SUG-05`** | Top Back Button Discards Preview | `desktop_client/main.py:208` & `views/suggested_wizard_view.py` | Clicking the top-left `← Back` in `WorkflowHeader` while in `view_mode == "itinerary"` or `"nearby"` jumps straight to `/home` instead of stepping back (`nearby` → `itinerary` → `form`). | Header Back button steps back from `nearby` → `itinerary` → `form` (`suggested-wizard.page.ts:695–708`). |
| **`CUS-01`** | Step 2 Search Not Live & Loses Focus | `desktop_client/views/custom_builder_view.py:464–472, 1260–1306` | `search_field` only binds `on_submit` (no live `on_change` filtering while typing and no Clear `✕` button), only queries 60 places instead of filtering the 2,673-POI catalog in-memory, and calls `_build_content()` on every search, destroying input focus. | [Custom Builder](https://edselrenz.github.io/Itinerary-App/#/custom-builder) filters places live on every keystroke with a Clear `✕` button and 0ms in-memory filtering (`custom-builder.page.ts:974–1080`). |
| **`CUS-02`** | Step 2 Missing Category Groups & `Details` Add Callback | `desktop_client/views/custom_builder_view.py:474–497, 570` | Step 2 only shows 5 raw categories (omitting 11 of 16 canonical categories including `tourist_attraction`, `cafe`, `hotel_accommodation`, `church_religious`) instead of the Web App's grouped pills (`All`, `✨ Recommended for You`, `Tourist Spots`, `Food`, `Resorts & Stays`, `Culture & Heritage`, `Shopping`, `Transit & Essentials`, `Other`). Also, clicking `Details` (`line 570`) calls `show_place_detail_dialog(self.page, place)` without `on_add_to_day`, so `+ Add to Trip` in the modal fails to add to the active day. | Displays all grouped category pills covering all 16 canonical categories and wires `addToDay` inside the Place Detail sheet (`custom-builder.page.ts:147–163, 1081–1130, 1372–1377`). |
| **`CUS-03`** | Step 2 Add Stop Uses Fixed 30m Buffer & Fails on Ranges | `desktop_client/views/custom_builder_view.py:909, 927–936` | `_calc_next_time()` uses a fixed 30-min buffer instead of dynamic Haversine transit time (`15–120` mins) and fails with `ValueError` (falling back to `"11:00 AM"`) whenever the previous stop's `planned_time` is a range (`"09:30 AM - 11:30 AM"`) or ISO time (`"09:00:00"`). | `calculateNextStopTime()` parses any time format and adds dynamic Haversine driving buffer (`15–120` mins) (`custom-builder.page.ts:1295–1346`). |
| **`CUS-04`** | Step 3 Timeline Missing Budget Input, Reorder Auto-Schedule & Bounds Flags | `desktop_client/views/custom_builder_view.py:626–776, 938–948` | Settings card in Step 3 omits the editable `Daily Budget (₱)` input; Day tabs omit the municipality name; `StopCard` is not passed `is_first`/`is_last` or `on_click`; and `_move_stop()` swaps items without calling `_auto_schedule_active_day()`, leaving stop times out of chronological order. | Settings card includes `Daily Budget (₱)`, Day tabs show `Day X • {Municipality}`, first/last reorder arrows are disabled, and moving a stop auto-recalculates times (`custom-builder.page.html:369–540`, `custom-builder.page.ts:816–842`). |
| **`CUS-05`** | Missing `itinerary_service` in `main.py` & Back Navigation | `desktop_client/main.py:225, 241` | `main.py:241` references undefined `itinerary_service` (`NameError`), and `workflow_header.on_back` jumps to `/home` instead of stepping back from `timeline`/`browse` → `form`. | Back button steps back to `form` during creation, and `/trips/:id` resolves cleanly from service or storage. |

---

## Phase 1: Fix `SlippyMapCanvas` Interactive Gestures, Route Polylines & Thread-Safe Tile Loading (`MAP-02`, `MAP-03`, `MAP-06`, `MAP-07`)

### 1.1 Add Missing `import httpx` in `desktop_client/services/place_service.py`
In `desktop_client/services/place_service.py` (top of file, around line 6):
```python
import logging
from typing import Any, Optional
import uuid
import httpx
```

### 1.2 Refactor `desktop_client/components/slippy_map_canvas.py`
Update `desktop_client/components/slippy_map_canvas.py` so that:
1. **`_resolve_tile_source()`** checks `settings.assets_dir / "tiles" / f"{zoom}_{x}_{y}.png"` and `settings.storage_dir / "tile_cache" / f"{zoom}_{x}_{y}.png"` directly (1 syscall each) and never calls `self.redraw()` across the whole map from worker threads.
2. **`gesture_layer`** has a hit-testable `#01000000` surface, supports **mouse scroll-wheel zoom (`on_scroll`)** and **double-click zoom (`on_double_tap`)**, and is layered **below `self._marker_stack`** so cluster pins and place markers receive `on_click` events without gesture arena contention.
3. **`__init__()`** automatically invokes `self.set_route(self._route_stops, polyline_points=route_polyline_points, active_stop_index=active_stop_index, auto_fit=True)` whenever `route_stops` is provided on initialization, ensuring road polylines and bounding-box zoom work on every route map (`PlacesView`, `ItineraryRouteMap`, `SuggestedWizardView`, `CustomBuilderView`, `TripDetailView`).
4. **`get_viewport_bounds()`** returns `(min_lat, max_lat, min_lng, max_lng)` for live OSM viewport discovery.

Replace `desktop_client/components/slippy_map_canvas.py` with:
```python
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

        if self._route_stops:
            self.set_route(
                self._route_stops,
                polyline_points=route_polyline_points,
                active_stop_index=active_stop_index,
                auto_fit=True,
            )
        else:
            self.redraw()

    def get_viewport_bounds(self) -> tuple[float, float, float, float]:
        """Returns (min_lat, max_lat, min_lng, max_lng) for the currently visible map viewport."""
        cx, cy = latlon_to_world_px(self.center_lat, self.center_lng, self.zoom)
        nw_lat, nw_lng = world_px_to_latlon(cx - self._map_w / 2.0, cy - self._map_h / 2.0, self.zoom)
        se_lat, se_lng = world_px_to_latlon(cx + self._map_w / 2.0, cy + self._map_h / 2.0, self.zoom)
        return (min(nw_lat, se_lat), max(nw_lat, se_lat), min(nw_lng, se_lng), max(nw_lng, se_lng))

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
```

---

## Phase 2: Fix Full-Bleed Map Tab (`PlacesView`) & App Shell (`main.py`) (`MAP-01`, `MAP-04`, `MAP-05`, `MAP-08`, `MAP-09`, `MAP-10`, `CUS-05`)

### 2.1 Update `desktop_client/main.py`
In `desktop_client/main.py`:
1. Import `get_itinerary_service`:
   ```python
   from desktop_client.services.itinerary_service import get_itinerary_service
   ```
   And inside `main(page: ft.Page)` (around line 63):
   ```python
   itinerary_service = get_itinerary_service()
   ```
   This fixes `NameError: name 'itinerary_service' is not defined` at line 241.
2. Configure window dimensions in `main(page: ft.Page)` (lines 66–71):
   ```python
   page.title = settings.app_title
   page.theme_mode = ft.ThemeMode.LIGHT
   page.padding = 0
   page.spacing = 0
   page.bgcolor = ThemeColors.BG_LIGHT
   try:
       page.window.width = settings.window_width
       page.window.height = settings.window_height
       page.window.min_width = settings.window_min_width
       page.window.min_height = settings.window_min_height
   except Exception:
       pass
   ```
3. Wire `workflow_header.on_back` in `main.py` (lines 208 & 225) to step back inside `SuggestedWizardView` (`nearby` → `itinerary` → `form`) and `CustomBuilderView` (`timeline`/`browse` → `form` when creating a new trip) before falling back to `navigate_to("/home")`:
   ```python
   def _handle_workflow_back():
       if content_area.content and hasattr(content_area.content, "handle_back"):
           if content_area.content.handle_back():
               return
       navigate_to("/home")
   ```
   Use `workflow_header.on_back = _handle_workflow_back` for both `/suggested` and `/builder`.
4. In `main.py:262–267`, only pass `active_trip=selected_trip` to `PlacesView` when the route query explicitly contains `itineraryId=` or `followRoute=true`:
   ```python
   elif base_route in ("/map", "/places"):
       has_route_param = ("itineraryId=" in route) or ("followRoute=true" in route)
       content_area.content = PlacesView(
           on_navigate=navigate_to,
           route_query=route,
           active_trip=selected_trip if has_route_param else None,
       )
   ```

### 2.2 Rewrite `desktop_client/views/places_view.py`
Update `desktop_client/views/places_view.py` to fix all 10 Map Tab defects (`MAP-01` through `MAP-10`):
- **Eliminate the full-screen pointer-blocking container in `_build_drawer_toggle_pill()` (`MAP-01`)**: Position the compact `"List View (N)"` pill directly at `bottom=18, left=530` (with no full-width `left=0, right=0, alignment=ft.Alignment(0, 1)` wrapper).
- **Never destroy `self.map_component` or `self._search_field` when typing or clicking filters (`MAP-05`)**: Update `self._clear_btn.visible`, `self._cat_row.controls`, `self._filter_badge`, `self._drawer_pill_label.value`, and `self._drawer_container` in-place while calling `self.map_component.set_places(self.filtered_places, auto_fit=...)` so typing in the search bar never loses focus and clicking category pills never resets map zoom/pan.
- **Only enter `is_follow_route_mode` when `itineraryId` or `followRoute=true` is in `self.route_query` (`MAP-04`)**, and implement `recenter_map(self)` so clicking the Map tab icon while already on `/map` resets to province discovery view.
- **Support multi-select categories (`self.selected_categories: set[str]`), active filter count badge (`Filters [N]`), and accurate price tier filtering (`MAP-09`)** matching `Project/src/app/tabs/map/map.page.ts:748–766 & 883–957`.
- **Separate floating action buttons (`right=12, bottom=185`) from `SlippyMapCanvas` zoom controls (`right=12, bottom=24`) (`MAP-08`)**, and pass current viewport bounds from `self.map_component.get_viewport_bounds()` into `fetch_live_osm_places()` (`MAP-07`).
- **Render the `"Destinations in View"` drawer as a vertical scrollable list with an empty-state `"Reset All Filters"` button (`MAP-10`)** matching `map.page.html:240–315`.

---

## Phase 3: Fix Suggested Itinerary Wizard & Offline Clustering Engine (`SUG-01` through `SUG-05`)

### 3.1 Fix `ItineraryDay.display_title` in `desktop_client/models/itinerary.py` (`SUG-02`)
In `desktop_client/models/itinerary.py` (lines 181–186), prevent double `"Day 1: Day 1: ..."` prefixes:
```python
    @property
    def display_title(self) -> str:
        if self.title and self.title.strip():
            clean_t = self.title.strip()
            if clean_t.lower().startswith("day "):
                return clean_t
            return f"Day {self.day_number}: {clean_t}"
        return f"Day {self.day_number}"
```

### 3.2 Fix `generate_offline_suggested_itinerary()` in `desktop_client/services/itinerary_service.py` (`SUG-01`, `SUG-03`)
In `desktop_client/services/itinerary_service.py`:
1. Support both `"packed"` and `"fast"` pacing keys (line 105):
   ```python
   target_stops = 2 if pacing == "relaxed" else (4 if pacing in ("fast", "packed") else 3)
   ```
2. Exclude non-tourist utility categories (`{"hospital_clinic", "pharmacy", "bank_atm", "fuel_station", "convenience_store", "transport_terminal", "public_facility"}`) from the candidate tourist pool unless no other places exist.
3. Fix `score_place()` (lines 152–179) so unrated raw OSM places do NOT receive a fake `4.5 * 2.0 = 9.0` rating bonus that outscores curated destinations:
   - Give curated/featured places (`p.get("is_featured") or str(p.get("id", "")).startswith("dest-")`) a `+20.0` curated quality boost.
   - Only add `float(p["rating"]) * 2.0` when `p.get("rating") is not None`.
4. Cluster each day's stops geographically around the day's first stop (within 25 km radius receive up to `+25.0` proximity score) and order non-lodging stops by nearest-neighbor / 2-Opt so stops on the same day never jump back and forth across the province.

### 3.3 Update `desktop_client/views/suggested_wizard_view.py` (`SUG-01`, `SUG-04`, `SUG-05`)
In `desktop_client/views/suggested_wizard_view.py`:
1. **Use canonical preference keys (`"nature"`, `"food"`, `"culture"`, `"shopping"`, `"resort"`) matching Web (`suggested-wizard.page.ts:113–121`) and Backend (`itinerary_generator.py:26–38`)**:
   ```python
   PREFERENCE_OPTIONS = [
       ("nature", "Nature & Parks", ft.Icons.LANDSCAPE),
       ("food", "Food Trip", ft.Icons.RESTAURANT),
       ("culture", "Culture & History", ft.Icons.MUSEUM),
       ("shopping", "Shopping", ft.Icons.SHOPPING_BAG),
       ("resort", "Resort", ft.Icons.POOL),
   ]
   ```
   Initialize `self.selected_preferences: set[str] = {"food", "culture", "resort"}` matching `suggested-wizard.page.ts:121`.
2. **Implement `handle_back(self) -> bool` for `WorkflowHeader` (`SUG-05`)**:
   ```python
   def handle_back(self) -> bool:
       if self.view_mode == "nearby":
           self._return_to_itinerary()
           return True
       if self.view_mode == "itinerary" and self.generated_itinerary:
           self.view_mode = "form"
           self._build_content()
           self._safe_update()
           return True
       return False
   ```
3. **Add Bottom `"Nearby Places in {Municipality}"` Banner & Bottom `"✓ Accept & Save Itinerary"` / `"✏️ Customize in Builder"` Action Buttons in `_build_result_view()` (`SUG-04`)** matching `suggested-wizard.page.html:384–413`, and wire `on_stop_click` on `ItineraryRouteMap` so clicking a route pin opens `show_place_detail_dialog`.
4. **Enhance Nearby Places View (`_build_nearby_view()` & `_inject_nearby_to_day()`) (`SUG-04`)**:
   - Display numbering (`1. {p.name}`), operating hours pill (`p.opening_hours or "Open Daily"`), a **`Maps`** button (`url=p.directions_url or f"https://www.google.com/maps/dir/?api=1&destination={p.latitude},{p.longitude}"`), and **`+ Add to Day {day_num}`**.
   - In `_inject_nearby_to_day()`, compute sequential `planned_time` after the last stop on `active_day` (instead of hardcoding `"01:30 PM"`) and update `travel_distance_meters` / `travel_duration_seconds`.

---

## Phase 4: Fix Custom Itinerary Builder (`CustomBuilderView`) & `TripDetailView` (`CUS-01` through `CUS-05`)

### 4.1 Update `desktop_client/views/custom_builder_view.py`
In `desktop_client/views/custom_builder_view.py`:
1. **Canonical Preference Keys & `handle_back()` (`CUS-02`, `CUS-05`)**:
   - Support canonical preference keys (`"nature"`, `"food"`, `"culture"`, `"shopping"`, `"resort"`) alongside human-readable labels so handoff from `SuggestedWizardView` (`[Customize in Builder]`) preserves all selected preferences.
   - Implement `handle_back(self) -> bool`:
     ```python
     def handle_back(self) -> bool:
         if self.active_view in ("browse", "timeline") and not self.existing_itinerary:
             self.active_view = "form"
             self._build_content()
             self._safe_update()
             return True
         return False
     ```
2. **Live In-Memory Search & Grouped Category Pills in Step 2 (`browse`) (`CUS-01`, `CUS-02`)**:
   - In `_build_browse_view()`, bind `on_change=lambda e: self._on_browse_search_live(e.control.value)` on `search_field` AND add a Clear (`✕`) `ft.IconButton(visible=bool(self.browse_search), on_click=self._clear_browse_search)` without recreating `search_field` on every keystroke (update only `self._browse_results_col.controls` in-place so typing never loses focus!).
   - Use the exact Web App category groups (`custom-builder.page.ts:147–163 & 1081–1130`) so all 16 canonical categories are reachable:
     - `("all", "All")`
     - `("recommended", "✨ Recommended for You")` (when `self.preferences` is non-empty)
     - `("tourist_spots", "Tourist Spots")` -> `{"tourist_attraction", "nature_park", "attraction"}`
     - `("food", "Food")` -> `{"restaurant", "cafe", "fast_food", "bar"}`
     - `("resorts_stays", "Resorts & Stays")` -> `{"hotel_accommodation", "resort_swimming"}`
     - `("culture_heritage", "Culture & Heritage")` -> `{"church_religious", "museum_cultural"}`
     - `("shopping", "Shopping")` -> `{"shopping_market", "convenience_store"}`
     - `("transit_essentials", "Transit & Essentials")` -> `{"transport_terminal", "hospital_clinic", "pharmacy", "fuel_station", "bank_atm", "public_facility"}`
   - Filter across the full 2,673-POI catalog (`self.place_service.get_loaded_places()`) in memory for 0ms response and sort places matching `self.destination` to the top.
   - In `_build_browse_place_card()` (`line 570`), pass `on_add_to_day=lambda pl: self._toggle_place_in_active_day(pl)` to `show_place_detail_dialog(self.page, place, on_add_to_day=...)` (`CUS-02`).
3. **Dynamic Haversine Transit Buffer in `_calc_next_time()` (`CUS-03`)**:
   - Update `_calc_next_time(self, day: ItineraryDay, next_place: Optional[Place] = None) -> str` to parse any time string (`"09:30 AM - 11:30 AM"`, `"09:00:00"`, `"09:00 AM"`) and compute the Haversine driving buffer (`15–120` mins at `40 km/h + 10 min` staging buffer) between the last stop in `day.items` and `next_place`.
4. **Complete Step 3 (`timeline`) Controls & Automatic Reorder Scheduling (`CUS-04`)**:
   - Add an editable `Daily Budget (₱)` `ft.TextField` to `settings_card` (`custom_builder_view.py:656–686`).
   - Display the primary municipality name on Day Switcher capsules (`Day {day.day_number} • {muni}`) and the Active Day header (`Day {day.day_number} - {muni} — {day.travel_date} ({len(day.items)} stops)`).
   - Pass `is_first=(idx == 0)`, `is_last=(idx == len(active_day.items) - 1)`, and `on_click=lambda itm: show_place_detail_dialog(self.safe_page, itm.place, on_navigate=self.on_navigate) if (itm.place and self.safe_page) else None` to `StopCard` (`custom_builder_view.py:768–775`).
   - In `_move_stop()` (`custom_builder_view.py:938–948`), call `self._auto_schedule_active_day()` after swapping two stops so `planned_time` is automatically recalculated in chronological order matching `custom-builder.page.ts:825 & 839`.
   - In `_open_custom_venue_dialog()` (`custom_builder_view.py:1088`), check `if bool(lat_str) != bool(lng_str):` first and display `"Please provide both Latitude and Longitude coordinates, or leave both blank."` matching `custom-builder.page.ts:1425–1434`.

---

## Phase 5: Standardize Modal Dialog Helpers in `desktop_client/components/dialogs.py`

In `desktop_client/components/dialogs.py`, add a helper function `_present_dialog(page: ft.Page, dialog: ft.AlertDialog)` and `_dismiss_dialog(page: ft.Page, dialog: ft.AlertDialog)` that supports both `page.overlay` and `page.pop_dialog()` cleanly without leaving stale closed dialogs in `page.overlay`:
```python
def _present_dialog(page: ft.Page, dialog: ft.AlertDialog) -> None:
    if dialog not in page.overlay:
        page.overlay.append(dialog)
    dialog.open = True
    page.update()


def _dismiss_dialog(page: ft.Page, dialog: ft.AlertDialog) -> None:
    dialog.open = False
    if dialog in page.overlay:
        page.overlay.remove(dialog)
    page.update()
```

---

## Phase 6: Exhaustive Verification Test Matrix

Run the automated test suites and add regression tests in `desktop_client/tests/test_parity_services_and_components.py` covering all 20 post-Session 53 defects:

| Test ID | Target Defect | Verification Assertion |
| :--- | :--- | :--- |
| **`TC-73`** | `MAP-01` | Verify `PlacesView._build_drawer_toggle_pill()` does not use a full-width `left=0, right=0, alignment=...` wrapper that blocks map clicks. |
| **`TC-74`** | `MAP-02` | Verify `SlippyMapCanvas` layers `gesture_surface` below `_marker_stack` and binds `on_pan_update`, `on_scroll`, and `on_double_tap`. |
| **`TC-75`** | `MAP-03` | Instantiate `ItineraryRouteMap(day=day_with_2_stops)` and `PlacesView(route_query="/map?itineraryId=draft&day=1", active_trip=itin)` and assert `len(map_component._route_pts) >= 2` on initialization without manual `set_route()` call. |
| **`TC-76`** | `MAP-04` | Instantiate `PlacesView(route_query="/map", active_trip=itin)` and assert `is_follow_route_mode is False` and all 2,673 places are loaded on the discovery map. |
| **`TC-77`** | `MAP-05` | Call `places_view._on_search_change("Bongabon")` and `places_view._select_category("nature_park")` and assert `places_view.map_component` and `places_view._search_field` object identities (`id(...)`) are preserved (not destroyed/recreated). |
| **`TC-78`** | `MAP-06` & `MAP-07` | Verify `import httpx` is present in `desktop_client.services.place_service` and `SlippyMapCanvas.get_viewport_bounds()` returns valid `(min_lat, max_lat, min_lng, max_lng)`. |
| **`TC-79`** | `MAP-09` | Verify `PlacesView` supports multi-select categories (`selected_categories = {"nature_park", "restaurant"}`) and `selected_price_tier = "budget"` excludes unpriced (`estimated_cost_min=None, estimated_cost_max=None`) places. |
| **`TC-80`** | `SUG-01` & `SUG-02` | Verify `SuggestedWizardView` sends canonical preference keys (`"food"`, `"culture"`, `"resort"`, `"nature"`, `"shopping"`) and `ItineraryDay.display_title` never produces `"Day 1: Day 1: ..."`. |
| **`TC-81`** | `SUG-03` | Run `generate_offline_suggested_itinerary()` with `pacing="packed"` and assert 4 stops/day are generated, zero utility POIs (`bank_atm`, `fuel_station`, `pharmacy`) are chosen as tourist stops, and same-day stops are geographically clustered. |
| **`TC-82`** | `SUG-04` & `SUG-05` | Verify `SuggestedWizardView.handle_back()` steps from `"nearby"` → `"itinerary"` → `"form"`, and `_inject_nearby_to_day()` computes sequential `planned_time`. |
| **`TC-83`** | `CUS-01` & `CUS-02` | Verify `CustomBuilderView` Step 2 (`browse`) filters live via `_on_browse_search_live()` without recreating the search `TextField`, supports all grouped categories (`tourist_spots`, `food`, `resorts_stays`, `culture_heritage`, `shopping`, `transit_essentials`), and passes `on_add_to_day` to `show_place_detail_dialog`. |
| **`TC-84`** | `CUS-03` & `CUS-04` | Verify `CustomBuilderView._calc_next_time()` handles `"09:30 AM - 11:30 AM"` and computes Haversine transit buffers (`15–120` mins), and `_move_stop()` automatically recalculates chronological `planned_time` values. |
| **`TC-85`** | `CUS-05` | Verify `desktop_client.main` imports `get_itinerary_service` without `NameError` and `CustomBuilderView.handle_back()` steps back to `"form"` mode. |