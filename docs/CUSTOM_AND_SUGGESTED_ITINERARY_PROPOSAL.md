# Custom & Suggested Itinerary Workflows: End-to-End Analysis & Proposal

**Target System**: Nueva Ecija Travel Itinerary App ("Trip mo, trip ko")  
**Audit Target**: Live Production Deployment at [edselrenz.github.io/Itinerary-App/tabs/home](https://edselrenz.github.io/Itinerary-App/tabs/home) & Local Monorepo (`Project/` Angular 22 / Ionic 9 / Capacitor 8, `backend/` FastAPI / SQLAlchemy 2.0)  
**Document Source**: `custom_and_suggested_itinerary_proposal.pdf`  
**Date Analyzed**: November 6, 2026  
**Status**: Documented & Staged for Phased Implementation (Phase 29)

---

## 1. Executive Summary: 11 Use Cases Audited Across Both Planning Engines

An exhaustive static code audit and interactive testing across [https://edselrenz.github.io/Itinerary-App/tabs/home](https://edselrenz.github.io/Itinerary-App/tabs/home) evaluated all 11 use cases spanning both the **Suggested Itinerary Wizard** (`/suggested-wizard`) and the **Custom Itinerary Builder** (`/custom-builder`, `/custom-builder/:id`, and `/itinerary/:id`).

While both workflows share a clean 3-stage conceptual progression (Questionnaire $\rightarrow$ Place Selection / Clustering $\rightarrow$ Day Timeline & Persistence) and implement honest null-cost budget rollups via `ItineraryService.calculateBudgetSummary()`, live testing and code tracing exposed **12 concrete functional and UI/UX defects**—including **two critical data-corruption bugs** in Guest/Offline mode:

1. **Critical Metadata Loss When Saving Custom Itineraries in Guest/Offline Mode (`C-BUG-06`)**:
   - In [`custom-builder.page.ts:806–826, 1114–1126`](file:///c:/Users/Edward/Desktop/CaseStudy/Project/src/app/features/itinerary/custom-builder/custom-builder.page.ts#L1114-L1126), `addPlaceStop()` and `saveItinerary()` omit `custom_title: it.name` and `place` from the save payload.
   - When saved via `GuestStorageService` (`createGuestItinerary()` at [`itinerary.service.ts:421–435`](file:///c:/Users/Edward/Desktop/CaseStudy/Project/src/app/core/services/itinerary.service.ts#L421-L435)), every catalog stop is persisted with `place: null` and `custom_title: undefined`.
   - On `/itinerary/:id`, every stop in a saved Custom Itinerary renders as generic *"Destination Stop — Explore the river and limestone formations..."* with a fabricated ₱200 fee and zero coordinates.
2. **Dead `matchedPool` Variable in Offline Suggested Generator (`S-BUG-03`, Critical)**:
   - In [`itinerary.service.ts:753–796`](file:///c:/Users/Edward/Desktop/CaseStudy/Project/src/app/core/services/itinerary.service.ts#L753-L796), `generateOfflineSuggestedItinerary()` filters and sorts `matchedPool` by the user's chosen municipality and preferences on lines 753–771, but **never reads `matchedPool` afterwards**.
   - Selecting Pantabangan, Cabanatuan City, Gapan City, or General Tinio offline sets `isProvincialOrBongabon = false` and falls back to `[curatedPool[0], curatedPool[1], curatedPool[2]]`, scheduling the exact same 3 Bongabon venues on every single day of the trip.
3. **Unconditional 4-Second Offline Network Stall on Suggested Generation (`S-BUG-04`, High)**:
   - Even when `ConnectivityService.isHostOffline$` is already true, `ItineraryService.suggestItinerary()` fires a live HTTP POST and waits for a 4,000 ms timeout before invoking the local generator, hanging the *"Clustering recommendations..."* spinner in offline sessions.
4. **Divergent Dual Editors & Missing Form Controls (`C-BUG-01` to `C-BUG-05`, High)**:
   - Step 1 of `CustomBuilderPage` omits the Trip Title input, quick destination chips, and budget presets; Step 2's category filter drops 7 of the 16 canonical POI categories; changing dates in Step 3's settings card fails to sync the days array; and `ItineraryDetailPage` introduces a competing in-place editor that orphans `/custom-builder/:id` and collapses min/max cost ranges into a single number.

---

## 2. Complete Use-Case Analysis: Suggested vs. Custom Itinerary

The table below documents all 11 use cases across both workflows, detailing the execution path in code, verified live behavior, and specific defects uncovered:

| Use Case | Workflow Stage & Code Path | How It Works (Live & Code Trace) | Identified Bugs & Edge Cases |
| :--- | :--- | :--- | :--- |
| **`UC-S1`**<br>Suggested Entry & Deep-Link | `HomePage` / `MapPage` $\rightarrow$ `/suggested-wizard?destination=...&placeId=...` | Launched from Home's Suggested Itinerary card, Home's *Build Itinerary Here* modal CTA, or Map's *Start Trip Here* bottom-sheet CTA. | **`S-BUG-01`**: `suggested-wizard.page.ts:171` reads `params['destination']` but ignores `params['placeId']`, never anchoring or guaranteeing the clicked POI in Day 1 of the generated plan. |
| **`UC-S2`**<br>Suggested Form & Date Modal | `SuggestedWizardPage`<br>(`viewMode === 'form'`, L32–132) | Collects destination (6 quick chips), `start_date`/`end_date` via pop-up modal (2D1N, 3D2N, 4D3N, 1 Week), `daily_budget` (4 presets), and 5 preference pills. | **`S-BUG-02`**: `openDatePicker()` (L190) and `setPresetDuration()` (L207) still use UTC `new Date(str).toISOString()` instead of `parseLocalIsoDate()`, risking off-by-one date shifts in UTC+8. |
| **`UC-S3`**<br>Suggested Generation Engine | `ItineraryService.suggestItinerary()` $\rightarrow$ `itinerary_generator.py` or `generateOfflineSuggestedItinerary()` | **Online**: SQL bbox pre-filter + Haversine scoring (25 km radius, +40 pref, +20 featured, -25 dup cat, cumulative budget) + chronological sort.<br>**Offline**: local TypeScript generator. | **`S-BUG-03` (Critical)**: Offline `matchedPool` (L753–771) is never used; non-Bongabon towns repeat the same 3 Bongabon stops on every single day.<br>**`S-BUG-04`**: Waits 4s for HTTP timeout even when offline banner is active. |
| **`UC-S4`**<br>Suggested Preview & Stop Modal | `SuggestedWizardPage`<br>(`viewMode === 'itinerary'`, L134–285) | Renders Trip Card, Verified Estimated Costs, collapsible Trip Assumptions insight cards, segmented Day capsule bar, photo stop cards, and Stop Detail modal. | No route map or polyline preview in Step 2; Day 2 & Day 3 offline presets zig-zag 176.2 km across the province (General Tinio $\rightarrow$ Pantabangan $\rightarrow$ Gapan City). |
| **`UC-S5`**<br>Suggested Nearby Essentials | `SuggestedWizardPage`<br>(`viewMode === 'nearby'`, L287–360) | Toggles 3-tab view (Restaurants, Hospital & Pharmacies, Stores) filtered by active day's municipality; *+ Add to Day X* appends stop. | **`S-BUG-05`**: `addNearbyPlaceToActiveDay()` (L422) hardcodes 12:00 PM, Bongabon coords (`15.63, 121.14`), and null cost, and appends after overnight stays without re-sorting. |
| **`UC-S6`**<br>Save vs. Customize Handoff | `acceptAndSave()` & `customizeInBuilder()` (L475–555) | **Accept & Save**: persists trip and routes to `/tabs/home`.<br>**Customize in Builder**: saves trip and routes to `/custom-builder/:id`. | **`S-BUG-06`**: `customizeInBuilder()` writes a permanent copy to storage *before* opening the builder; cancelling in the builder leaves an unwanted duplicate saved trip. |
| **`UC-C1`**<br>Custom Step 1 Setup Form | `CustomBuilderPage`<br>(`activeView === 'form'`, L48–137) | Collects Destination, Travel Dates (via pop-up modal), Daily Budget, and Preferences, then calls `proceedToBuilder()` to sync days array. | **`C-BUG-01`**: Missing Trip Title input field in Step 1 HTML (defaults silently to "Nueva Ecija Getaway"); missing quick destination & budget chips; button mislabeled *"Find Itinerary"*. |
| **`UC-C2`**<br>Custom Step 2 Browse & Add | `CustomBuilderPage`<br>(`activeView === 'browse'`, L138–266) | Target day selector chips (Day 1 (N), +), 300ms debounced server/offline search, 5 category pills, 2-col place grid with Add / Added toggle. | **`C-BUG-02`**: `catMap` (L697) maps only 9 of 16 categories, dropping 7 categories.<br>**`C-BUG-03`**: Ignores Step 1 destination and overwrites multi-preferences with a single tab.<br>**`C-BUG-04`**: Cards lack detail modal inspection. |
| **`UC-C3`**<br>Custom Step 3 Timeline & Edit | `CustomBuilderPage`<br>(`activeView === 'timeline'`, L268–475) | Trip settings card, budget summary, day tabs, numbered stop timeline with $\uparrow/\downarrow$ reorder, Edit Scheduled Stop modal (time, dur, cost, notes, move-to-day), and delete confirmation. | **`C-BUG-05`**: Editing `start_date` / `end_date` in the timeline settings card does not resize `this.days` or update `day.travel_date`.<br>**`C-BUG-06` (Critical)**: Omitting `custom_title: it.name` and `place` turns saved guest stops into generic *"Destination Stop"*. |
| **`UC-C4`**<br>Place Picker & Off-Grid Venue | `CustomBuilderPage`<br>(`isPlacePickerOpen`, L562–835) | 2-tab modal: Browse Places (live search) and Off-Grid Venue (custom title, address, min/max cost, planned time, optional NE lat/lng bounds check). | Clicking *"Add Off-Grid Custom Venue"* opens `pickerTab = 'browse'` instead of `'custom'` (L735); `[disabled]="isPlaceInActiveDay(id)"` makes duplicate confirmation alert dead code. |
| **`UC-C5`**<br>Saved Trip Editing & Guards | `pendingChangesGuard`;<br>`/custom-builder/:id` vs. `/itinerary/:id` | `CustomBuilderPage` enforces `canDeactivate` guard. `ItineraryDetailPage` provides an inline `isEditMode` form. | **Competing dual editors**: `/itinerary/:id` inline editor orphans `/custom-builder/:id`, lacks `canDeactivate` guard, has no catalog picker, and collapses min/max cost ranges into one number. |

---

## 3. Root-Cause Code Evidence for the Two Critical Data-Corruption Bugs

### 3.1 Critical Bug `C-BUG-06`: Why Saved Custom Itineraries Lose All Place Names, Photos & Coordinates
When a user adds a catalog destination in `CustomBuilderPage.addPlaceStop()` (`custom-builder.page.ts:806–826`), the stop stores `place_id: place.id` and `name: place.name`, leaving `custom_title` undefined. When `saveItinerary()` (lines 1114–1126) serializes the payload, it drops `it.name` and `place`:

```typescript
// 1. custom-builder.page.ts (Lines 1114–1126) — Drops it.name and place object!
items: d.items.map((it) => ({
  place_id: it.place_id,
  custom_title: it.custom_title, // undefined for all catalog places!
  custom_lat: it.custom_lat,     // undefined for all catalog places!
  custom_lng: it.custom_lng,     // undefined for all catalog places!
  sort_order: it.sort_order,
  planned_time: it.planned_time,
  duration_minutes: it.duration_minutes,
  notes: it.notes,
  estimated_cost_min: it.estimated_cost_min,
  estimated_cost_max: it.estimated_cost_max,
}))

// 2. itinerary.service.ts (Lines 421–435) — Saves place: null in GuestStorage!
const items: ItineraryItem[] = (d.items || []).map((it, itIdx) => ({
  id: this.generateId(),
  day_id: dayId,
  place_id: it.place_id,
  custom_title: it.custom_title, // undefined!
  ...
  place: it.place || null,       // null!
}));

// 3. itinerary-detail.page.ts (Lines 670–672) — Renders "Destination Stop" fallback!
public getStopTitle(item: ItineraryItem): string {
  return item.place?.name || item.custom_title || 'Destination Stop';
}
```

### 3.2 Critical Bug `S-BUG-03`: Why Offline Suggested Itineraries Ignore Chosen Municipalities & Preferences
In `ItineraryService.generateOfflineSuggestedItinerary()` (`itinerary.service.ts:753–796`), the logic filters and sorts `matchedPool`, but never connects `matchedPool` to `dayPlaces`:

```typescript
// Project/src/app/core/services/itinerary.service.ts (Lines 753–796)
let matchedPool = curatedPool;
if (targetDest && !targetDest.includes('nueva ecija')) {
  const muniMatches = curatedPool.filter((p) => p.municipality.toLowerCase().includes(targetDest));
  if (muniMatches.length > 0) {
    matchedPool = muniMatches; // Filtered & sorted on lines 753–771, but NEVER READ AGAIN!
  }
}
...
const isProvincialOrBongabon = !targetDest || targetDest.includes('nueva') || targetDest.includes('ecija')
  || targetDest.includes('bongabon');
const cluster = isProvincialOrBongabon ? dayClusterPresets[d % dayClusterPresets.length] : null;

// BUG: When user selects "Pantabangan" or "Gapan City", cluster is null, so it schedules
// curatedPool[0..2] (Rohi Cafe, Museo de Bongabon, Thornes BBQ in Bongabon) on EVERY day!
const dayPlaces = cluster?.places || [
  curatedPool[0],
  curatedPool[1],
  curatedPool[2],
];
```

---

## 4. User’s Point of View: Traveler UI/UX Critique & Suggestions

Evaluated against the **W3C WCAG 2.2 AA usability standards** and domain best practices for mobile trip planners, travelers encounter six major UX friction points across the Custom and Suggested workflows:

1. **Identical Step 1 Questionnaires Blurred Together ("Am I in Suggested or Custom?")**:
   - Both `/suggested-wizard` and `/custom-builder` open with the exact same headline (*"Tell us your travel details"*) and the exact same bottom CTA button label (*"Find Itinerary"*).
   - Yet on Custom Builder Step 1, the user cannot even enter a **Trip Title**, nor do they get the quick municipality or budget chips available in Suggested Wizard.
   - *User UX Suggestion*: Differentiate the two entry screens clearly. On Custom Builder Step 1, lead with a prominent Trip Title input (e.g., *"Weekend Family Roadtrip"*), include the Quick Destination & Budget preset chips, and rename the primary button to **"Next: Choose Places to Visit →"**.
2. **"Add Off-Grid Custom Venue" Button Opens the Wrong Modal Tab**:
   - In Step 3 of the Custom Builder, tapping the button explicitly labeled *"Add Off-Grid Custom Venue"* opens the Place Picker modal on the Browse Places tab instead of the Off-Grid Venue form, forcing the user to hunt for the secondary segment tab at the top of the sheet.
   - *User UX Suggestion*: Pass the target tab directly into `openPlacePicker('custom')` so tapping Add Off-Grid Custom Venue opens the custom venue form immediately.
3. **Cannot Inspect a Destination Before Adding It in Custom Browse Mode**:
   - In Step 2 of `/custom-builder` (`activeView === 'browse'`), place cards only show a thumbnail, name, municipality, cost tag, and `+ Add` button. Tapping a card's photo or title does nothing—travelers cannot read the description, check opening hours, or see commute info without leaving the Custom Builder.
   - *User UX Suggestion*: Make the card body/photo clickable in Browse mode to open the shared `<app-place-detail-sheet>`, with a primary **"+ Add to Day {{ activeDayNumber }}"** CTA inside the modal.
4. **No Auto-Calculated Schedule Times or Transit Connectors in Custom Builder**:
   - When a user adds 3 places to Day 1 in Custom Builder, every stop card displays only `(2 hrs)` in amber with no start/end time until the user manually edits each stop one by one, and there is no warning if a user schedules a stop outside its verified opening hours.
   - *User UX Suggestion*: Automatically chain default sequential time windows (e.g., Stop 1: 09:00 AM – 10:30 AM, Stop 2: 11:00 AM – 12:30 PM with a 30-min transit buffer) as stops are added or reordered, and add a one-tap **"Auto-Optimize Day Route & Times"** button on the timeline header.
5. **Confusing Dual Save Buttons & Premature Saving on "Customize in Builder"**:
   - In Custom Builder's Timeline view, the top-right header says *✓ Save* while the bottom bar says *View Full Itinerary / Save Trip*, and both immediately exit to `/tabs/home` rather than opening the saved itinerary. Meanwhile, clicking *Customize in Builder* on a Suggested Itinerary saves a permanent copy to storage before the user even makes an edit.
   - *User UX Suggestion*: Pass unsaved suggested drafts to Custom Builder via in-memory router state (saving only when the user clicks *Save Itinerary*), and redirect post-save to `/itinerary/:id` so the user sees their finished trip immediately.
6. **Two Different Editors for Saved Trips with Mismatched Capabilities**:
   - Tapping Edit on `/itinerary/:id` opens a raw text-input form where adding an activity creates a blank text box (with no way to pick a real place from the database!), whereas `/custom-builder/:id` has the full visual timeline, catalog picker, and off-grid coordinate validator but is hidden from the UI.
   - *User UX Suggestion*: Consolidate onto a single, unified visual editor (or add a *"Browse & Pick from Catalog"* button inside `/itinerary/:id` edit mode) so users never have to type destination names and descriptions by hand.

---

## 5. Developer's Point of View: Architecture & Code Improvement Proposals

To resolve all 12 functional and UI/UX defects cleanly while adhering to **coding-and-system-development principles** (SOLID, DRY, strict input validation, and minimal blast radius), the proposal defines six engineering refactors:

### Proposal 1: Fix Guest/Offline Custom Stop Serialization & Hydration (Fixes `C-BUG-06`)
Preserve the full `Place` reference on `BuilderStop` in `custom-builder.page.ts`, populate `custom_title: it.name` as a safe display fallback, and hydrate any stop with a `place_id` against `PlaceService` in `ItineraryService.mapGuestItinerary()`:

```typescript
// Project/src/app/features/itinerary/custom-builder/custom-builder.page.ts
// 1. In BuilderStop interface & addPlaceStop(place: Place):
const stop: BuilderStop = {
  id: this.generateTempId(),
  place_id: place.id,
  custom_title: place.name,
  custom_lat: place.latitude,
  custom_lng: place.longitude,
  name: place.name,
  place: place, // Preserve full Place entity for offline/guest persistence
  ...
};

// 2. In saveItinerary() payload mapping:
items: d.items.map((it) => ({
  place_id: it.place_id,
  custom_title: it.custom_title || it.name,
  custom_lat: it.custom_lat ?? it.place?.latitude ?? null,
  custom_lng: it.custom_lng ?? it.place?.longitude ?? null,
  ...
  place: it.place || null,
}))
```

### Proposal 2: Wire `matchedPool`, Budget Filtering & `placeId` Anchor in Offline Suggested Generator (Fixes `S-BUG-01`, `S-BUG-03`, `S-BUG-04`)
1. **Instant Offline Short-Circuit (`S-BUG-04`)**: Inject `ConnectivityService` into `ItineraryService`. If `this.connectivityService.isHostOfflineSnapshot` is true (or `!navigator.onLine`), skip the 4-second HTTP timeout and invoke `generateOfflineSuggestedItinerary(request)` in 0ms.
2. **Use `matchedPool` & Respect Daily Budget (`S-BUG-03`)**: When `targetDest` specifies a municipality (e.g., Pantabangan, San Jose City, Gapan City, General Tinio, Cabanatuan City) or when preferences/budget are set, build each day's 3 stops by slicing without replacement from `matchedPool` (filtered by cumulative `request.daily_budget` and Haversine proximity to the day's anchor) instead of falling back to `curatedPool[0..2]`.
3. **Honor `placeId` Deep-Link Anchor (`S-BUG-01`)**: Add `anchor_place_id?: string` to `SuggestedItineraryRequest`. When `SuggestedWizardPage` receives `queryParams['placeId']`, lock that POI as Stop 1 of Day 1 and cluster the remaining Day 1 stops around its coordinates.

### Proposal 3: Synchronize `CustomBuilderPage` Date Changes, Category Mapping & Step 1 Controls (Fixes `C-BUG-01`, `C-BUG-02`, `C-BUG-03`, `C-BUG-05`)
1. **Add Title Input & Quick Chips to Step 1 (`C-BUG-01`)**: Add the Trip Title input box and the reusable Quick Destination & Budget preset chips to `custom-builder.page.html` (`activeView === 'form'`), and change the primary CTA text from *"Find Itinerary"* to *"Start Building Itinerary"*.
2. **Reactive Date-to-Days Synchronization (`C-BUG-05`)**: Subscribe specifically to `start_date` and `end_date` value changes in `CustomBuilderPage.ngOnInit()` and invoke a non-destructive `syncDaysWithDateRange()` helper that updates every `day.travel_date = toLocalIsoDate(addDaysLocal(start, idx))` and appends/trims days while preserving existing stops.
3. **Complete 16-Category Filter Mapping (`C-BUG-02`)**: Expand `browseCategories` in `CustomBuilderPage` to cover all 16 canonical categories: All, Attractions & Nature, Food & Cafes, Resorts & Stays, Culture & Heritage, Shopping & Markets, and Transit & Essentials (mapping terminals, hospitals, pharmacies, ATMs, fuel stations, convenience stores, and public facilities).

### Proposal 4: Unify Dual Itinerary Editors & Fix Modal Tab Routing (Fixes `UC-C4`, `UC-C5`, `S-BUG-06`)
1. **Direct Tab Targeting on Place Picker Modal (`UC-C4`)**: Update `openPlacePicker(defaultTab: 'browse' | 'custom' = 'browse')` in `custom-builder.page.ts:732` and bind the *Add Off-Grid Custom Venue* button to `openPlacePicker('custom')`. Remove `[disabled]="isPlaceInActiveDay(place.id)"` on `.picker-add-action-btn` so clicking an already-added place triggers the helpful duplicate-stop confirmation alert (`selectPlaceFromPicker`) as designed.
2. **Draft State Handoff for Customize in Builder (`S-BUG-06`)**: Instead of calling `createItinerary()` before entering `/custom-builder`, pass `this.generatedPlan` via `this.router.navigate(['/custom-builder'], { state: { draftItinerary: this.generatedPlan } })` so the trip is only persisted when the user explicitly clicks *Save*.
3. **Unified Editor Experience (`UC-C5`)**: On `ItineraryDetailPage`, wire the primary Edit action to open `/custom-builder/:id` (or embed the Place Picker modal and `pendingChangesGuard` directly into `ItineraryDetailPage` while preserving separate `estimated_cost_min` and `estimated_cost_max` fields).

---

## 6. Prioritized Implementation & Verification Roadmap

| Phase | Target Files | Key Engineering Changes | Verification Gate |
| :--- | :--- | :--- | :--- |
| **Phase 29.1: Data Integrity & Offline Engines (P0)** | `custom-builder.page.ts`<br>`itinerary.service.ts`<br>`suggested-wizard.page.ts` | Fix **`C-BUG-06`** (preserve `place` & `custom_title` in Guest Custom save); fix **`S-BUG-03`** (wire `matchedPool` & budget filter in offline generator); fix **`S-BUG-04`** (0ms offline check); fix **`S-BUG-02`** (local date helpers). | Unit tests in `itinerary.service.spec.ts` & `custom-builder.page.spec.ts` asserting non-Bongabon offline generation & stop title/coord retention. |
| **Phase 29.2: Form, Browse & Date Sync (P1)** | `custom-builder.page.html`<br>`custom-builder.page.ts` | Add Trip Title & quick chips to Step 1 (**`C-BUG-01`**); map all 16 categories in `catMap` (**`C-BUG-02`**); add `syncDaysWithDateRange()` on timeline date changes (**`C-BUG-05`**); fix `openPlacePicker('custom')`. | `npm run test:unit` & Playwright test verifying Step 1 title input, 16-category filtering, and timeline date resizing. |
| **Phase 29.3: Unified Editor & Route Map (P2)** | `itinerary-detail.page.ts`<br>`itinerary-detail.page.html` | Unify editor flows (preserving min/max cost ranges & adding `pendingChangesGuard`), pass draft state on `customizeInBuilder()`, and redirect post-save to `/itinerary/:id`. | Full CI verification: `npm run lint`, `npm run build` (0 SCSS budget warnings), and E2E journey pass. |

