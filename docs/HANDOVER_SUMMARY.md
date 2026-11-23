# Nueva Ecija Travel Itinerary — Master Handover & System Architecture Document

**Application Name**: Nueva Ecija Travel Itinerary (*Trip mo, trip ko*)  
**Version**: `1.0.0` / `0.58.1` (Production Windows Desktop Installer + Portable Bundle + Web PWA + Android Signed APK + FastAPI Pilot)  
**Date of Handover**: November 22, 2026  
**Active Repository Branch**: `main`  
**Current Milestone**: **Phase 62 — Dual-Platform Release Packaging, Build Pipeline Alignment & Documentation Sync [COMPLETED & VERIFIED]**  

---

## 1. Executive Summary & Verification State

This document serves as the master onboarding and handoff reference for engineering teams, QA leads, and autonomous coding agents. It provides a complete technical blueprint of the application across all tiers: **Backend API**, **Web Application (Angular/Ionic)**, **Android Mobile Application (Capacitor/Gradle)**, and **Native Windows Desktop Application (Python/Flet)**.

### Comprehensive Test Suite Status (100% Green)
| Test Suite | Framework / Tool | Test Cases | Execution Time | Pass Rate | Status |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Native Desktop Client** | Pytest (`desktop_client/tests/`) | **115 / 115** | 6.27s | **100%** | **PASS** |
| **Angular / Ionic Web App** | Vitest (`Project/src/`) | **348 / 348** | 20.79s | **100%** | **PASS** |
| **FastAPI Backend** | Pytest (`backend/tests/`) | **21 / 21** | 13.66s | **100%** | **PASS** |
| **Total Test Matrix** | Unified Test Suite | **484 / 484** | ~41s | **100%** | **ALL GREEN** |

### Multi-Platform Distribution & Packaging
- **Standalone Desktop Executable**: [`dist/NuevaEcijaTravel/NuevaEcijaTravel.exe`](file:///c:/Users/Edward/Desktop/CaseStudy/dist/NuevaEcijaTravel/NuevaEcijaTravel.exe) (~15.3 MB binary, complete self-contained bundle with bundled Python runtime, Flet engine, `app_icon.ico`, and static assets).
- **Inno Setup Windows Installer**: `installer/NuevaEcijaTravel.iss` producing `NuevaEcijaTravel-Setup-x64.exe` with desktop icon, Start Menu shortcut, `%LOCALAPPDATA%` storage auto-fallback, and clean uninstaller.
- **Android Mobile Package**: `Project/android/` compiling release & debug APKs (`app-release.apk` / `app-debug.apk`) with native status bar theming, back-button handling, and service worker isolation.
- **Automated CI/CD Pipeline**: `.github/workflows/release-builds.yml` orchestrating cross-platform builds and GitHub releases upon tag pushes (`v*.*.*`) and manual dispatch.

---

## 2. Multi-Tier System Architecture

```
                                  +---------------------------------------+
                                  |     Traveler Client Interfaces       |
                                  +---------------------------------------+
                                       |                             |
                   +-------------------+                             +-------------------+
                   |                                                                     |
                   v                                                                     v
    +------------------------------+                                      +------------------------------+
    |   Angular 18 / Ionic 8 Web   |                                      |   Python 3.12+ / Flet 1.1    |
    |      (PWA / Mobile / Web)    |                                      |     (Native Windows Desktop) |
    +------------------------------+                                      +------------------------------+
    | * Leaflet OSM Canvas Map     |                                      | * Custom SlippyMapCanvas     |
    | * RxJS Reactive Stores       |                                      | * Thread-safe Tile Pool      |
    | * Ionic Storage (IndexedDB)  |                                      | * Local JSON Storage Engine  |
    | * Host: GitHub Pages / Local |                                      | * Standalone Win64 .EXE      |
    +------------------------------+                                      +------------------------------+
                   |                                                                     |
                   +-------------------+                             +-------------------+
                                       |                             |
                                       v                             v
                                  +---------------------------------------+
                                  |  FastAPI Backend (Port 8000)          |
                                  +---------------------------------------+
                                  | * Argon2id Auth & JWT Rotation        |
                                  | * Deterministic Haversine Clustering  |
                                  | * OSRM Routing & Geodesic Spline Fall |
                                  | * SlowAPI Rate Limiting & Health API  |
                                  +---------------------------------------+
                                       |                             |
                       +---------------+                             +---------------+
                       |                                                             |
                       v                                                             v
        +------------------------------+                             +------------------------------+
        |   PostgreSQL 16 in Docker    |                             |      SQLite Local Engine     |
        |  (`ne_postgres` Port 5432)   |                             |   (`nueva_ecija_travel.db`)  |
        +------------------------------+                             +------------------------------+
        | * 2,673 Real Places Catalog  |                             | * Automatic Zero-Config      |
        | * 12 Curated Municipalities  |                             |   Offline Failover Harness   |
        | * Extended Profile Columns   |                             | * Dual-Engine ORM Model      |
        +------------------------------+                             +------------------------------+
```

### 2.1 Backend Architecture (`backend/`)
- **Framework**: FastAPI with Pydantic v2 validation.
- **ORM**: SQLAlchemy 2.0 with engine-agnostic field types (`JsonType`, `sa.Uuid`) allowing seamless dual-mode execution on both PostgreSQL and SQLite.
- **Database Schema**: 7 core relational entities (`User`, `AuthIdentity`, `Municipality`, `Place`, `Itinerary`, `ItineraryDay`, `ItineraryItem`).
- **Database Migrations**: Alembic migrations (`0001_initial_schema`, `0002_google_places_and_routing`, `0003_widen_phone_column`) plus dynamic schema backfill (`ensure_user_profile_columns`).
- **Data Catalog**: **2,673 verified places** in Nueva Ecija (2,656 ingested from OpenStreetMap via Overpass API within provincial bounds `15.15 <= lat <= 16.15, 120.70 <= lng <= 121.40` + 17 curated tourist destinations).
- **Recommendation & Routing Engine**:
  - Deterministic Haversine clustering with 25km radius constraint (no cross-province backtracking).
  - 2-Opt traveling salesperson nearest-neighbor route ordering.
  - OSRM public road routing with local geodesic spline fallback for offline reliability.
  - Zero hallucinated venues; 100% grounded in the real POI database.

### 2.2 Web Application (`Project/`)
- **Framework**: Angular 18 (standalone components, zone event coalescing) + Ionic 8 UI toolkit.
- **Styling**: Tailored design tokens conforming to modern Figma specifications. Strict `<10kB` SCSS budget per component.
- **Map Engine**: Leaflet with custom vector pins, MarkerClusterGroup, and OpenStreetMap raster tiles.
- **Offline & Guest Architecture**:
  - Zero demo account dependency. First-class guest mode powered by `@ionic/storage-angular` (`ne_guest_itineraries_v1`).
  - Account migration service (`GuestMigrationService`) transferring guest itineraries to PostgreSQL upon signup or login.
- **Deployment**: Live on GitHub Pages at [https://edselrenz.github.io/Itinerary-App/](https://edselrenz.github.io/Itinerary-App/) and PWA ready.

### 2.3 Native Windows Desktop Client (`desktop_client/`)
- **Framework**: Python 3.12+ with Flet 1.1.2 (Flutter engine bridge for native Windows rendering).
- **Navigation Shell**: Stack-based root layout in [`desktop_client/main.py`](file:///c:/Users/Edward/Desktop/CaseStudy/desktop_client/main.py) with dynamic top workflow headers, bottom navigation bar, and splash screen overlay.
- **Custom Slippy Map Engine** ([`desktop_client/components/slippy_map_canvas.py`](file:///c:/Users/Edward/Desktop/CaseStudy/desktop_client/components/slippy_map_canvas.py)):
  - Pure Python + Flet canvas rendering without heavy web view wrappers.
  - Mercator projection math (`lat_lon_to_tile`, `tile_to_lat_lon`).
  - Thread-pooled tile downloader with memory tile caching and disk tile persistence (`storage/tiles/`).
  - Dynamic window resize handling (`resize_viewport`) recalculating tile grid on window resize or fullscreen toggle.
  - Marker clustering and overscan culling (`[-256, width + 256]`) for smooth 60 FPS panning.
- **Local Persistence**:
  - [`storage/guest_storage.json`](file:///c:/Users/Edward/Desktop/CaseStudy/desktop_client/storage/guest_storage.json): Local guest trips and itineraries.
  - [`storage/ui_prefs.json`](file:///c:/Users/Edward/Desktop/CaseStudy/desktop_client/storage/ui_prefs.json): Persistent UI preferences including dark mode toggle.
  - [`storage/auth_tokens.json`](file:///c:/Users/Edward/Desktop/CaseStudy/desktop_client/storage/auth_tokens.json): Encrypted JWT session tokens.
- **Standalone Binary**: Compiled Win64 executable located at [`dist/NuevaEcijaTravel/NuevaEcijaTravel.exe`](file:///c:/Users/Edward/Desktop/CaseStudy/dist/NuevaEcijaTravel/NuevaEcijaTravel.exe).

---

## 3. Quick Start & Operational Commands

### 3.1 Starting the Complete Environment (Local Development)

#### Option A: One-Click Startup Script (Recommended)
Run the automated orchestrator in PowerShell:
```powershell
.\scripts\start_server.ps1
```
*What this script does:*
1. Checks for Docker and starts the `ne_postgres` PostgreSQL 16 container on port 5432 (or falls back to SQLite).
2. Runs Alembic database migrations.
3. Starts the FastAPI backend daemon on `http://127.0.0.1:8000`.
4. Tests health status via `GET /api/v1/health`.

#### Option B: Manual Service Startup
1. **Start the FastAPI Backend**:
   ```powershell
   python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
2. **Start the Angular / Ionic Web Frontend**:
   ```powershell
   cd Project
   npm start
   ```
   *Web application will be available at `http://localhost:4200`.*
3. **Launch the Native Desktop Application (Dev Mode)**:
   ```powershell
   python desktop_client/main.py
   ```
4. **Launch the Standalone Desktop Executable (Production Build)**:
   ```powershell
   .\dist\NuevaEcijaTravel\NuevaEcijaTravel.exe
   ```

#### Stopping Services
To terminate background backend containers and processes cleanly:
```powershell
.\scripts\stop_server.ps1
```

---

## 4. Test Suite Execution & Verification

Always execute test suites prior to pushing code or creating releases.

### 4.1 Running the Desktop Test Suite (94 Tests)
```powershell
python -m pytest desktop_client/tests/ -v
```
> [!NOTE]
> On Windows, if running under restricted sandboxes, ensure execution allows local loopback sockets or pass `BypassSandbox: true`.

### 4.2 Running the Angular Web Unit Tests (348 Tests)
```powershell
cd Project
npm run test:unit
```

### 4.3 Running the FastAPI Backend Tests (21 Tests)
```powershell
python -m pytest backend/tests/ -v
```

### 4.4 Running the Full Acceptance Gate
```powershell
python scripts/verify_acceptance_gate.py
```
*Validates 24 system-level acceptance checks against real databases and endpoints.*

---

## 5. Production Compilation & Build Guide

### 5.1 Rebuilding the Standalone Windows Executable (.EXE)
The desktop client is packaged into a standalone distribution using PyInstaller:
```powershell
python scripts/build_standalone_exe.py
```
*Build script details:*
- Bundles Python 3.14 + Flet Flutter client libraries.
- Packages high-resolution assets from `assets/` and `desktop_client/assets/`.
- Compiles output to `dist/NuevaEcijaTravel/NuevaEcijaTravel.exe`.
- Automatically checks for and terminates any running instances of `NuevaEcijaTravel.exe` before compiling to prevent Windows `[WinError 5] Access is denied` file lock failures.

### 5.2 Building the Web Application (PWA / Production Bundle)
```powershell
cd Project
npm run build
```
- Outputs optimized static bundles to `Project/www/`.
- Verifies strict `<10kB` SCSS budget rules with 0 budget warnings.

---

## 6. Comprehensive Remediation Log (Phases 54–56)

The table below summarizes the defect clusters resolved and verified in recent development cycles:

| Defect / Feature Area | Summary of Problem & Root Cause | Technical Remediation Applied | Verifying Test / Proof |
| :--- | :--- | :--- | :--- |
| **Navigation Lockout** (`BUG-01`) | Unindented `return` statement in `desktop_client/main.py:navigate_to()` aborted any route transition after initial view mount. | Indented post-update blocks within Section 1 and Section 2 branches. | `test_tc_18_navigation_transitions_not_blocked` |
| **Auth Visual Feedback** (`BUG-02`) | Successful login and signup transitioned to dashboard silently without user feedback. | Wired green snackbar toasts (`show_toast`) on successful login and signup. | Manual verification in live desktop app. |
| **Splash Mouse Interception** (`BUG-03`) | Splash overlay remained in `root_stack.controls` after fade, blocking clicks. | Wired `_on_splash_dismiss()` to remove `splash_overlay` completely from control stack. | Cold boot navigation verification. |
| **Map Watermark Tiles** (`BUG-04`) | Slippy map rendered CartoDB watermark tiles ("API KEY REQUIRED"). | Swapped basemap URL template to clean Carto Light / OpenStreetMap raster tiles. | Screenshot verification & visual audit. |
| **Fullscreen Dynamic Map** (`BUG-05`) | Fullscreening desktop app left map canvas at fixed 1240x740 size. | Added `page.on_resized` listener dispatching `resize_viewport()` on window change. | `test_tc_16_map_canvas_resizing` |
| **Marker Culling Overscan** (`BUG-06`) | Markers popped in/out during fast panning due to tight `[-64, width+64]` culling. | Expanded overscan to `[-256, width+256]`, caching visible markers smoothly. | `test_tc_17_marker_overscan_culling` |
| **Tile Pool Retention** (`BUG-07`) | Tiles were cleared on zoom changes, causing grey visual flashes. | Retained cached tiles across zoom/pan in `_tile_pool`. | 60 FPS zoom panning validation. |
| **Route Map Callback** (`BUG-08`) | `on_stop_click` crashed with `TypeError` when passed 2 args (`day_num, stop_idx`). | Added `inspect.signature` inspection supporting both 1-arg and 2-arg callbacks. | `test_tc_12_route_map_callback` |
| **Budget Null-Safety** (`BUG-10`) | `daily_budget = None` caused string format crash in trip cards. | Guarded budget formatting with safe float defaulting (`2500.0`). | `test_tc_10_budget_null_safety` |
| **Step 2 POI Scroll** (`BUG-11`) | ResponsiveRow in Custom Builder overflowed viewport without scrolling. | Wrapped grid in `ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)`. | 2,673 POI catalog scroll test. |
| **Settings & Dark Mode** (`BUG-12`) | Dark mode did not persist across app restarts; missing palette aliases. | Added `surface_primary` and `border_color` aliases; persisted to `storage/ui_prefs.json`. | UI theme restart test. |
| **Fast API Failover** (`BUG-13`) | 10s connect timeout caused app freeze when backend was offline. | Reduced connect timeout to 2.5s for fast, responsive guest mode failover. | Offline boot test. |

---

## 7. Critical Architectural Rules & Invariants for Incoming Developers

1. **Zero Demo Accounts Policy**:
   - Do **NOT** introduce hardcoded demo credentials, mock user bypasses, or fake login shortcuts.
   - The application is designed to be fully functional in **Guest Mode** (offline-first). Users can plan itineraries, explore the map, and save trips without ever creating an account.
2. **Dual Database Engine Compatibility**:
   - All SQLAlchemy models must use `JsonType` and `sa.Uuid` from `backend/app/core/database.py`. Never use PostgreSQL-only primitives (such as raw `JSONB` or `UUID` without fallback) in shared models.
3. **Desktop Sizing & Layout Geometry**:
   - The desktop client targets a minimum resolution of `1024x600` and default resolution of `1366x768`.
   - Never hardcode fixed full-screen dimensions without listening to `page.on_resized`.
4. **PyInstaller Binary Rebuilds**:
   - Always verify that `NuevaEcijaTravel.exe` is not currently running before executing PyInstaller. If running, terminate it using `taskkill /IM NuevaEcijaTravel.exe /F` to avoid file-locking permissions errors.
5. **Clickable Links Mandatory**:
   - All file references in documentation, pull requests, and agent responses must use clickable GitHub-style markdown links with forward slashes (`[filename](file:///c:/Users/Edward/Desktop/CaseStudy/...)`).

---

## 8. Master File Registry & Relevant Code Locations

### 8.1 Native Desktop Application (`desktop_client/`)
- [`desktop_client/main.py`](file:///c:/Users/Edward/Desktop/CaseStudy/desktop_client/main.py): Application entry point, window configuration, router, and root stack shell.
- [`desktop_client/components/slippy_map_canvas.py`](file:///c:/Users/Edward/Desktop/CaseStudy/desktop_client/components/slippy_map_canvas.py): Interactive tile map engine, zoom/pan gesture detectors, and vector marker layers.
- [`desktop_client/components/itinerary_route_map.py`](file:///c:/Users/Edward/Desktop/CaseStudy/desktop_client/components/itinerary_route_map.py): Multi-day itinerary route map with turn-by-turn road polylines.
- [`desktop_client/components/nav_bars.py`](file:///c:/Users/Edward/Desktop/CaseStudy/desktop_client/components/nav_bars.py): Bottom navigation bar and top workflow header.
- [`desktop_client/components/destination_picker.py`](file:///c:/Users/Edward/Desktop/CaseStudy/desktop_client/components/destination_picker.py): Destination search and municipality picker.
- [`desktop_client/views/dashboard_view.py`](file:///c:/Users/Edward/Desktop/CaseStudy/desktop_client/views/dashboard_view.py): Home dashboard with quick action cards and popular destinations carousel.
- [`desktop_client/views/places_view.py`](file:///c:/Users/Edward/Desktop/CaseStudy/desktop_client/views/places_view.py): Map tab view with filter modal, search bar, and POI drawer.
- [`desktop_client/views/suggested_wizard_view.py`](file:///c:/Users/Edward/Desktop/CaseStudy/desktop_client/views/suggested_wizard_view.py): 3-step automated itinerary generation wizard.
- [`desktop_client/views/custom_builder_view.py`](file:///c:/Users/Edward/Desktop/CaseStudy/desktop_client/views/custom_builder_view.py): Multi-day custom itinerary builder and timeline editor.
- [`desktop_client/views/trip_detail_view.py`](file:///c:/Users/Edward/Desktop/CaseStudy/desktop_client/views/trip_detail_view.py): Single itinerary view with timeline, commute cards, and route preview.
- [`desktop_client/views/saved_trips_view.py`](file:///c:/Users/Edward/Desktop/CaseStudy/desktop_client/views/saved_trips_view.py): Saved trips manager with search, filtering, and deletion dialogs.
- [`desktop_client/views/profile_view.py`](file:///c:/Users/Edward/Desktop/CaseStudy/desktop_client/views/profile_view.py): Traveler profile, guest trip migration, settings, and logout dialog.
- [`desktop_client/views/login_view.py`](file:///c:/Users/Edward/Desktop/CaseStudy/desktop_client/views/login_view.py): Traveler authentication view with visual toast feedback.
- [`desktop_client/views/signup_view.py`](file:///c:/Users/Edward/Desktop/CaseStudy/desktop_client/views/signup_view.py): Traveler registration view with visual toast feedback.
- [`desktop_client/services/auth_service.py`](file:///c:/Users/Edward/Desktop/CaseStudy/desktop_client/services/auth_service.py): Authentication state, token storage, and guest session management.
- [`desktop_client/services/itinerary_service.py`](file:///c:/Users/Edward/Desktop/CaseStudy/desktop_client/services/itinerary_service.py): Itinerary CRUD, offline suggestion generator, and 2-Opt TSP routing.
- [`desktop_client/services/place_service.py`](file:///c:/Users/Edward/Desktop/CaseStudy/desktop_client/services/place_service.py): Bounded spatial search, category filtering, and municipality lookups.
- [`desktop_client/core/api_client.py`](file:///c:/Users/Edward/Desktop/CaseStudy/desktop_client/core/api_client.py): HTTP client with 2.5s connect timeout and offline trapping.
- [`desktop_client/core/storage.py`](file:///c:/Users/Edward/Desktop/CaseStudy/desktop_client/core/storage.py): JSON file persistence engine for guest trips and tokens.
- [`desktop_client/config/settings.py`](file:///c:/Users/Edward/Desktop/CaseStudy/desktop_client/config/settings.py): Theme tokens, color palettes, and persistent settings.

### 8.2 Web Application (`Project/`)
- [`Project/src/app/tabs/home/home.page.ts`](file:///c:/Users/Edward/Desktop/CaseStudy/Project/src/app/tabs/home/home.page.ts): Home tab with debounced search and destination carousel.
- [`Project/src/app/tabs/map/map.page.ts`](file:///c:/Users/Edward/Desktop/CaseStudy/Project/src/app/tabs/map/map.page.ts): Leaflet map view with category filters and POI bottom sheet.
- [`Project/src/app/tabs/history/history.page.ts`](file:///c:/Users/Edward/Desktop/CaseStudy/Project/src/app/tabs/history/history.page.ts): Saved itineraries tab with guest mode synchronization.
- [`Project/src/app/tabs/profile/profile.page.ts`](file:///c:/Users/Edward/Desktop/CaseStudy/Project/src/app/tabs/profile/profile.page.ts): User profile, guest sync button, and app settings.
- [`Project/src/app/features/itinerary/custom-builder/custom-builder.page.ts`](file:///c:/Users/Edward/Desktop/CaseStudy/Project/src/app/features/itinerary/custom-builder/custom-builder.page.ts): Custom itinerary builder page.
- [`Project/src/app/features/itinerary/suggested-wizard/suggested-wizard.page.ts`](file:///c:/Users/Edward/Desktop/CaseStudy/Project/src/app/features/itinerary/suggested-wizard/suggested-wizard.page.ts): Suggested itinerary questionnaire and preview sheet.
- [`Project/src/app/core/services/itinerary.service.ts`](file:///c:/Users/Edward/Desktop/CaseStudy/Project/src/app/core/services/itinerary.service.ts): Dual-path persistence service (REST + IndexedDB).
- [`Project/src/app/core/services/place.service.ts`](file:///c:/Users/Edward/Desktop/CaseStudy/Project/src/app/core/services/place.service.ts): POI retrieval and spatial caching service.
- [`Project/src/app/core/services/auth.service.ts`](file:///c:/Users/Edward/Desktop/CaseStudy/Project/src/app/core/services/auth.service.ts): Authentication, token rotation, and guest session management.

### 8.3 FastAPI Backend (`backend/`)
- [`backend/app/main.py`](file:///c:/Users/Edward/Desktop/CaseStudy/backend/app/main.py): FastAPI initialization, CORS middleware, and route mounting.
- [`backend/app/api/v1/auth.py`](file:///c:/Users/Edward/Desktop/CaseStudy/backend/app/api/v1/auth.py): Registration, login, token refresh, and user profile endpoints.
- [`backend/app/api/v1/places.py`](file:///c:/Users/Edward/Desktop/CaseStudy/backend/app/api/v1/places.py): Bounding box spatial search, category filters, and detail endpoints.
- [`backend/app/api/v1/municipalities.py`](file:///c:/Users/Edward/Desktop/CaseStudy/backend/app/api/v1/municipalities.py): Municipalities listing and fuzzy search.
- [`backend/app/api/v1/itineraries.py`](file:///c:/Users/Edward/Desktop/CaseStudy/backend/app/api/v1/itineraries.py): Itinerary CRUD, stop reordering, and recommendation endpoints.
- [`backend/app/models/entities.py`](file:///c:/Users/Edward/Desktop/CaseStudy/backend/app/models/entities.py): SQLAlchemy 2.0 ORM schemas.
- [`backend/app/algorithms/itinerary_generator.py`](file:///c:/Users/Edward/Desktop/CaseStudy/backend/app/algorithms/itinerary_generator.py): Deterministic clustering and 2-Opt TSP engine.

### 8.4 Infrastructure & Operations Scripts
- [`scripts/start_server.ps1`](file:///c:/Users/Edward/Desktop/CaseStudy/scripts/start_server.ps1): Automated environment launcher.
- [`scripts/stop_server.ps1`](file:///c:/Users/Edward/Desktop/CaseStudy/scripts/stop_server.ps1): Environment teardown script.
- [`scripts/build_standalone_exe.py`](file:///c:/Users/Edward/Desktop/CaseStudy/scripts/build_standalone_exe.py): Standalone Windows executable compiler.
- [`scripts/verify_acceptance_gate.py`](file:///c:/Users/Edward/Desktop/CaseStudy/scripts/verify_acceptance_gate.py): 24-point acceptance validation gate.

---

## 9. Handover Checklist for Incoming Engineers

Before cutting releases or implementing new features, verify the following checklist:

- [ ] **Docker PostgreSQL Running**: Execute `docker ps` to verify `ne_postgres` is active on port 5432 (or verify SQLite fallback boots cleanly).
- [ ] **FastAPI Health Check**: Access `http://127.0.0.1:8000/api/v1/health` and verify HTTP 200 `status: healthy`.
- [ ] **Desktop Test Suite Passing**: Run `python -m pytest desktop_client/tests/ -v` and verify **104/104 passed**.
- [ ] **Web Test Suite Passing**: Run `npm --prefix Project run test:unit` and verify **348/348 passed**.
- [ ] **Backend Test Suite Passing**: Run `python -m pytest backend/tests/ -v` and verify **21/21 passed**.
- [ ] **Standalone Executable Built**: Verify [`dist/NuevaEcijaTravel/NuevaEcijaTravel.exe`](file:///c:/Users/Edward/Desktop/CaseStudy/dist/NuevaEcijaTravel/NuevaEcijaTravel.exe) launches cleanly without console errors or missing DLL popups.
- [ ] **Documentation Synced**: Ensure any newly added endpoints, models, or UI features are documented in [`docs/TODO.md`](file:///c:/Users/Edward/Desktop/CaseStudy/docs/TODO.md), [`docs/PROJECT_STATE.md`](file:///c:/Users/Edward/Desktop/CaseStudy/docs/PROJECT_STATE.md), and [`docs/KNOWN_ISSUES.md`](file:///c:/Users/Edward/Desktop/CaseStudy/docs/KNOWN_ISSUES.md).

---

## 10. Completed Staging: Cycle 5 Desktop Map Deep-Dive QA Audit & 1:1 Web Parity Plan (Phase 57)

Per [`desktop_web_parity_qa_and_implementation_plan (8).md`](file:///c:/Users/Edward/Desktop/CaseStudy/desktop_web_parity_qa_and_implementation_plan%20(8).md), Phase 57 has been completely built, verified, and documented across all ledgers:

1. **`MAP-BUG-01` to `MAP-BUG-03`, `MAP-BUG-11` (Zero 403 Hazard Tiles & Watermark Elimination)**:
   - Eliminated raw `https://*.tile.openstreetmap.org` URLs passed to `ft.Image.src` (which triggers Dart `io.HttpClient` 403 blocks).
   - Python-only multi-mirror tile fetcher (OSM Standard with custom headers + OSM France + OSM HOT fallback) with instant SVG data URI placeholders.
   - Fixed ocean and rural tile rejection: accept valid PNGs of any size `>= 67` bytes, dynamically swapping freshly cached tiles into the active canvas via `on_tile_cached`.
   - Purged and permanently banned Carto watermark tiles (`API KEY REQUIRED carto.com/basemaps/apikey`).
2. **`MAP-BUG-04` (Purged 38 Stale ESRI RGB Tiles)**:
   - Automatically purged stale `'RGB'`-mode ESRI ArcGIS World Street Map tiles (`color_type == 2`, beige background `(246, 240, 218)`) from `assets/tiles_cache/` on startup.
3. **`MAP-BUG-05` (60 FPS GPU-Smooth Dragging & Continuous Clamping)**:
   - Dedicated lightweight container translations with 16ms throttling (~60 FPS), eliminating full control tree re-serialization during pan drags.
   - Continuously clamp prospective coordinates during drag to eliminate violent boundary snap-back on mouse release.
4. **`MAP-BUG-06` (Cursor-Centered Mouse Wheel Zooming)**:
   - Compute geographic coordinate under cursor and adjust center coordinates at the new zoom level (Leaflet `zoomAround` parity).
5. **`MAP-BUG-07` (Web-Parity Clustering Up to Z15 & Zero Dropped Pins)**:
   - Match Web Leaflet `disableClusteringAtZoom: 16` (`maxClusterRadius: 40`), clustering up to Z15 and raising the render cap to 160 markers at Z16–Z18.
6. **`MAP-BUG-08` to `MAP-BUG-10` (In-Map Interactive Bottom Sheet, 10 Deep-Link Query Params & UI Polish)**:
   - Implemented in-map non-blocking POI bottom sheet card (`<app-place-detail-sheet>` parity) with Favorite heart, Commute Guide, and Primary Actions: **`✨ Start Trip Here`**, **`+ Add to Trip`**, and **`Get Directions`**.
   - Parsed all 10 Web-compatible deep-link query parameters (`itineraryId`, `followRoute`, `day`/`dayNumber`, `lat`, `lng`, `placeId`, `destination`, `municipality`, `category`, `priceTier`, `search`).
   - Added horizontal scroll chevrons (`‹` / `›`) to category pills and styled right FABs as 44×44 circular pills with semantic colors.
   - Replaced raw `self.page.overlay.append(dlg)` in `date_range_dialog.py:205` with `present_dialog()`.
7. **`MAP-BUG-12` (Fullscreen Maximization & Theme Compatibility)**:
   - Fixed `_on_page_resize(e)` to extract dynamic logical pixels `getattr(e, "width", None) or page.window.width or page.width` and dispatches to active views.
   - Added `horizontal_alignment=ft.CrossAxisAlignment.STRETCH` on `main_column` and `width=float("inf")` on `content_area` and `PlacesView`.
   - Standalone Windows executable recompiled: [`dist/NuevaEcijaTravel/NuevaEcijaTravel.exe`](file:///c:/Users/Edward/Desktop/CaseStudy/dist/NuevaEcijaTravel/NuevaEcijaTravel.exe) (15.31 MB, 406.30 MB bundled distribution).

---

## 11. Multi-Platform Packaging, Android APK & Inno Setup Release Pipeline (Phase 61)

Phase 61 provides production-grade release packaging and automated deployment infrastructure across all target platforms:

1. **Android Capacitor Platform Hardening**:
   - `Project/src/main.ts`: Isolated Angular Service Worker to web-only (`!isDevMode() && !Capacitor.isNativePlatform()`), eliminating Android WebView asset lockups and stale cache collisions.
   - `Project/src/app/app.component.ts`: Configured native status bar styling (`StatusBar.setStyle({ style: Style.Light })`, `StatusBar.setBackgroundColor({ color: '#ffffff' })`) and Android hardware back-button listener via `App.addListener('backButton')`.
   - `Project/android/app/build.gradle`: Configured `signingConfigs.release` reading `keystore.properties` with fallback to debug signing when local release keystore is absent.
2. **Cross-Platform CORS Parity**:
   - `cloudflare-worker/worker.js`: Added `http://localhost` and `https://localhost` to `ALLOWED_ORIGINS` to permit API calls from the Capacitor Android WebView.
   - `backend/app/core/config.py`: Added `https://localhost` to `cors_origins` and updated `cors_origin_regex` to match `^(http|https)://(localhost|127\.0\.0\.1)(:\d+)?$`.
3. **Desktop Storage Hardening for Inno Setup / Program Files**:
   - `desktop_client/config/settings.py`: Implemented `.write_probe` test in `storage/`; if running in read-only or elevated directories (such as `C:\Program Files\NuevaEcijaTravel`), user data and tile caches automatically divert to `%LOCALAPPDATA%\NuevaEcijaTravel\storage`.
4. **CI/CD Cloud & Local Packaging Pipeline**:
   - `.github/workflows/release-builds.yml`: Cloud GitHub Actions workflow for building Windows PyInstaller standalone, Inno Setup installer (`NuevaEcijaTravel-Setup-x64.exe`), and Android release/debug APKs (`app-release.apk` / `app-debug.apk`) upon tag creation (`v*.*.*`) or manual workflow dispatch.
   - `installer/NuevaEcijaTravel.iss`: Production Inno Setup 6 installer definition with desktop icon creation, Start Menu shortcuts, and uninstaller.
   - `scripts/build_android_apk.ps1`: Local automation script for Ionic build, Capacitor sync, and Gradle APK compilation.
   - `scripts/build_desktop_installer.ps1`: Local automation script for packaging PyInstaller executable and compiling Inno Setup installer.
   - `scripts/build_standalone_exe.py`: Upgraded with `_ensure_ico_file()` generating `app_icon.ico` from `favicon.png`, PyInstaller `--icon` flag, hidden imports (`desktop_client.core.geo`, `desktop_client.components.date_range_dialog`, `dotenv`), and fallback `.env` generation.

---

## 12. Release Pipeline Hardening & Code Review Remediation (Phase 61.1)

Phase 61.1 resolves all 4 findings from the post-Phase 61 architectural code review (`PKG-REV-01` to `PKG-REV-04`):

1. **`PKG-REV-01` (SlippyMapCanvas Assets & Tile Cache Resolution)**:
   - Replaced hardcoded `Path(__file__)` in `desktop_client/components/slippy_map_canvas.py` with `_ASSETS_DIR = get_settings().assets_dir`.
   - Implemented `_resolve_writable_tile_cache_dir()` with write-probe (`.write_probe`), gracefully redirecting tile caching to `get_settings().storage_dir / "tiles_cache"` with absolute pathing if running in a read-only installation directory (`C:\Program Files\NuevaEcijaTravel`).
2. **`PKG-REV-02` (Flet Runtime Client Auto-Provisioning)**:
   - In `scripts/build_standalone_exe.py`: Embedded `flet_desktop.ensure_client_cached()` fallback to provision the Flet client on clean environments where the app has never run locally.
3. **`PKG-REV-03` (TripDetailView Route Navigation Contract)**:
   - In `desktop_client/views/trip_detail_view.py`: `_launch_in_app_nav` now passes `self.itinerary` as the second argument and includes `dayNumber={day_num}`, maintaining 100% contract parity with `_open_full_map()`.
4. **`PKG-REV-04` (Theme Palette Dark-Mode Alignment & Gitignore Cleanup)**:
   - In `desktop_client/views/places_view.py`: Replaced hardcoded `#f8fafc`, `#ffffff`, `#0f172a`, and `#e2e8f0` in `_build_drawer_row` and `_build_poi_bottom_sheet` with dynamic tokens from `get_settings().palette`.
   - In `.gitignore`: Removed trailing `for_updates` line and added `dist_apk/` and `dist_installer/`.
5. **Automated Regression Coverage (`TC-35` & `TC-36`)**:
   - Added `test_tc_35_slippy_map_assets_dir_uses_settings_and_writable_cache` and `test_tc_36_trip_detail_in_app_nav_passes_itinerary_and_day_number` to `desktop_client/tests/test_cycle2_regressions.py`.
   - Full desktop regression test suite: **115 / 115 passed (100% green)** in 6.27s.

---

## 13. Dual-Platform Release Packaging & Database CLI Tooling (Phase 62)

Phase 62 executes the full release packaging pipeline across Windows Desktop and Android Mobile, aligns build scripts, and adds interactive database inspection tooling:

1. **Compiled Release Deliverables (Excluded from Git Tracking via `.gitignore`)**:
   - **Windows Single-File Installer**: `dist_installer\NuevaEcijaTravel_Setup_v1.0.0.exe` (`156.58 MB` / `164,181,396` bytes, SHA-256: `3D08D6BAE3EB3926C0AFEA4FEB211D8BAF2FA9F36D1B0FA241F9EDE50CDFF410`).
   - **Windows Portable Zero-Admin Archive**: `dist_installer\NuevaEcijaTravel_Portable_Installer_v1.0.0.zip` (`232.64 MB` / `243,942,337` bytes, SHA-256: `3ED786E2FB9F0EE6E65373C0DBD56C3EF9E8B3C819D6227E36068FE936917708`).
   - **Android Debug APK**: `dist_apk\TripMoTripKo-debug.apk` (`30.88 MB` / `32,378,996` bytes, SHA-256: `C611658A662C68967B8174E1963C69AE74AA6D0945D3B4106AB7701DF03AB4EB`).
   - **Android Signed Release APK**: `dist_apk\TripMoTripKo-release.apk` (`29.72 MB` / `31,162,864` bytes, SHA-256: `0C5CED791D824CD81DF294198481C9F99E9175DC1AA336123B5B1E32BE1E80C6`).
2. **Build Pipeline & Gradle Wrapper Alignment**:
   - [`Project/android/gradle/wrapper/gradle-wrapper.properties`](file:///c:/Users/Edward/Desktop/CaseStudy/Project/android/gradle/wrapper/gradle-wrapper.properties): Pinned `distributionUrl` to `gradle-8.13-bin.zip` for Android Gradle Plugin 8.13.0 compatibility.
   - [`Project/android/gradle.properties`](file:///c:/Users/Edward/Desktop/CaseStudy/Project/android/gradle.properties): Added `android.builder.sdkDownload=true` for automated Android SDK component provisioning.
   - [`scripts/build_android_apk.ps1`](file:///c:/Users/Edward/Desktop/CaseStudy/scripts/build_android_apk.ps1) & [`.github/workflows/release-builds.yml`](file:///c:/Users/Edward/Desktop/CaseStudy/.github/workflows/release-builds.yml): Updated Angular production build flag from `--service-worker=false` to `--no-service-worker`.
   - [`scripts/build_desktop_installer.ps1`](file:///c:/Users/Edward/Desktop/CaseStudy/scripts/build_desktop_installer.ps1): Refactored `Install_And_Launch.bat` generation into `$InstallBatLines` array to prevent PowerShell string interpolation issues.
3. **Interactive Database Query CLI ([`scripts/db_query.py`](file:///c:/Users/Edward/Desktop/CaseStudy/scripts/db_query.py))**:
   - Supports one-shot SQL queries, `--tables` row count overview, and an interactive SQL prompt across both local SQLite (`nueva_ecija_travel.db`) and Docker PostgreSQL (`--postgres`).

