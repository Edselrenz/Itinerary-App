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
| **7** | **Suggested Itinerary Engine** | Deterministic Haversine clustering, preference scoring, diversity. | Transparent assumptions, no hallucinated venues. | **NEXT** |
| **8** | **Overview, Day View & Sync** | Timeline view, stop detail cards, reactive cross-tab persistence. | Home cards sync immediately after edit. | **PENDING** |
| **9** | **Pilot Security & Tunneling** | Rate limiting (SlowAPI), offline interceptor, backup/restore drills. | Cross-device LAN testing, isolated DB port. | **PENDING** |
| **10** | **QA & Pilot Acceptance** | Full automated verification matrix, 24-point acceptance checklist. | 100% pass across all 24 acceptance criteria. | **PENDING** |

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

### Milestone 8: Itinerary Management & Day Timeline View (Next)
- [ ] Itinerary Detail / Day Timeline view (`/itinerary/:id`) showing chronological stop cards.
- [ ] Stop details modal with opening hours, directions link, notes, and pricing tag.
- [ ] History / Saved Itineraries tab (`/tabs/history` or Tab 3) showing active, upcoming, and past trips.
- [ ] Edit action opening saved custom itineraries in `/custom-builder/:id`.
- [ ] Delete itinerary action with confirmation modal and optimistic local/server removal.
- [ ] Cross-tab reactive synchronization (`ItineraryService.itineraries$`).
- [ ] Comprehensive unit tests for timeline and itinerary management.

