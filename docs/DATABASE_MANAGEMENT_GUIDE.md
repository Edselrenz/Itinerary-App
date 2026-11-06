# Database Management & Operations Guide: Nueva Ecija Travel Itinerary

This guide provides practical, step-by-step instructions for developers, operators, and AI coding agents on how to manage, inspect, migrate, seed, back up, and troubleshoot the database in this project.

---

## Table of Contents
1. [Architecture & Engine Overview](#1-architecture--engine-overview)
2. [Active Engine Selection](#2-active-engine-selection)
3. [Connecting to the Database (GUI & CLI)](#3-connecting-to-the-database-gui--cli)
4. [Schema Migrations (Alembic)](#4-schema-migrations-alembic)
5. [Data Ingestion & Seeding](#5-data-ingestion--seeding)
6. [Backups, Restores & Drills](#6-backups-restores--drills)
7. [Resetting to a Clean Slate](#7-resetting-to-a-clean-slate)
8. [Troubleshooting & Maintenance FAQ](#8-troubleshooting--maintenance-faq)

---

## 1. Architecture & Engine Overview

The backend is built with **SQLAlchemy 2.0** using portable types, enabling the system to run seamlessly on two database engines:

```mermaid
flowchart TD
    App["FastAPI Backend (backend/app)"] --> Engine{"Engine Selection"}
    Engine -- "DATABASE_URL=postgresql+psycopg://..." --> PG[("PostgreSQL 15+ Container\n(ne_postgres on port 5432)")]
    Engine -- "DATABASE_URL=sqlite:///./nueva_ecija_travel.db" --> SQLITE[("SQLite Database File\n(nueva_ecija_travel.db at project root)")]
    PG --> Prod["Production / Pilot / Full Concurrency"]
    SQLITE --> Dev["Zero-Setup Development / CI / Offline Fallback"]
```

### Portable Data Types
- **Primary & Foreign Keys**: `sa.Uuid(as_uuid=True)` maps to native `UUID` in PostgreSQL and `CHAR(32)` in SQLite.
- **JSON Fields**: `JsonType = sa.JSON().with_variant(JSONB(), "postgresql")` provides native binary JSON (`JSONB`) indexing in PostgreSQL and standard `JSON` text in SQLite.

---

## 2. Active Engine Selection

The active engine is determined by the `DATABASE_URL` environment variable defined in `.env` or set at runtime:

### Option A: PostgreSQL (Recommended for Docker / Production)
```ini
DATABASE_URL=postgresql+psycopg://ne_travel_user:change_me_local_only@127.0.0.1:5432/nueva_ecija_travel
```
- **Host**: `127.0.0.1` (or `localhost`)
- **Port**: `5432`
- **Database**: `nueva_ecija_travel`
- **User**: `ne_travel_user`
- **Password**: `change_me_local_only`

### Option B: SQLite (Recommended for Local Dev / Tests)
```ini
DATABASE_URL=sqlite:///./nueva_ecija_travel.db
```
- Stores data in a single local binary file: `nueva_ecija_travel.db` at the **repository root**.

### Automated Runtime Fallback (`start_server.bat` / `scripts/start_server.ps1`)
When launching the backend via `start_server.bat` or `scripts/start_server.ps1`:
1. The script probes TCP port `5432`.
2. If PostgreSQL is reachable, it uses PostgreSQL.
3. If PostgreSQL is unreachable (Docker not running or container stopped), it prints a warning and automatically falls back to:
   ```powershell
   $env:DATABASE_URL = "sqlite:///./nueva_ecija_travel.db"
   ```
   This ensures the application starts without manual intervention.

---

## 3. Connecting to the Database (GUI & CLI)

### 3.1 SQLite Management

The active SQLite database file is located at:
```text
C:\Users\Edward\Desktop\CaseStudy\nueva_ecija_travel.db
```

#### Method 1: VS Code SQLite Viewer Extension (Recommended for quick edits)
1. Install the **SQLite Viewer** or **SQLite3 Editor** extension in VS Code.
2. In the Explorer pane, click directly on `nueva_ecija_travel.db`.
3. Browse tables, filter rows, sort columns, or edit values visually.

#### Method 2: Desktop GUI Tools (DB Browser for SQLite / DBeaver)
- Download and open [DB Browser for SQLite](https://sqlitebrowser.org/) or [DBeaver Community](https://dbeaver.io/).
- Choose **Open Database** and navigate to `CaseStudy\nueva_ecija_travel.db`.
- Execute custom SQL queries, export tables to CSV, or inspect indexes.

#### Method 3: Command Line (Python or sqlite3 CLI)
Run one-line queries directly in PowerShell without installing external tools:
```powershell
# Count places
python -c "import sqlite3; conn = sqlite3.connect('nueva_ecija_travel.db'); c = conn.cursor(); print('Places:', c.execute('SELECT COUNT(*) FROM places').fetchone()[0]); conn.close()"

# List all tables
python -c "import sqlite3; conn = sqlite3.connect('nueva_ecija_travel.db'); c = conn.cursor(); print([r[0] for r in c.execute(\"SELECT name FROM sqlite_master WHERE type='table'\")]); conn.close()"
```

---

### 3.2 PostgreSQL Management

#### Method 1: Docker Interactive Shell (`psql`)
Open a direct PostgreSQL terminal inside the running container:
```powershell
docker exec -it ne_postgres psql -U ne_travel_user -d nueva_ecija_travel
```
Common `psql` shortcuts:
- `\dt` — List all tables
- `\d+ places` — Describe table schema, columns, and indexes
- `\q` — Exit `psql`

#### Method 2: External GUI (DBeaver / pgAdmin)
- **Connection Type**: PostgreSQL
- **Host**: `127.0.0.1` | **Port**: `5432`
- **Database**: `nueva_ecija_travel`
- **Username**: `ne_travel_user`
- **Password**: `change_me_local_only`

---

## 4. Schema Migrations (Alembic)

All structural changes to database tables are version-controlled with **Alembic** under [`backend/alembic/`](file:///c:/Users/Edward/Desktop/CaseStudy/backend/alembic).

### Current Migration History
1. `0001_initial_schema`: Core 7 tables (`users`, `auth_identities`, `municipalities`, `places`, `itineraries`, `itinerary_days`, `itinerary_items`).
2. `0002_google_places_and_routing`: GIS upgrade columns (Google Place ID, ratings, reviews, photos, operating hours, polylines, leg details) and the `geospatial_cache` table.

### Migration Commands
Always run Alembic from inside the `backend/` directory:

```powershell
cd backend
```

#### Check Current Migration Version
```powershell
alembic current
```

#### Upgrade to Latest Schema (`head`)
```powershell
alembic upgrade head
```

#### Roll Back Last Migration
```powershell
alembic downgrade -1
```

#### Roll Back to Clean State
```powershell
alembic downgrade base
```

#### Create a New Migration After Modifying `entities.py`
```powershell
alembic revision --autogenerate -m "add_column_name_to_table"
```
> [!IMPORTANT]
> Always inspect the newly generated migration file in `backend/alembic/versions/` before running `alembic upgrade head`. For SQLite compatibility, ensure `render_as_batch=True` is enabled in `env.py` when dropping or renaming columns.

---

## 5. Data Ingestion & Seeding

### 5.1 Curated Destinations & Municipalities (Idempotent)
Populates 12 core municipalities and 17 curated destinations (including Bongabon Day 1 stops, Pantabangan resorts, and cultural museums).

```powershell
python scripts/seed_featured_places.py
```
- **Behavior**: Idempotent. If records already exist, it updates them in-place and creates zero duplicate rows.

### 5.2 Live OpenStreetMap (OSM) POI Importer
Fetches and imports real-world geographic venues from the live Overpass API bounded strictly to Nueva Ecija coordinates (`15.15 <= lat <= 16.15`, `120.70 <= lng <= 121.40`):

1. **Download Raw OSM Features**:
   ```powershell
   python scripts/fetch_osm_places.py
   ```
   Queries live Overpass endpoints for nodes and ways across cafes, restaurants, hotels, parks, attractions, and essentials, saving ~3,000 raw features to `data/raw/nueva_ecija_osm.json`.

2. **Validate & Upsert into Database**:
   ```powershell
   python scripts/import_osm.py data/raw/nueva_ecija_osm.json
   ```
   Filters out unmapped/out-of-bounds items, matches municipality centroids, and upserts ~2,650 verified real-world places into the `places` table.

```
- **Filters**: Maps raw OSM tags into 16 canonical categories (`cafe`, `restaurant`, `hotel`, `viewpoint`, `park`, `historic`, `museum`, `terminal`, etc.).
- **Honesty Guard**: Venues without verified prices have `estimated_cost_min` and `estimated_cost_max` set to `NULL` to avoid misleading travelers.

---

## 6. Backups, Restores & Drills

The project includes an enterprise-grade backup script in [`scripts/db_backup_restore.py`](file:///c:/Users/Edward/Desktop/CaseStudy/scripts/db_backup_restore.py) compatible with both SQLite and PostgreSQL.

### 6.1 Create a Backup Snapshot
```powershell
python scripts/db_backup_restore.py backup
```
- Automatically creates a timestamped file in `backups/`:
  - `backups/ne_backup_YYYYMMDD_HHMMSS.sqlite` (for SQLite)
  - `backups/ne_backup_YYYYMMDD_HHMMSS.sql` (for PostgreSQL via `pg_dump`)

### 6.2 Restore from a Backup File
```powershell
python scripts/db_backup_restore.py restore backups/ne_backup_20261106_120000.sqlite
```
- **PostgreSQL**: Invokes `psql` with `--clean --if-exists` to cleanly overwrite existing tables.
- **SQLite**: Performs an atomic file replacement.

### 6.3 Run Backup & Restore Verification Drill
Automates a full disaster-recovery drill (takes backup, injects canary data, restores, and validates table counts):
```powershell
python scripts/db_backup_restore.py verify
```

---

## 7. Resetting to a Clean Slate

### If Using SQLite:
1. Delete the SQLite file:
   ```powershell
   Remove-Item -Path "nueva_ecija_travel.db" -Force
   ```
2. Re-run the seed script to create and populate the database:
   ```powershell
   python scripts/seed_featured_places.py
   ```
3. Run Alembic to ensure migration markers match:
   ```powershell
   cd backend; alembic stamp head; cd ..
   ```

### If Using PostgreSQL:
1. Stop and remove the Docker container:
   ```powershell
   docker rm -f ne_postgres
   ```
2. Re-run `start_server.bat` or `scripts/start_server.ps1`.
   The script will automatically:
   - Create a fresh `ne_postgres` Docker container.
   - Run `alembic upgrade head`.
   - Run `seed_featured_places.py`.

---

## 8. Troubleshooting & Maintenance FAQ

### Q1: Why was there a 0-byte `backend/nueva_ecija_travel.db` file?
**Cause**: The connection string `sqlite:///./nueva_ecija_travel.db` uses a relative path (`./`). If a command was executed from inside `backend/`, SQLite created an empty file in `backend/`.  
**Fix**: Always execute application commands from the project root. The orphan file has been deleted, and only the root `nueva_ecija_travel.db` is used.

### Q2: I modified `entities.py`, but the backend says "column does not exist"?
**Cause**: SQLAlchemy does not alter existing database tables automatically on startup.  
**Fix**:
1. Run `cd backend; alembic revision --autogenerate -m "describe_change"`.
2. Review the generated migration file in `backend/alembic/versions/`.
3. Run `alembic upgrade head`.
4. Return to root: `cd ..`.

### Q3: How do I clean expired cache entries in `geospatial_cache`?
The `geospatial_cache` table automatically updates whenever a Google Places or Route calculation occurs. To purge expired cache entries manually:
```powershell
python -c "from backend.app.core.database import SessionLocal; from backend.app.models.entities import GeospatialCache; import datetime; db = SessionLocal(); count = db.query(GeospatialCache).filter(GeospatialCache.expires_at < datetime.datetime.now(datetime.timezone.utc)).delete(); db.commit(); print(f'Purged {count} expired cache records.'); db.close()"
```

### Q4: How do I verify the database integrity without launching the frontend?
Run the foundational pytest suite:
```powershell
python -m pytest backend/tests/test_foundation.py -v
```
This tests database connectivity, municipality filtering, POI category queries, and out-of-province coordinate rejection.

