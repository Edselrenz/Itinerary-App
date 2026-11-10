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
- **Core Utilities & Data**:
  - `date.utils.spec.ts`: 5 passing tests (calendar formatting, parsing, cross-timezone stability).
  - `polyline.util.spec.ts`: 5 passing tests (polyline encoding/decoding, haversine distance, segment projection).
  - `itinerary-export.util.spec.ts`: 9 passing tests (RFC 5545 .ics calendar export, print summary, clipboard copy).
  - `commute-guide.data.spec.ts`: 9 passing tests (walking hops, tricycle routes, arterial highway corridor hops).
- **Core Services & Interceptors**:
  - `connectivity.service.spec.ts`: 6 passing tests (health checks, 2-strike offline gate, custom tunnel URL).
  - `auth.interceptor.spec.ts`: 5 passing tests (Bearer token injection, gateway error reporting, async health probes).
  - `auth.service.spec.ts`: 4 passing tests (reactive currentUser$, JWT storage, login, logout).
  - `place.service.spec.ts`: 15 passing tests (search, category filtering, caching, nearby lookups, cache merging).
  - `itinerary.service.spec.ts`: 25 passing tests (CRUD, suggested wizard engine, sequential rolling windows, pacing, budget math).
  - `guest-migration.service.spec.ts`: 5 passing tests (guest trip detection, account migration).
  - `route-tracking.service.spec.ts`: 6 passing tests (Capacitor Geolocation watch, 10m throttle, off-route dispatch, arrival detection).
  - `secure-token-storage.service.spec.ts`: 5 passing tests (Capacitor secure storage vs web storage).
  - `osm-overpass.service.spec.ts`: 3 passing tests (bounding box filter, query construction).
- **Guards & Routing**:
  - `pending-changes.guard.spec.ts`: 3 passing tests (dirty form guard, confirmation dialog).
  - `tabs.routes.spec.ts`: 3 passing tests (/tabs/saved -> history redirect, root /saved redirect, primary tab paths).
- **Components & Modals**:
  - `place-detail-sheet.component.spec.ts`: 8 passing tests (photo gallery, schedule, reviews, commute guide, action button emissions).
  - `destination-autocomplete.component.spec.ts`: 11 passing tests (32 LGU indexing, diacritic normalization, fuzzy filtering).
  - `itinerary-route-map.component.spec.ts`: 8 passing tests (Leaflet route map, numbered stop pins, polyline rendering, full map handoff).
  - `app.component.spec.ts`: 8 passing tests (splash screen lifecycle, dark mode boot hydration, connectivity retry).
- **Tabs & Pages**:
  - `welcome.page.spec.ts`: Visual and navigation tests.
  - `login.page.spec.ts`: 7 passing tests (form validation, password recovery modal, login flow).
  - `signup.page.spec.ts`: 5 passing tests (form validation, matching passwords, username generation).
  - `home.page.spec.ts`: 14 passing tests (debounced search, popular carousel, category pills, shared sheet adoption).
  - `map.page.spec.ts`: 32 passing tests (Leaflet clustering, route focus mode, numbered pins, category filters, tile error resilience).
  - `history.page.spec.ts`: 7 passing tests (saved cards, search, segment filtering, trip deletion).
  - `profile.page.spec.ts`: 18 passing tests (authenticated state, guest status, favorites navigation, edit profile form with avatar preview & extra details, settings preferences, dark theme toggle, language selection, notifications, default budget, clear cache, Help & Support FAQs, About modal, Settings shortcuts, and Figma-styled logout dialog with unsynced trip guards).
  - `welcome.page.spec.ts`: 5 passing tests (default onboarding view, login/signup/guest button navigation, and After Log Out screen with skyscraper blob and stacked action buttons).
  - `tabs.page.spec.ts`: 2 passing tests (bottom tab navigation, map query param reset).
  - `custom-builder.page.spec.ts`: 24 passing tests (multi-day timeline, stop addition/reordering/edit, catalog browse, duplicate guards).
  - `suggested-wizard.page.spec.ts`: 21 passing tests (destination chips, budget selection, preference mapping, route connectors, sheet consolidation).
  - `itinerary-detail.page.spec.ts`: 32 passing tests (day selection, interactive route map preview, navigate CTA, leg travel badges, dynamic subtitles).
- **Total Unit Test Coverage**: 30 test files, 310 unit tests passing (100%).

### 2.5 End-to-End Browser Journey Suite (Playwright)
- **`Project/e2e/app.spec.ts`**: 5 comprehensive browser journeys running across Chromium headless shell:
  1. `welcome screen renders with key branding and CTAs`: Validates branding, "Log in", "Sign up", and "Continue as Guest" buttons.
  2. `guest flow activates and enters home dashboard`: Validates transition from `/guest` to `/tabs/home` and displays guest banner.
  3. `navigation tab bar switches between views`: Validates tab bar navigation between Home, Map, Saved, and Profile.
  4. `map loads and displays search header`: Validates Leaflet map loading, `.map-top-bar` floating search input, and filter controls.
  5. `custom itinerary builder form opens and displays inputs`: Validates opening custom builder from Home and renders form inputs.

### 2.6 Mobile Client Compilation Suite
- `npm run build` in `Project/`: Production Angular AOT compiler and bundler. Output in `Project/www/`.
- `npm run typecheck:e2e`: TypeScript strict compilation.
- `npm run test:unit`: Vitest Angular unit test runner.
- `npm run test:e2e`: Playwright Chromium end-to-end browser test runner.

---

## 3. Actual Verified Test Results

### 3.1 Mobile Client Unit Tests (`npm run test:unit`)
```text
 RUN  v5.0.5 C:/Users/Edward/Desktop/CaseStudy/Project

 ✓  app  src/app/core/services/place.service.spec.ts (15 tests)
 ✓  app  src/app/core/services/route-tracking.service.spec.ts (6 tests)
 ✓  app  src/app/core/services/secure-token-storage.service.spec.ts (5 tests)
 ✓  app  src/app/core/services/osm-overpass.service.spec.ts (3 tests)
 ✓  app  src/app/core/services/itinerary.service.spec.ts (25 tests)
 ✓  app  src/app/core/utils/polyline.util.spec.ts (5 tests)
 ✓  app  src/app/core/utils/date.utils.spec.ts (5 tests)
 ✓  app  src/app/core/services/connectivity.service.spec.ts (6 tests)
 ✓  app  src/app/core/interceptors/auth.interceptor.spec.ts (5 tests)
 ✓  app  src/app/core/services/auth.service.spec.ts (4 tests)
 ✓  app  src/app/core/utils/itinerary-export.util.spec.ts (9 tests)
 ✓  app  src/app/core/data/commute-guide.data.spec.ts (9 tests)
 ✓  app  src/app/core/services/guest-migration.service.spec.ts (5 tests)
 ✓  app  src/app/tabs/tabs.routes.spec.ts (3 tests)
 ✓  app  src/app/core/guards/pending-changes.guard.spec.ts (3 tests)
 ✓  app  src/app/tabs/tabs.page.spec.ts (2 tests)
 ✓  app  src/app/shared/components/itinerary-route-map/itinerary-route-map.component.spec.ts (8 tests)
 ✓  app  src/app/app.component.spec.ts (8 tests)
 ✓  app  src/app/shared/components/destination-autocomplete/destination-autocomplete.component.spec.ts (11 tests)
 ✓  app  src/app/features/auth/signup/signup.page.spec.ts (5 tests)
 ✓  app  src/app/features/auth/login/login.page.spec.ts (7 tests)
 ✓  app  src/app/tabs/history/history.page.spec.ts (7 tests)
 ✓  app  src/app/shared/components/place-detail-sheet/place-detail-sheet.component.spec.ts (8 tests)
 ✓  app  src/app/tabs/profile/profile.page.spec.ts (9 tests)
 ✓  app  src/app/tabs/home/home.page.spec.ts (14 tests)
 ✓  app  src/app/features/itinerary/suggested-wizard/suggested-wizard.page.spec.ts (21 tests)
 ✓  app  src/app/features/itinerary/custom-builder/custom-builder.page.spec.ts (24 tests)
 ✓  app  src/app/features/itinerary/itinerary-detail/itinerary-detail.page.spec.ts (32 tests)
 ✓  app  src/app/tabs/map/map.page.spec.ts (32 tests)

 Test Files  29 passed (29)
      Tests  296 passed (296)
   Duration  33.28s
```

### 3.2 Backend Pytest Run (`python -m pytest backend/tests/ -v`)
```text
backend/tests/test_auth.py::test_auth_lifecycle PASSED                   [  4%]
backend/tests/test_auth.py::test_auth_rate_limiting PASSED              [  9%]
backend/tests/test_auth.py::test_cloudflare_tunnel_ip_resolution PASSED  [ 14%]
backend/tests/test_auth.py::test_auth_rate_limiting_isolated_by_cloudflare_ip PASSED [ 19%]
backend/tests/test_auth.py::test_settings_secret_validation_in_production PASSED [ 23%]
backend/tests/test_auth.py::test_google_oauth_security_gates PASSED     [ 28%]
backend/tests/test_backup_restore.py::test_backup_restore_drill PASSED   [ 33%]
backend/tests/test_foundation.py::test_health_and_featured_places_pipeline PASSED [ 38%]
backend/tests/test_google_maps_service.py::test_compute_route_fallback PASSED [ 42%]
backend/tests/test_google_maps_service.py::test_geospatial_cache_persistence PASSED [ 47%]
backend/tests/test_google_maps_service.py::test_places_discover_endpoint PASSED [ 52%]
backend/tests/test_google_maps_service.py::test_bayesian_quality_scoring PASSED [ 57%]
backend/tests/test_google_maps_service.py::test_opening_hours_gating PASSED [ 61%]
backend/tests/test_itineraries.py::test_itinerary_lifecycle_and_bola_protection PASSED [ 66%]
backend/tests/test_itineraries.py::test_suggested_itinerary_engine PASSED [ 71%]
backend/tests/test_itineraries.py::test_single_stop_patch_and_place_validation PASSED [ 76%]
backend/tests/test_itineraries.py::test_suggested_generator_radius_and_budget_clustering PASSED [ 80%]
backend/tests/test_itineraries.py::test_generator_sql_bounding_box_pre_filtering PASSED [ 85%]
backend/tests/test_itineraries.py::test_compute_day_route_endpoint PASSED [ 90%]
backend/tests/test_itineraries.py::test_upsert_on_save_foreign_key_safety PASSED [ 95%]
backend/tests/test_itineraries.py::test_multi_day_2opt_route_generation PASSED [100%]

======================= 21 passed, 5 warnings in 11.13s =======================
```

### 3.3 End-to-End Playwright Journey Run (`npm run test:e2e`)
```text
> Project@0.0.1 test:e2e
> playwright test

Running 5 tests using 5 workers

  ✓  1 [chromium] › e2e\app.spec.ts:10:7 › App Navigation & Guest Flows › welcome screen renders with key branding and CTAs (1.9s)
  ✓  2 [chromium] › e2e\app.spec.ts:18:7 › App Navigation & Guest Flows › guest flow activates and enters home dashboard (2.2s)
  ✓  3 [chromium] › e2e\app.spec.ts:31:7 › App Navigation & Guest Flows › navigation tab bar switches between views (2.8s)
  ✓  4 [chromium] › e2e\app.spec.ts:44:7 › App Navigation & Guest Flows › map loads and displays search header (3.1s)
  ✓  5 [chromium] › e2e\app.spec.ts:54:7 › App Navigation & Guest Flows › custom itinerary builder form opens and displays inputs (3.4s)

  5 passed (11.9s)
```

### 3.4 Mobile Production Build Run (`npm run build`)
```text
> Project@0.0.1 build
> ng build

√ Building...
Initial chunk files | Names   | Raw size  | Transfer size
main-PZ2MQ3KL.js    | main    | 654.12 kB |     151.24 kB
styles-44A5G6LM.css | styles  |  68.21 kB |       8.32 kB
Initial total       |         | 722.33 kB |     159.56 kB

Application bundle generation complete. [8.031 seconds]
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

---

## 6. Live Server Routing & Turn-by-Turn Verification (Session 72)

- [x] **Live Server Health & Endpoint Readiness**:
  - `GET /api/v1/health`: Confirmed 200 OK (`province_scope: Nueva Ecija`, `status: ok`).
  - `GET /api/v1/places?limit=3`: Confirmed 200 OK with serialization of names, categories, and municipalities.
- [x] **Live Route Computation Scenarios (`POST /api/v1/itineraries/compute-day-route`)**:
  - **Drive Point-to-Point Route (Cabanatuan -> Palayan City)**:
    - Distance: 15,588 meters (15.58 km).
    - Duration: 890 seconds (~14.8 minutes).
    - Polyline: 866-character encoded polyline generated and cached.
    - Maneuvers: 6 turn-by-turn steps along Maharlika Hwy and Nueva Ecija-Aurora Rd.
  - **Multi-Stop Intermediate Routing (Cabanatuan -> Bongabon -> Pantabangan)**:
    - Distance: 54,724 meters (54.7 km).
    - Duration: 3,446 seconds (~57.4 minutes).
    - Leg 1: 29,210 meters with 5 maneuver steps.
    - Leg 2: 25,514 meters with 9 maneuver steps.
  - **Walking Route Mode (Cabanatuan Stroll)**:
    - Distance: 1,645 meters, 134 seconds duration.
- [x] **Suggested Itinerary Engine Routing (`POST /api/v1/itineraries/suggest`)**:
  - Successfully generated 2-day itinerary with geographic clustering and 3 stops per day.
- [x] **Frontend Navigation & Map Deep-Linking (Playwright E2E Suite)**:
  - 8/8 end-to-end tests passing (`Mobile Chrome` Pixel 7 emulation):
    1. Welcome page redirect with brand copy.
    2. Guest authentication flow into Home tab.
    3. Seamless navigation between Home and Map tabs.
    4. Custom Itinerary Builder navigation and questionnaire form.
    5. Direct deep-linking to core application routes.
    6. Interactive Leaflet markers and canvas responsiveness.
    7. 2,673 OpenStreetMap POI display, clustering, drawer selection, and detail sheet opening.
    8. Deep-linking to map coordinates (`/tabs/map?lat=15.4859&lng=120.9669&zoom=15`) with verified floating navigation controls and valid Google Maps directions routing URLs (`https://www.google.com/maps/dir/?api=1&destination=...`).



## 7. QA Remediation & Release Gate Verification (Session 97)

- [x] **Acceptance Gate Verification (`scripts/verify_acceptance_gate.py`)**:
  - Executed full 24-point acceptance gate: **24/24 checks passed (100.0%)**.
  - Pass Breakdown:
    - Auth & Guest Mode Checks (7 criteria): 7/7 PASSED.
    - Home & Places Checks (3 criteria): 3/3 PASSED.
    - Map Tab Checks (7 criteria): 7/7 PASSED.
    - Itineraries & Operations Checks (7 criteria): 7/7 PASSED.
- [x] **Vitest Mobile Unit Test Suite (`npm --prefix Project run test:unit`)**:
  - **30/30 test files passed (100%)**.
  - **310/310 unit tests passed (100%)**.
  - All feature modules covered: Auth, Welcome, Home, Map, Custom Builder, Suggested Wizard, Itinerary Detail, History, Profile.
- [x] **Angular Production Build (`npm --prefix Project run build`)**:
  - Exit code 0, 0 compilation errors.
  - All component stylesheet bundles strictly under the 16 kB warning budget.
- [x] **Capacitor Android Native Sync (`npx cap sync android`)**:
  - Exit code 0, 6 plugins synchronized in 0.627s (`@capacitor/app`, `@capacitor/geolocation`, `@capacitor/haptics`, `@capacitor/keyboard`, `@capacitor/status-bar`, `capacitor-secure-storage-plugin`).
