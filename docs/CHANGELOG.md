# Changelog

All notable changes to the Nueva Ecija Travel Itinerary project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.16.4] - 2026-11-03
### Removed
- **Server Connection Settings Dialog & Gear Button**:
  - In `Project/src/app/app.component.html`, `app.component.ts`, and `app.component.scss`:
    - Removed the Settings gear button (`banner-config-btn`) from the Offline Mode status banner.
    - Removed `openServerConfigAlert()` dialog and `showInvalidUrlToast()` from `AppComponent`.
    - Hardened the client interface so end users are never exposed to internal backend URLs or manual tunnel inputs.
    - Simplified `retryConnection()` to present a clean, user-friendly status toast when the backend is offline.
  - In `Project/src/app/app.component.spec.ts`:
    - Updated unit tests to verify clean Retry and Dismiss banner actions and offline status toast (121/121 passing).

---

## [0.16.3] - 2026-11-03
### Changed
- **Permanent Cloudflare Worker Production Activation**:
  - In `Project/src/environments/environment.prod.ts`:
    - Updated default production API base URL to permanent Cloudflare Worker reverse proxy: `https://ne-itinerary-api.edselrenz0.workers.dev/api/v1`.
    - Enables 100% zero-configuration permanent connectivity from GitHub Pages to developer laptop.
  - In `.env`:
    - Added user-configured `WORKER_SYNC_URL=https://ne-itinerary-api.edselrenz0.workers.dev` and `WORKER_SYNC_KEY`.
- **End-to-End Edge Verification**:
  - Verified edge health probe `https://ne-itinerary-api.edselrenz0.workers.dev/api/v1/health` returning `{"status":"ok"}`.
  - Verified edge places probe `https://ne-itinerary-api.edselrenz0.workers.dev/api/v1/places` returning live database records directly from developer laptop.

---

## [0.16.2] - 2026-11-03
### Changed
- **Default Production API Endpoint Update**:
  - In `Project/src/environments/environment.prod.ts`:
    - Updated default fallback API base URL from `https://anybody-cube-surprise.ngrok-free.dev/api/v1` to `https://incentive-fish-lung-observe.trycloudflare.com/api/v1`.
    - Eliminates initial `ERR_NAME_NOT_RESOLVED` offline failures on residential Philippine ISPs / Wi-Fi routers (e.g. Tenda/PLDT) that sinkhole `.dev` domains.
- **Snappy Health Check Timeout (`ConnectivityService`)**:
  - Added RxJS `timeout(5000)` operator to `ConnectivityService.checkHostHealth()` so failed DNS lookups fail fast within 5s instead of leaving the UI spinning indefinitely.
- **Automatic Reconnection Data Rehydration**:
  - In `Project/src/app/app.component.ts`:
    - Added automatic page rehydration (`window.location.reload()` after 800ms) upon successful server reconnection in `retryConnection()` and `openServerConfigAlert()` ("Save & Connect").
    - Guarantees that when server connectivity is restored, all components and services immediately fetch live backend data rather than displaying stale offline caches.

---

## [0.16.1] - 2026-11-03
### Added
- **Option 2: Cloudflare Worker Reverse Proxy Architecture**:
  - Created `cloudflare-worker/worker.js` with:
    - Dynamic CORS support for `https://edselrenz.github.io`, `localhost`, and `capacitor://localhost`.
    - Secure `POST /__sync_tunnel` admin endpoint authenticated via `X-Admin-Sync-Key` header.
    - `GET /__status` diagnostic endpoint returning worker health and active tunnel metadata.
    - Dual-tunnel failover proxy: routes incoming `/api/v1/*` requests to active Cloudflare Tunnel first, falling back to ngrok.
  - Created `cloudflare-worker/wrangler.toml` for declarative Wrangler CLI deployment.
  - Authored `cloudflare-worker/README.md` with a complete 2-minute web dashboard deployment walkthrough.
- **Automated Tunnel Publishing in `scripts/start_server.ps1`**:
  - Automatically loads `WORKER_SYNC_URL` and `WORKER_SYNC_KEY` from `.env`.
  - Sends an automated `POST` request to `/__sync_tunnel` upon tunnel startup, publishing the latest `$cfUrl` and `$ngrokUrl` to Cloudflare KV in 2 seconds.
  - Displays the permanent zero-touch Cloudflare Worker proxy URL in the console launch banner.
- **Frontend Hostname Security Expansion (`SEC-01`)**:
  - In `Project/src/environments/environment.prod.ts`, `environment.ts`, and `connectivity.service.ts`:
    - Added `*.workers.dev`, `*.onrender.com`, and `*.koyeb.app` to `isTrustedApiHostname()` and `isValidApiUrl()`.
  - In `Project/src/app/core/services/connectivity.service.spec.ts`:
    - Added unit test asserting that `*.workers.dev` URLs are recognized, validated, and normalized with `/api/v1`.
  - In `Project/src/app/app.component.ts`:
    - Updated connection settings alert message and placeholder to highlight `https://*.workers.dev`.
- **Environment & Architecture Documentation**:
  - Updated `.env.example` with `WORKER_SYNC_URL` and `WORKER_SYNC_KEY`.
  - Added Section 5 to `docs/SYSTEM_ARCHITECTURE.md` (Sequence diagram and edge routing data flow).
  - Added Section 5 to `docs/CONFIGURATION_GUIDE.md` (Worker deployment steps).

---

## [0.16.0] - 2026-11-03
### Added
- **Interactive Server Connection Manager (Offline Banner & Retry Experience)**:
  - In `Project/src/app/app.component.html`, `app.component.ts`, and `app.component.scss`:
    - Added interactive `[Settings]` gear button (`settingsOutline`) to the brand-aligned Offline Mode banner.
    - Enhanced `retryConnection()` with visual loading spinner and positive feedback toast (`Connected to backend server! Cloud sync active.`) upon successful health checks.
    - If a retry attempt fails or cannot resolve the host, automatically launches `openServerConfigAlert(true)` displaying the unreachable host and providing an intuitive input dialog to paste or update an active Cloudflare Tunnel (`https://*.trycloudflare.com`), ngrok URL, or localhost address.
    - Added "Reset to Default" action to restore the default permanent tunnel.
    - Added `showInvalidUrlToast()` to reject untrusted hostnames with informative guidance.
- **Dual-Tunnel Startup Architecture (`scripts/start_server.ps1` & `start_server.bat`)**:
  - Enhanced startup script to launch both permanent ngrok (`anybody-cube-surprise.ngrok-free.dev`) and Cloudflare Quick Tunnel (`*.trycloudflare.com`) concurrently forwarding to local port `8000`.
  - Added port collision detection: if port 8000 is already active, server startup avoids crashing uvicorn and maintains tunnel proxying without killing background processes.
  - Displayed both public connection URLs and diagnostic tips for residential Wi-Fi routers (e.g. Tenda/PLDT) with DNS-over-HTTPS guidance.
- **WQA-03 (Navigation Tab Parity)**:
  - In `Project/src/app/tabs/tabs.page.html` and `tabs.page.ts`:
    - Updated Tab 3 icon from `time-outline` to `bookmark-outline`.
    - Updated aria-label to `"Saved Itineraries"` for better clarity and alignment with modern mobile design.

### Fixed
- **SEC-01 & Dual-Tunnel Hostname Security**:
  - In `Project/src/environments/environment.prod.ts`, `environment.ts`, and `Project/src/app/core/services/connectivity.service.ts`:
    - Broadened `isValidApiUrl()` and `isTrustedApiHostname()` to securely trust `*.trycloudflare.com`, `*.ngrok-free.dev`, `*.ngrok.app`, and `*.ngrok.io`, while strictly rejecting arbitrary untrusted hostnames.
    - Added automatic `/api/v1` path normalization in `setCustomApiUrl()`.
    - Added `clearCustomApiUrl()` helper to safely clear overrides from `localStorage`.
- **WQA-01 (Guest Mode Body Copy Mismatch)**:
  - In `Project/src/app/features/auth/guest/guest.page.html`:
    - Replaced misleading copy (*"Your data won't be saved."*) with honest guest persistence notice: *"Your trips are saved locally on this device. Sign in anytime to back them up to the cloud."*.
- **WQA-02 (Suggested Wizard Day 2 Time Overlaps)**:
  - In `Project/src/app/core/data/offline-places.data.ts`:
    - Rescheduled Day 2 stops to clean, non-overlapping windows:
      - Stop 1 (Farm Villaronte): 09:00 AM – 10:30 AM (90 mins).
      - Stop 2 (Casa Batik): 11:00 AM – 12:30 PM (90 mins).
      - Stop 3 (D' Pavilion Farm and Resort): 01:00 PM – 03:00 PM (120 mins).
  - Updated corresponding unit tests in `itinerary.service.spec.ts`.

### Testing & Verification
- Unit test suite expanded to 121/121 passing tests in Vitest across all 16 test suites.
- Backend Pytest test suite (14/14 tests) passing with 100% green rate.
- Verified frontend production build compiles cleanly into `Project/www/` (829 kB initial chunk).

---

## [0.15.4-rc.10] - 2026-11-02
### Added
- **DEF-09 (Accessibility Enhancements & WCAG Compliance)**:
  - In `Project/src/app/app.component.html` and `app.component.ts`: added `tabindex="0"`, `(keydown.escape)="dismissSplash()"`, `(keydown.enter)="dismissSplash()"`, `(keydown.space)="dismissSplash()"`, `@HostListener('window:keydown.escape')`, and descriptive `aria-label` to the interactive splash screen overlay.
  - In `Project/src/app/tabs/map/map.page.ts`: decorated custom Leaflet divIcon pins with `tabindex="0"`, `role="button"`, `aria-label="${safeName}, ${safeMuni}"`, and `title="${safeName}"`, plus keyboard listeners for Enter and Space key activation.
  - Added unit test in `Project/src/app/app.component.spec.ts` asserting that `onEscapeKey()` triggers `dismissSplash()` and sets `isFadingOut = true`.
  - Added unit test in `Project/src/app/tabs/map/map.page.spec.ts` verifying that custom Leaflet pins contain `role="button"`, `tabindex="0"`, and `aria-label`.
- **CI Test Automation Gates**:
  - In `.github/workflows/deploy.yml`: Added automated test gates before build and deployment:
    - Python 3.12 setup (`actions/setup-python@v5`) with pip dependency caching.
    - Automated execution of backend Pytest suite (`python -m pytest backend/tests/ -v`).
    - Automated execution of frontend Vitest unit tests (`npm run test:unit`).
- **SEC-02 (Secure Token Storage Architectural Roadmap & ADR-010)**:
  - In `docs/SYSTEM_ARCHITECTURE.md`, `docs/TECHNICAL_DECISIONS.md` (ADR-010), and `docs/KNOWN_ISSUES.md`: Formulated comprehensive architectural migration roadmap from `window.localStorage` to `HttpOnly; Secure; SameSite=Strict` cookies for web production and native Biometric Keychain / Android Keystore enclave storage via `@capacitor-community/secure-storage-plugin` for Capacitor mobile binaries.

### Documentation
- Updated `docs/TODO.md`, `docs/DEVELOPMENT_PLAN.md`, `docs/KNOWN_ISSUES.md`, and `docs/PROJECT_STATE.md` marking Phase 15 and Milestone 15 as 100% completed.
- Verified test suite expanded to 16/16 test files and 120/120 unit tests (100% passing in Vitest), 14/14 Pytest backend tests (100% passing), and 24/24 acceptance checks (100%).

---

## [0.15.3-rc.9] - 2026-11-02
### Refactored
- **DEF-05 (Consolidated Offline POI Datasets)**:
  - Created canonical typed data module `Project/src/app/core/data/offline-places.data.ts` containing `CANONICAL_OFFLINE_PLACES` (13 curated destinations with complete metadata, verified pricing, opening hours, imagery, and coordinates).
  - Eliminated over 750 lines of duplicate hardcoded data across `home.page.ts`, `place.service.ts`, and `itinerary.service.ts` by using canonical converter functions (`getOfflineDestinationsForHome()`, `getOfflinePlacesAsPlaceEntities()`, `getOfflineCuratedPoolForItinerary()`, and `getOfflineDayClusterPresets()`).
  - Reduced `home-page` chunk transfer size from 34.95 kB to 29.44 kB.

### Fixed
- **DEF-06 (Nearby Places Category Misclassification)**:
  - Updated `getOfflineNearbyPlaces()` in `Project/src/app/core/data/offline-places.data.ts` and `place.service.ts` to strictly filter by genuine shopping/retail categories (`shopping_market`, `convenience_store`, `supermarket`, or tags containing store/market/retail).
  - Prevented cultural museum attractions (such as *Casa Batik*) and nature attractions from being erroneously categorized under "Stores" in the Suggested Itinerary Wizard's Nearby Places tab.

### Removed
- **DEF-10 (Git Hygiene & Counter Artifacts)**:
  - Added `.VSCodeCounter/` to root `.gitignore`.
  - Untracked 9 cached counter report files from Git version control via `git rm -r --cached .VSCodeCounter`.

---

## [0.15.2-rc.8] - 2026-11-02
### Fixed
- **DEF-03 (Chronological Stop Ordering & Overnight Placement)**:
  - In `backend/app/algorithms/itinerary_generator.py`: added `is_accommodation_place()` classifier, applied morning slot penalties for lodging, assigned overnight stays to the evening arrival slot (`17:30`), and enforced strict post-clustering chronological sorting by `planned_time` with sequential `sort_order` re-indexing (1, 2, 3...).
  - In `Project/src/app/core/services/itinerary.service.ts`: sorted day preset venues chronologically, added `parseTimeToMinutes()` and `isOvernightItem()` helpers, adjusted `dest-pantabangan-lake` time to `13:00`, and sorted all daily items chronologically ensuring overnight cabins (e.g. *La Casa Prime Cabins*, 22 hrs) are positioned strictly at the end of each day's schedule.

### Security
- **SEC-01 (API Hostname Allowlist)**: Restricted `resolveApiBaseUrl()` in `Project/src/environments/environment.prod.ts` and `Project/src/environments/environment.ts` to trusted hostnames (`localhost`, `127.0.0.1`, `anybody-cube-surprise.ngrok-free.dev`). Untrusted custom API hostnames stored in `localStorage` are automatically purged to prevent token exfiltration via malicious redirect URLs. Updated `ConnectivityService.isValidApiUrl()` and `setCustomApiUrl()` with domain validation.
- **SEC-03 (Production JWT Secret Enforcement)**: Strengthened Pydantic `@model_validator(mode="after")` in `backend/app/core/config.py` to reject blank, placeholder, or weak keys (<32 characters, `dev_only_replace_before_pilot_with_openssl_rand_hex_32`, `change-this-in-production-use-openssl-rand-hex-32`, etc.) when starting in non-development environments.

### Added
- **Unit Test Coverage**:
  - `backend/tests/test_itineraries.py`: Added `test_suggested_generator_chronological_ordering_and_overnight` verifying chronological sorting, sequential `sort_order`, and overnight accommodation placement.
  - `backend/tests/test_auth.py`: Extended `test_settings_secret_validation_in_production` testing insecure default placeholders and short secrets.
  - `Project/src/app/core/services/connectivity.service.spec.ts`: Added test case for `SEC-01` hostname allowlist validation and localStorage protection.
  - `Project/src/app/core/services/itinerary.service.spec.ts`: Added test case for `DEF-03` verifying chronological stop ordering and end-of-day overnight stay placement.
  - Test suites green: 14/14 Pytest backend tests (100%), 16/16 Vitest frontend suites with 117/117 unit tests (100%), and 24/24 acceptance checks (100%).

---

## [0.15.1-rc.7] - 2026-11-02
### Fixed
- **DEF-04 (Duplicate Route Handler)**: Deleted the first shadowed duplicate `@router.patch("/{itinerary_id}/days/{day_id}/items/{item_id}")` handler in `backend/app/api/v1/itineraries.py`. Ensured all single-stop update requests execute the complete handler supporting `day_id` consistency validation and automatic `itinerary.updated_at` timestamp refresh.
- **DEF-01 (Deceptive Forgot Password Toast)**: Remediated `onForgotPassword()` in `Project/src/app/features/auth/login/login.page.ts`: added `Validators.email` validation to the email form control and replaced misleading success toast with an honest pilot notice informing the user that self-service password reset is disabled in the pilot build and directing them to contact an administrator.
- **DEF-02 (Stubbed Google Auth Buttons)**: Gated non-functional Google Sign-In and Sign-Up buttons on `login.page` and `signup.page` with visual disabled cues (`unavailable-btn`, `disabled-logo`, grayscale styling, `aria-disabled="true"`), and truthfully notified users via toast that Google OAuth is disabled in the pilot build.
- **DEF-08 (Apple Sign-In Copy Typo)**: Corrected copy-paste typo in `login.page.ts` where clicking Apple Sign-In toasted *"Apple Sign-Up is disabled..."*, standardizing it to *"Apple Sign-In is disabled in this pilot build."*.

### Added
- **Unit Test Coverage**: Added dedicated Vitest spec suites for auth pages:
  - `Project/src/app/features/auth/login/login.page.spec.ts` (5 tests covering form initialization, validation, password toggle, disabled Google/Apple toasts, and forgot password handling).
  - `Project/src/app/features/auth/signup/signup.page.spec.ts` (3 tests covering form initialization, matching password validation, and disabled OAuth handlers).
  - Total frontend test suite expanded to 16 test files and 115 passing tests (100% green).

---

## [0.15.0-rc.6] - 2026-11-02
### Changed
- **Anti-Generic UI Refactoring (Approach 1)**: Replaced the developer-oriented "Pilot Backend Offline" prompt banner with a brand-aligned "Offline Mode" status banner in `Project/src/app/app.component.html` and `Project/src/app/app.component.scss`.
  - Removed `[Set Server]` button and `AppComponent.configureApiUrl()` prompt to prevent user confusion and eliminate the arbitrary backend URL injection / token exfiltration vector.
  - Updated title to **"Offline Mode"** and description to **"Cloud sync paused. Your saved trips and curated destinations remain accessible."**
  - Enhanced visual presentation per `anti-generic-frontend-design` guidelines: translucent slate-900 surface with subtle warm amber indicator icon wrapper, tactile `[Retry]` button with `ion-spinner`, accessible `[✕ Dismiss]` button, and full safe-area padding.
- **Persistent ngrok Integration**: Baked permanent ngrok endpoint `https://anybody-cube-surprise.ngrok-free.dev/api/v1` into `Project/src/environments/environment.prod.ts` and `Project/src/environments/environment.example.ts`, eliminating the need to copy ad-hoc Cloudflare URLs upon startup. Configured `scripts/start_server.ps1` to automatically tunnel port 8000 to the domain.
- **Unit Testing**: Updated `Project/src/app/app.component.spec.ts` to assert that the offline mode status and description render without developer inputs, and verified all 107/107 Vitest tests and the 24/24 acceptance gate pass.

---

## [0.14.0-rc.5] - 2026-11-02
### Added
- **CR-013**: Configured SlowAPI rate-limiting key function `get_client_ip` in `backend/app/core/limiter.py` to inspect `CF-Connecting-IP` and `X-Forwarded-For` when requests arrive from local proxies or Cloudflare Tunnel (`127.0.0.1`, `localhost`, `::1`, `testclient`). Added test coverage in `test_auth.py`.
- **CR-014**: Modern Playwright E2E journey test suite in `Project/e2e/app.spec.ts` covering root redirection, guest authentication, tab switching between Home and Map, and the Custom Itinerary Builder travel questionnaire. Verified with `npm run typecheck:e2e`.

### Optimized
- **CR-013**: Implemented SQL coordinate bounding box pre-filtering in `backend/app/algorithms/itinerary_generator.py` to filter candidates at the database query level instead of loading all 4,400+ POIs into Python memory.
- **CR-013**: Batch queried existing records using `Place.source_record_id.in_()` in chunks of 500 in `scripts/import_osm.py` and `scripts/seed_featured_places.py`, eliminating N+1 round trips.

---

## [0.13.0-rc.4] - 2026-11-02
### Removed
- **CR-014**: Deleted 16 dead starter files from initial Ionic template generation (`tab1/`, `tab2/`, `tab3/`, `explore-container/`).
- **CR-014**: Deleted destructive root scaffolding script `setup_steps_0_to_2.py`.
- **CR-015**: Pruned 44 unused SHA-1 hash image files from `Project/src/assets/images/`.

### Fixed
- **CR-014**: Replaced 7 tautological checks in `scripts/verify_acceptance_gate.py` with real assertions.
- **CR-015**: Fixed observable memory leak in `ProfilePage` (`Project/src/app/tabs/profile/profile.page.ts`) by implementing `OnDestroy` and storing/unsubscribing `userSub`. Added `profile.page.spec.ts`.
- **CR-015**: Corrected UI copy typos in `welcome.page.html`, `guest.page.html`, and `login.page.html`.
- **CR-015**: Dynamically resolved nearby places by municipality in `PlaceService.getNearbyPlaces()`.

---

## [0.12.0-rc.3] - 2026-11-02
### Added
- **CR-006 & CR-012**: Token refresh rotation in `Project/src/app/core/services/auth.service.ts` and 401 retry queueing in `auth.interceptor.ts`.
- **CR-007**: Centralized timezone-agnostic date utility `Project/src/app/core/utils/date.utils.ts` with local calendar arithmetic.
- **CR-010**: Single-stop update endpoint `PATCH /api/v1/itineraries/{id}/days/{day_id}/items/{item_id}`.
- **CR-011**: Query parameter navigation from Home to Map tab and non-blocking `tileerror` banner.
- **CR-013 (F.4)**: Clean drop-before-create flags (`--clean --if-exists`) in `scripts/db_backup_restore.py`.

### Fixed
- **CR-008**: Enforced `default_dest_radius_km` (25km) and cumulative daily budget tracking in `itinerary_generator.py`; escaped SQL wildcards in `places.py`.
- **CR-009**: Connected online guests to suggested generator and dynamically bound wizard budget presets.
- **CR-010**: Fixed sort-order auto-increment starting index bug and added 404 validation for nonexistent `place_id` foreign keys.

---

## [0.11.0-rc.2] - 2026-11-01
### Security
- **CR-001**: Fixed cross-itinerary BOLA in `POST /api/v1/itineraries/{id}/reorder` by verifying day membership.
- **CR-002**: Fixed cross-itinerary BOLA/IDOR in `DELETE /api/v1/itineraries/{id}/days/{day_id}/items/{item_id}`.
- **CR-004**: Blocked default JWT secret in non-development environments; enforced `google_oauth_client_id` audience validation; tightened CORS regex to explicit GitHub Pages origin.
- **CR-005**: Enforced `email_verified is True` on Google OAuth account linking and blocked deactivated users (`is_active=False`).

### Fixed
- **CR-003**: Fixed silent data loss when saving edited itineraries by extending `ItineraryUpdate` to accept `days`.

---

## [0.10.0-rc.1] - 2026-10-31
### Added
- **Phase 10: Pilot Acceptance Gate**:
  - Implemented 24-point automated acceptance verification runner `scripts/verify_acceptance_gate.py` with 100% pass rate.
  - End-to-end regression validation: 100% test pass rate across backend pytest, frontend vitest, and production build.

---

## [0.9.0-alpha] - 2026-10-31
### Added
- **Phase 9: Pilot Security, Connectivity Resilience & Disaster Recovery**:
  - **SlowAPI Rate Limiting**:
    - Integrated SlowAPI rate limiting (`app.core.limiter`) on authentication routes (`/api/v1/auth/login`, `/register`, `/refresh`, `/oauth/google`) capped at 5 req/min per IP.
    - Verified with integration test `test_auth_rate_limiting` asserting HTTP 429 Too Many Requests on the 6th attempt.
  - **Offline Host Laptop Warning Banner (`ConnectivityService`)**:
    - Built `ConnectivityService` with reactive `isHostOffline$` and active `checkHostHealth()` prober against `GET /api/v1/health`.
    - Wired into `authInterceptor` to detect connection drops (HTTP 0, 502, 504) and automatically recover when requests succeed.
    - Added floating offline status banner to `AppComponent` with "Retry" health check and dismiss controls.
    - Added comprehensive unit tests in `connectivity.service.spec.ts` and `app.component.spec.ts`.
  - **Database Disaster Recovery Utility (`scripts/db_backup_restore.py`)**:
    - Created backup and restore CLI utility supporting PostgreSQL (`pg_dump` / `psql`) and SQLite (online backup API / DDL iterdump).
    - Includes automated `drill` subcommand that seeds canary data, snapshots, simulates data loss, restores from snapshot, and verifies data integrity.
    - Created automated test `test_backup_restore.py` verifying the full drill cycle.
    - Created documentation guide in `docs/BACKUP_AND_RESTORE.md`.

---

## [0.8.6-alpha] - 2026-10-31
### Added
- **Phase 8: Unified Itinerary Overview, Day Timeline & Guest Migration**:
  - **Unified Itinerary Overview & Day View (`/itinerary/:id`)**:
    - Created `ItineraryDetailPage` matching Figma Screen 2 (`Suggested Itinirerary (1)`):
      - Hero card with destination photo thumbnail, title, travel duration, daily budget, and preference pills.
      - Segmented day switcher capsule bar with active `#0084ff` highlight.
      - Day timeline view with numbered stop cards, photos, scheduled timings (`12:00 PM - 2:00 PM (2 hrs)`), cost estimates, and notes.
      - Stop details modal sheet with opening hours, cost, description, and external Google Maps navigation.
      - "Customize Itinerary in Builder" action and delete confirmation alert.
  - **Nearby Places Sub-View (Figma Screens 3, 4, 5)**:
    - Integrated "Nearby Places" directly into `ItineraryDetailPage` and `SuggestedWizardPage`.
    - Tab filter capsule for Restaurants, Hospital & Pharmacies, and Stores.
    - Centered card format with opening hours matching Figma mockups.
  - **Guest-to-Account Itinerary Migration (`GuestMigrationService`)**:
    - Built `GuestMigrationService` to seamlessly sync local guest trips from `GuestStorageService` to the backend upon login or registration.
    - Wired into `LoginPage` and `SignupPage`.
    - Added reactive guest trip indicator and "Sync to Account Now" trigger to `ProfilePage`.
  - **Navigation Synchronization**:
    - Wired Home tab and History tab to navigate directly to `/itinerary/:id` when tapping saved itineraries.
  - **Automated Verification**:
    - 100% test pass rate across 15 test files (89/89 Vitest unit tests passing; 4/4 Pytest backend tests passing).
    - 0 compilation errors and 0 Angular style budget warnings.

---

## [0.8.5-alpha] - 2026-10-31
### Changed
- **Travel Dates Pop-Up Window Design Format Alignment (Anti-Generic Frontend Design)**:
  - **Previous Tab Format Consistency**: Refactored the "Select Travel Dates" pop-up window to match the exact visual language of the previous tabs (bold black labels, `.figma-input-box` with 1.5px dark charcoal border `#1e293b`, blue `#0084ff` calendar icons, and borderless date input controls).
  - **Quick Presets as Preference Pills**: Transformed duration presets into canonical `.figma-pref-pill` capsules with dark borders (`#1e293b`) that illuminate in solid `#0084ff` blue when active.
  - **Seamless Action Button Stack**: Replaced small side-by-side action buttons with the full-width `.find-itinerary-cta-btn` pill button and clean text cancel action.
  - **Production Verification**: 100% test pass rate across 13 test files (74/74 tests) and 0 Angular style budget warnings.

---

## [0.8.4-alpha] - 2026-10-31
### Changed
- **Suggested Itinerary & Custom Builder Questionnaire Redesign (Figma Match)**:
  - **Figma Alignment**: Redesigned Suggested Itinerary form to match the user's Figma screenshot (`media_1793429982308_d8faa776.png`) with clean white background, borderless header with left-aligned blue back arrow and title, crisp `#1e293b` input borders, and 2-2-1 preference pills.
  - **Interactive Travel Dates Pop-Up Window**: Replaced inline raw date pickers with a clean Travel Dates field that opens an interactive pop-up window to select "From" (departure) and "To" (return) dates.
  - **Pop-Up Window Capabilities**: Features dual departure/return inputs, friendly date formatting previews, duration preset chips (`2D1N`, `3D2N`, `4D3N`, `1 Week`), and live trip duration validation.
  - **Unified Builder Experience**: Brought the same date picker pop-up window into `CustomBuilderPage` for consistent questionnaire behavior.
  - **Automated Verification**: Added comprehensive unit test coverage for date picker pop-up controls in both wizards (13/13 test files, 74/74 unit tests passing; 0 build errors, 0 style budget warnings).

---

## [0.8.3-alpha] - 2026-10-31
### Added
- **Home Tab Saved Itineraries Limit & Dedicated History/Saved Itineraries Tab**:
  - **Home Tab Truncation**: Capped displayed saved itineraries to exactly 2 (`displayedSavedItineraries = savedItineraries.slice(0, 2)`) to keep the home feed clean and focused.
  - **"See all" Redirection**: Updated header button to "See all" and linked directly to the dedicated Saved Itineraries tab (`/tabs/history`).
  - **History Tab Implementation**: Replaced placeholder with a production-grade Saved Itineraries view reactively connected to `ItineraryService.itineraries$`.
  - **Rich Trip Cards**: Each saved itinerary displays plan type badges (`Suggested Plan` vs `Custom Plan`), daily budget pill (`₱X/day`), title, destination with location icon, travel date span, days and stops counter (`X Days · Y Stops`), and delete action with confirmation dialog.
  - **Empty State**: Added an empty state with dual action buttons linking travelers directly to `/suggested-wizard` and `/custom-builder`.
  - **Style Budget Compliant**: Kept `history.page.scss` at 9.50 kB, preserving zero Angular style budget warnings.
  - **Test Suite**: Added unit tests in `history.page.spec.ts` and updated `home.page.spec.ts`.

---

## [0.8.2-alpha] - 2026-10-31
### Added
- **Custom Itinerary Questionnaire Flow (Figma Alignment)**:
  - Added "Tell us your travel details" questionnaire view to Custom Itinerary matching Figma mockups (`media_1793427570420_e2591e62.png`).
  - Added blue icon accents (`#0084ff`), live date duration calculations, and 5 preference capsules (`Nature & Parks`, `Food Trip`, `Culture & History`, `Shopping`, `Resort`).
  - Added "Find Itinerary" CTA transitioning to the places browser and synchronizing days with chosen travel dates.
  - Centralized shared questionnaire styles in `src/global.scss`, keeping `custom-builder.page.scss` under 10.00 kB with 0 Angular style budget warnings.
  - Added unit test coverage for the questionnaire flow (66/66 frontend tests passing).

---

## [0.8.1-alpha] - 2026-10-31
### Added
- **Suggested Itinerary & Nearby Places Flow (Figma Alignment)**:
  - **Figma Screenshot Match**: Re-architected Suggested Itinerary into a seamless 3-view flow (`form` -> `itinerary` -> `nearby`) precisely reproducing Figma designs.
  - **Bongabon Day 1 Stops**: Added Rohi Paperflower Cafe, La Casa Prime Cabins, Museo de Bongabon, and Thornes Samgyupsal House with high-res assets and verified timings.
  - **Nearby Places Explorer**: Integrated Figma's 3-tab Nearby Places browser (`Restaurants`, `Hospital & Pharmacies`, `Stores`) for Bongabon with 16 venues and verified operating hours.
  - **Form Screen Enhancements**: Added blue icon styling, live date duration calculations, and 5 preference capsules (`Nature & Parks`, `Food Trip`, `Culture & History`, `Shopping`, `Resort`).
  - **Automated Verification**: Added comprehensive unit test coverage for tab switching, nearby modals, and timing formatters (64/64 frontend tests passing, 4/4 backend pytest suites passing).

---

## [0.8.0-alpha] - 2026-10-31
### Changed
- **Suggested Itinerary & Custom Itinerary Redesign (Figma Flow 2 & Anti-Generic Frontend Design)**:
  - **Figma Design Precision**: Rebuilt both itinerary workflows to mirror Figma `Travel Itinerary App.fig` Flow 2 layouts, typography, and copy without generic templates.
  - **Suggested Itinerary Wizard**:
    - Re-architected Screen 1 ("Tell us your travel details") with prominent search-style destination input, calendar date range selector, daily budget field, and 4 specific preference pills (`Nature & Parks`, `Food Trip`, `Culture & History`, `Shopping`).
    - Re-architected Screen 2 ("Your Itinerary") with top edit button, trip summary hero card, segmented day selector tabs, day location headlines, vertical timeline cards with duration/time pills (`12:00 PM - 2:00 PM (2 hrs)`), cost estimates, transparent assumptions box, and dual save actions ("Accept & Save Itinerary" / "Customize in Builder").
  - **Custom Itinerary Builder**:
    - Introduced Figma's two-view architecture toggled via a top segmented bar (`Add Places` vs `Your Itinerary (N)`).
    - View 1 ("Add the places you want to visit"): Day target chips, search bar with clear button, category filter chips (`All`, `Tourist Spots`, `Food`, `Shopping`, `Other`), responsive 2-column cards grid with instant `Add / Added` toggle, and sticky bottom CTA `"View my Itinerary (N places)"`.
    - View 2 ("Your Custom Itinerary"): Trip settings form (title, dates, destination, daily budget), verified budget summary card, day tabs, vertical timeline with reorder controls, "Add More Places", and "Add Off-Grid Custom Venue" modal sheet.
  - **Offline Place Fallback**:
    - Enhanced `PlaceService` with comprehensive offline curated fallback for 10 verified bundled Nueva Ecija destinations, guaranteeing seamless place catalog browsing on static GitHub Pages.
  - **Style Optimization & Zero Budget Warnings**:
    - Consolidated SCSS rules and centralized global modal/budget styles in `Project/src/global.scss`, reducing `custom-builder.page.scss` to <= 10.00 kB to achieve 0 Angular build warnings.

---

## [0.7.1-alpha] - 2026-10-31
### Fixed
- **Suggested Itinerary Offline & GitHub Pages Reliability**:
  - Fixed client hanging on static GitHub Pages HTTPS deployment by checking guest/offline state upfront in `ItineraryService.suggestItinerary()` and attaching a 4-second timeout fallback.
  - Replaced missing image asset references (`rohi_cafe.png`, `museo_bongabon.png`) in offline curated fallback pool with verified bundled photos (`minalungao.png`, `tagpuan_gapan.png`, `pantabangan_lake.png`, `george_point.png`, `highland_bali.png`, `farm_villaronte.png`, etc.).
  - Attached fully-formed `Place` objects to offline generated stops, preventing blank category badges, missing municipalities, and 404 images.
  - Fixed substring match bug in `PlaceService.getPlaceImage` when handling empty strings.
  - Added explicit `(click)` and `(keydown.enter)` navigation triggers to Home tab planner entry cards to guarantee touch responsiveness across mobile WebKit and Chrome.
  - Updated Home tab's `openItinerary()` to route saved suggested plans to `/custom-builder/:id` rather than dead-ending into `/tabs/history`.
  - Added "Customize in Builder" button in Suggested Wizard allowing instant transition to builder view.

---

## [0.7.0-alpha] - 2026-10-31
### Added
- **Deterministic Suggested Itinerary Recommendation Engine (`Milestone 7`)**:
  - Implemented `backend/app/algorithms/itinerary_generator.py` using deterministic Haversine distance clustering and category/preference scoring without paid external AI or mapping APIs.
  - Added preference scoring matrix (+40 category match, +20 featured place, up to +30 distance proximity, -25 duplicate category penalty, +10 budget fit).
  - Implemented multi-day geographic clustering preventing cross-province backtracking.
  - Implemented realistic pacing allocating 2-3 stops/day and dedicated lunchtime dining windows (11:30 AM - 1:30 PM).
  - Implemented transparent trip assumptions generator outlining pacing rationale, transit time exclusions, and unlisted entrance fee notices.
  - Added `get_current_user_optional` in `backend/app/services/auth_service.py` to support guest draft generation.
  - Added `POST /api/v1/itineraries/suggest` endpoint supporting optional persistence for authenticated users and guest drafts.
  - Authored automated pytest in `backend/tests/test_itineraries.py` (`test_suggested_itinerary_engine`) verifying multi-day clustering, anonymous mode, and validation (100% passing).
- **Frontend Suggested Itinerary Wizard (`Milestone 7`)**:
  - Implemented `suggestItinerary()` in `Project/src/app/core/services/itinerary.service.ts` with offline fallback (`generateOfflineSuggestedItinerary`) using seeded curated places.
  - Created `SuggestedWizardPage` in `Project/src/app/features/itinerary/suggested-wizard/`:
    - Responsive questionnaire form with quick destination chips, trip duration calculator, daily budget presets (₱1,500 - ₱6,000), and preference chips.
    - "Your Itinerary" preview sheet with day timeline, stop cards, transparent assumptions box, and "Accept & Save" persistence.
  - Authored 10 comprehensive Vitest unit tests in `suggested-wizard.page.spec.ts` (100% passing).
- **Home Tab & Router Integration**:
  - Connected "Suggested Itinerary" action card on Home tab (`Project/src/app/tabs/home/home.page.html`) to route `/suggested-wizard`.
  - Registered route `/suggested-wizard` in `Project/src/app/app.routes.ts`.

### Technical Improvements
- Added `"optimization": { "scripts": true, "styles": true, "fonts": false }` to `Project/angular.json` ensuring offline sandboxed Angular builds pass without font download errors.
- Styled `suggested-wizard.page.scss` cleanly under 5.5 kB, comfortably below Angular's strict 10 kB style budget.
- Expanded total automated unit tests to 63 Vitest tests (100% passing) and 4 Pytest backend test suites (100% passing).

---

## [0.6.0-alpha] - 2026-10-31
### Added
- **Backend Custom Itinerary CRUD & BOLA Architecture (`Milestone 6`)**:
  - Implemented Pydantic v2 schemas in `backend/app/schemas/itinerary.py` (`ItineraryCreate`, `ItineraryUpdate`, `ItineraryOut`, `ItineraryDayCreate`, `ItineraryItemCreate`, `ItineraryReorderIn`).
  - Added `place: Mapped["Place | None"] = relationship()` on `ItineraryItem` in `backend/app/models/entities.py` with eager `selectinload` loading.
  - Implemented FastAPI CRUD and sub-resource endpoints in `backend/app/api/v1/itineraries.py` with strict Broken Object Level Authorization (BOLA), returning 404 for unowned resources.
  - Added same-day duplicate POI check returning HTTP 400 when attempting to add an identical destination on the same day.
  - Added batch reorder endpoint `POST /api/v1/itineraries/{id}/reorder`.
  - Authored automated pytest suite in `backend/tests/test_itineraries.py` testing BOLA enforcement, full CRUD lifecycle, duplicate checks, and reordering.
- **Frontend Itinerary Service & Dual-Mode Persistence (`Milestone 6`)**:
  - Created TypeScript models in `Project/src/app/core/models/itinerary.models.ts`.
  - Implemented `ItineraryService` in `Project/src/app/core/services/itinerary.service.ts` supporting authenticated API persistence and seamless offline `GuestStorageService` fallback.
  - Implemented `calculateBudgetSummary()` computing honest verified cost ranges (`₱min - ₱max`) and flagging unverified stops.
  - Authored 13 unit tests in `itinerary.service.spec.ts` (100% passing).
- **Custom Itinerary Builder UI (`Project/src/app/features/itinerary/custom-builder`)**:
  - Built multi-day itinerary builder with trip title, dates, destination, and daily budget controls.
  - Added day tabs carousel with active highlight and dynamic "+ Add Day" and "Delete Day" actions.
  - Implemented chronological stop cards with order badge, category tag, verified cost tag, duration, and notes.
  - Added stop reordering controls (Move Up / Move Down) and delete stop actions.
  - Built Place Picker Modal with live database search (`PlaceService.searchPlaces`) and off-grid custom venue form.
  - Added duplicate stop confirmation dialog when a place is already scheduled for that day.
  - Implemented honest budget summary banner comparing verified costs against daily target budgets.
  - Implemented unsaved changes exit/cancel alert guard.
  - Authored 6 unit tests in `custom-builder.page.spec.ts` (100% passing).
- **Home Tab Integration**:
  - Connected "Custom Itinerary" action card and empty-state card to navigate to `/custom-builder`.
  - Subscribed Home tab's saved itineraries to `ItineraryService.itineraries$` so custom plans sync reactively.
- **Routing**:
  - Registered `/custom-builder` and `/custom-builder/:id` in `Project/src/app/app.routes.ts`.

### Technical Improvements
- Optimized `custom-builder.page.scss` to strictly stay under Angular's 10 kB style budget without warnings.
- Expanded project unit test suite from 32 tests to 51 tests (100% passing).

---

## [0.5.2-alpha] - 2026-10-31
### Fixed
- **GitHub Pages Deep-Linking & Base HREF (`.github/workflows/deploy.yml`)**:
  - Replaced ambiguous relative `--base-href ./` with explicit repository path `--base-href /Itinerary-App/` in CI build step.
  - Resolved 404 script loading failures and blank white screens when users directly enter deep URLs (`/tabs/home`, `/tabs/map`, etc.) on GitHub Pages.

---

## [0.5.1-alpha] - 2026-10-31
### Fixed
- **Map Tab Fullscreen Geometry & Tab Occlusion (`Project/src/app/tabs/map`)**:
  - Added `:host { display: block; position: absolute; inset: 0; width: 100%; height: 100%; background-color: #f8fafc; z-index: 10; }` preventing the underlying Home tab from bleeding through.
  - Set `.map-page-content`, `.map-wrapper`, and `.map-canvas` to `position: absolute; inset: 0; width: 100%; height: 100%;` resolving Leaflet 0-height container collapse.
  - Added `@ViewChild('mapElement')` and attached `window.L = L` in browser mode for robust element discovery.
  - Fixed tab button default color in `tabs.page.scss` to `#94a3b8` (muted slate) so inactive icons do not appear active.

---

## [0.5.0-alpha] - 2026-10-31
### Added
- **Interactive Leaflet Map & 16 Category Filters (`Milestone 5`)**:
  - Implemented bounded Leaflet map centered on Nueva Ecija `[15.58, 121.00]` with strict maxBounds constraint (`[15.05, 120.55]` to `[16.25, 121.55]`).
  - Integrated OpenStreetMap raster tiles with mandatory legal attribution.
  - Added horizontal scroll filter track with "All Places" and all 16 canonical categories (`tourist_attraction`, `nature_park`, `resort_swimming`, `hotel_accommodation`, `restaurant`, `cafe`, `church_religious`, `museum_cultural`, `shopping_market`, `transport_terminal`, `convenience_store`, `hospital_clinic`, `pharmacy`, `bank_atm`, `fuel_station`, `public_facility`).
  - Implemented POI clustering with `leaflet.markercluster` and custom CSS vector pins (teardrop pin with white inner dot, gradient for featured destinations).
  - Built interactive POI Bottom Sheet displaying hero image with local photography fallback, category badge, municipality pin, operating hours, honest pricing, tags, and keyless Google Maps directions link.
  - Handled Ionic tab switching lifecycle with `ionViewDidEnter()` calling `map.invalidateSize()`.
  - Added floating Recenter button (`locate-outline`) and live destination counter pill.
  - Added 9 Vitest unit tests in `map.page.spec.ts` (bringing total project unit tests to 32 passing).
  - Configured `allowedCommonJsDependencies` in `angular.json` for `leaflet`, `leaflet.markercluster`, and `localforage` for zero-warning production builds.

---

## [0.4.14-alpha] - 2026-10-31
### Fixed & Improved
- **Destination Detail Modal Layout & Image Alignment (`Project/src/app/tabs/home`)**:
  - Restored `.destination-modal` SCSS styling to prevent unconstrained full-resolution photography from pushing modal content below the visible fold.
  - Constrained modal hero photo container to 240px height with `object-fit: cover` and preserved responsive rounded sheet aesthetics.
  - Added `-webkit-overflow-scrolling: touch` and `max-height: 85vh; overflow-y: auto` to `.modal-detail-content` ensuring verified operating hours, honest cost bounds, tags, description, and external Google Maps buttons remain accessible across all screen sizes.
  - Optimized component SCSS selectors to strictly comply with Angular's 10 kB style budget without warnings.

---

## [0.4.13-alpha] - 2026-10-31
### Added & Changed
- **Home Tab Local Search, Dynamic Featured Places & Saved Itineraries (`Milestone 4`)**:
  - Implemented 300ms debounced RxJS search with `FormControl`, `debounceTime`, `distinctUntilChanged`, and `switchMap` cancellation to query `PlaceService.searchPlaces()` against local database POIs (zero Nominatim calls).
  - Built reactive search results view with 2-column cards, loading spinner, category badges, and empty-state guidance.
  - Connected Popular Destinations horizontal track to live featured places via `PlaceService.getFeaturedPlaces()` with seamless fallback to curated local high-res photography.
  - Enriched Destination Detail Modal with operating hours and honest cost estimates (`₱min - ₱max` or `"Cost not provided"`).
  - Integrated Saved Itineraries section connected to `GuestStorageService.itineraries$` with clean trip cards and an empty-state call-to-action.
  - Created unit test suite in `home.page.spec.ts` (6 tests passing, bringing total test count to 23).

---

## [0.4.12-alpha] - 2026-10-31
### Added
- **Place Models & PlaceService (`Milestone 4 Step 1`)**:
  - Implemented strong TypeScript interfaces in `Project/src/app/core/models/place.models.ts` (`Place`, `Municipality`, `PaginatedPlaces`, `PlaceSearchParams`).
  - Implemented `PlaceService` in `Project/src/app/core/services/place.service.ts` providing methods for `searchPlaces()`, `getFeaturedPlaces()`, `getPlaceById()`, and `getMunicipalities()`.
  - Added fallback high-definition photography mapper in `PlaceService.getPlaceImage()` mapping venues to bundled local assets (`minalungao.png`, `tagpuan_gapan.png`, `pantabangan_lake.png`, etc.).
  - Created complete Angular unit test suite in `place.service.spec.ts` with 11 passing tests verifying HTTP request shapes, query string serialization, and fallback branches.

---

## [0.4.11-alpha] - 2026-10-31
### Changed
- **Apple Social Auth Unavailable State (Login & Signup)**:
  - Visually grayed out the "Continue with Apple" button across both `/login` and `/signup` screens with a muted slate palette (`#f1f5f9` background, `#e2e8f0` border, `#94a3b8` icon and text) and `not-allowed` cursor.
  - Retained accessible informational feedback to clearly communicate pilot status.

---

## [0.4.10-alpha] - 2026-10-31
### Changed & Fixed
- **Signup Screen Exact Figma Alignment & Clean Typography**:
  - Refactored Signup screen layout to match exact Figma mockup with top blue back arrow, centered tilted airplane branding, left-aligned *"Create your account"*, and *"Get started and plan your new adventure."* subtitle.
  - Aligned input fields in exact screenshot sequence: First Name, Middle Initial (if applicable), Last Name, Email with mail icon, Password with key icon and eye toggle, and Confirm Password with checkmark-circle icon and eye toggle.
  - Implemented solid blue pill button (*"Sign up"*), switch row (*"Already have an account? Log in"*), centered *"or"* divider, and outlined social buttons (*Continue with Google*, *Continue with Apple*).
  - Derived username automatically to preserve backend registration schema integrity without cluttering the UI.

---

## [0.4.9-alpha] - 2026-10-31
### Changed & Fixed
- **Login Screen Figma Alignment & Boilerplate Cleanup**:
  - Replaced Login screen layout with exact Figma design: centered airplane branding, left-aligned *"Welcome back!"*, and clean *"Log in to continue your journey."* subtitle.
  - Removed all repetitive "Nueva Ecija" boilerplate from the authentication flow.
  - Updated inputs with embedded blue icons (`mail-outline` and `key-outline`) and trailing eye toggle.
  - Transformed Google and Apple social logins into uniform outlined pill buttons.
  - Upgraded action button to solid blue pill button with focus and disabled states.

---

## [0.4.8-alpha] - 2026-10-31
### Added
- **Fullscreen Interactive Loading / Splash Screen**:
  - Implemented the Figma-aligned loading screen with twilight cityscape imagery and *"Trip mo, trip ko"* branding.
  - Added support for auto-dismissal (2.8s after frontend readiness), click/tap to dismiss, and swipe gestures.
  - Implemented smooth cubic-bezier scale and opacity transition to seamlessly reveal the underlying view.

---

## [0.4.7-alpha] - 2026-10-30
### Added & Changed
- **High-Resolution Asset Upgrade**:
  - Unzipped and extracted `Log_in_pics` and `Popular_Destinations` asset archives into `Project/src/assets/images/`.
  - Replaced all blurry/low-resolution images across Welcome screen, Guest screen, and Home tab popular destination cards with high-definition assets.
  - Added *Lake Farm de La Marre* and *La Casa Prime Cabins* to the curated destination list.

---

## [0.4.6-alpha] - 2026-10-30
### Added & Changed
- **Home Tab & Navigation Bar Figma Alignment**:
  - Re-architected Home tab layout: bold 2-line header, blue notification bell, search box with right-aligned icon.
  - Implemented 2-column side-by-side planner cards: Midnight Navy *Suggested Itinerary* and Sky-Blue-bordered *Custom Itinerary*.
  - Simplified *Popular Destinations* into a clean horizontal track with 120px photo tiles, bold titles, and municipality subtitles.
  - Updated bottom tab bar to icon-only navigation with 4 electric blue icons (`#0084ff`).
  - Preserved destination detail modal sheet, search filtering, and external Google Maps routing.

---

## [0.4.5-alpha] - 2026-10-30
### Fixed
- **GitHub Actions CI Node.js Version for Angular 22**:
  - Upgraded `.github/workflows/deploy.yml` runner Node.js version from `20` to `24`.
  - Satisfies `@angular/cli@22.2.4` requirement (`>= v22.22.3 || >= v24.15.0`) and eliminates exit code 3 during GitHub Pages automated deployment.

---

## [0.4.4-alpha] - 2026-10-30
### Fixed
- **Untrack Gitignored Files from Index**:
  - Untracked `Project/src/environments/environment.prod.ts`, `Project/figma_strings.txt`, and `scripts/__pycache__/*.pyc` from Git index while preserving local files on disk.
  - Added `Project/src/environments/environment.example.ts` as an untracked environment fallback template.
  - Updated GitHub Actions workflow `.github/workflows/deploy.yml` to automatically initialize `environment.prod.ts` from `environment.example.ts` or `environment.ts` during CI runs.

---

## [0.4.3-alpha] - 2026-10-30
### Fixed
- **Gitignore Conflicts & Monorepo Hierarchy**:
  - Re-established comprehensive root `.gitignore` protecting secrets (`.env`), Python cache (`__pycache__`), SQLite databases (`*.db`, `*.sqlite3`), scratch files, and mobile build outputs.
  - Aligned `Project/.gitignore` with root rules.
  - Untracked `.env`, `scratch/`, `__pycache__`, and `*.bin` from Git tracking.
  - Cleaned up redundant root-level duplicate files (`src/`, `package.json`, `angular.json`, etc.) that were accidentally committed during an earlier merge, ensuring `Project/` remains the single canonical source of truth for the Ionic client.

---

## [0.4.2-alpha] - 2026-10-30
### Added
- **Dedicated Guest Onboarding Page (`/guest`)**:
  - Implemented standalone `GuestPage` (`Project/src/app/features/auth/guest/`) replacing the previous modal sheet popup.
  - Full-bleed mountain hiker hero photo (`assets/images/guest_hiker_hero.png`) with floating semi-transparent back button.
  - Exact layout with bold title *"Explore as a guest"*, copy, solid blue pill button *"Continue as Guest"*, and outline pill button *"Create an Account"*.
  - Configured route `/guest` in `app.routes.ts`.

### Changed
- Refactored `welcome.page.*` to remove popup modal and navigate cleanly to `/guest`.

---

## [0.4.1-alpha] - 2026-10-30
### Changed
- **Welcome Screen Layout Realignment**:
  - Re-anchored city buildings graphic (`welcome_hero_buildings.png`) to the bottom of the screen.
  - Implemented header row with inline Clarity airplane SVG + *"Trip mo, trip ko"* title.
  - Added subheadline *"Your next adventure is waiting."* and subtitle *"Get personalize iternaries, easy commutes, and nearby essentials."*
  - Converted *"Log in"* and *"Sign up"* into solid blue pill buttons (`#0084ff`).
  - Added centered `line or line` divider.
  - Converted *"Continue as Guest"* into an outline pill button with solid blue person icon.
- **Ionic 9 Standalone Cleanup**:
  - Replaced lingering `@ionic/angular/standalone` imports in `tabs.page.ts`, `history.page.ts`, and `map.page.ts` with standard `@ionic/angular`.

---

## [0.4.0-alpha] - 2026-10-30
### Added
- **Figma Visual Realignment & Extracted Assets**:
  - Extracted 44 high-resolution imagery assets from `Travel Itinerary App.fig` into `Project/src/assets/images/`.
  - Mapped assets for `welcome_hero_buildings.png`, `guest_illustration.png`, `google_logo.png`, and 9 venue destination cards (`minalungao.png`, `tagpuan_gapan.png`, `pantabangan_lake.png`, `george_point.png`, `highland_bali.png`, `farm_villaronte.png`, `casa_batik.png`, `pavillion_farm.png`, `la_casa_prime.png`).
  - Implemented interactive *"Explore as a guest"* modal sheet in `WelcomePage` with Figma illustrations and localized messaging.
  - Implemented authentic Google OAuth branded button with multi-colored logo `google_logo.png` in `LoginPage`.
  - Implemented Figma Flow 2 Home layout:
    - *"Where are you going next?"* header and profile shortcut.
    - Pill-shaped destination search bar with real-time reactive filtering across destination names, municipalities, and tags.
    - Adventure hero card with motivational travel copy.
    - Suggested & Custom planner entry cards with Figma badge and icon treatments.
    - Horizontal scroll carousel for **Popular Destinations** with snap alignment, real photography, and municipality pills.
    - Destination Detail Modal sheet with image hero, category badge, municipality, description, tags, and zero-cost *"Open in Google Maps"* external URL action.

### Changed
- Refactored `welcome.page.html` and `.scss` to replace generic placeholder icon with Figma hero illustration.
- Updated `Project/src/main.ts` import from `@ionic/angular/standalone` to `@ionic/angular`.
- Adjusted component SCSS budgets in `Project/angular.json` to 10kB warning / 16kB error to accommodate rich responsive styling.

---

## [0.3.0-alpha] - 2026-10-30
### Added
- **Argon2id Authentication Backend**:
  - `backend/app/schemas/auth.py`: Pydantic v2 schemas for registration, login, refresh tokens, Google OAuth, and profiles.
  - `backend/app/services/auth_service.py`: Password hashing with `pwdlib[argon2]`, 30-minute access JWTs, 7-day refresh JWTs, and Google ID token verification.
  - `backend/app/api/v1/auth.py`: REST endpoints `/register`, `/login`, `/refresh`, `/me`, `/oauth/google`, and `/oauth/apple`.
  - `backend/tests/test_auth.py`: Automated tests covering registration, duplicate collisions, wrong credentials, and bearer auth.
- **Mobile Client State & Services**:
  - `Project/src/app/core/services/guest-storage.service.ts`: Local storage driver using `@ionic/storage-angular` (`ne_guest_itineraries_v1`).
  - `Project/src/app/core/services/auth.service.ts`: Session management with reactive `currentUser$` and token storage.
  - `Project/src/app/core/interceptors/auth.interceptor.ts`: Token injection and host-offline graceful handling.
- **Figma-Aligned Screens**:
  - `WelcomePage` (`/welcome`): *"Trip mo, trip ko"* hero with `Log in`, `Sign up`, and `Continue as Guest`.
  - `LoginPage` (`/login`): Form, password toggle, Remember Me, Google button, truthfully disabled Apple button.
  - `SignupPage` (`/signup`): Name fields, username validation, email, password strength, matching-password confirmation validator.
  - `TabsPage` (4-tab shell): Home, Map, History placeholder (*"Planned for a later release"*), and Profile (account status / guest notice).
  - Design tokens in `theme/variables.scss` and `global.scss` with Inter typography and Travel Azure Blue (`#2563eb`).

### Changed
- Refactored Ionic component imports across all pages from `@ionic/angular/standalone` to `@ionic/angular` for Ionic 9 compatibility.
- Adjusted Angular component style budgets in `angular.json` to 6kB warning / 12kB error.

### Security
- Implemented Argon2id password hashing with high memory cost.
- Implemented case-insensitive normalization for usernames and emails to prevent identity impersonation.
- Gated Apple Sign-In behind `501 Not Implemented` and disabled UI state due to US\$99/year developer program requirement.

---

## [0.2.0-alpha] - 2026-10-30
### Added
- **Offline POI Pipeline & Seeding**:
  - `scripts/import_osm.py`: Overpass JSON importer with 16 canonical category mappings, bounding box check (`15.15 <= lat <= 16.15`, `120.70 <= lng <= 121.40`), and nearest municipality resolver.
  - `scripts/seed_featured_places.py`: Seeding script for 12 municipalities and 17 curated destinations (including Bongabon Day 1 stops and Pantabangan resorts).
  - `backend/app/api/v1/places.py`: REST endpoints for `/municipalities`, `/places`, and `/places/{id}` with comma-separated category filtering.
  - `backend/tests/test_foundation.py`: Automated test suite for health check, seeding idempotency, category filtering, and out-of-province POI rejection.

### Fixed
- Fixed category filtering in `places.py` to support comma-separated category strings (`?categories=cafe,restaurant`).
- Added fuzzy name normalization in `import_osm.py` to match "Muñoz" / "Munoz" / "Science City of Muñoz".
- Added `server_default=sa.func.now()` to timestamp columns in Alembic migration `0001_initial_nueva_ecija_schema.py`.

---

## [0.1.0-alpha] - 2026-10-30
### Added
- **Monorepo Foundation & Relational Schema**:
  - `.gitignore` and `.env.example` at repository root.
  - `backend/app/core/config.py`: Pydantic Settings loaded from `.env`.
  - `backend/app/core/database.py`: SQLAlchemy 2.0 engine, declarative base, and session dependency.
  - `backend/app/models/entities.py`: 7 core ORM models (`User`, `AuthIdentity`, `Municipality`, `Place`, `Itinerary`, `ItineraryDay`, `ItineraryItem`) with portable `JsonType` and `Uuid`.
  - `backend/alembic/`: Initial database migration `0001_initial_schema`.
  - `backend/app/main.py`: FastAPI application with CORS and `/health` route.

