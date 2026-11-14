# Desktop Application Overview: Nueva Ecija Travel ("Trip mo, trip ko")

**Framework**: Python Flet >= 1.1.2 (Flutter Material 3) + `flet-map`  
**Python Runtime**: Python 3.14.3 / 3.11+  
**Target Monorepo Location**: `desktop_client/`  
**Shared Backend API**: FastAPI 0.115+ at `http://127.0.0.1:8000/api/v1` (`backend/`)  
**Reference Web App**: Ionic 9 + Angular 22 + Leaflet (`Project/`)  
**Document Ref**: `docs/DESKTOP_APP_OVERVIEW.md`  

---

## 1. Executive Summary

The **Nueva Ecija Travel Desktop Client** is an independent, native desktop application developed using **Python Flet**. It serves as a dedicated desktop workstation companion to the existing **Ionic Angular web application** (`Project/`), sharing the exact same FastAPI backend, PostgreSQL/SQLite database, and deterministic travel planning algorithms without modifying or destabilizing the web client.

### Primary Design Objectives
1. **Web App Ergonomic Parity**: Replicate the exact navigation model of the canonical web client: a **4-Tab Bottom Navigation Bar (`.custom-tab-bar`, `60px`)** on core tab views (`Home`, `Map`, `Saved`, `Profile`) and full-screen contextual header bars (`.figma-header-bar`) on workflow views (`/welcome`, `/guest`, `/login`, `/signup`, `/suggested`, `/builder`, `/trips/:id`).
2. **True GIS & Embedded Route Mapping**: Deliver full-screen provincial mapping via `flet-map` (with interactive canvas fallback) on the Map tab (`/map`) and embedded `180px` collapsible day route maps (`ItineraryRouteMap`) inside Suggested Wizard, Custom Builder, and Trip Detail.
3. **Global Connectivity Awareness**: Replicate the Web App's global floating top offline banner (`.offline-host-banner`) across all routes with an active `[Retry]` button (spinner + feedback toast), `[X]` dismiss, and custom API URL configuration in Settings.
4. **3-Tier Proper Offline Resilience**: When the FastAPI server is offline, automatically fall back across 3 tiers: (a) loading 2,673 bundled OpenStreetMap POIs + 12 curated places in `PlaceService`; (b) generating itineraries via the deterministic offline clustering engine in `ItineraryService`; (c) saving authenticated edits to local `guest_storage.json`.
5. **Clean, Honest Authentication (`@anti-generic-frontend-design`)**: Eliminate redundant demo personas (`Pattranite`) and dead social buttons (`Continue with Google`/`Apple`). Provide clean Email/Password Log In, 6-field Sign Up (with auto-suggested `Username` & `M.I.`), `Forgot password?` modal, and dedicated Guest Mode (`/guest`).

---

## 2. Web vs. Desktop Feature Mapping

| Functional Area | Web Client Reference (`Project/src/app/`) | Desktop Client View (`desktop_client/views/`) | Shared Backend API Route | Data Persistence |
| :--- | :--- | :--- | :--- | :--- |
| **App Launch Splash** | `app.component.html` (Splash overlay) | `SplashOverlay` in `main.py` | N/A | Ephemeral (2.8s auto-dismiss) |
| **Welcome / Onboarding** | `features/auth/welcome/welcome.page.*` | `welcome_view.py` | N/A | Ephemeral |
| **Guest Onboarding** | `features/auth/guest/guest.page.*` | `guest_view.py` | N/A | Session State |
| **Traveler Login** | `features/auth/login/login.page.*` | `login_view.py` (with Account Recovery modal) | `POST /api/v1/auth/login` | Bearer JWT / `session.json` |
| **Traveler Signup** | `features/auth/signup/signup.page.*` | `signup_view.py` (6-field structured form) | `POST /api/v1/auth/register` | Relational `users` table |
| **Server Connection Status**| `app.component.html` (`.offline-host-banner`) | `OfflineHostBanner` in `main.py` | `GET /api/v1/health` | Memory / `ConnectivityService` |
| **Home Dashboard** | `tabs/home/home.page.*` | `dashboard_view.py` | `GET /places?featured=true` | Server / Offline OSM Fallback |
| **Place Detail Sheet** | `shared/components/place-detail-sheet/` | `dialogs.py` (`show_place_detail_dialog`) | `GET /places/{id}` | In-Memory / Favorites |
| **Map Tab & POI Explorer**| `tabs/map/map.page.*` | `places_view.py` (`MapView` via `flet-map`) | `GET /places`, `GET /municipalities` | Server / `osm_places.json` |
| **Embedded Day Route Map**| `shared/components/itinerary-route-map/` | `components/itinerary_route_map.py` | OSRM / Geodesic Polylines | In-Memory Route Cache |
| **Suggested Wizard** | `features/itinerary/suggested-wizard/` | `suggested_wizard_view.py` (3-view machine) | `POST /itineraries/suggest` | Cloud / Offline Clustering Engine |
| **Custom Builder** | `features/itinerary/custom-builder/` | `custom_builder_view.py` (3-stage flow) | `POST /itineraries`, `PATCH /itineraries/{id}` | Cloud / `guest_storage.json` |
| **Saved Trips** | `tabs/history/history.page.*` | `saved_trips_view.py` | `GET /itineraries/my` | Cloud / `guest_storage.json` |
| **Trip Detail & Edit** | `features/itinerary/itinerary-detail/` | `trip_detail_view.py` (In-Place Edit Mode) | `GET /itineraries/{id}`, `POST /reorder` | Cloud / Local Storage |
| **Traveler Profile** | `tabs/profile/profile.page.*` | `profile_view.py` (5-row menu card + 5 views)| `GET /auth/me`, `PATCH /auth/me` | Cloud / `profile_extra.json` |
| **Saved Favorites** | `tabs/favorites/favorites.page.*` | `profile_view.py` (`FavoritesSubView`) | Client-side IndexedDB $\to$ Desktop JSON | `storage/favorites.json` |
| **Multi-Format Export**| `core/utils/itinerary-export.util.ts` | `core/export.py` (`show_export_dialog`) | RFC 5545 iCalendar, Markdown, JSON, HTML | System Clipboard / Local Disk |

---

## 3. Technology Stack & Runtime Dependencies

```
┌────────────────────────────────────────────────────────────────────────┐
│             Desktop Client Application (desktop_client/)               │
│                                                                        │
│   • UI Framework: Python Flet >= 1.1.2 (Material 3 Flutter Engine)     │
│   • GIS Engine: flet-map >= 0.1.0 + flet.canvas Web-Mercator Fallback  │
│   • Runtime: Python 3.14.3 (Windows x64) / Python 3.11+ (POSIX)        │
│   • HTTP Client: httpx >= 0.28.1 (Asynchronous REST & Connection Pool) │
│   • Data Validation: Pydantic >= 2.10.6 (Strict Type Serialization)    │
│   • Packaging: PyInstaller 6.11+ (Zero-Dependency Windows Executable)  │
│   • Local Data: File-based JSON Storage with Atomic Disk Writes        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / REST (JSON)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   Shared FastAPI Backend (backend/)                    │
│                                                                        │
│   • Runtime: Python 3.14, FastAPI 0.115+, Uvicorn 0.34+                │
│   • Routing Engine: Deterministic Haversine Clustering & 2-Opt TSP     │
│   • Authentication: Argon2id Password Hashing, HS256 PyJWT Bearer      │
│   • Database: PostgreSQL 16 (Production) / SQLite 3 (Local Fallback)   │
└────────────────────────────────────────────────────────────────────────┘
```

### Desktop Client Dependency Manifest

| Package Name | Minimum Version | System Responsibility |
| :--- | :--- | :--- |
| **`flet`** | `>= 1.1.2` | Core graphical user interface engine, reactive controls, layout system, and windowing. |
| **`flet-desktop`** | `>= 0.28.0` | Desktop window constraints (min width 1080px, min height 720px, icon, title bar). |
| **`flet-map`** | `>= 0.1.0` | True OpenStreetMap tile rendering, vector marker layers, and polyline layers. |
| **`httpx`** | `>= 0.28.1` | High-performance asynchronous HTTP client communicating with FastAPI endpoints. |
| **`pydantic`** | `>= 2.10.6` | Data validation, contract modeling, and JSON serialization. |
| **`python-dotenv`** | `>= 1.0.1` | Environment variable hydration from `.env` files. |
| **`pytest`** | `>= 9.2.0` | Automated test runner for unit, integration, and UI verification suites. |
| **`pyinstaller`** | `>= 6.11.0` | Production binary compiler generating standalone `NuevaEcijaTravel.exe`. |

---

## 4. Key Architectural Differentiators

1. **Exact Web App Navigation Model**: Replaces enterprise sidebars with a sleek **`60px` Bottom Tab Bar** (`Home`, `Map`, `Saved`, `Profile`) on core tab screens, seamlessly hiding on full-screen workflow routes (`/welcome`, `/guest`, `/login`, `/signup`, `/suggested`, `/builder`, `/trips/:id`).
2. **Global Floating Offline Host Banner**: An amber cloud-offline banner overlaid at the top of the window on all screens whenever the backend is unreachable, featuring an active `[Retry]` button with spinner and toast feedback.
3. **Dual-Mode Interactive GIS Mapping**: Full-screen interactive map with category-colored pins, search/filter drawer, and Follow-Route navigation, plus embedded `180px` collapsible route maps inside itineraries.
4. **3-Tier Proper Offline Resilience**: Never displays blank screens or throws unhandled network errors when offline; seamlessly serves 2,673 bundled OSM places, runs local clustering for suggested trips, and caches edits in local JSON storage.
5. **Clean Anti-Generic Authentication**: Pure email/password authentication and guest exploration with zero fake demo personas and zero non-functional social buttons.
