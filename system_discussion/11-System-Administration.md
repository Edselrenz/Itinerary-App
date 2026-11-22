# 11 — System Administration and Maintenance

This manual documents the operational procedures supported by the actual scripts, containers, and edge infrastructure in `Edselrenz/Itinerary-App` (`v1.0.0`).

---

## 1. Service Lifecycle Management

### Windows Host Operations (Pilot / Tunneled Mode)
- **Start Full Stack + Dual Tunnels**: Run `start_server.bat` (executes `scripts/start_server.ps1`).
  1. Checks `.env` for SQLite vs. PostgreSQL; starts Docker PostgreSQL container if needed.
  2. Runs `python scripts/setup_postgres.py` to verify schema & seed data.
  3. Starts Uvicorn on `0.0.0.0:8000`.
  4. Launches Cloudflare Quick Tunnel (`cloudflared`) and `ngrok` fallback tunnel, and POSTs active URLs to `WORKER_SYNC_URL/__sync_tunnel` using `X-Admin-Sync-Key`.
- **Start Local Only (No Tunnels)**: `powershell -File scripts/start_server.ps1 -NoTunnel`.
- **Stop All Services**: Run `stop_server.bat` (executes `scripts/stop_server.ps1`):
  - Terminates `cloudflared` and `ngrok` processes and removes `%TEMP%\ne_cloudflared.log` / `ne_ngrok.log`.
  - Terminates processes bound to ports `8000` (FastAPI), `4200` (Angular), and `8100` (Ionic).
  - Pass `-KeepDatabase` to leave PostgreSQL running.

### Docker Production Stack (`docker-compose.prod.yml`)
```bash
# Start PostgreSQL 16 + FastAPI container in background
docker compose -f docker-compose.prod.yml up -d --build

# Check container health & logs
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f backend

# Restart backend after .env update
docker compose -f docker-compose.prod.yml restart backend

# Stop stack (preserves ne_postgres_prod_data volume)
docker compose -f docker-compose.prod.yml down
```

---

## 2. Health Monitoring, Database Inspection & Logs

| Component | Health Endpoint / Command | Expected Healthy Output |
|---|---|---|
| **FastAPI Backend** | `curl -f http://localhost:8000/api/v1/health` (also Docker `HEALTHCHECK` every 30s) | `{"status":"ok","province_scope":"Nueva Ecija","environment":"..."}` |
| **Cloudflare Worker Proxy** | `curl https://ne-itinerary-api.<subdomain>.workers.dev/__status` | `{"status":"ok","worker":"nueva-ecija-api-proxy","active_tunnels":{...}}` |
| **PostgreSQL Container** | `docker exec ne_postgres pg_isready -U ne_travel_user -d nueva_ecija_travel` | `accepting connections` |
| **Dual-Engine DB Query CLI** | `python scripts/db_query.py --tables` (or `python scripts/db_query.py --postgres --tables`) | Table list + row counts across all 8 schema tables (`2,673` places, `18` featured, `12+` municipalities) |
| **Backend Logs** | Docker: `docker compose logs -f backend`; Local: Uvicorn stdout/stderr | Standard Python `logging` + Uvicorn access logs |
| **Tunnel Logs (Windows)** | `%TEMP%\ne_cloudflared.log`, `%TEMP%\ne_ngrok.log`, `scratch/active_tunnel.txt` | Active `*.trycloudflare.com` and `*.ngrok-free.dev` URLs |

> **Administrative Inspection (`scripts/db_query.py`)**: Because there is no in-app web admin panel, administrators can inspect or update database records directly from the command line using `python scripts/db_query.py` (which supports an interactive SQL REPL with `.tables`, `.schema <table>`, `.count`, and `.quit`, or one-shot SQL strings against either SQLite or PostgreSQL).

---

## 3. Database Backup, Restore & Migrations

### Automated Backup & Restore (`scripts/db_backup_restore.py`)
Supports both PostgreSQL (`pg_dump` / `psql`) and SQLite (binary snapshot or `.sql` `iterdump()`):
```bash
# Create timestamped backup in backups/
python scripts/db_backup_restore.py backup

# Create backup at explicit path
python scripts/db_backup_restore.py backup --output backups/pre_release_snapshot.sql

# Restore from backup
python scripts/db_backup_restore.py restore backups/pre_release_snapshot.sql
```
> **Recommended Maintenance Cadence**: Take a backup before every `alembic upgrade head`, OSM bulk import, or production release.

### Applying Schema Migrations
```bash
# Local / Host
cd backend && alembic upgrade head

# Inside Docker production container
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

---

## 4. POI Catalog & Offline Asset Refresh

When refreshing OpenStreetMap data for Nueva Ecija:
```bash
# 1. Fetch latest POIs from Overpass API -> data/raw/nueva_ecija_osm.json
python scripts/fetch_osm_places.py

# 2. Preview import changes (idempotent upsert by source_name + source_record_id)
python scripts/import_osm.py data/raw/nueva_ecija_osm.json --dry-run

# 3. Apply import and re-verify curated featured venues
python scripts/import_osm.py data/raw/nueva_ecija_osm.json
python scripts/seed_featured_places.py

# 4. Regenerate bundled offline JSON for Web/Android and mirror to Desktop
python scripts/export_osm_to_client_asset.py
cp Project/src/assets/data/osm_places.json desktop_client/assets/data/osm_places.json
```

---

## 5. Cache & Storage Maintenance

- **Backend `geospatial_cache` Table**: Expired entries are ignored by `expires_at > now()`, but no automatic background purge job exists. Periodically clean expired rows via `scripts/db_query.py`:
  ```bash
  python scripts/db_query.py "DELETE FROM geospatial_cache WHERE expires_at < CURRENT_TIMESTAMP"
  ```
- **Cloudflare KV Edge Cache**: Entries (`EDGE_CACHE_*`) auto-expire after `86400s` (24 hours).
- **Desktop Tile Cache**: Pre-seeded tiles live in `desktop_client/assets/tiles/`; runtime tiles cache in `desktop_client/assets/tiles_cache/` or `%LOCALAPPDATA%\NuevaEcijaTravel\storage\tiles_cache/` when installed in a read-only directory. Use `python desktop_client/scripts/clean_and_seed_tiles.py` to maintain offline tiles.
- **Dependency Updates**:
  - Backend: update `backend/requirements.txt` and run `python -m pytest backend/tests/ -v`.
  - Frontend: update `Project/package.json`, run `npm run test:unit && npm run lint`.
  - Desktop: update `desktop_client/requirements.txt` and run `python -m pytest desktop_client/tests/ -v`.

---

## 6. Technical Terms & Concepts Explained (How It Works & What It Is Used For in This System)

| Technical Term | How It Works (Technical & Layman Explanation) | What It Is Used For in This System |
|---|---|---|
| **Daemon Process (`scripts/run_daemon.py`)** | **Layman**: A background helper program that runs quietly without needing a person to keep typing commands, watching over the server and tunnels and restarting or syncing them automatically.<br>**Technical**: A long-running supervisor script that spawns child subprocesses (`uvicorn`, `cloudflared`, `ngrok`), parses their stdout/log files for allocated `https://` tunnel endpoints, and periodically heartbeats `POST /__sync_tunnel`. | Automates local host backend and dual-tunnel startup on Windows (`start_server.bat`). |
| **`pg_dump`, `psql` & SQLite `iterdump()` (`scripts/db_backup_restore.py`)** | **Layman**: Tools that export the entire contents of a database (all tables, columns, users, places, and saved itineraries) into a single backup file so the database can be restored to that exact moment if anything ever goes wrong.<br>**Technical**: `pg_dump` and `psql` are PostgreSQL's native logical backup/restore CLI utilities; `sqlite3.Connection.iterdump()` generates an equivalent transactional SQL script (`BEGIN TRANSACTION; CREATE TABLE... INSERT INTO... COMMIT;`) for SQLite databases. | Wrapped by `scripts/db_backup_restore.py` (and tested by `backend/tests/test_backup_restore.py`) to provide unified single-command backup and recovery across both database engines. |
| **Idempotent Upsert (`import_osm.py` & `seed_featured_places.py`)** | **Layman**: "Idempotent" means you can run the import script 1 time or 50 times in a row without creating duplicate places. "Upsert" (Update + Insert) checks if a place already exists: if it does, it updates its details; if it doesn't, it inserts it as new.<br>**Technical**: Queries `Place` by `(source_name, source_record_id)` or `google_place_id` before deciding whether to mutate the existing ORM entity or `db.add()` a new entity, guarded by `uq_place_source_record`. | Allows administrators to re-run `scripts/import_osm.py` and `scripts/seed_featured_places.py` safely whenever new OpenStreetMap data is fetched. |
| **Dual-Engine SQL REPL (`scripts/db_query.py`)** | **Layman**: An interactive command-line console ("Read-Eval-Print Loop") where an administrator can type SQL questions or commands (like `.tables` or `SELECT * FROM users`) and immediately see formatted tables on screen.<br>**Technical**: A Python CLI tool that connects directly to `nueva_ecija_travel.db` via `sqlite3` (or PostgreSQL via SQLAlchemy when `--postgres` is passed) and formats query cursors into aligned ASCII tables. | Gives administrators and QA engineers instant visibility into database tables, row counts, and user records without needing external GUI tools like pgAdmin or DBeaver. |
| **TTL (Time-To-Live) Cache Expiration** | **Layman**: A freshness "best before" timestamp stamped onto cached data. Before the timer runs out, the system reuses the saved answer; after the timer expires, the system fetches a fresh answer.<br>**Technical**: Implemented via `expires_at` (`TIMESTAMPTZ`) in the `geospatial_cache` table (`168h` places, `24h` details, `336h` routes) and `expirationTtl: 86400` (`24h`) in Cloudflare KV `TUNNEL_KV.put()`. | Minimizes external Google Maps/OSRM API latency and cost while ensuring stale venue details and road routes automatically refresh over time. |
