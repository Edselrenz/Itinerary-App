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

## Phase 11: Priority 1 — Critical Security & Data-Loss Fixes (COMPLETED)
> Ref: [CODE_REVIEW_AUDIT.md](file:///c:/Users/Edward/Desktop/CaseStudy/docs/CODE_REVIEW_AUDIT.md) — Critical & High Severity Findings

- [x] **CR-001**: Fix cross-itinerary BOLA in `POST /api/v1/itineraries/{id}/reorder` (`backend/app/api/v1/itineraries.py`):
  - [x] Enforce `item.day_id in {d.id for d in itinerary.days}` before updating `sort_order`.
  - [x] Reject foreign items with HTTP 400 Bad Request.
  - [x] Add negative test in `backend/tests/test_itineraries.py` asserting cross-user reorder attempt fails.
- [x] **CR-002**: Fix cross-itinerary BOLA / IDOR in `DELETE /api/v1/itineraries/{id}/days/{day_id}/items/{item_id}` (`backend/app/api/v1/itineraries.py`):
  - [x] Verify `day.itinerary_id == itinerary.id` and `item.day_id == day.id` before executing delete.
  - [x] Reject mismatched day/item with HTTP 404 Not Found.
  - [x] Add negative test in `backend/tests/test_itineraries.py` asserting cross-user item deletion attempt fails.
- [x] **CR-003**: Fix edit-mode itinerary saving dropping all days and stops (Silent Data Loss):
  - [x] Extend `ItineraryUpdate` schema (`backend/app/schemas/itinerary.py`) to accept optional `days: Optional[List[ItineraryDayCreate]]`, `preferences`, and `assumptions`.
  - [x] Update `PATCH /api/v1/itineraries/{id}` in `backend/app/api/v1/itineraries.py` to synchronize days and items transactionally when provided.
  - [x] Update `ItineraryService.updateItinerary()` and `updateGuestItinerary()` in `Project/src/app/core/services/itinerary.service.ts` to pass full itinerary payload including `days`.
  - [x] Update `CustomBuilderPage.saveItinerary()` in `Project/src/app/features/itinerary/custom-builder/custom-builder.page.ts` to include `days` in edit mode.
  - [x] Add automated tests in `test_itineraries.py` and `itinerary.service.spec.ts` verifying edit mode preserves all days and stops.
- [x] **CR-004**: Harden JWT secrets, OAuth audience validation, and CORS scope:
  - [x] Add startup validation in `backend/app/core/config.py` rejecting the default JWT secret key if `environment != "development"`.
  - [x] Enforce non-empty `google_oauth_client_id` in `backend/app/services/auth_service.py` (`verify_google_id_token`); reject verification if audience is unconfigured instead of passing `audience=None`.
  - [x] Tighten CORS origin regex in `backend/app/core/config.py` from `r"^https://.*\.github\.io$"` to explicit `https://edselrenz.github.io`.
- [x] **CR-005**: Fix Google OAuth account takeover & deactivated user bypass:
  - [x] Assert `payload.get("email_verified") is True` in `backend/app/services/auth_service.py` before linking existing accounts by email.
  - [x] Enforce `user.is_active` check in `authenticate_google_user()`; return HTTP 403 Forbidden if user is inactive/banned.
  - [x] Add unit tests in `backend/tests/test_auth.py` verifying unverified emails and deactivated accounts are rejected.

---

## Phase 12: Priority 2 — Core Reliability & Functional Accuracy (COMPLETED)
> Ref: [CODE_REVIEW_AUDIT.md](file:///c:/Users/Edward/Desktop/CaseStudy/docs/CODE_REVIEW_AUDIT.md) — High & Medium Severity Functional Deficiencies

- [x] **CR-006**: Implement refresh token rotation & resilient interceptor:
  - [x] Implement `refreshSession()` in `Project/src/app/core/services/auth.service.ts` calling `POST /api/v1/auth/refresh`.
  - [x] Update `Project/src/app/core/interceptors/auth.interceptor.ts` to trap 401 Unauthorized, queue pending requests, and invoke token refresh.
  - [x] Check JWT expiration (`exp` claim) in `AuthService.isAuthenticated()`.
  - [x] Restrict `ItineraryService` guest storage fallback strictly to network outages (`status === 0 || status === 502 || status === 504`), not 401 authentication errors.
- [x] **CR-007**: Fix timezone off-by-one shifting in date parsing & generation:
  - [x] Create centralized date utility (`Project/src/app/core/utils/date.utils.ts`) with `toLocalIsoDate()`, `parseLocalIsoDate()`, and `addDaysLocal()`.
  - [x] Replace `new Date().toISOString().split('T')[0]` with local calendar date helper in `suggested-wizard.page.ts`.
  - [x] Replace `new Date("YYYY-MM-DD")` parsing and UTC arithmetic in `custom-builder.page.ts`, `itinerary-detail.page.ts`, and `itinerary.service.ts`.
  - [x] Add unit test suite in `Project/src/app/core/utils/date.utils.spec.ts` testing across timezones (UTC+8, UTC, UTC-8).
- [x] **CR-008**: Fix itinerary generator algorithm & SQL wildcard injection:
  - [x] Enforce `settings.default_dest_radius_km` (25.0 km) in `backend/app/algorithms/itinerary_generator.py` to prevent cross-province backtracking.
  - [x] Maintain cumulative daily budget tracking instead of independent per-stop budget check.
  - [x] Escape `%` and `_` SQL wildcards in `backend/app/api/v1/places.py` query parameters.
  - [x] Add test cases in `backend/tests/test_itineraries.py` verifying clustering radius enforcement.
- [x] **CR-009**: Fix offline suggested itinerary generator & dynamic form bindings:
  - [x] Call `POST /api/v1/itineraries/suggest` for guests when online; fall back to offline generator only on network failure.
  - [x] Filter POI pool in `generateOfflineSuggestedItinerary()` (`itinerary.service.ts`) by destination municipality and category preferences.
  - [x] Dynamically bind budget and preference chips in `suggested-wizard.page.html` to configured options.
- [x] **CR-010**: Implement single-stop PATCH endpoint & fix edge cases:
  - [x] Implement `PATCH /api/v1/itineraries/{id}/days/{day_id}/items/{item_id}` endpoint in `backend/app/api/v1/itineraries.py` using `ItineraryItemUpdate`.
  - [x] Fix `sort_order` default=1 bug in `add_itinerary_item()` (`default=0 + 1`).
  - [x] Validate `place_id` foreign key existence in `create_itinerary()` to prevent unhandled 500 `IntegrityError`.
- [x] **CR-011**: Fix Map page route parameters, tile error handling & honest pricing:
  - [x] Inject `ActivatedRoute` in `MapPage` (`Project/src/app/tabs/map/map.page.ts`) to read `queryParams` from Home page "Plan Route Here" and center/fly to coordinates.
  - [x] Add `tileerror` listener on Leaflet tile layer with user feedback indicator.
  - [x] Render explicit "Not verified / Not provided" labels and provenance badges in POI bottom sheet.
- [x] **CR-012**: Validate custom API URL & scope Bearer token injection:
  - [x] Validate URL protocol (`https://` or `http://localhost`) in `ConnectivityService.setCustomApiUrl()`.
  - [x] Scope `authInterceptor` Bearer token attachment strictly to `req.url.startsWith(environment.apiBaseUrl)`.
- [x] **CR-013 (F.4)**: Fix PostgreSQL restore script in `scripts/db_backup_restore.py`:
  - [x] Add `--clean --if-exists` flags to `pg_dump` invocation to ensure clean restore over existing tables.

---

## Phase 13: Priority 3 — Maintainability & Code Quality Cleanup (COMPLETED)
> Ref: [CODE_REVIEW_AUDIT.md](file:///c:/Users/Edward/Desktop/CaseStudy/docs/CODE_REVIEW_AUDIT.md) — Starter Files, Quality & Documentation

- [x] **CR-014**: Clean up dead starter code & strengthen test suite:
  - [x] Delete 16 unused starter files from initial Ionic template (`tab1/`, `tab2/`, `tab3/`, `explore-container/`).
  - [x] Remove destructive script `setup_steps_0_to_2.py`.
  - [x] Replace 7 tautological checks (`True` or `or True`) in `scripts/verify_acceptance_gate.py` with real assertions.
- [x] **CR-015**: Fix UI bugs, memory leaks, typos & unused assets:
  - [x] Fix unsubscribed observable memory leak in `ProfilePage` (`Project/src/app/tabs/profile/profile.page.ts`) by unsubscribing in `ngOnDestroy`.
  - [x] Add click handlers or disabled indicators to "Continue with Google" and "Forgot password?" in `login.page.html`.
  - [x] Dynamically query nearby places based on destination coordinates in `PlaceService.getNearbyPlaces()`.
  - [x] Correct typos: "iternaries" in `welcome.page.html:15`, "won't be save" in `guest.page.html:16`, "Remeber me" in `login.page.html:36`.
  - [x] Prune 44 unused SHA-1 hash image files in `Project/src/assets/images/`.
- [x] **CR-016**: Synchronize documentation suite:
  - [x] Update `docs/KNOWN_ISSUES.md` to reflect completed milestones and track audit findings.
  - [x] Update `docs/DEVELOPMENT_PLAN.md` to mark Milestones 7-10 completed and append Phases 11-14.
  - [x] Update `docs/PROJECT_STATE.md` with audit status and active roadmap.

---

## Phase 14: Priority 4 — Long-Term Performance & Comprehensive E2E Testing (COMPLETED)
> Ref: [CODE_REVIEW_AUDIT.md](file:///c:/Users/Edward/Desktop/CaseStudy/docs/CODE_REVIEW_AUDIT.md) — Scalability & End-to-End Test Suite

- [x] **CR-013**: Cloudflare Tunnel rate limiting & query optimizations:
  - [x] Configure SlowAPI key function in `backend/app/core/limiter.py` to inspect `CF-Connecting-IP` and `X-Forwarded-For` when `request.client.host` is local/tunnel.
  - [x] Pre-filter candidate places by bounding box in `itinerary_generator.py` instead of loading entire 4,400+ table into Python memory.
  - [x] Batch place lookups in `scripts/import_osm.py` and `scripts/seed_featured_places.py` using `in_()`.
  - [x] Add unit tests in `backend/tests/test_auth.py` and `backend/tests/test_itineraries.py`.
- [x] **CR-014**: Rewrite modern Playwright/Cypress E2E test suite:
  - [x] Replace outdated `Project/e2e/app.spec.ts` with end-to-end journey tests covering `/welcome` -> `/guest` -> `/tabs/home` -> `/tabs/map` -> `/custom-builder`.
  - [x] Verify Playwright TypeScript compilation with `npm run typecheck:e2e`.

---

## Phase 15: Technical Evaluation & QA/QC Audit Remediation (COMPLETED)
> Ref: [itinerary_app_technical_evaluation_report.pdf](file:///c:/Users/Edward/Desktop/CaseStudy/itinerary_app_technical_evaluation_report.pdf) (Audit of Commit `06cefc5`, November 2, 2026)

### Phase 15.1: Immediate Critical Fixes (Priority 1) (COMPLETED)
- [x] **DEF-04 (Duplicate Route Handler)**: Delete first shadowed `@router.patch("/{itinerary_id}/days/{day_id}/items/{item_id}")` handler (Lines 365–413) in `backend/app/api/v1/itineraries.py`, ensuring requests hit the full implementation (Lines 559–607) with `day_id` validation and `updated_at` updates.
- [x] **DEF-01 (Deceptive Forgot Password Toast)**: Remediate `onForgotPassword()` in `login.page.ts`: add email validation and connect to a backend recovery flow or display an honest pilot notice stating password recovery requires administrator assistance.
- [x] **DEF-02 (Stubbed Google Auth Buttons)**: Remediate `onGoogleLogin()` and `onGoogleSignup()`: connect Google Identity Services SDK to `POST /api/v1/auth/oauth/google`, or cleanly disable/gate the buttons with a truthful pilot caption.
- [x] **DEF-08 (Apple Sign-In Copy Typo)**: Fix copy-paste typo in `onAppleLogin()` in `Project/src/app/features/auth/login/login.page.ts:125` (*"Apple Sign-Up is disabled..."* -> *"Apple Sign-In is disabled in this pilot build."*).

### Phase 15.2: High-Priority Logic & Security Hardening (Priority 2) (COMPLETED)
- [x] **DEF-03 (Chronological Stop Ordering)**: Implement post-selection chronological sort by `planned_time` in `backend/app/algorithms/itinerary_generator.py` and `Project/src/app/core/services/itinerary.service.ts`, ensuring overnight stays are sorted to the end of each day.
- [x] **SEC-01 (API Hostname Allowlist)**: Restrict `resolveApiBaseUrl()` in `Project/src/environments/environment.prod.ts` to trusted hostnames (`localhost`, `127.0.0.1`, `anybody-cube-surprise.ngrok-free.dev`) to prevent unallowlisted `ne_custom_api_url` localStorage tampering.
- [x] **SEC-03 (Production JWT Secret Enforcement)**: Add a Pydantic `@model_validator` in `backend/app/core/config.py` raising a startup `ValueError` if `app_env != "development"` and `jwt_secret_key` is set to the default placeholder.

### Phase 15.3: Maintainability & Data Cleanliness (Priority 3) (COMPLETED)
- [x] **DEF-05 (Consolidate Offline POI Datasets)**: Consolidate triple-duplicated place arrays across `home.page.ts`, `place.service.ts`, and `itinerary.service.ts` into a single typed source: `Project/src/app/core/data/offline-places.data.ts`.
- [x] **DEF-06 (Nearby Places Category Misclassification)**: Fix `getNearbyPlaces()` in `place.service.ts` to strictly filter by retail/shopping tags when populating the Stores bucket so cultural attractions like Casa Batik are not classified as Stores.
- [x] **DEF-07 (Documentation Parity)**: Update `docs/KNOWN_ISSUES.md` Section 1.2 to reflect that History and Profile tabs are fully implemented.
- [x] **DEF-10 (Git Hygiene & Counter Artifacts)**: Add `.VSCodeCounter/` to `.gitignore` and untrack from Git index via `git rm -r --cached`.

### Phase 15.4: Long-Term Accessibility & CI (Priority 4) (COMPLETED)
- [x] **DEF-09 (Accessibility Attributes)**: Add `tabindex="0"`, `role="button"`, and `aria-label` to custom Leaflet pins in `map.page.ts`, and enable Escape key dismissal on the splash screen overlay.
- [x] **SEC-02 (Secure Token Storage)**: Formulate Architectural Decision Record (ADR-010) and migration roadmap for refresh tokens from `localStorage` to `HttpOnly; Secure; SameSite=Strict` cookies for web and native keychain for Capacitor mobile.
- [x] **CI Automation**: Add Pytest (`pytest backend/tests/`) and Vitest (`npm run test:unit`) test runs to `.github/workflows/deploy.yml` before building GitHub Pages assets.
---

## Phase 16: Release Candidate Deployment & Post-MVP Evolution (ACTIVE / PLANNED)

### Phase 16.1: Live Server Connectivity, Retry Resilience & QA Fixes (COMPLETED)
- [x] **Interactive Server Connection Manager (Offline Banner & Retry Experience)**:
  - [x] Add interactive `[Settings]` gear button to offline banner for immediate configuration.
  - [x] Enhance `retryConnection()` with visual loading spinner and positive feedback toast upon success.
  - [x] Launch `openServerConfigAlert(true)` automatically when retry fails, allowing users to inspect the unreachable URL and input/paste an active Cloudflare Tunnel (`https://*.trycloudflare.com`), ngrok URL, or localhost address.
  - [x] Implement "Reset to Default" action to restore default environment configuration.
- [x] **Dual-Tunnel Startup Architecture (`scripts/start_server.ps1` & `start_server.bat`)**:
  - [x] Launch both permanent ngrok (`anybody-cube-surprise.ngrok-free.dev`) and Cloudflare Quick Tunnel (`*.trycloudflare.com`) concurrently to port `8000`.
  - [x] Detect when port 8000 is already active to prevent port collision crashes.
  - [x] Output both connection URLs with residential Wi-Fi router Secure DNS (DoH) tips.
- [x] **QA & QC Report Remediation (itinerary_app_website_qa_report.pdf)**:
  - [x] **WQA-01**: In `guest.page.html`, replace *"Your data won't be saved."* with *"Your trips are saved locally on this device. Sign in anytime to back them up to the cloud."*.
  - [x] **WQA-02**: In `offline-places.data.ts`, adjust Day 2 venue default times/durations to prevent overlaps (Farm Villaronte: 09:00–10:30, Casa Batik: 11:00–12:30, D' Pavilion: 13:00–15:00).
  - [x] **WQA-03**: In `tabs.page.html` and `tabs.page.ts`, update Tab 3 icon to `bookmark-outline` and aria-label to `"Saved Itineraries"`.
- [x] **SEC-01 & Hostname Allowlist Expansion**:
  - [x] Update `isValidApiUrl()` and `isTrustedApiHostname()` in `environment.prod.ts`, `environment.ts`, and `connectivity.service.ts` to securely allow `*.trycloudflare.com` and `*.ngrok-free.dev`.
- [x] **Full Test Verification & Production Build**:
  - [x] Vitest unit test suite: 121/121 tests passing across 16 test files.
  - [x] Backend Pytest suite: 14/14 tests passing.
  - [x] Frontend production compilation: `npm run build` completed cleanly into `Project/www/`.

### Phase 16.2: Cloudflare Worker Reverse Proxy (Option 2) (COMPLETED)
- [x] **Cloudflare Worker Proxy Architecture (`cloudflare-worker/worker.js`)**:
  - [x] Author `cloudflare-worker/worker.js` supporting dynamic CORS (`https://edselrenz.github.io`, localhost, Capacitor).
  - [x] Implement secure `POST /__sync_tunnel` admin endpoint guarded by `X-Admin-Sync-Key`.
  - [x] Implement `GET /__status` health check and tunnel diagnostic endpoint.
  - [x] Implement auto-failover proxying (active Cloudflare Tunnel &rarr; ngrok fallback).
  - [x] Create `cloudflare-worker/wrangler.toml` configuration and `cloudflare-worker/README.md` 2-minute dashboard deployment guide.
- [x] **Auto-Publish Integration in `scripts/start_server.ps1`**:
  - [x] Automatically read `WORKER_SYNC_URL` and `WORKER_SYNC_KEY` from `.env`.
  - [x] Auto-push newly generated `$cfUrl` and `$ngrokUrl` to Worker KV on server startup.
- [x] **Frontend Security Allowlist & Settings (`SEC-01`)**:
  - [x] Allow `*.workers.dev` in `environment.prod.ts`, `environment.ts`, and `connectivity.service.ts`.
  - [x] Add unit tests in `connectivity.service.spec.ts` asserting `*.workers.dev` validation and path normalization.
  - [x] Update in-app connection settings alert and toast guidance in `app.component.ts`.
- [x] **Environment & Architecture Documentation**:
  - [x] Update `.env.example` with `WORKER_SYNC_URL` and `WORKER_SYNC_KEY`.
  - [x] Update `docs/SYSTEM_ARCHITECTURE.md` (Section 5) and `docs/CONFIGURATION_GUIDE.md` (Section 5).

### Phase 16.3: Release Candidate Deployment & Live Verification (Immediate)
- [x] Update `environment.prod.ts` fallback API base URL to permanent Cloudflare Worker (`https://ne-itinerary-api.edselrenz0.workers.dev/api/v1`).
- [x] Configure `.env` with user's permanent Worker URL and `ADMIN_SYNC_KEY`.
- [x] Add RxJS `timeout(5000)` operator to `ConnectivityService.checkHostHealth()` to eliminate browser hanging on stalled DNS lookups.
- [x] Implement automatic data rehydration via smooth reload (`window.location.reload()`) upon successful reconnection in `retryConnection()` and `Save & Connect`.
- [x] Verify end-to-end edge connectivity: `GET /api/v1/health` (200 OK) and `GET /api/v1/places` returning live database records.
- [x] Remove obsolete Settings gear button and manual tunnel configuration alert (`v0.16.4` UI hardening).
- [x] Proactive launch health probing (`AppComponent.ngOnInit()`) and ngrok offline error conversion (`v0.16.5`).
- [x] Commit all Phase 16 changes to Git with message `release: v0.16.5 proactive offline detection on app launch`.
- [x] Push to `origin/main` to trigger automated GitHub Actions CI pipeline (`deploy.yml`).
- [x] Smoke-test live production URL (`https://edselrenz.github.io/Itinerary-App/`).

---

## Phase 16: Unwired State & Template Parity (`Priority 1 — Quick Wins`) (COMPLETED)
- [x] **16.1: Render Quick Destination Chips in Suggested Wizard (`UI-01`)**:
  - [x] Target: `suggested-wizard.page.html`, `suggested-wizard.page.scss`.
  - [x] Horizontal chip row iterating over `quickDestinations` (`['Bongabon', 'Pantabangan', 'Cabanatuan City', 'Gapan City', 'General Tinio', 'Nueva Ecija']`).
  - [x] Bind to `(click)="setDestination(dest)"` with `.active` styling when `wizardForm.get('destination')?.value === dest`.
- [x] **16.2: Render Budget Summary & Assumptions Box in Suggested Wizard and Itinerary Detail (`UI-02`)**:
  - [x] Target: `suggested-wizard.page.html`, `itinerary-detail.page.html`, `global.scss`.
  - [x] In `suggested-wizard.page.html` (`viewMode === 'itinerary'`), add `.verified-budget-card` banner bound to `budgetSummary` (`minTotal`, `maxTotal`, `budgetWarning`, `dailyBudgetTarget`).
  - [x] In `suggested-wizard.page.html` and `itinerary-detail.page.html`, add expandable/collapsible **Trip Assumptions & Cost Notes** card (`.assumptions-info-box`) rendering `assumptions` array.
- [x] **16.3: Wire `pickerTab === 'browse'` Inside Custom Builder's Timeline Modal (`UI-03`)**:
  - [x] Target: `custom-builder.page.html` (Lines 515–621), `global.scss`.
  - [x] Add 2-segment switcher (`Browse Curated & OSM Places` vs. `Add Off-Grid Custom Venue`) at top of `<ion-modal [isOpen]="isPickerModalOpen">`.
  - [x] Wire search input bound to `pickerSearchQuery` / `onPickerSearchChange($event)` and scrollable list of `pickerSearchResults` calling `selectDatabasePlace(place)`.
- [x] **16.4: Eliminate Remaining Raw UTC Date Conversions (`UI-04`)**:
  - [x] Target: `suggested-wizard.page.ts` (Lines 210–211), `custom-builder.page.ts` (Lines 154–155, 189–201, 224, 241–244).
  - [x] Replace `new Date(startStr)` / `new Date(endStr)` with `formatDateRange(startStr, endStr)` from `core/utils/date-input.util.ts`.
  - [x] Replace all `new Date().toISOString().split('T')[0]` calls with `toLocalIsoDate(new Date())` and `addDaysLocal()`.
- [x] **16.5: Persist Splash Dismissal in `sessionStorage` & Clean Up Unused CSS (`UI-05`)**:
  - [x] Target: `app.component.ts`, `app.component.scss`.
  - [x] Check `sessionStorage.getItem('ne_splash_seen_v1')` in `AppComponent.ngOnInit()`. Skip 2.8s timer if already seen in current session.
  - [x] Write `'true'` to `sessionStorage` in `dismissSplash()`. Remove or bind `.pulse-ring` in `app.component.scss`.

---

## Phase 17: Custom Builder Stop Editing, Day-Move & Schedule Accuracy (`Priority 1 — Core Functional Parity`)
- [x] **17.1: Build Edit Scheduled Stop Modal & Move-to-Day Action (`UI-06`, `UI-07`)**:
  - [x] Target: `custom-builder.page.ts`, `custom-builder.page.html`, `custom-builder.page.scss`, `itinerary.service.ts`.
  - [x] Add `Edit` button (`create-outline`) on each `.timeline-stop-card`.
  - [x] Create `<ion-modal [isOpen]="isEditStopModalOpen">` to edit `planned_time`, `duration_minutes`, `estimated_cost_min`, `estimated_cost_max`, `notes`, and `targetDayNumber` (move stop across days).
  - [x] Add `updateItineraryItem()` to `ItineraryService` calling `PATCH /api/v1/itineraries/{id}/days/{day_id}/items/{item_id}`.
- [x] **17.2: Add Planned Time & Optional Coordinates to Off-Grid Custom Venue Modal (`UI-08`)**:
  - [x] Target: `custom-builder.page.ts`, `custom-builder.page.html` (Lines 529–617).
  - [x] Add `customPlannedTime` (`<input type="time">`) and collapsible `"Pin Coordinates (Lat / Lng)"` inputs bounded to Nueva Ecija (`15.15–16.15`, `120.70–121.40`).
- [x] **17.3: Fix Misleading Schedule, Budget, and Day Subtitle Fallbacks in `ItineraryDetailPage` (`UI-09`)**:
  - [x] Target: `itinerary-detail.page.ts` (Lines 169–215).
  - [x] Compute cumulative sequential windows starting from `08:30 AM` or return `'Flexible time'` (eliminate hardcoded `'12:00 PM - 2:00 PM'`).
  - [x] Update `formatDailyBudget()` to return `'Flexible Budget'` when `0` or null instead of `'₱ 3,000 - ₱ 5,000/day'`.
  - [x] Dynamically derive `getDaySubtitle(day)` from stop categories.
- [x] **17.4: Upgrade Custom Builder Browse Stage to Server-Backed Search & Add `CanDeactivate` Route Guard (`UI-10`)**:
  - [x] Target: `custom-builder.page.ts`, `app.routes.ts`, `unsaved-changes.guard.ts`.
  - [x] Pipe `browseSearchQuery` through debounced search querying all 4,400+ seeded OSM places via `placeService.searchPlaces()`.
  - [x] Add `unsavedChangesGuard` attached to `/custom-builder` and `/custom-builder/:id`.

---

## Phase 18: Missing Figma Windows — Popular Destinations Catalog, Stop Details & Commute Guide (`Priority 1 — Figma Design Parity`)
- [x] **18.1: Build Popular Destinations ("See All") Window / Modal (`UI-11`)**:
  - [x] Target: `home.page.ts`, `home.page.html`, `home.page.scss`, `global.scss`.
  - [x] Match Figma `Popular Destinations` frame: header with back button, municipality filter pills, and responsive destination catalog.
  - [x] Wire `onSeeAll()` to open this full-screen catalog view (`isPopularCatalogOpen = true`).
- [x] **18.2: Add Stop Detail Modal to `SuggestedWizardPage` & Fix Stop Card Click Binding (`UI-12`)**:
  - [x] Target: `suggested-wizard.page.html` (Line 189), `suggested-wizard.page.ts` (Line 319).
  - [x] Change `(click)="openNearbyPlaces(stop)"` to `(click)="openStopDetail(stop)"`.
  - [x] Add Stop Detail bottom-sheet modal to inspect photos, hours, cost breakdown, and transit links.
- [x] **18.3: Add Figma "How to Get There?" Commute Guide & `Travel Reminder` Section (`UI-13`)**:
  - [x] Target: `commute-guide.data.ts` (new), `itinerary-detail.page.html`, `suggested-wizard.page.html`, `global.scss`.
  - [x] Map Nueva Ecija municipalities to transit hubs (Cabanatuan Central Terminal, UV Express routes, drop-off points, travel time).
  - [x] Render advisory box with transit tips and Google Maps transit handoff.
- [x] **18.4: Make "Nearby Places" Cards Interactive with "Add to Day" & "Directions" Actions (`UI-14`)**:
  - [x] Target: `suggested-wizard.page.html`, `itinerary-detail.page.html`, `suggested-wizard.page.ts`, `itinerary-detail.page.ts`.
  - [x] Enrich `.figma-nearby-card` with category pills, cost badges, stop details click, and `"+ Add to Day"` action.
- [x] **18.5: Fix Home Destination Modal Primary CTA & Widen Popular Carousel Cards (`UI-15`)**:
  - [x] Target: `home.page.html`, `home.page.ts`, `home.page.scss`.
  - [x] Change primary CTA in Destination Detail modal to **"Build Itinerary Here"** navigating to `/suggested-wizard?destination=<muni>&placeId=<id>`.
  - [x] Widen `.dest-card` to `160px` with category and honest price badge overlays.

---

## Phase 19: Map Discovery, Multi-Select Filter Sheet & Accessible POI List Drawer (`Priority 2 — MVP Map Spec`)
- [x] **19.1: Add Floating Map Search Bar & Multi-Select Filter Bottom Sheet (`UI-16`)**:
  - [x] Target: `map.page.html`, `map.page.ts`, `map.page.scss`, `global.scss`.
  - [x] Floating search bar with clear button and active filter badge count; multi-select category checkboxes, municipality chips, price tier toggles, and Reset/Apply.
- [x] **19.2: Build Accessible Collapsible POI List Drawer on `/tabs/map` (`UI-16`)**:
  - [x] Target: `map.page.html`, `map.page.ts`, `global.scss`.
  - [x] Floating `"List View ({{ places.length }})"` toggle pill opening scrollable POI drawer with keyboard navigation, category tags, municipality, and price badges.
- [x] **19.3: Add "Add to Itinerary" CTA in Map Bottom Sheet & Dynamic Viewport Bounds Querying (`UI-17`)**:
  - [x] Target: `map.page.html`, `map.page.ts`, `custom-builder.page.ts`, `global.scss`.
  - [x] Add `"Start Trip Here"` and `"Add to Custom Trip"` buttons inside Map POI Bottom Sheet.
  - [x] Listen to Leaflet `moveend` (debounced 350ms) querying `min_lat, max_lat, min_lng, max_lng` via `placeService.searchPlaces()`.

---

## Phase 20: Profile Sub-Windows, Notifications & Saved Trips Filtering (`Priority 2 — Account & Navigation UX`)
- [x] **20.1: Build `Edit Profile` Modal & Backend `PATCH /api/v1/auth/me` Endpoint (`UI-18`)**:
  - [x] Target: `backend/app/api/v1/auth.py`, `backend/app/schemas/auth.py`, `auth.service.ts`, `profile.page.html`, `profile.page.ts`.
  - [x] Support updating `full_name`, `username`, and password with Argon2id current password check.
- [x] **20.2: Build `App Settings` Modal & Restore Optional Custom API/Tunnel Override (`UI-18`)**:
  - [x] Target: `profile.page.html`, `profile.page.ts`, `variables.scss`, `global.scss`.
  - [x] Light/Dark high-contrast theme toggle, default trip budget preference, offline data reset, and Advanced Connection Settings override.
- [x] **20.3: Add Logout Confirmation Dialog (`UI-18`)**:
  - [x] Target: `profile.page.ts`.
  - [x] Ionic `AlertController` confirmation dialog with unsynced guest trips alert.
- [x] **20.4: Build Notifications & Travel Reminders Drawer on Home (`UI-19`)**:
  - [x] Target: `home.page.html`, `home.page.ts`, `home.page.scss`.
  - [x] Modal/popover displaying upcoming trip reminders, guest trip sync status, and provincial travel advisories.
- [x] **20.5: Add Visible Text Labels to Bottom Tab Bar & Filtering to Saved Itineraries (`UI-20`)**:
  - [x] Target: `tabs.page.html`, `tabs.page.scss`, `tabs.routes.ts`, `history.page.html`, `history.page.ts`.
  - [x] Add `<ion-label>` (`Home`, `Map`, `Saved`, `Profile`); add search, segment filters (`Upcoming`, `Past`, `Suggested`, `Custom`), and total cost ranges on Saved trips.

---

## Phase 21: Authentication Completeness & Form Integrity (`Priority 2 — Auth Polish`)
- [x] **21.1: Add Explicit `Username` Field & Preserve `middleInitial` in `SignupPage` (`UI-21`)**:
  - [x] Target: `signup.page.html`, `signup.page.ts`.
  - [x] Dedicated `username` input with validation to prevent domain prefix collisions; include `middleInitial` in `fullName`.
- [x] **21.2: Wire `rememberMe` Storage Scope, Standardize Eye Icons & Add Forgot Password Modal (`UI-22`)**:
  - [x] Target: `login.page.ts`, `login.page.html`, `signup.page.html`, `auth.service.ts`.
  - [x] Toggle `localStorage` (remember) vs. `sessionStorage` (session only); standardize password eye icons; structured recovery modal.

---

## Phase 22: Trip Export/Sharing, PWA Caching & Capacitor Packaging (`Priority 3 — Post-MVP & Release`)
- [x] **22.1: Build Itinerary Export & Share Modal on `ItineraryDetailPage` (`UI-23`)**:
  - [x] Target: `itinerary-detail.page.html`, `itinerary-detail.page.ts`, `itinerary-export.util.ts`.
  - [x] Printable PDF summary view (`@media print`), RFC 5545 `.ics` calendar file download, and clipboard summary copy.
- [x] **22.2: Configure PWA Service Worker & Offline Map Tile Pre-Caching (`UI-24`)**:
  - [x] Target: `ngsw-config.json`, `angular.json`.
  - [x] Caching for `/api/v1/municipalities`, `/api/v1/places`, and OSM raster tiles within Nueva Ecija bounds (`15.15–16.15`, `120.70–121.40`).
- [x] **22.3: Scaffold Capacitor Android Project & Secure Token Storage (`UI-24`, `SEC-02`)**:
  - [x] Target: `capacitor.config.ts`, `auth.service.ts`.
  - [x] `npx cap add android`, sync web assets, abstract hardware Keystore token storage with `@capacitor-community/secure-storage-plugin`.
- [x] **22.4: Full Regression & E2E Verification Suite**:
  - [x] Target: `Project/e2e/app.spec.ts`, `scripts/verify_acceptance_gate.py`.
  - [x] Comprehensive test coverage for new catalog, modals, filter sheet, profile sub-windows, and offline behaviors.

---

## Phase 23: UI Layout Alignment, CI Robustness & Native Tooling (COMPLETED)
- [x] **23.1: Saved Itineraries & Trip Details Layout Alignment**:
  - [x] Redesigned Saved Itineraries card list (`/tabs/history`): Header, green `Custom Plan` pill, `₱3000/day` badge, trash icon, blue pin location, divider, and `2 Days - 1 Night` pill matching user layout (`media_1793789707820_06ef26d7.png`).
  - [x] Redesigned Trip Details view (`/itinerary/:id`): Day cards with destination, schedule time, duration, cost estimation, description, and personal notes (`media_1793789729229_67bc0ba8.png`).
  - [x] Implemented In-Place Trip Editor (`/itinerary/:id` Edit mode): Reorder stops (`↑`/`↓`), delete stop (`✕`), move stop across days, add activity, and add/remove days matching user layout (`media_1793789759164_2c7fb0e6.png`).
  - [x] Synchronous 0ms cached itinerary lookup (`getCachedItineraryById`) and 4s safety timeout fallback, eliminating infinite loading spinner.
- [x] **23.2: Headless CI Dependency Injection Token**:
  - [x] Introduced `SECURE_STORAGE_PLUGIN` Angular `InjectionToken` in `SecureTokenStorageService`, resolving esbuild mock proxy decoupling in Linux CI.
- [x] **23.3: VS Code Java 25 & Gradle Conflict Isolation**:
  - [x] Added `java.import.exclusions` for `**/Project/android/**` in `.vscode/settings.json` and `Project/.vscode/settings.json`, suppressing Gradle 9.6 incompatibility popups.

---

## Phase 24: Pilot Field Testing, UAT & Native Distribution (ACTIVE / NEXT)
- [ ] **24.1: Live Production Smoke Testing & UAT**:
  - [ ] Verify live GitHub Pages deployment at `https://edselrenz.github.io/Itinerary-App/` on both mobile browsers and desktop.
  - [ ] Verify Cloudflare Worker reverse proxy (`https://ne-itinerary-api.edselrenz0.workers.dev/api/v1`) edge routing and data persistence.
- [ ] **24.2: Android Device Installation & Native Packaging**:
  - [ ] Verify Progressive Web App (PWA) Add-to-Home-Screen (A2HS) installation on Android device.
  - [ ] Build and sign Android Debug/Release APK via Android Studio (`npx cap open android`) using Java 17/21.
- [ ] **24.3: End-to-End Automated Browser Journey Execution**:
  - [ ] Provision Playwright browser binaries (`npx playwright install chromium`) and execute full browser journey tests (`npm run test:e2e`).


