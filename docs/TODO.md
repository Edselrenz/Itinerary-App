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

## Phase 24: Pilot Field Testing, UAT & Native Distribution (COMPLETED)
- [x] **24.1: Live Production Smoke Testing & UAT**:
  - [x] Verified live GitHub Pages deployment at `https://edselrenz.github.io/Itinerary-App/` (HTTP 200, valid HTML title/assets).
  - [x] Verified Cloudflare Worker status endpoint (`https://ne-itinerary-api.edselrenz0.workers.dev/__status`) (HTTP 200, healthy JSON payload with active tunnel metadata).
  - [x] Added edge KV caching for `/api/v1/places/` and `/compute-day-route` in `cloudflare-worker/worker.js`.
- [x] **24.2: Android Device Installation & Native Packaging**:
  - [x] Verified Progressive Web App (PWA) manifest and Service Worker pre-caching.
  - [x] Synchronized Capacitor Android assets and native plugins (`npx cap sync android`): 6 plugins synced (@capacitor/geolocation v8.2.4, @capacitor/app, @capacitor/haptics, @capacitor/keyboard, @capacitor/status-bar, capacitor-secure-storage-plugin).
- [x] **24.3: End-to-End Automated Browser Journey Execution**:
  - [x] Provisioned Playwright Chromium browser binaries (`npx playwright install chromium`, Chrome Headless Shell, FFmpeg, Winldd).
  - [x] Executed full browser journey test suite (`npm run test:e2e`): 5/5 browser journey tests passed (100%) in 11.9s.

---

## Phase 25: GIS Upgrade, Live Google Places & Turn-by-Turn Routing (COMPLETED)
> Ref: [itinerary_app_gis_upgrade_technical_spec.md](file:///c:/Users/Edward/Desktop/CaseStudy/itinerary_app_gis_upgrade_technical_spec.md)

### Phase 25.1: Foundation, Schemas & Proxy Services (COMPLETED)
- [x] **25.1.1 (Config & Security)**: Add `google_maps_api_key`, `google_places_cache_ttl_hours`, and `google_routes_cache_ttl_hours` to `backend/app/core/config.py`.
- [x] **25.1.2 (ORM Models & Caching Table)**: Expand `Place`, `ItineraryDay`, and `ItineraryItem` models in `backend/app/models/entities.py` and define `GeospatialCache` table with portable `JsonType`.
- [x] **25.1.3 (Alembic Migration 0002)**: Create reversible Alembic migration `backend/alembic/versions/0002_google_places_and_routing.py`.
- [x] **25.1.4 (Pydantic Schemas & Frontend Models)**: Expand `PlaceOut`, `ItineraryItemOut`, and `SuggestedItineraryRequest` in `backend/app/schemas/` and TypeScript interfaces in `Project/src/app/core/models/`.
- [x] **25.1.5 (GoogleMapsService)**: Implement `GoogleMapsService` with Discovery/Details FieldMasks, `compute_route()`, in-db `GeospatialCache`, and automatic OSRM/Haversine fallback.
- [x] **25.1.6 (FK Upsert-on-Save Safety & Routing Endpoints)**: Update `create_itinerary()` and `update_itinerary()` in `itineraries.py` with `resolve_or_upsert_item_place()` and add route calculation endpoints (`POST /compute-day-route`, `POST /compute-route`).
- [x] **25.1.7 (Automated Test Suite)**: Implement `backend/tests/test_google_maps_service.py` verifying polyline utils, haversine, fallback routing, and discover endpoints. (20/20 backend tests passing, 205/205 frontend tests passing).

### Phase 25.2: Live Discovery & Recommendation Engine Upgrade (COMPLETED)
- [x] **25.2.1 (Bayesian Scoring & Hours Gate)**: Implement Bayesian quality scoring and `is_open_during_slot()` in `backend/app/algorithms/itinerary_generator.py`.
- [x] **25.2.2 (2-Opt & Dynamic Pacing)**: Implement 2-Opt permutation check and dynamic travel-time arrival scheduling from Routes API.
- [x] **25.2.3 (Polyline & Distance Utilities)**: Implement `Project/src/app/core/utils/polyline.util.ts` (`encodePolyline`, `decodePolyline`, `haversineDistanceMeters`) with unit tests.
- [x] **25.2.4 (Offline Generator Bug Fix)**: Fix `generateOfflineSuggestedItinerary()` in `itinerary.service.ts` to respect non-Bongabon destinations, utilize `matchedPool`, and compute offline overview polylines and turn legs.

### Phase 25.3: Active Routing & Geolocation Tracking (COMPLETED)
- [x] **25.3.1 (Capacitor Geolocation)**: Install `@capacitor/geolocation` and configure Android permissions in `AndroidManifest.xml` (`ACCESS_FINE_LOCATION`, `ACCESS_COARSE_LOCATION`, GPS feature).
- [x] **25.3.2 (Polyline Utilities & RouteTrackingService)**: Create `polyline.util.ts` geometric helpers (`distanceToSegmentMeters`, `distanceToPolylineMeters`, `remainingDistanceAlongPolylineMeters`) and `RouteTrackingService` with point-on-segment snapping, 10m movement throttle, 50m stop arrival detection, and 100m off-route event dispatch.
- [x] **25.3.3 (Unclustered Leaflet Layers on Map)**: Add `routePolylineLayer`, `itineraryStopsLayer` (numbered `1..N` outside cluster group), `userLocationMarker` (pulsing blue dot with heading pointer), and active route navigation HUD banner in `map.page.ts`.
- [x] **25.3.4 (Embedded Route Map on Detail)**: Add interactive Leaflet route preview map, day navigation CTA ("Navigate Day"), and route leg travel badges (`🚗 12 km • 18 min`) to `itinerary-detail.page.ts`.

### Phase 25.4: Unified PlaceDetailSheetComponent & UI Polish (COMPLETED)
- [x] **25.4.1 (Standalone Bottom Sheet)**: Implement `PlaceDetailSheetComponent` (`Project/src/app/shared/components/place-detail-sheet/`) with photo carousel/thumbnails, ratings, open/closed badges, weekly schedule accordion, reviews snippet, and itinerary CTAs.
- [x] **25.4.2 (Modal Consolidation Across All Pages)**: Replaced duplicate bottom sheet markup across `map.page.html`, `suggested-wizard.page.html`, and `itinerary-detail.page.html` with `<app-place-detail-sheet>`.
- [x] **25.4.3 (Nearby Coordinates Bug Fix)**: Added coordinates (`latitude`, `longitude`, `google_place_id`) to `NearbyPlaceItem` in `offline-places.data.ts` and updated `addNearbyPlaceToActiveDay()` in both `itinerary-detail.page.ts` and `suggested-wizard.page.ts` to bind real coordinates instead of hardcoded coordinates.
- [x] **25.4.4 (Wizard Quality Controls & Inter-Stop Leg Badges)**: Added Travel Mode and Minimum Rating controls to `SuggestedWizardPage`, rating pills, and road travel connectors between consecutive stops.
- [x] **25.4.5 (Regression, E2E & Production Build Verification)**: 21/21 backend pytest tests passing (100%), 24/24 frontend test files (230/230 unit tests) passing (100%), 5/5 Playwright E2E tests passing (100%), and `ng build` production bundle generated with 0 errors and 0 warnings.

---

## Phase 26: Provincial OpenStreetMap Ingestion & Interactive Real-World Map Display (COMPLETED)
- [x] **26.1: Provincial OpenStreetMap Overpass Extraction**:
  - [x] Extracted 2,995 raw features from OpenStreetMap via Overpass API into `data/raw/nueva_ecija_osm.json`.
  - [x] Validated and ingested 2,656 real-world places into `nueva_ecija_travel.db`, reaching 2,673 total destinations across all 32 municipalities.
  - [x] Ingested all mapped cafes (58), restaurants (374), hotels/lodgings (120), nature parks (122), tourist attractions (104), churches (487), museums (5), clinics/hospitals (102), pharmacies (146), banks (148), gas stations (293), and terminals (37).
- [x] **26.2: Bundled Client Asset Generation (`assets/data/osm_places.json`)**:
  - [x] Implemented `scripts/export_osm_to_client_asset.py` generating lean 1.5 MB static client asset with all 2,673 destinations.
  - [x] Verified asset bundling in Angular production build output (`Project/www/assets/data/osm_places.json`).
- [x] **26.3: Client-Side `PlaceService` & Live Overpass Service**:
  - [x] Enhanced `PlaceService.searchPlaces()` with `loadOsmPlaces()` fallback, enabling instant in-memory filtering by keyword, category, municipality, and bbox when offline or decoupled from backend.
  - [x] Created `OsmOverpassService` (`Project/src/app/core/services/osm-overpass.service.ts`) with unit tests for real-time live OpenStreetMap querying for any viewport.
- [x] **26.4: Interactive Map Display & Category Pins**:
  - [x] Raised `MapPage.loadPlaces()` limit to 3,000, displaying all 2,673 destinations across Nueva Ecija in Leaflet MarkerCluster badges.
  - [x] Raised backend `GET /api/v1/places` query cap to `le=5000` in `backend/app/api/v1/places.py`.
  - [x] Added Live OpenStreetMap discovery button (`sparkles-outline`) and status feedback pill.
  - [x] Added category-specific vector pin classes and color palettes for all 16 canonical categories.
  - [x] Elevated `.map-floating-controls` and centered `.poi-list-toggle-pill` to clear mobile bottom navigation tabs cleanly.
- [x] **26.5: Database Resiliency & Automated Verification**:
  - [x] Updated `.env` default to `DATABASE_URL=sqlite:///./nueva_ecija_travel.db` and added automatic SQLite root path resolution and graceful fallback in `backend/app/core/database.py`.
  - [x] 21/21 backend pytest tests passing (100%).
  - [x] 25/25 frontend unit test files (235/235 unit tests) passing (100%).
  - [x] Angular production build passes with 0 errors and 0 warnings.
  - [x] 7/7 Playwright E2E browser tests passing (100%) with verified visual screenshots (`map_places_display.png`, `place_detail_sheet_open.png`).



---

## Phase 27: Map & Routing System Architecture Overhaul (Phased Engineering Proposal)
> Ref: [itinerary_app_map_and_routing_proposal.pdf](file:///c:/Users/Edward/Desktop/CaseStudy/itinerary_app_map_and_routing_proposal.pdf) & [MAP_AND_ROUTING_PROPOSAL.md](./MAP_AND_ROUTING_PROPOSAL.md)

### Phase 27.1: Immediate Production Bug Fixes (Day 1) (COMPLETED)
- [x] **27.1.1 (MAP-01: Leaflet MarkerCluster ESM Initialization)**:
  - Unwrap canonical Leaflet object via `const LeafletLib = (L as any).default ?? L; (window as any).L = LeafletLib;` at module top-level in `Project/src/app/tabs/map/map.page.ts`.
  - Add graceful fallback to `L.layerGroup()` if `markerClusterGroup` is not found, ensuring pins always render on production esbuild bundles (GitHub Pages).
- [x] **27.1.2 (MAP-02: Full-Stack Municipality & Price Tier Filtering)**:
  - Extend `backend/app/api/v1/places.py` `GET /api/v1/places` with `municipality_name: str | None` and `price_tier: str | None` to filter in SQL before LIMIT is applied.
  - Mirror bounding-box, municipality, and price filtering logic inside `PlaceService.getFallbackPaginatedPlaces()`.
  - Pass municipality and price tier filters from `MapPage.loadPlaces()`.
- [x] **27.1.3 (MAP-03: Deep-Link Pin Selection & Programmatic Fly Guard)**:
  - Pass `placeId` in `HomePage.viewDestinationOnMap()` deep-links.
  - Set `isProgrammaticFly = true` during `flyTo()` in `MapPage` so `onMapMoveEnd()` does not wipe markers mid-flight.
  - Automatically resolve and assign `this.selectedPlace` to open `PlaceDetailSheetComponent`.
  - Remove hardcoded `15.48, 120.97` fallback in `home.page.ts`.
- [x] **27.1.4 (ROUTE-02: Re-cluster Offline Day Presets into Corridors)**:
  - Update `getOfflineDayClusterPresets()` in `Project/src/app/core/data/offline-places.data.ts`.
  - Re-cluster stops into East Corridor (Bongabon, 1.5 km), North Corridor (San Jose–Pantabangan, 13.8 km), and South Corridor (Cabanatuan–Gen. Tinio–Gapan, 45.5 km), cutting straight-line transit distance by 66.3% from 176.2 km to 59.4 km.
- [x] **27.1.5 (ROUTE-03: Nearby Place Coordinates & Storage Persistence)**:
  - Ensure verified coordinates on `NearbyPlaceItem` in `itinerary-detail.page.ts` and `suggested-wizard.page.ts`, removing hardcoded `15.63, 121.14` fallback.
  - Persist added nearby stops via `this.itineraryService.updateItinerary()` so changes survive page refresh.

### Phase 27.2: Reusable Route Map & Multi-Stop Waypoints (Days 2–3) (COMPLETED)
- [x] **27.2.1 (ROUTE-01: Shared ItineraryRouteMapComponent)**:
  - Create reusable standalone component `ItineraryRouteMapComponent` rendering numbered pins, connecting polylines, and bounds fitting.
  - Embed into `ItineraryDetailPage`, `SuggestedWizardPage` (Step 2), and `CustomBuilderPage` (Timeline view).
  - Add "Open Full Route on Map" action deep-linking to `/tabs/map?followRoute=true&dayNumber={d}&itineraryId={id}`.
- [x] **27.2.2 (ROUTE-01: Road Polylines & Geodesic Spline Fallback)**:
  - Integrate OSRM public routing API with local IndexedDB caching and 2.5s timeout.
  - Implement offline fallback rendering dashed Catmull-Rom geodesic spline arcs with road-winding multiplier ($1.28 \times$ lowlands, $1.45 \times$ mountains).
- [x] **27.2.3 (ROUTE-01: Multi-Stop Google Maps URL Builder)**:
  - Add "Navigate Entire Day in Google Maps" action building standard universal cross-platform multi-stop URLs:  
    `https://www.google.com/maps/dir/?api=1&origin={origin}&destination={dest}&waypoints={w1}|{w2}&travelmode=driving`.
- [x] **27.2.4 (ROUTE-02: Corridor Selection & 2-Opt TSP Engine Refinement)**:
  - Enhance backend `backend/app/algorithms/itinerary_generator.py` candidate clustering to partition multi-day trips across adjacent corridors and apply 2-opt TSP permutation before slot assignment.

### Phase 27.3: Router Polish & Leg-Aware Commute Guide (Day 4) (COMPLETED)
- [x] **27.3.1 (ROUTE-04: CanDeactivate Guard on /itinerary/:id)**:
  - Attach `pendingChangesGuard` to `/itinerary/:id` in `Project/src/app/app.routes.ts` and implement `canDeactivate()` on `ItineraryDetailPage` to prevent accidental loss of unsaved in-place edits.
- [x] **27.3.2 (ROUTE-04: History-Aware Back Navigation)**:
  - Implement history-aware back navigation via `Location.back()` with fallback to `/tabs/history`.
- [x] **27.3.3 (ROUTE-04: True GPS Locate Me Control)**:
  - Add dedicated "Locate Me" button invoking `navigator.geolocation.getCurrentPosition` with blue pulsing user dot and map camera flight.
  - Maintain a separate "Reset Province View" button flying to `NUEVA_ECIJA_CENTER`.
- [x] **27.3.4 (ROUTE-04: URL Query Parameter Synchronization)**:
  - Synchronize active map search, category, municipality, and price filters to URL query parameters via `router.navigate()`.
- [x] **27.3.5 (ROUTE-05: Leg-Aware Provincial Commute Engine)**:
  - Upgrade `commute-guide.data.ts` to `getLegCommuteInfo(prevStop, currentStop)`.
  - Provide specific route advice for intra-town hops ($\le 1.2$ km walk/tricycle ₱15–₱25), inter-town corridors, and provincial hubs across all 32 municipalities.


---

## Phase 28: Suggested Itinerary, Route Map & Navigation UI/UX Remediation
> Ref: [itinerary_app_ui_ux_evaluation_report.pdf](file:///c:/Users/Edward/Desktop/CaseStudy/itinerary_app_ui_ux_evaluation_report.pdf) & [UI_UX_EVALUATION_REPORT.md](./UI_UX_EVALUATION_REPORT.md)

### Phase 28.1: P0 Immediate Quick Wins (`itinerary-detail.page.html & .ts`) (COMPLETED)
- [x] **28.1.1 (UIUX-04: Restore Header Share Button)**:
  - Add visible Share button (`share-social-outline`) in `itinerary-detail.page.html` header toolbar wired to `openShareModal()`.
- [x] **28.1.2 (UIUX-05: Restore Nearby Places Banner)**:
  - Restore the interactive dashed *Nearby Places in {{ getDayLocation(day) }}* trigger banner inside each day card calling `openNearbyPlaces()`.
- [x] **28.1.3 (UIUX-03: Rich Time Window Formatting)**:
  - Replace `formatTimingHour()` with `getTimingTime(stop, sIdx)` in `itinerary-detail.page.html` to display full start-end time windows and duration (`12:00 PM - 2:00 PM (2 hrs)`).
- [x] **28.1.4 (UIUX-02: Eliminate Fabricated ₱200 Cost Fallbacks)**:
  - Remove `return '200'` in `getStopEstimatedCost()` and `?? 200` in `calculateTotalActivityExpenses()` in `itinerary-detail.page.ts`.
  - Display *Fee not listed* on unpriced stop cards and delegate directly to `this.budgetSummary` to align with the top Verified Estimated Costs banner.
- [x] **28.1.5 (UIUX-07: Human-Readable Date Range Formatting)**:
  - Bind `formattedDateSpan` in `itinerary-detail.page.html` to display human-readable formatted dates (`Nov 6 – Nov 8, 2026 (3 Days, 2 Nights)`).
- [x] **28.1.6 (UIUX-06: Header Chrome Simplification & False Affordances)**:
  - Remove the redundant top `Saved Itineraries [+]` bar on `/itinerary/:id`, unifying into a single header toolbar (`← Trip Title | [Share] [Edit]`).
  - Remove non-interactive right-arrow (`→`) icon in card footer.
- [x] **28.1.7 (UIUX-01: Stop Card Photo Thumbnails & Badges)**:
  - Restore 68×68px stop thumbnail photos and step numbering badges on `.activity-view-card` in `itinerary-detail.page.html`.

### Phase 28.2: P1 Navigation & Route Visualization (COMPLETED)
- [x] **28.2.1 (UIUX-08: Multi-Waypoint Day Route Builder)**:
  - Implement `buildGoogleMapsDayRouteUrl(items: ItineraryItem[]): string | null` in `Project/src/app/core/utils/itinerary-export.util.ts`.
- [x] **28.2.2 (UIUX-08: "Start Day Route in Google Maps" Primary Action)**:
  - Add primary action button on each day header to launch a single multi-waypoint Google Maps route for all stops on that day in sequence.
- [x] **28.2.3 (UIUX-08: Inline Per-Stop Quick Navigation)**:
  - Place a quick-action directions icon button (`navigate-outline`) on the right edge of every stop card for one-tap single-leg navigation without opening the detail sheet.
- [x] **28.2.4 (UIUX-09: Segmented Day Switcher on Saved Itineraries)**:
  - Implement sticky segmented day switcher capsule bar on `/itinerary/:id` synchronized with active day's timeline cards.
- [x] **28.2.5 (UIUX-10: Un-hide Budget & Assumptions on Custom Trips)**:
  - Remove `[class.hidden-on-custom]` restrictions so custom itineraries with budget entries display the verified budget card and editable assumptions.

### Phase 28.3: P2 Modals & Leg-Aware Commute Guidance (COMPLETED)
- [x] **28.3.1: Stop Detail Sheet Parity**:
  - Ensure `<app-place-detail-sheet>` displays hero photo, verified hours, price range, and WCAG 2.2 accessible close button across all calling contexts.
- [x] **28.3.2: Leg-Aware Commute Guidance**:
  - Coordinate with Phase 27.3.5 to render leg-level commute advice for intra-town hops (walk/tricycle) vs. inter-town corridors.

### Phase 28.4: Leaflet Marker Clustering & Zstopero-Watermark Production Hardening (COMPLETED)
- [x] **28.4.1 (Production Marker Clustering Hardening)**:
  - Guard `window.L` in `Project/src/main.ts` with an ES5 property descriptor getter/setter that prevents destructive overwrites from wiping out plugin attachments (`L.MarkerClusterGroup`, `L.markerClusterGroup`).
  - Eliminate redundant destructive `window.L = L` assignments across `map.page.ts`, `itinerary-detail.page.ts`, and `itinerary-route-map.component.ts`.
  - Fixes runtime `TypeError: L.MarkerClusterGroup is not a constructor` in production ES module builds on GitHub Pages (`edselrenz.github.io/Itinerary-App/tabs/map`).
  - Verified with Playwright: 2,673 places render across 73 interactive cluster circles and 91 visible pins.
- [x] **28.4.2 (Zero-Paid-API OSRM Road Routing & OSM Tiles)**:
  - Replace CartoDB Voyager raster tiles with OpenStreetMap raster tiles (`tile.openstreetmap.org`) in `ItineraryRouteMapComponent` to eliminate the "API KEY REQUIRED" watermark.
  - Wire client-side OSRM driving API (`router.project-osrm.org`) with geodesic spline fallback and IndexedDB caching for 100% free road routing adhering to ADR-001.

---

## Phase 29: Custom & Suggested Itinerary Workflow Remediation
> Ref: [custom_and_suggested_itinerary_proposal.pdf](file:///c:/Users/Edward/Desktop/CaseStudy/custom_and_suggested_itinerary_proposal.pdf) & [CUSTOM_AND_SUGGESTED_ITINERARY_PROPOSAL.md](./CUSTOM_AND_SUGGESTED_ITINERARY_PROPOSAL.md)

### Phase 29.1: P0 Data Integrity & Offline Engines (COMPLETED)
- [x] **29.1.1 (C-BUG-06: Custom Stop Metadata Retention in Guest Save)**:
  - In `custom-builder.page.ts` (`BuilderStop` interface & `addPlaceStop`), retain full `place: Place` reference and set `custom_title: place.name`.
  - In `saveItinerary()`, serialize `place` object, `custom_title || it.name`, and coordinates `custom_lat/custom_lng` from `it.place`.
  - In `ItineraryService.mapGuestItinerary()`, hydrate stops with `place_id` against `PlaceService` to eliminate fallback to generic "Destination Stop" with ₱200 fabricated fee.
- [x] **29.1.2 (S-BUG-03: Wire matchedPool in Offline Suggested Generator)**:
  - In `itinerary.service.ts` (`generateOfflineSuggestedItinerary`), connect `matchedPool` (filtered by municipality, budget, and Haversine proximity) to `dayPlaces` instead of discarding it and falling back to Bongabon `curatedPool[0..2]`.
- [x] **29.1.3 (S-BUG-04: 0ms Immediate Offline Short-Circuit)**:
  - Inject `ConnectivityService` into `ItineraryService.suggestItinerary()`; if `isHostOfflineSnapshot` or `!navigator.onLine`, invoke `generateOfflineSuggestedItinerary()` immediately without waiting for the 4-second HTTP timeout.
- [x] **29.1.4 (S-BUG-02: Enforce Local ISO Date Helpers in Suggested Wizard)**:
  - Replace UTC `new Date(str).toISOString()` in `SuggestedWizardPage.openDatePicker()` and `setPresetDuration()` with `parseLocalIsoDate()` / `toLocalIsoDate()` to prevent UTC+8 off-by-one shifts.
- [x] **29.1.5 (S-BUG-01: Anchor placeId in Suggested Deep-Link)**:
  - In `SuggestedWizardPage.ngOnInit()`, read `params['placeId']` and lock the selected POI as Stop 1 of Day 1 in the generated itinerary request.

### Phase 29.2: P1 Form, Browse & Date Sync (COMPLETED)
- [x] **29.2.1 (C-BUG-01: Custom Builder Step 1 Title & Quick Chips)**:
  - Add Trip Title input field (e.g., "Weekend Family Roadtrip") and reusable Quick Destination & Budget preset chips to `custom-builder.page.html`.
  - Rename bottom CTA button from "Find Itinerary" to "Start Building Itinerary →".
- [x] **29.2.2 (C-BUG-02: Complete 16-Category Filter Mapping in catMap)**:
  - Expand `catMap` in `custom-builder.page.ts` to map all 16 canonical categories: All, Attractions & Nature, Food & Cafes, Resorts & Stays, Culture & Heritage, Shopping & Markets, and Transit & Essentials (terminals, hospitals, pharmacies, ATMs, gas stations, convenience stores).
- [x] **29.2.3 (C-BUG-05: Reactive Date Range to Days Synchronization)**:
  - Implement `syncDaysWithDateRange()` in `custom-builder.page.ts` triggered when `start_date` or `end_date` is edited in Step 3 settings, preserving existing stops while updating `day.travel_date`.
- [x] **29.2.4 (UC-C4: Direct Modal Tab Routing for Off-Grid Venues)**:
  - Update `openPlacePicker(defaultTab: 'browse' | 'custom' = 'browse')` in `custom-builder.page.ts` and bind "Add Off-Grid Custom Venue" directly to `openPlacePicker('custom')`.
  - Enable `.picker-add-action-btn` for already-added places so clicking triggers the duplicate confirmation alert (`selectPlaceFromPicker`).

### Phase 29.3: P2 Unified Editor & Draft State Handoff (COMPLETED)
- [x] **29.3.1 (S-BUG-06: In-Memory Router State for Customize in Builder)**:
  - Update `SuggestedWizardPage.customizeInBuilder()` to pass `this.generatedPlan` via `router.navigate(['/custom-builder'], { state: { draftItinerary: this.generatedPlan } })` to eliminate duplicate premature saves.
  - Implement `CustomBuilderPage.populateFromItinerary()` checking `history.state.draftItinerary` / navigation state to hydrate draft days and form controls without premature persistence.
- [x] **29.3.2 (UC-C5: Unified Saved Trip Editor)**:
  - Direct the Edit action on `ItineraryDetailPage` to open `/custom-builder/:id`, giving users full visual timeline, catalog picker, and off-grid coordinate validator.
  - Preserve separate `estimated_cost_min` and `estimated_cost_max` fields across `EditableActivityItem`, `initEditForm()`, and `saveChanges()`.
- [x] **29.3.3 (C-BUG-04: Card Inspection in Browse Grid)**:
  - Make destination cards in `CustomBuilderPage` Browse view clickable to open `<app-place-detail-sheet>` with an inline "+ Add to Day {{ activeDayNumber }}" button and full photo gallery, hours, reviews, and commute info.
- [x] **29.3.4 (Automated Schedule Chaining & Post-Save Redirect)**:
  - Implement `calculateNextStopTime()` auto-chaining sequential stop time windows with a 30-min transit buffer when adding places in Custom Builder.
  - Add one-tap `autoOptimizeDaySchedule()` action button to timeline day banner.
  - Redirect user to `/itinerary/:id` upon successful save instead of exiting to `/tabs/home`.

---

## Phase 30: Live-Server Map & Suggested Itinerary Routing Upgrade
> Ref: [live_server_map_and_suggested_itinerary_proposal.pdf](file:///c:/Users/Edward/Desktop/CaseStudy/live_server_map_and_suggested_itinerary_proposal.pdf) & [LIVE_SERVER_MAP_AND_SUGGESTED_ITINERARY_PROPOSAL.md](./LIVE_SERVER_MAP_AND_SUGGESTED_ITINERARY_PROPOSAL.md)

### Phase 30.1: P0 Map Tab False-Offline Banner & Tile Latching Fix (COMPLETED)
- [x] **30.1.1 (GAP-04: Auto-Clear Map Tile Error Banner)**:
  - In `map.page.ts`, listen to `tilelayer.on('tileload')` to automatically clear `hasTileError = false` when tiles load successfully.
  - Guard `tileerror` so only sustained tile delivery failures (>= 3 consecutive) trigger the banner, rather than a single canceled or out-of-viewport tile request.
- [x] **30.1.2 (GAP-04: Resilient Connectivity State Reconciliation)**:
  - In `auth.interceptor.ts`, ensure successful API responses (`HttpResponse`) automatically reset `connectivityService.setHostOffline(false)` when the backend is reachable.
  - Prevent secondary background request aborts (`AbortError` or progress events) during 2,673-POI batch hydration from overriding verified online state.

### Phase 30.2: P1 Focused Route Mode & Pre-Save Draft Persistence (COMPLETED)
- [x] **30.2.1 (GAP-02: Isolated Route Focus Mode on MapPage)**:
  - In `map.page.ts` / `map.page.html`, implement `isFollowRouteMode`: when `followRoute=true`, hide the 2,673 background discovery markers/clusters by default so the active day's stops and route polyline are isolated.
  - Add a floating Active Route Control Bar with `← Back to Plan` button, `Day 1 | Day 2 | All Days` switcher chips, and a `"Show Nearby POIs (+2,673)"` toggle switch.
  - Add an interactive bottom route card carousel (`Stop 1 of 3 → Stop 2 of 3 → Stop 3 of 3`) with a `"Start Multi-Stop Google Maps Navigation"` CTA.
- [x] **30.2.2 (GAP-03: Pre-Save In-Memory Draft Persistence)**:
  - In `itinerary.service.ts`, implement `activeDraftItinerary$` caching in memory / `sessionStorage`.
  - When clicking "Full Map" from `SuggestedWizardPage`, preserve `this.generatedPlan` so navigating back from `/tabs/map` returns to the generated itinerary without resetting to the blank wizard form.

### Phase 30.3: P2 Road-Snapped Polylines, Commute Badges & Bi-Directional Pin Sync (COMPLETED)
- [x] **30.3.1 (GAP-01: Per-Leg Distance & Commute Pills)**:
  - Display compact connector pills between stop cards in `suggested-wizard.page.html` and `itinerary-detail.page.html`: `🚗 5.2 km • ~11 mins drive / 18 mins tricycle • Est. Fare ₱50–₱80`.
  - In `backend/app/algorithms/itinerary_generator.py`, implement `enrich_day_route_legs()` calculating arterial road circuity distance (`straight_km * 1.28`), drive/tricycle durations, and route geometry.
- [x] **30.3.2 (GAP-05: Bi-Directional Stop Card & Map Pin Highlighting)**:
  - In `ItineraryRouteMapComponent` and parent wizard/detail views, implement reactive `selectedStopIndex: number | null` two-way synchronization.
  - Tapping a stop card centers and pulses its numbered pin on the preview map; tapping a map pin scrolls to the corresponding stop card.

### Phase 30.4: P3 Spatial Indexing & Canvas Clustering for 2,673+ POIs (COMPLETED)
- [x] **30.4.1 (Performance: Canvas Rendering & Viewport SQL Indexing)**:
  - Set `preferCanvas: true` on `MapPage` Leaflet options to eliminate DOM element overhead across 2,673+ markers.
  - In `backend/app/models/entities.py`, add composite spatial index `Index("ix_places_lat_lng_active", "latitude", "longitude", "is_active")` on `Place` model.

---

## Phase 31: Suggested & Custom Itinerary Preference Engine, Destination Autofill & Catalog Browse Upgrade (COMPLETED)
> Ref: [suggested_and_custom_itinerary_live_evaluation.pdf](file:///c:/Users/Edward/Desktop/CaseStudy/suggested_and_custom_itinerary_live_evaluation.pdf) & [SUGGESTED_AND_CUSTOM_ITINERARY_LIVE_EVALUATION.md](./SUGGESTED_AND_CUSTOM_ITINERARY_LIVE_EVALUATION.md)

### Phase 31.1: P0 Destination Autofill Combobox, 32 LGUs & Wrapped Quick-Select Pills (COMPLETED)
- [x] **31.1.1 (Reusable Destination Autocomplete Component)**:
  - Create `<app-destination-autocomplete>` in `Project/src/app/shared/components/destination-autocomplete/destination-autocomplete.component.ts` (.html, .scss, .spec.ts).
  - Index all 32 Nueva Ecija municipalities/cities with district groupings, POI counts, and top highlight vibe tags.
  - Index loaded featured landmarks/attractions (e.g., Minalungao National Park, Highland Bali Villas) with automatic parent municipality resolution and `anchor_place_id` assignment.
  - Implement Unicode NFD diacritic stripping (`normalizeText()`) so unaccented typing (e.g. "munoz", "penaranda") correctly resolves to "Science City of Muñoz" and "Peñaranda".
  - Integrate combobox into both `suggested-wizard.page.html` and `custom-builder.page.html`.
- [x] **31.1.2 (Responsive 2-Row Wrapped Chips & Regional Explorer Modal)**:
  - Replace clipped single-row horizontal scroll (`overflow-x: auto`) in `suggested-wizard.page.scss` with a responsive wrapped pill grid (`flex-wrap: wrap`) displaying the top 6 travel hubs without text truncation.
  - Add an interactive `🗺️ Browse All 32 Towns` trigger chip opening a categorized North / Central / South / East Nueva Ecija regional picker modal.

### Phase 31.2: P0 Preference Category Mapping, Sequential Time Windows & Deduplication (COMPLETED)
- [x] **31.2.1 (PREF-02 & PREF-03: Canonical Preference Category Mapping & Strict Filtering)**:
  - In `Project/src/app/core/services/itinerary.service.ts`, replace broken `.includes(pr)` substring checks with canonical `PREFERENCE_CATEGORY_MAP` resolving `food` -> `['restaurant', 'cafe']`, `culture` -> `['museum_cultural', 'church_religious']`, `nature` -> `['nature_park', 'tourist_attraction']`, `resort` -> `['resort_swimming', 'hotel_accommodation']`, and `shopping` -> `['shopping_market', 'convenience_store']`.
  - Apply strict category gating on Day 1 activity slots within an expanding radius ($15\text{ km} \to 30\text{ km} \to 45\text{ km}$) so selecting "Nature & Parks ONLY" immediately updates Day 1 stops.
- [x] **31.2.2 (PREF-04: Sequential Rolling Time Slots with Transit Buffer)**:
  - Replace hardcoded static `10:00 AM - 12:00 PM` timestamps in `itinerary.service.ts` with sequential non-overlapping time slot windows (`09:30 AM – 11:30 AM`, `12:00 PM – 01:30 PM`, `03:00 PM – 05:00 PM`) calculating real inter-stop travel duration.
  - Fix backwards time ordering in `isOvernightItem()` so lodging is scheduled chronologically at end-of-day.
- [x] **31.2.3 (PREF-05: Pacing & Smart Dining Anchor)**:
  - Add lightweight Smart Dining toggle ("Include Daily Lunch Spot", default: ON) so single-category runs (e.g. Nature & Parks) always schedule 1 realistic midday dining stop (`12:00 PM – 01:30 PM`).
  - Add activity intensity guard (`isMountainPeak` / `is_mountain_peak`) capping strenuous mountain hikes to max 1 per day across frontend and backend generators.
- [x] **31.2.4 (PREF-06: Cross-Day Fuzzy Venue Name & Coordinate Deduplication)**:
  - Implement `normalizeVenueName()` / `normalize_venue_name()` stripping common venue suffixes (`viewdeck`, `resto`, `resort`, `villas`) and check physical proximity ($< 200\text{ m}$) preventing duplicate venues across different days.
- [x] **31.2.5 (PREF-01: Decoupled Fast-Path Generation & Increased Timeout)**:
  - In `backend/app/algorithms/itinerary_generator.py`, default `include_live_places = False` when local database contains $\ge 15$ candidates in bounding box.
  - Increase HTTP timeout in `itinerary.service.ts:360` from 4s to 10s (`timeout(10000)`).

### Phase 31.3: P1 Custom Builder Catalog Browse & Preference Tab Sync (COMPLETED)
- [x] **31.3.1 (CUST-01 & CUST-02: Full 2,673-POI Catalog Pre-Loading & Preference Filter Sync)**:
  - In `custom-builder.page.ts:865–879`, query `searchPlaces({ municipality_name: dest, limit: 100 })` pre-loading all local POIs for the chosen town instead of restricting to 17 featured places.
  - Fix category mapping in `proceedToBuilder()` so selecting Culture & History or Resort in Step 1 maps to matching categories instead of a restricted `Tourist Spots` tab.
  - Add `✨ Recommended for You` tab combining all selected Step 1 preferences.
- [x] **31.3.2 (CUST-03: Timeline Auto-Schedule Inter-Stop Transit Buffer)**:
  - In `custom-builder.page.ts:1165–1195`, update `autoOptimizeDaySchedule()` to incorporate inter-stop transit time between stops rather than scheduling back-to-back ($0\text{ min}$) transit.

---

## Phase 32: Full-Website QA Remediation, Connectivity Hardening & Polish (COMPLETED)
> Ref: [full_website_qa_audit_and_proposal.pdf](file:///c:/Users/Edward/Desktop/CaseStudy/full_website_qa_audit_and_proposal.pdf) & [FULL_WEBSITE_QA_AUDIT_AND_PROPOSAL.md](./FULL_WEBSITE_QA_AUDIT_AND_PROPOSAL.md)

### Phase 32.1: P0/P1 Connectivity Resilience, Map Merging & Dynamic URL (COMPLETED)
- [x] **32.1.1 (QA-01: Resilient Offline Banner Gate)**:
  - In `connectivity.service.ts`, implemented consecutive error counter (`consecutiveErrors`, threshold $\ge 2$) and `reportGatewayError()` before setting `isHostOffline = true`.
  - In `auth.interceptor.ts`, integrated `reportGatewayError()` and asynchronous background `checkHostHealth()` reconciliation on gateway/offline errors without interrupting traveler UX.
- [x] **32.1.2 (QA-02: Viewport Bounding-Box POI Dataset Merging)**:
  - In `place.service.ts:searchPlaces()`, added `mergePlacesIntoCache()` merging live bounded API responses with in-memory `osmPlacesCache` by ID rather than replacing the complete 2,673-POI catalog.
  - In `map.page.ts:loadPlaces()`, added `allLoadedPlaces` master collection merging live bounded places into memory on pan/zoom, preserving all marker cluster pins across Nueva Ecija.
- [x] **32.1.3 (QA-08: Dynamic activeApiBaseUrl in HTTP Services & Interceptors)**:
  - In `connectivity.service.ts`, added dynamic getter `activeApiBaseUrl` reading `localStorage.getItem('ne_custom_api_url')` with secure protocol validation (`isValidApiUrl`) and fallback to `environment.apiBaseUrl`.
  - In `place.service.ts`, `itinerary.service.ts`, `auth.service.ts`, `auth.interceptor.ts`, and `place-detail-sheet.component.ts`, replaced static `environment.apiBaseUrl` with dynamic `activeApiBaseUrl`.

### Phase 32.2: P2 UI Polish, Global Settings & Lifecycle Cleanup (COMPLETED)
- [x] **32.2.1 (QA-14C: Restore ne_theme_mode on App Boot & ne_default_budget in Wizards)**:
  - In `app.component.ts:ngOnInit()`, hydrated user dark mode preference on initial app startup from `localStorage.getItem('ne_theme_mode')`.
  - In `suggested-wizard.page.ts` and `custom-builder.page.ts`, initialized `daily_budget` form control dynamically from `Number(localStorage.getItem('ne_default_budget')) || 3000`.
- [x] **32.2.2 (QA-14B: Timezone-Safe Date Incrementation in Itinerary Detail)**:
  - In `itinerary-detail.page.ts:addDay()`, replaced UTC `new Date(lastDate).toISOString().split('T')[0]` with `toLocalIsoDate(addDaysLocal(parseLocalIsoDate(lastDate), 1))`.
- [x] **32.2.3 (QA-14A: Teardown Legacy previewMap Lifecycle in ItineraryDetailPage)**:
  - In `itinerary-detail.page.ts`, removed legacy `previewMap`, `previewPolylineLayer`, `previewStopsLayer`, `initPreviewMap()`, `updatePreviewMap()`, and `previewMapElementRef` to eliminate redundant DOM resize timers.
- [x] **32.2.4 (QA-09: Remove Duplicate Toast on Forgot Password Modal)**:
  - In `login.page.ts:onForgotPassword()`, removed redundant warning toast when opening the password recovery modal, allowing the modal to cleanly display account recovery instructions.
- [x] **32.2.5 (QA-10: Adopt Shared PlaceDetailSheet on Home Tab)**:
  - In `home.page.html`, replaced legacy inline modal markup with shared `<app-place-detail-sheet [place]="selectedPlace">`, wiring `onStartTripFromSheet` and `onAddToCustomTripFromSheet`.
- [x] **32.2.6 (QA-11: Public OSRM & Overpass Routing Resilience)**:
  - Verified and guarded `fetchOsrmRoute()` with immediate geodesic polyline fallback and backend caching via `geospatial_cache`.

---

## Phase 33: Exhaustive QA/QC Audit Assessment & Production Polish
> Ref: [itinerary_app_exhaustive_qa_qc_report.pdf](file:///c:/Users/Edward/Desktop/CaseStudy/itinerary_app_exhaustive_qa_qc_report.pdf)
> Audit Baseline: Commit `81fcc8d7` (evaluated 75 test cases across 12 modules; 56 Passed, 14 Defects, 5 Blocked/Deferred).
> Cross-Reference: 12 of the 14 reported defects (`BUG-01` to `BUG-10`, `BUG-12`, and `BUG-13`) were resolved and verified in Phase 30, 31, and 32. Phase 33 tracks the audit verification matrix, addresses remaining open defects (`BUG-14`), and stages production cloud deployment (`BUG-11`).

### Phase 33.1: Audit Verification & Regression Matrix (RESOLVED & VERIFIED)
- [x] **33.1.1 (BUG-01 / TASK-01 - MOD-10 / TC-067: Offline Circuit Breaker & Exponential Backoff)**:
  - Addressed in Phase 32.1 (`32.1.1`).
  - Added consecutive error counter (`consecutiveErrors >= 2`) and async `checkHostHealth()` reconciliation in `connectivity.service.ts` and `auth.interceptor.ts`.
  - Eliminates infinite retry toast/banner loops when the backend host is offline.
- [x] **33.1.2 (BUG-02 / TASK-02 - MOD-05 / TC-032 & TC-034: Destination Autocomplete & Responsive Wrapped Chips)**:
  - Addressed in Phase 31.1 (`31.1.1` & `31.1.2`).
  - Implemented `<app-destination-autocomplete>` combobox indexing all 32 Nueva Ecija LGUs and landmarks with Unicode diacritic stripping.
  - Replaced clipped single-row horizontal scroll in `suggested-wizard.page.scss` with responsive wrapped pill grid (`flex-wrap: wrap`) and regional modal.
- [x] **33.1.3 (BUG-03 / TASK-03 - MOD-05 / TC-036 & TC-038: Sequential Time Window Scheduling & Overnight Lodging Order)**:
  - Addressed in Phase 31.2 (`31.2.2`).
  - Replaced hardcoded static `10:00 AM - 12:00 PM` slots with dynamic rolling time windows (`09:30 AM – 11:30 AM`, `12:00 PM – 01:30 PM`, `03:00 PM – 05:00 PM`) calculating transit buffers.
  - Fixed backwards overnight lodging sequencing in `isOvernightItem()` to ensure accommodations are scheduled at the end of the day.
- [x] **33.1.4 (BUG-04 / TASK-04 - MOD-05 / TC-035 & TC-037: Canonical Preference Mapping, Smart Dining & Venue Deduplication)**:
  - Addressed in Phase 31.2 (`31.2.1`, `31.2.3`, `31.2.4`).
  - Replaced broken string matching with canonical `PREFERENCE_CATEGORY_MAP` resolving user preferences to backend categories.
  - Added Smart Dining toggle for midday lunch spots (`12:00 PM – 01:30 PM`).
  - Implemented `normalizeVenueName()` and cross-day coordinate proximity checks (<200m) preventing duplicate stops across days.
- [x] **33.1.5 (BUG-05 & BUG-06 / TASK-05 - MOD-06 / TC-042 & TC-043: Custom Builder Full-Catalog Ingestion & Step-1 Preference Tab Sync)**:
  - Addressed in Phase 31.3 (`31.3.1`).
  - Replaced 17-place restricted browse pool in `custom-builder.page.ts` with `searchPlaces({ municipality_name: dest, limit: 100 })` querying all 2,673 POIs.
  - Corrected category mapping in `proceedToBuilder()` and added `✨ Recommended for You` tab combining selected preferences.
- [x] **33.1.6 (BUG-07 & BUG-08 / TASK-06 - MOD-09 / TC-063 & TC-064: App-Boot Theme Hydration & Default Budget Preference Binding)**:
  - Addressed in Phase 32.2 (`32.2.1`).
  - Hydrated `ne_theme_mode` dark mode in `app.component.ts:ngOnInit()` on app startup.
  - Hydrated `ne_default_budget` dynamically into `daily_budget` form controls in `suggested-wizard.page.ts` and `custom-builder.page.ts`.
- [x] **33.1.7 (BUG-09 / TASK-08 - MOD-04 / TC-024 & TC-025: Additive POI Bounding-Box Cache Merging on Map Pan/Zoom)**:
  - Addressed in Phase 32.1 (`32.1.2`).
  - Implemented `mergePlacesIntoCache()` in `place.service.ts` and `allLoadedPlaces` master collection in `map.page.ts`.
  - Merges live bounded API query results with existing in-memory places by ID without purging provincial markers.
- [x] **33.1.8 (BUG-10 / TASK-09 - MOD-07 / TC-050: Dynamic Itinerary Subtitle Counter & Place Detail Sheet Adoption)**:
  - Addressed in Phase 32.2 (`32.2.5`) and verified in `itinerary-detail.page.ts`.
  - Replaced hardcoded "Estimated activities" with dynamic `getItinerarySubtitle()` calculating total stops and day counts.
  - Unified Home tab modal with `<app-place-detail-sheet>`.
- [x] **33.1.9 (BUG-12 / TASK-10 - MOD-03 / TC-017: Card Width Token Standardization & Responsive Clamp)**:
  - Addressed in Phase 30/31 (`home.page.scss`).
  - Increased popular destination card `min-width` from cramped 120px to 160px with `clamp()` responsiveness.
- [x] **33.1.10 (BUG-13 / TASK-11 - MOD-11 / TC-071 & TC-073: Asset Pruning, .VSCodeCounter Exclusion & Build Budgets)**:
  - Addressed in Phase 32.
  - Pruned unused assets down to 21 active production image assets; excluded `.VSCodeCounter/` via `.gitignore`.
  - Verified production build budgets (<10kB per component style).

### Phase 33.2: Open Actionable Remediation (TASK-12 / BUG-14 & TASK-07 / BUG-11)
- [x] **33.2.1 (BUG-14 / TASK-12 - MOD-12 / TC-074: Production SEO Meta & Open Graph Sharing Tags)**:
  - In `Project/src/index.html`:
    - Replaced generic `<title>Ionic App</title>` with `<title>Nueva Ecija Travel Itinerary | Trip mo, trip ko</title>`.
    - Added meta description: `"Discover Nueva Ecija destinations, plan budget-aware multi-day itineraries, explore 2,673 local attractions, and navigate provincial transit."`.
    - Added Open Graph tags: `og:title`, `og:description`, `og:image`, `og:url`, `og:type`.
    - Added Twitter Card tags: `twitter:card`, `twitter:title`, `twitter:description`, `twitter:image`.
    - Set mobile status bar `theme-color` to brand `#0084ff`.
    - Added inline pre-boot theme hydration script to prevent flash of unstyled theme on startup.
- [x] **33.2.2 (BUG-14 / TASK-12 - MOD-12 / TC-075: Route Alias Redirect /tabs/saved -> /tabs/history)**:
  - In `Project/src/app/tabs/tabs.routes.ts`:
    - Added `{ path: 'saved', redirectTo: 'history', pathMatch: 'full' }` alias route to gracefully handle legacy bookmarks, external deep links, and user expectations.
  - In `Project/src/app/app.routes.ts`:
    - Added `{ path: 'saved', redirectTo: '/tabs/history', pathMatch: 'full' }` top-level redirect.
  - Created automated regression test in `Project/src/app/tabs/tabs.routes.spec.ts` (3 tests passing).
- [x] **33.2.3 (Quality Gate Verification & Regression Checks)**:
  - Executed Vitest unit test suite (`npm --prefix Project run test:unit`): **29/29 suites, 296/296 tests passing [100%]**.
  - Executed TypeScript strict typechecks (`npm --prefix Project run typecheck:e2e`): **Exit code 0**.
  - Executed ESLint formatting check on modified files: **Exit code 0, 0 errors, 0 warnings**.
  - Executed production Angular build (`npm --prefix Project run build`): **Exit code 0, 0 budget overruns**.
  - Executed Capacitor Android asset synchronization (`npx cap sync android`): **Exit code 0**.
- [x] **33.2.4 (BUG-11 / TASK-07 - MOD-02 / TC-007: Cloud Backend Deployment Roadmap)**:
  - Mitigated via Cloudflare Worker proxy (`https://ne-itinerary-api.edselrenz0.workers.dev/api/v1`) in `environment.prod.ts` and `environment.example.ts`.
  - Added fail-fast Pydantic JWT secret validation in `backend/app/core/config.py` rejecting default keys when `APP_ENV != 'development'`.
  - Created multi-stage production container `backend/Dockerfile` with healthcheck endpoint and slim runtime.
  - Created `docker-compose.prod.yml` configuring production PostgreSQL 16 and FastAPI container orchestration.

---

## Phase 34: Figma-Aligned Profile Tab Implementation (`Travel Itinerary App.fig`)
- [x] **34.1 (Figma Design Extraction & Design System Alignment)**:
  - Decompressed and parsed `Travel Itinerary App.fig` Kiwi nodes, typography, color palettes, and frame hierarchies.
  - Mapped frames: `Profile`, `Edit Profile`, `Settings`, `Help & Support`, `About`, and `Log Out Confirmation`.
  - Aligned with `/anti-generic-frontend-design`: deliberate styling, no AI cliches, WCAG 2.2 AA contrast, 44px touch targets.
- [x] **34.2 (High-Fidelity Profile Main Screen & Navigation Architecture)**:
  - User identity card: Circular avatar (support photo URL & initials), traveler full name, username/email, verified badge, "Edit Profile" pill button.
  - 5 structured menu items matching Figma:
    1. **Favorites**: "Your favorite places, all saved in one place." with heart icon -> `/tabs/history`.
    2. **Settings**: "Manage your account and customize your app experience." with gear icon -> Settings subwindow.
    3. **Help & Support**: "Get assistance and find answers to common questions." with help icon -> Help & Support subwindow.
    4. **About**: "Version 1.0.0." with info icon -> About subwindow.
    5. **Log Out**: "Sign out of your account." with red exit icon -> Figma-styled Log Out modal.
  - Guest traveler mode: clear onboarding banner, local unsynced trip migration trigger, accessible preferences.
- [x] **34.3 (Figma-Aligned Edit Profile Sub-Window Modal)**:
  - Modal with back button, title "Edit Profile".
  - Circular avatar with camera overlay badge (`andrsrxn:camera`) and "Change Photo" action.
  - Form fields matching Figma: First Name, Middle Initial (if applicable), Last Name, Username, Email Address, Phone Number, Birthday, Gender, and Change Password section.
  - Reactive form validation and "Save Changes" primary action button with loading spinner.
- [x] **34.4 (Figma-Aligned Settings Sub-Window Modal)**:
  - Account Information summary.
  - Display & Appearance: Light/Dark theme switch with immediate DOM hydration.
  - Language selector: English / Filipino (Tagalog).
  - Push Notifications toggle switch.
  - Trip Planning Defaults: Daily budget preset chips (₱1,500 / ₱2,500 / ₱3,000 / ₱5,000).
  - Connection & Cloud Sync status with live indicator.
  - Device Storage: Clear local cache ("Free up storage space") action.
- [x] **34.5 (Help & Support and About Sub-Window Modals)**:
  - Help & Support: Nueva Ecija travel FAQs, provincial transit guidelines, emergency hotlines (PDRRMO, PNP, Provincial Tourism).
  - About: Version 1.0.0, Nueva Ecija Provincial Travel companion mission, OpenStreetMap & OSRM credits.
- [x] **34.6 (Figma-Aligned Log Out Confirmation Dialog)**:
  - Modal with red exit icon, title "Log Out?", description "You will be signed out of your account. You can always log back in anytime.", Cancel and Log Out buttons.
  - Safety check for unsynced local guest trips before logout.
- [x] **34.7 (Automated Test Suite Expansion)**:
  - Updated `profile.page.spec.ts` with comprehensive unit tests for all menu items, modals, forms, and workflows (17 tests passing).
- [x] **34.8 (Quality Gate Verification & Documentation Sync)**:
  - Vitest unit tests: **304/304 passing [100%] across 29 test files**.
  - Backend integration tests: **21/21 passing [100%] across 5 test suites**.
  - TypeScript strict typecheck: **Exit code 0**.
  - ESLint static analysis: **Exit code 0, 0 errors, 0 warnings**.
  - Angular production build: **Exit code 0, 0 budget errors**.
  - Capacitor Android sync: **Exit code 0 (6 plugins synced)**.

---

## Phase 35: Figma-Aligned Profile Tab Visual Alignment & After Log Out Screen (Travel Itinerary App.fig)
- [x] **35.1 (Exact High-Resolution Asset Extraction)**:
  - Extracted authentic profile avatar photo pattranite_avatar.jpg (Pattranite selfie taking photo in mirror) from Kiwi chunk 1 binary canvas (Travel Itinerary App.fig).
  - Extracted authentic 'After Log Out' skyscraper photo in organic blob logout_skyscrapers_blob.png.
  - Extracted authentic 'After Log Out' bottom cityscape skyline silhouette logout_cityscape_silhouette.png.
- [x] **35.2 (Figma Screen 1 - Profile Main Screen Visual Alignment)**:
  - Header: Left-aligned bold title Profile (ont-size: 26px, bold), no right gear icon in toolbar.
  - Identity row: Horizontal arrangement featuring circular avatar photo on left (76px x 76px, circular clip, subtle border) with Name (Pattranite Limpatiyakorn), handle/email (@loverrukk@gmail.com), and outline pill button Edit Profile (order: 1.5px solid #0088ff, transparent bg, rounded pill) on the right.
  - Profile Menu Card: Single rounded white container card (order-radius: 20px, order: 1px solid #e2e8f0, soft shadow) enclosing 5 items with thin horizontal dividers:
    1. **Settings**: Blue gear icon (#0088ff), title Settings, subtitle Manage your account and customize your app experience. Click opens Settings subwindow.
    2. **Favorites**: Blue filled heart icon (#0088ff), title Favorites, subtitle Your favorite places, all saved in one place. Find them whenever you're ready to explore. Click navigates to /tabs/history.
    3. **Help & Support**: Blue filled question mark circle icon (#0088ff), title Help & Support, subtitle Get assistance and find answers to common questions. Click opens Help & Support subwindow.
    4. **About**: Blue filled info circle icon (#0088ff), title About, subtitle Version 1.0.0. Click opens About subwindow.
    5. **Log Out**: Red exit door icon (#ff3b30), title Log Out (bold red text), subtitle Sign out of your account. Click opens Log Out Confirmation modal.
  - Removed right-chevron arrows to match the Figma screenshots with 100% precision.
- [x] **35.3 (Figma Screen 1 - Settings Sub-Window Alignment)**:
  - Header: Blue back arrow ← (#0088ff) + bold Settings.
  - Single rounded white card containing 6 settings rows with subtle dividers:
    1. **Account Information**: Blue person outline icon. Click opens Edit Profile.
    2. **Notifications**: Blue bell icon with iOS-style blue toggle switch.
    3. **Privacy & Security**: Blue padlock icon. Click displays encryption & security status alert.
    4. **Language**: Blue globe icon with 'English' text on right. Click toggles / switches language.
    5. **App Appearance**: Blue moon/sun icon with 'Light' text on right. Click toggles dark/light mode with instant DOM hydration.
    6. **Clear Cache**: Blue trash can icon with bold title Clear Cache and subtitle Free up storage space.
- [x] **35.4 (Figma Screen 1 - Log Out Confirmation Modal Alignment)**:
  - Centered floating modal card (order-radius: 28px, white background, soft shadow).
  - Subtle top triple-dot indicator handle (...).
  - Prominent blue exit door icon (#0088ff, 52px).
  - Title: Log Out? (ont-size: 20px, bold).
  - Subtitle: You will be signed out of your account. You can always log back in anytime.
  - Two stacked full-width solid vibrant blue buttons:
    - Primary: Log Out (background #0088ff, white text, order-radius: 16px).
    - Secondary: Cancel (background #0088ff, white text, order-radius: 16px).
- [x] **35.5 (Figma Screen 2 - Edit Profile Sub-Window Alignment)**:
  - Header: Blue back arrow ← (#0088ff) + bold Edit Profile.
  - Centered circular avatar photo (96px x 96px) with translucent camera overlay badge and pill button Change Photo (order: 1.5px solid #0088ff).
  - Form fields in exact Figma visual hierarchy and vertical order:
    1. First Name: Input 'Pattranite'
    2. Middle Initial (if applicable): Input 'N/A'
    3. Last Name: Input 'Limpatayakorn'
    4. Birthday: Input 'May 23, 2000'
    5. Gender: Input 'Female'
    6. Email Address: Readonly input '@loverrukk@gmail.com'
    7. Phone Number: Input '+66 81 234 5678'
  - Full-width primary button: Save Changes (solid vibrant blue #0088ff, white text, order-radius: 16px).
- [x] **35.6 (Figma Screen 3 - After Log Out Screen Implementation)**:
  - Integrated into WelcomePage (eatures/auth/welcome/):
    - Top: Slanted blue airplane icon (#0088ff) + bold black title Trip mo, trip ko.
    - Organic smooth blob frame (order-radius: 40% 60% 70% 30% / 45% 50% 50% 55%, cyan/blue border & shadow) enclosing skyscraper photography (ssets/images/logout_skyscrapers_blob.png).
    - Heading: You’re now logged out (bold, 22px).
    - Subtitle: Your account has been signed out. Explore as guest or log in again to access your saved trips and preferences.
    - Two stacked solid blue buttons: Continue as Guest and Log In (both solid #0088ff, white text, pill radius).
    - Bottom: Cityscape skyline illustration (ssets/images/logout_cityscape_silhouette.png).
- [x] **35.7 (Automated Testing & Full Verification Suite)**:
  - Vitest Unit Tests: **310/310 passing [100%] across 30 test files** (18 tests in profile.page.spec.ts + 5 tests in welcome.page.spec.ts).
  - TypeScript strict typecheck (	sconfig.e2e.json): **Exit code 0**.
  - Production Angular build (
g build): **Exit code 0** (component styles strictly under 16 kB budget).
  - Capacitor Android sync (
px cap sync android): **Exit code 0 (6 plugins synchronized)**.

---

## Phase 36: Comprehensive QA/QC Audit Remediation (QA-REPORT/ Release Gate)
- [x] **36.1 (Fix QA-BUG-CRIT-01 - P0 Critical: Permanent Splash Screen Freeze)**:
  - Injected `ChangeDetectorRef` in `Project/src/app/app.component.ts`.
  - Invoked `this.cdr.detectChanges()` inside the 500ms fade-out callback in `dismissSplash()` to guarantee DOM unmounting on first-time visits and clean sessions.
- [x] **36.2 (Fix QA-ARCH-DEF-01 - P0 Critical: Zone.js & Async Change Detection)**:
  - Configured `provideZoneChangeDetection({ eventCoalescing: true })` in `Project/src/main.ts`.
  - Injected `ChangeDetectorRef` in `Project/src/app/tabs/home/home.page.ts` and added explicit `this.cdr.markForCheck()` on debounced search updates and featured place stream responses.
- [x] **36.3 (Fix QA-UI-DEF-01 - P1 High: Log Out Modal Pointer Interception)**:
  - In `Project/src/app/tabs/profile/profile.page.scss`, removed `display: flex; align-items: center; justify-content: center;` from `.figma-logout-modal` host selector.
  - Set `--height: auto;` so Ionic's `.overlay-hidden { display: none; }` unmounts the closed modal element and allows clicks to reach the underlying Log Out row.
- [x] **36.4 (Fix QA-AUDIT-DEF-01 - P2 Medium: Acceptance Gate Check #15 Alignment)**:
  - Updated `scripts/verify_acceptance_gate.py` Check #15 to inspect `Project/src/app/shared/components/place-detail-sheet/place-detail-sheet.component.ts` and verify canonical fallback label `'Admission: Check on arrival'`.
  - Verified acceptance gate reaches **24/24 checks passed (100.0%)**.
- [x] **36.5 (Fix QA-LINT-DEF-01 - P2 Medium: Automated Lint & Code Quality Remediation)**:
  - Inspected lint rules; guarded runtime dependency injection tokens against `import type` erasure (preventing Angular NG2003 runtime compiler errors).
  - Maintained zero lint regressions and verified strict TypeScript compilation.
- [x] **36.6 (Verification & Production Readiness Gate)**:
  - Vitest Unit Tests: **310/310 passed across 30 test files (100%)**.
  - Acceptance Gate: **24/24 checks passed (100.0%)**.
  - Production Angular Build (`ng build`): **Exit code 0** (0 budget errors, <16 kB component styles).
  - Capacitor Android Sync (`npx cap sync android`): **Exit code 0** (6 plugins synchronized in 0.627s).
- [x] **36.7 (GitHub Pages CI/CD Workflow Fix)**:
  - Decoupled single-job `build-and-deploy` in `.github/workflows/deploy.yml` into official GitHub two-job pipeline (`build` and `deploy` with `needs: build`).
  - Fixed artifact indexing race condition (`Found 0 artifact(s)` / `No artifacts named "github-pages" were found`).
  - Set `concurrency.cancel-in-progress: false` to protect in-flight Pages deployments.
  - Upgraded Pages configuration to `actions/configure-pages@v5` and stabilized Node.js runtime to `node-version: 22`.
- [x] **36.8 (GitHub Pages SPA Hard Refresh Ctrl+F5 Support)**:
  - Enabled `withHashLocation()` in `Project/src/main.ts` so routes use hash fragments immune to server-side 404s.
  - Added `Project/src/404.html` and history receiver in `Project/src/index.html` via standard `spa-github-pages` redirect protocol.
- [x] **36.9 (Profile Tab Interactivity & Guest State Remediation)**:
  - Relocated all 5 `<ion-modal>` overlay components outside `<ion-content>` and wrapped in `@if` conditional rendering so closed modals never exist in the DOM or intercept pointer clicks.
  - Injected `ChangeDetectorRef` in `ProfilePage` with `markForCheck()` on all modal triggers and dismissals.
  - Implemented authentic Guest Mode profile state (neutral avatar, "Guest Explorer", "Browsing in Guest Mode", "Log In / Sign Up" button, and "Exit Guest Mode" row).
- [x] **36.10 (Fix Blank White Screen & NG0908 Zone.js Runtime Error)**:
  - Replaced `provideZoneChangeDetection` with native `provideZonelessChangeDetection()` in `Project/src/main.ts`.
  - Resolved `RuntimeError: NG0908: In this configuration Angular requires Zone.js` which caused the application to fail during `bootstrapApplication()` and render a blank white screen on `http://localhost:8100/` and GitHub Pages.
  - Verified application bootstrapping: `Current URL: http://localhost:8100/#/welcome`, full DOM tree hydrated with zero console errors.

---

## Phase 37: Profile Persona Pre-Set, Settings/Help Sub-Views, Logout Parity, Dark Mode Fix & Dedicated Favorites Tab
- [x] **37.1 (Authenticated Profile Pre-Set Persona)**:
  - Ensured logging in pre-populates traveler persona with Pattranite Limpatiyakorn (`assets/images/pattranite_avatar.jpg`, `Pattranite Limpatiyakorn`, `@loverrukk@gmail.com`).
  - Added seamless demo/offline login fallback in `AuthService.login()` with valid 30-day token generation so testers on GitHub Pages and local sessions log in directly to Pattranite's profile without local backend setup.
- [x] **37.2 (Settings, Help & Support, About In-Page Sub-Views Matching Image 1)**:
  - Transformed Settings, Help & Support, and About into in-page sub-views within `ProfilePage` (`viewMode: 'profile' | 'settings' | 'help' | 'about'`).
  - In Settings, rendered the exact single rounded card enclosing 6 rows with blue icons (`Account Information`, `Notifications` with iOS toggle, `Privacy & Security`, `Language`, `App Appearance`, `Clear Cache`), retaining the bottom tab bar visible matching Image 1 (`media_1794305628697_56ce48c5.png`).
  - In Help & Support and About, aligned to the same clean card-based design with blue back arrows and active bottom tab bar.
- [x] **37.3 (Before Log Out Modal & After Log Out Screen Alignment Matching Images 2 & 3)**:
  - In Before Log Out modal, implemented floating dialog with triple-dot handle, vibrant blue door exit SVG icon, bold "Log Out?", description, and stacked solid blue buttons matching Image 2 (`media_1794305642780_d5248c99.png`).
  - In After Log Out screen (`WelcomePage` with `loggedOut=true`), verified layout matching Image 3 (`media_1794305651445_190286a1.png`) with airplane logo, organic skyscraper photo blob mask, heading, stacked blue buttons, and cityscape skyline silhouette.
- [x] **37.4 (Dark Mode Color Inversion Bug Fix)**:
  - Eliminated the dark mode white-on-white bug across `Project/src/global.scss` and component stylesheets by establishing universal dark theme variables (`html.dark, body.dark`) with `--background: #0b1120 !important;`, card surfaces `#1e293b`, borders `#334155`, and high-contrast typography (`#f8fafc` headings, `#94a3b8` body/subtitles).
- [x] **37.5 (Dedicated Favorites Tab & Place Bookmarking)**:
  - Created `FavoritesService` managing persisted favorite destinations under `ne_favorite_places_v1`.
  - Added favorite heart toggle button to `PlaceDetailSheetComponent` allowing travelers to heart/unheart any venue.
  - Created `FavoritesPage` at `/tabs/favorites` with search, category filtering, venue cards, directions action, and empty state.
  - Added `Favorites` tab button in `tabs.page.html` with heart icon and wired Profile "Favorites" row to `/tabs/favorites`.
- [x] **37.6 (Verification & Test Suite Updates)**:
  - Vitest Unit Tests: **32/32 test suites passed, 321/321 unit tests passed (100%)**.
  - Production Angular Build (`ng build --base-href /Itinerary-App/`): **Exit code 0, 0 budget violations (all components < 16 kB)**.
  - 24-Point Acceptance Gate: **24/24 checks passed (100.0%)**.

---

## Phase 38: Edit Profile Screen Formatting, Photo Upload Fix & Blank Avatar Placeholder
- [x] **38.1 (Blank Avatar Placeholder for Signed-In Individuals)**:
  - Import and configure `Project/src/assets/images/default_avatar_placeholder.png` based on the user's uploaded neutral silhouette avatar (`media_1794313889456_46c51912.png`).
  - Set default avatar for signed-in individuals without uploaded photos to `assets/images/default_avatar_placeholder.png`, replacing hardcoded selfie placeholders.
- [x] **38.2 (Edit Profile In-Page Subview Alignment Matching Image 1)**:
  - Transition `Edit Profile` from an `<ion-modal>` into an in-page sub-view (`viewMode: 'edit'`) inside `ProfilePage`, retaining the visible bottom tab bar and matching Image 1 (`media_1794313719867_c04de25f.png`).
  - Render header `← Edit Profile` with blue back arrow navigating back to `viewMode = 'profile'`.
  - Render centered circular avatar with camera overlay, `Change Photo` blue outlined pill button, 7 form fields in exact sequence, and solid blue `Save Changes` pill button.
- [x] **38.3 (Profile Picture Upload & Preview Fix)**:
  - Resolve asynchronous `FileReader.onload` change detection issue under `provideZonelessChangeDetection()` by explicitly triggering `this.cdr.markForCheck()`.
  - Wire hidden file input with direct trigger on both the avatar circle and `Change Photo` button.
  - Maintain `editAvatarPreview` state and persist base64 data to `ne_profile_extra_<id>` upon saving.
- [x] **38.4 (Full Quality Gate Verification)**:
  - Vitest Unit Tests: **32/32 suites, 322/322 unit tests passed (100%)**.
  - Angular Production Build (`ng build --base-href /Itinerary-App/`): **0 errors, <16 kB component styles**.
  - Capacitor Android Sync (`npx cap sync android`): **6 plugins synced in 0.548s**.

---

## Phase 39: Favorites Profile-Only Migration (Bottom Navigation De-Clutter)
- [x] **39.1 (Remove Favorites from Bottom Tab Bar)**:
  - Removed the `<ion-tab-button tab="favorites">` from `Project/src/app/tabs/tabs.page.html`, restoring the bottom tab bar to exactly the 4 main canonical tabs (`Home`, `Map`, `Saved`, `Profile`).
  - Redirected `/tabs/favorites` in `Project/src/app/tabs/tabs.routes.ts` and `/favorites` in `Project/src/app/app.routes.ts` to `profile`.
- [x] **39.2 (Integrate Favorites Sub-View in Profile Tab)**:
  - Expanded `viewMode` in `ProfilePage` (`Project/src/app/tabs/profile/profile.page.ts`) to include `'favorites'`.
  - Connected `FavoritesService` and `PlaceService` in `ProfilePage`, loading bookmarked places reactive stream and supporting live search filtering and category chips.
  - Implemented in-page sub-view `@if (viewMode === 'favorites')` in `Project/src/app/tabs/profile/profile.page.html` with `← Favorites` header, search bar, category chips, card list with heart toggle, directions action, and empty state.
  - Retained bottom tab bar visible on Profile tab without cluttering the 4 main bottom tabs.
- [x] **39.3 (Quality Gate Verification & Regression Prevention)**:
  - Updated `profile.page.spec.ts` to verify in-page favorites view mode navigation and actions.
  - Vitest unit tests: **32/32 test suites passed, 322/322 tests passed (100.0%) in 21.91s**.
  - Angular production build (`ng build --base-href /Itinerary-App/`): **Exit code 0, 0 budget violations (all components < 16 kB)**.
  - Capacitor Android sync (`npx cap sync android`): **Exit code 0, 6 plugins synchronized in 0.485s**.

---

## Phase 40: Critical Remediation Suite (System Review Audit Findings)
- [x] **40.1 (Finding 11: Fix Zoneless Change Detection Freeze in Suggested Wizard)**:
  - In `suggested-wizard.page.ts`, injected `ChangeDetectorRef` and invoked `this.cdr.markForCheck()` across `suggestItinerary` next/error handlers, `saveItinerary` next/error handlers, `selectDay`, `refreshNearbyPlaces`, `setDestination`, `setBudgetPreset`, `togglePreference`, `openDatePicker`, `closeDatePicker`, `setTravelMode`, `setMinRating`, `openStopDetail`, and `closeStopDetail`. Generated itineraries render instantly upon calculation without requiring any artificial screen taps.
- [x] **40.2 (Finding 1: Prevent Silent Demo Login Usurpation & Provide Explicit Demo Action)**:
  - In `auth.service.ts`, removed automatic silent fallback to `loverrukk@gmail.com` on offline/502/504 errors so real login attempts report honest connectivity failures.
  - Added explicit `loginDemo(): Observable<AuthResponse>` to `AuthService` and helper `isDemoUser()`.
  - In `login.page.html` and `login.page.ts`, added a dedicated, clearly styled `[Explore Demo Account (Pattranite Persona)]` button triggering explicit demo login with toast notification.
- [x] **40.3 (Finding 2: Eliminate Foreign Persona Defaults on Real Accounts & Form Wipe Bug)**:
  - In `profile.page.ts`, ensured non-demo registered users (`currentUser.id !== 'usr_pattranite_demo_01'`) retain their real names and start with blank profile extra fields and Philippine placeholder hints (`+63 9XX XXX XXXX`).
  - Fixed the bug in `toggleCurrentPasswordVisibility()` and `toggleNewPasswordVisibility()`: replaced `this.openEditProfile()` with `this.cdr.markForCheck()` so toggling password visibility never wipes user input.
- [x] **40.4 (Finding 7: Prevent Active Map Navigation Cancellation on Tab Tap)**:
  - In `tabs.page.ts:onMapTabClicked()`, inspected `this.router.url`; if `followRoute=true` or `routeItineraryId` is active, preserved active route navigation parameters without wiping query parameters.
- [x] **40.5 (Finding 6 & Finding 4: Day-Trip Lodging Exclusion & Questionnaire Pacing in Generator)**:
  - In `backend/app/algorithms/itinerary_generator.py` and `Project/src/app/core/services/itinerary.service.ts`, excluded overnight hotel/resort accommodations on 1-day single-day getaways (`totalDays === 1`).
  - In `itinerary.service.ts:generateOfflineSuggestedItinerary()`, read `request.pacing` and dynamically scaled daily stops (`relaxed` = 2, `moderate` = 3, `fast` = 4).
- [x] **40.6 (Finding 8: Differentiate Free Venues (₱0) from Unpriced Venues)**:
  - In `itinerary-detail.page.ts`, ensured stops with `min === 0 && max === 0` render `'Free Admission'` badge instead of `'₱0'` or `'Price not listed'`.
- [x] **40.7 (Finding 3: Streamline Continue as Guest After Logout)**:
  - In `welcome.page.ts:goToGuest()`, if `isAfterLogout` is true, immediately invoked `authService.continueAsGuest()` and navigated directly to `/tabs/home`.
- [x] **40.8 (Playwright E2E Hash Routing Alignment)**:
  - In `Project/e2e/app.spec.ts`, aligned direct navigation URLs with hash location routing (`/#/tabs/map`, `/#/tabs/home`, `/#/welcome`, `/#/custom-builder`).
- [x] **40.9 (Verification & Quality Gates)**:
  - Vitest Unit Tests: **32/32 test suites passed, 327/327 tests passed (100.0%) in 47.64s**.
  - Backend Tests: Generator bounding box & chronological tests passed 100%.
  - Production Angular Build (`ng build --base-href /Itinerary-App/`): **Exit code 0, 0 budget violations (all components < 16 kB)**.
  - Capacitor Android Sync: **Exit code 0 (web directory synced)**.

---

## Phase 41: Post-Audit Polish & Zoneless Auth Reactivity (FIX-01C, Finding 5 & Finding 10)
- [x] **41.1 (Fix FIX-01C: Zoneless Reactivity in LoginPage)**:
  - In `Project/src/app/features/auth/login/login.page.ts`, injected `ChangeDetectorRef` (`private cdr = inject(ChangeDetectorRef)`).
  - Added explicit `this.cdr.markForCheck()` inside `onSubmit()` (`error` callback for 401/0/502/504 and `next` callback), `onDemoLogin()` error callback, `togglePassword()`, `submitRecoveryRequest()`, and modal toggle handlers.
  - Verified `<div class="error-banner">` renders immediately upon 401 Unauthorized or network failure without requiring external DOM interactions.
- [x] **41.2 (Fix Zoneless Reactivity in SignupPage)**:
  - In `Project/src/app/features/auth/signup/signup.page.ts`, injected `ChangeDetectorRef`.
  - Added explicit `this.cdr.markForCheck()` inside `onSubmit()` (`error` callback and `next` callback), `togglePassword()`, and `toggleConfirmPassword()`.
  - Verified registration error banners render immediately upon rejection.
- [x] **41.3 (Fix Finding 5: Balanced Category Browsing in Custom Builder)**:
  - In `Project/src/app/features/itinerary/custom-builder/custom-builder.page.ts`, prevented Step 1 preference selection from hiding essential dining, accommodation, and attractions in Step 2 browse modal.
  - Maintained balanced "All" view by default showing top highlights across all core categories, while populating "✨ Recommended for You" whenever preferences are selected.
- [x] **41.4 (Fix Finding 10: Copywriting & Typographic Polish)**:
  - Verified all customer-facing copywriting across `welcome.page.html` ("personalized itineraries") and `guest.page.html` ("Your trips are saved locally on this device") uses clean, professional English copy.
- [x] **41.5 (Full Verification & Quality Gates)**:
  - Added error banner reactivity unit tests in `login.page.spec.ts` and `signup.page.spec.ts`.
  - Vitest Unit Tests: **32/32 test suites passed, 329/329 tests passed (100.0%) in 23.74s**.
  - Angular Production Build (`ng build --base-href /Itinerary-App/`): **Exit code 0, 0 budget violations (all components < 16 kB)**.
  - Capacitor Android Sync: **Exit code 0 (web distribution directory synced)**.
  - Updated `docs/DEVELOPMENT_PLAN.md`, `docs/CHANGELOG.md`, and `docs/DEVELOPMENT_LOG.md`.

---

## Phase 42: Zoneless Immediate Feedback & Change Detection Synchronization
- [x] **42.1 (Login Immediate Feedback on Invalid Password)**:
  - In `Project/src/app/features/auth/login/login.page.ts`, resolved zoneless change detection latency where `this.cdr.markForCheck()` only marked views as dirty but failed to trigger an immediate template refresh without external DOM click events.
  - Injected `ApplicationRef` alongside `ChangeDetectorRef` and implemented `updateUI()`, combining synchronous `this.cdr.detectChanges()` with `this.appRef.tick()`.
  - Verified `<div class="error-banner">` renders immediately upon invalid password or network error and re-enables the submit button with zero user interaction delay.
- [x] **42.2 (Suggested Wizard Immediate Itinerary Feedback)**:
  - In `Project/src/app/features/itinerary/suggested-wizard/suggested-wizard.page.ts`, resolved freeze where the "Find Itinerary" button remained in an infinite circling spinner state (`isGenerating = true`) after recommendation clustering completed.
  - Injected `ApplicationRef` and implemented `updateUI()`, invoking immediate synchronous change detection upon `suggestItinerary` next/error resolution and `saveItinerary` handlers.
  - Verified the button spinner clears automatically and the view immediately transitions into the generated itinerary view without requiring any artificial screen clicks.
- [x] **42.3 (Auth & Custom Builder Zoneless Synchronization)**:
  - In `Project/src/app/features/auth/signup/signup.page.ts`, injected `ApplicationRef` and updated `onSubmit()` to invoke `updateUI()`.
  - In `Project/src/app/features/itinerary/custom-builder/custom-builder.page.ts`, injected `ChangeDetectorRef` and `ApplicationRef` and updated `saveItinerary()` to invoke `updateUI()`.
- [x] **42.4 (Automated Playwright & Quality Gates Verification)**:
  - Created automated Playwright verification script (`test_zoneless_reactivity.mjs`) testing both workflows against the production distribution bundle (`Project/www`):
    1. Login error banner feedback renders immediately upon submitting invalid credentials (no clicks needed).
    2. Suggested Wizard transitions automatically to the generated plan (no stuck circling spinner, no clicks needed).
  - All 4 Playwright reactivity tests passed (100.0%).
  - Vitest Unit Tests: **32/32 test suites passed, 329/329 tests passed (100.0%) in 23.92s**.
  - Production Angular Build (`ng build`): **Exit code 0, 0 budget violations (all components < 16 kB)**.

---

## Phase 43: System-Wide Loading States & Visual Feedback Remediation
- [x] **43.1 (Fix Infinite Loading Spinner in ItineraryDetailPage)**:
  - In `Project/src/app/features/itinerary/itinerary-detail/itinerary-detail.page.ts`, injected `ApplicationRef` alongside `ChangeDetectorRef` and implemented `updateUI()` (`this.cdr.detectChanges()` + `this.appRef.tick()`).
  - Invoked `this.updateUI()` inside `loadItinerary()` on both `next` and `error` paths when setting `this.isLoading = false`, ensuring direct route navigation (`/#/itinerary/:id`) dismisses the loading spinner immediately without requiring DOM interactions.
- [x] **43.2 (Fix Demo Account CTA Loading State in LoginPage)**:
  - In `Project/src/app/features/auth/login/login.page.ts`, introduced `isDemoLoading: boolean = false` state tracked during `onDemoLogin()`.
  - In `Project/src/app/features/auth/login/login.page.html`, updated `.demo-pill-btn` with an `@if (isDemoLoading)` block rendering `<ion-spinner name="crescent" class="demo-spinner"></ion-spinner> <span>Entering Demo Mode...</span>`.
  - Ensured `this.updateUI()` is invoked on start, success, and error so the loading indicator renders immediately.
- [x] **43.3 (Fix Account Recovery Submission Loading State in LoginPage)**:
  - In `Project/src/app/features/auth/login/login.page.ts`, introduced `isSubmittingRecovery: boolean = false` state tracked in `submitRecoveryRequest()`.
  - In `Project/src/app/features/auth/login/login.page.html`, bound `[disabled]="isSubmittingRecovery"` and rendered `<ion-spinner name="crescent" class="btn-spinner"></ion-spinner>` inside `.subwindow-save-btn`.
  - Ensured `this.updateUI()` is invoked on trigger and completion.
- [x] **43.4 (Fix Static Form During Suggested Wizard Generation)**:
  - In `Project/src/app/features/itinerary/suggested-wizard/suggested-wizard.page.html` and `suggested-wizard.page.scss`, added an overlay card (`.wizard-generating-scrim`) over the questionnaire when `isGenerating === true`.
  - Displayed crescent spinner with informative progress text ("Building Your Nueva Ecija Itinerary...", "Clustering destinations and optimizing route pacing...") guaranteeing immediate visual feedback on mobile viewports where the CTA button is below the fold.
- [x] **43.5 (Fix Success Toast Race Condition on Itinerary Save)**:
  - In `Project/src/app/features/itinerary/suggested-wizard/suggested-wizard.page.ts:acceptAndSave()`, introduced a graceful 350ms transition guard after `await toast.present()` before executing `this.router.navigate(['/tabs/home'])`.
  - Prevented view transition unmounting from obscuring the green confirmation toast.
- [x] **43.6 (Quality Gates Verification & E2E Testing)**:
  - Vitest Unit Tests: **32/32 suites passed, 330/330 tests passed (100.0%) in 36.92s**.
  - Production Angular build: **Exit code 0, 0 budget violations (all components < 16 kB)**.
  - Playwright automated verification: **4/4 checks passed (100.0%)** testing direct itinerary route, demo account loading, account recovery spinner, and wizard scrim.

