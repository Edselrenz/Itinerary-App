# Chapter 3: The Database & Its Components — PostgreSQL, SQLite, ORM, Tables, Keys, Indexes, and Local Storage

This chapter provides a complete, ground-up explanation of **how data is stored, organized, connected, and protected** inside the **Nueva Ecija Travel Itinerary (*Trip mo, trip ko*)** system. Every database concept—from **RDBMS**, **Docker Containers**, **PostgreSQL**, **SQLite**, **ORM (SQLAlchemy)**, and **Alembic Migrations** down to **Primary Keys (`UUID`)**, **Foreign Keys**, **`ON DELETE CASCADE`**, **Indexes**, **`JSONB`**, and **IndexedDB**—is explained in both technical precision and everyday layman's language.

---

## 1. Fundamental Database Concepts (Technical + Layman's Guide)

Before looking at our specific tables, let's demystify the core building blocks of a database:

### 1. **What Is an RDBMS (Relational Database Management System)?**
- **Technical**: Software that stores data in structured **tables** (relations) composed of **rows** (tuples/records) and **columns** (attributes with strict data types like `VARCHAR(255)`, `FLOAT`, `INTEGER`, `BOOLEAN`, `TIMESTAMP`), and links related records across different tables using **Keys**.
- **In Plain English (Layman's Analogy)**: Imagine a zwykły Excel spreadsheet, except instead of stuffing everything into one giant, messy sheet, you split your data into neat, separate tabs (**Tables**): one tab for *Users*, one tab for *Tourist Places*, and one tab for *Saved Trips*. An **RDBMS** is like a super-powered spreadsheet manager that enforces strict rules (so no one accidentally types a word into a price column) and connects the tabs together automatically.

### 2. **What Is a Primary Key (`PK`) & What Is a `UUID`?**
- **Technical**: A **Primary Key** is a column whose value uniquely identifies every single row in a table (it can never be duplicated or `NULL`). Instead of sequential integers (`1, 2, 3...`), our database uses **`UUID` (Universally Unique Identifier — v4)**, a 128-bit random alphanumeric ID such as `550e8400-e29b-41d4-a716-446655440000`.
- **In Plain English (Layman's Analogy)**: A **Primary Key** is like a **National ID Number or Passport Number**. Even if two travelers are both named *"Juan Dela Cruz"*, their Passport Numbers (`UUID`s) are completely different. Why do we use long random **`UUID`s** instead of `1, 2, 3`?
  1. **Security**: If user IDs were `1, 2, 3`, a hacker with ID `4` could easily guess that ID `5` is another person's trip. Nobody can guess a 36-character random `UUID`!
  2. **Offline Creation**: When your phone or laptop is offline in the mountains, it can generate a random `UUID` for a new trip locally without worrying that another phone will accidentally pick the same number!

### 3. **What Is a Foreign Key (`FK`) & What Is `ON DELETE CASCADE`?**
- **Technical**: A **Foreign Key** is a column in a child table (e.g., `itinerary_days.itinerary_id`) that references the **Primary Key** (`itineraries.id`) of a parent table, enforcing **Referential Integrity** at the database engine level. **`ON DELETE CASCADE`** is a constraint rule telling the database: *"When a parent row is deleted, automatically delete all child rows pointing to it."*
- **In Plain English (Layman's Analogy)**: A **Foreign Key** is a **Luggage Tag**. Imagine an Itinerary (*"3-Day Bongabon Trip"*) is a **Traveler**, and its 3 daily schedules (*Day 1, Day 2, Day 3*) are **3 Suitcases**. Each suitcase has a Luggage Tag (`itinerary_id`) stamped with the Traveler's ID so the database always knows which days belong to which trip.
  - **`ON DELETE CASCADE`** is the automatic cleanup rule: if you delete the *"3-Day Bongabon Trip"*, the database automatically throws away *Day 1, Day 2, and Day 3* and all the scheduled stops inside them so no "orphan suitcases" are left cluttering the database!

### 4. **What Is a Database Index (`ix_...`)?**
- **Technical**: A **B-Tree data structure** maintained by the database engine on specific columns (such as `places.category`, `places.latitude`, `places.longitude`, `users.email`) that reduces lookup complexity from a full-table scan $O(N)$ to a logarithmic tree traversal $O(\log N)$.
- **In Plain English (Layman's Analogy)**: Imagine trying to find *"Minalungao National Park"* in a 2,673-page textbook without an index—you would have to read every single page from Page 1 to Page 2,673 (**Full Table Scan**). A **Database Index** is like the **Alphabetical Index at the back of the textbook**: the database jumps straight to the exact row in milliseconds!

### 5. **What Is an ACID Transaction?**
- **Technical**: A database guarantee that a group of operations is **Atomic** (all succeed or all roll back), **Consistent** (obeys all schema constraints), **Isolated** (concurrent requests don't corrupt each other), and **Durable** (permanently written to disk once committed).
- **In Plain English (Layman's Analogy)**: Saving a 3-day itinerary requires writing 1 row to `itineraries`, 3 rows to `itinerary_days`, and 12 rows to `itinerary_items`. An **ACID Transaction** is like a **Bank Transfer**: either all 16 rows are saved together 100% intact, or if the power goes out halfway through, the database rewinds everything (**Rollback**) so you never end up with a half-saved, broken trip.

---

## 2. Our Dual-Engine Database Setup: PostgreSQL 16 (Docker) + SQLite Failover

One of the strongest engineering features of this codebase ([`backend/app/core/database.py`](file:///c:/Users/Edward/Desktop/CaseStudy/backend/app/core/database.py)) is its **Dual-Engine Architecture**: it supports enterprise **PostgreSQL 16** in Docker AND local **SQLite** seamlessly using the exact same Python code.

### 1. **Primary Production Engine: PostgreSQL 16 in Docker (`ne_postgres`)**
- **What Is PostgreSQL?**:
  - *Technical*: **PostgreSQL 16** is the world's most advanced open-source client-server relational database, supporting concurrent connection pooling, binary JSON indexing (`JSONB`), and strict data integrity.
  - *Layman's Explanation*: **PostgreSQL** is an industrial-strength bank vault designed to handle hundreds of travelers searching places and saving itineraries at the same time.
- **What Is a Docker Container & Docker Volume?**:
  - *Technical*: In [`scripts/start_server.ps1`](file:///c:/Users/Edward/Desktop/CaseStudy/scripts/start_server.ps1), PostgreSQL runs inside a **Docker Container** named `ne_postgres` (`postgres:16-alpine` on Port `5432`) backed by a persistent **Docker Volume** (`ne_pgdata`).
  - *Layman's Explanation*: Installing and configuring an enterprise database directly on Windows can be messy. A **Docker Container** is a **sealed, pre-packaged shipping container** that already has PostgreSQL 16 installed and configured inside it. The **Docker Volume (`ne_pgdata`)** is a permanent external hard drive plugged into that shipping container so that even if you stop or restart the container, none of your data is ever lost.

### 2. **Automatic Zero-Config Failover Engine: SQLite (`nueva_ecija_travel.db`)**
- **What Is SQLite?**:
  - *Technical*: **SQLite 3** is an embedded, serverless, zero-configuration SQL database engine that stores the entire relational database (all 8 tables and indexes) inside a single cross-platform file on disk: [`nueva_ecija_travel.db`](file:///c:/Users/Edward/Desktop/CaseStudy/nueva_ecija_travel.db).
  - *Layman's Explanation*: If **PostgreSQL in Docker** is a full walk-in bank vault, **SQLite** is a **portable fireproof lockbox file (`nueva_ecija_travel.db`)**. If a developer or panelist runs the project on a laptop that does not have Docker installed, our backend automatically uses `nueva_ecija_travel.db` with zero setup required!

---

## 3. How Python Talks to the Database: SQLAlchemy 2.0 (ORM) & Alembic (Migrations)

### 1. **What Is an ORM (Object-Relational Mapper) — SQLAlchemy 2.0?**
- **Technical**: [`backend/app/models/entities.py`](file:///c:/Users/Edward/Desktop/CaseStudy/backend/app/models/entities.py) defines our database tables as Python classes (`User`, `Place`, `Itinerary`, etc.) using **SQLAlchemy 2.0**. Instead of concatenating raw SQL strings (which can cause **SQL Injection** security vulnerabilities), we write type-safe Python queries like `db.query(Place).filter(Place.category == "nature_park").all()`, and SQLAlchemy compiles them into parameterized SQL statements for either PostgreSQL or SQLite.
- **In Plain English (Layman's Analogy)**: Python speaks "Objects" and Databases speak "SQL". **SQLAlchemy (the ORM)** is a **Bilingual Translator** sitting between FastAPI and the database. Even better, because SQLAlchemy speaks both *PostgreSQL dialect* and *SQLite dialect*, our custom `JsonType` in [`backend/app/core/database.py`](file:///c:/Users/Edward/Desktop/CaseStudy/backend/app/core/database.py#L22-L38) automatically stores arrays (like destination tags or photo lists) as high-speed **`JSONB`** when connected to PostgreSQL, and standard **`JSON`** when connected to SQLite!

### 2. **What Is Alembic (Database Schema Migrations)?**
- **Technical**: **Alembic** ([`backend/alembic/versions/`](file:///c:/Users/Edward/Desktop/CaseStudy/backend/alembic/versions/)) is a database schema migration tool. Each migration script has an `upgrade()` and `downgrade()` function tracking structural evolution:
  - [`0001_initial_schema.py`](file:///c:/Users/Edward/Desktop/CaseStudy/backend/alembic/versions/0001_initial_schema.py): Creates the 7 core relational tables and indexes.
  - [`0002_google_places_and_routing.py`](file:///c:/Users/Edward/Desktop/CaseStudy/backend/alembic/versions/0002_google_places_and_routing.py): Adds GIS upgrade columns (`rating`, `user_rating_count`, `photos`, `day_overview_polyline`, `route_polyline_from_prev`) and the `geospatial_cache` table.
  - [`0003_widen_phone_column.py`](file:///c:/Users/Edward/Desktop/CaseStudy/backend/alembic/versions/0003_widen_phone_column.py): Widens `places.phone` from `VARCHAR(64)` to `VARCHAR(255)` to fit multi-number OpenStreetMap phone strings.
- **In Plain English (Layman's Analogy)**: If you want to add a new room to an empty blueprint, you just redraw the blueprint. But what if people are *already living inside the house* (your database already has 2,673 places and real user accounts)? You can't bulldoze the house! **Alembic Migrations** are step-by-step **Renovation Instructions** (`0001`, `0002`, `0003`) that safely add new columns and tables to a live database without losing a single existing record.

---

## 4. Visual Map & Tour of All 8 Database Tables

Here is how the 8 tables in [`backend/app/models/entities.py`](file:///c:/Users/Edward/Desktop/CaseStudy/backend/app/models/entities.py) connect to one another:

```
┌──────────────────────┐       1 : Many       ┌─────────────────────────┐
│        users         │◄─────────────────────│     auth_identities     │
│ ──────────────────── │  (ON DELETE CASCADE) │ ─────────────────────── │
│ PK  id (UUID)        │                      │ PK  id (UUID)           │
│     email (Unique)   │                      │ FK  user_id ────────────┘
│     full_name        │                      │     provider ('password'│
│     first_name, ...  │                      │               'google') │
│     avatar_url       │                      │     password_hash       │
└──────────┬───────────┘                      └─────────────────────────┘
           │
           │ 1 : Many (A user can save many itineraries)
           ▼
┌──────────────────────┐       ┌─────────────────────────┐
│     itineraries      │       │     municipalities      │
│ ──────────────────── │       │ ─────────────────────── │
│ PK  id (UUID)        │       │ PK  id (UUID)           │
│ FK  user_id          │       │     name (Unique)       │
│     title            │       │     slug (Unique)       │
│     destination      │       │     center_lat          │
│     start_date       │       │     center_lng          │
│     end_date         │       └────────────┬────────────┘
│     daily_budget     │                    │ 1 : Many (A municipality has many places)
│     type ('suggested'│                    ▼
│           'custom')  │       ┌─────────────────────────┐
│     assumptions(JSON)│       │         places          │
└──────────┬───────────┘       │ ─────────────────────── │
           │                   │ PK  id (UUID)           │
           │ 1 : Many          │ FK  municipality_id     │
           ▼                   │     municipality_name   │
┌──────────────────────┐       │     name, category      │
│    itinerary_days    │       │     latitude, longitude │
│ ──────────────────── │       │     estimated_cost_min  │
│ PK  id (UUID)        │       │     estimated_cost_max  │
│ FK  itinerary_id     │       │     opening_hours       │
│     day_number (1..N)│       │     rating, photos(JSON)│
│     travel_date      │       └────────────┬────────────┘
│     day_overview_    │                    │
│       polyline       │                    │ 1 : Many (Optional link; NULL for off-grid venues)
└──────────┬───────────┘                    │
           │ 1 : Many                       │
           ▼                                ▼
┌────────────────────────────────────────────────────────┐
│                    itinerary_items                     │
│ ────────────────────────────────────────────────────── │
│ PK  id (UUID)                                          │
│ FK  day_id (ON DELETE CASCADE)                         │
│ FK  place_id (ON DELETE SET NULL — supports off-grid!) │
│     custom_title, custom_lat, custom_lng               │
│     sort_order (1, 2, 3...)                            │
│     planned_time ('09:30 AM'), duration_minutes (90)   │
│     estimated_cost_min, estimated_cost_max, notes      │
│     distance_from_prev_meters, route_polyline_from_prev│
└────────────────────────────────────────────────────────┘
```

### Detailed Breakdown of Every Table

| Table Name | Technical Role & Key Columns | Layman's Explanation |
| :--- | :--- | :--- |
| **1. `users`** | Stores registered traveler profiles (`id`, `email`, `full_name`, `first_name`, `middle_initial`, `last_name`, `username`, `birthday`, `gender`, `phone_number`, `avatar_url`, `default_daily_budget`). | The **Member Directory**. Holds each traveler's name, contact info, profile picture, and preferred daily travel budget. |
| **2. `auth_identities`** | Separates login credentials (`user_id`, `provider` [`password` or `google`], `password_hash` [Argon2id], `provider_subject`) from profile data with a unique constraint on `(provider, provider_subject)`. | The **Security Keycard Vault**. Keeping passwords in a separate table from `users` means a traveler can log in with a password today and link a Google account tomorrow—and profile queries never accidentally expose password hashes. |
| **3. `municipalities`** | Stores Nueva Ecija LGUs (`id`, `name`, `slug`, `center_lat`, `center_lng`, `is_active`). | The **Town & City Directory**. Stores the center GPS pin for Nueva Ecija towns and cities (like Cabanatuan, Bongabon, Gapan, Pantabangan) so the map knows where to fly when you pick a town. |
| **4. `places`** | Stores all **2,673 verified destinations** (`id`, `external_osm_id`, `name`, `category`, `municipality_id`, `municipality_name`, `latitude`, `longitude`, `estimated_cost_min`, `estimated_cost_max`, `opening_hours`, `rating`, `user_rating_count`, `photos`, `tags`). | The **Master Tourism Catalog**. Every tourist attraction, nature park, restaurant, cafe, resort, hotel, church, museum, terminal, and hospital in Nueva Ecija lives here, along with its GPS coordinates and verified admission price range. |
| **5. `itineraries`** | Stores the top-level header of a saved trip (`id`, `user_id`, `title`, `destination`, `start_date`, `end_date`, `days_count`, `daily_budget`, `preferences` [JSON], `type` [`suggested` or `custom`], `assumptions` [JSON]). | The **Trip Folder Cover**. Holds the overall summary of a trip (e.g., *"Bongabon 2-Day Getaway, Nov 22–23, ₱3,000/day budget"*). |
| **6. `itinerary_days`** | Stores each individual day within an itinerary (`id`, `itinerary_id`, `day_number` [`1, 2, 3...`], `travel_date`, `title`, `day_overview_polyline`, `total_distance_meters`, `total_duration_seconds`). | The **Daily Schedule Dividers** inside the Trip Folder (*Day 1*, *Day 2*, *Day 3*), including the full blue road route line (`day_overview_polyline`) for that day. |
| **7. `itinerary_items`** | Stores each scheduled stop inside a day (`id`, `day_id`, `place_id` [nullable], `custom_title`, `custom_lat`, `custom_lng`, `sort_order`, `planned_time`, `duration_minutes`, `estimated_cost_min`, `estimated_cost_max`, `notes`, `distance_from_prev_meters`, `duration_from_prev_seconds`, `route_polyline_from_prev`). | The **Individual Stop Cards** on a day's timeline (*Stop 1 at 09:00 AM, Stop 2 at 12:00 PM*). Notice `place_id` is **nullable** (`ON DELETE SET NULL`): if a stop is a catalog place, `place_id` links to `places`; if the user added an **Off-Grid Custom Venue** (like *"Grandma's Farm in Laur"*), `place_id` is `NULL` and `custom_title`, `custom_lat`, and `custom_lng` store the custom spot! |
| **8. `geospatial_cache`** | Key-value TTL cache (`cache_key`, `cache_type`, `payload` [JSON], `expires_at`) storing computed route geometries and external metadata. | The **Shortcut Notepad**. Once the server calculates the road route between two landmarks, it jots the answer down here with an expiration date so it doesn't have to recalculate the same road over and over. |

---

## 5. Client-Side Local Databases (How Offline Guest Storage Works)

When a traveler uses the app in **Guest Mode** (or when offline), where are their itineraries and favorites saved?

### 1. **On Web & Android: IndexedDB (`@ionic/storage-angular`)**
- **Technical**: Web browsers and Android WebViews provide **IndexedDB**, an asynchronous, transactional, object-oriented NoSQL database built directly into the browser engine. Our [`GuestStorageService`](file:///c:/Users/Edward/Desktop/CaseStudy/Project/src/app/core/services/guest-storage.service.ts) stores guest itineraries under the key `ne_guest_itineraries_v1` and UI settings (`ne_theme_mode`, `ne_default_budget`) in `localStorage`.
- **In Plain English (Layman's Analogy)**: **IndexedDB** is a private filing cabinet built directly inside Chrome and your Android phone. Unlike normal web variables that vanish when you close a tab, anything placed in IndexedDB stays safely on your device even if you restart your phone or turn off Wi-Fi.

### 2. **On Windows Desktop: Atomic JSON File Storage (`desktop_client/core/storage.py`)**
- **Technical**: The Windows Desktop client stores offline data as structured UTF-8 JSON files inside `%LOCALAPPDATA%\NuevaEcijaTravel\storage` (or `desktop_client/storage/` in dev mode):
  - `guest_storage.json`: Offline guest itineraries and days.
  - `favorites.json`: Saved favorite places.
  - `ui_prefs.json`: Persistent Dark/Light mode preference.
  - `auth_tokens.json`: Saved JWT session tokens for automatic login on app restart.
  - `tiles_cache/`: Cached `256×256` OpenStreetMap PNG tiles (`{z}_{x}_{y}.png`).
- **In Plain English (Layman's Analogy)**: On a Windows PC, the desktop app maintains its own dedicated folder of neatly organized digital ledger files (`guest_storage.json`, `favorites.json`, `ui_prefs.json`) and a photo album of downloaded map squares (`tiles_cache/`) so your trips, dark mode setting, and visited map areas load in less than a second.

### 3. **Guest-to-Cloud Migration (`GuestMigrationService`)**
- **How It Works**: When a Guest traveler who has created 3 local offline trips decides to register an account or log in, [`GuestMigrationService`](file:///c:/Users/Edward/Desktop/CaseStudy/Project/src/app/core/services/guest-migration.service.ts) (Web/Android) or `AuthService.migrate_guest_trips()` (Desktop) reads every trip from local guest storage, sends them via `POST /api/v1/itineraries` to PostgreSQL/SQLite under the user's new `user_id`, and clears the local guest queue once confirmed!

---

## 6. Operational Database CLI Tools (`scripts/db_query.py` & `scripts/db_backup_restore.py`)

We built two dedicated command-line utilities in `scripts/` so developers and administrators can inspect or back up both SQLite and PostgreSQL without needing heavy third-party GUI tools:
1. **[`scripts/db_query.py`](file:///c:/Users/Edward/Desktop/CaseStudy/scripts/db_query.py)**:
   - Run `python scripts/db_query.py --tables` (SQLite) or `python scripts/db_query.py --postgres --tables` (Docker PostgreSQL) to view live row counts across all tables, or run interactive SQL queries directly in the terminal.
2. **[`scripts/db_backup_restore.py`](file:///c:/Users/Edward/Desktop/CaseStudy/scripts/db_backup_restore.py)**:
   - Run `python scripts/db_backup_restore.py backup` to create timestamped disaster-recovery snapshots in `backups/`, or `python scripts/db_backup_restore.py verify` to execute an automated backup-and-restore verification drill.

---

👉 **Continue to Chapter 4**: [04_ALGORITHMS_ROUTING_AND_MAP_ENGINE.md](file:///c:/Users/Edward/Desktop/CaseStudy/system_discussion/04_ALGORITHMS_ROUTING_AND_MAP_ENGINE.md)
