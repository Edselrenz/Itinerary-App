# Nueva Ecija Travel App ("Trip mo, trip ko") — Deep Desktop vs. Web App Re-Evaluation, QA Audit & Antigravity Implementation Plan (v2)

**Skills Applied**: `@coding-and-system-development` | `@anti-generic-frontend-design`  
**Reference Web Application**: `Project/` (Ionic 9 + Angular 22 + Leaflet 1.9.4 + MarkerCluster + Capacitor 8)  
**Target Desktop Application**: `desktop_client/` (Python Flet >= 1.1.2 + `flet-map` + httpx + Pydantic 2.10)  
**Shared Backend API**: `backend/` (FastAPI at `http://127.0.0.1:8000/api/v1`)  
**Audit Date**: November 14, 2026

---

## 1. Antigravity Master Directive & Core Corrections

Act as a Senior Python Flet Engineer, GIS/Map Integration Architect, Senior UI/UX Designer, and QA Lead governed by `@coding-and-system-development` and `@anti-generic-frontend-design`.

### Why the Previous Desktop Implementation & QA Failed
The previous desktop build and its `DESKTOP_APP_DOCUMENTATION/03_QA_QC_REPORT.md` claimed "100% feature parity" while failing 6 fundamental product requirements:
1. **Layout Is Still a Side Menu (`SidebarNav` + `TopHeader`)**: The Web App uses a **4-Tab Bottom Navigation Bar (`.custom-tab-bar`: `Home`, `Map`, `Saved`, `Profile`)** on core tab screens and hides the tab bar on full-screen workflow views (`/welcome`, `/guest`, `/login`, `/signup`, `/suggested-wizard`, `/custom-builder`, `/itinerary/:id`) which use their own `.figma-header-bar` (`←` back button + title + action). The desktop app's `250px` dark-navy left side menu (`components/sidebar.py`) and `64px` top header (`components/header.py`) make it look and work like a generic enterprise admin dashboard and destroy in-progress wizard/builder state on navigation. **Delete the side menu layout and use the exact Bottom Tab Bar + Contextual Top Header architecture of the Web App.**
2. **Zero Map Creation**: The previous QA (`03_QA_QC_REPORT.md` and `09_KNOWN_LIMITATIONS.md`) skipped building the map entirely. In the Web App, the interactive map is the core of **two major modules**: (a) the full-screen **Map Tab (`/tabs/map`)** with OpenStreetMap tiles, category-colored teardrop pins, marker clustering, viewport search/filter, collapsible POI list drawer, and Follow-Route navigation mode; and (b) the **Embedded Day Route Map (`ItineraryRouteMapComponent`)** inside `SuggestedWizardPage`, `CustomBuilderPage`, and `ItineraryDetailPage` showing numbered stop pins (`1, 2, 3...`) and decoded road/geodesic polylines. **The desktop app must implement both interactive maps using `flet-map` (`flet_map`) + interactive canvas fallback.**
3. **Cannot See Server Connection Status Like the Web App**: In the Web App (`app.component.html` + `connectivity.service.ts`), whenever the backend is unreachable, a **Global Top Floating Offline Mode Banner (`.offline-host-banner`)** slides down across any screen with an amber cloud-offline icon, `"Offline Mode — Cloud sync paused. Your saved trips and curated destinations remain accessible."`, an active **`[Retry]` button** (with spinner and top toast feedback `"Connected to backend server! Reloading data..."` vs. `"Server is currently offline..."`), and a **`[X]` dismiss button**, alongside a live status dot and Custom API URL setting in `Profile → Settings`. In the desktop app, `welcome`, `login`, and `signup` had no connection indicator at all, and `api_client.check_health_sync()` hardcoded a raw socket to `("127.0.0.1", 8000)` with no retry button, no toast, and no URL override.
4. **No Proper Offline Fallback**: When the FastAPI backend is offline, the desktop app throws `NetworkError` and shows **0 places** on Home, Search, Map, and Custom Builder, and **completely blocks Suggested Itinerary generation** with a red error banner. In contrast, the Web App seamlessly falls back across 3 tiers: (a) loading the **2,673 bundled OpenStreetMap POIs (`Project/src/assets/data/osm_places.json`)** + **10 Curated Featured Places (`offline-places.data.ts`)** in `PlaceService`; (b) running the **Deterministic Offline Suggested Itinerary Clustering Engine (`generateOfflineSuggestedItinerary`)** in `ItineraryService`; and (c) falling back to `GuestStorage` when authenticated writes fail offline.
5. **Redundant Demo Account & Non-Functional Google/Apple Buttons**: Having an active `"Explore Demo Account (Pattranite Persona)"` when there is already a full **Guest Account (`Continue as Guest`)** is redundant and confusing (and `profile.page.html` even leaked `'Pattranite Limpatiyakorn'` / `'loverrukk'` as fallback strings). Furthermore, the **Google** and **Apple** social login buttons on Login and Signup are dead buttons that only show a `"disabled in this pilot build"` toast, violating `@anti-generic-frontend-design` Section 2 (*"Buttons that do nothing / Decorative controls that appear interactive but are not functional"*). **Remove the Demo Account and remove the Google and Apple buttons completely.**
6. **8 Uncaught Code-Level Runtime Crashes**: `SavedTripsView` crashes with `AttributeError: 'Itinerary' object has no attribute 'total_days'`; `PlacesView._fetch_places()` passes invalid kwargs (`municipality`, `sort_by`) raising `TypeError` on every call; `ProfileView._sync_guest_trips()` crashes with `AttributeError: 'AuthService' object has no attribute 'migrate_guest_trips'`; `ItineraryService.generate_suggested_itinerary()` misses `ApiClientError` import (`NameError`); `DashboardView` saved-trip cards fail to pass `trip_data` to `main.py`; `LoginView`/`SignupView`/`ProfileView` call bare `asyncio.run()` inside Flet's running event loop (`RuntimeError`); Dark Mode leaves all views hardcoded to Light Mode colors; and `+ Add to Trip` discards the selected place.

---

## 2. Comprehensive Comparison Matrix: Web App vs. Desktop App

| Feature / Architectural Layer | Web App Behavior (`Project/src/app/`) | Current Desktop App (`desktop_client/`) | Required Desktop Target (100% Parity + Clean Auth) |
| :--- | :--- | :--- | :--- |
| **1. App Launch Splash Screen** | Full-screen splash (`loading_screen.jpg`), rotated airplane + `"Trip mo, trip ko"`, tagline, pulsing `"Tap or swipe to enter"`, auto-dismisses after 2.8s or on click/Esc (`app.component.html`). | **Missing.** Launches straight into `/welcome` or `/dashboard`. | Implement `SplashOverlay` in `main.py` using `Project/src/assets/images/loading_screen.jpg` with 2.8s auto-dismiss and click/Esc dismiss. |
| **2. Primary Navigation Shell** | **Bottom Tab Bar (`.custom-tab-bar`, `60px` height)** with 4 tabs (`Home`, `Map`, `Saved`, `Profile`). Hidden on `/welcome`, `/guest`, `/login`, `/signup`, `/suggested-wizard`, `/custom-builder`, `/itinerary/:id`. | **250px Left Side Menu (`SidebarNav`) + 64px `TopHeader`** on all screens; resets view instances on click. | **Delete `SidebarNav` and `TopHeader`.** Implement `BottomTabBar` (`height=60`) shown ONLY on `/home`, `/map`, `/saved`, `/profile`. Use contextual `.figma-header-bar` on workflow screens. |
| **3. Server Connectivity Indicator** | **Global Floating Top Offline Banner (`.offline-host-banner`)** on all screens when `GET /api/v1/health` fails, with `[Retry]` button (spinner + toast) and `[X]` dismiss (`app.component.html`, `connectivity.service.ts`), plus Settings status dot & custom API URL. | Static pill in `TopHeader` (invisible on Welcome/Login/Signup); hardcoded `127.0.0.1:8000` socket check; no `[Retry]` button, no toast, no custom API URL. | Implement `ConnectivityService` (`GET {active_api_url}/health`) + Global Floating `OfflineHostBanner` overlaid at top of `page` across all routes with `[Retry]` & `[X]`, plus Settings API URL config. |
| **4. Offline Fallback Architecture** | **3-Tier Fallback**: (1) `PlaceService` loads `osm_places.json` (2,673 POIs) + `CANONICAL_OFFLINE_PLACES`; (2) `ItineraryService` runs `generateOfflineSuggestedItinerary()` clustering; (3) Authenticated writes fall back to `GuestStorage` on network error. | **Zero Fallback.** `ApiClient` raises `NetworkError` when offline; Home, Map, Search, and Builder show 0 places; Suggested Wizard fails with red error banner. | Port all 3 fallback tiers into `desktop_client`: load `osm_places.json` (2,673 POIs) + `CANONICAL_OFFLINE_PLACES`, port `generate_offline_suggested_itinerary()`, and fallback authenticated writes to `guest_storage.json`. |
| **5. Auth, Demo & Social Buttons** | Has Email/Password Login, Signup, Guest Mode (`/guest`), `Forgot password?` modal, plus pilot-disabled Google/Apple buttons and redundant `Pattranite` Demo Account. | Missing `/guest` screen, `Forgot password?`, and `Username` field; ignores `M.I.` field; crashes on `asyncio.run()`. | Keep **Email/Password Log In**, **Sign Up** (with `Username` + `M.I.`), **`Forgot password?` modal**, and **Guest Mode (`/guest`)**. **Strictly omit Demo Account (`Pattranite`) and omit Google/Apple buttons.** |
| **6. Interactive Map Tab (`/map`)** | Full-screen Leaflet map (`[15.58, 121.0]`, bounds `[[15.05, 120.55], [16.25, 121.55]]`), OSM tiles, category-colored teardrop pins, clustering, floating search + `Filters` modal + 17 category pills, floating `Live OSM`, `Locate`, `Recenter`, `List View (N)` drawer, POI bottom sheet, and Follow-Route mode (`map.page.ts`). | **No map exists.** `places_view.py` is a broken 3-column card grid that always shows 0 places due to `TypeError` (`BUG-02`). | Replace `places_view.py` with `MapView` powered by `flet_map` (`Map`, `TileLayer`, `MarkerLayer`, `PolylineLayer`) + interactive canvas fallback, replicating all overlays, drawers, filters, and Follow-Route mode. |
| **7. Embedded Day Route Map** | `ItineraryRouteMapComponent` (`180px` collapsible map card) inside `SuggestedWizardPage`, `CustomBuilderPage`, and `ItineraryDetailPage` with numbered stop pins (`1, 2, 3...`), OSRM/decoded/geodesic polyline, and `[Full Map]` button. | **Completely missing** in `suggested_wizard_view.py`, `custom_builder_view.py`, and `trip_detail_view.py`. | Create `ItineraryRouteMap` component (`desktop_client/components/itinerary_route_map.py`) and embed it inside every active day of Suggested Wizard, Custom Builder, and Trip Detail. |
| **8. Suggested Itinerary Wizard** | 3-view state machine (`form` → `itinerary` → `nearby`), 32-LGU Autocomplete + Quick Chips + All 32 Towns District Modal, Date Picker Modal (`From`/`To` + presets), Budget input + presets, 5 Preference pills, Travel Mode (`DRIVE`/`TWO_WHEELER`/`WALK`), Min Rating, preview-first (`save_immediately=False`), Verified Budget Card, Assumptions Box, Day Capsule Bar, Route Map, Leg Commute Badges, Nearby Places (`Restaurants`/`Hospitals`/`Stores`), `[Accept & Save]` + `[Customize in Builder]`. | Destination hardcoded to read-only `"Nueva Ecija"`; raw date strings; no autocomplete; no Travel Mode/Rating; saves immediately; missing Verified Budget, Assumptions, Route Map, Leg Commute Badges, Nearby Places, and `Customize in Builder`. | Rebuild `SuggestedWizardView` to match the Web App's exact 3-view flow, components, and offline clustering fallback. |
| **9. Custom Itinerary Builder** | 3-stage guided flow (`form` → `browse` → `timeline`), 32-LGU Autocomplete, Date Picker Modal (auto-creating Day 1..N), stateful `+ Add` / `✓ Added` buttons, `[Auto-Schedule]`, `[Delete Day]`, Route Map, Leg Commute Badges, `Move to Day` in Edit Stop, and geofenced Lat/Lng (`15.15–16.15`, `120.70–121.40`) + Address in Off-Grid modal. | Static split pane hardcoded to 2 days; no setup form; no `[Auto-Schedule]`; no `[Delete Day]`; no `✓ Added` toggle; no `Move to Day`; no Lat/Lng or Address in Off-Grid modal; discards pre-added place (`BUG-08`). | Rebuild `CustomBuilderView` to support Stage 1 setup, pre-loaded place banner, edit-existing-itinerary mode, stateful `+ Add` / `✓ Added`, `[Auto-Schedule]`, `[Delete Day]`, `Move to Day`, and geofenced custom coordinates. |
| **10. Saved Trips & Trip Detail** | `HistoryPage` with search, 5 segment pills (`All`, `Upcoming`, `Past`, `Suggested`, `Custom`), `X Days, Y Nights` pill. `ItineraryDetailPage` with **In-Place Edit Mode**, Verified Budget Card, Assumptions, Day Route Metrics, `[In-App Nav]`, `[Google Maps]` multi-stop route, Embedded Route Map, Leg Commute Badges, Nearby Places, and Share/Export modal (`.ics`, Copy Text, Print/PDF). | `SavedTripsView` crashes on `itin.total_days` (`BUG-01`); `TripDetailView` is a read-only stub with no Edit Mode, no route map, no route metrics, no leg commute badges, no multi-stop Google Maps link, and no Nearby Places. | Fix `BUG-01` and upgrade `TripDetailView` with full In-Place Edit Mode, Embedded Route Map, Day Route Metrics, Multi-Stop Google Maps launcher, Leg Commute Badges, Nearby Places, and 4-option Share/Export modal. |
| **11. Profile & Subviews** | 6-view hub (`profile`, `settings`, `edit`, `favorites`, `help`, `about`), 5-row Figma Menu Card, `FavoritesService` (seeded with 3 places), 7-field Edit Profile with Avatar upload, Help FAQs + Nueva Ecija Emergency Hotlines, and Figma Exit-Door Logout Modal. | Crashes on `"Sync Now"` (`BUG-03`); missing `Favorites`, `Help & Support`, `About`, `Password Change`, `Language`, and 6 of 7 profile fields; Dark Mode broken (`BUG-07`). | Implement all 6 Profile subviews, `FavoritesService`, `migrate_guest_trips()`, 7-field Edit Profile (with no hardcoded `'Pattranite'` strings), Figma Logout Modal, and reactive Light/Dark theme tokens. |

---

## 3. Deep QA Audit: All 14 Confirmed Defects (`QA-01` to `QA-14`)

### 3.1 Architectural, Layout & UX Defects (`QA-01` to `QA-06`)

* **QA-01 (Critical — Side Menu Layout Instead of Web App Bottom Tab Bar)**:
  * **Files**: `desktop_client/main.py` (Lines 75–128), `desktop_client/components/sidebar.py`, `desktop_client/components/header.py`.
  * **Defect**: The desktop app wraps views in a `250px` left `SidebarNav` and `64px` `TopHeader` instead of the Web App's `60px` bottom `.custom-tab-bar` (`Home`, `Map`, `Saved`, `Profile`) and full-screen workflow headers (`.figma-header-bar`). Furthermore, `main.py` instantiates fresh view objects on every route switch, wiping out unsaved wizard/builder drafts without a `pendingChangesGuard` prompt.
* **QA-02 (Critical — Complete Absence of Interactive Map & Embedded Route Map)**:
  * **Files**: `desktop_client/views/places_view.py`, `suggested_wizard_view.py`, `custom_builder_view.py`, `trip_detail_view.py`, `requirements.txt`.
  * **Defect**: Neither the full-screen interactive provincial map (`/tabs/map` with OSM tiles, category teardrop pins, clustering, floating filters, POI drawer, and Follow-Route mode) nor the `180px` embedded day route preview map (`ItineraryRouteMapComponent` with numbered stop pins and route polylines) was created.
* **QA-03 (Critical — Missing Web-Style Server Connection Banner, Retry Action & Health Endpoint Check)**:
  * **Files**: `desktop_client/main.py` (Lines 145–156), `desktop_client/core/api_client.py` (Lines 77–90), `desktop_client/components/header.py`.
  * **Defect**:
    1. `ApiClient.check_health_sync()` opens a raw TCP socket to hardcoded `("127.0.0.1", 8000)` instead of calling `GET {active_api_base_url}/health` and ignores custom API URLs.
    2. There is no Global Top Floating Offline Mode Banner (`.offline-host-banner`) with `[Retry]` (spinner + toast feedback) and `[X]` dismiss across all screens (`welcome`, `login`, `signup`, `home`, `map`, `wizard`, `builder`, `saved`, `profile`), nor an interactive Server Status & Custom API URL tester in Settings.
* **QA-04 (Critical — No Proper Offline Fallback for Places, Municipalities, Suggested Clustering, or Authenticated Writes)**:
  * **Files**: `desktop_client/core/api_client.py` (Line 102), `desktop_client/services/place_service.py`, `desktop_client/services/itinerary_service.py`.
  * **Defect**: When the FastAPI server is offline, `ApiClient.request()` immediately throws `NetworkError`. `PlaceService` has no fallback to `Project/src/assets/data/osm_places.json` (2,673 POIs) or `CANONICAL_OFFLINE_PLACES`, resulting in empty screens (`0 destinations`). `ItineraryService.generate_suggested_itinerary()` has no offline clustering fallback (`generateOfflineSuggestedItinerary`), blocking itinerary creation offline.
* **QA-05 (High — Active Demo Account & Non-Functional Google/Apple Buttons)**:
  * **Files**: `Project/src/app/features/auth/login/login.page.html`, `signup.page.html`, `Project/src/app/tabs/profile/profile.page.html`, `DESKTOP_APP_DOCUMENTATION/02_FEATURE_MAPPING.md`.
  * **Defect**: The app already has a dedicated **Guest Mode (`Continue as Guest`)** with local storage (`guest_storage.json`) and cloud sync migration. Having an active `"Explore Demo Account (Pattranite Persona)"` (and fallback strings `'Pattranite Limpatiyakorn'` / `'loverrukk'`) is redundant and confusing, and displaying non-functional `"Continue with Google"` and `"Continue with Apple"` buttons that only pop up a `"disabled in this pilot build"` toast violates `@anti-generic-frontend-design` (*"Buttons that do nothing"*).
* **QA-06 (High — Fake Notification Bell & Unresolved Local Asset Photography)**:
  * **Files**: `desktop_client/views/dashboard_view.py` (Lines 495–498), `desktop_client/components/place_card.py` (Line 41), `desktop_client/components/dialogs.py` (Line 34).
  * **Defect**: Clicking the notification bell on Home simply sets `self.unread_notifications = 0` without opening the **Travel Advisories & Notifications Drawer (`UI-19`)**. Additionally, `PlaceCard` and `dialogs.py` only render `ft.Image` when `place.image_url.startswith("http")`, failing to resolve local relative asset paths (`assets/images/...`) from `Project/src/assets/images/` and showing generic blue placeholder boxes instead of real Nueva Ecija photos.

### 3.2 Code-Level Runtime Exceptions & Logic Bugs (`QA-07` to `QA-14`)

* **QA-07 (Critical — `SavedTripsView._create_trip_card` Crashes with `AttributeError: 'Itinerary' object has no attribute 'total_days'`)**:
  * **Location**: `desktop_client/views/saved_trips_view.py` (Line 258) & `desktop_client/models/itinerary.py`.
  * **Fix**: Add `total_days` and `days_nights_label` properties to `Itinerary`.
* **QA-08 (Critical — `PlacesView._fetch_places` Raises Silent `TypeError` on Every Query)**:
  * **Location**: `desktop_client/views/places_view.py` (Lines 311–321) vs. `desktop_client/services/place_service.py` (Lines 46–55).
  * **Cause**: Passes `municipality=muni, sort_by=sort` to `PlaceService.get_places()`, which only accepts `municipality_id` and `sort`.
  * **Fix**: Align parameter names in both `PlacesView` and `PlaceService.get_places()`.
* **QA-09 (Critical — `ProfileView._sync_guest_trips` Crashes with `AttributeError: 'AuthService' object has no attribute 'migrate_guest_trips'`)**:
  * **Location**: `desktop_client/views/profile_view.py` (Line 294) & `desktop_client/services/auth_service.py`.
  * **Fix**: Implement `migrate_guest_trips()` on `AuthService` / `ItineraryService` to upload each guest itinerary from `guest_storage.json` to `POST /api/v1/itineraries` and remove synced items locally.
* **QA-10 (Critical — `ItineraryService.generate_suggested_itinerary` Raises `NameError: name 'ApiClientError' is not defined`)**:
  * **Location**: `desktop_client/services/itinerary_service.py` (Line 8 & Line 48).
  * **Fix**: Import `ApiClientError` and `NetworkError` from `desktop_client.core.api_client`.
* **QA-11 (High — Clicking a Saved Itinerary Card on `DashboardView` Reloads Home Instead of Opening `TripDetailView`)**:
  * **Location**: `desktop_client/views/dashboard_view.py` (Line 467) & `desktop_client/main.py` (Line 107).
  * **Cause**: `DashboardView` calls `self._navigate(f"/trips/{itin.id}")` without passing `itin` (`trip_data=None`), so `main.py` skips `elif route.startswith("/trips/") and selected_trip:` and falls back to `DashboardView`.
  * **Fix**: Pass `itin` in `on_navigate(f"/trips/{itin.id}", itin)` AND allow `main.py` to look up `itinerary_id` via `itinerary_service.get_itinerary(id)` if `trip_data` is `None`.
* **QA-12 (Critical — `asyncio.run()` Inside Active Flet Event Loop Raises `RuntimeError`)**:
  * **Location**: `desktop_client/views/login_view.py` (Line 208), `signup_view.py` (Line 253), `profile_view.py` (Lines 271 & 299).
  * **Cause**: Calling `asyncio.run(...)` inside synchronous Flet button callbacks while Flet's event loop is already running raises `RuntimeError: asyncio.run() cannot be called from a running event loop`.
  * **Fix**: Route all async UI tasks through a loop-safe helper `run_async(coro_func, page)`.
* **QA-13 (High — Dark Mode Toggle Does Not Re-Theme Views or Cards)**:
  * **Location**: `desktop_client/main.py` (Lines 53–61) and all view/component classes.
  * **Cause**: All views and cards hardcode `ThemeColors.BG_LIGHT`, `ThemeColors.SURFACE_LIGHT`, `ThemeColors.TEXT_BLACK`, and `ThemeColors.BORDER_LIGHT`.
  * **Fix**: Use a reactive `ThemePalette` (`palette = get_palette(is_dark)`) across all views and rebuild active controls when toggling Dark Mode.
* **QA-14 (High — `+ Add to Trip` Discards Selected Place & `SignupView` Discards `M.I.` Input)**:
  * **Location**: `desktop_client/views/places_view.py` (Lines 183 & 300) and `desktop_client/views/signup_view.py` (Lines 74 & 220).
  * **Cause**: `on_add_to_day=lambda p: self._navigate("/builder")` drops `p`; and `SignupView._handle_signup()` reads `first_name` and `last_name` but ignores `self.mi_input.value` and lacks the `Username` field.

---

## 4. Detailed Engineering Specifications for the 5 Core Fixes

### 4.1 Layout Shell: Replace Side Menu with Web App Bottom Tab Bar (`main.py` & `components/bottom_tab_bar.py`)
* **Delete `SidebarNav` (`components/sidebar.py`) and `TopHeader` (`components/header.py`) from `main.py`**.
* **Create `BottomTabBar` (`desktop_client/components/bottom_tab_bar.py`)** matching `Project/src/app/tabs/tabs.page.html` and `tabs.page.scss`:
  * Height: `60px`, top border `1px solid #f1f5f9` (Dark Mode `#1e293b`), background `#ffffff` (Dark Mode `#0f172a`).
  * 4 centered tab buttons (`expand=True` each):
    1. **Home** (`route="/home"`, icon `ft.Icons.HOME`, label `"Home"`)
    2. **Map** (`route="/map"`, icon `ft.Icons.LOCATION_ON`, label `"Map"`)
    3. **Saved** (`route="/saved"`, icon `ft.Icons.BOOKMARK_BORDER`, label `"Saved"`)
    4. **Profile** (`route="/profile"`, icon `ft.Icons.PERSON_OUTLINE`, label `"Profile"`)
  * Selected state: icon and label (`11px`, `W_700`) colored `#0084ff` (Dark Mode `#38bdf8`); unselected colored `#94a3b8` (Dark Mode `#64748b`).
  * Clicking the `Map` tab while in Follow-Route Mode exits Follow-Route Mode cleanly and resets to full province browse mode (matching `onMapTabClicked($event)` in `tabs.page.ts`).
* **Route Layout Rules in `main.py`**:
  * **Tab Routes (`/home`, `/map`, `/saved`, `/profile`)**: Render a `ft.Stack` containing:
    - Main column: `[content_area (expand=True), bottom_tab_bar (height=60)]`
    - Top overlay: `offline_host_banner` (visible whenever `connectivity_service.is_host_offline` is `True` and not dismissed)
    - Full-screen overlay (on initial launch only): `splash_overlay` (auto-dismissing after 2.8s or on click/Esc).
  * **Standalone Full-Screen Routes (`/welcome`, `/guest`, `/login`, `/signup`, `/suggested`, `/builder`, `/trips/{id}`)**:
    - Hide `bottom_tab_bar` completely!
    - Render `[content_area (expand=True)]` inside the `ft.Stack` alongside `offline_host_banner` so server connection status is visible on **every screen** (including Welcome, Login, Signup, Wizard, and Builder), just like `<ion-app>` in `Project/src/app/app.component.html`!
    - Preserve in-memory instances of `SuggestedWizardView` and `CustomBuilderView` when navigating to inspect a place or route map, and enforce the `pendingChangesGuard` confirmation dialog before discarding unsaved edits in `CustomBuilderView` or `TripDetailView`.

### 4.2 Interactive Map Creation (`components/interactive_map.py` & `components/itinerary_route_map.py`)

#### A. Dependency & Architecture
Add `flet-map>=0.1.0` to `desktop_client/requirements.txt` and build a dual-mode map engine in `desktop_client/components/interactive_map.py` that uses `flet_map` (`import flet_map as map`) when installed and automatically falls back to an interactive `flet.canvas` (`ft.canvas.Canvas`) Web-Mercator Slippy Tile + Vector Pin/Polyline renderer if `flet_map` is absent or offline:

1. **Map Viewport & Bounds (Matching `map.page.ts`)**:
   - `NUEVA_ECIJA_CENTER = (15.58, 121.0)`
   - `NUEVA_ECIJA_DEFAULT_ZOOM = 10` (`min_zoom=9`, `max_zoom=18`)
   - `NUEVA_ECIJA_BOUNDS = ((15.05, 120.55), (16.25, 121.55))`
   - Tile URL template: `https://tile.openstreetmap.org/{z}/{x}/{y}.png` with attribution `© OpenStreetMap contributors`.

2. **Full-Screen Map Tab (`views/places_view.py` → `MapView`)**:
   - Constructed as a full-screen `ft.Stack(expand=True)` with 6 layered elements matching `Project/src/app/tabs/map/map.page.html`:
     1. **Base Layer — Interactive Map Canvas**:
        - Renders OpenStreetMap tiles (`map.TileLayer`), `map.PolylineLayer` (for active day routes in `#0284c7`, stroke width `5`), and `map.MarkerLayer` (plotting category-colored teardrop pins for all filtered `places`, or numbered stop pins `1..N` in Follow-Route Mode).
        - Category pin color map (matching `global.scss` `.pin-cat-*`):
          - `cafe`: `#d97706` | `restaurant`: `#ea580c` | `hotel_accommodation`: `#0284c7`
          - `nature_park`: `#16a34a` | `resort_swimming`: `#0891b2` | `church_religious`: `#7c3aed`
          - `museum_cultural`: `#b45309` | `shopping_market`: `#e11d48` | `hospital_clinic` / `pharmacy`: `#dc2626`
          - `bank_atm`: `#059669` | `fuel_station`: `#475569` | `tourist_attraction` / default: `#0084ff`
        - Clicking any marker selects `self.selected_place = place`, centers the map on `(place.latitude, place.longitude)`, and opens the slide-up **Interactive POI Bottom Sheet**!
     2. **Top Overlay (Standard Browse Mode) — Floating Search & Filter Bar (`.map-top-bar`)**:
        - Search input (`"Search places in Nueva Ecija..."`) with `300ms` debounce and clear (`X`) button.
        - **`[Filters]` button** with active filter count badge (`self.active_filter_count`), opening the **Multi-Select Filter Modal (`UI-16`)**:
          - Section 1: **Categories Multi-Select** (16 category choice chips with checkmarks).
          - Section 2: **Municipality / City** (`All Municipalities` + 32 Nueva Ecija LGU chips).
          - Section 3: **Price Range** (`All Prices`, `Free (₱0)`, `Budget (≤ ₱500)`, `Mid-Range (> ₱500)`).
          - Footer: `[Reset]` and `[Apply Filters]`.
        - Horizontal scrollable row of **17 Quick Category Filter Pills** (`All Places`, `Attractions`, `Nature & Parks`, `Resorts & Pools`, `Hotels & Stays`, `Restaurants`, `Cafes & Coffee`, `Churches & Faith`, `Museums & Culture`, `Markets & Shops`, `Transit & Terminals`, `Convenience`, `Hospitals & Clinics`, `Pharmacies`, `Banks & ATMs`, `Fuel Stations`, `Public Facilities`).
     3. **Top Overlay (Follow-Route Mode) — Floating Active Route Control Bar (`.active-route-top-bar`)**:
        - Displayed when `is_follow_route_mode=True` (launched from `[Full Map]` or `[In-App Nav]`).
        - Contains `[← Back to Plan]`, `[Browse Map]`, destination title + `N stops` badge, `Day 1 / Day 2...` switcher pills, and `[Show Nearby POIs]` toggle button (which toggles background POI pins on/off while viewing the route).
     4. **Right Floating Controls Column (`.map-floating-controls`)**:
        - Status pills for `live_osm_message`, `is_loading`, or `has_tile_error` (`"Map tiles unavailable offline. Cached locations remain accessible."`).
        - **`[✨]` Live OpenStreetMap Overpass Button**: Queries `https://overpass-api.de/api/interpreter` (with fallback to `https://maps.mail.ru/osm/tools/overpass/api/interpreter`) for the current map bounding box, maps OSM tags via `map_osm_tags_to_category()`, merges new POIs into `PlaceService`, and updates markers!
        - **`[⊕]` Locate Position Button**: Centers on Cabanatuan City gateway or simulated/configured traveler coordinates with pulsing blue user marker (`.user-pulse-marker`).
        - **`[🧭]` Reset Province View Button**: Resets center to `[15.58, 121.0]`, zoom `10`.
        - **`[+]` and `[-]` Zoom Controls**.
     5. **Bottom Floating Pill & Collapsible POI List Drawer (`.poi-list-toggle-pill` & `.poi-list-drawer`)**:
        - In Browse Mode, floating bottom-center button `List View (N)` opens a slide-up drawer (`max_height=480`) listing all `N` filtered places with thumbnail photo, category, price, name, and municipality. Clicking a row closes the drawer, flies the map to that place's coordinates, and opens its POI Bottom Sheet.
        - In Follow-Route Mode, displays the **Active Route Stops Bottom Carousel (`.active-route-bottom-carousel`)** showing `Stop X of Y`, `[Google Maps Navigation]` multi-stop URL button, and horizontal stop cards (`1`, `2`, `3`...) that pan the map to the clicked stop.
     6. **Slide-Up Interactive POI Bottom Sheet (`PlaceDetailSheet`)**:
        - Overlaid at the bottom of the map (`border_radius=ft.BorderRadius.only(top_left=24, top_right=24)`) when `self.selected_place` is set, with hero photo, favorite heart toggle, Open Now badge, provenance badge, operating hours accordion, `How to get there?` Local Commute Guide, `[✨ Start Trip Here]`, `[+ Add to Trip]`, and `[Get Directions]`.

3. **Embedded Day Route Map (`desktop_client/components/itinerary_route_map.py` — `ItineraryRouteMap`)**:
   - Matches `Project/src/app/shared/components/itinerary-route-map/itinerary-route-map.component.html` & `.ts`:
   - Header bar: `🗺️ Day {day.day_number} Route` + `{len(day.items)} stops` badge on the left; `[Full Map]` button (navigates to `/map` with `follow_route=True, itinerary_id=itinerary.id, day_number=day.day_number`) and expand/collapse chevron button (`⌃` / `⌄`) on the right.
   - Body (`height=180` when expanded):
     - Renders an interactive map canvas fitted to the bounding box of the day's stops (`fit_route_bounds`).
     - Draws the route polyline (`#2563eb`, width `4`) by decoding `day.day_overview_polyline` or each stop's `route_polyline_from_prev` (or querying OSRM `https://router.project-osrm.org/route/v1/driving/{waypoints}?overview=full&geometries=polyline` with a 2.5s timeout online, falling back to `generate_geodesic_arc()` offline).
     - Plots numbered circular stop badges (`1`, `2`, `3`... in `#2563eb`, or `#f59e0b` amber when `active_stop_index == idx`). Clicking a stop marker highlights the corresponding stop card and opens its Stop Detail sheet!
   - Embed `ItineraryRouteMap` inside:
     1. `SuggestedWizardView` (View 2: Generated Itinerary active day section)
     2. `CustomBuilderView` (Timeline pane active day section whenever `len(day.items) > 0`)
     3. `TripDetailView` (View Mode active day card whenever `len(day.items) > 0`)

### 4.3 Server Connectivity Service & Global Offline Banner (`core/connectivity_service.py` & `components/offline_banner.py`)
* **Port `ConnectivityService` (`Project/src/app/core/services/connectivity.service.ts`) to `desktop_client/core/connectivity_service.py`**:
  * Stores `is_host_offline: bool`, `is_checking_health: bool`, `is_dismissed_manually: bool`, `consecutive_errors: int` (`ERROR_THRESHOLD = 2`), and `custom_api_url: Optional[str]` (persisted in `storage/settings.json` under `ne_custom_api_url`).
  * Validates custom API URLs with `is_valid_api_url(url)` (allowing `http://localhost`, `http://127.0.0.1`, and `https://` on `.trycloudflare.com`, `.ngrok-free.dev`, `.ngrok.app`, `.ngrok.io`, `.workers.dev`, `.onrender.com`, `.koyeb.app`) and normalizes them to end with `/api/v1`.
  * `check_host_health() -> bool`: Performs an async HTTP `GET {active_api_base_url}/health` (timeout `5.0s`).
    - On `200 OK`: sets `is_Checking_health = False`, resets `consecutive_errors = 0`, sets `is_host_offline = False`, and notifies listeners.
    - On error/timeout: sets `is_checking_health = False`, sets `consecutive_errors = ERROR_THRESHOLD`, sets `is_host_offline = True` (clearing `is_dismissed_manually`), and notifies listeners.
* **Create Global `OfflineHostBanner` (`desktop_client/components/offline_banner.py`) matching `.offline-host-banner` in `app.component.html` & `app.component.scss`**:
  * Floating dark slate banner (`bgcolor="#0f172a"`, border `1px solid #f59e0b` 28%, `border_radius=14`, `max_width=600`, top margin `12px`) rendered at the top of `main.py`'s root `ft.Stack` so it is visible on **all screens** whenever `connectivity_service.is_host_offline` is `True`:
    - Left icon box (`36x36`, `#f59e0b` cloud-offline icon).
    - Text stack: `"Offline Mode"` (`14px`, bold, `#f8fafc`) + `"Cloud sync paused. Your saved trips and curated destinations remain accessible."` (`12px`, `#cbd5e1`).
    - Right actions:
      - **`[Retry]` button** (`#0284c7` bg, white text, refresh icon or `ProgressRing` spinner while `is_checking_health=True`): Calls `connectivity_service.check_host_health()`. If online, shows a green top SnackBar (`"Connected to backend server! Reloading data..."`) and reloads active view data; if still offline, shows an amber SnackBar (`"Server is currently offline. Your saved trips and places remain available."`).
      - **`[X]` Dismiss button**: Calls `connectivity_service.dismiss_banner()`.
* **Remove the blocking `if not self.check_health_sync(): raise NetworkError(...)` pre-check from `ApiClient.request()`**:
  * Let `httpx.AsyncClient` attempt the request against `self.active_api_base_url`; if `httpx.ConnectError` or `httpx.TimeoutException` occurs, call `connectivity_service.report_gateway_error()` (or `set_host_offline(True, force=True)` on `ConnectError`) and raise `NetworkError` so the calling service immediately triggers its offline fallback!

### 4.4 Three-Tier Proper Offline Fallback (`core/offline_data.py`, `services/place_service.py`, `services/itinerary_service.py`)
1. **Tier 1 — Bundled 2,673 OSM Places + 12 Curated Places in `PlaceService`**:
   - Create `desktop_client/core/offline_data.py` porting `CANONICAL_OFFLINE_PLACES` (all 12 curated places from `offline-places.data.ts`: `Rohi Paperflower Cafe`, `Museo de Bongabon`, `Thornes Samgyupsal House`, `La Casa Prime Cabins`, `Minalungao National Park`, `Tagpuan sa Lumang Gapan`, `Pantabangan Dam and Lake Viewpoint`, `George Point`, `Highland Bali Villas Resort and Spa`, `Farm Villaronte`, `Casa Batik`, `D' Pavilion Farm and Resort`, `Lake Farm de La Marre`), `get_offline_day_cluster_presets()`, `get_offline_nearby_places()`, `NUEVA_ECIJA_32_LGUS`, and `NUEVA_ECIJA_TOP_LANDMARKS`.
   - Load `Project/src/assets/data/osm_places.json` (all 2,673 POIs) into memory once on startup (`load_osm_places()`), merging `CANONICAL_OFFLINE_PLACES` at the front so featured destinations always have rich descriptions, pricing, opening hours, and local images.
   - In `PlaceService.get_places()`, if `api_client.get("places")` raises `ApiClientError` or `NetworkError` (or if `connectivity_service.is_host_offline` is `True`), immediately filter the in-memory 2,673 OSM + curated places using `get_filtered_local_places()` (supporting `search`/`q`, single or multiple `categories`, `municipality_id`/`municipality_name`, `price_tier`, `is_featured`, `min_rating`, `min_lat`/`max_lat`/`min_lng`/`max_lng`, and `sort`) and return a populated `PaginatedPlaces` object!
   - In `PlaceService.get_municipalities()`, if offline, return the 32 municipalities built from `NUEVA_ECIJA_32_LGUS` with their live POI counts from `osm_places.json`.
2. **Tier 2 — Deterministic Offline Suggested Itinerary Clustering Engine in `ItineraryService`**:
   - Port `generateOfflineSuggestedItinerary()` from `Project/src/app/core/services/itinerary.service.ts` (Lines 457–790) into `desktop_client/services/itinerary_service.py` (`generate_offline_suggested_itinerary(request)`):
     - Supports specific municipality targeting (`Bongabon`, `Pantabangan`, `Cabanatuan City`, `Gapan City`, `General Tinio`, `Gabaldon`, `Science City of Muñoz`, `San Jose City`, etc.) or province-wide corridor presets (`East Corridor: Bongabon`, `North Corridor: San Jose & Pantabangan`, `South Corridor: Cabanatuan, General Tinio & Gapan`).
     - Scores candidates by preference category match (`+25`), tag match (`+5`), municipality match (`+10`), minimum rating filter, and daily budget fit (`+2`).
     - Enforces cross-day fuzzy name + `<200m` Haversine deduplication (`PREF-06`), 1-day trip overnight lodging exclusion, slot #2 (`12:00 PM`) midday dining anchor (`PREF-05`), max 1 mountain peak per day, chronological sorting with overnight stays last (`DEF-03`), budget substitution when day min cost exceeds `daily_budget`, Haversine leg distance/duration/polyline calculation (`encode_polyline`), non-overlapping rolling time windows (`09:30 AM`, `12:00 PM`, `03:00 PM`), and the 5 transparent `assumptions` strings!
   - Whenever `connectivity_service.is_host_offline` is `True` or `api_client.post("itineraries/suggest")` fails, `generate_suggested_itinerary()` returns `generate_offline_suggested_itinerary(request)` seamlessly with zero error banner!
3. **Tier 3 — Authenticated Write Fallback to Local Guest Storage**:
   - In `ItineraryService` (`create_itinerary`, `update_itinerary`, `delete_itinerary`, `add_stop`, `update_stop`, `delete_stop`, `reorder_stops`), wrap authenticated cloud API calls in `try ... except NetworkError:` and automatically fall back to `self.guest_storage.save_itinerary(...)` so offline transitions never lose user edits.

### 4.5 Clean Authentication: Remove Demo Account & Remove Google/Apple Buttons (`login_view.py`, `signup_view.py`, `profile_view.py`)
* **No Demo Account (`Pattranite Persona`) Anywhere**:
  * Do **NOT** render any `"Explore Demo Account (Pattranite Persona)"` button on `LoginView` or `WelcomeView`.
  * Remove any hardcoded `'Pattranite'`, `'Limpatiyakorn'`, or `'loverrukk'` fallback strings in `ProfileView`—authenticated users see their actual registered `first_name`, `middle_initial`, `last_name`, `@username`, and `email`, while unauthenticated users see `"Guest Explorer"` / `"Browsing in Guest Mode (Offline)"`.
* **No Google or Apple Buttons on Login or Signup**:
  * Do **NOT** render the `"Continue with Google"` or `"Continue with Apple"` buttons or the `"or"` social divider on `LoginView` or `SignupView`.
* **Exact `LoginView` Structure**:
  * Top-left `←` back arrow (navigates to `/welcome`).
  * Centered airplane icon + `"Trip mo, trip ko"`.
  * Left-aligned `"Welcome back!"` + `"Log in to continue your journey."`.
  * Email Address input + Password input (with eye toggle).
  * `Remember me` checkbox + **`Forgot password?` link** (opens the **Account Recovery Modal** matching `login.page.html` lines 135–208).
  * Solid blue pill **`[Log in]`** button (with loading spinner).
  * Footer: `"Don't have an account? Sign up"` + `"Continue as Guest"` link (routing to `/guest`).
* **Exact `SignupView` Structure**:
  * Top-left `←` back arrow (navigates to `/welcome`).
  * Centered airplane icon + `"Trip mo, trip ko"`.
  * Left-aligned `"Create your account"` + `"Get started and plan your new adventure."`.
  * 6 validated fields in exact vertical stack:
    1. `First Name` (required, auto-suggests `Username` on change)
    2. `Middle Initial (if applicable)` (optional, persisted in `profile_extra.json`)
    3. `Last Name` (required, auto-suggests `Username` on change)
    4. `Username` (leading `@` icon, required, min 3 chars `[a-zA-Z0-9_-]`)
    5. `Email Address` (leading mail icon, required valid email)
    6. `Password` (leading key icon + eye toggle, required **min 8 characters**) & `Confirm Password` (leading checkmark-circle icon + eye toggle, must match password)
  * Solid blue pill **`[Sign up]`** button.
  * Footer: `"Already have an account? Log in"`.

---

## 5. Phased Implementation Plan for Antigravity

Execute these 5 sequential phases in `desktop_client/` and verify with `pytest`:

### Phase 1: Core Services, 3-Tier Offline Fallback, Connectivity Banner & Bug Fixes (`QA-03`, `QA-04`, `QA-07`–`QA-14`)
1. **Update `desktop_client/requirements.txt`**: Add `flet-map>=0.1.0`.
2. **Create `desktop_client/core/async_utils.py`**: Implement `run_async(coro_func, page=None)` (`QA-12`).
3. **Create `desktop_client/core/polyline.py`**: Port `encode_polyline()`, `decode_polyline()`, `haversine_distance_meters()`, `generate_geodesic_arc()`, and `build_google_maps_day_route_url()` from `Project/src/app/core/utils/polyline.util.ts` and `itinerary-export.util.ts`.
4. **Create `desktop_client/core/connectivity_service.py`**: Port `ConnectivityService` (`check_host_health()` calling `GET {active_api_base_url}/health`, `is_host_offline`, `is_checking_health`, `set_custom_api_url()`, `clear_custom_api_url()`, `dismiss_banner()`, listener callbacks) (`QA-03`).
5. **Create `desktop_client/core/offline_data.py` & `desktop_client/core/commute_guide.py`**:
   - Load `Project/src/assets/data/osm_places.json` (2,673 POIs) + `CANONICAL_OFFLINE_PLACES` (`offline-places.data.ts`), `NUEVA_ECIJA_32_LGUS`, `NUEVA_ECIJA_TOP_LANDMARKS`, `get_offline_day_cluster_presets()`, and `get_offline_nearby_places()`.
   - Port `COMMUTE_BY_MUNICIPALITY`, `get_commute_info_for_municipality()`, and `get_leg_commute_info()` from `commute-guide.data.ts` (`QA-04`).
6. **Update `desktop_client/config/settings.py`**:
   - Add `ThemePalette` (Light & Dark tokens matching `global.scss` `body.dark`) (`QA-13`).
   - Add `resolve_place_image(name, image_url)` mapping local `assets/images/...` paths and place names to `Project/src/assets/images/` (`QA-06`).
7. **Update `desktop_client/models/itinerary.py`, `place.py`, and `user.py`**:
   - Add `total_days`, `days_nights_label`, and `calculate_budget_summary()` to `Itinerary` (`QA-07`).
   - Add `username`, `first_name`, `last_name`, `middle_initial`, `birthday`, `gender`, and `phone_number` support to `User` / `ProfileExtra`.
8. **Update `desktop_client/services/place_service.py`, `itinerary_service.py`, `auth_service.py`, and create `favorites_service.py`**:
   - Fix `PlaceService.get_places()` kwargs and add automatic fallback to the 2,673 OSM + curated places (`QA-04`, `QA-08`).
   - Import `ApiClientError`/`NetworkError` in `itinerary_service.py` (`QA-10`), add `generate_offline_suggested_itinerary()` (`QA-04`), add authenticated-write fallback to `guest_storage`, and add `active_draft_itinerary` caching.
   - Implement `migrate_guest_trips()` in `AuthService` (`QA-09`).
   - Create `FavoritesService` (`desktop_client/services/favorites_service.py`) seeded with 3 featured Nueva Ecija places.

### Phase 2: Bottom Tab Bar Shell, Splash Screen, Offline Banner & Clean Auth (`QA-01`, `QA-03`, `QA-05`)
1. **Create `desktop_client/components/bottom_tab_bar.py` & `desktop_client/components/offline_banner.py`**:
   - Build `BottomTabBar` (`Home`, `Map`, `Saved`, `Profile`, `height=60`) matching `.custom-tab-bar`.
   - Build `OfflineHostBanner` matching `.offline-host-banner` with `[Retry]` (spinner + toast) and `[X]` dismiss (`QA-03`).
2. **Refactor `desktop_client/main.py`**:
   - Remove `SidebarNav` and `TopHeader` (`QA-01`).
   - Add `SplashOverlay` (`loading_screen.jpg`, auto-dismiss after 2.8s or on click/Esc).
   - Mount `OfflineHostBanner` at the top of the root `ft.Stack` across all routes.
   - Show `BottomTabBar` only on `/home`, `/map`, `/saved`, `/profile`; hide it on `/welcome`, `/guest`, `/login`, `/signup`, `/suggested`, `/builder`, `/trips/{id}`.
   - Preserve view state and enforce the unsaved-changes confirmation guard (`pendingChangesGuard`).
3. **Update `welcome_view.py`, create `guest_view.py`, and update `login_view.py` & `signup_view.py`**:
   - Remove the 3-box SaaS feature strip from `WelcomeView`; add `welcome_hero_buildings.png`, `/guest` screen (`guest_hiker_hero.png`), and After-Logout view (`logout_skyscrapers_blob.png`, `logout_cityscape_silhouette.png`).
   - Add `Forgot password?` Account Recovery Modal to `LoginView`.
   - Add `Username` (auto-suggested) and `M.I.` persistence + `>= 8` char password check to `SignupView` (`QA-14`).
   - **Ensure zero Demo Account buttons and zero Google/Apple buttons exist on `LoginView`, `SignupView`, or `WelcomeView` (`QA-05`).**

### Phase 3: Interactive Map Creation (`MapView` & `ItineraryRouteMap`) (`QA-02`)
1. **Create `desktop_client/components/interactive_map.py` (`InteractiveProvinceMap`)**:
   - Implement the interactive map using `flet_map` (`Map`, `TileLayer`, `MarkerLayer`, `PolylineLayer`) with automatic interactive `ft.canvas.Canvas` fallback.
   - Support category-colored teardrop markers, numbered route stop markers (`1..N`), decoded route polylines (`#0284c7` / `#2563eb`), zoom `+ / -`, `Recenter`, `Locate`, and `Live OSM Overpass` fetching.
2. **Create `desktop_client/components/itinerary_route_map.py` (`ItineraryRouteMap`)**:
   - Build the `180px` collapsible day route map card (`Day X Route`, `N stops` badge, `[Full Map]` button, collapse chevron) that renders the day's numbered stop pins and OSRM/decoded/geodesic polyline.
3. **Rebuild `desktop_client/views/places_view.py` as `MapView`**:
   - Full-screen interactive map with top floating search bar, `[Filters]` button + **Multi-Select Filter Modal** (16 categories, 32 LGUs, 4 price tiers), 17 quick category filter pills, floating right-side controls, bottom `List View (N)` toggle pill + **Collapsible POI List Drawer**, slide-up **Interactive POI Bottom Sheet**, and **Isolated Follow-Route Mode** (top route control bar + day pills + `[Show Nearby POIs]` toggle + bottom stop carousel + `[Google Maps Navigation]` button).

### Phase 4: Home Dashboard, Suggested Wizard & Custom Builder Parity (`QA-06`, `QA-11`, `QA-14`)
1. **Update `desktop_client/views/dashboard_view.py` & `components/dialogs.py`**:
   - Add `300ms` debounced live search with clear (`X`) button and offline fallback.
   - Build the **Travel Advisories & Notifications Drawer (`UI-19`)** and **Popular Destinations "See all" Catalog Modal (`UI-11`)**.
   - Upgrade `PlaceDetailSheet` / `show_place_detail_dialog` with Favorite Heart toggle, `Open Now` badge, Provenance badge, Operating Hours accordion, **`How to get there?` Local Commute Guide**, **`[✨ Start Trip Here]`**, and **`[+ Add to Trip]`**.
   - Fix saved itinerary card click (`QA-11`) so clicking a trip opens `TripDetailView`.
2. **Create `desktop_client/components/destination_picker.py` & `date_range_dialog.py`**:
   - Build the **32-LGU Destination Autocomplete Combobox + Quick Chips + All 32 Towns District Modal (`All / Central / North / South / East`)** and **Figma Date Picker Pop-Up Modal (`From` & `To` + `2D/1N`, `3D/2N`, `4D/3N`, `1W` presets)**.
3. **Rebuild `desktop_client/views/suggested_wizard_view.py`**:
   - Implement the 3-view state machine (`form` → `itinerary` → `nearby`) with `.figma-header-bar`, Destination Autocomplete, Date Picker Modal, Budget input + presets, 5 Preference pills, Pacing, Travel Mode (`DRIVE`, `TWO_WHEELER`, `WALK`), and Min Rating (`0`, `4.0`, `4.5`).
   - In View 2 (`itinerary`), render the Destination Top Card, `.verified-budget-card`, collapsible `.assumptions-info-box`, Day Capsule Bar with municipality names, **Embedded `ItineraryRouteMap`**, Stop Cards with thumbnails and **Inter-Stop Leg Commute Badges (`km • drive/tricycle • fare`)**, Nearby Places trigger banner, `[✓ Accept & Save Itinerary]`, and `[✎ Customize in Builder]`.
   - In View 3 (`nearby`), render segmented tabs (`Restaurants`, `Hospital & Pharmacies`, `Stores`) with `[Maps]` and `[+ Add to Day N]`.
4. **Rebuild `desktop_client/views/custom_builder_view.py`**:
   - Support Stage 1 setup questionnaire (`form`), Catalog browse (`browse`), and Timeline (`timeline`) (or responsive desktop split-pane after Stage 1), plus pre-loaded place banner (`QA-14`) and edit-existing-itinerary mode.
   - Add stateful `+ Add` / `✓ Added` buttons, `[Auto-Schedule]`, `[Delete Day]`, **Embedded `ItineraryRouteMap`**, Leg Commute Badges, `Move to Day` in Edit Stop, and Nueva Ecija geofenced coordinates (`Lat 15.15–16.15`, `Lng 120.70–121.40`) + Address in the Off-Grid Venue modal.

### Phase 5: Saved Trips, In-Place Trip Editor, Profile Subviews & Automated QA Suite
1. **Update `desktop_client/views/saved_trips_view.py` & `views/trip_detail_view.py`**:
   - Display `days_nights_label` on saved trip cards (`QA-07`).
   - Add **In-Place Edit Mode (`is_edit_mode`)**, Verified Budget Card, Trip Assumptions, Day Route Metrics Banner (`km` + travel time + stops), `[In-App Nav]` (routes to `/map` in Follow-Route Mode), `[Google Maps]` multi-stop route launcher, **Embedded `ItineraryRouteMap`**, Leg Commute Badges, Nearby Places explorer, and the 4-option **Share & Export Modal** (`.ics`, Copy Text Summary, `.md`/`.json`, Print/PDF sheet).
2. **Update `desktop_client/views/profile_view.py`**:
   - Implement all 6 views (`profile`, `settings`, `edit`, `favorites`, `help`, `about`), the **5-row Figma Profile Menu Card**, `Favorites` manager, 7-field `Edit Profile` with Avatar upload (and zero `'Pattranite'` hardcoded strings), `Settings` with **Server Connection Status & Custom API URL tester**, `Help & Support` with FAQs & Nueva Ecija Emergency Hotlines, and the Figma Exit-Door `Log Out?` modal.
3. **Expand `desktop_client/tests/`**:
   - Add comprehensive tests verifying:
     - Bottom Tab Bar navigation and absence of `SidebarNav` (`QA-01`).
     - `InteractiveProvinceMap` and `ItineraryRouteMap` instantiation, marker plotting, polyline decoding, and Follow-Route mode (`QA-02`).
     - `ConnectivityService` health check, custom API URL validation, and `OfflineHostBanner` retry/dismiss behavior (`QA-03`).
     - 3-tier offline fallback: 2,673 OSM places loading/filtering offline, `generate_offline_suggested_itinerary()` clustering offline, and authenticated write fallback to `guest_storage.json` (`QA-04`).
     - Absence of Demo Account and Google/Apple buttons on `LoginView` and `SignupView` (`QA-05`).
     - All 8 runtime bug fixes (`QA-07` through `QA-14`) inside an active `asyncio` event loop.

---

## 6. Verification Commands

Run the full test suite after implementation:

```powershell
# Windows PowerShell
python -m pip install -r desktop_client/requirements.txt
python -m pytest desktop_client/tests -v
```

```bash
# Linux / WSL 2 / macOS
python3 -m pip install -r desktop_client/requirements.txt
python3 -m pytest desktop_client/tests -v
```
