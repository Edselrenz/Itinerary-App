# 10 — Installation and Development Environment Setup

Follow this start-to-finish guide to clone `Edselrenz/Itinerary-App` (`v1.0.0`) and run the Backend, Database, Web/PWA Frontend, Desktop Client, and optional Android/Cloudflare Worker targets locally.

---

## 1. Prerequisites

| Tool / Runtime | Required Version | Required For |
|---|---|---|
| **Git** | Any modern version | Cloning repository |
| **Python** | `3.12+` (verified in `Dockerfile` & GitHub Actions) | Backend API, Desktop Client, CLI scripts |
| **Node.js & npm** | Node `22.x` (verified in `.github/workflows/deploy.yml`) | Ionic Angular Web/PWA & Android frontend |
| **Docker Desktop** *(optional)* | Docker Engine + Compose v2 | Local PostgreSQL 16 (`docker-compose.yml`). If omitted, backend automatically falls back to SQLite (`nueva_ecija_travel.db`). |
| **Java JDK & Android SDK** *(optional)* | Eclipse Temurin **JDK 21** + Android SDK (auto-downloads Build-Tools/Platform via `android.builder.sdkDownload=true` with Gradle `8.13`) | Building Android APK (`Project/android/`) |
| **Inno Setup 6** *(optional, Windows)* | `ISCC.exe` v6 | Compiling single-file Windows `NuevaEcijaTravel_Setup_v1.0.0.exe` |
| **Cloudflare Wrangler / `cloudflared` / `ngrok`** *(optional)* | Latest | Remote tunneling & Cloudflare Worker proxy |

---

## 2. Repository & Environment Setup

### Step 1 — Clone the Repository
```bash
git clone https://github.com/Edselrenz/Itinerary-App.git
cd Itinerary-App
```

### Step 2 — Configure Environment Variables
```bash
# Backend root environment
cp .env.example .env

# Desktop client environment (optional)
cp desktop_client/.env.example desktop_client/.env
```
Edit `.env` and set a strong `JWT_SECRET_KEY` (generate via `openssl rand -hex 32`).

### Step 3 — Backend Virtual Environment & Dependencies
```bash
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# macOS / Linux:
source .venv/bin/activate

pip install --upgrade pip
pip install -r backend/requirements.txt
```

### Step 4 — Database Initialization & Seeding
**Option A: PostgreSQL 16 via Docker (Recommended)**
```bash
docker compose up -d
python scripts/setup_postgres.py
```
`scripts/setup_postgres.py` waits for PostgreSQL on `127.0.0.1:5432`, runs `alembic upgrade head`, and automatically invokes `scripts/seed_featured_places.py` (12 core municipalities + 18 featured destinations) if empty.

**Option B: Zero-Config Local SQLite**
In `.env`, uncomment:
```ini
DATABASE_URL=sqlite:///./nueva_ecija_travel.db
```
Then run `python scripts/setup_postgres.py` (creates tables via `Base.metadata.create_all` and seeds curated places).

*(Optional)* Populate full OpenStreetMap catalog & verify row counts:
```bash
python scripts/fetch_osm_places.py
python scripts/import_osm.py data/raw/nueva_ecija_osm.json
python scripts/export_osm_to_client_asset.py
python scripts/db_query.py --tables
```

### Step 5 — Frontend Dependencies (`Project/`)
```bash
cd Project
npm ci
cd ..
```

### Step 6 — Desktop Client Dependencies (`desktop_client/`)
```bash
pip install -r desktop_client/requirements.txt
```

---

## 3. Environment Variables Reference

### Backend (`.env` — loaded by `backend/app/core/config.py`)
| Variable | Purpose | Required | Example Format | Used By |
|---|---|---|---|---|
| `APP_ENV` | Runtime mode (`development` enables `/docs`, relaxes secret check; `production` enforces strict JWT secret) | No (default `development`) | `development` / `production` | `backend/app/main.py`, `config.py` |
| `API_V1_PREFIX` | REST route prefix | No (default `/api/v1`) | `/api/v1` | `backend/app/main.py` |
| `DATABASE_URL` | SQLAlchemy connection string | Yes (defaults to local PG) | `postgresql+psycopg://user:pass@127.0.0.1:5432/nueva_ecija_travel` | `backend/app/core/database.py`, `alembic/env.py` |
| `JWT_SECRET_KEY` | HS256 signing key (min 32 chars in prod) | **Yes in prod** | `<64-char hex via openssl rand -hex 32>` | `backend/app/services/auth_service.py` |
| `JWT_ALGORITHM` | JWT signing algorithm | No (default `HS256`) | `HS256` | `auth_service.py` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token TTL | No (default `30`) | `30` | `auth_service.py` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token TTL | No (default `7`) | `7` | `auth_service.py` |
| `CORS_ORIGINS` | JSON array of allowed origins | No | `["http://localhost:4200","http://localhost:8100"]` | `backend/app/main.py` |
| `CORS_ORIGIN_REGEX` | Regex for dynamic tunnel/localhost origins | No | `^https?://localhost(:\d+)?$` | `backend/app/main.py` |
| `GOOGLE_OAUTH_CLIENT_ID` | Google OAuth audience for ID token check | Optional | `<id>.apps.googleusercontent.com` | `auth_service.py` |
| `ENABLE_APPLE_AUTH` | Feature flag for Apple Sign-In (currently 501) | No (default `false`) | `false` | `backend/app/api/v1/auth.py` |
| `DEFAULT_DEST_RADIUS_KM` | Clustering radius for suggested itineraries | No (default `25.0`) | `25.0` | `itinerary_generator.py` |
| `GOOGLE_MAPS_API_KEY` | Google Places (New) & Routes v2 key | Optional | `<google-api-key>` | `google_maps_service.py`, `places.py` |
| `GOOGLE_PLACES_CACHE_TTL_HOURS` | Discovery cache TTL | No (default `168`) | `168` | `google_maps_service.py` |
| `GOOGLE_DETAILS_CACHE_TTL_HOURS` | Place details cache TTL | No (default `24`) | `24` | `google_maps_service.py` |
| `GOOGLE_ROUTES_CACHE_TTL_HOURS` | Routes cache TTL | No (default `336`) | `336` | `google_maps_service.py` |
| `WORKER_SYNC_URL` | Cloudflare Worker base URL for tunnel sync | Optional | `https://ne-itinerary-api.<subd>.workers.dev` | `scripts/start_server.ps1`, `run_daemon.py` |
| `WORKER_SYNC_KEY` | Shared secret sent in `X-Admin-Sync-Key` | Optional | `<random-secret>` | `scripts/start_server.ps1`, `run_daemon.py` |

### Desktop Client (`desktop_client/.env` — loaded by `desktop_client/config/settings.py`)
| Variable | Purpose | Required | Example Format |
|---|---|---|---|
| `API_BASE_URL` | Backend REST API URL | No | `http://127.0.0.1:8000/api/v1` |
| `APP_TITLE` | Window title | No | `Trip mo, trip ko — Nueva Ecija Desktop` |
| `APP_ENV` | Environment label | No | `development` |
| `API_TIMEOUT_SECONDS` | Standard HTTP timeout | No (default `15`) | `15` |
| `ITINERARY_GEN_TIMEOUT_SECONDS` | Timeout for `/itineraries/suggest` | No (default `45`) | `45` |
| `DEBUG` | Debug logging flag | No (default `False`) | `False` |

---

## 4. Running the Complete Application Locally

**Required Startup Order**: `1. Database` → `2. FastAPI Backend` → `3. Web Frontend and/or Desktop Client`.

| Service | Command | Default Port | Local URL |
|---|---|---|---|
| **PostgreSQL 16** | `docker compose up -d` | `5432` | `127.0.0.1:5432` |
| **FastAPI Backend (Dev)** | `uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port 8000` | `8000` | `http://127.0.0.1:8000/api/v1/health` (Swagger: `http://127.0.0.1:8000/docs`) |
| **FastAPI + Dual Tunnels (Windows)** | `start_server.bat` (or `.\scripts\start_server.ps1 -NoTunnel` for local-only) | `8000` | `http://127.0.0.1:8000` |
| **Ionic Angular Web Dev Server** | `cd Project && npm start` (or `npx ionic serve`) | `4200` / `8100` | `http://localhost:4200/#/welcome` |
| **Flet Desktop Client** | `python desktop_client/main.py` (or `run_desktop_app.bat`) | Native Window | Desktop GUI |

> **Pointing Local Web Dev to Local Backend**: By default, `Project/src/environments/environment.ts` points to the Cloudflare Worker URL (`https://ne-itinerary-api.edselrenz0.workers.dev/api/v1`). To point the browser to your local Uvicorn server without editing code, set `localStorage.setItem('ne_custom_api_url', 'http://127.0.0.1:8000/api/v1')` (or configure it in **Profile → Settings**) and reload.

---

## 5. Common Installation Problems

| Issue | Likely Cause | Solution |
|---|---|---|
| `ValueError: jwt_secret_key must be explicitly configured` | `APP_ENV` is set to `production` with default `JWT_SECRET_KEY` | Generate a 64-char hex secret (`openssl rand -hex 32`) and set `JWT_SECRET_KEY` in `.env`. |
| Backend starts but uses SQLite instead of PostgreSQL | Docker Desktop not running or port `5432` unreachable within 2s | Start Docker Desktop, run `docker compose up -d`, and restart Uvicorn. |
| `npm ci` fails or Angular CLI complains about Node version | Node.js version `< 22` | Install Node.js `22.x` via nvm/fnm and re-run `npm ci` inside `Project/`. |
| CORS error when calling local backend from `localhost:4200` | Origin missing from `CORS_ORIGINS` | Verify `http://localhost:4200` is in `CORS_ORIGINS` or `CORS_ORIGIN_REGEX` in `.env` and restart Uvicorn. |
| Gradle Android build fails with Java version error | JDK version is not 21 | Install Eclipse Temurin JDK 21 and set `JAVA_HOME` (or use `scripts/build_android_apk.ps1` which auto-detects Android Studio JBR). |

---

## 6. Technical Terms & Concepts Explained (How It Works & What It Is Used For in This System)

| Technical Term | How It Works (Technical & Layman Explanation) | What It Is Used For in This System |
|---|---|---|
| **Python Virtual Environment (`.venv`)** | **Layman**: An isolated "sandbox" folder for Python libraries so the packages installed for this project (like FastAPI and Flet) never clash with other Python programs on your computer.<br>**Technical**: Created via `python -m venv .venv`, providing a dedicated Python interpreter binary and `site-packages` directory isolated from the OS system Python. | Hosts all backend (`backend/requirements.txt`) and desktop (`desktop_client/requirements.txt`) dependencies during local development and PyInstaller compilation. |
| **Environment Variables (`.env` & `pydantic-settings`)** | **Layman**: Secret configuration settings (like database passwords and API keys) stored in a local `.env` text file that is excluded from Git so passwords are never accidentally uploaded to GitHub.<br>**Technical**: Key-value pairs read from the OS process environment or `.env` file by `pydantic_settings.BaseSettings` (`backend/app/core/config.py`) and `python-dotenv` (`desktop_client/config/settings.py`) and coerced into strongly typed Python attributes. | Configures `DATABASE_URL`, `JWT_SECRET_KEY`, `GOOGLE_MAPS_API_KEY`, `CORS_ORIGINS`, `WORKER_SYNC_URL`, and `API_BASE_URL` per environment without changing source code. |
| **`npm ci` vs. `npm install`** | **Layman**: `npm install` might download slightly newer sub-packages than what the team tested, whereas `npm ci` ("Clean Install") installs the *exact* locked versions listed in `package-lock.json` down to the last digit.<br>**Technical**: Deletes `node_modules/` and installs exact dependency versions from `Project/package-lock.json`, failing immediately if `package.json` and `package-lock.json` are out of sync. | Used in local setup and GitHub Actions (`.github/workflows/deploy.yml`, `release-builds.yml`) to guarantee reproducible Angular 22.2.3 and Capacitor 8.6.0 builds. |
| **Docker & Docker Compose (`docker-compose.yml`)** | **Layman**: Instead of manually installing and configuring a complex PostgreSQL database server on Windows or macOS, Docker runs PostgreSQL inside a lightweight, pre-configured virtual container with one command (`docker compose up -d`).<br>**Technical**: Declarative container orchestration defining the `postgres:16-alpine` image, persistent volume (`ne_postgres_data`), port mapping (`5432:5432`), and `pg_isready` health check. | Provides the local development PostgreSQL 16 database (`docker-compose.yml`) and the full multi-container production stack (`docker-compose.prod.yml`). |
| **JDK 21 & Gradle Wrapper (`gradlew`, `gradle-8.13-bin.zip`)** | **Layman**: Android apps are compiled using Java tools. **JDK 21** is the Java compiler kit, and the **Gradle Wrapper (`gradlew`)** automatically downloads the exact build engine version (`Gradle 8.13`) and Android SDK pieces needed to assemble the `.apk` file.<br>**Technical**: `Project/android/gradle/wrapper/gradle-wrapper.properties` pins `gradle-8.13-bin.zip`, and `Project/android/gradle.properties` sets `android.builder.sdkDownload=true` so the Android Gradle Plugin automatically provisions missing SDK platforms and build-tools. | Compiles the Capacitor Android project (`Project/android/`) into `TripMoTripKo-debug.apk` and `TripMoTripKo-release.apk` via `scripts/build_android_apk.ps1` and GitHub Actions. |
