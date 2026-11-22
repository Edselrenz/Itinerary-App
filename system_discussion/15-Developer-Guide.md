# 15 — Developer Contribution and Continued Development Guide

This guide helps incoming engineers navigate the codebase quickly and implement new features consistently across the Backend, Ionic Angular Web/Android client, and Python Flet Desktop client (`v1.0.0`).

---

## 1. Codebase Navigation Matrix

| Task | Where to Look First | Related Files |
|---|---|---|
| **Modify a Web/Android page** | `Project/src/app/app.routes.ts` or `tabs/tabs.routes.ts` | `features/*/*.page.{ts,html,scss,spec.ts}` or `tabs/*/*.page.*` |
| **Modify a Desktop view** | `desktop_client/main.py` (`navigate_to()`) | `desktop_client/views/*.py`, `desktop_client/components/*.py` |
| **Add or change an API endpoint** | `backend/app/api/v1/{auth,places,itineraries}.py` | `backend/app/schemas/*.py`, `backend/app/main.py` |
| **Modify itinerary generation logic** | `backend/app/algorithms/itinerary_generator.py` | `Project/src/app/core/services/itinerary.service.ts` & `desktop_client/services/itinerary_service.py` (offline fallbacks) |
| **Add a database table or column** | `backend/app/models/entities.py` | `backend/alembic/versions/` (`alembic revision --autogenerate`) |
| **Inspect or query database tables** | `scripts/db_query.py` | `backend/app/core/database.py`, `nueva_ecija_travel.db` |
| **Modify authentication or JWT rules** | `backend/app/services/auth_service.py` | `backend/app/api/v1/auth.py`, `auth.interceptor.ts`, `desktop_client/core/api_client.py` |
| **Integrate a new external API** | `backend/app/services/google_maps_service.py` | `backend/app/core/config.py`, `geospatial_cache` table |
| **Update offline POI data or categories** | `scripts/import_osm.py`, `backend/app/api/v1/places.py` (`CANONICAL_CATEGORIES`) | `scripts/export_osm_to_client_asset.py`, `osm_places.json` (Web + Desktop), `place.service.ts` |
| **Debug offline/tunnel connectivity** | `cloudflare-worker/worker.js`, `ConnectivityService` (Web + Desktop) | `scripts/start_server.ps1`, `environment.ts` |
| **Rebuild Android APK or Desktop Installer** | `scripts/build_android_apk.ps1`, `scripts/build_desktop_installer.ps1` | `scripts/build_standalone_exe.py`, `installer/NuevaEcijaTravel.iss` |

---

## 2. Observed Coding Conventions & Recommended Workflow

### Verified Codebase Conventions
- **Backend (Python 3.12)**: Type-annotated SQLAlchemy 2.0 `Mapped[...]` models, Pydantic v2 `BaseModel` schemas with `ConfigDict(from_attributes=True)`, `ruff` and `mypy` listed in `backend/requirements.txt`, `pytest` for unit/integration tests.
- **Frontend (TypeScript / Angular 22)**: Standalone components (`standalone: true`), `inject()` dependency injection, `provideZonelessChangeDetection()` (explicit `ChangeDetectorRef.detectChanges()`), strict ESLint (`--max-warnings 0`), Prettier (`@ionic/prettier-config`), Vitest unit tests alongside every service/component (`*.spec.ts`).
- **Desktop (Python Flet)**: Modular separation into `config/`, `core/`, `models/`, `services/`, `components/`, `views/`, and `tests/`, mirroring Angular service/model contracts 1:1. Always use `get_settings().assets_dir` for bundled read-only assets and `get_settings().storage_dir` for writable runtime files so frozen PyInstaller builds and `%LOCALAPPDATA%` relocation work seamlessly.

### Recommended Git & PR Workflow
1. Create feature branches from `main` using descriptive prefixes (`feat/<topic>`, `fix/<issue>`, `docs/<topic>`).
2. Keep changes synchronized across Backend + Web (`Project/`) + Desktop (`desktop_client/`) when changing API contracts or UI workflows.
3. Never commit compiled binaries (`dist/`, `dist_apk/`, `dist_installer/`, `*.apk`, `*.exe`, `*.zip`) or secrets (`.env`, `*.jks`, `keystore.properties`) to Git.
4. Run all local quality gates before opening a PR (**488 automated tests**):
   ```bash
   python -m pytest backend/tests/ -v
   python -m pytest desktop_client/tests/ -v
   cd Project && npm run lint && npm run test:unit
   ```
5. Tag releases as `vX.Y.Z` to trigger `.github/workflows/release-builds.yml`.

---

## 3. End-to-End Walkthrough: Adding a New Feature (Example: Cloud-Synced Favorites)

Currently, Favorites are stored locally only (`localStorage` on Web, `storage/favorites.json` on Desktop). Here is how a developer would implement cloud-synced favorites consistently with the existing architecture:

1. **Define Scope**: Allow authenticated users to persist favorite `Place` UUIDs in PostgreSQL while keeping local fallback for guests/offline mode.
2. **Database Model (`backend/app/models/entities.py`)**:
   - Add a `UserFavorite(Base)` model with `id` (UUID PK), `user_id` (FK `users.id`, `ON DELETE CASCADE`), `place_id` (FK `places.id`, `ON DELETE CASCADE`), `created_at`, and `UniqueConstraint("user_id", "place_id", name="uq_user_favorite_place")`.
3. **Create Alembic Migration**:
   ```bash
   cd backend && alembic revision --autogenerate -m "add_user_favorites_table"
   alembic upgrade head
   ```
4. **Pydantic Schemas (`backend/app/schemas/place.py`)**: Add `FavoriteCreateIn(place_id: uuid.UUID)` and reuse `PlaceOut` for responses.
5. **Backend Router (`backend/app/api/v1/places.py` or new `favorites.py` mounted in `main.py`)**:
   - `GET /api/v1/favorites` (Bearer JWT, returns `list[PlaceOut]`).
   - `POST /api/v1/favorites` (Bearer JWT, idempotent insert, returns `201`).
   - `DELETE /api/v1/favorites/{place_id}` (Bearer JWT, BOLA-scoped to `current_user.id`, returns `204`).
6. **Web Frontend (`Project/src/app/core/services/favorites.service.ts`)**:
   - Inject `HttpClient`, `AuthService`, and `ConnectivityService`.
   - When authenticated and online, sync `addFavorite`/`removeFavorite` to `/api/v1/favorites` while retaining `localStorage` as offline cache.
7. **Desktop Client (`desktop_client/services/favorites_service.py`)**:
   - Inject `ApiClient` and `SessionManager`, mirroring the same online sync + `favorites.json` fallback.
8. **Automated Tests**:
   - Add BOLA & CRUD tests in `backend/tests/test_favorites.py`.
   - Update `Project/src/app/core/services/favorites.service.spec.ts` and `desktop_client/tests/test_parity_services_and_components.py`.
9. **Update Documentation**: Update `06-API-Reference.md` and `07-Database-Documentation.md`.

---

## 4. Technical Terms & Concepts Explained (How It Works & What It Is Used For in This System)

| Technical Term | How It Works (Technical & Layman Explanation) | What It Is Used For in This System |
|---|---|---|
| **Static Type Checking & Linting (`ESLint`, `Prettier`, `Ruff`, `Mypy`, `tsc`)** | **Layman**: Automated proofreaders for code that catch spelling mistakes, mismatched data types, unused variables, and messy formatting *before* the program is even run.<br>**Technical**: **ESLint** (`10.10.0`) enforces TypeScript/Angular static analysis rules (`--max-warnings 0`); **Prettier** (`3.9.10`) enforces deterministic code formatting; **Ruff** and **Mypy** provide Python linting and PEP 484 static type verification. | Executed via `npm run lint` in `Project/` and during code reviews to maintain clean, bug-free TypeScript and Python code. |
| **SQLAlchemy 2.0 `Mapped[...]` & `mapped_column()`** | **Layman**: A modern way of writing database table definitions in Python so both the code editor and the database know whether a column is a required text string (`Mapped[str]`), an optional number (`Mapped[float | None]`), or a unique ID (`Mapped[uuid.UUID]`).<br>**Technical**: SQLAlchemy 2.0's PEP 484 type-annotated declarative syntax replacing legacy `Column(...)` declarations, enabling full IDE autocompletion and static type checking across ORM queries. | Used across all 8 models and 109 columns in `backend/app/models/entities.py`. |
| **Pydantic `ConfigDict(from_attributes=True)`** | **Layman**: A setting that lets FastAPI take a database object loaded by SQLAlchemy (`user.first_name`) and automatically convert it into a clean JSON response without manually copying every field one by one.<br>**Technical**: Pydantic v2's replacement for v1's `orm_mode = True`, allowing `BaseModel.model_validate(orm_obj)` to read object attributes directly in addition to dictionary keys. | Configured on output schemas (`UserOut`, `MunicipalityOut`, `PlaceOut`, `ItineraryOut`, `ItineraryDayOut`, `ItineraryItemOut`) in `backend/app/schemas/`. |
| **Observer Pattern (`add_listener` / `_notify` vs. RxJS `Observable`)** | **Layman**: A "subscribe to notifications" pattern. When your login status, internet connection, or favorite places change, the central service rings a bell so every open screen or banner updates itself immediately.<br>**Technical**: Implemented via RxJS `BehaviorSubject` streams (`.asObservable()`) in Angular (`Project/src/app/core/services/`) and callback listener lists (`add_listener(cb)` / `_notify()`) in the Python Flet desktop services (`desktop_client/services/`). | Keeps the top/bottom navigation bars, `OfflineHostBanner`, favorite heart icons, and saved itinerary lists synchronized in real time across both Web and Desktop clients. |
