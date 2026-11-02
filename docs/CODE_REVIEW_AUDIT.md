# Comprehensive Code Review & Security Audit Report

**Application**: Nueva Ecija Travel Itinerary (MVP)  
**Audit Date**: October 31, 2026  
**Auditor**: Independent Principal Software Engineer & Security Specialist  
**Status**: Completed — Ingested into Project Documentation & Roadmap  
**Target Remediation**: Phases 11, 12, 13, and 14 in [TODO.md](file:///c:/Users/Edward/Desktop/CaseStudy/docs/TODO.md)

---

## 1. Executive Summary

An exhaustive, line-by-line architectural, security, data integrity, and code quality review was conducted on the Nueva Ecija Travel Itinerary MVP codebase. The review evaluated the FastAPI backend, Angular/Ionic mobile client, SQLAlchemy/PostgreSQL data layer, Leaflet mapping engine, and offline synchronization mechanisms.

### Key Takeaways
1. **Strong Architectural Foundation**: Clean separation of concerns, strict adherence to zero-cost MVP guidelines, robust local data pipelines, and verified 24/24 acceptance criteria.
2. **Critical Security & Data Integrity Gaps**: Two Broken Object Level Authorization (BOLA/IDOR) vulnerabilities, a silent data-loss defect in custom itinerary editing, and fallback JWT secrets/unvalidated OAuth audiences.
3. **Actionable Remediation Plan**: All findings have been assigned unique identifiers (`CR-001` through `CR-016`) and mapped into a 4-phase prioritized action plan.

---

## 2. Severity Breakdown

| Severity | Count | Issue IDs | Summary |
| :--- | :---: | :--- | :--- |
| **Critical** | 2 | `CR-001`, `CR-002` | Cross-itinerary BOLA / IDOR stop reordering and deletion |
| **High** | 5 | `CR-003`, `CR-004`, `CR-005`, `CR-006`, `CR-007` | Silent data loss in edit mode, JWT/OAuth hardening, token refresh/interceptor failure, timezone off-by-one shifting |
| **Medium** | 6 | `CR-008`, `CR-009`, `CR-010`, `CR-011`, `CR-012`, `CR-013` | Generator radius/budget flaws, offline generator disregard of inputs, missing PATCH stop, map route queryParams, custom API URL injection, Cloudflare tunnel rate limiting |
| **Low** | 2 | `CR-014`, `CR-015` | Outdated E2E spec, starter dead code, tautological test assertions, profile memory leak, UI typos, unused assets |
| **Informational** | 1 | `CR-016` | Documentation drift and outdated milestone progress indicators |
| **Total** | **16** | | |

---

## 3. Detailed Audit Findings

### CR-001: Cross-Itinerary BOLA in Stop Reordering
- **Severity**: Critical
- **Category**: Broken Object Level Authorization (CWE-639 / OWASP API1:2023)
- **Affected File**: `backend/app/api/v1/itineraries.py` (lines 519–529)
- **Description**: The endpoint `POST /api/v1/itineraries/{id}/reorder` verifies that the target `itinerary_id` belongs to `current_user.id`. However, when iterating over `payload.items`, it queries `db.get(ItineraryItem, reorder_entry.id)` globally. It never verifies that the retrieved `item` belongs to one of the days of `itinerary`.
- **Root Cause**: Missing check asserting `item.day_id in {d.id for d in itinerary.days}`.
- **Impact**: An authenticated user can supply `item_id` values belonging to another user's private itinerary, altering their `sort_order` or moving their stops into arbitrary days.
- **Remediation**:
  ```python
  allowed_day_ids = {day.id for day in itinerary.days}
  for entry in payload.items:
      item = db.get(ItineraryItem, entry.id)
      if not item or item.day_id not in allowed_day_ids:
          raise HTTPException(
              status_code=status.HTTP_400_BAD_REQUEST,
              detail=f"Item {entry.id} does not belong to itinerary {itinerary_id}"
          )
      item.sort_order = entry.sort_order
  ```

---

### CR-002: Cross-Itinerary Stop Deletion (IDOR)
- **Severity**: Critical
- **Category**: Broken Object Level Authorization (CWE-639 / OWASP API1:2023)
- **Affected File**: `backend/app/api/v1/itineraries.py` (lines 464–474)
- **Description**: In `DELETE /api/v1/itineraries/{id}/days/{day_id}/items/{item_id}`, the endpoint verifies `itinerary.user_id == current_user.id`, but queries `item = db.get(ItineraryItem, item_id)` directly. It does not verify that `day_id` belongs to `itinerary`, nor that `item.day_id == day_id`.
- **Root Cause**: Missing scoping check between itinerary, day, and item before issuing `db.delete(item)`.
- **Impact**: Any authenticated attacker owning at least one empty itinerary can delete arbitrary itinerary items across the database by supplying the victim's `item_id`.
- **Remediation**:
  ```python
  day = db.get(ItineraryDay, day_id)
  if not day or day.itinerary_id != itinerary.id:
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Day not found in this itinerary")
  item = db.get(ItineraryItem, item_id)
  if not item or item.day_id != day.id:
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found in this day")
  db.delete(item)
  ```

---

### CR-003: Custom Builder Edit Mode Drops All Days and Stops (Silent Data Loss)
- **Severity**: High
- **Category**: Data Integrity / Core Functional Defect
- **Affected Files**:
  - `Project/src/app/features/itinerary/custom-builder/custom-builder.page.ts` (lines 326–340)
  - `Project/src/app/core/services/itinerary.service.ts` (lines 133–146)
  - `backend/app/api/v1/itineraries.py` (lines 382–397)
  - `backend/app/schemas/itinerary.py` (lines 31–36)
- **Description**: When editing an existing itinerary (`isEditMode = true`), `saveItinerary()` calls `updateItinerary(this.itineraryId, { title, destination, startDate, endDate, budgetMin, budgetMax, pace, notes })`. The `days` array is never passed. Furthermore, the backend `ItineraryUpdate` schema has no `days` field, and `PATCH /api/v1/itineraries/{id}` only updates top-level scalar fields. In guest mode, `updateGuestItinerary()` similarly merges top-level fields only.
- **Root Cause**: The edit path was implemented as a metadata update rather than a composite aggregate update.
- **Impact**: 100% of day additions, removals, reorderings, and stop modifications made in edit mode are discarded silently when the user clicks "Save".
- **Remediation**:
  - Extend `ItineraryUpdate` to accept optional `days: Optional[List[ItineraryDayCreate]]`, `preferences`, and `assumptions`.
  - Update backend `PATCH /api/v1/itineraries/{id}` and `ItineraryService.updateItinerary()` to sync days and items transactionally.

---

### CR-004: Hardcoded Fallback Secrets, Unenforced OAuth Audience & Permissive CORS
- **Severity**: High
- **Category**: Security / Authentication Hardening (CWE-798, CWE-287, CWE-942)
- **Affected Files**:
  - `backend/app/core/config.py` (lines 17, 35)
  - `backend/app/services/auth_service.py` (lines 165–177)
- **Description**:
  1. `jwt_secret_key` defaults to `"dev-secret-key-change-in-production-only-long-random-string"` with no startup validation asserting it was changed when `environment != "development"`.
  2. If `google_oauth_client_id` is empty (default in `.env.example`), `id_token.verify_oauth2_token(token, requests.Request(), audience=None)` is called with `audience=None`, which skips Google client ID audience validation entirely.
  3. `cors_origins_regex = r"^https://.*\.github\.io$"` permits any GitHub Pages website globally to make credentialed requests.
- **Remediation**:
  - Add validator in `Settings` refusing to start in staging/production with the default JWT secret.
  - Assert `google_oauth_client_id` is set before verifying Google tokens; return 500/503 if unconfigured.
  - Restrict `cors_origins` explicitly to `https://edselrenz.github.io` and local origins.

---

### CR-005: Google OAuth Account Takeover & Deactivated User Bypass
- **Severity**: High
- **Category**: Authentication & Access Control (CWE-287)
- **Affected File**: `backend/app/services/auth_service.py` (lines 179–216)
- **Description**:
  1. `authenticate_google_user()` looks up existing users by `email` and links Google credentials without asserting `payload.get("email_verified") is True`. An attacker could register a Google account with an unverified email address to claim a target account.
  2. Does not check `user.is_active`. A deactivated or banned user can authenticate via Google and obtain active JWT access tokens.
- **Remediation**:
  - Reject OAuth payloads if `payload.get("email_verified") is not True`.
  - Check `if not user.is_active: raise HTTPException(status_code=403, detail="Account is deactivated")`.

---

### CR-006: Missing Token Refresh & Silent Fallback to Guest Storage
- **Severity**: High
- **Category**: Authentication / User Experience / Data Integrity
- **Affected Files**:
  - `Project/src/app/core/interceptors/auth.interceptor.ts`
  - `Project/src/app/core/services/itinerary.service.ts` (lines 109–114, 140–145, 159–164)
  - `Project/src/app/core/services/auth.service.ts`
- **Description**:
  1. The Angular client never calls `POST /api/v1/auth/refresh`. When the 30-minute access token expires, API requests fail with 401.
  2. `authInterceptor` does not handle 401 by attempting token refresh via refresh token.
  3. In `ItineraryService`, `catchError` catches 401s and all other HTTP errors and silently falls back to `GuestStorageService`. The user is never notified that their session expired; their new itineraries are stored in local IndexedDB and never reach their account on the backend.
  4. `AuthService.isAuthenticated()` checks only `Boolean(this.accessToken)` without checking JWT expiration (`exp`).
- **Remediation**:
  - Implement 401 refresh interceptor with queueing in `authInterceptor`.
  - Implement `AuthService.refreshSession()` calling `/api/v1/auth/refresh`.
  - Inspect `exp` claim in `AuthService.isAuthenticated()`.
  - Restrict `ItineraryService` guest storage fallback strictly to offline status (`status === 0 || status === 502 || status === 504`).

---

### CR-007: Timezone Off-by-One Shifting in Date Parsing & Generation
- **Severity**: High
- **Category**: Localization & Date Arithmetic (CWE-398)
- **Affected Files**:
  - `Project/src/app/features/itinerary/suggested-wizard/suggested-wizard.page.ts` (line 79)
  - `Project/src/app/features/itinerary/custom-builder/custom-builder.page.ts` (lines 167–176, 319–322)
  - `Project/src/app/features/itinerary/itinerary-detail/itinerary-detail.page.ts` (line 98)
  - `Project/src/app/core/services/itinerary.service.ts` (line 404)
- **Description**:
  1. `new Date("YYYY-MM-DD")` parses dates as UTC midnight (00:00:00Z). In local time zones (e.g., UTC-X or UTC+8), accessing local date getters or formatting produces off-by-one calendar dates.
  2. In `suggested-wizard.page.ts`, `today = new Date().toISOString().split('T')[0]` evaluates in UTC. In UTC+8 (Philippine Time), between 00:00 and 07:59 AM, UTC date is yesterday's date, allowing users to select a past date as "today".
  3. Adding days via `d.setDate(d.getDate() + dayNum - 1)` on UTC date objects causes shifting when converting back to strings.
- **Remediation**:
  - Create centralized date utility (`Project/src/app/core/utils/date.utils.ts`) with `toLocalIsoDate()`, `parseLocalIsoDate()`, and `addDaysLocal()`.
  - Replace all `toISOString().split('T')[0]` calls with local calendar date helpers.

---

### CR-008: Generator Ignores Destination Radius, Has Budget Flaws & Unescaped SQL
- **Severity**: Medium
- **Category**: Algorithm Accuracy & SQL Wildcard Safety
- **Affected Files**:
  - `backend/app/algorithms/itinerary_generator.py` (lines 106–122, 222–224)
  - `backend/app/api/v1/places.py` (lines 46, 51)
- **Description**:
  1. `settings.default_dest_radius_km` (25.0 km) is never referenced or filtered in `itinerary_generator.py`. A destination in Bongabon can select POIs in Nampicuan or Cuyapo 60+ km away if category scores align.
  2. The budget filter checks `cost_min > daily_budget` per stop independently instead of tracking cumulative daily expenditures. Three ₱450 stops can be placed in a ₱500 daily budget.
  3. SQL `.ilike()` queries in `places.py` pass raw user inputs without escaping `%` or `_` characters.
- **Remediation**:
  - Enforce `haversine_distance(dest_coords, place_coords) <= settings.default_dest_radius_km`.
  - Track running daily cost against `daily_budget`.
  - Helper to escape SQL wildcards: `def escape_like(query: str) -> str: return query.replace("%", "\\%").replace("_", "\\_")`.

---

### CR-009: Offline Suggested Generator Ignores Inputs & Hardcoded UI Chips
- **Severity**: Medium
- **Category**: Frontend Logic / User Experience
- **Affected Files**:
  - `Project/src/app/core/services/itinerary.service.ts` (lines 394–436)
  - `Project/src/app/features/itinerary/suggested-wizard/suggested-wizard.page.html` (lines 136–142)
  - `Project/src/app/features/itinerary/suggested-wizard/suggested-wizard.page.ts` (lines 182–198)
- **Description**:
  1. When a guest user is online, `suggestItinerary()` checks `if (isGuest)` and immediately runs the offline generator, completely bypassing the backend generator.
  2. `generateOfflineSuggestedItinerary()` in `ItineraryService` hardcodes Day 1 (Bongabon), Day 2 (Cabanatuan), and Day 3 (Gapan), ignoring destination, budget, and selected preferences.
  3. In `suggested-wizard.page.html`, budget chips and preference chips have hardcoded values.
- **Remediation**:
  - Call `/api/v1/itineraries/suggest` for guests if online; use offline generator only on network failure.
  - Filter curated pool in `generateOfflineSuggestedItinerary()` by destination municipality and category tags.
  - Dynamically bind budget and preference chips to configured options.

---

### CR-010: Missing Single-Stop PATCH, Sort Order Default Bug & Missing Place Check
- **Severity**: Medium
- **Category**: API Completeness / Edge Case Robustness
- **Affected Files**:
  - `backend/app/schemas/itinerary.py` (lines 48–52)
  - `backend/app/api/v1/itineraries.py` (lines 186–218, 421–456)
- **Description**:
  1. `ItineraryItemUpdate` schema exists in schemas but is not wired to any endpoint. Travelers cannot update notes, time, or cost of an existing stop without deleting and recreating it.
  2. In `add_itinerary_item()`: `sort_order = max([i.sort_order for i in day.items], default=1) + 1`. For the first item, `max([], default=1)` yields 1, resulting in `sort_order = 2` instead of 1.
  3. `create_itinerary()` does not verify `place_id` existence prior to insert, causing an unhandled 500 `IntegrityError` if an invalid ID is provided.
- **Remediation**:
  - Implement `PATCH /api/v1/itineraries/{id}/days/{day_id}/items/{item_id}`.
  - Fix default: `sort_order = max([i.sort_order for i in day.items], default=0) + 1`.
  - Validate `place_id` against `places` table; return 404 or 422 on nonexistent ID.

---

### CR-011: Map Page Ignores Route Query Params, Tile Error & Bottom Sheet Honesty
- **Severity**: Medium
- **Category**: Frontend Integration / Observability
- **Affected Files**:
  - `Project/src/app/features/map/map.page.ts` (lines 32–44)
  - `Project/src/app/features/home/home.page.ts` (line 98)
  - `Project/src/app/features/map/map.page.html`
- **Description**:
  1. Home tab "Plan Route Here" passes query parameters to `/tabs/map`, but `MapPage` does not read `queryParams` or center on the requested municipality/coordinates.
  2. Leaflet tile layer lacks a `tileerror` listener; network drops leave silent gray tiles without status messaging.
  3. POI bottom sheet does not render explicit "Not verified / Not provided" labels for missing hours/fees.
- **Remediation**:
  - Inject `ActivatedRoute` in `MapPage` and fly to `[lat, lng]` or municipality when params are provided.
  - Add `tileerror` listener displaying non-intrusive offline notification.
  - Render explicit honest pricing and provenance badges in bottom sheet.

---

### CR-012: Unvalidated Custom API URL & Bearer Token Exfiltration Risk
- **Severity**: Medium
- **Category**: Frontend Security (CWE-20, CWE-200)
- **Affected Files**:
  - `Project/src/app/core/services/connectivity.service.ts` (lines 77–83)
  - `Project/src/app/core/interceptors/auth.interceptor.ts` (lines 25–33)
- **Description**:
  1. `ConnectivityService.setCustomApiUrl(url)` accepts any arbitrary string without verifying protocol (`https://` or `http://localhost`) or valid URL format.
  2. `authInterceptor` unconditionally injects `Authorization: Bearer <token>` to all HTTP requests without verifying that `req.url` starts with `environment.apiBaseUrl`.
- **Remediation**:
  - Validate URL format and protocol in `setCustomApiUrl()`.
  - Condition token attachment: `if (this.authService.getAccessToken() && req.url.startsWith(environment.apiBaseUrl))`.

---

### CR-013: Cloudflare Tunnel Shared Rate-Limit Lockout, Generator Scalability & N+1 Queries
- **Severity**: Medium
- **Category**: Scalability & Network Configuration
- **Affected Files**:
  - `backend/app/api/v1/auth.py` (lines 32, 60, 93, 117)
  - `backend/app/algorithms/itinerary_generator.py` (lines 101–103)
  - `scripts/import_osm.py`
  - `scripts/seed_featured_places.py`
  - `scripts/db_backup_restore.py`
- **Description**:
  1. SlowAPI uses `get_remote_address` (`request.client.host`). When traffic is proxied through `cloudflared`, all remote requests appear as `127.0.0.1`, placing all remote users in a single shared 5 req/min rate limit bucket.
  2. `itinerary_generator.py` queries `db.scalars(select(Place)).all()`, loading all 4,400+ places into memory on every request.
  3. `import_osm.py` and `seed_featured_places.py` run individual queries per place in a loop ($O(N)$ round trips).
  4. `db_backup_restore.py` fails restore on existing tables because `pg_dump` lacks `--clean --if-exists`.
- **Remediation**:
  - Configure SlowAPI key function: if `request.client.host == "127.0.0.1"` and `CF-Connecting-IP` header is present, key on `CF-Connecting-IP`.
  - Filter candidate places in SQL query using bounding box or municipality radius before loading into memory.
  - Batch place lookups in seeding scripts using `in_()`.
  - Add `--clean --if-exists` to `pg_dump` command.

---

### CR-014: Outdated E2E Test Suite, Dead Starter Files & Acceptance Script Tautologies
- **Severity**: Low
- **Category**: Code Quality / Test Accuracy
- **Affected Files**:
  - `Project/e2e/app.spec.ts`
  - `Project/src/app/tab1/`, `tab2/`, `tab3/`, `explore-container/`
  - `scripts/verify_acceptance_gate.py`
  - `scripts/setup_steps_0_to_2.py`
- **Description**:
  1. `Project/e2e/app.spec.ts` tests for `'Tab 1 page'`, failing on modern build.
  2. 16 unused starter template files remain in `Project/src/app/`.
  3. `verify_acceptance_gate.py` contains 7 tautological checks (`True` or `or True` fallbacks).
  4. `setup_steps_0_to_2.py` contains destructive `DROP TABLE` statements that risk accidental invocation.
- **Remediation**:
  - Rewrite `app.spec.ts` to test `/welcome` -> `/guest` -> `/tabs/home` flow.
  - Delete 16 unused starter files and `setup_steps_0_to_2.py`.
  - Strengthen assertions in `verify_acceptance_gate.py` to test actual conditions.

---

### CR-015: Profile Memory Leak, Non-Functional Buttons, Hardcoded Bongabon & UI Typos
- **Severity**: Low
- **Category**: UI Polish / Frontend Maintenance
- **Affected Files**:
  - `Project/src/app/features/profile/profile.page.ts` (lines 25–33)
  - `Project/src/app/features/login/login.page.html` (lines 45–55)
  - `Project/src/app/core/services/place.service.ts` (lines 162–182)
  - `Project/src/app/features/welcome/welcome.page.html` (line 15)
  - `Project/src/app/features/guest/guest.page.html` (line 16)
  - `Project/src/app/features/login/login.page.html` (line 36)
  - `Project/src/assets/images/`
- **Description**:
  1. `ProfilePage` subscribes to `currentUser$` without unsubscribing on destroy.
  2. "Continue with Google" and "Forgot password?" buttons on login page lack click handlers or disabled indicators.
  3. `PlaceService.getNearbyPlaces()` hardcodes Bongabon coordinates for all queries.
  4. Typos in UI text: "iternaries", "won't be save", "Remeber me".
  5. 44 unused SHA-1 hash image files in assets.
- **Remediation**:
  - Store `Subscription` in `ProfilePage` and unsubscribe in `ngOnDestroy`.
  - Wire handlers or disable buttons with truthful tooltips.
  - Query nearby places based on destination coordinates.
  - Correct typos in templates and prune unused asset files.

---

### CR-016: Documentation Drift & Milestone Status Discrepancies
- **Severity**: Informational
- **Category**: Documentation Integrity
- **Affected Files**:
  - `docs/KNOWN_ISSUES.md`
  - `docs/DEVELOPMENT_PLAN.md`
  - `docs/TESTING_DOCUMENTATION.md`
- **Description**: Several documentation files listed Milestones 4 through 9 as pending, conflicting with completed Phase 10 verification records.
- **Remediation**:
  - Synchronize all documentation files with current completed state (Phases 0–10).
  - Add dedicated Audit section and roadmap for Phases 11–14.

---

## 4. Remediation Roadmap Alignment

| Phase | Priority Level | Target Findings | Primary Objective |
| :---: | :--- | :--- | :--- |
| **Phase 11** | **Priority 1 (Critical)** | `CR-001`, `CR-002`, `CR-003`, `CR-004`, `CR-005` | Security authorization, data loss prevention, authentication hardening |
| **Phase 12** | **Priority 2 (High)** | `CR-006`, `CR-007`, `CR-008`, `CR-009`, `CR-010`, `CR-011`, `CR-012` | Token refresh, timezone accuracy, generator radius/budget, API completeness |
| **Phase 13** | **Priority 3 (Medium)** | `CR-014` (part), `CR-015`, `CR-016` | Starter file pruning, UI typos, memory leaks, doc synchronization |
| **Phase 14** | **Priority 4 (Low/Long-term)** | `CR-013`, `CR-014` (E2E) | Cloudflare Tunnel rate limiting, generator SQL pre-filtering, modern E2E spec |

