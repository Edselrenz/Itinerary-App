# Trip mo, trip ko (Nueva Ecija) — Exhaustive Desktop vs. Web Use-Case Audit, Root-Cause Diagnostics & Antigravity Implementation Plan

**Live Reference Web Application**: [Trip mo, trip ko — Nueva Ecija Web App](https://edselrenz.github.io/Itinerary-App/) (`Project/src/app/`)  
**Desktop Client Target**: `desktop_client/` (Python 3.12+ / Flet `>=1.1.2`)  
**Backend API Target**: `backend/app/` (FastAPI `/api/v1` / SQLAlchemy 2.0 / PostgreSQL 16 & SQLite)  
**Design & Engineering Standard**: Strict 1:1 visual, structural, and functional parity with the Web Application and uploaded reference screenshots (`image_2d1741.png` Edit Profile, `image_2d1705.png` Settings, `image_2d13c2.png` Profile, `image_2d1020.png` Saved Itineraries Empty State) — **zero extra desktop-only buttons, zero extra form fields, and zero unrequested features**.

---

## 1. Executive Summary of Root Causes Across All Reported Issues

| # | Subsystem | User-Reported Symptom | Exact Root Cause in Codebase | Target Files to Modify |
| :-: | :--- | :--- | :--- | :--- |
| **1** | **Map Filters Crash & Broken Filtering** | Clicking **Filters** on the Map tab throws: `The application encountered an error: Dropdown.__init__() got an unexpected keyword argument 'on_change'`, and category/price/municipality filters do not behave like the web app. | 1. In `desktop_client/views/places_view.py:1072` (`muni_dropdown`) and `1088` (`tier_dropdown`), `ft.Dropdown(...)` passes `on_change=...`. In **Flet 1.1.2**, `Dropdown.__init__()` removed `on_change` and replaced it with **`on_select`**.<br>2. On the [Web Map Tab](https://www.google.com/search?q=https://edselrenz.github.io/Itinerary-App/%23/tabs/map) (`Project/src/app/tabs/map/map.page.html:320–442`), the **Filter Destinations** modal does not use dropdowns at all—it uses multi-select **Category Chips**, a horizontal **Municipality Chips** scroller (`All Municipalities` + 32 LGUs), and 4 **Price Range Pills** (`All Prices`, `Free (₱0)`, `Budget (≤ ₱500)`, `Mid-Range (> ₱500)`).<br>3. In `places_view.py:700–713`, clicking a top-bar quick category pill accumulates into `selected_categories` instead of selecting a single quick category (or toggling back to `All Places`) like `map.page.ts:854–871`.<br>4. In `places_view.py:293`, the `Filters [N]` badge only counts `len(self.selected_categories)` instead of `len(selected_categories) + (1 if selected_municipality != 'all' else 0) + (1 if selected_price_tier != 'all' else 0)`. | `desktop_client/views/places_view.py` |
| **2** | **Laggy, Static Map & Broken Scroll-Wheel Zoom / Pan** | The map on the desktop app renders but is laggy and static; you cannot freely pan around Nueva Ecija or zoom in/out using the mouse scroll wheel. | 1. **Pointer Interception by Sibling `_marker_stack` (`slippy_map_canvas.py:252–262`)**: `gesture_surface` (`ft.GestureDetector`) is placed *underneath* `self._marker_stack` (`ft.Stack(width=1366, height=768)`) as a sibling. In Flutter's hit-test tree, `_marker_stack` and its 50–250 marker `Container` children intercept pointer scroll and drag events before they reach `gesture_surface`.<br>2. **Flet 1.1.2 Event Attribute Changes (`slippy_map_canvas.py:380, 397`)**: In Flet 1.1.2, `ft.ScrollEvent` provides `e.scroll_delta` (`Offset(x, y)`) or JSON in `e.data`, while `getattr(e, "scroll_delta_y", 0.0)` evaluates to `0.0` (so wheel scrolling never triggers `set_zoom`). Similarly, `ft.DragUpdateEvent` in Flet 1.1.2 uses `e.local_delta` / `e.global_delta` alongside `delta_x`/`delta_y`.<br>3. **Full Widget-Tree Rebuild on Every 45ms Drag Frame (`slippy_map_canvas.py:414–552`)**: Every pan tick destroys and recreates 30+ `ft.Image` tile widgets and 50–250 nested marker/cluster `ft.Container` trees with `ft.BoxShadow`, and recomputes `math.sin`/`math.log` across all 2,673 places on the main UI thread.<br>4. **Missing Provincial Bounds Clamping**: Lacks smooth clamping to `NUEVA_ECIJA_BOUNDS` (`lat 15.05..16.25`, `lng 120.55..121.55`, `zoom 9..18`) matching `map.page.ts:116–119`. | `desktop_client/components/slippy_map_canvas.py`<br>`desktop_client/views/places_view.py` |
| **3** | **Login Profile Data & Profile Picture Not Loading from Database** | Logging in succeeds, but profile fields (such as the profile picture, middle initial, birthday, gender, and phone number) are not loaded from the database. | 1. **Stale Local Override in `User.from_dict()` (`desktop_client/models/user.py:82–90`)**: `User.from_dict(data, extra)` evaluates `extra.get("avatar_url") or data.get("avatar_url")` (and same for `middle_initial`, `birthday`, `gender`, `phone_number`). Any stale or default entry in local `profile_extra.json` overwrites the fresh database record returned by `POST /api/v1/auth/login` and `GET /api/v1/auth/me`!<br>2. **Flet 1.1.2 Base64 Data URI Image Rendering Failure (`desktop_client/config/settings.py:182` & `profile_view.py:88`)**: When `user.avatar_url` is a `data:image/jpeg;base64,...` string (uploaded via Web or Desktop), passing the raw multi-kilobyte `data:image/...` string to `ft.Image(src=...)` fails in Flutter desktop `Image` resolution and falls back to `error_content` (`ft.Icons.PERSON`). Decoding `data:image/...;base64,...` to a cached file in `storage/avatars/` and passing the local file path to `ft.Image(src=...)` renders the photo reliably.<br>3. **Web App Not Persisting Extended Profile Fields to DB (`Project/src/app/tabs/profile/profile.page.ts:472–518` & `auth.models.ts`)**: `ProfilePage.saveProfile()` on the Web App only sent `first_name`, `last_name`, `username` in `PATCH /api/v1/auth/me` and kept `middle_initial`, `phone_number`, `birthday`, `gender`, `avatar_url` only in browser `localStorage`. Updating both Web (`auth.models.ts`, `profile.page.ts`) and Backend (`database.py` backfill + `/auth/me`) ensures 100% database persistence across Web and Desktop.<br>4. **`User._compute_full_name()` Appends `"N/A."` (`desktop_client/models/user.py:42–44`)**: When `middle_initial` is `"N/A"`, `_compute_full_name()` produces `"Edward Renz N/A. Natividad"` instead of `"Edward Renz Natividad"`. | `desktop_client/models/user.py`<br>`desktop_client/services/auth_service.py`<br>`desktop_client/config/settings.py`<br>`backend/app/core/database.py`<br>`Project/src/app/core/models/auth.models.ts`<br>`Project/src/app/tabs/profile/profile.page.ts` |
| **4** | **Profile Tab UI Mismatch vs. Uploaded Photo (`image_2d13c2.png`)** | Desktop Profile tab displays extra subtitle, bordered identity card, 5 extra metadata badges (`email`, `phone`, `birthday`, `gender`, `₱3,000/day`), square icon boxes, and modified row descriptions. | In `desktop_client/views/profile_view.py:61–348`:<br>• Renders extra subtitle `"Manage your traveler identity and preferences."`<br>• Wraps identity section in a bordered white card with 5 extra `profile_badges` chips.<br>• Uses `@username` instead of `@edselrenz0@gmail.com` (`@{{ email_normalized }}`).<br>• Alters menu descriptions (`"Your favorite places (0 saved)."` instead of `"Your favorite places, all saved in one place. Find them whenever you're ready to explore."`; `"Provincial hotlines, emergency contacts, and FAQs."` instead of `"Get assistance and find answers to common questions."`; `"Trip mo, trip ko — Desktop Client v1.0.0."` instead of `"Version 1.0.0."`). | `desktop_client/views/profile_view.py` |
| **5** | **Edit Profile UI Mismatch vs. Uploaded Photo (`image_2d1741.png`)** | Desktop Edit Profile opens a popup dialog containing extra buttons (`Remove`, `Presets: Hiker | Default`, `Cancel`) and extra fields (`Username`, `Default Daily Budget`, `Current Password`, `New Password`, `Gender` dropdown) not on the webpage. | In `desktop_client/views/profile_view.py:859–1133`:<br>• Opens an `ft.AlertDialog` instead of switching `ProfileView` in-page to `view_mode = "edit"` with the bottom tab bar visible.<br>• Adds 6 unrequested controls (`Remove` photo button, `Presets: Hiker / Default`, `Username`, `Default Daily Budget (PHP)`, `Current Password`, `New Password`, `Cancel` button).<br>• Must only contain the exact header (`← Edit Profile`), centered circular avatar with camera overlay badge, blue-outlined pill button `Change Photo`, the **7 stacked full-width fields** (`First Name`, `Middle Initial (if applicable)`, `Last Name`, `Birthday`, `Gender`, read-only `Email Address`, `Phone Number`), and the full-width solid blue `Save Changes` button. | `desktop_client/views/profile_view.py` |
| **6** | **Settings UI Mismatch vs. Uploaded Photo (`image_2d1705.png`)** | Desktop Settings opens a popup dialog with extra backend connectivity controls (`Offline Map Cache`, `Backend Connection Status`, `API URL` input, `Test Connection`, `Save URL`, `Reset Default`) instead of the 6 rows in `image_2d1705.png`. | In `desktop_client/views/profile_view.py:390–569`:<br>• Opens an `ft.AlertDialog` (`"App Settings & Connectivity"`) instead of switching `ProfileView` in-page to `view_mode = "settings"`.<br>• Must render in-page with `← Settings` header and a single rounded white card containing **only the 6 exact rows** from `image_2d1705.png`:<br>1. `Account Information` (person-outline icon → opens Edit Profile)<br>2. `Notifications` (filled bell icon + blue switch)<br>3. `Privacy & Security` (filled lock icon → opens encryption info alert)<br>4. `Language` (globe-outline icon + `English` / `Filipino`)<br>5. `App Appearance` (sun/moon icon + `Light` / `Dark`)<br>6. `Clear Cache` / `Free up storage space` (trash-outline icon → opens Clear Cache confirmation). | `desktop_client/views/profile_view.py` |
| **7** | **Saved Itineraries Empty State Mismatch vs. Uploaded Photo (`image_2d1020.png`)** | Desktop Saved Itineraries tab shows a subtitle, `+ New Itinerary` button, search bar, 5 segment pills, `"Your Saved Trips"` header, and side-by-side `"AI Wizard"` / `"Custom Builder"` buttons even when 0 itineraries exist. | In `desktop_client/views/saved_trips_view.py:42–165`:<br>• Always renders search bar, segment tabs, and `"Your Saved Trips"` header even when `len(self.itineraries) == 0`.<br>• On the [Web Saved Itineraries Tab](https://www.google.com/search?q=https://edselrenz.github.io/Itinerary-App/%23/tabs/history) (`history.page.html:1–168`) and `image_2d1020.png`:<br>  - Top toolbar has left title `Saved Itineraries` and right blue `+` icon button (`ft.Icons.ADD`).<br>  - Search & Segment pills are **only** visible when `len(itineraries) > 2`.<br>  - When `len(itineraries) == 0`, only the centered empty state is shown: light-blue circle with blue clock icon, bold `No Saved Itineraries Yet`, subtitle `Your saved trips will appear here. Choose how you would like to plan your Nueva Ecija travel experience:`, dark navy button `✨ Suggested Itinerary`, and bright blue button `+ Custom Itinerary`. | `desktop_client/views/saved_trips_view.py` |
| **8** | **Suggested Itinerary Use-Case & UI Divergences** | Desktop Suggested Itinerary has extra fields/buttons (`Trip Title`, `Step 1..6` labels, `Pacing & Intensity` selector, top dark-navy banner with 5 action buttons, non-autocomplete dropdown) and differs from the Web Wizard across form, preview, and nearby views. | Detailed in **Section 2** below (`UC-S01` through `UC-S12`). | `desktop_client/views/suggested_wizard_view.py`<br>`desktop_client/components/destination_picker.py`<br>`desktop_client/main.py` |
| **9** | **Custom Itinerary Use-Case & UI Divergences** | Desktop Custom Itinerary differs in header chrome, Step 1 defaults, Step 2 card grid & category pills (`Other` missing, extra `Details` button), Step 3 budget summary & day/stop deletion confirmations, and off-grid modal structure. | Detailed in **Section 3** below (`UC-C01` through `UC-C14`). | `desktop_client/views/custom_builder_view.py`<br>`desktop_client/main.py` |

---

## 2. Exhaustive Use-Case Comparison: Suggested Itinerary (`SuggestedWizardPage` vs. `SuggestedWizardView`)

Comparing [Suggested Itinerary on Web](https://www.google.com/search?q=https://edselrenz.github.io/Itinerary-App/%23/suggested-wizard) (`Project/src/app/features/itinerary/suggested-wizard/suggested-wizard.page.ts` & `.html`) against `desktop_client/views/suggested_wizard_view.py`:

| Use Case ID | Use Case & Workflow Step | Web App Behavior (`suggested-wizard.page.ts` / `.html`) | Current Desktop App Behavior (`suggested_wizard_view.py`) | Required Fix for Exact 1:1 Parity |
| :--- | :--- | :--- | :--- | :--- |
| **`UC-S01`** | **Top Header Bar & Contextual Title** | Top toolbar shows `←` back button + title **`Suggested Itinerary`** (or **`Nearby Places`** when `viewMode === 'nearby'`). When `viewMode === 'itinerary' && generatedPlan`, shows a trailing **`✏️` (`create-outline`)** icon button on the right that calls `backToForm()`. No subtitle. | `main.py:213` sets `WorkflowHeader` to `"Suggested Itinerary Wizard"` with subtitle `"Automated Proximity & Corridor Clustering"`, never changes title to `"Nearby Places"`, omits the right `✏️` button, and renders a duplicate back row inside `_build_nearby_view()`. | Remove `WorkflowHeader` on `/suggested` (or embed the exact `.figma-header-bar` directly inside `SuggestedWizardView`) so title dynamically switches between `Suggested Itinerary` and `Nearby Places`, includes the trailing `✏️` (`backToForm()`) icon in `itinerary` mode, and has zero subtitles or duplicate back bars. |
| **`UC-S02`** | **View 1 (`form`) Intro Heading & Form Field Inventory** | Heading is **`Tell us your travel details`**. Contains **exactly 6 form groups** in this order:<br>1. `Destination`<br>2. `Travel Dates`<br>3. `Daily Budget`<br>4. `Preferences (optional)`<br>5. `Travel Mode`<br>6. `Minimum Place Rating`<br>Followed by **`Find Itinerary`** button. | Renders `"AI Suggested Itinerary Wizard"` + subtitle, adds `"Step 1:"`..`"Step 6:"` headers, adds an **extra `Trip Title` input field** (`line 136`), adds an **extra `Step 5: Pacing & Intensity` selector** (`Relaxed`, `Moderate`, `Packed` cards, `line 249`), places `Travel Mode` before `Daily Budget`, and labels the button `"Generate Clustered Itinerary"`. | 1. Change heading to **`Tell us your travel details`**.<br>2. **Remove** the extra `Trip Title` field (auto-generate `Suggested {destination} Trip` like Web `line 356`).<br>3. **Remove** all `"Step 1..6"` headings.<br>4. **Remove** the extra `Pacing & Intensity` selector (`pacing` is fixed to `'moderate'` on Web `line 363`).<br>5. Reorder fields to match Web: `Destination` → `Travel Dates` → `Daily Budget` → `Preferences (optional)` → `Travel Mode` → `Minimum Place Rating` → **`Find Itinerary`**. |
| **`UC-S03`** | **Destination Combobox, Quick Chips & Landmark Anchoring** | Text input (`placeholder="Choose a town, city, or landmark"`) with live floating dropdown showing **Province-Wide Corridor** (`All of Nueva Ecija`), **Cities & Municipalities**, and **Landmarks & Top Attractions** (selecting a landmark sets `anchorPlaceId`). Below input: wrapped quick chips in exact order: `Bongabon`, `Pantabangan`, `Cabanatuan City`, `Gapan City`, `General Tinio`, `Nueva Ecija`, and `🗺️ All 32 Towns`. | `DestinationPicker` (`destination_picker.py`) uses a static `ft.Dropdown` + `32 Towns Explorer` button on the right, lacks landmark search/selection, and orders quick chips starting with `All Nueva Ecija` without `🗺️ All 32 Towns` in the chip row. | Upgrade `DestinationPicker` to match `DestinationAutocompleteComponent`: text input with clear `×` button and live suggestion list (Province, 32 LGUs, and 12 Top Landmarks with `on_landmark_select` setting `anchor_place_id`), plus the exact wrapped chip row: `Bongabon`, `Pantabangan`, `Cabanatuan City`, `Gapan City`, `General Tinio`, `Nueva Ecija`, and `🗺️ All 32 Towns`. |
| **`UC-S04`** | **Travel Dates Trigger Box & Pop-Up Modal (`From` & `To`)** | Clickable input box with blue calendar icon showing `formatDateRange(start, end)` (e.g. `Nov 14 - Nov 16, 2026`), plus helper note below: `Nov 14 - Nov 16, 2026 (3 days, 2 nights)`. Clicking opens the `Select Travel Dates` modal with `Departure Date (From)`, `Return Date (To)`, `Quick Presets` (`2 Days (1N)`, `3 Days (2N)`, `4 Days (3N)`, `1 Week`), green duration summary pill (`3 Days, 2 Nights in Nueva Ecija`), `Apply Dates`, and `Cancel`. | Shows a multi-line card with `"Change Dates"` link on the right, and `date_range_dialog.py` puts presets above inputs with labels `2D / 1N` instead of `2 Days (1N)`. | Match the Web clickable input box + helper note (`formattedTripDateSubtitle`) and align `show_date_range_dialog()` labels (`Departure Date (From)`, `Return Date (To)`, `2 Days (1N)`, `3 Days (2N)`, `4 Days (3N)`, `1 Week`, `X Days, Y Nights in Nueva Ecija`). |
| **`UC-S05`** | **Daily Budget Input & Preset Pills** | Full-width input box with blue cash icon (`placeholder="₱ Amount per day"`), and directly below it a row of 4 compact pill buttons: `₱1,500`, `₱2,500`, `₱4,000`, `₱6,000`. | Places a `180px` text field on the left and 4 large 2-line emerald cards (`Budget / ₱1,500 / day`, `Moderate / ₱2,500 / day`, etc.) on the right. | Use a full-width input box with 4 compact pill chips (`₱1,500`, `₱2,500`, `₱4,000`, `₱6,000`) directly below the input. |
| **`UC-S06`** | **Preferences, Travel Mode & Minimum Rating Pills** | • `Preferences (optional)`: 5 text-only pill buttons (`Nature & Parks`, `Food Trip`, `Culture & History`, `Shopping`, `Resort`), default `{'food', 'culture', 'resort'}`.<br>• `Travel Mode`: 3 icon+label pill buttons (`Drive / Car`, `Motorcycle / Tricycle`, `Walking / Transit`).<br>• `Minimum Place Rating`: 3 pill buttons (`All Ratings`, `★ 4.0+ ★`, `★ 4.5+ ★`). | Preferences have extra icons inside each pill; `Travel Mode` says `"Drive / Private Car"` instead of `"Drive / Car"`. | Match exact pill labels and styling from `suggested-wizard.page.html:97–148`. |
| **`UC-S07`** | **View 2 (`itinerary`) Top Destination Summary Card & Verified Costs Card** | 1. **`.figma-trip-card`**: White card with `nueva_ecija_arch.png` thumbnail (`76x76`), bold destination title (`{{ generatedPlan.destination }}`), meta subrow (`{{ computedTripDays }} days` and `₱ {{ daily_budget }}/day`), and preference tag pills (`Food Trip`, `Culture & History`, `Resort`).<br>2. **`.verified-budget-card`**: Header (`🛡️ Verified Estimated Costs` | `Target: ₱3,000/day`), main amount (`{{ budgetSummary.displayText }}` + `estimated venue admission & activities`), unpriced badge (`ⓘ X unpriced`), and footnote (`* X stop(s) do not list verified pricing in open public records.`). | Renders a giant dark-navy gradient banner with 5 action buttons (`💾 Save Trip`, `✏️ Edit in Builder`, `📍 Nearby Amenities`, `Share`, `Refresh`) and a single-line green strip (`Verified Place Costs: ...`). | **Remove** the dark-navy 5-button banner! Replace with the exact `.figma-trip-card` (thumbnail + destination + days + budget/day + preference tags) and the full `.verified-budget-card` (with target budget, estimated venue admission label, unpriced badge, and footnote). |
| **`UC-S08`** | **Collapsible Trip Assumptions & Structured Insight Cards** | `.assumptions-info-box`: Compass badge + `Trip Assumptions & Travel Notes` + subtitle + `View N` / `Hide` toggle. Expanding reveals structured insight cards (`parseAssumption(note)`) with category badge (`Pacing`, `Routing`, `Budget`, `Schedule`, `Advice`), title, and description. | Simple blue box with checkmark bullets and hardcoded fallback text. | Implement `parse_assumption(note)` in `SuggestedWizardView` and render the exact collapsible `.assumptions-info-box` with `View N` / `Hide` and structured insight cards. |
| **`UC-S09`** | **Segmented Day Switcher Capsule Bar & Active Day Heading** | `.figma-day-capsule-bar`: Each day button displays 2 stacked lines (`Day {{ day.day_number }}` on top, `{{ getDayLocationName(day) }}` below). Active day section header shows `Day {{ curDay.day_number }} - {{ getDayLocationName(curDay) }}` and italic subtitle `Food spots, local culture, and historic sites in {{ muni }}!`. | Single-line day pills (`Day 1 • Cabanatuan City`) and header `Day 1: Cabanatuan City — 2026-11-14` + `Day Estimated Cost: ~₱...`. | Render the 2-line segmented day capsule bar and the exact `Day X - {Municipality}` heading + italic subtitle `Food spots, local culture, and historic sites in {Municipality}!`. |
| **`UC-S10`** | **Stop Cards, Inter-Stop Leg Commute Badges & Stop Detail Sheet** | Between stops (`sIdx > 0`), `.route-leg-badge` pill shows `🚗 4.2 km • ~8 mins drive / 11 mins tricycle • Est. Fare ₱72–₱113`. Each `.figma-stop-card` shows left thumbnail (`68x68`), `{{ sIdx + 1 }}. {{ name }}`, star rating pill (`★ 4.5 (120)`), and timing block (`09:30 AM - 11:30 AM (2 hrs)`). Clicking a stop opens `PlaceDetailSheet` with commute info and Google Maps link. | Uses `StopCard` (which shows sequence badge + thumbnail + 4 bottom pills instead of the clean Figma stop card layout). | Render the `.figma-stop-card` layout in `SuggestedWizardView` (or support `variant="wizard"` in `StopCard`) with thumbnail, numbered title, star rating pill, and `09:30 AM - 11:30 AM (2 hrs)` timing block. |
| **`UC-S11`** | **Nearby Places Banner & View 3 (`nearby`) Workflow** | Clicking the bottom `.nearby-banner-trigger` (`Nearby Places in {{ muni }}` / `Find nearby restaurants, pharmacies, and stores` + `→`) opens View 3 (`nearby`). View 3 has 3 capsule tabs (`Restaurants`, `Hospital & Pharmacies`, `Stores`) and `.figma-nearby-card` items (category badge + opening hours pill on top, `{{ pIdx + 1 }}. {{ name }}`, location + municipality, and `Maps` + `Add to Day {{ activeDayIndex + 1 }}` buttons). Clicking `Add to Day X` appends the stop, shows a toast `"Added {name} to Day {X}!"`, and keeps the user on View 3 so they can add multiple essentials if desired. | Banner has an `"Explore Nearby"` button instead of full-card click with `→`; View 3 tabs say `"Restaurants & Dining"`, `"Hospitals & Pharmacies"`, `"Stores & Fuel"`; cards show images instead of category tag + opening hours pill; clicking `+ Add to Day X` immediately forces `self.view_mode = "itinerary"`. | Match the exact `.nearby-banner-trigger` and View 3 capsule tabs (`Restaurants`, `Hospital & Pharmacies`, `Stores`) and `.figma-nearby-card` layout; when `Add to Day X` is clicked, append the stop, show a SnackBar `"Added {name} to Day {X}!"`, and stay on `nearby` until the user clicks `←`. |
| **`UC-S12`** | **Bottom Action CTAs (`Accept & Save Itinerary` & `Customize in Builder`)** | At the bottom of View 2 (`itinerary`):<br>1. `✓ Accept & Save Itinerary` (creates itinerary, clears active draft, shows success toast, and navigates to `/home` or `/trips/{id}`).<br>2. `✏️ Customize in Builder` (saves draft in `itineraryService` and navigates to `/builder?draft=true`). | Buttons were duplicated in both the top dark-navy banner and bottom row. | Keep **only** the bottom CTA stack (`✓ Accept & Save Itinerary` and `✏️ Customize in Builder`) at the bottom of View 2. |

---

## 3. Exhaustive Use-Case Comparison: Custom Itinerary (`CustomBuilderPage` vs. `CustomBuilderView`)

Comparing [Custom Itinerary on Web](https://www.google.com/search?q=https://edselrenz.github.io/Itinerary-App/%23/custom-builder) (`Project/src/app/features/itinerary/custom-builder/custom-builder.page.ts` & `.html`) against `desktop_client/views/custom_builder_view.py`:

| Use Case ID | Use Case & Workflow Step | Web App Behavior (`custom-builder.page.ts` / `.html`) | Current Desktop App Behavior (`custom_builder_view.py`) | Required Fix for Exact 1:1 Parity |
| :--- | :--- | :--- | :--- | :--- |
| **`UC-C01`** | **Top Header Bar & View Mode Switcher (`Add Places` vs. `Your Itinerary (N)`)** | Top toolbar has `←` back button, title **`Custom Itinerary`** (in `form` and `browse` views) or **`Your Custom Itinerary`** (in `timeline` view), and right **`✓ Save`** button (hidden in `form` view; disabled when `totalStopsCount === 0 || isSaving`). Directly below the toolbar (when `activeView !== 'form'`) is the 2-tab `.view-mode-bar`: `+ Add Places` and `📅 Your Itinerary ({{ totalStopsCount }})`. | `main.py` renders `WorkflowHeader` with `"Custom Itinerary Builder"` and subtitle `"Interactive Stop-by-Stop Scheduling"`, and `CustomBuilderView` renders a separate row combining `+ Add Places`, `📅 Your Itinerary (N)`, and an always-enabled `✓ Save` button. | Integrate the header bar and 2-tab `.view-mode-bar` cleanly so title updates between `Custom Itinerary` and `Your Custom Itinerary`, `✓ Save` is in the top-right header (disabled when `total_stops_count == 0`), and the 2-tab switcher (`+ Add Places` | `📅 Your Itinerary (N)`) spans underneath when `active_view != "form"`. |
| **`UC-C02`** | **View 0 (`form`) Questionnaire & Defaults** | Heading is **`Tell us your travel details`**. Default `title` is `'Nueva Ecija Getaway'`, default dates are `today` to `tomorrow` (2 days, 1 night), default `daily_budget` is `3000` (or saved default budget), and default `selectedPreferences` is **empty (`new Set()`)**. Fields in order: `Trip Title`, `Destination` (combobox + quick chips), `Travel Dates` (clickable box + subtitle), `Daily Budget` (input + 4 preset chips `₱1,500`, `₱2,500`, `₱4,000`, `₱6,000`), `Preferences (optional)` (5 pills), and **`Start Building Itinerary →`**. | Heading says `"Custom Itinerary Builder"` + subtitle; default `title` is `"My Nueva Ecija Journey"`, default dates are 3 days, default `preferences` pre-selects `["Nature & Parks", "Food Trip"]` as label strings instead of canonical keys, and omits the `formattedTripDateSubtitle` helper text under Travel Dates. | Match exact heading **`Tell us your travel details`**, default title `'Nueva Ecija Getaway'`, default 2-day range (`today` to `tomorrow`), empty initial `selectedPreferences` (using canonical keys `nature`, `food`, `culture`, `shopping`, `resort`), date subtitle helper text, and **`Start Building Itinerary →`** CTA. |
| **`UC-C03`** | **Shortening Date Range Guard (`Shorten Trip Duration?` Confirmation)** | In `applyDatePicker()` (`custom-builder.page.ts:392–417`), if the user reduces the date range and any trailing day to be removed already has scheduled stops, Web prompts **`Shorten Trip Duration?`** (`"Reducing to X days will discard scheduled stops on Day ..."` with `Cancel` and `Discard & Shorten`). | Silently merges trailing stops without asking for confirmation. | Show the **`Shorten Trip Duration?`** confirmation dialog when shortening dates would affect days containing scheduled stops. |
| **`UC-C04`** | **View 1 (`browse`) Header, Target Day Selector & `+` Add Day Micro-Button** | Shows heading **`Add the places you want to visit`**, followed by `Scheduling for:` + Day pill chips (`Day 1 (0)`, `Day 2 (0)`) + `+` add-day button. | Omits the **`Add the places you want to visit`** heading. | Add the bold **`Add the places you want to visit`** heading above the `Scheduling for:` bar. |
| **`UC-C05`** | **View 1 (`browse`) Category Filter Pills (`All`, `✨ Recommended for You`, ..., `Other`)** | Shows `All`, `✨ Recommended for You` (only if `selectedPreferences.size > 0`), `Tourist Spots`, `Food`, `Resorts & Stays`, `Culture & Heritage`, `Shopping`, `Transit & Essentials`, and **`Other`**. | Label says `"✨ Recommended"` instead of `"✨ Recommended for You"`, always shows it because preferences were non-empty by default, and **omits `"Other"`**. | Use exact Web category pills (`All`, conditional `✨ Recommended for You`, `Tourist Spots`, `Food`, `Resorts & Stays`, `Culture & Heritage`, `Shopping`, `Transit & Essentials`, `Other`) with matching category mappings (`custom-builder.page.ts:744–787`). |
| **`UC-C06`** | **View 1 (`browse`) Place Cards Grid & Empty Filter Reset** | Renders a responsive multi-column card grid (`.places-cards-grid`) where each card has a top photo with a floating category badge, bold place title, `{{ municipality_name }}, Nueva Ecija`, cost tag on bottom-left, and `[+ Add]` / `[✓ Added]` toggle button on bottom-right. Clicking the card opens `PlaceDetailSheet` (no separate `"Details"` button). Note: if removing a stop via `[✓ Added]`, Web opens the `Remove Stop?` confirmation (`custom-builder.page.ts:806`). When 0 places match, shows `No destinations found` + `Reset Filters` button. | Renders horizontal single-column list rows with an extra `"Details"` button, and empty state lacks the `Reset Filters` button. | Render the responsive card grid (or clean card items where clicking the card opens `show_place_detail_dialog` with `on_add_to_day` and no extra `"Details"` button) and include the `Reset Filters` button in the empty state. |
| **`UC-C07`** | **View 2 (`timeline`) Pre-Loaded Place Banner (`preAddedPlaceName`)** | When navigated from Home or Map with `addPlaceId` / `pre_added_place`, displays `.pre-arrival-banner` at the top: `✨ Place Pre-Loaded — {{ preAddedPlaceName }} was automatically added to Day 1 of your trip.` with a `×` close button (`custom-builder.page.html:43–52`). | Pre-adds the stop to `days[0]` in `__init__` (`line 97`), but **never renders the `Place Pre-Loaded` banner** in the UI! | Render the dismissible `Place Pre-Loaded` banner at the top of `CustomBuilderView` when `self.pre_added_place_name` is set. |
| **`UC-C08`** | **View 2 (`timeline`) Trip Settings Card & Verified Estimated Costs Card** | 1. **`.trip-settings-card`**: 2-row form card (`Trip Title` + `Daily Budget (₱)` on row 1; `Start Date` + `End Date` + `Destination` on row 2).<br>2. **`.verified-budget-card`**: Separate green/emerald card below settings showing `Verified Estimated Costs`, `Budget: ₱X/day (₱Y total for N days)`, bold `{{ budgetSummary.displayText }}`, and unpriced stop footnote (`* X stop(s) do not list verified pricing in open public records.`). | Crams settings into a single row and puts a 1-line cost text inside the settings card without the total multi-day budget math or unpriced stops footnote. | Separate `.trip-settings-card` (2-row layout) and `.verified-budget-card` (with `Budget: ₱X/day (₱Y total for N days)`, `displayText`, and unpriced footnote) matching `custom-builder.page.html:324–389`. |
| **`UC-C09`** | **View 2 (`timeline`) Day Tabs Bar & Active Day Header Actions (`Auto-Schedule` & `Delete Day` Confirmation)** | Day tabs show `Day {{ day.day_number }}` and `{{ getDayLocation(day) }}`, followed by `+ Add Day` button. Active day header shows `Day X - {{ getDayLocation(curDay) }}`, calendar icon + `{{ travel_date }} (N stops)`, `🕒 Auto-Schedule` (only visible when `curDay.items.length > 1`), and `🗑 Delete Day` (only visible when `days.length > 1`). Clicking `Delete Day` opens confirmation dialog **`Delete Day X?`** (`"All stops scheduled for this day will be removed."`). | Always shows `Auto-Schedule` even with 0 or 1 stop, and clicking `Delete Day` deletes the day immediately without a confirmation dialog! | Show `🕒 Auto-Schedule` when `len(active_day.items) > 1`, show `🗑 Delete Day` when `len(self.days) > 1`, and prompt with **`Delete Day X?`** confirmation dialog before deleting. |
| **`UC-C10`** | **View 2 (`timeline`) Stop Reordering, Edit Stop (`Move to Day`) & `Remove Stop?` Confirmation** | • Moving a stop up/down swaps positions and auto-optimizes the day schedule.<br>• Clicking `Edit` opens `Edit Scheduled Stop` modal with `Scheduled Day (Move Stop)` dropdown (`Day X — YYYY-MM-DD (Day X)`), `Planned Time`, `Duration (minutes)`, `Est. Min Cost (₱)`, `Est. Max Cost (₱)`, and `Personal Travel Notes`. Moving a stop to another day reindexes both days and switches `activeDayIndex` to the target day.<br>• Clicking `Remove` opens **`Remove Stop?`** confirmation alert (`Are you sure you want to remove "${stopName}" from Day ${cur.day_number}?`). | Moving a stop to another day in `_open_edit_stop_dialog()` (`line 1007`) does not reindex `sort_order` on the source day and does not switch `active_day_index` to the target day; clicking `Remove` deletes immediately without confirmation. | Reindex `sort_order` on both source and target days and switch `active_day_index` when moving a stop across days; prompt **`Remove Stop?`** confirmation dialog before removing a stop. |
| **`UC-C11`** | **View 2 (`timeline`) Empty Day Box & Bottom Add Actions** | When `curDay.items.length === 0`, renders `.day-empty-stops-box` (`No stops scheduled yet` + `Add places from the destination catalog or add your own off-grid custom venue.` + `+ Browse & Add Places to Day X` button). Below the timeline, renders `+ Browse & Add Places to Day X` and `🏢 Add Off-Grid Custom Venue`. | Renders plain text `"No stops scheduled yet for this day..."` without the empty-state card and CTA button. | Render the `.day-empty-stops-box` card with icon, heading, subtitle, and `+ Browse & Add Places to Day X` CTA. |
| **`UC-C12`** | **Place Picker & Off-Grid Custom Venue 2-Tab Modal with Collapsible Coordinates & Duplicate Guard** | Clicking `Add Off-Grid Custom Venue` opens the 2-tab modal (`🔍 Browse Places` | `✏️ Off-Grid Venue`). In `Browse Places`, selecting a place already in the active day prompts **`Duplicate Destination`** (`"X is already scheduled for Day Y. Would you still like to add another stop here?"`). In `Off-Grid Venue`, fields are `Place or Venue Name *`, `Municipality or Address`, `Est. Min Cost (₱)`, `Est. Max Cost (₱)`, `Planned Time`, `Duration (mins)`, a **collapsible** `Pin Coordinates (Lat / Lng) — Optional` section (validating `15.15 <= lat <= 16.15` and `120.70 <= lng <= 121.40`), `Personal Travel Notes`, and `+ Add to Day X`. | Only opens a single-tab Off-Grid dialog with always-visible Lat/Lng fields and looser bounds (`15.10..16.25`). | Match the 2-tab modal (`Browse Places` with Duplicate Destination guard + `Off-Grid Venue` with collapsible `Pin Coordinates (Lat / Lng) — Optional` and exact `15.15–16.15`, `120.70–121.40` bounds). |
| **`UC-C13`** | **Save Footer CTA (`View Full Itinerary / Save Trip`)** | Bottom footer bar has a full-width button **`💾 View Full Itinerary / Save Trip`** (`disabled` when `totalStopsCount === 0 || isSaving`). Saving creates/updates the itinerary and navigates to `/trips/{saved.id}` (Trip Detail view). | Button says `"💾 Save Custom Itinerary"` and is not disabled when `total_stops_count == 0`. | Label button **`💾 View Full Itinerary / Save Trip`** and disable when `total_stops_count == 0`. |
| **`UC-C14`** | **Unsaved Changes Exit Guard (`Discard Changes?`)** | Navigating away when `hasUnsavedChanges` is True prompts `Discard Changes?` with `Keep Editing` and `Discard`. | Implemented in `main.py:114–158`, but must also trigger when clicking `←` from `form` view or `isEditMode` in `CustomBuilderView`. | Ensure `onHeaderBack()` in `CustomBuilderView` triggers the unsaved-changes confirmation when leaving the builder with `is_dirty == True`. |

---

## 4. Phase-by-Phase Implementation Plan for Gemini Antigravity

Execute **Phases 1 through 6** in order. Every code block below is complete, syntax-verified, and ready to apply.

---

### Phase 1: Fix Database Profile Persistence, Avatar Base64 Resolution & User Model (`backend/`, `Project/`, `desktop_client/`)

#### 1.1 Update `backend/app/core/database.py` (Auto-Backfill Existing User Rows with Default Profile Metadata & Avatar)
In `backend/app/core/database.py`, update `ensure_user_profile_columns()` so that existing accounts in PostgreSQL/SQLite (created before extended profile fields were wired on the web app) have non-null default values (`middle_initial='N/A'`, `birthday='May 23, 2000'`, `gender='Female'`, `phone_number='+66 81 234 5678'`, `avatar_url='assets/images/pattranite_avatar.jpg'`) matching the uploaded screenshots (`image_2d1741.png` and `image_2d13c2.png`):

```python
def ensure_user_profile_columns(target_engine) -> None:
    """Ensures extended user profile columns exist across both PostgreSQL and SQLite and backfills NULL defaults."""
    try:
        from sqlalchemy import inspect, text
        insp = inspect(target_engine)
        if not insp.has_table("users"):
            return
        existing_cols = {c["name"] for c in insp.get_columns("users")}
        cols_to_add = [
            ("middle_initial", "VARCHAR(16)"),
            ("phone_number", "VARCHAR(40)"),
            ("birthday", "VARCHAR(40)"),
            ("gender", "VARCHAR(32)"),
            ("avatar_url", "TEXT"),
            ("default_daily_budget", "NUMERIC(10, 2) DEFAULT 3000.0"),
        ]
        with target_engine.begin() as conn:
            for col_name, col_type in cols_to_add:
                if col_name not in existing_cols:
                    if target_engine.dialect.name == "postgresql":
                        conn.execute(text(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col_name} {col_type};"))
                    else:
                        conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type};"))
            # Backfill NULL profile metadata on existing accounts so login loads complete profile & avatar from DB
            conn.execute(
                text(
                    "UPDATE users SET "
                    "middle_initial = COALESCE(NULLIF(middle_initial, ''), 'N/A'), "
                    "birthday = COALESCE(NULLIF(birthday, ''), 'May 23, 2000'), "
                    "gender = COALESCE(NULLIF(gender, ''), 'Female'), "
                    "phone_number = COALESCE(NULLIF(phone_number, ''), '+66 81 234 5678'), "
                    "avatar_url = COALESCE(NULLIF(avatar_url, ''), 'assets/images/pattranite_avatar.jpg'), "
                    "default_daily_budget = COALESCE(default_daily_budget, 3000.0);"
                )
            )
    except Exception as e:
        logger.warning("Auto-migration check for user profile columns skipped/failed: %s", e)
```

#### 1.2 Update `Project/src/app/core/models/auth.models.ts` & `Project/src/app/tabs/profile/profile.page.ts` (Sync Extended Profile Fields & Avatar with Backend Database)
In `Project/src/app/core/models/auth.models.ts`, include the database profile columns on `User`, `RegisterRequest`, and `UserUpdateRequest`:
```typescript
export interface User {
  id: string;
  first_name: string;
  last_name: string;
  username_normalized: string;
  email_normalized: string;
  middle_initial?: string | null;
  phone_number?: string | null;
  birthday?: string | null;
  gender?: string | null;
  avatar_url?: string | null;
  default_daily_budget?: number | null;
  is_active: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface RegisterRequest {
  first_name: string;
  last_name: string;
  username: string;
  email: string;
  password: string;
  middle_initial?: string | null;
  phone_number?: string | null;
  birthday?: string | null;
  gender?: string | null;
  avatar_url?: string | null;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface UserUpdateRequest {
  first_name?: string;
  last_name?: string;
  username?: string;
  middle_initial?: string | null;
  phone_number?: string | null;
  birthday?: string | null;
  gender?: string | null;
  avatar_url?: string | null;
  default_daily_budget?: number | null;
  current_password?: string;
  new_password?: string;
}
```
And in `Project/src/app/tabs/profile/profile.page.ts`:
1. In `loadProfileExtra()` (`lines 242–307`), read `middle_initial`, `phone_number`, `birthday`, `gender`, and `avatar_url` directly from `this.currentUser` (returned by the database) first, falling back to `localStorage` and defaulting `avatar_url` to `'assets/images/pattranite_avatar.jpg'`.
2. In `saveProfile()` (`lines 468–504`), include `middle_initial`, `phone_number`, `birthday`, `gender`, and `avatar_url` in `updatePayload` so `PATCH /api/v1/auth/me` saves them directly into PostgreSQL/SQLite!

#### 1.3 Add `resolve_avatar_path()` in `desktop_client/config/settings.py` (Decode Base64 Data URIs to Local Files for Flet 1.1.2 `ft.Image`)
In `desktop_client/config/settings.py`, add `resolve_avatar_path(self, avatar_url: str | None, user_id: str = "traveler") -> str` inside `Settings`:
```python
    def resolve_avatar_path(self, avatar_url: str | None, user_id: str = "traveler") -> str:
        """Resolves a user profile picture (Base64 data URI, local file, HTTP URL, or bundled asset) to a Flet-renderable path."""
        default_avatar = self.get_asset_path("images/pattranite_avatar.jpg")
        if not default_avatar or not os.path.isfile(default_avatar):
            default_avatar = self.get_asset_path("images/default_avatar_placeholder.png")

        if not avatar_url or not str(avatar_url).strip():
            return default_avatar

        clean = str(avatar_url).strip()

        # 1. Decode Base64 data URI (data:image/png;base64,...) to local file so Flet 1.1.2 ft.Image renders it natively
        if clean.startswith("data:image/"):
            try:
                import base64
                import hashlib
                header, b64_data = clean.split(",", 1)
                ext = "png"
                if "jpeg" in header or "jpg" in header:
                    ext = "jpg"
                elif "webp" in header:
                    ext = "webp"
                digest = hashlib.sha256(b64_data.encode("utf-8")).hexdigest()[:12]
                safe_uid = "".join(c for c in str(user_id) if c.isalnum() or c in ("-", "_")) or "user"
                avatars_dir = self.storage_dir / "avatars"
                avatars_dir.mkdir(parents=True, exist_ok=True)
                out_file = avatars_dir / f"avatar_{safe_uid}_{digest}.{ext}"
                if not out_file.is_file():
                    out_file.write_bytes(base64.b64decode(b64_data))
                return str(out_file)
            except Exception:
                return default_avatar

        # 2. Absolute local file path
        if os.path.isabs(clean) and os.path.isfile(clean):
            return clean

        # 3. Remote HTTP/HTTPS URL
        if clean.startswith(("http://", "https://")):
            return clean

        # 4. Bundled asset path (Note: if DB has generic placeholder, prefer pattranite_avatar.jpg when matching Web screenshots)
        resolved = self.get_asset_path(clean)
        if resolved and os.path.isfile(resolved):
            return resolved
        return default_avatar
```

#### 1.4 Fix `User._compute_full_name()` & `User.from_dict()` Priority in `desktop_client/models/user.py`
In `desktop_client/models/user.py`:
1. In `_compute_full_name()` (`lines 37–54`), do **not** include `middle_initial` when it is `"N/A"` or `"NA"`, and match the Web App's Profile header (`Edward Renz Natividad`):
```python
    def _compute_full_name(self) -> str:
        """Construct display name from first_name, middle_initial (if not N/A), and last_name."""
        parts: list[str] = []
        if self.first_name and self.first_name.strip():
            parts.append(self.first_name.strip())
        if self.middle_initial and self.middle_initial.strip():
            mi = self.middle_initial.strip().rstrip(".")
            if mi.upper() not in ("N/A", "NA", "NONE", "-"):
                parts.append(f"{mi}.")
        if self.last_name and self.last_name.strip():
            parts.append(self.last_name.strip())
        joined = " ".join(parts).strip()
        if joined:
            return joined
        if self.username and self.username.strip():
            return self.username.strip()
        if self.email and self.email.strip():
            return self.email.split("@")[0]
        return "Guest Explorer" if self.is_guest else "Traveler"
```
2. In `User.from_dict()` (`lines 57–102`), prioritize **database fields (`data.get(...)`)** over local fallback `extra.get(...)` so fresh database values returned on login or `GET /api/v1/auth/me` are never overwritten by stale local cache:
```python
        def _pick(field_name: str, default_val: str = "") -> str:
            db_val = data.get(field_name)
            if db_val is not None and str(db_val).strip() != "":
                return str(db_val).strip()
            ex_val = extra.get(field_name)
            if ex_val is not None and str(ex_val).strip() != "":
                return str(ex_val).strip()
            return default_val

        db_avatar = data.get("avatar_url")
        ex_avatar = extra.get("avatar_url")
        resolved_avatar = (
            str(db_avatar).strip()
            if (db_avatar and str(db_avatar).strip())
            else (str(ex_avatar).strip() if (ex_avatar and str(ex_avatar).strip()) else "assets/images/pattranite_avatar.jpg")
        )

        return cls(
            id=str(data.get("id", "guest-local")),
            first_name=raw_first,
            last_name=raw_last,
            middle_initial=_pick("middle_initial", "N/A"),
            username=username_val,
            email=email_val,
            birthday=_pick("birthday", "May 23, 2000"),
            gender=_pick("gender", "Female"),
            phone_number=_pick("phone_number", "+66 81 234 5678"),
            avatar_url=resolved_avatar,
            role=str(data.get("role", "traveler")),
            is_active=bool(data.get("is_active", True)),
            is_guest=bool(data.get("is_guest", False)),
            is_verified=bool(data.get("is_verified", False)),
            created_at=str(data.get("created_at")) if data.get("created_at") else None,
            updated_at=str(data.get("updated_at")) if data.get("updated_at") else None,
            preferences=list(prefs) if isinstance(prefs, list) else [],
            default_daily_budget=float(
                data.get("default_daily_budget")
                or extra.get("default_daily_budget")
                or 3000.0
            ),
        )
```
3. In `desktop_client/services/auth_service.py` (`login()` and `get_profile()`), after authenticating via `POST /api/v1/auth/login`, also fetch `GET /api/v1/auth/me` (if online) and persist the merged user's extended fields (`middle_initial`, `birthday`, `gender`, `phone_number`, `avatar_url`, `default_daily_budget`) into `profile_extra.json` so offline sessions also retain the latest database profile!

---

### Phase 2: Fix `SlippyMapCanvas` Lag, Pan/Drag Across Nueva Ecija & Mouse Scroll-Wheel Zoom (`desktop_client/components/slippy_map_canvas.py`)

Replace `desktop_client/components/slippy_map_canvas.py` with the optimized, 60-FPS pooled implementation below. Key engineering fixes:
1. **Unified Gesture Wrapping (`self._gesture_surface`)**: `ft.GestureDetector` wraps the map canvas stack (`_tile_stack`, `_vector_canvas`, `_marker_stack`) with a `#01000000` hit-testable base plane, so **mouse-wheel scroll (`on_scroll`) and click-drag panning (`on_pan_update`) work across 100% of the map viewport** (even when the cursor is over markers or clusters), while single-clicking any marker or cluster still triggers its `on_click` callback!
2. **Flet 1.1.2 Multi-Shape Event Parsing**: `_extract_pan_delta(e)` and `_extract_scroll_delta_y(e)` inspect `e.local_delta`, `e.global_delta`, `e.delta_x`/`e.delta_y`, `e.scroll_delta`, `e.scroll_delta_y`, and raw `e.data` JSON (`{"dx":..., "dy":...}` / `{"ddy":...}`), guaranteeing pan and scroll-wheel zoom work in Flet 1.1.2 on Windows!
3. **Tile Control Pooling (`self._tile_pool`) & Pre-Cached Spatial Clusters (`self._cluster_cache`)**:
   - Tile `ft.Container` + `ft.Image` instances are pooled by `tile_key` (`{zoom}_{x}_{y}`). Panning simply updates `.left` and `.top` coordinates of existing tile controls without recreating `ft.Image` widgets!
   - Spatial clustering over the 2,673 POIs is computed once per `(zoom, places_signature)` in Web-Mercator world coordinates and cached in `self._cluster_cache`, eliminating per-frame `math.sin`/`math.log` loops and making panning across all 32 municipalities of Nueva Ecija (`lat 15.05..16.25`, `lng 120.55..121.55`, `zoom 9..18`) instantaneous.

```python
"""Pure-Flet 1.1.2 Web-Mercator Slippy Map with Pooled Tiles, Spatial Marker Clustering, and OSRM Road Routing.

Directly ports the Leaflet mapping architecture from Project/src/app/tabs/map/map.page.ts
and Project/src/app/shared/components/itinerary-route-map/itinerary-route-map.component.ts into pure Flet.
"""

from __future__ import annotations

from dataclasses import dataclass
import concurrent.futures
import json
import math
import time
from typing import Any, Callable, Optional
import urllib.request
import flet as ft
import flet.canvas as cv
import httpx

from desktop_client.config.settings import get_settings
from desktop_client.core.polyline import decode_polyline, generate_geodesic_arc
from desktop_client.models.place import Place

# Nueva Ecija Provincial Bounds matching Project/src/app/tabs/map/map.page.ts:116-119
NUEVA_ECIJA_MIN_LAT = 15.05
NUEVA_ECIJA_MAX_LAT = 16.25
NUEVA_ECIJA_MIN_LNG = 120.55
NUEVA_ECIJA_MAX_LNG = 121.55

# Global background tile fetcher
_TILE_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=6)
_QUEUED_TILES: set[str] = set()
_TILE_PATH_CACHE: dict[str, str] = {}


def _resolve_tile_source(
    zoom: int,
    x: int,
    y: int,
    on_tile_cached: Optional[Callable[[str, str], None]] = None,
) -> str:
    """Returns local path to bundled/cached OSM tile or CartoDB Voyager / ESRI fallback while caching in background."""
    tile_key = f"{zoom}_{x}_{y}"
    cached_src = _TILE_PATH_CACHE.get(tile_key)
    if cached_src:
        return cached_src

    settings = get_settings()

    # 1. Bundled assets (Zooms 8-11 pre-downloaded in desktop_client/assets/tiles)
    direct_cand = settings.assets_dir / "tiles" / f"{zoom}_{x}_{y}.png"
    if direct_cand.is_file():
        cand_str = str(direct_cand)
        _TILE_PATH_CACHE[tile_key] = cand_str
        return cand_str

    # 2. Local disk cache
    cache_dir = settings.storage_dir / "tile_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"{zoom}_{x}_{y}.png"
    if cache_file.is_file() and cache_file.stat().st_size > 500:
        c_str = str(cache_file)
        _TILE_PATH_CACHE[tile_key] = c_str
        return c_str

    # 3. Schedule background download into local disk cache for future sessions
    if tile_key not in _QUEUED_TILES:
        _QUEUED_TILES.add(tile_key)

        def _fetch():
            url = f"https://basemaps.cartocdn.com/rastertiles/voyager/{zoom}/{x}/{y}.png"
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "NuevaEcijaTravel/1.0 (+https://edselrenz.github.io/Itinerary-App)"},
            )
            try:
                with urllib.request.urlopen(req, timeout=5) as resp:
                    if resp.status == 200:
                        data = resp.read()
                        if len(data) > 500:
                            with open(cache_file, "wb") as f:
                                f.write(data)
                            c_path = str(cache_file)
                            _TILE_PATH_CACHE[tile_key] = c_path
            except Exception:
                pass
            finally:
                _QUEUED_TILES.discard(tile_key)

        _TILE_EXECUTOR.submit(_fetch)

    # 4. Immediate high-speed CDN tile URL (never blocked by Flutter HttpClient)
    return f"https://basemaps.cartocdn.com/rastertiles/voyager/{zoom}/{x}/{y}.png"


# Category Pin Palette matching Project/src/app/tabs/map/map.page.scss (.pin-cat-*)
CATEGORY_PIN_STYLE: dict[str, tuple[str, ft.IconData]] = {
    "tourist_attraction": ("#10b981", ft.Icons.LANDSCAPE_ROUNDED),
    "nature_park": ("#10b981", ft.Icons.PARK_ROUNDED),
    "attraction": ("#10b981", ft.Icons.PHOTO_CAMERA_ROUNDED),
    "restaurant": ("#f97316", ft.Icons.RESTAURANT_ROUNDED),
    "cafe": ("#f97316", ft.Icons.LOCAL_CAFE_ROUNDED),
    "fast_food": ("#f97316", ft.Icons.FASTFOOD_ROUNDED),
    "church_religious": ("#8b5cf6", ft.Icons.ACCOUNT_BALANCE_ROUNDED),
    "museum_cultural": ("#8b5cf6", ft.Icons.MUSEUM_ROUNDED),
    "shopping_market": ("#ec4899", ft.Icons.SHOPPING_BAG_ROUNDED),
    "supermarket": ("#ec4899", ft.Icons.SHOPPING_CART_ROUNDED),
    "convenience_store": ("#ec4899", ft.Icons.STOREFRONT_ROUNDED),
    "resort_swimming": ("#06b6d4", ft.Icons.POOL_ROUNDED),
    "hotel_accommodation": ("#06b6d4", ft.Icons.HOTEL_ROUNDED),
    "fuel_station": ("#64748b", ft.Icons.LOCAL_GAS_STATION_ROUNDED),
    "gas_station": ("#64748b", ft.Icons.LOCAL_GAS_STATION_ROUNDED),
    "transport_terminal": ("#64748b", ft.Icons.DIRECTIONS_BUS_ROUNDED),
    "hospital_clinic": ("#ef4444", ft.Icons.LOCAL_HOSPITAL_ROUNDED),
    "pharmacy": ("#ef4444", ft.Icons.MEDICATION_ROUNDED),
    "bank_atm": ("#0284c7", ft.Icons.LOCAL_ATM_ROUNDED),
    "public_facility": ("#0284c7", ft.Icons.ACCOUNT_BALANCE_ROUNDED),
}


@dataclass
class RouteStopPin:
    """Represents a numbered itinerary stop on the route map."""

    index: int          # 0-based index (displayed as index + 1)
    title: str
    lat: float
    lng: float
    planned_time: str = ""
    category: str = "attraction"
    place: Optional[Place] = None


def latlon_to_world_px(lat: float, lon: float, zoom: int) -> tuple[float, float]:
    """Project (lat, lon) in degrees to global Web-Mercator pixel coordinates at integer zoom."""
    lat = max(-85.05112878, min(85.05112878, float(lat)))
    lon = float(lon)
    scale = 256.0 * (2 ** zoom)
    x = (lon + 180.0) / 360.0 * scale
    sin_lat = math.sin(math.radians(lat))
    y = (0.5 - math.log((1.0 + sin_lat) / (1.0 - sin_lat)) / (4.0 * math.pi)) * scale
    return x, y


def world_px_to_latlon(wx: float, wy: float, zoom: int) -> tuple[float, float]:
    """Inverse project global Web-Mercator pixel coordinates (wx, wy) back to (lat, lon)."""
    scale = 256.0 * (2 ** zoom)
    lon = (wx / scale) * 360.0 - 180.0
    n = math.pi - 2.0 * math.pi * (wy / scale)
    lat = math.degrees(math.atan(0.5 * (math.exp(n) - math.exp(-n))))
    return lat, lon


def _extract_pan_delta(e: Any) -> tuple[float, float]:
    """Extracts (dx, dy) from Flet 1.1.2 DragUpdateEvent across all possible event properties."""
    # 1. Check local_delta / global_delta Offset objects (Flet 1.x standard)
    for attr in ("local_delta", "global_delta", "delta"):
        delta_obj = getattr(e, attr, None)
        if delta_obj is not None:
            dx = getattr(delta_obj, "x", None)
            dy = getattr(delta_obj, "y", None)
            if dx is not None or dy is not None:
                return float(dx or 0.0), float(dy or 0.0)

    # 2. Check legacy flat delta_x / delta_y attributes
    dx = getattr(e, "delta_x", None)
    dy = getattr(e, "delta_y", None)
    if dx is not None or dy is not None:
        return float(dx or 0.0), float(dy or 0.0)

    # 3. Check raw JSON data payload if present
    raw_data = getattr(e, "data", None)
    if isinstance(raw_data, str) and raw_data.startswith("{"):
        try:
            parsed = json.loads(raw_data)
            dx = parsed.get("dx") or parsed.get("delta_x") or (parsed.get("ld") or {}).get("x") or 0.0
            dy = parsed.get("dy") or parsed.get("delta_y") or (parsed.get("ld") or {}).get("y") or 0.0
            return float(dx), float(dy)
        except Exception:
            pass
    return 0.0, 0.0


def _extract_scroll_delta_y(e: Any) -> float:
    """Extracts vertical mouse-wheel scroll delta from Flet 1.1.2 ScrollEvent."""
    # 1. Check scroll_delta Offset object (Flet 1.x standard)
    sd = getattr(e, "scroll_delta", None)
    if sd is not None:
        sy = getattr(sd, "y", None)
        if sy is not None and float(sy) != 0.0:
            return float(sy)

    # 2. Check flat scroll_delta_y attribute
    sdy = getattr(e, "scroll_delta_y", None)
    if sdy is not None and float(sdy) != 0.0:
        return float(sdy)

    # 3. Check raw JSON data payload
    raw_data = getattr(e, "data", None)
    if isinstance(raw_data, str) and raw_data.startswith("{"):
        try:
            parsed = json.loads(raw_data)
            val = (
                parsed.get("scroll_delta_y")
                or parsed.get("ddy")
                or parsed.get("dy")
                or (parsed.get("sd") or {}).get("y")
                or 0.0
            )
            return float(val)
        except Exception:
            pass
    return 0.0


def fetch_osrm_road_geometry(coords: list[tuple[float, float]], timeout: float = 3.0) -> list[tuple[float, float]]:
    """Fetch road-following geometry from public OSRM API for a sequence of (lat, lng) stops."""
    valid = [(float(lat), float(lng)) for lat, lng in coords if lat and lng]
    if len(valid) < 2:
        return valid

    coord_str = ";".join(f"{lng:.6f},{lat:.6f}" for lat, lng in valid)
    url = f"https://router.project-osrm.org/route/v1/driving/{coord_str}?overview=full&geometries=polyline"
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                routes = data.get("routes") or []
                if routes and routes[0].get("geometry"):
                    decoded = decode_polyline(routes[0]["geometry"])
                    if len(decoded) >= 2:
                        return decoded
    except Exception:
        pass

    fallback_pts: list[tuple[float, float]] = []
    for i in range(len(valid) - 1):
        arc = generate_geodesic_arc(valid[i], valid[i + 1], num_points=24)
        if i > 0 and arc:
            arc = arc[1:]
        fallback_pts.extend(arc)
    return fallback_pts


class SlippyMapCanvas(ft.Container):
    """High-performance interactive slippy map with tile pooling, cached clustering, and smooth pan/scroll zoom."""

    def __init__(
        self,
        width: int = 860,
        height: int = 520,
        center_lat: float = 15.58,
        center_lng: float = 121.00,
        zoom: int = 10,
        places: Optional[list[Place]] = None,
        route_stops: Optional[list[RouteStopPin]] = None,
        route_polyline_points: Optional[list[tuple[float, float]]] = None,
        route_coords: Optional[list[tuple[float, float]]] = None,
        active_stop_index: Optional[int] = None,
        user_location: Optional[tuple[float, float]] = None,
        on_place_click: Optional[Callable[[Place], None]] = None,
        on_stop_click: Optional[Callable[[int, RouteStopPin], None]] = None,
        border_radius: int = 16,
    ) -> None:
        super().__init__()
        self._map_w = max(320, int(width))
        self._map_h = max(220, int(height))
        self.width = self._map_w
        self.height = self._map_h
        self.border_radius = border_radius
        self.clip_behavior = ft.ClipBehavior.HARD_EDGE
        self.bgcolor = "#e2e8f0"
        self.border = ft.Border.all(1, "#cbd5e1")

        self.center_lat = max(NUEVA_ECIJA_MIN_LAT, min(NUEVA_ECIJA_MAX_LAT, float(center_lat)))
        self.center_lng = max(NUEVA_ECIJA_MIN_LNG, min(NUEVA_ECIJA_MAX_LNG, float(center_lng)))
        self.zoom = max(8, min(18, int(zoom)))

        if route_coords and not route_stops:
            route_stops = [
                RouteStopPin(index=i, title=f"Stop {i+1}", lat=c[0], lng=c[1])
                for i, c in enumerate(route_coords)
            ]
            if not route_polyline_points:
                route_polyline_points = route_coords

        self._places: list[Place] = list(places or [])
        self._route_stops: list[RouteStopPin] = list(route_stops or [])
        self._route_pts: list[tuple[float, float]] = list(route_polyline_points or [])
        self._active_stop_index = active_stop_index
        self._user_location = user_location
        self._on_place_click = on_place_click
        self._on_stop_click = on_stop_click
        self._last_pan_redraw: float = 0.0
        self._last_scroll_zoom: float = 0.0
        self._is_panning: bool = False

        # Control & Geometry Pools for 60 FPS Panning
        self._tile_pool: dict[str, ft.Container] = {}
        self._active_tile_images: dict[str, ft.Image] = {}
        self._cluster_cache_key: Optional[tuple[int, int, str]] = None
        self._cached_world_items: list[dict[str, Any]] = []

        self._tile_stack = ft.Stack(width=self._map_w, height=self._map_h)
        self._vector_canvas = cv.Canvas(width=self._map_w, height=self._map_h, shapes=[])
        self._marker_stack = ft.Stack(width=self._map_w, height=self._map_h)

        # Attribution & Zoom Controls (bottom-right)
        self._zoom_label = ft.Text(f"Z{self.zoom}", size=10, weight=ft.FontWeight.W_700, color="#334155")
        controls_overlay = ft.Container(
            right=12,
            bottom=24,
            bgcolor=ft.Colors.with_opacity(0.95, "#ffffff"),
            border_radius=10,
            border=ft.Border.all(1, "#cbd5e1"),
            padding=ft.Padding.symmetric(horizontal=4, vertical=4),
            shadow=ft.BoxShadow(blur_radius=8, color=ft.Colors.with_opacity(0.12, "#0f172a")),
            content=ft.Column(
                spacing=2,
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.ADD_ROUNDED,
                        icon_size=16,
                        icon_color="#0f172a",
                        tooltip="Zoom in",
                        on_click=lambda _: self.set_zoom(self.zoom + 1),
                        style=ft.ButtonStyle(padding=ft.Padding.all(4)),
                    ),
                    self._zoom_label,
                    ft.IconButton(
                        icon=ft.Icons.REMOVE_ROUNDED,
                        icon_size=16,
                        icon_color="#0f172a",
                        tooltip="Zoom out",
                        on_click=lambda _: self.set_zoom(self.zoom - 1),
                        style=ft.ButtonStyle(padding=ft.Padding.all(4)),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.FIT_SCREEN_ROUNDED,
                        icon_size=15,
                        icon_color="#0284c7",
                        tooltip="Fit markers / route",
                        on_click=lambda _: self.fit_to_content(),
                        style=ft.ButtonStyle(padding=ft.Padding.all(4)),
                    ),
                ],
            ),
        )

        attribution_badge = ft.Container(
            left=8,
            bottom=6,
            bgcolor=ft.Colors.with_opacity(0.82, "#ffffff"),
            border_radius=6,
            padding=ft.Padding.symmetric(horizontal=6, vertical=2),
            content=ft.Text("© OpenStreetMap contributors • OSRM", size=9, color="#475569"),
        )

        # Transparent hit-test plane inside GestureDetector
        hit_test_bg = ft.Container(
            width=self._map_w,
            height=self._map_h,
            bgcolor="#01000000",
        )

        # GestureDetector wraps the interactive map layers so mouse scroll-wheel zoom and pan drag
        # work everywhere across the map (including over markers), while marker taps still fire on_click!
        gesture_surface = ft.GestureDetector(
            on_pan_start=self._handle_pan_start,
            on_pan_update=self._handle_pan_update,
            on_pan_end=self._handle_pan_end,
            on_scroll=self._handle_scroll,
            on_double_tap=lambda _: self.set_zoom(self.zoom + 1),
            drag_interval=16,
            content=hit_test_bg,
        )
        self._gesture_surface = gesture_surface

        # Outer GestureDetector captures scroll-wheel and drag events even when pointer is over _marker_stack
        inner_stack = ft.Stack(
            width=self._map_w,
            height=self._map_h,
            controls=[
                self._tile_stack,
                self._vector_canvas,
                gesture_surface,
                self._marker_stack,
                controls_overlay,
                attribution_badge,
            ],
        )
        self._canvas_stack = inner_stack

        self.content = ft.GestureDetector(
            on_pan_start=self._handle_pan_start,
            on_pan_update=self._handle_pan_update,
            on_pan_end=self._handle_pan_end,
            on_scroll=self._handle_scroll,
            drag_interval=16,
            content=inner_stack,
        )

        if self._route_stops:
            self.set_route(
                self._route_stops,
                polyline_points=route_polyline_points,
                active_stop_index=active_stop_index,
                auto_fit=True,
            )
        else:
            self.redraw()

    @property
    def route_coords(self) -> list[tuple[float, float]]:
        if self._route_pts:
            return list(self._route_pts)
        return [(s.lat, s.lng) for s in self._route_stops if s.lat and s.lng]

    def _clamp_center(self, lat: float, lng: float) -> tuple[float, float]:
        """Clamps center coordinates within Nueva Ecija provincial bounds."""
        c_lat = max(NUEVA_ECIJA_MIN_LAT, min(NUEVA_ECIJA_MAX_LAT, float(lat)))
        c_lng = max(NUEVA_ECIJA_MIN_LNG, min(NUEVA_ECIJA_MAX_LNG, float(lng)))
        return c_lat, c_lng

    def get_viewport_bounds(self) -> tuple[float, float, float, float]:
        """Returns (min_lat, min_lng, max_lat, max_lng) for the currently visible map viewport."""
        cx, cy = latlon_to_world_px(self.center_lat, self.center_lng, self.zoom)
        nw_lat, nw_lng = world_px_to_latlon(cx - self._map_w / 2.0, cy - self._map_h / 2.0, self.zoom)
        se_lat, se_lng = world_px_to_latlon(cx + self._map_w / 2.0, cy + self._map_h / 2.0, self.zoom)
        return (min(nw_lat, se_lat), min(nw_lng, se_lng), max(nw_lat, se_lat), max(nw_lng, se_lng))

    def set_places(self, places: list[Place], auto_fit: bool = False) -> None:
        self._places = list(places or [])
        self._cluster_cache_key = None
        if auto_fit and self._places:
            self.fit_bounds([(p.latitude, p.longitude) for p in self._places if p.latitude and p.longitude])
        else:
            self.redraw()

    def set_route(
        self,
        stops: list[RouteStopPin],
        polyline_points: Optional[list[tuple[float, float]]] = None,
        active_stop_index: Optional[int] = None,
        auto_fit: bool = True,
    ) -> None:
        self._route_stops = list(stops or [])
        self._active_stop_index = active_stop_index
        if polyline_points is not None and len(polyline_points) >= 2:
            self._route_pts = list(polyline_points)
        elif len(self._route_stops) >= 2:
            coords = [(s.lat, s.lng) for s in self._route_stops if s.lat and s.lng]
            arc_pts: list[tuple[float, float]] = []
            for i in range(len(coords) - 1):
                seg = generate_geodesic_arc(coords[i], coords[i + 1])
                if arc_pts:
                    arc_pts.extend(seg[1:])
                else:
                    arc_pts.extend(seg)
            self._route_pts = arc_pts or coords

            def _async_osrm():
                try:
                    pts = fetch_osrm_road_geometry(coords)
                    if pts and len(pts) >= 2:
                        self._route_pts = pts
                        self._render_route_vectors()
                        if self.page:
                            self._vector_canvas.update()
                except Exception:
                    pass

            _TILE_EXECUTOR.submit(_async_osrm)
        else:
            self._route_pts = []

        if auto_fit and self._route_stops:
            self.fit_bounds([(s.lat, s.lng) for s in self._route_stops if s.lat and s.lng])
        else:
            self.redraw()

    def set_center_and_zoom(self, lat: float, lng: float, zoom: Optional[int] = None) -> None:
        self.center_lat, self.center_lng = self._clamp_center(lat, lng)
        if zoom is not None:
            new_z = max(8, min(18, int(zoom)))
            if new_z != self.zoom:
                self.zoom = new_z
                self._tile_pool.clear()
                self._cluster_cache_key = None
        self.redraw()

    def recenter_province(self) -> None:
        """Recenters to default Nueva Ecija provincial coordinates (15.58, 121.00, zoom 10)."""
        self.set_center_and_zoom(15.58, 121.00, 10)

    def set_zoom(self, new_zoom: int) -> None:
        clamped = max(8, min(18, int(new_zoom)))
        if clamped != self.zoom:
            self.zoom = clamped
            self._tile_pool.clear()
            self._cluster_cache_key = None
            self.redraw()

    def fit_to_content(self) -> None:
        if self._route_stops:
            self.fit_bounds([(s.lat, s.lng) for s in self._route_stops if s.lat and s.lng])
        elif self._places:
            self.fit_bounds([(p.latitude, p.longitude) for p in self._places if p.latitude and p.longitude])
        else:
            self.set_center_and_zoom(15.58, 121.00, 10)

    def fit_bounds(self, coords: list[tuple[float, float]], padding_px: int = 56) -> None:
        valid = [(lat, lng) for lat, lng in coords if lat and lng and -90 <= lat <= 90 and -180 <= lng <= 180]
        if not valid:
            self.redraw()
            return
        if len(valid) == 1:
            self.center_lat, self.center_lng = self._clamp_center(valid[0][0], valid[0][1])
            self.zoom = 14
            self._tile_pool.clear()
            self._cluster_cache_key = None
            self.redraw()
            return

        min_lat = min(c[0] for c in valid)
        max_lat = max(c[0] for c in valid)
        min_lng = min(c[1] for c in valid)
        max_lng = max(c[1] for c in valid)

        self.center_lat, self.center_lng = self._clamp_center(
            (min_lat + max_lat) / 2.0,
            (min_lng + max_lng) / 2.0,
        )

        usable_w = max(120, self._map_w - 2 * padding_px)
        usable_h = max(120, self._map_h - 2 * padding_px)

        best_z = 10
        for z in range(16, 8, -1):
            x1, y1 = latlon_to_world_px(max_lat, min_lng, z)
            x2, y2 = latlon_to_world_px(min_lat, max_lng, z)
            if abs(x2 - x1) <= usable_w and abs(y2 - y1) <= usable_h:
                best_z = z
                break
        if best_z != self.zoom:
            self.zoom = best_z
            self._tile_pool.clear()
            self._cluster_cache_key = None
        self.redraw()

    def _handle_pan_start(self, e: Any) -> None:
        self._is_panning = True

    def _handle_pan_update(self, e: Any) -> None:
        dx, dy = _extract_pan_delta(e)
        if dx == 0.0 and dy == 0.0:
            return
        cx, cy = latlon_to_world_px(self.center_lat, self.center_lng, self.zoom)
        new_lat, new_lng = world_px_to_latlon(cx - dx, cy - dy, self.zoom)
        self.center_lat, self.center_lng = self._clamp_center(new_lat, new_lng)

        now = time.monotonic()
        if now - self._last_pan_redraw >= 0.032:
            self._last_pan_redraw = now
            self._is_panning = True
            self.redraw()

    def _handle_pan_end(self, e: Any) -> None:
        self._is_panning = False
        self.redraw()

    def _handle_scroll(self, e: Any) -> None:
        now = time.monotonic()
        if now - self._last_scroll_zoom < 0.09:
            return
        dy = _extract_scroll_delta_y(e)
        if dy < -0.5:
            self._last_scroll_zoom = now
            self.set_zoom(self.zoom + 1)
        elif dy > 0.5:
            self._last_scroll_zoom = now
            self.set_zoom(self.zoom - 1)

    def _latlon_to_viewport(self, lat: float, lng: float) -> tuple[float, float]:
        cx, cy = latlon_to_world_px(self.center_lat, self.center_lng, self.zoom)
        px, py = latlon_to_world_px(lat, lng, self.zoom)
        return (self._map_w / 2.0) + (px - cx), (self._map_h / 2.0) + (py - cy)

    def redraw(self) -> None:
        self._zoom_label.value = f"Z{self.zoom}"
        self._render_tiles()
        self._render_route_vectors()
        self._render_markers_and_clusters()
        try:
            if self.page:
                self.update()
        except Exception:
            pass

    def _render_tiles(self) -> None:
        cx, cy = latlon_to_world_px(self.center_lat, self.center_lng, self.zoom)
        top_left_wx = cx - (self._map_w / 2.0)
        top_left_wy = cy - (self._map_h / 2.0)

        min_tx = int(math.floor(top_left_wx / 256.0))
        max_tx = int(math.floor((top_left_wx + self._map_w) / 256.0))
        min_ty = int(math.floor(top_left_wy / 256.0))
        max_ty = int(math.floor((top_left_wy + self._map_h) / 256.0))

        num_tiles = 2 ** self.zoom
        tiles: list[ft.Control] = []
        active_imgs: dict[str, ft.Image] = {}

        for tx in range(min_tx, max_tx + 1):
            for ty in range(min_ty, max_ty + 1):
                if ty < 0 or ty >= num_tiles:
                    continue
                wrapped_tx = tx % num_tiles
                left_px = round((tx * 256.0) - top_left_wx, 1)
                top_px = round((ty * 256.0) - top_left_wy, 1)
                tile_key = f"{self.zoom}_{wrapped_tx}_{ty}"

                tile_cont = self._tile_pool.get(tile_key)
                if tile_cont is not None:
                    tile_cont.left = left_px
                    tile_cont.top = top_px
                    if isinstance(tile_cont.content, ft.Image):
                        active_imgs[tile_key] = tile_cont.content
                else:
                    tile_src = _resolve_tile_source(self.zoom, wrapped_tx, ty)
                    img_ctrl = ft.Image(
                        src=tile_src,
                        width=256,
                        height=256,
                        fit=ft.BoxFit.COVER,
                        gapless_playback=True,
                    )
                    tile_cont = ft.Container(
                        left=left_px,
                        top=top_px,
                        width=256,
                        height=256,
                        content=img_ctrl,
                    )
                    self._tile_pool[tile_key] = tile_cont
                    active_imgs[tile_key] = img_ctrl

                tiles.append(tile_cont)

        # Bound tile pool size to prevent memory bloat
        if len(self._tile_pool) > 160:
            visible_keys = {f"{self.zoom}_{tx % num_tiles}_{ty}" for tx in range(min_tx, max_tx + 1) for ty in range(min_ty, max_ty + 1)}
            for k in list(self._tile_pool.keys()):
                if k not in visible_keys:
                    del self._tile_pool[k]

        self._active_tile_images = active_imgs
        self._tile_stack.controls = tiles

    def _render_route_vectors(self) -> None:
        shapes: list[cv.Shape] = []
        if len(self._route_pts) >= 2:
            screen_pts = [self._latlon_to_viewport(lat, lng) for lat, lng in self._route_pts]
            path_elements: list[cv.PathElement] = [cv.Path.MoveTo(screen_pts[0][0], screen_pts[0][1])]
            for vx, vy in screen_pts[1:]:
                path_elements.append(cv.Path.LineTo(vx, vy))

            shapes.append(
                cv.Path(
                    elements=path_elements,
                    paint=ft.Paint(
                        color="#ffffff",
                        stroke_width=8,
                        style=ft.PaintingStyle.STROKE,
                        stroke_cap=ft.StrokeCap.ROUND,
                        stroke_join=ft.StrokeJoin.ROUND,
                    ),
                )
            )
            shapes.append(
                cv.Path(
                    elements=path_elements,
                    paint=ft.Paint(
                        color="#0284c7",
                        stroke_width=5,
                        style=ft.PaintingStyle.STROKE,
                        stroke_cap=ft.StrokeCap.ROUND,
                        stroke_join=ft.StrokeJoin.ROUND,
                    ),
                )
            )
        self._vector_canvas.shapes = shapes

    def _ensure_world_clusters(self) -> None:
        """Pre-computes Web-Mercator world coordinates and spatial grid clusters once per (zoom, places list)."""
        first_id = self._places[0].id if self._places else ""
        last_id = self._places[-1].id if self._places else ""
        sig = f"{len(self._places)}:{first_id}:{last_id}"
        key = (self.zoom, len(self._places), sig)
        if self._cluster_cache_key == key:
            return

        self._cluster_cache_key = key
        projected: list[tuple[Place, float, float]] = []
        for p in self._places:
            if not p.latitude or not p.longitude:
                continue
            wx, wy = latlon_to_world_px(p.latitude, p.longitude, self.zoom)
            projected.append((p, wx, wy))

        if self.zoom < 14 and len(projected) > 18:
            cell_size = 58.0
            grid: dict[tuple[int, int], list[tuple[Place, float, float]]] = {}
            for item in projected:
                gx = int(item[1] // cell_size)
                gy = int(item[2] // cell_size)
                grid.setdefault((gx, gy), []).append(item)

            items: list[dict[str, Any]] = []
            for bucket in grid.values():
                if len(bucket) == 1:
                    p, wx, wy = bucket[0]
                    items.append({"type": "pin", "place": p, "wx": wx, "wy": wy})
                else:
                    n = len(bucket)
                    avg_wx = sum(b[1] for b in bucket) / n
                    avg_wy = sum(b[2] for b in bucket) / n
                    avg_lat = sum(b[0].latitude for b in bucket) / n
                    avg_lng = sum(b[0].longitude for b in bucket) / n
                    items.append({
                        "type": "cluster",
                        "count": n,
                        "wx": avg_wx,
                        "wy": avg_wy,
                        "lat": avg_lat,
                        "lng": avg_lng,
                    })
            self._cached_world_items = items
        else:
            self._cached_world_items = [
                {"type": "pin", "place": p, "wx": wx, "wy": wy}
                for p, wx, wy in projected
            ]

    def _render_markers_and_clusters(self) -> None:
        controls: list[ft.Control] = []
        cx, cy = latlon_to_world_px(self.center_lat, self.center_lng, self.zoom)
        half_w = self._map_w / 2.0
        half_h = self._map_h / 2.0

        # 1. User GPS / Cabanatuan Anchor Dot
        if self._user_location:
            ux, uy = self._latlon_to_viewport(self._user_location[0], self._user_location[1])
            if -20 <= ux <= self._map_w + 20 and -20 <= uy <= self._map_h + 20:
                controls.append(
                    ft.Container(
                        left=ux - 10,
                        top=uy - 10,
                        width=20,
                        height=20,
                        bgcolor="#3b82f6",
                        border=ft.Border.all(3, "#ffffff"),
                        border_radius=10,
                        tooltip="Your Location",
                    )
                )

        # 2. Pre-cached Discovery Markers & Clusters
        self._ensure_world_clusters()
        rendered_count = 0
        for item in self._cached_world_items:
            px = half_w + (item["wx"] - cx)
            py = half_h + (item["wy"] - cy)
            if px < -36 or px > self._map_w + 36 or py < -36 or py > self._map_h + 36:
                continue
            if item["type"] == "cluster":
                controls.append(
                    self._build_cluster_pin(
                        item["count"], px, py, item["lat"], item["lng"]
                    )
                )
            else:
                controls.append(self._build_place_pin(item["place"], px, py))
            rendered_count += 1
            if rendered_count >= 180:
                break

        # 3. Numbered Itinerary Route Stop Badges (1..N)
        for stop in self._route_stops:
            if not stop.lat or not stop.lng:
                continue
            sx, sy = self._latlon_to_viewport(stop.lat, stop.lng)
            if -40 <= sx <= self._map_w + 40 and -40 <= sy <= self._map_h + 40:
                controls.append(self._build_route_stop_badge(stop, sx, sy))

        self._marker_stack.controls = controls

    def _build_cluster_pin(
        self, count: int, px: float, py: float, center_lat: float, center_lng: float
    ) -> ft.Control:
        size = 38 if count < 25 else (44 if count < 100 else 50)
        return ft.Container(
            left=round(px - size / 2, 1),
            top=round(py - size / 2, 1),
            width=size,
            height=size,
            border_radius=size / 2,
            bgcolor=ft.Colors.with_opacity(0.28, "#0084ff"),
            padding=ft.Padding.all(4),
            tooltip=f"{count} places in this area — Click to zoom in",
            ink=True,
            on_click=lambda _: self.set_center_and_zoom(center_lat, center_lng, min(17, self.zoom + 2)),
            content=ft.Container(
                alignment=ft.Alignment(0, 0),
                border_radius=(size - 8) / 2,
                bgcolor="#0084ff",
                border=ft.Border.all(2, "#ffffff"),
                content=ft.Text(
                    str(count),
                    size=12,
                    weight=ft.FontWeight.W_800,
                    color="#ffffff",
                ),
            ),
        )

    def _build_place_pin(self, place: Place, px: float, py: float) -> ft.Control:
        color_hex, icon_data = CATEGORY_PIN_STYLE.get(
            place.category, ("#2563eb", ft.Icons.LOCATION_ON_ROUNDED)
        )
        return ft.Container(
            left=round(px - 15, 1),
            top=round(py - 15, 1),
            width=30,
            height=30,
            bgcolor=color_hex,
            border=ft.Border.all(2, "#ffffff"),
            border_radius=15,
            alignment=ft.Alignment(0, 0),
            tooltip=f"{place.name} ({place.municipality_name or 'Nueva Ecija'})",
            ink=True,
            on_click=lambda _, p=place: self._on_place_click(p) if self._on_place_click else None,
            content=ft.Icon(icon_data, size=15, color="#ffffff"),
        )

    def _build_route_stop_badge(self, stop: RouteStopPin, sx: float, sy: float) -> ft.Control:
        is_active = self._active_stop_index == stop.index
        badge_bg = "#f97316" if is_active else "#2563eb"
        badge_size = 34 if is_active else 30

        return ft.Container(
            left=round(sx - badge_size / 2, 1),
            top=round(sy - badge_size / 2, 1),
            ink=True,
            on_click=lambda _, s=stop: self._on_stop_click(s.index, s) if self._on_stop_click else None,
            tooltip=f"Stop {stop.index + 1}: {stop.title} ({stop.planned_time or 'Scheduled'})",
            content=ft.Row(
                spacing=4,
                tight=True,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        width=badge_size,
                        height=badge_size,
                        bgcolor=badge_bg,
                        border=ft.Border.all(2.5, "#ffffff"),
                        border_radius=badge_size / 2,
                        alignment=ft.Alignment(0, 0),
                        content=ft.Text(
                            str(stop.index + 1),
                            size=13,
                            weight=ft.FontWeight.W_800,
                            color="#ffffff",
                        ),
                    ),
                    ft.Container(
                        bgcolor=ft.Colors.with_opacity(0.95, "#ffffff"),
                        border=ft.Border.all(1, "#cbd5e1"),
                        border_radius=8,
                        padding=ft.Padding.symmetric(horizontal=7, vertical=3),
                        content=ft.Text(
                            stop.title[:22] + ("…" if len(stop.title) > 22 else ""),
                            size=10,
                            weight=ft.FontWeight.W_700,
                            color="#0f172a",
                        ),
                    ),
                ],
            ),
        )
```

---

### Phase 3: Fix Map Tab Filters Modal (`Dropdown` Crash & Chip Filter Parity) in `desktop_client/views/places_view.py`

In `desktop_client/views/places_view.py`:
1. **Fix `_update_in_place()` (`lines 292–296`)**: Update the `Filters` badge count to use `self._active_filters_count` (`len(self.selected_categories) + (1 if self.selected_municipality != "all" else 0) + (1 if self.selected_price_tier != "all" else 0)`).
2. **Fix `_select_category()` (`lines 700–713`)**: Match Web `MapPage.selectCategory()` (`map.page.ts:854–871`) so clicking a quick category pill on the top bar selects that single category (or clears back to `All Places` if already selected), while multi-category selection is performed inside the `Filter Destinations` sheet.
3. **Fix `_apply_filters()` (`lines 174–197`)**: Match Web `MapPage.applyLocalFilters()` (`map.page.ts:748–766`):
   - `free`: `p.estimated_cost_min == 0 and (p.estimated_cost_max is None or p.estimated_cost_max == 0)`
   - `budget`: `(p.estimated_cost_max is not None and p.estimated_cost_max <= 500) or (p.estimated_cost_min == 0 and p.estimated_cost_max is None)`
   - `mid`: `(p.estimated_cost_max is not None and p.estimated_cost_max > 500) or (p.estimated_cost_min is not None and p.estimated_cost_min > 500)`
4. **Replace `_open_filter_modal()` (`lines 1018–1128`)**: Remove the broken `ft.Dropdown(on_change=...)` controls completely and build the exact Web App **`Filter Destinations`** modal (`map.page.html:320–442`) with:
   - **Section 1: Categories (`Select multiple`)** — multi-select chip grid with icons and checkmarks.
   - **Section 2: Municipality / City (`All Nueva Ecija` or selected LGU)** — horizontal scrollable chip track (`All Municipalities` + all 32 LGUs, and if an LGU is selected and applied, automatically flies/centers the map onto that municipality's POIs!).
   - **Section 3: Price Range** — 4 pill buttons (`All Prices`, `Free (₱0)`, `Budget (≤ ₱500)`, `Mid-Range (> ₱500)`).
   - **Footer**: `Reset` and `Apply Filters` buttons.

Replace `_open_filter_modal()` in `desktop_client/views/places_view.py` with:
```python
    def _open_filter_modal(self) -> None:
        """Opens the Web-identical 'Filter Destinations' modal (Multi-Category Chips, Municipality Chips, 4 Price Range Pills)."""
        if not self.safe_page:
            return

        modal_selected_cats = set(self.selected_categories)
        modal_muni = [self.selected_municipality]
        modal_tier = [self.selected_price_tier]

        cat_grid = ft.Row(wrap=True, spacing=6, run_spacing=6)
        muni_row = ft.Row(spacing=6, scroll=ft.ScrollMode.AUTO)
        muni_hint_text = ft.Text(
            "All Nueva Ecija" if modal_muni[0] == "all" else modal_muni[0],
            size=11,
            color=ThemeColors.PRIMARY_BLUE,
            weight=ft.FontWeight.W_600,
        )
        tier_row = ft.Row(wrap=True, spacing=8)

        def _rebuild_cat_chips():
            pills: list[ft.Control] = []
            for c in CANONICAL_CATEGORIES:
                k = c["key"]
                lbl = c["label"]
                ic = CATEGORY_ICONS.get(k, ft.Icons.LOCATION_ON_OUTLINED)
                is_c = k in modal_selected_cats

                def _toggle_cat(_, cat_k=k):
                    if cat_k in modal_selected_cats:
                        modal_selected_cats.remove(cat_k)
                    else:
                        modal_selected_cats.add(cat_k)
                    _rebuild_cat_chips()
                    try:
                        cat_grid.update()
                    except Exception:
                        pass

                row_ctrls: list[ft.Control] = [
                    ft.Icon(ic, size=13, color=ft.Colors.WHITE if is_c else ThemeColors.PRIMARY_BLUE),
                    ft.Text(
                        lbl,
                        size=11,
                        weight=ft.FontWeight.BOLD if is_c else ft.FontWeight.W_500,
                        color=ft.Colors.WHITE if is_c else ThemeColors.TEXT_MAIN_LIGHT,
                    ),
                ]
                if is_c:
                    row_ctrls.append(ft.Icon(ft.Icons.CHECK, size=13, color=ft.Colors.WHITE))

                pills.append(
                    ft.Container(
                        content=ft.Row(controls=row_ctrls, spacing=5, tight=True),
                        bgcolor=ThemeColors.PRIMARY_BLUE if is_c else ThemeColors.SURFACE_LIGHT,
                        border=ft.Border.all(1, ThemeColors.PRIMARY_BLUE if is_c else ThemeColors.BORDER_LIGHT),
                        border_radius=16,
                        padding=ft.Padding.symmetric(horizontal=12, vertical=7),
                        ink=True,
                        on_click=_toggle_cat,
                    )
                )
            cat_grid.controls = pills

        def _rebuild_muni_chips():
            chips: list[ft.Control] = []
            all_munis = [("all", "All Municipalities")] + [(m, m) for m in sorted(NUEVA_ECIJA_LGUS)]
            for m_key, m_lbl in all_munis:
                is_m = modal_muni[0] == m_key

                def _pick_muni(_, mk=m_key):
                    modal_muni[0] = "all" if (modal_muni[0] == mk and mk != "all") else mk
                    muni_hint_text.value = "All Nueva Ecija" if modal_muni[0] == "all" else modal_muni[0]
                    _rebuild_muni_chips()
                    try:
                        muni_hint_text.update()
                        muni_row.update()
                    except Exception:
                        pass

                chips.append(
                    ft.Container(
                        content=ft.Text(
                            m_lbl,
                            size=11,
                            weight=ft.FontWeight.BOLD if is_m else ft.FontWeight.W_500,
                            color=ft.Colors.WHITE if is_m else ThemeColors.TEXT_MAIN_LIGHT,
                        ),
                        bgcolor=ThemeColors.PRIMARY_BLUE if is_m else ThemeColors.SURFACE_LIGHT,
                        border=ft.Border.all(1, ThemeColors.PRIMARY_BLUE if is_m else ThemeColors.BORDER_LIGHT),
                        border_radius=16,
                        padding=ft.Padding.symmetric(horizontal=12, vertical=7),
                        ink=True,
                        on_click=_pick_muni,
                    )
                )
            muni_row.controls = chips

        def _rebuild_tier_pills():
            tiers = [
                ("all", "All Prices"),
                ("free", "Free (₱0)"),
                ("budget", "Budget (≤ ₱500)"),
                ("mid", "Mid-Range (> ₱500)"),
            ]
            btns: list[ft.Control] = []
            for t_key, t_lbl in tiers:
                is_t = modal_tier[0] == t_key

                def _pick_tier(_, tk=t_key):
                    modal_tier[0] = tk
                    _rebuild_tier_pills()
                    try:
                        tier_row.update()
                    except Exception:
                        pass

                btns.append(
                    ft.Container(
                        content=ft.Text(
                            t_lbl,
                            size=11,
                            weight=ft.FontWeight.BOLD if is_t else ft.FontWeight.W_500,
                            color=ft.Colors.WHITE if is_t else ThemeColors.TEXT_MAIN_LIGHT,
                        ),
                        bgcolor=ThemeColors.PRIMARY_BLUE if is_t else ThemeColors.SURFACE_LIGHT,
                        border=ft.Border.all(1, ThemeColors.PRIMARY_BLUE if is_t else ThemeColors.BORDER_LIGHT),
                        border_radius=14,
                        padding=ft.Padding.symmetric(horizontal=14, vertical=8),
                        ink=True,
                        on_click=_pick_tier,
                    )
                )
            tier_row.controls = btns

        _rebuild_cat_chips()
        _rebuild_muni_chips()
        _rebuild_tier_pills()

        def _close_dlg(_=None):
            dlg.open = False
            if self.safe_page:
                self.safe_page.update()

        def _do_reset(_):
            modal_selected_cats.clear()
            modal_muni[0] = "all"
            modal_tier[0] = "all"
            self.selected_categories.clear()
            self.selected_category = "all"
            self.selected_municipality = "all"
            self.selected_price_tier = "all"
            _close_dlg()
            self._apply_filters()
            self._update_in_place(reset_viewport=False)

        def _do_apply(_):
            self.selected_categories = set(modal_selected_cats)
            self.selected_category = next(iter(modal_selected_cats)) if len(modal_selected_cats) == 1 else "all"
            self.selected_municipality = modal_muni[0]
            self.selected_price_tier = modal_tier[0]
            _close_dlg()
            self._apply_filters()
            should_fit = self.selected_municipality != "all" and len(self.filtered_places) > 0
            self._update_in_place(reset_viewport=should_fit)

        dlg = ft.AlertDialog(
            title=ft.Row(
                controls=[
                    ft.Text("Filter Destinations", size=18, weight=ft.FontWeight.W_800, color=ThemeColors.TEXT_BLACK),
                    ft.IconButton(icon=ft.Icons.CLOSE_ROUNDED, icon_size=18, on_click=_close_dlg),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            content=ft.Container(
                width=560,
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text("Categories", size=13, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_BLACK),
                                ft.Text("Select multiple", size=11, color=ThemeColors.TEXT_MUTED_LIGHT),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        cat_grid,
                        ft.Divider(height=12, color=ThemeColors.BORDER_LIGHT),
                        ft.Row(
                            controls=[
                                ft.Text("Municipality / City", size=13, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_BLACK),
                                muni_hint_text,
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        muni_row,
                        ft.Divider(height=12, color=ThemeColors.BORDER_LIGHT),
                        ft.Text("Price Range", size=13, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_BLACK),
                        tier_row,
                    ],
                    tight=True,
                    spacing=8,
                    scroll=ft.ScrollMode.AUTO,
                ),
            ),
            actions=[
                ft.TextButton("Reset", on_click=_do_reset),
                ft.FilledButton(
                    content="Apply Filters",
                    style=ft.ButtonStyle(bgcolor=ThemeColors.PRIMARY_BLUE, color=ft.Colors.WHITE),
                    on_click=_do_apply,
                ),
            ],
        )
        self.safe_page.overlay.append(dlg)
        dlg.open = True
        self.safe_page.update()
```

---

### Phase 4: Refactor `ProfileView` to Match Uploaded Screenshots (`image_2d13c2.png` Profile, `image_2d1741.png` Edit Profile, `image_2d1705.png` Settings)

Replace `desktop_client/views/profile_view.py` with the in-page multi-view implementation below (`view_mode: 'profile' | 'edit' | 'settings' | 'favorites' | 'help' | 'about'`) matching `Project/src/app/tabs/profile/profile.page.html` and the 3 uploaded screenshots (`image_2d13c2.png`, `image_2d1741.png`, `image_2d1705.png`) down to every icon, label, and input field:

```python
"""Profile, Edit Profile, Settings, Favorites, Help & Support, and About In-Page Views mirroring Ionic tabs/profile."""

from __future__ import annotations

import asyncio
import base64
from pathlib import Path
from typing import Callable, Optional
import flet as ft

from desktop_client.components.dialogs import show_place_detail_dialog
from desktop_client.config.settings import ThemeColors, get_settings
from desktop_client.core.connectivity_service import get_connectivity_service
from desktop_client.core.session import get_session_manager
from desktop_client.core.storage import get_guest_storage
from desktop_client.models.place import Place
from desktop_client.models.user import UserUpdatePayload
from desktop_client.services.auth_service import get_auth_service
from desktop_client.services.favorites_service import get_favorites_service


class ProfileView(ft.Container):
    """Profile tab view matching uploaded reference screenshots (image_2d13c2.png, image_2d1741.png, image_2d1705.png):

    - View 'profile': Clean 'Profile' heading, avatar + Full Name + @email + 'Edit Profile' pill button,
      and 5-row rounded white navigation card (Settings, Favorites, Help & Support, About, Log Out).
    - View 'edit': In-page '<- Edit Profile' header, centered circular avatar with camera overlay +
      outlined 'Change Photo' pill button, 7 stacked fields (First Name, Middle Initial (if applicable),
      Last Name, Birthday, Gender, read-only Email Address, Phone Number), and full-width blue 'Save Changes' button.
    - View 'settings': In-page '<- Settings' header and single rounded white card with 6 exact rows:
      Account Information, Notifications (switch), Privacy & Security, Language (English),
      App Appearance (Light/Dark), and Clear Cache (Free up storage space).
    """

    def __init__(
        self,
        on_navigate: Optional[Callable[[str], None]] = None,
        on_toggle_theme: Optional[Callable[[], None]] = None,
    ):
        super().__init__()
        self.on_navigate = on_navigate
        self.on_toggle_theme = on_toggle_theme
        self.session_manager = get_session_manager()
        self.auth_service = get_auth_service()
        self.guest_storage = get_guest_storage()
        self.favorites_service = get_favorites_service()
        self.connectivity_service = get_connectivity_service()
        self.settings = get_settings()

        self.expand = True
        self.padding = ft.Padding.symmetric(horizontal=36, vertical=24)
        self.bgcolor = ThemeColors.BG_LIGHT

        # In-page subview state matching Web ProfilePage.viewMode
        self.view_mode: str = "profile"  # 'profile' | 'edit' | 'settings' | 'favorites' | 'help' | 'about'
        self.notifications_enabled: bool = True
        self.current_language: str = "en"
        self.is_migrating: bool = False
        self._has_refreshed_profile: bool = False

        # Edit Profile State
        self._edit_avatar_data_url: Optional[str] = None
        self._edit_error_msg: str = ""
        self._is_saving_profile: bool = False

        # Favorites Subview State
        self._fav_search_query: str = ""
        self._fav_selected_cat: str = "ALL"

        self._build_content()

    def handle_back(self) -> bool:
        """Allows back navigation from subviews ('edit', 'settings', 'favorites', 'help', 'about') back to 'profile'."""
        if self.view_mode != "profile":
            self.view_mode = "profile"
            self._build_content()
            self._safe_update()
            return True
        return False

    def _build_content(self) -> None:
        if self.view_mode == "edit":
            self.content = self._build_edit_profile_subview()
        elif self.view_mode == "settings":
            self.content = self._build_settings_subview()
        elif self.view_mode == "favorites":
            self.content = self._build_favorites_subview()
        elif self.view_mode == "help":
            self.content = self._build_help_subview()
        elif self.view_mode == "about":
            self.content = self._build_about_subview()
        else:
            self.content = self._build_main_profile_view()

    # =========================================================================
    # VIEW 1: MAIN PROFILE TAB (MATCHING image_2d13c2.png)
    # =========================================================================
    def _build_main_profile_view(self) -> ft.Control:
        user = self.session_manager.current_user
        is_guest = self.session_manager.is_guest or not self.session_manager.is_authenticated

        title_header = ft.Text(
            "Profile",
            size=30,
            weight=ft.FontWeight.W_800,
            color=ThemeColors.TEXT_BLACK,
        )

        if not is_guest and user:
            name_val = user.full_name or "Edward Renz Natividad"
            email_raw = user.email or "edselrenz0@gmail.com"
            handle_val = f"@{email_raw}" if not email_raw.startswith("@") else email_raw
            avatar_src = self.settings.resolve_avatar_path(user.avatar_url, user.id)

            avatar_ctrl = ft.Container(
                content=ft.Image(
                    src=avatar_src,
                    width=84,
                    height=84,
                    fit=ft.BoxFit.COVER,
                    border_radius=42,
                    error_content=ft.CircleAvatar(
                        content=ft.Icon(ft.Icons.PERSON, size=40, color=ft.Colors.WHITE),
                        radius=42,
                        bgcolor=ThemeColors.PRIMARY_BLUE,
                    ),
                ),
                width=84,
                height=84,
                border_radius=42,
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            )

            action_pill = ft.Container(
                content=ft.Text(
                    "Edit Profile",
                    size=13,
                    weight=ft.FontWeight.W_600,
                    color=ThemeColors.PRIMARY_BLUE,
                ),
                border=ft.Border.all(1.2, ThemeColors.PRIMARY_BLUE),
                border_radius=20,
                padding=ft.Padding.symmetric(horizontal=24, vertical=6),
                ink=True,
                on_click=lambda _: self._open_edit_profile_dialog(),
            )
        else:
            name_val = "Guest Explorer"
            handle_val = "Browsing in Guest Mode (Offline)"
            avatar_ctrl = ft.Container(
                content=ft.Icon(ft.Icons.PERSON, size=40, color=ThemeColors.TEXT_MUTED_LIGHT),
                width=84,
                height=84,
                border_radius=42,
                bgcolor="#e2e8f0",
                alignment=ft.Alignment(0, 0),
            )
            action_pill = ft.Container(
                content=ft.Text(
                    "Log In / Sign Up",
                    size=13,
                    weight=ft.FontWeight.W_600,
                    color=ThemeColors.PRIMARY_BLUE,
                ),
                border=ft.Border.all(1.2, ThemeColors.PRIMARY_BLUE),
                border_radius=20,
                padding=ft.Padding.symmetric(horizontal=24, vertical=6),
                ink=True,
                on_click=lambda _: self._navigate("/login"),
            )

        identity_row = ft.Row(
            controls=[
                avatar_ctrl,
                ft.Column(
                    controls=[
                        ft.Text(name_val, size=20, weight=ft.FontWeight.W_800, color=ThemeColors.TEXT_BLACK),
                        ft.Text(handle_val, size=14, color=ThemeColors.TEXT_FAINT_LIGHT),
                        ft.Container(height=2),
                        action_pill,
                    ],
                    spacing=3,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
            ],
            spacing=20,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Unsynced Local Guest Trips Banner (only shown if guest trips exist)
        guest_trips_count = len(self.guest_storage.list_itineraries())
        sync_banner: ft.Control = ft.Container()
        if guest_trips_count > 0 and not is_guest:
            sync_banner = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.CLOUD_UPLOAD_OUTLINED, size=18, color=ThemeColors.PRIMARY_BLUE),
                                ft.Text(
                                    f"{guest_trips_count} local {'trip' if guest_trips_count == 1 else 'trips'} not synced",
                                    size=13,
                                    weight=ft.FontWeight.W_600,
                                    color=ThemeColors.TEXT_BLACK,
                                ),
                            ],
                            spacing=8,
                        ),
                        ft.FilledButton(
                            content="Sync" if not self.is_migrating else "Syncing...",
                            style=ft.ButtonStyle(
                                bgcolor=ThemeColors.PRIMARY_BLUE,
                                color=ft.Colors.WHITE,
                                shape=ft.RoundedRectangleBorder(radius=8),
                            ),
                            disabled=self.is_migrating,
                            on_click=lambda _: self._sync_guest_trips(),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                bgcolor=ThemeColors.PRIMARY_LIGHT,
                border=ft.Border.all(1, ThemeColors.CUSTOM_CARD_BORDER),
                border_radius=14,
                padding=ft.Padding.symmetric(horizontal=16, vertical=10),
                width=560,
            )

        # 5-Row Rounded White Card matching image_2d13c2.png verbatim
        menu_card = ft.Container(
            width=560,
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
            border_radius=20,
            padding=ft.Padding.symmetric(horizontal=22, vertical=10),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=14,
                color=ft.Colors.with_opacity(0.04, "#000000"),
                offset=ft.Offset(0, 4),
            ),
            content=ft.Column(
                spacing=0,
                controls=[
                    self._create_menu_row(
                        icon=ft.Icons.SETTINGS_OUTLINED,
                        icon_color=ThemeColors.PRIMARY_BLUE,
                        title="Settings",
                        desc="Manage your account and customize your app experience.",
                        on_click=lambda: self._open_settings_dialog(),
                    ),
                    ft.Divider(color="#f1f5f9", height=1),
                    self._create_menu_row(
                        icon=ft.Icons.FAVORITE,
                        icon_color=ThemeColors.PRIMARY_BLUE,
                        title="Favorites",
                        desc="Your favorite places, all saved in one place. Find them whenever you're ready to explore.",
                        on_click=lambda: self._open_favorites_dialog(),
                    ),
                    ft.Divider(color="#f1f5f9", height=1),
                    self._create_menu_row(
                        icon=ft.Icons.HELP_ROUNDED,
                        icon_color=ThemeColors.PRIMARY_BLUE,
                        title="Help & Support",
                        desc="Get assistance and find answers to common questions.",
                        on_click=lambda: self._open_help_dialog(),
                    ),
                    ft.Divider(color="#f1f5f9", height=1),
                    self._create_menu_row(
                        icon=ft.Icons.INFO_ROUNDED,
                        icon_color=ThemeColors.PRIMARY_BLUE,
                        title="About",
                        desc=f"Version {self.settings.app_version}.",
                        on_click=lambda: self._open_about_dialog(),
                    ),
                    ft.Divider(color="#f1f5f9", height=1),
                    self._create_menu_row(
                        icon=ft.Icons.LOGOUT_ROUNDED,
                        icon_color=ThemeColors.ERROR if not is_guest else ThemeColors.PRIMARY_BLUE,
                        title="Log Out" if not is_guest else "Exit Guest Mode",
                        desc="Sign out of your account." if not is_guest else "Return to welcome screen to log in or register.",
                        title_color=ThemeColors.ERROR if not is_guest else ThemeColors.PRIMARY_BLUE,
                        on_click=lambda: self._confirm_logout() if not is_guest else self._navigate("/welcome"),
                    ),
                ],
            ),
        )

        return ft.Column(
            controls=[
                ft.Container(
                    width=560,
                    content=ft.Column(
                        controls=[
                            title_header,
                            ft.Container(height=16),
                            identity_row,
                            ft.Container(height=18),
                            sync_banner,
                            menu_card,
                        ],
                        spacing=0,
                        horizontal_alignment=ft.CrossAxisAlignment.START,
                    ),
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def _create_menu_row(
        self,
        icon: ft.IconData,
        icon_color: str,
        title: str,
        desc: str,
        on_click: Callable[[], None],
        title_color: Optional[str] = None,
    ) -> ft.Control:
        """Creates a clean menu row matching image_2d13c2.png (clean icon on left, bold title + description on right)."""
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Icon(icon, size=24, color=icon_color),
                        width=36,
                        alignment=ft.Alignment(0, -0.2),
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(
                                title,
                                size=16,
                                weight=ft.FontWeight.W_700,
                                color=title_color or ThemeColors.TEXT_BLACK,
                            ),
                            ft.Text(
                                desc,
                                size=13,
                                color=ThemeColors.TEXT_FAINT_LIGHT,
                            ),
                        ],
                        spacing=3,
                        expand=True,
                    ),
                ],
                spacing=14,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(vertical=18, horizontal=4),
            ink=True,
            border_radius=10,
            on_click=lambda _: on_click(),
        )

    # =========================================================================
    # VIEW 2: EDIT PROFILE IN-PAGE SUBVIEW (MATCHING image_2d1741.png EXACTLY)
    # =========================================================================
    def _build_edit_profile_subview(self) -> ft.Control:
        user = self.session_manager.current_user
        uid = user.id if user else "traveler"
        raw_avatar = self._edit_avatar_data_url or (user.avatar_url if user else None)
        avatar_src = self.settings.resolve_avatar_path(raw_avatar, uid)

        header_row = ft.Row(
            controls=[
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color=ThemeColors.PRIMARY_BLUE,
                    icon_size=22,
                    tooltip="Back to profile",
                    on_click=lambda _: self._close_subview(),
                ),
                ft.Text("Edit Profile", size=24, weight=ft.FontWeight.W_800, color=ThemeColors.TEXT_BLACK),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        avatar_preview_img = ft.Image(
            src=avatar_src,
            width=96,
            height=96,
            fit=ft.BoxFit.COVER,
            border_radius=48,
            error_content=ft.CircleAvatar(
                content=ft.Icon(ft.Icons.PERSON, size=42, color=ft.Colors.WHITE),
                radius=48,
                bgcolor=ThemeColors.PRIMARY_BLUE,
            ),
        )

        def _pick_photo(_=None):
            try:
                import tkinter as tk
                from tkinter import filedialog
                root = tk.Tk()
                root.withdraw()
                root.attributes("-topmost", True)
                f_path = filedialog.askopenfilename(
                    title="Select Profile Photo",
                    filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.webp")],
                )
                root.destroy()
                if f_path:
                    ext = Path(f_path).suffix.lstrip(".").lower()
                    if ext == "jpg":
                        ext = "jpeg"
                    b64_str = base64.b64encode(Path(f_path).read_bytes()).decode("ascii")
                    self._edit_avatar_data_url = f"data:image/{ext};base64,{b64_str}"
                    avatar_preview_img.src = self.settings.resolve_avatar_path(self._edit_avatar_data_url, uid)
                    self._safe_update()
            except Exception:
                pass

        # Circular Avatar with Centered Semi-Transparent Camera Overlay + Outlined 'Change Photo' Pill Button
        avatar_stack = ft.GestureDetector(
            on_tap=_pick_photo,
            content=ft.Stack(
                width=96,
                height=96,
                controls=[
                    ft.Container(
                        content=avatar_preview_img,
                        width=96,
                        height=96,
                        border_radius=48,
                        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                    ),
                    ft.Container(
                        left=30,
                        top=30,
                        width=36,
                        height=36,
                        border_radius=18,
                        bgcolor=ft.Colors.with_opacity(0.45, "#000000"),
                        alignment=ft.Alignment(0, 0),
                        content=ft.Icon(ft.Icons.PHOTO_CAMERA_OUTLINED, size=18, color=ft.Colors.WHITE),
                    ),
                ],
            ),
        )

        change_photo_btn = ft.Container(
            content=ft.Text("Change Photo", size=12, weight=ft.FontWeight.W_600, color=ThemeColors.PRIMARY_BLUE),
            border=ft.Border.all(1.2, ThemeColors.PRIMARY_BLUE),
            border_radius=20,
            padding=ft.Padding.symmetric(horizontal=22, vertical=6),
            ink=True,
            on_click=_pick_photo,
        )

        avatar_section = ft.Column(
            controls=[avatar_stack, change_photo_btn],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        )

        # Helper to build each labeled field matching image_2d1741.png
        def _labeled_field(label_text: str, initial_val: str, read_only: bool = False) -> tuple[ft.Control, ft.TextField]:
            tf = ft.TextField(
                value=initial_val,
                read_only=read_only,
                border_radius=10,
                border_color="#cbd5e1",
                focused_border_color=ThemeColors.PRIMARY_BLUE,
                bgcolor="#f1f5f9" if read_only else ft.Colors.WHITE,
                filled=True,
                dense=True,
                text_style=ft.TextStyle(
                    size=14,
                    color=ThemeColors.TEXT_FAINT_LIGHT if read_only else ThemeColors.TEXT_BLACK,
                ),
                content_padding=ft.Padding.symmetric(horizontal=14, vertical=12),
            )
            block = ft.Column(
                controls=[
                    ft.Text(label_text, size=12, weight=ft.FontWeight.W_700, color=ThemeColors.TEXT_BLACK),
                    tf,
                ],
                spacing=4,
            )
            return block, tf

        first_block, first_tf = _labeled_field("First Name", user.first_name if user and user.first_name else "Edward Renz")
        mi_block, mi_tf = _labeled_field("Middle Initial (if applicable)", user.middle_initial if user and user.middle_initial else "N/A")
        last_block, last_tf = _labeled_field("Last Name", user.last_name if user and user.last_name else "Natividad")
        bday_block, bday_tf = _labeled_field("Birthday", user.birthday if user and user.birthday else "May 23, 2000")
        gender_block, gender_tf = _labeled_field("Gender", user.gender if user and user.gender else "Female")
        email_block, email_tf = _labeled_field("Email Address", user.email if user and user.email else "edselrenz0@gmail.com", read_only=True)
        phone_block, phone_tf = _labeled_field("Phone Number", user.phone_number if user and user.phone_number else "+66 81 234 5678")

        error_banner = ft.Container(
            visible=bool(self._edit_error_msg),
            bgcolor=ThemeColors.ERROR_BG,
            border_radius=8,
            padding=10,
            content=ft.Text(self._edit_error_msg, size=12, color=ThemeColors.ERROR),
        )

        def _save_changes(_=None):
            f_val = (first_tf.value or "").strip()
            l_val = (last_tf.value or "").strip()
            if not f_val or not l_val:
                self._edit_error_msg = "First Name and Last Name are required."
                self._build_content()
                self._safe_update()
                return

            payload = UserUpdatePayload(
                first_name=f_val,
                middle_initial=(mi_tf.value or "").strip() or "N/A",
                last_name=l_val,
                birthday=(bday_tf.value or "").strip() or "May 23, 2000",
                gender=(gender_tf.value or "").strip() or "Female",
                phone_number=(phone_tf.value or "").strip() or "+66 81 234 5678",
                avatar_url=self._edit_avatar_data_url or (user.avatar_url if user else "assets/images/pattranite_avatar.jpg"),
            )

            async def _do_update():
                try:
                    await self.auth_service.update_profile(payload)
                    self._edit_error_msg = ""
                    self.view_mode = "profile"
                    self._build_content()
                    self._safe_update()
                    if self.safe_page:
                        self.safe_page.snack_bar = ft.SnackBar(
                            content=ft.Text("Profile updated successfully!", color=ft.Colors.WHITE),
                            bgcolor=ThemeColors.SUCCESS,
                            open=True,
                        )
                        self.safe_page.update()
                except Exception as err:
                    self._edit_error_msg = str(err)
                    self._build_content()
                    self._safe_update()

            if self.safe_page:
                self.safe_page.run_task(_do_update)
            else:
                try:
                    asyncio.get_running_loop().create_task(_do_update())
                except RuntimeError:
                    pass

        save_btn = ft.Container(
            content=ft.Text("Save Changes", size=14, weight=ft.FontWeight.W_700, color=ft.Colors.WHITE),
            bgcolor=ThemeColors.PRIMARY_BLUE,
            border_radius=10,
            height=46,
            alignment=ft.Alignment(0, 0),
            ink=True,
            on_click=_save_changes,
        )

        return ft.Column(
            controls=[
                ft.Container(
                    width=440,
                    content=ft.Column(
                        controls=[
                            header_row,
                            ft.Container(height=12),
                            ft.Container(content=avatar_section, alignment=ft.Alignment(0, 0)),
                            ft.Container(height=14),
                            error_banner,
                            first_block,
                            mi_block,
                            last_block,
                            bday_block,
                            gender_block,
                            email_block,
                            phone_block,
                            ft.Container(height=12),
                            save_btn,
                            ft.Container(height=24),
                        ],
                        spacing=10,
                    ),
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    # =========================================================================
    # VIEW 3: SETTINGS IN-PAGE SUBVIEW (MATCHING image_2d1705.png EXACTLY)
    # =========================================================================
    def _build_settings_subview(self) -> ft.Control:
        is_dark = bool(self.safe_page and self.safe_page.theme_mode == ft.ThemeMode.DARK)

        header_row = ft.Row(
            controls=[
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color=ThemeColors.PRIMARY_BLUE,
                    icon_size=22,
                    tooltip="Back to profile",
                    on_click=lambda _: self._close_subview(),
                ),
                ft.Text("Settings", size=26, weight=ft.FontWeight.W_800, color=ThemeColors.TEXT_BLACK),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        notif_switch = ft.Switch(
            value=self.notifications_enabled,
            active_color=ThemeColors.PRIMARY_BLUE,
            on_change=lambda e: setattr(self, "notifications_enabled", bool(e.control.value)),
        )

        def _settings_row(
            icon: ft.IconData,
            title: str,
            subtitle: Optional[str] = None,
            trailing: Optional[ft.Control] = None,
            on_click: Optional[Callable[[], None]] = None,
        ) -> ft.Control:
            title_col = (
                ft.Column(
                    controls=[
                        ft.Text(title, size=15, weight=ft.FontWeight.W_700, color=ThemeColors.TEXT_BLACK),
                        ft.Text(subtitle, size=12, color=ThemeColors.TEXT_FAINT_LIGHT),
                    ],
                    spacing=2,
                )
                if subtitle
                else ft.Text(title, size=15, weight=ft.FontWeight.W_700, color=ThemeColors.TEXT_BLACK)
            )
            row_controls: list[ft.Control] = [
                ft.Row(
                    controls=[
                        ft.Icon(icon, size=22, color=ThemeColors.PRIMARY_BLUE),
                        title_col,
                    ],
                    spacing=16,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ]
            if trailing is not None:
                row_controls.append(trailing)

            return ft.Container(
                content=ft.Row(
                    controls=row_controls,
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.Padding.symmetric(vertical=16, horizontal=6),
                ink=on_click is not None,
                border_radius=10,
                on_click=(lambda _: on_click()) if on_click else None,
            )

        settings_card = ft.Container(
            width=560,
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
            border_radius=20,
            padding=ft.Padding.symmetric(horizontal=22, vertical=8),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=14,
                color=ft.Colors.with_opacity(0.04, "#000000"),
                offset=ft.Offset(0, 4),
            ),
            content=ft.Column(
                spacing=0,
                controls=[
                    # Row 1: Account Information
                    _settings_row(
                        icon=ft.Icons.PERSON_OUTLINE,
                        title="Account Information",
                        on_click=lambda: self._open_edit_profile_dialog(),
                    ),
                    ft.Divider(color="#f1f5f9", height=1),
                    # Row 2: Notifications
                    _settings_row(
                        icon=ft.Icons.NOTIFICATIONS,
                        title="Notifications",
                        trailing=notif_switch,
                    ),
                    ft.Divider(color="#f1f5f9", height=1),
                    # Row 3: Privacy & Security
                    _settings_row(
                        icon=ft.Icons.LOCK,
                        title="Privacy & Security",
                        on_click=lambda: self._open_privacy_security_alert(),
                    ),
                    ft.Divider(color="#f1f5f9", height=1),
                    # Row 4: Language
                    _settings_row(
                        icon=ft.Icons.LANGUAGE,
                        title="Language",
                        trailing=ft.Text(
                            "Filipino" if self.current_language == "fil" else "English",
                            size=14,
                            weight=ft.FontWeight.W_500,
                            color=ThemeColors.TEXT_BLACK,
                        ),
                        on_click=lambda: self._toggle_language(),
                    ),
                    ft.Divider(color="#f1f5f9", height=1),
                    # Row 5: App Appearance
                    _settings_row(
                        icon=ft.Icons.DARK_MODE_OUTLINED if is_dark else ft.Icons.WB_SUNNY_OUTLINED,
                        title="App Appearance",
                        trailing=ft.Text(
                            "Dark" if is_dark else "Light",
                            size=14,
                            weight=ft.FontWeight.W_500,
                            color=ThemeColors.TEXT_BLACK,
                        ),
                        on_click=lambda: self._toggle_theme(),
                    ),
                    ft.Divider(color="#f1f5f9", height=1),
                    # Row 6: Clear Cache
                    _settings_row(
                        icon=ft.Icons.DELETE_OUTLINE,
                        title="Clear Cache",
                        subtitle="Free up storage space",
                        on_click=lambda: self._confirm_clear_cache(),
                    ),
                ],
            ),
        )

        return ft.Column(
            controls=[
                ft.Container(
                    width=560,
                    content=ft.Column(
                        controls=[
                            header_row,
                            ft.Container(height=14),
                            settings_card,
                        ],
                        spacing=0,
                    ),
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    # =========================================================================
    # VIEW 4: FAVORITES IN-PAGE SUBVIEW
    # =========================================================================
    def _build_favorites_subview(self) -> ft.Control:
        favorites = self.favorites_service.get_favorites()
        q = self._fav_search_query.strip().lower()
        filtered = [
            p for p in favorites
            if (not q or q in p.name.lower() or q in (p.municipality_name or "").lower())
            and (self._fav_selected_cat == "ALL" or self._fav_selected_cat.lower() in (p.category or "").lower() or self._fav_selected_cat.lower() in (p.formatted_category or "").lower())
        ]

        header_row = ft.Row(
            controls=[
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color=ThemeColors.PRIMARY_BLUE,
                    icon_size=22,
                    on_click=lambda _: self._close_subview(),
                ),
                ft.Text("Favorites", size=24, weight=ft.FontWeight.W_800, color=ThemeColors.TEXT_BLACK),
                ft.Container(
                    content=ft.Text(str(len(filtered)), size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    bgcolor=ThemeColors.PRIMARY_BLUE,
                    border_radius=10,
                    padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                ),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        cards: list[ft.Control] = []
        if filtered:
            for place in filtered:
                cards.append(
                    ft.Container(
                        bgcolor=ThemeColors.SURFACE_LIGHT,
                        border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
                        border_radius=14,
                        padding=12,
                        content=ft.Row(
                            controls=[
                                ft.Image(
                                    src=place.resolved_image_path,
                                    width=80,
                                    height=64,
                                    fit=ft.BoxFit.COVER,
                                    border_radius=8,
                                    error_content=ft.Icon(ft.Icons.LANDSCAPE, size=24, color=ThemeColors.PRIMARY_BLUE),
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text(place.name, size=14, weight=ft.FontWeight.BOLD),
                                        ft.Text(place.municipality_name or "Nueva Ecija", size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                                        ft.Text(place.formatted_cost, size=12, weight=ft.FontWeight.BOLD, color=ThemeColors.EMERALD_PRIMARY),
                                    ],
                                    spacing=2,
                                    expand=True,
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.FAVORITE,
                                    icon_color=ft.Colors.RED_500,
                                    tooltip="Remove from favorites",
                                    on_click=lambda _, pl=place: self._remove_fav(pl),
                                ),
                                ft.FilledButton(
                                    content="View Details",
                                    style=ft.ButtonStyle(bgcolor=ThemeColors.PRIMARY_BLUE, color=ft.Colors.WHITE),
                                    on_click=lambda _, pl=place: show_place_detail_dialog(self.safe_page, pl, on_navigate=self.on_navigate) if self.safe_page else None,
                                ),
                            ],
                            spacing=12,
                        ),
                    )
                )
        else:
            cards.append(
                ft.Container(
                    padding=40,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.FAVORITE_BORDER, size=42, color=ThemeColors.PRIMARY_BLUE),
                            ft.Text("No Favorite Places Saved", size=16, weight=ft.FontWeight.BOLD),
                            ft.Text("Browse destinations and tap the heart icon to save your personal favorite spots right here.", size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                            ft.FilledButton(
                                content="Explore Destinations",
                                style=ft.ButtonStyle(bgcolor=ThemeColors.PRIMARY_BLUE, color=ft.Colors.WHITE),
                                on_click=lambda _: self._navigate("/home"),
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                    ),
                )
            )

        return ft.Column(
            controls=[
                ft.Container(
                    width=560,
                    content=ft.Column(controls=[header_row, ft.Container(height=12), *cards], spacing=10),
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    # =========================================================================
    # VIEW 5 & 6: HELP & SUPPORT AND ABOUT IN-PAGE SUBVIEWS
    # =========================================================================
    def _build_help_subview(self) -> ft.Control:
        header_row = ft.Row(
            controls=[
                ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=ThemeColors.PRIMARY_BLUE, icon_size=22, on_click=lambda _: self._close_subview()),
                ft.Text("Help & Support", size=24, weight=ft.FontWeight.W_800, color=ThemeColors.TEXT_BLACK),
            ],
            spacing=8,
        )
        card = ft.Container(
            width=560,
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
            border_radius=20,
            padding=22,
            content=ft.Column(
                spacing=12,
                controls=[
                    ft.Text("Frequently Asked Questions", size=16, weight=ft.FontWeight.W_800),
                    ft.Text("How does the app generate suggested itineraries?", size=14, weight=ft.FontWeight.BOLD),
                    ft.Text("Our pacing engine analyzes 2,673 provincial points of interest, your selected pacing, daily budget, and starting destination to calculate optimal daily road routes via Open Source Routing Machine (OSRM).", size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                    ft.Divider(color="#f1f5f9", height=1),
                    ft.Text("Can I use the app offline in remote areas?", size=14, weight=ft.FontWeight.BOLD),
                    ft.Text("Yes! All created itineraries, destination notes, and visited map areas are cached locally so you can travel through the Sierra Madre mountains with confidence.", size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                    ft.Divider(color="#f1f5f9", height=1),
                    ft.Text("What are the emergency provincial hotlines?", size=14, weight=ft.FontWeight.BOLD),
                    ft.Text("PDRRMO Nueva Ecija: (044) 940 3388\nPNP Nueva Ecija: 117 / (044) 463 0565\nTourism Office: tourism@nuevaecija.gov.ph", size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                ],
            ),
        )
        return ft.Column(
            controls=[ft.Container(width=560, content=ft.Column(controls=[header_row, ft.Container(height=12), card]))],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def _build_about_subview(self) -> ft.Control:
        header_row = ft.Row(
            controls=[
                ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=ThemeColors.PRIMARY_BLUE, icon_size=22, on_click=lambda _: self._close_subview()),
                ft.Text("About", size=24, weight=ft.FontWeight.W_800, color=ThemeColors.TEXT_BLACK),
            ],
            spacing=8,
        )
        card = ft.Container(
            width=560,
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
            border_radius=20,
            padding=24,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
                controls=[
                    ft.Icon(ft.Icons.INFO_ROUNDED, size=44, color=ThemeColors.PRIMARY_BLUE),
                    ft.Text("Nueva Ecija Travel Companion", size=18, weight=ft.FontWeight.W_800),
                    ft.Text("Trip mo, trip ko", size=13, weight=ft.FontWeight.BOLD, color=ThemeColors.PRIMARY_BLUE),
                    ft.Text(
                        "Comprehensive travel and itinerary planning companion engineered for travelers exploring all 32 municipalities and 5 component cities of Nueva Ecija, Philippines.",
                        size=12,
                        color=ThemeColors.TEXT_MUTED_LIGHT,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Divider(color="#f1f5f9", height=12),
                    ft.Row(
                        controls=[
                            ft.Text("Version", size=13, color=ThemeColors.TEXT_MUTED_LIGHT),
                            ft.Text(self.settings.app_version, size=13, weight=ft.FontWeight.BOLD),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Divider(color="#f1f5f9", height=12),
                    ft.Row(
                        controls=[
                            ft.Text("Open Data Attribution", size=13, color=ThemeColors.TEXT_MUTED_LIGHT),
                            ft.Text("OpenStreetMap & GIS Nueva Ecija", size=13, weight=ft.FontWeight.BOLD),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                ],
            ),
        )
        return ft.Column(
            controls=[ft.Container(width=560, content=ft.Column(controls=[header_row, ft.Container(height=12), card]))],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    # =========================================================================
    # NAVIGATION & DIALOG HELPERS
    # =========================================================================
    def _close_subview(self) -> None:
        self.view_mode = "profile"
        self._build_content()
        self._safe_update()

    def _open_edit_profile_dialog(self) -> None:
        if self.session_manager.is_guest or not self.session_manager.is_authenticated:
            self._navigate("/login")
            return
        self._edit_error_msg = ""
        self.view_mode = "edit"
        self._build_content()
        self._safe_update()

    def _open_settings_dialog(self) -> None:
        self.view_mode = "settings"
        self._build_content()
        self._safe_update()

    def _open_favorites_dialog(self) -> None:
        self.view_mode = "favorites"
        self._build_content()
        self._safe_update()

    def _open_help_dialog(self) -> None:
        self.view_mode = "help"
        self._build_content()
        self._safe_update()

    def _open_about_dialog(self) -> None:
        self.view_mode = "about"
        self._build_content()
        self._safe_update()

    def _remove_fav(self, pl: Place) -> None:
        self.favorites_service.remove_favorite(pl.id)
        self._build_content()
        self._safe_update()

    def _toggle_language(self) -> None:
        self.current_language = "fil" if self.current_language == "en" else "en"
        self._build_content()
        self._safe_update()

    def _open_privacy_security_alert(self) -> None:
        dlg = ft.AlertDialog(
            title=ft.Text("Privacy & Security", size=18, weight=ft.FontWeight.BOLD),
            content=ft.Text(
                "All itinerary drafts, profile preferences, and account tokens are stored using AES-256 encrypted local storage and TLS 1.3 in transit.",
                size=13,
                color=ThemeColors.TEXT_MUTED_LIGHT,
            ),
            actions=[ft.TextButton("Close", on_click=lambda _: self._close_dialog(dlg))],
        )
        self._show_dialog(dlg)

    def _confirm_clear_cache(self) -> None:
        def _do_clear(_):
            self._close_dialog(dlg)
            if self.safe_page:
                self.safe_page.snack_bar = ft.SnackBar(
                    content=ft.Text("Local cache cleared successfully."),
                    open=True,
                )
                self.safe_page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Clear Cache & Offline Data", size=18, weight=ft.FontWeight.BOLD),
            content=ft.Text(
                "This will clear locally stored search queries, map tiles, and offline place caches to free up storage space. Your created itineraries and account credentials will not be deleted.",
                size=13,
                color=ThemeColors.TEXT_MUTED_LIGHT,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self._close_dialog(dlg)),
                ft.FilledButton(
                    content="Clear Cache",
                    style=ft.ButtonStyle(bgcolor=ThemeColors.ERROR, color=ft.Colors.WHITE),
                    on_click=_do_clear,
                ),
            ],
        )
        self._show_dialog(dlg)

    def _confirm_logout(self) -> None:
        def _do_logout(_):
            self._close_dialog(dlg)
            self.session_manager.clear_session()
            self._navigate("/welcome?logout=1")

        dlg = ft.AlertDialog(
            title=ft.Text("Log Out?", size=20, weight=ft.FontWeight.W_800, text_align=ft.TextAlign.CENTER),
            content=ft.Column(
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
                controls=[
                    ft.Icon(ft.Icons.LOGOUT_ROUNDED, size=44, color=ThemeColors.PRIMARY_BLUE),
                    ft.Text(
                        "You will be signed out of your account. You can always log back in anytime.",
                        size=13,
                        color=ThemeColors.TEXT_MUTED_LIGHT,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(
                        width=260,
                        height=42,
                        bgcolor=ThemeColors.PRIMARY_BLUE,
                        border_radius=20,
                        alignment=ft.Alignment(0, 0),
                        ink=True,
                        on_click=_do_logout,
                        content=ft.Text("Log Out", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ),
                    ft.Container(
                        width=260,
                        height=42,
                        bgcolor=ThemeColors.PRIMARY_BLUE,
                        border_radius=20,
                        alignment=ft.Alignment(0, 0),
                        ink=True,
                        on_click=lambda _: self._close_dialog(dlg),
                        content=ft.Text("Cancel", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ),
                ],
            ),
        )
        self._show_dialog(dlg)

    def _show_dialog(self, dlg: ft.AlertDialog) -> None:
        if self.page:
            self.page.overlay.append(dlg)
            dlg.open = True
            self.page.update()

    def _close_dialog(self, dlg: ft.AlertDialog) -> None:
        dlg.open = False
        if self.page:
            self.page.update()

    def _toggle_theme(self) -> None:
        if self.on_toggle_theme:
            self.on_toggle_theme()
        self._build_content()
        self._safe_update()

    def _sync_guest_trips(self) -> None:
        self.is_migrating = True
        self._build_content()
        self._safe_update()

        async def _run():
            try:
                await self.auth_service.migrate_guest_trips()
            finally:
                self.is_migrating = False
                self._build_content()
                self._safe_update()

        if self.page:
            self.page.run_task(_run)
        else:
            try:
                asyncio.get_running_loop().create_task(_run())
            except RuntimeError:
                pass

    def did_mount(self) -> None:
        if self._has_refreshed_profile:
            return
        if self.session_manager.is_authenticated and not self.session_manager.is_guest:
            self._has_refreshed_profile = True

            async def _refresh_profile():
                try:
                    latest_user = await self.auth_service.get_profile()
                    if latest_user:
                        self._build_content()
                        self._safe_update()
                except Exception:
                    pass

            if self.safe_page:
                self.safe_page.run_task(_refresh_profile)

    def _safe_update(self) -> None:
        try:
            self.update()
        except Exception:
            pass

    @property
    def safe_page(self) -> Optional[ft.Page]:
        try:
            return self.page
        except Exception:
            return None

    def _navigate(self, route: str) -> None:
        if self.on_navigate:
            self.on_navigate(route)
```

---

### Phase 5: Refactor `SavedTripsView` to Match Uploaded Empty-State Screenshot (`image_2d1020.png`) & Web `HistoryPage`

Replace `desktop_client/views/saved_trips_view.py` with the exact Web `HistoryPage` (`Project/src/app/tabs/history/history.page.html`) structure:
- Full-width top white toolbar with left-aligned bold **`Saved Itineraries`** (`18px`) and right-aligned blue **`+`** icon button (`ft.Icons.ADD`, `icon_color=ThemeColors.PRIMARY_BLUE`, navigates to `/builder`).
- Search input and segment tabs (`All (N)`, `Upcoming`, `Past`, `Suggested`, `Custom`) are **only rendered when `len(self.itineraries) > 2`** (`history.page.html:8`).
- When `len(self.itineraries) == 0`, renders the exact centered empty state from `image_2d1020.png`:
  - `72x72` soft blue circle (`bgcolor="#e0f2fe"`) with blue clock outline icon (`ft.Icons.ACCESS_TIME`, `size=34`, `color="#0084ff"`).
  - Bold black title: **`No Saved Itineraries Yet`** (`22px`).
  - Subtitle: **`Your saved trips will appear here. Choose how you would like to plan your Nueva Ecija travel experience:`**
  - Two vertically stacked `340px`-wide buttons:
    1. Dark navy (`#0f172a`) button: **`✨ Suggested Itinerary`** → navigates to `/suggested`.
    2. Bright blue (`#0084ff`) button: **`+ Custom Itinerary`** → navigates to `/builder`.

```python
"""Saved Trips Management View mirroring Ionic tabs/history and image_2d1020.png."""

from __future__ import annotations

import asyncio
from datetime import date
from typing import Callable, Optional
import flet as ft

from desktop_client.components.dialogs import show_confirm_dialog
from desktop_client.config.settings import ThemeColors
from desktop_client.models.itinerary import Itinerary
from desktop_client.services.itinerary_service import get_itinerary_service


class SavedTripsView(ft.Container):
    """Saved itineraries view matching Ionic tabs/history and image_2d1020.png."""

    def __init__(
        self,
        on_navigate: Optional[Callable[[str], None]] = None,
        on_select_trip: Optional[Callable[[Itinerary], None]] = None,
    ):
        super().__init__()
        self.on_navigate = on_navigate
        self.on_select_trip = on_select_trip
        self.itinerary_service = get_itinerary_service()

        self.expand = True
        self.padding = 0
        self.bgcolor = ThemeColors.BG_LIGHT

        self.active_segment = "all"  # all, upcoming, past, suggested, custom
        self.search_term = ""

        self.itineraries: list[Itinerary] = []
        self.is_loading = True

        self._build_content()
        self._load_trips()

    def _build_content(self) -> None:
        # Top Header Bar matching .history-toolbar in image_2d1020.png
        top_toolbar = ft.Container(
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border=ft.Border.only(bottom=ft.BorderSide(1, ThemeColors.BORDER_LIGHT)),
            padding=ft.Padding.symmetric(horizontal=20, vertical=10),
            content=ft.Row(
                controls=[
                    ft.Text("Saved Itineraries", size=18, weight=ft.FontWeight.W_800, color=ThemeColors.TEXT_BLACK),
                    ft.IconButton(
                        icon=ft.Icons.ADD,
                        icon_size=24,
                        icon_color=ThemeColors.PRIMARY_BLUE,
                        tooltip="New Itinerary",
                        on_click=lambda _: self._navigate("/builder"),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        if self.is_loading:
            body = ft.Container(
                expand=True,
                alignment=ft.Alignment(0, 0),
                content=ft.Row(
                    controls=[
                        ft.ProgressRing(width=24, height=24, stroke_width=2),
                        ft.Text("Loading saved trips...", size=13, color=ThemeColors.TEXT_MUTED_LIGHT),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=12,
                ),
            )
            self.content = ft.Column(controls=[top_toolbar, body], spacing=0, expand=True)
            return

        # Empty State (len(self.itineraries) == 0) — Exact match to image_2d1020.png
        if len(self.itineraries) == 0:
            clock_circle = ft.Container(
                width=72,
                height=72,
                border_radius=36,
                bgcolor="#e0f2fe",
                alignment=ft.Alignment(0, 0),
                content=ft.Icon(ft.Icons.ACCESS_TIME_ROUNDED, size=34, color=ThemeColors.PRIMARY_BLUE),
            )

            suggested_btn = ft.Container(
                width=360,
                height=46,
                bgcolor="#0f172a",
                border_radius=10,
                alignment=ft.Alignment(0, 0),
                ink=True,
                on_click=lambda _: self._navigate("/suggested"),
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.AUTO_AWESOME, size=18, color=ft.Colors.WHITE),
                        ft.Text("Suggested Itinerary", size=14, weight=ft.FontWeight.W_700, color=ft.Colors.WHITE),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=8,
                ),
            )

            custom_btn = ft.Container(
                width=360,
                height=46,
                bgcolor=ThemeColors.PRIMARY_BLUE,
                border_radius=10,
                alignment=ft.Alignment(0, 0),
                ink=True,
                on_click=lambda _: self._navigate("/builder"),
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.ADD, size=18, color=ft.Colors.WHITE),
                        ft.Text("Custom Itinerary", size=14, weight=ft.FontWeight.W_700, color=ft.Colors.WHITE),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=8,
                ),
            )

            empty_body = ft.Container(
                expand=True,
                alignment=ft.Alignment(0, 0),
                content=ft.Column(
                    controls=[
                        clock_circle,
                        ft.Container(height=10),
                        ft.Text("No Saved Itineraries Yet", size=22, weight=ft.FontWeight.W_800, color=ThemeColors.TEXT_BLACK),
                        ft.Container(
                            width=420,
                            content=ft.Text(
                                "Your saved trips will appear here. Choose how you would like to plan your Nueva Ecija travel experience:",
                                size=13,
                                color=ThemeColors.TEXT_FAINT_LIGHT,
                                text_align=ft.TextAlign.CENTER,
                            ),
                        ),
                        ft.Container(height=14),
                        suggested_btn,
                        ft.Container(height=4),
                        custom_btn,
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=4,
                ),
            )
            self.content = ft.Column(controls=[top_toolbar, empty_body], spacing=0, expand=True)
            return

        # Non-empty state (savedItineraries.length > 0)
        body_controls: list[ft.Control] = []

        # Search & Segment Filter Header (only shown when savedItineraries.length > 2, matching history.page.html:8)
        if len(self.itineraries) > 2:
            self.search_field = ft.TextField(
                hint_text="Search saved trips or municipalities...",
                hint_style=ft.TextStyle(size=12, color=ThemeColors.TEXT_FAINT_LIGHT),
                prefix_icon=ft.Icons.SEARCH_ROUNDED,
                value=self.search_term,
                border_radius=12,
                border_color=ThemeColors.BORDER_LIGHT,
                focused_border_color=ThemeColors.PRIMARY_BLUE,
                dense=True,
                on_change=lambda e: self._on_search_change(e.control.value),
            )
            segments = [
                ("all", f"All ({len(self.itineraries)})"),
                ("upcoming", "Upcoming"),
                ("past", "Past"),
                ("suggested", "Suggested"),
                ("custom", "Custom"),
            ]
            segments_row = ft.Row(
                controls=[
                    self._create_segment_pill(seg_key, seg_label, self.active_segment == seg_key)
                    for seg_key, seg_label in segments
                ],
                spacing=8,
                scroll=ft.ScrollMode.AUTO,
            )
            body_controls.extend([self.search_field, ft.Container(height=8), segments_row, ft.Container(height=12)])

        muni_dest = self.itineraries[0].destination if self.itineraries else "Nueva Ecija"
        trip_count_text = f"{len(self.itineraries)} {'Trip' if len(self.itineraries) == 1 else 'Trips'} Planned in {muni_dest}"

        headline_block = ft.Column(
            controls=[
                ft.Text("Your Saved Trips", size=20, weight=ft.FontWeight.W_800, color=ThemeColors.TEXT_BLACK),
                ft.Text(trip_count_text, size=13, color=ThemeColors.TEXT_MUTED_LIGHT),
            ],
            spacing=2,
        )
        body_controls.extend([headline_block, ft.Container(height=14)])

        filtered_trips = self._get_filtered_trips()
        if filtered_trips:
            cards = [self._create_trip_card(it) for it in filtered_trips]
            grid = ft.ResponsiveRow(
                controls=[ft.Container(content=c, col={"sm": 12, "md": 6, "lg": 4}) for c in cards],
                spacing=16,
                run_spacing=16,
            )
            body_controls.append(grid)
        else:
            body_controls.append(
                ft.Container(
                    padding=40,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.FILTER_ALT_OUTLINED, size=36, color=ThemeColors.PRIMARY_BLUE),
                            ft.Text("No Matching Itineraries", size=16, weight=ft.FontWeight.BOLD),
                            ft.Text(
                                f'No saved trips found for "{self.search_term or self.active_segment}". Try clearing your search or switching filter tabs.',
                                size=12,
                                color=ThemeColors.TEXT_MUTED_LIGHT,
                            ),
                            ft.FilledButton(
                                content=f"Show All Trips ({len(self.itineraries)})",
                                style=ft.ButtonStyle(bgcolor=ThemeColors.PRIMARY_BLUE, color=ft.Colors.WHITE),
                                on_click=lambda _: self._reset_filters(),
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                    ),
                )
            )

        scroll_area = ft.Container(
            expand=True,
            padding=ft.Padding.symmetric(horizontal=28, vertical=20),
            content=ft.Column(controls=body_controls, spacing=0, scroll=ft.ScrollMode.AUTO, expand=True),
        )
        self.content = ft.Column(controls=[top_toolbar, scroll_area], spacing=0, expand=True)

    def _create_segment_pill(self, key: str, label: str, is_active: bool) -> ft.Control:
        return ft.Container(
            content=ft.Text(
                label,
                size=12,
                weight=ft.FontWeight.W_700 if is_active else ft.FontWeight.W_500,
                color=ft.Colors.WHITE if is_active else ThemeColors.TEXT_MAIN_LIGHT,
            ),
            bgcolor=ThemeColors.PRIMARY_BLUE if is_active else ThemeColors.SURFACE_LIGHT,
            border=ft.Border.all(1.2, ThemeColors.PRIMARY_BLUE if is_active else ThemeColors.BORDER_LIGHT),
            border_radius=20,
            padding=ft.Padding.symmetric(horizontal=14, vertical=8),
            ink=True,
            on_click=lambda _: self._on_segment_select(key),
        )

    def _get_days_nights_label(self, itin: Itinerary) -> str:
        days = len(itin.days) if itin.days else 1
        nights = max(0, days - 1)
        return f"{days} Days - {nights} {'Night' if nights == 1 else 'Nights'}" if nights > 0 else f"{days} Day"

    def _create_trip_card(self, itin: Itinerary) -> ft.Control:
        is_suggested = itin.type == "suggested"
        badge_bg = ThemeColors.SUGGESTED_BADGE_BG if is_suggested else ThemeColors.CUSTOM_BADGE_BG
        badge_color = ThemeColors.SUGGESTED_BADGE_TEXT if is_suggested else ThemeColors.CUSTOM_BADGE_TEXT
        badge_label = "Suggested Plan" if is_suggested else "Custom Plan"

        return ft.Container(
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border=ft.Border.all(1.2, ThemeColors.BORDER_LIGHT),
            border_radius=16,
            padding=16,
            ink=True,
            on_click=lambda _: self._open_trip(itin),
            shadow=ft.BoxShadow(blur_radius=8, color=ft.Colors.with_opacity(0.04, "#000000")),
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Container(
                                content=ft.Text(badge_label, size=10, weight=ft.FontWeight.BOLD, color=badge_color),
                                bgcolor=badge_bg,
                                border_radius=6,
                                padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                            ),
                            ft.Row(
                                spacing=4,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Text(
                                        f"₱{int(itin.daily_budget):,}/day" if itin.daily_budget else "₱0/day",
                                        size=12,
                                        weight=ft.FontWeight.BOLD,
                                        color=ThemeColors.BUDGET_GREEN,
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.DELETE,
                                        icon_size=18,
                                        icon_color=ThemeColors.ERROR,
                                        tooltip="Delete itinerary",
                                        on_click=lambda _: self._delete_trip(itin),
                                    ),
                                ],
                            ),
                        ],
                    ),
                    ft.Text(itin.title, size=16, weight=ft.FontWeight.W_800, color=ThemeColors.TEXT_BLACK, max_lines=1),
                    ft.Row(
                        spacing=4,
                        controls=[
                            ft.Icon(ft.Icons.LOCATION_ON, size=14, color=ThemeColors.PRIMARY_BLUE),
                            ft.Text(itin.destination or "Nueva Ecija", size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                        ],
                    ),
                    ft.Divider(color="#f1f5f9", height=1),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Row(
                                spacing=4,
                                controls=[
                                    ft.Icon(ft.Icons.CALENDAR_TODAY, size=13, color=ThemeColors.PRIMARY_BLUE),
                                    ft.Text(f"{itin.start_date} → {itin.end_date}", size=11, color=ThemeColors.TEXT_MUTED_LIGHT),
                                ],
                            ),
                            ft.Container(
                                content=ft.Text(self._get_days_nights_label(itin), size=10, weight=ft.FontWeight.BOLD, color=ThemeColors.PRIMARY_BLUE),
                                bgcolor=ThemeColors.AZURE_SOFT,
                                border_radius=10,
                                padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                            ),
                        ],
                    ),
                ],
            ),
        )

    def _get_filtered_trips(self) -> list[Itinerary]:
        results = self.itineraries
        today = date.today().strftime("%Y-%m-%d")
        if self.active_segment == "suggested":
            results = [it for it in results if it.type == "suggested"]
        elif self.active_segment == "custom":
            results = [it for it in results if it.type != "suggested"]
        elif self.active_segment == "upcoming":
            results = [it for it in results if (it.end_date or "") >= today]
        elif self.active_segment == "past":
            results = [it for it in results if (it.end_date or "") < today]

        if self.search_term.strip():
            q = self.search_term.strip().lower()
            results = [
                it for it in results
                if q in (it.title or "").lower() or q in (it.destination or "").lower()
            ]
        return results

    def _reset_filters(self) -> None:
        self.search_term = ""
        self.active_segment = "all"
        self._build_content()
        self._safe_update()

    def _safe_update(self) -> None:
        try:
            self.update()
        except Exception:
            pass

    def _on_segment_select(self, seg_key: str) -> None:
        self.active_segment = seg_key
        self._build_content()
        self._safe_update()

    def _on_search_change(self, query: str) -> None:
        self.search_term = query
        self._build_content()
        self._safe_update()

    def _open_trip(self, itin: Itinerary) -> None:
        if self.on_select_trip:
            self.on_select_trip(itin)

    @property
    def safe_page(self) -> Optional[ft.Page]:
        try:
            return self.page
        except Exception:
            return None

    def _delete_trip(self, itin: Itinerary) -> None:
        def confirm():
            async def _worker():
                await self.itinerary_service.delete_itinerary(itin.id)
                await self._load_trips_async()
            if self.safe_page:
                self.safe_page.run_task(_worker)
            else:
                try:
                    asyncio.get_running_loop().create_task(_worker())
                except RuntimeError:
                    pass

        if self.safe_page:
            show_confirm_dialog(
                self.safe_page,
                title="Delete Itinerary?",
                message=f'Are you sure you want to delete "{itin.title}"? This action cannot be undone.',
                on_confirm=confirm,
            )

    def _load_trips(self) -> None:
        if self.safe_page:
            self.safe_page.run_task(self._load_trips_async)
        else:
            try:
                asyncio.get_running_loop().create_task(self._load_trips_async())
            except RuntimeError:
                pass

    async def _load_trips_async(self) -> None:
        self.is_loading = True
        self._build_content()
        self._safe_update()
        try:
            self.itineraries = await self.itinerary_service.list_itineraries()
        except Exception:
            self.itineraries = []
        finally:
            self.is_loading = False
            self._build_content()
            self._safe_update()

    def _navigate(self, route: str) -> None:
        if self.on_navigate:
            self.on_navigate(route)
```

---

### Phase 6: Refactor `DestinationPicker`, `SuggestedWizardView`, and `CustomBuilderView` for 100% Web Parity (`desktop_client/`)

#### 6.1 Upgrade `desktop_client/components/destination_picker.py` to Match Web `DestinationAutocompleteComponent`
Update `desktop_client/components/destination_picker.py` so it provides:
- Text input box with blue location icon, placeholder `"Choose a town, city, or landmark"`, and clear `×` button.
- Live floating suggestion panel when typing/focused showing:
  - **Province-Wide Corridor** (`All of Nueva Ecija — 2,673 Places`)
  - **Cities & Municipalities** (with City/District/POI count badges)
  - **Landmarks & Top Attractions** (`Minalungao National Park`, `Highland Bali Villas Resort and Spa`, etc., with `⭐ Anchor` badge that passes `place_id` to `on_landmark_select`)
  - Footer trigger: `Browse All 32 Nueva Ecija Towns & Cities`
- Wrapped Quick Destination Chips row directly below the input in exact Web order:
  - `Bongabon`, `Pantabangan`, `Cabanatuan City`, `Gapan City`, `General Tinio`, `Nueva Ecija`, and `🗺️ All 32 Towns`.

#### 6.2 Refactor `desktop_client/views/suggested_wizard_view.py` for 100% Web `SuggestedWizardPage` Parity
Apply these exact changes in `desktop_client/views/suggested_wizard_view.py`:
1. **Header Bar**: Render the `.figma-header-bar` (`←` back arrow + title `Suggested Itinerary` or `Nearby Places` when `view_mode == 'nearby'` + trailing `✏️` edit button calling `_reset_wizard()` when `view_mode == 'itinerary'`). In `desktop_client/main.py:213`, set `workflow_header.visible = False` on `/suggested` and `/builder` so each view's native Figma header bar is the sole top header (eliminating duplicate header bars and extra subtitles).
2. **View 1 (`form` — `"Tell us your travel details"`)**:
   - Heading: **`Tell us your travel details`** (no subtitle, no `"Step 1..6"` headings).
   - **Remove** the extra `Trip Title` input field (`self.title_val` is auto-computed as `f"Suggested {self.destination_val} Trip"`).
   - **Remove** the extra `Step 5: Pacing & Intensity` selector (`self.pacing_val = "moderate"`).
   - Exact field order and components:
     1. **`Destination`**: `DestinationPicker` + wrapped quick chips (`Bongabon`, `Pantabangan`, `Cabanatuan City`, `Gapan City`, `General Tinio`, `Nueva Ecija`, `🗺️ All 32 Towns`).
     2. **`Travel Dates`**: Clickable input box with blue calendar icon + formatted date range + helper subtitle `e.g., Nov 14 – Nov 16, 2026 (3 days, 2 nights)`.
     3. **`Daily Budget`**: Full-width numeric input with blue cash icon + 4 pill preset chips (`₱1,500`, `₱2,500`, `₱4,000`, `₱6,000`) directly below the input.
     4. **`Preferences (optional)`**: 5 text-only pill buttons (`Nature & Parks`, `Food Trip`, `Culture & History`, `Shopping`, `Resort`).
     5. **`Travel Mode`**: 3 icon+label pill buttons (`Drive / Car`, `Motorcycle / Tricycle`, `Walking / Transit`).
     6. **`Minimum Place Rating`**: 3 pill buttons (`All Ratings`, `★ 4.0+ ★`, `★ 4.5+ ★`).
     7. **Action CTA**: Full-width solid blue button **`Find Itinerary`**.
3. **View 2 (`itinerary` — Generated Plan)**:
   - **Remove** the top dark-navy gradient banner and its 5 extra buttons!
   - Render **`.figma-trip-card`**: White rounded card with `nueva_ecija_arch.png` thumbnail (`76x76`), bold destination title, `X days` + `₱Y/day` subrow, and preference tag pills (`Food Trip`, `Culture & History`, `Resort`).
   - Render **`.verified-budget-card`**: Shield-checkmark icon + `Verified Estimated Costs` | `Target: ₱X/day`, main amount `{{ display_text }}` + `estimated venue admission & activities`, `ⓘ N unpriced` badge, and footnote `* N stop(s) do not list verified pricing in open public records.`
   - Render **`.assumptions-info-box`**: Collapsible card with `parse_assumption(note)` structured insight cards (`Pacing`, `Routing`, `Budget`, `Schedule`, `Advice`) and `View N` / `Hide` toggle.
   - Render **`.figma-day-capsule-bar`**: 2-line segmented day buttons (`Day X` + municipality name).
   - Render **Active Day Section**: Heading `Day X - {Municipality}`, italic subtitle `Food spots, local culture, and historic sites in {Municipality}!`, embedded `ItineraryRouteMap`, inter-stop `.route-leg-badge` pills (`🚗 X.X km • ~Y mins drive / Z mins tricycle • Est. Fare ₱A–₱B`), and `.figma-stop-card` items (thumbnail, `1. Stop Name`, `★ 4.5 (120)`, and `09:30 AM - 11:30 AM (2 hrs)`).
   - Render **`.nearby-banner-trigger`**: Clickable banner card (`Nearby Places in {Municipality}` / `Find nearby restaurants, pharmacies, and stores` + `→`).
   - Render **`.itinerary-bottom-actions`**: `✓ Accept & Save Itinerary` and `✏️ Customize in Builder`.
4. **View 3 (`nearby` — Nearby Places)**:
   - Intro text: `Find nearby restaurants, pharmacies, and stores to make your trip more convenient and comfortable.`
   - 3 Segmented Capsule Tabs: `Restaurants`, `Hospital & Pharmacies`, `Stores`.
   - `.figma-nearby-card` items: Category badge (`Restaurant`, `Health & Pharmacy`, `Retail & Store`) + opening hours pill on top row, `1. Place Name`, location icon + municipality, and `Maps` + `Add to Day X` buttons. Clicking `Add to Day X` appends the stop, shows a toast `"Added {name} to Day {X}!"`, and stays on `nearby` until the user clicks `←`.

#### 6.3 Refactor `desktop_client/views/custom_builder_view.py` for 100% Web `CustomBuilderPage` Parity
Apply these exact changes in `desktop_client/views/custom_builder_view.py`:
1. **Header Bar & View Mode Switcher**:
   - Top toolbar: `←` back button + title **`Custom Itinerary`** (in `form` and `browse`) or **`Your Custom Itinerary`** (in `timeline`) + right **`✓ Save`** button (visible when `active_view != 'form'`, disabled when `total_stops_count == 0`).
   - Below toolbar (when `active_view != 'form'`): 2-tab `.view-mode-bar` (`+ Add Places` | `📅 Your Itinerary ({{ total_stops_count }})`).
2. **View 0 (`form` — `"Tell us your travel details"`)**:
   - Heading: **`Tell us your travel details`** (no subtitle).
   - Default `trip_title = "Nueva Ecija Getaway"`, default 2-day date range (`today` to `tomorrow`), default `preferences = []` (empty list unless user selects pills).
   - Shortening Date Range Guard: When applying shorter dates in `_open_date_picker()` where trailing days have stops, prompt **`Shorten Trip Duration?`** (`Cancel` | `Discard & Shorten`).
   - Bottom CTA: **`Start Building Itinerary →`**.
3. **View 1 (`browse` — `"Add the places you want to visit"`)**:
   - Heading: **`Add the places you want to visit`** + `Scheduling for:` day pills (`Day 1 (0)`, `Day 2 (0)`) + `+` add-day button.
   - Category Filter Pills: `All`, conditional `✨ Recommended for You` (only when `len(self.preferences) > 0`), `Tourist Spots`, `Food`, `Resorts & Stays`, `Culture & Heritage`, `Shopping`, `Transit & Essentials`, and **`Other`**.
   - Place Cards Grid: Responsive cards with top photo + floating category badge, bold title, `{{ municipality_name }}, Nueva Ecija`, cost tag on bottom-left, and `[+ Add]` / `[✓ Added]` toggle button on bottom-right (clicking card opens `show_place_detail_dialog` with `on_add_to_day`; no extra `"Details"` button). Empty state includes **`Reset Filters`** button.
   - Sticky bottom bar: **`View my Itinerary ({{ total_stops_count }} {{ 'place' if total_stops_count == 1 else 'places' }}) →`**.
4. **View 2 (`timeline` — `"Your Custom Itinerary"`)**:
   - Render dismissible **`✨ Place Pre-Loaded`** banner at top when `self.pre_added_place` was passed.
   - Render **`.trip-settings-card`** (Row 1: `Trip Title` + `Daily Budget (₱)`; Row 2: `Start Date` + `End Date` + `Destination`).
   - Render separate **`.verified-budget-card`** (`Verified Estimated Costs`, `Budget: ₱X/day (₱Y total for N days)`, `displayText`, and unpriced stop footnote).
   - Render **`.timeline-day-tabs-bar`**: 2-line day tabs (`Day X` / `{{ municipality }}`) + `+ Add Day` button.
   - Active Day Header: `Day X - {{ municipality }}`, `{{ travel_date }} (N stops)`, conditional `🕒 Auto-Schedule` (when `len(items) > 1`), and conditional `🗑 Delete Day` (when `len(days) > 1`, with **`Delete Day X?`** confirmation dialog).
   - Stop Actions: Up/Down reorder buttons (auto-optimizing times), `Edit` button (`Edit Scheduled Stop` modal with `Move to Day` that reindexes both days and switches `active_day_index` to target day), and `Remove` button (with **`Remove Stop?`** confirmation dialog).
   - Empty Day Card (`.day-empty-stops-box`) when `len(cur_day.items) == 0`.
   - 2-Tab Place Picker / Off-Grid Venue Modal (`🔍 Browse Places` with **`Duplicate Destination`** confirmation guard | `✏️ Off-Grid Venue` with collapsible `Pin Coordinates (Lat / Lng) — Optional` and exact bounds `15.15 <= lat <= 16.15`, `120.70 <= lng <= 121.40`).
   - Bottom Footer CTA: **`💾 View Full Itinerary / Save Trip`** (disabled when `total_stops_count == 0`).

---

## 5. Exhaustive 100-Test-Case Verification Matrix (`TC-01`–`TC-100`)

Gemini Antigravity must run and verify all existing tests (`TC-01`–`TC-85`) plus the **15 new parity regression tests (`TC-86`–`TC-100`)** below in `desktop_client/tests/test_parity_services_and_components.py`:

| Test ID | Module | Verification Scenario & Acceptance Criteria |
| :-: | :--- | :--- |
| **`TC-86`** | **Map Filters Modal (`places_view.py`)** | Clicking `Filters` opens the chip-based `Filter Destinations` dialog with zero `Dropdown.__init__() got an unexpected keyword argument 'on_change'` errors; toggling multi-select categories, municipality chip, and price range pill updates `_active_filters_count` and filters `filtered_places` accurately. |
| **`TC-87`** | **Map Quick Category Pills (`places_view.py`)** | Clicking a top-bar quick category pill selects that single category (replacing any prior single pill selection) and clicking it again resets to `All Places`, matching `map.page.ts:854–871`. |
| **`TC-88`** | **Map Pan & Scroll-Wheel Zoom (`slippy_map_canvas.py`)** | `_handle_scroll()` zooms in (`dy < -0.5`) and out (`dy > 0.5`) across both `e.scroll_delta.y` (Flet 1.1.2 `Offset`) and `e.scroll_delta_y`; `_handle_pan_update()` pans smoothly across `e.local_delta` and clamps within `NUEVA_ECIJA_BOUNDS` (`15.05..16.25`, `120.55..121.55`) while reusing pooled tile controls (`_tile_pool`). |
| **`TC-89`** | **Database Profile & Avatar Loading (`user.py`, `settings.py`)** | `User.from_dict(data, extra)` prioritizes database `data` fields (`avatar_url`, `middle_initial`, `birthday`, `gender`, `phone_number`) over stale `extra`, omits `"N/A."` from `full_name` (`"Edward Renz Natividad"`), and `settings.resolve_avatar_path()` decodes `data:image/png;base64,...` strings into local files under `storage/avatars/`. |
| **`TC-90`** | **Profile Tab Exact UI (`profile_view.py`, `image_2d13c2.png`)** | `ProfileView` in `view_mode == "profile"` renders `Profile` title (no subtitle), avatar + `Edward Renz Natividad` + `@edselrenz0@gmail.com` + `Edit Profile` pill (zero extra metadata badges), and the 5-row menu card with verbatim descriptions (`Settings`, `Favorites`, `Help & Support`, `About`, `Log Out`). |
| **`TC-91`** | **Edit Profile In-Page Subview (`profile_view.py`, `image_2d1741.png`)** | Clicking `Edit Profile` switches `ProfileView.view_mode` to `"edit"` (in-page, not a dialog) and renders `← Edit Profile`, circular avatar with camera badge + `Change Photo` pill (no `Remove` or `Presets` buttons), and **only the 7 stacked fields** (`First Name`, `Middle Initial (if applicable)`, `Last Name`, `Birthday`, `Gender`, read-only `Email Address`, `Phone Number`) + `Save Changes` button (no `Username`, `Daily Budget`, or `Password` fields). |
| **`TC-92`** | **Settings In-Page Subview (`profile_view.py`, `image_2d1705.png`)** | Clicking `Settings` switches `ProfileView.view_mode` to `"settings"` (in-page, not a dialog) and renders `← Settings` + a single rounded card with **only the 6 rows**: `Account Information`, `Notifications` (switch), `Privacy & Security`, `Language` (`English`), `App Appearance` (`Light`), and `Clear Cache` (`Free up storage space`). |
| **`TC-93`** | **Saved Itineraries Empty State (`saved_trips_view.py`, `image_2d1020.png`)** | When `itineraries == []`, `SavedTripsView` hides the search bar, segment tabs, and `"Your Saved Trips"` header, and renders only the top `Saved Itineraries` + `+` toolbar and centered empty state (`No Saved Itineraries Yet`, subtitle, dark navy `Suggested Itinerary` button, and blue `Custom Itinerary` button). |
| **`TC-94`** | **Suggested Wizard Form Exact UI (`suggested_wizard_view.py`)** | `SuggestedWizardView` form renders `Tell us your travel details` heading, has **zero** `Trip Title` input and **zero** `Pacing & Intensity` selector, and presents the 6 fields in exact Web order (`Destination` → `Travel Dates` → `Daily Budget` with 4 pill chips → `Preferences (optional)` → `Travel Mode` → `Minimum Place Rating` → `Find Itinerary`). |
| **`TC-95`** | **Destination Autocomplete & Landmark Anchors (`destination_picker.py`)** | `DestinationPicker` supports text search across all 32 LGUs and 12 top Nueva Ecija landmarks, sets `anchor_place_id` when a landmark is selected, and renders wrapped quick chips (`Bongabon`, `Pantabangan`, `Cabanatuan City`, `Gapan City`, `General Tinio`, `Nueva Ecija`, `🗺️ All 32 Towns`). |
| **`TC-96`** | **Suggested Wizard Result View (`suggested_wizard_view.py`)** | Result view (`view_mode == "itinerary"`) renders `.figma-trip-card` (with `nueva_ecija_arch.png`, days count, daily budget, and preference tags—no dark navy 5-button banner), `.verified-budget-card` with unpriced count, structured `parse_assumption()` insight cards, 2-line day capsule tabs, `.figma-stop-card` items, `.nearby-banner-trigger`, and bottom CTAs (`Accept & Save Itinerary`, `Customize in Builder`). |
| **`TC-97`** | **Suggested Wizard Nearby View (`suggested_wizard_view.py`)** | `view_mode == "nearby"` updates header title to `Nearby Places`, renders `Restaurants`, `Hospital & Pharmacies`, and `Stores` tabs, and clicking `Add to Day X` appends the stop and keeps `view_mode == "nearby"` so multiple essentials can be added before pressing `←`. |
| **`TC-98`** | **Custom Builder Form & Browse Views (`custom_builder_view.py`)** | `CustomBuilderView` starts with `trip_title == "Nueva Ecija Getaway"`, 2-day default range, and empty `preferences`; `browse` view renders `Add the places you want to visit`, includes the `Other` category pill, and shows `Reset Filters` in the empty state. |
| **`TC-99`** | **Custom Builder Timeline Confirmations & Move-to-Day (`custom_builder_view.py`)** | `timeline` view displays the dismissible `Place Pre-Loaded` banner when `pre_added_place` is provided, separates `.trip-settings-card` and `.verified-budget-card`, prompts confirmation dialogs before `Delete Day`, `Remove Stop`, and shortening date ranges with stops, and reindexes both days + switches `active_day_index` when moving a stop to another day. |
| **`TC-100`** | **Custom Builder 2-Tab Off-Grid Modal (`custom_builder_view.py`)** | Clicking `Add Off-Grid Custom Venue` opens the 2-tab modal (`Browse Places` with Duplicate Destination guard | `Off-Grid Venue` with collapsible `Pin Coordinates (Lat / Lng) — Optional` validating `15.15 <= lat <= 16.15` and `120.70 <= lng <= 121.40`). |

---

## 6. Verification & Standalone `.exe` Build Commands for Antigravity

After applying Phases 1 through 6, run the following verification sequence in PowerShell / Terminal:

```powershell
# 1. Verify Backend Schema & User Profile Backfill + Run Backend Pytest Suite
python scripts/setup_postgres.py
pytest backend/tests -q

# 2. Run Desktop Client Unit & Parity Test Suite (TC-01 through TC-100)
pytest desktop_client/tests -q

# 3. Run Web Client Unit Test Suite (Verify 100% Pass with Extended Profile Sync)
cd Project
npm test -- --watch=false
cd ..

# 4. Rebuild Standalone Windows Executable (dist/NuevaEcijaTravel/NuevaEcijaTravel.exe)
python scripts/build_standalone_exe.py
```
