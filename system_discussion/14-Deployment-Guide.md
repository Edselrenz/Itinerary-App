# 14 — Deployment and Production Management

This guide documents the **actual verified deployment pipelines and Phase 62 (`v1.0.0`) release deliverables** implemented in `.github/workflows/`, `backend/Dockerfile`, `docker-compose.prod.yml`, `cloudflare-worker/`, and `scripts/`, followed by **recommended production hardening** where cloud infrastructure is not yet provisioned.

---

## 1. Verified Deployment Targets & Phase 62 (`v1.0.0`) Release Artifacts

### 1.1 Verified Phase 62 (`v1.0.0`) Binary Deliverables & Checksums

All standalone desktop and mobile deliverables were rebuilt and verified in Phase 62 (`v1.0.0`):

| Platform & Artifact | Output Path | Verified Size | SHA-256 Checksum / Verification Details |
|---|---|---|---|
| **Windows Inno Setup Installer** | `dist_installer\NuevaEcijaTravel_Setup_v1.0.0.exe` | **`156.58 MB`** (`164,181,396` B) | `3D08D6BAE3EB3926C0AFEA4FEB211D8BAF2FA9F36D1B0FA241F9EDE50CDFF410` (LZMA2/ultra64, `PrivilegesRequired=lowest`) |
| **Windows Portable Archive** | `dist_installer\NuevaEcijaTravel_Portable_Installer_v1.0.0.zip` | **`232.64 MB`** (`243,942,337` B) | `3ED786E2FB9F0EE6E65373C0DBD56C3EF9E8B3C819D6227E36068FE936917708` (Deflate level 6 via Python `zipfile`) |
| **Windows Standalone Executable Bundle** | `dist\NuevaEcijaTravel\NuevaEcijaTravel.exe` | **`15.27 MB`** (`411.57 MB` bundle) | Includes `flet/flet.exe`, `flet/controls/material/icons.json`, `cupertino_icons.json`, `welcome_hero_buildings_wide.png`, `2,673` OSM POIs, and offline map tiles |
| **Android Signed Release APK** | `dist_apk\TripMoTripKo-release.apk` | **`29.72 MB`** (`31,162,864` B) | `0C5CED791D824CD81DF294198481C9F99E9175DC1AA336123B5B1E32BE1E80C6` (Verified via `apksigner`: v1 JAR + v2 + v3 scheme, RSA-2048 `CN=Trip Mo Trip Ko, O=Nueva Ecija Travel`) |
| **Android Debug APK** | `dist_apk\TripMoTripKo-debug.apk` | **`30.88 MB`** (`32,378,996` B) | `C611658A662C68967B819481C9F99E9175DC1AA336123B5B1E32BE1E80C6` / `C611658A662C68967B8174E1963C69AE74AA6D0945D3B4106AB7701DF03AB4EB` |

---

### 1.2 Web / PWA Deployment — GitHub Pages (Automated CI/CD)
- **Workflow**: `.github/workflows/deploy.yml` (triggers on push to `main` or `workflow_dispatch`).
- **Live URL**: `https://edselrenz.github.io/Itinerary-App/`.
- **Exact Pipeline Steps**:
  1. Python `3.12` setup → `pip install -r backend/requirements.txt` → `python -m pytest backend/tests/ -v` (21 tests).
  2. Node.js `22` setup → `npm ci` (in `Project/`) → `npm run test:unit` (348 Vitest unit tests).
  3. Ensures `Project/src/environments/environment.prod.ts` exists (copies from `environment.example.ts` if absent).
  4. Builds production PWA bundle: `npm run build -- --base-href /Itinerary-App/` (outputs to `Project/www`, with `ngsw-config.json` Service Worker enabled).
  5. Prepares GitHub Pages SPA support: `touch Project/www/.nojekyll` and `cp Project/src/404.html Project/www/404.html`.
  6. Uploads `Project/www` via `actions/upload-pages-artifact@v3` and deploys via `actions/deploy-pages@v4`.

### 1.3 Android APK & Windows Desktop Installer — GitHub Releases (Automated CI/CD)
- **Workflow**: `.github/workflows/release-builds.yml` (triggers on `v*` tags or manual `workflow_dispatch`).
- **Job 1 — Android APK (`ubuntu-latest`, Node 22, Temurin JDK 21, Gradle 8.13)**:
  - `npx ng build --configuration production --no-service-worker` (SW disabled for native Android WebView using Angular 22 CLI flag).
  - `npx cap sync android`
  - `./gradlew assembleDebug --no-daemon` → `TripMoTripKo-debug.apk`.
  - If repository secrets `ANDROID_KEYSTORE_BASE64`, `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS`, and `ANDROID_KEY_PASSWORD` are set, writes temporary `keystore.properties`, runs `./gradlew assembleRelease --no-daemon` → `TripMoTripKo-release-signed.apk`, and deletes keystore files immediately.
  - Local Windows equivalent: `.\scripts\build_android_apk.ps1 -BuildType both` (auto-provisions missing Android SDK tools via `android.builder.sdkDownload=true`).
- **Job 2 — Windows Desktop Installer (`windows-latest`, Python 3.12, Inno Setup 6)**:
  - Caches Flet desktop Flutter engine (`flet_desktop.ensure_client_cached()`).
  - Runs `python scripts/build_standalone_exe.py` (stages PyInstaller build in `build_temp/dist_stage/NuevaEcijaTravel` bundling `flet/controls/material/icons.json`, `certifi`, `tzdata`, and `desktop_client/assets/`, then syncs to `dist/NuevaEcijaTravel/NuevaEcijaTravel.exe` with NTFS `.old` hot-swap protection).
  - Runs `ISCC.exe installer\NuevaEcijaTravel.iss` → `dist_installer/NuevaEcijaTravel_Setup_v1.0.0.exe` (LZMA2 ultra64, installs to `%LOCALAPPDATA%\Programs\NuevaEcijaTravel` with `PrivilegesRequired=lowest` — no UAC admin prompt).
  - Archives `dist_installer/NuevaEcijaTravel_Portable_Installer_v1.0.0.zip` using Python's `zipfile.ZipFile(..., ZIP_DEFLATED, compresslevel=6)`.
  - Local Windows equivalent: `.\scripts\build_desktop_installer.ps1`.
- **Job 3 — GitHub Release**: Generates `SHA256SUMS.txt` and publishes all `.apk`, `.exe`, and `.zip` assets via `softprops/action-gh-release@v2`.

### 1.4 Cloudflare Worker Edge Proxy (`cloudflare-worker/`)
- **Purpose**: Fixed HTTPS gateway (`https://ne-itinerary-api.edselrenz0.workers.dev`) routing traffic to the host machine's active Cloudflare Tunnel (`cfUrl`) or `ngrok` fallback (`ngrokUrl`) stored in Cloudflare KV (`TUNNEL_KV`).
- **Deployment Commands**:
  ```bash
  cd cloudflare-worker
  npx wrangler kv:namespace create TUNNEL_KV
  # Paste generated id / preview_id into wrangler.toml
  npx wrangler secret put ADMIN_SYNC_KEY
  npx wrangler deploy
  ```

### 1.5 Backend Container Deployment (`backend/Dockerfile` & `docker-compose.prod.yml`)
- **Dockerfile**: Multi-stage `python:3.12-slim` image copying `backend/app`, `backend/alembic`, `backend/alembic.ini`, and `scripts/`. Runs `uvicorn app.main:app --host 0.0.0.0 --port 8000` with `APP_ENV=production` and 30s `HEALTHCHECK` on `/api/v1/health`.
- **Startup Commands**:
  ```bash
  export POSTGRES_USER=ne_travel_user
  export POSTGRES_PASSWORD="<strong-unique-password>"
  export POSTGRES_DB=nueva_ecija_travel
  export JWT_SECRET_KEY="$(openssl rand -hex 32)"

  docker compose -f docker-compose.prod.yml up -d --build
  docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
  docker compose -f docker-compose.prod.yml exec backend python scripts/seed_featured_places.py
  ```

---

## 2. Recommended Production Cloud Architecture (Not Yet Provisioned)

The current pilot architecture relies on a host machine running `start_server.bat` + Cloudflare Tunnel + Cloudflare Worker. For 24/7 public production availability, the following **recommended** migration is advised:
1. **Managed Backend Hosting**: Deploy `backend/Dockerfile` to Render, Koyeb, Railway, or Fly.io (note that `*.onrender.com` and `*.koyeb.app` are already in `Project/src/environments/environment.prod.ts`'s trusted hostname allowlist).
2. **Managed PostgreSQL**: Provision managed PostgreSQL 16 (e.g., Neon, Supabase, or Render Postgres) with automated daily snapshots and TLS (`sslmode=require`).
3. **HTTPS & Reverse Proxy**: Terminate TLS at the cloud load balancer / Cloudflare proxy; restrict `CORS_ORIGINS` strictly to `https://edselrenz.github.io` and `capacitor://localhost` (remove wildcard tunnel regex).
4. **Secrets & Observability**: Store `JWT_SECRET_KEY`, `DATABASE_URL`, `GOOGLE_MAPS_API_KEY`, and `GOOGLE_OAUTH_CLIENT_ID` in the cloud provider's secret manager; attach structured JSON logging and uptime alerting on `GET /api/v1/health`.
5. **Rollback Procedure**:
   - **Web/PWA**: Re-run previous passing commit on `.github/workflows/deploy.yml` or revert commit on `main`.
   - **Backend Container**: Re-deploy previous image tag and, if a migration caused regression, run `alembic downgrade -1` (after restoring from pre-migration backup via `scripts/db_backup_restore.py restore`).

---

## 3. Technical Terms & Concepts Explained (How It Works & What It Is Used For in This System)

| Technical Term | How It Works (Technical & Layman Explanation) | What It Is Used For in This System |
|---|---|---|
| **CI/CD (Continuous Integration / Continuous Deployment — GitHub Actions)** | **Layman**: An automated robot assembly line on GitHub. Every time code is pushed, the robot runs all automated tests (**CI**); if every test passes, it automatically builds the website or installer packages and publishes them online (**CD**).<br>**Technical**: Event-driven YAML workflows (`.github/workflows/deploy.yml` and `release-builds.yml`) executing on ephemeral Ubuntu and Windows virtual runners in GitHub Actions. | Automates running our Backend Pytest and Web Vitest suites, deploying the PWA to GitHub Pages, and compiling Android `.apk` and Windows `Setup.exe` release binaries. |
| **APK Signing, RSA-2048 Keystore (`.jks`) & `apksigner` (v1/v2/v3 Schemes)** | **Layman**: Android phones refuse to install an `.apk` file unless it carries an unforgeable cryptographic wax seal (**Digital Signature**) proving who built the app and guaranteeing nobody tampered with the file after it was built.<br>**Technical**: A Java KeyStore (`release-keystore.jks`, excluded from Git) holds a 2048-bit RSA private key (`SHA256withRSA`). Gradle signs the release APK using Android Signature Schemes **v1 (JAR)**, **v2 (Full APK Signature Block)**, and **v3 (Key Rotation)**, verified by Android SDK Build-Tools `apksigner verify`. | Signs `dist_apk/TripMoTripKo-release.apk` (`29.72 MB`) so it can be installed directly onto physical Android devices without tampering warnings. |
| **LZMA2 / `ultra64` Solid Compression (`installer/NuevaEcijaTravel.iss`)** | **Layman**: An extra-powerful file compression engine that squeezes a `411 MB` desktop app folder down into a single `156 MB` setup file by finding repeated patterns across all files at once.<br>**Technical**: The **Lempel-Ziv-Markov chain Algorithm 2 (LZMA2)** configured at `ultra64` dictionary size with `SolidCompression=yes` in Inno Setup 6 (`ISCC.exe`), compressing the entire PyInstaller payload as a continuous byte stream. | Produces `dist_installer/NuevaEcijaTravel_Setup_v1.0.0.exe` (`156.58 MB`), achieving a 62% size reduction over the uncompressed `411.57 MB` standalone bundle. |
| **SHA-256 Cryptographic Checksum (`SHA256SUMS.txt`)** | **Layman**: A unique 64-character digital fingerprint calculated from every byte of a downloadable `.exe`, `.zip`, or `.apk` file. If even one bit of the file is corrupted during download, the SHA-256 fingerprint changes completely.<br>**Technical**: The **Secure Hash Algorithm 256-bit (FIPS 180-4)** one-way cryptographic digest computed over binary release artifacts. | Published alongside every release build (`Setup.exe`, Portable `.zip`, `TripMoTripKo-release.apk`, `TripMoTripKo-debug.apk`) to verify file integrity and authenticity. |
| **`.nojekyll` & `404.html` GitHub Pages SPA Routing** | **Layman**: GitHub Pages normally uses a blog tool called Jekyll that ignores folders starting with `_` and shows a generic 404 error if you refresh a deep link. Adding an empty `.nojekyll` file turns off Jekyll, and `404.html` catches any deep URL and hands it back to our Angular app.<br>**Technical**: Static hosting configuration created during `.github/workflows/deploy.yml` inside `Project/www/` before `actions/upload-pages-artifact@v3`. | Ensures all Angular chunks, underscore-prefixed assets, and deep client routes load reliably on `https://edselrenz.github.io/Itinerary-App/`. |
