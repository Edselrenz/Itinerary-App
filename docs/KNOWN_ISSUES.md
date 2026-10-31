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

## 4. Code Review Audit Findings & Pending Remediations

An independent code review conducted on October 31, 2026 identified 16 findings across security, data integrity, core functionality, and code quality. Full analysis is documented in [CODE_REVIEW_AUDIT.md](file:///c:/Users/Edward/Desktop/CaseStudy/docs/CODE_REVIEW_AUDIT.md) and tracked in [TODO.md](file:///c:/Users/Edward/Desktop/CaseStudy/docs/TODO.md).

### 4.1 Critical Severity
- **CR-001 (BOLA in Itinerary Reorder)**:
  - **Issue**: `POST /api/v1/itineraries/{id}/reorder` does not verify `item.day_id` belongs to `itinerary.days`.
  - **Target**: Phase 11 (`backend/app/api/v1/itineraries.py`).
  - **Status**: Pending Fix.
- **CR-002 (BOLA / IDOR in Stop Deletion)**:
  - **Issue**: `DELETE /api/v1/itineraries/{id}/days/{day_id}/items/{item_id}` deletes item without scoping to `day_id` or `itinerary_id`.
  - **Target**: Phase 11 (`backend/app/api/v1/itineraries.py`).
  - **Status**: Pending Fix.

### 4.2 High Severity
- **CR-003 (Silent Data Loss in Itinerary Edit Mode)**:
  - **Issue**: `CustomBuilderPage.saveItinerary()` in edit mode calls `updateItinerary()` without `days`, dropping all day additions, removals, and stop edits upon save.
  - **Target**: Phase 11 (`Project/src/app/features/itinerary/custom-builder/custom-builder.page.ts`, `backend/app/api/v1/itineraries.py`, `backend/app/schemas/itinerary.py`).
  - **Status**: Pending Fix.
- **CR-004 (JWT Secret Fallback, OAuth Audience & CORS Scope)**:
  - **Issue**: Default JWT secret not blocked in non-dev environments; `google_oauth_client_id` empty allows arbitrary token audiences (`audience=None`); wildcard CORS regex `r"^https://.*\.github\.io$"`.
  - **Target**: Phase 11 (`backend/app/core/config.py`, `backend/app/services/auth_service.py`).
  - **Status**: Pending Fix.
- **CR-005 (Google OAuth Account Takeover & Deactivated User Bypass)**:
  - **Issue**: Google account links by email without verifying `email_verified is True`; deactivated users (`is_active=False`) can authenticate via Google OAuth.
  - **Target**: Phase 11 (`backend/app/services/auth_service.py`).
  - **Status**: Pending Fix.
- **CR-006 (Missing Token Refresh & Silent Guest Downgrade)**:
  - **Issue**: Client never calls `/auth/refresh`; 401 triggers `ItineraryService` catchError which silently downgrades the user to guest storage instead of refreshing session.
  - **Target**: Phase 12 (`Project/src/app/core/interceptors/auth.interceptor.ts`, `Project/src/app/core/services/itinerary.service.ts`, `auth.service.ts`).
  - **Status**: Pending Fix.
- **CR-007 (Timezone Off-by-One Shifting in Date Parsing)**:
  - **Issue**: `new Date("YYYY-MM-DD")` UTC midnight parsing and `toISOString().split('T')[0]` shifts dates in UTC+8 (Philippine Time).
  - **Target**: Phase 12 (`Project/src/app/core/utils/date.utils.ts`, wizard, builder, detail pages).
  - **Status**: Pending Fix.

### 4.3 Medium Severity
- **CR-008 (Generator Ignores Dest Radius, Budget Flaws & Unescaped SQL)**:
  - **Issue**: `default_dest_radius_km` (25km) not enforced; budget filter checks cost per stop instead of cumulative daily budget; SQL `.ilike()` does not escape `%`/`_`.
  - **Target**: Phase 12 (`backend/app/algorithms/itinerary_generator.py`, `backend/app/api/v1/places.py`).
  - **Status**: Pending Fix.
- **CR-009 (Offline Suggested Generator Ignores Inputs & Hardcoded UI Chips)**:
  - **Issue**: Guests bypass backend generator even when online; offline generator ignores destination/budget/preferences; wizard template has hardcoded chips.
  - **Target**: Phase 12 (`Project/src/app/core/services/itinerary.service.ts`, `suggested-wizard.page.html`).
  - **Status**: Pending Fix.
- **CR-010 (Missing Single-Stop PATCH, Sort Order Bug & Missing Place Check)**:
  - **Issue**: No PATCH endpoint for single stop notes/cost; `add_itinerary_item` sort_order default bug; `create_itinerary` missing `place_id` foreign key check.
  - **Target**: Phase 12 (`backend/app/api/v1/itineraries.py`, `backend/app/schemas/itinerary.py`).
  - **Status**: Pending Fix.
- **CR-011 (Map Page Ignores Query Params, Tile Error & Bottom Sheet Honesty)**:
  - **Issue**: Route queryParams from Home tab ignored by map; no `tileerror` listener; bottom sheet lacks explicit "Not verified / Not provided" labels.
  - **Target**: Phase 12 (`Project/src/app/features/map/map.page.ts`, `map.page.html`).
  - **Status**: Pending Fix.
- **CR-012 (Unvalidated Custom API URL & Bearer Token Exfiltration Risk)**:
  - **Issue**: `ConnectivityService.setCustomApiUrl()` accepts unvalidated URLs; `authInterceptor` attaches Bearer token without checking origin starts with `apiBaseUrl`.
  - **Target**: Phase 12 (`Project/src/app/core/services/connectivity.service.ts`, `Project/src/app/core/interceptors/auth.interceptor.ts`).
  - **Status**: Pending Fix.
- **CR-013 (Cloudflare Tunnel Rate Limiting, Generator Pre-Filtering & N+1 Queries)**:
  - **Issue**: SlowAPI keys on `127.0.0.1` for all tunnel users; `itinerary_generator` loads all 4,400+ places into memory; $N+1$ queries in seeding; `db_backup_restore.py` restore lacks `--clean --if-exists`.
  - **Target**: Phase 12 (backup restore) & Phase 14 (`backend/app/api/v1/auth.py`, `itinerary_generator.py`, `scripts/`).
  - **Status**: Pending Fix.

### 4.4 Low & Informational Severity
- **CR-014 (Outdated E2E Test, Dead Starter Code & Tautological Checks)**:
  - **Issue**: E2E spec tests for Tab 1; 16 dead starter files in `Project/src/app/`; 7 tautological checks in `verify_acceptance_gate.py`; destructive `setup_steps_0_to_2.py`.
  - **Target**: Phase 13 & Phase 14.
  - **Status**: Pending Fix.
- **CR-015 (Profile Memory Leak, Non-Functional Buttons, Typos & Unused Images)**:
  - **Issue**: Unsubscribed observable in `ProfilePage`; non-functional buttons on login page; Bongabon-only nearby places; UI copy typos; 44 unused image files.
  - **Target**: Phase 13.
  - **Status**: Pending Fix.
- **CR-016 (Documentation Discrepancies)**:
  - **Issue**: Stale documentation showing completed milestones as pending.
  - **Target**: Phase 13 (`docs/`).
  - **Status**: Addressed / In Sync.


