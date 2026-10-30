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

### 2.3 Mobile Client Compilation Suite
- `npm run build` in `Project/`: Production Angular AOT compiler and bundler.
- `npm run typecheck:e2e`: TypeScript strict compilation.

---

## 3. Actual Verified Test Results

### 3.1 Backend Pytest Run
```text
============================= test session starts =============================
platform win32 -- Python 3.14.3, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\Edward\Desktop\CaseStudy
plugins: anyio-4.13.0
collected 2 items

backend/tests/test_auth.py::test_auth_lifecycle PASSED                   [ 50%]
backend/tests/test_foundation.py::test_health_and_featured_places_pipeline PASSED [100%]

======================== 2 passed, 1 warning in 5.48s =========================
```

### 3.2 Mobile Production Build Run
```text
> Project@0.0.1 build
> ng build

√ Building...
Initial total  | 827.04 kB | 186.78 kB transfer
Lazy chunk files:
  chunk-BrlJGmfL.js (login-page)
  chunk-BUF0x-PC.js (signup-page)
  chunk-BDDiel8w.js (welcome-page)
  chunk-OxupxWYB.js (tabs-routes)
  chunk-GIN5YfVD.js (home-page)
  chunk-DgGNJ41a.js (map-page)
  chunk-BQGgx5QT.js (history-page)
  chunk-F6MWumre.js (profile-page)
Application bundle generation complete. [16.968 seconds]
Output location: C:\Users\Edward\Desktop\CaseStudy\Project\www
Exit Code: 0
```

---

## 4. Pending Tests for Upcoming Milestones

- [ ] Milestone 4: RxJS debounce and query cancellation tests for Home search bar.
- [ ] Milestone 5: Leaflet bounds and marker clustering integration tests.
- [ ] Milestone 6: BOLA authorization tests (attempting cross-user itinerary PATCH/DELETE to assert `404 Not Found`).
- [ ] Milestone 7: Haversine recommendation scoring unit tests (preference weighting, category diversity penalty, sparse-data fallback).

