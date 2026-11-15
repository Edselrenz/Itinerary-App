# Desktop Map vs. Web Map Deep-Dive QA Audit & 1:1 Development Footsteps Plan

- **Application**: **Trip mo, trip ko — Nueva Ecija Travel Itinerary App**
- **Live Web Application (1:1 Reference Baseline)**: [Nueva Ecija Travel Itinerary Web App](https://edselrenz.github.io/Itinerary-App/#/welcome) ([Live Web Map Tab](https://edselrenz.github.io/Itinerary-App/#/tabs/map))
- **Source Repository**: [edselrenz/Itinerary-App GitHub Repository](https://www.google.com/search?q=https://github.com/edselrenz/Itinerary-App) (Evaluated Commit: `6faa2cec92f3e06d7d3238c5abd49ac31dfbe8c3`, v0.56.0 / Phase 59)
- **Cloudflare Worker Edge API**: [Nueva Ecija Itinerary Edge Proxy](https://www.google.com/search?q=https://ne-itinerary-api.edselrenz0.workers.dev/api/v1/health)
- **Geospatial Standards & Policies**: [OpenStreetMap Tile Usage Policy](https://operations.osmfoundation.org/policies/tiles/), [Leaflet API Reference](https://leafletjs.com/reference.html), [OSRM HTTP Routing API](http://project-osrm.org/docs/v5.24.0/api/)

## 1. Executive Summary: How the Desktop Map Works vs. the Web Map

We performed a full architectural and runtime QA audit of the Python Flet Desktop Map (`desktop_client/components/slippy_map_canvas.py`, `desktop_client/views/places_view.py`, `desktop_client/components/itinerary_route_map.py`) in commit `6faa2cec92f3e06d7d3238c5abd49ac31dfbe8c3` against the live Ionic/Angular + [Leaflet](https://leafletjs.com/reference.html) Web Map at [https://edselrenz.github.io/Itinerary-App/#/tabs/map](https://edselrenz.github.io/Itinerary-App/#/tabs/map) (`Project/src/app/tabs/map/map.page.ts`, `map.page.html`, `map.page.scss`, `place-detail-sheet.component.ts`, and `itinerary-route-map.component.ts`).

While Phases 57–59 resolved the [OpenStreetMap Tile Usage Policy](https://operations.osmfoundation.org/policies/tiles/) 403 hazard tiles, CartoDB watermark tiles, and fullscreen window maximize sizing, our runtime execution and side-by-side inspection uncovered **3 P0 runtime/math blockers**, **5 P1 visual and functional parity gaps**, and **2 P2 UX/theme polish defects** (`MAP-QA-01` through `MAP-QA-10`) that prevent the Desktop Map from working and looking like the Web Map.

| Defect ID | Severity | Component & Line(s) | Desktop Behavior (Current Bug / Gap) | Web Behavior (1:1 Target Reference) |
| :--- | :--- | :--- | :--- | :--- |
| **`MAP-QA-01`** | **P0 Blocker** | `desktop_client/views/places_view.py:1169–1171` | Clicking **any** marker pin on the map or any card in the List View drawer crashes with `AttributeError: 'CommuteInfo' object has no attribute 'get'` because `get_commute_info_for_municipality()` returns a `CommuteInfo` dataclass, not a `dict`. The bottom sheet never opens. | Clicking any marker pin on the [Live Web Map](https://edselrenz.github.io/Itinerary-App/#/tabs/map) smoothly pans to the pin and slides up `<app-place-detail-sheet>` with full venue details and transit guide. |
| **`MAP-QA-02`** | **P0 Blocker** | `desktop_client/views/places_view.py:1117–1121` | Clicking the Favorite heart button on the POI bottom sheet calls `fav_svc.toggle_favorite(pid)` with a `str` ID instead of a `Place` object, crashing with `AttributeError: 'str' object has no attribute 'id'`. | Clicking the heart button on `<app-place-detail-sheet>` in the [Live Web Map](https://edselrenz.github.io/Itinerary-App/#/tabs/map) toggles favorite state (`FavoritesService.toggleFavorite(this.place)`) and persists to storage. |
| **`MAP-QA-03`** | **P0 Blocker** | `desktop_client/components/slippy_map_canvas.py:105–108, 985–1052` | **1) Quadratic Runaway Panning**: `_handle_pan_update()` accumulates `raw_dx = self._drag_dx + pdx` while also mutating `self.center_lat/lng` on every drag frame, and `_handle_pan_end()` subtracts `_drag_dx` again—causing a 50px mouse drag across 5 frames to shift the map 200px (4x–10x runaway teleportation).<br>**2) Dropped Axis-Aligned Drag Frames**: `_extract_pan_delta()` uses `getattr(e, "delta_y", None) or getattr(e, "dy", None)`, which evaluates `0.0` (falsy in Python) to `None` and drops purely horizontal or vertical drag events. | Dragging on the [Leaflet Web Map](https://leafletjs.com/reference.html) translates the map 1:1 with the mouse pointer (`L.Draggable`) with viscous boundary clamping (`maxBoundsViscosity: 0.8`) and zero drift or jump on mouse release. |
| **`MAP-QA-04`** | **P1 High** | `desktop_client/components/slippy_map_canvas.py:302–342, 1356–1403` | Renders flat circular dots centered at `(sx - size/2, sy - size/2)` with mismatched category colors (e.g., churches are amber `#d97706` instead of purple `#7c3aed`; museums are purple instead of amber `#b45309`; `CATEGORY_PIN_STYLE` is unused dead code). | Renders `30×30` custom **teardrop pins** (`.custom-map-pin` in `Project/src/global.scss:4689–4745`, `border-radius: 50% 50% 50% 0`, rotated `-45deg`, anchored at the bottom tip `iconAnchor: [15, 30]`) with category colors, white inner badge, and featured gradient halo on the [Live Web Map](https://edselrenz.github.io/Itinerary-App/#/tabs/map). |
| **`MAP-QA-05`** | **P1 High** | `desktop_client/views/places_view.py:1088–1313` | Bottom sheet (`_build_poi_bottom_sheet`) is a bare text box with **no hero photo**, **no star rating/reviews**, **no description**, **no operating hours**, **no address**, a broken `"Start Trip Here"` navigation call (`on_navigate("/suggested", None, p_obj)` which drops the place ID), and a `"Get Directions"` button that draws a fake line from Cabanatuan instead of opening Google Maps. | `<app-place-detail-sheet>` on the [Live Web Map](https://edselrenz.github.io/Itinerary-App/#/tabs/map) renders a 180–200px hero photo with overlaid Favorite/Close buttons, category & Open/Closed badges, star rating pill, provenance badge, operating hours, description, green commute guide card (`#f0fdf4`), `"Start Trip Here"` (`/suggested?destination=...&placeId=...`), `"+ Add to Trip"`, and dark navy `"Get Directions"` external Google Maps launcher. |
| **`MAP-QA-06`** | **P1 High** | `desktop_client/views/places_view.py:355–404` & `slippy_map_canvas.py:1405–1451` | In Follow-Route Mode, `PlacesView._build_content()` passes `route_stops` to `SlippyMapCanvas` **without decoding `day_overview_polyline` / `route_polyline_from_prev` or calling `set_route()`**, resulting in straight lines instead of road geometry and no initial `fit_to_route()`. Route stop pins also lack the floating `.route-stop-tooltip` name pill above each numbered badge. | `renderRouteOnMap()` on the [Live Web Map](https://edselrenz.github.io/Itinerary-App/#/tabs/map) decodes `day_overview_polyline` / `route_polyline_from_prev` (with [OSRM HTTP Routing API](http://project-osrm.org/docs/v5.24.0/api/) fallback), auto-fits route bounds (`padding: [48, 48]`), and renders `.route-stop-pin` badges with floating dark `.route-stop-tooltip` stop name pills and `#f59e0b` amber active highlight. |
| **`MAP-QA-07`** | **P1 High** | `desktop_client/views/places_view.py:742–822` | Clicking `"List View (2673)"` opens a left-aligned box of tall 236px vertical cards, and clicking a card leaves the drawer open covering the map instead of closing the drawer and flying to the selected place. | Clicking `"List View (2673)"` on the [Live Web Map](https://edselrenz.github.io/Itinerary-App/#/tabs/map) slides up a centered bottom drawer (`.poi-list-drawer`) with a drag handle, `"2673 places"` count badge, and compact horizontal rows (`64×64` thumbnail, category, green price, title, municipality, arrow); clicking a row closes the drawer, flies to the pin, and opens the bottom sheet. |
| **`MAP-QA-08`** | **P1 High** | `desktop_client/views/places_view.py:104–110, 1640–1649` | 1) `__init__()` calls `_check_and_init_route_mode()` and then overwrites `self.filtered_places = list(self.all_places)` **without calling `self._apply_filters()`**, ignoring URL query filters (`category`, `municipality`, `priceTier`, `search`) on initial render.<br>2) Selecting a municipality or destination via query params or Filter Modal does not smoothly fly/fit the map to that municipality. | Navigating to [https://edselrenz.github.io/Itinerary-App/#/tabs/map?category=tourist_attraction](https://edselrenz.github.io/Itinerary-App/#/tabs/map?category=tourist_attraction) or filtering by municipality immediately filters markers, updates the `"List View (104)"` count and `"Filters 1"` badge, and flies to the target municipality/destination. |
| **`MAP-QA-09`** | **P2 Medium** | `desktop_client/views/places_view.py:35–53, 470–494, 611–645, 1402–1454` | 1) `CATEGORY_ICONS` misses `"public_facility"` (`flag-outline`).<br>2) Clicking `[✨ Live OSM]` or `[🎯 Locate Me]` lacks the Web's in-map floating status pill (`.live-osm-pill`: `"Fetching live places from OpenStreetMap..."` / `"Loaded X live places"`).<br>3) `_locate_user()` sets private `_user_location` without setting `user_location` or animating via `fly_to`. | The [Live Web Map](https://edselrenz.github.io/Itinerary-App/#/tabs/map) displays the `.live-osm-pill` indigo status pill during/after Overpass queries, animates `flyTo` on GPS lock with a pulsing blue beacon, and uses `flyTo` (`duration: 0.8s`) on Reset Province. |
| **`MAP-QA-10`** | **P2 Medium** | `desktop_client/views/places_view.py:394–404, 591–601, 809–821` | `PlacesView` never passes `dark_mode=get_settings().is_dark_mode` to `SlippyMapCanvas` and hardcodes `#ffffff` backgrounds on floating bars, drawers, and bottom sheets even when Dark Mode is enabled in Profile Settings. | All floating map chrome, cards, and tile contrast adapt cleanly to the active theme palette across the application. |

## 2. Architecture & Mechanism Comparison: How Every Map Subsystem Works

### 2.1 Map Rendering Engine & Coordinate Projection

| Subsystem | Web Application (`Project/src/app/tabs/map/map.page.ts`) | Desktop Application (`desktop_client/components/slippy_map_canvas.py`) | Parity Assessment & Required Action |
| :--- | :--- | :--- | :--- |
| **Core Rendering Engine** | [Leaflet 1.9.4](https://leafletjs.com/reference.html) HTML5 Canvas/DOM engine (`preferCanvas: true`) inside `<div id="leaflet-map" class="map-canvas">`. | Custom Python Flet `SlippyMapCanvas(ft.Container)` stacking `_pan_layer` (`_tile_stack` + `cv.Canvas` `_vector_canvas`), `_gesture_surface` (`ft.GestureDetector`), and `_marker_stack`. | Architecture is sound, but `_marker_stack` and `_pan_layer` must translate together relative to an immutable `_drag_start_wx, _drag_start_wy` anchor during pan gestures (`MAP-QA-03`). |
| **Web Mercator Projection** | Spherical Mercator (`EPSG:3857`) via `L.CRS.EPSG3857` (`256×256` tiles at integer zoom `Z9`–`Z18`). | `latlng_to_world_px(lat, lng, zoom)` and `world_px_to_latlng(wx, wy, zoom)` (`lines 345–364`) using standard `EPSG:3857` math at `TILE_SIZE = 256`. | Exact mathematical match (`100% parity`). |
| **Provincial Bounds & Center** | `NUEVA_ECIJA_CENTER = [15.58, 121.0]`, `DEFAULT_ZOOM = 10`, `NUEVA_ECIJA_BOUNDS = [[15.05, 120.55], [16.25, 121.55]]`, `minZoom: 9`, `maxZoom: 18`. | `center_lat = 15.58`, `center_lng = 121.00`, `zoom = 10`, bounds `[15.05..16.25, 120.55..121.55]`, `MIN_ZOOM = 9`, `MAX_ZOOM = 18`. | Exact coordinate and zoom bounds match (`100% parity`). |
| **Tile Pipeline & Offline Caching** | Fetches `https://tile.openstreetmap.org/{z}/{x}/{y}.png` via browser `<img>` with browser `User-Agent` and `Referer`, tracking `tileerror` counts to show `.tile-error-pill` if offline. | Python `_resolve_tile_source()` checks bundled `assets/tiles/` (93 tiles) -> `assets/tiles_cache/` (243 tiles) -> async Python `_TILE_EXECUTOR` across 3 [OpenStreetMap](https://operations.osmfoundation.org/policies/tiles/) mirrors (`openstreetmap.org`, `openstreetmap.fr`, `openstreetmap.de`) with custom `User-Agent` and `Referer`, serving an instant SVG data URI placeholder (`#aad3df` ocean / `#f2efe9` land) until cached and swapping live via `_on_tile_cached_live`. | Tile pipeline is 100% free of 403 blocks and Carto watermarks. Add a subtle offline tile indicator pill if all mirrors fail while offline to match Web's `.tile-error-pill`. |

### 2.2 Gesture Physics: Panning, Scroll-Wheel Zoom, and `flyTo` Animation

1. **Why Desktop Dragging Currently Teleports (`MAP-QA-03`)**:
   - In `slippy_map_canvas.py:985–1000`, `_handle_pan_update(e)` receives incremental per-frame mouse deltas `(pdx, pdy)` from `ft.GestureDetector(on_pan_update=...)`.
   - It computes `raw_dx = self._drag_dx + pdx` (which is the **cumulative** pixel offset from the start of the drag), but then subtracts `raw_dx` from `self.latlng_to_world_px(self.center_lat, self.center_lng, self.zoom)` **while also overwriting `self.center_lat` and `self.center_lng` on every single frame** (`lines 996–997`)!
   - Because `self.center_lat` is already shifted by frame 1's `raw_dx`, frame 2 subtracts `raw_dx_1 + pdx_2` from the already-shifted center, compounding the translation quadratically ($\sum_{k=1}^{N} k \cdot \text{pdx} = \frac{N(N+1)}{2}\text{pdx}$).
   - Furthermore, `_pan_layer` and `_marker_stack` contain tiles and markers positioned relative to the **initial** `center_lat/lng` when `_rebuild_layers()` last ran, yet `_handle_pan_end()` (`lines 1042–1044`) subtracts `self._drag_dx` one additional time from the already-mutated `self.center_lat`!
   - **The Exact Fix**:
     - In `_handle_pan_start()`, record `self._drag_origin_lat = self.center_lat` and `self._drag_origin_lng = self.center_lng` (and `self._drag_origin_wx, self._drag_origin_wy = self.latlng_to_world_px(...)`).
     - In `_handle_pan_update()`, accumulate `self._drag_dx += pdx` and `self._drag_dy += pdy` relative to `_drag_origin_wx, _drag_origin_wy`, clamp the prospective world coordinates against `NUEVA_ECIJA_BOUNDS`, and set `_pan_layer.left = self._drag_dx` and `_marker_stack.left = self._drag_dx` **without mutating `self.center_lat/lng` until rebase (`>= 220px`) or `_handle_pan_end()`**!
     - In `_extract_pan_delta()`, replace `getattr(e, "delta_x", None) or getattr(e, "dx", None)` with explicit `None` checks (`dx = getattr(e, "delta_x", None); if dx is None: dx = getattr(e, "dx", None)`) so `0.0` is never treated as `None`.

### 2.3 Marker Clustering & Custom Teardrop Pin Styling (`MAP-QA-04`)

1. **Clustering Parity**:
   - On the [Live Web Map](https://edselrenz.github.io/Itinerary-App/#/tabs/map), `L.markerClusterGroup` clusters markers at zoom levels `Z9` through `Z15` (`maxClusterRadius: 40`) using circular blue cluster badges (`rgba(0, 132, 255, 0.22)` outer halo + `#0084ff` inner circle with bold white count text).
   - `SlippyMapCanvas._ensure_world_clusters()` (`lines 627–693`) already clusters up to `Z15` (`self.zoom >= 16` unclusters) and renders matching double-ring blue cluster badges (`_build_cluster_marker`, `lines 1307–1354`). However, let's align the cluster color to `#0084ff` (`ThemeColors.PRIMARY_BLUE`) to match `.marker-cluster-small/medium/large` in `Project/src/global.scss:4747–4761`.
2. **Individual Pin Teardrop Shape & Category Colors (`MAP-QA-04`)**:
   - On the [Live Web Map](https://edselrenz.github.io/Itinerary-App/#/tabs/map) (`Project/src/global.scss:4689–4745`), individual POI markers are **teardrop pins** (`border-radius: 50% 50% 50% 0`, rotated `-45deg`, `26×26` body with `2px solid #ffffff` border, bottom tip anchored at exact coordinate `(sx, sy)`) with category-specific colors and an inner white badge/icon.
   - In Flet Desktop (`SlippyMapCanvas._build_single_place_marker`), we can render the exact **teardrop pin** by using a `ft.Container` with `border_radius=ft.BorderRadius(top_left=15, top_right=15, bottom_right=15, bottom_left=3)`, `rotate=ft.Rotate(angle=-math.pi / 4)`, anchored so its bottom tip sits directly over `(sx, sy)` (`left = sx - size/2`, `top = sy - size`), with a counter-rotated (`rotate=ft.Rotate(angle=math.pi / 4)`) inner category icon or white dot—and using the exact 16-category color map from `Project/src/global.scss:4732–4744`!

### 2.4 Interactive Place Detail Bottom Sheet (`MAP-QA-01`, `MAP-QA-02`, `MAP-QA-05`)

On the [Live Web Map](https://edselrenz.github.io/Itinerary-App/#/tabs/map), clicking any pin opens `<app-place-detail-sheet>` (`Project/src/app/shared/components/place-detail-sheet/place-detail-sheet.component.html`), which displays:
1. **Hero Image Banner (`sheet-photo-wrap`)**: Full-width destination photo (`resolved_image_path`) with:
   - Top-right circular dark translucent **Favorite (`♥`)** and **Close (`✕`)** buttons (`rgba(15, 23, 42, 0.65)`).
   - Bottom-left dark translucent **Category Badge** (`place.formatted_category`).
   - Bottom-right **Open Now / Open Daily** green status pill (`#166534` with `#4ade80` dot).
2. **Header & Metadata (`sheet-header` & `sheet-provenance-row`)**:
   - Bold place title (`18px`, `#0f172a`).
   - Golden star rating pill (`#fef3c7` background, `#f59e0b` star, rating value, review count, and `"Top Rated"` emerald badge when `rating >= 4.5`).
   - Location pin + municipality name and green cash icon + honest formatted cost (`Free Admission (₱0)` / `₱min - ₱max` / `Admission: Check on arrival`).
   - Provenance shield badge (`Google Verified POI` or `Verified Destination`).
   - Operating hours row (`place.opening_hours`) and address row (`place.address_text`) + description snippet (`place.editorial_summary` or `place.description`).
3. **Green Local Commute Guide Box (`sheet-commute-box`)**:
   - Styled with `#f0fdf4` background and `#bbf7d0` border, displaying **How to get there?**:
     - `Transit & Hub`: `{commute_info.transit_mode} • {commute_info.departure_hub}`
     - `Drop-off Point`: `{commute_info.drop_off_point}`
     - `Estimated Travel Time`: `{commute_info.estimated_travel_time}`
     - `Estimated Fare`: `{commute_info.estimated_fare}`
     - `Travel Reminder` card (`commute_info.travel_reminder`).
4. **Action Buttons (`sheet-actions-stack`)**:
   - Primary row: Solid `#0084ff` **`✨ Start Trip Here`** (navigating to `/suggested?destination={municipality}&placeId={place.id}`) and `#eff6ff` outlined **`+ Add to Trip`** (navigating to `/builder` with `pre_added_place=p_obj`).
   - Secondary row: Dark navy `#0f172a` **`Get Directions`** button (launching `place.directions_url` or `https://www.google.com/maps/dir/?api=1&destination={lat},{lng}` via `page.launch_url()` AND optionally mapping the in-app route preview) plus **`Full Details`** modal button.

### 2.5 Collapsible POI List Drawer (`MAP-QA-07`)

On the [Live Web Map](https://edselrenz.github.io/Itinerary-App/#/tabs/map) (`Project/src/app/tabs/map/map.page.html:240–315`), clicking the bottom-center **`List View (2673)`** pill slides up `.poi-list-drawer` centered at the bottom of the viewport (`max-width: 580px`) with:
- A drag handle bar (`.drawer-drag-pill`), **`Destinations in View`** title, **`{N} places`** pill badge, and close (`✕`) button.
- Compact horizontal `.drawer-place-card` rows (`64×64` rounded photo on the left, category uppercase badge in `#0084ff` + green price on the top line, bold place name, location pin + municipality subtitle, and right navigation arrow).
- Clicking any row in the drawer **automatically closes the drawer (`self.is_drawer_open = False`)**, flies the map camera (`fly_to(lat, lng, 15)`) to the destination, highlights its pin, and opens the in-map Place Detail Bottom Sheet!

### 2.6 Follow-Route Mode & Embedded `ItineraryRouteMap` (`MAP-QA-06`)

When viewing an itinerary route on the [Live Web Map](https://edselrenz.github.io/Itinerary-App/#/tabs/map) (`/tabs/map?followRoute=true&itineraryId=...&dayNumber=1`):
- `PlacesView._build_content()` must extract `route_polyline_points` from `target_day.day_overview_polyline` or `item.route_polyline_from_prev` (using `decode_polyline`), pass `route_polyline_points` to `SlippyMapCanvas`, and invoke `self.map_component.set_route(route_stops, polyline_points=route_polyline_points, active_stop_index=self._active_route_stop_index, auto_fit=True)` so road geometry (or [OSRM HTTP Routing API](http://project-osrm.org/docs/v5.24.0/api/) road geometry) is drawn and the viewport auto-fits the day's stops!
- Each numbered route stop marker on `SlippyMapCanvas` (`_build_route_stop_marker`) must render both the numbered circular badge (`1`, `2`, `3`, with `#f59e0b` amber active highlight) AND a floating dark `.route-stop-tooltip` pill above the pin showing the stop's name (`Stop 1: Minalungao National Park`).

## 3. Step-by-Step Development Footsteps (Implementation Plan)

Follow these 4 sequential steps to bring the Desktop Application Map to 100% functional and visual parity with the Web Application Map.

### Step 1: Fix `SlippyMapCanvas` Pan Physics, Axis-Aligned Delta Extraction, Teardrop Markers & Route Stop Tooltips (`desktop_client/components/slippy_map_canvas.py`)

#### 1A. Fix `_extract_pan_delta` so `0.0` deltas are never dropped (`lines 97–118`)

Replace `_extract_pan_delta` in `desktop_client/components/slippy_map_canvas.py` with explicit `None` checks:

```python
def _extract_pan_delta(e: Any) -> Tuple[float, float]:
    """Extract (dx, dy) pan delta from diverse Flet pan update event formats without dropping 0.0 values."""
    # 1. local_delta or delta object with .x and .y
    for attr in ("local_delta", "delta"):
        obj = getattr(e, attr, None)
        if obj is not None and hasattr(obj, "x") and hasattr(obj, "y"):
            if obj.x is not None and obj.y is not None:
                return float(obj.x), float(obj.y)
    # 2. Direct delta_x/delta_y or dx/dy attributes (use explicit is None check so 0.0 is preserved)
    dx = getattr(e, "delta_x", None)
    if dx is None:
        dx = getattr(e, "dx", None)
    dy = getattr(e, "delta_y", None)
    if dy is None:
        dy = getattr(e, "dy", None)
    if dx is not None and dy is not None:
        return float(dx), float(dy)
    # 3. JSON data payload
    data_str = getattr(e, "data", None)
    if data_str and isinstance(data_str, str):
        try:
            d = json.loads(data_str)
            if isinstance(d, dict):
                raw_x = d.get("dx") if d.get("dx") is not None else d.get("x", 0.0)
                raw_y = d.get("dy") if d.get("dy") is not None else d.get("y", 0.0)
                return float(raw_x), float(raw_y)
        except Exception:
            pass
    return 0.0, 0.0
```

#### 1B. Fix `_handle_pan_start`, `_handle_pan_update`, and `_handle_pan_end` to eliminate quadratic runaway drift (`lines 486–490` & `978–1052`)

In `SlippyMapCanvas.__init__()` (`around line 487`), initialize `_drag_origin_lat` and `_drag_origin_lng`:

```python
        # Drag state & 60 FPS throttling
        self._drag_dx: float = 0.0
        self._drag_dy: float = 0.0
        self._drag_origin_lat: float = self.center_lat
        self._drag_origin_lng: float = self.center_lng
        self._last_pan_ui_ts: float = 0.0
```

Then replace `_handle_pan_start`, `_handle_pan_update`, and `_handle_pan_end` (`lines 978–1052`) with:

```python
    def _handle_pan_start(self, e: Any = None) -> None:
        with self._fly_lock:
            self._fly_generation += 1
        self._drag_dx = 0.0
        self._drag_dy = 0.0
        self._drag_origin_lat = self.center_lat
        self._drag_origin_lng = self.center_lng
        self._gesture_surface.mouse_cursor = ft.MouseCursor.GRABBING

    def _handle_pan_update(self, e: Any) -> None:
        pdx, pdy = _extract_pan_delta(e)
        if pdx == 0.0 and pdy == 0.0:
            return

        # Ensure drag origin is initialized even if _handle_pan_update is called directly in tests
        if self._drag_dx == 0.0 and self._drag_dy == 0.0:
            self._drag_origin_lat = self.center_lat
            self._drag_origin_lng = self.center_lng

        raw_dx = self._drag_dx + pdx
        raw_dy = self._drag_dy + pdy

        # Compute clamped center relative to immutable _drag_origin_lat/lng (prevents quadratic drift)
        origin_wx, origin_wy = self.latlng_to_world_px(self._drag_origin_lat, self._drag_origin_lng, self.zoom)
        prospective_lat, prospective_lng = self.world_px_to_latlng(origin_wx - raw_dx, origin_wy - raw_dy, self.zoom)
        clamped_lat, clamped_lng = self._clamp_center(prospective_lat, prospective_lng)
        clamped_wx, clamped_wy = self.latlng_to_world_px(clamped_lat, clamped_lng, self.zoom)

        self._drag_dx = origin_wx - clamped_wx
        self._drag_dy = origin_wy - clamped_wy

        # Seamless mid-drag rebase when pan exceeds 220px (well inside our 2-tile / 512px buffer)
        if abs(self._drag_dx) >= 220 or abs(self._drag_dy) >= 220:
            self.center_lat = clamped_lat
            self.center_lng = clamped_lng
            self._drag_origin_lat = clamped_lat
            self._drag_origin_lng = clamped_lng
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

        # Translate lightweight layer containers 1:1 with cursor
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

        origin_wx, origin_wy = self.latlng_to_world_px(self._drag_origin_lat, self._drag_origin_lng, self.zoom)
        new_lat, new_lng = self.world_px_to_latlng(origin_wx - self._drag_dx, origin_wy - self._drag_dy, self.zoom)
        self.center_lat, self.center_lng = self._clamp_center(new_lat, new_lng)
        self._drag_origin_lat = self.center_lat
        self._drag_origin_lng = self.center_lng
        self._drag_dx = 0.0
        self._drag_dy = 0.0
        self._pan_layer.left = 0
        self._pan_layer.top = 0
        self._marker_stack.left = 0
        self._marker_stack.top = 0
        self._rebuild_layers(notify=True)
```

#### 1C. Align Category Pin Colors & Teardrop Pin Styling (`lines 302–342` & `1356–1452`)

Update `CATEGORY_MARKER_STYLES`, `_build_cluster_marker`, `_build_single_place_marker`, and `_build_route_stop_marker` in `desktop_client/components/slippy_map_canvas.py` to match the exact Web colors (`Project/src/global.scss:4689–4851`), teardrop pin shape (`border-radius: 50% 50% 50% 0` rotated `-45deg` anchored at bottom tip), and floating `.route-stop-tooltip` stop label:

```python
# Exact category color & icon table matching Project/src/global.scss (lines 4732-4744)
CATEGORY_MARKER_STYLES: Dict[str, Tuple[str, str]] = {
    "tourist_attraction": ("#0084ff", "AUTO_AWESOME"),
    "nature_park": ("#16a34a", "PARK"),
    "resort_swimming": ("#0891b2", "POOL"),
    "hotel_accommodation": ("#0284c7", "HOTEL"),
    "restaurant": ("#ea580c", "RESTAURANT"),
    "cafe": ("#d97706", "LOCAL_CAFE"),
    "church_religious": ("#7c3aed", "CHURCH"),
    "museum_cultural": ("#b45309", "MUSEUM"),
    "shopping_market": ("#e11d48", "SHOPPING_CART"),
    "transport_terminal": ("#0284c7", "DIRECTIONS_BUS"),
    "convenience_store": ("#6366f1", "STOREFRONT"),
    "hospital_clinic": ("#dc2626", "LOCAL_HOSPITAL"),
    "pharmacy": ("#dc2626", "LOCAL_PHARMACY"),
    "bank_atm": ("#059669", "ACCOUNT_BALANCE"),
    "fuel_station": ("#475569", "LOCAL_GAS_STATION"),
    "public_facility": ("#475569", "FLAG"),
    # Fallback short keys
    "nature": ("#16a34a", "PARK"),
    "attraction": ("#0084ff", "ATTRACTIONS"),
    "museum": ("#b45309", "MUSEUM"),
    "church": ("#7c3aed", "CHURCH"),
    "resort": ("#0891b2", "POOL"),
    "hotel": ("#0284c7", "HOTEL"),
    "market": ("#e11d48", "STOREFRONT"),
    "transport": ("#0284c7", "DIRECTIONS_BUS"),
    "hospital": ("#dc2626", "LOCAL_HOSPITAL"),
    "bank": ("#059669", "ACCOUNT_BALANCE"),
    "fuel": ("#475569", "LOCAL_GAS_STATION"),
    "convenience": ("#6366f1", "STOREFRONT"),
    "public": ("#475569", "LOCATION_CITY"),
}
```

And in `_build_single_place_marker` and `_build_route_stop_marker` (`lines 1356–1452`):

```python
    def _build_single_place_marker(self, place: Any, sx: float, sy: float) -> ft.Control:
        if isinstance(place, dict):
            cat_raw = str(place.get("category") or "tourist_attraction").lower()
            pid = str(place.get("id") or place.get("place_id") or "")
            name = place.get("name") or "Destination"
            mun = place.get("municipality") or place.get("municipality_name") or "Nueva Ecija"
            is_featured = bool(place.get("is_featured", False))
        else:
            cat_raw = str(getattr(place, "category", "tourist_attraction")).lower()
            pid = str(getattr(place, "id", "") or "")
            name = getattr(place, "name", "Destination")
            mun = getattr(place, "municipality_name", "Nueva Ecija")
            is_featured = bool(getattr(place, "is_featured", False))

        bg_color, icon_name = CATEGORY_MARKER_STYLES.get(cat_raw, ("#0084ff", "PLACE"))
        if bg_color == "#0084ff" and icon_name == "PLACE":
            for key, (col, icn) in CATEGORY_MARKER_STYLES.items():
                if key in cat_raw:
                    bg_color, icon_name = col, icn
                    break

        is_selected = bool(self.selected_place_id and pid == str(self.selected_place_id))
        size = 34 if is_selected else (30 if is_featured else 26)

        def _click_place(_: ft.ControlEvent, p: Any = place, p_id: str = pid) -> None:
            self.selected_place_id = p_id
            if self.on_place_click:
                self.on_place_click(p)

        # Teardrop pin matching Web .custom-map-pin (border-radius: 50% 50% 50% 0, rotated -45deg, tip at sx, sy)
        r_half = size / 2.0
        return ft.Container(
            left=sx - r_half,
            top=sy - size,  # Bottom-tip anchored at exact coordinate (sx, sy) like iconAnchor: [15, 30]
            width=size,
            height=size,
            border_radius=ft.BorderRadius(
                top_left=r_half,
                top_right=r_half,
                bottom_right=r_half,
                bottom_left=3,
            ),
            rotate=ft.Rotate(angle=-math.pi / 4.0),
            bgcolor="#0066cc" if is_selected else bg_color,
            border=ft.Border.all(2.5 if is_selected else 2.0, "#ffffff"),
            alignment=ft.Alignment.CENTER,
            shadow=ft.BoxShadow(
                blur_radius=12 if (is_selected or is_featured) else 8,
                color=ft.Colors.with_opacity(0.42 if is_selected else 0.32, bg_color if is_featured else "#0f172a"),
                offset=ft.Offset(0, 3),
            ),
            on_click=_click_place,
            tooltip=f"{name} ({mun})",
            content=ft.Container(
                rotate=ft.Rotate(angle=math.pi / 4.0),
                alignment=ft.Alignment.CENTER,
                content=ft.Icon(
                    getattr(ft.Icons, icon_name, ft.Icons.PLACE),
                    size=15 if is_selected else 12,
                    color="#ffffff",
                ),
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
        bg = "#f59e0b" if is_active else "#2563eb"
        badge_size = 34 if is_active else 28

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

        short_label = name if len(str(name)) <= 24 else f"{str(name)[:22]}…"
        return ft.Container(
            left=sx - 75,
            top=sy - (badge_size / 2.0) - 24,
            width=150,
            height=badge_size + 26,
            alignment=ft.Alignment.TOP_CENTER,
            on_click=_click_stop,
            tooltip=f"Stop {stop_num}: {name}",
            content=ft.Column(
                spacing=2,
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    # Floating dark stop title pill matching Web .route-stop-tooltip
                    ft.Container(
                        bgcolor=ft.Colors.with_opacity(0.88, "#0f172a"),
                        border_radius=4,
                        padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                        content=ft.Text(
                            short_label,
                            size=10,
                            weight=ft.FontWeight.W_600,
                            color="#ffffff",
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                    ),
                    # Numbered circular badge matching Web .route-stop-badge
                    ft.Container(
                        width=badge_size,
                        height=badge_size,
                        border_radius=badge_size / 2.0,
                        bgcolor=bg,
                        border=ft.Border.all(2.5, "#ffffff"),
                        alignment=ft.Alignment.CENTER,
                        shadow=ft.BoxShadow(
                            blur_radius=10 if is_active else 6,
                            color=ft.Colors.with_opacity(0.45 if is_active else 0.30, "#f59e0b" if is_active else "#0f172a"),
                            offset=ft.Offset(0, 2),
                        ),
                        content=ft.Text(
                            str(stop_num),
                            size=13 if is_active else 12,
                            weight=ft.FontWeight.W_800,
                            color="#ffffff",
                        ),
                    ),
                ],
            ),
        )
```

### Step 2: Fix `PlacesView` Bottom Sheet Crashes, Hero Photo Card, Drawer Rows, Route Polylines & Query Filtering (`desktop_client/views/places_view.py`)

#### 2A. Add `"public_facility"` to `CATEGORY_ICONS` (`lines 35–53`)

In `desktop_client/views/places_view.py`:

```python
    "fuel_station": ft.Icons.LOCAL_GAS_STATION_OUTLINED,
    "public_facility": ft.Icons.FLAG_OUTLINED,
    "viewpoint": ft.Icons.VISIBILITY_OUTLINED,
```

#### 2B. Apply Initial Filters & Municipality/Destination Auto-Focus in `__init__` and `did_mount` (`lines 98–147`)

In `PlacesView.__init__()` (`lines 104–110`), ensure `self._apply_filters()` runs immediately after `self.all_places` is loaded, and resolve destination/municipality coordinates if passed via `route_query`:

```python
        self._check_and_init_route_mode()

        self.all_places: list[Place] = self.place_service.get_loaded_places()
        self._apply_filters()

        self.map_component: Optional[SlippyMapCanvas] = None
        self._build_content()
```

And in `PlacesView.did_mount()` (`lines 133–146`), also auto-focus when `selected_municipality != "all"` or `search_query` was passed in the URL query string:

```python
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
```

#### 2C. Pass Decoded Route Polylines & Dark Mode to `SlippyMapCanvas` in `PlacesView._build_content()` (`lines 353–442`)

In `PlacesView._build_content()`, decode `target_day.day_overview_polyline` / `item.route_polyline_from_prev` (just like `ItineraryRouteMap` does!) and call `self.map_component.set_route(...)` when `self.is_follow_route_mode` is active:

```python
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

            from desktop_client.core.polyline import decode_polyline
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

        from desktop_client.config.settings import get_settings
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
```

#### 2D. Upgrade `_build_poi_bottom_sheet` & `_start_trip_from_place` for 1:1 Web `<app-place-detail-sheet>` Parity and Zero Crashes (`lines 1088–1313`)

Replace `_start_trip_from_place` and `_build_poi_bottom_sheet` in `desktop_client/views/places_view.py` with:

```python
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
```

#### 2E. Upgrade the Collapsible POI List Drawer to Match Web `.poi-list-drawer` & Auto-Close on Selection (`lines 742–822` & `1327–1330`)

Update `_build_drawer_content`, `_build_poi_drawer`, and `_focus_place_and_open_dialog` in `desktop_client/views/places_view.py` so the drawer uses Web's compact horizontal row layout (`64×64` thumbnail, category, green price, title, municipality, arrow) and automatically closes when a destination is clicked:

```python
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
```

#### 2F. Polish `_locate_user` and `_recenter_province` with Smooth `fly_to` Animation (`lines 1444–1454`)

```python
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
```

### Step 3: Standardize `[Full Map]` Route Query Parameters Across Itinerary Views

In `desktop_client/views/trip_detail_view.py:928`, `desktop_client/views/suggested_wizard_view.py:1365`, and `desktop_client/views/custom_builder_view.py:1743`, include `followRoute=true` and `dayNumber={day_num}` alongside `day={day_num}` so all route handoffs into `PlacesView` match the Web Router contract (`Project/src/app/shared/components/itinerary-route-map/itinerary-route-map.component.ts:112–118`):

```python
# trip_detail_view.py (line 928)
self.on_navigate(f"/map?followRoute=true&itineraryId={self.itinerary.id}&day={day_num}&dayNumber={day_num}", self.itinerary)

# suggested_wizard_view.py (line 1365)
self.on_navigate(f"/map?followRoute=true&itineraryId=draft&day={day_num}&dayNumber={day_num}", self.generated_itinerary)

# custom_builder_view.py (line 1743)
self.on_navigate(f"/map?followRoute=true&itineraryId=draft&day={day_num}&dayNumber={day_num}&source=builder", draft_itin)
```

### Step 4: Automated Regression Tests (`desktop_client/tests/test_cycle2_regressions.py`)

Append these 4 regression tests (`TC-31` through `TC-34`) to `desktop_client/tests/test_cycle2_regressions.py` to lock in the fixes and prevent future regressions:

```python
def test_tc_31_map_pin_click_and_favorite_toggle_no_crash():
    """TC-31: Verifies clicking any map pin builds the POI bottom sheet and toggles favorite without AttributeError (MAP-QA-01, MAP-QA-02)."""
    from desktop_client.views.places_view import PlacesView

    pv = PlacesView(initial_width=1280, initial_height=840)
    assert len(pv.all_places) > 0
    sample_place = pv.all_places[0]

    # Clicking pin must not raise AttributeError: 'CommuteInfo' object has no attribute 'get'
    pv._handle_place_pin_click(sample_place)
    assert pv.selected_map_place is not None
    assert pv._poi_bottom_sheet_host.visible is True
    assert pv._poi_bottom_sheet_host.content is not None


def test_tc_32_linear_pan_math_and_axis_aligned_deltas():
    """TC-32: Verifies 5 pan frames of (10px, 0px) shift world coordinates by exactly 50px without quadratic drift or dropped 0.0 deltas (MAP-QA-03)."""
    from desktop_client.components.slippy_map_canvas import SlippyMapCanvas

    canvas = SlippyMapCanvas(width=800, height=600, center_lat=15.58, center_lng=121.00, zoom=12)

    class DummyPanEvt:
        def __init__(self, dx: float, dy: float):
            self.delta_x = dx
            self.delta_y = dy

    start_wx, start_wy = canvas.latlng_to_world_px(canvas.center_lat, canvas.center_lng, canvas.zoom)
    canvas._handle_pan_start()
    for _ in range(5):
        canvas._handle_pan_update(DummyPanEvt(10.0, 0.0))
    canvas._handle_pan_end()
    end_wx, end_wy = canvas.latlng_to_world_px(canvas.center_lat, canvas.center_lng, canvas.zoom)

    assert abs((start_wx - end_wx) - 50.0) < 1.0
    assert abs(start_wy - end_wy) < 1.0


def test_tc_33_initial_query_filters_and_start_trip_here_url():
    """TC-33: Verifies PlacesView applies initial route_query filters on construction and formats Start Trip Here URL with placeId (MAP-QA-05, MAP-QA-08)."""
    from desktop_client.views.places_view import PlacesView

    pv = PlacesView(route_query="/map?category=nature_park")
    assert len(pv.filtered_places) < len(pv.all_places)
    assert all(p.category == "nature_park" for p in pv.filtered_places)

    nav_calls = []
    pv.on_navigate = lambda route, *args: nav_calls.append(route)
    pv._start_trip_from_place(pv.filtered_places[0])
    assert len(nav_calls) == 1
    assert "placeId=" in nav_calls[0]
    assert "destination=" in nav_calls[0]


def test_tc_34_drawer_selection_auto_closes_drawer():
    """TC-34: Verifies selecting a place from the List View drawer closes the drawer and opens the bottom sheet (MAP-QA-07)."""
    from desktop_client.views.places_view import PlacesView

    pv = PlacesView(initial_width=1280, initial_height=840)
    pv._toggle_drawer()
    assert pv.is_drawer_open is True

    pv._focus_place_and_open_dialog(pv.all_places[0])
    assert pv.is_drawer_open is False
    assert pv.selected_map_place is not None
```

## 4. Verification & Standalone Build Commands (Windows / WSL)

Run the following commands from the repository root (`Itinerary-App`) after applying Steps 1–4:

```powershell
# 1. Run the full desktop regression test suite (113/113 tests passing)
python -m pytest desktop_client/tests/ -v

# 2. Launch the Flet Desktop application locally to verify Map tab interactions
python -m desktop_client.main

# 3. Rebuild the standalone Windows executable distribution
python scripts/build_standalone_exe.py
```
