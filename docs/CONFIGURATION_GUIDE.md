# Configuration Guide: Nueva Ecija Travel Itinerary

This guide provides setup and runtime instructions for local development, testing, and deployment.

---

## 1. Prerequisites & Required Tools

| Runtime / Tool | Verified Version | Installation Check |
| :--- | :--- | :--- |
| **Node.js** | v24.19.0 (or v20+ LTS) | `node -v` |
| **npm** | 11.10.0 (or v10+) | `npm -v` |
| **Python** | 3.14.3 (or 3.11+) | `python --version` |
| **Ionic CLI** | Global or local (`@ionic/cli`) | `npx ionic -v` |
| **PostgreSQL** (Optional for dev) | 15+ | `psql --version` |

---

## 2. Environment Variables Specification (`.env`)

The application loads environment variables using Pydantic Settings from the repository root `.env`. An `.env.example` file is provided as a non-secret template.

| Variable Name | Default / Example Value | Description |
| :--- | :--- | :--- |
| `APP_ENV` | `development` | Set to `development`, `testing`, or `pilot`. Controls `/docs` exposure. |
| `API_V1_PREFIX` | `/api/v1` | URL routing prefix for all REST endpoints. |
| `DATABASE_URL` | `postgresql+psycopg://ne_travel_user:change_me_local_only@127.0.0.1:5432/nueva_ecija_travel` | Database connection string. For quick local dev without Postgres, use `sqlite:///./nueva_ecija_travel.db`. |
| `JWT_SECRET_KEY` | *(64-char hex)* | Cryptographic HMAC secret for signing access and refresh tokens. |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token lifetime. |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token lifetime. |
| `CORS_ORIGINS` | `["http://localhost:8100", "http://localhost:4200", "capacitor://localhost", "http://localhost"]` | Allowed CORS origins for the hybrid client. |
| `GOOGLE_OAUTH_CLIENT_ID` | `your-google-client-id.apps.googleusercontent.com` | Google Cloud Web Client ID for server-side ID token verification. |
| `ENABLE_APPLE_AUTH` | `false` | Apple Sign-In feature flag. Keep `false` unless paid Apple Developer membership is active. |
| `DEFAULT_DEST_RADIUS_KM` | `25.0` | Default search radius in kilometers for destination clustering. |

---

## 3. Setup Commands

### 3.1 Backend Setup
1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```
2. Install Python dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
3. Run Alembic migrations (when using PostgreSQL):
   ```bash
   cd backend && alembic upgrade head
   ```
4. Seed municipalities and curated featured places:
   ```bash
   python scripts/seed_featured_places.py
   ```
5. Start the FastAPI local development server:
   ```bash
   python -m uvicorn app.main:app --app-dir backend --reload --port 8000
   ```
   Verify at `http://127.0.0.1:8000/api/v1/health`.

### 3.2 Mobile App Setup (`Project/`)
1. Navigate to the client directory:
   ```bash
   cd Project
   ```
2. Install npm dependencies:
   ```bash
   npm install
   ```
3. Start the Angular / Ionic development server:
   ```bash
   npm start
   ```
   Opens on `http://localhost:4200` (or `http://localhost:8100`).
4. Build production bundle:
   ```bash
   npm run build
   ```

---

## 4. Running Automated Tests

- **Run all backend pytest suites**:
  ```bash
  python -m pytest backend/tests/ -v
  ```
- **Run mobile TypeScript checks**:
  ```bash
  cd Project && npm run typecheck:e2e
  ```

---

## 5. Cloudflare Worker Reverse Proxy Setup (Option 2)

Option 2 enables zero-touch connectivity between the static GitHub Pages application and your laptop's backend, bypassing residential ISP DNS blocks (PLDT, Converge, Globe, Smart) and home router NXDOMAIN caching.

### 5.1 Environment Variables (.env)
Add the following optional variables to `.env` on your laptop:
```env
# Cloudflare Worker Reverse Proxy Endpoint
WORKER_SYNC_URL=https://ne-itinerary-api.<your-subdomain>.workers.dev

# Shared secret key between laptop start_server.ps1 and Cloudflare Worker
WORKER_SYNC_KEY=your_chosen_admin_sync_secret_key
```

### 5.2 Deploying the Worker (2 Minutes)
1. Go to [dash.cloudflare.com](https://dash.cloudflare.com/) &rarr; **Storage & Databases** &rarr; **KV** &rarr; Create namespace `TUNNEL_KV`.
2. Go to **Compute (Workers)** &rarr; **Create Worker** (`ne-itinerary-api`).
3. Paste code from [`cloudflare-worker/worker.js`](../cloudflare-worker/worker.js) and click **Deploy**.
4. In Worker **Settings** &rarr; **Variables & Secrets**:
   - Bind KV namespace `TUNNEL_KV` to variable `TUNNEL_KV`.
   - Add environment variable `ADMIN_SYNC_KEY` with your secret key.
5. In your laptop `.env`, set `WORKER_SYNC_URL` and `WORKER_SYNC_KEY`.
6. Run `start_server.bat`. It will automatically sync active tunnels (`$cfUrl` and `$ngrokUrl`) to the worker on startup.
