# Live-Server Map & Suggested Itinerary Evaluation & Improvement Proposal

**Evaluation Version**: v3.0  
**Target System**: Nueva Ecija Travel Itinerary App ("Trip mo, trip ko")  
**Live Deployment**: [https://edselrenz.github.io/Itinerary-App/tabs/home](https://edselrenz.github.io/Itinerary-App/tabs/home)  
**Gateway API**: `https://ne-itinerary-api.edselrenz0.workers.dev/api/v1`  
**Repository Baseline**: `edselrenz/itinerary-app` (`b5bbc083`)  
**Evaluation Date**: November 7, 2026  
**Document Source**: `live_server_map_and_suggested_itinerary_proposal.pdf`  
**Status**: Documented & Staged for Phased Implementation (Phase 30)

---

## 1. Executive Summary: What Changed With the Live Server Running

Re-testing the live deployment at [edselrenz.github.io/Itinerary-App/tabs/home](https://edselrenz.github.io/Itinerary-App/tabs/home) with the backend server running confirms that the Cloudflare Worker proxy (`https://ne-itinerary-api.edselrenz0.workers.dev/api/v1`) and local FastAPI tunnel are actively serving database queries.

Compared to the prior offline-mode evaluation (where the application was restricted to 17 static fallback items in `offline-places.data.ts`), running the live server unlocks three major functional shifts across the application:

| Surface / Route | Previous State (Server Offline) | Current Live State (Server Online) | Live Verdict |
| :--- | :--- | :--- | :---: |
| **Home Tab**<br>`/tabs/home` | Yellow Offline Mode banner displayed; Popular Destinations limited to static curated fallback records. | Offline Mode banner is gone. Live database records populate Popular Destinations (e.g., *Rohi Paperflower Cafe*, *Museo de Bongabon*, *Thornes Samgyupsal House*). | **VERIFIED ONLINE** |
| **Explore Map Tab**<br>`/tabs/map` | Counter showed 17 destinations; marker pins failed to hydrate when cluster initialization raced. | Bottom drawer badge displays **List View (2673)**; interactive category pins and cluster badges (`520`, `186`, `150`, `114`) render across Nueva Ecija. However, a false-positive Offline Mode banner still appears at the top of the Map view. | **2,673 PINS + BANNER DESYNC** |
| **Suggested Wizard**<br>`/suggested-wizard` | Fell back to client-side TypeScript heuristic over 17 POIs; earlier repository snapshot lacked an inline route map. | Live 1-day generation for Cabanatuan City (Nov 7, 2026) returns 3 database stops: 1. *Camp Pangatian War Memorial Shrine*, 2. *Casa Batik*, and 3. *Edna's Cakeland & Cafe Kapitan*, paired with an embedded Day 1 Route preview map. | **LIVE ENGINE + PREVIEW MAP** |
| **Suggested Route $\rightarrow$ Full Map Handoff**<br>`/tabs/map?followRoute=true` | Only offered external Google Maps links per stop or via saved detail view; no in-app route map handoff. | Clicking the **Full Map** button on the Suggested Itinerary's Day 1 Route card navigates directly to `/tabs/map?followRoute=true&dayNumber=1&itineraryId=...` to inspect the route on the full interactive Leaflet canvas. | **ACTIVE DEEP-LINK HANDOFF** |

---

## 2. Deep-Dive Technical Analysis: How the Map & Suggested Itinerary Map Work

### 2.1 How the Main Explore Map (`/tabs/map`) Works With the Live Server

When navigating to `/tabs/map` ([`Project/src/app/tabs/map/map.page.ts`](file:///c:/Users/Edward/Desktop/CaseStudy/Project/src/app/tabs/map/map.page.ts)), the map lifecycle operates across four layers:

1. **Bounded Leaflet Canvas & Tile Layer**:
   - `initMap()` instantiates a Leaflet map bounded to Nueva Ecija's geographic envelope:
     ```typescript
     NE_BOUNDS = [[15.05, 120.55], [16.25, 121.55]], minZoom: 9, maxZoom: 18
     ```
   - Serves OpenStreetMap raster tiles via `https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png`.
2. **2,673-POI Hydration & Marker Clustering**:
   - With the backend online, the live deployment hydrates 2,673 active Nueva Ecija POIs into the bottom drawer (**List View (2673)**) and groups nearby coordinates via `L.markerClusterGroup`.
   - High-density commercial hubs such as Cabanatuan City, Gapan City, San Jose City, and Palayan City render aggregate cluster badges (e.g., `520`, `186`, `150`, `114`) that spiderfy or zoom on click into color-coded category pins (`restaurant`, `cafe`, `nature`, `historical`, `museum`, `resort`, `hotel`).
3. **Root Cause of the False-Positive Offline Banner on `/tabs/map` (State Desynchronization)**:
   - Even though `/tabs/home` shows no offline banner and loads live records, switching to `/tabs/map` displays the top notice indicating cloud sync is paused while local destinations remain accessible.
   - In `connectivity.interceptor.ts` and `connectivity.service.ts`, any single timed-out or aborted request (such as an un-debounced viewport query, a secondary health check racing with the large 2,673-POI payload over the Cloudflare Quick Tunnel, or a rate-limited request under SlowAPI) flips `isOfflineSubject.next(true)` globally without automatically clearing when subsequent tile or cached responses succeed.
   - In `map.page.ts:431–436`, a single `tileerror` event permanently sets `hasTileError = true` without an auto-clearing `tileload` handler.
4. **Filter & Viewport Mechanics**:
   - Category chips (*All*, *Nature*, *Food*, *Historical*, *Farm*, *Resort*, *Religious*, etc.), Municipality pills, and Price Tier filters (*Free*, *₱ Budget*, *₱₱ Mid-Range*, *₱₱₱ Luxury*) filter the loaded places and trigger `updateMarkers()` to rebuild the cluster layer.

---

### 2.2 How the Map Works Inside Suggested Itinerary (`/suggested-wizard` & `followRoute=true`)

Testing the live Suggested Itinerary flow at `/tabs/home` $\rightarrow$ *Create Suggested Itinerary* (generating a 1-day plan for Cabanatuan City on November 7, 2026) reveals a four-tier map architecture:

- **Tier 1 — Live Backend Spatial Clustering** ([`backend/app/algorithms/itinerary_generator.py`](file:///c:/Users/Edward/Desktop/CaseStudy/backend/app/algorithms/itinerary_generator.py)):
  - When the user submits the wizard form, `POST /api/v1/itineraries/suggest` resolves the destination anchor for Cabanatuan City ($15.4865^\circ\text{ N}, 120.9674^\circ\text{ E}$), queries active database places within a 25 km Haversine radius, and scores candidates per time slot (09:00 morning activity, 12:00 lunch dining, 14:30 afternoon activity) using:
    - Preference match ($+40$)
    - Featured priority ($+20$)
    - Haversine distance ($\max(0, 30 - \text{dist} \times 1.2)$)
    - Category diversity ($-25$ repeat penalty)
    - Daily budget fit ($+10 / -30$)
  - On the live server, this generated:
    - **Stop 1**: Camp Pangatian War Memorial Shrine (Historical/Memorial landmark in Cabanatuan City)
    - **Stop 2**: Casa Batik (Local heritage/dining stop)
    - **Stop 3**: Edna's Cakeland & Cafe Kapitan (Iconic Cabanatuan culinary/cafe destination)
- **Tier 2 — Embedded Day 1 Route Preview Map Card**:
  - Inside the generated Suggested Itinerary result screen, the app renders an inline Day 1 Route map card directly above the day's timeline stops.
  - It plots numbered circular markers (`1`, `2`, `3`) corresponding to the stop sequence so travelers can visually verify the spatial layout of their generated day without leaving the wizard.
- **Tier 3 — Interactive Full Map Handoff** (`/tabs/map?followRoute=true&dayNumber=1&itineraryId=...`):
  - The header of the embedded route card includes a **Full Map** button.
  - Clicking Full Map navigates the Angular router to `/tabs/map` with three query parameters: `followRoute=true`, `dayNumber=1`, and `itineraryId=<id>`. This hands off the active day's stop sequence to the main Map tab so the user can pan, zoom, and inspect the route in full-screen view.
- **Tier 4 — External Turn-by-Turn Handoff (Google Maps Directions API URL)**:
  - For live road navigation while traveling, clicking a stop's detail modal or clicking *Navigate / Open Route in Google Maps* constructs a Google Maps Directions URL:
    ```
    https://www.google.com/maps/dir/?api=1&origin=...&destination=...&waypoints=...&travelmode=driving
    ```
  - Pairs coordinates with local tricycle/jeepney terminal instructions from `commute-guide.data.ts`.

---

## 3. Dual-Perspective Evaluation: User POV vs. Developer POV (5 Priority Gaps)

```
+----------------------------------------------------------------------------------------------------+
|                                    5 PRIORITY LIVE GAPS AUDITED                                    |
+---------+---------------+-------------------------------------+------------------------------------+
| ID      | SEVERITY      | USER POINT OF VIEW (UI/UX)          | DEVELOPER POINT OF VIEW (CODE)     |
+---------+---------------+-------------------------------------+------------------------------------+
| GAP-01  | HIGH          | Straight Euclidean line preview     | L.polyline without OSRM GeoJSON    |
| GAP-02  | HIGH          | Route buried in 2,673 POI clusters  | MapPage lacks isolated route mode  |
| GAP-03  | MEDIUM-HIGH   | Draft lost when inspecting Full Map | In-memory draft cleared on route   |
| GAP-04  | MEDIUM-HIGH   | False-positive offline map banner   | tileerror/interceptor latching     |
| GAP-05  | MEDIUM        | No bi-directional card/pin click    | Missing selectedStopIndex binding  |
+---------+---------------+-------------------------------------+------------------------------------+
```

### Detailed Gap Breakdown:

#### **GAP-01: Suggested Route Preview & Polyline Geometry (Severity: HIGH)**
- **Workflow / Surface**: `/suggested-wizard` & `/tabs/map?followRoute=true`
- **User Point of View**:
  - The embedded Day 1 Route preview map plots numbered pins (`1`, `2`, `3`) for Camp Pangatian $\rightarrow$ Casa Batik $\rightarrow$ Edna's Cakeland, but connects them via straight Euclidean lines (or static markers) without showing road-network paths, per-leg distance (km), or tricycle/car travel time between stops.
  - Travelers cannot tell if Stop 1 $\rightarrow$ Stop 2 takes 5 minutes on a paved highway or 35 minutes across winding provincial roads.
- **Developer Point of View**:
  - Leaflet's `L.polyline(latLngs)` draws point-to-point segments directly between stop coordinates. Neither `itinerary_generator.py` nor the frontend fetches road-snapped GeoJSON polylines or duration matrices from an OSRM routing service.
  - Furthermore, `itinerary_generator.py` greedily chains `current_anchor_lat/lng` slot-by-slot without running a 2-Opt pass after morning/lunch/afternoon assignment.

#### **GAP-02: Full Map Handoff Visual Overload & Context Loss (Severity: HIGH)**
- **Workflow / Surface**: `/tabs/map?followRoute=true&dayNumber=1&itineraryId=...`
- **User Point of View**:
  - Clicking "Full Map" from the Suggested Itinerary takes the user to `/tabs/map?followRoute=true...` where all 2,673 Nueva Ecija POIs (**List View (2673)**) and cluster badges (`520`, `186`, `150`) remain active on the canvas.
  - The user's 3 itinerary stops get visually buried inside the 520-pin Cabanatuan cluster, and there is no floating "Back to Suggested Itinerary" button or "Day 1 / Day 2" switcher on the Map tab.
- **Developer Point of View**:
  - When `followRoute=true` is present in `ActivatedRoute.queryParams`, `MapPage` loads the full 2,673-place dataset into `this.markerCluster` alongside the route overlay.
  - `MapPage` lacks a dedicated `routeFocusMode: 'isolated' | 'with_nearby'` state that hides background clusters by default and renders an active route header bar with a direct back-navigation action.

#### **GAP-03: Pre-Save State Risk on Full Map Navigation (Severity: MEDIUM–HIGH)**
- **Workflow / Surface**: `/suggested-wizard` $\rightarrow$ `/tabs/map`
- **User Point of View**:
  - In the Suggested Wizard, the user sees the "Full Map" button before clicking "Save Itinerary" at the bottom of the page.
  - If a user clicks Full Map to inspect the route and then taps Back to return to the wizard, they expect their generated plan to still be open—not reset back to the blank Step 1 wizard form, nor fail to load the route if the draft ID is not yet saved in the database.
- **Developer Point of View**:
  - `SuggestedWizardPage` stores the newly generated plan in component memory (`this.generatedPlan`) until `saveItinerary()` persists it via `POST /api/v1/itineraries`.
  - Passing a transient `itineraryId` in `/tabs/map?followRoute=true&itineraryId=...` requires `ItineraryService` to cache `activeDraftItinerary$` in memory / `sessionStorage` so both `MapPage` and back-navigation to `SuggestedWizardPage` preserve the unsaved plan.

#### **GAP-04: False-Positive Offline Mode Banner on Map Tab (Severity: MEDIUM–HIGH)**
- **Workflow / Surface**: `/tabs/map` vs. `/tabs/home`
- **User Point of View**:
  - While `/tabs/home` cleanly shows online status and live Popular Destinations, switching to `/tabs/map` displays an Offline Mode banner at the top (*"cloud sync is paused while local destinations remain accessible"*) even though 2,673 destinations and live Suggested Itineraries just loaded.
  - This confuses users into thinking the server crashed.
- **Developer Point of View**:
  - `ConnectivityService` flips `isOffline$` to `true` whenever any HTTP call fails, times out, or hits Cloudflare/SlowAPI rate limits during the heavy map initialization burst, or when `MapPage` falls back to a bundled 2,673-POI local JSON cache without resetting `isOffline$` once `GET /api/v1/health` succeeds.
  - In `map.page.ts`, `tileLayer.on('tileerror')` latches `hasTileError = true` permanently on any single aborted tile.

#### **GAP-05: One-Way Preview Map & Stop Card Interaction (Severity: MEDIUM)**
- **Workflow / Surface**: `/suggested-wizard` & `/itinerary/:id`
- **User Point of View**:
  - On the Suggested Itinerary result screen, the embedded Day 1 Route preview map and the stop cards below it (*1. Camp Pangatian*, *2. Casa Batik*, *3. Edna's Cakeland*) do not interact bi-directionally.
  - Tapping Stop Card #2 does not highlight or center Pin #2 on the preview map, and tapping Pin #2 on the preview map does not scroll to or open Stop #2's commute guide.
- **Developer Point of View**:
  - The embedded preview map and the stop card list lack a shared reactive `selectedStopIndex: number | null` state binding that triggers `previewMap.panTo([stop.lat, stop.lng])` and pulses the active SVG/DOM marker class.

---

## 4. User POV Improvement Proposal: UI & UX Enhancements

### 4.1 Upgrade the Embedded Suggested Itinerary Map Into an Interactive "Route Strip"
1. **Road-Snapped Polyline with Directional Chevrons**:
   - Replace straight point-to-point lines on the Day 1 Route preview map with a styled road-following polyline (`#0284C7` stroke, 4px weight, directional arrows) so users see the actual highway/arterial corridor through Cabanatuan City (e.g., along Maharlika Highway / Pangatian Rd).
2. **Per-Leg Distance & Commute Pills Between Stop Cards**:
   - Directly between Stop 1 (*Camp Pangatian War Memorial Shrine*), Stop 2 (*Casa Batik*), and Stop 3 (*Edna's Cakeland & Cafe Kapitan*), display a compact connector pill:
     $$\text{🚗 5.2 km • ~11 mins drive / 18 mins tricycle • Est. Fare ₱50–₱80}$$
3. **Bi-Directional Card $\leftrightarrow$ Pin Highlighting**:
   - Tapping any stop card highlights its numbered marker (`1`, `2`, or `3`) on the embedded preview map and pans smoothly to that stop.
   - Tapping a numbered pin on the preview map scrolls the timeline to that stop card and offers a quick *"How to get there?"* action.

### 4.2 Redesign the Full Map (`followRoute=true`) Mode with Focused Route Controls
1. **Isolate the Active Route by Default (Hide Background Clutter)**:
   - When the user clicks Full Map (`/tabs/map?followRoute=true&dayNumber=1&itineraryId=...`), hide the 2,673 background discovery pins by default so only Stops `1`, `2`, and `3` and their connecting road polyline are rendered on the canvas.
2. **Floating "Active Route Control Bar" at the Top of `/tabs/map`**:
   - **Back to Itinerary Pill**: A prominent `← Back to Cabanatuan City Plan` button that returns directly to `/suggested-wizard` (preserving the unsaved draft) or `/itinerary/:id`.
   - **Day Switcher Chips**: Inline `Day 1 | Day 2 | All Days` pills so multi-day trips can be inspected on the full map without leaving `/tabs/map`.
   - **"Show Nearby POIs (+2,673)" Toggle Switch**: A secondary toggle pill allowing the traveler to overlay nearby restaurants, cafes, or gas stations within 2 km of the active route polyline when desired, instead of dumping all 2,673 provincial pins onto the route view at once.
3. **Interactive Bottom Route Carousel on `/tabs/map?followRoute=true`**:
   - Replace the generic **List View (2673)** button during `followRoute=true` mode with a horizontal swipeable card carousel of the day's stops (*Stop 1 of 3 $\rightarrow$ Stop 2 of 3 $\rightarrow$ Stop 3 of 3*) plus a primary *"Start Multi-Stop Google Maps Navigation"* CTA.

---

## 5. Developer POV Improvement Proposal: Architecture & Code Blueprints

### 5.1 Reusable `<app-itinerary-route-map>` Component & Draft State Cache
Create a standalone `ItineraryRouteMapComponent` and cache unsaved wizard drafts in `ItineraryService`:

```typescript
// Project/src/app/shared/components/itinerary-route-map/itinerary-route-map.component.ts
@Component({
  selector: 'app-itinerary-route-map',
  standalone: true,
  template: `
    <div class="route-preview-card">
      <div class="route-preview-header">
        <div class="route-title-group">
          <span class="route-day-badge">Day {{ dayNumber }} Route</span>
          <span class="route-meta" *ngIf="totalDistanceKm">
            {{ stops.length }} stops • {{ totalDistanceKm | number:'1.1-1' }} km • ~{{ totalDriveMinutes }} mins
          </span>
        </div>
        <div class="route-actions">
          <button type="button" class="btn-full-map" (click)="openFullMap()">
            <ion-icon name="expand-outline"></ion-icon> Full Map
          </button>
        </div>
      </div>
      <div #previewMapContainer class="preview-leaflet-canvas"></div>
    </div>
  `
})
export class ItineraryRouteMapComponent implements OnChanges, AfterViewInit, OnDestroy {
  @Input() itineraryId: string = 'draft';
  @Input() dayNumber: number = 1;
  @Input() stops: Array<{ name: string; lat: number; lng: number; category?: string }> = [];
  @Input() routeGeometry?: [number, number][]; // Road-snapped [lat, lng] coordinates from OSRM
  @Input() activeStopIndex: number | null = null;
  @Output() stopMarkerSelected = new EventEmitter<number>();

  constructor(private router: Router, private itineraryService: ItineraryService) {}

  public openFullMap(): void {
    // Ensure unsaved Suggested Wizard draft is cached before navigating to /tabs/map
    this.router.navigate(['/tabs/map'], {
      queryParams: {
        followRoute: 'true',
        dayNumber: this.dayNumber,
        itineraryId: this.itineraryId || 'draft'
      }
    });
  }
}
```

---

### 5.2 Implement Focused `followRoute=true` Mode & Fix False Offline Banner in `MapPage`
In `Project/src/app/tabs/map/map.page.ts`, separate Discovery Mode (browsing 2,673 places) from Focused Route Mode (`followRoute=true`), and prevent local fallback hydration or secondary request timeouts from displaying a false Offline Mode banner when `GET /api/v1/health` is healthy:

```typescript
// Project/src/app/tabs/map/map.page.ts (Focused Route Mode + Cluster Separation)
public isFollowRouteMode = false;
public showBackgroundPoisInRouteMode = false;
public activeRouteDayNumber = 1;
public activeRouteStops: Place[] = [];
private routeLayerGroup?: L.LayerGroup;

private handleRouteQueryParams(params: ParamMap): void {
  const followRoute = params.get('followRoute') === 'true';
  const itineraryId = params.get('itineraryId');
  const dayNumber = Number(params.get('dayNumber') || 1);

  if (followRoute && itineraryId) {
    this.isFollowRouteMode = true;
    this.activeRouteDayNumber = dayNumber;
    const plan = this.itineraryService.getItineraryOrDraftById(itineraryId);
    if (plan) {
      this.renderFocusedItineraryRoute(plan, dayNumber);
    }
  } else {
    this.isFollowRouteMode = false;
    this.clearFocusedItineraryRoute();
  }
}

private renderFocusedItineraryRoute(plan: any, dayNumber: number): void {
  if (!this.map) return;
  // Hide the 2,673 background discovery clusters unless explicitly toggled on
  if (!this.showBackgroundPoisInRouteMode && this.markerCluster) {
    this.map.removeLayer(this.markerCluster);
  }
  this.routeLayerGroup?.clearLayers();
  this.routeLayerGroup = L.layerGroup().addTo(this.map);

  const day = (plan.days || []).find((d: any) => Number(d.day_number || d.dayNumber) === dayNumber) || plan.days?.[0];
  const validStops = (day?.items || day?.stops || []).filter((s: any) => Number.isFinite(Number(s.lat || s.latitude)));

  const latLngs: L.LatLngExpression[] = validStops.map((s: any, idx: number) => {
    const lat = Number(s.lat ?? s.latitude);
    const lng = Number(s.lng ?? s.longitude);
    const numberedIcon = L.divIcon({
      className: 'route-sequence-pin',
      html: `<div class="seq-badge">${idx + 1}</div><span class="seq-label">${this.escapeHtml(s.name)}</span>`,
      iconSize: [32, 32],
      iconAnchor: [16, 16]
    });
    L.marker([lat, lng], { icon: numberedIcon }).addTo(this.routeLayerGroup!);
    return [lat, lng] as [number, number];
  });

  if (latLngs.length > 1) {
    const poly = L.polyline(day.routeGeometry || latLngs, { color: '#0284C7', weight: 5, opacity: 0.9 }).addTo(this.routeLayerGroup!);
    this.map.fitBounds(poly.getBounds(), { padding: [48, 48], maxZoom: 15 });
  }
}
```

---

### 5.3 Backend OSRM Road Geometry & 2-Opt Intra-Day Stop Optimization
In `backend/app/algorithms/itinerary_generator.py`, add a post-selection 2-Opt pass per day (preserving the 12:00 lunch anchor while ensuring morning and afternoon stops minimize backtracking) and return road-snapped polyline coordinates plus per-leg travel metrics:

```python
# backend/app/algorithms/itinerary_generator.py — Per-Leg Distance & Road Geometry Enrichment
def enrich_day_route_legs(day_items: list[dict]) -> dict:
    """Computes per-leg distance (km), estimated drive/tricycle minutes, and polyline coordinates."""
    legs = []
    total_km = 0.0
    total_mins = 0
    coords = []
    
    for idx, item in enumerate(day_items):
        lat, lng = float(item["latitude"]), float(item["longitude"])
        coords.append([lat, lng])
        if idx > 0:
            prev = day_items[idx - 1]
            straight_km = haversine_distance(float(prev["latitude"]), float(prev["longitude"]), lat, lng)
            road_km = round(straight_km * 1.28, 2)  # Nueva Ecija arterial road circuity factor (or OSRM leg distance)
            drive_mins = max(3, int(round((road_km / 32.0) * 60)))
            tricycle_mins = max(5, int(round((road_km / 22.0) * 60)))
            total_km += road_km
            total_mins += drive_mins
            legs.append({
                "from_order": idx,
                "to_order": idx + 1,
                "distance_km": road_km,
                "drive_minutes": drive_mins,
                "tricycle_minutes": tricycle_mins
            })
            
    return {
        "total_distance_km": round(total_km, 2),
        "total_drive_minutes": total_mins,
        "legs": legs,
        "route_geometry": coords
    }
```

---

## 6. Phased Implementation Roadmap & Verification Matrix

| Phase | Priority | Target Files / Endpoints | Key Engineering Changes | Acceptance & Verification Gate |
| :--- | :---: | :--- | :--- | :--- |
| **Phase 30.1** | **IMMEDIATE** | `connectivity.service.ts`<br>`connectivity.interceptor.ts`<br>`map.page.ts`<br>`map.page.html` | **Fix Map Tab False-Offline Banner & Tile Error Latching**: Auto-clear `hasTileError` on successful tile loads; prevent single aborted/failed requests or OSM tile drops from latching `isOffline$ = true` when `GET /api/v1/health` is 200 OK. | Switching from `/tabs/home` to `/tabs/map` with the backend server running shows 0 false Offline Mode banners; map tiles load cleanly without false warnings. |
| **Phase 30.2** | **SHORT-TERM** | `map.page.ts`<br>`map.page.html`<br>`itinerary.service.ts` | **Focused `followRoute=true` Map Mode & Pre-Save Draft Persistence**: Hide the 2,673 background discovery clusters by default in route mode; render floating Active Route Control Bar (`Back to Plan`, `Day 1 \| Day 2`, `Show Nearby POIs`); cache unsaved wizard draft via `activeDraftItinerary$`. | Clicking Full Map on an unsaved Suggested Itinerary isolates Stops 1–2–3, shows the Active Route Bar, and returns to `/suggested-wizard` without losing the draft plan. |
| **Phase 30.3** | **MEDIUM-TERM** | `itinerary-route-map.component.ts`<br>`itinerary-route-map.component.html`<br>`itinerary_generator.py` | **Road-Snapped Polylines, Per-Leg Commute Badges & Bi-Directional Pin Sync**: Display per-leg connector pills (`🚗 5.2 km • ~11 mins / 18 mins tricycle • Est. Fare ₱50–₱80`) between stop cards; implement bi-directional stop card click $\leftrightarrow$ map pin pan/pulse sync. | Each stop transition displays distance (km), drive/tricycle time, fare estimate, and road-following polyline; tapping a stop card centers and highlights its pin. |
| **Phase 30.4** | **SCALE & PERF** | `backend/app/api/v1/places.py`<br>`map.page.ts` (`preferCanvas: true`) | **Server-Side Spatial Indexing & Canvas Clustering for 2,673+ POIs**: Enable `preferCanvas: true` on Leaflet map; add SQL bounding-box index and viewport queries on `GET /api/v1/places`. | `GET /api/v1/places` supports municipality, price tier, and viewport BBox queries in SQL with sub-50ms response time and 60fps panning across all 2,673 POIs. |
