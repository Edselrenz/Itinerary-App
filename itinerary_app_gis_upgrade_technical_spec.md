# Technical Specification & Implementation Plan: Suggested Itinerary Generation, Live Google Places Discovery & Active GIS Route Tracking

**Target Repository:** `edselrenz/itinerary-app` (Nueva Ecija Travel Itinerary Application)  
**Frontend Stack:** [Ionic Framework v9](https://ionicframework.com/docs) + [Angular v22 (Standalone Components)](https://angular.dev/overview) + [Capacitor v8.6](https://capacitorjs.com/docs/) + [Leaflet v1.9.4](https://leafletjs.com/) (`leaflet.markercluster` v1.5.3)  
**Backend & Edge Stack:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3, SQLAlchemy 2.0, Pydantic v2, PostgreSQL / Alembic) + Cloudflare Worker Reverse Proxy (`cloudflare-worker/worker.js`)  
**Audit Mode:** Strictly Read-Only Architectural Analysis & Upgrade Specification

---

## 1. Executive Summary of Current Architecture & Gaps

The `Itinerary-App` repository currently operates as an offline-resilient, province-scoped travel planner for Nueva Ecija, Philippines. While its hybrid fallback architecture (FastAPI + PostgreSQL backed by local Ionic Storage and static TypeScript datasets) provides high reliability when the local backend is unreachable, both the **Suggested Itinerary Generation** pipeline and the **Map & Routing System** are constrained by static/pre-seeded datasets, spherical straight-line distance approximations, and external map handoffs instead of real-time geospatial discovery and in-app turn-by-turn route tracking.

| Capability Domain | Current "As-Is" Implementation | Key Architectural Gaps | Target "To-Be" Upgrade |
| :--- | :--- | :--- | :--- |
| **Place Discovery & Suggested Itinerary Generation** | Queries local PostgreSQL `places` (seeded via `scripts/seed_featured_places.py` and `scripts/import_osm.py`) or falls back to 13 hardcoded venues in `Project/src/app/core/data/offline-places.data.ts`. | Cannot discover live establishments on Google Maps; ignores real-time opening hours, user ratings, review counts, and price levels; static 3-day cluster presets repeat when offline. | Hybrid pipeline integrating [Google Places API (New) Text Search](https://developers.google.com/maps/documentation/places/web-service/text-search) & [Nearby Search (New)](https://developers.google.com/maps/documentation/places/web-service/nearby-search) with PostgreSQL upsert caching, live time-of-day operating-hours validation, and multi-factor Bayesian rating + travel-time scheduling. |
| **Map Rendering & Stop Visualization** | `Project/src/app/tabs/map/map.page.ts` renders OpenStreetMap raster tiles via [Leaflet v1.9.4](https://leafletjs.com/install.html) and groups POIs with [Leaflet.markercluster](https://github.com/leaflet/leaflet.markercluster). `itinerary-detail.page.ts` has no embedded map canvas at all. | `itinerary-detail.page.ts` only lists stops as cards and opens external URLs (`https://www.google.com/maps/dir/?api=1&destination=...`). `map.page.ts` only plots general catalog POIs—not ordered itinerary stops or multi-stop paths. | Dual-mode map architecture supporting ordered stop markers (`1..N`), multi-leg road polylines on both `map.page.ts` and an interactive map drawer/header in `itinerary-detail.page.ts`. |
| **Route Calculation & Active Navigation** | Backend `itinerary_generator.py` uses `haversine_distance_km()` (spherical great-circle distance). Frontend `commute-guide.data.ts` returns static text lookup strings per municipality. | Zero road-network geometry, no encoded polylines, no real leg-by-leg drive/transit durations, and no live GPS progress tracking (`@capacitor/geolocation` is not installed in `Project/package.json`). | Integration of [Google Routes API (`computeRoutes`)](https://developers.google.com/maps/documentation/routes/compute_route_directions) for encoded road polylines and leg durations/distances, paired with [Capacitor Geolocation (`@capacitor/geolocation`)](https://capacitorjs.com/docs/apis/geolocation) live progress snapping against active route legs. |
| **Interactive Marker Details & Reviews** | Clicking a marker in `map.page.ts` opens a custom `.poi-bottom-sheet` `<div>` displaying only basic static `Place` fields (`name`, `category`, `municipality_name`, `opening_hours`, `description`). | No Google ratings (`rating`, `userRatingCount`), no user reviews (`reviews[]`), no Google Place Photos gallery, no editorial summary, and separate non-reusable modal templates across pages. | Unified Ionic bottom-sheet modal (`ion-modal` with breakpoints `[0, 0.45, 0.85, 1.0]`) powered by on-demand [Google Place Details (New)](https://developers.google.com/maps/documentation/places/web-service/place-details) with two-tier FieldMask + TTL caching. |

---

## 2. Part 1: Current State Analysis ("As-Is" Architecture)

### 2.1 Suggested Itinerary Generation Flow

#### A. Frontend Wizard Input Capture & State Machine (`Project/src/app/features/itinerary/suggested-wizard/`)
1. **Form Initialization (`suggested-wizard.page.ts`, lines 158–166):**
   - `SuggestedWizardPage` initializes a reactive `FormGroup` with four controls:
     - `destination`: defaults to `'Nueva Ecija'` (`Validators.required`), selectable via 6 quick-destination chips (`'Bongabon'`, `'Pantabangan'`, `'Cabanatuan City'`, `'Gapan City'`, `'General Tinio'`, `'Nueva Ecija'`, lines 87–94) or free-text input (`suggested-wizard.page.html`, lines 33–40).
     - `start_date`: defaults to `toLocalIsoDate(today)` (`Validators.required`).
     - `end_date`: defaults to `toLocalIsoDate(addDaysLocal(today, 2))` (3 days, 2 nights default).
     - `daily_budget`: defaults to `3000` PHP (`Validators.required, Validators.min(0)`), with preset chips `[1500, 2500, 4000, 6000]` (line 96).
   - **Preferences Selection (`suggested-wizard.page.ts`, lines 99–107):** Stored outside the `FormGroup` in `selectedPreferences: Set<string>`, pre-populated with `new Set(['food', 'culture', 'resort'])` from 5 options (`nature`, `food`, `culture`, `shopping`, `resort`).
2. **Submission & Service Invocation (`suggested-wizard.page.ts`, lines 309–348):**
   - Calling `generateItinerary()` validates `this.form`, constructs a `SuggestedItineraryRequest` object with `save_immediately: false`, and invokes `this.itineraryService.suggestItinerary(req)`.
   - On response (`lines 329–336`), it assigns `this.generatedPlan = plan`, switches `this.viewMode = 'itinerary'`, computes the budget summary via `this.itineraryService.calculateBudgetSummary(plan)`, and populates `this.nearbyPlacesList` by calling `this.placeService.getNearbyPlaces(muni)` (synchronous static lookup).
   - **Critical Observation on Nearby Essentials (`lines 422–455`):** When a user clicks "Add to Day X" on a nearby essential item (`addNearbyPlaceToActiveDay()`), the method hardcodes coordinates `latitude: 15.63, longitude: 121.14` (Bongabon coordinates) and `planned_time: '12:00 PM'` regardless of the actual establishment's location or municipality.
3. **Persistence Handoff (`suggested-wizard.page.ts`, lines 488–552):**
   - Clicking "Accept & Save Itinerary" or "Customize in Builder" calls `acceptAndSave(targetRoute)`, which maps `this.generatedPlan` into an `ItineraryCreatePayload` and calls `this.itineraryService.createItinerary(payload)`.

#### B. Frontend Service & Offline Fallback (`Project/src/app/core/services/itinerary.service.ts`)
1. **Primary API Call with 4-Second Timeout (`itinerary.service.ts`, lines 282–306):**
   - `suggestItinerary(request: SuggestedItineraryRequest)` issues an HTTP `POST` to `${environment.apiBaseUrl}/itineraries/suggest` with `.pipe(timeout(4000))`.
   - If the backend responds within 4 seconds, the returned `Itinerary` is passed to the component. If the backend times out, returns an error, or is offline (e.g., static GitHub Pages deployment when the host laptop tunnel is down), `catchError` transparently invokes `this.generateOfflineSuggestedItinerary(request)`.
2. **Client-Side Offline Generator (`itinerary.service.ts`, lines 740–885):**
   - Calls `getOfflineCuratedPoolForItinerary()` from `offline-places.data.ts` (which contains exactly 13 curated venues across Nueva Ecija).
   - Filters `curatedPool` by substring match on `municipality` if `request.destination` is not `'nueva ecija'` (`lines 753–759`), and sorts by binary preference match (`lines 761–771`).
   - **Critical Flaw in Offline Day Assignment (`lines 773–796`):**
     - If `isProvincialOrBongabon` is true (`destination` is empty, `'nueva ecija'`, or `'bongabon'`), it ignores the preference-sorted `matchedPool` and instead pulls hardcoded day clusters from `getOfflineDayClusterPresets(curatedPool)` (`offline-places.data.ts`, lines 451–482): Day 1 is always Bongabon (4 stops), Day 2 is always Cabanatuan City/San Jose (3 stops), and Day 3 is always Gapan/General Tinio/Pantabangan (3 stops).
     - Worse, if the user selects a specific municipality like `'Cabanatuan City'` or `'Pantabangan'` (`isProvincialOrBongabon === false`), `cluster` evaluates to `null` (`line 790`) and `dayPlaces` falls back to `[curatedPool[0], curatedPool[1], curatedPool[2]]` (`lines 792–796`)—which are the first three items in `CANONICAL_OFFLINE_PLACES` (all located in Bongabon: Rohi Paperflower Cafe, Museo de Bongabon, Thornes Samgyupsal House), completely ignoring `matchedPool`!
   - Sort order is adjusted chronologically via `parseTimeToMinutes()` and `isOvernightItem()` so overnight stays (`hotel_accommodation` or `duration >= 720`) appear at the end of the day (`lines 843–853`).

#### C. Backend Algorithmic Generator (`backend/app/algorithms/itinerary_generator.py`)
When the FastAPI backend is reachable (`POST /api/v1/itineraries/suggest` in `backend/app/api/v1/itineraries.py`, lines 115–184), `generate_suggested_itinerary_data()` executes a 5-stage heuristic:
1. **Date Span Validation (`lines 180–188`):** Rejects spans exceeding 14 days.
2. **Geographic Anchor Resolution (`resolve_geographic_anchor()`, lines 65–88):**
   - Queries `Municipality` by `ILIKE` on `name` or `slug` to get `center_lat, center_lng`.
   - Falls back to querying `Place.name.ilike()`, or defaults to Nueva Ecija's center `(15.5800, 121.0000)`.
3. **Candidate Fetching via SQL Bounding Box (`lines 194–239`):**
   - Uses `settings.default_dest_radius_km` (`25.0` km in `backend/app/core/config.py`, line 32) plus a `10.0` km buffer converted to degree deltas (`111.0` km/deg) to filter `Place.is_active == True` in SQL, then refines via `haversine_distance_km()`.
   - If fewer than `min(total_days * 2, 3)` places exist within the radius, it loads all active `Place` rows from PostgreSQL (`lines 228–235`).
   - **Data Source Limitation:** The PostgreSQL `places` table only contains what was manually seeded by `scripts/seed_featured_places.py` (17 places) or batch-imported from a static Overpass JSON file via `scripts/import_osm.py`. No external API is ever queried.
4. **Greedy Slot-by-Slot Scoring (`score_place()`, lines 105–170 & `lines 250–334`):**
   - Schedules 3 fixed slots per day from `DAILY_TIME_SLOTS` (`09:00` morning activity, `12:00` lunch dining, `14:30` afternoon activity).
   - Scores each unvisited candidate `Place`:
     - Base score: `80.0` for `restaurant`/`cafe` during the `12:00` lunch slot (`10.0` otherwise); `50.0` for non-dining slots.
     - Overnight accommodation penalty: `-40.0` in morning slot, `+20.0` in later slots (`lines 126–130`).
     - Preference match: `+40.0` if `place.category in preferred_categories`, `+15.0` if any tag matches (`lines 132–138`).
     - Featured boost: `+20.0` if `place.is_featured` (`lines 140–142`).
     - Proximity score: `+30.0 - (dist * 1.2)` within `25 km` of `current_anchor_lat/lng`, or `-(dist - 25.0) * 2.0` penalty outside (`lines 144–150`).
     - Category diversity penalty: `-25.0` if `place.category` was already scheduled on the same day (`lines 152–154`).
     - Budget fit: `+10.0` if `place_cost <= remaining_daily_budget`, `-30.0` if over budget (`lines 156–169`).
   - Updates `current_anchor_lat, current_anchor_lng` to the newly selected place's coordinates (`lines 312–313`) to form a greedy nearest-neighbor chain, and re-sorts accommodations to `17:30` at the end of the day (`lines 345–366`).

#### D. Current Data Models & Limitations (`place.models.ts`, `itinerary.models.ts`, `entities.py`)
- **`Place` (`Project/src/app/core/models/place.models.ts`, lines 10–36 & `backend/app/models/entities.py`, lines 99–136):**
  - Stores basic OSM/curated fields (`id`, `name`, `category`, `latitude`, `longitude`, `municipality_id`, `address_text`, `description`, `phone`, `website`, `opening_hours` as a raw `VARCHAR(255)` string, `estimated_cost_min`, `estimated_cost_max`, `image_url`, `source_name`, `source_record_id`, `tags`).
  - **Missing Fields:** No `google_place_id` (indexed unique column), no `rating` (1.0–5.0 float), no `user_rating_count` (integer), no `price_level` (Google enum/int 0–4), no `google_types` (`string[]`), no structured `regular_opening_hours` (periods/weekday descriptions/openNow metadata), no `editorial_summary`, no `photos` metadata array (`photo_reference` / `name`, attributions), no `reviews` JSON cache, and no `google_last_synced_at` TTL timestamp.
- **`ItineraryItem` (`Project/src/app/core/models/itinerary.models.ts`, lines 3–19 & `backend/app/models/entities.py`, lines 195–227):**
  - Links to `place_id` (UUID FK to local `places.id`) or stores `custom_title`, `custom_lat`, `custom_lng`.
  - **Critical Foreign Key Constraint Issue (`backend/app/api/v1/itineraries.py`, lines 194–209):** When saving an itinerary via `POST /api/v1/itineraries`, the backend checks `Place.id.in_(all_place_ids)` and throws `404 Not Found` if any `place_id` is not a valid UUID already persisted in PostgreSQL. In offline/fallback mode (`offline-places.data.ts`), place IDs are strings like `'dest-rohi-paperflower'` or `'nb-r-1'`, which fail Pydantic UUID validation (`422 Unprocessable Content`) or FK lookup (`404`) when an authenticated user saves an offline-generated or Google-discovered itinerary unless places are upserted by `google_place_id` / `source_record_id` during save!
  - **Missing Routing Fields on `ItineraryItem` and `ItineraryDay`:** No `travel_mode`, `travel_duration_seconds`, `travel_distance_meters`, or `route_polyline` (encoded polyline from the previous stop to the current stop) to persist computed routes.

---

### 2.2 Map & Routing Implementation

#### A. Mapping Library & Initialization (`Project/src/app/tabs/map/map.page.ts`)
1. **SDK & Dependencies (`Project/package.json`, lines 38–43):**
   - Uses **[Leaflet v1.9.4](https://leafletjs.com/)** (`import * as L from 'leaflet'`) with **[Leaflet.markercluster v1.5.3](https://github.com/leaflet/leaflet.markercluster)** (`import 'leaflet.markercluster'`).
   - Renders standard raster tiles from OpenStreetMap (`environment.tileUrlTemplate = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'`, `map.page.ts`, lines 311–328).
2. **Map Instance Setup (`map.page.ts`, lines 281–357):**
   - `initMap()` binds to `#mapElement` (`<div #mapElement id="leaflet-map" class="map-canvas"></div>`), centering on `NUEVA_ECIJA_CENTER = [15.58, 121.0]` at zoom `10`, constrained to `NUEVA_ECIJA_BOUNDS = [[15.05, 120.55], [16.25, 121.55]]` with `maxBoundsViscosity: 0.8`.
   - Initializes a single `L.MarkerClusterGroup` (`this.markerCluster`, lines 331–338) with `maxClusterRadius: 40`, `spiderfyOnMaxZoom: true`, and `chunkedLoading: true`.
3. **Viewport-Bounded Querying (`map.page.ts`, lines 349–372 & 393–469):**
   - Listening to `map.on('moveend')` triggers a 350ms debounced `onMapMoveEnd()`, which calls `this.loadPlaces(this.map.getBounds())` when `zoom >= 10`.
   - `loadPlaces()` calls `this.placeService.searchPlaces(searchParams)` (`GET /api/v1/places?min_lat=...&max_lat=...&min_lng=...&max_lng=...&limit=150`), and applies client-side filters (`applyLocalFilters()`, lines 471–502) for `selectedMunicipality` and `selectedPriceTier`.

#### B. Marker Rendering & Click Interaction (`map.page.ts`, lines 507–569 & `map.page.html`, lines 323–433)
1. **Marker Creation (`updateMarkers()`, lines 507–569):**
   - Clears `this.markerCluster` on every filter/pan update and iterates through `this.places`.
   - Constructs a custom HTML pin using `L.divIcon` (`.custom-map-pin`, styled in `map.page.scss`, lines 348–387 as a `-45deg` rotated teardrop in `#0084ff`, or a gradient for `.pin-featured`).
   - **No Stop Numbering or Active Itinerary Layer:** All markers are identical unnumbered blue teardrops inside a single cluster group. If an itinerary is active, its stops are not distinguished from general POIs, nor are they excluded from clustering so the user can see their sequential route.
2. **Marker Click Behavior (`lines 546–558`):**
   - Clicking a marker stops event propagation, sets `this.selectedPlace = place`, triggers `this.cdr.detectChanges()`, and pans the map to `[place.latitude, place.longitude]`.
   - Setting `this.selectedPlace` conditionally renders a custom CSS overlay `<div class="poi-bottom-sheet">` in `map.page.html` (`lines 324–433`).
   - **No On-Demand Details Fetch:** The bottom sheet only renders properties already present in the list response (`selectedPlace.name`, `municipality_name`, `estimated_cost_min/max`, `source_name`, `opening_hours`, `description`, `address_text`, `tags`). It makes zero API calls for reviews, ratings, photos, or live opening status.
   - **Directions Handoff Only (`map.page.ts`, lines 738–743):** Clicking "Get Directions (Google Maps)" simply opens an external tab to `https://www.google.com/maps/dir/?api=1&destination=${place.latitude},${place.longitude}`.

#### C. Itinerary Detail View & Absence of Routing (`Project/src/app/features/itinerary/itinerary-detail/`)
1. **No Map or Polyline Rendering (`itinerary-detail.page.ts` & `.html`):**
   - `ItineraryDetailPage` does not import Leaflet or render any map view. Stops are displayed purely as vertical cards grouped by day (`itinerary-detail.page.html`, lines 193–225).
   - Clicking a stop opens an `ion-modal` (`lines 474–528`) that displays `getStopTitle(selectedStop)`, `getStopDescription(selectedStop)` (which defaults to the hardcoded string `'Explore the river and limestone formations. Enjoy sightseeing and take photos.'` at `itinerary-detail.page.ts`, line 521 when `description` and `notes` are empty!), and static municipality-level commute text from `commute-guide.data.ts`.
   - Clicking "Open in Google Maps" (`openInGoogleMaps()`, lines 777–791) opens a single-destination external link (`https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`)—it does not even pass multi-stop waypoints or origin coordinates.
2. **Zero Geolocation Integration:**
   - Neither `@capacitor/geolocation` nor `navigator.geolocation` is used anywhere in `Project/src/`. Users cannot see their current position on `map.page.ts` or track their progress along an active itinerary.

---

## 3. Data Model & Schema Changes ("To-Be" Design)

To support Google Places API (New) discovery, rich Place Details (reviews, ratings, photos, opening hours), and persisted multi-leg route geometry, we must evolve both the frontend TypeScript interfaces and the backend SQLAlchemy/Pydantic schemas using a backwards-compatible expand-and-contract migration.

### 3.1 Frontend TypeScript Interfaces

#### A. `Project/src/app/core/models/place.models.ts`
```typescript
export interface PlacePhotoAttribution {
  displayName: string;
  uri?: string | null;
  photoUri?: string | null;
}

export interface PlacePhoto {
  /** Google Places API (New) photo resource name: places/{place_id}/photos/{photo_reference} */
  name: string;
  widthPx: number;
  heightPx: number;
  authorAttributions: PlacePhotoAttribution[];
  /** Resolved proxy or cached CDN URL for direct <img [src]> rendering */
  url?: string | null;
}

export interface PlaceReview {
  name: string;
  relativePublishTimeDescription: string;
  rating: number;
  text: string;
  originalText?: string | null;
  authorName: string;
  authorUri?: string | null;
  authorPhotoUri?: string | null;
  publishTime: string;
}

export interface PlaceOpeningHoursPeriodPoint {
  day: number; // 0 (Sunday) to 6 (Saturday)
  hour: number; // 0 to 23
  minute: number; // 0 to 59
}

export interface PlaceOpeningHoursPeriod {
  open: PlaceOpeningHoursPeriodPoint;
  close?: PlaceOpeningHoursPeriodPoint | null;
}

export interface PlaceRegularOpeningHours {
  openNow?: boolean | null;
  periods?: PlaceOpeningHoursPeriod[];
  weekdayDescriptions?: string[];
  nextOpenTime?: string | null;
  nextCloseTime?: string | null;
}

export interface Place {
  id: string;
  /** Canonical Google Place ID (e.g., "ChIJ...") for Places API (New) & Directions */
  google_place_id?: string | null;
  name: string;
  category: string;
  /** Raw Google place types (e.g., ["restaurant", "food", "point_of_interest"]) */
  google_types?: string[];
  latitude: number;
  longitude: number;
  municipality_id?: string | null;
  municipality_name?: string | null;
  address_text?: string | null;
  /** Curated or OSM description */
  description?: string | null;
  /** Google Places editorialSummary.text */
  editorial_summary?: string | null;
  phone?: string | null;
  website?: string | null;
  /** Legacy human-readable string fallback (e.g., "08:00-17:00") */
  opening_hours?: string | null;
  /** Structured Google regularOpeningHours metadata */
  regular_opening_hours?: PlaceRegularOpeningHours | null;
  /** Google average user rating (1.0 - 5.0) */
  rating?: number | null;
  /** Total number of Google user ratings */
  user_rating_count?: number | null;
  /** Google priceLevel mapped to numeric tier (0 = Free, 1 = Inexpensive, 2 = Moderate, 3 = Expensive, 4 = Very Expensive) */
  price_level?: number | null;
  estimated_cost_min?: number | null;
  estimated_cost_max?: number | null;
  cost_currency: string;
  image_url?: string | null;
  image_license?: string | null;
  /** Rich photo gallery metadata from Google Places */
  photos?: PlacePhoto[];
  /** Top user reviews (up to 5 returned by Google Place Details API) */
  reviews?: PlaceReview[];
  business_status?: 'OPERATIONAL' | 'CLOSED_TEMPORARILY' | 'CLOSED_PERMANENTLY' | string | null;
  google_maps_uri?: string | null;
  source_name: string;
  source_record_id: string;
  source_url?: string | null;
  imported_at: string;
  verified_at?: string | null;
  /** ISO timestamp when full Place Details (reviews/photos/hours) were last fetched */
  details_cached_at?: string | null;
  is_featured: boolean;
  tags: string[];
  directions_url: string;
}

export interface PlaceSearchParams {
  q?: string;
  categories?: string[] | string;
  municipality_id?: string;
  municipality_name?: string;
  featured?: boolean;
  min_lat?: number;
  max_lat?: number;
  min_lng?: number;
  max_lng?: number;
  min_rating?: number;
  open_now?: boolean;
  include_live_google?: boolean;
  limit?: number;
  offset?: number;
}
```

#### B. `Project/src/app/core/models/itinerary.models.ts`
```typescript
import type { Place } from './place.models';

export type TravelMode = 'DRIVE' | 'TWO_WHEELER' | 'WALK' | 'TRANSIT';

export interface RouteStepInstruction {
  instruction: string;
  maneuver?: string | null;
  distance_meters: number;
  duration_seconds: number;
  start_lat: number;
  start_lng: number;
  end_lat: number;
  end_lng: number;
  encoded_polyline?: string | null;
}

export interface RouteLegMetadata {
  origin_item_id?: string | null;
  destination_item_id: string;
  travel_mode: TravelMode;
  distance_meters: number;
  duration_seconds: number;
  /** Google Encoded Polyline string representing actual road geometry for this leg */
  encoded_polyline: string;
  steps?: RouteStepInstruction[];
  computed_at: string;
}

export interface ItineraryItem {
  id: string;
  day_id: string;
  place_id?: string | null;
  /** Direct Google Place ID reference so unpersisted/live Google places can be resolved or upserted on save */
  google_place_id?: string | null;
  custom_title?: string | null;
  custom_lat?: number | null;
  custom_lng?: number | null;
  sort_order: number;
  planned_time?: string | null;
  duration_minutes: number;
  notes?: string | null;
  estimated_cost_min?: number | null;
  estimated_cost_max?: number | null;
  /** Routing telemetry from the preceding stop (null for first stop of the day unless routed from user origin) */
  travel_mode_from_prev?: TravelMode | null;
  travel_distance_meters?: number | null;
  travel_duration_seconds?: number | null;
  route_polyline_from_prev?: string | null;
  created_at?: string;
  updated_at?: string;
  place?: Place | null;
}

export interface ItineraryDay {
  id: string;
  itinerary_id: string;
  day_number: number;
  travel_date: string;
  title?: string | null;
  /** Combined encoded overview polyline for the entire day's route */
  day_overview_polyline?: string | null;
  total_distance_meters?: number | null;
  total_travel_duration_seconds?: number | null;
  route_legs?: RouteLegMetadata[];
  items: ItineraryItem[];
}

export interface SuggestedItineraryRequest {
  title?: string;
  destination: string;
  start_date: string;
  end_date: string;
  daily_budget: number;
  preferences: string[];
  /** Optional user starting coordinates or municipality center bias */
  origin_lat?: number;
  origin_lng?: number;
  travel_mode?: TravelMode;
  min_rating?: number;
  include_live_places?: boolean;
  save_immediately?: boolean;
}
```

### 3.2 Backend Database & ORM Schema Changes (`backend/app/models/entities.py` & Alembic Migration `0002`)

Add a new reversible Alembic migration `backend/alembic/versions/0002_google_places_and_routing.py` that expands `places`, `itinerary_days`, and `itinerary_items`, and introduces a dedicated `google_api_cache` table for query/route caching:

```python
# Additions to Place model in backend/app/models/entities.py
class Place(Base):
    # ... existing columns ...
    google_place_id: Mapped[str | None] = mapped_column(
        String(128), unique=True, index=True, nullable=True
    )
    google_types: Mapped[list[str]] = mapped_column(JsonType, default=list, nullable=False)
    editorial_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    regular_opening_hours: Mapped[dict | None] = mapped_column(JsonType, nullable=True)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)
    user_rating_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    price_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    photos: Mapped[list[dict]] = mapped_column(JsonType, default=list, nullable=False)
    reviews: Mapped[list[dict]] = mapped_column(JsonType, default=list, nullable=False)
    business_status: Mapped[str | None] = mapped_column(String(40), nullable=True)
    google_maps_uri: Mapped[str | None] = mapped_column(String(500), nullable=True)
    details_cached_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

# Additions to ItineraryDay model in backend/app/models/entities.py
class ItineraryDay(Base):
    # ... existing columns ...
    day_overview_polyline: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_distance_meters: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_travel_duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    route_legs: Mapped[list[dict]] = mapped_column(JsonType, default=list, nullable=False)

# Additions to ItineraryItem model in backend/app/models/entities.py
class ItineraryItem(Base):
    # ... existing columns ...
    google_place_id: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    travel_mode_from_prev: Mapped[str | None] = mapped_column(String(20), nullable=True)
    travel_distance_meters: Mapped[int | None] = mapped_column(Integer, nullable=True)
    travel_duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    route_polyline_from_prev: Mapped[str | None] = mapped_column(Text, nullable=True)

# New table for caching Google Places Search & Routes API responses
class GeospatialCache(Base):
    """TTL cache for Google Places Search queries and Routes API polylines."""
    __tablename__ = "geospatial_cache"

    cache_key: Mapped[str] = mapped_column(String(255), primary_key=True)
    cache_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False) # 'places_search' | 'route_matrix' | 'directions'
    payload: Mapped[dict] = mapped_column(JsonType, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
```

---

## 4. Google Maps & Places API Integration Architecture

### 4.1 Security Boundary & Proxy Architecture
Per security engineering best practices ([OWASP API Security](https://owasp.org/projects/cheat-sheet-series)) and [Google Maps Platform API Key Best Practices](https://developers.google.com/maps/documentation/places/web-service/get-api-key):
- **Never expose the unrestricted server-side `GOOGLE_MAPS_API_KEY` in the Angular frontend bundle (`environment.ts` / `environment.prod.ts`).**
- All calls to [Places API (New)](https://developers.google.com/maps/documentation/places/web-service/overview) (`places:searchText`, `places:searchNearby`, `places/{placeId}`, and `places/{placeId}/photos/{photoRef}/media`) and [Routes API (`computeRoutes`)](https://developers.google.com/maps/documentation/routes/compute_route_directions) must be routed through:
  1. **Primary Backend Proxy:** FastAPI (`backend/app/services/google_maps_service.py`) reading `settings.google_maps_api_key` from `.env`.
  2. **Edge Fallback Proxy (`cloudflare-worker/worker.js`):** Because the app is deployed on GitHub Pages (`https://edselrenz.github.io`) behind `cloudflare-worker/worker.js`, when the developer laptop's local FastAPI server is offline, the Cloudflare Worker can optionally handle `/api/v1/places/google-proxy/*` and `/api/v1/routes/compute` directly using a Worker secret (`env.GOOGLE_MAPS_API_KEY`) and Cloudflare KV (`env.GEO_CACHE_KV`) before falling back to `offline-places.data.ts`.

### 4.2 Google API Endpoints & Strict FieldMask Strategy
In [Places API (New)](https://developers.google.com/maps/documentation/places/web-service/usage-and-billing) and [Routes API](https://developers.google.com/maps/documentation/routes/usage-and-billing), Google bills every request at the highest SKU tier among the fields requested in `X-Goog-FieldMask`. We must enforce **three tiered FieldMasks** so bulk discovery never triggers Atmosphere/Review billing until a user explicitly clicks a marker:

| Operation | Google Endpoint | HTTP Method | Exact `X-Goog-FieldMask` | Billing SKU Tier & Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **1. Discovery: Text Search (New)** | `https://places.googleapis.com/v1/places:searchText` | `POST` | `places.id,places.displayName,places.formattedAddress,places.location,places.types,places.primaryType,places.rating,places.userRatingCount,places.priceLevel,places.regularOpeningHours,places.photos,places.businessStatus,places.googleMapsUri` | **Text Search Enterprise SKU**: Fetches candidate places for itinerary generation & map search with coordinates, ratings, price level, and opening hours. |
| **2. Discovery: Nearby Search (New)** | `https://places.googleapis.com/v1/places:searchNearby` | `POST` | `places.id,places.displayName,places.formattedAddress,places.location,places.types,places.primaryType,places.rating,places.userRatingCount,places.priceLevel,places.regularOpeningHours,places.photos,places.businessStatus,places.googleMapsUri` | **Nearby Search Enterprise SKU**: Discovers radial POIs around a day's anchor coordinate or nearby essentials (`restaurant`, `hospital`, `pharmacy`, `convenience_store`). |
| **3. On-Demand Marker Click: Place Details (New)** | `https://places.googleapis.com/v1/places/{place_id}` | `GET` | `id,displayName,formattedAddress,location,types,primaryType,rating,userRatingCount,priceLevel,regularOpeningHours,currentOpeningHours,editorialSummary,reviews,photos,nationalPhoneNumber,websiteUri,googleMapsUri,businessStatus` | **Place Details Enterprise + Atmosphere SKU**: Triggered **only** when a user clicks a map marker or itinerary stop card to view `editorialSummary`, `reviews[]` (up to 5 user reviews), and full photo gallery. |
| **4. Place Photo Media Proxy** | `https://places.googleapis.com/v1/{photo.name}/media?maxWidthPx=800&skipHttpRedirect=true` | `GET` | *(Query params: `maxWidthPx=800`, `key=...`)* | **Place Photo SKU**: Resolves `lh3.googleusercontent.com` signed CDN photo URLs without leaking the API key to the browser `<img>` tag. |
| **5. Multi-Stop Route Calculation: Compute Routes** | `https://routes.googleapis.com/directions/v2:computeRoutes` | `POST` | `routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline,routes.legs.duration,routes.legs.distanceMeters,routes.legs.polyline.encodedPolyline,routes.legs.startLocation,routes.legs.endLocation,routes.legs.steps.distanceMeters,routes.legs.steps.staticDuration,routes.legs.steps.polyline.encodedPolyline,routes.legs.steps.navigationInstruction` | **Routes API Compute Routes Basic/Advanced SKU**: Computes road polylines, leg distances, durations, and turn-by-turn steps between ordered stops. |

### 4.3 Multi-Layer Quota & Caching Strategy
To stay compliant with Google Maps Platform Terms of Service while minimizing billable calls:
1. **Place ID Indefinite Storage + Metadata 7-Day TTL (`places` table):**
   - `google_place_id` is stored permanently on `places.google_place_id`.
   - Basic discovery metadata (`name`, `latitude`, `longitude`, `rating`, `user_rating_count`, `price_level`, `regular_opening_hours`, first `image_url`) is upserted into PostgreSQL `places` with `verified_at = utcnow()`. Subsequent itinerary generations within **7 days** reuse cached `Place` rows within the bounding box if `count >= 15`, avoiding repeat `searchText`/`searchNearby` calls.
2. **Rich Details 24-Hour TTL (`details_cached_at` + Client `IonicStorage`):**
   - When a user clicks a marker (`GET /api/v1/places/{id}/details` or `GET /api/v1/places/google/{google_place_id}/details`), the backend checks `place.details_cached_at`. If `details_cached_at` is within **24 hours** and `reviews` / `editorial_summary` are populated, it returns the PostgreSQL row immediately (`0` external API calls).
   - On the frontend, `PlaceService` caches fetched rich `Place` objects in an in-memory `Map<string, { place: Place; expiresAt: number }>` backed by `@ionic/storage-angular` (`ne_place_details_cache_v1`) with a 24-hour TTL.
3. **Deterministic Route Hash Caching (`geospatial_cache` table):**
   - Route requests are hashed by `sha256(f"{travel_mode}:{ ordered_place_ids_or_latlngs }")`.
   - Computed polylines and legs are stored both on `itinerary_days.route_legs` / `itinerary_items.route_polyline_from_prev` and in `geospatial_cache` with a **14-day TTL**. Editing stop notes or times does not recompute routes; only adding, deleting, or reordering stops invalidates that day's route hash.

---

## 5. Part 2: Target Architecture & Upgrade Design

### 5.1 Capability 1: Real-World Place Discovery via Google Places API (New)

#### A. Hybrid Discovery Pipeline Architecture
```
[SuggestedWizardPage]
       │ POST /api/v1/itineraries/suggest (destination, dates, budget, preferences, min_rating)
       ▼
[FastAPI: itinerary_generator.py]
       ├─► 1. Resolve Geographic Anchor (Municipality table -> Google Text Search Geocoding fallback)
       ├─► 2. Query Local PostgreSQL `places` within anchor bounding box
       ├─► 3. Hybrid Sufficiency Check:
       │      Are there >= (total_days * 6) active places matching preferences with fresh Google metadata (< 7 days)?
       │      ├─► YES: Use local DB pool directly
       │      └─► NO: Invoke `GoogleMapsService.discover_places_for_itinerary()`
       │               ├─► Parallel `places:searchNearby` (around anchor_lat/lng, radius=15km..25km, includedTypes mapped from preferences)
       │               ├─► Optional `places:searchText` ("top tourist attractions and restaurants in {destination}, Nueva Ecija")
       │               └─► Upsert discovered places into PostgreSQL `places` (on_conflict `google_place_id`)
       ├─► 4. Merge Curated Featured Places + Newly Upserted Google Places + OSM Places (Deduplicated by `google_place_id` or Haversine < 75m + fuzzy name match)
       ├─► 5. Multi-Factor Scoring, Time-of-Day Opening Hours Gate & Route-Aware Sequencing
       └─► 6. Compute Day Route Polylines via `GoogleMapsService.compute_day_route()` & Return `ItineraryOut`
```

#### B. Preference-to-Google-Place-Type Mapping (`backend/app/services/google_maps_service.py`)
Map the wizard's preference keys and the map's 16 canonical categories to official [Google Place Types (New) Table A](https://developers.google.com/maps/documentation/places/web-service/place-types):

| Wizard Preference Key | App Canonical Category | Google Places API (New) `includedTypes` |Price / Budget Mapping |
| :--- | :--- | :--- | :--- |
| `nature` | `nature_park`, `tourist_attraction` | `["national_park", "park", "hiking_area", "tourist_attraction", "historical_landmark"]` | ₱0 – ₱500 |
| `food` | `restaurant`, `cafe` | `["restaurant", "cafe", "bakery", "coffee_shop", "barbecue_restaurant"]` | `PRICE_LEVEL_INEXPENSIVE` (₱150–₱350), `MODERATE` (₱350–₱800), `EXPENSIVE` (₱800+) |
| `culture` | `museum_cultural`, `church_religious` | `["museum", "art_gallery", "cultural_center", "church", "place_of_worship", "historical_landmark"]` | ₱0 – ₱200 |
| `shopping` | `shopping_market`, `convenience_store` | `["shopping_mall", "market", "supermarket", "gift_shop", "convenience_store"]` | ₱100 – ₱1,000 |
| `resort` | `resort_swimming`, `hotel_accommodation` | `["resort_hotel", "hotel", "Water_park", "swimming_pool", "campground", "lodging"]` | ₱500 – ₱6,000 |

#### C. Upgraded Recommendation & Scheduling Algorithm (`backend/app/algorithms/itinerary_generator.py`)
Replace the static Haversine-only `score_place()` with a **6-factor Google-aware scoring and constraint function**:
1. **Hard Operating Hours Gate (`is_open_during_slot()`):**
   - Inspects `place.regular_opening_hours["periods"]` against the target `travel_date.weekday()` (converting Python Monday=0..Sunday=6 to Google Sunday=0..Saturday=6) and `slot["planned_time"]` (`09:00`, `12:00`, `14:30`, `18:00`).
   - If a venue has verified `regular_opening_hours` and is **closed** during the slot window, apply a `-200.0` penalty (effectively excluding it from that slot while allowing it in open slots, e.g., night markets at `18:00`).
   - Permanently or temporarily closed venues (`business_status != "OPERATIONAL"`) are filtered out upfront.
2. **Bayesian Quality Score (`0` to `+35` points):**
   - Compute a confidence-weighted rating score so a 5.0-star place with 1 review does not beat a 4.6-star landmark with 800 reviews:
     $$W = \frac{v}{v + m} R + \frac{m}{v + m} C$$
     where $R = \text{place.rating}$, $v = \text{place.user\_rating\_count}$, $m = 25$ (minimum review threshold), and $C = 4.1$ (provincial mean rating).
   - Score boost: `max(0.0, (W - 3.5) * 23.3)` (up to `+35.0` pts for a 5.0 Bayesian rating).
3. **Price Level & Daily Budget Fit (`-40` to `+15` points):**
   - If `place.estimated_cost_min` is null, infer estimated PHP cost range from Google's `price_level` and category:
     - `PRICE_LEVEL_FREE` (0): `₱0`
     - `PRICE_LEVEL_INEXPENSIVE` (1): `₱120 – ₱300`
     - `PRICE_LEVEL_MODERATE` (2): `₱350 – ₱750`
     - `PRICE_LEVEL_EXPENSIVE` (3): `₱800 – ₱2,000`
     - `PRICE_LEVEL_VERY_EXPENSIVE` (4): `₱2,500 – ₱6,000`
4. **2-Opt Intra-Day Route Ordering + Real Travel Time Scheduling:**
   - Once the day's candidate stops (Morning Activity, Lunch Dining, Afternoon Activity, Evening Dining/Stay) are selected, run a quick **2-Opt / TSP permutation check** on the non-fixed activity stops to minimize total Haversine distance before calling `GoogleMapsService.compute_day_route()`.
   - Use the returned `legs[i].duration_seconds` from Google Routes API to dynamically compute each subsequent stop's `planned_time`:
     $$\text{Stop}_{i}.\text{planned\_time} = \text{Stop}_{i-1}.\text{planned\_time} + \text{Stop}_{i-1}.\text{duration\_minutes} + \lceil \text{Leg}_{i-1 \to i}.\text{duration\_minutes} / 15 \rceil \times 15$$
     This eliminates fixed, unrealistic schedule gaps when two stops are 40 minutes apart by road.

---

### 5.2 Capability 2: Active Itinerary Route Tracking & Turn-by-Turn Path Rendering

#### A. Google Routes API Integration (`POST /api/v1/itineraries/{id}/compute-routes` & `/api/v1/routes/compute`)
1. **Backend Route Computation (`backend/app/services/google_maps_service.py`):**
   - Calls `https://routes.googleapis.com/directions/v2:computeRoutes` with:
     - `origin`: Stop 1 (`placeId: item.google_place_id` or `location: { latLng: { latitude, longitude } }`)
     - `destination`: Stop $N$
     - `intermediates`: Stops $2 \dots N-1$
     - `travelMode`: `"DRIVE"` (default), `"TWO_WHEELER"`, `"WALK"`, or `"TRANSIT"`
     - `routingPreference`: `"TRAFFIC_AWARE"` (for `DRIVE` / `TWO_WHEELER`)
     - `polylineQuality`: `"OVERVIEW"` and `polylineEncoding`: `"ENCODED_POLYLINE"`
   - **Graceful Open-Source Routing Fallback (OSRM):** If `GOOGLE_MAPS_API_KEY` is unconfigured in local dev or quota is exhausted, fall back to OSRM (`https://router.project-osrm.org/route/v1/driving/...`) or Haversine straight-line polyline encoding with a `35 km/h` provincial road speed estimate so route polylines always render on the map.

#### B. Multi-Leg Polyline & Ordered Stop Marker Rendering in Leaflet (`map.page.ts` & `itinerary-detail.page.ts`)
1. **Dedicated Leaflet Layer Groups (`Project/src/app/core/services/route-tracking.service.ts` + `map.page.ts`):**
   - Keep `this.markerCluster` (`L.MarkerClusterGroup`) for general background POI discovery.
   - Add three dedicated, **unclustered** `L.LayerGroup` instances added directly to `this.map` above the cluster layer:
     - `this.routePolylineLayer = L.layerGroup().addTo(this.map)`: Renders the active day's road geometry.
     - `this.itineraryStopsLayer = L.layerGroup().addTo(this.map)`: Renders numbered sequence markers (`1`, `2`, `3`, `4`) with high `zIndexOffset: 1000` so itinerary stops are never swallowed into blue cluster bubbles.
     - `this.userLocationLayer = L.layerGroup().addTo(this.map)`: Renders the live GPS accuracy halo (`L.circle`) and pulsing directional user puck (`L.marker` with heading rotation).
2. **Multi-Leg Polyline Styling & Directional Indicators:**
   - Decode each `RouteLegMetadata.encoded_polyline` using a lightweight zero-dependency Google Polyline decoder utility (`Project/src/app/core/utils/polyline.util.ts`, ~35 lines of TypeScript).
   - For each leg $i \to i+1$:
     - Render an outer casing polyline (`L.polyline(latLngs, { color: '#1e3a8a', weight: 8, opacity: 0.85, lineCap: 'round', lineJoin: 'round' })`).
     - Render an inner active path polyline (`L.polyline(latLngs, { color: isCompletedLeg ? '#94a3b8' : '#0084ff', weight: 5, opacity: 1.0, dashArray: travelMode === 'WALK' ? '6, 8' : undefined })`).
     - Render directional chevron markers along each leg's midpoint (computing bearing $\theta = \text{atan2}(\Delta\text{lng}, \Delta\text{lat})$ and placing a rotated SVG arrow `L.divIcon`) plus a floating leg pill (`"14.2 km • 22 mins"`) clickable to inspect turn-by-turn steps.
3. **Interactive Map in `itinerary-detail.page.ts` & Deep-Link to `map.page.ts`:**
   - Add an embedded collapsible/expandable Leaflet route map card at the top of `itinerary-detail.page.html` (showing the active `selectedDay`'s numbered stops and road polylines) AND a primary **"Track Active Route on Map"** button that navigates to `/tabs/map?itineraryId=${itinerary.id}&day=${activeDay.day_number}&track=true`.

#### C. Live User Location Tracking & Route Progress Snapping (`@capacitor/geolocation`)
1. **Dependencies & Native Permissions:**
   - Add `@capacitor/geolocation` (`^8.0.0`, matching Capacitor v8.6 in `Project/package.json`).
   - Configure Android permissions (`ACCESS_COARSE_LOCATION`, `ACCESS_FINE_LOCATION`) in `Project/android/app/src/main/AndroidManifest.xml`.
2. **Continuous Watch & Snap-to-Polyline Progress (`RouteTrackingService`):**
   - Start tracking via `Geolocation.watchPosition({ enableHighAccuracy: true, timeout: 10000, maximumAge: 3000 }, callback)` on native Capacitor, with automatic fallback to `navigator.geolocation.watchPosition` in desktop/mobile browsers.
   - On each GPS fix `(userLat, userLng, accuracy, heading)`:
     - Project the user's coordinate onto the nearest segment $[A, B]$ of the active day's decoded polyline (`projectPointOnSegment()`).
     - Split the active leg polyline at the projected point into:
       - **Traveled Segment:** Rendered in muted slate (`#94a3b8`, `opacity: 0.6`).
       - **Remaining Segment:** Rendered in vibrant navigation blue (`#0084ff`, `weight: 6`).
     - Compute real-time remaining distance and ETA to the next stop (`nextStop`), automatically advancing `activeLegIndex` when `haversineDistance(userPos, nextStop) <= 80` meters (arrival geofence) and displaying a live top/bottom navigation HUD bar (`"Next: Museo de Bongabon • 2.4 km (5 mins)"`).

---

### 5.3 Capability 3: Interactive Map Markers with Rich Place Details (Reviews & Descriptions)

#### A. On-Demand Marker Click & Rich Details Flow
1. **Triggering Rich Place Details:**
   - When a user clicks any POI marker in `map.page.ts`, a numbered itinerary stop marker, or a stop card in `suggested-wizard.page.ts` / `itinerary-detail.page.ts`:
     - Immediately open the unified `<app-place-detail-sheet>` modal displaying the already-loaded basic fields (`name`, `category`, `municipality_name`, `latitude`, `longitude`, cached `rating`, and hero image) so the UI responds in `<16ms`.
     - Concurrently invoke `this.placeService.getRichPlaceDetails(place.id, place.google_place_id)`:
       - Checks client L1/L2 cache (`Map` + `IonicStorage` TTL 24h).
       - On cache miss, calls `GET /api/v1/places/{place_id}/details` (or `GET /api/v1/places/google/{google_place_id}/details`).
       - While fetching, renders skeleton shimmer placeholders inside the modal for the **Editorial Summary**, **Opening Hours Schedule**, **Photo Carousel**, and **User Reviews** sections.
       - If offline, displays cached metadata plus an explicit badge: `"Offline Mode — Live Google reviews & current open status unavailable"`.

#### B. Reusable UI/UX Component Specification (`PlaceDetailSheetComponent`)
Following the project's Ionic Angular standalone component architecture and intentional design principles (avoiding generic AI card clutter and unifying the duplicated modals in `map.page.html`, `suggested-wizard.page.html`, and `itinerary-detail.page.html`):
- **Component Location:** `Project/src/app/core/components/place-detail-sheet/place-detail-sheet.component.{ts,html,scss}`
- **Container:** `<ion-modal [isOpen]="isOpen" [initialBreakpoint]="0.55" [breakpoints]="[0, 0.55, 0.92, 1.0]" [backdropBreakpoint]="0.55">`
  - At breakpoint `0.55` (peek state), the user can still see the active map marker and route polyline in the top 45% of the viewport while inspecting the place's photo, rating, open status, summary, and primary CTAs.
  - Dragging up to `0.92` or `1.0` reveals the full horizontal photo gallery, expandable 7-day `weekdayDescriptions` schedule, local commute guide, and scrollable Google user reviews.
- **Visual & Information Hierarchy:**
  1. **Swipe Handle & Media Header:** Horizontal snap-scroll gallery of Google Place Photos (`photos[]` resolved via backend photo proxy, falling back to `placeService.getPlaceImage()`), with a floating Google attribution pill (`"Photo by {authorAttributions[0].displayName}"`) required by Google Maps Platform Terms of Service.
  2. **Identity & Live Status Bar:**
     - Category pill + Municipality tag.
     - Place Title (`h2`) + Price Tier badge (`₱` to `₱₱₱₱` or verified PHP range).
     - **Rating & Review Summary Row:** Star icon + numeric rating (`4.7 ★`), review count (`(342 Google reviews)`), and live status pill (`Open Now • Closes 9:00 PM` in emerald `#10b981` or `Closed • Opens 8:00 AM` in rose `#e11d48` derived from `regular_opening_hours`).
  3. **Primary Action Bar (Sticky or Top-Accessible):**
     - Context-aware primary CTAs: `"Add to Active Day"` / `"Start Trip Here"` / `"Route Here Now (In-App)"` + secondary `"Open in Google Maps"` (`google_maps_uri` or `directions_url`).
  4. **Editorial Summary & Curated Description:**
     - Displays `editorial_summary` (from Google) and/or `description` (from local curation), clearly attributed.
  5. **Expandable Opening Hours & Contact Accordion:**
     - Shows today's hours upfront; expands to show all 7 `weekdayDescriptions`, `phone` (`tel:` link), `website`, and `address_text`.
  6. **User Reviews Feed (`reviews[]`):**
     - Rating distribution header + vertical stack of up to 5 Google user review cards showing author avatar (`authorPhotoUri` with initials fallback), `authorName`, `relativePublishTimeDescription` (e.g., `"2 weeks ago"`), 5-star visual indicator, and expandable review text (`text`).
  7. **Local Commute Guide Integration:**
     - Preserves the existing Nueva Ecija public transit card (`getCommuteInfoForMunicipality()` from `commute-guide.data.ts`) beneath reviews so commuters still have local tricycle/UV Express terminal guidance alongside live road routing.

---

## 6. File-by-File Implementation Plan

### 6.1 Backend (FastAPI & PostgreSQL)

| Action | File Path | Affected Classes / Functions | Step-by-Step Logic Changes Required |
| :--- | :--- | :--- | :--- |
| **MODIFY** | `backend/app/core/config.py` | `Settings` | 1. Add `google_maps_api_key: str = ""` loaded from `.env` (`GOOGLE_MAPS_API_KEY`).<br>2. Add `google_places_cache_ttl_hours: int = 168` (7 days for discovery) and `google_details_cache_ttl_hours: int = 24` (24 hours for reviews/details).<br>3. Add `google_routes_cache_ttl_hours: int = 336` (14 days for route polylines). |
| **MODIFY** | `backend/app/models/entities.py` | `Place`, `ItineraryDay`, `ItineraryItem`, `GeospatialCache` (new) | 1. Add `google_place_id` (unique, indexed), `google_types`, `editorial_summary`, `regular_opening_hours`, `rating`, `user_rating_count`, `price_level`, `photos`, `reviews`, `business_status`, `google_maps_uri`, and `details_cached_at` to `Place`.<br>2. Add `day_overview_polyline`, `total_distance_meters`, `total_travel_duration_seconds`, and `route_legs` to `ItineraryDay`.<br>3. Add `google_place_id`, `travel_mode_from_prev`, `travel_distance_meters`, `travel_duration_seconds`, and `route_polyline_from_prev` to `ItineraryItem`.<br>4. Define `GeospatialCache` ORM model for caching search queries and routes. |
| **CREATE** | `backend/alembic/versions/0002_google_places_and_routing.py` | `upgrade()`, `downgrade()` | 1. Author Alembic migration adding the new nullable columns to `places`, `itinerary_days`, and `itinerary_items`.<br>2. Create `ix_places_google_place_id` unique index and `ix_places_rating` index.<br>3. Create `geospatial_cache` table with index on `expires_at`. |
| **MODIFY** | `backend/app/schemas/place.py` | `PlaceOut`, `PlacePhotoOut`, `PlaceReviewOut`, `PlaceOpeningHoursOut` | 1. Add Pydantic v2 schemas for `PlacePhotoOut`, `PlaceReviewOut`, and `PlaceOpeningHoursOut`.<br>2. Expand `PlaceOut` with all new Google Places fields while maintaining default values (`[]` or `None`) so existing tests and OSM records serialize without breaking. |
| **MODIFY** | `backend/app/schemas/itinerary.py` | `ItineraryItemBase`, `ItineraryItemCreate`, `ItineraryItemOut`, `ItineraryDayOut`, `SuggestedItineraryRequest`, `RouteComputeRequest`, `RouteLegOut` | 1. Add `google_place_id`, `travel_mode_from_prev`, `travel_distance_meters`, `travel_duration_seconds`, and `route_polyline_from_prev` to `ItineraryItemBase` / `ItineraryItemOut`.<br>2. Add `place_payload: dict | None = None` to `ItineraryItemCreate` so that if a frontend client saves an itinerary containing a newly discovered Google Place or offline place not yet in PostgreSQL, the backend can upsert the `Place` on the fly.<br>3. Update `ItineraryItemCreate.validate_place_or_custom` to accept `place_id`, `google_place_id`, or `custom_title`.<br>4. Add `origin_lat`, `origin_lng`, `travel_mode`, `min_rating`, and `include_live_places` to `SuggestedItineraryRequest`. |
| **CREATE** | `backend/app/services/google_maps_service.py` | `GoogleMapsService` | 1. Implement `search_places_text(query, location_bias, included_types, min_rating)` calling `POST https://places.googleapis.com/v1/places:searchText` via `httpx.Client` with Discovery FieldMask.<br>2. Implement `search_places_nearby(lat, lng, radius_m, included_types)` calling `POST https://places.googleapis.com/v1/places:searchNearby`.<br>3. Implement `fetch_place_details(google_place_id)` calling `GET https://places.googleapis.com/v1/places/{google_place_id}` with Rich Details FieldMask (`reviews`, `editorialSummary`, `regularOpeningHours`, `photos`).<br>4. Implement `upsert_google_places_to_db(db, google_places_list)` that maps Google Places JSON to `Place` ORM entities, matches nearest Nueva Ecija `Municipality` via `resolve_municipality_id()`, and upserts on `google_place_id` (or fuzzy name + `<75m` coordinate match against existing curated/OSM rows to prevent duplicates).<br>5. Implement `compute_route(waypoints, travel_mode)` calling `POST https://routes.googleapis.com/directions/v2:computeRoutes` with fallback to OSRM / Haversine encoder if API key is absent. |
| **MODIFY** | `backend/app/algorithms/itinerary_generator.py` | `resolve_geographic_anchor()`, `score_place()`, `is_open_during_slot()`, `generate_suggested_itinerary_data()`, `persist_generated_itinerary()` | 1. Update `resolve_geographic_anchor()` to query `GoogleMapsService.search_places_text()` when `destination` is a specific landmark or barangay not found in local SQL.<br>2. In `generate_suggested_itinerary_data()`, check if local DB candidates matching `preferred_categories` within `cluster_radius_km` are below threshold (`total_days * 5`) or stale; if so, call `GoogleMapsService.discover_places_for_itinerary()` and upsert into `places`.<br>3. Add `is_open_during_slot(place, travel_date, slot_time, duration_minutes)` checking `regular_opening_hours.periods`.<br>4. Upgrade `score_place()` to incorporate Bayesian rating score (`rating` + `user_rating_count`), `price_level` budget estimation, and operating-hours compatibility.<br>5. After selecting stops for each day, run 2-Opt ordering on non-fixed stops and call `GoogleMapsService.compute_route()` to populate `route_polyline_from_prev`, `travel_distance_meters`, `travel_duration_seconds`, `day_overview_polyline`, and dynamic arrival `planned_time`. |
| **MODIFY** | `backend/app/api/v1/places.py` | `list_places()`, `get_place_detail()`, `get_place_rich_details()` (new), `proxy_place_photo()` (new), `search_nearby_essentials()` (new) | 1. In `list_places()`, add `include_live_google: bool = Query(default=False)` and `min_rating: float | None = Query(default=None)`. When `include_live_google=True` and local DB results `< 10`, query `GoogleMapsService` and merge/upsert results.<br>2. Add `GET /api/v1/places/{place_id}/details` and `GET /api/v1/places/google/{google_place_id}/details`: checks `place.details_cached_at` against 24h TTL; if stale or missing `reviews`, fetches from `GoogleMapsService.fetch_place_details()`, updates the DB row, and returns `PlaceOut`.<br>3. Add `GET /api/v1/places/photo-proxy` accepting `photo_name: str` and `max_width: int = 800` to securely resolve or redirect Google Places Photo URLs without exposing `GOOGLE_MAPS_API_KEY`.<br>4. Add `GET /api/v1/places/nearby-essentials` accepting `lat`, `lng`, `municipality`, and `category` (`restaurant`, `hospital`, `store`) to replace hardcoded Bongabon essentials with live Google Nearby Search results. |
| **MODIFY** | `backend/app/api/v1/itineraries.py` | `create_itinerary()`, `update_itinerary()`, `compute_itinerary_routes()` (new) | 1. In `create_itinerary()` and `update_itinerary()`, replace the strict `404` rejection on missing `place_id` with an upsert resolver: if an item provides `google_place_id` or `place_payload` whose UUID is not yet in `places`, upsert the `Place` record first and link its `id`.<br>2. Add `POST /api/v1/itineraries/{itinerary_id}/routes` and stateless `POST /api/v1/itineraries/compute-day-route` (for unsaved wizard previews and guest users) to compute/recompute multi-stop polylines and travel durations whenever stops are added, removed, or reordered. |

---

### 6.2 Frontend (Ionic Angular & Capacitor)

| Action | File Path | Affected Components / Services | Step-by-Step Logic Changes Required |
| :--- | :--- | :--- | :--- |
| **MODIFY** | `Project/package.json` | `dependencies` | 1. Add `"@capacitor/geolocation": "^8.0.0"` to `dependencies` so native Android/iOS GPS tracking and web fallback work seamlessly with Capacitor v8.6. |
| **MODIFY** | `Project/src/app/core/models/place.models.ts` | `Place`, `PlacePhoto`, `PlaceReview`, `PlaceRegularOpeningHours`, `PlaceSearchParams` | 1. Add TypeScript interfaces for `PlacePhoto`, `PlaceReview`, `PlaceRegularOpeningHours`, and expand `Place` and `PlaceSearchParams` as specified in Section 3.1.A. |
| **MODIFY** | `Project/src/app/core/models/itinerary.models.ts` | `ItineraryItem`, `ItineraryDay`, `RouteLegMetadata`, `RouteStepInstruction`, `SuggestedItineraryRequest` | 1. Add routing and Google Place ID properties to `ItineraryItem`, `ItineraryDay`, and `SuggestedItineraryRequest` as specified in Section 3.1.B. |
| **CREATE** | `Project/src/app/core/utils/polyline.util.ts` | `decodePolyline()`, `encodePolyline()`, `projectPointOnPolyline()`, `splitPolylineAtPoint()`, `computeBearingDegrees()` | 1. Implement Google Encoded Polyline Algorithm decoder (`decodePolyline(encoded: string): [number, number][]`) and encoder.<br>2. Implement `projectPointOnPolyline(userLatLng, polylineLatLngs)` returning `{ snappedLatLng, segmentIndex, distanceFromRouteMeters, traveledLatLngs, remainingLatLngs, remainingDistanceMeters }` for live route progress tracking. |
| **CREATE** | `Project/src/app/core/services/route-tracking.service.ts` | `RouteTrackingService` | 1. Manage active itinerary route state (`activeItinerary$`, `activeDayIndex$`, `activeRouteLegs$`, `userLocation$`, `routeProgress$`, `isTracking$`).<br>2. Implement `computeDayRoute(day: ItineraryDay, travelMode: TravelMode, userOrigin?: [number, number]): Observable<ItineraryDay>` calling `POST ${apiBaseUrl}/itineraries/compute-day-route` with client-side straight-line/cached fallback when offline.<br>3. Implement `startLiveTracking()` and `stopLiveTracking()` using `Geolocation.watchPosition()` from `@capacitor/geolocation`, updating `routeProgress$` (snapped position, remaining leg distance/ETA, next stop banner, and arrival detection within 80m). |
| **MODIFY** | `Project/src/app/core/services/place.service.ts` | `PlaceService` | 1. Add two-tier client cache (`private detailsCache = new Map<string, { place: Place; expiresAt: number }>()` backed by `@ionic/storage-angular`).<br>2. Add `getRichPlaceDetails(placeId?: string | null, googlePlaceId?: string | null, fallbackPlace?: Place): Observable<Place>` which checks cache first, then calls `/api/v1/places/{placeId}/details` or `/api/v1/places/google/{googlePlaceId}/details`, falling back gracefully to `fallbackPlace` if offline.<br>3. Upgrade `getNearbyPlaces(municipality: string, lat?: number, lng?: number): Observable<NearbyPlaceItem[]>` (or keep synchronous getter with reactive refresh) to query `GET /api/v1/places/nearby-essentials` with real coordinates and `google_place_id` before falling back to `getOfflineNearbyPlaces()`.<br>4. Update `getPlaceImage(placeName, remoteUrl, photos)` to prioritize `photos[0].url` (or `/api/v1/places/photo-proxy?photo_name=...`), then `remoteUrl`, then `localImageMap`. |
| **MODIFY** | `Project/src/app/core/services/itinerary.service.ts` | `ItineraryService` | 1. Increase `suggestItinerary()` HTTP timeout from `4000ms` to `10000ms` to accommodate first-time live Google Places + Routes API discovery on cold cache.<br>2. Fix the bug in `generateOfflineSuggestedItinerary()` (`lines 773–796`) where non-Bongabon destinations (`isProvincialOrBongabon === false`) ignored `matchedPool` and defaulted to `[curatedPool[0], curatedPool[1], curatedPool[2]]`. Instead, slice `matchedPool` across days and generate Haversine fallback `route_polyline_from_prev` and `travel_duration_seconds` so offline itineraries also render route lines on the map. |
| **CREATE** | `Project/src/app/core/components/place-detail-sheet/place-detail-sheet.component.{ts,html,scss}` | `PlaceDetailSheetComponent` | 1. Build a standalone, reusable Ionic bottom-sheet modal (`ion-modal` with `[breakpoints]="[0, 0.55, 0.92, 1.0]"`) accepting `@Input() isOpen`, `@Input() place`, `@Input() itineraryStop`, `@Input() mode ('map' | 'wizard' | 'detail')`.<br>2. Automatically fetch rich details via `PlaceService.getRichPlaceDetails()` when opened, showing skeleton loaders for `editorial_summary`, `regular_opening_hours.weekdayDescriptions`, `photos[]` carousel, and `reviews[]` cards.<br>3. Render star ratings, review count, live Open/Closed status badge, Google photo attributions, user review cards, commute guide, and action buttons (`Start Trip Here`, `Add to Trip`, `Route Here in App`, `Open in Google Maps`). |
| **MODIFY** | `Project/src/app/tabs/map/map.page.ts`, `.html`, `.scss` | `MapPage` | 1. Inject `RouteTrackingService` and `ItineraryService`.<br>2. Subscribe to `route.queryParams` for `itineraryId`, `day`, and `track`. When an itinerary is active on the map, display a top/bottom **Active Itinerary Route Bar** with a Day selector pill (`Day 1`, `Day 2`...), travel mode selector (`Drive`, `Two-Wheeler`, `Walk`), total distance/duration summary, and a `"Start Live GPS Tracking"` toggle button.<br>3. In `initMap()`, initialize `this.routePolylineLayer`, `this.itineraryStopsLayer`, and `this.userLocationLayer`.<br>4. Add `renderActiveItineraryRoute(day: ItineraryDay)` which decodes `route_polyline_from_prev` (or `day_overview_polyline`), draws cased polylines + directional arrows + leg duration badges on `this.routePolylineLayer`, and plots numbered stop pins (`1..N`) on `this.itineraryStopsLayer`, fitting map bounds (`this.map.fitBounds(routeBounds, { padding: [60, 60] })`).<br>5. Add `toggleLiveTracking()` wired to `RouteTrackingService`, rendering the user's live GPS puck, accuracy circle, and split traveled/remaining route polylines.<br>6. Replace the custom inline `<div class="poi-bottom-sheet">` in `map.page.html` (`lines 324–433`) with `<app-place-detail-sheet>` so clicking any map marker or numbered stop marker opens the rich Place Details modal with Google reviews, photos, and descriptions. |
| **MODIFY** | `Project/src/app/features/itinerary/itinerary-detail/itinerary-detail.page.ts`, `.html`, `.scss` | `ItineraryDetailPage` | 1. Add an interactive embedded Leaflet route preview map (`#detailMapElement`) inside `itinerary-detail.page.html` above the active day's stop list, rendering the day's numbered stop markers and road route polylines.<br>2. Display leg-by-leg travel connectors between stop cards in the timeline (e.g., `"🚗 12.4 km • 18 mins drive via Bongabon–Rizal Rd"` derived from `stop.travel_distance_meters` and `stop.travel_duration_seconds`).<br>3. Add a **"Track Route on Live Map"** CTA button that navigates to `/tabs/map` with `{ queryParams: { itineraryId: this.itinerary.id, day: this.activeDayIndex + 1, track: 'true' } }`.<br>4. Replace the basic `ion-modal` (`lines 474–528` in `itinerary-detail.page.html`) with `<app-place-detail-sheet>` so clicking any stop card displays full Google reviews, photos, opening hours, and commute info.<br>5. Fix `addNearbyPlaceToActiveDay()` (`lines 807–849`) so it uses the actual coordinates (`place.latitude`, `place.longitude`) and `google_place_id` of the selected nearby place instead of hardcoding `15.63, 121.14`, and triggers `routeTrackingService.computeDayRoute()` to update the day's polyline. |
| **MODIFY** | `Project/src/app/features/itinerary/suggested-wizard/suggested-wizard.page.ts`, `.html`, `.scss` | `SuggestedWizardPage` | 1. Add optional wizard controls for **Minimum Rating** (`All`, `4.0+ ★`, `4.5+ ★`) and **Travel Mode** (`Drive / Car`, `Motorcycle / Tricycle`, `Public Transit`).<br>2. On View 2 (`viewMode === 'itinerary'`), display each stop's Google star rating (`stop.place?.rating`), review count, and inter-stop road travel leg Connector (`travel_distance_meters`, `travel_duration_seconds`).<br>3. Replace the basic stop modal (`suggested-wizard.page.html`, lines 528–632) with `<app-place-detail-sheet>` so users can read Google reviews and inspect photos before saving their suggested itinerary.<br>4. Fix `addNearbyPlaceToActiveDay()` (`suggested-wizard.page.ts`, lines 422–464) to pass real `place.latitude`, `place.longitude`, and `google_place_id` instead of hardcoded `15.63, 121.14`. |
| **MODIFY** | `cloudflare-worker/worker.js` | `fetch()` | 1. Preserve existing tunnel proxy behavior while adding optional edge caching for `GET /api/v1/places/*/details` and `POST /api/v1/itineraries/compute-day-route` in Cloudflare KV (`env.TUNNEL_KV`) so static GitHub Pages users still benefit from cached Google Place Details and routes even if the developer laptop tunnel is temporarily restarted. |

---

## 7. Verification & Acceptance Plan (Post-Implementation)

When the engineering team executes this implementation plan, the following verification checks must be run to validate functional and non-functional requirements:

1. **Backend Automated Tests & Type Checking (`backend/`):**
   ```bash
   cd backend
   alembic upgrade head
   ruff check . && mypy .
   pytest -q
   ```
   - Add unit/integration tests in `backend/tests/test_itineraries.py` mocking `GoogleMapsService` HTTP responses to verify:
     - Hybrid discovery upserts Google Places into `places` with `google_place_id` deduplication.
     - Closed venues (`regular_opening_hours`) are not scheduled during closed time slots.
     - Saving an itinerary with newly discovered `google_place_id` items succeeds (`201 Created`) without foreign-key `404`/`500` errors.
     - `POST /api/v1/itineraries/compute-day-route` returns valid encoded polylines and leg durations.

2. **Frontend Lint, Type-Check & Unit Tests (`Project/`):**
   ```bash
   cd Project
   npm run lint
   npm run test:unit
   ```
   - Add unit specs in `route-tracking.service.spec.ts`, `polyline.util.spec.ts`, and `place-detail-sheet.component.spec.ts` verifying polyline decoding, GPS point-to-segment projection, 24-hour Place Details caching, and modal rendering of `reviews[]` and `editorial_summary`.
