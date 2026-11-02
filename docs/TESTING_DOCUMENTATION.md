# Testing Documentation: Nueva Ecija Travel Itinerary

## 1. Testing Strategy

The project employs a multi-tiered verification strategy designed to prevent regressions and verify compliance with open-data and security guardrails:

1. **In-Memory SQLite Database Test Harness**:
   - Backend tests run with zero dependence on a running PostgreSQL server by utilizing `sqlite:///:memory:` and `StaticPool`.
   - Dependency override `app.dependency_overrides[get_db]` injects an ephemeral session per test suite.
2. **FastAPI `TestClient` API Integration Tests**:
   - Full-lifecycle HTTP testing of endpoints, status codes, payload serialization, and headers.
3. **Frontend Static Typing & Production Compilation Checks**:
   - Angular TypeScript compilation (`tsc`) and production bundle generation (`ng build`).

---

## 2. Test Suites & Test Cases

### 2.1 Backend Foundation Suite (`backend/tests/test_foundation.py`)
- **`test_health_and_featured_places_pipeline`**:
  1. Verifies `GET /api/v1/health` returns status `200` with `status: ok` and `province_scope: Nueva Ecija`.
  2. Verifies `seed_municipalities_and_featured()` seeds 12 municipalities and 17 curated places.
  3. Verifies idempotency: running `seed_municipalities_and_featured()` a second time creates 0 new rows and updates existing records.
  4. Verifies `GET /api/v1/municipalities?q=Cabanatuan` filters accurately.
  5. Verifies `GET /api/v1/places?featured=true` returns 17 places, enforces honest null costs for unverified venues (e.g. Pantabangan Dam), and verifies key-free Google Maps URLs in `directions_url`.
  6. Verifies Figma-featured Bongabon stops exist (*Rohi Paperflower Cafe*, *La Casa Prime Cabins*, *Museo de Bongabon*, *Thornes Samgyupsal House*).
  7. Verifies comma-separated category query parameters (`?categories=cafe,restaurant`).
  8. Verifies OSM import idempotency and out-of-province rejection: 1 Nueva Ecija POI accepted, 1 Manila coordinate rejected.

### 2.2 Backend Authentication Suite (`backend/tests/test_auth.py`)
- **`test_auth_lifecycle`**:
  1. Valid registration creates a user, hashes password with Argon2id, and issues access + refresh tokens (status `201`).
  2. Case-insensitive duplicate username rejection (status `409 Conflict`).
  3. Case-insensitive duplicate email rejection (status `409 Conflict`).
  4. Wrong password login fails with generic message (status `401 Unauthorized`).
  5. Correct password login succeeds and issues tokens (status `200 OK`).
  6. Protected route `/api/v1/auth/me` with Bearer token succeeds (status `200 OK`).
  7. Unauthenticated request to `/api/v1/auth/me` is rejected (status `401 Unauthorized`).
  8. Refresh token exchange at `/api/v1/auth/refresh` succeeds and issues new access token.
  9. Apple Sign-In returns `501 Not Implemented` with truthful explanation when `enableAppleAuth = false`.

### 2.3 Backend Itineraries Suite (`backend/tests/test_itineraries.py`)
- **`test_itinerary_lifecycle_and_bola_protection`**:
  1. Multi-day custom itinerary creation with nested day and stop structures (status `201 Created`).
  2. Owner listing and single retrieval (status `200 OK`).
  3. **BOLA Enforcement**: Second authenticated user cannot view, modify (`PATCH`), or delete (`DELETE`) User A's itinerary (returns status `404 Not Found`).
  4. Same-day duplicate stop guard: Attempting to add the same POI to the same day returns status `400 Bad Request`.
  5. Cross-day and within-day stop reordering with sort order re-indexing (status `200 OK`).
  6. Stop deletion (status `200 OK`) and cascade itinerary deletion (status `204 No Content`).

### 2.4 Mobile Client Unit Test Suite
- **`PlaceService` Suite (`Project/src/app/core/services/place.service.spec.ts`)**: 11 passing tests.
- **`ItineraryService` Suite (`Project/src/app/core/services/itinerary.service.spec.ts`)**: 13 passing tests.
  1. Initial constructor fetch and state emission via `itineraries$`.
  2. Honest budget calculations (verified cost range calculation and unpriced stop counting).
  3. Authenticated API operations (single fetch, creation, update, deletion, stop addition, stop deletion, stop reordering).
  4. Guest/offline fallback operations (local storage persistence, same-day duplicate stop guard).
- **`CustomBuilderPage` Suite (`Project/src/app/features/itinerary/custom-builder/custom-builder.page.spec.ts`)**: 6 passing tests.
  1. Component creation and initial multi-day date calculation.
  2. Day addition and selection.
  3. Stop addition and reordering (move up/down).
  4. Stop deletion.
  5. Save flow execution and redirection to `/tabs/home`.
  6. Cancel exit without unsaved changes.
- **`MapPage` Suite (`Project/src/app/tabs/map/map.page.spec.ts`)**: 9 passing tests.
- **`HomePage` Suite (`Project/src/app/tabs/home/home.page.spec.ts`)**: 6 passing tests.
- **Other Tab Suites (`tab1`, `tab2`, `tab3`, `tabs`, `app`)**: 6 passing tests.

### 2.5 Mobile Client Compilation Suite
- `npm run build` in `Project/`: Production Angular AOT compiler and bundler.
- `npm run typecheck:e2e`: TypeScript strict compilation.
- `npm run test:unit`: Vitest Angular unit test runner.

---

## 3. Actual Verified Test Results

### 3.1 Mobile Client Unit Tests (`npm run test:unit`)
```text
 RUN  v5.0.5 C:/Users/Edward/Desktop/CaseStudy/Project

 ✓  app  src/app/core/utils/date.utils.spec.ts (5 tests) 140ms
 ✓  app  src/app/core/services/connectivity.service.spec.ts (5 tests) 125ms
 ✓  app  src/app/core/services/place.service.spec.ts (13 tests) 215ms
 ✓  app  src/app/core/services/itinerary.service.spec.ts (16 tests) 261ms
 ✓  app  src/app/core/services/guest-migration.service.spec.ts (5 tests) 49ms
 ✓  app  src/app/tabs/tabs.page.spec.ts (1 test) 442ms
 ✓  app  src/app/tabs/profile/profile.page.spec.ts (3 tests) 747ms
 ✓  app  src/app/app.component.spec.ts (5 tests) 746ms
 ✓  app  src/app/tabs/history/history.page.spec.ts (4 tests) 904ms
 ✓  app  src/app/tabs/home/home.page.spec.ts (9 tests) 1322ms
 ✓  app  src/app/features/itinerary/itinerary-detail/itinerary-detail.page.spec.ts (9 tests) 1425ms
 ✓  app  src/app/features/itinerary/suggested-wizard/suggested-wizard.page.spec.ts (12 tests) 1493ms
 ✓  app  src/app/features/itinerary/custom-builder/custom-builder.page.spec.ts (10 tests) 1582ms
 ✓  app  src/app/tabs/map/map.page.spec.ts (10 tests) 1635ms

 Test Files  14 passed (14)
      Tests  107 passed (107)
   Duration  23.39s
```

### 3.2 Backend Pytest Run (`python -m pytest backend/tests/ -v`)
```text
backend/tests/test_auth.py::test_auth_lifecycle PASSED                   [  7%]
backend/tests/test_auth.py::test_auth_rate_limiting PASSED              [ 15%]
backend/tests/test_cloudflare_tunnel_ip_resolution PASSED               [ 23%]
backend/tests/test_auth_rate_limiting_isolated_by_cloudflare_ip PASSED   [ 30%]
backend/tests/test_settings_secret_validation_in_production PASSED       [ 38%]
backend/tests/test_google_oauth_security_gates PASSED                   [ 46%]
backend/tests/test_backup_restore.py::test_backup_restore_drill PASSED   [ 53%]
backend/tests/test_foundation.py::test_health_and_featured_places_pipeline PASSED [ 61%]
backend/tests/test_itineraries.py::test_itinerary_lifecycle_and_bola_protection PASSED [ 69%]
backend/tests/test_itineraries.py::test_suggested_itinerary_engine PASSED [ 76%]
backend/tests/test_itineraries.py::test_single_stop_patch_and_place_validation PASSED [ 84%]
backend/tests/test_itineraries.py::test_suggested_generator_radius_and_budget_clustering PASSED [ 92%]
backend/tests/test_itineraries.py::test_generator_sql_bounding_box_pre_filtering PASSED [100%]

======================= 13 passed, 5 warnings in 3.42s ========================
```

### 3.3 Mobile Production Build Run (`npm run build`)
```text
> Project@0.0.1 build
> ng build

√ Building...
Initial chunk files | Names   | Raw size  | Transfer size
main-LOAM4BHC.js    | main    | 642.11 kB |     149.00 kB
styles-54SWNLJA.css | styles  |  65.58 kB |       8.01 kB
Initial total       |         | 769.49 kB |     179.79 kB

Lazy chunk files:
  custom-builder-page (38.00 kB)
  map-page            (203.80 kB)
  home-page           (34.17 kB)
  signup-page         (13.43 kB)
  login-page          (12.18 kB)
  profile-page        (6.36 kB)
  welcome-page        (5.10 kB)
  guest-page          (4.38 kB)
Application bundle generation complete. [7.063 seconds]
Output location: C:\Users\Edward\Desktop\CaseStudy\Project\www
Budget Warnings: 0
Exit Code: 0
```

---

## 4. Completed Milestone Verification Gates (Phases 7–10)

- [x] **Milestone 7 (Suggested Itinerary Engine)**:
  - Haversine clustering algorithm, preference weight matrix, 2–3 stops/day pacing, and diversity penalty tests (`backend/tests/test_itineraries.py::test_suggested_itinerary_engine`).
  - Wizard UI lifecycle and scoring tests (`Project/src/app/features/itinerary/suggested-wizard/suggested-wizard.page.spec.ts`).
- [x] **Milestone 8 (Itinerary Management & Day Timeline View)**:
  - Day timeline view, stop details, and reactive cross-tab persistence (`Project/src/app/features/itinerary/itinerary-detail/itinerary-detail.page.spec.ts`).
  - Guest-to-account migration helper (`backend/tests/test_phase8.py`).
- [x] **Milestone 9 (Pilot Security & Tunneling)**:
  - SlowAPI rate limiting (5 req/min) verification (`backend/tests/test_phase9.py`).
  - PostgreSQL backup and restore drill (`scripts/db_backup_restore.py` + `backend/tests/test_backup_restore.py`).
  - Connectivity service and offline warning banner unit tests (`connectivity.service.spec.ts`).
- [x] **Milestone 10 (QA & Pilot Acceptance Gate)**:
  - 24-point acceptance checklist fully verified via `scripts/verify_acceptance_gate.py` (24/24 passing, 100.0%).
  - Full suite verification: 6/6 backend test suites passing, 16 frontend test files passing (98/98 unit tests).

---

## 5. Verified Security & Hardening Tests (Phases 11–14)
> Ref: [CODE_REVIEW_AUDIT.md](file:///c:/Users/Edward/Desktop/CaseStudy/docs/CODE_REVIEW_AUDIT.md) & [TODO.md](file:///c:/Users/Edward/Desktop/CaseStudy/docs/TODO.md)

- [x] **BOLA Negative Security Tests (`CR-001`, `CR-002`)**:
  - Test cross-itinerary reorder rejection (`POST /api/v1/itineraries/{id}/reorder` with foreign item ID returns 400).
  - Test cross-itinerary item deletion rejection (`DELETE /api/v1/itineraries/{id}/days/{day_id}/items/{item_id}` returns 404).
- [x] **Itinerary Edit Mode Data Retention Test (`CR-003`)**:
  - Test that updating an itinerary via `PATCH` with new days and modified stops preserves all days and stops in both PostgreSQL and guest IndexedDB.
- [x] **Auth Hardening Tests (`CR-004`, `CR-005`)**:
  - Startup validation rejects default JWT secret outside development mode (`test_jwt_secret_startup_validation`).
  - Google OAuth login rejects unverified emails (`email_verified is not True`) and deactivated accounts (`is_active = False`).
- [x] **Token Refresh & Interceptor Queue Tests (`CR-006`)**:
  - 401 response queues requests, refreshes token via `/auth/refresh`, and resumes requests without guest downgrade.
- [x] **Timezone-Agnostic Date Utility Tests (`CR-007`)**:
  - Unit test suite (`date.utils.spec.ts`) verifying calendar arithmetic behaves identically across UTC+8, UTC, and UTC-8 without off-by-one shifts.
- [x] **Clustering Radius & Budget Bounds Tests (`CR-008`)**:
  - Unit tests (`test_suggested_generator_radius_and_budget_clustering`) verifying no POI farther than `default_dest_radius_km` (25km) is recommended and cumulative daily budget is tracked.
- [x] **Single-Stop Update & Place Validation Tests (`CR-010`)**:
  - Unit tests (`test_single_stop_patch_and_place_validation`) verifying `PATCH /api/v1/itineraries/{id}/days/{day_id}/items/{item_id}` and 404 rejection on nonexistent `place_id`.
- [x] **End-to-End User Journey Tests (`CR-014`)**:
  - Modern Playwright E2E spec verifying `/welcome` -> `/guest` -> `/tabs/home` -> `/tabs/map` -> `/custom-builder` flows in `Project/e2e/app.spec.ts` (100% verified with `npm run typecheck:e2e`).


