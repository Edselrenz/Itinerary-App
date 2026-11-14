# Antigravity Master Development & Remediation Plan v2: Exhaustive Desktop-to-Web Use-Case Parity, Map Performance, Profile Sync & Asset Resolution

**Repository**: `Edselrenz/Itinerary-App` (`feature/flet-desktop-app`)  
**Reference Web Application**: `Project/` (Ionic 9 / Angular 22 / Leaflet 1.9 / TypeScript)  
**Target Desktop Application**: `desktop_client/` (Python 3.12+ / Flet 1.1.2 / `httpx` / PyInstaller)  
**Shared Backend**: `backend/app/` (FastAPI / SQLAlchemy 2.0 / PostgreSQL) & `cloudflare-worker/worker.js`

---

## 1. Root-Cause Diagnosis of All User-Reported Desktop Defects

### 1.1 Why All Assets, Destination Photos, Welcome Art & Default Avatars Are Missing (`exists: False`)
In `desktop_client/assets/`, all image files reside inside **`desktop_client/assets/images/`** (and `desktop_client/assets/images/popular_destinations/`). However:
1. **`desktop_client/config/settings.py:180–189` (`Settings.get_asset_path`)** only checks `self.assets_dir / clean_rel` (`desktop_client/assets/<name>`), **never checking `self.assets_dir / "images" / clean_rel`**!
   - When `profile_view.py:77` calls `self.settings.get_asset_path("default_avatar_placeholder.png")`, it returns `.../desktop_client/assets/default_avatar_placeholder.png` (`exists: False`), whereas the actual file is at `.../desktop_client/assets/images/default_avatar_placeholder.png`!
   - When `welcome_view.py:80, 176, 221, 277` requests `"logout_skyscrapers_blob.png"`, `"welcome_hero_buildings.png"`, and `"logout_cityscape_silhouette.png"`, all three return non-existent paths!
   - When `profile_view.py:991, 996` sets preset avatars to `"assets/guest_hiker_hero.png"` and `"assets/default_avatar_placeholder.png"`, both fail to load!
2. **`desktop_client/config/settings.py:253–298` (`resolve_place_image`) & `desktop_client/models/place.py:173–218` (`Place.resolved_image_path`) Rewrite Paths to a Non-Existent Directory**:
   - Line 259 of `settings.py` runs `rel = clean_url.replace("assets/images/", "popular_destinations/").replace("assets/", "")` and checks `settings.assets_dir / "popular_destinations" / ...`.
   - Lines 274–292 of `settings.py` and lines 190–216 of `models/place.py` map every destination (`minalungao`, `pantabangan`, `highland bali`, `rohi`, `museo de bongabon`, etc.) to `"popular_destinations/<file>.png"`.
   - **Result**: `desktop_client/assets/popular_destinations/` **does not exist**! Those PNGs are actually at **`desktop_client/assets/images/<file>.png`** (and the secondary folder is at `desktop_client/assets/images/popular_destinations/`). Consequently, **100% of destination cards on Home, Map Drawer, Favorites, Suggested Wizard, Custom Builder, and Trip Detail fail to load their photos and fall back to generic blue icons!**

---

### 1.2 Why the Map Is Laggy & Why Filters Throw `module 'flet' has no attribute 'FilterChip'`
1. **`AttributeError: module 'flet' has no attribute 'FilterChip'` (`desktop_client/views/places_view.py:799`)**:
   - In Flet `1.1.2`, `ft.FilterChip` was removed (replaced by `ft.Chip` or custom `ft.Container` pills). Clicking the **Filters** button on the Map tab executes `ft.FilterChip(...)` at `places_view.py:799` and immediately crashes.
   - Furthermore, lines 834–836 of `places_view.py` call `self.safe_page.pop_dialog(); self.safe_page.dialog = dlg; dlg.open = True`, which uses the deprecated Flet 0.21 dialog API instead of `self.safe_page.overlay.append(dlg)`, and the modal omits the **32-Municipality filter selector**.
2. **Why Map Top Category Pills, Search Box & List Count Don't Update Visually (`desktop_client/views/places_view.py:137–177` & `736–748`)**:
   - When a user clicks any of the 17 category pills in `_build_discovery_top_bar()`, `_select_category()` (line 746) sets `self.selected_category = cat_key` and calls `self._apply_filters()`.
   - However, `_apply_filters()` only updates `self.map_component.set_places(self.filtered_places)` and **never rebuilds the top bar (`_build_discovery_top_bar`) or bottom pill (`_build_drawer_toggle_pill`)**!
   - **Result**: Clicking a category pill never changes its active blue highlight (`"All Places"` stays blue forever), typing in the search box never reveals the Clear `[✕]` button, clicking Clear never empties the text input, and the bottom `"List View (2,672)"` pill count never updates to reflect the filtered count!
3. **Why `PlacesView._toggle_drawer()` Crashes When Clicking `"List View (2,672)"` (`places_view.py:450`)**:
   - `_build_poi_drawer()` instantiates `PlaceCard(place=p, compact=True, on_click=...)`, which raises `TypeError: PlaceCard.__init__() got an unexpected keyword argument 'compact'` because `PlaceCard.__init__()` (`place_card.py:16`) does not accept `compact` or `on_click`.
4. **Why `SlippyMapCanvas` Is Severely Laggy on Pan & Zoom (`desktop_client/components/slippy_map_canvas.py`)**:
   - **60 FPS Full-Tree Re-Allocation & 160,000 Trig Calls/Sec**: `_handle_pan_update()` (`slippy_map_canvas.py:318`) fires every `16ms` during mouse drag and calls `self.redraw()`. On every single 16ms drag frame, `_render_markers_and_clusters()` loops over all **2,673 places**, runs `math.sin`/`math.log` Web-Mercator projections 2,673 times, re-runs grid clustering, and instantiates brand-new nested `ft.Container` objects.
   - **2,100 Synchronous Disk `stat()` Calls/Sec**: On every 16ms drag frame, `_render_tiles()` calls `_resolve_tile_source()` for ~35 visible tiles, executing synchronous `os.path.isfile()`, `Path.is_file()`, `mkdir()`, and `stat()` syscalls on the UI thread.
   - **Multi-Thread UI Race Storm**: `_resolve_tile_source()` spawns 6 background threads (`_TILE_EXECUTOR`) that download tiles from `tile.openstreetmap.org` and call `on_ready=self.redraw` (`self.update()`) directly from worker threads, flooding the Flet bridge with concurrent full-tree mutations.
   - **Synchronous 3-Second UI Freeze on Route Maps**: `set_route()` (`slippy_map_canvas.py:258`) calls `fetch_osrm_road_geometry()` using synchronous `httpx.Client(timeout=3.0).get(...)` on the main UI thread, freezing the entire window whenever a day route is rendered.

---

### 1.3 Why Login Succeeds But Profile Picture & Extended Profile Data Are Missing
1. **Default Avatar & Preset Avatars Use Broken Asset Paths (`profile_view.py:77, 991, 996`)**:
   - Because `self.settings.get_asset_path("default_avatar_placeholder.png")` returns a non-existent path (`assets/default_avatar_placeholder.png` instead of `assets/images/default_avatar_placeholder.png`), `ft.Image(src=avatar_src)` always fails and falls back to a generic icon.
2. **`SessionManager.load_session()` Ignores `profile_extra.json` on Startup (`desktop_client/core/session.py:114–126`)**:
   - When the Desktop App starts up with a saved session (`storage/session.json`), `SessionManager.load_session()` constructs `User.from_dict(user_data)` without merging `storage/profile_extra.json`!
3. **`ProfileView` Never Calls `auth_service.get_profile()` on Mount & Hides Extended Profile Fields (`profile_view.py:55–185`)**:
   - `ProfileView` only displays `user.full_name` and `@username` on the identity card—it never displays the user's `email`, `middle_initial` (if not merged), `phone_number`, `birthday`, `gender`, or `default_daily_budget` summary badges on the Profile screen, and lacks an `Account Information` subview / password update section in Settings.
4. **Backend `User` Schema Only Persists Core Auth Fields (`backend/app/models/entities.py` & `backend/app/schemas/auth.py`)**:
   - Currently, the Web App stores `middle_initial`, `phone_number`, `birthday`, `gender`, and `avatar_url` (including uploaded Base64 avatars) exclusively in browser `localStorage` (`ne_profile_extra_${userId}`), while Desktop stores them in `desktop_client/storage/profile_extra.json`.
   - Adding optional `middle_initial`, `phone_number`, `birthday`, `gender`, and `avatar_url` fields to `backend/app/models/entities.py` (`User`), `backend/app/schemas/auth.py` (`UserOut`, `UserUpdateIn`, `UserRegisterIn`), and `backend/app/services/auth_service.py` (with an automatic SQLite/PostgreSQL column check on startup) allows **both Web and Desktop to sync the user's profile picture (`avatar_url`) and extended profile fields through `/api/v1/auth/me`**!
   - In addition, `ProfileView._open_edit_profile_dialog()` should convert selected local avatar image files into a `data:image/png;base64,...` data URI (or copy them into `storage/avatars/`) so the profile picture persists across machines and renders reliably in Flet!

---

### 1.4 Exhaustive Audit of Every Suggested Itinerary Use Case (`UC-S1` to `UC-S6`)

| Use Case | Web App Behavior (`Project/src/app/features/itinerary/suggested-wizard/`) | Desktop App Behavior (`desktop_client/views/suggested_wizard_view.py`) | Root-Cause Bugs Found in Desktop App |
| :--- | :--- | :--- | :--- |
| **`UC-S1`: Entry & Anchor Place Deep-Link** | Clicking `[✨ Start Trip Here]` on any place sheet routes to `/suggested-wizard?destination={muni}&placeId={id}`, locking that place as Stop 1 of Day 1 (`anchor_place_id`). | `dialogs.py:45` calls `on_navigate("/suggested")` with **no query params**. `itinerary_service.py:85` ignores `request.anchor_place_id`. | 1) `dialogs.py:45` drops `destination` and `placeId`.<br>2) `ItineraryService.generate_offline_suggested_itinerary()` ignores `request.anchor_place_id`.<br>3) Returning from Full Map (`[← Back to Plan]`) re-creates `SuggestedWizardView` in `"form"` mode, wiping out `generated_itinerary`! |
| **`UC-S2`: Wizard Form, Date Modal, Budget, Preferences, Travel Mode & Rating** | Form has Destination + 6 quick chips + `All 32 Towns`, Dates (default `today` to `today+2`), Daily Budget input + 4 preset pills (hydrated from `ne_default_budget`), **5 Preference pills** (`nature`, `food`, `culture`, `shopping`, `resort`), **Travel Mode** (`DRIVE`, `TWO_WHEELER`, `WALK`), and **Minimum Rating chips** (`All`, `4.0+ ★`, `4.5+ ★`). | Form uses 16 raw category chips (cannot deselect last chip), hardcodes `budget_val = 2500.0` with no custom number input, omits Minimum Rating chips, and sends `travel_mode="MOTORCYCLE"`. | 1) `date_range_dialog.py:100` resets start date to `today + 3` when clicking `2D/1N`, `3D/2N`, etc., instead of keeping `start_input.value`.<br>2) Missing numeric budget `TextField` and `default_daily_budget` hydration.<br>3) Uses 16 categories instead of the 5 Figma Preference pills.<br>4) Sends `"MOTORCYCLE"` instead of `"TWO_WHEELER"`.<br>5) `min_rating_val` chips are never rendered in `_build_wizard_form()`. |
| **`UC-S3`: Suggested Clustering & Pacing Engine** | Uses `PREFERENCE_CATEGORY_MAP`, filters by `min_rating`, enforces max 1 mountain hike/day, deduplicates fuzzy venue names (`viewdeck`/`viewpoint`) + 200m radius, uses Bongabon cluster presets, and computes Haversine `travel_distance_meters`, `travel_duration_seconds`, and rolling sequential time windows (`09:30 AM - 11:30 AM` + transit). | `itinerary_service.py:85–286` ignores `min_rating` and `anchor_place_id`, has no mountain-hike cap, uses static `time_slots`, and leaves `travel_distance_meters = None` on all items. | 1) Offline generator never filters by `request.min_rating` or `anchor_place_id`.<br>2) Static time slots ignore inter-stop driving durations.<br>3) Day titles are `"Day 1"` instead of `"Day 1: {Municipality}"`. |
| **`UC-S4`: Result Preview, Verified Budget Card, Assumptions, Map & Stop Detail** | Shows Destination Card (`nueva_ecija_arch.png`), **Verified Estimated Costs Card** (`calculateBudgetSummary()`), **Collapsible Assumptions Accordion** with category tags, Day tabs with Municipality names, Photo Stop Cards with rating badges, and clicking any Stop Card opens `PlaceDetailSheet` with its commute guide. | Shows misleading `total_estimated_cost` (treating `None` as `₱0`), non-collapsible 1-line hardcoded assumption text, non-clickable text-only `StopCard` (no photo, no rating), and Day tabs without municipality names. | 1) Missing Verified Estimated Costs Card (`calculate_budget_summary()`).<br>2) Hardcoded 1-line assumption box ignores `itin.assumptions`.<br>3) `StopCard` lacks thumbnail image, rating badge, and `on_click` handler to open `show_place_detail_dialog()`. |
| **`UC-S5`: Nearby Places Discovery (`Restaurants`, `Hospitals`, `Stores`)** | Filters nearby essentials by the **active day's municipality** (`getDayLocationName(curDay)`) across 3 working tabs (`Restaurants`, `Hospital & Pharmacies`, `Stores`) and appends to active day. | `suggested_wizard_view.py:604` sets `cat_arg = "restaurant" if self.nearby_category == "restaurant" else None` and never passes `municipality_name`. | **CRITICAL BUG**: Clicking `Hospitals & Pharmacies` or `Stores & Fuel` passes `category=None` to `get_places()`, returning tourist parks (`Minalungao National Park`) instead of hospitals or stores, and ignores the active day's municipality! |
| **`UC-S6`: Save vs. Customize in Builder Handoff** | `Accept & Save` normalizes `planned_time` via `toBackendIsoTime()`, saves to cloud/guest storage, clears draft, and navigates to the saved itinerary. | `suggested_wizard_view.py:652–704` sends raw `"dest-*"` `place_id` and raw `"09:30 AM - 11:30 AM"` `planned_time`, omits `custom_lat`/`custom_lng`, and stays on the wizard view after saving. | 1) Cloud save fails with FastAPI `422 Unprocessable Content` on non-UUID `place_id` and range `planned_time`.<br>2) Does not navigate to `/trips/{saved.id}` after saving. |

---

### 1.5 Exhaustive Audit of Every Custom Itinerary Use Case (`UC-C1` to `UC-C5`)

| Use Case | Web App Behavior (`Project/src/app/features/itinerary/custom-builder/`) | Desktop App Behavior (`desktop_client/views/custom_builder_view.py`) | Root-Cause Bugs Found in Desktop App |
| :--- | :--- | :--- | :--- |
| **`UC-C1`: Step 1 Setup Form & Date Picker** | Collects `Trip Title`, `Destination` (quick chips + `All 32 Towns`), `Travel Dates` (From/To Date Modal), `Daily Budget` (hydrated from `ne_default_budget` + 4 preset chips), and **5 Preferences pills**. | Clicking **Travel Dates** in Step 1 (`custom_builder_view.py:701`) **crashes immediately**, and Step 1 omits the 5 Preference pills. | 1) **CRASH BUG (`custom_builder_view.py:701`)**: Calls `show_date_range_dialog(self.page, initial_start=..., initial_end=..., on_apply=...)`, raising `TypeError: got an unexpected keyword argument 'initial_start'` (actual params are `current_start, current_end, on_save`).<br>2) Missing 5 Traveler Preferences pills in `_build_form_view()`. |
| **`UC-C2`: Step 2 Browse & Add Places** | Pre-loads all 2,673 POIs (`getLoadedPlaces(dest)`), sorts Step 1 `destination` municipality to the top, filters live on every keystroke (`onBrowseSearch`), offers `All`, `✨ Recommended for You`, and all 16 categories mapped across 8 pills, and opens `PlaceDetailSheet` (with `+ Add to Day N`) on card click. | Search box only triggers on Enter (`on_submit`), category bar only has 6 raw keys (dropping 11 of 16 categories and `✨ Recommended for You`), ignores Step 1 `self.destination`, and `Details` button doesn't pass `on_add_to_day`. | 1) `search_field` lacks `on_change` live filtering and Clear `[✕]` button.<br>2) Category filter drops `tourist_attraction`, `cafe`, `church_religious`, `hotel_accommodation`, `transport_terminal`, `hospital_clinic`, `pharmacy`, `bank_atm`, `fuel_station`, `convenience_store`, `public_facility`, and `✨ Recommended for You`.<br>3) `_load_browse_places()` ignores `self.destination`.<br>4) `show_place_detail_dialog(self.page, place)` in `_build_browse_place_card()` omits `on_add_to_day`. |
| **`UC-C3`: Step 3 Timeline, Settings Card, Budget Card & Reordering** | Top of timeline has **Editable Trip Settings Card** (`Title`, `Budget`, `Start/End Dates`, `Destination`) + **Verified Estimated Costs Card**. Changing dates preserves stops on shortened days. Moving stops Up/Down auto-optimizes schedule times. | Timeline (`_build_timeline_view`) has **no Trip Settings Card** and **no Verified Budget Card**. Shortening dates deletes stops silently. Moving stops Up/Down leaves times out of order. | 1) Missing Editable Trip Settings Card & Verified Budget Card in `_build_timeline_view()`.<br>2) `sync_days_with_date_range()` discards stops from trimmed days instead of moving them to the last retained day.<br>3) `_move_stop()` does not call `_auto_schedule_active_day()` or pass `is_first`/`is_last` to `StopCard`. |
| **`UC-C4`: Off-Grid Custom Venue & Edit Stop Modals** | `Off-Grid Venue` form has Venue Name, Municipality/Address, Min Cost, Max Cost, Planned Time, Duration, Notes, and Optional Collapsible Coordinates (can be left blank). `Edit Stop` validates `min_cost <= max_cost`. | `_open_custom_venue_dialog()` (`custom_builder_view.py:884`) only has Name, Municipality (which is discarded!), and mandatory Lat/Lng. | 1) `_open_custom_venue_dialog()` is missing Min Cost, Max Cost, Planned Time, Duration, and Notes, discards `muni_field.value`, and forces mandatory coordinates.<br>2) `_open_edit_stop_dialog()` does not validate `estimated_cost_min <= estimated_cost_max`. |
| **`UC-C5`: Saving, Editing Existing Trips & `TripDetailView`** | Saving in edit mode calls `PATCH /api/v1/itineraries/{id}`. `ItineraryDetailPage` shows Verified Budget Card, Collapsible Assumptions, clickable Stop Cards (with photos & commute guide), and Nearby Places tab. | `_save_custom_itinerary()` (`custom_builder_view.py:986`) **always calls `create_itinerary()`** (duplicating edited trips), omits `custom_lat`/`custom_lng`, and sends invalid `place_id` / `planned_time`. `TripDetailView` drops `custom_lat`/`custom_lng` and Move-to-Day in edit mode. | 1) `_save_custom_itinerary()` creates duplicate itineraries instead of calling `update_itinerary()` when `self.existing_itinerary` is set.<br>2) `_save_custom_itinerary()` drops `custom_lat`/`custom_lng` and fails FastAPI `422` on non-UUID `place_id`.<br>3) `TripDetailView` lacks Verified Budget Card, Collapsible Assumptions, clickable photo `StopCard`s, Nearby Places view, and catalog place picker in edit mode, and drops `custom_lat`/`custom_lng` and `target_day` when editing stops. |

---

## 2. Complete File-by-File Implementation Plan for Antigravity

### Phase 1: Fix All Asset Paths, Destination Photos & Profile Avatar Resolution (`desktop_client/config/settings.py` & `desktop_client/models/place.py`)

#### 1.1 Update `Settings.get_asset_path()` and `resolve_place_image()` in `desktop_client/config/settings.py`
Replace `get_asset_path()` (lines 180–189) and `resolve_place_image()` (lines 253–298) in `desktop_client/config/settings.py` so they automatically check `assets/images/`, `assets/images/popular_destinations/`, and `assets/`:

```python
    def get_asset_path(self, rel_path: str) -> str:
        """Resolves bundled asset path across assets/, assets/images/, and assets/images/popular_destinations/."""
        if not rel_path:
            return ""
        clean_rel = str(rel_path).strip()
        if clean_rel.startswith(("http://", "https://", "data:image/")):
            return clean_rel
        # If it is already an existing absolute path on disk (e.g. user-picked avatar photo)
        if os.path.isabs(clean_rel) and os.path.isfile(clean_rel):
            return clean_rel

        clean_rel = clean_rel.lstrip("/\\")
        if clean_rel.startswith("assets/"):
            clean_rel = clean_rel[len("assets/"):].lstrip("/\\")

        fname = Path(clean_rel).name
        candidates = [
            self.assets_dir / clean_rel,
            self.assets_dir / "images" / clean_rel,
            self.assets_dir / "images" / fname,
            self.assets_dir / "images" / "popular_destinations" / fname,
            self.assets_dir / "popular_destinations" / fname,
            Path(__file__).resolve().parent.parent.parent / "Project" / "src" / "assets" / clean_rel,
            Path(__file__).resolve().parent.parent.parent / "Project" / "src" / "assets" / "images" / fname,
        ]
        for cand in candidates:
            if cand.is_file():
                return str(cand)
        return str(self.assets_dir / "images" / fname)
```

And replace `resolve_place_image()` in `desktop_client/config/settings.py`:

```python
def resolve_place_image(place_name: str, image_url: str | None = None) -> str | None:
    """Resolves local high-resolution photography path for places across assets/images/ and popular_destinations/."""
    settings = get_settings()
    if image_url:
        clean_url = str(image_url).strip()
        if clean_url.startswith(("http://", "https://", "data:image/")):
            return clean_url
        resolved = settings.get_asset_path(clean_url)
        if resolved and os.path.isfile(resolved):
            return resolved

    name_lower = (place_name or "").lower().strip()
    mapping = {
        "minalungao": "images/minalungao.png",
        "pantabangan lake": "images/pantabangan_lake.png",
        "pantabangan": "images/pantabangan_lake.png",
        "highland bali": "images/highland_bali.png",
        "george point": "images/george_point.png",
        "casa batik": "images/casa_batik.png",
        "tagpuan": "images/tagpuan_gapan.png",
        "lumang gapan": "images/tagpuan_gapan.png",
        "gapan": "images/tagpuan_gapan.png",
        "rohi": "images/rohi_paperflower.png",
        "paperflower": "images/rohi_paperflower.png",
        "museo de bongabon": "images/museo_bongabon.png",
        "bongabon": "images/museo_bongabon.png",
        "thornes": "images/thornes_samgyupsal.png",
        "samgyupsal": "images/thornes_samgyupsal.png",
        "pavilion": "images/pavillion_farm.png",
        "villaronte": "images/farm_villaronte.png",
        "carabao": "images/farm_villaronte.png",
        "la casa prime": "images/la_casa_prime.png",
        "lake farm": "images/lake_farm_marre.png",
        "marre": "images/lake_farm_marre.png",
        "nueva ecija": "images/nueva_ecija_arch.png",
    }
    for kw, rel_path in mapping.items():
        if kw in name_lower:
            p = settings.get_asset_path(rel_path)
            if p and os.path.isfile(p):
                return p

    default_img = settings.get_asset_path("images/minalungao.png")
    return default_img if os.path.isfile(default_img) else None
```

#### 1.2 Simplify `Place.resolved_image_path` in `desktop_client/models/place.py`
Replace `Place.resolved_image_path` (`desktop_client/models/place.py:173–218`) with:
```python
    @property
    def resolved_image_path(self) -> str:
        """Resolves local asset image or network image for this place."""
        from desktop_client.config.settings import get_settings, resolve_place_image
        resolved = resolve_place_image(self.name, self.image_url)
        if resolved:
            return resolved
        return get_settings().get_asset_path("images/minalungao.png")
```

---

### Phase 2: Fix Map Lag (`SlippyMapCanvas`) & Map Filter Crash (`PlacesView`)

#### 2.1 Optimize `desktop_client/components/slippy_map_canvas.py` for 60 FPS Zero-Lag Panning & Non-Blocking Routing
In `desktop_client/components/slippy_map_canvas.py`:
1. **In-Memory Tile Path Resolution Cache (`_TILE_PATH_CACHE`) & CartoDB Voyager OSM Tiles**:
   - Cache resolved local tile file paths in a module-level dict `_TILE_PATH_CACHE: dict[str, str] = {}` so `_render_tiles()` never performs repeated `os.path.isfile()` / `stat()` disk syscalls during mouse drag!
   - Use CartoDB Voyager OSM tiles (`f"https://{sub}.basemaps.cartocdn.com/rastertiles/voyager/{zoom}/{x}/{y}.png"`) as the immediate online tile URL when a tile is not in `assets/tiles/`, and debounce background tile cache callbacks so worker threads never call `self.redraw()` concurrently during a drag!
2. **Pre-Computed Spatial Grid & Throttled Pan Redraw**:
   - Add `import time` and track `self._last_pan_redraw: float = 0.0` in `SlippyMapCanvas.__init__()`.
   - In `_handle_pan_update(self, e: ft.DragUpdateEvent)`:
     ```python
     def _handle_pan_update(self, e: ft.DragUpdateEvent) -> None:
         dx = float(getattr(e, "delta_x", 0.0) or 0.0)
         dy = float(getattr(e, "delta_y", 0.0) or 0.0)
         cx, cy = latlon_to_world_px(self.center_lat, self.center_lng, self.zoom)
         self.center_lat, self.center_lng = world_px_to_latlon(cx - dx, cy - dy, self.zoom)
         now = time.monotonic()
         if now - self._last_pan_redraw >= 0.045:  # Cap redraws at ~22 FPS during drag
             self._last_pan_redraw = now
             self.redraw()
     ```
   - In `_render_markers_and_clusters()`, pre-filter `self._places` by a fast latitude/longitude bounding-box check (`abs(p.latitude - self.center_lat) <= lat_span and abs(p.longitude - self.center_lng) <= lng_span`) **before** calling `math.sin` / `math.log` in `_latlon_to_viewport()`, cutting trigonometric calls per frame by 90%!
3. **Make OSRM Road Geometry Fetching Non-Blocking in `set_route()`**:
   - In `set_route()` (`slippy_map_canvas.py:258`), render the smooth geodesic spline immediately (`generate_geodesic_arc`) so the UI never freezes for 3 seconds, and fetch OSRM road geometry asynchronously in `_TILE_EXECUTOR`, updating `self._route_pts` when it completes!

#### 2.2 Fix `PlacesView` Filter Crash (`ft.FilterChip`), Unresponsive Category Pills & Drawer Crash (`desktop_client/views/places_view.py`)
1. **Fix `_on_search_change()`, `_clear_search()`, and `_select_category()` (`places_view.py:736–748`)**:
   - In `_select_category(self, cat_key: str)`:
     ```python
     def _select_category(self, cat_key: str) -> None:
         self.selected_category = cat_key
         self._apply_filters()
         self._build_content()
         self._safe_update()
     ```
   - In `_clear_search(self)`:
     ```python
     def _clear_search(self) -> None:
         self.search_query = ""
         self._apply_filters()
         self._build_content()
         self._safe_update()
     ```
   - In `_apply_filters(self)`, update the bottom drawer toggle pill text (`self._drawer_pill_text.value = f"List View ({len(self.filtered_places):,})"` if stored on `self`) so the filtered count updates live on every keystroke!
2. **Fix `_open_filter_modal()` (`places_view.py:788–850`) — Replace `ft.FilterChip` with Multi-Select Custom Pills & Add 32-Municipality Dropdown**:
   - Replace `self.selected_category` with `self.selected_categories: set[str] = set()` (keeping `self.selected_category` synchronized for single-pill clicks) so users can select multiple categories in the Filter Modal just like on the Web App (`map.page.ts:selectedCategories`)!
   - Replace `ft.FilterChip(...)` (which crashes in Flet 1.1.2 with `AttributeError: module 'flet' has no attribute 'FilterChip'`) with interactive `ft.Container` filter pills that toggle selection visually inside the dialog (`dlg.update()`).
   - Add a **Municipality `ft.Dropdown`** with `"all"` (`"All 32 Municipalities"`) + `NUEVA_ECIJA_LGUS`.
   - Open the dialog using Flet 1.1.2's `self.safe_page.overlay.append(dlg); dlg.open = True; self.safe_page.update()`.

---

### Phase 3: Fix Profile Picture, Extended Profile Sync & Settings Crash (`backend/`, `session.py`, `auth_service.py`, `profile_view.py`)

1. **Extend Backend `User` Model & Auth Schemas (`backend/app/models/entities.py` & `backend/app/schemas/auth.py`)**:
   - Add optional nullable columns to `User` in `backend/app/models/entities.py`:
     ```python
     middle_initial: Mapped[str | None] = mapped_column(String(16), nullable=True)
     phone_number: Mapped[str | None] = mapped_column(String(40), nullable=True)
     birthday: Mapped[str | None] = mapped_column(String(40), nullable=True)
     gender: Mapped[str | None] = mapped_column(String(32), nullable=True)
     avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
     default_daily_budget: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True, default=3000.0)
     ```
   - Include those optional fields in `UserRegisterIn`, `UserUpdateIn`, and `UserOut` (`backend/app/schemas/auth.py`) and update `register_user()` and `update_user_profile()` in `backend/app/services/auth_service.py` so `PATCH /api/v1/auth/me` and `GET /api/v1/auth/me` persist and return the user's profile picture (`avatar_url`) and extended fields!
2. **Merge `profile_extra.json` in `SessionManager.load_session()` (`desktop_client/core/session.py:114–126`)**:
   - When loading `session.json` on startup, also read `self.settings.storage_dir / "profile_extra.json"` for `user_data.get("id")` and pass `extra=extra` into `User.from_dict(user_data, extra=extra)`.
3. **Convert Picked Avatar Image to Base64 Data URI & Fix Preset Avatars in `desktop_client/views/profile_view.py`**:
   - In `ProfileView._build_content()` (`profile_view.py:77`), resolve `avatar_path = self.settings.get_asset_path("images/default_avatar_placeholder.png")`, and if `user.avatar_url` is a relative asset path (e.g. `"assets/images/..."`), resolve it via `self.settings.get_asset_path(user.avatar_url)`.
   - Display the user's extended profile metadata pills (`Email`, `Phone`, `Birthday`, `Gender`, `Default Budget: ₱{int(user.default_daily_budget):,}/day`) on the `identity_card` in `ProfileView`!
   - When `ProfileView` mounts, asynchronously call `await self.auth_service.get_profile()` so the latest server profile data is fetched after login.
   - In `_open_edit_profile_dialog()` (`profile_view.py:965–978`), when a user selects a local image file in `_pick_photo`, copy the image into `self.settings.storage_dir / "avatars" / Path(f_path).name` (and/or encode as base64) so it remains valid across sessions, and fix the preset buttons (lines 991, 996) to pass `self.settings.get_asset_path("images/guest_hiker_hero.png")` and `self.settings.get_asset_path("images/default_avatar_placeholder.png")`.
   - Fix `ProfileView._test_health()` (`profile_view.py:456`) by replacing `self._run_async(_do_test)` with `if self.safe_page: self.safe_page.run_task(_do_test)`.

---

### Phase 4: Fix All 6 Use Cases of Suggested Itinerary (`desktop_client/views/suggested_wizard_view.py`, `desktop_client/services/itinerary_service.py`, `desktop_client/components/date_range_dialog.py`)

1. **Fix `show_date_range_dialog()` (`desktop_client/components/date_range_dialog.py:10–15` & `100`)**:
   - Accept both `(page, current_start, current_end, on_save)` AND keyword aliases `initial_start: Optional[str] = None, initial_end: Optional[str] = None, on_apply: Optional[Callable[[str, str], None]] = None` so **neither `SuggestedWizardView` nor `CustomBuilderView` ever crashes with `TypeError`!**
   - In `set_preset(num_days: int)` (line 100), anchor the preset duration to the currently entered `start_input.value` (matching Web's `setPresetDuration`) instead of overwriting `start_input` with `today + timedelta(days=3)`:
     ```python
     def set_preset(num_days: int):
         try:
             s = datetime.strptime((start_input.value or "").strip(), "%Y-%m-%d").date()
         except Exception:
             s = today
         e = s + timedelta(days=max(0, num_days - 1))
         start_input.value = s.strftime("%Y-%m-%d")
         end_input.value = e.strftime("%Y-%m-%d")
         _update_duration()
     ```
2. **Upgrade `ItineraryService.generate_offline_suggested_itinerary()` (`desktop_client/services/itinerary_service.py:85–286`)**:
   - **Honor `request.anchor_place_id` (`UC-S1`)**: If `request.anchor_place_id` is set, find that place in `curated_pool` and lock it as Stop 1 of Day 1 (`day_places.append(anchor_place); mark_used(anchor_place)`).
   - **Honor `request.min_rating` (`UC-S2`)**: If `request.min_rating and request.min_rating > 0`, filter candidates with `float(p.get("rating") or 4.5) >= request.min_rating`.
   - **Map the 5 Figma Preference Keys (`PREFERENCE_CATEGORY_MAP`) (`UC-S3`)**:
     ```python
     PREF_MAP = {
         "nature": {"nature_park", "tourist_attraction"},
         "nature & parks": {"nature_park", "tourist_attraction"},
         "food": {"restaurant", "cafe"},
         "food trip": {"restaurant", "cafe"},
         "culture": {"museum_cultural", "church_religious"},
         "culture & history": {"museum_cultural", "church_religious"},
         "shopping": {"shopping_market", "convenience_store"},
         "resort": {"resort_swimming", "hotel_accommodation"},
     }
     ```
   - **Enforce Max 1 Mountain Hike/Day & Fuzzy Venue Name Deduplication (`UC-S3`)**: Strip `"viewdeck"`, `"viewpoint"`, `"resort"`, `"park"`, `"hotel"`, `"cafe"`, `"restaurant"` when normalizing venue names, and prevent scheduling more than 1 `"mt."`/`"mount "` stop per day.
   - **Calculate Rolling Sequential Time Windows & Leg Distances (`UC-S3`)**: Compute Haversine driving distances (`travel_distance_meters = int(dist * 1.28)`) and durations (`travel_duration_seconds = int(dist * 1.28 / 11.11)`) between consecutive stops, set rolling non-overlapping `planned_time` strings (`09:30 AM - 11:30 AM`, `12:00 PM - 01:30 PM`, `02:30 PM - 04:30 PM`), and set `title=f"Day {d_idx + 1}: {primary_muni}"`.
3. **Upgrade `SuggestedWizardView` (`desktop_client/views/suggested_wizard_view.py`) to Match Web 1:1**:
   - **Pre-Save Draft Restoration (`UC-S1` / `GAP-03`)**: In `__init__`, if `not anchor_place_id` and `self.itinerary_service.get_active_draft_itinerary()` exists, restore `self.generated_itinerary = existing_draft` and `self.view_mode = "itinerary"` so clicking `[← Back to Plan]` from Full Map returns directly to the generated itinerary!
   - **Wizard Form Parity (`UC-S2`)**:
     - Default `start_date_val = today.strftime("%Y-%m-%d")` and `end_date_val = (today + timedelta(days=2)).strftime("%Y-%m-%d")`.
     - Hydrate `self.budget_val` from `get_session_manager().current_user.default_daily_budget` (`3000.0` default) and include **both** a numeric `Daily Budget (₱)` `TextField` and the 4 preset pills (`₱1,500`, `₱2,500`, `₱4,000`, `₱6,000`).
     - Use the **5 Figma Preference pills** (`Nature & Parks`, `Food Trip`, `Culture & History`, `Shopping`, `Resort`) and allow toggling any pill on/off freely (even 0 selected).
     - Use the **3 Web Travel Mode options** (`("DRIVE", "Drive / Car")`, `("TWO_WHEELER", "Motorcycle / Tricycle")`, `("WALK", "Walking / Transit")`).
     - Render the **Minimum Place Rating Chips** (`All Ratings`, `4.0+ ★`, `4.5+ ★`).
   - **Result View Parity (`UC-S4`)**:
     - Render the **Verified Estimated Costs Card** (`self.itinerary_service.calculate_budget_summary(itin)`) showing the verified cost range and unpriced stop count badge.
     - Render a **Collapsible Trip Assumptions & Travel Notes Accordion** (`self.is_assumptions_expanded`) with category tags (`Pacing`, `Routing`, `Budget`, `Schedule`) parsed from `itin.assumptions`.
     - Show the municipality name on each Day Switcher capsule (`Day 1 • Bongabon`) and in the Day Header (`Day 1 — Bongabon`).
     - Pass `on_click=lambda itm: self._open_stop_detail(itm)` to `StopCard`, and update `StopCard` (`desktop_client/components/stop_card.py`) to display the place's **thumbnail image (`resolved_image_path`)**, **star rating badge**, and **clickable card surface**!
   - **Nearby Places View Parity (`UC-S5`)**:
     - Fix `_load_nearby_amenities()` (`suggested_wizard_view.py:595–618`) so it extracts the active day's municipality (`active_muni`) and filters by category group:
       - `"restaurant"` -> `categories=["restaurant", "cafe"]`
       - `"hospital"` -> `categories=["hospital_clinic", "pharmacy"]`
       - `"store"` -> `categories=["convenience_store", "shopping_market", "fuel_station"]`
   - **Save & Handoff Parity (`UC-S6`)**:
     - In `_save_generated_itinerary()`, call `payload = self.generated_itinerary.to_create_payload()` (which sanitizes non-UUID `place_id` values and converts `planned_time` via `to_backend_iso_time()`), save via `saved = await self.itinerary_service.create_itinerary(payload)`, clear `self.itinerary_service.set_active_draft_itinerary(None)`, and navigate to `self.on_navigate(f"/trips/{saved.id}", saved)`.

---

### Phase 5: Fix All 5 Use Cases of Custom Itinerary & `TripDetailView` (`desktop_client/views/custom_builder_view.py` & `desktop_client/views/trip_detail_view.py`)

1. **Fix Step 1 Questionnaire Form (`UC-C1` in `custom_builder_view.py`)**:
   - Fix `_open_date_picker()` (line 701) to call `show_date_range_dialog(self.page, self.start_date_str, self.end_date_str, _on_dates)`.
   - Hydrate `self.daily_budget` from `get_session_manager().current_user.default_daily_budget` (`3000.0` default).
   - Add the **5 Traveler Preferences Pills** (`Nature & Parks`, `Food Trip`, `Culture & History`, `Shopping`, `Resort`) to `_build_form_view()`.
   - If `pre_added_place` was passed from Map/Home, display a dismissible `"Place Pre-Loaded: {pre_added_place.name} was added to Day 1"` banner at the top of the builder.
2. **Fix Step 2 Browse & Add Places (`UC-C2` in `custom_builder_view.py`)**:
   - Bind `on_change=lambda e: self._on_browse_search(e.control.value)` on `search_field` (with a Clear `[✕]` icon button) so searching filters live as the user types!
   - Expand category pills to match the Web App's 8 groups covering all 16 canonical categories:
     - `"All"` -> all 16 categories
     - `"✨ Recommended for You"` -> categories matching `self.preferences`
     - `"Tourist Spots"` -> `["tourist_attraction", "nature_park"]`
     - `"Food"` -> `["restaurant", "cafe"]`
     - `"Resorts & Stays"` -> `["resort_swimming", "hotel_accommodation"]`
     - `"Culture & Heritage"` -> `["church_religious", "museum_cultural"]`
     - `"Shopping"` -> `["shopping_market", "convenience_store"]`
     - `"Transit & Essentials"` -> `["transport_terminal", "hospital_clinic", "pharmacy", "bank_atm", "fuel_station", "public_facility"]`
   - In `_load_browse_places()`, load from all 2,673 places (`self.place_service.get_loaded_places()`), filter by the selected category group and search query, and **sort places matching `self.destination` to the top** (`C-BUG-03`)!
   - In `_build_browse_place_card()`, make the card and `Details` button call `show_place_detail_dialog(self.page, place, on_add_to_day=lambda pl: self._toggle_place_in_active_day(pl), on_navigate=self.on_navigate)`.
3. **Fix Step 3 Timeline Builder, Editable Settings Card & Non-Destructive Date Sync (`UC-C3` in `custom_builder_view.py`)**:
   - In `sync_days_with_date_range()` (line 129), if the new date range has fewer days than `len(self.days)`, **move any scheduled stops from the trimmed trailing days into the last retained day** (`new_days[-1].items.extend(trimmed_day.items)`) so shortening trip dates never deletes user stops!
   - At the top of `_build_timeline_view()`, render:
     1. **Editable Trip Settings Card**: Inline `Trip Title` input, `Daily Budget (₱)` input, `Destination` input, and clickable `Travel Dates` button (`_open_date_picker`).
     2. **Verified Estimated Costs Card**: Displaying `self.itinerary_service.calculate_budget_summary(...)`.
   - Show the municipality name on each Day tab (`Day 1 • Cabanatuan City`).
   - Pass `is_first=(idx == 0)` and `is_last=(idx == len(active_day.items) - 1)` to `StopCard`, and in `_move_stop()`, call `self._auto_schedule_active_day()` after swapping stops so schedule times automatically update in chronological order!
4. **Fix Off-Grid Custom Venue & Edit Stop Modals (`UC-C4` in `custom_builder_view.py`)**:
   - In `_open_custom_venue_dialog()` (line 884), include all Web App fields: `Venue Name *`, `Municipality or Address`, `Est. Min Cost (₱)`, `Est. Max Cost (₱)`, `Planned Time`, `Duration (mins)`, `Personal Travel Notes`, and **Optional** `Latitude` / `Longitude` (if left blank, set `custom_lat=None, custom_lng=None`; if provided, validate Nueva Ecija bounds `15.10..16.25`, `120.65..121.50` and `min_cost <= max_cost`).
   - In `_open_edit_stop_dialog()` (line 815), validate `estimated_cost_min <= estimated_cost_max` and show an error message if `min > max`.
5. **Fix Custom Builder Save & `TripDetailView` Parity (`UC-C5` in `custom_builder_view.py` & `trip_detail_view.py`)**:
   - In `CustomBuilderView._save_custom_itinerary()` (`custom_builder_view.py:953`), construct an `Itinerary` object with `self.days`:
     - If `self.existing_itinerary and not self.is_draft_from_wizard and self.existing_itinerary.id != "draft"`, update `self.existing_itinerary` and call `saved = await self.itinerary_service.update_itinerary(self.existing_itinerary)` (`PATCH /api/v1/itineraries/{id}`).
     - Otherwise, call `saved = await self.itinerary_service.create_itinerary(itin_obj.to_create_payload())` (`POST /api/v1/itineraries`).
   - In `TripDetailView` (`desktop_client/views/trip_detail_view.py`):
     - Add the **Verified Estimated Costs Card**, **Collapsible Assumptions Accordion**, and **`[📍 Nearby Places]` button & view mode** to `_build_view_mode()`.
     - Pass `on_click` to `StopCard` in `_build_view_mode()` so clicking any stop opens `show_place_detail_dialog()`.
     - Add a **`[🛠️ Open in Full Builder]`** button alongside inline edit mode, and in inline edit mode:
       - Pass `custom_lat=venue_data.get("latitude")` and `custom_lng=venue_data.get("longitude")` in `_open_add_custom_stop()`.
       - Pass `available_days=[d.day_number for d in self.itinerary.days]` and `current_day=active_day.day_number` in `_edit_stop()`, moving the stop across days when `data.get("target_day") != active_day.day_number`.

---

## 3. Exhaustive 72-Test-Case Desktop vs. Web Verification Matrix

Antigravity must verify all **72 test cases** across the 8 system modules before marking the remediation complete:

| Test ID | Module | Test Case Description | Web Reference | Desktop Target |
| :--- | :--- | :--- | :--- | :--- |
| **`TC-01`–`TC-06`** | **1. App Shell & Connectivity** | Cold-start splash (`loading_screen.jpg` resolved from `assets/images/`), 4-tab bottom bar (`Home`, `Map`, `Saved`, `Profile`), non-expanding `OfflineHostBanner` (`height=52`), `ngrok-skip-browser-warning` header, `502/503/504` gateway offline detection, and Cloudflare Worker failover. | `app.component.ts`, `auth.interceptor.ts`, `connectivity.service.ts` | `main.py`, `splash_overlay.py`, `offline_banner.py`, `api_client.py`, `connectivity_service.py` |
| **`TC-07`–`TC-14`** | **2. Auth, Login, Signup & Guest** | Welcome screen hero images (`logout_skyscrapers_blob.png`, `welcome_hero_buildings.png` resolved from `assets/images/`), Guest onboarding (`guest_hiker_hero.png`), Signup `M.I.` & auto-username, Login `remember_me`, concurrent `401` refresh lock (excluding `/auth/*`), and automatic `migrate_guest_trips()` after login/signup. | `welcome.page.ts`, `guest.page.ts`, `login.page.ts`, `signup.page.ts`, `auth.service.ts` | `welcome_view.py`, `guest_view.py`, `login_view.py`, `signup_view.py`, `auth_service.py` |
| **`TC-15`–`TC-22`** | **3. Home Dashboard & Search** | Popular Destinations photos (`exists: True` for all 13 curated places), `See all` catalog modal with LGU filter pills, 300ms debounced search with Clear `[✕]`, Notification Bell modal (`get_guest_storage`), max 2 Saved Itinerary preview cards, and clicking a Saved Itinerary card opens `TripDetailView` without `TypeError`. | `home.page.ts`, `home.page.html` | `dashboard_view.py`, `settings.py`, `models/place.py` |
| **`TC-23`–`TC-34`** | **4. Map Explorer & Route Mode** | Zero-lag pan/zoom (`_TILE_PATH_CACHE` + 22fps drag throttle + bbox pre-filter + CartoDB Voyager OSM tiles), clicking top Category pills highlights active pill & updates `List View (N)` count, clicking `Filters` opens Multi-Select Category + 32-LGU + Price Tier modal without `ft.FilterChip` `AttributeError`, clicking `List View (N)` opens POI Drawer without `PlaceCard(compact=True)` `TypeError`, `[✨ Live OSM]` queries Overpass API, and `Follow-Route Mode` isolates day stops & returns to `/suggested` or `/builder` on `[← Back to Plan]`. | `map.page.ts`, `map.page.html`, `osm-overpass.service.ts` | `places_view.py`, `slippy_map_canvas.py`, `place_card.py`, `place_service.py` |
| **`TC-35`–`TC-48`** | **5. Suggested Itinerary Wizard (`UC-S1`–`UC-S6`)** | Deep-link `/suggested?destination=...&placeId=...` locks Stop 1 (`UC-S1`); pre-save draft restored when returning from Full Map (`GAP-03`); Date Picker presets keep chosen start date (`UC-S2`); Daily Budget input + 4 presets hydrated from `default_daily_budget`; 5 Figma Preference pills; `DRIVE`/`TWO_WHEELER`/`WALK` modes; `All`/`4.0+`/`4.5+` Rating chips; offline generator respects `min_rating`, `anchor_place_id`, 1-hike/day cap, and rolling transit times (`UC-S3`); Result view shows Verified Budget Card, Collapsible Assumptions, Municipality on Day tabs, and clickable Photo `StopCard`s (`UC-S4`); Nearby Places filters by active day's municipality across `Restaurants`, `Hospitals & Pharmacies`, and `Stores` (`UC-S5`); `Accept & Save` sanitizes `place_id`/`planned_time` and routes to `/trips/{id}` (`UC-S6`). | `suggested-wizard.page.ts`, `suggested-wizard.page.html`, `itinerary.service.ts` | `suggested_wizard_view.py`, `itinerary_service.py`, `date_range_dialog.py`, `stop_card.py` |
| **`TC-49`–`TC-62`** | **6. Custom Itinerary Builder (`UC-C1`–`UC-C5`)** | Step 1 Date Picker opens without `initial_start` `TypeError` (`UC-C1`); Step 1 includes 5 Preference pills & `default_daily_budget`; Step 2 searches live on keystroke (`on_change`), includes `✨ Recommended for You` & all 16 categories across 8 pills, sorts Step 1 `destination` to top, and allows adding from `Details` modal (`UC-C2`); Step 3 renders Editable Trip Settings Card & Verified Budget Card, preserves stops when shortening dates, and auto-schedules times on Up/Down reorder (`UC-C3`); Off-Grid Custom Venue modal includes Min/Max Cost, Time, Duration, Notes, and optional coordinates (`UC-C4`); Saving an edited itinerary calls `PATCH /api/v1/itineraries/{id}` (`update_itinerary`) and preserves `custom_lat`/`custom_lng` (`UC-C5`). | `custom-builder.page.ts`, `custom-builder.page.html` | `custom_builder_view.py`, `date_range_dialog.py`, `models/itinerary.py` |
| **`TC-63`–`TC-67`** | **7. Saved Trips & Trip Detail** | Segment filters (`All`, `Upcoming`, `Past`, `Suggested`, `Custom`), `TripDetailView` Verified Budget Card, Collapsible Assumptions, clickable Photo `StopCard`s, Nearby Places view, and In-Place Edit preserving `custom_lat`/`custom_lng` and Move-to-Day (`target_day`). | `history.page.ts`, `itinerary-detail.page.ts` | `saved_trips_view.py`, `trip_detail_view.py`, `dialogs.py` |
| **`TC-68`–`TC-72`** | **8. Profile, Avatar Sync & Settings** | Default avatar & preset avatars load from `assets/images/`; uploaded avatar & extended fields (`middle_initial`, `phone_number`, `birthday`, `gender`, `default_daily_budget`) persist in `profile_extra.json` + `session.py` + backend `/api/v1/auth/me`; Settings `[Test Connection]` runs via `safe_page.run_task()` without `_run_async` `AttributeError`. | `profile.page.ts`, `profile.page.html` | `profile_view.py`, `session.py`, `auth_service.py`, `backend/app/models/entities.py` |

---

## 4. Verification Commands for Antigravity

Execute the following commands after implementing Phases 1–5 to verify zero regressions:

```bash
# 1. Verify all asset paths resolve to existing files on disk
python3 -c "
import os
from desktop_client.config.settings import get_settings
from desktop_client.core.offline_data import CANONICAL_OFFLINE_PLACES
from desktop_client.models.place import Place
st = get_settings()
for name in ['default_avatar_placeholder.png', 'logout_skyscrapers_blob.png', 'welcome_hero_buildings.png', 'guest_hiker_hero.png']:
    p = st.get_asset_path(name)
    assert os.path.isfile(p), f'Missing asset: {name} -> {p}'
for cp in CANONICAL_OFFLINE_PLACES:
    pl = Place.from_dict(cp.to_dict())
    assert os.path.isfile(pl.resolved_image_path), f'Missing place photo: {pl.name} -> {pl.resolved_image_path}'
print('ALL ASSETS VERIFIED OK!')
"

# 2. Verify zero forbidden Flet 0.21 APIs remain in desktop_client/
! grep -rn "FilterChip\|ChoiceChip\|_run_async\|muni_name_resolved" desktop_client/

# 3. Run Desktop & Backend test suites
PYTHONPATH=. pytest desktop_client/tests/ -v
PYTHONPATH=backend pytest backend/tests/ -v
```