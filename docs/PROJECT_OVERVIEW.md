# Project Overview: Nueva Ecija Travel Itinerary (*Trip mo, trip ko*)

**Version**: `1.0.0` (Phase 62 — Production Multi-Platform Release)  
**Platforms**: Web PWA (GitHub Pages) • Android Mobile APK (Capacitor 8) • Windows Native Desktop (Python Flet / Inno Setup & Portable) • FastAPI Cloud/Local Backend  

---

## 1. Executive Summary

The **Nueva Ecija Travel Itinerary Application** (*Trip mo, trip ko*) is a full-stack, multi-platform travel discovery, itinerary generation, and route navigation ecosystem engineered for travelers exploring all **32 Local Government Units (27 municipalities and 5 component cities)** of **Nueva Ecija, Central Luzon, Philippines**.

The system implements the official **Product and Engineering Blueprint** and **Figma UI/UX Specifications** (`Travel Itinerary App.fig`) across four synchronized runtime tiers—**Web PWA**, **Native Android Mobile**, **Native Windows Desktop**, and an **Asynchronous FastAPI + PostgreSQL/SQLite Backend**—using a **100% zero-cost, open-data architecture** that eliminates paid third-party API dependencies (such as paid Google Maps Platform SDKs, paid Places APIs, or paid generative AI endpoints).

---

## 2. Core Objectives & Functional Scope

1. **Province-Wide Discovery (32 LGUs & 2,673 Verified Places)**:
   - Comprehensive geographic coverage across all 32 LGUs of Nueva Ecija (including Cabanatuan City, Gapan City, Science City of Muñoz, Palayan City, San Jose City, Bongabon, Pantabangan, General Tinio, Gabaldon, Laur, Santa Rosa, Talavera, and 20 additional municipalities).
   - Backed by a curated and geofenced database of **2,673 real-world Points of Interest (POIs)** (`15.15 <= lat <= 16.15`, `120.70 <= lng <= 121.40`), combining **17 flagship curated tourist destinations** (with authentic local photography and terminal-to-destination commute guides) and **2,656 verified OpenStreetMap venues** mapped across **16 canonical categories**.
2. **Flexible Traveler Entry & Offline-First Guest Mode**:
   - **Authenticated Cloud Accounts**: Email/password registration and sign-in secured with **Argon2id** password hashing, short-lived **JWT access/refresh token rotation**, and **SlowAPI** rate limiting (30 requests/minute).
   - **First-Class Guest Mode (Zero Demo Accounts)**: Travelers can browse destinations, build or generate itineraries, and navigate routes offline without creating an account. Guest trips persist locally (`ne_guest_itineraries_v1` in IndexedDB on Web/Android; `storage/guest_storage.json` on Windows Desktop) and automatically migrate to the cloud database upon sign-in or registration.
3. **Dual Itinerary Planning Modes**:
   - **Suggested Itinerary Generator (3-Step Wizard)**: A deterministic spatial-scoring recommendation engine that clusters nearby destinations within a **25 km Haversine corridor radius**, orders daily stops using **2-Opt Nearest-Neighbor Traveling Salesperson (TSP)** optimization, anchors midday dining (`12:00 PM – 01:00 PM`), caps high-intensity mountain summits at 1 per day, deduplicates proximate coordinates (<200 m), calculates road polylines via **OSRM** (with geodesic spline fallback), displays verified admission cost summaries and collapsible corridor assumptions, and offers one-click discovery of nearby restaurants, hospitals/pharmacies, and convenience stores.
   - **Custom Itinerary Builder (3-View Editor)**: An interactive multi-day trip builder comprising a travel questionnaire (`View 0`), a searchable 16-category POI browser (`View 1`), and a timeline schedule editor (`View 2`). Supports catalog POIs and geofenced off-grid custom venues, stop reordering with chronological Haversine transit buffer auto-scheduling (`autoOptimizeDaySchedule`), cross-day stop movement, honest min/max cost validation, and multi-format offline export (**iCalendar `.ics`**, **Markdown `.md` dossier**, **JSON `.json`**, and **clipboard summary**).
4. **Interactive Exploration Map & In-App Turn-by-Turn Route Navigation**:
   - **Web & Android Map**: Powered by **Leaflet v1.9.4** and **Leaflet.markercluster** (`disableClusteringAtZoom: 16`) with 16 category-colored 30×30 teardrop pins, an interactive `<app-place-detail-sheet>` bottom sheet, and **Follow-Route Mode** featuring multi-stop road polylines, leg distance/duration badges, and live GPS tracking.
   - **Windows Desktop Slippy Map**: Powered by a custom pure-Python/Flet **`SlippyMapCanvas`** raster tile engine featuring multi-mirror OpenStreetMap tile fetching, automated watermark/hazard tile sanitization, memory + writable disk tile caching (`tiles_cache`), 60 FPS drag-origin linear panning, cursor-centered mouse-wheel zooming (`zoomAround` parity), Z9–Z15 marker clustering, 16 Web-identical teardrop pins, an in-map POI detail bottom sheet, OSRM polyline decoding with floating stop tooltips, and full support for all **10 Web-compatible deep-link query parameters** (`followRoute`, `itineraryId`, `dayNumber`, `placeId`, `destination`, `municipality`, `category`, `priceTier`, `search`, `lat`/`lng`).
5. **Traveler Profile, Favorites, Theme & Localization**:
   - Full in-page Profile suite including **Edit Profile** (with custom avatar photo picker and Base64 persistence), **Favorites** manager with live search and category pills, **Settings** (persistent Light/Dark mode theme toggle, English/Filipino language switch, and local cache management), **Help & Support** (FAQs and Nueva Ecija provincial emergency hotlines), and **About** metadata.

---

## 3. Technology Stack

| Layer | Technology | Version / Specification | Role in System |
| :--- | :--- | :--- | :--- |
| **Web / Hybrid Mobile Client** | Ionic Framework + Angular | Ionic 9 (`^9.0.0`), Angular 22 (`22.2.3`), TypeScript 6.0 | Standalone-component SPA & PWA deployed on GitHub Pages and packaged for mobile. |
| **Native Android Runtime** | Capacitor + Android Gradle | Capacitor 8 (`8.6.0`), Gradle 8.13, AGP 8.13.0, JDK 21 | Native Android WebView bridge with status bar styling, hardware back-button handling, and SW isolation. |
| **Native Desktop Client** | Python + Flet | Python 3.12+ / 3.14, Flet `>= 1.1.2` (Flutter Engine) | Native Windows desktop application (`desktop_client/`) with 1:1 visual and functional parity. |
| **Desktop Packaging & Setup** | PyInstaller + Inno Setup 6 | PyInstaller 6.22.3, Inno Setup 6.7.3 (`ISCC.exe`) | Compiles standalone `NuevaEcijaTravel.exe`, single-file setup wizard `.exe`, and portable `.zip`. |
| **Local Client Persistence** | `@ionic/storage-angular` & JSON | IndexedDB (Web/Android) / `%LOCALAPPDATA%` JSON (Desktop) | Offline-first storage for guest itineraries, favorites, cached map tiles, and UI preferences. |
| **Interactive Mapping & Routing** | Leaflet + Custom `SlippyMapCanvas` + OSRM | Leaflet 1.9.4, MarkerCluster 1.5.3, Public OSRM + Spline Fallback | Provincial raster tile rendering, spatial marker clustering, and road polyline routing. |
| **Edge API Gateway** | Cloudflare Workers + ngrok | Cloudflare Worker (`worker.js`) | HTTPS edge proxy (`ne-itinerary-api.edselrenz0.workers.dev`) with CORS origin validation and health routing. |
| **Backend REST API** | Python + FastAPI + Uvicorn | FastAPI `>= 0.115.0` (`0.136+`), Uvicorn, SlowAPI `>= 0.1.9` | Asynchronous REST backend exposing versioned `/api/v1` endpoints with rate limiting. |
| **Data Validation & Config** | Pydantic v2 | Pydantic `>= 2.8.0` (`2.13+`), `pydantic-settings` | Strict request/response DTO validation, ISO/12-hour time normalization, and `.env` configuration. |
| **ORM & Schema Migrations** | SQLAlchemy 2.0 + Alembic | SQLAlchemy `>= 2.0.30` (`2.0.50`), Alembic `>= 1.13.2` | Engine-agnostic relational models (`JsonType`, `sa.Uuid`) and versioned schema migrations (`0001`–`0003`). |
| **Relational Database** | PostgreSQL 16 / SQLite 3 | Docker `postgres:16-alpine` (`ne_postgres`) & `nueva_ecija_travel.db` | Dual-engine persistence for 7 core entities (`User`, `AuthIdentity`, `Municipality`, `Place`, `Itinerary`, `ItineraryDay`, `ItineraryItem`) + `GeospatialCache`. |
| **Authentication & Security** | Argon2id + PyJWT + Google Auth | `pwdlib[argon2]`, `pyjwt >= 2.9.0`, `google-auth` | Memory-hard password hashing, JWT access/refresh rotation, and OAuth token verification. |
| **Automated QA & Testing** | Vitest + Pytest + Playwright | Vitest 5.0.5, Pytest 8.3+, Playwright 1.64.1 | **488 automated tests** (348 Web unit tests + 119 Desktop regression tests + 21 Backend integration tests). |

---

## 4. Multi-Platform Release Deliverables & Verification Matrix (Phase 62)

All four client and server tiers are verified at **100% test pass rate (488 / 488 tests passing)** and packaged into distributable release artifacts:

| Platform / Tier | Deliverable / Endpoint | Size | Verification / Checksum | Distribution & Usage |
| :--- | :--- | :---: | :--- | :--- |
| **Web Application (PWA)** | [https://edselrenz.github.io/Itinerary-App/](https://edselrenz.github.io/Itinerary-App/) | Static Bundle (<16 kB SCSS budget) | **348 / 348** Vitest unit tests passing (`100%`) | Live production web deployment via GitHub Pages CI/CD. |
| **Windows Desktop (Installer)** | `dist_installer\NuevaEcijaTravel_Setup_v1.0.0.exe` | **156.58 MB** (`164,181,396` B) | SHA-256: `3D08D6BAE3EB3926C0AFEA4FEB211D8BAF2FA9F36D1B0FA241F9EDE50CDFF410` | Standard 64-bit Windows Inno Setup wizard with Desktop/Start Menu shortcuts and uninstaller. |
| **Windows Desktop (Portable)** | `dist_installer\NuevaEcijaTravel_Portable_Installer_v1.0.0.zip` | **232.64 MB** (`243,942,337` B) | SHA-256: `3ED786E2FB9F0EE6E65373C0DBD56C3EF9E8B3C819D6227E36068FE936917708` | Zero-admin portable archive with `Install_And_Launch.bat` for USB drives or restricted PCs. |
| **Windows Desktop (Standalone)** | `dist\NuevaEcijaTravel\NuevaEcijaTravel.exe` | **15.27 MB** (`411.57 MB` bundle) | **119 / 119** Pytest regression tests passing (`100%`) | Unpacked PyInstaller self-contained executable with embedded Python 3.14 & Flet runtime. |
| **Android Mobile (Signed APK)** | `dist_apk\TripMoTripKo-release.apk` | **29.72 MB** (`31,162,864` B) | SHA-256: `0C5CED791D824CD81DF294198481C9F99E9175DC1AA336123B5B1E32BE1E80C6` | Production Android package signed with 2048-bit RSA release keystore. |
| **Android Mobile (Debug APK)** | `dist_apk\TripMoTripKo-debug.apk` | **30.88 MB** (`32,378,996` B) | SHA-256: `C611658A662C68967B8174E1963C69AE74AA6D0945D3B4106AB7701DF03AB4EB` | Debug-signed Android APK for direct USB/sideload testing. |
| **FastAPI Backend & DB** | `http://127.0.0.1:8000/api/v1` & Cloudflare Edge Proxy | 2,673 Places / 12 Curated LGUs | **21 / 21** Backend Pytest + **24 / 24** Acceptance Gate checks (`100%`) | Dual-engine PostgreSQL 16 (`ne_postgres`) & SQLite (`nueva_ecija_travel.db`) with `scripts/db_query.py`. |

---

## 5. Target Users

1. **Day-Trippers & Weekend Travelers**: Seeking curated flagship destinations (e.g., Minalungao National Park, Pantabangan Lake, Lumang Gapan Heritage District, Highland Bali, Farm Villaronte) with verified operating hours, local transit instructions, and honest admission cost ranges.
2. **Multi-Day Vacationers & Families**: Requiring geographically clustered, conflict-free daily schedules (e.g., a 3-day Bongabon–Gabaldon–Pantabangan nature and food corridor) with automatic travel-time buffers and midday lunch anchors.
3. **Offline & Mountain Corridor Explorers**: Travelers visiting low-signal areas in the Sierra Madre foothills (Gabaldon, General Tinio, Carranglan, Pantabangan) who rely on cached map tiles, offline POI catalogs, and local itinerary persistence.
4. **Guest & Privacy-Conscious Planners**: Users who prefer to evaluate the platform and organize complete trips locally on their phone, browser, or Windows PC without mandatory account registration.

---

## 6. Non-Negotiable System Constraints & Architectural Invariants

- **No Paid Maps or Places APIs**: External turn-by-turn navigation hands off to standard Google Maps deep links (`https://www.google.com/maps/dir/?api=1&...`), while in-app road geometry uses public OSRM routing with an automatic local geodesic spline fallback—incurring zero API billing.
- **No Client-Side Nominatim or Live Overpass Abuse**: Client search queries the local PostgreSQL/SQLite and bundled 2,673-POI catalog with a 300 ms debounce. Nominatim and Overpass public servers are never queried on user keystrokes; OSM data is ingested and validated offline via [`scripts/fetch_osm_places.py`](file:///c:/Users/Edward/Desktop/CaseStudy/scripts/fetch_osm_places.py) and [`scripts/import_osm.py`](file:///c:/Users/Edward/Desktop/CaseStudy/scripts/import_osm.py).
- **Honest Cost Presentation**: Venues without verified public pricing store `NULL` cost bounds and render `"Cost not provided"` (with an explicit unpriced-stops footnote in budget summaries) rather than misleading travelers with `₱0.00`.
- **Zero Demo Accounts Policy**: Production and pilot builds never inject fake demo personas or bypass credentials; anonymous usage is served natively through Guest Mode.
- **Read-Only Installation Directory Resilience**: When installed into protected Windows directories (`C:\Program Files\NuevaEcijaTravel`), the desktop client probes write permissions (`.write_probe`) and automatically redirects user storage, avatars, exports, and map tile caches to `%LOCALAPPDATA%\NuevaEcijaTravel\storage`.
- **Repository Binary Hygiene**: Large compiled deliverables (`dist/`, `dist_apk/`, `dist_installer/`, `*.apk`, `*.exe`, `*.zip`) and signing credentials (`*.jks`, `**/keystore.properties`, `.env`) are strictly excluded via [`.gitignore`](file:///c:/Users/Edward/Desktop/CaseStudy/.gitignore) and distributed via release artifacts or local build scripts ([`scripts/build_desktop_installer.ps1`](file:///c:/Users/Edward/Desktop/CaseStudy/scripts/build_desktop_installer.ps1) and [`scripts/build_android_apk.ps1`](file:///c:/Users/Edward/Desktop/CaseStudy/scripts/build_android_apk.ps1)).
- **Gated Social Sign-In in Pilot Builds**: Until paid Apple Developer Program credentials are provisioned, social sign-in buttons display an explicit pilot disclosure toast (*"Apple Sign-In / Google Sign-In is disabled in this pilot build"*).


