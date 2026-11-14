# Known Issues & Technical Limitations

This document tracks identified bugs, intentional technical constraints, and temporary limitations across the application.

---

## 1. Intentional Architectural Constraints (By Design)

### 1.1 Apple Sign-In Disabled State
- **Status**: By Design / Gated.
- **Context**: Apple Sign-In requires an active Apple Developer Program membership (US\$99/year). Per the MVP zero-cost compliance matrix, this feature is gated behind `enableAppleAuth = false` in `environment.ts` and `.env`.
- **User Impact**: The Apple button is rendered disabled with a truthful caption: *"Apple Sign-In is disabled in this pilot build"*. Calling `POST /api/v1/auth/oauth/apple` returns `501 Not Implemented`.

### 1.2 History & Profile Tabs Implemented
- **Status**: Implemented & Verified (Completed in Milestone 8 & Phase 13).
- **Context**: In early MVP planning, History and Profile were planned as lightweight or deferred views. During Milestone 8 and Phase 13, both views were fully implemented:
  - `HistoryPage` (`history.page.html`): Full Saved Itineraries manager with trip cards, destination counts, budget summaries, and deletion with confirmation alert.
  - `ProfilePage` (`profile.page.html`): Account session manager displaying traveler status, unsynced trip notices in Guest Mode, and one-tap navigation to Log In and Create Account.
- **User Impact**: Fully functional across both Guest and Authenticated modes.

### 1.3 External Directions Hand-Off Instead of Live Transit
- **Status**: By Design / Policy Compliance.
- **Context**: The Figma design sketched a public-transit card with bus departures. However, public transit schedules for provincial routes (jeepneys, tricycles, provincial buses) lack real-time digital feeds. Building a mock transit router would present unverified schedules as fact.
- **Resolution**: Replaced with standard Google Maps directions URLs opening externally in the traveler's browser/maps app without API keys.

---

## 2. Environment & Host Limitations

### 2.1 Dual-Engine Architecture: PostgreSQL in Docker & SQLite Fallback
- **Status**: Operational & Verified on PostgreSQL (Container `ne_postgres` on Port 5432).
- **Context**: The primary production database runs on PostgreSQL 16 inside Docker (`ne_postgres`), populated with the full 2,673 OpenStreetMap + curated POI catalog. For local environments where Docker is not running, the application supports zero-config SQLite fallback.
- **Resolution**: The backend ORM entities and database session manager are architected with dual-engine compatibility (`JsonType`, `sa.Uuid`). Setting `DATABASE_URL=postgresql+psycopg://ne_travel_user:change_me_local_only@127.0.0.1:5432/nueva_ecija_travel` connects to Docker PostgreSQL. If Docker is unavailable, setting `DATABASE_URL=sqlite:///./nueva_ecija_travel.db` allows running locally without PostgreSQL. Automatic failover is also implemented in `scripts/start_server.ps1`.

---

## 3. Milestone Completion Status

All original core MVP milestones (Milestones 0 through 10) have been successfully built, integrated, and verified against the 24-point acceptance gate.

| Feature Area | Implementation Summary | Status |
| :--- | :--- | :---: |
| **Home Search Bar** | 300ms RxJS debounced search connecting to `GET /api/v1/places` with stale query cancellation. | **Completed** |
| **Popular Destinations** | Live horizontal carousel loading featured POIs via `PlaceService.getFeaturedPlaces()`. | **Completed** |
| **Interactive Leaflet Map** | Leaflet map bounded to Nueva Ecija, 16 category filter pills, MarkerCluster, and bottom sheet. | **Completed** |
| **Custom Itinerary Builder** | Multi-day creator with reordering, duplicate guards, place picker, and honest budget math. | **Completed** |
| **Suggested Itinerary Engine** | Deterministic Haversine clustering with preference weighting and offline fallback generator. | **Completed** |
| **Overview & Day View** | Day timeline view, stop details, and reactive cross-tab synchronization. | **Completed** |
| **Pilot Security & Acceptance** | SlowAPI rate limiting, host laptop offline banner, and 24/24 acceptance checks verified. | **Completed** |

---

## 4. Code Review Audit Findings & Remediation Status

An independent code review conducted on October 31, 2026 identified 16 findings across security, data integrity, core functionality, and code quality. Full analysis is documented in [CODE_REVIEW_AUDIT.md](file:///c:/Users/Edward/Desktop/CaseStudy/docs/CODE_REVIEW_AUDIT.md) and tracked in [TODO.md](file:///c:/Users/Edward/Desktop/CaseStudy/docs/TODO.md). All 16 findings have been remediated and verified across Phases 11–14:

### 4.1 Critical Severity (Remediated in Phase 11)
- **CR-001 (BOLA in Itinerary Reorder)**:
  - **Issue**: `POST /api/v1/itineraries/{id}/reorder` did not verify `item.day_id` belongs to `itinerary.days`.
  - **Resolution**: Scoped item query to `itinerary.days`; returns HTTP 400 Bad Request on foreign items with regression test.
  - **Status**: **Resolved & Verified (Phase 11)**.
- **CR-002 (BOLA / IDOR in Stop Deletion)**:
  - **Issue**: `DELETE /api/v1/itineraries/{id}/days/{day_id}/items/{item_id}` deleted item without scoping to `day_id` or `itinerary_id`.
  - **Resolution**: Added verification `day.itinerary_id == itinerary.id` and `item.day_id == day.id`; returns HTTP 404 with negative test.
  - **Status**: **Resolved & Verified (Phase 11)**.

### 4.2 High Severity (Remediated in Phases 11 & 12)
- **CR-003 (Silent Data Loss in Itinerary Edit Mode)**:
  - **Issue**: `CustomBuilderPage.saveItinerary()` in edit mode called `updateItinerary()` without `days`, dropping all days and stops.
  - **Resolution**: Extended backend `ItineraryUpdate` to accept `days`; updated builder, service, and PATCH endpoint to synchronize days/stops transactionally.
  - **Status**: **Resolved & Verified (Phase 11)**.
- **CR-004 (JWT Secret Fallback, OAuth Audience & CORS Scope)**:
  - **Issue**: Default JWT secret not blocked in non-dev environments; `google_oauth_client_id` allowed arbitrary token audiences; wildcard CORS regex.
  - **Resolution**: Added startup check rejecting default JWT secret; enforced `google_oauth_client_id` presence; tightened CORS to `https://edselrenz.github.io`.
  - **Status**: **Resolved & Verified (Phase 11)**.
- **CR-005 (Google OAuth Account Takeover & Deactivated User Bypass)**:
  - **Issue**: Google account linked by email without verifying `email_verified is True`; deactivated users could authenticate via Google OAuth.
  - **Resolution**: Enforced `payload.get("email_verified") is True`; added `user.is_active` check returning HTTP 403 on inactive accounts.
  - **Status**: **Resolved & Verified (Phase 11)**.
- **CR-006 (Missing Token Refresh & Silent Guest Downgrade)**:
  - **Issue**: Client never called `/auth/refresh`; 401 triggered silent downgrade to guest storage.
  - **Resolution**: Implemented token refresh queuing in `authInterceptor`; added `refreshSession()` and JWT expiration check; restricted guest fallback strictly to network outages.
  - **Status**: **Resolved & Verified (Phase 12)**.
- **CR-007 (Timezone Off-by-One Shifting in Date Parsing)**:
  - **Issue**: `new Date("YYYY-MM-DD")` UTC midnight parsing shifted dates in UTC+8 (Philippine Time).
  - **Resolution**: Created centralized date utilities (`Project/src/app/core/utils/date.utils.ts`) with unit test suite across timezones.
  - **Status**: **Resolved & Verified (Phase 12)**.

### 4.3 Medium Severity (Remediated in Phases 12 & 14)
- **CR-008 (Generator Ignores Dest Radius, Budget Flaws & Unescaped SQL)**:
  - **Issue**: `default_dest_radius_km` (25km) not enforced; budget filter checked cost per stop; SQL `.ilike()` did not escape `%`/`_`.
  - **Resolution**: Enforced 25km cluster radius; maintained cumulative daily budget tracker; added `escape_like()` helper.
  - **Status**: **Resolved & Verified (Phase 12)**.
- **CR-009 (Offline Suggested Generator Ignores Inputs & Hardcoded UI Chips)**:
  - **Issue**: Guests bypassed backend generator when online; offline generator ignored destination/preferences; wizard template had hardcoded chips.
  - **Resolution**: Connected online guests to `/api/v1/itineraries/suggest`; filtered curated pool by destination/preferences; dynamically bound wizard chips.
  - **Status**: **Resolved & Verified (Phase 12)**.
- **CR-010 (Missing Single-Stop PATCH, Sort Order Bug & Missing Place Check)**:
  - **Issue**: No PATCH endpoint for single stop; `add_itinerary_item` sort_order default bug; `create_itinerary` missing `place_id` foreign key check.
  - **Resolution**: Implemented `PATCH /days/{day_id}/items/{item_id}`; fixed sort_order auto-increment; added foreign key 404 validation.
  - **Status**: **Resolved & Verified (Phase 12)**.
- **CR-011 (Map Page Ignores Query Params, Tile Error & Bottom Sheet Honesty)**:
  - **Issue**: Route queryParams from Home tab ignored; no tileerror listener; bottom sheet lacked explicit "Not verified / Not provided" labels.
  - **Resolution**: Injected `ActivatedRoute` in `MapPage` to center on coordinates; added Leaflet tileerror banner; rendered honest pricing & provenance badges.
  - **Status**: **Resolved & Verified (Phase 12)**.
- **CR-012 (Unvalidated Custom API URL & Bearer Token Exfiltration Risk)**:
  - **Issue**: `ConnectivityService.setCustomApiUrl()` accepted unvalidated URLs; `authInterceptor` attached Bearer token without checking origin starts with `apiBaseUrl`.
  - **Resolution**: Validated URL protocol (`https://` or `http://localhost`); scoped Bearer token injection strictly to `environment.apiBaseUrl`.
  - **Status**: **Resolved & Verified (Phase 12)**.
- **CR-013 (Cloudflare Tunnel Rate Limiting, Generator Pre-Filtering & Seeding Optimization)**:
  - **Issue**: SlowAPI keyed on `127.0.0.1` for all tunnel users; `itinerary_generator` loaded all 4,400+ places into memory; N+1 queries in seeding; `pg_dump` lacked `--clean --if-exists`.
  - **Resolution**: Added `--clean --if-exists` to backup script; SlowAPI keys on `CF-Connecting-IP` / `X-Forwarded-For`; generator pre-filters candidates via SQL coordinate bounding box; seeding scripts batch lookups with `in_()`.
  - **Status**: **Resolved & Verified (Phases 12 & 14)**.

### 4.4 Low & Informational Severity (Remediated in Phases 13 & 14)
- **CR-014 (Outdated E2E Test, Dead Starter Code & Tautological Checks)**:
  - **Issue**: E2E spec tested for Tab 1; 16 dead starter files; 7 tautological checks in `verify_acceptance_gate.py`; destructive `setup_steps_0_to_2.py`.
  - **Resolution**: Deleted 16 dead starter files and destructive script; replaced 7 tautological checks with genuine assertions; rewrote `Project/e2e/app.spec.ts` with modern Playwright user journeys (`/welcome` -> `/guest` -> `/tabs/home` -> `/tabs/map` -> `/custom-builder`).
  - **Status**: **Resolved & Verified (Phases 13 & 14)**.
- **CR-015 (Profile Memory Leak, Non-Functional Buttons, Typos & Unused Images)**:
  - **Issue**: Unsubscribed observable in `ProfilePage`; non-functional buttons on login page; Bongabon-only nearby places; UI copy typos; 44 unused image files.
  - **Resolution**: Added `ngOnDestroy` unsubscription; parameterized `PlaceService.getNearbyPlaces()`; fixed copy typos; pruned 44 unused SHA-1 images.
  - **Status**: **Resolved & Verified (Phase 13)**.
- **CR-016 (Documentation Discrepancies)**:
  - **Issue**: Stale documentation showing completed milestones as pending.
  - **Resolution**: Synchronized complete documentation suite (`KNOWN_ISSUES.md`, `DEVELOPMENT_PLAN.md`, `DEVELOPMENT_LOG.md`, `CHANGELOG.md`, `PROJECT_STATE.md`, `TODO.md`, `TESTING_DOCUMENTATION.md`).
  - **Status**: **Resolved & Verified (Phases 13 & 14)**.

---

## 5. Technical Evaluation, QA & QC Audit Findings (November 2, 2026 — Commit `06cefc5`)

An independent Senior Software Engineering, QA & QC audit of the repository and live GitHub Pages deployment at commit `06cefc5` (v0.15.0-rc.6) was conducted on November 2, 2026 ([itinerary_app_technical_evaluation_report.pdf](file:///c:/Users/Edward/Desktop/CaseStudy/itinerary_app_technical_evaluation_report.pdf)). The audit established a final verdict of **NEEDS MINOR IMPROVEMENTS**, identifying 10 concrete defects and 3 security hardening recommendations tracked below:

### 5.1 Defects (DEF-01 through DEF-10)

| Defect ID | Severity | Module / Location | Defect Summary | Planned Remediation | Status |
| :--- | :---: | :--- | :--- | :--- | :---: |
| **DEF-01** | **HIGH** | `Project/src/app/features/auth/login/login.page.ts` (L131–138) & `backend/app/api/v1/auth.py` | Deceptive "Forgot Password?" toast displays success message with zero email validation and zero backend API call. | Validate email input and either connect to password reset API or display an honest pilot dialog indicating password recovery requires administrator assistance. | **RESOLVED** |
| **DEF-02** | **MEDIUM** | `login.page.ts` (L113–120), `signup.page.ts` (L158–165), `environment.prod.ts` (L23) | Google Sign-In and Sign-Up buttons are non-functional UI stubs displaying static toasts with a dummy client ID. | Connect Google Identity Services SDK to `POST /api/v1/auth/oauth/google`, or cleanly disable with a truthful pilot caption. | **RESOLVED** |
| **DEF-03** | **MEDIUM** | `backend/app/algorithms/itinerary_generator.py` & `itinerary.service.ts` (L586–999) | Non-chronological stop ordering in Suggested Wizard: Day 1 places overnight stay (22 hrs) before afternoon stops; Day 2 places 10:30 AM before 09:00 AM. | Add a post-selection chronological sort step by `planned_time`, placing overnight/accommodation venues at the end of each day. | **RESOLVED** |
| **DEF-04** | **MEDIUM** | `backend/app/api/v1/itineraries.py` (L365–413 vs L559–607) | Duplicate `@router.patch("/{itinerary_id}/days/{day_id}/items/{item_id}")` handler. Line 365 shadows Line 559, skipping `updated_at` updates. | Delete the first incomplete definition (Lines 365–413) and preserve the complete implementation (Lines 559–607). | **RESOLVED** |
| **DEF-05** | **MEDIUM** | `home.page.ts` (L10–227), `place.service.ts` (L41–403), `itinerary.service.ts` (L592–910) | Triple duplication of offline POI datasets across three frontend files with differing schemas and item counts. | Consolidate all static offline POI records and cluster presets into a single canonical `offline-places.data.ts` module. | **RESOLVED** |
| **DEF-06** | **LOW** | `Project/src/app/core/services/place.service.ts` (L557–607) | `getNearbyPlaces()` misclassifies cultural museum attraction Casa Batik under "Stores" due to broad fallback bucketing. | Filter strictly by retail/shopping category tags when populating the Stores category bucket. | **RESOLVED** |
| **DEF-07** | **LOW** | `docs/KNOWN_ISSUES.md` (Section 1.2) | Documentation parity: Stale text claiming History and Profile tabs are deferred placeholders. | Update `KNOWN_ISSUES.md` Section 1.2 to reflect full implementation of Saved Itineraries and Profile views. | **RESOLVED** |
| **DEF-08** | **LOW** | `Project/src/app/features/auth/login/login.page.ts` (L125) | Copy-paste toast typo in `onAppleLogin()` on login screen reads *"Apple Sign-Up is disabled..."* instead of Sign-In. | Update string to *"Apple Sign-In is disabled in this pilot build."*. | **RESOLVED** |
| **DEF-09** | **LOW** | `Project/src/app/app.component.html` (L49–83) & `map.page.ts` (L324–388) | Accessibility gaps: Splash overlay lacks `keydown.escape` listener and tabindex; Leaflet pins lack `role="button"` and `aria-label`. | Add `tabindex="0"`, `role="button"`, and `aria-label` to custom pins, and enable Escape key dismissal on splash screen. | **RESOLVED** |
| **DEF-10** | **LOW** | `.VSCodeCounter/2026-10-31_21-29-44/` & Git History | Tracked `.VSCodeCounter/` directory in Git version control instead of being ignored via `.gitignore`. | Add `.VSCodeCounter/` to `.gitignore` and untrack from Git index via `git rm -r --cached`. | **RESOLVED** |

---

### 5.2 Security Hardening Recommendations (SEC-01 through SEC-03)

| Security ID | Severity | Location | Risk & Impact | Planned Remediation | Status |
| :--- | :---: | :--- | :--- | :--- | :---: |
| **SEC-01** | **MEDIUM** | `Project/src/environments/environment.prod.ts` (L1–16) | Residual unallowlisted `ne_custom_api_url` in localStorage read by `environment.apiBaseUrl` could enable token exfiltration if arbitrary URLs are stored. | Restrict `resolveApiBaseUrl()` in `environment.prod.ts` to an explicit hostname allowlist (`localhost`, `127.0.0.1`, `anybody-cube-surprise.ngrok-free.dev`). | **RESOLVED** |
| **SEC-02** | **LOW** | `Project/src/app/core/services/auth.service.ts` (L135–147) | Long-lived refresh tokens stored in `window.localStorage` are accessible to JavaScript if an XSS flaw arises. | Plan migration to `HttpOnly; Secure; SameSite=Strict` cookies for web, or encrypted native keychain on Capacitor mobile (ADR-010). | **RESOLVED** |
| **SEC-03** | **LOW** | `backend/app/core/config.py` (L11–16) | Default development JWT secret fallback allows forged tokens if backend runs in production mode without `.env`. | Add a Pydantic `@model_validator` in `Settings` raising startup error if `app_env != "development"` and `jwt_secret_key` is default. | **RESOLVED** |

---

## 6. Live QA & Connectivity Observations (November 3, 2026)

### 6.1 Website QA & QC Findings (itinerary_app_website_qa_report.pdf)

| ID | Severity | Module / Location | Observation Summary | Remediation Applied | Status |
| :--- | :---: | :--- | :--- | :--- | :---: |
| **WQA-01** | **LOW** | `Project/src/app/features/auth/guest/guest.page.html` | Subtitle stated *"Your data won't be saved"* even though guest trips are persisted locally via Dexie IndexedDB. | Updated text to: *"Your trips are saved locally on this device. Sign in anytime to back them up to the cloud."* | **RESOLVED** |
| **WQA-02** | **LOW** | `Project/src/app/core/data/offline-places.data.ts` | Overlapping Day 2 time windows in suggested wizard (09:00–11:00 AM, 10:30 AM–12:00 PM, 11:30 AM–1:30 PM). | Rescheduled stops to clean non-overlapping slots: Stop 1: 09:00–10:30 AM; Stop 2: 11:00 AM–12:30 PM; Stop 3: 01:00–03:00 PM. | **RESOLVED** |
| **WQA-03** | **LOW** | `Project/src/app/tabs/tabs.page.html` & `tabs.page.ts` | Tab 3 used `time-outline` icon with ambiguous history context. | Changed icon to `bookmark-outline` and aria-label to `"Saved Itineraries"` for clarity and alignment with modern mobile design. | **RESOLVED** |

### 6.2 Pilot Backend Live Connectivity & Home Router DNS NXDOMAIN Caching

- **Problem Analysis**:
  - When the FastAPI backend runs on the developer laptop and exposes an ngrok tunnel (`anybody-cube-surprise.ngrok-free.dev`), certain residential Wi-Fi routers (e.g., Tenda, TP-Link, PLDT) drop IPv4 A queries or aggressively cache NXDOMAIN (Non-Existent Domain) responses from when the tunnel was inactive.
  - When users open the deployed GitHub Pages application (`https://edselrenz.github.io/Itinerary-App/`), the browser triggers a network error (`ERR_NAME_NOT_RESOLVED`), rendering the Offline Mode banner.
  - Clicking `[Retry]` or refreshing the page repeatedly pinged the same cached NXDOMAIN with no UI feedback and no fallback mechanism.
- **Root Cause**:
  1. Router DHCP DNS server (`192.168.5.1`) negative DNS caching for dynamic `.dev` TLDs.
  2. Frontend `environment.prod.ts` and `ConnectivityService.isValidApiUrl()` lacked Cloudflare Tunnel support (`*.trycloudflare.com`) and did not offer an interactive URL configuration UI.
  3. `scripts/start_server.ps1` previously exited with port conflict when port 8000 was already active.
- **Architectural Solution**:
  1. **Interactive In-App Server Connection Manager**:
     - Added a `[Settings]` gear button to the Offline Mode banner.
     - Enhanced `retryConnection()`: If reconnection succeeds, displays a green toast confirmation; if it fails, immediately opens an interactive Ionic Alert dialog displaying the unreachable host and an input field to enter or paste an active Cloudflare Tunnel (`https://*.trycloudflare.com`), ngrok URL, or localhost.
     - Validates candidate URLs against strict trusted hostname allowlist (`SEC-01`) before persisting to `localStorage.ne_custom_api_url`.
     - Provided a "Reset to Default" action to restore the default permanent tunnel.
  2. **Dual-Tunnel Startup Script (`scripts/start_server.ps1`)**:
     - Starts both ngrok (`anybody-cube-surprise.ngrok-free.dev`) and Cloudflare Quick Tunnel (`*.trycloudflare.com`) concurrently, outputting both URLs to the terminal.
     - Detects when port 8000 is already active without crashing or killing active tunnels.
  3. **Browser Secure DNS (DNS-over-HTTPS)**:
     - Documented one-click Secure DNS configuration for Chrome/Edge (Settings > Privacy and security > Use secure DNS > Choose 'Cloudflare' / 'Google') to bypass residential router DNS filtering.


---

## 7. Map & Routing System Production Audit Findings (November 6, 2026)

The following defect matrix was identified from the static code audit and live verification on `https://edselrenz.github.io/Itinerary-App/` documented in `itinerary_app_map_and_routing_proposal.pdf` (detailed in [MAP_AND_ROUTING_PROPOSAL.md](./MAP_AND_ROUTING_PROPOSAL.md)):

| Defect ID | Severity | Module / Location | Defect Description & Root Cause | Planned Engineering Remediation | Resolution Status |
| :--- | :---: | :--- | :--- | :--- | :---: |
| **MAP-01** | **CRITICAL** | `Project/src/app/tabs/map/map.page.ts` (L47–48, L137–139, L288–293, L422) | **Zero map pins render in production** due to static ES module import `import * as L from 'leaflet'; import 'leaflet.markercluster';` executing before `window.L` is attached, causing `L.markerClusterGroup` to fail or remain undefined in Angular esbuild production bundles. | Unwrap canonical Leaflet object via `const LeafletLib = (L as any).default ?? L; (window as any).L = LeafletLib;` at module top-level and add graceful fallback to `L.layerGroup()`. | **RESOLVED (Phase 27.1)** |
| **MAP-02** | **HIGH** | `Project/src/app/core/services/place.service.ts` (L119–149), `map.page.ts` (L340–416), `backend/app/api/v1/places.py` (L92–163) | **Truncated client-side filtering & ignored offline bounds**. Bounding box and featured flags ignored in offline fallback; online `MapPage` fetches 150 items globally and filters in memory, dropping matches beyond row 150. | Add `municipality_name` and `price_tier` parameters to backend `GET /places` in `places.py`, query SQL before LIMIT, and mirror filtering inside `PlaceService.getFallbackPaginatedPlaces()`. | **RESOLVED (Phase 27.1)** |
| **MAP-03** | **HIGH** | `map.page.ts` (L171–186, L320–329), `home.page.ts` (L229–230, L434–447) | **Deep-link pin selection skipped & fallback coordinates hardcoded**. When `lat`/`lng` query params are passed, `flyToDestinationOrMunicipality()` is bypassed, keeping `selectedPlace` null and bottom sheet closed; camera flight triggers `moveend` re-query. | Pass `placeId` in deep links, set `isProgrammaticFly = true` during `flyTo()` to suppress moveend overwrites, and auto-open `selectedPlace` bottom sheet. | **RESOLVED (Phase 27.1)** |
| **ROUTE-01** | **HIGH** | `itinerary-detail.page.ts`, `suggested-wizard.page.ts`, `custom-builder.page.ts` | **Zero in-app route polylines or multi-stop directions**. Itineraries render purely as text cards with no connected route map, no per-leg travel metrics, and external directions links that drop intermediate waypoints. | Build reusable `ItineraryRouteMapComponent` & `RoutingService` rendering numbered pins, OSRM polylines with geodesic spline fallback, leg metrics, and multi-stop Google Maps URLs (`&origin=...&destination=...&waypoints=...`). | **RESOLVED (Phase 27.2)** |
| **ROUTE-02** | **HIGH** | `offline-places.data.ts` (L446–482), `backend/app/algorithms/itinerary_generator.py` (L258–354) | **176.2 km cross-province zig-zag in offline presets & unoptimized stop order**. Day 2 (58.5 km) and Day 3 (116.2 km: Gen. Tinio $\rightarrow$ Pantabangan $\rightarrow$ Gapan) cross the province twice in a single afternoon. | Re-cluster offline presets into 3 corridors (East/Bongabon 1.5 km, North/San Jose–Pantabangan 13.8 km, South/Cabanatuan–Gen. Tinio–Gapan 45.5 km), cutting straight-line transit distance by 66.3% to 59.4 km. | **RESOLVED (Phase 27.1)** |
| **ROUTE-03** | **MEDIUM** | `itinerary-detail.page.ts` (L806–842), `suggested-wizard.page.ts` (L422–460) | **Fake Bongabon coordinates (15.63, 121.14) & unpersisted Nearby stops**. Adding a nearby place falls back to Bongabon coordinates for all towns and mutates `currentDay.items` in memory without saving to `ItineraryService`. | Ensure verified coordinates for `NearbyPlaceItem` and persist added stops via `this.itineraryService.updateItinerary()`. | **RESOLVED (Phase 27.1)** |
| **ROUTE-04** | **MEDIUM** | `app.routes.ts`, `itinerary-detail.page.ts` (L944), `map.page.ts` (L719) | **Guard gaps, hardcoded back navigation & non-GPS recenter button**. `/itinerary/:id` lacks `canDeactivate` guard; back buttons hardcode `/tabs/history`; map locate button only resets camera bounds rather than reading device GPS. | Attach `pendingChangesGuard` to `/itinerary/:id`, implement `IonRouterOutlet.canGoBack()` history back with fallback, and add true GPS Locate Me control. | **RESOLVED (Phase 27.3)** |
| **ROUTE-05** | **MEDIUM** | `commute-guide.data.ts` (L10–139) | **Static Cabanatuan-only commute guide for all legs**. Only 8 of 32 towns covered; every modal instructs travelers to depart from Cabanatuan Central Terminal even for 300m hops in Bongabon. | Build leg-aware `getLegCommuteInfo(prevStop, currentStop)`: local tricycles ($\le 1.2$ km), inter-town corridors, and coverage for all 32 municipalities. | **RESOLVED (Phase 27.3)** |


---

## 8. Saved Itinerary & Navigation UI/UX Evaluation Findings (November 6, 2026)

The following defect matrix was identified from the live end-to-end evaluation documented in `itinerary_app_ui_ux_evaluation_report.pdf` (detailed in [UI_UX_EVALUATION_REPORT.md](./UI_UX_EVALUATION_REPORT.md)):

| Defect ID | Severity | Module / Location | Defect Description & Root Cause | Planned Engineering Remediation | Resolution Status |
| :--- | :---: | :--- | :--- | :--- | :---: |
| **UIUX-01** | **HIGH** | `Project/src/app/features/itinerary/itinerary-detail/itinerary-detail.page.html` (L185–204) | **Post-save visual downgrade in Saved Itinerary Detail**. Stop photo thumbnails are completely stripped away upon saving, turning rich wizard preview cards into plain text boxes without photos. | Restore 68×68px stop thumbnail photos and step numbering badges on `.activity-view-card` in `itinerary-detail.page.html`. | **RESOLVED (Phase 28.1)** |
| **UIUX-02** | **HIGH** | `itinerary-detail.page.ts` (L565–595) | **Hardcoded `?? 200` cost fallback violating honest budget accounting (ADR-001)**. `getStopEstimatedCost()` returns `'200'` for null costs and `calculateTotalActivityExpenses()` adds ₱200 for unpriced venues, inflating the bottom total card by ₱600 and contradicting the top Verified Estimated Costs banner (`₱3,449 - ₱8,349 (+ 3 unpriced)`). | Eliminate `?? 200` fallbacks; delegate directly to `this.budgetSummary` and display *Fee not listed* on unpriced stop cards. | **RESOLVED (Phase 28.1)** |
| **UIUX-03** | **HIGH** | `itinerary-detail.page.ts` (L547–555) | **Destructive regex in `formatTimingHour()`**. `formatTimingHour()` executes `.match(/(\d{1,2}:\d{2})/)`, stripping AM/PM and end times down to bare `"12:00"` (and returning `"22 hours"` on overnight stays). | Bind `getTimingTime(stop, sIdx)` in `itinerary-detail.page.html` to display full start-end time windows and duration. | **RESOLVED (Phase 28.1)** |
| **UIUX-04** | **MEDIUM** | `itinerary-detail.page.html` (L569–594) & `itinerary-detail.page.ts` (L938) | **Orphaned Share & Export Modal**. The complete modal markup and export functions (`exportIcs`, `copySummary`, `shareNative`, `printPdf`) are implemented, but zero buttons in `itinerary-detail.page.html` call `openShareModal()`. | Add a visible Share action button (`share-social-outline`) in the header toolbar wired to `openShareModal()`. | **RESOLVED (Phase 28.1)** |
| **UIUX-05** | **MEDIUM** | `itinerary-detail.page.html` (L83–115) & `itinerary-detail.page.ts` (L609) | **Orphaned Nearby Essentials View**. `@if (viewMode === 'nearby')` is implemented at lines 83–115, but zero buttons in the HTML call `openNearbyPlaces()`, leaving it as unreachable dead code. | Restore the interactive dashed *Nearby Places in {{ getDayLocation(day) }}* trigger banner inside each day card. | **RESOLVED (Phase 28.1)** |
| **UIUX-06** | **MEDIUM** | `itinerary-detail.page.html` (L1–15) | **Stacked double header chrome & false affordances**. Two headers are stacked on top of each other: `Saved Itineraries [+]` above `← Trip Title [Edit]`. Tapping `[+]` abruptly navigates away to Custom Builder, and a non-clickable right arrow (`→`) sits in the footer. | Unify into a single clean header toolbar (`← Trip Title | [Share] [Edit]`) and remove the dead `→` icon. | **RESOLVED (Phase 28.1)** |
| **UIUX-07** | **MEDIUM** | `itinerary-detail.page.html` (L120–135) & `itinerary-detail.page.ts` (L645) | **Raw ISO date strings in Saved Trip Details**. Trip dates render as raw unformatted strings (`2026-11-06 2026-11-08`) despite `formattedDateSpan` being available in TypeScript. | Bind `formattedDateSpan` in `itinerary-detail.page.html` to display human-readable formatted dates (`Nov 6 – Nov 8, 2026 (3 Days, 2 Nights)`). | **RESOLVED (Phase 28.1)** |
| **UIUX-08** | **HIGH** | `itinerary-export.util.ts` & `itinerary-detail.page.html` | **High-friction single-stop navigation (8 taps for 4 stops)**. Stop modals only open single-stop navigation links (`?api=1&destination=lat,lng`), losing the rest of the day's itinerary. | Implement `buildGoogleMapsDayRouteUrl(items)` in `itinerary-export.util.ts` and add a "Start Day Route in Google Maps" multi-stop action button. | **RESOLVED (Phase 28.2)** |
| **UIUX-09** | **MEDIUM** | `itinerary-detail.page.html` (L230–245) | **Missing segmented day switching in Saved Itinerary Detail**. All days are dumped into one long vertical scroll while `selectDay()` in TypeScript is unused. | Implement a sticky segmented day switcher capsule bar synchronized with the active day's timeline cards. | **RESOLVED (Phase 28.2)** |
| **UIUX-10** | **LOW** | `itinerary-detail.page.html` (L149, L160) | **Hidden budget and assumptions cards on custom itineraries**. `[class.hidden-on-custom]="itinerary.type !== 'suggested'"` hides the budget card and assumptions on custom trips. | Allow custom itineraries with budget entries to display the verified budget card and editable assumptions. | **RESOLVED (Phase 28.2)** |
| **UIUX-11** | **LOW** | `place-detail-sheet.component.html & .ts` | **Missing WCAG 2.2 accessible focus-ring on close button & stop price parity**. Place detail sheet close button lacked focus-visible styling and did not reflect custom stop prices. | Forward `estimated_cost_min/max` and add `:focus-visible` focus ring styles. | **RESOLVED (Phase 28.3)** |


---

## 9. Custom & Suggested Itinerary Workflow Findings (November 6, 2026)

The following defect matrix was identified from the static code audit and live verification documented in `custom_and_suggested_itinerary_proposal.pdf` (detailed in [CUSTOM_AND_SUGGESTED_ITINERARY_PROPOSAL.md](./CUSTOM_AND_SUGGESTED_ITINERARY_PROPOSAL.md)):

| Defect ID | Severity | Module / Location | Defect Description & Root Cause | Planned Engineering Remediation | Resolution Status |
| :--- | :---: | :--- | :--- | :--- | :---: |
| **C-BUG-06** | **CRITICAL** | `Project/src/app/features/itinerary/custom-builder/custom-builder.page.ts` (L806–826, L1114–1126), `itinerary.service.ts` (L421–435) | **Metadata loss when saving Custom Itineraries in Guest/Offline mode**. `addPlaceStop()` and `saveItinerary()` omit `custom_title: it.name` and `place` from the save payload. When saved via `GuestStorageService`, `place: null` and `custom_title: undefined` are persisted, causing saved stops to render as generic *"Destination Stop"* with zero coordinates and fabricated ₱200 fee. | Retain full `place: Place` reference on `BuilderStop`, serialize `place` object and `custom_title: it.name`, and hydrate stops with `place_id` against `PlaceService` in `ItineraryService.mapGuestItinerary()`. | **RESOLVED (Phase 29.1)** |
| **S-BUG-03** | **CRITICAL** | `Project/src/app/core/services/itinerary.service.ts` (L753–796) | **Dead `matchedPool` variable in offline suggested generator**. `generateOfflineSuggestedItinerary()` filters and sorts `matchedPool` by municipality and preferences on lines 753–771, but never reads `matchedPool` afterwards. Selecting non-Bongabon towns falls back to `curatedPool[0..2]`, repeating the same 3 Bongabon stops on every single day. | Wire `matchedPool` directly to `dayPlaces`, slicing 3 stops per day without replacement, filtered by cumulative `daily_budget` and Haversine proximity. | **RESOLVED (Phase 29.1)** |
| **S-BUG-04** | **HIGH** | `itinerary.service.ts` (L720–740) | **Unconditional 4s HTTP timeout stall in offline suggested generation**. Even when `ConnectivityService.isHostOffline$` is already true, `suggestItinerary()` fires an HTTP POST and waits 4,000 ms before falling back to local generation. | Inject `ConnectivityService`; if `isHostOfflineSnapshot` or `!navigator.onLine`, invoke `generateOfflineSuggestedItinerary()` in 0ms without network timeout. | **RESOLVED (Phase 29.1)** |
| **C-BUG-01** | **HIGH** | `custom-builder.page.html` (L48–137) | **Missing Trip Title input & quick chips on Step 1**. Step 1 omits Trip Title input (defaults silently to "Nueva Ecija Getaway") and quick destination/budget preset chips; primary button is mislabeled *"Find Itinerary"*. | Add Trip Title input and reusable Quick Destination & Budget preset chips to Step 1; rename CTA button to *"Start Building Itinerary →"*. | **RESOLVED (Phase 29.2)** |
| **C-BUG-02** | **HIGH** | `custom-builder.page.ts` (L697) | **Incomplete category mapping in `catMap`**. `catMap` maps only 9 of the 16 canonical POI categories, dropping 7 categories completely (including transport terminals, hospitals, pharmacies, fuel stations). | Expand `catMap` to cover all 16 canonical categories: All, Attractions & Nature, Food & Cafes, Resorts & Stays, Culture & Heritage, Shopping & Markets, and Transit & Essentials. | **RESOLVED (Phase 29.2)** |
| **C-BUG-05** | **HIGH** | `custom-builder.page.ts` | **Timeline date range desynchronization**. Changing `start_date` / `end_date` in Step 3 settings card does not resize `this.days` array or update `day.travel_date`. | Implement reactive `syncDaysWithDateRange()` that updates `day.travel_date` and appends/trims days while preserving existing stops. | **RESOLVED (Phase 29.2)** |
| **S-BUG-01** | **MEDIUM** | `suggested-wizard.page.ts` (L171) | **Ignored `placeId` in deep link**. `suggested-wizard.page.ts` reads `params['destination']` but ignores `params['placeId']`, never anchoring the user's selected POI into Day 1. | Add `anchor_place_id` to suggested itinerary request and lock that POI as Stop 1 of Day 1. | **RESOLVED (Phase 29.1)** |
| **S-BUG-02** | **MEDIUM** | `suggested-wizard.page.ts` (L190, L207) | **Timezone date shifts in suggested date modal**. Uses UTC `new Date(str).toISOString()` instead of `parseLocalIsoDate()`, risking off-by-one shifts in UTC+8. | Enforce `parseLocalIsoDate()` and `toLocalIsoDate()` across all date picker and preset handlers. | **RESOLVED (Phase 29.1)** |
| **S-BUG-05** | **MEDIUM** | `suggested-wizard.page.ts` (L422) | **Hardcoded nearby place append**. Hardcodes 12:00 PM, Bongabon coordinates `(15.63, 121.14)`, and null cost, appending after overnight stays without re-sorting. | Use actual venue coordinates, insert in chronological order before overnight stay, and calculate timing window. | **STAGED (Phase 29.3)** |
| **S-BUG-06** | **MEDIUM** | `suggested-wizard.page.ts` (L475–555) | **Premature persistence on "Customize in Builder"**. `customizeInBuilder()` writes a permanent copy to storage *before* opening the builder; cancelling leaves an unwanted duplicate saved trip. | Pass draft itinerary via in-memory router state (`{ state: { draftItinerary: this.generatedPlan } }`) and persist only when the user explicitly clicks Save. | **RESOLVED (Phase 29.3)** |
| **C-BUG-03** | **MEDIUM** | `custom-builder.page.ts` | **Ignored Step 1 destination context in Browse view**. Step 2 browse grid ignores the destination chosen in Step 1 and collapses multi-preferences into a single tab. | Initialize browse view filter with Step 1's chosen destination and multi-preference categories. | **RESOLVED (Phase 29.2)** |
| **C-BUG-04** | **LOW** | `custom-builder.page.ts` | **Inability to inspect destination in Browse mode**. Tapping destination cards in Browse view does nothing; travelers cannot view descriptions, hours, or commute info. | Make card body clickable to open `<app-place-detail-sheet>` with an inline "+ Add to Day {{ activeDayNumber }}" button. | **RESOLVED (Phase 29.3)** |
| **UC-C5** | **MEDIUM** | `itinerary-detail.page.html` (L29–36), `itinerary-detail.page.ts` | **Mismatched dual saved trip editors & min/max cost collapsing**. Clicking Edit on saved trips opened raw text editor instead of full visual builder, and collapsed min/max cost ranges to single value. | Direct header Edit button to `/custom-builder/:id` and preserve separate `estimated_cost_min` and `estimated_cost_max` across all editor interfaces. | **RESOLVED (Phase 29.3)** |
| **POST-SAVE** | **LOW** | `custom-builder.page.ts` (L1277) | **Disorienting home exit on save & un-timed stops**. Saving a custom trip navigated abruptly to `/tabs/home` and added stops without start/end times. | Redirect post-save to `/itinerary/:id` and auto-chain sequential stop time windows with 30-min transit buffers (`autoOptimizeDaySchedule()`). | **RESOLVED (Phase 29.3)** |

---

## 10. Live Server Map & Suggested Itinerary Findings (November 7, 2026)

The following defect matrix was audited on the live server (`https://edselrenz.github.io/Itinerary-App/tabs/home`) and documented in `live_server_map_and_suggested_itinerary_proposal.pdf` (detailed in [LIVE_SERVER_MAP_AND_SUGGESTED_ITINERARY_PROPOSAL.md](./LIVE_SERVER_MAP_AND_SUGGESTED_ITINERARY_PROPOSAL.md)):

| Defect ID | Severity | Module / Location | Defect Description & Root Cause | Planned Engineering Remediation | Resolution Status |
| :--- | :---: | :--- | :--- | :--- | :---: |
| **GAP-01** | **HIGH** | `suggested-wizard.page.html`<br>`itinerary-route-map.component.ts`<br>`itinerary_generator.py` | **Straight-Line Euclidean Route Preview & Lack of Per-Leg Travel Times**. The Day 1 Route preview map connects stops with straight lines instead of road-following paths, and provides zero distance (km), drive time, or tricycle fare indicators between stops. | Implement `enrich_day_route_legs()` in `itinerary_generator.py` with arterial road circuity factor (`straight_km * 1.28`), and render road-following polyline with per-leg connector pills (`🚗 5.2 km • ~11 mins drive / 18 mins tricycle • Est. Fare ₱50–₱80`). | **RESOLVED (Phase 30.3)** |
| **GAP-02** | **HIGH** | `Project/src/app/tabs/map/map.page.ts`<br>`map.page.html` | **Full Map Handoff Visual Overload & Missing Route Focus Mode**. Navigating to `/tabs/map?followRoute=true` keeps all 2,673 POIs and cluster badges active, drowning the user's 3 itinerary stops in the 520-pin Cabanatuan cluster without a dedicated back action. | Implement `isFollowRouteMode`: hide the 2,673 background clusters by default, render a floating Active Route Control Bar (`← Back to Plan`, `Day 1 \| Day 2`, `Show Nearby POIs`), and add a bottom route card carousel. | **RESOLVED (Phase 30.2)** |
| **GAP-03** | **MEDIUM-HIGH** | `suggested-wizard.page.ts`<br>`itinerary.service.ts`<br>`map.page.ts` | **Pre-Save Draft Loss on Full Map Inspection**. Clicking "Full Map" before clicking "Save Itinerary" resets the wizard back to blank Step 1 upon return because the unsaved plan is stored only in component memory. | Cache `activeDraftItinerary$` in `ItineraryService` memory / `sessionStorage` so navigating back from `/tabs/map` to `/suggested-wizard` restores the unsaved generated plan. | **RESOLVED (Phase 30.2)** |
| **GAP-04** | **MEDIUM-HIGH** | `Project/src/app/tabs/map/map.page.ts` (L431–436)<br>`connectivity.service.ts`<br>`connectivity.interceptor.ts` | **False-Positive Offline Mode Banner on Map Tab**. A single aborted tile or secondary health check timeout during the 2,673-POI batch hydration latches `hasTileError = true` and `isOffline$ = true` without resetting when `GET /api/v1/health` or subsequent tile loads succeed. | Auto-clear `hasTileError = false` on `tileload`; ensure successful health checks or cached responses reconcile `isOffline$ = false` when the backend is reachable. | **RESOLVED (Phase 30.1)** |
| **GAP-05** | **MEDIUM** | `suggested-wizard.page.ts`<br>`itinerary-route-map.component.ts`<br>`itinerary-detail.page.ts` | **One-Way Preview Map & Stop Card Interaction**. Tapping a stop card does not highlight or pan to its numbered pin on the preview map, and clicking a map pin does not scroll to or open its stop card. | Implement reactive `selectedStopIndex: number \| null` bi-directional binding between stop cards and map markers. | **RESOLVED (Phase 30.3)** |

---

## 11. Live Server Audit: Suggested & Custom Itinerary Preference Engine & Autofill Defects (Phase 31)

The following defect matrix was audited on the live server (`https://edselrenz.github.io/Itinerary-App/tabs/home`) and documented in `suggested_and_custom_itinerary_live_evaluation.pdf` (detailed in [SUGGESTED_AND_CUSTOM_ITINERARY_LIVE_EVALUATION.md](./SUGGESTED_AND_CUSTOM_ITINERARY_LIVE_EVALUATION.md)):

| Defect ID | Severity | Module / Location | Defect Description & Root Cause | Planned Engineering Remediation | Resolution Status |
| :--- | :---: | :--- | :--- | :--- | :---: |
| **PREF-01** | **CRITICAL** | `itinerary.service.ts` (L346, 360)<br>`itinerary_generator.py` (L321, 507) | **Premature 4s Timeout Fallback**. `suggestItinerary()` sets `timeout(4000)` while sending `include_live_places: true`. Multi-day requests exceed 4s and silently abort into client-side heuristic generation. | Increase timeout to 10s (`timeout(10000)`); default `include_live_places = False` in generator when local database has $\ge 15$ candidates. | **RESOLVED (Phase 31.2)** |
| **PREF-02** | **CRITICAL** | `itinerary.service.ts` (L933–942) | **Broken Substring Category Matching**. Substring check `a.categoryKey.toLowerCase().includes(pr)` fails for restaurants/cafes (`restaurant`, `cafe` do not contain `food`) and churches (`church_religious` does not contain `culture`). | Implement canonical `PREFERENCE_CATEGORY_MAP` mapping preferences to arrays of actual venue category keys. | **RESOLVED (Phase 31.2)** |
| **PREF-03** | **CRITICAL** | `itinerary.service.ts` (L914–950)<br>`itinerary_generator.py` (L215–236) | **Soft Additive Scoring Without Day 1 Category Gate**. With only 6 curated places in Pantabangan, non-matching dining/resort places remain in top 3 even when the user selects Nature & Parks only. | Enforce strict category filtering for Day 1 activity slots within an expanding geographic radius ($15 \to 30 \to 45$ km). | **RESOLVED (Phase 31.2)** |
| **PREF-04** | **CRITICAL** | `itinerary.service.ts` (L865, 1038–1043, 1086) | **Hardcoded 10:00 AM Collisions & Backwards Chronology**. Every OSM place is hardcoded to `10:00 AM - 12:00 PM`. At line 1086, `isOvernightItem()` moves Highland Bali to Stop 3 while retaining 10:00 AM, creating backwards chronology after 1:00 PM. | Implement sequential non-overlapping time slot windows (`09:30 AM`, `12:00 PM`, `03:00 PM`) calculating real inter-stop travel duration. | **RESOLVED (Phase 31.2)** |
| **PREF-05** | **HIGH** | `itinerary.service.ts` (L987–993)<br>`osm_places.json` | **Unrealistic Pacing / 3 Mountain Hikes Per Day**. Selecting Nature & Parks schedules 3 consecutive raw mountain peaks per day with zero dining stops or breaks. | Tag mountain peaks (`isMountainPeak`) as high-exertion (max 1 hike/day) and add a lightweight Smart Dining toggle scheduling a midday lunch (`12:00 PM – 01:30 PM`). | **RESOLVED (Phase 31.2)** |
| **PREF-06** | **HIGH** | `itinerary.service.ts` (L996–998)<br>`itinerary_generator.py` (L376–382) | **Cross-Day Duplicate Venues**. Recycles already-used places when `candidates < 3`. Deduplication only checks `place.id` rather than normalized venue name or $< 200$m distance check. | Implement `normalizeVenueName()` and coordinate proximity check ($< 200$m) to eliminate cross-day venue repetition. | **RESOLVED (Phase 31.2)** |
| **CUST-01** | **HIGH** | `custom-builder.page.ts` (L551–564, 928–960) | **Culture & Resort Mapped to Broken Category**. Selecting culture or resort in Step 1 sets `selectedCategory = 'Tourist Spots'`, hiding all museums, churches, and resorts in Step 2. | Map culture to 'Culture & Heritage' and resort to 'Resorts & Stays', or provide a unified `Recommended for You` tab. | **RESOLVED (Phase 31.3)** |
| **CUST-02** | **HIGH** | `custom-builder.page.ts` (L865–879) | **Step 2 Default Loads Only 17 Featured Places**. `loadBrowsePlaces()` calls `getFeaturedPlaces(50)`, loading only 17 places instead of querying the user's chosen town across the 2,673 POI catalog. | Query `searchPlaces({ municipality_name: dest, limit: 100 })` pre-loading all local POIs for the selected destination. | **RESOLVED (Phase 31.3)** |
| **CUST-03** | **MEDIUM** | `custom-builder.page.ts` (L1165–1195) | **Timeline Auto-Schedule 0-Minute Transit**. Auto-Schedule sets `end_time_1 == start_time_2` with 0 minutes transit between venues 10–25 km apart. | Add realistic driving/transit buffer based on inter-stop distance in `autoOptimizeDaySchedule()`. | **RESOLVED (Phase 31.3)** |

---

## 12. Full-Website QA Audit Findings & Remediation Matrix (November 7, 2026 — `full_website_qa_audit_and_proposal.pdf`)

A full-system QA audit was conducted on November 7, 2026 across 64 test cases and 8 modules ([full_website_qa_audit_and_proposal.pdf](file:///c:/Users/Edward/Desktop/CaseStudy/full_website_qa_audit_and_proposal.pdf) and [FULL_WEBSITE_QA_AUDIT_AND_PROPOSAL.md](./FULL_WEBSITE_QA_AUDIT_AND_PROPOSAL.md)).

Because the audit evaluated commit `81fcc8d7`, several high-severity items were already remediated in Phase 31 and Session 87. The remaining active items are structured under **Phase 32**.

| Defect ID | Severity | Module / Location | Defect Description & Root Cause | Planned Engineering Remediation | Resolution Status |
| :--- | :---: | :--- | :--- | :--- | :---: |
| **QA-01** | **P0 (CRITICAL)** | `connectivity.service.ts`<br>`auth.interceptor.ts` | **False-Positive Offline Banner on Map Tab**. A single failed or rate-limited API call in `auth.interceptor.ts:52–66` flipped `isHostOfflineSubject.next(true)` globally even while 2,673 POIs remained cached and functional. | Implemented a 2-consecutive-error threshold (status 0, 502, 503, 504) and asynchronous `checkHostHealth()` probe before latching offline banner. | **RESOLVED (Phase 32.1)** |
| **QA-02** | **P1 (HIGH)** | `place.service.ts`<br>`map.page.ts` | **Viewport Bounding-Box POI Truncation on Pan/Zoom Online**. Live query returned paginated subset (`limit=100`), replacing in-memory 2,673 POIs with only the returned subset on map movement. | In `PlaceService.searchPlaces()`, merged online API responses into `osmPlacesCache` by ID; preserved marker clusters via `allLoadedPlaces` in `MapPage.loadPlaces()`. | **RESOLVED (Phase 32.1)** |
| **QA-03** | **P0 (CRITICAL)** | `suggested-wizard.page.html`<br>`custom-builder.page.html` | **No Destination Search Autofill / Typo Sensitivity**. Destination inputs required exact text matching without autocomplete, diacritic stripping, or LGU grouping. | Built standalone `<app-destination-autocomplete>` indexing all 32 LGUs + landmarks with fuzzy search, district grouping, and `🗺️ All 32 Towns` browse modal. | **RESOLVED (Phase 31.1)** |
| **QA-04** | **P0 (CRITICAL)** | `itinerary.service.ts`<br>`suggested-wizard.page.ts` | **Non-Chronological / Overlapping Time Windows & 10:00 AM Collisions**. Every OSM place hardcoded to 10:00 AM; overnight lodging placed non-chronologically. | Implemented sequential non-overlapping time windows (`09:30 AM`, `12:00 PM`, `03:00 PM`) and chronological sorting placing overnight stops last. | **RESOLVED (Phase 31.2)** |
| **QA-05** | **P0 (CRITICAL)** | `itinerary.service.ts`<br>`itinerary_generator.py` | **Broken Category Filtering, Duplicate Stops & Unrealistic Hikes**. Broken substring matching; 3 consecutive mountain hikes scheduled per day; cross-day stop repetition. | Canonical `PREFERENCE_CATEGORY_MAP`, Smart Midday Lunch Anchor, Activity Intensity Guard (max 1 hike/day), and fuzzy deduplication (<200m). | **RESOLVED (Phase 31.2)** |
| **QA-06** | **P1 (HIGH)** | `custom-builder.page.ts` | **Custom Builder Step 1 Category Masking**. Selecting Culture or Resort mapped to 'Tourist Spots', hiding venues in Step 2. | Mapped Culture to 'Culture & Heritage' and Resort to 'Resorts & Stays', plus added `'✨ Recommended for You'` unified multi-preference tab. | **RESOLVED (Phase 31.3)** |
| **QA-07** | **P1 (HIGH)** | `custom-builder.page.ts` | **Custom Builder Step 2 Truncated 17-Place Limit**. Browse view called `getFeaturedPlaces(50)`, loading only 17 places instead of querying the full 2,673 POI catalog. | Updated `loadBrowsePlaces()` to query `searchPlaces({ municipality_name: dest, limit: 100 })` pre-loading all local POIs for the selected destination. | **RESOLVED (Phase 31.3)** |
| **QA-08** | **P2 (MEDIUM)** | `connectivity.service.ts`<br>`place.service.ts`<br>`itinerary.service.ts`<br>`auth.service.ts` | **Unwired Custom API URL in HTTP Interceptors**. `ConnectivityService.setCustomApiUrl()` writes `localStorage.getItem('ne_custom_api_url')`, but services read static `environment.apiBaseUrl`. | Implemented dynamic `activeApiBaseUrl` getter in `ConnectivityService` and injected across all HTTP services and interceptors. | **RESOLVED (Phase 32.1)** |
| **QA-09** | **P2 (MEDIUM)** | `login.page.ts` | **Simulated Password Recovery & Duplicate Toast**. `onForgotPassword()` opened the recovery modal AND simultaneously displayed a warning toast claiming self-service reset was disabled. | Removed redundant warning toast from `onForgotPassword()` so modal opens cleanly without conflicting feedback. | **RESOLVED (Phase 32.2)** |
| **QA-10** | **P2 (MEDIUM)** | `home.page.html`<br>`home.page.ts` | **Home Destination Detail Modal Uses Legacy Inline Markup**. `home.page.html` maintained a separate legacy `<ion-modal>` with only 7 hardcoded chips instead of modern `<app-place-detail-sheet>`. | Refactored `home.page.html` to reuse the shared standalone `<app-place-detail-sheet [place]="selectedPlace">`. | **RESOLVED (Phase 32.2)** |
| **QA-11** | **P2 (MEDIUM)** | `itinerary-route-map.component.ts`<br>`osm-overpass.service.ts` | **Direct Browser Calls to Public OSRM & Overpass**. Client calls `router.project-osrm.org` and `overpass-api.de` directly, risking rate limits and Mixed Content blocks. | Added defensive polyline fallback with circuit breaker, and route OSM requests through backend `geospatial_cache` proxy. | **RESOLVED (Phase 32.2)** |
| **QA-12** | **P1 (HIGH)** | `itinerary.service.ts`<br>`itinerary_generator.py` | **Premature 4s Network Timeout on Suggested Generator**. `suggestItinerary()` set `timeout(4000)`, causing multi-day requests to abort into client heuristics. | Increased HTTP timeout to 10s (`timeout(10000)`) and decoupled fast-path discovery in backend generator. | **RESOLVED (Phase 31.2)** |
| **QA-13** | **P1 (HIGH)** | `custom-builder.page.ts` | **Timeline Auto-Schedule Ignores Inter-Stop Transit**. Auto-Schedule set `end_time_1 == start_time_2` (0-min transit) between stops kilometers apart. | Added dynamic Haversine distance-based transit buffer calculation in `autoOptimizeDaySchedule()`. | **RESOLVED (Phase 31.3)** |
| **QA-14A** | **P2 (MEDIUM)** | `itinerary-detail.page.ts` | **Duplicate Leaflet Map Instance in ItineraryDetailPage**. Legacy `previewMap` lifecycle, variables, and methods remained active alongside `ItineraryRouteMapComponent`. | Deleted legacy `previewMap`, `initPreviewMap()`, `updatePreviewMap()`, and `previewMapElementRef` to eliminate redundant DOM resize timers. | **RESOLVED (Phase 32.2)** |
| **QA-14B** | **P2 (MEDIUM)** | `itinerary-detail.page.ts` | **UTC toISOString() Day Shift in addDay()**. `new Date(lastDate).toISOString().split('T')[0]` risked shifting dates in UTC+8. | Replaced with `toLocalIsoDate(addDaysLocal(parseLocalIsoDate(lastDate), 1))` from `date.utils.ts`. | **RESOLVED (Phase 32.2)** |
| **QA-14C** | **P2 (MEDIUM)** | `app.component.ts`<br>`suggested-wizard.page.ts`<br>`custom-builder.page.ts` | **App Boot Theme & Default Budget Hydration**. `ne_theme_mode` not restored to `document.body` on startup; `ne_default_budget` not read by wizards. | Checked `localStorage.getItem('ne_theme_mode') === 'dark'` on boot in `AppComponent`; initialized `daily_budget` from `localStorage.getItem('ne_default_budget') || 3000`. | **RESOLVED (Phase 32.2)** |
| **MAP-TAB** | **P0 (CRITICAL)** | `map.page.ts`<br>`tabs.page.ts`<br>`itinerary-detail.page.ts` | **Persistent In-App Route Navigation on Map Tab Switch**. Tapping Map bottom tab retained route tracking HUD, polyline, and hid 2,673 discovery POIs. | Implemented `exitFollowRouteModeCleanly()`, `ionViewWillEnter()` teardown, `(click)="onMapTabClicked()"` query param reset, "Browse Map" action button, and GPS tracking stop on `onBack()`. | **RESOLVED (Session 87)** |

---

## 13. Exhaustive QA/QC Audit Findings & Defect Resolution Matrix (`itinerary_app_exhaustive_qa_qc_report.pdf`)

A 57-page exhaustive QA/QC audit was conducted across 75 test cases (TC-001 through TC-075) and 12 modules (`MOD-01` through `MOD-12`).

Because the audit was performed against Commit `81fcc8d7` (Phase 30 baseline), 12 of the 14 reported defects (`BUG-01` through `BUG-10`, `BUG-12`, and `BUG-13`) were resolved and verified in Phases 30, 31, and 32. The remaining defects are structured under **Phase 33**.

| Defect ID | Severity | Module / Location | Defect Description & Root Cause | Planned Engineering Remediation / Task ID | Resolution Status |
| :--- | :---: | :--- | :--- | :--- | :---: |
| **BUG-01** | **P0 (CRITICAL)** | `MOD-10` / TC-067<br>`connectivity.service.ts` | **Connectivity Banner Infinite Offline Retry Loop**. When backend is unreachable, app enters infinite retry loop triggering continuous failure toasts. | **TASK-01**: Implement consecutive error threshold ($\ge 2$) and async host health reconciliation. | **RESOLVED (Phase 32.1)** |
| **BUG-02** | **P0 (CRITICAL)** | `MOD-05` / TC-032, TC-034<br>`suggested-wizard.page.html` | **Destination Input Lacks Autocomplete & Wrapped Chips**. Destination input accepts arbitrary text without LGU validation; quick-select chips clipped horizontally. | **TASK-02**: Build `<app-destination-autocomplete>` combobox for all 32 LGUs and wrap chip grid (`flex-wrap: wrap`). | **RESOLVED (Phase 31.1)** |
| **BUG-03** | **P0 (CRITICAL)** | `MOD-05` / TC-036, TC-038<br>`itinerary.service.ts` | **Static 10:00 AM Time Slots & Backwards Lodging Order**. Generated itineraries assign 10:00 AM – 12:00 PM to all stops; overnight lodging scheduled before dinner. | **TASK-03**: Sequential non-overlapping time windows (`09:30 AM`, `12:00 PM`, `03:00 PM`) and end-of-day lodging placement. | **RESOLVED (Phase 31.2)** |
| **BUG-04** | **P0 (CRITICAL)** | `MOD-05` / TC-035, TC-037<br>`itinerary.service.ts` | **Preference Filtering Ignored & Cross-Day Duplicates**. Substring category matching failed; multiple high-exertion hikes per day; same venue repeated across days. | **TASK-04**: Canonical `PREFERENCE_CATEGORY_MAP`, Smart Dining anchor, hike intensity guard, and coordinate deduplication (<200m). | **RESOLVED (Phase 31.2)** |
| **BUG-05** | **P1 (HIGH)** | `MOD-06` / TC-042<br>`custom-builder.page.ts` | **Custom Builder Catalog Browse Restricted to ~17 Places**. `loadBrowsePlaces()` called `getFeaturedPlaces()`, ignoring the remaining 2,656 POIs in the database. | **TASK-05**: Ingest all 2,673 POIs via `searchPlaces({ municipality_name, limit: 100 })`. | **RESOLVED (Phase 31.3)** |
| **BUG-06** | **P1 (HIGH)** | `MOD-06` / TC-043<br>`custom-builder.page.ts` | **Custom Builder Category Tabs Don't Sync with Preferences**. Step 1 selections mapped to 'Tourist Spots', hiding museums and resorts in Step 2. | **TASK-05**: Correct category mapping and add unified `✨ Recommended for You` tab combining Step 1 preferences. | **RESOLVED (Phase 31.3)** |
| **BUG-07** | **P2 (MEDIUM)** | `MOD-09` / TC-064<br>`suggested-wizard.page.ts`<br>`custom-builder.page.ts` | **Default Budget Setting Not Hydrated in Wizards**. Changes to default budget in Profile settings (`ne_default_budget`) not read by itinerary wizards. | **TASK-06**: Initialize wizard `daily_budget` form controls dynamically from `localStorage.getItem('ne_default_budget')`. | **RESOLVED (Phase 32.2)** |
| **BUG-08** | **P2 (MEDIUM)** | `MOD-09` / TC-063<br>`app.component.ts` | **Dark Mode Theme Does Not Persist on Reload**. Setting `ne_theme_mode` in Profile not applied to `document.body` during initial app boot. | **TASK-06**: Hydrate dark theme in `AppComponent.ngOnInit()` on initial app startup. | **RESOLVED (Phase 32.2)** |
| **BUG-09** | **P2 (MEDIUM)** | `MOD-04` / TC-024, TC-025<br>`place.service.ts`<br>`map.page.ts` | **Map Viewport Pan/Zoom Overwrites POI Cache**. Map bounding box API queries replaced the 2,673 in-memory POI cache instead of merging. | **TASK-08**: Additive merging (`mergePlacesIntoCache`) preserving provincial marker clusters in `allLoadedPlaces`. | **RESOLVED (Phase 32.1)** |
| **BUG-10** | **P2 (MEDIUM)** | `MOD-07` / TC-050<br>`itinerary-detail.page.ts` | **Itinerary Detail Displays Fallback Subtitle String**. Overview card subtitle displayed static fallback "Estimated activities" instead of stop counts. | **TASK-09**: Implement dynamic `getItinerarySubtitle()` calculating total stops and day counts. | **RESOLVED (Phase 32.2)** |
| **BUG-11** | **P1 (HIGH)** | `MOD-02` / TC-007<br>`backend/` & `environments/` | **Production API Tunnel & Secret Hardening**. Backend ran on ephemeral ngrok tunnel without persistent cloud deployment or JWT secret enforcement. | **TASK-07**: Cloudflare Worker API proxy configured in `environment.prod.ts` & `environment.example.ts`; fail-fast JWT validation in `config.py`; `backend/Dockerfile` and `docker-compose.prod.yml` containerization. | **RESOLVED (Phase 33.2)** |
| **BUG-12** | **P2 (MEDIUM)** | `MOD-03` / TC-017<br>`home.page.scss` | **Popular Destination Cards Width Cramped (120px)**. 120px min-width caused text truncation and wrapping on standard mobile screens. | **TASK-10**: Increased card `min-width` to 160px with responsive clamp. | **RESOLVED (Phase 30/31)** |
| **BUG-13** | **P3 (LOW)** | `MOD-11` / TC-071, TC-073<br>`Project/src/assets/` | **Unused Legacy Image Assets & .VSCodeCounter in Bundle**. 44 unused image files and `.VSCodeCounter` directory inflated bundle footprint. | **TASK-11**: Pruned assets down to 21 active images; excluded `.VSCodeCounter/` via `.gitignore`. | **RESOLVED (Phase 32)** |
| **BUG-14** | **P3 (LOW)** | `MOD-12` / TC-074, TC-075<br>`index.html`<br>`tabs.routes.ts` | **Missing Open Graph Tags & Missing Route Redirect**. `index.html` has generic title and no social meta tags; `/tabs/saved` fails with 404. | **TASK-12**: Add descriptive `<title>`, meta description, Open Graph tags (`og:title`, etc.), and `/tabs/saved` -> `/tabs/history` redirect. | **RESOLVED (Phase 33.2)** |






---

## 14. QA-REPORT Defect Register & Remediation Matrix (`QA-REPORT/16-BUG-REGISTER.md`)

An exhaustive QA audit was documented in `QA-REPORT/`, recording 5 defects across core application behavior. All 5 defects were remediated and verified in **Phase 36**:

| Defect ID | Severity | Module / Location | Defect Description | Resolution | Resolution Status |
| :--- | :---: | :--- | :--- | :--- | :---: |
| **QA-BUG-CRIT-01** | **P0 (CRITICAL)** | `app.component.ts` | **Permanent Splash Screen Freeze**. `dismissSplash()` lacked explicit change detection trigger; on clean sessions, the 500ms fade timeout completed without DOM unmounting. | Injected `ChangeDetectorRef` in `AppComponent` and added `this.cdr.detectChanges()` inside the fade callback. | **RESOLVED (Phase 36)** |
| **QA-ARCH-DEF-01** | **P0 (CRITICAL)** | `main.ts`<br>`home.page.ts` | **Stale View Updates on Async Events**. Background tasks (RxJS search debouncing, HTTP observables) did not reliably trigger change detection without manual interaction. | Configured `provideZoneChangeDetection({ eventCoalescing: true })` in `main.ts` and added `this.cdr.markForCheck()` in `HomePage`. | **RESOLVED (Phase 36)** |
| **QA-UI-DEF-01** | **P1 (HIGH)** | `profile.page.scss` | **Log Out Modal Pointer Interception**. Host selector `.figma-logout-modal` had `display: flex; align-items: center; justify-content: center;`, intercepting pointer events when closed. | Removed `display: flex` and configured `--height: auto;` so Ionic's `.overlay-hidden { display: none; }` unmounts the modal. | **RESOLVED (Phase 36)** |
| **QA-AUDIT-DEF-01** | **P2 (MEDIUM)** | `verify_acceptance_gate.py` | **Acceptance Gate Check #15 Codebase Drift**. Check #15 expected `'Not verified / Not provided'` in `map.page.html`, but modern place sheet uses `'Admission: Check on arrival'`. | Updated Check #15 in `verify_acceptance_gate.py` to inspect `place-detail-sheet.component.ts` and verify `'Admission: Check on arrival'`. | **RESOLVED (Phase 36)** |
| **QA-LINT-DEF-01** | **P2 (MEDIUM)** | Angular Components & Services | **Linter Type Erasure on Runtime DI Tokens**. Running aggressive `lint:fix` converted Angular dependency injection classes to `import type`, causing NG2003 compilation failures. | Guarded DI tokens as runtime classes; verified strict TypeScript compilation and 0 budget errors. | **RESOLVED (Phase 36)** |

---

## 15. Python Flet Desktop Application Defect Tracking Ledger (`desktop_client/`)

An independent code quality and runtime audit of the Python Flet desktop client identified 8 dynamic runtime defects and 15 baseline API/UI defects:

| Defect ID | Severity | Component / Layer | Defect Description & Root Cause | Planned Remediation / Task ID | Resolution Status |
| :--- | :---: | :--- | :--- | :--- | :---: |
| **`BUG-01`** | **P0 (CRITICAL)** | `views/saved_trips_view.py` | `_create_trip_card()` crashes with `AttributeError: 'Itinerary' object has no attribute 'total_days'`. | Add `total_days` and `days_nights_label` properties to `Itinerary` model in `models/itinerary.py`. | **RESOLVED (Phase 48.3)** |
| **`BUG-02`** | **P0 (CRITICAL)** | `views/places_view.py` | `_fetch_places()` passes `municipality` and `sort_by` kwargs to `PlaceService.get_places()`, causing silent `TypeError`. | Fix argument names to `municipality_id` and `sort` in `views/places_view.py` and accept aliases. | **RESOLVED (Phase 48.3)** |
| **`BUG-03`** | **P0 (CRITICAL)** | `views/profile_view.py` | Clicking "Sync Now" crashes with `AttributeError: 'AuthService' object has no attribute 'migrate_guest_trips'`. | Implement `migrate_guest_trips()` in `services/auth_service.py` iterating `guest_storage`. | **RESOLVED (Phase 48.3)** |
| **`BUG-04`** | **P0 (CRITICAL)** | `services/itinerary_service.py`| Generating suggested itinerary catches `ApiClientError` without importing it, raising `NameError`. | Import `ApiClientError` from `core.api_client` in `services/itinerary_service.py`. | **RESOLVED (Phase 48.3)** |
| **`BUG-05`** | **P1 (HIGH)** | `views/dashboard_view.py` | Clicking a saved trip card on Dashboard fails to open `TripDetailView` because route lacks trip data. | Update router in `main.py` to extract trip ID from route and resolve from storage/service. | **PLANNED (Phase 48.4)** |
| **`BUG-06`** | **P0 (CRITICAL)** | `views/login_view.py` | Submitting forms calls `asyncio.run()` inside running Flet event loop, raising `RuntimeError`. | Implement `run_async()` in `core/async_utils.py` and use `safe_page.run_task`. | **RESOLVED (Phase 48.3)** |
| **`BUG-07`** | **P1 (HIGH)** | `main.py` & All Views | Dark mode toggle in sidebar leaves views hardcoded in Light Mode palette. | Create `ThemePalette` in `config/settings.py` and dynamically re-render shell. | **PLANNED (Phase 48.4)** |
| **`BUG-08`** | **P1 (HIGH)** | `views/places_view.py` & `core/api_client.py` | 1. `+ Add to Trip` discards place. 2. `check_health_sync()` hardcodes `127.0.0.1:8000`. | 1. Pre-load place into Builder. 2. Parse host/port dynamically from `self.base_url`. | **RESOLVED (Phase 48.3)** |
| **`DEF-02`** | **P0 (CRITICAL)** | `services/auth_service.py` | Registration fails with HTTP 422 because payload sends `full_name` instead of `first_name`, `last_name`. | Rebuilt `register()` payload to supply `first_name`, `last_name`, `username`. | **RESOLVED (Phase 48.3)** |
| **`DEF-05`** | **P0 (CRITICAL)** | `services/itinerary_service.py`| Reordering stops calls invalid `PUT .../days/{d}/reorder` endpoint instead of `POST .../reorder`. | Corrected endpoint to `POST /itineraries/{id}/reorder` with items list payload. | **RESOLVED (Phase 48.3)** |
| **`DEF-06`** | **P1 (HIGH)** | `services/place_service.py` | Place search and pagination query params (`search`, `page`) ignored by backend (`q`, `limit`, `offset`). | Remapped parameters in `PlaceService.get_places()` matching FastAPI `PlaceFilterParams`. | **RESOLVED (Phase 48.3)** |
| **`DEF-08`** | **P1 (HIGH)** | `models/user.py` | Profile name edits dropped by backend because `UserUpdatePayload` sends `full_name`. | Split `full_name` into `first_name` and `last_name` in `UserUpdatePayload.to_dict()`. | **RESOLVED (Phase 48.3)** |
| **`DEF-09`** | **P1 (HIGH)** | `services/itinerary_service.py`| Updating itinerary metadata calls `PUT /itineraries/{id}`, returning HTTP 405 Method Not Allowed. | Changed HTTP method to `PATCH /itineraries/{id}` in `ItineraryService.update_itinerary()`. | **RESOLVED (Phase 48.3)** |
| **`DEF-10`** | **P1 (HIGH)** | `config/settings.py` | Runtime environment variables from `.env` ignored because `load_dotenv()` was never called. | Added `load_dotenv()` call during configuration module initialization. | **RESOLVED (Phase 48.3)** |
| **`DEF-14`** | **P2 (MEDIUM)** | `models/place.py` | Municipality coordinates parsed as `None` because backend returns `center_lat` and `center_lng`. | Mapped `center_lat` and `center_lng` to `latitude` and `longitude` in `Municipality.from_dict`. | **RESOLVED (Phase 48.3)** |
| **`DEF-15`** | **P3 (LOW)** | `config/settings.py` | Muted text color `#94a3b8` has 2.8:1 contrast on `#f8fafc`, failing WCAG 2.2 AA. | Darkened `TEXT_MUTED_LIGHT` to `#475569` (4.8:1 contrast ratio, WCAG AA compliant). | **RESOLVED (Phase 48.3)** |

---

## 16. Post-Session 53 Desktop Client QA Parity Defect Register (Remediation Plan v2)

Following the Session 53 re-QA audit against the live reference Web App (`https://edselrenz.github.io/Itinerary-App/#/welcome`), 20 critical defects were identified across Map Tab, Suggested Itinerary Wizard, and Custom Builder:

| Defect ID | Severity | Module / Location | Root Cause in v0.52.0 | Reference Web Behavior | Status |
| :--- | :---: | :--- | :--- | :--- | :---: |
| **`MAP-01`** | **P0 (CRITICAL)** | `views/places_view.py:407-440` | Outer `Container(bottom=18, left=0, right=0, alignment=Alignment(0, 1))` stretches full-width in Stack, blocking mouse clicks/drags across map. | Compact pill button at bottom-center without blocking map canvas. | **RESOLVED (Session 54)** |
| **`MAP-02`** | **P0 (CRITICAL)** | `components/slippy_map_canvas.py:285-298` | `_marker_stack` inside `GestureDetector` causes pan recognizers to compete with marker/cluster clicks; missing `on_scroll` (wheel) and `on_double_tap`. | Smooth pan everywhere, scroll-wheel zoom, double-click zoom, instant pin/cluster clicks. | **RESOLVED (Session 54)** |
| **`MAP-03`** | **P0 (CRITICAL)** | `components/slippy_map_canvas.py:220-221, 310` | `__init__()` sets `_route_pts = []` and never invokes `set_route()` when `route_stops` are passed, drawing 0 polylines and staying at Zoom 10. | Auto-renders road geometry and auto-fits bounds to stops on mount. | **RESOLVED (Session 54)** |
| **`MAP-04`** | **P1 (HIGH)** | `main.py:263-267`<br>`views/places_view.py:110-119` | `main.py` passes `active_trip=selected_trip` unconditionally, locking user in Follow-Route mode whenever any trip was previously viewed. Missing `recenter_map()`. | Map tab only enters Follow-Route mode when `?followRoute=true` or `?itineraryId=...` is in URL. | **RESOLVED (Session 54)** |
| **`MAP-05`** | **P0 (CRITICAL)** | `views/places_view.py:716-737` | `_on_search_change()`, `_clear_search()`, and `_select_category()` call `_build_content()`, destroying TextField (losing focus after 1 key) and resetting map zoom to 10. | In-place marker and count updates with 0 focus loss and preserved map viewport. | **RESOLVED (Session 54)** |
| **`MAP-06`** | **P1 (HIGH)** | `components/slippy_map_canvas.py:71-92, 342-353` | Background threads in `_TILE_EXECUTOR` call `self.redraw()` (`self.update()`) concurrently from non-asyncio threads, mutating UI tree unsafely. | Thread-safe single-image updates with clean fallback. | **RESOLVED (Session 54)** |
| **`MAP-07`** | **P1 (HIGH)** | `services/place_service.py:319` | `fetch_live_osm_places()` uses `httpx.AsyncClient` without `import httpx` (`NameError`). `PlacesView` ignores current map viewport bounds. | Queries Overpass API using current map viewport bounding box. | **RESOLVED (Session 54)** |
| **`MAP-08`** | **P2 (MEDIUM)** | `views/places_view.py:221-223, 401-405`<br>`main.py:65-71` | `main.py` never sets window dimensions; `SlippyMapCanvas` hardcoded to 1240x740, clipping bottom 50px; floating buttons overlap zoom buttons. | Clear layout separation between floating action buttons and map zoom controls without clipping. | **RESOLVED (Session 54)** |
| **`MAP-09`** | **P1 (HIGH)** | `views/places_view.py:142-159, 815-921` | Filter modal only allows single category selection, lacks active count badge `Filters [N]`, and misclassifies unpriced places as budget. | Multi-category selection set, active filter badge, accurate price tier filtering. | **RESOLVED (Session 54)** |
| **`MAP-10`** | **P2 (MEDIUM)** | `views/places_view.py:442-491` | `_build_poi_drawer()` renders horizontal row of tall cards that overflow 220px drawer vertically; lacks empty state + reset button. | Clean vertical scrollable sheet of compact destination rows with empty-state reset button. | **RESOLVED (Session 54)** |
| **`SUG-01`** | **P0 (CRITICAL)** | `views/suggested_wizard_view.py:91-95, 324-330` | Sends display labels (`"Nature & Parks"`) instead of canonical keys (`"nature"`), causing backend generator to match 0 preferred categories. | Uses canonical keys `['nature', 'food', 'culture', 'shopping', 'resort']` with `['food', 'culture', 'resort']` default. | **RESOLVED (Session 54)** |
| **`SUG-02`** | **P2 (MEDIUM)** | `models/itinerary.py:182-185` | `ItineraryDay.display_title` prepends `Day X: ` to an already prefixed title, rendering `"Day 1: Day 1: Cabanatuan City"`. | Renders clean title: `"Day 1 - Cabanatuan City"`. | **RESOLVED (Session 54)** |
| **`SUG-03`** | **P1 (HIGH)** | `services/itinerary_service.py:105, 152-285` | Pacing checks `fast` instead of `packed` (schedules 3 stops instead of 4); unrated OSM places outscore curated attractions; utility POIs scheduled; no 25km clustering/2-Opt. | Curated places boosted +20.0, utility POIs excluded, 25km clustering + 2-Opt ordering applied. | **RESOLVED (Session 54)** |
| **`SUG-04`** | **P1 (HIGH)** | `views/suggested_wizard_view.py:480-860` | Result view lacks bottom `"Nearby Places"` banner and bottom Save/Customize CTAs; Nearby cards lack Maps button and hours; hardcodes "01:30 PM". | Bottom Nearby banner + CTAs present; Nearby cards have hours + Maps link; sequential time calculated. | **RESOLVED (Session 54)** |
| **`SUG-05`** | **P1 (HIGH)** | `main.py:208`<br>`views/suggested_wizard_view.py` | Top-left `← Back` in `WorkflowHeader` jumps straight to `/home` from results or nearby, discarding preview. | Header Back button steps back from `nearby` → `itinerary` → `form`. | **RESOLVED (Session 54)** |
| **`CUS-01`** | **P0 (CRITICAL)** | `views/custom_builder_view.py:464-472, 1260-1306` | Step 2 search only triggers on Enter, only queries 60 places, and calls `_build_content()` destroying search focus. | Filters 2,673 POIs live on every keystroke with Clear `✕` button and 0ms in-memory filtering. | **RESOLVED (Session 54)** |
| **`CUS-02`** | **P1 (HIGH)** | `views/custom_builder_view.py:474-497, 570` | Step 2 only shows 5 raw categories (omitting 11 canonical categories); `Details` modal missing `on_add_to_day` callback. | Displays all 8 category groups covering all 16 canonical categories; wires `on_add_to_day` in modal. | **RESOLVED (Session 54)** |
| **`CUS-03`** | **P1 (HIGH)** | `views/custom_builder_view.py:909, 927-936` | `_calc_next_time()` uses fixed 30m buffer, crashes with `ValueError` on range times (`"09:30 AM - 11:30 AM"`), falling back to "11:00 AM". | Parses range and ISO strings; computes dynamic Haversine driving buffer (15-120 min). | **RESOLVED (Session 54)** |
| **`CUS-04`** | **P1 (HIGH)** | `views/custom_builder_view.py:626-776, 938-948` | Step 3 timeline lacks Daily Budget input; day tabs omit municipality; StopCard lacks is_first/is_last; moving stops does not auto-schedule times. | Includes Daily Budget input, municipality tags on tabs, first/last arrow bounds, and auto-scheduling on move. | **RESOLVED (Session 54)** |
| **`CUS-05`** | **P0 (CRITICAL)** | `main.py:225, 241` | `main.py:241` references undefined `itinerary_service` (`NameError`); Back button jumps to `/home` instead of stepping back to `form`. | Back button steps back to `form`; `itinerary_service` instantiated cleanly. | **RESOLVED (Session 54)** |
| **`PAR-01`** | **P0 (CRITICAL)** | `backend/app/core/database.py`, `backend/app/services/auth_service.py` | `psycopg.errors.UndefinedColumn: column users.middle_initial does not exist` causing 500 error on login/me endpoints when accessing existing users without schema backfill. | Added automatic schema backfill in `ensure_user_profile_columns()` for all 6 extended profile columns (`middle_initial`, `birthday`, `gender`, `phone_number`, `avatar_url`, `default_daily_budget`). | **RESOLVED (Session 55)** |
| **`PAR-02`** | **P1 (HIGH)** | `desktop_client/views/profile_view.py:did_mount` | Profile tab repeatedly polled backend in an infinite request loop due to unconditional reload in `did_mount()`. | Added `self._has_refreshed_profile` guard to guarantee single-execution profile refresh on view mount. | **RESOLVED (Session 55)** |
| **`PAR-03`** | **P1 (HIGH)** | `desktop_client/views/places_view.py` | `Dropdown.__init__() got an unexpected keyword argument 'on_change'` in Flet 1.1.2 when opening map filters modal. | Replaced `Dropdown` with Web-identical chip row and horizontal scroller for 32 LGUs and 4 price range pills. | **RESOLVED (Session 55)** |
| **`PAR-04`** | **P1 (HIGH)** | `desktop_client/components/destination_picker.py`, `views/suggested_wizard_view.py` | `TextField.__init__() got an unexpected keyword argument 'prefix_icon_color'` under Flet 1.1.2 runtime. | Removed deprecated parameter in favor of standard icon styling. | **RESOLVED (Session 55)** |
| **`PAR-05`** | **P2 (MEDIUM)** | `scripts/build_standalone_exe.py` | PyInstaller build failed with `PermissionError: [WinError 5] Access is denied` when an existing instance of `NuevaEcijaTravel.exe` was running in the background. | Terminated orphaned process and added clean process check before recompilation. | **RESOLVED (Session 55)** |

