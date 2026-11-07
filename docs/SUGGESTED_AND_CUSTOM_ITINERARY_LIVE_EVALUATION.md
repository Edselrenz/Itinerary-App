# Suggested & Custom Itinerary Live Evaluation, Preference Audit & Autofill Proposal

**Evaluation Version**: v4.0  
**Target System**: Nueva Ecija Travel Itinerary App ("Trip mo, trip ko")  
**Live Deployment**: [https://edselrenz.github.io/Itinerary-App/tabs/home](https://edselrenz.github.io/Itinerary-App/tabs/home)  
**Gateway API**: `https://ne-itinerary-api.edselrenz0.workers.dev/api/v1`  
**Repository Baseline**: `edselrenz/itinerary-app` (`81fcc8d7`)  
**Evaluation Date**: November 7, 2026  
**Document Source**: `suggested_and_custom_itinerary_live_evaluation.pdf`  
**Status**: Documented & Staged for Phased Implementation (Phase 31)

---

## 1. Executive Summary: Live Server Audit & Evaluation Scorecard

An end-to-end evaluation of the live production build at [edselrenz.github.io/Itinerary-App/tabs/home](https://edselrenz.github.io/Itinerary-App/tabs/home) was conducted with the backend server actively running, examining the **Suggested Itinerary Wizard** and **Custom Itinerary Builder** across Nueva Ecija's **2,673 POI database**.

While prior phases successfully resolved map marker clustering, offline state latching, and isolated route focus mode (Phase 30, GAP-01..05), this evaluation audited whether user inputs and preferences are genuinely respected by the itinerary generation engines:

```
+----------------------------------------------------------------------------------------------------+
|                                    LIVE EVALUATION SCORECARD                                       |
+------------------------------+---------------------------+-----------------------------------------+
| Metric                       | Measured Live Value       | Target Proposed State (Phase 31)        |
+------------------------------+---------------------------+-----------------------------------------+
| Destination Autofill         | 0 Autofill / 6 Chips      | Instant 32-LGU & Landmark Combobox      |
| Quick-Select Chip Overflow   | 4th chip cut off ("G...") | 2-Row Wrapped Grid + "Browse 32 Towns"  |
| Preference Category Match    | 67% (fails food & church) | 96% (Canonical category mapping)        |
| Non-Overlapping Time Slots   | 11% (Collisions at 10 AM) | 100% (Sequential rolling time windows)  |
| Cross-Day Venue Deduplication| 78% (Duplicate entities)  | 100% (Fuzzy name & <200m coordinate dedup)|
| Realistic Day Pacing         | 33% (3 hikes, 0 meals)    | 95% (Max 1 hike/day + midday lunch stop)|
| Custom Builder Default POIs  | 17 of 2,673 Places        | 100% Catalog (dest query + 2,673 pool)  |
+------------------------------+---------------------------+-----------------------------------------+
```

---

## 2. Live Audit of the Wizard Form & Destination Input

Inspecting the live Suggested Itinerary questionnaire screen ([`Project/src/app/features/itinerary/suggested-wizard/suggested-wizard.page.html:29–56`](file:///c:/Users/Edward/Desktop/CaseStudy/Project/src/app/features/itinerary/suggested-wizard/suggested-wizard.page.html#L29-L56)) alongside the Custom Builder form ([`custom-builder.page.html:80–106`](file:///c:/Users/Edward/Desktop/CaseStudy/Project/src/app/features/itinerary/custom-builder/custom-builder.page.html#L80-L106)) reveals four concrete input flaws:

1. **Zero Autofill / Autocomplete Dropdown**:
   Both wizards render a plain `<input type="text" formControlName="destination">`. Typing `"panta"`, `"gabal"`, or `"minal"` provides no suggestions, forcing travelers to know and spell Nueva Ecija's 32 municipalities, cities, and landmarks from memory.
2. **Clipped Horizontal Chip Row with Hidden Overflow**:
   `.quick-dest-row` ([`suggested-wizard.page.scss:58–69`](file:///c:/Users/Edward/Desktop/CaseStudy/Project/src/app/features/itinerary/suggested-wizard/suggested-wizard.page.scss#L58-L69)) defines `overflow-x: auto; scrollbar-width: none;` without fade gradients or scroll indicators. On mobile widths ($\le 480$px), *Gapan City* is sliced off as `"G..."`, and *General Tinio* and *Nueva Ecija* are hidden offscreen unless users guess they can swipe horizontally.
3. **Only 6 of Nueva Ecija's 32 Municipalities/Cities Are Represented**:
   Prominent travel hubs—including San Jose City, Science City of Muñoz, Palayan City, Gabaldon (Dupinga River / eco-resorts), Carranglan, Talavera, Laur, Santa Rosa, Cabiao, Peñaranda, and Cuyapo—have zero quick-select representation.
4. **Diacritic & Landmark Resolution Failures**:
   - In [`itinerary.service.ts:915`](file:///c:/Users/Edward/Desktop/CaseStudy/Project/src/app/core/services/itinerary.service.ts#L915), client-side destination matching only checks `p.municipality.toLowerCase().includes(targetDest)`. Typing a famous attraction name into Destination (e.g. `"Minalungao National Park"` or `"Highland Bali"`) yields 0 results because it never evaluates `p.name`.
   - Without Unicode NFD diacritic stripping, typing `"Munoz"` or `"Penaranda"` fails to match `"Science City of Muñoz"` or `"Peñaranda"` because `'science city of muñoz'.includes('munoz')` evaluates to `false`.

---

## 3. Controlled Live Experiment: Does the Suggested Wizard Respect Preferences?

To determine whether the Suggested Itinerary Wizard genuinely tailors stops to selected user preferences, two controlled runs were executed on the live deployment, holding Destination (*Pantabangan*), Travel Dates (*Nov 7–9, 2026*, 3 days / 2 nights), and Daily Budget (*₱3,000*) constant while changing only the Preferences pills:

- **Live Test A**: *Food Trip + Culture & History + Resort*
- **Live Test B**: *Nature & Parks ONLY*

### Empirical Results Table

| Day & Stop | Live Test A: Multi-Preference<br>*(Food Trip + Culture + Resort)* | Live Test B: Single Preference<br>*(Nature & Parks ONLY)* | Match Analysis |
| :--- | :--- | :--- | :---: |
| **Day 1 • Stop 1**<br>(Pantabangan) | **George Point Viewdeck & Resto**<br>`10:00 AM – 12:00 PM` • Dining / Viewpoint | **George Point Viewdeck & Resto**<br>`10:00 AM – 12:00 PM` • Dining / Viewpoint | **IDENTICAL (0% Turn)** |
| **Day 1 • Stop 2**<br>(Pantabangan) | **Lake Farm De La Marre**<br>`10:00 AM – 12:00 PM` • Farm Resort | **Lake Farm De La Marre**<br>`10:00 AM – 12:00 PM` • Farm Resort | **IDENTICAL (0% Turn)** |
| **Day 1 • Stop 3**<br>(Pantabangan) | **Double R Resort**<br>`10:00 AM – 12:00 PM` • Resort | **Pantabangan Dam and Lake Viewpoint**<br>`10:00 AM – 12:00 PM` • Nature / Viewpoint | Changed |
| **Day 2 • Stop 1**<br>(Bongabon) | **Rohi Paperflower Cafe**<br>`12:00 PM – 2:00 PM` • Cafe & Dining | **Mount Agsil**<br>`10:00 AM – 12:00 PM` • Mountain Peak | Changed |
| **Day 2 • Stop 2**<br>(Bongabon) | **Pantabangan Dam and Lake Viewpoint**<br>`1:00 PM – 3:00 PM` • Nature / Viewpoint | **Mount Aja**<br>`10:00 AM – 12:00 PM` • Mountain Peak | Changed |
| **Day 2 • Stop 3**<br>(Bongabon) | **Highland Bali Villas Resort and Spa**<br>`10:00 AM – 12:00 PM` • **Backwards Time!** | **Mount Anao**<br>`10:00 AM – 12:00 PM` • Mountain Peak | Changed |
| **Day 3 • Stop 1**<br>(Pantabangan) | **Pantabangan Dam and Lake Viewpoint**<br>`10:00 AM – 12:00 PM` • **Duplicate of Day 2!** | **Mount Anunas**<br>`10:00 AM – 12:00 PM` • Mountain Peak | Changed |
| **Day 3 • Stop 2**<br>(Pantabangan) | **George Point**<br>`12:00 PM – 1:30 PM` • **Duplicate entity of D1S1!** | **Mount Balukbok**<br>`10:00 AM – 12:00 PM` • Mountain Peak | Changed |
| **Day 3 • Stop 3**<br>(Pantabangan) | **Museo de Bongabon**<br>`2:00 PM – 5:00 PM` • Culture & Museum | **Mount Bonaba**<br>`10:00 AM – 12:00 PM` • Mountain Peak | Changed |

### Observations from the Experiment
1. **Day 1 Immobility**: In both Test A and Test B, Day 1 Stops 1 and 2 are 100% identical. Even when the user selected *Nature & Parks ONLY*, the generator still forced a dining spot and a farm resort into Stops 1 & 2.
2. **Universal 10:00 AM Collisions**: All 3 stops on Day 1 in Test A and all 9 stops in Test B share the exact same timestamp: `10:00 AM – 12:00 PM`.
3. **Backwards Chronology**: On Day 2 in Test A, Stop 3 (*Highland Bali Villas*) is scheduled at `10:00 AM – 12:00 PM`, directly following a `1:00 PM – 3:00 PM` stop.
4. **Duplicate Venues Across Days**: *Pantabangan Dam and Lake Viewpoint* is scheduled on Day 2 Stop 2 and repeated on Day 3 Stop 1. *George Point Viewdeck & Resto* (Day 1) and *George Point* (Day 3) represent the exact same physical venue.
5. **Extreme Pacing in Test B**: In Test B (*Nature & Parks*), the user is scheduled to hike 3 separate mountains on Day 2 (Mount Agsil, Mount Aja, Mount Anao) and 3 more mountains on Day 3 (Mount Anunas, Mount Balukbok, Mount Bonaba) with zero dining stops, water breaks, or rest periods.

---

## 4. Root-Cause Diagnosis: 6 Preference & Scheduling Bugs + 3 Custom Builder Bugs

```
+------------------------------------------------------------------------------------------------------------------------------------------+
|                                                  CODE FORENSICS MATRIX (COMMIT 81fcc8d7)                                                 |
+---------+----------+-------------------------------------------------+-------------------------------------------------------------------+
| Bug ID  | Severity | Code Location                                   | Root Cause & Impact on Traveler                                   |
+---------+----------+-------------------------------------------------+-------------------------------------------------------------------+
| PREF-01 | CRITICAL | itinerary.service.ts:346, 360                   | suggestItinerary() sets timeout(4000) while sending               |
|         |          | itinerary_generator.py:321, 507                 | include_live_places: true. 3-day requests exceed 4s and silently  |
|         |          |                                                 | fall back to client-side generateOfflineSuggestedItinerary().      |
| PREF-02 | CRITICAL | itinerary.service.ts:933–942                    | Substring check a.categoryKey.toLowerCase().includes(pr) fails:  |
|         |          |                                                 | restaurant/cafe has key 'restaurant'|'cafe' (never contains       |
|         |          |                                                 | 'food'!), and churches have 'church_religious' (no 'culture'!).   |
| PREF-03 | CRITICAL | itinerary.service.ts:914–950                    | Soft additive scoring without hard Day 1 category gate: in        |
|         |          | itinerary_generator.py:215–236                  | Pantabangan, only 6 curated places exist, so George Point Resto   |
|         |          |                                                 | and Lake Farm remain in top 3 even for Nature-only selections.    |
| PREF-04 | CRITICAL | itinerary.service.ts:865, 1038–1043, 1086       | Every OSM place loaded at line 865 is assigned static 10:00 AM.   |
|         |          |                                                 | Thus if (!plannedTime) at 1039 is unreachable dead code! At 1086,  |
|         |          |                                                 | isOvernightItem() pushes Highland Bali to Stop 3 with 10:00 AM.   |
| PREF-05 | HIGH     | itinerary.service.ts:987–993                    | When matchedPool < 9, raw mountain peaks are loaded               |
|         |          | osm_places.json                                 | alphabetically (Mount Agsil, Aja, Anao...) with no meal slot or   |
|         |          |                                                 | max-1-hike-per-day pacing rule.                                   |
| PREF-06 | HIGH     | itinerary.service.ts:996–998                    | When candidates < 3, line 997 recycles already-used places.       |
|         |          | itinerary_generator.py:376–382                  | Dedup only checks place.id rather than normalized name or coord   |
|         |          |                                                 | distance (< 200m), producing duplicate venue stops across days.   |
| CUST-01 | HIGH     | custom-builder.page.ts:551–564, 928–960         | Selecting culture or resort in Step 1 sets selectedCategory =     |
|         |          |                                                 | 'Tourist Spots', which strictly filters out museum_cultural,      |
|         |          |                                                 | church_religious, and resort_swimming in Step 2!                 |
| CUST-02 | HIGH     | custom-builder.page.ts:865–879                  | loadBrowsePlaces() calls placeService.getFeaturedPlaces(50),      |
|         |          |                                                 | showing only 17 places (0 in Gabaldon/Muñoz/Talavera) instead of  |
|         |          |                                                 | querying user's chosen destination across the 2,673 POI catalog.  |
| CUST-03 | MEDIUM   | custom-builder.page.ts:1165–1195                | Auto-Schedule in Step 3 sets end_time_1 == start_time_2 with zero |
|         |          |                                                 | transit buffer between destinations that are 10–25 km apart.      |
+---------+----------+-------------------------------------------------+-------------------------------------------------------------------+
```

---

## 5. User POV Improvement Proposal: UI & UX Redesign

### 5.1 Categorized Destination Autofill Combobox & Regional Explorer Sheet
1. **Instant Grouped Dropdown on Focus & Typing**:
   As soon as the traveler focuses or types into the Destination input in either wizard, open a scannable floating combobox dropdown categorized into three sections:
   - **Province-Wide Option**: `🌏 All of Nueva Ecija (Best Multi-Town Corridor) — 2,673 places`
   - **Municipalities & Cities (All 32 LGUs with POI Counts & Highlights)**:
     - `📍 Pantabangan (Lake, Dam Viewpoints & Highland Resorts • 48 places)`
     - `📍 Cabanatuan City (Food Trip, Heritage & Cafes • 612 places)`
     - `📍 Gabaldon (Eco-Parks, Falls & River Resorts • 64 places)`
     - `📍 Science City of Muñoz (Agri-Tourism & Science Museums • 185 places)`
     - `📍 Gapan City (Lumang Gapan Heritage & Dining • 210 places)`
     - `📍 Bongabon (Farms, Cafes & Museums • 95 places)`
   - **Specific Landmarks & Direct Anchors**:
     - `⭐ Minalungao National Park (General Tinio)`
     - `⭐ Highland Bali Villas Resort and Spa (Pantabangan)`
     - Selecting a landmark automatically sets its municipality as the geographic corridor and locks the landmark as Day 1 Stop 1 (`anchor_place_id`).
2. **Replace Clipped Chip Row with Wrapped 2-Row Grid + All 32 Towns Modal**:
   Replace the clipped single row (`overflow-x: auto`) with a wrapped pill layout (`flex-wrap: wrap`) displaying the top 6 travel hubs in full text, accompanied by a `🗺️ Browse All 32 Towns` chip that opens a categorized North / Central / South / East Nueva Ecija regional picker modal.

### 5.2 Preference-Driven Pacing & Transparent Match Feedback
1. **Strict Preference Priority with Expanding Radius**:
   When preferences are chosen (e.g., *Nature & Parks ONLY*), activity slots (09:30 AM and 03:00 PM) must strictly pull from matching categories within an expanding geographic radius ($15\text{ km} \to 30\text{ km} \to 45\text{ km}$) before falling back to non-matching venues.
2. **Smart Dining Anchor ("Include Daily Lunch Spot")**:
   Add a lightweight toggle pill under Preferences (default: **ON**) so even when a traveler selects only *Nature & Parks*, each day still schedules 1 realistic midday dining stop (`12:00 PM – 01:30 PM`) near the morning attraction instead of scheduling 3 consecutive mountain hikes.
3. **Activity Intensity Guard (Max 1 Mountain Hike Per Day)**:
   Tag mountain peaks (`isMountainPeak`) as high-exertion, ensuring at most 1 strenuous mountain trail is scheduled per day alongside scenic parks, viewpoints, or eco-farms.
4. **Per-Stop "Why This Was Chosen" Match Pills**:
   Render subtle contextual match pills on generated cards (e.g. `✓ Matches: Nature & Parks • 3.2 km from previous stop` or `🍽️ Midday Lunch Anchor`).

### 5.3 Custom Itinerary Builder Step 1 $\rightarrow$ Step 2 Continuity
1. **Pre-Load Destination POIs on "Start Building"**:
   When the user proceeds to Step 2, query `GET /api/v1/places?municipality_name=<dest>&limit=100` (with 2,673 POI local OSM fallback) so the user sees all available places in their chosen town rather than only 17 featured POIs.
2. **Multi-Preference Filter Sync**:
   Add a `✨ Recommended for You` tab combining all preferences selected in Step 1 (e.g. food + culture + resort) instead of locking to a `'Tourist Spots'` tab that hides resorts and museums.

---

## 6. Developer POV Improvement Proposal: Code & Algorithmic Blueprints

### 6.1 Reusable `<app-destination-autocomplete>` Component
Create a standalone combobox component in `Project/src/app/shared/components/destination-autocomplete/destination-autocomplete.component.ts` indexing all 32 LGUs plus top landmarks, using Unicode NFD diacritic stripping:

```typescript
export interface DestinationSuggestion {
  label: string;
  municipality: string;
  type: 'province' | 'municipality' | 'landmark';
  placeId?: string;
  subtitle: string;
  poiCount?: number;
}

export const NUEVA_ECIJA_32_LGUS = [
  { name: 'Cabanatuan City', district: 'Central', highlights: 'Food Trip, Cafes & WWII Heritage' },
  { name: 'Pantabangan', district: 'North-East', highlights: 'Pantabangan Lake, Dam Viewpoints & Highland Resorts' },
  { name: 'Gabaldon', district: 'East', highlights: 'Dupinga River, Eco-Parks & Mountain Resorts' },
  { name: 'Bongabon', district: 'East', highlights: 'Farm Resorts, Rohi Cafe & Museo de Bongabon' },
  { name: 'Gapan City', district: 'South', highlights: 'Lumang Gapan Heritage Street & Local Dining' },
  { name: 'General Tinio', district: 'South-East', highlights: 'Minalungao National Park & Limestone River' },
  { name: 'San Jose City', district: 'North', highlights: 'Northern Gateway, Parks & Culinary Stops' },
  { name: 'Science City of Muñoz', district: 'North-West', highlights: 'PhilRice, CLSU Agri-Tourism & Museums' },
  { name: 'Palayan City', district: 'Central', highlights: 'Provincial Capitol Hub, Nature & Resorts' },
  { name: 'Talavera', district: 'Central', highlights: 'Highway Dining, Farm Parks & Resorts' },
  { name: 'Laur', district: 'East', highlights: 'Scenic Mountain Views & Nature Trails' },
  { name: 'Santa Rosa', district: 'Central-South', highlights: 'Family Resorts, Dining & Heritage Churches' },
  // ... + remaining 20 municipalities
];

export function normalizeText(str: string): string {
  return (str || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim();
}
```

### 6.2 Canonical Preference Mapping, Sequential Slot Scheduling & Deduplication
In [`itinerary.service.ts`](file:///c:/Users/Edward/Desktop/CaseStudy/Project/src/app/core/services/itinerary.service.ts):

```typescript
private readonly PREFERENCE_CATEGORY_MAP: Record<string, string[]> = {
  nature: ['nature_park', 'tourist_attraction'],
  food: ['restaurant', 'cafe'],
  culture: ['museum_cultural', 'church_religious'],
  shopping: ['shopping_market', 'convenience_store'],
  resort: ['resort_swimming', 'hotel_accommodation'],
};

private normalizeVenueName(name: string): string {
  return (name || '')
    .toLowerCase()
    .replace(/\b(viewdeck|viewpoint|and|&|resto|restaurant|cafe|resort|spa|hotel|villas)\b/g, '')
    .replace(/[^a-z0-9]/g, '');
}

private isMountainPeak(name: string): boolean {
  return /^(\bmt\.?\b|\bmount\b)/i.test((name || '').trim());
}

// Sequential non-overlapping slot allocation with travel time
const SLOT_START_MINUTES = [9 * 60 + 30, 12 * 60 + 0, 15 * 60 + 0]; // 09:30 AM, 12:00 PM, 03:00 PM
let rollingMinutes = 9 * 60 + 30;

items.forEach((item, idx) => {
  item.sort_order = idx + 1;
  const dur = item.duration_minutes || 120;
  const travelMins = idx > 0 && item.travel_duration_seconds
    ? Math.max(15, Math.round(item.travel_duration_seconds / 60))
    : 0;
  const startMins = Math.max(SLOT_START_MINUTES[idx] ?? rollingMinutes, rollingMinutes + travelMins);
  const endMins = startMins + dur;
  item.planned_time = `${this.formatMinutesTo12Hr(startMins)} - ${this.formatMinutesTo12Hr(endMins)}`;
  rollingMinutes = endMins;
});
```

### 6.3 Decouple Synchronous Google API Calls & Fast-Path Generation
- In [`backend/app/algorithms/itinerary_generator.py`](file:///c:/Users/Edward/Desktop/CaseStudy/backend/app/algorithms/itinerary_generator.py), default `include_live_places = False` when the local database already contains $\ge 15$ candidates within the bounding box.
- Increase [`itinerary.service.ts:360`](file:///c:/Users/Edward/Desktop/CaseStudy/Project/src/app/core/services/itinerary.service.ts#L360) HTTP timeout from 4,000 ms to 10,000 ms (`timeout(10000)`).

---

## 7. Phased Implementation Roadmap & Verification Matrix (Phase 31)

```
+-----------------------------------------------------------------------------------------------------------------------------------------------------+
|                                                          PHASE 31 IMPLEMENTATION ROADMAP                                                            |
+-----------+-----------------------------------+-------------------------------------------------------------+---------------------------------------+
| Phase     | Scope & Key Deliverables          | Target Files                                                | Verification Gate                     |
+-----------+-----------------------------------+-------------------------------------------------------------+---------------------------------------+
| 31.1      | Destination Autofill Combobox,    | destination-autocomplete.component.ts (NEW)                | Typing "panta", "munoz", or           |
| (P0)      | 32 LGUs & Wrapped Quick Pills     | destination-autocomplete.component.html / scss (NEW)        | "minalungao" opens grouped suggestions|
|           |                                   | suggested-wizard.page.html, custom-builder.page.html        | with diacritic stripping; 0 clipped   |
|           |                                   | suggested-wizard.page.scss                                  | chips on mobile/desktop.              |
+-----------+-----------------------------------+-------------------------------------------------------------+---------------------------------------+
| 31.2      | Preference Category Mapping,      | itinerary.service.ts                                        | Selecting Nature & Parks immediately  |
| (P0)      | Sequential Time Windows,          | itinerary_generator.py                                      | changes Day 1 Stop 1; schedules max 1 |
|           | Smart Midday Lunch & Dedup        | osm_places.json                                             | mountain hike/day + 1 lunch stop;     |
|           |                                   |                                                             | produces 0 duplicate venues; assigns  |
|           |                                   |                                                             | non-overlapping times (9:30, 12, 3).  |
+-----------+-----------------------------------+-------------------------------------------------------------+---------------------------------------+
| 31.3      | Custom Builder Full-Catalog       | custom-builder.page.ts                                      | Selecting Culture or Resort in Step 1 |
| (P1)      | Browse, Preference Tab Sync &     | custom-builder.page.html                                    | surfaces matching places in Step 2    |
|           | Auto-Schedule Transit Buffer      |                                                             | across all 2,673 POIs; Auto-Schedule  |
|           |                                   |                                                             | adds realistic transit buffer.        |
+-----------+-----------------------------------+-------------------------------------------------------------+---------------------------------------+
```
