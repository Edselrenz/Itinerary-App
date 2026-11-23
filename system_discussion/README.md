# Trip Mo, Trip Ko — Nueva Ecija Travel Itinerary System Documentation (`v1.0.0`)

Welcome to the primary technical and layman-friendly documentation suite for **Trip Mo, Trip Ko (Nueva Ecija Travel Itinerary App)** (`https://github.com/Edselrenz/Itinerary-App`).

This documentation was produced through a complete source-code audit of the repository (`backend/`, `Project/`, `desktop_client/`, `cloudflare-worker/`, `scripts/`, `installer/`, and `.github/workflows/`) and updated through **Phase 62 (`v1.0.0` Final Release Verification)**. Every architecture diagram, API contract, database column, file path, command, release checksum, and security finding reflects the **actual verified implementation**.

> [!TIP]
> **Dual Technical & Layman Format**: Every document in this folder pairs exact engineering specifications with a dedicated **"Technical Terms & Concepts Explained (How It Works & What It Is Used For in This System)"** section so both software engineers and non-technical readers can understand how every component operates and why it exists in **Trip Mo, Trip Ko**.

---

## Quick System Snapshot (`v1.0.0`)

| Attribute | Verified Implementation |
|---|---|
| **Application Name** | Trip Mo, Trip Ko — Nueva Ecija Travel Itinerary Planner (`v1.0.0`) |
| **Geographic Scope** | Nueva Ecija Province, Philippines (32 LGUs, 2,673 bundled OSM POIs + 18 curated featured venues across 16 canonical categories) |
| **Web / PWA / Mobile Client** | Ionic Angular 9 + Angular 22.2.3 (zoneless standalone) + Capacitor 8.6.0 (Android APK) + Leaflet 1.9.4 (`Project/`) |
| **Desktop Client** | Python Flet 1.1.2+ + `flet-map` + custom `SlippyMapCanvas` + `httpx` + PyInstaller + Inno Setup 6 (`desktop_client/`) |
| **Backend API** | FastAPI 0.115+ + Uvicorn (ASGI) + SQLAlchemy 2.0 + Alembic + SlowAPI (`backend/`) |
| **Database** | PostgreSQL 16 (primary, Docker Compose) with automatic 2-second local SQLite 3 fallback (`nueva_ecija_travel.db`) |
| **Edge Proxy & Tunneling** | Cloudflare Worker (`cloudflare-worker/worker.js`) + KV (`TUNNEL_KV`) routing to Cloudflare Quick Tunnel & `ngrok` |
| **External Services** | Google Places API (New), Google Routes API v2, OpenStreetMap Overpass API, OSRM Public Router, OSM Tile Server |
| **Authentication** | Email/Username + Argon2id (`pwdlib`) + HS256 JWT (30-min access / 7-day refresh) + Guest Mode with seamless cloud migration |
| **Automated QA Gate** | **488 automated tests passing (100%)**: 348 Web Vitest unit tests + 119 Desktop Pytest tests + 21 Backend Pytest tests + 24-point MVP acceptance gate |

---

## Documentation Index

### Core Architecture & Codebase
1. **[01 — System Overview](./01-System-Overview.md)** — Purpose, problems solved, objectives, technology stack, target users, roles, verified scope/limitations, and core system terminology.
2. **[02 — System Architecture](./02-System-Architecture.md)** — High-level topology, component layers, communication lifecycle, edge tunneling (`cloudflared` & `ngrok`), auth, database, and deployment architecture.
3. **[03 — Project Structure](./03-Project-Structure.md)** — Complete annotated repository tree (including `scripts/db_query.py`, build pipelines, and 488-test layout) and navigation map for developers.

### Application Subsystems
4. **[04 — Frontend Documentation](./04-Frontend-Documentation.md)** — Ionic Angular web/mobile client (`Project/`) and Flet desktop client (`desktop_client/`) architecture, full-screen `SplashOverlay`, boxless `WelcomeView` with mirrored cityscape `welcome_hero_buildings_wide.png`, `%LOCALAPPDATA%` `.write_probe` fallback, pages/screens, and workflows.
5. **[05 — Backend Documentation](./05-Backend-Documentation.md)** — FastAPI entry point, middleware stack, proxy-aware SlowAPI rate limiting, services, routing lifecycle, and external API integrations.
6. **[06 — API Reference](./06-API-Reference.md)** — Complete REST API specification for all 27 backend endpoints plus Cloudflare Worker edge routes, with verified payloads and HTTP status codes.
7. **[07 — Database Documentation](./07-Database-Documentation.md)** — Full 8-table, 109-column schema, Entity-Relationship Diagram (ERD), Alembic migrations (`0001`–`0004`), indexes, ORM operations, and `scripts/db_query.py` CLI usage.
8. **[08 — Business Logic](./08-Business-Logic.md)** — Deep dive into the deterministic itinerary generator (Haversine clustering, Bayesian quality scoring, opening-hours gate, 2-Opt TSP), routing fallbacks, geodesic splines, offline sync, and guest migration.

### Security, Operations & Lifecycle
9. **[09 — Authentication and Security](./09-Authentication-and-Security.md)** — Argon2id password hashing, HS256 JWT lifecycle, BOLA enforcement, rate limiting, CORS, Android Keystore storage, and confirmed security assessment.
10. **[10 — Installation and Setup](./10-Installation-and-Setup.md)** — End-to-end local environment setup for Backend, PostgreSQL/SQLite, Web/PWA, Android (JDK 21 / Gradle 8.13), Desktop, and Cloudflare Worker.
11. **[11 — System Administration](./11-System-Administration.md)** — Service startup/shutdown, dual-tunnel management, database querying (`scripts/db_query.py`), backups/restores (`scripts/db_backup_restore.py`), and OSM catalog refresh.
12. **[12 — Troubleshooting](./12-Troubleshooting.md)** — Structured diagnostic table covering frontend, desktop (including PyInstaller `icons.json` hot-swap protection and `%LOCALAPPDATA%` permissions), backend, database, tunnels, CORS, and build failures.
13. **[13 — Testing and QA](./13-Testing-and-QA.md)** — Verified inventory of all **488 automated tests** (21 Backend Pytest, 348 Web Vitest across 32 specs, 119 Desktop Pytest across 10 modules including `TC-35`–`TC-40`), Playwright E2E, and 24-point acceptance gate.
14. **[14 — Deployment Guide](./14-Deployment-Guide.md)** — GitHub Pages CI/CD, GitHub Releases, verified Phase 62 deliverable sizes & SHA-256 checksums (`Setup.exe`, Portable `.zip`, Release & Debug `.apk`), Docker Compose production stack, and Cloudflare Worker deployment.
15. **[15 — Developer Guide](./15-Developer-Guide.md)** — Codebase navigation matrix, coding conventions, and end-to-end feature addition walkthrough.
16. **[16 — Technical Debt and Roadmap](./16-Technical-Debt-and-Roadmap.md)** — Prioritized (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`) architectural and code-level remediation roadmap and resolved Phase 61–62 milestones.
17. **[17 — ERD Explanation and Discussion](./17-ERD-Explanation-and-Discussion.md)** — Deep-dive technical and layman-friendly guide to the 8-table, 109-column Entity-Relationship Diagram (Crow's Foot notation, entity-by-entity rationale, all 6 `CASCADE` vs. `SET NULL` relationships, and real-world data walkthroughs).

---

## Visual Architecture & Workflow Diagrams Included Across Chapters

- **Printable Full-Stack Repository Architecture Diagram (PDF)** → [`Trip_Mo_Trip_Ko_System_Architecture_Diagram.pdf`](./Trip_Mo_Trip_Ko_System_Architecture_Diagram.pdf)
- **Interactive Full-Stack Repository Architecture Diagram (HTML/SVG Canvas)** → [`trip_mo_trip_ko_full_stack_repository_architecture_diagram.html`](./trip_mo_trip_ko_full_stack_repository_architecture_diagram.html)
- **Multi-Tier System & Edge Tunnel Topology** → [02 — System Architecture (§1)](./02-System-Architecture.md)
- **End-to-End Request & Failover Sequence** → [02 — System Architecture (§2.4)](./02-System-Architecture.md)
- **UI Navigation & Auth-to-Trip User Flow** → [04 — Frontend Documentation (§4)](./04-Frontend-Documentation.md)
- **Complete 8-Table, 109-Column Database ERD** → [07 — Database Documentation (§3)](./07-Database-Documentation.md)
- **Deterministic Itinerary Generator & 4-Tier Routing Pipeline** → [08 — Business Logic (§1–§2)](./08-Business-Logic.md)
- **JWT Refresh Queue & Guest-to-Cloud Migration Flow** → [09 — Authentication and Security (§1)](./09-Authentication-and-Security.md)

---

## Technical Terms & Concepts Explained (How It Works & What It Is Used For in This System)

| Technical Term | How It Works (Technical & Layman Explanation) | What It Is Used For in This System |
|---|---|---|
| **Full-Stack Multi-Client Application** | **Layman**: Imagine a restaurant with one central kitchen (the backend and database) that serves orders to three different dining rooms: a website, a smartphone app, and a Windows computer program.<br>**Technical**: A software architecture separating presentation clients (Web/PWA, Android APK, Windows Desktop GUI) from a shared stateless REST API and relational database layer. | Enables travelers to plan Nueva Ecija trips from any browser (`Project/`), an Android phone (`TripMoTripKo-release.apk`), or a Windows PC (`NuevaEcijaTravel.exe`) while sharing the exact same cloud account, saved itineraries, and 2,673-POI catalog. |
| **Progressive Web App (PWA)** | **Layman**: A website that can save itself onto your phone or laptop so it opens and works like an installed app, even when your internet signal drops.<br>**Technical**: A web application enhanced with a Web App Manifest and a browser background script called a **Service Worker** (`ngsw-worker.js`) that intercepts network requests and caches HTML, JS, CSS, API responses, and map tiles locally. | Powers the GitHub Pages web deployment (`https://edselrenz.github.io/Itinerary-App/`) so travelers in rural Nueva Ecija towns can still browse cached destinations and map tiles offline. |
| **Capacitor (Native Mobile Bridge)** | **Layman**: A protective native shell that wraps a web application inside an Android `.apk` installer and gives it direct access to the phone's GPS chip, hardware Back button, and encrypted security vault.<br>**Technical**: A cross-platform native runtime (`@capacitor/core`, `@capacitor/android` v8.6.0) that hosts the compiled Angular `www/` bundle inside an Android `WebView` and bridges JavaScript calls to native Java/Kotlin APIs via Capacitor plugins. | Compiles the Ionic Angular codebase into `TripMoTripKo-release.apk` (`29.72 MB`) and `TripMoTripKo-debug.apk` (`30.88 MB`), providing live GPS route tracking (`@capacitor/geolocation`) and Android Keystore token encryption (`capacitor-secure-storage-plugin`). |
| **Python Flet (Flutter Desktop Engine)** | **Layman**: A toolkit that lets developers write desktop software in Python while drawing smooth, modern graphics on the screen using Google's Flutter engine.<br>**Technical**: A UI framework (`flet>=1.1.2`) where a Python process constructs a declarative control tree and communicates over an internal socket/pipe with a bundled native `flet.exe` Flutter desktop binary. | Powers the native Windows desktop client (`desktop_client/`), including the custom interactive slippy map (`SlippyMapCanvas`), boxless welcome/auth screens, and itinerary builders packaged into `NuevaEcijaTravel_Setup_v1.0.0.exe`. |
| **REST API & FastAPI** | **Layman**: A standardized menu of URLs that the apps use to ask the server for data (like searching for cafes) or send updates (like saving a trip), formatted as structured text called JSON.<br>**Technical**: **Representational State Transfer (REST)** over HTTP using standard verbs (`GET`, `POST`, `PATCH`, `DELETE`). **FastAPI** is a high-performance Python 3.12 ASGI web framework that uses **Pydantic v2** type annotations to automatically validate JSON payloads. | Exposes all 27 `/api/v1/*` endpoints in `backend/app/main.py` for user authentication, POI discovery, deterministic itinerary generation, BOLA-protected trip CRUD, and route computation. |
| **Tunneling (`cloudflared` & `ngrok`)** | **Layman**: Normally, a laptop sitting behind home Wi-Fi cannot accept incoming connections from the public internet. Tunneling opens a secure outbound "secret tunnel" from the laptop to a public cloud server, giving the laptop a public `https://` web address.<br>**Technical**: An outbound persistent encrypted connection (HTTP/2, QUIC, or TLS) established by a daemon (`cloudflared` or `ngrok`) from a private NAT host (`127.0.0.1:8000`) to a public edge POP, which reverse-proxies public HTTPS requests back down the outbound socket. | Allows the FastAPI backend running on a local Windows host machine (`start_server.bat`) to serve live HTTPS requests from GitHub Pages, Android phones, and remote desktop clients without requiring a dedicated cloud VPS or router port-forwarding. |
| **Cloudflare Worker & Cloudflare KV** | **Layman**: Because free tunnels change their random web address every time the host laptop restarts, the Cloudflare Worker acts as a permanent receptionist at a fixed address (`workers.dev`) that always knows the laptop's newest tunnel link stored in its digital sticky-note pad (**Cloudflare KV**).<br>**Technical**: A serverless JavaScript execution environment (`cloudflare-worker/worker.js`) running on Cloudflare's global edge network, bound to an eventually consistent key-value store (`TUNNEL_KV`) that holds `ACTIVE_TUNNELS` (`cfUrl`, `ngrokUrl`) and 24-hour cached JSON responses (`EDGE_CACHE_*`). | Provides a permanent HTTPS API gateway (`https://ne-itinerary-api.edselrenz0.workers.dev/api/v1`), automatically fails over from Cloudflare Quick Tunnel to `ngrok` if one drops, and serves 24-hour cached destination/route data (`X-Edge-Cache: HIT`) when the host machine is completely powered off. |
| **Relational Database (`PostgreSQL 16` & `SQLite 3`)** | **Layman**: A digital filing cabinet organized into linked spreadsheets (tables with strict columns and rows) that stores user accounts, 2,673 tourist spots, and saved day-by-day trips.<br>**Technical**: An ACID-compliant **Relational Database Management System (RDBMS)** queried via **SQLAlchemy 2.0 ORM**. PostgreSQL 16 is the primary client-server engine (running in Docker on port `5432`), while SQLite 3 is a serverless single-file relational database (`nueva_ecija_travel.db`). | Persists all 8 system tables (`users`, `auth_identities`, `municipalities`, `places`, `itineraries`, `itinerary_days`, `itinerary_items`, `geospatial_cache`). On startup, `backend/app/core/database.py` probes PostgreSQL with a 2-second timeout and automatically switches to SQLite if Docker is offline. |
| **OpenStreetMap (OSM), Overpass API & OSRM** | **Layman**: The "Wikipedia of Maps" — a free, community-built world map. **Overpass** is its search engine for finding places (like all waterfalls or cafes in Nueva Ecija), and **OSRM** is its free driving-directions calculator.<br>**Technical**: **OSM** stores geospatial nodes/ways with key-value tags; **Overpass API** executes spatial Overpass QL queries; **Open Source Routing Machine (OSRM)** computes shortest-path road routes and precision-5 encoded polylines over OSM road graphs. | Supplies the 2,673 bundled Nueva Ecija POIs (`osm_places.json`), live map viewport discovery (`OsmOverpassService`), slippy map raster tiles (`tile.openstreetmap.org`), and free turn-by-turn road routing (`router.project-osrm.org`) when `GOOGLE_MAPS_API_KEY` is not configured. |

---

## Implementation Verification Legend

Throughout this documentation, implementation status is explicitly distinguished using five labels:
- **Implemented & Verified**: Present in repository source code, tested, and traced end-to-end.
- **Partially Implemented**: Backend or UI exists, but end-to-end integration is incomplete (e.g., Google OAuth backend exists while frontend buttons are disabled in the pilot build; Forgot Password modal is UI-simulated).
- **Referenced / Optional**: Supported via optional configuration (e.g., `GOOGLE_MAPS_API_KEY` live discovery/routing).
- **Planned / Disabled**: Explicitly gated off in code (e.g., Apple Sign-In returning HTTP `501`).
- **Missing / Undocumented**: Not present in the repository (e.g., RBAC/admin roles, automated email delivery, centralized log aggregation).
