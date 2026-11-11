# Development Plan & UI/UX Audit: Nueva Ecija Travel Itinerary App (`v2.0`)

This document combines the **Comprehensive UI/UX & Figma Parity Audit** (Missing Tabs, Windows, Modals, and Screen-by-Screen Feedback) with the **Complete Engineering Development Plan (Milestones 0–22)** so it can serve as a drop-in replacement for `docs/DEVELOPMENT_PLAN.md`.

## Part 1: Missing Tabs, Windows & Modals

The bottom navigation bar implements all 4 planned primary tabs (`/tabs/home`, `/tabs/map`, `/tabs/history`, `/tabs/profile`), so no top-level bottom tab is missing. However, comparing the Angular frontend (`Project/src/app/`) against the Figma design file (`Travel Itinerary App.fig`), the MVP specification (`nueva_ecija_travel_itinerary_mvp_plan.docx`), and the FastAPI backend (`backend/app/api/v1/`) reveals **9 missing windows, sub-views, and modals**:

| Missing Window / Modal | Source Specification | Current State in Codebase | Required Implementation |
| :--- | :--- | :--- | :--- |
| **Popular Destinations ("See All") Window** | `Travel Itinerary App.fig` (`Popular Destinations` frame with back arrow and full destination catalog) | Clicking **"See all"** on Home (`home.page.ts:237` `onSeeAll()`) routes to `/tabs/map` instead of opening the catalog window. | Dedicated window or modal listing all featured Nueva Ecija destinations with municipality badges, cost ranges, category filters, and quick actions to view details or start a trip. |
| **Scheduled Stop Edit Modal & Day-Move Sheet** | MVP Plan (§6.5, §12.7) & Backend `PATCH /itineraries/{id}/days/{day_id}/items/{item_id}` (`itineraries.py:216`) | The backend `PATCH` endpoint is implemented, but `custom-builder.page.html:296–388` only renders Move Up, Move Down, and Delete buttons on timeline stops. | An **Edit Stop Modal** in `CustomBuilderPage` to edit a stop's `planned_time`, `duration_minutes`, `notes`, `estimated_cost_min/max`, and move the stop to another day. |
| **Database Place Search Tab inside Timeline Picker Modal** | `custom-builder.page.ts:116, 492–518` (`pickerTab: 'browse' \| 'custom'`, `pickerSearchResults`) | `openPlacePicker()` initializes `pickerTab = 'browse'` and fetches places in TypeScript, but `custom-builder.page.html:515–621` only renders the Off-Grid Custom Venue form inside `<ion-modal>`. | Add the segmented tab switcher (`Browse Places` vs. `Off-Grid Custom Venue`) and search results list inside the `<ion-modal>` in `custom-builder.page.html`. |
| **Stop Detail & "How to Get There?" Commute Window** | `Travel Itinerary App.fig` (`How to get there?` frame: Bus terminal, drop-off point, estimated travel time, and `Travel Reminder` callout) | `ItineraryDetailPage` has a partial Stop Detail modal (`itinerary-detail.page.html:194–285`) without commute/terminal guidance, while `SuggestedWizardPage` (`suggested-wizard.page.html:189`) has no Stop Detail modal at all—clicking a stop card opens `Nearby Places`. | Add the Stop Detail modal to `SuggestedWizardPage`, and include a curated **"How to Get There / Terminal Guide & Travel Reminder"** section (e.g., Cabanatuan Central Terminal bus/jeepney guidance + Google Maps handoff). |
| **Profile Sub-Windows: `Edit Profile`, `Settings`, & `After Log Out`** | `Travel Itinerary App.fig` (`Edit Profile`, `Settings`, `Log Out`, `After Log Out` frames) & MVP Plan (§6.8) | `/tabs/profile` (`profile.page.html`) is a static card with an immediate `Log out` button. Server URL settings were also removed in `v0.16.4` (`app.component.ts`). | Add an **Edit Profile** modal (name, username, password), an **App Settings** window (default budget, high-contrast/dark theme toggle from Figma, cache reset, optional custom API/tunnel URL override), and a **Logout Confirmation** alert. |
| **Map Search, Multi-Select Filter Sheet & Accessible POI List Drawer** | MVP Plan (§6.7 & §12.6: search bar, multi-select filter modal with Reset/Apply, and accessible list view) | `/tabs/map` (`map.page.html`) only has a single-select horizontal category pill bar, no search input, and no list drawer. | Add a floating search input on `/tabs/map`, a multi-select filter bottom sheet with budget/municipality/category filters, and a collapsible bottom drawer listing visible POIs. |
| **Assumptions & Budget Breakdown Banner in Suggested Wizard** | MVP Plan (§6.4, §12.8) & `TODO.md` Phase 7 (`assumptions` box + `budgetSummary`) | `suggested-wizard.page.ts:242` calculates `this.budgetSummary` and receives `generatedPlan.assumptions`, but `suggested-wizard.page.html` never renders either property. | Render the **Verified Estimated Costs** card and an expandable **Trip Assumptions & Disclaimers** box in `suggested-wizard.page.html` (and `itinerary-detail.page.html`). |
| **Notifications / Travel Alerts Drawer** | Home Header Bell (`home.page.html:18`, `home.page.ts:242`) | Clicking the notification bell only triggers a hardcoded 2.5s toast (`"You're all caught up! No active travel alerts..."`). | Add a Notifications / Travel Reminders popover or modal showing upcoming saved trip reminders, offline sync alerts, and provincial travel advisories. |
| **Password Reset & Itinerary Share/Export Sheet** | Login (`login.page.ts:112`) & `TODO.md` Phase 16.4 (Trip Export & Sharing) | `onForgotPassword()` only displays an admin contact toast; `ItineraryDetailPage` has no Share/Export action. | Add a Password Reset request modal on `/login` and an Export/Share action sheet (printable PDF summary, shareable link, or `.ics` calendar export) on `/itinerary/:id`. |

## Part 2: Feedback on Existing Tabs, Windows & Overlays

### 2.1 Global App Shell & Overlays (`Project/src/app/app.component.*`)
- **Splash Screen Overlay (`app.component.html:2–51`)**: Uses clean animations, accessible dialog attributes (`role="dialog"`, `aria-modal="true"`), and multi-trigger dismissal (click, swipe, keyboard `Escape`/`Enter`/`Space`, and a 2.8s timer). However, `showSplashScreen` initializes to `true` in memory on every page reload (`app.component.ts:19`), so calling `window.location.reload()` from `ConnectivityService.retryConnection()` forces the user through the 2.8s splash screen again mid-session. Persist dismissal in `sessionStorage` and remove or bind the unused `.pulse-ring` class in `app.component.scss:134`.
- **Offline Mode Banner (`app.component.html:54–78`)**: Non-blocking top banner with `role="status"` and retry spinner works well. Because the manual tunnel URL configuration alert was removed in `v0.16.4`, testers on physical devices have no UI fallback if the default Cloudflare tunnel URL changes; relocating that override into an "Advanced Connection Settings" modal inside Profile preserves a clean top banner without losing field configurability.

### 2.2 Authentication Windows (`Project/src/app/features/auth/`)
- **Welcome Window (`welcome/welcome.page.*`)**: Clean layout faithful to Figma with clear paths for Sign Up, Log In, and Guest mode.
- **Guest Mode Prompt (`guest/guest.page.*`)**: Clearly explains that guest trips are saved locally on the device and can be synced to an account later.
- **Login Window (`login/login.page.*`)**:
  - **Unused `rememberMe` Control**: `rememberMe` is defined in the form (`login.page.ts:47`), but `onSubmit()` (`login.page.ts:72`) never reads `this.loginForm.value.rememberMe`, and `AuthService` unconditionally writes tokens to `localStorage`. Pass `rememberMe` to `AuthService` (`sessionStorage` when unchecked, `localStorage` when checked).
  - **Inverted Password Visibility Icon**: `login.page.html:58` uses `[name]="showPassword ? 'eye-off-outline' : 'eye-outline'"`, whereas `signup.page.html:88` uses the opposite (`[name]="showPassword ? 'eye-outline' : 'eye-off-outline'"`). Standardize both templates.
- **Sign Up Window (`signup/signup.page.*`)**:
  - **Silent Data Loss on `middleInitial`**: The form renders a `Middle Initial` input (`signup.page.html:39`), but `onSubmit()` (`signup.page.ts:116–128`) combines only `firstName` and `lastName` into `fullName` and drops `middleInitial`.
  - **Auto-Generated Username Collision Risk**: Although the MVP plan (§6.2) specifies a user-chosen `Username` field, `signup.page.ts:119` auto-generates `username` from the email prefix (`emailStr.split('@')[0]`). Two users with the same prefix on different email providers (e.g., `juan@gmail.com` and `juan@yahoo.com`) will collide on the backend's unique `username` constraint with a `409 Conflict` error and have no input field to change their username.

### 2.3 Bottom Tab Bar & Primary Tabs (`Project/src/app/tabs/`)
- **Bottom Tab Bar (`tabs.page.html`)**:
  - **Icon-Only Navigation Hurts Discoverability**: Rendering only icons (`home`, `location-sharp`, `bookmark-outline`, `person-circle-outline`) without visible `<ion-label>` text (`Home`, `Map`, `Saved`, `Profile`) forces first-time users to guess what the bookmark and pin tabs represent.
  - **Route/Label Naming Inconsistency**: The route and component are named `/tabs/history` (`HistoryPage`), while the tab button `aria-label` and page title are `"Saved Itineraries"`. Add `/tabs/saved` as a route alias.
- **Tab 1 — Home (`home/home.page.*`)**:
  - **Strengths**: 300ms debounced search with `switchMap` cancellation and offline fallback (`home.page.ts:89–118`), clear 2-column entry cards for *Suggested* vs. *Custom* itineraries, and reactive synchronization with `ItineraryService.savedItineraries$`.
  - **Misleading "Plan Route Here" CTA in Destination Modal**: Inside the Home Destination Detail modal (`home.page.html:243`), the primary button says **"Plan Route Here"** (`startPlanningWithDestination()`), which navigates to `/tabs/map?lat=...&lng=...` instead of launching `/suggested-wizard` or `/custom-builder` pre-filled with that destination's municipality.
  - **Narrow Popular Destination Cards**: `.dest-card` items (`home.page.scss:241`) are `120px` wide (`120px × 140px`) and omit category badges and cost estimates, unlike the richer search result cards above them.
- **Tab 2 — Map (`map/map.page.*`)**:
  - **Strengths**: Bounded to Nueva Ecija (`NE_BOUNDS`), uses `MarkerCluster` with custom accessible HTML pins (`tabindex="0"`, `role="button"`, `aria-label`), handles offline map tile failures gracefully (`tileError` banner), and recalculates layout via `map.invalidateSize()` in `ionViewDidEnter()`.
  - **Dead-End POI Bottom Sheet**: Tapping a pin opens a bottom sheet (`map.page.html:52–95`) that only offers `"Get Directions (Google Maps)"` with no button to add the place to an existing itinerary or start a new itinerary from that pin.
  - **Hardcoded `limit: 100` Without Viewport Bounds**: `loadPlaces()` (`map.page.ts:116`) fetches `{ limit: 100 }` globally rather than passing the map's current bounding box (`min_lat`, `max_lat`, `min_lng`, `max_lng`) supported by `GET /api/v1/places`.
- **Tab 3 — History / Saved Itineraries (`history/history.page.*`)**:
  - **Strengths**: Clean summary cards showing plan type badge (`Suggested Plan` vs. `Custom Plan`), daily budget, date range, day/stop counts, and an empty state with dual CTAs.
  - **Missing Filtering & Estimated Cost Comparison**: Lacks segment filters (*All*, *Upcoming*, *Past*, *Suggested*, *Custom*) or a search bar, and cards show only `daily_budget` without displaying the calculated `Verified Estimated Costs` range (`minTotal–maxTotal`).
- **Tab 4 — Profile (`profile/profile.page.*`)**:
  - **Strengths**: Distinguishes Guest Mode from Verified Account and includes the **"Unsaved Local Trips Detected — Sync to Account Now"** migration card (`profile.page.html:66–81`).
  - **Immediate Unconfirmed Logout**: Clicking `Log out` (`profile.page.ts:59`) immediately clears tokens and navigates to `/welcome` without an `AlertController` confirmation dialog.

### 2.4 Standalone Itinerary Windows (`Project/src/app/features/itinerary/`)
- **Window 1 — Suggested Itinerary Wizard (`suggested-wizard/suggested-wizard.page.*`)**:
  - **Quick Destination Chips Implemented in TS But Unrendered in HTML**: `suggested-wizard.page.ts:69–76` defines `public quickDestinations = ['Bongabon', 'Pantabangan', 'Cabanatuan City', 'Gapan City', 'General Tinio', 'Nueva Ecija']` and `setDestination(dest: string)`, but `suggested-wizard.page.html` never renders them.
  - **Clicking a Stop Card Opens "Nearby Places" Instead of Stop Details**: In `suggested-wizard.page.html:189`, every `.figma-stop-card` has `(click)="openNearbyPlaces(stop)"`, which switches the entire screen to `viewMode = 'nearby'` (and ignores the `stop` argument in `openNearbyPlaces(_stop?: any)` at line 319) instead of opening a Stop Detail Modal.
  - **Non-Interactive "Nearby Places" View**: In `viewMode === 'nearby'` (`suggested-wizard.page.html:231–263`), `.figma-nearby-card` items only show the place's name and opening hours with no click action or `"Add to Day"` button.
  - **Remaining UTC `new Date()` Parsing in `formattedTripDateSubtitle()`**: `suggested-wizard.page.ts:210–211` still calls `new Date(startStr)` and `new Date(endStr)` directly on ISO `YYYY-MM-DD` strings instead of `parseLocalIsoDate()`.
- **Window 2 — Custom Itinerary Builder (`custom-builder/custom-builder.page.*`)**:
  - **Strengths**: Smooth 3-stage progression (`form` -> `browse` -> `timeline`), live budget math banner (`Verified Estimated Costs`), same-day duplicate stop guard, and unsaved-changes confirmation on the header back button.
  - **Client-Side-Only Browse Cap (`getFeaturedPlaces(50)`)**: `loadBrowsePlaces()` (`custom-builder.page.ts:415`) fetches only 50 featured places and filters them in memory during `onBrowseSearch()` instead of querying `placeService.searchPlaces(query, category)` against the backend database.
  - **Missing Time & Coordinate Inputs on Custom Venue Modal**: The "Add Off-Grid Custom Venue" modal (`custom-builder.page.html:529–617`) omits inputs for `planned_time`, `custom_lat`, and `custom_lng` even though `BuilderStop` and the backend schema support them.
  - **Remaining UTC `.toISOString().split('T')[0]` Calls**: Lines `154–155`, `189`, `201`, `224`, and `241–244` in `custom-builder.page.ts` still use `new Date().toISOString().split('T')[0]` instead of `toLocalIsoDate()`.
- **Window 3 — Itinerary Detail (`itinerary-detail/itinerary-detail.page.*`)**:
  - **Hardcoded Fallback Strings Create Misleading Schedules**:
    - `getTimingTime(stop)` (`itinerary-detail.page.ts:206–215`) falls back to `'12:00 PM - 2:00 PM'` whenever `stop.time` is empty, causing every stop in a saved Custom Itinerary to display `12:00 PM - 2:00 PM`.
    - `formatDailyBudget()` (`itinerary-detail.page.ts:171`) falls back to `'₱ 3,000 - ₱ 5,000/day'` when `daily_budget` is `0` rather than `'Flexible Budget'`.
    - `getDaySubtitle(day)` (`itinerary-detail.page.ts:201`) hardcodes `'Food spots, local culture, and historic sites in ' + muni + '!'` regardless of the actual stop categories on that day.
  - **Static Nearby Places Sub-View**: `.figma-nearby-card` items in `viewMode === 'nearby'` (`itinerary-detail.page.html:151–186`) lack click actions, cost badges, and `"Add to Day"` / `"Directions"` buttons.

## Part 3: Milestone Status Overview & Audit Registry

### 3.1 Milestone Status Table (Milestones 0–22)

| Step | Milestone Name | Primary Focus | Verification Gate | Status |
| :---: | :--- | :--- | :--- | :---: |
| **0** | **Monorepo & Scope Freeze** | Monorepo layout, `.gitignore`, `.env.example`, dependency locking. | Clean tree, zero hardcoded secrets. | **COMPLETED** |
| **1** | **PostgreSQL & FastAPI Core** | 7 SQLAlchemy 2.0 ORM models, Alembic migration, health check. | `GET /api/v1/health` returns 200 OK. | **COMPLETED** |
| **2** | **OSM POI Pipeline & Seeding** | Overpass importer, bounding box check, 17 curated featured places. | Idempotent seed produces 0 duplicate rows. | **COMPLETED** |
| **3** | **Auth & Ionic App Shell** | Argon2id auth, JWT, Google OAuth verify, Guest storage, 4-tab shell. | Pytest 100% pass; Angular build succeeds. | **COMPLETED** |
| **4** | **Home Tab & Debounced Search** | 300ms RxJS search, popular destinations carousel, saved cards. | Local database search, 0 Nominatim calls. | **COMPLETED** |
| **5** | **Leaflet Map & 16 Filters** | Bounded Leaflet map, category filters, marker cluster, bottom sheet. | Responsive map, external directions handoff. | **COMPLETED** |
| **6** | **Custom Itinerary Builder** | Multi-day custom creator, stop reordering, honest budget math. | BOLA ownership checks, duplicate guards. | **COMPLETED** |
| **7** | **Suggested Itinerary Engine** | Deterministic Haversine clustering, preference scoring, diversity. | Transparent assumptions, no hallucinated venues. | **COMPLETED** |
| **8** | **Overview, Day View & Sync** | Timeline view, stop detail cards, reactive cross-tab persistence. | Home cards sync immediately after edit. | **COMPLETED** |
| **9** | **Pilot Security & Tunneling** | Rate limiting (SlowAPI), offline interceptor, backup/restore drills. | Cross-device LAN testing, isolated DB port. | **COMPLETED** |
| **10** | **QA & Pilot Acceptance** | Full automated verification matrix, 24-point acceptance checklist. | 100% pass across all 24 acceptance criteria. | **COMPLETED** |
| **11** | **Priority 1: Security & Data-Loss** | Fix BOLA/IDOR (CR-001, CR-002), edit-mode data loss (CR-003), JWT/OAuth hardening (CR-004, CR-005). | Negative BOLA tests pass; edit preserves days; strong secrets enforced. | **COMPLETED** |
| **12** | **Priority 2: Core Reliability** | Token refresh (CR-006), timezone calendar fixes (CR-007), generator radius/budget (CR-008, CR-009), PATCH stop (CR-010), map routing (CR-011), URL safety (CR-012). | Zero timezone shift; 25km radius bound; auth refresh works seamlessly. | **COMPLETED** |
| **13** | **Priority 3: Maintainability** | Clean dead starter files, remove destructive scripts, fix acceptance tautologies (CR-014), memory leaks & typos (CR-015), doc sync (CR-016). | Clean codebase; 0 memory leaks; exact test assertions. | **COMPLETED** |
| **14** | **Priority 4: Performance & E2E** | Cloudflare Tunnel IP rate limiting, SQL generator pre-filtering, OSM batching (CR-013), rewrite modern E2E test suite (CR-014). | Independent remote rate limiting; sub-100ms generation; passing E2E spec. | **COMPLETED** |
| **15** | **Audit Remediation & Hardening** | Remediate 10 defects (DEF-01 to DEF-10) and 3 security items (SEC-01 to SEC-03) from Nov 2, 2026 Audit Report. | 30/30 QA cases passing, 0 shadowed routes, consolidated offline POI module. | **COMPLETED** |
| **16** | **Unwired State & Template Parity** | Render unwired TypeScript state (`quickDestinations`, `budgetSummary`, `assumptions`, `pickerTab`), fix remaining UTC date calls, persist splash state. | All computed TS properties rendered in HTML; 0 UTC off-by-one calls; splash skips reload. | **COMPLETED** |
| **17** | **Custom Builder Stop Edit & Scheduling** | Build Edit Stop Modal (`PATCH` stop item), Move-to-Day action, custom venue time/coord inputs, server-backed browse search, sequential time formatting, `canDeactivate` guard. | Users can edit time/duration/cost/notes and move stops across days; 0 hardcoded `12:00 PM` fallbacks. | **COMPLETED** |
| **18** | **Missing Figma Windows & Commute Guide** | Build Popular Destinations ("See All") window, wire Stop Detail Modal in Suggested Wizard, add "How to Get There?" commute/terminal section, make Nearby Places interactive. | Clicking "See all" opens catalog; stop cards open detail modal with commute info; nearby cards add to day. | **COMPLETED** |
| **19** | **Map Search, Multi-Filter & POI Drawer** | Add floating Map search bar, multi-select filter bottom sheet, accessible POI list drawer, "Add to Itinerary" bottom-sheet CTA, dynamic viewport bounding-box queries. | Map supports keyword search, multi-category filter, list toggle, and direct itinerary insertion. | **COMPLETED** |
| **20** | **Profile Windows, Notifications & Saved Filters** | Build `Edit Profile` modal (`PATCH /auth/me`), `Settings` modal (theme/contrast, budget, tunnel URL), Logout confirmation, Notifications popover, tab labels, History filters. | Users can edit profile/settings, confirm logout, filter saved trips, and view travel alerts. | **COMPLETED** |
| **21** | **Auth Form Integrity & Recovery UI** | Add explicit `Username` field on Signup, preserve `middleInitial`, wire `rememberMe` storage scope on Login, standardize eye icons, build Forgot Password modal. | Zero email-prefix username collisions; `middleInitial` saved; `rememberMe` toggles `sessionStorage`. | **COMPLETED** |
| **22** | **Export/Share, PWA Caching & Capacitor** | Build Share/Export sheet (PDF & `.ics` export), configure Service Worker offline tile cache, scaffold Capacitor Android APK with Secure Storage (`SEC-02`), expand E2E tests. | Printable PDF & `.ics` downloads work offline; Android APK builds cleanly; E2E suite passes 100%. | **COMPLETED** |

### 3.2 Audit Gap & Defect Registry (`UI-01` to `UI-24`)

| ID | Category | Affected Component / File | Finding Summary | Target Milestone |
| :---: | :--- | :--- | :--- | :---: |
| **UI-01** | Unwired TS State | `suggested-wizard.page.ts:69–76` & `.html` | `quickDestinations` array and `setDestination(dest)` exist in TypeScript but are never rendered as quick-select chips in HTML. | **Milestone 16** |
| **UI-02** | Missing MVP UI | `suggested-wizard.page.ts:242` & `.html`, `itinerary-detail.page.html` | `budgetSummary` (`Verified Estimated Costs`) and `assumptions` array are computed/stored in TS but never rendered in `SuggestedWizardPage` (and `assumptions` is missing in `ItineraryDetailPage`). | **Milestone 16** |
| **UI-03** | Dead Modal Tab | `custom-builder.page.ts:116, 492–518` & `.html:515–621` | `openPlacePicker()` initializes `pickerTab: 'browse' \| 'custom'` and loads `pickerSearchResults`, but the `<ion-modal>` HTML only renders the Off-Grid Custom Venue form. | **Milestone 16** |
| **UI-04** | Timezone Bug | `suggested-wizard.page.ts:210–211`, `custom-builder.page.ts:154–244` | Remaining `new Date(isoStr)` and `new Date().toISOString().split('T')[0]` calls bypass `date-input.util.ts` (`parseLocalIsoDate` / `toLocalIsoDate`). | **Milestone 16** |
| **UI-05** | Global Overlay UX | `app.component.ts:19`, `app.component.scss:134` | `showSplashScreen = true` resets on every page reload (including `ConnectivityService.retryConnection()`), replaying the 2.8s splash screen mid-session; `.pulse-ring` CSS is unused. | **Milestone 16** |
| **UI-06** | Missing Modal | `custom-builder.page.html:296–388`, `itineraries.py:216` | Backend `PATCH /api/v1/itineraries/{id}/days/{day_id}/items/{item_id}` exists, but timeline cards lack an **Edit Stop Modal** to update time, duration, cost, or notes. | **Milestone 17** |
| **UI-07** | Missing MVP Action | `custom-builder.page.html:296–388` (MVP §6.5, §12.7) | Scheduled stops only support same-day Move Up / Move Down / Remove; there is no UI to move a stop between days. | **Milestone 17** |
| **UI-08** | Incomplete Form | `custom-builder.page.html:529–617` | The "Add Off-Grid Custom Venue" form omits inputs for `planned_time`, `custom_lat`, and `custom_lng` despite full backend schema support. | **Milestone 17** |
| **UI-09** | Misleading Fallbacks | `itinerary-detail.page.ts:171, 201, 206–215` | `getTimingTime()` defaults every unscheduled custom stop to `'12:00 PM - 2:00 PM'`; `formatDailyBudget()` defaults `0` to `'₱ 3,000 - ₱ 5,000/day'`; `getDaySubtitle()` hardcodes `'Food spots, local culture, and historic sites...'`. | **Milestone 17** |
| **UI-10** | Search Cap & Guard | `custom-builder.page.ts:415`, `app.routes.ts:39–49` | `loadBrowsePlaces()` only loads 50 featured places and filters client-side; `hasUnsavedChanges` is not registered as an Angular Router `canDeactivate` guard. | **Milestone 17** |
| **UI-11** | Missing Figma Screen | `home.page.ts:237` (`Travel Itinerary App.fig` strings `1460–1650`) | Clicking **"See all"** next to Popular Destinations routes to `/tabs/map` instead of opening the Figma **Popular Destinations** catalog window. | **Milestone 18** |
| **UI-12** | Wrong Click Binding | `suggested-wizard.page.html:189`, `suggested-wizard.page.ts:319` | Clicking a `.figma-stop-card` calls `openNearbyPlaces(stop)` (switching the whole screen to Nearby Places) instead of opening a **Stop Detail Modal**. | **Milestone 18** |
| **UI-13** | Missing Figma Section | `itinerary-detail.page.html:194–285` (`Travel Itinerary App.fig` strings `1396–1456`) | Stop Detail modal lacks the Figma **"How to get there?"** commute guide (terminal departure, drop-off point, estimated travel time) and **`Travel Reminder`** info callout. | **Milestone 18** |
| **UI-14** | Static Sub-View | `suggested-wizard.page.html:231–263`, `itinerary-detail.page.html:151–186` | `.figma-nearby-card` items in `viewMode === 'nearby'` are non-interactive and lack cost/category badges, distance, or `"Add to Day"` / `"Directions"` actions. | **Milestone 18** |
| **UI-15** | Misleading Home CTA | `home.page.html:243`, `home.page.ts:294`, `home.page.scss:241` | "Plan Route Here" in Home's Destination Detail Modal redirects to `/tabs/map` instead of starting an itinerary; `.dest-card` carousel items (`120px`) omit cost and category badges. | **Milestone 18** |
| **UI-16** | Missing Map Controls | `map.page.html`, `map.page.ts` (MVP §6.7, §12.6) | `/tabs/map` lacks a keyword search bar, a multi-select category/budget filter sheet with Reset/Apply, and an accessible POI list drawer. | **Milestone 19** |
| **UI-17** | Dead-End Map Sheet & Query Cap | `map.page.html:52–95`, `map.page.ts:116` | Map POI bottom sheet lacks an `"Add to Itinerary"` CTA; `loadPlaces()` queries a static `{ limit: 100 }` without passing viewport bounding-box coordinates (`min_lat`, `max_lat`, `min_lng`, `max_lng`). | **Milestone 19** |
| **UI-18** | Missing Figma Profile Windows | `profile.page.html`, `profile.page.ts:59` (`Travel Itinerary App.fig` strings `1349–1352`) | `/tabs/profile` lacks `Edit Profile`, `Settings` (theme/contrast toggle, default budget, custom API/tunnel URL), and a `Log Out` confirmation dialog. | **Milestone 20** |
| **UI-19** | Missing Notifications UI | `home.page.html:18`, `home.page.ts:242` | Tapping the Home notification bell only shows a static 2.5s toast instead of opening a Notifications / Travel Reminders popover or drawer. | **Milestone 20** |
| **UI-20** | Tab & History UX Gaps | `tabs.page.html`, `history.page.html` | Bottom tab bar is icon-only (no text labels); `/tabs/history` lacks segment filtering (`Upcoming`, `Past`, `Suggested`, `Custom`), keyword search, and calculated total cost range display. | **Milestone 20** |
| **UI-21** | Signup Data & Username Bug | `signup.page.html:39`, `signup.page.ts:116–128` (MVP §6.2) | `middleInitial` is collected in the form but silently dropped in `onSubmit()`; `username` is auto-derived via `email.split('@')[0]`, causing `409 Conflict` collisions across domains. | **Milestone 21** |
| **UI-22** | Login Form Bugs | `login.page.ts:47, 72`, `login.page.html:58`, `signup.page.html:88` | `rememberMe` form control is ignored; password visibility eye icon logic is inverted between Login and Signup; Forgot Password lacks a recovery modal. | **Milestone 21** |
| **UI-23** | Missing Share/Export | `itinerary-detail.page.html` (`TODO.md` Phase 16.4) | No UI action sheet or modal to export an itinerary as a printable PDF summary or `.ics` calendar file. | **Milestone 22** |
| **UI-24** | PWA & Native Packaging | `Project/` (`TODO.md` Phases 16.2–16.3, `SEC-02`) | Service Worker tile pre-caching and Capacitor Android packaging with hardware-backed Secure Storage (`@capacitor-community/secure-storage-plugin`) remain unbuilt. | **Milestone 22** |

## Part 4: Detailed Task Breakdown (Milestones 0–22)

### Completed Foundation & Hardening Milestones (Milestones 0–15)

#### Milestone 0: Monorepo & Scope Freeze (Completed)
- [x] Configure repository root `.gitignore` protecting secrets, virtual environments, node artifacts, and dumps.
- [x] Create `.env.example` with documented environment variable template.
- [x] Establish backend dependency pins in `backend/requirements.txt`.
- [x] Align directory layout containing `Project/`, `backend/`, and `scripts/`.

#### Milestone 1: PostgreSQL, SQLAlchemy Models & FastAPI Foundation (Completed)
- [x] Implement database session manager in `backend/app/core/database.py`.
- [x] Implement settings loader in `backend/app/core/config.py`.
- [x] Implement 7 core SQLAlchemy 2.0 entities in `backend/app/models/entities.py` (`User`, `AuthIdentity`, `Municipality`, `Place`, `Itinerary`, `ItineraryDay`, `ItineraryItem`).
- [x] Generate initial Alembic migration (`0001_initial_nueva_ecija_schema.py`).
- [x] Implement FastAPI main entrypoint with CORS and `GET /api/v1/health` in `backend/app/main.py`.

#### Milestone 2: POI Ingestion & Curated Seeding Pipeline (Completed)
- [x] Implement canonical 16-category mapping in `scripts/import_osm.py`.
- [x] Enforce Nueva Ecija bounding box filter (`15.15 <= lat <= 16.15`, `120.70 <= lng <= 121.40`).
- [x] Implement fuzzy municipality resolver for "Muñoz" / "Science City of Muñoz".
- [x] Implement `scripts/seed_featured_places.py` with 12 municipalities and 17 curated destinations.
- [x] Implement `GET /api/v1/municipalities` and `GET /api/v1/places` endpoints with comma-separated category support in `backend/app/api/v1/places.py`.
- [x] Verify with automated test suite `backend/tests/test_foundation.py`.

#### Milestone 3: Authentication & Ionic Angular Shell (Completed)
- [x] Implement Argon2id password hashing and short-lived JWT token service in `backend/app/services/auth_service.py`.
- [x] Implement REST endpoints in `backend/app/api/v1/auth.py` (`/register`, `/login`, `/refresh`, `/me`, `/oauth/google`, `/oauth/apple`).
- [x] Verify with automated test suite `backend/tests/test_auth.py`.
- [x] Install `@ionic/storage-angular`, `leaflet`, `leaflet.markercluster` in `Project/`.
- [x] Configure `environment.ts` and `environment.prod.ts`.
- [x] Implement `GuestStorageService` (`ne_guest_itineraries_v1`), `AuthService`, and `authInterceptor`.
- [x] Build Welcome Page, Login Page, Signup Page, and 4-Tab Shell (`tabs.routes.ts`).

#### Milestone 4: Home Tab & Local Place Search (Completed)
- [x] Implement `PlaceService` (`place.service.ts`) and models (`place.models.ts`).
- [x] Connect Home tab search bar to `GET /api/v1/places` using 300ms RxJS debounce and `switchMap` cancellation.
- [x] Connect Popular Destinations horizontal carousel to `PlaceService.getFeaturedPlaces()`.
- [x] Build Saved Itineraries card list and Destination Detail Modal.

#### Milestone 5: Leaflet Map & 16 Category Filters (Completed)
- [x] Implement Leaflet map bounded to Nueva Ecija `[15.58, 121.00]` with max bounds constraint.
- [x] Configure OpenStreetMap raster tile layer with attribution and `MarkerCluster` custom pins.
- [x] Build interactive POI Bottom Sheet and handle `map.invalidateSize()` on `ionViewDidEnter()`.

#### Milestone 6: Custom Itinerary Builder (Completed)
- [x] Backend CRUD endpoints in `backend/app/api/v1/itineraries.py` with BOLA checks.
- [x] Multi-day custom creator with day tabs and stop reordering (`POST /api/v1/itineraries/{id}/reorder`).
- [x] Same-day duplicate stop guard dialog and honest budget calculation helper (`ItineraryService.calculateBudgetSummary`).

#### Milestone 7: Suggested Itinerary Engine (Completed)
- [x] Backend generation endpoint `POST /api/v1/itineraries/suggest` with deterministic Haversine geographic clustering.
- [x] User preference questionnaire, scoring matrix, and transparent assumptions list.
- [x] Suggested Itinerary wizard frontend and offline fallback generator.

#### Milestone 8: Itinerary Management & Day Timeline View (Completed)
- [x] Itinerary Detail / Day Timeline view (`/itinerary/:id`) and Stop Detail modal.
- [x] History / Saved Itineraries tab (`/tabs/history`), Edit action (`/custom-builder/:id`), and Delete confirmation modal.

#### Milestone 9: Pilot Security & Tunneling (Completed)
- [x] Rate limiting on auth endpoints with SlowAPI (5/min per IP).
- [x] Offline host warning banner (`ConnectivityService` + `app.component`).
- [x] PostgreSQL backup/restore drill (`scripts/db_backup_restore.py`) and Cloudflare Tunnel scripts.

#### Milestone 10: QA & Pilot Acceptance Gate (Completed)
- [x] Walk through full 24-point MVP acceptance checklist (`scripts/verify_acceptance_gate.py`).

#### Milestone 11: Priority 1 — Critical Security & Data-Loss Fixes (Completed)
- [x] **CR-001 & CR-002**: Fix cross-itinerary BOLA in `reorder` and `DELETE` item endpoints.
- [x] **CR-003**: Fix edit-mode itinerary saving dropping days and stops (`ItineraryUpdate`).
- [x] **CR-004 & CR-005**: Reject default JWT secret outside dev/test; require `email_verified` and `is_active` in OAuth.

#### Milestone 12: Priority 2 — Core Reliability & Functional Accuracy (Completed)
- [x] **CR-006**: Implement refresh token rotation in `authInterceptor` and `AuthService.refreshSession()`.
- [x] **CR-007**: Create local calendar date helpers (`toLocalIsoDate`, `parseLocalIsoDate`, `addDaysLocal`).
- [x] **CR-008 & CR-009**: Enforce 25km radius and cumulative daily budget in generator; connect online guests to `/suggest`.
- [x] **CR-010**: Implement `PATCH /api/v1/itineraries/{id}/days/{day_id}/items/{item_id}`.
- [x] **CR-011 & CR-012**: Support route `queryParams` in `MapPage`; scope Bearer token injection to `environment.apiBaseUrl`.

#### Milestone 13: Priority 3 — Maintainability & Code Quality Cleanup (Completed)
- [x] **CR-014, CR-015, CR-016**: Remove dead starter files, fix `ProfilePage` subscription leak, prune unused images, and sync docs.

#### Milestone 14: Priority 4 — Long-Term Performance & Comprehensive E2E Testing (Completed)
- [x] **CR-013 & CR-014**: Key SlowAPI rate limits by `CF-Connecting-IP` / `X-Forwarded-For`; SQL bounding-box pre-filter; rewrite `Project/e2e/app.spec.ts`.

#### Milestone 15: Technical Evaluation & QA/QC Audit Remediation (Completed)
- [x] **DEF-01 to DEF-10 & SEC-01 to SEC-03**: Remove duplicate `PATCH` route handler, enforce chronological stop sorting, restrict production API hostnames allowlist, consolidate `offline-places.data.ts`, fix `getNearbyPlaces()` category mapping, add keyboard accessibility to splash/pins, and automate CI gates.

### New Roadmap Milestones (Milestones 16–22)

#### Milestone 16: Unwired State & Template Parity (`Priority 1 — Quick Wins`)

**Objective**: Surface all computed TypeScript data and modal tabs that are already implemented in component logic but missing from HTML templates, eliminate remaining UTC date parsing discrepancies, and fix mid-session splash screen reloads.

- [ ] **16.1: Render Quick Destination Chips in Suggested Wizard (`UI-01`)**
  - **Target Files**: `Project/src/app/features/itinerary/suggested-wizard/suggested-wizard.page.html`, `suggested-wizard.page.scss`
  - **Implementation**: Below the Destination input box in `viewMode === 'form'`, render a horizontal chip row iterating over `quickDestinations` (`['Bongabon', 'Pantabangan', 'Cabanatuan City', 'Gapan City', 'General Tinio', 'Nueva Ecija']`) bound to `(click)="setDestination(dest)"` with `.active` styling when `wizardForm.get('destination')?.value === dest`.
- [ ] **16.2: Render Budget Summary & Assumptions Box in Suggested Wizard and Itinerary Detail (`UI-02`)**
  - **Target Files**: `Project/src/app/features/itinerary/suggested-wizard/suggested-wizard.page.html`, `Project/src/app/features/itinerary/itinerary-detail/itinerary-detail.page.html`, `Project/src/global.scss`
  - **Implementation**:
    - In `suggested-wizard.page.html` (`viewMode === 'itinerary'`), add the `.verified-budget-card` banner bound to `budgetSummary` (`minTotal`, `maxTotal`, `budgetWarning`, `dailyBudgetTarget`) directly below `.figma-trip-card`.
    - In both `suggested-wizard.page.html` and `itinerary-detail.page.html`, add an expandable/collapsible **Trip Assumptions & Cost Notes** card (`.assumptions-info-box`) rendering `generatedPlan?.assumptions` / `itinerary?.assumptions` whenever the array is non-empty.
- [ ] **16.3: Wire `pickerTab === 'browse'` Inside Custom Builder's Timeline Modal (`UI-03`)**
  - **Target Files**: `Project/src/app/features/itinerary/custom-builder/custom-builder.page.html` (Lines 515–621), `Project/src/global.scss`
  - **Implementation**: Add a 2-segment switcher (`Browse Curated & OSM Places` vs. `Add Off-Grid Custom Venue`) at the top of `<ion-modal [isOpen]="isPickerModalOpen">`. When `pickerTab === 'browse'`, render a search input bound to `pickerSearchQuery` / `(ngModelChange)="onPickerSearchChange($event)"` and a scrollable list of `pickerSearchResults` calling `selectDatabasePlace(place)`. When `pickerTab === 'custom'`, render the existing custom venue form.
- [ ] **16.4: Eliminate Remaining Raw UTC Date Conversions (`UI-04`)**
  - **Target Files**: `Project/src/app/features/itinerary/suggested-wizard/suggested-wizard.page.ts` (Lines 210–211), `Project/src/app/features/itinerary/custom-builder/custom-builder.page.ts` (Lines 154–155, 189–201, 224, 241–244)
  - **Implementation**: Replace `new Date(startStr)` / `new Date(endStr)` in `SuggestedWizardPage.formattedTripDateSubtitle()` with `formatDateRange(startStr, endStr)` from `core/utils/date-input.util.ts`. Replace all `new Date().toISOString().split('T')[0]` calls in `CustomBuilderPage` with `toLocalIsoDate(new Date())` and `addDaysLocal()`.
- [ ] **16.5: Persist Splash Dismissal in `sessionStorage` & Clean Up Unused CSS (`UI-05`)**
  - **Target Files**: `Project/src/app/app.component.ts`, `Project/src/app/app.component.scss`
  - **Implementation**: Check `sessionStorage.getItem('ne_splash_seen_v1')` in `AppComponent.ngOnInit()`. If `'true'`, set `this.showSplashScreen = false` immediately so `window.location.reload()` from `ConnectivityService.retryConnection()` does not replay the 2.8s splash screen. Write `'true'` to `sessionStorage` inside `dismissSplash()`. Remove or bind `.pulse-ring` in `app.component.scss`.

#### Milestone 17: Custom Builder Stop Editing, Day-Move & Schedule Accuracy (`Priority 1 — Core Functional Parity`)

**Objective**: Connect the existing backend stop-update endpoint (`PATCH /api/v1/itineraries/{id}/days/{day_id}/items/{item_id}`) to a full **Edit Scheduled Stop Modal**, enable moving stops across days, capture time/coordinates on custom venues, and fix misleading schedule/budget fallbacks on the detail view.

- [ ] **17.1: Build the Edit Scheduled Stop Modal & Move-to-Day Action (`UI-06`, `UI-07`)**
  - **Target Files**: `Project/src/app/features/itinerary/custom-builder/custom-builder.page.ts`, `custom-builder.page.html`, `custom-builder.page.scss`, `Project/src/app/core/services/itinerary.service.ts`
  - **Implementation**:
    - Add an `Edit` button (`create-outline`) on each `.timeline-stop-card` in `custom-builder.page.html:360`.
    - Create an `<ion-modal [isOpen]="isEditStopModalOpen">` allowing the user to edit `planned_time`, `duration_minutes`, `estimated_cost_min`, `estimated_cost_max`, `notes`, and `targetDayNumber` (select dropdown listing `Day 1` … `Day N` to move the stop between days, fulfilling MVP Plan §6.5 & §12.7).
    - Add `updateItineraryItem(itineraryId, dayId, itemId, payload)` to `ItineraryService` calling `PATCH /api/v1/itineraries/{id}/days/{day_id}/items/{item_id}` when editing an existing server-backed stop, while also updating the in-memory `days` array and `recalculateBudget()`.
- [ ] **17.2: Add Planned Time & Optional Coordinates to Off-Grid Custom Venue Modal (`UI-08`)**
  - **Target Files**: `Project/src/app/features/itinerary/custom-builder/custom-builder.page.ts`, `custom-builder.page.html` (Lines 529–617)
  - **Implementation**: Add `customPlannedTime` (`<input type="time">`) and an optional collapsible `"Pin Coordinates (Lat / Lng)"` two-column input (`customLat`, `customLng` bounded to Nueva Ecija `15.15–16.15`, `120.70–121.40`) to `addCustomStop()`, mapping directly to `BuilderStop.planned_time`, `custom_lat`, and `custom_lng`.
- [ ] **17.3: Fix Misleading Schedule, Budget, and Day Subtitle Fallbacks in `ItineraryDetailPage` (`UI-09`)**
  - **Target Files**: `Project/src/app/features/itinerary/itinerary-detail/itinerary-detail.page.ts` (Lines 169–215)
  - **Implementation**:
    - Update `getTimingTime(stop, index, dayStops)`: if `stop.time` is present, format the start-to-end window using `stop.durationMinutes`; if `stop.time` is absent, either compute cumulative sequential windows starting from `08:30 AM` based on prior stops' `durationMinutes` or return `'Flexible time'` (never hardcode `'12:00 PM - 2:00 PM'` for every stop).
    - Update `formatDailyBudget()`: return `'Flexible Budget'` when `daily_budget` is `0` or null instead of `'₱ 3,000 - ₱ 5,000/day'`.
    - Update `getDaySubtitle(day)`: derive a natural summary from the unique categories of `day.stops` (e.g., `'Nature parks and local dining in Bongabon!'`) with a generic fallback only when `day.stops` is empty.
- [ ] **17.4: Upgrade Custom Builder Browse Stage to Server-Backed Search & Add `CanDeactivate` Route Guard (`UI-10`)**
  - **Target Files**: `Project/src/app/features/itinerary/custom-builder/custom-builder.page.ts` (Lines 415–456), `Project/src/app/app.routes.ts` (Lines 39–49), `Project/src/app/core/guards/unsaved-changes.guard.ts` (new)
  - **Implementation**:
    - In `CustomBuilderPage`, pipe `browseSearchQuery` changes through a 300ms debounced `Subject` calling `placeService.searchPlaces(query, category, municipality, 100)` so all 4,400+ seeded OSM places are searchable during the `browse` stage.
    - Create `unsavedChangesGuard: CanDeactivateFn<CustomBuilderPage>` and attach it to `/custom-builder` and `/custom-builder/:id` in `app.routes.ts`.

#### Milestone 18: Missing Figma Windows — Popular Destinations Catalog, Stop Details & Commute Guide (`Priority 1 — Figma Design Parity`)

**Objective**: Implement the missing screens and sections defined in `Travel Itinerary App.fig`, fix the broken stop-card click action in `SuggestedWizardPage`, and turn static Nearby Places cards into interactive planning tools.

- [ ] **18.1: Build the Popular Destinations ("See All") Window / Modal (`UI-11`)**
  - **Target Files**: `Project/src/app/tabs/home/home.page.ts` (Line 237), `home.page.html`, `home.page.scss`
  - **Implementation**:
    - Match the `Popular Destinations` frame in `Travel Itinerary App.fig` (strings `1460–1650`): header bar with back button (`arrow-back-outline`) and title `"Popular Destinations"`, horizontal municipality filter pills (`All`, `Bongabon`, `Pantabangan`, `Gapan City`, `General Tinio`, `Cabanatuan City`, `Science City of Muñoz`), and a responsive 2-column / vertical card catalog showing destination photo, name, municipality, category badge, opening hours, and honest price badge.
    - Wire `onSeeAll()` on Home to open this full-screen modal/view (`isPopularCatalogOpen = true`), where tapping any card opens the Destination Detail modal.
- [ ] **18.2: Add Stop Detail Modal to `SuggestedWizardPage` & Fix Stop Card Click Binding (`UI-12`)**
  - **Target Files**: `Project/src/app/features/itinerary/suggested-wizard/suggested-wizard.page.html` (Line 189), `suggested-wizard.page.ts` (Line 319)
  - **Implementation**:
    - Change `(click)="openNearbyPlaces(stop)"` on `.figma-stop-card` in `suggested-wizard.page.html:189` to `(click)="openStopDetail(stop)"`.
    - Add the Stop Detail bottom-sheet modal (`isStopModalOpen`, `selectedStop`) to `SuggestedWizardPage` matching `ItineraryDetailPage` so users can inspect stop photos, operating hours, cost breakdown, and Google Maps links before saving a suggested plan.
- [ ] **18.3: Add the Figma "How to Get There?" Commute Guide & `Travel Reminder` Section (`UI-13`)**
  - **Target Files**: `Project/src/app/core/data/commute-guide.data.ts` (new), `Project/src/app/features/itinerary/itinerary-detail/itinerary-detail.page.html`, `Project/src/app/features/itinerary/suggested-wizard/suggested-wizard.page.html`, `Project/src/global.scss`
  - **Implementation**:
    - Create `commute-guide.data.ts` mapping Nueva Ecija municipalities (e.g., Bongabon, Pantabangan, General Tinio, Gapan City, Science City of Muñoz, Gabaldon, Laur) to curated provincial transit hub metadata modeled on `Travel Itinerary App.fig` (`strings 1396–1456` & `1846–1882`):
      - **Transit Mode & Hub**: e.g., `By Bus / UV Express — Departure: Cabanatuan City Central Terminal`
      - **Drop-off Point**: Municipality town proper / landmark or resort junction
      - **Estimated Travel Time**: e.g., `45 mins – 1 hr 30 mins`
      - **Travel Reminder**: Honest advisory box (`information-circle`) noting that schedules and tricycle transfer fares vary by time of day, paired with the one-tap `"Open Directions in Google Maps"` button.
    - Render this section inside the Stop Detail modal in both `SuggestedWizardPage` and `ItineraryDetailPage`.
- [ ] **18.4: Make "Nearby Places" Cards Interactive with "Add to Day" & "Directions" Actions (`UI-14`)**
  - **Target Files**: `Project/src/app/features/itinerary/suggested-wizard/suggested-wizard.page.html` (Lines 231–263), `suggested-wizard.page.ts`, `Project/src/app/features/itinerary/itinerary-detail/itinerary-detail.page.html` (Lines 151–186), `itinerary-detail.page.ts`
  - **Implementation**: Enrich `.figma-nearby-card` items in `viewMode === 'nearby'` with category pills, formatted cost badges, a click handler to view stop details, an `"Open in Maps"` icon button, and an `"+ Add to Day {{ activeDayNumber }}"` button that appends the nearby place to the active day and recalculates the trip budget.
- [ ] **18.5: Fix Home Destination Modal Primary CTA & Widen Popular Carousel Cards (`UI-15`)**
  - **Target Files**: `Project/src/app/tabs/home/home.page.html` (Line 243), `home.page.ts` (Lines 294–308), `home.page.scss` (Line 241)
  - **Implementation**:
    - Change `startPlanningWithDestination(dest)` in `home.page.ts` so the primary CTA (**"Build Itinerary Here"**) navigates to `/suggested-wizard?destination=<municipality>&placeId=<id>` (and pre-fills `SuggestedWizardPage` via `ActivatedRoute.queryParams`), while adding a secondary `"View Pin on Map"` button for `/tabs/map?lat=...&lng=...`.
    - Widen `.dest-card` in `home.page.scss` from `120px` to `160px` and display the destination's category badge and honest cost tag on the card overlay.

#### Milestone 19: Map Discovery, Multi-Select Filter Sheet & Accessible POI List Drawer (`Priority 2 — MVP Map Spec`) (COMPLETED)

**Objective**: Bring `/tabs/map` to 100% compliance with Sections 6.7 and 12.6 of `nueva_ecija_travel_itinerary_mvp_plan.docx` by adding keyword search, multi-select filtering, an accessible list drawer, itinerary integration in the POI bottom sheet, and viewport-bounded queries.

- [x] **19.1: Add Floating Map Search Bar & Multi-Select Filter Bottom Sheet (`UI-16`)**
  - **Target Files**: `Project/src/app/tabs/map/map.page.html`, `map.page.ts`, `map.page.scss`
  - **Implementation**:
    - Add a floating search bar at the top of `/tabs/map` with a `"Filter"` button badge showing the active filter count.
    - Build an `<ion-modal [isOpen]="isFilterSheetOpen">` with multi-select category checkboxes (`selectedCategories: Set<string>`), municipality filter chips, price tier toggles (`Free`, `Budget <= ₱500`, `Mid-Range`), and `Reset` / `Apply Filters` buttons (`MVP Plan §12.6`).
    - Update `PlaceService.getPlaces()` to pass comma-separated categories (`Array.from(selectedCategories).join(',')`), which `GET /api/v1/places` (`backend/app/api/v1/places.py:42`) already supports.
- [x] **19.2: Build Accessible Collapsible POI List Drawer on `/tabs/map` (`UI-16`)**
  - **Target Files**: `Project/src/app/tabs/map/map.page.html`, `map.page.ts`, `map.page.scss`
  - **Implementation**: Add a floating `"List View ({{ places.length }})"` toggle pill at the bottom of the map that opens a scrollable drawer of visible POIs with keyboard navigation, category badges, and one-tap focus (`selectPlace(place)`), satisfying the accessibility requirement in MVP Plan §12.6.
- [x] **19.3: Add "Add to Itinerary" CTA in Map Bottom Sheet & Dynamic Viewport Bounds Querying (`UI-17`)**
  - **Target Files**: `Project/src/app/tabs/map/map.page.html` (Lines 52–95), `map.page.ts` (Lines 90–145)
  - **Implementation**:
    - Add `"Start Trip Here"` and `"Add to Custom Itinerary"` buttons inside the Map POI Bottom Sheet (`map.page.html:90`) alongside the existing `"Get Directions (Google Maps)"` link.
    - Listen to Leaflet `moveend` (debounced by 350ms) and pass `min_lat`, `max_lat`, `min_lng`, `max_lng` from `map.getBounds()` to `placeService.getPlaces()` with `limit: 250` so panning/zooming dynamically loads POIs across all 32 Nueva Ecija municipalities.

#### Milestone 20: Profile Sub-Windows, Notifications & Saved Trips Filtering (`Priority 2 — Account & Navigation UX`) (COMPLETED)

**Objective**: Implement the missing Profile screens from `Travel Itinerary App.fig` (`Edit Profile`, `Settings`, `Log Out` confirmation), turn the Home notification bell into a functional drawer, add text labels to the bottom tab bar, and add filtering to Saved Itineraries.

- [x] **20.1: Build `Edit Profile` Modal & Backend `PATCH /api/v1/auth/me` Endpoint (`UI-18`)**
  - **Target Files**: `backend/app/api/v1/auth.py`, `backend/app/schemas/auth.py`, `Project/src/app/core/services/auth.service.ts`, `Project/src/app/tabs/profile/profile.page.html`, `profile.page.ts`, `profile.page.scss`
  - **Implementation**:
    - Add `PATCH /api/v1/auth/me` in `backend/app/api/v1/auth.py` allowing authenticated users to update `full_name`, `username` (checking case-insensitive uniqueness), and optionally change their password (verifying `current_password` via Argon2id).
    - Add an `"Edit Profile"` button and `<ion-modal [isOpen]="isEditProfileOpen">` on `/tabs/profile` matching the `Edit Profile` frame in `Travel Itinerary App.fig`.
- [x] **20.2: Build `App Settings` Modal & Restore Optional Custom API/Tunnel Override (`UI-18`)**
  - **Target Files**: `Project/src/app/tabs/profile/profile.page.html`, `profile.page.ts`, `Project/src/theme/variables.scss`, `Project/src/global.scss`
  - **Implementation**:
    - Add a `"Settings"` button and modal on `/tabs/profile` (`Travel Itinerary App.fig` frame `1350`) supporting:
      - **Appearance**: Light Mode vs. Dark / High-Contrast Mode toggle (toggling `.ion-palette-dark` on `document.documentElement` using the dark tokens from `Travel Itinerary App.fig` strings `1654–1753`).
      - **Default Trip Preferences**: Default daily budget (`₱500`, `₱1,000`, `₱1,500`, `₱3,000`) pre-filled in wizards.
      - **Storage & Sync**: Button to clear cached offline data or trigger manual guest trip migration.
      - **Advanced Connection Settings**: Input to set or reset a custom backend/tunnel URL (`ConnectivityService.setCustomApiUrl()`), restoring the field-testing capability removed from `app.component` in `v0.16.4`.
- [x] **20.3: Add Logout Confirmation Dialog (`UI-18`)**
  - **Target Files**: `Project/src/app/tabs/profile/profile.page.ts` (Line 59)
  - **Implementation**: Wrap `onLogout()` in an Ionic `AlertController` confirmation dialog (`"Log Out of Your Account?"`). If `unsyncedCount > 0`, warn the user that unsynced guest itineraries remain in local browser storage and offer a `"Sync First"` action alongside `"Log Out Anyway"`.
- [x] **20.4: Build Notifications & Travel Reminders Drawer on Home (`UI-19`)**
  - **Target Files**: `Project/src/app/tabs/home/home.page.html` (Line 18), `home.page.ts` (Line 242), `home.page.scss`
  - **Implementation**: Replace the static toast in `onNotificationClick()` with a slide-up modal or popover displaying upcoming trip reminders (within 7 days), unsynced local guest trip alerts, and curated Nueva Ecija seasonal travel advisories.
- [x] **20.5: Add Visible Text Labels to Bottom Tab Bar & Filtering to Saved Itineraries (`UI-20`)**
  - **Target Files**: `Project/src/app/tabs/tabs.page.html`, `tabs.page.scss`, `Project/src/app/tabs/tabs.routes.ts`, `Project/src/app/tabs/history/history.page.html`, `history.page.ts`, `history.page.scss`
  - **Implementation**:
    - Add `<ion-label>` elements (`Home`, `Map`, `Saved`, `Profile`) inside `tabs.page.html` with `10.5px` semi-bold typography and add `/tabs/saved` as a route alias redirecting to `/tabs/history`.
    - In `HistoryPage`, add a search input, segment filter pills (`All`, `Upcoming`, `Past`, `Suggested`, `Custom`), and render `ItineraryService.calculateBudgetSummary(itin)` (`Est. ₱min – ₱max total`) on each saved itinerary card.

#### Milestone 21: Authentication Completeness & Form Integrity (`Priority 2 — Auth Polish`) (COMPLETED)

**Objective**: Eliminate username collisions and silent data drops during registration, honor `rememberMe` on login, standardize form icons, and provide a structured password recovery modal.

- [x] **21.1: Add Explicit `Username` Field & Preserve `middleInitial` in `SignupPage` (`UI-21`)**
  - **Target Files**: `Project/src/app/features/auth/signup/signup.page.html`, `signup.page.ts` (Lines 45–135)
  - **Implementation**:
    - Add a `username` form control (`Validators.required`, `Validators.minLength(3)`, `Validators.pattern(/^[a-zA-Z0-9_.-]+$/)`) to `signupForm` and `signup.page.html` (`MVP Plan §6.2`), auto-suggesting a sanitized handle from `firstName` + `lastName` only if untouched.
    - Update `onSubmit()` in `signup.page.ts:116` to include `val.middleInitial` when constructing `fullName` (`[firstName, middleInitial ? middleInitial + '.' : '', lastName].filter(Boolean).join(' ')`).
- [x] **21.2: Wire `rememberMe` Storage Scope, Standardize Eye Icons & Add Forgot Password Modal (`UI-22`)**
  - **Target Files**: `Project/src/app/features/auth/login/login.page.ts`, `login.page.html`, `Project/src/app/features/auth/signup/signup.page.html`, `Project/src/app/core/services/auth.service.ts`
  - **Implementation**:
    - Pass `rememberMe` from `LoginPage.onSubmit()` to `AuthService.login()`. Store tokens in `localStorage` when `rememberMe === true` and in `sessionStorage` when `rememberMe === false`.
    - Align password toggle icons across `login.page.html` and `signup.page.html` so both display `eye-outline` when hidden and `eye-off-outline` when visible.
    - Replace the toast-only `onForgotPassword()` in `login.page.ts:112` with a clean recovery modal that validates the user's email and explains pilot account reset options.

#### Milestone 22: Trip Export/Sharing, PWA Caching & Capacitor Packaging (`Priority 3 — Post-MVP & Release`) (COMPLETED)

**Objective**: Complete the remaining Phase 16 roadmap items from `docs/TODO.md`: printable PDF and `.ics` calendar export, Service Worker offline map tile caching, and native Android APK packaging with hardware-backed token storage (`SEC-02`).

- [x] **22.1: Build Itinerary Export & Share Modal on `ItineraryDetailPage` (`UI-23`)**
  - **Target Files**: `Project/src/app/features/itinerary/itinerary-detail/itinerary-detail.page.html`, `itinerary-detail.page.ts`, `Project/src/app/core/utils/itinerary-export.util.ts` (new)
  - **Implementation**:
    - Add a Share/Export button (`share-social-outline`) in the `.figma-header-bar` of `ItineraryDetailPage`.
    - Implement `itinerary-export.util.ts` supporting RFC 5545 `.ics` calendar export, dedicated `@media print` A4 PDF summary view, and one-tap clipboard text summary copy.
- [x] **22.2: Configure PWA Service Worker & Offline Map Tile Pre-Caching (`UI-24`)**
  - **Target Files**: `Project/ngsw-config.json`, `Project/angular.json`
  - **Implementation**: Configure Angular Service Worker (`@angular/service-worker`) with `dataGroups` caching `/api/v1/municipalities`, `/api/v1/places`, and OpenStreetMap tile requests within Nueva Ecija zoom levels `10–14`.
- [x] **22.3: Scaffold Capacitor Android Project & Secure Token Storage (`UI-24`, `SEC-02`)**
  - **Target Files**: `Project/capacitor.config.ts`, `Project/src/app/core/services/auth.service.ts`
  - **Implementation**: Scaffold the Android target (`npx cap add android`) and abstract token storage behind a `SecureTokenStorageService` using `@capacitor-community/secure-storage-plugin` on native devices and `localStorage`/`sessionStorage` on web (`ADR-010`).
- [x] **22.4: Full Regression & E2E Verification Suite**
  - **Target Files**: `Project/e2e/app.spec.ts`, `scripts/verify_acceptance_gate.py`
  - **Implementation**: Extend `Project/e2e/app.spec.ts` and `verify_acceptance_gate.py` to test the Popular Destinations catalog, Stop Detail + Commute Guide modal, Custom Builder Edit Stop modal, Map multi-select filter sheet, and Profile sub-windows.

#### Milestone 23: UI Layout Alignment, CI Robustness & Native Tooling (COMPLETED)

**Objective**: Align Saved Itineraries and Trip Details views with user layout specifications, eliminate infinite loading spinners, decouple native plugins for CI, and isolate Gradle conflicts.

- [x] **23.1: Saved Itineraries & Trip Details Layout Alignment**
  - **Target Files**: `history.page.html`, `history.page.scss`, `itinerary-detail.page.html`, `itinerary-detail.page.scss`
  - **Implementation**: Redesigned Saved Itineraries cards with pill badges, trash button, location pin, and divider; redesigned Trip Details view with day cards, schedule time, duration, cost estimation, description, and notes; built In-Place Trip Editor (reorder, delete, move across days, add activity); added synchronous cached retrieval (`getCachedItineraryById`) and 4s timeout fallback.
- [x] **23.2: Headless CI Dependency Injection Token**
  - **Target Files**: `Project/src/app/core/services/secure-token-storage.service.ts`
  - **Implementation**: Introduced `SECURE_STORAGE_PLUGIN` Angular `InjectionToken`, resolving esbuild mock decoupling errors during headless Linux CI runs.
- [x] **23.3: VS Code Java 25 & Gradle Conflict Isolation**
  - **Target Files**: `.vscode/settings.json`, `Project/.vscode/settings.json`
  - **Implementation**: Added `java.import.exclusions` for `**/Project/android/**` suppressing Gradle 9.6 incompatibility warnings.

#### Milestone 24: Pilot Field Testing, Cloudflare Edge & Playwright E2E (COMPLETED)

**Objective**: Verify live production endpoints, synchronize native Capacitor Android plugins, configure Cloudflare edge caching, and execute headless browser E2E journeys.

- [x] **24.1: Live Production Smoke Testing & Edge Caching**
  - **Target Files**: `cloudflare-worker/worker.js`, live GitHub Pages deployment
  - **Implementation**: Probed live GitHub Pages deployment (HTTP 200) and Cloudflare Worker status (HTTP 200); added 24h KV edge caching (`env.TUNNEL_KV`) for `/api/v1/places/` and `/compute-day-route` with `X-Edge-Cache: HIT` fallback.
- [x] **24.2: Android Device Installation & Native Packaging Sync**
  - **Target Files**: `Project/android/`
  - **Implementation**: Synchronized web assets and 6 Capacitor Android plugins (`@capacitor/app@8.1.2`, `@capacitor/geolocation@8.2.4`, `@capacitor/haptics@8.0.2`, `@capacitor/keyboard@8.0.6`, `@capacitor/status-bar@8.0.4`, and `capacitor-secure-storage-plugin@0.13.0`) via `npx cap sync android`.
- [x] **24.3: Automated Playwright Browser Journey Execution**
  - **Target Files**: `Project/e2e/app.spec.ts`
  - **Implementation**: Installed Playwright Chromium v1248 binaries; executed 5 full browser journey tests passing 100% in 11.9s with cold-start splash bypass via `sessionStorage`.

#### Milestone 25: Enterprise GIS Upgrade, Live Google Places Discovery & Active Routing (COMPLETED)

**Objective**: Implement production-grade GIS architecture, live Google Places proxying, turn-by-turn road routing, Bayesian quality ranking, active geolocation tracking, and unified modal architecture.

- [x] **25.1: Foundation, Schemas & Proxy Services**
  - **Target Files**: `backend/app/models/entities.py`, `backend/alembic/versions/0002_google_places_and_routing.py`, `backend/app/services/google_maps_service.py`, `backend/app/api/v1/places.py`, `backend/app/api/v1/itineraries.py`
  - **Implementation**: Created reversible migration 0002, expanded `Place`/`ItineraryDay`/`ItineraryItem` models, added `GeospatialCache` with `JsonType`, implemented `GoogleMapsService` with Places New & Routes v2 APIs and OSRM fallback, and added upsert-on-save foreign key resolver.
- [x] **25.2: Live Discovery & Recommendation Engine Upgrade**
  - **Target Files**: `backend/app/algorithms/itinerary_generator.py`, `Project/src/app/core/utils/polyline.util.ts`, `Project/src/app/core/services/itinerary.service.ts`
  - **Implementation**: Bayesian quality scoring, opening hours gating (`is_open_during_slot`), 2-Opt TSP permutation, dynamic travel-time pacing, polyline utilities (`encodePolyline`, `decodePolyline`), and offline generator destination matching fixes.
- [x] **25.3: Active Routing & Geolocation Tracking**
  - **Target Files**: `Project/android/app/src/main/AndroidManifest.xml`, `Project/src/app/core/services/route-tracking.service.ts`, `Project/src/app/tabs/map/map.page.ts`, `Project/src/app/features/itinerary/itinerary-detail/itinerary-detail.page.ts`
  - **Implementation**: Configured Capacitor Geolocation v8 permissions, implemented `RouteTrackingService` (10m movement throttle, 100m off-route detection, 50m stop arrival threshold), unclustered Leaflet route layers, navigation HUD banner, embedded detail route preview map, and inter-stop leg badges.
- [x] **25.4: Unified PlaceDetailSheetComponent & UI Polish**
  - **Target Files**: `Project/src/app/shared/components/place-detail-sheet/`, `Project/src/app/features/itinerary/suggested-wizard/`, `Project/src/app/features/itinerary/itinerary-detail/`
  - **Implementation**: Consolidated duplicate modal markup across all pages with `<app-place-detail-sheet>`, added traveler annotations and public transit commute guide, added Travel Mode and Minimum Rating controls to Suggested Wizard, and added inter-stop road travel leg connectors.

#### Milestone 26: Map-Routing Architecture Refactoring & Geo-Spatial Caching (COMPLETED)
- [x] **26.1: Public OSRM Road Routing & Geodesic Spline Arcs**: Zero-cost arterial routing via OSRM with 2.5s AbortController and geodesic spline fallback.
- [x] **26.2: OpenStreetMap Raster Tiles Standard**: Switched to OpenStreetMap raster tiles, eliminating watermark notices.
- [x] **26.3: Geospatial Caching Layer**: In-database route and POI caching via `geospatial_cache` table.

#### Milestone 27: Road-Routing Overhaul, Commute Engine & True Geolocation (COMPLETED)
- [x] **27.1: True GPS Geolocation**: High-accuracy `watchPosition` tracking with 10m movement throttle and pulsing beacon.
- [x] **27.2: Leg-Aware Provincial Commute Engine**: Integrated walking, tricycle, and highway bus corridor commute pills (`commute-guide.data.ts`).
- [x] **27.3: URL Query Parameter State**: Two-way filter synchronization to browser URL parameters.

#### Milestone 28: Live Full-Map Routing, Marker Clustering & In-App Navigation (COMPLETED)
- [x] **28.1: Leaflet MarkerCluster Production Hardening**: Guarded `window.L` with non-destructive property descriptor setter in `main.ts` (`MAP-01`).
- [x] **28.2: In-App Turn Navigation HUD**: Real-time stop guidance with off-route recalculation.
- [x] **28.3: Stop Detail Sheet Parity**: Dynamic price propagation and WCAG 2.2 focus accessibility.

#### Milestone 29: Wizard Offline Engine & Custom Builder Deep Alignment (COMPLETED)
- [x] **29.1: Offline Suggested Generator Slicing**: Dynamic destination matching and budget substitutions in `ItineraryService`.
- [x] **29.2: 0ms Offline Short-Circuit**: Immediate fallback when `isHostOfflineSnapshot` is true.
- [x] **29.3: Router State Handoff**: Draft persistence via router navigation state without duplicate saves.

#### Milestone 30: Live-Server Map & Suggested Itinerary Routing Upgrade (COMPLETED)
- [x] **30.1: False-Offline Banner Clearance**: Auto-reset on tile load and 3-strike threshold (`GAP-04`).
- [x] **30.2: Isolated Route Focus Mode**: `isFollowRouteMode` on `MapPage` isolating active route and hiding background markers (`GAP-02`).
- [x] **30.3: Pre-Save Draft Persistence**: `activeDraftItinerary$` caching across map handoffs (`GAP-03`).
- [x] **30.4: Spatial Indexing & Canvas Clustering**: `preferCanvas: true` and composite spatial index on `Place` model.

#### Milestone 31: Suggested & Custom Itinerary Preference Engine, Destination Autofill & Catalog Browse Upgrade (COMPLETED)
- [x] **31.1: Reusable Destination Autocomplete Combobox**: `<app-destination-autocomplete>` covering 32 LGUs and landmarks with NFD diacritic folding (`PREF-01`).
- [x] **31.2: Canonical Preference Mapping & Pacing Engine**: `PREFERENCE_CATEGORY_MAP`, sequential rolling time windows, midday dining anchor, and coordinate deduplication (`PREF-02` to `PREF-06`).
- [x] **31.3: Custom Builder Full-Catalog Ingestion**: Replaced 17-place cap with 2,673 POI catalog query and `✨ Recommended for You` tab (`CUST-01` to `CUST-03`).

#### Milestone 32: Full-Website QA Remediation, Connectivity Hardening & Polish (COMPLETED)
- [x] **32.1: Resilient Connectivity Circuit Breaker**: Consecutive error threshold ($\ge 2$) and async host health probes (`QA-01`).
- [x] **32.2: Additive In-Memory POI Cache Merging**: `mergePlacesIntoCache` in `PlaceService` and `allLoadedPlaces` in `MapPage` (`QA-02`).
- [x] **32.3: Dynamic API Base URL**: Injected `activeApiBaseUrl` across all HTTP services (`QA-08`).
- [x] **32.4: App-Boot Theme Hydration & Settings Sync**: Hydrated dark mode on boot and default budget into wizards (`QA-14C`).
- [x] **32.5: Timezone-Safe Date Arithmetic**: Replaced UTC date parsing with `toLocalIsoDate` (`QA-14B`).

#### Milestone 33: Exhaustive QA/QC Audit Assessment & Production Polish (COMPLETED)
- [x] **33.1: Audit Defect Ingestion**: Ingested and mapped 75 test cases and 14 defects from `itinerary_app_exhaustive_qa_qc_report.pdf`.
- [x] **33.2: Production SEO Meta & Open Graph Sharing Tags (`BUG-14` / `TASK-12`)**: Configured descriptive page title, meta description, Open Graph tags, Twitter card tags, theme color, and pre-boot dark theme hydration in `Project/src/index.html`.
- [x] **33.3: Route Alias Redirects (`BUG-14` / `TASK-12`)**: Implemented `/tabs/saved` -> `history` in `tabs.routes.ts` and `/saved` -> `/tabs/history` in `app.routes.ts`.
- [x] **33.4: Automated Test Gate**: Authored `tabs.routes.spec.ts` bringing total unit test coverage to 296 tests across 29 test files (100% passing).

#### Milestone 34: Figma-Aligned Profile Tab Redesign & Comprehensive Traveler Experience (COMPLETED)
- [x] **34.1: Figma Design Extraction**: Extracted Kiwi compressed nodes and frame metadata from `Travel Itinerary App.fig`, mapping Profile, Edit Profile, Settings, Help & Support, About, and Log Out frames.
- [x] **34.2: Anti-Generic Profile Main Screen**: Rebuilt Profile tab with high-fidelity identity card, circular avatar, traveler name, verified badge, Edit Profile pill, and 5 structured menu items (Favorites, Settings, Help & Support, About, Log Out).
- [x] **34.3: Edit Profile Sub-Window**: Implemented modal with photo management, first name, middle initial, last name, username, email, phone number, birthday, gender, and password change fields.
- [x] **34.4: Settings Sub-Window**: Implemented modal with account summary, theme switcher (Light/Dark), language selector, notifications toggle, daily budget presets, connection status, and cache clearing.
- [x] **34.5: Help & Support & About Modals**: Implemented Nueva Ecija travel FAQs, emergency hotlines, provincial transit guidance, and application credits/attribution.
- [x] **34.6: Figma-Styled Log Out Modal**: Implemented confirmation dialog matching Figma specifications with unsynced local trip safety guard.
- [x] **34.7: Comprehensive Test Suite & Quality Gates**: Expanded `profile.page.spec.ts` (17 tests passing) bringing unit test coverage to 304 tests across 29 test files, and verified Vitest, Typecheck, ESLint, Angular build, and Capacitor sync.

#### Milestone 35: Exact Figma Screenshot Layout Realignment & After Log Out Screen (COMPLETED)
- [x] **35.1: High-Resolution Figma Asset Extraction**: Extracted genuine selfie avatar (`pattranite_avatar.jpg`), skyscraper photo in organic blob (`logout_skyscrapers_blob.png`), and cityscape silhouette (`logout_cityscape_silhouette.png`) from Kiwi binary canvas.
- [x] **35.2: Profile Main Screen Layout & Iconography Alignment**: Rebuilt layout with left circular avatar, right Name + Email + "Edit Profile" pill button, and a single rounded container card enclosing 5 rows (Settings, Favorites, Help & Support, About, Log Out) without chevrons.
- [x] **35.3: Settings Sub-Window Alignment**: Rebuilt with blue back arrow, bold title `Settings`, and single card enclosing 6 rows (Account Information, Notifications with iOS toggle, Privacy & Security, Language "English", App Appearance "Light", and Clear Cache).
- [x] **35.4: Log Out Confirmation Modal Alignment**: Rebuilt with centered floating white card, top triple-dot handle indicator, prominent blue exit door icon, title, description, and two stacked full-width solid blue buttons (`Log Out` and `Cancel`).
- [x] **35.5: Edit Profile Sub-Window Alignment**: Rebuilt with blue back arrow, centered circular avatar with camera overlay badge and `Change Photo` pill, 7 form fields in exact Figma order, and solid blue `Save Changes` button.
- [x] **35.6: After Log Out Screen Implementation**: Implemented in `WelcomePage` with airplane logo + "Trip mo, trip ko", skyscraper photography in organic smooth wavy blob mask with blue border, heading, description, two stacked solid blue buttons (`Continue as Guest` and `Log In`), and cityscape silhouette.
- [x] **35.7: Unit Testing & Full Verification Suite**: Created `welcome.page.spec.ts` and enhanced `profile.page.spec.ts`, reaching **310 total passing unit tests across 30 test files**, strict TypeScript typecheck (code 0), clean Angular production build (code 0), and Capacitor Android sync (code 0).

#### Milestone 36: Comprehensive QA/QC Audit Remediation & Production Release Gate (COMPLETED)
- [x] **36.1: Splash Screen Freeze Remediation (`QA-BUG-CRIT-01`)**: Injected `ChangeDetectorRef` in `AppComponent` and invoked `this.cdr.detectChanges()` in `dismissSplash()` within the 500ms fade callback to ensure immediate DOM unmounting on first visits and clean sessions.
- [x] **36.2: Change Detection & Async Reactivity (`QA-ARCH-DEF-01`)**: Registered `provideZoneChangeDetection({ eventCoalescing: true })` in `main.ts` and injected `ChangeDetectorRef` in `HomePage` with `markForCheck()` on search debouncing and featured places loading.
- [x] **36.3: Log Out Modal Pointer Interception Fix (`QA-UI-DEF-01`)**: Removed `display: flex; align-items: center; justify-content: center;` from `.figma-logout-modal` in `profile.page.scss`, setting `--height: auto;` so Ionic's `.overlay-hidden { display: none; }` unmounts the modal and restores clicks to the Log Out row.
- [x] **36.4: Acceptance Gate Check #15 Alignment (`QA-AUDIT-DEF-01`)**: Updated `scripts/verify_acceptance_gate.py` Check #15 to inspect `place-detail-sheet.component.ts` and verify `'Admission: Check on arrival'`, achieving **24/24 checks passed (100.0%)**.
- [x] **36.5: Automated Lint & Code Quality Guard (`QA-LINT-DEF-01`)**: Preserved Angular runtime dependency injection tokens against accidental `import type` erasure from aggressive linters, guaranteeing clean runtime DI behavior.
- [x] **36.6: Comprehensive Test Verification & Quality Gates**: Verified 310/310 passing unit tests across 30 test files, clean Angular production build (`ng build`), 24/24 Acceptance Gate pass rate, and Capacitor Android sync.

#### Milestone 37: Profile Persona Pre-Set, In-Page Settings & Sub-Views, Logout Parity, Dark Mode Fix & Dedicated Favorites Tab (COMPLETED)
- [x] **37.1: Authenticated Profile Persona Pre-Set**: Ensured logging in pre-populates traveler persona with Pattranite Limpatiyakorn (`assets/images/pattranite_avatar.jpg`, `Pattranite Limpatiyakorn`, `@loverrukk@gmail.com`) with offline/demo fallback in `AuthService.login()`.
- [x] **37.2: In-Page Settings, Help & Support, About Sub-Views**: Implemented in-page sub-views (`viewMode: 'profile' | 'settings' | 'help' | 'about'`) inside `ProfilePage`, rendering the exact single rounded card with blue icons and keeping the bottom tab bar visible matching Image 1 (`media_1794305628697_56ce48c5.png`).
- [x] **37.3: Before Logout Modal & After Logout Screen Parity**: Implemented Before Logout floating dialog with triple-dot handle, blue door exit SVG icon, bold title, description, and stacked blue buttons matching Image 2 (`media_1794305642780_d5248c99.png`), and verified After Logout screen matches Image 3 (`media_1794305651445_190286a1.png`).
- [x] **37.4: Dark Mode Color Inversion Bug Fix**: Fixed dark mode color styling across `global.scss` and component stylesheets so dark mode turns backgrounds to dark slate (`#0b1120`/`#0f172a`), surfaces/cards to `#1e293b`, borders to `#334155`, and text to crisp `#f8fafc`/`#94a3b8`, permanently eliminating the white-on-white bug.
- [x] **37.5: Dedicated Favorites Tab & Place Bookmarking**: Built `FavoritesService` under `ne_favorite_places_v1`, added heart toggle button to `PlaceDetailSheetComponent`, created `FavoritesPage` at `/tabs/favorites` with search, category filtering, and venue cards, and added `Favorites` tab button in `tabs.page.html`.
- [x] **37.6: Full Verification Gate**: Vitest unit tests (32/32 suites, 321/321 tests passed, 100%), Angular production build (exit code 0, 0 budget violations, <16 kB component styles), and 24-point acceptance gate (24/24 checks passed, 100.0%).

#### Milestone 38: Edit Profile Screen Formatting, Photo Upload Fix & Blank Avatar Placeholder (COMPLETED)
- [x] **38.1: Blank Avatar Placeholder for Signed-In Individuals**: Configured `default_avatar_placeholder.png` from user upload as the default avatar for signed-in travelers without custom photos, replacing hardcoded portrait images.
- [x] **38.2: In-Page Edit Profile Subview**: Implemented `viewMode: 'edit'` in `ProfilePage` matching Image 1 (`media_1794313719867_c04de25f.png`) with `← Edit Profile`, centered circular avatar with camera overlay, `Change Photo` blue pill, 7 form fields, and `Save Changes` button while keeping the bottom tab bar visible.
- [x] **38.3: Profile Picture Upload Reactivity Fix**: Resolved `FileReader.onload` async event decoupling in Angular zoneless change detection via explicit `cdr.markForCheck()`, validating file MIME types and updating avatar preview immediately upon file selection.
- [x] **38.4: Full Test & Build Verification**: Vitest unit tests (32/32 suites, 322/322 tests passed, 100%), Angular production build (`ng build --base-href /Itinerary-App/` exit code 0, 0 budget violations, <16 kB component styles), and Capacitor Android sync (exit code 0, 6 plugins synced).

#### Milestone 39: Favorites Profile-Only Migration (Bottom Navigation De-Clutter) (COMPLETED)
- [x] **39.1: Bottom Navigation Bar De-Cluttering**: Removed the 5th `favorites` tab button from `tabs.page.html`, restoring the 4 canonical bottom navigation tabs (`Home`, `Map`, `Saved`, `Profile`) matching Figma design.
- [x] **39.2: Profile In-Page Favorites Subview**: Migrated full Favorites management into an in-page subview within `ProfilePage` (`viewMode: 'favorites'`) accessible exclusively through the Profile tab menu card, retaining the visible 4-tab bottom navigation bar.
- [x] **39.3: Route Harmonization**: Redirected `/tabs/favorites` and `/favorites` to the Profile tab.
- [x] **39.4: Full Test & Build Quality Gate**: Vitest unit tests (32/32 test suites passed, 322/322 tests passed, 100.0%), clean production Angular build (0 budget violations, <16 kB component styles), and Capacitor Android sync (exit code 0, 6 plugins synchronized).

#### Milestone 40: Critical Remediation Suite (System Review Audit Findings) (COMPLETED)
- [x] **40.1: Zoneless Change Detection Reactivity in Suggested Wizard**: Injected `ChangeDetectorRef` and invoked `this.cdr.markForCheck()` across all async lifecycle, observable callbacks, and user-action paths in `suggested-wizard.page.ts`, eliminating the UI freeze.
- [x] **40.2: Transparent Offline Auth & Explicit Demo Mode**: Removed silent demo usurpation in `auth.service.ts` so offline/network errors are truthfully reported; added explicit `loginDemo()` and an `[Explore Demo Account (Pattranite Persona)]` button on the login screen with dark mode support.
- [x] **40.3: Elimination of Foreign Persona Defaults on Philippine Accounts**: Restricted foreign persona metadata strictly to demo mode (`usr_pattranite_demo_01`); real registered accounts retain their names and blank extra fields with Philippine placeholder hints (`+63 9XX XXX XXXX`). Fixed the form-wiping bug on password visibility toggle.
- [x] **40.4: Active Map Navigation Preservation**: Guarded `tabs.page.ts:onMapTabClicked()` so active GPS navigation (`followRoute=true` / `routeItineraryId`) is not wiped out when tapping the Map bottom navigation tab.
- [x] **40.5: Day-Trip Lodging Exclusion & Questionnaire Pacing**: Excluded overnight hotel accommodations on single-day itineraries (`totalDays === 1`) in both backend algorithm (`itinerary_generator.py`) and frontend offline generator (`itinerary.service.ts`). Dynamically scaled stops per day based on questionnaire pacing (`relaxed`: 2, `moderate`: 3, `fast`: 4).
- [x] **40.6: Free Venues (₱0) Accounting**: Formatted verified zero-cost attractions as "Free Admission" instead of "Price not listed" in `itinerary-detail.page.ts`.
- [x] **40.7: One-Tap Post-Logout Guest Access**: Directed travelers clicking "Continue as Guest" after logout straight into `/tabs/home` without the redundant tutorial interstitial in `welcome.page.ts`.
- [x] **40.8: Playwright E2E Hash Routing Alignment**: Updated direct navigation URLs in `Project/e2e/app.spec.ts` to use hash location routing (`/#/...`).
- [x] **40.9: Quality Gates & Verification**: 100% test pass rate achieved across Vitest (32/32 suites, 327/327 tests), clean Angular production build (0 budget violations, <16 kB component styles), and clean Capacitor sync.
