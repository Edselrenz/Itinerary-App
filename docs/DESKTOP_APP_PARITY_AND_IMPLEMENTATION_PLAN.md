# Nueva Ecija Travel Itinerary App ("Trip mo, trip ko") — Desktop (`desktop_client/`) vs. Web (`Project/`) QA Audit v3 & Antigravity Remediation Specification

**Repository**: `https://github.com/Edselrenz/Itinerary-App`  
**Target Desktop Package**: `desktop_client/` (Python 3.12+ / Flet `>=1.1.2` / `httpx` / `pytest`)  
**Reference Web Application**: `Project/` (Ionic 9 / Angular 22 / Leaflet 1.9 / TypeScript) & `https://edselrenz.github.io/Itinerary-App`  
**Backend API Reference**: `backend/app/schemas/user.py` & `backend/app/schemas/itinerary.py` (FastAPI / SQLAlchemy / PostGIS)  
**Applied Engineering & Design Standards**: `@coding-and-system-development` & `@anti-generic-frontend-design`  
**Document Ref**: `docs/DESKTOP_APP_PARITY_AND_IMPLEMENTATION_PLAN.md`

---

## 1. Executive Summary & Root-Cause Analysis of the 4 Reported Failures (QA v3)

Hands-on testing of the Flet `1.1.2` desktop application exposed **4 critical functional and layout regressions** compared to the Web App (`Project/`). Below is the exact technical root cause of each defect and its required architectural remediation:

| # | User-Reported Issue | Root Cause in Flet `1.1.2` & FastAPI Contract | Exact Fix Required |
| :--- | :--- | :--- | :--- |
| **1** | **"The `'You are offline'` notice spans the whole application"** | In Flet `1.1.2`, placing `OfflineHostBanner` (an `ft.Container` with `bgcolor="#0f172a"`) as an unpositioned child inside `main.py`'s root `ft.Stack(expand=True)` (or without `expand=False` and fixed `height=52`) causes Flutter's `StackFit.expand` behavior to stretch the dark `#0f172a` background across the **entire 1280×840 application window**, covering the UI. | **Never** place `OfflineHostBanner` as an unpositioned child of `ft.Stack(expand=True)`. Render `OfflineHostBanner` as the first non-expanding child (`expand=False`, fixed `height=52`) inside the root `ft.Column(spacing=0, expand=True)` directly above `content_area`, wrapped in a centered floating pill (`width=620, height=44, border_radius=12`), with a working `[✕]` dismiss button (`self.visible = False; self.height = 0; self.page.update()`). |
| **2** | **"The map is not working properly, it does not display the places like the website, it does not show the routing"** | 1) **`flet_map` Incompatibility**: `flet_map` is either absent or incompatible with Flet `1.1.2`'s control tree, and `ft.canvas` shapes (`cv.Circle`) **do not support click handlers** in Flet.<br>2) **Missing 2,673 OSM Places**: `PlaceService` failed to resolve the relative path to `Project/src/assets/data/osm_places.json` (`2,673` POIs) when launched from `desktop_client/` and did not implement zoom-aware marker clustering (`zoom < 14` → `#0084ff` numbered cluster circles; `zoom >= 14` → category-colored teardrop pins).<br>3) **Missing Route Polyline & Stop Projection**: `ItineraryRouteMap` and `MapView` failed to extract `(lat, lng)` from both `item.place.latitude/longitude` and `item.custom_lat/custom_lng`, failed to query OSRM (`https://router.project-osrm.org/route/v1/driving/...?overview=full&geometries=polyline`) or decode `day_overview_polyline` / geodesic spline fallback, and failed to project `(lat, lng)` into Web-Mercator pixel coordinates `(x, y)` on an `ft.canvas.Canvas` layer over 256×256 OpenStreetMap tiles (`https://tile.openstreetmap.org/{z}/{x}/{y}.png`). | Build a **100% Pure-Flet `1.1.2` Web-Mercator Slippy Map Engine (`desktop_client/components/slippy_map_canvas.py`)** that layers:<br>• **Layer 1**: 256×256 OpenStreetMap `ft.Image` tiles positioned via Web-Mercator math with drag-to-pan (`ft.GestureDetector`) and zoom (`+`/`-`).<br>• **Layer 2**: `ft.canvas.Canvas` with `cv.Path` drawing the `#0284c7` / `#2563eb` (`stroke_width=5`) OSRM road polyline (plus white casing `stroke_width=8`) and dashed walk connectors.<br>• **Layer 3**: Clickable `ft.Container` controls positioned at `(px, py)` for **Blue Marker Clusters (`#0084ff`)**, **Category Teardrop Pins**, and **Numbered Route Stop Badges (`1..N`)**. |
| **3** | **"The edit profile does not really work properly"** | **Backend Schema Mismatch (`backend/app/schemas/user.py` vs. `desktop_client/models/user.py`)**:<br>• FastAPI `UserOut` returns `first_name`, `last_name`, `username_normalized`, `email_normalized` — it **never** returns `full_name` or `email`!<br>• FastAPI `UserUpdateIn` (`PATCH /api/v1/auth/me`) accepts `first_name`, `last_name`, `username`, `current_password`, `new_password` — it **ignores** `full_name` and `avatar_url`!<br>• `User.from_dict()` read `data.get("full_name", "")`, wiping out the user's name after login or update, and Guest/Offline mode lacked local persistence (`profile_extra.json`) for `first_name`, `last_name`, `middle_initial`, `birthday`, `gender`, `phone_number`, and `avatar_url` (plus native file picker for `Change Photo`). | 1) Update `desktop_client/models/user.py` so `User.from_dict()` reads `first_name`, `last_name`, `username_normalized`, and `email_normalized` (computing `full_name` dynamically), and `UserUpdatePayload.to_backend_dict()` sends `first_name`, `last_name`, `username`.<br>2) Persist extended profile fields (`middle_initial`, `birthday`, `gender`, `phone_number`, `avatar_url`) and Guest profile edits locally in `LocalStorage` (`profile_extra_{user_id}`), merging them on load and save.<br>3) Wire `[Change Photo]` in `ProfileView` to open a native file dialog (`tkinter.filedialog` / `ft.FilePicker`) with preset avatar fallbacks. |
| **4** | **"Both the custom and suggested itinerary also does not work the same as the web"** | • **`SuggestedWizardView`** used a single static view instead of the Web App's **3-View State Machine (`view_mode = "form" | "itinerary" | "nearby"`)** in `suggested-wizard.page.html/.ts`, missing the pre-save preview mode (`save_immediately=False`), `set_active_draft_itinerary(plan)` (needed for `[Full Map]` handoff), collapsible `Travel Notes & Planning Assumptions`, embedded `ItineraryRouteMap`, inter-stop leg commute badges (`🚗 X.X km • ~X mins drive • Y mins tricycle • Est. Fare ₱XX–₱YY`), `Nearby Places in [Municipality]` view (`Restaurants | Hospital & Pharmacies | Stores` with `[+ Add to Day X]`), and `[Customize in Builder]` handoff.<br>• **`CustomBuilderView`** used a cramped 2-column split-pane instead of the Web App's **3-View State Machine (`active_view = "form" | "browse" | "timeline"`)** in `custom-builder.page.html/.ts` with the top segmented switcher (`[+ Add Places]` \| `[📅 Your Itinerary (N)]`), target day selector (`Scheduling for: Day 1 (0) | Day 2 (0) | [+]`), stateful `[+ Add]` / `[✓ Added]` place cards, editable Trip Settings header (`syncDaysWithDateRange`), `[🕒 Auto-Schedule]`, embedded `ItineraryRouteMap`, inter-stop commute leg badges, `[Edit Stop]` modal with `Move to Day` dropdown, and `[+ Add Off-Grid Custom Venue]` modal with Nueva Ecija geofence validation (`Lat 15.15–16.15, Lng 120.70–121.40`). | Rewrite `SuggestedWizardView` and `CustomBuilderView` to mirror `suggested-wizard.page.html/.ts` and `custom-builder.page.html/.ts` 1:1, including their exact 3-view state machines, top view switcher, embedded `ItineraryRouteMap`, inter-stop leg commute calculator, draft itinerary handoff to `MapView` (`itineraryId="draft"`), and `[Customize in Builder]` handoff. |

---

## 2. Mandatory Architectural Corrections

### 2.1 Bounded `OfflineHostBanner` in Root `ft.Column`
- In Flet `1.1.2`, unpositioned children in `ft.Stack(expand=True)` trigger Flutter's `StackFit.expand`, stretching a dark banner across the entire screen.
- **Architectural Rule**: `OfflineHostBanner` must have `expand=False`, fixed `height=52` when visible, `height=0` when hidden or dismissed, and must be rendered as the top child in an `ft.Column(spacing=0, expand=True)` containing `[offline_banner, content_area, bottom_tab_bar]`.
- The banner's inner card is a centered floating pill card (`width=620, height=42, border_radius=12, bgcolor="#0f172a"`).
- Clicking `[✕]` calls `connectivity_service.dismiss_banner()` and sets `self.visible = False; self.height = 0; self.page.update()`.

### 2.2 Domain Model & Backend Schema Alignment (`User` & `Edit Profile`)
- **FastAPI `UserOut` Contract**: Only returns `first_name`, `last_name`, `username_normalized`, `email_normalized`, `is_active`, `created_at`.
- **FastAPI `UserUpdateIn` Contract**: Only accepts `first_name`, `last_name`, `username`, `current_password`, `new_password`.
- **Desktop Architecture**:
  - `desktop_client/models/user.py`: Update `User.from_dict()` to read `first_name`, `last_name`, `username_normalized`, `email_normalized`. Compute `full_name` dynamically.
  - Implement `UserUpdatePayload`:
    - `to_backend_dict()`: Filters strictly to `first_name`, `last_name`, `username`, passwords for `PATCH /api/v1/auth/me`.
    - `to_extra_dict()`: Captures `middle_initial`, `birthday`, `gender`, `phone_number`, `avatar_url`, `preferences`, `default_daily_budget`.
  - `AuthService.update_profile()`: Saves extended fields to `LocalStorage` under `profile_extra.json` (`profile_extra_{user_id}`), issues `PATCH /api/v1/auth/me` if authenticated, and gracefully falls back in Guest or Offline mode.
  - `ProfileView._open_edit_profile_modal()`: Offers standard image file picker via `tkinter.filedialog.askopenfilename` + avatar presets, updating all fields seamlessly.

### 2.3 Pure-Flet Slippy Map Engine (`SlippyMapCanvas`)
- Replace unreliable third-party Flutter mapping libraries with a pure-Flet Web-Mercator engine:
  - **Tile Plane**: 256×256 OpenStreetMap tiles positioned via `latlon_to_world_px(lat, lon, zoom)` math with pan gestures (`ft.GestureDetector`) and zoom buttons (`Z8..Z18`).
  - **Vector Route Polyline Plane**: `ft.canvas.Canvas` drawing OSRM road geometry (`https://router.project-osrm.org/route/v1/driving/...`) with `#0284c7` inner line (width 5) and white outer casing (width 8), with geodesic arc fallback.
  - **Interactive Marker Plane**: Positioned `ft.Container` controls:
    - At `zoom < 14`: Grid spatial clustering into blue `.marker-cluster` badges (`#0084ff`), clicking zooms into cluster center by `+2`.
    - At `zoom >= 14`: Category-colored teardrop pins opening `PlaceDetailSheet`.
    - In route mode: Numbered circular stop badges (`1..N`) with stop title pills.
- Path resolution: Locate `Project/src/assets/data/osm_places.json` using absolute parent resolution so all 2,673 POIs load regardless of working directory.

### 2.4 Suggested Itinerary Wizard 3-View State Machine
- **View 1 (`form`)**: 32-LGU Destination Autocomplete + `[All 32 Towns]` modal + Quick Chips, Travel Dates modal (`From`/`To` + duration presets), daily budget presets, preferences pills, travel mode pills, ratings chips, and `[Find Itinerary]`.
- **View 2 (`itinerary`)**: Calls `suggest_itinerary(..., save_immediately=False)`, sets active draft in `ItineraryService` (`set_active_draft_itinerary(plan)`), renders Trip Summary, Verified Budget Card, collapsible Planning Assumptions accordion, Day Capsule Bar, embedded `ItineraryRouteMap` (with `[Full Map]` launcher to `/map?itineraryId=draft`), stop cards with inter-stop leg commute badges, Nearby Places banner button, `[✓ Accept & Save Itinerary]`, and `[✏️ Customize in Builder]`.
- **View 3 (`nearby`)**: Segmented bar (`Restaurants` | `Hospital & Pharmacies` | `Stores`) for active day municipality with `[+ Add to Day X]` and `[Maps]`.

### 2.5 Custom Itinerary Builder 3-View State Machine
- **View 0 (`form`)**: Trip title, destination, dates, budget presets, preferences. `[Start Building Itinerary →]` -> `sync_days_with_date_range()` -> switches to `browse`. (If editing existing trip or draft from wizard, starts in `timeline`).
- **View 1 (`browse`)**: Top segmented switcher (`[+ Add Places]` active | `[📅 Your Itinerary (N)]`), target day selector (`Scheduling for: Day 1 (0) | Day 2 (0) | [+]`), search & category pills, place card grid with stateful `[+ Add]` / `[✓ Added]` buttons (with auto-calculated time and travel buffer), sticky footer `[View my Itinerary (N places) →]`.
- **View 2 (`timeline`)**: Top segmented switcher (`[+ Add Places]` | `[📅 Your Itinerary (N)]` active) + `[✓ Save]` button, editable Trip Settings card (dates, title, budget), verified place costs card, day capsule switcher + `[+ Add Day]`, active day header with `[🕒 Auto-Schedule]` and `[🗑 Delete Day]`, embedded `ItineraryRouteMap` (with OSRM route & `[Full Map]` button), ordered stop cards with inter-stop leg commute badges, `[↑]`, `[↓]`, `[✏️ Edit]` (with `Move to Day` dropdown), `[🗑 Remove]`, `[+ Browse & Add Places to Day X]`, `[+ Add Off-Grid Custom Venue]` (geofenced), and sticky footer `[💾 Save Custom Itinerary]`.

---

## 3. Implementation Roadmap (Phase 50)

- **Step 1**: Fix `OfflineHostBanner` & Root Layout (`components/offline_banner.py` & `main.py`).
- **Step 2**: Fix `User` Model, `AuthService`, and `ProfileView` (`models/user.py`, `services/auth_service.py`, `views/profile_view.py`).
- **Step 3**: Load All 2,673 OSM Places & Build Pure-Flet Slippy Map + Clustering + Road Routing (`services/place_service.py`, `components/slippy_map_canvas.py`, `components/itinerary_route_map.py`, `views/map_view.py`).
- **Step 4**: Upgrade `SuggestedWizardView` to the Exact 3-View Web Workflow (`views/suggested_wizard_view.py`).
- **Step 5**: Upgrade `CustomBuilderView` to the Exact 3-View Web Workflow (`views/custom_builder_view.py`).
- **Step 6**: Automated Verification & QA Test Suite (`pytest desktop_client/tests/`).
