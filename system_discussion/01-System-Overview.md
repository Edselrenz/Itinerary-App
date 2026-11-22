# 01 — System Overview and Introduction

## 1. What Is the System?

### Plain-Language Overview
**Trip Mo, Trip Ko** (repository: `Edselrenz/Itinerary-App`) is a multi-platform travel itinerary planning and destination discovery application built specifically for **Nueva Ecija Province, Philippines**. It helps travelers discover local attractions, cafes, restaurants, resorts, churches, and essential services across all 32 cities and municipalities of Nueva Ecija, automatically generate multi-day travel schedules tailored to their budget and interests, or build custom day-by-day itineraries with interactive maps, turn-by-turn route previews, and offline access.

### Technical Overview
The system is a **decoupled, multi-client, offline-resilient full-stack application** composed of four deployable runtime tiers:
1. **Web / PWA & Mobile Client (`Project/`)**: A standalone, zoneless **Angular 22.2.3 + Ionic 9** application wrapped with **Capacitor 8.6.0** for Android APK builds (`TripMoTripKo-release.apk` and `TripMoTripKo-debug.apk`) and configured with Angular Service Worker (`ngsw-config.json`) for Progressive Web App (PWA) caching. Uses **Leaflet 1.9.4** and `leaflet.markercluster` for geospatial mapping.
2. **Native Windows Desktop Client (`desktop_client/`)**: A **Python Flet 1.1.2+** desktop application achieving feature and visual parity with the web client, featuring a full-screen `SplashOverlay`, a boxless `WelcomeView` with a seamless 3-tile mirrored widescreen cityscape (`welcome_hero_buildings_wide.png`), a custom `SlippyMapCanvas` tile renderer, writable `%LOCALAPPDATA%` tile and storage caching, and PyInstaller + Inno Setup 6 Windows packaging (`installer/NuevaEcijaTravel.iss`).
3. **REST API Backend (`backend/`)**: A **Python 3.12 FastAPI** service backed by **SQLAlchemy 2.0**, **Alembic**, and **PostgreSQL 16** (with automatic 2-second fallback to a local SQLite database `nueva_ecija_travel.db` when PostgreSQL is unreachable). Exposes 27 `/api/v1` endpoints for authentication, POI search/discovery, deterministic itinerary generation, itinerary CRUD, and turn-by-turn route computation.
4. **Edge Reverse Proxy (`cloudflare-worker/`)**: A **Cloudflare Worker** (`worker.js`) backed by **Cloudflare KV** (`TUNNEL_KV`) that provides a permanent HTTPS endpoint for GitHub Pages and mobile clients, dynamically routing traffic to a host machine's active Cloudflare Quick Tunnel or `ngrok` tunnel with 24-hour edge caching for offline resilience.

### Application Metadata
| Property | Verified Value | Source Reference |
|---|---|---|
| **Brand Name** | Trip Mo, Trip Ko | `Project/capacitor.config.ts`, `installer/NuevaEcijaTravel.iss`, `desktop_client/components/splash_overlay.py` |
| **Android Package ID** | `ph.nuevaecijatravel.app` | `Project/capacitor.config.ts` |
| **API Title & Version** | Nueva Ecija Travel Itinerary API `v0.1.0` | `backend/app/main.py` |
| **Release & Installer Version** | `1.0.0` (Phase 62 Verified) | `installer/NuevaEcijaTravel.iss`, `Project/android/app/build.gradle` |
| **Supported Platforms** | Web Browser / PWA (GitHub Pages), Android (Capacitor APK), Windows x64 Desktop (Flet `.exe` / Inno Setup Installer / Portable `.zip`) | `.github/workflows/deploy.yml`, `.github/workflows/release-builds.yml` |
| **Automated Test Suite** | **488 tests passing** (348 Web Vitest + 119 Desktop Pytest + 21 Backend Pytest) | `Project/src/**/*.spec.ts`, `desktop_client/tests/`, `backend/tests/` |

---

## 2. Problems the System Solves

| Problem | Why It Matters | How the System Solves It | Handling Modules | Technical Mechanism |
|---|---|---|---|---|
| **Fragmented local tourism & POI data in Nueva Ecija** | Mainstream travel apps often lack structured, categorized, and locally curated data for provincial municipalities outside major hubs. | Consolidates 2,673 OpenStreetMap POIs and 18 curated featured destinations across 32 Nueva Ecija LGUs into 16 canonical categories, optionally augmented by live Google Places API (New). | `scripts/fetch_osm_places.py`, `scripts/import_osm.py`, `scripts/seed_featured_places.py`, `backend/app/api/v1/places.py`, `PlaceService` | Overpass QL bounding-box extraction (`15.15–16.15 N, 120.70–121.40 E`), deterministic tag-to-category mapping, PostgreSQL/SQLite persistence, and static JSON export (`osm_places.json`) bundled into Web & Desktop clients. |
| **Inefficient cross-province backtracking & unrealistic trip pacing** | Manual provincial trip planning frequently pairs distant towns on the same day or schedules closed/overnight venues during day trips. | Generates geographically clustered, road-paced itineraries automatically with transparent assumptions. | `backend/app/algorithms/itinerary_generator.py`, `SuggestedWizardPage`, `SuggestedWizardView` | SQL bounding-box pre-filtering (`25 km` default radius), multi-factor `score_place()` (preference match, Bayesian rating, Haversine proximity, opening-hours gate, budget fit, overnight/mountain guards), and 2-Opt TSP permutation ordering (`itertools.permutations`). |
| **Unreliable rural connectivity & intermittent host backend availability** | Travelers in rural Nueva Ecija (e.g., Minalungao, Pantabangan, Gabaldon) experience intermittent mobile data; pilot deployments also run on a tunneled local host. | Multi-layer offline resilience across Edge, Web/PWA, and Desktop clients. | `ConnectivityService`, `GuestStorageService`, `cloudflare-worker/worker.js`, `Project/ngsw-config.json`, `SlippyMapCanvas` | Bundled 2,673-POI `osm_places.json`, local guest storage (`@ionic/storage-angular` / `guest_storage.json`), offline itinerary clustering fallback, 24h Cloudflare KV edge cache, PWA Service Worker tile/API caching, and bundled/cached desktop map tiles with `%LOCALAPPDATA%` write-probe fallback. |
| **Friction of mandatory account creation before planning** | Requiring sign-up up front causes user drop-off when travelers just want to test routes or plan a quick trip. | Full Guest Mode with seamless, non-blocking migration to an authenticated cloud account upon login/registration. | `GuestPage`, `GuestStorageService`, `GuestMigrationService`, `desktop_client/core/storage.py` | Stores guest itineraries locally; upon authentication, `GuestMigrationService.migrateGuestData()` iterates local trips and POSTs them to `/api/v1/itineraries`. |
| **Lack of provincial commute & budget transparency** | Travelers need honest cost ranges (without treating missing fees as ₱0) and public transit guidance from provincial terminals. | Displays explicit verified vs. unverified cost summaries and municipality-level commute guides. | `commute-guide.data.ts`, `desktop_client/core/commute_guide.py`, `ItineraryBudgetSummary` | Tracks `unverifiedCount` alongside `verifiedMin`/`verifiedMax`, emits pricing notices in `itinerary.assumptions`, and maps municipalities to bus/UV Express/jeepney hub, drop-off, travel time, and fare ranges. |

---

## 3. System Objectives

Based on verified code and repository artifacts:
- **General Objective**: Provide an accessible, offline-capable, cross-platform travel itinerary planner tailored to Nueva Ecija Province that supports both automated trip generation and custom trip authoring.
- **Functional Goals**:
  - Search, filter, and map POIs across 16 canonical categories and 32 municipalities (`GET /api/v1/places`, `GET /api/v1/municipalities`).
  - Generate multi-day suggested itineraries up to 14 days with geographic clustering, budget awareness, and route polylines (`POST /api/v1/itineraries/suggest`).
  - Create, edit, reorder, and delete custom multi-day itineraries with linked POIs or custom off-grid stops (`POST/GET/PATCH/DELETE /api/v1/itineraries`).
  - Compute driving/walking routes with turn-by-turn legs and live GPS route tracking on mobile/web (`POST /api/v1/itineraries/compute-day-route`, `RouteTrackingService`).
  - Export itineraries to RFC 5545 iCalendar (`.ics`), Markdown/text summary, and JSON (`itinerary-export.util.ts`, `desktop_client/core/export.py`).
- **Technical Goals**:
  - Maintain strict data isolation (BOLA protection) for user-owned itineraries and Argon2id + JWT authentication.
  - Operate with zero paid API dependency by falling back gracefully from Google Maps Platform to OSRM + local OSM datasets + Haversine routing.
  - Achieve UI, workflow, and data-model parity across Web/PWA, Android APK, and Windows Desktop.
- **User Experience Goals**:
  - Non-blocking offline status banner (`OfflineHostBanner`), unsaved-changes route guard (`pendingChangesGuard`), dark/light theme persistence, and mobile-first 4-tab bottom navigation (`Home`, `Map`, `Saved`, `Profile`).

---

## 4. Technology Stack (Verified)

| Category | Technology & Version | Where Used | Why Used (Implementation Evidence) | Dependent Components |
|---|---|---|---|---|
| **Languages** | Python `3.12+` | `backend/`, `desktop_client/`, `scripts/` | Unified language for FastAPI backend, Flet desktop app, and OSM/DB/packaging scripts. | Backend API, Desktop Client, Build/DB Scripts |
| **Languages** | TypeScript `~6.0.0`, SCSS, HTML | `Project/` | Type-safe Ionic Angular frontend and Playwright E2E tests. | Web/PWA & Android Client |
| **Languages** | JavaScript (ES Modules) | `cloudflare-worker/worker.js` | Native Cloudflare Workers runtime for edge reverse proxy. | Edge Proxy |
| **Web/Mobile Framework** | Angular `22.2.3` (zoneless, standalone) + Ionic Angular `^9.0.0` | `Project/src/` | Mobile-first UI components, cross-platform Web/PWA + Android parity, lazy-loaded standalone routes. | All pages, tabs, shared components |
| **Mobile Wrapper** | Capacitor `8.6.0` (`@capacitor/android`, `app`, `geolocation`, `haptics`, `keyboard`, `status-bar`) | `Project/capacitor.config.ts`, `Project/android/` | Compiles Ionic Angular `www/` bundle into native Android APK with GPS, status bar, back button, and native secure storage. | `AppComponent`, `RouteTrackingService`, `SecureTokenStorageService` |
| **Desktop Framework** | Flet `>=1.1.2` + `flet-map>=0.1.0` | `desktop_client/` | Flutter-backed Python desktop UI enabling rapid parity with Ionic views and standalone Windows `.exe` packaging. | All desktop views & components |
| **Backend Framework** | FastAPI `>=0.115.0` + Uvicorn `>=0.30.0` | `backend/app/main.py` | Async/sync REST API with automatic OpenAPI docs (dev-only) and Pydantic v2 validation. | All `/api/v1/*` endpoints |
| **ORM & Migrations** | SQLAlchemy `>=2.0.30` + Alembic `>=1.13.2` + `psycopg[binary]>=3.2.0` | `backend/app/models/`, `backend/alembic/` | Portable `JsonType` (`JSONB` on PostgreSQL, `JSON` on SQLite) and versioned schema migrations (`0001`–`0004`). | All DB models, repositories, tests |
| **Database** | PostgreSQL `16-alpine` (Docker) & SQLite 3 (fallback) | `docker-compose.yml`, `backend/app/core/database.py` | Production relational store with zero-config local SQLite fallback (`nueva_ecija_travel.db`) if Postgres is unreachable. | Backend API, Backup/Restore & Query scripts |
| **Auth & Security** | `pwdlib[argon2]>=0.2.1`, `pyjwt>=2.9.0`, `google-auth>=2.34.0`, `slowapi>=0.1.9`, `capacitor-secure-storage-plugin` | `backend/app/services/auth_service.py`, `backend/app/core/limiter.py`, `SecureTokenStorageService` | Argon2id password hashing, HS256 JWT issuance, server-side Google ID token verification, proxy-aware rate limiting, native Keystore token storage. | Auth routes, HTTP interceptor |
| **Mapping & GIS** | Leaflet `^1.9.4`, `leaflet.markercluster ^1.5.3`, Custom `SlippyMapCanvas` | `MapPage`, `ItineraryRouteMapComponent`, `desktop_client/components/slippy_map_canvas.py` | Interactive slippy tile maps, marker clustering for 2,673 POIs, encoded polyline rendering, and offline tile caching. | Map tab, Route previews, Live tracking |
| **HTTP Clients** | Angular `HttpClient` + RxJS `~7.8.0`, Python `httpx>=0.27.0` / `>=0.28.1` | `Project/src/app/core/services/`, `backend/app/services/google_maps_service.py`, `desktop_client/core/api_client.py` | Interceptor-based JWT refresh on web; async `httpx.AsyncClient` with refresh lock on desktop; sync `httpx.Client` on backend. | All API consumers |
| **Testing & Linting** | Pytest `>=8.3.0`, Vitest `~5.0.5`, Playwright `^1.64.1`, ESLint `10.10.0`, Prettier `3.9.10`, Ruff, Mypy | `backend/tests/`, `desktop_client/tests/`, `Project/src/**/*.spec.ts`, `Project/e2e/` | Automated backend (21), desktop (119), frontend unit (348), and mobile E2E testing plus CI quality gates. | CI workflows, local QA |
| **Packaging & DevOps** | Docker / Docker Compose, GitHub Actions, PyInstaller, Inno Setup 6, Gradle 8.13, Wrangler | `backend/Dockerfile`, `.github/workflows/`, `scripts/build_*`, `installer/NuevaEcijaTravel.iss`, `cloudflare-worker/` | Automated GitHub Pages deployment, Android APK builds, Windows `Setup.exe` & Portable `.zip` releases, and edge proxy deployment. | Release & deployment pipelines |

---

## 5. Target Users and User Roles

**Role-Based Access Control (RBAC) Status**: **Not Implemented.**
The `users` table (`backend/app/models/entities.py`) contains no `role`, `is_admin`, or `permissions` column. Authorization is strictly binary (**Unauthenticated Guest** vs. **Authenticated Traveler**) combined with object-level ownership (`Itinerary.user_id == current_user.id`).

| User Type | Status | Responsibilities & Capabilities | Accessible Modules | Restricted Actions |
|---|---|---|---|---|
| **Guest Traveler (Unauthenticated)** | Implemented & Verified | Browse/search 2,673+ POIs, explore interactive map, generate suggested itinerary drafts (`POST /api/v1/itineraries/suggest`), build custom itineraries stored locally on device, manage local favorites, export `.ics`/text, compute stateless routes (`POST /api/v1/itineraries/compute-day-route`). | Welcome, Guest Onboarding, Home, Map, Saved (local), Profile (guest view + favorites/settings), Suggested Wizard, Custom Builder, Itinerary Detail (local/draft). | Cannot persist itineraries to PostgreSQL/cloud (`POST/GET/PATCH/DELETE /api/v1/itineraries` require Bearer JWT), cannot edit cloud user profile (`GET/PATCH /api/v1/auth/me`), cannot sync across devices until signing in. |
| **Authenticated Traveler** | Implemented & Verified | All Guest capabilities plus cloud-persisted multi-day itineraries, cross-device sync, automatic migration of local guest trips on login/signup, profile editing (name, username, middle initial, phone, birthday, gender, avatar, default daily budget), and password changes. | All frontend and desktop views plus authenticated `/api/v1/auth/me` and `/api/v1/itineraries/*` endpoints. | Strictly restricted to own itineraries via BOLA checks (`user_id == current_user.id`); cannot view/modify other users' trips; no admin moderation panel. |
| **System Administrator / Operator** | Infrastructure-Only (No In-App Role) | Manages backend server, PostgreSQL/SQLite database (`scripts/db_query.py`), backups/restores (`scripts/db_backup_restore.py`), OSM imports, Cloudflare Worker KV tunnel sync (`X-Admin-Sync-Key`), and CI/CD releases via CLI scripts. | Host OS / Docker / `scripts/*` / Cloudflare Worker `/__sync_tunnel` & `/__status`. | No dedicated admin UI or admin API endpoints exist inside FastAPI. |

---

## 6. Scope and Limitations (Honest Implementation Audit)

| Capability | Status | Evidence & Notes |
|---|---|---|
| Email/Username + Password Auth & JWT Refresh | **Implemented & Verified** | `backend/app/api/v1/auth.py`, `auth_service.py`, `auth.interceptor.ts`, `desktop_client/core/api_client.py`. |
| Guest Mode & Post-Login Migration | **Implemented & Verified** | `GuestStorageService`, `GuestMigrationService`, `desktop_client/core/storage.py`. |
| POI Search, Filtering, Map Clustering & Live OSM | **Implemented & Verified** | 16 canonical categories, 2,673 bundled OSM POIs, `OsmOverpassService`, Leaflet MarkerCluster, Desktop `SlippyMapCanvas`. |
| Deterministic Suggested Itinerary Generator | **Implemented & Verified** | `backend/app/algorithms/itinerary_generator.py` (up to 14 days, Haversine clustering, Bayesian scoring, 2-Opt TSP) + offline client fallback. |
| Custom Itinerary Builder & In-Place Editor | **Implemented & Verified** | `CustomBuilderPage`, `ItineraryDetailPage`, `CustomBuilderView`, `TripDetailView` with `pendingChangesGuard` and responsive modal forms (`TC-38`). |
| Turn-by-Turn Routing & GPS Tracking | **Implemented & Verified** | Google Routes v2 → OSRM → Haversine fallback; `RouteTrackingService` via `@capacitor/geolocation` on web/Android and `_launch_in_app_nav()` on Desktop (`TC-36`). |
| Desktop-Web Visual & UX Parity (`v1.0.0`) | **Implemented & Verified** | Full-screen `SplashOverlay` (`TC-39`), boxless `WelcomeView` with seamless 3-tile mirrored cityscape `welcome_hero_buildings_wide.png` (`TC-40`), centered full-width `Edit Profile` form (`TC-37`), and `%LOCALAPPDATA%` writable cache fallback (`TC-35`). |
| Google OAuth Sign-In | **Partially Implemented** | Backend `POST /api/v1/auth/oauth/google` is implemented and tested, but web (`login.page.ts`) and desktop (`login_view.py`) Google Sign-In buttons currently show a "disabled in this pilot build" notice. |
| Forgot Password / Password Recovery | **Partially Implemented (UI-Simulated)** | Web `LoginPage.submitRecoveryRequest()` and Desktop `LoginView._send_recovery()` simulate submission client-side; no backend recovery endpoint or email service exists. |
| Apple Sign-In | **Planned / Disabled** | `POST /api/v1/auth/oauth/apple` explicitly returns HTTP `501 Not Implemented` (`ENABLE_APPLE_AUTH=false`). |
| Favorites Cloud Sync | **Local-Only** | Favorites are stored only in `localStorage` (`ne_favorite_places_v1`) on web and `storage/favorites.json` on desktop; there is no `favorites` database table or backend endpoint. |
| Live Google Places & Routes API | **Referenced / Optional** | Requires `GOOGLE_MAPS_API_KEY`; when omitted, system gracefully uses local DB, OSM Overpass, OSRM, and Haversine fallbacks. |
| iOS Native Build | **Not Implemented** | Only `@capacitor/android` and `Project/android/` exist; no iOS Capacitor platform is configured. |
| Role-Based Access Control (RBAC) / Admin Panel | **Missing** | No user roles or admin endpoints exist. |

---

## 7. Technical Terms & Concepts Explained (How It Works & What It Is Used For in This System)

| Technical Term | How It Works (Technical & Layman Explanation) | What It Is Used For in This System |
|---|---|---|
| **POI (Point of Interest)** | **Layman**: Any specific pin on a map that a traveler might care about — a waterfall, church, cafe, hotel, gas station, or hospital.<br>**Technical**: A geospatial entity containing WGS84 coordinates (`latitude`, `longitude`), a normalized category, metadata (address, hours, cost range, rating), and an upstream provenance key (`source_name`, `source_record_id`). | Stored in the `places` table (36 columns) and bundled offline in `osm_places.json` (2,673 Nueva Ecija records + 18 curated featured venues across 16 canonical categories). |
| **LGU (Local Government Unit)** | **Layman**: A city or municipality (town) in the Philippines.<br>**Technical**: An administrative geographic subdivision with a name, URL slug, `is_city` flag, and centroid coordinates (`center_lat`, `center_lng`). | Stored in the `municipalities` table representing the 32 cities and municipalities of Nueva Ecija (e.g., Cabanatuan City, Science City of Muñoz, Palayan City, Gapan City, San Jose City, Bongabon, Gabaldon, Pantabangan). |
| **Zoneless Angular (`provideZonelessChangeDetection`)** | **Layman**: Traditional Angular apps run a background watcher (`Zone.js`) that checks the entire screen after every mouse move or timer tick. "Zoneless" turns off that noisy background watcher and only redraws the screen when the app explicitly says new data has arrived.<br>**Technical**: Removes the `zone.js` monkey-patching of browser async APIs (`setTimeout`, `Promise`, `fetch`) in Angular 22.2.3, relying instead on Angular Signals, RxJS `async` pipes, and explicit `ChangeDetectorRef.detectChanges()` triggers. | Configured in `Project/src/main.ts` to eliminate `Zone.js` bundle overhead and improve mobile scrolling/map performance on low-end Android devices. |
| **Leaflet & MarkerCluster** | **Layman**: Leaflet is the interactive map box that lets you drag and zoom map tiles. MarkerCluster groups hundreds of nearby pins into numbered circles (like `"45"`) when you zoom out so the map doesn't turn into an unreadable sea of overlapping icons.<br>**Technical**: `leaflet` (`1.9.4`) renders slippy `256×256` raster map tiles and SVG vector polylines in the DOM; `leaflet.markercluster` (`1.5.3`) builds a hierarchical spatial grid across zoom levels to cluster and spiderfy nearby `L.Marker` instances. | Renders all 2,673 Nueva Ecija POIs, category-colored custom SVG pins, and day-route polylines in `MapPage` and `ItineraryRouteMapComponent`. |
| **ORM (Object-Relational Mapping — SQLAlchemy 2.0)** | **Layman**: A translator that lets Python code work with database rows as ordinary Python objects (`user.first_name`, `itinerary.days`) instead of writing raw SQL text strings by hand.<br>**Technical**: Maps Python classes inheriting from `DeclarativeBase` (`backend/app/models/entities.py`) to relational database tables, compiling type-safe Python expressions (`select(Place).where(...)`) into parameterized SQL statements for PostgreSQL or SQLite. | Powers all database reads/writes across the 8 tables while preventing SQL injection and abstracting dialect differences between PostgreSQL 16 and SQLite 3. |
| **Alembic Schema Migrations** | **Layman**: Version control (like Git) specifically for database tables. When a developer adds a new column to the database, Alembic records a numbered step so any server can upgrade its tables safely without losing existing data.<br>**Technical**: A database migration tool for SQLAlchemy (`backend/alembic/versions/0001..0004`) that tracks the current schema revision in an `alembic_version` table and executes sequential `upgrade()` / `downgrade()` DDL operations. | Manages the evolution of thePostgreSQL/SQLite schema across 4 revisions (`0001` initial 7 tables → `0002` Google Places & `geospatial_cache` → `0003` widen `phone` → `0004` extended user profile fields). |
| **Argon2id & HS256 JWT** | **Layman**: **Argon2id** scrambles user passwords into an irreversible cryptographic lock that requires heavy computer memory to crack. Once logged in, the server hands the app a tamper-proof digital VIP wristband (**JWT**) good for 30 minutes.<br>**Technical**: **Argon2id** is a memory-hard password-hashing function (`pwdlib[argon2]`). **JSON Web Token (JWT)** signed with **HMAC-SHA256 (`HS256`)** encodes a signed JSON payload (`sub`, `type`, `exp`, `iat`) verified statelessly by the server on every API call. | Protects traveler passwords in `users.password_hash` and authenticates all private API calls (`Authorization: Bearer <access_token>`) with 30-minute access tokens and 7-day refresh tokens. |
| **BOLA (Broken Object Level Authorization) Protection** | **Layman**: A security check ensuring that User A cannot peek at, edit, or delete User B's private trip just by guessing User B's trip ID number in the web address.<br>**Technical**: The #1 API vulnerability on the OWASP API Security Top 10. Prevented by enforcing ownership predicates (`WHERE itineraries.id = :id AND itineraries.user_id = :current_user_id`) at the database query level on every object-targeted endpoint. | Enforced across all `/api/v1/itineraries/{itinerary_id}*` endpoints in `backend/app/api/v1/itineraries.py`, returning `404 Not Found` if another user attempts to access an itinerary they do not own. |
| **RFC 5545 iCalendar (`.ics`)** | **Layman**: The universal calendar file format accepted by Google Calendar, Apple Calendar, and Microsoft Outlook.<br>**Technical**: A plain-text MIME format (`text/calendar`) structured around `VCALENDAR` and `VEVENT` blocks with `DTSTART`, `DTEND`, `SUMMARY`, `LOCATION`, and `DESCRIPTION` properties. | Generated by `itinerary-export.util.ts` (Web/Android) and `desktop_client/core/export.py` (Desktop) so travelers can export their multi-day Nueva Ecija itinerary into their phone or desktop calendar with one click. |
