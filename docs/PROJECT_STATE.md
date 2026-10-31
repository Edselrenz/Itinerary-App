# Project State & Handoff Document

This document serves as the primary handoff reference for developers and coding agents. It reflects the exact current state of the codebase, verified working functionality, active blockers, and immediate next tasks.

---

## 1. Project Status Overview

- **Application Name**: Nueva Ecija Travel Itinerary (MVP)
- **Current Development Phase**: **Post-Acceptance Security & Code Quality Hardening (Phases 11–14)**
- **Last Verified Working State**: **Phase 10 (24-Point MVP Pilot Acceptance Gate)** completely verified (24/24 criteria passing, 98/98 frontend unit tests, 6/6 backend test suites, ESLint 0 warnings, Prettier clean, clean Angular build).
- **Recent Audit**: Independent Comprehensive Code Review completed on October 31, 2026 ([CODE_REVIEW_AUDIT.md](file:///c:/Users/Edward/Desktop/CaseStudy/docs/CODE_REVIEW_AUDIT.md)) identifying 16 findings (`CR-001` through `CR-016`).
- **Current Active Tasks**: **Phase 11: Priority 1 — Critical Security & Data-Loss Fixes** ([TODO.md](file:///c:/Users/Edward/Desktop/CaseStudy/docs/TODO.md)).
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
- [x] **Fullscreen Interactive Loading / Splash Screen**:
  - Full-bleed illuminated cityscape background (`loading_screen.jpg`) with subtle gradient scrim.
  - Airplane branding + *"Trip mo, trip ko"* headline + *"Plan your trip, explore new places, make better memories."* slogan.
  - Multi-trigger dismissal: Auto-dismissal (2.8s after frontend load), click/tap to dismiss, and touch swipe gestures.
  - Smooth 500ms fade/scale transition into the active view.
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
- [x] **Figma-Aligned Login Screen (`/login`)**:
  - Blue back navigation arrow (`←`).
  - Centered brand header with 45-degree tilted airplane icon + *"Trip mo, trip ko"*.
  - Left-aligned headline: *"Welcome back!"* and subtitle: *"Log in to continue your journey."*.
  - Clean input fields with blue `mail-outline` and `key-outline` leading icons, and `eye-outline` toggle.
  - Remember me checkbox and blue `Forgot password?` link.
  - Solid blue pill action button (*"Log in"*).
  - Outlined pill social logins (*Continue with Google* and grayed-out unavailable *Continue with Apple*).
  - Clean footer: *"Don't have an account? Sign up"*.
- [x] **Figma-Aligned Signup Screen (`/signup`)**:
  - Blue back navigation arrow (`←`).
  - Centered brand header with 45-degree tilted airplane icon + *"Trip mo, trip ko"*.
  - Left-aligned headline: *"Create your account"* and subtitle: *"Get started and plan your new adventure."* (no boilerplate).
  - Clean input fields with 12px rounded borders: *First Name*, *Middle Initial (if applicable)*, *Last Name*, *Email Address* (blue `mail-outline` icon), *Password* (blue `key-outline` icon and eye toggle), *Confirm Password* (blue `checkmark-circle` icon and eye toggle).
  - Cross-field password matching validation.
  - Solid blue pill action button (*"Sign up"*).
  - Centered switch prompt directly below button: *"Already have an account? Log in"*.
  - Centered *"or"* divider rule.
  - Outlined pill social logins (*Continue with Google* and grayed-out unavailable *Continue with Apple*).
  - Automated username generation for backend compatibility.
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
- [x] **Place Service & Models (`Project/src/app/core/`)**:
  - `Place`, `Municipality`, `PaginatedPlaces`, and `PlaceSearchParams` TypeScript interfaces matching backend schemas.
  - `PlaceService` with `searchPlaces()`, `getFeaturedPlaces()`, `getPlaceById()`, and `getMunicipalities()`.
  - Curated high-resolution image fallback resolver `getPlaceImage()`.
  - Canonical category display formatter `formatCategoryName()`.
  - 11 passing Angular unit tests in `place.service.spec.ts`.
- [x] **Home Tab Integration (`Project/src/app/tabs/home/`)**:
  - Reactive search input with `FormControl`, `debounceTime(300)`, and `switchMap` cancellation querying `/api/v1/places?q=...` (0 Nominatim calls).
  - Search results view with 2-column cards, loading spinner, category badges, and empty-state guidance.
  - Popular Destinations carousel populated dynamically via `PlaceService.getFeaturedPlaces()`.
  - Destination Detail Modal sheet with verified operating hours, honest cost bounds (`₱min - ₱max` or "Cost not provided"), and keyless Google Maps external URL directions.
  - Fixed modal hero image overflow (240px cover constraint) and added touch scrollability to modal content.
  - Saved Itineraries card list connected to `GuestStorageService.itineraries$` with clean trip cards and empty-state planner prompt.
  - 6 passing unit tests in `home.page.spec.ts`.
- [x] **Interactive Leaflet Map & 16 Category Filters (`Project/src/app/tabs/map/`)**:
  - Bounded Leaflet map centered on Nueva Ecija `[15.58, 121.00]` with OpenStreetMap raster tiles and proper attribution.
  - 17 category filter pills track ("All Places" + 16 canonical categories) with reactive filtering.
  - Leaflet MarkerCluster integration (`L.markerClusterGroup`) with custom CSS vector pins (`.custom-map-pin`).
  - Interactive POI Bottom Sheet displaying venue photography with local fallbacks, category badges, operating hours, honest pricing, and direct Google Maps directions handoff.
  - Ionic tab lifecycle resize handling (`map.invalidateSize()` on `ionViewDidEnter()`).
  - Fixed map host and canvas viewport height collapsing and tab occlusion (`position: absolute; inset: 0`).
  - Floating Recenter button and live destination counter pill.
  - 9 passing unit tests in `map.page.spec.ts`.
- [x] **Production Build**: Verified with `npm run build` (0 errors, 0 warnings, allowedCommonJsDependencies configured).
- [x] **Custom Itinerary Builder (`Milestone 6`)**:
  - Backend CRUD endpoints in `backend/app/api/v1/itineraries.py` with Broken Object Level Authorization (BOLA).
  - Stop management: add stop with same-day duplicate check, delete stop, and batch reorder (`POST /api/v1/itineraries/{id}/reorder`).
  - Frontend dual-mode service in `Project/src/app/core/services/itinerary.service.ts` with transparent budget math.
  - Multi-day Custom Builder UI (`Project/src/app/features/itinerary/custom-builder`) with day tabs, stop cards, place picker modal, off-grid venues, duplicate alerts, and unsaved changes exit guard.
  - Home tab integration with custom builder navigation and reactive saved itinerary cards.
  - 19 automated tests (3 backend, 13 itinerary service, 6 custom builder) passing with 100% coverage.
- [x] **Suggested Itinerary Recommendation Engine (`Milestone 7`)**:
  - Deterministic clustering generator (`backend/app/algorithms/itinerary_generator.py`) using Haversine distance and database scoring without paid external AI or mapping APIs.
  - Preference scoring (+40 match, +20 featured, +30 proximity, -25 duplicate category penalty, +10 budget fit).
  - Multi-day geographic cluster anchor preventing cross-province backtracking.
  - Realistic daily pacing (2-3 stops/day) with lunchtime dining slot (12:00 PM).
  - Transparent trip assumptions list (transit time exclusions, honest unpriced venue notices).
  - FastAPI endpoint `POST /api/v1/itineraries/suggest` with optional authentication support.
  - Automated pytest suite verifying clustering radius, category diversity, and zero hallucinated venues.
  - Frontend Suggested Itinerary Wizard (`Project/src/app/features/itinerary/suggested-wizard/`):
    - Questionnaire form with destination chips, trip duration calculator, budget presets, and preference chips.
    - "Your Itinerary" preview sheet with day timeline, stop cards, transparent assumptions, and "Accept & Save" persistence.
    - Offline fallback generator in `ItineraryService` (`generateOfflineSuggestedItinerary`).
    - Home tab Suggested Itinerary action card wired to `/suggested-wizard`.
  - 10 unit tests in `suggested-wizard.page.spec.ts` (100% passing).
- [x] **Saved Itineraries & History Tab (`Milestone 8`)**:
  - Home tab list capped at max 2 saved itineraries with "See all" redirection button.
  - History Tab (`/tabs/history`) fully converted into a dedicated Saved Itineraries screen reactively synced with `ItineraryService.itineraries$`.
  - Cards feature plan type badges (`Suggested Plan` / `Custom Plan`), budget tags, destination with location icon, date ranges, days and stop counters, and delete confirmation dialogs.
  - Direct routing to `/custom-builder/:id` upon card selection.
- [x] **Live GitHub Pages Deployment**: Fully deployed and verified live at [https://edselrenz.github.io/Itinerary-App/](https://edselrenz.github.io/Itinerary-App/) (HTTP 200 OK with `--base-href /Itinerary-App/` deep linking enabled).

---

## 3. Features Currently Being Developed (Active Roadmap)

Having completed all foundational milestones (Milestones 0–10) and the 24-Point MVP Acceptance Gate, active engineering has shifted to addressing findings from the October 31, 2026 Code Review & Security Audit:

- **Phase 11: Priority 1 — Critical Security & Data-Loss Fixes**:
  - `CR-001`: Fix cross-itinerary BOLA in `POST /api/v1/itineraries/{id}/reorder` (scope items to itinerary days).
  - `CR-002`: Fix cross-itinerary BOLA/IDOR in `DELETE /api/v1/itineraries/{id}/days/{day_id}/items/{item_id}`.
  - `CR-003`: Fix silent data loss when saving edited itineraries (`CustomBuilderPage`, `ItineraryService`, `PATCH /itineraries/{id}`).
  - `CR-004`: Enforce JWT secret non-default validation in non-dev environments, validate Google OAuth audience, and restrict CORS origin.
  - `CR-005`: Require `email_verified is True` on Google OAuth account linking and block deactivated users (`is_active=False`).

---

## 4. Features Scheduled for Subsequent Phases

- **Phase 12: Priority 2 — Core Reliability & Functional Accuracy**:
  - `CR-006`: Token refresh rotation in `authInterceptor` and `AuthService.refreshSession()`; prevent silent guest storage fallback on 401.
  - `CR-007`: Centralized local date utilities to eliminate UTC midnight off-by-one calendar shifting in UTC+8.
  - `CR-008`: Enforce `default_dest_radius_km` (25km) and cumulative daily budget in `itinerary_generator.py`; escape SQL wildcards in search.
  - `CR-009`: Connect online guests to `/api/v1/itineraries/suggest`; make offline generator respect destination/tags; bind wizard chips dynamically.
  - `CR-010`: Add single-stop `PATCH` endpoint; fix `sort_order` default=1 bug; validate `place_id` foreign key.
  - `CR-011`: Support route queryParams in `MapPage`; add `tileerror` listener; render honest pricing & provenance badges in bottom sheet.
  - `CR-012`: Validate custom API URL format; scope Bearer token injection strictly to `environment.apiBaseUrl`.
  - `CR-013`: Add `--clean --if-exists` to PostgreSQL backup/restore script.
- **Phase 13: Priority 3 — Maintainability & Code Quality Cleanup**:
  - `CR-014`: Delete 16 dead starter files and remove destructive `setup_steps_0_to_2.py`; replace tautological test assertions.
  - `CR-015`: Fix profile observable memory leak, wire non-functional login buttons, fix typos, query nearby places dynamically, prune unused images.
  - `CR-016`: Synchronize all documentation files.
- **Phase 14: Priority 4 — Long-Term Performance & Comprehensive E2E Testing**:
  - `CR-013`: Key SlowAPI rate limits by `CF-Connecting-IP` for Cloudflare Tunnel traffic; pre-filter places in SQL; batch OSM imports.
  - `CR-014`: Rewrite Playwright/Cypress E2E test suite for modern user journeys.

---

## 5. Verification Records & Passing Proof

1. **24-Point MVP Acceptance Gate**:
   - Command: `python scripts/verify_acceptance_gate.py` (with `BypassSandbox: true` on Windows)
   - Result: `All 24/24 acceptance checks passed (100.0%)`.
2. **Backend Automated Tests**:
   - Command: `python -m pytest backend/tests/ -v` (with `BypassSandbox: true` on Windows)
   - Result: `6 passed test suites, 0 failures` (`test_foundation.py`, `test_auth.py`, `test_itineraries.py`, `test_backup_restore.py`, `test_phase8.py`, `test_phase9.py`).
3. **Mobile Client Unit Tests**:
   - Command: `npm run test:unit` in `Project/`
   - Result: `16 test files passed, 98 tests passed in 24.32s [100%]` (includes `place.service.spec.ts`, `itinerary.service.spec.ts`, `custom-builder.page.spec.ts`, `suggested-wizard.page.spec.ts`, `home.page.spec.ts`, `map.page.spec.ts`, `itinerary-detail.page.spec.ts`, `connectivity.service.spec.ts`).
4. **Mobile Client Compilation**:
   - Command: `npm run build` in `Project/`
   - Result: `Application bundle generation complete [0 errors, 0 warnings]` (Artifacts in `Project/www`, component styles strictly under 10kB budget).
5. **Code Quality & Style**:
   - Command: `npm run lint` and `npm run prettier -- --check` in `Project/`
   - Result: `0 ESLint errors, 0 Prettier formatting warnings`.

---

## 6. Immediate Next Development Task

Begin execution of **Phase 11: Priority 1 — Critical Security & Data-Loss Fixes** ([TODO.md](file:///c:/Users/Edward/Desktop/CaseStudy/docs/TODO.md)):
1. Implement BOLA checks in `backend/app/api/v1/itineraries.py` (`CR-001` reorder and `CR-002` item deletion).
2. Fix itinerary update data loss in edit mode (`CR-003`).
3. Add JWT secret startup validation and OAuth client ID enforcement (`CR-004`).
4. Enforce `email_verified` check and active account status on Google OAuth login (`CR-005`).
5. Write and verify automated regression tests in `test_itineraries.py` and `test_auth.py`.




