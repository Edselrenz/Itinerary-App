# Development Changelog: Nueva Ecija Travel Desktop Client

**Repository:** `CaseStudy`  
**Git Branch:** `feature/flet-desktop-app`  
**Document Ref:** `DESKTOP_APP_DOCUMENTATION/10_DEVELOPMENT_CHANGELOG.md`

---

## [1.0.0] - 2026-11-12

### Initial Standalone Desktop Release (Python Flet)

#### 🚀 Added
- **Project Scaffolding (`desktop_client/`)**:
  - Standalone desktop client directory completely isolated from existing Ionic Angular web client (`Project/`).
  - Strict preservation of all web client assets and codebase.
  - Python configuration with `.env.example`, `.gitignore`, `requirements.txt`, and `README.md`.

- **Core Infrastructure Layer (`desktop_client/core/`)**:
  - `api_client.py`: Async HTTP client powered by `httpx.AsyncClient` with connection pooling, Bearer token header injection, automatic 401 token refresh retry, and typed error hierarchy (`AuthenticationError`, `NotFoundError`, `ValidationError`, `NetworkError`).
  - `session.py`: Persistent session and credential manager with JSON file storage (`storage/session.json`) and pub-sub listener notifications.
  - `storage.py`: Local guest storage manager (`storage/guest_storage.json`) directly mirroring web client `ne_guest_itineraries_v1`.
  - `export.py`: Multi-format itinerary exporter supporting RFC 5545 iCalendar (`.ics`), Markdown travel dossiers (`.md`), and formatted JSON (`.json`).

- **Domain Models Layer (`desktop_client/models/`)**:
  - `user.py`: `User`, `AuthTokenResponse`, `UserUpdatePayload`.
  - `place.py`: `Place` (with honest pricing formatter `formatted_cost`), `Municipality`, `PaginatedPlaces`, `PlaceCategory`.
  - `itinerary.py`: `Itinerary`, `ItineraryDay`, `ItineraryItem`, `SuggestedItineraryRequest`, `ItineraryCreatePayload`.

- **Services Layer (`desktop_client/services/`)**:
  - `auth_service.py`: Login, registration, token refresh, profile updates, and guest mode transitions.
  - `place_service.py`: POI catalog queries with 16-category and 32-municipality filters, search debouncing, and caching.
  - `itinerary_service.py`: Algorithmic multi-day suggested itinerary generation, custom draft creation, stop addition, in-place reordering, and cloud/local synchronization.

- **Component Library (`desktop_client/components/`)**:
  - `sidebar.py`: Persistent left-hand desktop navigation drawer with active pill highlighting, session status badge, and theme switch.
  - `header.py`: Context breadcrumb bar with real-time backend connection status indicator pill.
  - `place_card.py`: Destination card with honest pricing badges, category chips, rating stars, and one-click add to day.
  - `stop_card.py`: Chronological timeline stop item with sequence badge, planned time, duration, move up/down reorder buttons, notes editing, and turn-by-turn route metrics.
  - `dialogs.py`: Place details modal with external Google Maps launch, off-grid custom venue dialog, edit stop dialog, export modal, and destructive action confirmations.

- **Desktop Views (`desktop_client/views/`)**:
  - `welcome_view.py`: Onboarding hero introducing Nueva Ecija travel with "Start Planning as Guest".
  - `login_view.py`: Secure traveler sign-in with email, password, "Remember Me", and guest fallback.
  - `signup_view.py`: Account creation form with password confirmation and client-side validation.
  - `dashboard_view.py`: Metric hub displaying 2,673 POIs, 32 LGUs, saved trip counts, AI Wizard card, Custom Builder card, and featured carousel.
  - `places_view.py`: Full destination catalog explorer with 16 category filter chips, 32 LGU municipality dropdown, sorting options, and pagination.
  - `suggested_wizard_view.py`: 4-step wizard with greedy geographical clustering, loading progress scrim, day switcher, and cost breakdown.
  - `custom_builder_view.py`: Dual-pane desktop layout with catalog search on left, chronological timeline on right, off-grid venue creation, and zero-stop validation guard.
  - `saved_trips_view.py`: Saved itineraries catalog with cloud vs. guest filtering, trip metrics, and export actions.
  - `trip_detail_view.py`: Read-only timeline inspector with route statistics and export options.
  - `profile_view.py`: Traveler settings, display name editing, theme toggle, and local guest cache clearing.

- **Desktop Shell Entrypoint (`desktop_client/main.py`)**:
  - Desktop window configuration (min 1024x720, default 1280x820).
  - Background async healthcheck task monitoring backend connectivity every 15 seconds.
  - Reactive shell switching between full-screen auth and persistent sidebar workspace.

- **Automated Test Suite (`desktop_client/tests/`)**:
  - 19 automated test cases covering API client, authentication, place models, honest pricing, itinerary scheduling, storage CRUD, export formatting, and live backend integration.
  - 100% test pass rate with zero regression.

- **Documentation Deliverables (`DESKTOP_APP_DOCUMENTATION/`)**:
  - `01_EXISTING_SYSTEM_ANALYSIS.md`: Architectural baseline, entities, and integration boundaries.
  - `02_FEATURE_MAPPING.md`: Complete 31-feature comparison matrix between web client and desktop client.
  - `03_QA_QC_REPORT.md`: Comprehensive quality assurance and test execution report.
  - `04_DESKTOP_ARCHITECTURE.md`: High-level desktop architecture, shell pattern, and state management.
  - `05_API_INTEGRATION.md`: REST API catalog, endpoints, payloads, and error mapping.
  - `06_AUTHENTICATION_AND_SECURITY.md`: Security threat model, JWT lifecycle, and BOLA protection.
  - `07_INSTALLATION_GUIDE.md`: Step-by-step setup, prerequisites, and runtime instructions.
  - `08_BUILD_AND_DISTRIBUTION.md`: PyInstaller and Flet native binary packaging guides.
  - `09_KNOWN_LIMITATIONS.md`: Known constraints, OAuth desktop handling, and future roadmap.
  - `10_DEVELOPMENT_CHANGELOG.md`: Chronological milestone and release log.
