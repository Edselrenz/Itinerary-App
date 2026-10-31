# Changelog

All notable changes to the Nueva Ecija Travel Itinerary project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.4.13-alpha] - 2026-10-31
### Added & Changed
- **Home Tab Local Search, Dynamic Featured Places & Saved Itineraries (`Milestone 4`)**:
  - Implemented 300ms debounced RxJS search with `FormControl`, `debounceTime`, `distinctUntilChanged`, and `switchMap` cancellation to query `PlaceService.searchPlaces()` against local database POIs (zero Nominatim calls).
  - Built reactive search results view with 2-column cards, loading spinner, category badges, and empty-state guidance.
  - Connected Popular Destinations horizontal track to live featured places via `PlaceService.getFeaturedPlaces()` with seamless fallback to curated local high-res photography.
  - Enriched Destination Detail Modal with operating hours and honest cost estimates (`₱min - ₱max` or `"Cost not provided"`).
  - Integrated Saved Itineraries section connected to `GuestStorageService.itineraries$` with clean trip cards and an empty-state call-to-action.
  - Created unit test suite in `home.page.spec.ts` (6 tests passing, bringing total test count to 23).

---

## [0.4.12-alpha] - 2026-10-31
### Added
- **Place Models & PlaceService (`Milestone 4 Step 1`)**:
  - Implemented strong TypeScript interfaces in `Project/src/app/core/models/place.models.ts` (`Place`, `Municipality`, `PaginatedPlaces`, `PlaceSearchParams`).
  - Implemented `PlaceService` in `Project/src/app/core/services/place.service.ts` providing methods for `searchPlaces()`, `getFeaturedPlaces()`, `getPlaceById()`, and `getMunicipalities()`.
  - Added fallback high-definition photography mapper in `PlaceService.getPlaceImage()` mapping venues to bundled local assets (`minalungao.png`, `tagpuan_gapan.png`, `pantabangan_lake.png`, etc.).
  - Created complete Angular unit test suite in `place.service.spec.ts` with 11 passing tests verifying HTTP request shapes, query string serialization, and fallback branches.

---

## [0.4.11-alpha] - 2026-10-31
### Changed
- **Apple Social Auth Unavailable State (Login & Signup)**:
  - Visually grayed out the "Continue with Apple" button across both `/login` and `/signup` screens with a muted slate palette (`#f1f5f9` background, `#e2e8f0` border, `#94a3b8` icon and text) and `not-allowed` cursor.
  - Retained accessible informational feedback to clearly communicate pilot status.

---

## [0.4.10-alpha] - 2026-10-31
### Changed & Fixed
- **Signup Screen Exact Figma Alignment & Clean Typography**:
  - Refactored Signup screen layout to match exact Figma mockup with top blue back arrow, centered tilted airplane branding, left-aligned *"Create your account"*, and *"Get started and plan your new adventure."* subtitle.
  - Aligned input fields in exact screenshot sequence: First Name, Middle Initial (if applicable), Last Name, Email with mail icon, Password with key icon and eye toggle, and Confirm Password with checkmark-circle icon and eye toggle.
  - Implemented solid blue pill button (*"Sign up"*), switch row (*"Already have an account? Log in"*), centered *"or"* divider, and outlined social buttons (*Continue with Google*, *Continue with Apple*).
  - Derived username automatically to preserve backend registration schema integrity without cluttering the UI.

---

## [0.4.9-alpha] - 2026-10-31
### Changed & Fixed
- **Login Screen Figma Alignment & Boilerplate Cleanup**:
  - Replaced Login screen layout with exact Figma design: centered airplane branding, left-aligned *"Welcome back!"*, and clean *"Log in to continue your journey."* subtitle.
  - Removed all repetitive "Nueva Ecija" boilerplate from the authentication flow.
  - Updated inputs with embedded blue icons (`mail-outline` and `key-outline`) and trailing eye toggle.
  - Transformed Google and Apple social logins into uniform outlined pill buttons.
  - Upgraded action button to solid blue pill button with focus and disabled states.

---

## [0.4.8-alpha] - 2026-10-31
### Added
- **Fullscreen Interactive Loading / Splash Screen**:
  - Implemented the Figma-aligned loading screen with twilight cityscape imagery and *"Trip mo, trip ko"* branding.
  - Added support for auto-dismissal (2.8s after frontend readiness), click/tap to dismiss, and swipe gestures.
  - Implemented smooth cubic-bezier scale and opacity transition to seamlessly reveal the underlying view.

---

## [0.4.7-alpha] - 2026-10-30
### Added & Changed
- **High-Resolution Asset Upgrade**:
  - Unzipped and extracted `Log_in_pics` and `Popular_Destinations` asset archives into `Project/src/assets/images/`.
  - Replaced all blurry/low-resolution images across Welcome screen, Guest screen, and Home tab popular destination cards with high-definition assets.
  - Added *Lake Farm de La Marre* and *La Casa Prime Cabins* to the curated destination list.

---

## [0.4.6-alpha] - 2026-10-30
### Added & Changed
- **Home Tab & Navigation Bar Figma Alignment**:
  - Re-architected Home tab layout: bold 2-line header, blue notification bell, search box with right-aligned icon.
  - Implemented 2-column side-by-side planner cards: Midnight Navy *Suggested Itinerary* and Sky-Blue-bordered *Custom Itinerary*.
  - Simplified *Popular Destinations* into a clean horizontal track with 120px photo tiles, bold titles, and municipality subtitles.
  - Updated bottom tab bar to icon-only navigation with 4 electric blue icons (`#0084ff`).
  - Preserved destination detail modal sheet, search filtering, and external Google Maps routing.

---

## [0.4.5-alpha] - 2026-10-30
### Fixed
- **GitHub Actions CI Node.js Version for Angular 22**:
  - Upgraded `.github/workflows/deploy.yml` runner Node.js version from `20` to `24`.
  - Satisfies `@angular/cli@22.2.4` requirement (`>= v22.22.3 || >= v24.15.0`) and eliminates exit code 3 during GitHub Pages automated deployment.

---

## [0.4.4-alpha] - 2026-10-30
### Fixed
- **Untrack Gitignored Files from Index**:
  - Untracked `Project/src/environments/environment.prod.ts`, `Project/figma_strings.txt`, and `scripts/__pycache__/*.pyc` from Git index while preserving local files on disk.
  - Added `Project/src/environments/environment.example.ts` as an untracked environment fallback template.
  - Updated GitHub Actions workflow `.github/workflows/deploy.yml` to automatically initialize `environment.prod.ts` from `environment.example.ts` or `environment.ts` during CI runs.

---

## [0.4.3-alpha] - 2026-10-30
### Fixed
- **Gitignore Conflicts & Monorepo Hierarchy**:
  - Re-established comprehensive root `.gitignore` protecting secrets (`.env`), Python cache (`__pycache__`), SQLite databases (`*.db`, `*.sqlite3`), scratch files, and mobile build outputs.
  - Aligned `Project/.gitignore` with root rules.
  - Untracked `.env`, `scratch/`, `__pycache__`, and `*.bin` from Git tracking.
  - Cleaned up redundant root-level duplicate files (`src/`, `package.json`, `angular.json`, etc.) that were accidentally committed during an earlier merge, ensuring `Project/` remains the single canonical source of truth for the Ionic client.

---

## [0.4.2-alpha] - 2026-10-30
### Added
- **Dedicated Guest Onboarding Page (`/guest`)**:
  - Implemented standalone `GuestPage` (`Project/src/app/features/auth/guest/`) replacing the previous modal sheet popup.
  - Full-bleed mountain hiker hero photo (`assets/images/guest_hiker_hero.png`) with floating semi-transparent back button.
  - Exact layout with bold title *"Explore as a guest"*, copy, solid blue pill button *"Continue as Guest"*, and outline pill button *"Create an Account"*.
  - Configured route `/guest` in `app.routes.ts`.

### Changed
- Refactored `welcome.page.*` to remove popup modal and navigate cleanly to `/guest`.

---

## [0.4.1-alpha] - 2026-10-30
### Changed
- **Welcome Screen Layout Realignment**:
  - Re-anchored city buildings graphic (`welcome_hero_buildings.png`) to the bottom of the screen.
  - Implemented header row with inline Clarity airplane SVG + *"Trip mo, trip ko"* title.
  - Added subheadline *"Your next adventure is waiting."* and subtitle *"Get personalize iternaries, easy commutes, and nearby essentials."*
  - Converted *"Log in"* and *"Sign up"* into solid blue pill buttons (`#0084ff`).
  - Added centered `line or line` divider.
  - Converted *"Continue as Guest"* into an outline pill button with solid blue person icon.
- **Ionic 9 Standalone Cleanup**:
  - Replaced lingering `@ionic/angular/standalone` imports in `tabs.page.ts`, `history.page.ts`, and `map.page.ts` with standard `@ionic/angular`.

---

## [0.4.0-alpha] - 2026-10-30
### Added
- **Figma Visual Realignment & Extracted Assets**:
  - Extracted 44 high-resolution imagery assets from `Travel Itinerary App.fig` into `Project/src/assets/images/`.
  - Mapped assets for `welcome_hero_buildings.png`, `guest_illustration.png`, `google_logo.png`, and 9 venue destination cards (`minalungao.png`, `tagpuan_gapan.png`, `pantabangan_lake.png`, `george_point.png`, `highland_bali.png`, `farm_villaronte.png`, `casa_batik.png`, `pavillion_farm.png`, `la_casa_prime.png`).
  - Implemented interactive *"Explore as a guest"* modal sheet in `WelcomePage` with Figma illustrations and localized messaging.
  - Implemented authentic Google OAuth branded button with multi-colored logo `google_logo.png` in `LoginPage`.
  - Implemented Figma Flow 2 Home layout:
    - *"Where are you going next?"* header and profile shortcut.
    - Pill-shaped destination search bar with real-time reactive filtering across destination names, municipalities, and tags.
    - Adventure hero card with motivational travel copy.
    - Suggested & Custom planner entry cards with Figma badge and icon treatments.
    - Horizontal scroll carousel for **Popular Destinations** with snap alignment, real photography, and municipality pills.
    - Destination Detail Modal sheet with image hero, category badge, municipality, description, tags, and zero-cost *"Open in Google Maps"* external URL action.

### Changed
- Refactored `welcome.page.html` and `.scss` to replace generic placeholder icon with Figma hero illustration.
- Updated `Project/src/main.ts` import from `@ionic/angular/standalone` to `@ionic/angular`.
- Adjusted component SCSS budgets in `Project/angular.json` to 10kB warning / 16kB error to accommodate rich responsive styling.

---

## [0.3.0-alpha] - 2026-10-30
### Added
- **Argon2id Authentication Backend**:
  - `backend/app/schemas/auth.py`: Pydantic v2 schemas for registration, login, refresh tokens, Google OAuth, and profiles.
  - `backend/app/services/auth_service.py`: Password hashing with `pwdlib[argon2]`, 30-minute access JWTs, 7-day refresh JWTs, and Google ID token verification.
  - `backend/app/api/v1/auth.py`: REST endpoints `/register`, `/login`, `/refresh`, `/me`, `/oauth/google`, and `/oauth/apple`.
  - `backend/tests/test_auth.py`: Automated tests covering registration, duplicate collisions, wrong credentials, and bearer auth.
- **Mobile Client State & Services**:
  - `Project/src/app/core/services/guest-storage.service.ts`: Local storage driver using `@ionic/storage-angular` (`ne_guest_itineraries_v1`).
  - `Project/src/app/core/services/auth.service.ts`: Session management with reactive `currentUser$` and token storage.
  - `Project/src/app/core/interceptors/auth.interceptor.ts`: Token injection and host-offline graceful handling.
- **Figma-Aligned Screens**:
  - `WelcomePage` (`/welcome`): *"Trip mo, trip ko"* hero with `Log in`, `Sign up`, and `Continue as Guest`.
  - `LoginPage` (`/login`): Form, password toggle, Remember Me, Google button, truthfully disabled Apple button.
  - `SignupPage` (`/signup`): Name fields, username validation, email, password strength, matching-password confirmation validator.
  - `TabsPage` (4-tab shell): Home, Map, History placeholder (*"Planned for a later release"*), and Profile (account status / guest notice).
  - Design tokens in `theme/variables.scss` and `global.scss` with Inter typography and Travel Azure Blue (`#2563eb`).

### Changed
- Refactored Ionic component imports across all pages from `@ionic/angular/standalone` to `@ionic/angular` for Ionic 9 compatibility.
- Adjusted Angular component style budgets in `angular.json` to 6kB warning / 12kB error.

### Security
- Implemented Argon2id password hashing with high memory cost.
- Implemented case-insensitive normalization for usernames and emails to prevent identity impersonation.
- Gated Apple Sign-In behind `501 Not Implemented` and disabled UI state due to US\$99/year developer program requirement.

---

## [0.2.0-alpha] - 2026-10-30
### Added
- **Offline POI Pipeline & Seeding**:
  - `scripts/import_osm.py`: Overpass JSON importer with 16 canonical category mappings, bounding box check (`15.15 <= lat <= 16.15`, `120.70 <= lng <= 121.40`), and nearest municipality resolver.
  - `scripts/seed_featured_places.py`: Seeding script for 12 municipalities and 17 curated destinations (including Bongabon Day 1 stops and Pantabangan resorts).
  - `backend/app/api/v1/places.py`: REST endpoints for `/municipalities`, `/places`, and `/places/{id}` with comma-separated category filtering.
  - `backend/tests/test_foundation.py`: Automated test suite for health check, seeding idempotency, category filtering, and out-of-province POI rejection.

### Fixed
- Fixed category filtering in `places.py` to support comma-separated category strings (`?categories=cafe,restaurant`).
- Added fuzzy name normalization in `import_osm.py` to match "Muñoz" / "Munoz" / "Science City of Muñoz".
- Added `server_default=sa.func.now()` to timestamp columns in Alembic migration `0001_initial_nueva_ecija_schema.py`.

---

## [0.1.0-alpha] - 2026-10-30
### Added
- **Monorepo Foundation & Relational Schema**:
  - `.gitignore` and `.env.example` at repository root.
  - `backend/app/core/config.py`: Pydantic Settings loaded from `.env`.
  - `backend/app/core/database.py`: SQLAlchemy 2.0 engine, declarative base, and session dependency.
  - `backend/app/models/entities.py`: 7 core ORM models (`User`, `AuthIdentity`, `Municipality`, `Place`, `Itinerary`, `ItineraryDay`, `ItineraryItem`) with portable `JsonType` and `Uuid`.
  - `backend/alembic/`: Initial database migration `0001_initial_schema`.
  - `backend/app/main.py`: FastAPI application with CORS and `/health` route.

