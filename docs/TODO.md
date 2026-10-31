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

## Phase 10: QA & Pilot Acceptance Gate (COMPLETED)
- [x] Walk through full 24-point MVP acceptance checklist (`scripts/verify_acceptance_gate.py` passing 24/24 checks, 100%).
- [x] End-to-end automated verification run (Backend pytest 6/6, Frontend Vitest 98/98, ESLint & Prettier 0 warnings).

---

## Phase 11: Priority 1 — Critical Security & Data-Loss Fixes (PENDING)
> Ref: [CODE_REVIEW_AUDIT.md](file:///c:/Users/Edward/Desktop/CaseStudy/docs/CODE_REVIEW_AUDIT.md) — Critical & High Severity Findings

- [ ] **CR-001**: Fix cross-itinerary BOLA in `POST /api/v1/itineraries/{id}/reorder` (`backend/app/api/v1/itineraries.py`):
  - [ ] Enforce `item.day_id in {d.id for d in itinerary.days}` before updating `sort_order`.
  - [ ] Reject foreign items with HTTP 400 Bad Request.
  - [ ] Add negative test in `backend/tests/test_itineraries.py` asserting cross-user reorder attempt fails.
- [ ] **CR-002**: Fix cross-itinerary BOLA / IDOR in `DELETE /api/v1/itineraries/{id}/days/{day_id}/items/{item_id}` (`backend/app/api/v1/itineraries.py`):
  - [ ] Verify `day.itinerary_id == itinerary.id` and `item.day_id == day.id` before executing delete.
  - [ ] Reject mismatched day/item with HTTP 404 Not Found.
  - [ ] Add negative test in `backend/tests/test_itineraries.py` asserting cross-user item deletion attempt fails.
- [ ] **CR-003**: Fix edit-mode itinerary saving dropping all days and stops (Silent Data Loss):
  - [ ] Extend `ItineraryUpdate` schema (`backend/app/schemas/itinerary.py`) to accept optional `days: Optional[List[ItineraryDayCreate]]`, `preferences`, and `assumptions`.
  - [ ] Update `PATCH /api/v1/itineraries/{id}` in `backend/app/api/v1/itineraries.py` to synchronize days and items transactionally when provided.
  - [ ] Update `ItineraryService.updateItinerary()` and `updateGuestItinerary()` in `Project/src/app/core/services/itinerary.service.ts` to pass full itinerary payload including `days`.
  - [ ] Update `CustomBuilderPage.saveItinerary()` in `Project/src/app/features/itinerary/custom-builder/custom-builder.page.ts` to include `days` in edit mode.
  - [ ] Add automated tests in `test_itineraries.py` and `itinerary.service.spec.ts` verifying edit mode preserves all days and stops.
- [ ] **CR-004**: Harden JWT secrets, OAuth audience validation, and CORS scope:
  - [ ] Add startup validation in `backend/app/core/config.py` rejecting the default JWT secret key if `environment != "development"`.
  - [ ] Enforce non-empty `google_oauth_client_id` in `backend/app/services/auth_service.py` (`verify_google_id_token`); reject verification if audience is unconfigured instead of passing `audience=None`.
  - [ ] Tighten CORS origin regex in `backend/app/core/config.py` from `r"^https://.*\.github\.io$"` to explicit `https://edselrenz.github.io`.
- [ ] **CR-005**: Fix Google OAuth account takeover & deactivated user bypass:
  - [ ] Assert `payload.get("email_verified") is True` in `backend/app/services/auth_service.py` before linking existing accounts by email.
  - [ ] Enforce `user.is_active` check in `authenticate_google_user()`; return HTTP 403 Forbidden if user is inactive/banned.
  - [ ] Add unit tests in `backend/tests/test_auth.py` verifying unverified emails and deactivated accounts are rejected.

---

## Phase 12: Priority 2 — Core Reliability & Functional Accuracy (PENDING)
> Ref: [CODE_REVIEW_AUDIT.md](file:///c:/Users/Edward/Desktop/CaseStudy/docs/CODE_REVIEW_AUDIT.md) — High & Medium Severity Functional Deficiencies

- [ ] **CR-006**: Implement refresh token rotation & resilient interceptor:
  - [ ] Implement `refreshSession()` in `Project/src/app/core/services/auth.service.ts` calling `POST /api/v1/auth/refresh`.
  - [ ] Update `Project/src/app/core/interceptors/auth.interceptor.ts` to trap 401 Unauthorized, queue pending requests, and invoke token refresh.
  - [ ] Check JWT expiration (`exp` claim) in `AuthService.isAuthenticated()`.
  - [ ] Restrict `ItineraryService` guest storage fallback strictly to network outages (`status === 0 || status === 502 || status === 504`), not 401 authentication errors.
- [ ] **CR-007**: Fix timezone off-by-one shifting in date parsing & generation:
  - [ ] Create centralized date utility (`Project/src/app/core/utils/date.utils.ts`) with `toLocalIsoDate()`, `parseLocalIsoDate()`, and `addDaysLocal()`.
  - [ ] Replace `new Date().toISOString().split('T')[0]` with local calendar date helper in `suggested-wizard.page.ts`.
  - [ ] Replace `new Date("YYYY-MM-DD")` parsing and UTC arithmetic in `custom-builder.page.ts`, `itinerary-detail.page.ts`, and `itinerary.service.ts`.
  - [ ] Add unit test suite in `Project/src/app/core/utils/date.utils.spec.ts` testing across timezones (UTC+8, UTC, UTC-8).
- [ ] **CR-008**: Fix itinerary generator algorithm & SQL wildcard injection:
  - [ ] Enforce `settings.default_dest_radius_km` (25.0 km) in `backend/app/algorithms/itinerary_generator.py` to prevent cross-province backtracking.
  - [ ] Maintain cumulative daily budget tracking instead of independent per-stop budget check.
  - [ ] Escape `%` and `_` SQL wildcards in `backend/app/api/v1/places.py` query parameters.
  - [ ] Add test cases in `backend/tests/test_itineraries.py` verifying clustering radius enforcement.
- [ ] **CR-009**: Fix offline suggested itinerary generator & dynamic form bindings:
  - [ ] Call `POST /api/v1/itineraries/suggest` for guests when online; fall back to offline generator only on network failure.
  - [ ] Filter POI pool in `generateOfflineSuggestedItinerary()` (`itinerary.service.ts`) by destination municipality and category preferences.
  - [ ] Dynamically bind budget and preference chips in `suggested-wizard.page.html` to configured options.
- [ ] **CR-010**: Implement single-stop PATCH endpoint & fix edge cases:
  - [ ] Implement `PATCH /api/v1/itineraries/{id}/days/{day_id}/items/{item_id}` endpoint in `backend/app/api/v1/itineraries.py` using `ItineraryItemUpdate`.
  - [ ] Fix `sort_order` default=1 bug in `add_itinerary_item()` (`default=0 + 1`).
  - [ ] Validate `place_id` foreign key existence in `create_itinerary()` to prevent unhandled 500 `IntegrityError`.
- [ ] **CR-011**: Fix Map page route parameters, tile error handling & honest pricing:
  - [ ] Inject `ActivatedRoute` in `MapPage` (`Project/src/app/features/map/map.page.ts`) to read `queryParams` from Home page "Plan Route Here" and center/fly to coordinates.
  - [ ] Add `tileerror` listener on Leaflet tile layer with user feedback indicator.
  - [ ] Render explicit "Not verified / Not provided" labels and provenance badges in POI bottom sheet.
- [ ] **CR-012**: Validate custom API URL & scope Bearer token injection:
  - [ ] Validate URL protocol (`https://` or `http://localhost`) in `ConnectivityService.setCustomApiUrl()`.
  - [ ] Scope `authInterceptor` Bearer token attachment strictly to `req.url.startsWith(environment.apiBaseUrl)`.
- [ ] **CR-013 (F.4)**: Fix PostgreSQL restore script in `scripts/db_backup_restore.py`:
  - [ ] Add `--clean --if-exists` flags to `pg_dump` invocation to ensure clean restore over existing tables.

---

## Phase 13: Priority 3 — Maintainability & Code Quality Cleanup (PENDING)
> Ref: [CODE_REVIEW_AUDIT.md](file:///c:/Users/Edward/Desktop/CaseStudy/docs/CODE_REVIEW_AUDIT.md) — Starter Files, Quality & Documentation

- [ ] **CR-014**: Clean up dead starter code & strengthen test suite:
  - [ ] Delete 16 unused starter files from initial Ionic template (`tab1/`, `tab2/`, `tab3/`, `explore-container/`).
  - [ ] Remove destructive script `scripts/setup_steps_0_to_2.py`.
  - [ ] Replace 7 tautological checks (`True` or `or True`) in `scripts/verify_acceptance_gate.py` with real assertions.
- [ ] **CR-015**: Fix UI bugs, memory leaks, typos & unused assets:
  - [ ] Fix unsubscribed observable memory leak in `ProfilePage` (`Project/src/app/features/profile/profile.page.ts`) by unsubscribing in `ngOnDestroy`.
  - [ ] Add click handlers or disabled indicators to "Continue with Google" and "Forgot password?" in `login.page.html`.
  - [ ] Dynamically query nearby places based on destination coordinates in `PlaceService.getNearbyPlaces()`.
  - [ ] Correct typos: "iternaries" in `welcome.page.html:15`, "won't be save" in `guest.page.html:16`, "Remeber me" in `login.page.html:36`.
  - [ ] Prune 44 unused SHA-1 hash image files in `Project/src/assets/images/`.
- [ ] **CR-016**: Synchronize documentation suite:
  - [ ] Update `docs/KNOWN_ISSUES.md` to reflect completed milestones and track audit findings.
  - [ ] Update `docs/DEVELOPMENT_PLAN.md` to mark Milestones 7-10 completed and append Phases 11-14.
  - [ ] Update `docs/PROJECT_STATE.md` with audit status and active roadmap.

---

## Phase 14: Priority 4 — Long-Term Performance & Comprehensive E2E Testing (PENDING)
> Ref: [CODE_REVIEW_AUDIT.md](file:///c:/Users/Edward/Desktop/CaseStudy/docs/CODE_REVIEW_AUDIT.md) — Scalability & End-to-End Test Suite

- [ ] **CR-013**: Cloudflare Tunnel rate limiting & query optimizations:
  - [ ] Configure SlowAPI key function in `backend/app/api/v1/auth.py` to inspect `CF-Connecting-IP` when `request.client.host == "127.0.0.1"`.
  - [ ] Pre-filter candidate places by bounding box or municipality in `itinerary_generator.py` instead of loading entire 4,400+ table into Python memory.
  - [ ] Batch place lookups in `scripts/import_osm.py` and `scripts/seed_featured_places.py`.
- [ ] **CR-014**: Rewrite modern Playwright/Cypress E2E test suite:
  - [ ] Replace outdated `Project/e2e/app.spec.ts` with end-to-end journey tests covering `/welcome` -> `/guest` -> `/tabs/home` -> `/tabs/map` -> `/custom-builder`.


