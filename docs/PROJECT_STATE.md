# Project State & Handoff Document

This document serves as the primary handoff reference for developers and coding agents. It reflects the exact current state of the codebase, verified working functionality, active blockers, and immediate next tasks.

---

## 1. Project Status Overview

- **Application Name**: Nueva Ecija Travel Itinerary (MVP)
- **Current Development Phase**: **Milestone 4 — Home Tab & Local Place Search**
- **Last Verified Working State**: **Milestone 3 (Authentication & Ionic App Shell)** completely implemented and verified with automated test suites and production bundle generation.
- **Current Blockers**: **None**.

---

## 2. Completed Features (Verified)

### Backend (`backend/`)
- [x] **Relational Schema**: 7 core SQLAlchemy 2.0 models (`User`, `AuthIdentity`, `Municipality`, `Place`, `Itinerary`, `ItineraryDay`, `ItineraryItem`) supporting both PostgreSQL and SQLite.
- [x] **Alembic Migration**: `0001_initial_schema` with foreign key cascades and server-side timestamp defaults.
- [x] **System Health Endpoint**: `GET /api/v1/health` verifying liveness and provincial scope.
- [x] **Municipality & Places API**:
  - `GET /api/v1/municipalities` (fuzzy text search).
  - `GET /api/v1/places` (supports bounding box, featured flag, text search, and comma-separated categories).
  - `GET /api/v1/places/{id}` (full provenance and external Google Maps directions URL).
- [x] **Authentication Endpoints**:
  - `POST /api/v1/auth/register` (Argon2id password hashing, case-insensitive uniqueness).
  - `POST /api/v1/auth/login` (generic 401 error, short-lived JWT access and refresh tokens).
  - `POST /api/v1/auth/refresh` (token rotation).
  - `GET /api/v1/auth/me` (Bearer token authentication).
  - `POST /api/v1/auth/oauth/google` (server-side ID token verification).
  - `POST /api/v1/auth/oauth/apple` (truthful 501 gate).
- [x] **Offline Data Pipeline (`scripts/`)**:
  - `import_osm.py`: Overpass JSON import with strict Nueva Ecija bounds (`15.15 <= lat <= 16.15`, `120.70 <= lng <= 121.40`) and 16 canonical categories.
  - `seed_featured_places.py`: Seeds 12 municipalities and 17 curated destinations (including all Bongabon Day 1 stops and Pantabangan resorts).

### Mobile Client (`Project/`)
- [x] **Environment Configuration & Gitignore Integrity**:
  - Untracked `Project/src/environments/environment.prod.ts`, `Project/figma_strings.txt`, and Python bytecode `__pycache__` from Git index while preserving local development files intact.
  - Added `Project/src/environments/environment.example.ts` as fallback template for CI.
  - Updated `.github/workflows/deploy.yml` to automatically initialize `environment.prod.ts` from example before building.
  - Configured local API (`http://127.0.0.1:8000/api/v1`), OSM raster tiles, and `enableAppleAuth: false`.
- [x] **Guest Mode Storage**: `@ionic/storage-angular` configured under key `ne_guest_itineraries_v1`.
- [x] **Authentication Service**: Reactive `currentUser$` session state, JWT storage, login, register, and guest toggle.
- [x] **HTTP Interceptor**: Automatic `Bearer` token injection and offline host error trapping.
- [x] **Figma-Aligned Welcome Screen (`/welcome`)**: Refactored to exact user specification:
  - Header row: Airplane SVG + *"Trip mo, trip ko"*.
  - Subheadline: *"Your next adventure is waiting."*
  - Subtitle: *"Get personalize iternaries, easy commutes, and nearby essentials."*
  - *"Log in"* & *"Sign up"* solid blue pill buttons (`#0084ff`).
  - Centered `line or line` divider.
  - *"Continue as Guest"* outline pill button with blue person icon navigating to `/guest`.
  - City buildings illustration (`welcome_hero_buildings.png`) anchored at the bottom edge.
- [x] **Dedicated Guest Page (`/guest`)**:
  - Full-bleed mountain hiker photography (`guest_hiker_hero.png`) with floating back button (`←`).
  - Heading: *"Explore as a guest"*.
  - Subtitle: *"You can browse destinations, view sample itineraries, and explore features. Your data won't be save"*.
  - Solid blue pill button: *"Continue as Guest"* (activates guest session & enters `/tabs/home`).
  - Outline blue pill button: *"Create an Account"* (navigates to `/signup`).
- [x] **Figma-Aligned Login Screen (`/login`)**: Full form, password visibility toggle, Remember Me, authentic Google logo button (`google_logo.png`), disabled Apple button.
- [x] **Figma-Aligned Signup Screen (`/signup`)**: Name fields, username, email, password strength, and cross-field matching-passwords confirmation validator.
- [x] **Figma-Aligned Home Page (`/tabs/home`)**:
  - Top header with bold 2-line title (*"Where are you / going next?"*) and electric blue notification bell.
  - Destination search bar with 12px rounded borders, placeholder, and trailing magnifying glass icon.
  - Side-by-side 2-column action cards:
    - *Suggested Itinerary* (Midnight Navy gradient, electric blue sparkles, white title).
    - *Custom Itinerary* (White card with 1.5px sky-blue outline, cyan document+clock icon, dark title).
  - **Popular Destinations** horizontal scroll carousel with 120px photo tiles, venue titles, and municipality names.
  - Destination Detail Modal sheet with full image hero, tags, description, and external *"Open in Google Maps"* button.
- [x] **4-Tab Navigation Shell (`/tabs`)**:
  - Icon-only tab bar with 4 solid blue icons (`home`, `location-sharp`, `time-outline`, `person-circle-outline`) in `#0084ff`.
  - Seamless navigation to Home (`/tabs/home`), Map (`/tabs/map`), History (`/tabs/history`), and Profile (`/tabs/profile`).
- [x] **Figma Theme Tokens**: Configured Inter font, Travel Azure Blue (`#2563eb`), and Leaflet CSS.
- [x] **Production Build**: Verified with `npm run build` (0 errors, 0 warnings).
- [x] **Live GitHub Pages Deployment**: Fully deployed and verified live at [https://edselrenz.github.io/Itinerary-App/](https://edselrenz.github.io/Itinerary-App/) (HTTP 200 OK).

---

## 3. Features Currently Being Developed

- **Milestone 4: Home Tab & Local Place Search**:
  - Implementation of Angular `PlaceService` to communicate with `GET /api/v1/places`.
  - Connecting the Home tab search bar with RxJS 300ms debounce and query cancellation.
  - Populating the Popular Destinations section with curated cards.
  - Displaying the Saved Itineraries card list.

---

## 4. Features Not Yet Implemented

- **Milestone 5**: Interactive Leaflet map with 16 category filter pills and POI bottom sheet.
- **Milestone 6**: Custom Itinerary multi-day builder with stop reordering and BOLA checks.
- **Milestone 7**: Deterministic Haversine clustering recommendation engine.
- **Milestone 8**: Day timeline view, stop detail cards, and cross-tab reactive persistence.
- **Milestone 9**: Rate limiting via SlowAPI and backup/restore drills.
- **Milestone 10**: End-to-end 24-point acceptance checklist verification.

---

## 5. Verification Records & Passing Proof

1. **Backend Automated Tests**:
   - Command: `python -m pytest backend/tests/ -v`
   - Result: `2 passed, 1 warning in 5.48s [100%]` (`test_foundation.py` and `test_auth.py`).
2. **Mobile Client Compilation**:
   - Command: `npm run build` in `Project/`
   - Result: `Application bundle generation complete [0 errors]` (Artifacts in `Project/www`).
3. **TypeScript Strict Type Check**:
   - Command: `npm run typecheck:e2e` in `Project/`
   - Result: `0 errors`.

---

## 6. Immediate Next Development Task

Proceed to **Milestone 4 — Implement the Home Tab & Local Place Search**:
1. Create `Project/src/app/core/services/place.service.ts`.
2. Update `Project/src/app/tabs/home/` with:
   - Search input connected to `FormControl` with 300ms debounce.
   - Popular Destinations horizontal carousel displaying the 17 seeded curated places.
   - Saved Itineraries section connected to `GuestStorageService` and `GET /api/v1/itineraries`.
3. Verify search debounce cancels in-flight stale requests and Nominatim is never queried.

