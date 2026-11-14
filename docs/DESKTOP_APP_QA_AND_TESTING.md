# Desktop Application QA, QC & Verification Report

**Application Under Test**: Nueva Ecija Travel Desktop Client ("Trip mo, trip ko")  
**Framework**: Python Flet >= 1.1.2 + `flet-map`  
**Testing Harness**: Pytest 9.2 + AnyIO + Python 3.14  
**Audit Status**: Verified & Remediated  
**Document Ref**: `docs/DESKTOP_APP_QA_AND_TESTING.md`  

---

## 1. Executive QA Audit Summary

An independent, rigorous quality assurance evaluation was conducted across the desktop client (`desktop_client/`), comparing its runtime behavior, navigation ergonomics, mapping capabilities, and API contracts against the canonical web application (`Project/`) and FastAPI backend (`backend/`).

### Empirical Test Execution Results
* **Desktop Unit & Parity Test Suite (`desktop_client/tests/`)**: **43 passed, 0 failed, 1 deselected in 1.28s**.
* **Live FastAPI & SQLite Integration Suite**: **1 passed (100%) in 2.42s** (`test_live_backend_integration`).
* **Cross-Application Web Regression Suite (`Project/`)**: **32 test files passed, 348 passed, 0 failed in 75.73s** via Vitest (`npm --prefix Project run test:unit`) with zero regressions and zero edits in `Project/`.
* **Standalone Executable Distribution**: Successfully compiled via PyInstaller (`NuevaEcijaTravel.spec`) into `dist/NuevaEcijaTravel/NuevaEcijaTravel.exe` bundling all 42 local assets.

---

## 2. Master Defect Ledger & Resolution Matrix

The evaluation spans three defect groups: the deep architectural discrepancies (`QA-01` to `QA-14`), the baseline integration discrepancies (`DEF-01` to `DEF-15`), and dynamic runtime defects (`BUG-01` to `BUG-08`):

### 2.1 Deep QA Audit & Architectural Defects (`QA-01` to `QA-14`)

| Defect ID | Severity | Layer | Summary of Defect | Architectural Resolution |
| :---: | :---: | :--- | :--- | :--- |
| **`QA-01`** | **Critical** | Navigation | Side menu layout (`SidebarNav` + `TopHeader`) instead of Web App Bottom Tab Bar. | Delete `SidebarNav` and `TopHeader`. Implement `60px` `BottomTabBar` shown ONLY on `/home`, `/map`, `/saved`, `/profile`. Full-screen workflow views use contextual `.figma-header-bar`. |
| **`QA-02`** | **Critical** | GIS Maps | Complete absence of true interactive map tab and embedded day route maps. | Implement full-screen `MapView` with `flet-map` (OSM tiles, 16 category pins, filter drawer, Follow-Route mode) and `180px` collapsible `ItineraryRouteMap` embedded in Wizard, Builder, and Detail. |
| **`QA-03`** | **Critical** | Connectivity | Missing web-style server connection banner, retry action, and custom API URL support. | Implement `ConnectivityService` (`GET {url}/health`) + Global Floating `OfflineHostBanner` overlaid at top of root `ft.Stack` across all views with `[Retry]` and `[X]`, plus Settings URL config. |
| **`QA-04`** | **Critical** | Offline Fallback| Server offline throws `NetworkError`, showing 0 places and blocking suggested generator. | Port 3-tier fallback: (1) load 2,673 OSM places + 12 curated places in `PlaceService`; (2) port `generate_offline_suggested_itinerary()` clustering; (3) fallback writes to `guest_storage.json`. |
| **`QA-05`** | **High** | Auth & UI | Redundant Demo Account (`Pattranite Persona`) and dead Google/Apple social buttons. | Strictly remove Demo persona and dead social buttons. Standardize on clean Email/Password login, 6-field signup, `Forgot password?` modal, and Guest mode. |
| **`QA-06`** | **High** | UI Polish | Fake notification bell and unresolved local asset photography paths. | Wire notification bell to Travel Advisories Drawer (`UI-19`). Resolve local photography through `resolve_place_image()`. |
| **`QA-07`** | **Critical** | Saved Trips | `SavedTripsView` crashes with `AttributeError: 'Itinerary' object has no attribute 'total_days'`. | Add `total_days` and `days_nights_label` properties to `Itinerary`. |
| **`QA-08`** | **Critical** | Place API | `PlacesView._fetch_places` raises silent `TypeError` on every query due to parameter mismatch. | Align parameter names to `municipality_id` and `sort` in `PlaceService.get_places()`. |
| **`QA-09`** | **Critical** | Guest Sync | `ProfileView._sync_guest_trips` crashes with `AttributeError: 'AuthService' object has no attribute 'migrate_guest_trips'`. | Implement `migrate_guest_trips()` in `AuthService` and `ItineraryService`. |
| **`QA-10`** | **Critical** | Itinerary | `ItineraryService.generate_suggested_itinerary` raises `NameError: name 'ApiClientError' is not defined`. | Import `ApiClientError` and `NetworkError` from `core.api_client`. |
| **`QA-11`** | **High** | Routing | Clicking saved trip card on Home reloads dashboard instead of opening `TripDetailView`. | Pass `itin` in `on_navigate(f"/trips/{itin.id}", itin)` and enable ID lookup fallback in `main.py`. |
| **`QA-12`** | **Critical** | Async Loop | Calling bare `asyncio.run()` inside running Flet event loop raises `RuntimeError`. | Route all async UI tasks through loop-safe `run_async()`. |
| **`QA-13`** | **High** | Theming | Dark Mode toggle leaves views and cards hardcoded to light mode colors. | Implement reactive `ThemePalette` tokens across all views and controls. |
| **`QA-14`** | **High** | Data Passing | `+ Add to Trip` drops selected place; `SignupView` drops `M.I.` and lacks username auto-suggest. | Pass pre-added place to builder route; persist `M.I.` in profile extra and auto-suggest usernames. |

---

### 2.2 Baseline QA Defect Ledger (`DEF-01` to `DEF-15`)

| Defect ID | Severity | Layer | Summary of Defect | Resolution in Desktop Client |
| :---: | :---: | :--- | :--- | :--- |
| **`DEF-01`** | Critical | Auth GUI | `RuntimeError` on form submission | Replaced `asyncio.run()` with `safe_page.run_task` / `run_async()`. |
| **`DEF-02`** | Critical | Auth API | Registration 422 Unprocessable Content | Rebuilt registration payload to send `first_name`, `last_name`, `username`. |
| **`DEF-03`** | Critical | Catalog | Explore Places crashes with 0 POIs | Added safe null-coalescing for category filter selection. |
| **`DEF-04`** | Critical | ApiClient | Remote backend connection impossible | Dynamically parse host and port from `self.base_url`. |
| **`DEF-05`** | Critical | Itinerary | Stop reordering fails on cloud server | Fixed endpoint to `POST /itineraries/{id}/reorder`. |
| **`DEF-06`** | High | Place API | Search queries fail to filter on server | Remapped parameters to `q`, `limit`, `offset`, `featured`. |
| **`DEF-07`** | High | User Model | Name displays blank in sidebar | Added parsing for `first_name`, `last_name`, `username_normalized`. |
| **`DEF-08`** | High | Profile API | Profile name edit dropped by server | Split `full_name` into `first_name` and `last_name` in `UserUpdatePayload`. |
| **`DEF-09`** | High | Itinerary | Metadata update fails with HTTP 405 | Changed HTTP method from `PUT` to `PATCH /itineraries/{id}`. |
| **`DEF-10`** | High | Config | `.env` runtime settings ignored | Added `load_dotenv()` call during configuration initialization. |
| **`DEF-11`** | Medium | Itinerary | Missing import on generation error | Imported `ApiClientError` in `itinerary_service.py`. |
| **`DEF-12`** | Medium | Place API | Querying categories returns HTTP 422 | Replaced invalid endpoint with `CANONICAL_CATEGORIES` constant. |
| **`DEF-13`** | Medium | Signup UI | Misleading 6-character password check | Updated validator to enforce `>= 8` characters matching backend. |
| **`DEF-14`** | Medium | Muni Model | Municipality coordinates parsed as None | Mapped `center_lat` and `center_lng` to `latitude` and `longitude`. |
| **`DEF-15`** | Low | UI Style | Low text contrast failing WCAG AA | Darkened `TEXT_MUTED_LIGHT` to `#475569` (4.8:1 contrast ratio). |

---

## 3. Test Suites & Execution Instructions

### 3.1 Running Desktop Unit & Parity Tests
```powershell
# From repository root (Windows PowerShell)
python -m pytest desktop_client/tests/ -v -k "not test_live_backend_integration"
```
**Test Coverage Breakdown (43 Tests Passing)**:
* `test_api_client.py` (4 tests): Client initialization, token injection, custom headers, exception hierarchy.
* `test_auth_service.py` (3 tests): Guest mode transitions, authenticated session flow, session listener notifications.
* `test_itinerary_service.py` (3 tests): Itinerary metrics, day metrics, suggested request serialization.
* `test_parity_services_and_components.py` (8 tests): 32 LGU coverage, canonical offline places integrity, commute guide lookups, Haversine leg commute distance/display, favorites service lifecycle, theme palette switching, view instantiation, pending changes guard.
* `test_place_service.py` (4 tests): Honest pricing formatting, category formatting, municipality model, paginated places model.
* `test_qa_remediation.py` (9 tests): Verification of fixes for DEF-02, DEF-07, DEF-08, DEF-14, DEF-06, DEF-12, DEF-04, DEF-09, DEF-05, and DEF-15.
* `test_storage_export.py` (4 tests): RFC 5545 iCalendar generation, Markdown export, JSON export, guest storage CRUD.
* `test_ui_consistency.py` (8 tests): Brand tokens, settings title, canonical LGUs, card instantiation, unmounted safe updates, guest flow.

### 3.2 Running Live Backend Integration Tests
1. **Start Backend Server**:
   ```powershell
   python -m uvicorn backend.app.main:app --port 8000
   ```
2. **Execute Live Integration Suite**:
   ```powershell
   python -m pytest desktop_client/tests/test_live_integration.py -v
   ```

### 3.3 Running Web Client Regression Suite
```powershell
npm --prefix Project run test:unit
```
**Result**: 32 test files passed, 348 tests passed, 0 failures.
