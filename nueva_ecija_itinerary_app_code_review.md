# Comprehensive Code Review Report: `edselrenz/itinerary-app`

**Repository:** `edselrenz/itinerary-app` (Commit `43d55225016775814a05be2671501190f86ab3ec`)  
**Application Name:** Nueva Ecija Travel Itinerary Application (MVP / Pilot Build `v0.9.0-alpha`)  
**Review Scope:** Full-Stack Static Architecture, Logic, Security, Database, Performance, Dependency, and Testing Audit  
**Verification Mode:** Complete static source inspection across all repository files and Python AST compilation (`python3 -m py_compile` across all `.py` modules). Runtime execution of `pytest` and `ng test`/`playwright` was not performed inside the isolated review sandbox because external network access is disabled and `node_modules` / Python virtual environments were excluded from the archive.

## A. Executive Summary

### Application Purpose
The **Nueva Ecija Travel Itinerary Application** ("Trip mo, trip ko") is a hybrid mobile and web travel-planning platform scoped exclusively to the province of Nueva Ecija, Central Luzon, Philippines. It enables travelers—either as authenticated account holders or local-first anonymous guests—to search provincial Points of Interest (POIs), explore an interactive OpenStreetMap/Leaflet map across 16 canonical categories, generate deterministic multi-day suggested itineraries based on Haversine geographic clustering and PHP daily budgets, author custom multi-day itineraries (including off-grid custom stops), and hand off turn-by-turn directions to external Google Maps URLs without incurring paid mapping, geocoding, or generative-AI API costs.

### Technologies and Architecture
- **Frontend (`Project/`):** Ionic Framework (`^9.0.0`) with Angular standalone components, Capacitor (`8.6.0`), RxJS (`~7.8.0`), `@ionic/storage-angular` (`^4.0.0`) for offline guest persistence, and Leaflet (`^1.9.4`) + `leaflet.markercluster` (`^1.5.3`) for bounded map rendering. Deployed statically to GitHub Pages via GitHub Actions (`.github/workflows/deploy.yml`).
- **Backend (`backend/`):** Python 3.11+ with FastAPI (`>=0.115.0`), Pydantic v2 (`>=2.8.0`), SQLAlchemy 2.0 ORM (`>=2.0.30`), Alembic (`>=1.13.2`), `pwdlib[argon2]` for Argon2id password hashing, `pyjwt` for HMAC-SHA256 JWTs, `google-auth` for Google ID token verification, and `slowapi` (`>=0.1.9`) for IP-based rate limiting.
- **Database & Data Pipeline (`docker-compose.yml`, `scripts/`):** PostgreSQL 16 (`postgres:16-alpine`) in production/pilot with portable `JsonType` and `sa.Uuid` fallback to SQLite for local development and unit tests. Offline ETL scripts (`scripts/import_osm.py`, `scripts/seed_featured_places.py`, `scripts/db_backup_restore.py`) handle OSM Overpass ingestion, curated seeding, and backup/restore drills.

### Overall Implementation Quality
The codebase demonstrates thoughtful adherence to several core MVP engineering principles: SQLAlchemy 2.0 typed models, portable PostgreSQL/SQLite types, Argon2id password hashing, case-insensitive user normalization, honest null-cost math (`calculateBudgetSummary`), and an offline-first fallback strategy. However, beneath the surface of passing unit tests and polished Figma screens, **critical security vulnerabilities, broken core workflows, and data-corrupting logic defects** exist in the actual implementation.

### Summary of Findings by Severity

| Severity | Count | Issue IDs | Key Themes |
| :--- | :---: | :--- | :--- |
| **CRITICAL** | 2 | `CR-001`, `CR-002` | Cross-user BOLA/IDOR stop theft, data exposure, and cross-itinerary stop deletion in `itineraries.py` |
| **HIGH** | 5 | `CR-003` – `CR-007` | Editing saved itineraries silently drops all day/stop changes; hardcoded JWT secret fallback & wildcard CORS; Google OAuth unverified-email account takeover & inactive-user bypass; dead refresh-token lifecycle causing silent data diversion after 30 minutes; UTC/local timezone off-by-one date shifting |
| **MEDIUM** | 6 | `CR-008` – `CR-013` | Suggested itinerary cross-day anchor drift & budget overflow; guest mode bypassing backend `/suggest` & hardcoded UI tags/budgets; dead `ItineraryItemUpdate` schema & missing stop-edit endpoint; Map tab ignoring route query params, viewport bounds, & `tileerror`; unvalidated custom API URL token exfiltration; Cloudflare Tunnel shared IP rate-limit lockout & $N+1$ import queries |
| **LOW** | 2 | `CR-014`, `CR-015` | Broken Playwright E2E spec (`Tab 1 page`), 16 dead starter files, hardcoded `True` assertions in `verify_acceptance_gate.py`, destructive `setup_steps_0_to_2.py`, memory leak in `ProfilePage`, non-functional Google/Forgot-Password buttons, Bongabon-only nearby places, and 44 unused hash images |
| **INFORMATIONAL** | 1 | `CR-016` | Non-standard/future package versions in `Project/package.json` (`@angular/core@22.2.3`) and documentation drift across `docs/` |

### Production Readiness Assessment
**NOT READY FOR PRODUCTION (CHANGES REQUIRED BEFORE PILOT).** The application contains two **Critical** Broken Object Level Authorization (BOLA / IDOR) vulnerabilities (`CR-001`, `CR-002`) that allow any authenticated user to steal or delete stops belonging to other users' itineraries, along with five **High** severity functional and security defects—including complete loss of day/stop edits when saving an existing itinerary (`CR-003`) and silent session expiration after 30 minutes (`CR-006`).

## B. Repository Overview

The repository is structured as a single monorepo combining the backend API, hybrid frontend client, offline data scripts, and documentation:

| Directory / File Path | Architectural Role & Responsibilities |
| :--- | :--- |
| `backend/app/main.py` | FastAPI application factory, SlowAPI rate-limiting middleware, CORS configuration, router mounting (`/api/v1/auth`, `/api/v1/places`, `/api/v1/itineraries`), and `GET /api/v1/health`. |
| `backend/app/core/` | `config.py` (Pydantic `BaseSettings` reading `.env`), `database.py` (SQLAlchemy 2.0 `engine`, `SessionLocal`, `Base`, and `get_db` generator), and `limiter.py` (SlowAPI `Limiter` keyed by `get_remote_address`). |
| `backend/app/models/entities.py` | Declarative SQLAlchemy 2.0 ORM models for all 7 tables: `User`, `AuthIdentity`, `Municipality`, `Place`, `Itinerary`, `ItineraryDay`, and `ItineraryItem`. |
| `backend/app/schemas/` | Pydantic v2 request/response validation schemas for authentication (`auth.py`), municipalities and POIs (`place.py`), and multi-day itineraries (`itinerary.py`). |
| `backend/app/services/auth_service.py` | Argon2id password hashing/verification, JWT access/refresh creation and decoding, user registration/login, Google ID token verification, and `get_current_user` / `get_current_user_optional` dependencies. |
| `backend/app/algorithms/itinerary_generator.py` | Deterministic Haversine distance calculator, preference-to-category mapper, geographic anchor resolver, candidate POI scorer, and multi-day itinerary draft generator. |
| `backend/app/api/v1/` | REST controllers for authentication (`auth.py`), municipality/place search (`places.py`), and itinerary CRUD, day/stop additions, deletion, reordering, and suggestion (`itineraries.py`). |
| `backend/alembic/` | Alembic migration environment (`env.py`) and initial schema revision (`versions/0001_initial_nueva_ecija_schema.py`). |
| `backend/tests/` | Pytest integration suites using in-memory SQLite (`test_foundation.py`, `test_auth.py`, `test_itineraries.py`, `test_backup_restore.py`). |
| `Project/src/app/core/` | Angular singleton services (`AuthService`, `PlaceService`, `ItineraryService`, `GuestStorageService`, `GuestMigrationService`, `ConnectivityService`), HTTP interceptor (`authInterceptor`), and TypeScript models. |
| `Project/src/app/features/auth/` | Standalone onboarding and authentication pages (`welcome/`, `guest/`, `login/`, `signup/`). |
| `Project/src/app/features/itinerary/` | Standalone itinerary planning pages: `suggested-wizard/` (3-view suggested flow), `custom-builder/` (3-view custom builder), and `itinerary-detail/` (saved itinerary overview, day timeline, stop modal, and nearby places). |
| `Project/src/app/tabs/` | 4-tab navigation shell (`tabs.page.*`, `tabs.routes.ts`) and active tab pages: `home/`, `map/`, `history/`, and `profile/`. Also contains unused legacy starter folders `Project/src/app/tab1/`, `tab2/`, `tab3/`, and `explore-container/`. |
| `scripts/` | Operational CLI tools: `import_osm.py` (Overpass JSON importer), `seed_featured_places.py` (seeds 12 municipalities and 17 featured POIs), `db_backup_restore.py` (backup/verify/restore/drill), `setup_postgres.py`, `verify_acceptance_gate.py`, and PowerShell server/tunnel launchers (`start_server.ps1`, `stop_server.ps1`, `start_postgres.ps1`). |
| `docs/` | 13 Markdown documentation files tracking architecture, API contracts, database schema, changelog, and development logs, alongside root specification files (`nueva_ecija_travel_itinerary_mvp_plan.docx`, `nueva_ecija_travel_itinerary_build_guide.pdf`, `Travel Itinerary App.fig`). |

## C. Architecture Assessment

### End-to-End Component Interaction & Data Flows
1. **Authentication & Session Lifecycle:**
   - A user registers (`POST /api/v1/auth/register`) or logs in (`POST /api/v1/auth/login`). `auth_service.py` normalizes `email` and `username` via `.strip().lower()`, verifies/hashes passwords with Argon2id, and returns an access JWT (30 min), refresh JWT (7 days), and serialized `UserOut`.
   - On the client, `AuthService` persists `ne_access_token`, `ne_refresh_token`, and `ne_user_profile` in `localStorage`. `LoginPage` and `SignupPage` invoke `GuestMigrationService.migrateGuestData()`, which reads any device-local trips from `GuestStorageService` (`@ionic/storage-angular` key `ne_guest_itineraries_v1`), posts them to `POST /api/v1/itineraries`, and clears guest storage.
   - `authInterceptor` attaches `Authorization: Bearer <token>` to outgoing `HttpClient` requests and updates `ConnectivityService.setHostOffline(true/false)` when network/gateway errors (`0`, `502`, `504`) occur.
2. **POI Search & Map Discovery:**
   - `HomePage` binds a `FormControl` with `debounceTime(300)`, `distinctUntilChanged()`, and `switchMap()` to `PlaceService.searchPlaces({ q, limit: 20 })`, which calls `GET /api/v1/places`.
   - `MapPage` initializes a Leaflet map bounded to `[[15.05, 120.55], [16.25, 121.55]]` and queries `PlaceService.searchPlaces({ categories, limit: 100 })`, rendering custom HTML vector pins inside a `L.MarkerClusterGroup`.
   - If the backend is unreachable, `PlaceService` catches HTTP errors and returns a hardcoded 13-item `curatedOfflinePlaces` array.
3. **Itinerary Generation, Authoring & Persistence:**
   - **Suggested Flow:** `SuggestedWizardPage` collects destination, dates, daily budget, and preferences, calling `ItineraryService.suggestItinerary()`. When authenticated, it posts to `POST /api/v1/itineraries/suggest` (with a 4-second timeout fallback to `generateOfflineSuggestedItinerary()`); when unauthenticated, it immediately runs `generateOfflineSuggestedItinerary()` on the client. Clicking "Accept & Save" calls `ItineraryService.createItinerary()`.
   - **Custom Flow:** `CustomBuilderPage` collects trip details, lets users toggle places per day or add custom venues, and calls `createItinerary()` (for new trips) or `updateItinerary()` (for existing trips).

### Architectural Strengths
- **Zero-Paid-API Compliance:** Strictly avoids paid Google Maps/Places/Routes and paid LLM APIs by combining local database search, OpenStreetMap raster tiles, deterministic Haversine scoring, and keyless Google Maps URL hand-offs.
- **Database Portability:** `JsonType = JSON().with_variant(JSONB(), "postgresql")` and `Uuid(as_uuid=True)` allow the exact same SQLAlchemy 2.0 models to run against PostgreSQL 16 in production and in-memory SQLite in tests.
- **Honest Null-Cost Accounting:** Both backend and frontend distinguish `null` (unverified) venue costs from `0` (free), preventing misleading budget totals.

### Architectural Weaknesses and Risks
1. **Incomplete Dual-Mode Abstraction & Silent Split-Brain Storage:** `ItineraryService` wraps every authenticated HTTP call (`createItinerary`, `updateItinerary`, `deleteItinerary`, `addStop`, `deleteStop`, `reorderStops`, `refreshItineraries`) in a blanket `catchError(() => ...guestStorage...)`. It does not distinguish network offline errors (`status === 0`) from `401 Unauthorized`, `409 Conflict`, or `422 Unprocessable Entity`. When an authenticated user's access token expires after 30 minutes (`401`) or a validation error occurs (`422`), `ItineraryService` silently writes the authenticated user's data into local `GuestStorageService`, creating a split-brain state where the user thinks their changes are saved to their account, but they are actually trapped in guest storage.
2. **Missing Repository Layer & Controller-Embedded Data Access:** Despite Section 5.1 and Section 11 of the MVP Blueprint mandating a dedicated `backend/app/repositories/` data-access layer and `backend/app/services/` business-logic layer, `places.py` and `itineraries.py` embed raw SQLAlchemy queries and transaction `db.commit()` calls directly inside FastAPI route handlers. This direct query duplication directly contributed to the BOLA vulnerabilities in `delete_itinerary_item()` and `reorder_itinerary_items()`.
3. **Client/Server Algorithmic Duplication & Drift:** The suggested itinerary generator is implemented twice—once in Python (`backend/app/algorithms/itinerary_generator.py`) using Haversine clustering, and once in TypeScript (`ItineraryService.generateOfflineSuggestedItinerary`) using hardcoded 3-day Bongabon/Cabanatuan/Gapan presets that ignore preferences and budgets.

## D. Findings and Issues

### [CRITICAL] CR-001 — Cross-Itinerary Stop Tampering and Data Exposure (BOLA / IDOR) in `reorder_itinerary_items()`
- **Location:** `backend/app/api/v1/itineraries.py` (Lines 495–534; vulnerable query at lines 519–529)
- **Component:** `reorder_itinerary_items()`
- **Problem:** When processing a batch reorder request (`POST /api/v1/itineraries/{itinerary_id}/reorder`), the endpoint verifies that `itinerary_id` belongs to `current_user.id` (line 503) and that each target `reorder_entry.day_id` belongs to `itinerary.days` (lines 510–517). However, when looking up the stop to move (`reorder_entry.id`), line 519 executes `select(ItineraryItem).where(ItineraryItem.id == reorder_entry.id)` without verifying that the `ItineraryItem` currently belongs to one of `itinerary.days` (or belongs to `current_user.id`). It then overwrites `item.day_id = reorder_entry.day_id` and `item.sort_order = reorder_entry.sort_order` (lines 528–529) and commits.
- **Impact:** Any authenticated user (User B) can steal `ItineraryItem` records belonging to another user (User A) by supplying User A's `item.id` and User B's `day_id`. This corrupts User A's itinerary by removing their stop and attaches the stolen stop to User B's itinerary, returning User A's private `custom_title`, `custom_lat`, `custom_lng`, `notes`, and cost estimates in the HTTP response to User B.
- **Reproduction:**
  1. Authenticate as User A and create an itinerary containing a stop (`item_A_id`).
  2. Authenticate as User B and create an itinerary (`itin_B_id`) containing a day (`day_B_id`).
  3. As User B, send `POST /api/v1/itineraries/{itin_B_id}/reorder` with JSON body `{"items": [{"id": "<item_A_id>", "day_id": "<day_B_id>", "sort_order": 1}]}`.
  4. Observe HTTP `200 OK` returning User A's stop inside User B's itinerary, while User A's itinerary loses the stop.
- **Expected behavior:** The endpoint must reject any `reorder_entry.id` that does not currently belong to a day within the authenticated user's target `itinerary_id` with HTTP `400 Bad Request` or `404 Not Found`.
- **Actual behavior:** The endpoint moves any `ItineraryItem` in the entire database into the caller's itinerary day.
- **Recommendation:** Build a dictionary of valid item objects (`items_by_id`) from the eagerly loaded `itinerary.days` before iterating, or scope the `select(ItineraryItem)` query with `ItineraryItem.day_id.in_(valid_day_ids)`.
- **Suggested implementation:**
```python
@router.post("/{itinerary_id}/reorder", response_model=ItineraryOut)
def reorder_itinerary_items(
    itinerary_id: uuid.UUID,
    payload: ItineraryReorderIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ItineraryOut:
    # Batch reorders stops within or across days. Enforces strict BOLA protection.
    itinerary = db.scalar(get_eager_itinerary_stmt(itinerary_id, current_user.id))
    if not itinerary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Itinerary not found",
        )

    valid_day_ids = {day.id for day in itinerary.days}
    items_by_id = {
        item.id: item
        for day in itinerary.days
        for item in day.items
    }

    for reorder_entry in payload.items:
        if reorder_entry.day_id not in valid_day_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Target day {reorder_entry.day_id} does not belong to this itinerary.",
            )
        item = items_by_id.get(reorder_entry.id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Stop {reorder_entry.id} not found in this itinerary.",
            )
        item.day_id = reorder_entry.day_id
        item.sort_order = reorder_entry.sort_order

    db.commit()
    loaded = db.scalar(get_eager_itinerary_stmt(itinerary_id, current_user.id))
    return serialize_itinerary(loaded)
```

### [CRITICAL] CR-002 — Cross-Itinerary Stop Deletion (BOLA / IDOR) in `delete_itinerary_item()`
- **Location:** `backend/app/api/v1/itineraries.py` (Lines 446–492; missing day ownership check at lines 464–474)
- **Component:** `delete_itinerary_item()`
- **Problem:** `delete_itinerary_item()` verifies that `itinerary_id` is owned by `current_user.id` (line 457), then queries `ItineraryItem` using `where(ItineraryItem.id == item_id, ItineraryItem.day_id == day_id)` (lines 464–468). Unlike `add_itinerary_item()` (lines 392–397), `delete_itinerary_item()` never checks that `day_id` belongs to `itinerary_id` (`ItineraryDay.itinerary_id == itinerary_id`).
- **Impact:** An authenticated attacker (User B) can pass their own valid `itinerary_id` in the path while supplying another user's `day_id` and `item_id` (`DELETE /api/v1/itineraries/{user_B_itinerary_id}/days/{user_A_day_id}/items/{user_A_item_id}`), deleting User A's stop and mutating `sort_order` on User A's remaining stops.
- **Reproduction:**
  1. User A creates `itinerary_A` with `day_A` and `item_A`.
  2. User B creates `itinerary_B`.
  3. User B sends `DELETE /api/v1/itineraries/{itinerary_B}/days/{day_A}/items/{item_A}`.
  4. `itinerary_B` passes the ownership check; `item_A` is deleted from `day_A`.
- **Expected behavior:** `delete_itinerary_item()` must verify that `day_id` belongs to the authenticated user's `itinerary_id` before locating or deleting `item_id`.
- **Actual behavior:** Any stop in the database whose `(item_id, day_id)` pair matches is deleted regardless of which itinerary owns `day_id`.
- **Recommendation:** Verify `day_id in {d.id for d in itinerary.days}` before querying `ItineraryItem`.
- **Suggested implementation:**
```python
    valid_day_ids = {d.id for d in itinerary.days}
    if day_id not in valid_day_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Itinerary day not found in this itinerary",
        )

    item = db.scalar(
        select(ItineraryItem).where(
            ItineraryItem.id == item_id,
            ItineraryItem.day_id == day_id,
        )
    )
```

### [HIGH] CR-003 — Editing an Existing Itinerary in `CustomBuilderPage` Silently Discards All Day and Stop Modifications
- **Location:** `Project/src/app/features/itinerary/custom-builder/custom-builder.page.ts` (Lines 521–870, 910–988), `Project/src/app/core/services/itinerary.service.ts` (Lines 108–116, 338–364), and `backend/app/api/v1/itineraries.py` (Lines 275–312)
- **Component:** `CustomBuilderPage.saveItinerary()`, `ItineraryService.updateItinerary()`, and `PATCH /api/v1/itineraries/{itinerary_id}`
- **Problem:** When `CustomBuilderPage` loads an existing itinerary via `/custom-builder/:id` (`isEditMode = true`, lines 201–205), all day and stop operations (`addDay()`, `removeDay()`, `addPlaceStop()`, `addCustomVenueStop()`, `removeStop()`, `moveStopUp()`, `moveStopDown()`) mutate only the local in-memory `this.days` array without calling any sub-resource endpoints (`addStop`, `deleteStop`, `reorderStops`). When the user clicks **Save**, `saveItinerary()` constructs `payload` with `days` (lines 926–952), but at lines 954–962 branches on `this.isEditMode && this.itineraryId` and calls `this.itineraryService.updateItinerary(this.itineraryId, { title, destination, start_date, end_date, daily_budget })`, discarding `payload.days`, `payload.preferences`, and `payload.assumptions`. Furthermore, `PATCH /api/v1/itineraries/{id}` on the backend (`itineraries.py` lines 275–312) and `updateGuestItinerary()` on the frontend (`itinerary.service.ts` lines 338–364) only update top-level metadata fields and do not accept or update `days`.
- **Impact:** The primary itinerary editing workflow—including clicking **"Customize Itinerary in Builder"** from `ItineraryDetailPage` (`/itinerary/:id`) or `SuggestedWizardPage`—is completely broken for day and stop edits. Users can spend minutes adding, removing, or reordering stops on an existing itinerary, click Save, see a green success toast (`"Itinerary ... saved successfully!"`), and lose 100% of their day and stop changes.
- **Reproduction:**
  1. Create and save an itinerary (either in Guest Mode or while logged in).
  2. Open the saved itinerary and click **"Customize Itinerary in Builder"** (`/custom-builder/:id`).
  3. Add a place to Day 1, remove an existing stop, or add Day 2, then click **Save**.
  4. Open the itinerary again: all added/removed/reordered stops and days are gone.
- **Expected behavior:** Saving an edited itinerary in `CustomBuilderPage` must persist the updated `days` and `items` collection (as well as `preferences` and `assumptions`) in both backend PostgreSQL and local `GuestStorageService`.
- **Actual behavior:** Only `title`, `destination`, `start_date`, `end_date`, and `daily_budget` are updated; all changes to `days` and `items` are silently discarded.
- **Recommendation:** Extend `ItineraryUpdate` (backend schema), `update_itinerary()` (`backend/app/api/v1/itineraries.py`), `ItineraryUpdatePayload` (`itinerary.models.ts`), and `updateGuestItinerary()` (`itinerary.service.ts`) to accept an optional `days: list[ItineraryDayCreate]` replacement list, and pass `preferences`, `assumptions`, and `days` from `CustomBuilderPage.saveItinerary()`.
- **Suggested implementation:**
```python
# In backend/app/schemas/itinerary.py (ItineraryUpdate):
class ItineraryUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=160)
    destination: str | None = Field(None, max_length=120)
    start_date: date | None = None
    end_date: date | None = None
    daily_budget: float | None = Field(None, ge=0.0)
    preferences: list[str] | None = None
    assumptions: list[str] | None = None
    days: list[ItineraryDayCreate] | None = None

# In backend/app/api/v1/itineraries.py (update_itinerary):
    if payload.days is not None:
        itinerary.days.clear()
        db.flush()
        for day_payload in payload.days:
            day = ItineraryDay(
                itinerary_id=itinerary.id,
                day_number=day_payload.day_number,
                travel_date=day_payload.travel_date,
                title=day_payload.title,
            )
            db.add(day)
            db.flush()
            for item_payload in day_payload.items:
                db.add(
                    ItineraryItem(
                        day_id=day.id,
                        place_id=item_payload.place_id,
                        custom_title=item_payload.custom_title,
                        custom_lat=item_payload.custom_lat,
                        custom_lng=item_payload.custom_lng,
                        sort_order=item_payload.sort_order,
                        planned_time=item_payload.planned_time,
                        duration_minutes=item_payload.duration_minutes,
                        notes=item_payload.notes,
                        estimated_cost_min=item_payload.estimated_cost_min,
                        estimated_cost_max=item_payload.estimated_cost_max,
                    )
                )
```

### [HIGH] CR-004 — Hardcoded Fallback JWT Secret, Missing Google OAuth Audience Enforcement, and Overly Permissive CORS Regex
- **Location:** `backend/app/core/config.py` (Lines 12–28), `backend/app/main.py` (Lines 26–33), and `backend/app/services/auth_service.py` (Lines 158–173)
- **Component:** `Settings`, `CORSMiddleware`, and `verify_google_id_token()`
- **Problem:**
  1. `backend/app/core/config.py` (line 17) sets a default `jwt_secret_key: str = "dev_only_replace_before_pilot_with_openssl_rand_hex_32"` and `.env.example` (line 7) sets `JWT_SECRET_KEY=replace_with_64_char_hex_generated_via_openssl_rand_hex_32`. There is no validator rejecting these known placeholder strings when `app_env != "development"`, nor checking minimum key entropy.
  2. In `backend/app/services/auth_service.py` (lines 160–165), `verify_google_id_token()` calls `id_token.verify_oauth2_token(raw_id_token, google_requests.Request(), settings.google_oauth_client_id or None)`. Because `settings.google_oauth_client_id` defaults to `""` (`config.py` line 27), `settings.google_oauth_client_id or None` evaluates to `None`. In `google-auth`, passing `audience=None` disables audience (`aud`) verification, allowing an attacker to authenticate using a Google ID token issued for *any* arbitrary third-party Google OAuth application. Furthermore, line 172 leaks the raw internal exception string (`detail=f"Google token verification failed: {exc}"`) to the client.
  3. In `backend/app/main.py` (lines 28–30), `CORSMiddleware` sets `allow_origin_regex=r"^https://.*\.github\.io$"` with `allow_credentials=True`. Every GitHub user's Pages site (`https://attacker.github.io`) matches this regex.
- **Impact:**
  - If deployed to a pilot or production host without overriding `JWT_SECRET_KEY`, any attacker can sign arbitrary JWT access and refresh tokens with the public default key from GitHub.
  - If `GOOGLE_OAUTH_CLIENT_ID` is not set, `POST /api/v1/auth/oauth/google` accepts Google ID tokens minted for any other website/app.
  - Any malicious website hosted on `*.github.io` is granted cross-origin credentialed access to the backend API.
- **Reproduction:**
  1. Start the backend with `APP_ENV=pilot` and no `JWT_SECRET_KEY` in `.env`: the server starts without error using `"dev_only_replace_before_pilot_with_openssl_rand_hex_32"`.
  2. Call `POST /api/v1/auth/oauth/google` when `GOOGLE_OAUTH_CLIENT_ID=""` using a valid Google ID token obtained from another app's OAuth client: `verify_oauth2_token` skips audience validation because `audience=None`.
- **Expected behavior:**
  - Non-development environments must fail fast at startup if `jwt_secret_key` is a default placeholder or shorter than 32 bytes.
  - `verify_google_id_token()` must reject requests with `501 Not Implemented` or `401 Unauthorized` if `settings.google_oauth_client_id` is empty.
  - CORS must explicitly allow `https://edselrenz.github.io` via `cors_origins` instead of a wildcard `*.github.io` regex.
- **Actual behavior:** Insecure defaults silently remain active at runtime.
- **Recommendation:** Add a `@model_validator(mode="after")` on `Settings`, enforce `settings.google_oauth_client_id` before calling `verify_oauth2_token`, and replace `allow_origin_regex` with explicit origins in `cors_origins`.
- **Suggested implementation:**
```python
# In backend/app/core/config.py:
from pydantic import model_validator

INSECURE_JWT_DEFAULTS = {
    "dev_only_replace_before_pilot_with_openssl_rand_hex_32",
    "replace_with_64_char_hex_generated_via_openssl_rand_hex_32",
    "replace_with_output_of_openssl_rand_hex_32",
}

class Settings(BaseSettings):
    ...
    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        if self.app_env.lower() not in ("development", "test", "testing"):
            if self.jwt_secret_key in INSECURE_JWT_DEFAULTS or len(self.jwt_secret_key) < 32:
                raise ValueError(
                    "CRITICAL: A strong, non-default JWT_SECRET_KEY (>=32 chars) is required outside development."
                )
        return self

# In backend/app/services/auth_service.py:
def verify_google_id_token(raw_id_token: str) -> dict:
    # Server-side verification of Google OAuth ID token.
    if not settings.google_oauth_client_id.strip():
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google Sign-In is not configured on this server.",
        )
    try:
        idinfo = id_token.verify_oauth2_token(
            raw_id_token,
            google_requests.Request(),
            settings.google_oauth_client_id.strip(),
        )
        if idinfo.get("iss") not in ("accounts.google.com", "https://accounts.google.com"):
            raise ValueError("Invalid Google token issuer")
        if not idinfo.get("email_verified", False):
            raise ValueError("Google email address is not verified")
        return idinfo
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google token verification failed",
        )
```

### [HIGH] CR-005 — Unverified Email Account Takeover and Deactivated Account (`is_active=False`) Bypass in Google OAuth
- **Location:** `backend/app/services/auth_service.py` (Lines 176–229)
- **Component:** `authenticate_google_user()`
- **Problem:**
  1. When `authenticate_google_user()` finds an existing `AuthIdentity` (lines 189–190), it immediately returns `identity.user` without checking `if not identity.user.is_active`.
  2. When no `AuthIdentity` exists yet, lines 193–196 look up an existing `User` by `User.email_normalized == norm_email` and automatically link the Google identity to that existing account without checking whether `info.get("email_verified")` is `True`, without checking `user.is_active`, and without handling `IntegrityError` on `db.commit()`.
- **Impact:**
  - Any user account that has been deactivated (`is_active = False`), which is blocked from password login (`auth_service.py` lines 150–154) and token refresh (`auth.py` line 91), can still log in and receive fresh tokens via `POST /api/v1/auth/oauth/google`.
  - If an OAuth token contains an unverified email matching an existing user's email, the account is automatically linked and hijacked.
- **Reproduction:**
  1. Set a user's `is_active = False` in the `users` table.
  2. Call `POST /api/v1/auth/login` with their password -> rejected with `403 Forbidden ("Account is inactive")`.
  3. Call `POST /api/v1/auth/oauth/google` with their Google ID token -> succeeds with `200 OK` and issues new tokens.
- **Expected behavior:** `authenticate_google_user()` must require `info.get("email_verified") is True` before email-based account linking and must reject inactive users (`not user.is_active`) with HTTP `403 Forbidden`.
- **Actual behavior:** `authenticate_google_user()` skips both `email_verified` and `user.is_active` checks.
- **Recommendation:** Enforce `email_verified` in `verify_google_id_token()` and check `if not user.is_active: raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")` in `authenticate_google_user()` before issuing tokens.

### [HIGH] CR-006 — Unimplemented Frontend Refresh Token Rotation and Silent Split-Brain Fallback on `401 Unauthorized`
- **Location:** `Project/src/app/core/interceptors/auth.interceptor.ts` (Lines 7–38), `Project/src/app/core/services/auth.service.ts` (Lines 38–95), and `Project/src/app/core/services/itinerary.service.ts` (Lines 43–192)
- **Component:** `authInterceptor`, `AuthService.isAuthenticated()`, and `ItineraryService` error handlers
- **Problem:**
  1. The backend issues access tokens that expire after 30 minutes (`access_token_expire_minutes: int = 30`) and refresh tokens valid for 7 days (`POST /api/v1/auth/refresh`).
  2. On the frontend, `AuthService.getRefreshToken()` (`auth.service.ts` line 42) is never called anywhere in the codebase. `authInterceptor` (`auth.interceptor.ts` lines 27–36) never intercepts `401 Unauthorized` responses to call `/api/v1/auth/refresh` or log the user out.
  3. `AuthService.isAuthenticated()` (`auth.service.ts` lines 46–48) only checks `!!this.getAccessToken() && !!this.currentUserSubject.value` without inspecting the JWT `exp` claim.
  4. When the access token expires after 30 minutes, `AuthService.isAuthenticated()` remains `true`. Every subsequent call in `ItineraryService` (`refreshItineraries`, `createItinerary`, `updateItinerary`, `deleteItinerary`, `addStop`, `deleteStop`, `reorderStops`) receives HTTP `401 Unauthorized` from FastAPI, hits `catchError(() => ...)`, and **silently falls back to `GuestStorageService`** instead of refreshing the token or prompting re-authentication!
- **Impact:** Thirty minutes after logging in, an authenticated traveler's session silently breaks: their saved server itineraries disappear from the Home and History tabs (replaced by whatever is in local `GuestStorageService`), and any new itineraries they create are written to local guest storage instead of PostgreSQL, violating Section 13.5 of the MVP Blueprint (*"expired sessions are handled safely"*).
- **Reproduction:**
  1. Log in as a registered user and create an itinerary (saved in PostgreSQL).
  2. Wait 30 minutes (or set `ACCESS_TOKEN_EXPIRE_MINUTES=1`).
  3. Reload the app or create a new itinerary: `GET /api/v1/itineraries` and `POST /api/v1/itineraries` return `401 Unauthorized`, `authInterceptor` does not refresh the token, and `ItineraryService` silently switches to `GuestStorageService`.
- **Expected behavior:** When an authenticated request fails with `401 Unauthorized`, `authInterceptor` should attempt a token refresh via `POST /api/v1/auth/refresh` using `refresh_token` and retry the failed request; if the refresh token is also expired/invalid, it must call `authService.logout()` and redirect to `/login`. Furthermore, `ItineraryService` should only fall back to offline guest storage on network/gateway errors (`status === 0 || status === 502 || status === 504`), not on `401`/`403`/`409`/`422` client errors.
- **Actual behavior:** `refresh_token` is never used, expired access tokens remain in `localStorage` indefinitely, and `401` errors trigger silent fallback to local guest storage.
- **Recommendation:** Add a `refreshSession()` method to `AuthService`, handle `401` token rotation inside `authInterceptor` (excluding `/auth/login`, `/auth/register`, and `/auth/refresh`), and restrict `ItineraryService` offline fallbacks to network connectivity failures.
- **Suggested implementation:**
```typescript
// In Project/src/app/core/services/auth.service.ts:
public refreshSession(): Observable<AuthResponse> {
  const refreshToken = this.getRefreshToken();
  if (!refreshToken) {
    this.logout();
    return throwError(() => new Error('No refresh token available'));
  }
  return this.http
    .post<AuthResponse>(`${environment.apiBaseUrl}/auth/refresh`, {
      refresh_token: refreshToken,
    })
    .pipe(tap((res) => this.handleAuthSuccess(res)));
}
```

### [HIGH] CR-007 — Timezone Off-By-One Date Shifting in ISO Date Parsing and Serialization
- **Location:**
  - `Project/src/app/features/itinerary/suggested-wizard/suggested-wizard.page.ts` (Lines 98, 128–137, 194–200, 217–230, 239–245, 253–268, 277–290)
  - `Project/src/app/features/itinerary/custom-builder/custom-builder.page.ts` (Lines 118, 185–194, 225–244, 292–298, 315–329, 339–346, 351–389, 399–416, 523–529)
  - `Project/src/app/features/itinerary/itinerary-detail/itinerary-detail.page.ts` (Lines 190–201)
  - `Project/src/app/core/services/itinerary.service.ts` (Lines 525–528, 824–828)
- **Component:** Date initialization, preset duration calculation, day-date generation, and friendly date formatting
- **Problem:**
  1. **UTC vs. Local Date Initialization:** `new Date().toISOString().split('T')[0]` is used to compute "today" (`minDate`, `start_date`, `end_date`). Because `toISOString()` always outputs UTC, any user in the Philippines (`Asia/Manila`, `UTC+8`) using the app between `00:00` and `07:59` local time gets **yesterday's calendar date** as the default start date and minimum selectable date.
  2. **Mixed UTC Parsing (`new Date("YYYY-MM-DD")`) and Local Getters/Setters:** Under the ECMAScript specification, `new Date("2026-11-15")` (a date-only ISO string) is parsed as **UTC midnight** (`2026-11-15T00:00:00.000Z`), whereas `.getDate()`, `.setDate()`, `.getFullYear()`, and `.toLocaleDateString()` operate in the browser's **local timezone**. In any timezone west of UTC (or when mixing `.setDate(start.getDate() + i)` with `.toISOString().split('T')[0]`), `start.getDate()` and `setDate()` shift the calendar date by 1 day.
- **Impact:** Travel dates displayed in headers, date-picker popups, preset buttons (`2 Days (1N)`, `3 Days (2N)`), and generated `ItineraryDay.travel_date` records can be off by 1 day from what the traveler selected.
- **Reproduction:**
  1. In `Asia/Manila` (`UTC+8`) at `06:00 AM` on `2026-10-31`, open `/suggested-wizard`: `minDate` and `start_date` initialize to `2026-10-30` (yesterday) because `2026-10-31T06:00:00+08:00` is `2026-10-30T22:00:00Z`.
  2. In any negative UTC offset (e.g., `America/Los_Angeles`), select `2026-11-15` in the date picker: `displayDateRangeText` and `formatFriendlyDate("2026-11-15")` render `Nov 14, 2026` and `setPresetDuration(2)` sets `popupEndDate` to `2026-11-15` instead of `2026-11-16`.
- **Expected behavior:** All calendar date strings (`YYYY-MM-DD`) must be constructed, incremented, and formatted using local calendar year/month/day components without UTC midnight conversion.
- **Actual behavior:** `new Date("YYYY-MM-DD")` and `.toISOString().split('T')[0]` mix UTC and local time methods across 4 files.
- **Recommendation:** Introduce a small date utility in `Project/src/app/core/` that parses `"YYYY-MM-DD"` into local `new Date(year, month - 1, day)` and formats `Date` objects using local `getFullYear()`, `getMonth() + 1`, and `getDate()`.
- **Suggested implementation:**
```typescript
// Helper functions for timezone-safe local YYYY-MM-DD manipulation:
export function toLocalIsoDate(d: Date = new Date()): string {
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export function parseLocalIsoDate(dateStr: string): Date {
  const [y, m, d] = dateStr.split('-').map(Number);
  return new Date(y, (m || 1) - 1, d || 1);
}

export function addLocalDays(dateStr: string, daysToAdd: number): string {
  const d = parseLocalIsoDate(dateStr);
  d.setDate(d.getDate() + daysToAdd);
  return toLocalIsoDate(d);
}
```

### [MEDIUM] CR-008 — Backend Suggested Itinerary Generator Mutates Anchor Without Radius Bounds and Violates Daily Budget Constraints
- **Location:** `backend/app/algorithms/itinerary_generator.py` (Lines 64–133, 174–265) and `backend/app/core/config.py` (Line 29)
- **Component:** `generate_suggested_itinerary_data()` and `score_place()`
- **Problem:**
  1. **Unused `default_dest_radius_km` & Unbounded Distance Selection:** `settings.default_dest_radius_km` (`25.0` km) is defined in `backend/app/core/config.py` (line 29), and Section 8.2 of the MVP Blueprint states: *"Select eligible active POIs inside Nueva Ecija and within a configurable radius/municipality range of the requested destination."* However, `itinerary_generator.py` never imports `settings` or filters out candidates beyond `default_dest_radius_km`. Instead, `score_place()` (line 121) computes `max(0.0, 30.0 - (dist * 1.2))`, meaning any POI beyond 25 km gets `0.0` proximity points—so a featured POI 60 km away on the opposite side of Nueva Ecija still scores `50 + 40 (pref) + 20 (featured) = 110` and gets scheduled on the same day, causing severe cross-province backtracking!
  2. **Per-Stop Instead of Cumulative Daily Budget Check:** In `score_place()` (lines 128–130), `if place.estimated_cost_max <= daily_budget: score += 10.0` compares each individual stop's max cost against the *entire* `daily_budget` rather than tracking the remaining daily budget across the 3 stops of that day.
  3. **Day Title Mismatch When Anchor Drifts:** `current_anchor_lat`/`lng` are updated to the last stop of Day $N$ and carried over to Day $N+1$ (lines 223–224), which is good for multi-day progression, but `assumptions` (line 270) claims *"Stops on each day are clustered around {resolved_area}"* even when Day 2 or Day 3 has drifted to a different municipality.
  4. **Unescaped SQL `LIKE` Wildcards:** `resolve_geographic_anchor()` (lines 71–72, 79) and `backend/app/api/v1/places.py` (lines 78, 106) pass unescaped user strings into `.ilike(f"%{q}%")`, allowing `%` or `_` characters in user input to act as SQL wildcards.
- **Impact:** Suggested itineraries generated by the backend can schedule stops 50+ km apart on the same day and exceed the user's daily PHP budget by up to 3x while still awarding budget-fit bonus points.
- **Reproduction:**
  1. Seed places across General Tinio (south) and Pantabangan (north, ~60 km away).
  2. Request `POST /api/v1/itineraries/suggest` with `destination="Bongabon"`, `daily_budget=2500`, `preferences=["resort", "nature"]`.
  3. Observe that once local matching stops are picked, `score_place()` selects featured stops across distant municipalities on the same day and gives `+10.0` cost fit to multiple stops that each cost ₱2,500 (totaling ₱5,000+ in a single day).
- **Expected behavior:** Candidate POIs for a given day should prefer stops within `settings.default_dest_radius_km` of that day's anchor, and budget-fit scoring should compare `place.estimated_cost_max` (or `min`) against the *remaining* daily budget (`remaining_day_budget`).
- **Actual behavior:** No radius filter is applied and `daily_budget` is never decremented as stops are added to a day.
- **Recommendation:** Track `remaining_budget` per day inside `generate_suggested_itinerary_data()`, penalize or filter stops exceeding `settings.default_dest_radius_km` when closer candidates exist, and escape `%`/`_` in `ilike` queries.

### [MEDIUM] CR-009 — Frontend `suggestItinerary()` Bypasses Backend API in Guest Mode and Hardcodes Static Trip Metadata in `SuggestedWizardPage`
- **Location:** `Project/src/app/core/services/itinerary.service.ts` (Lines 198–228, 522–915) and `Project/src/app/features/itinerary/suggested-wizard/suggested-wizard.page.html` (Lines 133–143, 172)
- **Component:** `ItineraryService.suggestItinerary()`, `generateOfflineSuggestedItinerary()`, and `SuggestedWizardPage`
- **Problem:**
  1. **Backend `/suggest` bypassed for guests:** In `backend/app/api/v1/itineraries.py` (line 118), `POST /api/v1/itineraries/suggest` uses `Depends(get_current_user_optional)` specifically so anonymous/guest travelers can use the backend Haversine recommendation engine. However, `ItineraryService.suggestItinerary()` (`itinerary.service.ts` line 199) checks `if (!this.authService.isAuthenticated())` and immediately returns `this.generateOfflineSuggestedItinerary(request)` without ever calling the backend API—even when the backend server is running locally!
  2. **Offline generator ignores `preferences`, `daily_budget`, and most `destination` values:** In `generateOfflineSuggestedItinerary()` (`itinerary.service.ts` lines 785–840), `request.preferences` and `request.daily_budget` are never read when selecting stops. Regardless of whether the user selects `Nature & Parks`, `Shopping`, or a `₱500` budget, Day 1 always returns the exact same 4 Bongabon venues (`Rohi Paperflower Cafe`, `La Casa Prime Cabins` at ₱2,500–₱6,000, `Museo de Bongabon`, `Thornes Samgyupsal House`), Day 2 always returns Cabanatuan, and Day 3 always returns Gapan! Furthermore, if the user enters a specific municipality like `"Pantabangan"` or `"General Tinio"`, `isProvincialOrBongabon` (line 786) is `false`, so `dayPlaces` falls back to `curatedPool[0..2]` (lines 835–839)—which are still the Bongabon venues!
  3. **Duplicate item in `curatedPool`:** `'dest-la-casa-prime'` is defined twice in `curatedPool` (`itinerary.service.ts` lines 550–566 and 766–782).
  4. **Hardcoded budget and preference pills in `suggested-wizard.page.html`:** Lines 136–142 of `suggested-wizard.page.html` hardcode `<span class="trip-budget-range">₱ 3,000 - ₱ 5,000/day</span>` and hardcode the three pills `Food Trip`, `Cultural & History`, and `Resort` instead of binding to `generatedPlan.daily_budget` and `generatedPlan.preferences` (unlike `itinerary-detail.page.html` lines 60–68 which bind dynamically).
  5. **Clicking a stop card in `SuggestedWizardPage` opens Nearby Places instead of Stop Details:** In `suggested-wizard.page.html` (line 172), `<div class="figma-stop-card" (click)="openNearbyPlaces(stop)">` opens the generic Nearby Places list rather than a stop detail modal.
- **Impact:** Guest users (and any user when offline) receive a static, non-responsive itinerary that ignores their chosen destination (e.g., Pantabangan), budget, and preferences, and the preview header displays hardcoded `₱ 3,000 - ₱ 5,000/day` and `Food Trip / Cultural & History / Resort` tags regardless of what the user actually entered in the form.
- **Reproduction:**
  1. Open `/suggested-wizard` as a Guest.
  2. Enter Destination: `Pantabangan`, Daily Budget: `1000`, Preferences: `Nature & Parks` (unchecking `Food Trip`, `Culture & History`, `Resort`).
  3. Click **Find Itinerary**.
  4. Observe that the top card still displays `₱ 3,000 - ₱ 5,000/day` and `Food Trip | Cultural & History | Resort`, and Day 1 schedules Bongabon venues (`Rohi Paperflower Cafe`, `La Casa Prime Cabins`, `Museo de Bongabon`) instead of Pantabangan nature spots!
- **Expected behavior:** `suggestItinerary()` should attempt `POST /api/v1/itineraries/suggest` with a short timeout for both guest and authenticated users, falling back to `generateOfflineSuggestedItinerary()` only on network failure; `generateOfflineSuggestedItinerary()` must filter/score `curatedPool` by `request.destination`, `request.preferences`, and `request.daily_budget`; and `suggested-wizard.page.html` must bind dynamically to `generatedPlan.daily_budget` and `generatedPlan.preferences`.
- **Actual behavior:** Guest mode skips the backend `/suggest` endpoint entirely, the offline generator ignores destination/preferences/budget, and the preview header renders hardcoded strings.
- **Recommendation:** Remove the `if (!this.authService.isAuthenticated())` short-circuit in `suggestItinerary()` (relying on `timeout(4000)` + `catchError`), filter `curatedPool` by municipality, category preference, and budget in `generateOfflineSuggestedItinerary()`, and replace the hardcoded budget/tags in `suggested-wizard.page.html` with dynamic bindings matching `itinerary-detail.page.html`.

### [MEDIUM] CR-010 — Missing Stop Update Endpoint (`ItineraryItemUpdate` is Unused), `sort_order=1` Insertion Bug, and Foreign Key Validation Gap
- **Location:** `backend/app/schemas/itinerary.py` (Lines 16, 37–49) and `backend/app/api/v1/itineraries.py` (Lines 21, 186–236, 336–444)
- **Component:** `add_itinerary_item()`, `create_itinerary()`, and `ItineraryItemUpdate`
- **Problem:**
  1. **Missing `PATCH` endpoint for itinerary stops:** `ItineraryItemUpdate` is defined in `backend/app/schemas/itinerary.py` (lines 37–49) and imported in `backend/app/api/v1/itineraries.py` (line 21), but is never used. Neither a `PATCH /api/v1/itineraries/{id}/days/{day_id}/items/{item_id}` endpoint nor UI controls in `CustomBuilderPage` exist to edit a scheduled stop's `planned_time`, `duration_minutes`, `notes`, or `estimated_cost_min/max`.
  2. **`sort_order=1` bug in `add_itinerary_item()`:** Line 424 of `backend/app/api/v1/itineraries.py` computes `next_order = (max_order or 0) + 1 if payload.sort_order <= 1 else payload.sort_order`. Because `ItineraryItemBase.sort_order` defaults to `1` (`schemas/itinerary.py` line 16) rather than `None`, the backend cannot distinguish an omitted `sort_order` from an explicit `sort_order=1`, and even when `payload.sort_order > 1` is passed, existing items at or after that `sort_order` are not shifted, creating duplicate `sort_order` numbers.
  3. **Missing `place_id` existence check & duplicate `day_number` check in `create_itinerary()`:** If a client passes a non-existent `place_id` in `POST /api/v1/itineraries` or `POST /api/v1/itineraries/{id}/days/{day_id}/items`, or passes duplicate `day_number` entries in `ItineraryCreate.days`, `create_itinerary()` does not validate them beforehand, causing an unhandled `sqlalchemy.exc.IntegrityError` (`500 Internal Server Error`) on PostgreSQL.
  4. **Status code discrepancies with `docs/API_DOCUMENTATION.md`:** `add_itinerary_day()` (line 336) and `add_itinerary_item()` (line 376) omit `status_code=status.HTTP_201_CREATED` and return `200 OK`, whereas `docs/API_DOCUMENTATION.md` (lines 278, 303) specifies `201 Created`.
- **Impact:** Travelers cannot edit the planned time, duration, or notes of a stop once added to an itinerary, and malformed `place_id` or duplicate `day_number` payloads in `POST /api/v1/itineraries` crash with an unhandled `500 Internal Server Error`.
- **Reproduction:**
  1. Send `POST /api/v1/itineraries` with two days both having `"day_number": 1`: SQLAlchemy raises an unhandled `IntegrityError` on `uq_itinerary_day_num` (`500 Internal Server Error`).
  2. Attempt to update a stop's `notes` or `planned_time` via API: no `PATCH` route exists.
- **Expected behavior:** A `PATCH /{itinerary_id}/days/{day_id}/items/{item_id}` endpoint using `ItineraryItemUpdate` should exist; `sort_order: int | None = None` should default to `None` on `ItineraryItemCreate`; and `create_itinerary()` / `add_itinerary_item()` should validate `place_id` existence and unique `day_number` values cleanly with `404`/`422` responses.
- **Actual behavior:** `ItineraryItemUpdate` is unused dead code, and `IntegrityError` is unhandled in `itineraries.py`.
- **Recommendation:** Implement `PATCH /{itinerary_id}/days/{day_id}/items/{item_id}`, change `ItineraryItemCreate.sort_order` default to `None`, validate `place_id` against `Place`, and catch `IntegrityError` with `db.rollback()`.

### [MEDIUM] CR-011 — Map Tab Ignores Route Query Parameters (`Plan Route Here`), Viewport Bounding Boxes, Multi-Select Filters, and Provenance Fallbacks
- **Location:** `Project/src/app/tabs/map/map.page.ts` (Lines 97–355), `Project/src/app/tabs/map/map.page.html` (Lines 3–125), and `Project/src/app/tabs/home/home.page.ts` (Lines 429–434)
- **Component:** `MapPage` and `HomePage.startPlanningWithDestination()`
- **Problem:**
  1. **Broken "Plan Route Here" hand-off from Home tab:** In `HomePage.startPlanningWithDestination()` (`home.page.ts` lines 429–434), tapping **"Plan Route Here"** inside the destination detail modal navigates to `/tabs/map?destination=<name>&municipality=<municipality>`. However, `MapPage` does not inject `ActivatedRoute` or subscribe to `queryParams`. The query parameters are completely ignored!
  2. **No viewport bounding-box filtering or `tileerror` handling:** Despite the Build Guide (page 14) and `scripts/verify_acceptance_gate.py` (line 221) stating that `map.page.ts` listens to `tileerror` and `moveend` bounds, `map.page.ts` never attaches a `tileerror` listener to the `L.tileLayer` (lines 227–230) and never passes `min_lat`, `max_lat`, `min_lng`, `max_lng` to `PlaceService.searchPlaces()`.
  3. **Single-select category filter only:** `selectCategory(categoryKey)` (`map.page.ts` lines 347–354) overwrites a single `selectedCategory: string | null` instead of supporting multi-select category filtering or text search on the Map tab (Section 6.7 & 13.3 of the MVP Blueprint).
  4. **Missing provenance and `"Not verified / Not provided"` fallbacks in Map bottom sheet:** In `map.page.html` (lines 88–95), `*ngIf="selectedPlace.opening_hours"` and `*ngIf="selectedPlace.description"` simply hide missing fields instead of displaying `"Not verified / Not provided"`, and `source_name` / `verified_at` provenance metadata is completely omitted from the bottom sheet.
- **Impact:** Tapping "Plan Route Here" on the Home tab fails to focus or select the destination on the map; map tile failures fail silently without user feedback; and travelers cannot view data provenance or unverified-hours disclaimers on map markers.
- **Reproduction:**
  1. On `/tabs/home`, tap any Popular Destination card to open its modal, then tap **"Plan Route Here"**.
  2. The router navigates to `/tabs/map?destination=Minalungao%20National%20Park&municipality=General%20Tinio`, but the map remains at zoom 10 with no marker selected.
- **Expected behavior:** `MapPage` should read `ActivatedRoute.queryParams` on enter, select and pan/zoom to the matching `destination` place (or filter by `municipality`), attach a `tileerror` listener to display a non-blocking offline tile notice, and display provenance (`source_name`, `verified_at`) and `"Not verified / Not provided"` when `opening_hours` is null.
- **Actual behavior:** `queryParams`, `tileerror`, viewport bounds, and provenance fields are ignored in `MapPage`.
- **Recommendation:** Inject `ActivatedRoute` in `MapPage` to pan to and open the requested `destination` in `loadPlaces()`, add `tileLayer.on('tileerror', ...)` in `initMap()`, and render explicit fallback text and provenance in `map.page.html`.

### [MEDIUM] CR-012 — Unvalidated `ne_custom_api_url` Override Allows Arbitrary Backend Redirection and Bearer Token Exfiltration
- **Location:** `Project/src/app/app.component.ts` (Lines 49–59), `Project/src/app/core/services/connectivity.service.ts` (Lines 59–66), `Project/src/environments/environment.ts` & `environment.prod.ts` (Lines 1–13), and `Project/src/app/core/interceptors/auth.interceptor.ts` (Lines 13–19)
- **Component:** `configureApiUrl()`, `resolveApiBaseUrl()`, and `authInterceptor`
- **Problem:**
  1. `AppComponent.configureApiUrl()` prompts the user via `window.prompt()` for a custom backend URL and stores it raw in `localStorage.setItem('ne_custom_api_url', ...)` without validating that it is a valid `https://` or localhost `http://` URL.
  2. `authInterceptor` (`auth.interceptor.ts` lines 13–19) attaches `Authorization: Bearer ${token}` to **every** outgoing `HttpClient` request without checking whether `req.url` starts with `environment.apiBaseUrl`.
- **Impact:** If a user is socially engineered into pasting an untrusted URL into `[Set Server]` (or if any script writes to `ne_custom_api_url`), all subsequent API calls—including the user's `Bearer` access token and plaintext login/signup passwords—are sent to the untrusted server. Additionally, a malformed string in `ne_custom_api_url` breaks all `HttpClient` requests until `localStorage` is manually cleared.
- **Reproduction:**
  1. Click **[Set Server]** in the offline banner and enter `http://evil.example.com` or `not-a-valid-url`.
  2. Every subsequent `HttpClient` request is sent to `http://evil.example.com/api/v1/...` with `Authorization: Bearer <token>`.
- **Expected behavior:** `setCustomApiUrl()` must validate that the input is a well-formed URL using `new URL(input)` and restrict schemes to `https:` (or `http:` only for `localhost` / `127.0.0.1` / private LAN IPs `192.168.*` / `10.*`), and `authInterceptor` should only attach the `Authorization` header when `req.url.startsWith(environment.apiBaseUrl)`.
- **Actual behavior:** Arbitrary strings are persisted to `ne_custom_api_url` and `authInterceptor` attaches Bearer tokens unconditionally.
- **Recommendation:** Validate the URL scheme and host in `ConnectivityService.setCustomApiUrl()` and scope `authInterceptor` token injection to `req.url.startsWith(environment.apiBaseUrl)`.

### [MEDIUM] CR-013 — Shared IP Rate-Limiting Lockout Behind Cloudflare Tunnel, Full-Table Scan in `/suggest`, and $N+1$ Queries in Import Scripts
- **Location:**
  - `backend/app/core/limiter.py` (Lines 6–11)
  - `backend/app/algorithms/itinerary_generator.py` (Lines 157–163)
  - `scripts/import_osm.py` (Lines 220–242) & `scripts/seed_featured_places.py` (Lines 391–447)
- **Component:** `limiter`, `generate_suggested_itinerary_data()`, and `import_osm_payload()`
- **Problem:**
  1. **Proxy-unaware rate limiting:** `limiter.py` uses `get_remote_address` (`request.client.host`). When the backend is accessed through the Cloudflare Tunnel launched by `scripts/start_server.ps1` (`cloudflared tunnel --url http://127.0.0.1:8000`), `cloudflared` acts as a local reverse proxy, so every remote traveler's request arrives at Uvicorn with `request.client.host == "127.0.0.1"`. Consequently, all pilot users share a single `5/minute` rate-limit counter on `/auth/login`, `/auth/register`, and `/auth/oauth/google`.
  2. **Unbounded full-table load in `generate_suggested_itinerary_data()`:** Every call to `POST /api/v1/itineraries/suggest` executes `select(Place).where(Place.is_active == True).options(selectinload(Place.municipality))` (lines 157–163), loading the entire `places` table into Python memory and scoring every row in Python loops (`O(days * slots * N)`). Also, `POST /api/v1/itineraries/suggest` has no dedicated endpoint rate limit beyond the global 120/min default.
  3. **$N+1$ query loop in `scripts/import_osm.py`:** `import_osm_payload()` (lines 220–242) executes an individual `SELECT` statement inside the `for rec in validated_records:` loop for every single OSM element instead of pre-loading existing `(source_name, source_record_id)` pairs in one query.
- **Impact:** Under a Cloudflare Tunnel pilot, a single user mistyping their password 5 times blocks all other users from logging in or signing up for 60 seconds (`429 Too Many Requests`). As the OSM POI dataset grows to thousands of records, `/itineraries/suggest` and `import_osm.py` will experience avoidable database and CPU overhead.
- **Reproduction:**
  1. Start the server with `scripts/start_server.ps1` (Cloudflare Tunnel).
  2. From Device A, fail login 5 times.
  3. From Device B on a different network, attempt to log in or register: Device B immediately receives `429 Too Many Requests`.
- **Expected behavior:** When running behind a local loopback tunnel (`request.client.host == "127.0.0.1"`), the rate-limit key function should inspect `CF-Connecting-IP` (only when `request.client.host` is trusted loopback `127.0.0.1`), and `import_osm_payload()` should pre-fetch existing places by `(source_name, source_record_id)` in a single query.
- **Actual behavior:** All tunnel traffic shares the `127.0.0.1` bucket, and `import_osm.py` issues $N$ individual `SELECT` queries.
- **Recommendation:** Implement a loopback-aware key function in `backend/app/core/limiter.py` and batch-fetch existing `Place` records in `scripts/import_osm.py`.

### [LOW] CR-014 — Broken Playwright E2E Test (`Tab 1 page`), 16 Dead Starter Files, Hardcoded `True` Gate Checks, and Destructive `setup_steps_0_to_2.py`
- **Location:**
  - `Project/e2e/app.spec.ts` (Lines 1–6)
  - `Project/src/app/tab1/`, `Project/src/app/tab2/`, `Project/src/app/tab3/`, `Project/src/app/explore-container/` (16 files)
  - `scripts/verify_acceptance_gate.py` (Lines 161, 203, 222, 268, 273, 278, 283)
  - `setup_steps_0_to_2.py` (Lines 1–1797)
- **Component:** Test suite, dead starter components, and repository scripts
- **Problem:**
  1. **Outdated E2E test:** `Project/e2e/app.spec.ts` (line 5) still checks `await expect(page.locator('ion-content')).toContainText('Tab 1 page');`. Because the root route `/` redirects to `/welcome`, running `npm run test:e2e` (or `npm test`) fails.
  2. **16 dead starter files:** `tab1`, `tab2`, `tab3`, and `explore-container` are unused Ionic template files not wired to any route, yet their unit tests (`tab1.page.spec.ts`, `tab2.page.spec.ts`, `tab3.page.spec.ts`, `explore-container.component.spec.ts`) still run in Vitest and inflate the reported test count.
  3. **Tautological `True` checks in `scripts/verify_acceptance_gate.py`:** Seven of the 24 acceptance checks in `scripts/verify_acceptance_gate.py` cannot fail because they are hardcoded to `True` or `... or True`:
     - Line 161: `p6 = True`
     - Line 203: `p12 = "OpenStreetMap contributors" in settings.model_config.get("extra", "") or True`
     - Line 222: `p16 = True`
     - Line 268: `p20 = has_unpriced or True`
     - Line 273: `p21 = True`
     - Line 278: `p22 = True`
     - Line 283: `p23 = True`
  4. **Destructive root scaffolding script (`setup_steps_0_to_2.py`):** Executing `python setup_steps_0_to_2.py` overwrites `.gitignore`, `backend/app/main.py`, `backend/app/models/entities.py`, and `scripts/*` with early Milestone 2 code, wiping out authentication, itineraries, rate limiting, and relationships.
- **Impact:** `npm test` fails on the E2E stage, `verify_acceptance_gate.py` reports a false-positive 24/24 pass even if frontend/map/budget logic is broken, and accidentally running `setup_steps_0_to_2.py` destroys the backend application.
- **Recommendation:** Update `Project/e2e/app.spec.ts` to test the actual `/welcome` -> `/guest` -> `/tabs/home` flow, delete `tab1/`, `tab2/`, `tab3/`, `explore-container/`, and `setup_steps_0_to_2.py`, and replace the `or True` tautologies in `verify_acceptance_gate.py` with real assertions.

### [LOW] CR-015 — Unsubscribed Observable in `ProfilePage`, Non-Functional Auth Controls, Copy Typos, Bongabon-Only Nearby Places, and Asset Bloat
- **Location:**
  - `Project/src/app/tabs/profile/profile.page.ts` (Lines 67–72)
  - `Project/src/app/features/auth/login/login.page.html` (Line 80) & `login.page.ts` (Lines 50, 113–138)
  - `Project/src/app/features/auth/welcome/welcome.page.html` (Line 23)
  - `Project/src/app/features/auth/guest/guest.page.html` (Line 22)
  - `Project/src/app/features/itinerary/itinerary-detail/itinerary-detail.page.ts` (Line 237)
  - `Project/src/app/core/services/place.service.ts` (Lines 557–584)
  - `Project/src/assets/images/` & `Travel Itinerary App.fig`
- **Component:** Frontend pages, `PlaceService.getNearbyPlaces()`, and static assets
- **Problem:**
  1. **Memory leak in `ProfilePage`:** `this.authService.currentUser$.subscribe(...)` in `profile.page.ts` (line 68) is never unsubscribed on `ngOnDestroy`.
  2. **Non-functional auth controls:** In `LoginPage` and `SignupPage`, clicking **"Continue with Google"** (`onGoogleLogin()` / `onGoogleSignup()`) only displays a toast (`"Google Sign-In is configured for production credentials."`) without invoking Google Identity Services or calling `POST /api/v1/auth/oauth/google`. Similarly, `onForgotPassword()` only shows a fake toast (`"Password reset link will be sent..."`) with no backend endpoint, and the `rememberMe` checkbox control (`login.page.ts` line 50) is never read.
  3. **`PlaceService.getNearbyPlaces(municipality)` ignores `municipality`:** At line 558 of `place.service.ts`, `const norm = (municipality || '').toLowerCase();` is computed and never used; the method always returns the 16 hardcoded Bongabon restaurants, hospitals, and stores—even when the header says `"Nearby Places in Cabanatuan City"` or `"Nearby Places in Gapan City"`!
  4. **`ItineraryDetailPage.getStopImage()` ignores `image_url`:** Line 237 of `itinerary-detail.page.ts` calls `this.placeService.getPlaceImage(name)` without passing `item.place?.image_url` as the second argument.
  5. **User-facing typos & misleading guest copy:**
     - `welcome.page.html` line 23: `"Get personalize iternaries"` (should be `"Get personalized itineraries"`).
     - `login.page.html` line 80: `"Remeber me"` (should be `"Remember me"`).
     - `guest.page.html` line 22: `"Your data won't be save"` (grammatically broken and contradicts the actual implementation where guest itineraries *are* saved locally on the device via `GuestStorageService`).
  6. **Repository & bundle asset bloat:** `Project/src/assets/images/` contains 44 unused raw SHA-1 hash image files (`052ef0568b645cc40c7faf3792aff8460e8499eb.png`, etc.) and duplicate subdirectories (`login_pics/`, `popular_destinations/`) that are copied into every production build (`Project/www/assets/images/`), plus the binary `Travel Itinerary App.fig` file in the repository root.
- **Impact:** Memory leak across profile tab visits, misleading UI buttons/copy, inaccurate nearby places for non-Bongabon days, and unnecessary megabytes in the deployed web/mobile bundle.
- **Recommendation:** Unsubscribe `currentUser$` in `ProfilePage`, wire `getNearbyPlaces()` to query `searchPlaces({ categories: ['restaurant', 'hospital_clinic', 'pharmacy', 'convenience_store', 'shopping_market'] })` for the active municipality, pass `item.place?.image_url` in `getStopImage()`, fix the three typos, and remove unused SHA-1 hash images from `Project/src/assets/images/`.

### [INFORMATIONAL] CR-016 — Non-Standard / Future Package Versions in `Project/package.json` and Documentation Drift Across `docs/`
- **Location:** `Project/package.json` (Lines 23–62) and `docs/KNOWN_ISSUES.md`, `docs/DEVELOPMENT_PLAN.md`, `docs/PROJECT_STATE.md`, `docs/TESTING_DOCUMENTATION.md`
- **Component:** Dependency manifest and documentation suite
- **Problem:**
  1. `Project/package.json` lists version numbers such as `@angular/core: "22.2.3"`, `@angular/cli: "22.2.4"`, `@ionic/angular: "^9.0.0"`, `typescript: "~6.0.0"`, `vitest: "~5.0.5"`, `@playwright/test: "^1.64.1"`, and `eslint: "^10.10.0"`, which match the committed `Project/package-lock.json` generated in the author's custom environment (dated October 2026 in the project metadata). If a developer attempts `npm install` against standard public npm registries where those versions do not exist, installation will fail unless aligned with published registry versions.
  2. `docs/KNOWN_ISSUES.md` (lines 14–17, 35–43), `docs/DEVELOPMENT_PLAN.md` (lines 18–20, 103–110), `docs/PROJECT_STATE.md` (lines 151–164), and `docs/TESTING_DOCUMENTATION.md` (lines 78–141) contain stale sections stating that Milestones 4–9 or History/Profile tabs are still unimplemented placeholders, contradicting the completed status at the top of `docs/PROJECT_STATE.md` and `docs/CHANGELOG.md`.
- **Recommendation:** Synchronize `docs/KNOWN_ISSUES.md`, `docs/DEVELOPMENT_PLAN.md`, `docs/PROJECT_STATE.md`, and `docs/TESTING_DOCUMENTATION.md` so all sections reflect the `v0.9.0-alpha` state accurately.

## E. Security Assessment

| Vulnerability Category | Status in Repository | Technical Assessment & Remediation Summary |
| :--- | :--- | :--- |
| **Broken Object Level Authorization (BOLA / IDOR)** | **VULNERABLE (`CR-001`, `CR-002`)** | Top-level `GET/PATCH/DELETE /api/v1/itineraries/{id}` properly check `Itinerary.user_id == current_user.id`. However, `reorder_itinerary_items()` (`itineraries.py:519`) and `delete_itinerary_item()` (`itineraries.py:464`) fail to scope child `ItineraryItem` / `ItineraryDay` lookups to the parent `itinerary_id`, enabling cross-user stop theft, data exposure, and deletion. **Fix:** Scope all `ItineraryDay` and `ItineraryItem` queries to `itinerary.days`. |
| **Broken Authentication & OAuth Linking** | **VULNERABLE (`CR-004`, `CR-005`)** | `verify_google_id_token()` passes `audience=None` when `google_oauth_client_id` is empty (`auth_service.py:164`), bypassing audience validation, and `authenticate_google_user()` links accounts by email without checking `email_verified` or `user.is_active`. **Fix:** Require non-empty `google_oauth_client_id`, assert `email_verified is True`, and enforce `user.is_active` before issuing tokens. |
| **Secrets & Cryptographic Keys** | **WEAK DEFAULT (`CR-004`)** | No live production credentials are committed in `.env` (which is gitignored), and `docker-compose.yml` / `config.py` use local dev placeholders. However, `config.py:17` falls back to a hardcoded default `jwt_secret_key` without failing startup when `app_env != "development"`. **Fix:** Add a startup validator in `Settings` rejecting default/short keys outside dev/test. |
| **Session & Token Management** | **INCOMPLETE (`CR-006`, `CR-012`)** | Access tokens expire in 30m and refresh tokens in 7d, with `type` claim separation (`"access"` vs `"refresh"`). However, tokens are stored in `localStorage`, the frontend never calls `/api/v1/auth/refresh`, `isAuthenticated()` ignores `exp`, and `authInterceptor` sends Bearer tokens to any custom URL set in `ne_custom_api_url`. **Fix:** Implement `401` refresh rotation in `authInterceptor` and validate/scope `ne_custom_api_url`. |
| **Password Storage** | **SECURE** | Passwords are hashed using `pwdlib` `PasswordHash.recommended()` (Argon2id) and never logged or returned in `UserOut`. Login failures return a generic `401` (`"Invalid email or password"`) to prevent user enumeration. |
| **SQL Injection** | **SAFE (MINOR WILDCARD GAP `CR-008`)** | All application queries use SQLAlchemy 2.0 parameterized ORM constructs (`select()`, `.where()`). Note: `scripts/db_backup_restore.py:204` interpolates table names from `sqlite_master` (`DROP TABLE IF EXISTS "{t}"`), which is internal metadata, and `places.py` / `itinerary_generator.py` do not escape `%`/`_` wildcards in `.ilike()` patterns. |
| **Cross-Site Scripting (XSS)** | **SAFE** | Angular template bindings automatically encode HTML, and `MapPage.updateMarkers()` (`map.page.ts:311, 411–418`) explicitly sanitizes `place.name` via `this.escapeHtml(place.name)` before interpolating into Leaflet `L.divIcon` HTML. |
| **CORS & CSRF Configuration** | **OVERLY PERMISSIVE (`CR-004`)** | `main.py:29` sets `allow_origin_regex=r"^https://.*\.github\.io$"` with `allow_credentials=True`, trusting every GitHub Pages user domain. Because auth uses `Authorization: Bearer` headers rather than cookies, classical cookie CSRF does not apply, but wildcard `*.github.io` CORS should be restricted to `https://edselrenz.github.io`. |
| **Rate Limiting** | **PROXY FLAW (`CR-013`)** | SlowAPI limits `/register`, `/login`, `/refresh`, and `/oauth/google` to 5–10 req/min, and sets a 120/min global limit. However, `get_remote_address` treats all Cloudflare Tunnel users as `127.0.0.1`, causing shared lockout across all remote users. |
| **Error Message Information Exposure** | **MINOR LEAK (`CR-004`)** | `verify_google_id_token()` (`auth_service.py:172`) returns raw exception details (`f"Google token verification failed: {exc}"`) to the client. |

## F. Database Assessment

### Schema Design, Keys, and Relationships
The relational schema (`backend/app/models/entities.py` and `backend/alembic/versions/0001_initial_nueva_ecija_schema.py`) is well-normalized (3NF) across 7 tables (`users`, `auth_identities`, `municipalities`, `places`, `itineraries`, `itinerary_days`, `itinerary_items`):
- **Primary & Foreign Keys:** All 7 tables use UUID primary keys (`sa.Uuid(as_uuid=True)`). Foreign keys define appropriate `ondelete` behaviors: `CASCADE` on `auth_identities.user_id`, `itineraries.user_id`, `itinerary_days.itinerary_id`, and `itinerary_items.day_id`; and `SET NULL` on `places.municipality_id` and `itinerary_items.place_id`.
- **Unique Constraints & Indexes:** Proper unique constraints exist on `users.username_normalized`, `users.email_normalized`, `auth_identities(provider, provider_subject)`, `municipalities.name`, `municipalities.slug`, `places(source_name, source_record_id)`, and `itinerary_days(itinerary_id, day_number)`. Indexes are present on foreign keys and `places(latitude, longitude)`.

### Identified Database & Data Integrity Issues
1. **Unenforced Foreign Keys on SQLite Connections:** On SQLite (`sqlite:///...`), `PRAGMA foreign_keys = ON` is **not** enabled on connection creation in `backend/app/core/database.py` (line 9). As a result, when running against SQLite in local dev or tests, foreign key constraints and `ON DELETE CASCADE` / `ON DELETE SET NULL` are **not enforced at the database engine level** (only via SQLAlchemy ORM cascades when objects are deleted through the session).
2. **Missing Database `CHECK` Constraints:** The schema lacks database-level `CHECK` constraints for `itineraries.end_date >= itineraries.start_date`, `itineraries.daily_budget >= 0`, `places.estimated_cost_max >= places.estimated_cost_min`, and `itinerary_items.duration_minutes > 0`, relying solely on Pydantic request schemas.
3. **Missing `updated_at` Trigger in PostgreSQL:** While `entities.py` defines `onupdate=utcnow` on `User.updated_at`, `Itinerary.updated_at`, and `ItineraryItem.updated_at` (which works for ORM-level updates), direct SQL updates do not update `updated_at`.
4. **PostgreSQL Restore Defect in `scripts/db_backup_restore.py`:** In `restore_backup()` for PostgreSQL (lines 211–237), `psql -f <backup_path>` executes a plain SQL `pg_dump` file against the existing database **without `--clean` / `--if-exists` in `pg_dump` (`create_backup()` lines 93–108)**. When `psql` replays `CREATE TABLE` and `COPY` statements over an existing populated PostgreSQL database (such as during `run_drill()` on PostgreSQL), `CREATE TABLE` and primary key inserts for existing rows will fail or collide unless `--clean --if-exists` is passed to `pg_dump`. (The automated test `test_backup_restore.py` only tested `run_drill()` against SQLite, where lines 200–205 explicitly drop all tables before `executescript()`, masking the PostgreSQL restore bug.)

## G. Performance Assessment

### Confirmed Performance Issues
1. **Unbounded Full-Table Scan & In-Memory Scoring in `generate_suggested_itinerary_data()` (`backend/app/algorithms/itinerary_generator.py:157–163`):** Every request to `POST /api/v1/itineraries/suggest` loads **all** active `Place` rows and their joined `Municipality` objects into memory (`db.scalars(select(Place).where(Place.is_active == True).options(selectinload(Place.municipality))).all()`). While negligible for 17 seeded places, once a full Nueva Ecija OpenStreetMap extract (thousands of POIs) is imported via `scripts/import_osm.py`, this query will deserialize the entire table on every request instead of filtering by bounding box or category in SQL.
2. **$N+1$ Queries in `scripts/import_osm.py` (`lines 220–242`) and `scripts/seed_featured_places.py` (`lines 391–447`):** Both scripts issue a separate `SELECT` query per record inside a loop rather than pre-fetching existing keys into a dictionary or using bulk `ON CONFLICT DO UPDATE`.
3. **Redundant Count Subquery Join in `list_places()` (`backend/app/api/v1/places.py:98–143`):** `stmt` includes `.options(joinedload(Place.municipality))` and an `outerjoin(Municipality)` even when `q` is not searching municipality names, and `count_stmt = select(func.count()).select_from(stmt.subquery())` wraps the joined query in a subquery on every `/places` request.
4. **Unused Static Image Assets in `Project/src/assets/images/`:** 44 raw SHA-1 hash PNG/JPG files and duplicate folders (`login_pics/`, `popular_destinations/`) are bundled into `Project/www/assets/images/` during `ng build`, unnecessarily increasing mobile app package size and GitHub Pages artifact size.

### Areas Requiring Runtime Profiling / Benchmarking
- **Leaflet MarkerCluster Rendering at Scale:** `MapPage.loadPlaces()` currently requests `limit: 100` (`map.page.ts:262`). If increased to render all imported provincial POIs, DOM creation inside `updateMarkers()` (`L.divIcon` per marker) should be benchmarked on low-end Android WebViews.

## H. Testing Assessment

### Existing Test Coverage Analysis
The repository contains **4 backend Pytest files** (`backend/tests/test_foundation.py`, `test_auth.py`, `test_itineraries.py`, `test_backup_restore.py`), **16 frontend Vitest spec files** (`Project/src/**/*.spec.ts`), **1 Playwright E2E spec** (`Project/e2e/app.spec.ts`), and **1 acceptance script** (`scripts/verify_acceptance_gate.py`).
- **What is well tested:**
  - User registration, Argon2id hashing, case-insensitive duplicate email/username rejection, login, `/auth/me`, refresh endpoint, and SlowAPI 6th-request `429` throttling (`test_auth.py`).
  - Municipality/place seeding idempotency, OSM import out-of-bounds rejection, and comma-separated category filtering (`test_foundation.py`).
  - Top-level itinerary `GET`/`PATCH`/`DELETE` BOLA isolation between User A and User B, same-day duplicate stop guard, and basic stop reordering (`test_itineraries.py`).
  - Frontend service unit tests (`place.service.spec.ts`, `itinerary.service.spec.ts`, `connectivity.service.spec.ts`, `guest-migration.service.spec.ts`).

### Critical Gaps and Flaws in Existing Tests
1. **Cross-Itinerary BOLA Attacks Not Tested:** `test_itineraries.py` only tests User B calling `GET`, `PATCH`, and `DELETE` on `/api/v1/itineraries/{user_A_itinerary_id}`. It never tests User B passing User A's `day_id` or `item_id` into `POST /api/v1/itineraries/{user_B_itinerary_id}/reorder` (`CR-001`) or `DELETE /api/v1/itineraries/{user_B_itinerary_id}/days/{user_A_day_id}/items/{user_A_item_id}` (`CR-002`).
2. **Edit-Mode Save in `CustomBuilderPage` Not Tested:** `custom-builder.page.spec.ts` only tests saving a *new* itinerary (`isEditMode = false`, line 206), completely missing the bug where `isEditMode = true` calls `updateItinerary()` and drops all modified days and stops (`CR-003`).
3. **Google OAuth (`POST /api/v1/auth/oauth/google`) Not Tested:** `test_auth.py` has zero tests (mocked or otherwise) for `authenticate_google_user()`, missing the empty client-ID audience bypass (`CR-004`) and inactive-user / unverified-email bypass (`CR-005`).
4. **PostgreSQL Backup/Restore Not Tested:** `test_backup_restore.py` only tests `db_backup_restore.py` against SQLite (`test_drill.sqlite`), missing the `--clean --if-exists` restoration defect on PostgreSQL.
5. **Broken E2E Spec (`Project/e2e/app.spec.ts`):** Still tests the stock Ionic starter `'Tab 1 page'`, which does not exist at `/`.
6. **Hardcoded `True` Assertions in `scripts/verify_acceptance_gate.py`:** 7 of the 24 checks use `True` or `... or True` (`CR-014`).

## I. Prioritized Action Plan

### Priority 1 — Fix Immediately (Critical & High Security / Data-Loss Blockers)
1. **Patch Cross-Itinerary BOLA in Stop Reorder & Delete (`CR-001`, `CR-002`):**
   - **Files:** `backend/app/api/v1/itineraries.py`, `backend/tests/test_itineraries.py`
   - **Action:** In `reorder_itinerary_items()` and `delete_itinerary_item()`, verify that every `day_id` and `item_id` belongs to `itinerary.days` before mutating or deleting. Add negative cross-user BOLA tests for `/reorder` and `/days/{day_id}/items/{item_id}` in `test_itineraries.py`.
2. **Fix Edit-Mode Itinerary Save Dropping All Days and Stops (`CR-003`):**
   - **Files:** `backend/app/schemas/itinerary.py`, `backend/app/api/v1/itineraries.py`, `Project/src/app/core/models/itinerary.models.ts`, `Project/src/app/core/services/itinerary.service.ts`, `Project/src/app/features/itinerary/custom-builder/custom-builder.page.ts`
   - **Action:** Allow `ItineraryUpdate` / `PATCH /api/v1/itineraries/{id}` and `updateGuestItinerary()` to accept and replace `days`, `preferences`, and `assumptions`, and pass the full payload from `CustomBuilderPage.saveItinerary()` when `isEditMode` is true.
3. **Harden JWT Secrets, Google OAuth Verification, and CORS (`CR-004`, `CR-005`):**
   - **Files:** `backend/app/core/config.py`, `backend/app/main.py`, `backend/app/services/auth_service.py`
   - **Action:** Reject default/weak `jwt_secret_key` outside development/test; require non-empty `google_oauth_client_id` and `email_verified == True` in `verify_google_id_token()`; check `user.is_active` in `authenticate_google_user()`; and replace `allow_origin_regex=r"^https://.*\.github\.io$"` with `"https://edselrenz.github.io"` in `cors_origins`.

### Priority 2 — Fix Before Production / Pilot Launch (Core Reliability & Functional Accuracy)
4. **Implement Refresh Token Rotation & Fix Silent `401` Guest Fallback (`CR-006`):**
   - **Files:** `Project/src/app/core/services/auth.service.ts`, `Project/src/app/core/interceptors/auth.interceptor.ts`, `Project/src/app/core/services/itinerary.service.ts`
   - **Action:** Add `refreshSession()` to `AuthService`, intercept `401` responses in `authInterceptor` to rotate tokens or log out cleanly, check JWT `exp` in `isAuthenticated()`, and restrict `ItineraryService` `catchError` guest fallbacks to network offline statuses (`0`, `502`, `504`).
5. **Fix Timezone Off-By-One Date Shifting (`CR-007`):**
   - **Files:** `Project/src/app/features/itinerary/suggested-wizard/suggested-wizard.page.ts`, `Project/src/app/features/itinerary/custom-builder/custom-builder.page.ts`, `Project/src/app/features/itinerary/itinerary-detail/itinerary-detail.page.ts`, `Project/src/app/core/services/itinerary.service.ts`
   - **Action:** Replace `new Date("YYYY-MM-DD")` and `.toISOString().split('T')[0]` with local calendar date helpers (`toLocalIsoDate`, `parseLocalIsoDate`).
6. **Fix Suggested Itinerary Generator & Frontend Suggested Wizard (`CR-008`, `CR-009`):**
   - **Files:** `backend/app/algorithms/itinerary_generator.py`, `Project/src/app/core/services/itinerary.service.ts`, `Project/src/app/features/itinerary/suggested-wizard/suggested-wizard.page.html`
   - **Action:** Enforce `settings.default_dest_radius_km` and cumulative `remaining_budget` per day in `itinerary_generator.py`; call `/api/v1/itineraries/suggest` for guests when online; make `generateOfflineSuggestedItinerary()` filter by destination, preferences, and budget; and bind `generatedPlan.daily_budget` and `generatedPlan.preferences` dynamically in `suggested-wizard.page.html`.
7. **Complete Map Tab Requirements & Stop Editing (`CR-010`, `CR-011`):**
   - **Files:** `Project/src/app/tabs/map/map.page.ts`, `Project/src/app/tabs/map/map.page.html`, `backend/app/api/v1/itineraries.py`
   - **Action:** Read `ActivatedRoute.queryParams` in `MapPage` so "Plan Route Here" selects/zooms to the destination; add `tileerror` handling and `"Not verified / Not provided"` / provenance labels in `map.page.html`; and add `PATCH /{itinerary_id}/days/{day_id}/items/{item_id}` using `ItineraryItemUpdate`.
8. **Validate Custom API URL Override & Fix PostgreSQL Backup Restore (`CR-012`, `F.4`):**
   - **Files:** `Project/src/app/core/services/connectivity.service.ts`, `Project/src/app/core/interceptors/auth.interceptor.ts`, `scripts/db_backup_restore.py`
   - **Action:** Validate `ne_custom_api_url` protocol/hostname, only attach `Authorization` headers to requests matching `environment.apiBaseUrl`, and pass `--clean --if-exists` to `pg_dump` in `scripts/db_backup_restore.py`.

### Priority 3 — Improve Maintainability & Code Quality
9. **Remove Dead Starter Code, Legacy Scaffolding Script, and Unused Image Bloat (`CR-014`, `CR-015`):**
   - **Files:** `Project/src/app/tab1/`, `tab2/`, `tab3/`, `explore-container/`, `setup_steps_0_to_2.py`, `Project/src/assets/images/`
   - **Action:** Delete the 16 unused starter files and `setup_steps_0_to_2.py`; prune the 44 unused SHA-1 hash images; fix the unsubscribed observable in `ProfilePage`; and fix the typos in `welcome.page.html`, `login.page.html`, and `guest.page.html`.
10. **Synchronize Documentation (`CR-016`):**
    - **Files:** `docs/KNOWN_ISSUES.md`, `docs/DEVELOPMENT_PLAN.md`, `docs/PROJECT_STATE.md`, `docs/TESTING_DOCUMENTATION.md`
    - **Action:** Remove outdated "Pending / Not Yet Implemented" sections that conflict with the completed Milestone 8–10 implementation.

### Priority 4 — Long-Term Improvements (Performance, Scalability & QA)
11. **Optimize Database & Tunnel Rate-Limiting Operations (`CR-013`):**
    - **Files:** `backend/app/core/limiter.py`, `backend/app/algorithms/itinerary_generator.py`, `scripts/import_osm.py`
    - **Action:** Key SlowAPI rate limits by `CF-Connecting-IP` when `request.client.host == "127.0.0.1"`, push geographic bounding-box filters into SQL in `itinerary_generator.py`, and batch-fetch existing places in `import_osm.py`.
12. **Rewrite Playwright E2E Suite & Acceptance Gate Assertions (`CR-014`):**
    - **Files:** `Project/e2e/app.spec.ts`, `scripts/verify_acceptance_gate.py`
    - **Action:** Replace the broken `'Tab 1 page'` E2E test with end-to-end Playwright journeys covering guest mode, signup/login, search, map filtering, and itinerary creation/editing, and replace all `or True` lines in `verify_acceptance_gate.py` with real checks.

## J. Overall Code Review Verdict

**VERDICT: CHANGES REQUIRED (NOT READY FOR PRODUCTION)**

### Evidence-Based Justification
While `edselrenz/itinerary-app` has a well-structured database schema, clean UI alignment with the Figma mockups, Argon2id password hashing, and a solid foundation for zero-cost open-data travel planning, it cannot be approved for production or external pilot deployment in its current state due to:
1. **Two Critical BOLA/IDOR Vulnerabilities (`CR-001`, `CR-002`):** Authenticated users can hijack or delete stops belonging to other users' itineraries via `/reorder` and `DELETE .../items/{item_id}`.
2. **Broken Itinerary Editing Workflow (`CR-003`):** Editing an existing itinerary in `CustomBuilderPage` (`isEditMode = true`) silently discards all added, removed, or reordered stops and days upon saving.
3. **High-Risk Authentication & Session Flaws (`CR-004`, `CR-005`, `CR-006`):** Unenforced Google OAuth audience (`aud`) and `email_verified` / `is_active` checks, a hardcoded default JWT secret key without non-dev startup enforcement, wildcard `*.github.io` CORS with credentials, and an unused refresh token flow that silently diverts authenticated users into local guest storage after 30 minutes.
4. **Timezone & Algorithmic Inaccuracies (`CR-007`, `CR-008`, `CR-009`):** UTC/local date parsing shifts travel dates by 1 day, the backend suggestion engine ignores `default_dest_radius_km` and cumulative daily budgets, and the frontend guest suggestion flow ignores user preferences, budgets, and non-Bongabon destinations while displaying hardcoded budget/preference tags.

Completing the **Priority 1** and **Priority 2** items in Section I will resolve these blockers and bring the application to genuine pilot and production readiness.
