# Nueva Ecija Travel Itinerary App ("Trip mo, trip ko") — Full Documentation-Driven QA Audit v4, API Parity Matrix & Antigravity Remediation Plan

**Repository**: [https://github.com/Edselrenz/Itinerary-App](https://www.google.com/search?q=https://github.com/Edselrenz/Itinerary-App) (`feature/flet-desktop-app`)  
**Target Desktop Package**: `desktop_client/` (Python 3.12+ / Flet `>=1.1.2` / `httpx` / `pytest` / PyInstaller)  
**Reference Web Application**: `Project/` (Ionic 9 / Angular 22 / Leaflet 1.9 / TypeScript) & [https://edselrenz.github.io/Itinerary-App](https://www.google.com/search?q=https://edselrenz.github.io/Itinerary-App)  
**Reference Project Documentation Audited**:
- `docs/PROJECT_STATE.md` (Phases 1–50 & 24-Point MVP Gate)
- `docs/API_DOCUMENTATION.md` (19 Canonical FastAPI `/api/v1` Endpoints)
- `docs/FULL_WEBSITE_QA_AUDIT_AND_PROPOSAL.md` (64 Test Cases across 8 Modules, `QA-01` to `QA-14`)
- `docs/MAP_AND_ROUTING_PROPOSAL.md` (`MAP-01` to `MAP-03`, `ROUTE-01` to `ROUTE-05`)
- `docs/CUSTOM_AND_SUGGESTED_ITINERARY_PROPOSAL.md` (`UC-S1` to `UC-S6`, `UC-C1` to `UC-C5`, `S-BUG-01` to `S-BUG-06`, `C-BUG-01` to `C-BUG-06`)
- `docs/LIVE_SERVER_MAP_AND_SUGGESTED_ITINERARY_PROPOSAL.md` (`GAP-01` to `GAP-05`)
- `docs/DESKTOP_APP_API_INTEGRATION.md`, `docs/DESKTOP_APP_QA_AND_TESTING.md`, `docs/DESKTOP_APP_INSTALLATION_AND_BUILD.md`, and `scripts/build_standalone_exe.py`

---

## 1. Visual & Runtime Root-Cause Analysis of Your Screenshot (`image_4b1823.png`)

Inspecting your screenshot of the Map tab in `Trip mo, trip ko — Nueva Ecija Desktop` alongside `desktop_client/` and `scripts/build_standalone_exe.py` reveals **4 exact root causes** for everything visible in the image:

| # | Visual Defect Seen in Your Screenshot | Exact Root Cause in Code (`desktop_client/` & `scripts/build_standalone_exe.py`) | Mandatory Fix |
| :--- | :--- | :--- | :--- |
| **1** | **Every map tile displays yellow/black hazard bars: `"403 Access blocked — App is not following the tile usage policy of OpenStreetMap's volunteer-run servers: http://osm.wiki/Blocked"`** | In `desktop_client/components/slippy_map_canvas.py:353`, the app passes `https://tile.openstreetmap.org/{z}/{x}/{y}.png` directly into `ft.Image(src=tile_url)`. In Flet Desktop (Flutter engine), `ft.Image` fetches URLs using Dart's native `HttpClient`, which sends `User-Agent: Dart/3.x (dart:io)` with no `Referer`. OpenStreetMap's volunteer tile servers (`tile.openstreetmap.org`) **strictly block `Dart/3.x`** with HTTP `403 Access blocked`! | **Never** pass `https://tile.openstreetmap.org/...` directly to `ft.Image(src=...)`. Switch `SlippyMapCanvas` to **CartoDB Voyager OSM Tiles** (`https://basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png`, which renders clean OpenStreetMap road/POI cartography and **never blocks Flutter/Dart `ft.Image` with HTTP 403**), with an optional Python `httpx` tile cacher (`User-Agent: TripMoTripKoDesktop/1.0`) for offline tile caching. |
| **2** | **Header says `"Nueva Ecija GIS Map Explorer (13 Places Plotted)"` instead of `2,673` places** | **Three compounding bugs**:<br>1) **`scripts/build_standalone_exe.py:76–89`** never copies `desktop_client/assets` into `dist/NuevaEcijaTravel/assets` and omits `--add-data desktop_client/assets;assets`!<br>2) **`desktop_client/config/settings.py:18–20`**: When frozen (`NuevaEcijaTravel.exe`), `_resolve_base_dir()` returns `Path(sys.executable).parent` without checking `Path(getattr(sys, "_MEIPASS", ""))` (`_internal/`). Thus `osm_places.json` (`2,673` POIs) is not found in the `.exe`, so `load_osm_places()` (`offline_data.py:412`) returns **only the 13 `CANONICAL_OFFLINE_PLACES`**!<br>3) **`desktop_client/services/place_service.py:104`** passes `pages=...` instead of `total_pages=...` to `PaginatedPlaces(...)`, crashing with `TypeError: PaginatedPlaces.__init__() got an unexpected keyword argument 'pages'` whenever offline! | 1) Fix `scripts/build_standalone_exe.py` to bundle and copy `desktop_client/assets` (including `data/osm_places.json`) into `dist/NuevaEcijaTravel/assets` and `dist/NuevaEcijaTravel/_internal/assets`.<br>2) Update `settings.py` and `offline_data.py:load_osm_places()` to check `sys._MEIPASS`, `exe_dir / "assets"`, `exe_dir / "_internal" / "assets"`, and `Project/src/assets` so all **2,673 places** load in both dev mode and `.exe` mode.<br>3) Fix `place_service.py:104` (`total_pages=` instead of `pages=`). |
| **3** | **Clicking any marker pin on the map does nothing (silent crash)** | In `desktop_client/views/places_view.py:515`, `_select_map_place()` calls:<br>`show_place_detail_dialog(p, place, on_add_to_trip=...)`<br>But `show_place_detail_dialog()` in `desktop_client/components/dialogs.py:19` defines the parameter as **`on_add_to_day`**, NOT **`on_add_to_trip`**! Every pin click raises `TypeError: show_place_detail_dialog() got an unexpected keyword argument 'on_add_to_trip'`! | Fix `places_view.py:515` to pass `on_add_to_day=...` and `on_navigate=self.on_navigate` (and accept `on_add_to_trip` as an alias in `dialogs.py:show_place_detail_dialog()`). |
| **4** | **Map layout has a giant white form header on top (`Search`, `Filters`, `Reset`, `[Grid \| Map]`, `Filter by Municipality`, `Sort By`) and a fixed `920×520` box leaving a large blank white gap on the right** | `PlacesView` (`places_view.py`) was built as a paginated catalog table with a `[Grid \| Map]` toggle and a hardcoded `SlippyMapCanvas(width=920, height=520)` instead of matching the Web App's **`MapPage` (`Project/src/app/tabs/map/map.page.html`)**, which is a **100% full-bleed interactive map** with floating overlays and `isFollowRouteMode`! | Replace the static top form and fixed `920×520` box in `places_view.py` with the Web App's **Full-Bleed Interactive Map Layout (`expand=True`)**:<br>• **Floating Top Search & 17 Category Pills Bar (`.map-top-bar`)** overlaid on the map.<br>• **Floating Right Controls**: `[✨ Live OSM]`, `[🎯 Locate Me (GPS)]`, `[🧭 Reset Province View]`, `[+]`/`[-]`.<br>• **Floating Bottom `"List View (2,673)"` Pill** opening the collapsible **Destinations in View Drawer**.<br>• **Focused `isFollowRouteMode`** when navigated via `/map?itineraryId=...&day=...`! |

---

## 2. API Parity Audit: Does the Desktop App Use the Same API as the Web App?

We audited all **19 REST API endpoints** documented in `docs/API_DOCUMENTATION.md` across `backend/app/api/v1/`, `Project/src/app/core/services/` (Web App), and `desktop_client/services/` (Desktop App).

### 2.1 Complete Endpoint-by-Endpoint API Comparison Matrix

| # | FastAPI Backend Endpoint (`backend/app/api/v1/`) | Web App (`Project/src/app/core/services/`) | Desktop App (`desktop_client/services/`) | API Parity Status & Discrepancies Found |
| :-: | :--- | :--- | :--- | :--- |
| **1** | `GET /api/v1/health` | `ConnectivityService.checkHostHealth()` (`GET /health`) | `ConnectivityService.check_host_health()` (`GET /health`) | ⚠️ **BUG IN `main.py:308`**: `main.py` calls `await connectivity_service.check_host_health(api_client)`, passing 1 extra arg to a 0-arg method (`TypeError` on every 15s health check!). |
| **2** | `POST /api/v1/auth/register`<br>Body: `{first_name, last_name, username, email, password}` | `AuthService.register()` sends `{first_name, last_name, username, email, password}` + saves `middle_initial` locally + runs `GuestMigrationService`. | `AuthService.register()` sends `{first_name, last_name, username, email, password}`. | ⚠️ **2 GAPS**:<br>1) `SignupView._handle_signup()` (`signup_view.py:343`) **forgets to pass `middle_initial=self.mi_input.value`** to `auth_service.register()`!<br>2) Does not call `migrate_guest_trips()` after registration. |
| **3** | `POST /api/v1/auth/login`<br>Body: `{email, password}` | `AuthService.login()` sends `{email, password}`, respects `rememberMe`, and triggers `GuestMigrationService.promptAndMigrateIfNeeded()`. | `AuthService.login()` sends `{email, password}`. | ⚠️ **1 GAP**: `LoginView._handle_login()` does not trigger `migrate_guest_trips()` after login when local guest itineraries exist. |
| **4** | `POST /api/v1/auth/refresh`<br>Body: `{refresh_token}` | `auth.interceptor.ts` auto-refreshes on `401`. | `ApiClient.request()` auto-calls `_refresh_handler` on `401`. | ✅ **MATCHES** |
| **5** | `GET /api/v1/auth/me` | `AuthService.fetchCurrentUser()` | `AuthService.get_profile()` | ✅ **MATCHES** |
| **6** | `PATCH /api/v1/auth/me`<br>Body: `{first_name, last_name, username, current_password, new_password}` | `AuthService.updateProfile()` sends `UserUpdateIn` + stores extended fields in `localStorage`. | `AuthService.update_profile()` sends `payload.to_backend_dict()` + stores `profile_extra.json`. | ✅ **MATCHES** (Fixed in v3, but `ProfileView` needs password change fields optional support). |
| **7** | `POST /api/v1/auth/oauth/google` & `/oauth/apple` | Disabled in pilot build (`DEF-02`) with truthful pilot notice. | Completely omitted from `LoginView`/`SignupView`. | ✅ **MATCHES** (Keep social buttons removed per user instruction in Turn 3). |
| **8** | `GET /api/v1/municipalities?q=...` | `PlaceService.getMunicipalities(q)` | `PlaceService.get_municipalities()` | ✅ **MATCHES** |
| **9** | `GET /api/v1/places`<br>Params: `q`, `categories`, `municipality_id`, `municipality_name`, `price_tier`, `featured`, `min_lat`, `max_lat`, `min_lng`, `max_lng`, `limit` (`1..5000`), `offset` | `PlaceService.searchPlaces()` sends `q`, `categories` (comma-joined), `municipality_id`, `municipality_name`, `price_tier`, `featured`, bbox (`min_lat..max_lng`), `limit=3000` on Map, and merges into `osmPlacesCache` (`QA-02`). | `PlaceService.get_places()` ONLY sends `q`, `categories` (as list), `municipality_id`, `featured`, `limit=18`, `offset`, plus a non-existent `sort` param! | ❌ **4 API MISMATCHES**:<br>1) Desktop never sends **`municipality_name`**, **`price_tier`**, or **bounding-box (`min_lat..max_lng`)** to `GET /api/v1/places`!<br>2) Desktop passes `municipality_name` (e.g. `"Bongabon"`) inside the `municipality_id` UUID query param (`places_view.py:741`), which causes FastAPI (`municipality_id: uuid.UUID`) to return **`422 Unprocessable Content`** whenever a user filters by municipality name!<br>3) Offline fallback in `place_service.py:104` passes `pages=` instead of `total_pages=`, crashing with **`TypeError`**!<br>4) Does not merge online results into the 2,673 OSM cache (`merge_places_into_cache`). |
| **10** | `GET /api/v1/places/{place_id}` | `PlaceService.getPlaceById(id)` | `PlaceService.get_place_by_id(id)` | ✅ **MATCHES** |
| **11** | `POST /api/v1/places/discover`<br>(Live Google Places / Local DB discovery) | Called during live discovery (`OsmOverpassService` / `PlaceService`). | **NOT USED AT ALL** in `desktop_client/`! | ❌ **MISSING**: Add `PlaceService.discover_places()` & Live OSM Overpass discovery button on `MapView`. |
| **12** | `POST /api/v1/itineraries/suggest`<br>Body: `{title, destination, start_date, end_date, daily_budget, preferences, pacing, save_immediately, travel_mode, min_rating, include_live_places, anchor_place_id}` | `ItineraryService.suggestItinerary()` sends all fields with `save_immediately: false` and **does NOT save to `GuestStorage`** until user clicks `[Accept & Save]`. | `SuggestedItineraryRequest` omits `min_rating`, `include_live_places`, `anchor_place_id`, and `itinerary_service.py:57–59` **auto-saves every preview to `guest_storage` immediately** (`S-BUG-06` regression)! | ❌ **2 API/LOGIC BUGS**:<br>1) Add `min_rating`, `include_live_places`, `anchor_place_id` to `SuggestedItineraryRequest`.<br>2) Remove premature `self.guest_storage.save_itinerary(itinerary)` when `save_immediately=False` in `itinerary_service.py:57–70`! |
| **13** | `GET /api/v1/itineraries` | `ItineraryService.refreshItineraries()` | `ItineraryService.list_itineraries()` | ✅ **MATCHES** |
| **14** | `GET /api/v1/itineraries/{id}` | `ItineraryService.getItineraryById(id)` + `getItineraryOrDraftById(id)` | `ItineraryService.get_itinerary(id)` | ⚠️ **MISSING HELPER**: Add `get_itinerary_or_draft(id)` so `/map?itineraryId=draft` and `/trips/{id}` resolve drafts and cached cloud trips. |
| **15** | `POST /api/v1/itineraries` | `ItineraryService.createItinerary(payload)` | `ItineraryService.create_itinerary(payload)` | ✅ **MATCHES** |
| **16** | `PATCH /api/v1/itineraries/{id}`<br>Body: `{title, destination, start_date, end_date, daily_budget, preferences, assumptions, days}` | `ItineraryService.updateItinerary(id, payload)` sends **`days`** array so edited stops/days are persisted transactionally (`CR-003`). | `ItineraryService.update_itinerary(itinerary)` (`itinerary_service.py:401–411`) **omits `days`** from `update_data`, and `TripDetailView._save_changes()` (`trip_detail_view.py:557–588`) crashes with `ImportError: cannot import name 'ItineraryUpdatePayload'`! | ❌ **CRITICAL DATA-LOSS & CRASH BUG**:<br>1) Include `"days"` in `ItineraryService.update_itinerary()` `PATCH` payload.<br>2) Fix `TripDetailView._save_changes()` and `CustomBuilderView` edit mode to call `update_itinerary()` properly. |
| **17** | `DELETE /api/v1/itineraries/{id}` | `ItineraryService.deleteItinerary(id)` | `ItineraryService.delete_itinerary(id)` | ✅ **MATCHES** |
| **18** | `POST /api/v1/itineraries/{id}/days`, `POST .../items`, `PATCH .../items/{item_id}`, `DELETE .../items/{item_id}`, `POST .../reorder` | Used by `ItineraryService`. | `add_stop`, `delete_stop`, `reorder_stops` implemented; `update_stop` (`PATCH .../items/{item_id}`) missing. | ⚠️ Add `update_stop()` in `ItineraryService`. |
| **19** | `POST /api/v1/itineraries/compute-day-route` & `POST .../days/{day_id}/compute-route` | Used for road polyline & leg calculation (`RouteComputeRequest`). | `SlippyMapCanvas` calls OSRM directly without calling backend `/itineraries/compute-day-route` first. | ⚠️ **ENHANCEMENT**: Try backend `POST /api/v1/itineraries/compute-day-route` or OSRM (`router.project-osrm.org`), falling back to `generate_geodesic_arc`. |

---

## 3. Master Action Matrix: What to REMOVE, MODIFY, and ADD in `desktop_client/`

Based on `docs/PROJECT_STATE.md` and our **64-Test-Case Full-System Audit**, here is the exact inventory of what must be **REMOVED**, **MODIFIED**, and **ADDED**:

### 3.1 What to REMOVE (Dead Legacy Code, Broken Patterns & Premature Saves)
1. **DELETE Legacy Unreferenced Components**:
   - **Delete `desktop_client/components/sidebar.py`** (`SidebarNav`) and **`desktop_client/components/header.py`** (`TopHeader`) — remnants of the old side-menu layout (`QA-01`). Remove their imports from `desktop_client/components/__init__.py` and `desktop_client/tests/test_ui_consistency.py`.
   - **Delete `desktop_client/components/interactive_map.py`** (`InteractiveProvinceMap`) — imports `flet_map` (`ModuleNotFoundError: No module named 'flet_map'` on environments without `flet-map`) and is superseded by `SlippyMapCanvas`. Remove its import from `desktop_client/components/__init__.py`.
2. **REMOVE Direct `tile.openstreetmap.org` URLs in `ft.Image` (`slippy_map_canvas.py:353`)**:
   - OpenStreetMap's volunteer servers return `403 Access blocked` to Flutter/Dart `ft.Image`. Replace with CartoDB Voyager OSM (`https://basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png`) + local Python tile cache.
3. **REMOVE the Static Catalog Form Header, `[Grid | Map]` Switcher, and `Sort By` Dropdown from the `/map` Tab (`places_view.py`)**:
   - On the Web App (`map.page.html`), `/tabs/map` is a **full-bleed map** with floating search/category pills and a floating `List View (2,673)` drawer pill—not a `920×520` box under a giant white form header.
4. **REMOVE Premature Guest Storage Saving in `ItineraryService.generate_suggested_itinerary()` (`itinerary_service.py:57–70`)**:
   - Currently, generating a Suggested Itinerary preview (`save_immediately=False`) immediately writes the draft into `guest_storage.json` before the user clicks `[Accept & Save]` (`S-BUG-06`). Only cache it in `self.active_draft_itinerary` during preview, and persist to `guest_storage` / cloud ONLY when the user clicks `[Accept & Save]`!
5. **REMOVE Destructive `self.guest_storage.clear_all()` in `ProfileView._sync_guest_trips()` (`profile_view.py:1241`)**:
   - Currently, clicking `[Sync Now]` on the Profile screen deletes all local guest trips without uploading them! Replace with `await self.auth_service.migrate_guest_trips()`.

---

### 3.2 What to MODIFY (12 Critical Runtime Bugs & Layout Fixes)

1. **`desktop_client/main.py` (4 Router & Health Loop Bugs)**:
   - **Bug 1A (`main.py:308`)**: Change `await connectivity_service.check_host_health(api_client)` to `await connectivity_service.check_host_health()` (fixes silent `TypeError` every 15s).
   - **Bug 1B (`main.py:196–223`)**: Support query parameters on workflow routes (`route.startswith("/suggested")`, `route.startswith("/builder")`) and parse `?draft=true`, `?destination=...`, `?placeId=...`, and `/builder/{id}`! Also do **not** return a stale `cached_views["/builder"]` when `trip_data` (from `[Customize in Builder]` or `[Edit Itinerary]`) or `?draft=true` is passed!
   - **Bug 1C (`main.py:251`)**: Change `elif route in ("/map", "/places"):` to `elif route.startswith("/map") or route.startswith("/places"):` and pass `route_query=route` + `trip_data=selected_trip` into `PlacesView(on_navigate=navigate_to, route_query=route, active_trip=selected_trip)` so clicking **`[Full Map]`** in Suggested Wizard, Custom Builder, or Trip Detail actually opens the Map in **Follow-Route Mode** instead of falling through to the Home Dashboard!
   - **Bug 1D (`main.py:224–239`)**: When navigating to `/trips/{id}`, if `selected_trip` is `None`, check `itinerary_service.get_active_draft_itinerary()` and `guest_storage.get_itinerary(trip_id)` and async cloud lookup `itinerary_service.get_itinerary(trip_id)` so clicking a cloud-saved itinerary card on the Home screen opens `TripDetailView` instead of redirecting to `/saved`!

2. **`desktop_client/config/settings.py` & `scripts/build_standalone_exe.py` (Missing 2,673 OSM Places in `.exe` & Budget Presets)**:
   - **Bug 2A (`settings.py:18–22` & `165–180`)**: In `_resolve_base_dir()` and `get_asset_path()`, when `getattr(sys, "frozen", False)` is True, check:
     1. `Path(sys.executable).parent / "assets"`
     2. `Path(getattr(sys, "_MEIPASS", "")) / "assets"`
     3. `Path(getattr(sys, "_MEIPASS", "")) / "desktop_client" / "assets"`
   - **Bug 2B (`scripts/build_standalone_exe.py:76–89` & `180`)**: Add `--add-data "{desktop_dir / 'assets'}{os.pathsep}assets"` to the PyInstaller command AND explicitly copy `shutil.copytree(desktop_dir / "assets", out_app_dir / "assets", dirs_exist_ok=True)` so `dist/NuevaEcijaTravel/assets/data/osm_places.json` (all 2,673 POIs) and all 42 photos are guaranteed to exist in the standalone `.exe`!
   - **Bug 2C (`settings.py:134–139`)**: Align `BUDGET_PRESETS` with the Web App (`₱1,500`, `₱2,500`, `₱4,000`, `₱6,000`).

3. **`desktop_client/services/place_service.py` (Offline Crash & HTTP 422 Municipality Filter Bug)**:
   - **Bug 3A (`place_service.py:104`)**: Change `pages=max(1, (total + limit - 1) // limit)` to `total_pages=max(1, (total + limit - 1) // limit)` so offline `PlaceService.get_places()` stops throwing `TypeError`!
   - **Bug 3B (`place_service.py:76–77`)**: Check if `municipality_id` is a valid UUID (`uuid.UUID(municipality_id)`). If it is a municipality **name** (like `"Bongabon"` or `"Cabanatuan City"` or `"muni-bongabon"`), send it as `params["municipality_name"] = ...` instead of `params["municipality_id"]` so FastAPI (`backend/app/api/v1/places.py:114–115`) never rejects it with `422 Unprocessable Content`!
   - **Bug 3C**: Add `in_memory_places_cache` (`merge_places_into_cache`) initialized with all **2,673 places** from `get_all_offline_places()`, merging live API results by `id` (`QA-02`).

4. **`desktop_client/components/slippy_map_canvas.py` (Fix `403 Access blocked` Tiles & Responsive Viewport Sizing)**:
   - **Bug 4A (`slippy_map_canvas.py:353`)**: Replace `https://tile.openstreetmap.org/{z}/{x}/{y}.png` with CartoDB Voyager OSM (`https://basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png`) so Flutter/Dart `ft.Image` loads street & POI tiles with **zero `403 Access blocked` errors**!
   - **Bug 4B**: Support `expand=True` with dynamic viewport dimensions (`width=1220, height=700` on full-screen Map tab) so the map fills the entire desktop window without a blank white gap on the right.

5. **`desktop_client/views/dashboard_view.py` (Notification Bell Crash, Card Cap & Trip Click Bug)**:
   - **Bug 5A (`dashboard_view.py:681–683`)**: Fix `_on_bell_clicked()`:
     ```python
     from desktop_client.core.storage import get_guest_storage
     guest_count = len(get_guest_storage().list_itineraries())
     is_guest = self.session_manager.is_guest
     ```
   - **Bug 5B (`dashboard_view.py:311` & `606`)**: Cap Home Saved Itineraries preview at `self.saved_itineraries[:2]` (matching Web App Milestone 8) and pass `itin` when clicking a card: `on_click=lambda _, it=itin: self.on_navigate(f"/trips/{it.id}", it) if self.on_navigate else None`.

6. **`desktop_client/views/signup_view.py` & `desktop_client/services/auth_service.py` & `desktop_client/models/itinerary.py` (Middle Initial & Guest Trip Migration)**:
   - **Bug 6A (`signup_view.py:343`)**: Pass `middle_initial=(self.mi_input.value or "").strip()` into `self.auth_service.register(...)`.
   - **Bug 6B (`models/itinerary.py`)**: Add `def to_create_payload(self) -> ItineraryCreatePayload:` to `Itinerary` so `AuthService.migrate_guest_trips()` works without raising `AttributeError`!
   - **Bug 6C (`profile_view.py:1227–1246`)**: In `ProfileView._sync_guest_trips()`, call `migrated = await self.auth_service.migrate_guest_trips()` and show a toast `"Migrated {migrated} local trips to your cloud account!"` instead of wiping `guest_storage`!
   - **Bug 6D (`profile_view.py:460` & `464`)**: Replace `self._run_async(_do_test)` with `self.safe_page.run_task(_do_test)` and wrap `self.connectivity_service.set_custom_api_url(new_url)` in `try ... except ValueError as err:`.

7. **`desktop_client/views/trip_detail_view.py` & `desktop_client/services/itinerary_service.py` (In-Place Edit Save Crash & `[Full Map]` Button)**:
   - **Bug 7A (`trip_detail_view.py:554–598` & `itinerary_service.py:395–416`)**:
     - In `ItineraryService.update_itinerary(self, itinerary: Itinerary)`, include `"days"` in `update_data` so all stop edits, reorders, and added/deleted days are persisted to `PATCH /api/v1/itineraries/{id}`!
     - In `TripDetailView._save_changes()`, remove the broken `from desktop_client.models.itinerary import ItineraryUpdatePayload` import and call `updated = await self.itinerary_service.update_itinerary(self.itinerary)` directly!
   - **Bug 7B (`trip_detail_view.py:238`)**: Pass `on_view_full_map=lambda: self._open_full_map()` to `ItineraryRouteMap` so clicking `[Full Map]` in `TripDetailView` navigates to `f"/map?itineraryId={self.itinerary.id}&day={active_day.day_number}"`!

---

### 3.3 What to ADD (Missing Web App Features across Map, Suggested Wizard & Custom Builder)

1. **Full-Bleed Interactive `MapView` (`desktop_client/views/places_view.py`) Matching `Project/src/app/tabs/map/map.page.html`**:
   - **Discovery Mode (`is_follow_route_mode = False`)**:
     - Full-bleed `SlippyMapCanvas(width=1220, height=700)` plotting all **2,673 merged places** (`get_all_offline_places()` + live API places) with blue `#0084ff` marker clusters (`zoom < 14`) and category pins (`zoom >= 14`).
     - **Floating Top Search & 17 Category Filter Pills Bar** overlaid at `top=12, left=16, right=16`.
     - **Floating Right Control Buttons**: `[✨ Live OSM]`, `[🎯 Locate Me (GPS)]`, `[🧭 Reset Province View]`.
     - **Floating Bottom-Center `"List View (N)"` Pill** that toggles the **Collapsible POI List Drawer (`Destinations in View`)**.
   - **Focused Follow-Route Mode (`is_follow_route_mode = True` when route has `?itineraryId=...&day=...`)**:
     - Loads the target `Itinerary` (from `active_trip`, `itinerary_service.get_active_draft_itinerary()`, or `guest_storage` / cloud) and isolates the active day's stops & OSRM road polyline on the map (hiding the 2,673 background clusters unless `[Show Nearby POIs]` is toggled ON!).
     - **Floating Active Route Top Bar**: `[← Back to Plan]`, `[🗺️ Browse Map]`, destination title & stop count, **Day Switcher Pills (`Day 1 | Day 2 | ...`)**, and **`[👁️ Show Nearby POIs]`** toggle button.
     - **Bottom Active Route Stops Carousel**: Displays `Stop X of Y`, **`[↗ Google Maps Navigation]`** multi-stop URL button, and horizontal clickable stop cards (`1. [Stop Name]`, `2. [Stop Name]`...) that pan/highlight the corresponding numbered stop pin on the map!

2. **Web-App-Identical `SuggestedWizardView` (`desktop_client/views/suggested_wizard_view.py`)**:
   - Hydrate `budget_val` from the user's saved `default_daily_budget` (`3000.0` default).
   - Support `anchor_place_id` when launched from `PlaceDetailSheet`'s `[✨ Start Trip Here]` button.
   - Add **Minimum Place Rating Chips** (`All Ratings`, `4.0+ ★`, `4.5+ ★`) to the wizard form.
   - In Result View (`view_mode == "itinerary"`):
     - Add the **Verified Place Costs Card (`.verified-budget-card`)** using `calculate_budget_summary()` (showing verified min–max range + unpriced stop count).
     - Make the **Travel Notes & Planning Assumptions Box** a collapsible accordion with categorized tags (`Pacing`, `Routing`, `Budget`, `Schedule`).
     - Make every `StopCard` clickable (`on_click`) to open `show_place_detail_dialog()` with the stop's commute guide!
     - In `_load_nearby_amenities()`, filter nearby restaurants, hospitals/pharmacies, and stores **by the active day's municipality** (`get_day_location_name(active_day)`), and when `[✓ Accept & Save Itinerary]` is clicked, navigate directly to `/trips/{saved.id}`!

3. **Web-App-Identical `CustomBuilderView` (`desktop_client/views/custom_builder_view.py`)**:
   - In **View 0 (`form`)**: Add the 5 **Traveler Preferences Pills** (`Nature & Parks`, `Food Trip`, `Culture & History`, `Shopping`, `Resort`) and initialize `daily_budget` from `user.default_daily_budget`.
   - In **View 1 (`browse`)**: Add the **`✨ Recommended for You`** category pill when preferences are selected, map all 16 canonical categories (`All`, `✨ Recommended for You`, `Tourist Spots`, `Food`, `Resorts & Stays`, `Culture & Heritage`, `Shopping`, `Transit & Essentials`, `Other`), and sort places matching `self.destination` to the top!
   - In **View 2 (`timeline`)**:
     - Add the **Editable Trip Settings Card** (`Trip Title`, `Daily Budget`, and clickable `Travel Dates` that run `sync_days_with_date_range()`) and the **Verified Place Costs Card** at the top of the timeline.
     - In `_auto_schedule_active_day()`, compute dynamic **Haversine driving transit buffers (`15..120 mins` at `40 km/h + 10 min buffer`)** between consecutive stops (`QA-13`).
     - In `_open_edit_stop_dialog()`, include **Min Cost (₱)** and **Max Cost (₱)** fields alongside `Move to Day`, `Planned Time`, `Duration`, and `Notes`.
     - In `_open_custom_venue_dialog()`, remove the invalid `latitude=lat, longitude=lng` kwargs from `ItineraryItem(...)` (use `custom_lat=lat, custom_lng=lng`) so adding an off-grid venue never crashes with `TypeError`!
     - Support **Edit Existing Itinerary Mode** (`if self.existing_itinerary: await self.itinerary_service.update_itinerary(...)` on save).

---

## 4. Complete Drop-In Code Implementations for Antigravity

### 4.1 Fix `desktop_client/components/slippy_map_canvas.py` (Eliminate `403 Access blocked` + Responsive Sizing)
In `desktop_client/components/slippy_map_canvas.py`, replace `_render_tiles()` (lines 334–370) so it uses **CartoDB Voyager OSM raster tiles** (`https://basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png`) which never return `403 Access blocked` to Flutter's `ft.Image` client:

```python
    # Inside SlippyMapCanvas._render_tiles() in desktop_client/components/slippy_map_canvas.py:
    def _render_tiles(self) -> None:
        cx, cy = latlon_to_world_px(self.center_lat, self.center_lng, self.zoom)
        top_left_wx = cx - (self._map_w / 2.0)
        top_left_wy = cy - (self._map_h / 2.0)

        min_tx = int(math.floor(top_left_wx / 256.0))
        max_tx = int(math.floor((top_left_wx + self._map_w) / 256.0))
        min_ty = int(math.floor(top_left_wy / 256.0))
        max_ty = int(math.floor((top_left_wy + self._map_h) / 256.0))

        num_tiles = 2 ** self.zoom
        subdomains = ("a", "b", "c", "d")
        tiles: list[ft.Control] = []
        for tx in range(min_tx, max_tx + 1):
            for ty in range(min_ty, max_ty + 1):
                if ty < 0 or ty >= num_tiles:
                    continue
                wrapped_tx = tx % num_tiles
                left_px = (tx * 256.0) - top_left_wx
                top_px = (ty * 256.0) - top_left_wy
                sub = subdomains[(wrapped_tx + ty) % len(subdomains)]
                # CartoDB Voyager OSM tile server — 100% compatible with Flutter/Flet desktop without 403 blocks
                tile_url = f"https://{sub}.basemaps.cartocdn.com/rastertiles/voyager/{self.zoom}/{wrapped_tx}/{ty}.png"
                tiles.append(
                    ft.Container(
                        left=left_px,
                        top=top_px,
                        width=256,
                        height=256,
                        content=ft.Image(
                            src=tile_url,
                            width=256,
                            height=256,
                            fit=ft.BoxFit.COVER,
                            gapless_playback=True,
                        ),
                    )
                )
        self._tile_stack.controls = tiles
```

---

### 4.2 Fix `desktop_client/config/settings.py` & `desktop_client/core/offline_data.py` & `scripts/build_standalone_exe.py` (Ensure All 2,673 Places Load in Both Dev & `.exe`)

1. **In `desktop_client/config/settings.py`**:
```python
def _resolve_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        exe_parent = Path(sys.executable).parent
        if (exe_parent / "assets" / "data" / "osm_places.json").is_file():
            return exe_parent
        meipass = Path(getattr(sys, "_MEIPASS", ""))
        if (meipass / "assets" / "data" / "osm_places.json").is_file():
            return meipass
        if (meipass / "desktop_client" / "assets" / "data" / "osm_places.json").is_file():
            return meipass / "desktop_client"
        if (exe_parent / "_internal" / "assets" / "data" / "osm_places.json").is_file():
            return exe_parent / "_internal"
        return exe_parent
    return Path(__file__).resolve().parent.parent

BUDGET_PRESETS = [
    {"key": "budget", "label": "Budget (₱1,500 / day)", "amount": 1500.0},
    {"key": "moderate", "label": "Moderate (₱2,500 / day)", "amount": 2500.0},
    {"key": "comfort", "label": "Comfort (₱4,000 / day)", "amount": 4000.0},
    {"key": "luxury", "label": "Luxury (₱6,000 / day)", "amount": 6000.0},
]
```

2. **In `desktop_client/core/offline_data.py` (`load_osm_places()`)**:
Check all candidate paths for `osm_places.json` and **only cache `_CACHED_ALL_PLACES` if `raw_osm` was found** (or after checking all candidate paths):
```python
def load_osm_places() -> list[dict[str, Any]]:
    """Loads curated OpenStreetMap places (2,673 POIs) from bundled, frozen, or repo assets."""
    global _CACHED_ALL_PLACES
    if _CACHED_ALL_PLACES is not None and len(_CACHED_ALL_PLACES) > 100:
        return _CACHED_ALL_PLACES

    import sys
    settings = get_settings()
    here = Path(__file__).resolve()
    candidates = [
        settings.assets_dir / "data" / "osm_places.json",
        here.parent.parent / "assets" / "data" / "osm_places.json",
        here.parent.parent.parent / "Project" / "src" / "assets" / "data" / "osm_places.json",
        Path.cwd() / "desktop_client" / "assets" / "data" / "osm_places.json",
        Path.cwd() / "Project" / "src" / "assets" / "data" / "osm_places.json",
    ]
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).parent
        meipass = Path(getattr(sys, "_MEIPASS", ""))
        candidates = [
            exe_dir / "assets" / "data" / "osm_places.json",
            exe_dir / "_internal" / "assets" / "data" / "osm_places.json",
            exe_dir / "_internal" / "desktop_client" / "assets" / "data" / "osm_places.json",
            meipass / "assets" / "data" / "osm_places.json",
            meipass / "desktop_client" / "assets" / "data" / "osm_places.json",
            *candidates,
        ]

    raw_osm: list[dict[str, Any]] = []
    for cand in candidates:
        if cand.is_file():
            try:
                with open(cand, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > 0:
                        raw_osm = data
                        break
                    elif isinstance(data, dict) and "places" in data:
                        raw_osm = data["places"]
                        break
            except Exception:
                continue
    # (Proceed with merging CANONICAL_OFFLINE_PLACES + raw_osm as before)
```

3. **In `scripts/build_standalone_exe.py`**:
Add `--add-data f"{desktop_dir / 'assets'}{os.pathsep}assets"` to `cmd`, and after PyInstaller finishes (around line 180), explicitly copy the assets folder into `dist/NuevaEcijaTravel/assets`:
```python
    # Copy desktop_client/assets into dist/NuevaEcijaTravel/assets so osm_places.json (2,673 POIs) & photos are always present
    target_assets_dir = out_app_dir / "assets"
    shutil.copytree(desktop_dir / "assets", target_assets_dir, dirs_exist_ok=True)
    if internal_dir.exists():
        shutil.copytree(desktop_dir / "assets", internal_dir / "assets", dirs_exist_ok=True)
```

---

### 4.3 Fix `desktop_client/services/place_service.py` (Fix Offline `TypeError`, Municipality Name Filter & 2,673-Place Cache Merging)

Replace `desktop_client/services/place_service.py` with this implementation that matches `Project/src/app/core/services/place.service.ts`:

```python
"""Place Service managing POI queries, 2,673-POI cache merging, filtering, search, and municipality catalogs."""

import logging
from typing import Any, Optional
import uuid

from desktop_client.config.settings import CANONICAL_CATEGORIES
from desktop_client.core.api_client import ApiClient, get_api_client
from desktop_client.core.offline_data import (
    ALL_32_LGUS_METADATA,
    get_all_offline_places,
    get_filtered_local_places,
)
from desktop_client.models.place import Municipality, PaginatedPlaces, Place

logger = logging.getLogger(__name__)


def _is_valid_uuid(val: str) -> bool:
    try:
        uuid.UUID(str(val))
        return True
    except Exception:
        return False


class PlaceService:
    """Interacts with backend Places and Municipalities endpoints with 2,673-POI in-memory cache merging."""

    def __init__(self, api_client: Optional[ApiClient] = None):
        self.api_client = api_client or get_api_client()
        self._municipalities_cache: Optional[list[Municipality]] = None
        self._categories_cache: Optional[list[str]] = None
        self._osm_places_cache: list[Place] = []

    def get_loaded_places(self, municipality: Optional[str] = None) -> list[Place]:
        """Synchronously returns all 2,673+ places (merged online + offline OSM dataset)."""
        if not self._osm_places_cache:
            self._osm_places_cache = [Place.from_dict(p) for p in get_all_offline_places()]
        if not municipality or municipality.lower().strip() in ("all", "nueva ecija", "all 32 municipalities"):
            return list(self._osm_places_cache)
        m_low = municipality.lower().strip()
        return [
            p for p in self._osm_places_cache
            if m_low in (p.municipality_name or "").lower() or m_low == (p.municipality_id or "").lower()
        ]

    def merge_places_into_cache(self, new_places: list[Place]) -> None:
        """Merges online API places into the 2,673-POI cache by ID without purging unseen places (QA-02)."""
        if not new_places:
            return
        if not self._osm_places_cache:
            self._osm_places_cache = [Place.from_dict(p) for p in get_all_offline_places()]
        by_id = {p.id: p for p in self._osm_places_cache}
        for np in new_places:
            by_id[np.id] = np
        self._osm_places_cache = list(by_id.values())

    async def get_municipalities(self, force_refresh: bool = False) -> list[Municipality]:
        """Fetches all 32 Nueva Ecija municipalities and cities with offline fallback."""
        if self._municipalities_cache is not None and not force_refresh:
            return self._municipalities_cache

        try:
            data = await self.api_client.get("municipalities")
            if isinstance(data, list) and data:
                # Merge backend UUIDs with full 32-LGU metadata
                by_name = {str(m.get("name", "")).lower(): Municipality.from_dict(m) for m in data}
                merged: list[Municipality] = []
                for name, meta in ALL_32_LGUS_METADATA.items():
                    found = by_name.get(name.lower())
                    if found:
                        if not found.place_count:
                            found.place_count = meta.get("poi_count", 0)
                        merged.append(found)
                    else:
                        merged.append(
                            Municipality(
                                id=name,
                                name=name,
                                place_count=meta.get("poi_count", 0),
                            )
                        )
                self._municipalities_cache = merged
                return self._municipalities_cache
        except Exception as err:
            logger.info(f"Could not load municipalities from backend, using offline dataset: {err}")

        fallback: list[Municipality] = []
        for name, meta in ALL_32_LGUS_METADATA.items():
            fallback.append(
                Municipality(
                    id=name,
                    name=name,
                    place_count=meta.get("poi_count", 0),
                )
            )
        self._municipalities_cache = fallback
        return self._municipalities_cache

    async def get_categories(self, force_refresh: bool = False) -> list[str]:
        """Returns the 16 canonical categories conforming to the Nueva Ecija schema."""
        if self._categories_cache is None or force_refresh:
            self._categories_cache = [c["key"] for c in CANONICAL_CATEGORIES]
        return self._categories_cache

    async def get_places(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        category: Optional[str] = None,
        categories: Optional[list[str]] = None,
        municipality_id: Optional[str] = None,
        municipality_name: Optional[str] = None,
        price_tier: Optional[str] = None,
        is_featured: Optional[bool] = None,
        min_lat: Optional[float] = None,
        max_lat: Optional[float] = None,
        min_lng: Optional[float] = None,
        max_lng: Optional[float] = None,
        sort: Optional[str] = None,
    ) -> PaginatedPlaces:
        """Queries places via GET /api/v1/places with full parameter parity and 2,673-POI offline fallback."""
        limit = max(1, page_size)
        offset = max(0, (page - 1) * limit)
        params: dict[str, Any] = {
            "limit": limit,
            "offset": offset,
        }
        if search and search.strip():
            params["q"] = search.strip()
        if categories:
            valid_cats = [c.strip() for c in categories if c and c.strip() and c != "all"]
            if valid_cats:
                params["categories"] = valid_cats
        elif category and category.strip() and category != "all":
            params["categories"] = [category.strip()]

        # Resolve municipality_id vs municipality_name safely (prevents FastAPI 422 on non-UUID names)
        muni_Name_resolved = municipality_name
        if municipality_id and municipality_id.strip() and municipality_id != "all":
            raw_m = municipality_id.strip()
            if _is_valid_uuid(raw_m):
                params["municipality_id"] = raw_m
            else:
                clean_m = raw_m.replace("muni-", "").replace("-", " ")
                muni_Name_resolved = clean_m

        if muni_Name_resolved and muni_Name_resolved.strip() and muni_Name_resolved.lower() != "all":
            params["municipality_name"] = muni_Name_resolved.strip()

        if price_tier and price_tier.strip() and price_tier != "all":
            params["price_tier"] = price_tier.strip().lower()

        if is_featured is not None:
            params["featured"] = is_featured

        if None not in (min_lat, max_lat, min_lng, max_lng):
            params["min_lat"] = min_lat
            params["max_lat"] = max_lat
            params["min_lng"] = min_lng
            params["max_lng"] = max_lng

        if sort:
            params["sort"] = sort

        try:
            data = await self.api_client.get("places", params=params)
            paginated = PaginatedPlaces.from_dict(data)
            self.merge_places_into_cache(paginated.items)
            return paginated
        except Exception as err:
            logger.info(f"Using offline 2,673-POI catalog fallback: {err}")
            bounds = (min_lat, max_lat, min_lng, max_lng) if None not in (min_lat, max_lat, min_lng, max_lng) else None
            items, total = get_filtered_local_places(
                q=search,
                category=category,
                categories=categories,
                municipality_name=muni_Name_resolved,
                municipality_id=municipality_id if (municipality_id and _is_valid_uuid(municipality_id)) else None,
                is_featured=is_featured,
                price_tier=price_tier,
                bounds=bounds,
                sort=sort,
                limit=limit,
                offset=offset,
            )
            place_objs = [Place.from_dict(it) for it in items]
            return PaginatedPlaces(
                items=place_objs,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=max(1, (total + limit - 1) // limit),
            )

    async def get_featured_places(self, limit: int = 12) -> list[Place]:
        """Retrieves top curated destinations for the dashboard."""
        try:
            paginated = await self.get_places(page=1, page_size=limit, is_featured=True)
            if paginated.items:
                return paginated.items
            fallback = await self.get_places(page=1, page_size=limit)
            return fallback.items
        except Exception:
            return self.get_loaded_places()[:limit]

    async def get_place_by_id(self, place_id: str) -> Optional[Place]:
        """Fetches full place details with offline lookup across all 2,673 places."""
        try:
            data = await self.api_client.get(f"places/{place_id}")
            if data:
                return Place.from_dict(data)
        except Exception:
            pass

        for p in self.get_loaded_places():
            if str(p.id) == str(place_id):
                return p
        return None


_place_service_instance: Optional[PlaceService] = None


def get_place_service() -> PlaceService:
    """Singleton getter for PlaceService."""
    global _place_service_instance
    if _place_service_instance is None:
        _place_service_instance = PlaceService()
    return _place_service_instance
```

---

### 4.4 Full-Bleed Web-Parity `PlacesView` / `MapView` (`desktop_client/views/places_view.py`)
Replace `desktop_client/views/places_view.py` so `/map` looks, feels, and works **100% like `Project/src/app/tabs/map/map.page.html`**:
- **Full-Bleed Map Canvas (`expand=True`, `width=1240, height=740`)** filling the entire viewport above the bottom tab bar (no static top form, no `[Grid | Map]` toggle, no `Sort By` dropdown, no blank right-side gap!).
- **Floating Top Search & 17 Category Filter Pills Bar (`.map-top-bar`)** positioned at `top=14, left=16, right=16` over the map, with a live search box, clear `[✕]` button, and **`[Filters (N)]`** button opening the Multi-Select Filter Modal (Categories multi-select, 32 Municipalities chips, and Price Tiers `All Prices | Free (₱0) | Budget (≤ ₱500) | Mid-Range (> ₱500)`).
- **Floating Right Controls (`right=16, bottom=100`)**:
  - **`[✨]` Live OSM Discovery**: Queries `/api/v1/places?limit=3000` / Overpass and merges into the 2,673-POI map layer.
  - **`[🎯]` Locate My Position (GPS)**: Centers on Cabanatuan City (`15.4865, 120.9674`, `zoom=14`) with the blue user GPS indicator dot.
  - **`[🧭]` Reset Province View**: Recenters to `[15.58, 121.00], zoom=10`.
- **Floating Bottom-Center `"List View (2,672)"` Pill (`bottom=18`)**:
  - Clicking it opens the **Collapsible POI List Drawer (`Destinations in View`)** over the bottom of the map where clicking any card flies to that pin and opens `show_place_detail_dialog()` (passing `on_add_to_day` and `on_navigate` properly!).
- **Focused `is_follow_route_mode` (`?itineraryId=...&day=...`)**:
  - Automatically activates when navigated via `/map?itineraryId=draft&day=1` (from Suggested Wizard or Custom Builder) or `/map?itineraryId={id}&day={day}` (from Trip Detail)!
  - Hides the 2,673 background discovery clusters by default (`show_background_pois_in_route_mode = False`) so the day's numbered stops (`1..N`) and OSRM road polyline stand out clearly!
  - Renders the **Floating Active Route Control Bar** at the top of the map:
    - **`[← Back to Plan]`** (returns to `/suggested`, `/builder`, or `/trips/{id}` while preserving the draft!).
    - **`[🗺️ Browse Map]`** (`exit_follow_route_mode_cleanly()`).
    - **Day Switcher Pills (`Day 1`, `Day 2`, ...)** for multi-day itineraries.
    - **`[👁️ Show Nearby POIs]`** toggle button to overlay/hide nearby POIs along the route.
  - Renders the **Bottom Active Route Stops Carousel** with `Stop X of Y`, **`[↗ Google Maps Navigation]`** multi-stop URL launcher, and clickable horizontal stop cards (`1. [Stop Name]`, `2. [Stop Name]`...) that center and highlight the active stop pin on the map!

---

### 4.5 Fix `main.py` Query-String Routing, Draft Preservation & Background Health Check
In `desktop_client/main.py`:
1. Parse `base_route = route.split("?")[0]` and `query_params = urllib.parse.parse_qs(urllib.parse.urlparse(route).query)` at the start of `navigate_to()`.
2. When `base_route == "/suggested"`:
   - If `query_params.get("destination")` or `query_params.get("placeId")` is passed (e.g., from `PlaceDetailSheet`'s `[✨ Start Trip Here]`), pass `initial_destination` and `anchor_place_id` into `SuggestedWizardView`.
   - If returning from `/map?itineraryId=draft`, restore the existing `SuggestedWizardView` instance (or hydrate from `itinerary_service.get_active_draft_itinerary()`).
3. When `base_route == "/builder"`:
   - If `query_params.get("draft") == ["true"]` or `trip_data` is passed (from `[Customize in Builder]` or `[Edit Itinerary]`), instantiate `CustomBuilderView(on_navigate=navigate_to, existing_itinerary=trip_data, is_draft_from_wizard=("draft=true" in route))` so it opens directly in `active_view = "timeline"` with all stops populated!
4. When `base_route in ("/map", "/places")`:
   - Instantiate `PlacesView(on_navigate=navigate_to, route_query=route, active_trip=selected_trip)` so `/map?itineraryId=draft&day=1` enters **Follow-Route Mode**!
5. In `check_backend_loop()` (`main.py:308`):
   - Call `await connectivity_service.check_host_health()` with **0 arguments**.

---

### 4.6 Fix `models/itinerary.py`, `services/itinerary_service.py`, `views/suggested_wizard_view.py`, `views/custom_builder_view.py`, and `views/trip_detail_view.py`

1. **In `desktop_client/models/itinerary.py`**:
   - Add `min_rating: Optional[float] = None`, `include_live_places: bool = True`, and `anchor_place_id: Optional[str] = None` to `SuggestedItineraryRequest` and include them in `to_dict()`.
   - Add `total_days` property (`return max(1, len(self.days))`) and `to_create_payload()` method to `Itinerary`:
     ```python
     @property
     def total_days(self) -> int:
         return max(1, len(self.days))

     def to_create_payload(self) -> "ItineraryCreatePayload":
         days_data = []
         for d in self.days:
             items_data = []
             for it in d.items:
                 items_data.append({
                     "place_id": it.place_id,
                     "custom_title": it.custom_title or it.display_title,
                     "custom_lat": it.custom_lat or (it.place.latitude if it.place else None),
                     "custom_lng": it.custom_lng or (it.place.longitude if it.place else None),
                     "sort_order": it.sort_order,
                     "planned_time": it.planned_time,
                     "duration_minutes": it.duration_minutes,
                     "notes": it.notes,
                     "estimated_cost_min": it.estimated_cost_min,
                     "estimated_cost_max": it.estimated_cost_max,
                     "place": it.place.to_dict() if it.place else None,
                 })
             days_data.append({
                 "day_number": d.day_number,
                 "travel_date": d.travel_date,
                 "title": d.title,
                 "items": items_data,
             })
         return ItineraryCreatePayload(
             title=self.title,
             destination=self.destination,
             start_date=self.start_date,
             end_date=self.end_date,
             daily_budget=self.daily_budget,
             preferences=self.preferences,
             type=self.type,
             assumptions=self.assumptions,
             days=days_data,
         )
     ```
   - Add `calculate_budget_summary(itinerary: Itinerary) -> dict[str, Any]` helper in `ItineraryService` matching `itinerary.service.ts:393–432` (`verified_min`, `verified_max`, `unverified_count`, `display_text`).

2. **In `desktop_client/services/itinerary_service.py`**:
   - In `generate_suggested_itinerary()` (lines 57–70), **only** call `self.guest_storage.save_itinerary(itinerary)` if `request.save_immediately is True`! Always store `self.active_draft_itinerary = itinerary`.
   - In `update_itinerary(self, itinerary: Itinerary)` (lines 401–411), include `"days": itinerary.to_create_payload().days` inside `update_data` so `PATCH /api/v1/itineraries/{id}` saves modified days and stops to PostgreSQL!

3. **In `desktop_client/views/custom_builder_view.py`**:
   - In `_open_custom_venue_dialog()` (line 897), remove `latitude=lat, longitude=lng` and pass only `custom_lat=lat, custom_lng=lng` to `ItineraryItem(...)`.
   - In `_open_edit_stop_dialog()` (line 822), add `cost_min_field` and `cost_max_field` (validating `min <= max`) alongside `Move to Day`, `Planned Time`, `Duration`, and `Notes`.
   - In `_auto_schedule_active_day()` (line 162), calculate Haversine transit time between `prev_item` and `item` (`calculate_haversine_meters` at `40 km/h + 10 min buffer`, clamped to `15..120 mins`) instead of a hardcoded `30` mins.
   - Add the **Editable Trip Settings Card** (`Trip Title`, `Daily Budget`, `Travel Dates`) and **Verified Place Costs Card** at the top of `_build_timeline_view()`.
   - In `_save_custom_itinerary()`, if `self.existing_itinerary` is present and not a wizard draft, update `self.existing_itinerary` and call `await self.itinerary_service.update_itinerary(self.existing_itinerary)`!

---

## 5. Complete 64-Test-Case Acceptance Checklist for Antigravity

Before finishing, Antigravity must verify that **both** the 47 unit tests (`pytest desktop_client/tests/ -v`) AND the following **12 End-to-End Parity Gates** pass with 0 errors:

1. **Map Tile Gate (`TC-25`)**: `SlippyMapCanvas` uses `basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png` (0 references to `tile.openstreetmap.org` in `ft.Image`), eliminating all `403 Access blocked` tiles.
2. **2,673-POI Map & Standalone `.exe` Gate (`TC-07`, `TC-28`, `TC-64`)**: `PlaceService.get_loaded_places()` returns `>= 2,670` places in both dev mode and compiled `NuevaEcijaTravel.exe` (`scripts/build_standalone_exe.py` copies `desktop_client/assets` to `dist/NuevaEcijaTravel/assets`), and `PlaceService.get_places()` offline fallback uses `total_pages=` (0 `TypeError` crashes).
3. **Full-Bleed Map Layout & Pin Click Gate (`TC-26`, `TC-27`, `TC-29`, `TC-30`, `TC-31`)**: `/map` renders a full-bleed `SlippyMapCanvas` with floating top search & 17 category pills, floating right `[✨ Live OSM]`, `[🎯 Locate Me]`, `[🧭 Reset View]` buttons, floating bottom `List View (2,672)` drawer pill, and clicking any pin opens `show_place_detail_dialog` without `TypeError`.
4. **Map Follow-Route Mode Gate (`TC-05`, `TC-32`, `TC-33`, `TC-34`, `TC-56`)**: Navigating to `/map?itineraryId=draft&day=1` or `/map?itineraryId={id}&day=1` from Suggested Wizard, Custom Builder, or Trip Detail enters `is_follow_route_mode = True`, isolates the active day's numbered stops & OSRM road polyline, shows the Floating Active Route Top Bar (`Back to Plan`, `Browse Map`, `Day 1..N` pills, `Show Nearby POIs`), and shows the Bottom Stop Carousel with `Google Maps Navigation`.
5. **Home Notification Bell & Saved Card Gate (`TC-18`, `TC-22`, `TC-23`)**: Clicking the notification bell on `DashboardView` opens the Travel Advisories modal without `ModuleNotFoundError`, Home displays at most 2 saved itinerary cards, and clicking a saved card opens `TripDetailView`.
6. **Suggested Wizard 3-View & Draft Gate (`TC-35` to `TC-44`)**: Wizard form includes rating chips (`All`, `4.0+`, `4.5+`), initializes budget from `default_daily_budget`, does NOT save to `guest_storage` until `[Accept & Save]` is clicked, displays Verified Budget Card & collapsible Assumptions, filters `Nearby Places` by the active day's municipality, and hands off cleanly to `[Full Map]` and `[Customize in Builder]`.
7. **Custom Builder 3-View & Off-Grid Venue Gate (`TC-45` to `TC-54`)**: Custom Builder supports `form` → `browse` (`✨ Recommended for You` + 16 categories + municipality priority) → `timeline` (Editable Trip Settings card, Verified Budget card, Haversine `Auto-Schedule`, `Edit Stop` with min/max cost & `Move to Day`, and `Add Off-Grid Custom Venue` without `TypeError(latitude=...)`).
8. **Trip Detail Edit & `PATCH /itineraries/{id}` Gate (`TC-57`, `TC-58`)**: Saving edits in `TripDetailView` calls `ItineraryService.update_itinerary(self.itinerary)` without `ImportError`, and `update_itinerary()` sends the full `days` list in `PATCH /api/v1/itineraries/{id}`.
9. **Profile Sync, Settings & Signup M.I. Gate (`TC-03`, `TC-14`, `TC-16`, `TC-60` to `TC-63`)**: `SignupView` passes `middle_initial`, `Itinerary.to_create_payload()` exists, `ProfileView._sync_guest_trips()` calls `await self.auth_service.migrate_guest_trips()` (never deleting unsynced trips with `clear_all()`), and Settings `[Test Connection]` and `[Save URL]` work without `AttributeError` or uncaught `ValueError`.
10. **Clean Codebase Gate (`TC-08`)**: Legacy `sidebar.py`, `header.py`, and `interactive_map.py` (`flet_map`) are removed from active imports.
