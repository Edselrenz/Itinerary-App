# Desktop Application Overview: Nueva Ecija Travel ("Trip mo, trip ko")

**Framework**: Python Flet >= 1.1.2 (Flutter Material 3)  
**Python Runtime**: Python 3.14.3 / 3.11+  
**Target Monorepo Location**: `desktop_client/`  
**Shared Backend API**: FastAPI 0.115+ at `http://127.0.0.1:8000/api/v1` (`backend/`)  
**Reference Web App**: Ionic 9 + Angular 22 (`Project/`)  
**Document Ref**: `docs/DESKTOP_APP_OVERVIEW.md`  

---

## 1. Executive Summary

The **Nueva Ecija Travel Desktop Client** is an independent, native desktop application developed using **Python Flet**. It serves as a dedicated desktop workstation companion to the existing **Ionic Angular web application** (`Project/`), sharing the exact same FastAPI backend, PostgreSQL/SQLite database, and deterministic travel planning algorithms without modifying or destabilizing the web client.

### Primary Design Objectives
1. **Desktop Ergonomics**: Deliver an expansive dual-pane planning environment optimized for laptop and multi-monitor desktop displays (1080p to 4K), supporting persistent navigation, keyboard shortcuts, and full-screen map views.
2. **Native Performance**: Leverage Flutter's high-performance graphics rendering engine via Python Flet, providing smooth 60fps animations, reactive theme transitions, and standalone executable distribution without requiring Electron or browser runtimes.
3. **Consumer Travel Character (`@anti-generic-frontend-design`)**: Eliminate generic administrative table patterns in favor of rich consumer travel cards, authentic local photography from Nueva Ecija (`Project/src/assets/`), honest admission cost displays (`₱min - ₱max` or "Free Admission"), and local municipal commute intelligence.
4. **Offline & Guest Resilience**: Fully support offline local planning using bundled canonical data (`CANONICAL_OFFLINE_PLACES`, `osm_places.json`) and local JSON persistence (`guest_storage.json`, `favorites.json`), with automated cloud synchronization upon traveler sign-in.

---

## 2. Web vs. Desktop Feature Mapping

The desktop client mirrors the functional workflows, view hierarchy, and business logic of the Ionic Angular web client:

| Functional Area | Web Client Reference (`Project/src/app/`) | Desktop Client View (`desktop_client/views/`) | Shared Backend API Route | Data Persistence |
| :--- | :--- | :--- | :--- | :--- |
| **Welcome / Splash** | `features/auth/welcome/welcome.page.*` | `welcome_view.py` | N/A (Static Onboarding) | Ephemeral |
| **Guest Onboarding** | `features/auth/guest/guest.page.*` | `guest_view.py` / `welcome_view.py` | N/A | Session State |
| **Traveler Login** | `features/auth/login/login.page.*` | `login_view.py` | `POST /api/v1/auth/login` | Bearer JWT / `session.json` |
| **Traveler Signup** | `features/auth/signup/signup.page.*` | `signup_view.py` | `POST /api/v1/auth/register` | Relational `users` table |
| **Home Dashboard** | `tabs/home/home.page.*` | `dashboard_view.py` | `GET /places?featured=true` | Server Cache / Local Fallback |
| **Place Detail Sheet** | `shared/components/place-detail-sheet/` | `components/dialogs.py` (`show_place_detail_dialog`) | `GET /places/{id}` | In-Memory / Favorites |
| **Map & POI Explorer** | `tabs/map/map.page.*` | `places_view.py` | `GET /places`, `GET /municipalities` | Server / `osm_places.json` |
| **Suggested Wizard** | `features/itinerary/suggested-wizard/` | `suggested_wizard_view.py` | `POST /itineraries/suggest` | PostgreSQL / SQLite |
| **Custom Builder** | `features/itinerary/custom-builder/` | `custom_builder_view.py` | `POST /itineraries`, `PATCH /itineraries/{id}` | Cloud / `guest_storage.json` |
| **Saved Trips** | `tabs/history/history.page.*` | `saved_trips_view.py` | `GET /itineraries/my` | Cloud / `guest_storage.json` |
| **Trip Detail & Edit** | `features/itinerary/itinerary-detail/` | `trip_detail_view.py` | `GET /itineraries/{id}`, `POST /reorder` | Cloud / Local Storage |
| **Traveler Profile** | `tabs/profile/profile.page.*` | `profile_view.py` | `GET /auth/me`, `PATCH /auth/me` | Cloud / `profile_extra.json` |
| **Saved Favorites** | `tabs/favorites/favorites.page.*` | `profile_view.py` (`FavoritesSubView`) | Client-side IndexedDB $\to$ Desktop JSON | `storage/favorites.json` |
| **Multi-Format Export**| `core/utils/itinerary-export.util.ts` | `core/export.py` (`show_export_dialog`) | RFC 5545 iCalendar, Markdown, JSON, HTML | System Clipboard / Local Disk |

---

## 3. Technology Stack & Runtime Dependencies

```
┌────────────────────────────────────────────────────────────────────────┐
│             Desktop Client Application (desktop_client/)               │
│                                                                        │
│   • UI Framework: Python Flet >= 1.1.2 (Material 3 Flutter Engine)     │
│   • Runtime: Python 3.14.3 (Windows x64) / Python 3.11+ (POSIX)        │
│   • HTTP Client: httpx >= 0.28.1 (Asynchronous REST with Connection    │
│     Pooling & Automatic Timeout Management)                            │
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
| **`httpx`** | `>= 0.28.1` | High-performance asynchronous HTTP client communicating with FastAPI endpoints. |
| **`pydantic`** | `>= 2.10.6` | Data validation, contract modeling, and JSON serialization. |
| **`python-dotenv`** | `>= 1.0.1` | Environment variable hydration from `.env` files. |
| **`pytest`** | `>= 9.2.0` | Automated test runner for unit, integration, and UI verification suites. |
| **`pyinstaller`** | `>= 6.11.0` | Production binary compiler generating standalone `NuevaEcijaTravel.exe`. |

---

## 4. Key Architectural Differentiators

1. **Dual-Pane Custom Builder**: While mobile web users must toggle between a catalog tab and a timeline tab, the desktop builder renders a simultaneous **Left Catalog Explorer** and **Right Schedule Timeline**, dramatically accelerating trip creation.
2. **Deterministic Offline Fallback**: If the FastAPI backend is offline (e.g., host laptop disconnected or tunnel closed), the desktop client automatically activates `CANONICAL_OFFLINE_PLACES` and `osm_places.json`, allowing full search, itinerary generation, and custom trip planning without an active server connection.
3. **Loop-Safe Asynchronous Dispatch**: All Flet UI controls execute background coroutines through a unified `run_async()` wrapper in `desktop_client/core/async_utils.py`, preventing `RuntimeError: asyncio.run() cannot be called from a running event loop`.
4. **Honest Provincial Commute Math**: The desktop client integrates the complete Nueva Ecija municipal commute guide (`desktop_client/core/commute_guide.py`), calculating exact driving vs. tricycle travel durations and local fares between consecutive stops.
