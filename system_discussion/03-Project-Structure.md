# 03 — Project Directory Structure

This guide maps the complete repository layout of `Edselrenz/Itinerary-App` (`v1.0.0`) and explains the exact purpose, responsibilities, and operational criticality of every directory and key file.

---

## 1. Complete Repository Tree

```text
Itinerary-App/
├── .env.example                          # Backend environment variable template (Essential)
├── .gitignore                            # Git exclusion rules for secrets, caches, builds, dist_*, *.apk, *.exe
├── .github/
│   └── workflows/
│       ├── deploy.yml                    # CI/CD: Backend pytest + Vitest + GitHub Pages deploy
│       └── release-builds.yml            # CI/CD: Android APK + Windows Setup.exe + GitHub Release
├── .vscode/                              # Shared VS Code workspace settings & recommended extensions
├── docker-compose.yml                    # Local PostgreSQL 16 container (Essential for PG dev)
├── docker-compose.prod.yml               # Production multi-container PostgreSQL 16 + FastAPI stack
├── start_server.bat                      # Windows launcher invoking scripts/start_server.ps1
├── stop_server.bat                       # Windows shutdown invoking scripts/stop_server.ps1
├── run_desktop_app.bat                   # Windows dev launcher: python desktop_client\main.py
├── Run_NuevaEcijaTravel_EXE.bat          # Windows launcher for compiled dist\NuevaEcijaTravel\*.exe
│
├── backend/                              # FastAPI REST API & Database Layer (Essential)
│   ├── Dockerfile                        # Multi-stage Python 3.12 production container image
│   ├── alembic.ini                       # Alembic CLI & logging configuration
│   ├── requirements.txt                  # Python backend dependencies
│   ├── alembic/
│   │   ├── env.py                        # Alembic migration runner bound to Base.metadata
│   │   └── versions/
│   │       ├── 0001_initial_nueva_ecija_schema.py   # 7 core tables
│   │       ├── 0002_google_places_and_routing.py    # Google GIS fields + geospatial_cache table
│   │       ├── 0003_widen_phone_column.py           # places.phone VARCHAR(64) -> VARCHAR(255)
│   │       └── 0004_add_user_profile_fields.py      # Extended users profile columns
│   ├── app/
│   │   ├── main.py                       # FastAPI app init, SlowAPI, CORS, router mounts, /health
│   │   ├── core/
│   │   │   ├── config.py                 # Pydantic BaseSettings & production secret validator
│   │   │   ├── database.py               # SQLAlchemy engine, SQLite fallback, auto-migration helper
│   │   │   └── limiter.py                # SlowAPI rate limiter with Cloudflare/proxy IP resolution
│   │   ├── models/
│   │   │   └── entities.py               # 8 SQLAlchemy 2.0 ORM models (109 columns)
│   │   ├── schemas/
│   │   │   ├── auth.py                   # Register, Login, Refresh, GoogleOAuth, UserUpdate, TokenOut
│   │   │   ├── place.py                  # MunicipalityOut, PlaceOut, LivePlaceSearch*, PaginatedPlacesOut
│   │   │   └── itinerary.py              # Itinerary/Day/Item CRUD, Suggest, Reorder, RouteCompute schemas
│   │   ├── api/v1/
│   │   │   ├── auth.py                   # /api/v1/auth/* endpoints (7 routes)
│   │   │   ├── places.py                 # /api/v1/municipalities & /api/v1/places/* (6 routes)
│   │   │   └── itineraries.py            # /api/v1/itineraries/* (13 routes, BOLA-enforced)
│   │   ├── services/
│   │   │   ├── auth_service.py           # Argon2id hashing, PyJWT, Google ID token verification
│   │   │   └── google_maps_service.py    # Places v1, Routes v2, OSRM, Haversine, KV/DB cache, upsert
│   │   └── algorithms/
│   │       └── itinerary_generator.py    # Clustering, Bayesian scoring, hours gate, 2-Opt TSP
│   └── tests/                            # 21 Pytest functions across 5 modules (100% green)
│       ├── test_auth.py
│       ├── test_backup_restore.py
│       ├── test_foundation.py
│       ├── test_google_maps_service.py
│       └── test_itineraries.py
│
├── Project/                              # Ionic Angular 22 Web/PWA & Android Frontend (Essential)
│   ├── angular.json                      # Angular build, budgets, fileReplacements, NGSW config
│   ├── capacitor.config.ts               # Android appId (ph.nuevaecijatravel.app), webDir: www
│   ├── eslint.config.js                  # Flat ESLint config
│   ├── ionic.config.json                 # Ionic Angular standalone integration
│   ├── ngsw-config.json                  # PWA Service Worker asset & API/OSM tile cache policies
│   ├── package.json                      # NPM dependencies & build/lint/test scripts
│   ├── playwright.config.ts              # Mobile Chrome (Pixel 7) E2E test configuration
│   ├── vitest.config.mts                 # Vitest runner config (fsModuleCache: false)
│   ├── tsconfig*.json                    # Base, app, spec, and e2e TypeScript configs
│   ├── custom_itinerary_qa.mjs           # Standalone Node QA verification script
│   ├── android/                          # Capacitor Android Gradle 8.13 project (JDK 21, sdkDownload=true)
│   ├── e2e/
│   │   └── app.spec.ts                   # Playwright E2E user journey specs
│   └── src/
│       ├── main.ts                       # Zoneless Angular bootstrap, Leaflet window.L guard, SW
│       ├── index.html                    # SPA HTML shell
│       ├── 404.html                      # GitHub Pages SPA fallback redirect
│       ├── global.scss                   # Global Ionic & custom layout styles
│       ├── theme/variables.scss          # Figma color tokens & CSS custom properties
│       ├── environments/                 # environment.ts, environment.prod.ts, environment.example.ts
│       ├── assets/
│       │   ├── data/osm_places.json      # 2,673 pre-indexed Nueva Ecija OSM POIs (offline dataset)
│       │   ├── images/                   # Curated destination photography & splash/avatar assets
│       │   └── icon/favicon.png          # App icon
│       └── app/                          # 32 Vitest .spec.ts files (348 unit tests passing)
│           ├── app.component.*           # Root shell: splash overlay, offline banner, Android back btn
│           ├── app.routes.ts             # Top-level lazy routes & redirects
│           ├── core/
│           │   ├── data/                 # commute-guide.data.ts, offline-places.data.ts
│           │   ├── guards/               # pending-changes.guard.ts
│           │   ├── interceptors/         # auth.interceptor.ts (Bearer injection + 401 refresh queue)
│           │   ├── models/               # auth.models.ts, place.models.ts, itinerary.models.ts
│           │   ├── services/             # 10 singleton services (+ 9 .spec.ts files)
│           │   └── utils/                # date.utils.ts, itinerary-export.util.ts, polyline.util.ts
│           ├── features/
│           │   ├── auth/                 # welcome/, login/, signup/, guest/
│           │   └── itinerary/            # custom-builder/, suggested-wizard/, itinerary-detail/
│           ├── shared/components/        # destination-autocomplete/, itinerary-route-map/, place-detail-sheet/
│           └── tabs/                     # tabs.page.*, tabs.routes.ts, home/, map/, history/, profile/, favorites/
│
├── desktop_client/                       # Python Flet 1.1.2 Desktop Application (Essential for Desktop)
│   ├── main.py                           # Entry point, route dispatcher, theme, splash, tab bar
│   ├── requirements.txt                  # Flet, flet-map, httpx, pydantic, pytest, python-dotenv
│   ├── .env.example                      # Desktop client environment template
│   ├── config/settings.py                # Palette tokens, window sizes, API base URL, .write_probe storage fallback
│   ├── core/                             # api_client.py, connectivity_service.py, session.py, storage.py,
│   │                                     # geo.py, polyline.py, commute_guide.py, offline_data.py, export.py
│   ├── models/                           # user.py, place.py, itinerary.py
│   ├── services/                         # auth_service.py, place_service.py, itinerary_service.py, favorites_service.py
│   ├── components/                       # 11 reusable UI widgets including slippy_map_canvas.py & splash_overlay.py
│   ├── views/                            # 11 full-screen views mirroring Ionic Web pages (boxless welcome/auth)
│   ├── assets/                           # osm_places.json (2,673 POIs), tiles/, tiles_cache/, images/ (incl.
│   │                                     # welcome_hero_buildings_wide.png 1848x336), icon/
│   ├── storage/                          # Local JSON persistence (relocates to %LOCALAPPDATA% if read-only)
│   ├── scripts/clean_and_seed_tiles.py   # Offline tile maintenance utility
│   └── tests/                            # 119 Pytest functions across 10 test modules (TC-01 to TC-40)
│
├── cloudflare-worker/                    # Edge Reverse Proxy (Optional for Local, Essential for GH Pages)
│   ├── worker.js                         # Dynamic tunnel failover + 24h KV edge caching + CORS
│   ├── wrangler.toml                     # Worker name, KV namespace placeholder, dev sync key
│   └── README.md                         # Worker setup notes
│
├── installer/
│   └── NuevaEcijaTravel.iss              # Inno Setup 6 script producing NuevaEcijaTravel_Setup_v1.0.0.exe
│
├── scripts/                              # Operational, Data, Build & Verification Scripts
│   ├── setup_postgres.py                 # DB connectivity check, Alembic upgrade, automatic seeding
│   ├── start_postgres.ps1                # Starts Docker PostgreSQL and runs setup_postgres.py
│   ├── start_server.ps1                  # Starts DB, Uvicorn, ngrok + Cloudflare tunnels, Worker sync
│   ├── stop_server.ps1                   # Cleanly stops tunnels, Uvicorn (:8000), dev servers (:4200/:8100)
│   ├── run_daemon.py                     # Background Python daemon launching Uvicorn + dual tunnels
│   ├── db_query.py                       # Interactive & one-shot dual-engine (SQLite/PostgreSQL) SQL query CLI
│   ├── db_backup_restore.py              # PostgreSQL (pg_dump/psql) & SQLite backup/restore CLI
│   ├── fetch_osm_places.py               # Queries Overpass API for Nueva Ecija POIs -> data/raw/
│   ├── import_osm.py                     # Idempotent Overpass JSON -> DB importer (16 categories)
│   ├── seed_featured_places.py           # Seeds 12 core municipalities & 18 curated featured POIs
│   ├── export_osm_to_client_asset.py     # Exports active SQLite places -> Project/src/assets/data/osm_places.json
│   ├── build_standalone_exe.py           # Staged PyInstaller compiler (build_temp/dist_stage -> dist/) with icons.json
│   ├── build_desktop_installer.ps1       # Orchestrates PyInstaller + Inno Setup 6 + Python zipfile portable .zip
│   ├── build_android_apk.ps1             # Orchestrates ng build (--no-service-worker) + cap sync + Gradle APK build
│   └── verify_acceptance_gate.py         # 24-point automated MVP acceptance test script
│
├── system_discussion/                    # Complete 17-part technical & layman system documentation suite
├── docs/                                 # Project overview, release verification reports, & development logs
├── for_updates/                          # Phase 60–62 remediation & review notes
└── build/                                # PyInstaller build artifacts (non-essential; see Tech Debt)
```

---

## 2. Directory Responsibilities & Criticality

| Path | Responsibility | Interacts With | Essential to Runtime? |
|---|---|---|---|
| `backend/app/` | Core REST API, auth, GIS service, itinerary algorithm, ORM models. | PostgreSQL/SQLite, Google Maps APIs, OSRM, Web/Desktop clients | **Yes** (required for cloud features) |
| `backend/alembic/` | Database schema version control (`0001`–`0004`). | `backend/app/models/entities.py`, PostgreSQL | **Yes** (for PostgreSQL deployments) |
| `Project/src/` | Ionic Angular Web/PWA & Android UI, services, Leaflet map, offline data. | Backend `/api/v1`, OSM Overpass/Tiles, Capacitor native plugins | **Yes** (Web/Mobile client) |
| `Project/android/` | Capacitor Android native shell and Gradle 8.13 build scripts. | `Project/www/` (via `npx cap sync android`) | **Yes** (Android APK only) |
| `desktop_client/` | Standalone Python Flet Windows desktop app with offline tile map. | Backend `/api/v1`, `desktop_client/storage/` or `%LOCALAPPDATA%`, OSM Tiles | **Yes** (Desktop client) |
| `cloudflare-worker/` | Permanent HTTPS reverse proxy + KV tunnel registry + 24h edge cache. | GitHub Pages, Android, Desktop, Host Tunnels | **Yes** (for GitHub Pages / remote pilot) |
| `scripts/` | Automation for DB setup, SQL querying (`db_query.py`), seeding, OSM ETL, server lifecycle, backups, and builds. | `backend/`, `Project/`, `desktop_client/`, Docker, Cloudflare Worker | **Yes** (for DevOps & local setup) |
| `installer/` | Inno Setup 6 definition for Windows `NuevaEcijaTravel_Setup_v1.0.0.exe`. | `dist/NuevaEcijaTravel/` | **Optional** (Windows release packaging) |
| `.github/workflows/` | Automated CI tests, GitHub Pages deploy, and release binary builds. | `backend/`, `Project/`, `desktop_client/`, `installer/` | **Optional** (CI/CD automation) |
| `system_discussion/` | Primary 17-document technical + layman architecture and operations reference. | All subsystems (documentation) | **No** (Documentation) |

---

## 3. Developer Navigation Guide

- **Need to trace an API endpoint?** Start at `backend/app/main.py` → `backend/app/api/v1/{auth,places,itineraries}.py` → `backend/app/schemas/` → `backend/app/services/` or `backend/app/algorithms/` → `backend/app/models/entities.py`.
- **Need to modify a Web/Android screen?** Start at `Project/src/app/app.routes.ts` or `Project/src/app/tabs/tabs.routes.ts` → locate the page under `features/` or `tabs/` → check injected services in `core/services/`.
- **Need to modify a Desktop screen?** Start at `desktop_client/main.py` (route dispatcher in `navigate_to()`) → open the matching file in `desktop_client/views/` → check widgets in `desktop_client/components/` and services in `desktop_client/services/`.
- **Need to inspect or query the database quickly?** Run `python scripts/db_query.py --tables` or `python scripts/db_query.py "SELECT name, category FROM places LIMIT 10"`.
- **Need to update offline POI data?** Run `scripts/fetch_osm_places.py` → `scripts/import_osm.py` → `scripts/seed_featured_places.py` → `scripts/export_osm_to_client_asset.py` (and mirror `osm_places.json` into `desktop_client/assets/data/osm_places.json`).

---

## 4. Technical Terms & Concepts Explained (How It Works & What It Is Used For in This System)

| Technical Term | How It Works (Technical & Layman Explanation) | What It Is Used For in This System |
|---|---|---|
| **Monorepo (Multi-Project Repository)** | **Layman**: Keeping the blueprints for the website, the Android phone app, the Windows desktop program, the cloud server, and the installer scripts all organized inside one master project folder instead of scattering them across five separate repositories.<br>**Technical**: A single Git repository hosting multiple distinct deployable packages (`backend/`, `Project/`, `desktop_client/`, `cloudflare-worker/`, `installer/`, `scripts/`) that share version history, documentation, and CI/CD pipelines. | Allows a single commit or release tag (`v1.0.0`) to test and package the FastAPI backend, Ionic Angular PWA, Android APK, and Windows Desktop installer together in lockstep. |
| **Multi-Stage `Dockerfile` (`backend/Dockerfile`)** | **Layman**: Building a clean shipping container in two steps: first using a "workshop" room full of heavy construction tools to compile the software, and then copying only the finished software into a lightweight, locked delivery box.<br>**Technical**: A Docker build file with multiple `FROM` stages (`builder` and `runtime`) on `python:3.12-slim` so build-time caches and compiler artifacts are discarded from the final runtime image, which runs as a non-root user (`appuser`) with a 30-second `/api/v1/health` `HEALTHCHECK`. | Packages the FastAPI backend and Alembic migrations for repeatable cloud or on-premise container deployments via `docker-compose.prod.yml`. |
| **PyInstaller & `_MEIPASS` Staging (`scripts/build_standalone_exe.py`)** | **Layman**: Most Windows users don't have Python installed on their PC. PyInstaller bundles Python, all required libraries, the Flet graphics engine, and our map data into one self-contained folder with a clickable `NuevaEcijaTravel.exe` program.<br>**Technical**: Freezes `desktop_client/main.py` and its dependency graph into a standalone Windows distribution. At runtime, `sys.frozen` is `True` and `sys._MEIPASS` points to the `_internal/` directory containing bundled data (`desktop_client/assets/`, `flet/controls/material/icons.json`, `certifi`, `tzdata`). | Compiles `dist/NuevaEcijaTravel/NuevaEcijaTravel.exe`. In Phase 62, `scripts/build_standalone_exe.py` builds into `build_temp/dist_stage/NuevaEcijaTravel` first and overlays into `dist/NuevaEcijaTravel` using an NTFS `.old` rename fallback so running instances never lose `icons.json`. |
| **Inno Setup 6 (`installer/NuevaEcijaTravel.iss`)** | **Layman**: The tool that creates a professional Windows setup wizard (`NuevaEcijaTravel_Setup_v1.0.0.exe`) with Next/Install buttons, Desktop shortcuts, Start Menu icons, and an Add/Remove Programs uninstaller.<br>**Technical**: A script-driven Windows installer compiler (`ISCC.exe`) configured with `Compression=lzma2/ultra64`, `PrivilegesRequired=lowest`, and `DefaultDirName={autopf}\NuevaEcijaTravel` (resolving to `%LOCALAPPDATA%\Programs\NuevaEcijaTravel` without triggering a UAC administrator prompt). | Compresses the `411.57 MB` standalone PyInstaller bundle into a single `156.58 MB` Windows installer executable (`dist_installer/NuevaEcijaTravel_Setup_v1.0.0.exe`). |
| **ETL Pipeline (Extract, Transform, Load — `scripts/*_osm*.py`)** | **Layman**: A 3-step data assembly line: **Extract** raw map points from OpenStreetMap, **Transform** messy community tags into our 16 clean categories with assigned Nueva Ecija towns, and **Load** them into our database and offline JSON files.<br>**Technical**: `fetch_osm_places.py` extracts raw Overpass QL JSON (`data/raw/`); `import_osm.py` normalizes tags, filters out non-tourism infrastructure, maps coordinates to the nearest `Municipality`, and idempotently upserts `Place` rows; `export_osm_to_client_asset.py` serializes active places to `osm_places.json`. | Populates and refreshes the 2,673-POI catalog in both the backend database and the offline client bundles (`Project/src/assets/data/osm_places.json` and `desktop_client/assets/data/osm_places.json`). |
| **Lazy Loading (`loadComponent` in `app.routes.ts`)** | **Layman**: Instead of forcing a phone browser to download every single screen of the app before showing the Welcome page, the browser only downloads the code for a screen (like the Map or Custom Builder) the moment the traveler taps on it.<br>**Technical**: Dynamic ES module `import()` statements inside Angular route definitions (`app.routes.ts` and `tabs.routes.ts`), paired with `withPreloading(PreloadAllModules)` to background-fetch remaining chunks after initial paint. | Keeps initial startup fast on mobile networks while preloading remaining screens in the background for instant offline tab switching. |
