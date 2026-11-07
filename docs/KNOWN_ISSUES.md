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

### 2.1 Local PostgreSQL vs SQLite Configuration
- **Status**: Active Workaround Available.
- **Context**: Local development environments may not have a PostgreSQL daemon running or `psql` on the system PATH.
- **Resolution**: The backend ORM entities and database session manager are architected with dual-engine compatibility (`JsonType`, `sa.Uuid`). Setting `DATABASE_URL=sqlite:///./nueva_ecija_travel.db` in `.env` allows running the complete application locally without starting PostgreSQL.

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



