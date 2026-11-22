# 13 — Testing and Quality Assurance

This document catalogs the **actual automated test suites** present in the repository (verified at **488 total automated unit/integration tests passing** plus Playwright E2E and the 24-point acceptance gate in Phase 62 `v1.0.0`) and provides a **recommended expansion test plan** for future cloud scaling.

---

## 1. Existing Testing Infrastructure (Verified — 488 Automated Tests Passing)

The repository has comprehensive automated test coverage across **five distinct test layers**:
- **Backend Pytest Suite**: **21 / 21** tests passing (`backend/tests/`)
- **Web / Mobile Vitest Unit Suite**: **348 / 348** tests passing across **32 spec files** (`Project/src/**/*.spec.ts`)
- **Desktop Client Pytest Suite**: **119 / 119** tests passing across **10 test modules** (`desktop_client/tests/`)
- **Playwright Mobile E2E Suite**: End-to-end user journey specs (`Project/e2e/app.spec.ts`)
- **24-Point MVP Acceptance Gate**: Full-stack automated acceptance script (`scripts/verify_acceptance_gate.py`)

### 1.1 Backend Pytest Suite (`backend/tests/` — 21 test functions)
- **Framework**: `pytest>=8.3.0` with FastAPI `TestClient` and in-memory SQLite (`StaticPool`).
- **Execution Command**:
  ```bash
  python -m pytest backend/tests/ -v
  ```
- **CI Integration**: Executed automatically on every push to `main` in `.github/workflows/deploy.yml`.
- **Verified Modules**:
  - `test_auth.py` (6 tests): Full auth lifecycle, rate limiting, Cloudflare Tunnel IP resolution, IP-isolated rate limits, production JWT secret validation, Google OAuth security hardening.
  - `test_itineraries.py` (6 tests): Itinerary CRUD + BOLA protection, suggested itinerary engine, single-stop PATCH & place validation, radius/budget clustering, SQL bounding-box pre-filtering, chronological ordering & overnight lodging logic.
  - `test_google_maps_service.py` (7 tests): Polyline encode/decode, Haversine & duration helpers, Google type-to-category mapping, place normalization, DB cache integration, discover & route endpoints, Bayesian quality score & opening-hours gate.
  - `test_foundation.py` (1 test): Health endpoint & featured places pipeline.
  - `test_backup_restore.py` (1 test): End-to-end backup & restore drill using `tmp_path`.

### 1.2 Frontend Unit Tests (`Project/src/**/*.spec.ts` — 32 Vitest spec files, 348 tests)
- **Framework**: **Vitest `~5.0.5`** with `jsdom` (`Project/vitest.config.mts`, `fsModuleCache: false` to avoid stale Angular bundle caching).
- **Execution Commands** (from `Project/`):
  ```bash
  npm run test:unit        # ng test --no-watch (348 tests, runs in CI)
  npm run test:unit:watch  # interactive watch mode
  npm run lint             # ESLint (0 warnings) + E2E tsc + Prettier check
  ```
- **Coverage**: Covers `AppComponent`, `pendingChangesGuard`, `authInterceptor`, 9 of 10 core services, 3 utilities (`date.utils`, `itinerary-export.util`, `polyline.util`), `commute-guide.data`, 3 auth pages, 3 itinerary pages, 3 shared components, and all 6 tab pages + `tabs.routes`. *(Missing spec: `guest.page.ts`, `guest-storage.service.ts`.)*

### 1.3 Frontend E2E Tests (`Project/e2e/app.spec.ts`)
- **Framework**: **Playwright `^1.64.1`** (`Project/playwright.config.ts`), configured for **Mobile Chrome (Pixel 7)** against `http://localhost:4200` (`webServer` auto-starts `npm start -- --port 4200`).
- **Execution Command** (from `Project/`):
  ```bash
  npm run test:e2e
  ```
- **Verified Scenarios**: Root redirect to `/#/welcome`, guest onboarding journey (`/#/welcome` → `/#/guest` → `/#/tabs/home`), Home ↔ Map tab navigation, Custom Itinerary Builder questionnaire verification.

### 1.4 Desktop Client Pytest Suite (`desktop_client/tests/` — 10 modules, 119 test functions)
- **Framework**: `pytest>=8.0.0` + `pytest-asyncio>=0.24.0`.
- **Execution Command**:
  ```bash
  python -m pytest desktop_client/tests/ -v
  ```
- **Verified Modules**:
  - `test_api_client.py` (4 tests)
  - `test_auth_service.py` (6 tests)
  - `test_cycle2_regressions.py` (**37 tests**, `TC-01` through `TC-40`, including Phase 61.1 & Session 58 regressions:
    - `TC-35`: Frozen PyInstaller `_ASSETS_DIR` resolution & writable `%LOCALAPPDATA%` tile cache fallback
    - `TC-36`: In-app navigation deep link contract (`_launch_in_app_nav`)
    - `TC-37`: `ProfileView` `Edit Profile` form full-width centering (`width=card_w`, `horizontal_alignment=CENTER`)
    - `TC-38`: `Off-Grid Custom Venue` & `Edit Stop` modal horizontal overflow elimination (`expand=True` paired row controls)
    - `TC-39`: `SplashOverlay` full-screen `Positioned.fill` (`left/top/right/bottom=0`, `BoxFit.COVER`) & Web branding parity
    - `TC-40`: Boxless `WelcomeView` / `GuestView` / `LoginView` / `SignupView` layout parity & seamless 3-tile mirrored cityscape `welcome_hero_buildings_wide.png` `1848 × 336`)
  - `test_itinerary_service.py` (3 tests)
  - `test_live_integration.py` (1 test)
  - `test_parity_services_and_components.py` (42 tests)
  - `test_place_service.py` (4 tests)
  - `test_qa_remediation.py` (9 tests)
  - `test_storage_export.py` (4 tests)
  - `test_ui_consistency.py` (9 tests)

### 1.5 Automated 24-Point MVP Acceptance Gate (`scripts/verify_acceptance_gate.py`)
- **Execution Command**: `python scripts/verify_acceptance_gate.py`
- **Scope**: Runs 24 assertions across Auth & Guest Mode (7), Home & Places (3), Map Tab (7), and Itineraries & Operations (7) using in-memory SQLite + seeded curated places.

---

## 2. Recommended Test Plan (Gaps to Close)

Distinguished clearly from existing tests above, the following areas should be added before wide public release:

| Category | Recommended Test Cases | Target Layer |
|---|---|---|
| **1. Authentication & Security** | Expired refresh token rejection; password change invalidation check; `photo_name` path traversal rejection on `/places/photos/`; `avatar_url` oversized/malicious URI rejection; Cloudflare Worker `/__sync_tunnel` invalid key `401` test. | Backend Pytest + Worker Miniflare |
| **2. PostgreSQL Parity** | Run `backend/tests/` against a live PostgreSQL 16 service container in GitHub Actions (currently runs on SQLite in-memory) to catch PostgreSQL-specific `JSONB`, `UUID`, and `alembic upgrade head` regressions. | GitHub Actions CI |
| **3. Playwright Full-Stack E2E** | Add CI job running Playwright against live Uvicorn + Angular covering: Register → Create Custom Itinerary → Reorder Stops → Export `.ics` → Logout → Guest Create → Login & Verify Guest Migration. | `Project/e2e/` |
| **4. Desktop CI Gate** | Add `python -m pytest desktop_client/tests/ -v` (119 tests) step to `.github/workflows/release-builds.yml` before PyInstaller packaging. | `.github/workflows/release-builds.yml` |
| **5. Responsive & Accessibility QA** | Automated Lighthouse / axe-core checks on Web/PWA viewports (`375px`, `768px`, `1280px`) in light and dark modes. | Playwright + axe |
| **6. External Outage & Performance** | Load test `/api/v1/places?limit=5000` and `/api/v1/itineraries/suggest` (14-day trip) under simulated OSRM/Google timeouts; verify fallback latency stays `< 3s`. | Backend Pytest / Locust |

---

## 3. Technical Terms & Concepts Explained (How It Works & What It Is Used For in This System)

| Technical Term | How It Works (Technical & Layman Explanation) | What It Is Used For in This System |
|---|---|---|
| **Unit Testing vs. Integration Testing vs. End-to-End (E2E) Testing** | **Layman**: **Unit testing** checks one small part in isolation (like testing a spark plug on a workbench). **Integration testing** checks how several parts work together (like testing the engine connected to the fuel pump). **E2E testing** puts a robot driver in the seat to press the pedals and steer the whole car down a real road.<br>**Technical**: Unit tests (`Vitest`, `desktop_client/tests/`) mock external dependencies to verify pure component/service logic; integration tests (`backend/tests/` via FastAPI `TestClient`) exercise HTTP routers, Pydantic validation, and SQLAlchemy queries together; E2E tests (`Playwright`) drive a headless Chromium browser against the running application. | Forms our 488-test quality pyramid ensuring math helpers, UI views, REST API endpoints, and mobile user journeys all work without regressions. |
| **In-Memory SQLite & `StaticPool` (`backend/tests/`)** | **Layman**: Instead of touching the real database on disk during automated tests, the test runner creates a temporary, ultra-fast database completely inside computer RAM (`sqlite:///:memory:`) and wipes it clean after the test finishes.<br>**Technical**: SQLAlchemy's `StaticPool` forces all connections in a test session to share the same single in-memory SQLite connection handle, paired with `app.dependency_overrides[get_db]` so `TestClient` requests operate on an isolated schema created via `Base.metadata.create_all()`. | Allows all 21 backend integration tests (`test_auth.py`, `test_itineraries.py`, `test_google_maps_service.py`) to run in a few seconds with zero external database dependencies. |
| **Vitest & `jsdom` (`Project/vitest.config.mts`)** | **Layman**: A super-fast JavaScript test runner (**Vitest**) paired with a simulated browser window in Node.js (**jsdom**) so all 348 web tests can click buttons and inspect HTML without waiting for a real Chrome window to open.<br>**Technical**: Executes `*.spec.ts` files compiled by Angular's `@analogjs/vitest-angular` / `@angular/build:unit-test` builder inside a virtual DOM environment (`jsdom`), with `fsModuleCache: false` configured to prevent stale transform caches. | Runs all 348 unit tests across 32 Angular spec files in ~20 seconds locally and inside GitHub Actions CI. |
| **Playwright Device Emulation (`Pixel 7`)** | **Layman**: A browser automation tool that opens a real Chromium browser engine sized and configured to act like a Google Pixel 7 Android smartphone (touch screen, mobile viewport size, mobile user-agent) and walks through the app like a real traveler.<br>**Technical**: Configured in `Project/playwright.config.ts` using `devices['Pixel 7']` against `http://localhost:4200`, asserting DOM visibility, hash URL transitions (`/#/welcome` → `/#/guest` → `/#/tabs/home`), and form interactions. | Verifies mobile-first responsive layouts and multi-page user journeys in `Project/e2e/app.spec.ts`. |
| **AST / Source Contract Regression Tests (`test_cycle2_regressions.py`)** | **Layman**: Automated tests that inspect both the live Python UI objects and the source code rules (like verifying that the Splash Screen background image is pinned to all 4 edges of the screen, or that the Welcome Screen uses the mirrored widescreen skyline image) so fixed UI bugs can never accidentally creep back in.<br>**Technical**: Combines live Flet control-tree inspection (`SplashOverlay`, `WelcomeView`, `ProfileView`, `SlippyMapCanvas`) with structural source assertions across `TC-01` through `TC-40`. | Enforces all 40 desktop-web parity and packaging invariants across the 119-test desktop Pytest suite. |
