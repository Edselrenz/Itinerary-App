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

---

## ADR-010: Secure Token Storage & Refresh Migration Roadmap (SEC-02)

- **Date**: 2026-11-02
- **Context**: The Technical Evaluation Audit (SEC-02) flagged that storing refresh tokens in `window.localStorage` exposes them to JavaScript in the event of an XSS vulnerability.
- **Problem**: Modern web applications must balance decoupled hosting architectures (e.g., GitHub Pages static SPA frontend communicating with a tunneled FastAPI backend on `ngrok-free.dev`) against cross-site cookie restrictions (Safari Intelligent Tracking Prevention, Chrome Privacy Sandbox, third-party cookie blocking) while providing ironclad token security.
- **Options Considered**:
  1. *Immediate enforcement of HttpOnly cookies in pilot cross-origin setup*: Browser third-party cookie blocking on cross-site domains (`github.io` vs `ngrok-free.dev`) breaks cookie transmission in Safari, iOS WebViews, and strict Chrome configurations, rendering the live web demo unauthenticated.
  2. *Status quo localStorage indefinitely*: Leaves refresh tokens accessible to potential XSS vectors in the long term.
  3. *Phased Security Migration Architecture*:
     - **Phase A (Current Pilot / Cross-Origin)**: Keep short-lived JWT access tokens (30 minutes) and single-use rotating refresh tokens (7 days) with strict origin/hostname allowlisting (`SEC-01`), Argon2id password hashing, and strict input validation.
     - **Phase B (Production Web / Unified Domain)**: When deploying to a custom domain (e.g., `app.tripmo.ph` with API on `api.tripmo.ph`), issue refresh tokens via `Set-Cookie: ne_refresh=...; HttpOnly; Secure; SameSite=Strict; Path=/api/v1/auth/refresh`. Access tokens are maintained strictly in Angular service memory (`AuthService.currentUser$`) and refreshed automatically via silent HTTP interceptor calls.
     - **Phase C (Mobile Binaries / Capacitor)**: On iOS and Android builds, employ `@capacitor-community/secure-storage-plugin` or native Biometric Keychain / Android Keystore encrypted storage, ensuring tokens are protected by hardware security enclaves at rest.
- **Selected Approach**: Option 3 (Phased Security Migration Roadmap).
- **Consequences**:
  - *Advantages*: Preserves 100% functionality and cross-device testing capability for the current GitHub Pages live pilot demo while formally specifying and enforcing the migration path for enterprise web production and native app store distributions.
  - *Disadvantages*: Requires backend cookie-handling support flags and domain-level DNS configuration upon production deployment.

---

## ADR-011: Enterprise GIS Integration & Safe Google API Proxying

- **Date**: 2026-11-05
- **Context**: The application required live Google Places POI discovery, photo galleries, user ratings/reviews, and turn-by-turn road route computations. However, Google API keys must never be exposed to client bundles, billing costs must be contained, and the app must operate seamlessly offline.
- **Problem**: How to integrate Google Maps Platform (Places API New, Routes API v2) without client key leakage, quota overruns, or breaking offline-first resilience.
- **Options Considered**:
  1. *Direct client-side Google Maps JS SDK*: Leaks API key in client bundle, requires paying for map vector tiles, and breaks when offline.
  2. *Backend proxy service with multi-tier caching and automatic fallback*: Server-side API key containment, strict FieldMask projection to reduce billing tier, database `geospatial_cache` table with 24h–168h TTL, Cloudflare Worker KV edge caching, and automatic fallback to public OSRM and Haversine calculations when offline or unconfigured.
- **Selected Approach**: Option 2.
  - Backend `GoogleMapsService` (`backend/app/services/google_maps_service.py`) handles all external calls using explicit `X-Goog-FieldMask`.
  - Photo proxy endpoint (`GET /api/v1/places/photos/{photo_name}`) streams image bytes without exposing underlying Google photo references.
  - Upsert-on-save helper (`resolve_or_upsert_item_place`) stores external Places in the local relational database with zero foreign key integrity errors.
- **Consequences**:
  - *Advantages*: 100% security against API key scraping, predictable billing through database and edge caching, and graceful offline fallback.
  - *Disadvantages*: Adds routing latency on initial cache misses (mitigated by asynchronous pre-computation).

---

## ADR-012: Unified Place Detail Bottom Sheet Architecture

- **Date**: 2026-11-06
- **Context**: `MapPage`, `SuggestedWizardPage`, and `ItineraryDetailPage` originally each maintained separate, duplicated modal markup and logic for showing destination details, leading to divergent designs and repetitive maintenance.
- **Problem**: Inconsistent presentation of photo galleries, reviews, open/closed hours, traveler notes, and commute guides across different application pages.
- **Options Considered**:
  1. *Maintain separate modals in each page*: Results in hundreds of redundant template lines and styling inconsistencies.
  2. *Create a single standalone `PlaceDetailSheetComponent`*: Shared component accepting inputs for `place`, `isOpen`, `stopNotes`, and `commuteInfo`, emitting action events for itinerary actions and directions.
- **Selected Approach**: Option 2.
  - Standalone Angular component `PlaceDetailSheetComponent` placed in `Project/src/app/shared/components/place-detail-sheet/`.
  - Employs `ChangeDetectionStrategy.OnPush` with custom backdrop blur and responsive slide-up animation.
  - Consolidated into `map.page.html`, `suggested-wizard.page.html`, and `itinerary-detail.page.html`.
- **Consequences**:
  - *Advantages*: Eliminated over 250 lines of duplicate template markup, standardized the user experience across all three pages, and simplified test coverage.
  - *Disadvantages*: Unit tests must trigger change detection via `fixture.componentRef.setInput()` due to `OnPush`.

---

## ADR-013: Provincial OpenStreetMap Asset Bundling & Overpass Live Query Architecture

- **Date**: 2026-11-06
- **Context**: The user identified that the map only displayed 13-17 seeded destinations when testing offline or decoupled from the backend server, rather than all real-world establishments (every cafe, tourist spot, lodging, nature park, museum, etc.) mapped in OpenStreetMap across Nueva Ecija.
- **Problem**: How to make thousands of real-world OpenStreetMap POIs available instantly across the mobile/web interface even in standalone/offline mode, while simultaneously providing a path for live, crowd-sourced OpenStreetMap updates without incurring paid API fees.
- **Options Considered**:
  1. *Rely strictly on live backend REST API queries*: Fails whenever the local backend process is stopped, on GitHub Pages static hosting, or in mobile offline field conditions.
  2. *Live client-side Overpass API querying only*: High initial latency, potential rate limiting from public Overpass servers, and complete failure when mobile device lacks internet connection.
  3. *Hybrid Architecture (Pre-indexed Bundled Asset + Backend SQLite/PostgreSQL + Client-Side Live Overpass Discovery)*:
     - Bundle all 2,673 OpenStreetMap POIs across Nueva Ecija as a lean 1.5 MB static asset (`assets/data/osm_places.json`).
     - Load and cache in `PlaceService` with `shareReplay(1)`, powering instant in-memory filtering by keyword, category, municipality, and bbox.
     - Provide an on-demand "Live OSM" action powered by `OsmOverpassService` querying live Overpass API for real-time discoveries in any map view.
     - Configure backend database connection with automatic fallback to root SQLite DB (`nueva_ecija_travel.db`).
- **Selected Approach**: Option 3.
- **Consequences**:
  - *Advantages*: Zero latency on startup; thousands of destinations render immediately via Leaflet MarkerCluster; 100% functionality offline and on GitHub Pages; users can discover new live OSM venues on demand; 0 external API costs.
  - *Disadvantages*: Increases initial client bundle assets by ~1.5 MB (mitigated by asynchronous lazy loading and HTTP caching).




---

## ADR-014: Map & Routing System Overhaul (Production ESM Clustering, Corridor Preset Optimization, and Multi-Waypoint Routing Architecture)

- **Date**: 2026-11-06
- **Context**: An architectural audit of the live deployment on GitHub Pages (`edselrenz.github.io/Itinerary-App`) documented in `itinerary_app_map_and_routing_proposal.pdf` (and detailed in [MAP_AND_ROUTING_PROPOSAL.md](./MAP_AND_ROUTING_PROPOSAL.md)) revealed critical-to-high map and routing gaps: production builds failed to render map pins due to ESM/UMD bundling incompatibilities in `leaflet.markercluster`; offline presets caused 176.2 km cross-province zig-zagging; itineraries lacked multi-waypoint directions and route maps; and commute advice was static Cabanatuan-only.
- **Problem**: How to guarantee resilient production pin rendering on modern esbuild bundlers, eliminate cross-province travel backtracking without breaking existing itineraries, provide universal multi-waypoint directions without paid APIs, and make commute advice route-aware across all 32 municipalities.
- **Options Considered**:
  1. *Use paid routing and map SDKs (Google Maps JavaScript SDK / Mapbox GL)*: Violates ADR-001; incurs recurring API billing and risks bundle key scraping.
  2. *Retain existing static Leaflet and text card architecture*: Leaves production map blank on GitHub Pages and subjects travelers to 176.2 km zig-zags.
  3. *Comprehensive Open-Data Architecture Overhaul (Proposal Blueprints 1–5)*:
     - Fix ESM namespace initialization: unwrap `(L as any).default ?? L`, bind `(window as any).L = LeafletLib` at module top level, and add `L.layerGroup()` fallback.
     - Re-cluster offline presets into 3 geographic corridors (East, North, South) with 2-opt TSP ordering, cutting straight-line transit distance from 176.2 km to 59.4 km (-66.3%).
     - Build reusable `ItineraryRouteMapComponent` with OSRM polylines and Catmull-Rom geodesic spline fallback ($d_{\text{road}} \approx 1.28 \times d_{\text{haversine}}$ for lowlands, $1.45 \times$ for mountains).
     - Construct universal cross-platform multi-stop Google Maps URLs (`&origin=...&destination=...&waypoints=...`).
     - Upgrade commute guide to `getLegCommuteInfo(prevStop, currentStop)`: local tricycles ($\le 1.2$ km), inter-town corridor transfers, and 32-municipality coverage.
     - Add `canDeactivate` guard to `/itinerary/:id`, history-aware back navigation via `IonRouterOutlet`, and true GPS Locate Me control.
- **Selected Approach**: Option 3.
- **Consequences**:
  - *Advantages*: Zero paid API costs (ADR-001 compliant); bulletproof pin rendering in production; 66.3% transit distance reduction for travelers; universal multi-stop Google Maps navigation; leg-aware commute guidance; full offline support.
  - *Disadvantages*: Requires refactoring `map.page.ts` cluster initialization and updating offline preset mock data.
  - *Consequences*: Phased rollout tracked across Phase 27.1 (Immediate Bug Fixes), Phase 27.2 (Route Map & TSP), and Phase 27.3 (Router Guards & Commute Guide).


---

## ADR-015: Saved Itinerary Visual Flagship Alignment & Multi-Waypoint Navigation Architecture

- **Date**: 2026-11-06
- **Context**: A live evaluation of `https://edselrenz.github.io/Itinerary-App/` documented in `itinerary_app_ui_ux_evaluation_report.pdf` (and detailed in [UI_UX_EVALUATION_REPORT.md](./UI_UX_EVALUATION_REPORT.md)) revealed that upon saving a generated itinerary and opening `/itinerary/:id`, the visual presentation severely regressed compared to the pre-save Suggested Wizard preview. Stop photos, segmented day switching, rich time windows, Nearby Places, and Share triggers were stripped or orphaned, while `?? 200` cost fallbacks in `itinerary-detail.page.ts` inflated budgets and contradicted top banners.
- **Problem**: How to restore parity between the pre-save preview and saved trip detail views, eliminate fabricated fees, unbundle orphaned features, and enable seamless multi-stop navigation without violating ADR-001 (Zero Paid APIs) or SCSS bundle budgets.
- **Options Considered**:
  1. *Leave views divergent*: Results in traveler confusion ("bait-and-switch" sensation), fabricated ₱200 fees, and 8-tap single-stop navigation friction.
  2. *Align Saved Itinerary Detail as the Visual Flagship*:
     - Restore 68×68px stop photo thumbnails, step badges, and rich start-end time windows on saved activity cards.
     - Eliminate `?? 200` cost fallbacks; show *Fee not listed* on unpriced cards and delegate to `this.budgetSummary`.
     - Wire `openShareModal()` to a visible header action button.
     - Restore the interactive dashed *Nearby Places* trigger banner on each day card.
     - Unify into a single clean header toolbar (`← Trip Title | [Share] [Edit]`).
     - Implement `buildGoogleMapsDayRouteUrl(items)` for one-tap multi-stop day navigation in Google Maps.
- **Selected Approach**: Option 2.
- **Consequences**:
  - *Advantages*: Eliminates post-save visual drop-off; restores honest budget accounting adhering to ADR-001; reduces multi-stop navigation from 8 taps to 1 tap; un-orphans Share/Export and Nearby Places features.
  - *Disadvantages*: Requires template refactoring in `itinerary-detail.page.html` and updating unit tests in `itinerary-detail.page.spec.ts`.
  - *Consequences*: Remediation tracked across Phase 28 (P0 Immediate, P1 Navigation & Map, P2 Modals).
