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




