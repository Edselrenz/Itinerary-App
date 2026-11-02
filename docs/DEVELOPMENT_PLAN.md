# Development Plan: Nueva Ecija Travel Itinerary

This plan tracks the 11 sequential milestones defined in the **End-to-End Engineering Implementation Manual**.

---

## Milestone Status Overview

| Step | Milestone Name | Primary Focus | Verification Gate | Status |
| :---: | :--- | :--- | :--- | :---: |
| **0** | **Monorepo & Scope Freeze** | Monorepo layout, `.gitignore`, `.env.example`, dependency locking. | Clean tree, zero hardcoded secrets. | **COMPLETED** |
| **1** | **PostgreSQL & FastAPI Core** | 7 SQLAlchemy 2.0 ORM models, Alembic migration, health check. | `GET /api/v1/health` returns 200 OK. | **COMPLETED** |
| **2** | **OSM POI Pipeline & Seeding** | Overpass importer, bounding box check, 17 curated featured places. | Idempotent seed produces 0 duplicate rows. | **COMPLETED** |
| **3** | **Auth & Ionic App Shell** | Argon2id auth, JWT, Google OAuth verify, Guest storage, 4-tab shell. | Pytest 100% pass; Angular build succeeds. | **COMPLETED** |
| **4** | **Home Tab & Debounced Search** | 300ms RxJS search, popular destinations carousel, saved cards. | Local database search, 0 Nominatim calls. | **COMPLETED** |
| **5** | **Leaflet Map & 16 Filters** | Bounded Leaflet map, category filters, marker cluster, bottom sheet. | Responsive map, external directions handoff. | **COMPLETED** |
| **6** | **Custom Itinerary Builder** | Multi-day custom creator, stop reordering, honest budget math. | BOLA ownership checks, duplicate guards. | **COMPLETED** |
| **7** | **Suggested Itinerary Engine** | Deterministic Haversine clustering, preference scoring, diversity. | Transparent assumptions, no hallucinated venues. | **COMPLETED** |
| **8** | **Overview, Day View & Sync** | Timeline view, stop detail cards, reactive cross-tab persistence. | Home cards sync immediately after edit. | **COMPLETED** |
| **9** | **Pilot Security & Tunneling** | Rate limiting (SlowAPI), offline interceptor, backup/restore drills. | Cross-device LAN testing, isolated DB port. | **COMPLETED** |
| **10** | **QA & Pilot Acceptance** | Full automated verification matrix, 24-point acceptance checklist. | 100% pass across all 24 acceptance criteria. | **COMPLETED** |
| **11** | **Priority 1: Security & Data-Loss** | Fix BOLA/IDOR (CR-001, CR-002), edit-mode data loss (CR-003), JWT/OAuth hardening (CR-004, CR-005). | Negative BOLA tests pass; edit preserves days; strong secrets enforced. | **COMPLETED** |
| **12** | **Priority 2: Core Reliability** | Token refresh (CR-006), timezone calendar fixes (CR-007), generator radius/budget (CR-008, CR-009), PATCH stop (CR-010), map routing (CR-011), URL safety (CR-012). | Zero timezone shift; 25km radius bound; auth refresh works seamlessly. | **COMPLETED** |
| **13** | **Priority 3: Maintainability** | Clean dead starter files, remove destructive scripts, fix acceptance tautologies (CR-014), memory leaks & typos (CR-015), doc sync (CR-016). | Clean codebase; 0 memory leaks; exact test assertions. | **COMPLETED** |
| **14** | **Priority 4: Performance & E2E** | Cloudflare Tunnel IP rate limiting, SQL generator pre-filtering, OSM batching (CR-013), rewrite modern E2E test suite (CR-014). | Independent remote rate limiting; sub-100ms generation; passing E2E spec. | **PENDING** |

---

## Detailed Task Breakdown

### Milestone 0: Monorepo & Scope Freeze
- [x] Configure repository root `.gitignore` protecting secrets, virtual environments, node artifacts, and dumps.
- [x] Create `.env.example` with documented environment variable template.
- [x] Establish backend dependency pins in `backend/requirements.txt`.
- [x] Align directory layout containing `Project/`, `backend/`, and `scripts/`.

### Milestone 1: PostgreSQL, SQLAlchemy Models & FastAPI Foundation
- [x] Implement database session manager in `backend/app/core/database.py`.
- [x] Implement settings loader in `backend/app/core/config.py`.
- [x] Implement 7 core SQLAlchemy 2.0 entities in `backend/app/models/entities.py`:
  - `User`, `AuthIdentity`, `Municipality`, `Place`, `Itinerary`, `ItineraryDay`, `ItineraryItem`.
- [x] Generate initial Alembic migration (`0001_initial_nueva_ecija_schema.py`).
- [x] Implement FastAPI main entrypoint with CORS and `GET /api/v1/health` in `backend/app/main.py`.

### Milestone 2: POI Ingestion & Curated Seeding Pipeline
- [x] Implement canonical 16-category mapping in `scripts/import_osm.py`.
- [x] Enforce Nueva Ecija bounding box filter (`15.15 <= lat <= 16.15`, `120.70 <= lng <= 121.40`).
- [x] Implement fuzzy municipality resolver for "Muñoz" / "Science City of Muñoz".
- [x] Implement `scripts/seed_featured_places.py` with 12 municipalities and 17 curated destinations (including Bongabon Day 1 stops and Pantabangan resorts).
- [x] Implement `GET /api/v1/municipalities` and `GET /api/v1/places` endpoints with comma-separated category support in `backend/app/api/v1/places.py`.
- [x] Verify with automated test suite `backend/tests/test_foundation.py`.

### Milestone 3: Authentication & Ionic Angular Shell
- [x] Implement Argon2id password hashing and short-lived JWT token service in `backend/app/services/auth_service.py`.
- [x] Implement REST endpoints in `backend/app/api/v1/auth.py` (`/register`, `/login`, `/refresh`, `/me`, `/oauth/google`, `/oauth/apple`).
- [x] Verify with automated test suite `backend/tests/test_auth.py` (case-insensitive uniqueness, 401 generic error, 501 Apple gate).
- [x] Install `@ionic/storage-angular`, `leaflet`, `leaflet.markercluster` in `Project/`.
- [x] Configure `environment.ts` and `environment.prod.ts`.
- [x] Implement `GuestStorageService` with `ne_guest_itineraries_v1`.
- [x] Implement `AuthService` with reactive `currentUser$` and token management.
- [x] Implement `authInterceptor` with graceful offline interceptor for laptop-sleep resilience.
- [x] Build Welcome Page (`welcome.page`) matching Figma hero and buttons.
- [x] Build Login Page (`login.page`) with validation, password toggle, and disabled Apple button.
- [x] Build Signup Page (`signup.page`) with cross-field password matching validator.
- [x] Build 4-Tab Shell (`tabs.routes.ts`) for Home, Map, History (placeholder), and Profile (account status / guest notice).
- [x] Fix Angular Ionic 9 import resolution (`@ionic/angular`) and verify clean `npm run build`.

### Milestone 4: Home Tab & Local Place Search
- [x] Implement Place service (`place.service.ts`) and models (`place.models.ts`) in Angular client with 11 passing unit tests.
- [x] Connect Home tab search bar to `GET /api/v1/places` using 300ms RxJS debounce and `switchMap` cancellation.
- [x] Connect Popular Destinations horizontal carousel to live `PlaceService.getFeaturedPlaces()`.
- [x] Build Saved Itineraries card list fetching from `GuestStorageService` with empty-state planner prompt.
- [x] Enrich Destination Detail Modal with operating hours and honest cost formatting.
- [x] Implement Home tab unit tests (`home.page.spec.ts`) with 6 passing tests.

### Milestone 5: Leaflet Map & 16 Category Filters
- [x] Implement Leaflet map bounded to Nueva Ecija `[15.58, 121.00]` with max bounds constraint.
- [x] Configure OpenStreetMap raster tile layer with mandatory attribution.
- [x] Integrate 16 canonical category filter pills carousel with reactive filtering.
- [x] Integrate Leaflet MarkerCluster with custom CSS vector pins (`.custom-map-pin`).
- [x] Build interactive POI Bottom Sheet with operating hours, honest pricing, and Google Maps directions link.
- [x] Handle Ionic tab switching lifecycle with `map.invalidateSize()` on `ionViewDidEnter()`.
- [x] Implement 9 Vitest unit tests in `map.page.spec.ts` (100% passing).
- [x] Eliminate CommonJS optimization warnings via `allowedCommonJsDependencies` in `angular.json`.

### Milestone 6: Custom Itinerary Builder
- [x] Backend CRUD endpoints in `backend/app/api/v1/itineraries.py` with strict BOLA checks.
- [x] Multi-day custom creator with day tabs and stop reordering (`POST /api/v1/itineraries/{id}/reorder`).
- [x] Place picker modal with live database search and manual off-grid venue entry.
- [x] Same-day duplicate stop guard dialog.
- [x] Honest budget calculation helper (`ItineraryService.calculateBudgetSummary`).
- [x] Dual-mode client persistence with `GuestStorageService` fallback.
- [x] Unsaved changes route/exit guard.
- [x] 19 automated tests (3 backend pytest, 13 itinerary service vitest, 6 custom builder vitest).

### Milestone 7: Suggested Itinerary Engine (Completed)
- [x] Backend generation endpoint `POST /api/v1/itineraries/suggest` with deterministic Haversine geographic clustering.
- [x] User preference questionnaire and scoring matrix (nature, heritage, food, leisure).
- [x] Same-day municipality proximity clustering to prevent cross-province backtracking.
- [x] 2-3 stops per day pacing with lunch/dining window slotting.
- [x] Transparent assumptions list (admission costs, travel window, fuel/transit exclusions).
- [x] Automated pytest suite verifying clustering radius, category diversity, and zero hallucinated venues.
- [x] Suggested Itinerary wizard frontend and preview sheet with "Accept & Save" persistence.
- [x] Offline fallback suggested itinerary generator for offline/guest mode.
- [x] 10 unit tests in `suggested-wizard.page.spec.ts` (100% passing).

### Milestone 8: Itinerary Management & Day Timeline View (Completed)
- [x] Itinerary Detail / Day Timeline view (`/itinerary/:id`) showing chronological stop cards.
- [x] Stop details modal with opening hours, directions link, notes, and pricing tag.
- [x] History / Saved Itineraries tab (`/tabs/history`) showing active, upcoming, and past trips reactively synced.
- [x] Edit action opening saved custom itineraries in `/custom-builder/:id`.
- [x] Delete itinerary action with confirmation modal and optimistic local/server removal.
- [x] Cross-tab reactive synchronization (`ItineraryService.itineraries$`).
- [x] Comprehensive unit tests for timeline and itinerary management (`itinerary-detail.page.spec.ts`).

### Milestone 9: Pilot Security & Tunneling (Completed)
- [x] Rate limiting on auth endpoints with SlowAPI (5/min per IP on login, register, refresh, and OAuth).
- [x] Offline host laptop warning banner in client (`ConnectivityService` + `app.component` floating status banner with live health probe).
- [x] PostgreSQL backup and restore drill (`scripts/db_backup_restore.py` + `backend/tests/test_backup_restore.py`).
- [x] Cloudflare Tunnel automated start/stop scripts (`start_server.bat` / `stop_server.bat` and PowerShell helpers).

### Milestone 10: QA & Pilot Acceptance Gate (Completed)
- [x] Walk through full 24-point MVP acceptance checklist (`scripts/verify_acceptance_gate.py` passing 24/24 checks, 100%).
- [x] End-to-end automated verification run (Backend pytest 6/6, Frontend Vitest 98/98, ESLint & Prettier 0 warnings).

---

## Post-Acceptance Hardening & Optimization Roadmap

### Milestone 11: Priority 1 — Critical Security & Data-Loss Fixes (Completed)
- [x] **CR-001**: Fix cross-itinerary BOLA in `POST /api/v1/itineraries/{id}/reorder` (`backend/app/api/v1/itineraries.py`). Scope item lookup to `itinerary.days`.
- [x] **CR-002**: Fix cross-itinerary BOLA in `DELETE /api/v1/itineraries/{id}/days/{day_id}/items/{item_id}`. Verify `day.itinerary_id == itinerary.id` and `item.day_id == day.id`.
- [x] **CR-003**: Fix edit-mode itinerary saving dropping all days and stops (`CustomBuilderPage.saveItinerary()`, `ItineraryService.updateItinerary()`, `PATCH /api/v1/itineraries/{id}`). Extend `ItineraryUpdate` to accept `days`.
- [x] **CR-004**: Reject default JWT secret outside development/test mode; enforce `google_oauth_client_id` in token verification; restrict CORS regex to `https://edselrenz.github.io`.
- [x] **CR-005**: Require `email_verified is True` in Google OAuth account linking; enforce `user.is_active` check in `authenticate_google_user()`.

### Milestone 12: Priority 2 — Core Reliability & Functional Accuracy (Completed)
- [x] **CR-006**: Implement refresh token rotation in `authInterceptor` and `AuthService.refreshSession()`; prevent silent guest storage fallback on 401.
- [x] **CR-007**: Fix timezone off-by-one shifting by creating local calendar date helpers (`toLocalIsoDate`, `parseLocalIsoDate`, `addDaysLocal`).
- [x] **CR-008**: Enforce `settings.default_dest_radius_km` (25km) and cumulative daily budget in `backend/app/algorithms/itinerary_generator.py`; escape `%`/`_` in SQL queries.
- [x] **CR-009**: Connect online guests to `/api/v1/itineraries/suggest`; filter curated pool by destination/preferences in offline generator; bind wizard chips dynamically.
- [x] **CR-010**: Implement `PATCH /api/v1/itineraries/{id}/days/{day_id}/items/{item_id}`; fix `sort_order` default=1 bug; validate `place_id` foreign key.
- [x] **CR-011**: Support route queryParams in `MapPage` from Home tab; add `tileerror` listener; render honest pricing & provenance badges in bottom sheet.
- [x] **CR-012**: Validate custom API URL; scope Bearer token injection strictly to `environment.apiBaseUrl`.
- [x] **CR-013 (F.4)**: Add `--clean --if-exists` to PostgreSQL backup/restore script.

### Milestone 13: Priority 3 — Maintainability & Code Quality Cleanup (Completed)
- [x] **CR-014**: Delete 16 dead starter files and remove destructive `setup_steps_0_to_2.py`; replace 7 tautological checks in `verify_acceptance_gate.py`.
- [x] **CR-015**: Fix memory leak in `ProfilePage`; wire non-functional buttons; dynamically query nearby places; fix UI copy typos; prune 44 unused image files.
- [x] **CR-016**: Synchronize all documentation files (`docs/KNOWN_ISSUES.md`, `docs/DEVELOPMENT_PLAN.md`, `docs/TESTING_DOCUMENTATION.md`).

### Milestone 14: Priority 4 — Long-Term Performance & Comprehensive E2E Testing (Active)
- [ ] **CR-013**: Key SlowAPI rate limits by `CF-Connecting-IP` for Cloudflare Tunnel traffic; pre-filter places in SQL; batch OSM imports.
- [ ] **CR-014**: Rewrite `Project/e2e/app.spec.ts` to test actual user journeys.


