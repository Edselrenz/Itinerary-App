# 01. Existing System Analysis & Architectural Assessment

**Target System**: Nueva Ecija Travel Itinerary Planner ("Trip mo, trip ko")  
**Project Role**: Desktop Application Architecture & Integration Analysis  
**Client Framework**: Python Flet (Desktop Client)  
**Existing Web Client**: Ionic 9 / Angular 22 (Preserved Intact in `Project/`)  
**Backend & Persistence**: FastAPI / SQLAlchemy 2.0 / PostgreSQL 16 & SQLite Fallback (`backend/`)  
**Document**: `DESKTOP_APP_DOCUMENTATION/01_EXISTING_SYSTEM_ANALYSIS.md`  

---

## 1. Executive Summary

This document delivers an exhaustive architectural assessment of the existing **Nueva Ecija Travel Itinerary** platform to establish the foundation for an independent, native-feeling desktop application built with **Python Flet**. 

The existing platform is an offline-resilient, hybrid mobile/web travel planner specifically designed for the province of **Nueva Ecija, Central Luzon, Philippines**. The backend is an asynchronous REST API built with FastAPI and SQLAlchemy 2.0, persisting relational data to PostgreSQL (with an automatic SQLite fallback). The web client is built with Ionic 9 and Angular 22.

The Python Flet desktop application will serve as a first-class, dedicated desktop client communicating directly with the existing FastAPI backend via REST API (`http://127.0.0.1:8000/api/v1` or configured `API_BASE_URL`). The desktop application will reuse all existing business logic, authentication mechanics, database models, and recommendation algorithms without requiring code changes to the web client (`Project/`).

---

## 2. Existing System Architecture & Topology

The existing repository is structured as a monorepo maintaining a clean separation of concerns:

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                         Ionic Angular Client (Project/)                          │
│  • Framework: Angular 22.2, Ionic 9.0, Capacitor 8.6, Leaflet 1.9.4              │
│  • Role: Web and hybrid mobile client (Preserved 100% untouched)                 │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │ HTTPS / HTTP REST (JSON)
                                         ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                     Target Desktop Client (desktop_client/)                      │
│  • Framework: Python Flet (Modern Flutter-powered Python UI)                     │
│  • Role: Standalone native desktop application (Windows, macOS, Linux)           │
│  • Communication: Asynchronous REST API client (httpx)                           │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │ HTTP REST (JSON)
                                         ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                            FastAPI Backend (backend/)                            │
│  • Runtime: Python 3.14 / 3.11+, Uvicorn, FastAPI 0.136+, Pydantic v2            │
│  • Security: Argon2id password hashing, PyJWT HS256, SlowAPI rate-limiting        │
│  • Scheduling: Deterministic Haversine clustering, 2-Opt TSP road route pacing   │
│  • Authorization: Broken Object-Level Authorization (BOLA/IDOR) on all mutations │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │ SQLAlchemy 2.0 ORM
                                         ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                     Database Layer (PostgreSQL 16 / SQLite)                      │
│  • Production Database: PostgreSQL 16 (Docker ne_postgres on port 5432)          │
│  • Zero-Config Fallback: nueva_ecija_travel.db (SQLite at project root)          │
│  • Entities: 7 core relational tables + geospatial_cache                         │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Technology Stack Breakdown

| Subsystem | Technology | Version | Purpose in Existing Platform |
| :--- | :--- | :--- | :--- |
| **Web Frontend** | Ionic + Angular | Ionic 9.0.0, Angular 22.2.0 | Hybrid mobile & web SPA; preserved completely intact. |
| **Backend API** | FastAPI | 0.136.0+ | Asynchronous REST backend under `/api/v1`. |
| **Data Validation** | Pydantic | 2.13.0+ | Schema validation, settings management, and pre-validators. |
| **ORM & Database** | SQLAlchemy | 2.0.50 | Relational mapping with dual-engine portable types. |
| **Database Engines**| PostgreSQL / SQLite | PG 16 / SQLite 3 | Relational persistence (`sa.Uuid`, `JsonType`). |
| **Migrations** | Alembic | 1.20.0+ | Reversible migrations (`0001`, `0002`, `0003`). |
| **Authentication** | Argon2id + PyJWT | `pwdlib[argon2]`, `pyjwt` | Modern password hashing & short-lived JWT access/refresh tokens. |
| **Rate Limiting** | SlowAPI | 0.1.9+ | Per-client IP rate limiting on sensitive auth endpoints. |
| **GIS & Routing** | Haversine + 2-Opt | Custom Python engine | Deterministic clustering & travel pacing. |

---

## 4. Relational Database Structure & Entities

The relational database layer consists of 7 primary tables plus 1 cache table:

1. **`users`**:
   - `id` (`UUID`, PK), `first_name`, `last_name`, `username_normalized` (UK), `email_normalized` (UK), `password_hash` (Argon2id), `is_active`, `created_at`, `updated_at`.
2. **`auth_identities`**:
   - `id` (`UUID`, PK), `user_id` (FK $\to$ `users.id`), `provider` (`'google'`, `'apple'`), `provider_subject`, `provider_email`, `created_at`.
3. **`municipalities`**:
   - `id` (`UUID`, PK), `name` (UK), `slug` (UK), `is_city`, `center_lat`, `center_lng`, `boundary_geojson`. Covers all 32 LGUs of Nueva Ecija.
4. **`places`**:
   - `id` (`UUID`, PK), `name`, `category` (16 canonical categories), `latitude`, `longitude`, `municipality_id` (FK), `address_text`, `description`, `phone` (`VARCHAR(255)`), `website`, `opening_hours`, `estimated_cost_min`, `estimated_cost_max`, `cost_currency` (`PHP`), `image_url`, `is_featured`, `is_active`, `tags`, `rating`, `user_rating_count`, `photos`, `google_place_id`.
   - **Catalog Size**: 2,673 verified places (2,656 OSM + 17 curated featured destinations).
5. **`itineraries`**:
   - `id` (`UUID`, PK), `user_id` (FK $\to$ `users.id`), `title`, `destination`, `start_date`, `end_date`, `daily_budget`, `preferences` (`JSON`), `type` (`'suggested'` or `'custom'`), `assumptions` (`JSON`), timestamps.
6. **`itinerary_days`**:
   - `id` (`UUID`, PK), `itinerary_id` (FK $\to$ `itineraries.id`), `day_number`, `travel_date`, `title`, `day_overview_polyline`, `total_distance_meters`, `total_travel_duration_seconds`, `route_legs` (`JSON`).
7. **`itinerary_items`**:
   - `id` (`UUID`, PK), `day_id` (FK $\to$ `itinerary_days.id`), `place_id` (FK $\to$ `places.id`, nullable), `custom_title`, `custom_lat`, `custom_lng`, `sort_order`, `planned_time` (`TIME`), `duration_minutes`, `notes`, `estimated_cost_min`, `estimated_cost_max`, `travel_mode_from_prev`, `travel_distance_meters`, `travel_duration_seconds`, `route_polyline_from_prev`.
8. **`geospatial_cache`**:
   - `cache_key` (PK), `cache_type`, `payload` (`JSON`), `created_at`, `expires_at`.

---

## 5. Authentication Flow & Security Boundaries

1. **Registration (`POST /api/v1/auth/register`)**:
   - Body: `first_name`, `last_name`, `username`, `email`, `password`.
   - Hashes password with Argon2id; normalizes email and username to lowercase.
   - Returns HTTP 201 with `access_token` (30m), `refresh_token` (7d), and `user` object.
2. **Login (`POST /api/v1/auth/login`)**:
   - Body: `email`, `password`.
   - Returns HTTP 200 with new `access_token` and `refresh_token`.
   - Returns HTTP 401 with generic message `"Invalid email or password"` on mismatch.
3. **Session Refresh (`POST /api/v1/auth/refresh`)**:
   - Body: `refresh_token`.
   - Rotates token and returns fresh access token.
4. **Current User (`GET /api/v1/auth/me`)**:
   - Header: `Authorization: Bearer <access_token>`.
   - Returns full `UserOut` profile.
5. **Profile Update (`PATCH /api/v1/auth/me`)**:
   - Header: `Authorization: Bearer <access_token>`.
   - Updates `first_name`, `last_name`, `username`, or password.
6. **Guest & Demo Access**:
   - The platform supports anonymous Guest Mode (storing itineraries locally) and Demo Traveler Mode (Pattranite Limpatiyakorn persona) for instant exploration without registration.
7. **Broken Object-Level Authorization (BOLA / IDOR Defense)**:
   - All itinerary endpoints verify `itinerary.user_id == current_user.id`. Accessing or mutating another user's itinerary immediately returns `404 Not Found` to prevent user reconnaissance.

---

## 6. Available API Endpoints Summary

| Endpoint | Method | Auth Required | Purpose |
| :--- | :---: | :---: | :--- |
| `/api/v1/health` | `GET` | No | System liveness, province scope verification. |
| `/api/v1/auth/register` | `POST` | No | Register new account. |
| `/api/v1/auth/login` | `POST` | No | Authenticate with email/password. |
| `/api/v1/auth/refresh` | `POST` | No | Rotate refresh token for new access token. |
| `/api/v1/auth/me` | `GET` | Yes | Get authenticated user profile. |
| `/api/v1/auth/me` | `PATCH` | Yes | Update user profile / password. |
| `/api/v1/municipalities` | `GET` | No | List 32 LGUs of Nueva Ecija with search. |
| `/api/v1/places` | `GET` | No | Filter & search 2,673 POIs by query, categories, municipality, bbox. |
| `/api/v1/places/{id}` | `GET` | No | Get verified place detail and external directions URL. |
| `/api/v1/itineraries` | `GET` | Yes | List authenticated user's saved itineraries. |
| `/api/v1/itineraries` | `POST` | Yes | Create a multi-day custom or suggested itinerary. |
| `/api/v1/itineraries/{id}` | `GET` | Yes | Retrieve full itinerary with days and scheduled stops. |
| `/api/v1/itineraries/{id}` | `PATCH` | Yes | Synchronize itinerary metadata, days, and items. |
| `/api/v1/itineraries/{id}` | `DELETE` | Yes | Delete itinerary and cascade child records. |
| `/api/v1/itineraries/{id}/days` | `POST` | Yes | Add a new day to an existing itinerary. |
| `/api/v1/itineraries/{id}/days/{day_id}/items` | `POST` | Yes | Add a database POI or off-grid custom venue stop. |
| `/api/v1/itineraries/{id}/days/{day_id}/items/{item_id}` | `PATCH` | Yes | Update planned time, duration, cost, notes of a stop. |
| `/api/v1/itineraries/{id}/days/{day_id}/items/{item_id}` | `DELETE` | Yes | Delete a scheduled stop and re-index sort order. |
| `/api/v1/itineraries/{id}/reorder` | `POST` | Yes | Batch reorder stops within or across days. |
| `/api/v1/itineraries/suggest` | `POST` | Optional | Algorithmic itinerary recommendation engine. |
| `/api/v1/itineraries/compute-day-route` | `POST` | No | Stateless polyline & leg transit calculation. |

---

## 7. Existing Application Modules & User Workflows

1. **Authentication & Onboarding**:
   - Welcome Screen (*"Trip mo, trip ko"* branding), Login, Signup, Dedicated Guest Onboarding, and Demo Account access.
2. **Home Dashboard**:
   - 300ms debounced search over 2,673 POIs, dual entry cards (*Suggested Itinerary* vs. *Custom Itinerary*), Popular Destinations horizontal carousel, and Saved Trips preview.
3. **Interactive Map Exploration**:
   - Leaflet map bounded to Nueva Ecija with 16 category filter pills, marker clustering, bottom sheet venue details, and keyless external Google Maps directions.
4. **Suggested Itinerary Generator**:
   - Multi-step questionnaire (destination autocomplete across 32 LGUs, travel date calendar, budget presets, pacing, and travel preferences).
   - Deterministic clustering generator preventing backtracking, slotting lunch at 12:00 PM, and excluding single-day overnight stays.
   - Preview sheet with day capsules, stop cards, transparent assumptions, verified budget math, and one-tap save.
5. **Custom Itinerary Builder**:
   - Multi-day trip setup, 16-category venue browser, off-grid custom venue modal with coordinate geofencing, timeline view with drag/move reordering, stop editing modal, and zero-stop save prevention.
6. **Saved Itineraries & History**:
   - Categorized saved trip cards, search/filter, detail view with route map, in-place editing, and export (.ics calendar, text summary, print).
7. **Profile & Settings**:
   - User account details, dark mode toggle, default budget settings, favorites collection, and clear cache.

---

## 8. Limitations & Desktop Integration Considerations

1. **No Direct Database Connections from Desktop Client**:
   - In accordance with the system specification, the Python Flet desktop app must **never connect directly to PostgreSQL or expose database credentials**. It must interact exclusively via HTTP REST against FastAPI.
2. **Map Visualization on Desktop**:
   - While the web client uses Leaflet in a browser DOM, desktop Flet provides rich interactive components: custom canvas vector rendering, interactive list/card views, coordinate pins, and launchable external web views / browser maps via standard URLs.
3. **Local Guest Persistence on Desktop**:
   - While the web client uses `@ionic/storage-angular` (IndexedDB), the desktop client will use a lightweight local JSON or SQLite file cache (e.g. `desktop_client/storage/guest_storage.json`) to persist guest itineraries offline with identical schema compatibility.
4. **Desktop Layout Optimization**:
   - Desktop displays offer much higher horizontal resolution (1024px to 1920px+) compared to mobile screens (360px to 412px). The Flet application will use a **persistent responsive sidebar navigation**, multi-column master-detail views, and spacious data tables/grids rather than shrinking a mobile layout.

---

## 9. Recommended Desktop Application Architecture

The desktop application will be structured under `desktop_client/` adhering to modern software engineering principles (separation of concerns, dependency injection, reactive state, and typed models):

```text
desktop_client/
├── main.py                     # Application entrypoint & window configuration
├── requirements.txt            # Desktop dependencies (flet, httpx, pydantic, etc.)
├── README.md                   # Desktop setup & execution instructions
├── .env.example                # Desktop environment template
├── config/                     # Settings & API base URL resolution
├── core/                       # HTTP API client, session manager, local storage
├── models/                     # Strongly-typed data models matching backend schemas
├── services/                   # Business logic services (Auth, Places, Itinerary)
├── components/                 # Reusable UI controls (Sidebar, Header, Dialogs, Cards)
├── views/                      # Application views (Welcome, Login, Home, Map, Builders, Trips, Profile)
└── tests/                      # Automated unit and integration tests (pytest)
```
