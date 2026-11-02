# Known Issues & Technical Limitations

This document tracks identified bugs, intentional technical constraints, and temporary limitations across the application.

---

## 1. Intentional Architectural Constraints (By Design)

### 1.1 Apple Sign-In Disabled State
- **Status**: By Design / Gated.
- **Context**: Apple Sign-In requires an active Apple Developer Program membership (US\$99/year). Per the MVP zero-cost compliance matrix, this feature is gated behind `enableAppleAuth = false` in `environment.ts` and `.env`.
- **User Impact**: The Apple button is rendered disabled with a truthful caption: *"Apple Sign-In is disabled in this pilot build"*. Calling `POST /api/v1/auth/oauth/apple` returns `501 Not Implemented`.

### 1.2 History & Profile Tabs Deferred to v1.1
- **Status**: By Design / Phased Scope.
- **Context**: The MVP blueprint explicitly focuses on Home, Map, and Itinerary Planning flows.
- **User Impact**: In the 4-tab shell, the History tab displays a clean placeholder (*"Planned for a later release — MVP focuses on Home discovery, interactive Map, and Itinerary Planning"*), and the Profile tab serves as a session status / guest mode indicator.

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



