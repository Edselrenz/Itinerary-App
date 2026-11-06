# Map & Routing System: Architecture Analysis & Engineering Proposal

**Target System**: Nueva Ecija Travel Itinerary App ("Trip mo, trip ko")  
**Audit Target**: Live Production Deployment at [edselrenz.github.io/Itinerary-App/tabs/home](https://edselrenz.github.io/Itinerary-App/tabs/home) & Local Monorepo (`Project/` Angular 22 / Ionic 9 / Capacitor 8, `backend/` FastAPI / SQLAlchemy 2.0)  
**Document Source**: `itinerary_app_map_and_routing_proposal.pdf`  
**Date Analyzed**: November 6, 2026  
**Status**: Documented & Staged for Phased Implementation (Phase 27)

---

## 1. Executive Summary & Production Audit Context

An end-to-end static code audit and interactive browser evaluation of the live GitHub Pages deployment revealed that while client-side Angular SPA routing transitions cleanly without page reloads, the geospatial mapping and route planning subsystems exhibit **four critical-to-high engineering gaps**:

1. **Silent Map Pin Rendering Failure on Production Builds (`MAP-01`, Critical)**:
   - Navigating to `/tabs/map` or deep-linking via "View Pin on Map" renders OpenStreetMap raster tiles and reports destinations in the drawer pill, but renders **zero marker pins** on the canvas due to an ES module namespace / UMD global initialization collision in `leaflet.markercluster` under Angular esbuild.
2. **Zero In-App Route Polylines or Multi-Stop Directions (`ROUTE-01`, High)**:
   - Generated and custom itineraries (`/suggested-wizard`, `/custom-builder`, `/tabs/history`) render purely as text cards with no connecting road polylines, no leg-by-leg metrics, and external directions links that only support single destinations.
3. **176.2 km Cross-Province Backtracking in Presets & Chaining (`ROUTE-02`, High)**:
   - Offline presets in [`offline-places.data.ts`](file:///c:/Users/Edward/Desktop/CaseStudy/Project/src/app/core/data/offline-places.data.ts) route travelers from General Tinio to Pantabangan (57.2 km north) and back to Gapan City (58.9 km south) in a single afternoon.
4. **Truncated Client-Side Filtering & Hardcoded Fallbacks (`MAP-02`, `MAP-03`, `ROUTE-03`, High)**:
   - MapPage filters only the first 100/150 rows in browser memory; deep-linking with coordinates skips opening the target POI bottom sheet; adding a Nearby Place injects hardcoded Bongabon coordinates (`15.63, 121.14`) and mutates memory without saving to storage.

---

## 2. Root-Cause Diagnostic Matrix (8 Verified Defects)

The proposal identifies 8 specific defects across the codebase:

| Defect ID | Severity | Module & Lines | Observed Behavior & Root Cause | Engineering Remediation |
| :--- | :---: | :--- | :--- | :--- |
| **MAP-01** | **Critical** | `Project/src/app/tabs/map/map.page.ts`<br>`L47–48, L137–139, L288–293, L422` | **Zero map pins render in production**.<br>Static ES imports `import * as L from 'leaflet'; import 'leaflet.markercluster';` execute before `MapPage.constructor()` sets `window.L = L`. Under Angular esbuild, `L` is a frozen ESM namespace object, so `L.markerClusterGroup` is undefined or fails in `initMap()`, leaving `this.markerCluster = null` and causing `updateMarkers()` to return early. | Resolve canonical Leaflet object via `const LeafletLib = (L as any).default ?? L; (window as any).L = LeafletLib;` at module top-level before invoking `markerClusterGroup`, and add a graceful fallback to a standard `L.layerGroup()` if cluster initialization fails. |
| **MAP-02** | **High** | `Project/src/app/core/services/place.service.ts`<br>`L119–149`<br>`map.page.ts L340–416`<br>`backend/app/api/v1/places.py L92–163` | **Truncated client-side filtering & ignored offline bounds**.<br>`getFallbackPaginatedPlaces()` ignores `min_lat/max_lat/min_lng/max_lng` and featured. Online, `MapPage` fetches 100/150 items globally and applies municipality and price filters in memory (`applyLocalFilters`), yielding 0 matches if matching POIs sit past row 150 in PostgreSQL. | Add `municipality_name: str \| None` and `price_tier: Literal['all', 'free', 'budget', 'mid'] \| None` query parameters to `GET /api/v1/places` in `places.py`, pass them from `MapPage.loadPlaces()`, and enforce bounding-box, municipality, and price filtering inside `PlaceService.getFallbackPaginatedPlaces()`. |
| **MAP-03** | **High** | `map.page.ts L171–186, L320–329`<br>`home.page.ts L229–230, L434–447` | **Deep-link pin selection skipped & fallback coordinates hardcoded**.<br>In `map.page.ts:177`, when `lat` and `lng` query params exist, the if/else skips `flyToDestinationOrMunicipality()`, so `selectedPlace` is never set and the bottom sheet stays closed. Also, `home.page.ts:229` hardcodes `15.48, 120.97` on offline search errors. | Pass `placeId` directly in `HomePage.viewDestinationOnMap()`, select and open the matching `Place` in `MapPage` even when `lat/lng` are provided, and suppress the `moveend` reload during programmatic `flyTo()` animations via `isProgrammaticFly = true`. |
| **ROUTE-01** | **High** | `itinerary-detail.page.ts`<br>`suggested-wizard.page.ts`<br>`custom-builder.page.ts` | **No itinerary route map, polylines, leg metrics, or multi-stop directions**.<br>Travelers cannot visualize their daily stop sequence on a map, see road distances/travel times between stops, or launch a multi-stop route in Google Maps (only single-stop `?destination=lat,lng` links exist). | Introduce a shared `RouteMapComponent` & `RoutingService` that renders numbered stop pins, road-network polylines (via OSRM / GeoJSON fallback), per-leg distance/time badges, a View Day Route on Map deep-link, and multi-stop Google Maps URLs (`&origin=...&destination=...&waypoints=...`). |
| **ROUTE-02** | **High** | `offline-places.data.ts L446–482`<br>`itinerary_generator.py L258–354` | **176.2 km cross-province zig-zag in presets & unoptimized stop order**.<br>Offline Day 2 (58.5 km) and Day 3 (116.2 km: General Tinio $\rightarrow$ Pantabangan $\rightarrow$ Gapan City) cross the province twice. Online, `DEF-03` re-sorts stops chronologically after greedy chaining without optimizing route order. | Re-cluster offline presets into coherent corridors (East/Bongabon, North/San Jose–Pantabangan, South/Cabanatuan–Gapan–Gen. Tinio, cutting distance by 66.3% to 59.4 km) and apply a 2-opt Nearest-Neighbor TSP pass to activity stops before assigning time slots. |
| **ROUTE-03** | **Medium** | `itinerary-detail.page.ts L806–842`<br>`suggested-wizard.page.ts L422–460` | **Fake Bongabon coordinates (15.63, 121.14) & unpersisted Nearby stops**.<br>`NearbyPlaceItem` lacks `latitude/longitude`, so `addNearbyPlaceToActiveDay()` injects `15.63, 121.14` for every town and mutates `currentDay.items` in memory without calling `ItineraryService.addStop()`. | Add verified coordinates to `NearbyPlaceItem` (or resolve municipality center coordinates), and persist added stops via `this.itineraryService.addStop()` / `updateItinerary()` so they survive page reloads. |
| **ROUTE-04** | **Medium** | `app.routes.ts`<br>`itinerary-detail.page.ts L944`<br>`map.page.ts L719` | **Guard gaps, hardcoded back navigation & non-GPS recenter button**.<br>`/itinerary/:id` lacks `canDeactivate: [pendingChangesGuard]` for its in-place editor; back buttons hardcode `/tabs/history` or `/tabs/home` instead of checking navigation history; and the `locate-outline` button only resets camera bounds instead of reading device GPS. | Attach `pendingChangesGuard` to `/itinerary/:id`, use `IonRouterOutlet.canGoBack()` / `Location.back()` with fallback, sync map filters to URL `queryParams`, and add a real GPS Locate Me control alongside a separate Reset Province View button. |
| **ROUTE-05** | **Medium** | `commute-guide.data.ts L10–139` | **Static Cabanatuan-only commute guide for all legs**.<br>Only 8 of 32 municipalities have specific entries, and every stop modal advises departing from Cabanatuan City Central Terminal—even when travelling 300m between two stops in Bongabon. | Make commute guidance leg-aware (`getLegCommuteInfo(prevStop, currentStop)`): detect intra-municipality hops ($\le 1.2$ km $\rightarrow$ local tricycle/walk), inter-municipality corridor transfers, and provincial hub departures across all 32 municipalities. |

---

## 3. Quantitative Spatial Analysis (176.2 km vs. 59.4 km)

To quantify the impact of **ROUTE-02**, the proposal calculated the exact great-circle Haversine leg distances across the coordinates defined in [`Project/src/app/core/data/offline-places.data.ts`](file:///c:/Users/Edward/Desktop/CaseStudy/Project/src/app/core/data/offline-places.data.ts):

### Current Unoptimized Presets (176.2 km Straight-Line)
- **Day 1 (Bongabon)**: 1.51 km across 4 stops (tightly clustered).
- **Day 2 (San Jose $\rightarrow$ Cabanatuan $\rightarrow$ Bongabon)**:
  - Farm Villaronte (San Jose City, `15.7850, 120.9980`) $\rightarrow$ Casa Batik (Cabanatuan City, `15.4850, 120.9680`): **33.51 km south**.
  - Casa Batik $\rightarrow$ D’ Pavilion Farm (Bongabon, `15.6322, 121.1447`): **25.02 km east**.
  - **Day 2 Total**: **58.54 km**.
- **Day 3 (General Tinio $\rightarrow$ Pantabangan $\rightarrow$ Gapan City)**:
  - Minalungao National Park (General Tinio, `15.2981, 121.1223`) $\rightarrow$ Pantabangan Dam (`15.8126, 121.1098`): **57.23 km north**.
  - Pantabangan Dam $\rightarrow$ Tagpuan sa Lumang Gapan (Gapan City, `15.3065, 120.9461`): **58.94 km south**.
  - **Day 3 Total**: **116.17 km** (over 160 km on provincial roads).

### Proposed Corridor Clustering + 2-Opt TSP (59.4 km Straight-Line)
Re-clustering the identical stops into three geographic corridors cuts total transit distance by **66.3%** (saving **116.8 km** of unnecessary road travel):
1. **Day 1: East Corridor (Bongabon)**:
   - Rohi Paperflower Cafe $\rightarrow$ Museo de Bongabon $\rightarrow$ La Casa Prime Cabins $\rightarrow$ Thornes Samgyupsal: **1.5 km**.
2. **Day 2: North Corridor (San Jose & Pantabangan)**:
   - Farm Villaronte (San Jose) $\rightarrow$ George Point Viewdeck (Pantabangan) $\rightarrow$ Pantabangan Dam $\rightarrow$ Highland Bali Villas: **13.8 km**.
3. **Day 3: South Corridor (Cabanatuan $\rightarrow$ General Tinio $\rightarrow$ Gapan City)**:
   - Casa Batik (Cabanatuan) $\rightarrow$ Minalungao National Park (Gen. Tinio) $\rightarrow$ Tagpuan sa Lumang Gapan: **45.5 km**.

---

## 4. Engineering Blueprints & Target Architecture

In strict compliance with **ADR-001 (Zero-Paid-API & Open-Data Compliance)** and **W3C WCAG 2.2 accessibility standards**, the proposal outlines 5 concrete architectural blueprints:

### Blueprint 1: Leaflet MarkerCluster ESM Initialization & Layer Fallback (Fixes MAP-01)
```typescript
// Project/src/app/tabs/map/map.page.ts
const LeafletLib: typeof L = ((L as unknown as { default?: typeof L }).default ?? L);
if (typeof window !== 'undefined') {
  (window as unknown as { L: typeof L }).L = LeafletLib;
}

// Inside initMap():
const clusterFactory =
  (LeafletLib as unknown as { markerClusterGroup?: (opts?: unknown) => L.MarkerClusterGroup }).markerClusterGroup
  ?? ((window as unknown as { L?: { markerClusterGroup?: (opts?: unknown) => L.MarkerClusterGroup } }).L?.markerClusterGroup);

this.markerCluster = typeof clusterFactory === 'function'
  ? clusterFactory({ showCoverageOnHover: false, maxClusterRadius: 40, spiderfyOnMaxZoom: true, chunkedLoading: true })
  : (LeafletLib.layerGroup() as unknown as L.MarkerClusterGroup);

this.map.addLayer(this.markerCluster);
```

### Blueprint 2: Reusable Route Map & Multi-Stop Google Maps Builder (Fixes ROUTE-01)
- Create a shared `ItineraryRouteMapComponent` embedded in `ItineraryDetailPage`, `SuggestedWizardPage` (Step 2), and `CustomBuilderPage` (Timeline view).
- Multi-Stop Google Maps universal cross-platform URL builder:
  ```text
  https://www.google.com/maps/dir/?api=1&origin={stop1Lat},{stop1Lng}&destination={lastLat},{lastLng}&waypoints={stop2Lat},{stop2Lng}|{stop3Lat},{stop3Lng}&travelmode=driving
  ```
- OSRM route fallback with Catmull-Rom geodesic spline approximation when offline ($d_{\text{road}} \approx 1.28 \times d_{\text{haversine}}$ for lowlands, $1.45 \times$ for Sierra Madre mountain legs).

### Blueprint 3: Corridor Clustering & 2-Opt TSP Optimization (Fixes ROUTE-02)
- Re-cluster offline presets in `offline-places.data.ts` to follow the East (1.5 km), North (13.8 km), and South (45.5 km) corridors.
- In backend `itinerary_generator.py`: Partition candidate selection into geographic corridor selection per day, apply 2-opt TSP ordering to activity stops, select the lunch venue nearest to the midpoint between morning and afternoon activities, and pin lodging to the final evening slot (17:30).

### Blueprint 4: Full-Stack Attribute & Spatial Filtering + True Geolocation (Fixes MAP-02, MAP-03, ROUTE-03)
- Extend `backend/app/api/v1/places.py` `GET /api/v1/places` with `municipality_name: str | None` and `price_tier: str | None` so filtering occurs in SQL before `LIMIT` truncation.
- Pass `placeId` in `viewDestinationOnMap()` deep-links; guard `onMapMoveEnd()` with `isProgrammaticFly = true` during camera flight; auto-open `selectedPlace` bottom sheet.
- Split map controls into **Locate Me** (`navigator.geolocation.getCurrentPosition`) and **Reset Province View** (`NUEVA_ECIJA_CENTER`).
- Bind real coordinates to `NearbyPlaceItem` and persist via `itineraryService.updateItinerary()`.

### Blueprint 5: Angular Router Hardening & Origin-Aware Commute Guide (Fixes ROUTE-04, ROUTE-05)
- Attach `canDeactivate: [pendingChangesGuard]` to `/itinerary/:id`.
- Replace hardcoded `this.router.navigate(['/tabs/history'])` with `this.ionRouterOutlet?.canGoBack() ? this.navCtrl.back() : ...`.
- Upgrade `commute-guide.data.ts` into a leg-aware provincial commute engine comparing previous stop against current stop:
  - Same town $\le 1.2$ km: 5–10 min walk or local tricycle (₱15–₱25).
  - Same town $> 1.2$ km: Local tricycle transfer.
  - Adjacent towns on same corridor: Direct corridor jeepney / UV Express transfer across all 32 municipalities without detour to Cabanatuan City.

---

## 5. Phased Implementation Roadmap & Verification Plan

```text
┌────────────────────────────────────────────────────────────────────────┐
│ Phase 1: Immediate Production Bug Fixes (Day 1)                        │
│ ├── MAP-01: Leaflet MarkerCluster ESM & UMD window.L unwrap            │
│ ├── MAP-02: Backend & client municipality + price tier filtering       │
│ ├── MAP-03: Deep-link pin selection with isProgrammaticFly             │
│ ├── ROUTE-02: Re-cluster offline presets (59.4 km corridors)           │
│ └── ROUTE-03: Fix nearby place coords & persistence                    │
│ Verification Gate: npm run test:unit; Playwright E2E .custom-map-pin   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Phase 2: Route Map & TSP Engine (Days 2–3)                             │
│ ├── ROUTE-01: Reusable ItineraryRouteMapComponent                     │
│ ├── ROUTE-01: OSRM road polylines + geodesic spline fallback           │
│ ├── ROUTE-01: Multi-stop Google Maps URL builder                       │
│ └── ROUTE-02: 2-opt TSP candidate clustering in generator              │
│ Verification Gate: pytest test_itineraries.py; 0 cross-backtracking    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Phase 3: Router Polish & Leg Commute (Day 4)                           │
│ ├── ROUTE-04: Attach pendingChangesGuard to /itinerary/:id             │
│ ├── ROUTE-04: History-aware back navigation & GPS Locate Me            │
│ ├── ROUTE-04: URL query-param filter synchronization                   │
│ └── ROUTE-05: Leg-aware 32-municipality commute guide                  │
│ Verification Gate: Full CI suite (npm run lint, build, test:e2e)       │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Codebase Delta Comparison (Session 72 Baseline vs. Proposal)

| Component | Proposal Requirement | Codebase Status at Session 72 | Delta / Action Item |
| :--- | :--- | :--- | :--- |
| **Map Clustering** | ESM `window.L` unwrap & `L.layerGroup()` fallback | Direct `import 'leaflet.markercluster';` | Apply Proposal 1 in `map.page.ts`. |
| **Places Dataset** | 2,673 OSM places with client caching | Implemented (`osm_places.json` + `PlaceService`) | Complete. |
| **Backend Places Filter** | `municipality_name` and `price_tier` in SQL | Has `municipality_id`, `categories`, costs | Add name & tier parameters to `GET /places`. |
| **Offline Day Presets** | 59.4 km East/North/South corridors | Has 176.2 km zig-zag presets | Update `getOfflineDayClusterPresets()` in `offline-places.data.ts`. |
| **Nearby Places** | Real coords and persistence | Has coords, lacks persistence | Save added stops via `itineraryService.updateItinerary()`. |
| **Itinerary Route Map** | Embedded route preview on all planner pages | Implemented in Detail page | Extract into reusable component for Wizard & Builder. |
| **Directions Handoff** | Multi-waypoint Google Maps URLs | Single-stop destination URLs | Add multi-stop URL builder function. |
| **Commute Guidance** | Leg-aware across 32 towns | Static Cabanatuan-only guide (8 towns) | Build `getLegCommuteInfo(prev, curr)` across 32 towns. |
| **Router Guards & Back**| `pendingChangesGuard` on `/itinerary/:id` & history back | Missing guard & hardcoded back | Attach guard in `app.routes.ts` & use `IonRouterOutlet`. |

