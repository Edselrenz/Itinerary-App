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

 ✓  app  src/app/explore-container/explore-container.component.spec.ts (1 test) 155ms
 ✓  app  src/app/core/services/place.service.spec.ts (11 tests) 117ms
 ✓  app  src/app/core/services/itinerary.service.spec.ts (13 tests) 191ms
 ✓  app  src/app/tab2/tab2.page.spec.ts (1 test) 287ms
 ✓  app  src/app/tab3/tab3.page.spec.ts (1 test) 287ms
 ✓  app  src/app/tab1/tab1.page.spec.ts (1 test) 306ms
 ✓  app  src/app/app.component.spec.ts (1 test) 349ms
 ✓  app  src/app/tabs/tabs.page.spec.ts (1 test) 367ms
 ✓  app  src/app/tabs/home/home.page.spec.ts (6 tests) 928ms
 ✓  app  src/app/features/itinerary/custom-builder/custom-builder.page.spec.ts (6 tests) 1167ms
 ✓  app  src/app/tabs/map/map.page.spec.ts (9 tests) 1248ms

 Test Files  11 passed (11)
      Tests  51 passed (51)
   Duration  19.82s
```

### 3.2 Backend Pytest Run (`python -m pytest backend/tests/ -v`)
```text
backend/tests/test_auth.py::test_auth_lifecycle PASSED                   [ 33%]
backend/tests/test_foundation.py::test_health_and_featured_places_pipeline PASSED [ 66%]
backend/tests/test_itineraries.py::test_itinerary_lifecycle_and_bola_protection PASSED [100%]

======================== 3 passed, 1 warning in 3.77s =========================
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

## 4. Pending Tests for Upcoming Milestones

- [ ] Milestone 7: Deterministic Haversine clustering algorithms, preference weight scoring matrix, 2-3 stops/day pacing, and category diversity penalty tests.
- [ ] Milestone 8: Cross-tab reactive persistence and guest-to-account itinerary migration synchronization.
- [ ] Milestone 9: SlowAPI rate limiting under concurrent load and laptop-sleep offline interceptor recovery.
- [ ] Milestone 10: 24-point pilot acceptance verification matrix.

