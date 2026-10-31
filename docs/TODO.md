# Project TODO: Nueva Ecija Travel Itinerary

This checklist tracks completed, active, and pending tasks across all development phases.

---

## Phase 0: Monorepo Foundation & Setup
- [x] Configure `.gitignore` for secrets, Python virtual environments, and node artifacts.
- [x] Create `.env.example` template with documented parameters.
- [x] Lock backend dependencies in `backend/requirements.txt`.
- [x] Initialize `/docs` documentation suite.

---

## Phase 1: Database Foundation & FastAPI Core
- [x] Configure SQLAlchemy 2.0 engine and session factory (`backend/app/core/database.py`).
- [x] Implement Pydantic Settings loader (`backend/app/core/config.py`).
- [x] Define 7 core SQLAlchemy 2.0 ORM models (`backend/app/models/entities.py`):
  - [x] `User`
  - [x] `AuthIdentity`
  - [x] `Municipality`
  - [x] `Place`
  - [x] `Itinerary`
  - [x] `ItineraryDay`
  - [x] `ItineraryItem`
- [x] Implement Alembic initial schema migration (`0001_initial_nueva_ecija_schema.py`).
- [x] Create FastAPI application with CORS middleware and `GET /api/v1/health`.

---

## Phase 2: POI Pipeline & Data Seeding
- [x] Implement OSM Overpass ingestion script (`scripts/import_osm.py`):
  - [x] Bounding box geographic filter (`15.15 <= lat <= 16.15`, `120.70 <= lng <= 121.40`).
  - [x] 16 canonical category tag mapping.
  - [x] Municipality resolver with fuzzy matching for Muñoz.
  - [x] Idempotent upsert logic.
- [x] Implement curated destination seeding script (`scripts/seed_featured_places.py`):
  - [x] 12 Nueva Ecija municipalities.
  - [x] 17 curated destinations (including Bongabon Day 1 stops and Pantabangan resorts).
- [x] Implement endpoints in `backend/app/api/v1/places.py`:
  - [x] `GET /api/v1/municipalities`
  - [x] `GET /api/v1/places` (with comma-separated category support)
  - [x] `GET /api/v1/places/{id}`
- [x] Write and verify automated test suite `backend/tests/test_foundation.py`.

---

## Phase 3: Authentication & Ionic App Shell
- [x] Backend Authentication:
  - [x] Argon2id password hashing via `pwdlib`.
  - [x] JWT access tokens (30m) and refresh tokens (7d) via `pyjwt`.
  - [x] Server-side Google OAuth ID token verification via `google-auth`.
  - [x] Endpoints in `backend/app/api/v1/auth.py` (`/register`, `/login`, `/refresh`, `/me`, `/oauth/google`, `/oauth/apple`).
  - [x] Write and verify automated test suite `backend/tests/test_auth.py`.
- [x] Mobile Client Architecture:
  - [x] Install `@ionic/storage-angular`, `leaflet`, `leaflet.markercluster`.
  - [x] Configure `environment.ts` and `environment.prod.ts`.
  - [x] Implement `GuestStorageService` with `@ionic/storage-angular` (`ne_guest_itineraries_v1`).
  - [x] Implement `AuthService` with reactive `currentUser$` and token management.
  - [x] Implement `authInterceptor` with token attachment and offline error handling.
- [x] UI Screens & Navigation:
  - [x] Welcome Page (`/welcome`) with hero buildings illustration (`welcome_hero_buildings.png`) and "Explore as a guest" modal sheet (`guest_illustration.png`).
  - [x] Login Page (`/login`) with authentic Google logo (`google_logo.png`), form validation, password toggle, and disabled Apple button.
  - [x] Signup Page (`/signup`) with matching-passwords confirmation validator.
  - [x] 4-Tab Navigation Shell (`/tabs`):
    - [x] Home tab (`/tabs/home`):
      - [x] Header: *"Where are you going next?"* with profile avatar.
      - [x] Destination search pill bar matching Figma with instant reactive search filtering and empty state.
      - [x] Adventure hero card (*"Your next adventure is waiting"*).
      - [x] Suggested & Custom Itinerary entry cards matching Figma Flow 2.
      - [x] Popular Destinations horizontal carousel with extracted venue imagery and municipality pills.
      - [x] Destination Detail Modal sheet with Google Maps external navigation.
    - [x] Map tab shell (`/tabs/map`).
    - [x] History tab placeholder (`/tabs/history` - *"Planned for a later release"*).
    - [x] Profile tab (`/tabs/profile`) with verified account status and guest migration triggers.
  - [x] Configure design tokens in `variables.scss` and `global.scss`.
  - [x] Verify production build (`npm run build`) with zero errors and zero budget warnings.

---

## Phase 4: Home Tab & Local Place Search
- [x] Implement `PlaceService` in `Project/src/app/core/services/place.service.ts`:
  - [x] `searchPlaces(params)` (query, categories, bounding box, municipality, limit, offset)
  - [x] `getFeaturedPlaces(limit)`
  - [x] `getPlaceById(id)`
  - [x] `getMunicipalities(query)`
  - [x] `getPlaceImage(name, remoteUrl)` local photography fallback resolver
  - [x] `formatCategoryName(categoryKey)`
  - [x] Unit test suite (`place.service.spec.ts`) with 11 passing tests
- [x] Connect Home tab search bar with RxJS 300ms debounce to live `PlaceService` backend (`switchMap` stale query cancellation).
- [x] Render Popular Destinations carousel with verified imagery, descriptions, and category tags.
- [x] Connect Popular Destinations carousel to live `PlaceService.getFeaturedPlaces()`.
- [x] Render Saved Itineraries card list (`GuestStorageService` for guests, with empty-state planner prompt).
- [x] Enrich Destination Detail Modal with hours and honest pricing (`₱min - ₱max` or "Cost not provided").
- [x] Home tab unit test suite (`home.page.spec.ts`) with 6 passing tests.
- [x] Verify search response times and zero-Nominatim network calls.

---

## Phase 5: Leaflet Map & Category Filters (CURRENT FOCUS)
- [ ] Implement Leaflet map bounded to Nueva Ecija `[15.58, 121.00]`.
- [ ] Integrate 16 category filter modal / pills.
- [ ] Implement Leaflet MarkerCluster integration for POI markers.
- [ ] Build POI Bottom Sheet with opening hours, cost range, verified facts, and "Get Directions" button.
- [ ] Handle Ionic tab resize (`map.invalidateSize()`).

---

## Phase 6: Custom Itinerary Builder
- [ ] Backend CRUD endpoints in `backend/app/api/v1/itineraries.py` with strict BOLA ownership checks.
- [ ] Reorder endpoint `POST /api/v1/itineraries/{id}/reorder`.
- [ ] Frontend Custom Itinerary creator with day tabs.
- [ ] Place picker modal and manual custom off-grid stop modal.
- [ ] Same-day duplicate stop guard dialog.
- [ ] Honest budget calculation helper (never treating null cost as zero).
- [ ] Unsaved changes route guard (`CanDeactivateFn`).

---

## Phase 7: Deterministic Suggested Itinerary Engine
- [ ] Implement `backend/app/algorithms/itinerary_generator.py`:
  - [ ] Haversine distance clustering anchor.
  - [ ] Configurable weights (preference, proximity, featured status, diversity penalty).
  - [ ] Transparent assumptions banner generator.
  - [ ] Sparse-data fallback handling.
- [ ] Backend endpoint `POST /api/v1/itineraries/suggest`.
- [ ] Frontend Suggested Itinerary form ("Tell us your travel details") with destination picker, date range, daily budget, and preference chips.
- [ ] Unit tests for recommendation scoring and diversity rules.

---

## Phase 8: Overview, Day View & Reactive Home Persistence
- [ ] Unified Itinerary Overview screen with day selector chips.
- [ ] Day timeline view with scheduled stop cards and category badges.
- [ ] Reactive synchronization: Home tab updates immediately when an itinerary is modified or deleted.
- [ ] Guest-to-account migration helper.

---

## Phase 9: Pilot Security & Deployment Readiness
- [ ] Rate limiting on auth endpoints with SlowAPI (e.g. 5/min per IP).
- [ ] Offline host laptop warning banner in client.
- [ ] PostgreSQL backup and restore drill (`pg_dump` / `pg_restore`).

---

## Phase 10: QA & Pilot Acceptance Gate
- [ ] Walk through full 24-point MVP acceptance checklist.
- [ ] End-to-end automated verification run.

