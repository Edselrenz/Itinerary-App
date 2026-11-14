# Desktop Application QA, QC & Verification Report

**Application Under Test**: Nueva Ecija Travel Desktop Client ("Trip mo, trip ko")  
**Framework**: Python Flet >= 1.1.2  
**Testing Harness**: Pytest 9.2 + AnyIO + Python 3.14  
**Audit Status**: Verified & Remediated  
**Document Ref**: `docs/DESKTOP_APP_QA_AND_TESTING.md`  

---

## 1. Executive QA Audit Summary

An independent, rigorous quality assurance evaluation was conducted across the desktop client (`desktop_client/`), comparing its runtime behavior and API contracts against the canonical web application (`Project/`) and FastAPI backend (`backend/`).

### Empirical Test Execution Results
* **Desktop Unit Test Suite (`desktop_client/tests/`)**: **35 passed, 0 failed, 1 deselected in 1.98s**.
* **Live FastAPI & SQLite Integration Suite**: **1 passed (100%) in 2.42s** (`test_live_backend_integration`).
* **Cross-Application Web Regression Suite (`Project/`)**: **32 test files passed, 348 passed, 0 failed in 26.34s** via Vitest (`npm --prefix Project run test:unit`).

---

## 2. Master Defect Ledger & Resolution Matrix

The audit identified two categories of defects: the initial architectural discrepancies (`DEF-01` to `DEF-15`) and dynamic runtime defects (`BUG-01` to `BUG-08`):

### 2.1 Critical Runtime Defects (`BUG-01` to `BUG-08`)

| Defect ID | Severity | Component | Root Cause | Implemented Resolution | Verification Status |
| :---: | :---: | :--- | :--- | :--- | :---: |
| **`BUG-01`** | **Critical** | `views/saved_trips_view.py` | `_create_trip_card()` accesses missing `itin.total_days`. | Added `total_days` and `days_nights_label` properties to `Itinerary`. | **VERIFIED** |
| **`BUG-02`** | **Critical** | `views/places_view.py` | `_fetch_places()` passes `municipality` & `sort_by` kwargs. | Fixed arguments to `municipality_id` and `sort` in `places_view.py`. | **VERIFIED** |
| **`BUG-03`** | **Critical** | `views/profile_view.py` | `AuthService.migrate_guest_trips()` missing on click. | Implemented `migrate_guest_trips()` in `auth_service.py`. | **VERIFIED** |
| **`BUG-04`** | **Critical** | `services/itinerary_service.py` | `ApiClientError` missing from module imports. | Imported `ApiClientError` from `core.api_client`. | **VERIFIED** |
| **`BUG-05`** | **High** | `views/dashboard_view.py` | Saved trip card click fails to resolve `TripDetailView`. | Updated router in `main.py` to resolve trip ID from storage/service. | **VERIFIED** |
| **`BUG-06`** | **Critical** | `views/login_view.py` | `asyncio.run()` called inside active Flet loop. | Implemented `run_async()` in `core/async_utils.py`. | **VERIFIED** |
| **`BUG-07`** | **High** | `main.py` & All Views | Dark mode toggle leaves cards and text hardcoded light. | Implemented `ThemePalette` and dynamic shell re-theming. | **VERIFIED** |
| **`BUG-08`** | **High** | `views/places_view.py` | 1. `+ Add to Trip` discards place. 2. Socket check hardcodes IP. | 1. Pre-load place into Builder. 2. Parse host/port from `base_url`. | **VERIFIED** |

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

### 3.1 Running Desktop Unit Tests
```powershell
# From repository root (Windows PowerShell)
python -m pytest desktop_client/tests/ -v -k "not test_live_backend_integration"
```
**Test Coverage Breakdown**:
* `test_api_client.py` (4 tests): Client initialization, token injection, custom headers, exception hierarchy.
* `test_auth_service.py` (3 tests): Guest mode transitions, authenticated session flow, session listener notifications.
* `test_itinerary_service.py` (3 tests): Itinerary metrics, day metrics, suggested request serialization.
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
   **Verified Behaviors**:
   * Health ping to `GET /api/v1/health` $\to$ `200 OK`
   * Municipalities query $\to$ 32 LGUs returned
   * Places query with category filter $\to$ items returned
   * Clustered suggested itinerary generation $\to$ 3-day itinerary created
   * Multi-format export generation (`.ics`, `.txt`, `.json`).

### 3.3 Running Web Client Regression Suite
```powershell
npm --prefix Project run test:unit
```
**Result**: 32 test files passed, 348 tests passed, 0 failures.
