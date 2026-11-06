# Suggested Itinerary, Route Map & Navigation: UI/UX Evaluation Report

**Target System**: Nueva Ecija Travel Itinerary App ("Trip mo, trip ko")  
**Evaluation Scope**: User & Developer evaluation of the Suggested Itinerary lifecycle on the live deployment ([`edselrenz.github.io/Itinerary-App/tabs/home`](https://edselrenz.github.io/Itinerary-App/tabs/home)) comparing the Wizard Preview ([`suggested-wizard.page.html`](file:///c:/Users/Edward/Desktop/CaseStudy/Project/src/app/features/itinerary/suggested-wizard/suggested-wizard.page.html)) against the Saved Itinerary Detail screen ([`itinerary-detail.page.html`](file:///c:/Users/Edward/Desktop/CaseStudy/Project/src/app/features/itinerary/itinerary-detail/itinerary-detail.page.html)).  
**Source Document**: `itinerary_app_ui_ux_evaluation_report.pdf`  
**Date Analyzed**: November 6, 2026  
**Status**: Documented & Staged for Remediation (Phase 28)

---

## 1. Executive Summary: The Post-Save UI Downgrade & Product Paradox

A live end-to-end evaluation conducted on `https://edselrenz.github.io/Itinerary-App/tabs/home` evaluated the complete lifecycle of a Suggested Itinerary:
1. Generating a new 3-day plan in the Suggested Itinerary Wizard (`/suggested-wizard`).
2. Saving it to local storage (`IndexedDB` / `localStorage`).
3. Opening the saved trip from Saved Itineraries (`/tabs/history` $\rightarrow$ `/itinerary/:id`).
4. Inspecting the route map and transit connectivity across views.
5. Testing the external turn-by-turn navigation handoff ("Open in Google Maps").

### The Core Finding: Product Paradox
> **The temporary, pre-save preview in the Suggested Wizard is visually richer, more informative, and more interactive than the permanent Saved Itinerary Detail view that travelers actually rely on during their trip.**

### The Three Critical Regressions
- **Complete Absence of Route Maps in Saved Trips**: Neither the Saved Itineraries list nor the Saved Trip Detail view renders an embedded route map, numbered stop markers, or connecting polylines. Switching to the Map Tab displays an unlinked provincial exploration canvas where marker pins failed to render on production builds due to an ES module namespace defect.
- **Severe Visual & Feature Regression After Saving**: Saving a generated plan and opening it in `/itinerary/:id` strips away all stop thumbnail photos, removes the segmented day switcher tabs, truncates time windows from `12:00 PM - 2:00 PM (2 hrs)` to bare `12:00`, hides the Nearby Places and Share/Export triggers (leaving orphaned dead code in the template), and removes the hero photo, close button, opening hours, fare, and drop-off point from the stop modal.
- **High-Friction Single-Stop Navigation & Contradictory Cost Math**: Clicking "Open in Google Maps" inside a stop modal only routes from the user’s live location to that single stop (`?api=1&destination=15.6315,121.144`) rather than chaining the day’s itinerary stops as waypoints. Meanwhile, `itinerary-detail.page.ts:580` fabricates a hardcoded ₱200 fee for every unpriced venue (`?? 200`), causing the bottom total card to contradict the top Verified Estimated Costs banner on the same screen (displaying ₱4,049 bottom total vs. ₱3,449 – ₱8,349 top banner).

---

## 2. Step-by-Step Live Walkthrough & Behavioral Trace

1. **Launching the Generator (`/tabs/home` $\rightarrow$ `/suggested-wizard`)**:
   - Tapping the Suggested Itinerary card opens the questionnaire form with Destination = `"Nueva Ecija"`, Travel Dates = `"Nov 6 – 8, 2026"` (3 days, 2 nights), Daily Budget = `3000`, and pre-selected preference pills (Food Trip, Culture & History, Resort).
2. **Generating & Reviewing the Preview (`/suggested-wizard`, `viewMode === 'itinerary'`)**:
   - Tapping *Find Itinerary* displays a spinner ("Clustering recommendations...") and renders a 3-day plan:
     - Day 1: Bongabon (Rohi Paperflower Cafe, Museo de Bongabon, Thornes Samgyupsal House, La Casa Prime Cabins).
     - Day 2: Cabanatuan City / San Jose.
     - Day 3: Gapan City / General Tinio.
   - The preview includes:
     - Top summary card with thumbnail.
     - Green Verified Estimated Costs ledger (`₱3,449 - ₱8,349 (+ 3 unpriced)`).
     - Collapsible color-coded Trip Assumptions & Travel Notes cards.
     - Segmented day capsule bar (`Day 1 | Day 2 | Day 3`).
     - 68×68px photo thumbnail stop cards.
     - Dashed blue *Nearby Places in Bongabon* trigger banner.
3. **Saving & Opening from Saved Itineraries (`/tabs/history` $\rightarrow$ `/itinerary/:id`)**:
   - Tapping *Accept & Save Itinerary* saves the trip to local storage, displays a toast, and navigates to Saved Itineraries. Tapping the saved card opens `ItineraryDetailPage`.
4. **Inspecting Saved Trip & Testing Navigation**:
   - On `/itinerary/:id`, all stop cards are plain text boxes without photos.
   - Times are stripped to bare hours (`12:00`).
   - The top header has a stacked double header with a `[+]` button that leaves the trip.
   - Share and Nearby triggers are missing from the UI.
   - Tapping Stop 1 opens a modal with a single-stop Google Maps link that forgets the rest of the day.

---

## 3. Screen-by-Screen UI/UX Parity & Regression Matrix

| UI / UX Dimension | Suggested Wizard Preview (`suggested-wizard.page.html`) | Saved Itinerary Detail (`itinerary-detail.page.html`) | Proposed Unified Design (Target) |
| :--- | :--- | :--- | :--- |
| **1. Route Map & Polylines** | None. Displays vertical stop cards only without spatial preview. | None. No embedded map, no stop pins, and no deep-link to `/tabs/map`. | Collapsible 220px interactive Leaflet route map with numbered pins (`1 → 2 → 3`), OSRM/geodesic polylines, and Expand on Map Tab CTA. |
| **2. Turn-by-Turn Navigation** | Single-stop external link inside modal (`openInGoogleMaps(stop)`). | Single-stop link (`?destination=15.6315,121.144`); ignores stop sequence. | Primary **Navigate Day Route** button (`&origin=...&destination=...&waypoints=...`) plus inline per-stop navigate icon buttons. |
| **3. Day Switching vs. Scrolling** | Segmented capsule bar (`.figma-day-capsule-bar`, L221–233) focusing on 1 day at a time. | Dumps all days into one long vertical list (`.days-view-list`, L175–207); `selectDay()` in TS is unused. | Sticky segmented day switcher capsule bar synchronized with the active day’s route map and timeline cards. |
| **4. Stop Card Visuals & Photos** | Rich `.figma-stop-card` (L244–260) with 68×68px photo thumbnail and numbered title. | Plain text-only box (`.activity-view-card`, L185–204) with zero photos and no step numbers. | Shared `<app-itinerary-stop-card>` with photo thumbnail, step badge, category pill, and leg transit connector badge. |
| **5. Time Window Formatting** | Full range + duration via `getTimingTime(stop)`: `12:00 PM - 2:00 PM (2 hrs)`. | Calls `formatTimingHour(stop)` (L188), stripping times to bare `12:00` without AM/PM or end time. | Bind `getTimingTime(stop, sIdx)` consistently so every stop displays its complete start–end window and duration. |
| **6. Cost Honesty & Rollup** | Honest range via `budgetSummary.displayText`: `₱3,449 - ₱8,349 (+ 3 unpriced)`. | `getStopEstimatedCost()` (TS L580) returns hardcoded `'200'` for null costs, inflating bottom total by ₱600. | Never fabricate ₱200 for unverified stops; show *Fee not listed* on unpriced cards and use `budgetSummary` everywhere. |
| **7. Stop Detail Modal** | Full modal (L392–495): 240px hero image, X close button, category badge, hours, and cost pill. | Stripped modal (L367–423): no photo, no X close button, no hours, and no cost pill. | Extract a single shared `<app-stop-detail-modal>` (or `<app-place-detail-sheet>`) used across Home, Map, Wizard, and Itinerary Detail. |
| **8. Commute Guide ("How to get there?")** | Shows all 4 fields (Transit & Hub, Drop-off Point, Travel Time, Fare) + Travel Reminder. | Omits Drop-off Point, Estimated Fare, and Travel Reminder (L389–408); always assumes Cabanatuan hub. | Render all 4 fields + reminder, and compute origin-aware leg advice (walk/tricycle for intra-town hops vs. inter-town transit). |
| **9. Nearby Essentials Explorer** | Interactive dashed banner (`.nearby-banner-trigger`, L263–273) opening 3-tab essential services view. | **Unreachable dead view**: `viewMode === 'nearby'` exists at L62–112, but no button in HTML calls `openNearbyPlaces()`. | Restore the *Nearby Places in {{ getDayLocation(day) }}* banner inside each day card and persist added stops via `ItineraryService`. |
| **10. Header Chrome & Share Sheet** | Clean single toolbar: `← Suggested Itinerary [Edit]`. | Stacked double header (`Saved Itineraries [+]` above `← Trip Title [Edit]`); Share modal (L428) has no trigger button. | Single unified toolbar (`← Trip Title | [Share] [Edit]`), wiring `openShareModal()` to a visible header action button. |

---

## 4. Traveler UX Critique: 5 Usability Pain Points

1. **Eliminate the Post-Save "Bait-and-Switch" Visual Downgrade**:
   - The Saved Itinerary Detail screen should be the visual flagship of the application. Retain the destination photo thumbnail on every stop card, preserve the full schedule badge (`12:00 PM – 2:00 PM (2 hrs)`), and keep the segmented Day capsule bar sticky below the header so travelers can switch days with one thumb tap.
2. **Embed an Interactive Day Route Map & Transit Leg Connectors**:
   - Place a collapsible 220px route map card directly above the active day’s stop timeline showing numbered markers (`1 → 2 → 3 → 4`) connected by a route line, paired with a *View Fullscreen on Map Tab* button. Between each consecutive stop card, insert a compact transit connector spine (e.g. `↓ 1.2 km • ~4 mins drive / tricycle`).
3. **Replace 8-Tap Single-Stop Handoffs with One-Tap Multi-Stop Day Navigation**:
   - Add a prominent primary action on each day header: **Start Day Route in Google Maps** (which opens a single multi-waypoint Google Maps route for all stops on that day in sequence), and place a quick-action directions icon (`navigate-outline`) on the right edge of every stop card for one-tap single-leg navigation.
4. **Make the "How to Get There?" Commute Guide Leg-Aware**:
   - Restore all four commute fields and the reminder callout in the modal. Display inter-city bus terminal instructions on Stop 1 of the day (or when crossing municipalities), and display local transfer instructions (*"From Rohi Paperflower Cafe (0.2 km): 3 min walk or ₱15–₱20 local tricycle"*) for intra-municipality stops.
5. **Clean Up Confusing Header Chrome, Raw ISO Dates & False Affordances**:
   - Remove the redundant top `Saved Itineraries [+]` bar on `/itinerary/:id`. Format dates human-readably via `formatDateRange()` (`Nov 6 – Nov 8, 2026 (3 Days, 2 Nights)`), remove the non-interactive `→` icon, and place Share/Export (`share-social-outline`) and Edit (`create-outline`) side by side in the header.

---

## 5. Developer Perspective: Codebase, Template & Architecture Critique

### 5.1 Orphaned Template Views & Unbound Component Methods in `itinerary-detail.page.html`
- **Unreachable Share & Export Modal**: `<ion-modal class="profile-subwindow-modal share-export-modal" [isOpen]="isShareModalOpen">` is rendered at lines 428–452 (now 569–594), and `openShareModal()`, `exportIcs()`, `copySummary()`, `shareNative()`, and `printPdf()` are implemented in TypeScript (lines 844–896)—**but zero buttons in `itinerary-detail.page.html` call `openShareModal()`.**
- **Unreachable Nearby Places View**: `@if (viewMode === 'nearby')` is rendered at lines 62–112 (now 83–115), and `openNearbyPlaces()` is defined in TypeScript (line 609)—**but zero buttons in `itinerary-detail.page.html` call `openNearbyPlaces()`.**
- **Unused Day Selection & Rich Time Formatters**: `activeDayIndex`, `selectDay(index)`, `formattedDateSpan`, and `getTimingTime(stop, index)` remain in TypeScript but are bypassed in the template in favor of raw `{{ itinerary.start_date }}` and `formatTimingHour(stop)`.

### 5.2 Hardcoded `?? 200` Cost Fallbacks Violating Honest Budget Accounting (ADR-001)
In [`Project/src/app/features/itinerary/itinerary-detail/itinerary-detail.page.ts:565–595`](file:///c:/Users/Edward/Desktop/CaseStudy/Project/src/app/features/itinerary/itinerary-detail/itinerary-detail.page.ts#L565-L595):
```typescript
public getStopEstimatedCost(item: ItineraryItem): number | string {
  const cost = item.estimated_cost_min ?? item.estimated_cost_max;
  if (cost != null && cost > 0) {
    return cost.toLocaleString();
  }
  return '200'; // BUG: Fabricates ₱200 for free (₱0) and unverified venues!
}

public calculateTotalActivityExpenses(): number {
  if (!this.itinerary?.days) return 0;
  let sum = 0;
  for (const day of this.itinerary.days) {
    for (const item of day.items || []) {
      const cost = item.estimated_cost_min ?? item.estimated_cost_max ?? 200; // BUG: Adds ₱200 per unpriced stop
      if (cost && !isNaN(Number(cost))) sum += Number(cost);
    }
  }
  return sum;
}
```
In our 3-day test trip, three stops (*Museo de Bongabon*, *Pantabangan Dam Viewpoint*, and *Tagpuan sa Lumang Gapan*) have null costs in `offline-places.data.ts`. Because of `?? 200`, each card falsely displays `Est. ₱200`, and the bottom *Estimated activity expenses* card displays **₱4,049** while the top *Verified Estimated Costs* banner displays **₱3,449 – ₱8,349 (+ 3 unpriced)**. Both methods must delegate directly to `getStopCost(item)` and `budgetSummary`.

### 5.3 Destructive Regex in `formatTimingHour()` & Hidden Custom Assumptions
- **Regex Time Truncation**: `formatTimingHour(item)` executes `item.planned_time.match(/(\d{1,2}:\d{2})/)` and returns `match[1]`. When `planned_time` is `"12:00 PM - 2:00 PM"`, it strips the meridian and end time, returning `"12:00"`; when `planned_time` is `"1 Night · 2 Days"`, the regex fails and returns `"22 hours"`. Binding `getTimingTime(stop, sIdx)` resolves this immediately.
- **Hidden Budget & Assumptions on Custom Plans**: In `itinerary-detail.page.html:149, 160`, `[class.hidden-on-custom]="itinerary.type !== 'suggested'"` applies `display: none !important` to `.verified-budget-card` and `.assumptions-info-box` whenever a user opens a Custom Itinerary—hiding budget warnings on custom trips.

### 5.4 Multi-Waypoint URL Builder Specification
To unify navigation across `SuggestedWizardPage`, `CustomBuilderPage`, `ItineraryDetailPage`, and `MapPage` without violating ADR-001 (Zero Paid APIs) or SCSS budgets:

```typescript
// Project/src/app/core/utils/itinerary-export.util.ts
export function buildGoogleMapsDayRouteUrl(items: ItineraryItem[]): string | null {
  const coords = (items || [])
    .map((it) => ({
      lat: it.place?.latitude ?? it.custom_lat,
      lng: it.place?.longitude ?? it.custom_lng,
    }))
    .filter((c): c is { lat: number; lng: number } => typeof c.lat === 'number' && typeof c.lng === 'number');

  if (coords.length === 0) return null;
  if (coords.length === 1) {
    return `https://www.google.com/maps/dir/?api=1&destination=${coords[0].lat},${coords[0].lng}&travelmode=driving`;
  }

  const origin = `${coords[0].lat},${coords[0].lng}`;
  const destination = `${coords[coords.length - 1].lat},${coords[coords.length - 1].lng}`;
  const middle = coords.slice(1, -1).map((c) => `${c.lat},${c.lng}`).join('|');
  const waypointsParam = middle ? `&waypoints=${encodeURIComponent(middle)}` : '';

  return `https://www.google.com/maps/dir/?api=1&origin=${origin}&destination=${destination}${waypointsParam}&travelmode=driving`;
}
```

---

## 6. Prioritized Remediation Action Checklist

| Priority | Target Component / File | Concrete Code & UI/UX Change | User & Dev Impact |
| :--- | :--- | :--- | :--- |
| **P0** (Immediate) | `itinerary-detail.page.html` & `.ts` | Restore header Share button (`openShareModal()`) and per-day Nearby banner (`openNearbyPlaces()`); replace `formatTimingHour()` with `getTimingTime()`; remove `?? 200` cost fallback; format dates via `formattedDateSpan`; remove dead `→` icon. | Eliminates post-save feature loss, fake ₱200 fees, and raw ISO date strings in under 40 lines of template changes. |
| **P1** (High) | `itinerary-export.util.ts`<br>`itinerary-route-map.component.ts` | Add `buildGoogleMapsDayRouteUrl(day.items)` and embed a reusable collapsible Leaflet route map with numbered stop pins, geodesic/OSRM polylines, and leg distance/time connector pills. | Reduces 4-stop navigation from 8 taps to 1 tap and gives travelers visual route context inside Saved Itineraries. |
| **P2** (Medium) | `stop-detail-modal.component.ts`<br>`commute-guide.data.ts` | Unify the Stop Detail Modal across Wizard and Detail views (restoring hero photo, X close button per WCAG 2.2, hours, fare, drop-off point, and reminder) and make commute guidance origin-aware. | Eliminates 150+ lines of duplicated modal HTML/SCSS and stops advising inter-city buses for 200m same-town hops. |
