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

## Phase 5: Leaflet Map & Category Filters (COMPLETED)
- [x] Implement Leaflet map bounded to Nueva Ecija `[15.58, 121.00]`.
- [x] Integrate 16 canonical category filter pills carousel.
- [x] Implement Leaflet MarkerCluster integration with custom CSS pins.
- [x] Build interactive POI Bottom Sheet with operating hours, cost bounds, and "Get Directions" button.
- [x] Handle Ionic tab lifecycle resizing (`map.invalidateSize()` on `ionViewDidEnter`).
- [x] Implement comprehensive Vitest unit tests in `map.page.spec.ts` (9 tests passing).
- [x] Eliminate CommonJS optimization warnings in `angular.json`.

---

## Phase 6: Custom Itinerary Builder (COMPLETED)
- [x] Backend CRUD endpoints in `backend/app/api/v1/itineraries.py` with strict BOLA ownership checks.
- [x] Sub-resource endpoints for adding days, adding stops, removing stops, and reordering (`POST /api/v1/itineraries/{id}/reorder`).
- [x] Automated test suite in `backend/tests/test_itineraries.py` (BOLA isolation, duplicate checks, reordering).
- [x] Frontend `ItineraryService` and models in `itinerary.models.ts` and `itinerary.service.ts` with dual-mode API + Guest fallback.
- [x] Comprehensive unit tests in `itinerary.service.spec.ts` (13 tests passing).
- [x] Multi-day Custom Itinerary creator UI (`Project/src/app/features/itinerary/custom-builder/`):
  - [x] Day tabs and "+ Add Day" action.
  - [x] Stop cards with sort badges, reorder buttons (move up/down), and delete stop.
  - [x] Place picker modal with live database search (`PlaceService.searchPlaces`).
  - [x] Off-grid custom venue support (title, municipality/address, cost range, notes).
  - [x] Same-day duplicate stop guard dialog.
  - [x] Honest budget calculation helper (`calculateBudgetSummary`).
  - [x] Unsaved changes route/exit guard.
  - [x] Unit test suite in `custom-builder.page.spec.ts` (6 tests passing).
- [x] Home tab integration:
  - [x] Connected Custom Itinerary action card and empty-state card to `/custom-builder`.
  - [x] Wired `savedItineraries` to `ItineraryService.itineraries$` for instant reactivity.
- [x] Angular build budgets passing with 0 warnings (<10kB per component style).

---

## Phase 7: Deterministic Suggested Itinerary Engine (COMPLETED)
- [x] Implement `backend/app/algorithms/itinerary_generator.py`:
  - [x] Haversine distance clustering anchor.
  - [x] Configurable weights (preference, proximity, featured status, diversity penalty).
  - [x] Transparent assumptions banner generator.
  - [x] Sparse-data fallback handling.
- [x] Backend endpoint `POST /api/v1/itineraries/suggest` (guest drafts + optional saving).
- [x] Automated pytest suite in `backend/tests/test_itineraries.py` (`test_suggested_itinerary_engine`).
- [x] Frontend Suggested Itinerary form ("Tell us your travel details") with destination picker, date range, daily budget presets, and preference chips.
- [x] Frontend "Your Itinerary" preview sheet with day timeline, honest pricing, assumptions box, and "Accept & Save" CTA.
- [x] Offline fallback generator in `ItineraryService` (`generateOfflineSuggestedItinerary`).
- [x] Unit tests for recommendation scoring and wizard lifecycle (`suggested-wizard.page.spec.ts`, 10/10 passing).

---

## Phase 8: Overview, Day View & Reactive Home Persistence (COMPLETED)
- [x] Unified Itinerary Overview screen with day selector chips (`ItineraryDetailPage` matching Figma Screen 2).
- [x] Day timeline view with scheduled stop cards, category badges, and Nearby Places modal / sub-view (Figma Screens 3-5).
- [x] Reactive synchronization: Home tab & History tab update immediately when an itinerary is created, modified, or deleted.
- [x] Guest-to-account migration helper (`GuestMigrationService` wired to login, signup, and profile tab).

---

## Phase 9: Pilot Security & Deployment Readiness (COMPLETED)
- [x] Rate limiting on auth endpoints with SlowAPI (5/min per IP on login, register, refresh, and OAuth).
- [x] Offline host laptop warning banner in client (`ConnectivityService` + `app.component` floating status banner with live health probe).
- [x] PostgreSQL backup and restore drill (`scripts/db_backup_restore.py` + `backend/tests/test_backup_restore.py`).

---

## Phase 10: QA & Pilot Acceptance Gate (NEXT FOCUS)
- [ ] Walk through full 24-point MVP acceptance checklist.
- [ ] End-to-end automated verification run.

