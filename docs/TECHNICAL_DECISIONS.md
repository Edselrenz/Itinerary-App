# Architectural Decision Records (ADRs)

This document records key technical decisions, their context, alternatives evaluated, and practical consequences.

---

## ADR-001: Zero-Paid-API & Open-Data Compliance

- **Date**: 2026-10-30
- **Context**: The application must run without incurring operational costs from paid mapping, geocoding, or generative AI APIs (such as Google Maps Platform, Mapbox, or OpenAI).
- **Problem**: How to provide rich map visualization, destination search, routing, and itinerary generation without paid services.
- **Options Considered**:
  1. *Use free tiers of Google Maps Platform and OpenAI*: Risky; accidental usage spikes cause billing, and API keys can be scraped from mobile bundles.
  2. *Fully open-source stack (Leaflet, OpenStreetMap, local database search, deterministic scoring)*: Zero external recurring costs, zero key leakage risk.
- **Selected Approach**: Option 2.
  - Map display uses Leaflet with standard OSM raster tiles.
  - Search queries local PostgreSQL/SQLite database with a 300ms debounce.
  - Navigation hands off to standard Google Maps URLs (`https://www.google.com/maps/dir/?api=1&destination=lat,lng`).
  - Itinerary generator uses deterministic Haversine distance clustering and preference scoring.
- **Consequences**:
  - *Advantages*: Zero billing risk, no API keys stored in client code, verifiable data privacy, predictable and repeatable recommendations.
  - *Disadvantages*: Does not include live turn-by-turn navigation or real-time traffic updates inside the mobile shell.

---

## ADR-002: Portable Database Schema (PostgreSQL + SQLite Support)

- **Date**: 2026-10-30
- **Context**: The production specification mandates PostgreSQL with `JSONB` and `UUID` primary keys. However, developers and CI/CD pipelines need to run unit tests and development instances without maintaining a live PostgreSQL server.
- **Problem**: Hardcoding PostgreSQL-specific types (`from sqlalchemy.dialects.postgresql import JSONB, UUID`) causes SQLite test harnesses to crash.
- **Options Considered**:
  1. *Require PostgreSQL for all tests and development*: Fragile on machines without Docker or local Postgres installed.
  2. *Use SQLAlchemy portable types with PostgreSQL dialect variants*:
     - `sa.Uuid(as_uuid=True)`: maps to native `UUID` on Postgres and `CHAR(32)` on SQLite.
     - `JsonType = sa.JSON().with_variant(JSONB(), "postgresql")`: uses `JSONB` on Postgres and standard `JSON` on SQLite.
- **Selected Approach**: Option 2.
- **Consequences**:
  - *Advantages*: 100% of unit tests run instantly in-memory (`sqlite:///:memory:`) in under 5 seconds. Production deployments still benefit from PostgreSQL native `JSONB` indexing.
  - *Disadvantages*: Minor care needed in Alembic migrations to avoid raw Postgres-only operators in cross-database migration paths.

---

## ADR-003: Monorepo Root Alignment & Co-location

- **Date**: 2026-10-30
- **Context**: The workspace root is `CaseStudy/`, and the Ionic Angular frontend was already initialized in `CaseStudy/Project/`. The initial `setup_steps_0_to_2.py` script targeted a nested `./nueva-ecija-travel` folder.
- **Problem**: Running the script as written would isolate the backend and data pipeline from the frontend project and break git tracking.
- **Selected Approach**: Consolidated `BASE_DIR = "."` in `CaseStudy/`, co-locating `backend/`, `Project/`, `scripts/`, and root configuration files (`.env`, `.gitignore`).
- **Consequences**:
  - *Advantages*: Single unified git workspace, shared environment variables, and clear folder hierarchy.

---

## ADR-004: Argon2id Password Hashing & Strict User Normalization

- **Date**: 2026-10-30
- **Context**: User registration requires secure credential handling and protection against duplicate account collision attacks.
- **Problem**: Legacy hashing algorithms (bcrypt/MD5) are less resistant to GPU attacks. Case-variation signups (`User@example.com` vs `user@example.com`) can lead to account enumeration or impersonation.
- **Selected Approach**:
  - Use `pwdlib` configured with `PasswordHash.recommended()` (Argon2id).
  - Normalize all usernames and emails via `.strip().lower()` before querying or storing.
  - Enforce database-level `UNIQUE` constraints on `username_normalized` and `email_normalized`.
  - Use generic error messages on login (`"Invalid email or password"`) to prevent account enumeration.

---

## ADR-005: Guest Mode Local-First Storage Architecture

- **Date**: 2026-10-30
- **Context**: Travelers should be able to create itineraries without creating an account or logging in.
- **Problem**: Storing guest itineraries in the backend database without authentication leads to orphan data pollution, privacy concerns, and storage costs.
- **Selected Approach**:
  - Guest travelers store itineraries directly on their device via `@ionic/storage-angular` (key `ne_guest_itineraries_v1`).
  - Clear banners inform guests that itineraries are device-local and will not sync across devices until they log in or create an account.
- **Consequences**:
  - *Advantages*: Zero backend storage overhead for anonymous users; travelers can use the app completely offline in Guest Mode.

---

## ADR-006: Standalone Component Exports in Ionic 9

- **Date**: 2026-10-30
- **Context**: The project was scaffolded with `@ionic/angular` v9.0.0 and Angular 22.
- **Problem**: Attempting to import standalone components from `@ionic/angular/standalone` caused Angular bundle generation errors because Ionic 9 exports standalone components directly from `@ionic/angular`.
- **Selected Approach**: Updated all component imports across all pages to import directly from `@ionic/angular`.
- **Consequences**:
  - Production build compiles cleanly with zero unresolved imports.

---

## ADR-007: Broken Object Level Authorization (BOLA) Defense on Itinerary Endpoints

- **Date**: 2026-10-31
- **Context**: User itineraries contain private travel plans, notes, dates, and venue stops. Malicious actors could guess or enumerate UUIDs to access, modify, or delete another user's itinerary.
- **Problem**: How to prevent unauthorized access and ID enumeration across all itinerary operations.
- **Selected Approach**:
  - In all database queries for itineraries and child resources (days, stops, reorder operations), the query filter explicitly mandates `where(Itinerary.id == itinerary_id, Itinerary.user_id == current_user.id)`.
  - If no record matches the combined ID and ownership check, the endpoint returns `404 Not Found` rather than `403 Forbidden`.
- **Consequences**:
  - *Advantages*: Complete mitigation of OWASP API Security Top 10 BOLA vulnerabilities. Returning 404 ensures attackers cannot determine whether an itinerary ID exists or belongs to another user.
  - *Disadvantages*: Requires passing `current_user` into every sub-resource query helper.

---

## ADR-008: Dual-Mode Client Persistence (Authenticated API + GuestStorage Fallback)

- **Date**: 2026-10-31
- **Context**: Travelers in Nueva Ecija may experience sporadic mobile data connectivity, switch between Guest Mode and logged-in accounts, or plan offline trips.
- **Problem**: Frontend components shouldn't need duplicate code paths to handle online vs offline or guest vs authenticated states.
- **Selected Approach**:
  - Encapsulate storage switching inside `ItineraryService`.
  - If `AuthService.isAuthenticated()` is true, operations route to `HttpClient` against `/api/v1/itineraries`. If an HTTP error occurs (e.g. backend offline), the service transparently falls back to local `@ionic/storage-angular`.
  - If unauthenticated, operations directly persist to `GuestStorageService`.
  - A unified `BehaviorSubject<Itinerary[]>` broadcasts updates so components (Home tab, Builder, History) update reactively without polling.
- **Consequences**:
  - *Advantages*: Clean separation of concerns; UI pages work identically regardless of authentication or connectivity status.
  - *Disadvantages*: Custom client-side UUID generation required for guest itineraries.

---

## ADR-009: Component Style Budget Optimization (<10kB)

- **Date**: 2026-10-31
- **Context**: Angular CLI enforces a strict production build budget on component stylesheets (`maximumWarning: 10kB`).
- **Problem**: Rich pages (like Custom Builder with modals, day tracks, timelines, and forms) can easily exceed 10kB when nested SCSS generates repetitive selectors.
- **Selected Approach**:
  - Consolidate common form controls (`.field-input, .custom-input, .custom-textarea`).
  - Share layout rules (`.fields-row, .custom-row`) and avoid deeply nested element chains.
  - Rely on CSS variables (`--background`, `--color`) for Ionic components rather than duplicate selector overrides.
- **Consequences**:
  - *Advantages*: Zero build warnings, faster stylesheet parsing, and consistent component aesthetics.


