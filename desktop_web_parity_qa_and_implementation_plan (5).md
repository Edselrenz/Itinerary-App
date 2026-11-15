# Cycle 2 Post-Update QA Audit, 1:1 Web-Desktop Parity Verification & Antigravity Implementation Plan
**Project:** Nueva Ecija Travel Itinerary App (*"Trip mo, trip ko"*)  
**Audited Commit:** `40507f51c34620caea48eb5cc758ce7fffdaa7e0` (Diffed against `d81e6b278f6927b48c6d12379c7f3521f87102f1`)  
**Reference Web Deployment:** [Trip mo, trip ko Live Web App](https://www.google.com/search?q=https://edselrenz.github.io/Itinerary-App/) ([Welcome Route](https://www.google.com/search?q=https://edselrenz.github.io/Itinerary-App/%23/welcome))  
**Cloudflare Worker API Proxy:** [NE Itinerary API Worker](https://www.google.com/search?q=https%3A%2F%2Fwww.google.com%2Furl%3Fsa%3DE%26source%3Dgmail%26q%3Dhttps%3A%2F%2Fne-itinerary-api.edselrenz0.workers.dev%2Fapi%2Fv1) ([Tunnel Status Endpoint](https://www.google.com/search?q=https://ne-itinerary-api.edselrenz0.workers.dev/__status))  
**Permanent Ngrok Fallback:** [Ngrok Tunnel Endpoint](https://www.google.com/search?q=https://anybody-cube-surprise.ngrok-free.dev)

---

## 1. Executive Summary — Cycle 2 Post-Update Status & Newly Uncovered Regressions

Comparing your updated codebase (`40507f51c34620caea48eb5cc758ce7fffdaa7e0`) against the previous version (`d81e6b278f6927b48c6d12379c7f3521f87102f1`) confirms that **12 previous issues were resolved** (Welcome screen skyscraper blob removal, Login/Signup social buttons & spinners, stacked Middle Initial field, `show_toast()` Flet 1.1.2 helper, `BottomTabBar` active route preservation, `DestinationPicker` & `SavedTripsView` live-search focus retention, `ProfileView` Favorites search/category scroller & Help FAQ accordions, and `scripts/run_daemon.py` Worker tunnel sync).

However, our AST static analysis and end-to-end execution trace of commit `40507f51c34620caea48eb5cc758ce7fffdaa7e0` uncovered **16 critical runtime crashes, logic regressions, and dark-mode visual failures** across the exact areas you flagged:

| ID | Focus Area | Severity | File & Line Numbers | Root-Cause Summary |
| :--- | :--- | :--- | :--- | :--- |
| **REG-01** | **Desktop Startup Crash** | **P0 Blocker** | `desktop_client/config/settings.py:376, 390, 442` & `desktop_client/main.py:133` | `settings.py` uses `Optional[str]` and `Optional[float]` without importing `Optional` from `typing` (`NameError: name 'Optional' is not defined` on import). `main.py:133` uses `Optional[Any]` without importing `Any` (`NameError: name 'Any' is not defined`). Also `resolve_avatar_path` is defined twice in `settings.py` (`line 217` and `line 390`). |
| **REG-02** | **Creating / Saving Custom Itinerary Throws Error** | **P0 Blocker** | `desktop_client/views/custom_builder_view.py:1786–1789` & `desktop_client/views/trip_detail_view.py:390–395` | When `_save_custom_itinerary()` finishes saving a Custom Itinerary, it calls `self.on_navigate(f"/trips/{saved.id}", saved)` **inside** its `try...except` block. `navigate_to` instantiates `TripDetailView`, which evaluates `float(itm.estimated_cost or 0.0)` at `trip_detail_view.py:391`. Because `ItineraryItem` has **no `.estimated_cost` attribute** (only `.representative_cost`, `.estimated_cost_min`, `.estimated_cost_max`), `TripDetailView` throws `AttributeError: 'ItineraryItem' object has no attribute 'estimated_cost'`, which `_save_custom_itinerary()` catches and displays as `"Failed to save itinerary: 'ItineraryItem' object has no attribute 'estimated_cost'"`! |
| **REG-03** | **Custom Builder Back Button Traps User in "Discard Changes?" Loop** | **P0 Critical** | `desktop_client/views/custom_builder_view.py:138–167` | `if self.is_dirty: self._prompt_discard_changes(); return True` was placed at the **very top** of `handle_back()` before checking `self.active_view`. As soon as a user selects a budget preset, edits dates, or adds 1 stop (`is_dirty = True`), clicking `←` in `browse` (`View 1`) or `timeline` (`View 2`) refuses to step back to `timeline` or `form` (`View 0`) and instead pops `"Discard Changes?"` (which dumps the user out to `/home`). |
| **REG-04** | **Custom Builder Mount & Off-Grid Coordinates Bugs** | **P1 High** | `desktop_client/views/custom_builder_view.py:131, 1553–1557` | `did_mount()` calls `await self.place_service.list_places()`, which does not exist on `PlaceService` (`AttributeError`, should be `get_places(page=1, page_size=250)`). In `_open_custom_venue_dialog()`, `_toggle_coords` sets `coords_toggle_btn.text = ...`, which fails in Flet 1.1.2 because `ft.TextButton` uses `.content` instead of `.text`. |
| **REG-05** | **Suggested Wizard Save Crashes 100% of the Time** | **P0 Blocker** | `desktop_client/views/suggested_wizard_view.py:1302–1338` | `_save_generated_itinerary()` accesses non-existent attributes `item.start_time`, `item.estimated_cost`, `item.travel_time_from_prev_mins`, `item.travel_mode`, `d.date`, `d.theme`, `self.generated_itinerary.description`, `self.generated_itinerary.total_budget`, and passes invalid kwargs (`description`, `total_budget`, `travel_mode`, `is_suggested`) to `ItineraryCreatePayload(...)`. Crashes immediately with `AttributeError: 'ItineraryItem' object has no attribute 'start_time'`. |
| **REG-06** | **"Start Trip Here" Ignored by Backend When Online** | **P0 Critical** | `backend/app/algorithms/itinerary_generator.py:216–470` & `backend/app/schemas/itinerary.py:314–320` | `backend/app/algorithms/itinerary_generator.py` **never reads `request.anchor_place_id` or `request.anchor_place_payload` at all**! Furthermore, `SuggestedItineraryRequest.coerce_anchor_id` (`schemas/itinerary.py:317`) wipes any non-UUID string (`"dest-minalungao"`, `"osm-..."`) to `None`. Thus, when online, clicking `"✨ Start Trip Here"` on a Map POI on **both Web and Desktop** completely ignores the clicked POI! |
| **REG-07** | **"Start Trip Here" Offline & Resort/Hotel Anchor Bugs** | **P1 High** | `desktop_client/services/itinerary_service.py:224–236, 319–323, 387` & `Project/src/app/core/services/itinerary.service.ts:1082–1086, 1148` & `Project/src/app/tabs/map/map.page.ts:990` | (1) On Desktop, `curated_pool` omits API-merged/Live-OSM places from `place_service.get_loaded_places()`. (2) On both Web and Desktop, if the user clicks `"Start Trip Here"` on a resort/hotel (`resort_swimming` / `hotel_accommodation`), 1-day trips drop the anchor place on Web (`line 1083`), and multi-day trips move the anchor place from Stop 1 to the **last stop of the day** (`lodging` split at `itinerary_service.py:387` & `itinerary.service.ts:1148`). (3) On Web `map.page.ts:990`, if `place.municipality_name` is missing, `destination: place.name` is passed as the municipality filter, causing `muniMatches` to be empty. |
| **REG-08** | **Desktop Dark Mode Toggle & Window Resize Crash** | **P0 Blocker** | `desktop_client/main.py:115–122, 389–392` & `config/settings.py` & `components/bottom_tab_bar.py` | Clicking the Dark Mode toggle in `Profile -> Settings` calls `settings.set_dark_mode(new_is_dark)` (`AttributeError: 'Settings' object has no attribute 'set_dark_mode'`), `settings.palette` (`AttributeError`), `palette.bg_primary` (`AttributeError: 'ThemePalette' has 'bg_main', not 'bg_primary'`), and `bottom_tab_bar.refresh_theme()` (`AttributeError`). Window resize (`_on_page_resize`, line 390) also crashes with `AttributeError: 'Settings' object has no attribute 'palette'`. |
| **REG-09** | **Desktop Dark Mode White-on-White Unreadable Views** | **P1 High** | All Desktop Views (`dashboard_view.py`, `places_view.py`, `custom_builder_view.py`, `suggested_wizard_view.py`, `saved_trips_view.py`, `trip_detail_view.py`, `profile_view.py`, `login_view.py`, `signup_view.py`, `dialogs.py`) | When `page.theme_mode = ft.ThemeMode.DARK`, Flet flips uncolored `ft.Text` and `ft.TextField` foregrounds to white (`#f8fafc`), while these 9 views hardcode `self.bgcolor = ThemeColors.BG_LIGHT` (`#f8fafc`) and `bgcolor=ft.Colors.WHITE` on cards—creating **white-on-white invisible text** across cards, inputs, FAQs, and modals. |
| **REG-10** | **Web Dark Mode Black-on-Dark Headings & White Card Inversions** | **P1 High** | `Project/src/global.scss:3323–3580` & page SCSS files (`home.page.scss`, `history.page.scss`, `map.page.scss`, `custom-builder.page.scss`, `suggested-wizard.page.scss`, `itinerary-detail.page.scss`, `place-detail-sheet.component.scss`, `destination-autocomplete.component.scss`) | `global.scss` sets `ion-content { background: #0b1120 !important }`, but targets wrong class names (`.custom-builder-content` instead of `.builder-content`, `.suggested-wizard-content` instead of `.wizard-content`, `.itinerary-detail-content` instead of `.detail-content`, `.itinerary-card` instead of `.history-itinerary-card`, `.place-detail-sheet` instead of `.detail-sheet-card`) and omits `.section-heading`, `.dest-title`, `.custom-card .card-heading`, `.saved-trips-headline`, `.main-heading`, `.group-label`, `.browse-main-heading`, `.figma-input-box`, `.figma-trip-card`, `.figma-stop-card`, `.place-browser-card`, `.trip-details-card`, etc.—leaving `#000000` / `#0f172a` black headings on a `#0b1120` dark background! |
| **REG-11** | **Desktop Logout Button Crashes Before Modal Opens** | **P0 Blocker** | `desktop_client/views/profile_view.py:1219` | `_confirm_logout()` references `ThemeColors.TEXT_PRIMARY_LIGHT`, which does not exist on `ThemeColors` (`TEXT_MAIN_LIGHT`). Clicking **Log Out** in Profile crashes with `AttributeError: type object 'ThemeColors' has no attribute 'TEXT_PRIMARY_LIGHT'`. |
| **REG-12** | **Desktop Cloud Failover Silently Fails on Localhost ConnectError** | **P0 Critical** | `desktop_client/core/api_client.py:169–170, 182` | When `127.0.0.1:8000` is down, `ApiClient.request()` tries to fail over to `CLOUDFLARE_WORKER_API_URL`, but line 169 calls `logger.info(...)` (`NameError: name 'logger' is not defined`) and line 170 calls `self.set_base_url(worker_url)` (`AttributeError: 'ApiClient' object has no attribute 'set_base_url'`). Both errors are swallowed by `except Exception: pass` on line 182, aborting failover! |
| **REG-13** | **`TripDetailView` Adding Nearby Place Crashes** | **P1 High** | `desktop_client/views/trip_detail_view.py:471–480` | `_add_nearby_to_active_day()` passes invalid kwargs (`day_number`, `order_index`, `travel_mode`) and omits required args (`id`, `day_id`, `sort_order`) on `ItineraryItem(...)`, then assigns `self.itinerary.total_stops = ...` (a read-only `@property`), crashing with `TypeError` / `AttributeError`. |
| **REG-14** | **Desktop Dialogs Opened via `page.overlay.append` Never Removed on Close** | **P2 Medium** | `desktop_client/main.py:199`, `custom_builder_view.py:191, 275, 456, 1403, 1447, 1502, 1705`, `profile_view.py:1257`, `dashboard_view.py`, `places_view.py` | Dialogs opened with `page.overlay.append(dlg); dlg.open = True` and closed with `dlg.open = False` remain in `page.overlay` permanently instead of using `open_overlay_dialog` / `close_overlay_dialog`, causing overlay buildup and interfering with `page.pop_dialog()`. |
| **REG-15** | **Desktop `SavedTripsView` & `DashboardView` Flash Stale Guest Trips When Logged In** | **P2 Medium** | `desktop_client/views/saved_trips_view.py:37` & `views/dashboard_view.py:50` | Both `__init__` constructors pre-populate `self.itineraries` from `self.itinerary_service.guest_storage.list_itineraries()` even when `session_manager.is_authenticated` is `True`. If a cloud request fails or while it is loading, guest trips appear under the logged-in user's account. |
| **REG-16** | **Scripts Hardcoded Path & Missing PyInstaller Hidden Imports** | **P2 Medium** | `scripts/run_daemon.py:7` & `scripts/build_standalone_exe.py:100–135` | `run_daemon.py:7` hardcodes `r"C:\Users\Edward\Desktop\CaseStudy"` instead of `Path(__file__).resolve().parent.parent`. `build_standalone_exe.py` omits `--hidden-import` entries for `connectivity_service`, `offline_data`, `polyline`, `commute_guide`, `favorites_service`, and view/component modules. |

---

## 2. Deep Investigation of Your 4 Specific Focus Areas

### 2.1 Why Creating / Saving a Custom Itinerary Throws an Error (Scripts, Views, Services & Backend)

We traced the entire Custom Itinerary lifecycle from Step 1 (`form`) -> Step 2 (`browse`) -> Step 3 (`timeline`) -> Save (`POST /api/v1/itineraries`) -> Post-Save Redirect (`/trips/{saved.id}`) and found **4 bugs** that cause errors or trap the user:

1. **The Post-Save `TripDetailView` Crash Caught by `CustomBuilderView` (`REG-02`)**:
   - In `desktop_client/views/custom_builder_view.py:1750–1790`:
     ```python
     saved = await self.itinerary_service.create_itinerary(payload)
     self.is_dirty = False
     self.itinerary_service.clear_active_draft_itinerary()
     if self.safe_page:
         show_toast(self.safe_page, f"Saved '{saved.title}'!")
     if self.on_navigate:
         self.on_navigate(f"/trips/{saved.id}", saved)
     except Exception as e:
         if self.safe_page:
             show_toast(self.safe_page, f"Failed to save itinerary: {e}", is_error=True)
     ```
   - When `self.on_navigate(f"/trips/{saved.id}", saved)` runs, `main.py:292` constructs `TripDetailView(itinerary=trip_obj, ...)`, which immediately calls `self._build_view_mode()`.
   - At `desktop_client/views/trip_detail_view.py:390–394`:
     ```python
     total_activity_expenses = sum(
         float(itm.estimated_cost or 0.0)
         for d in itin.days
         for itm in d.items
     )
     ```
   - `ItineraryItem` (`desktop_client/models/itinerary.py:42`) **does NOT have an `estimated_cost` attribute**—it has `representative_cost` (a `@property`), `estimated_cost_min`, and `estimated_cost_max`!
   - Therefore, as soon as you save a Custom Itinerary with at least 1 stop, `TripDetailView` throws `AttributeError: 'ItineraryItem' object has no attribute 'estimated_cost'`, which is caught by `_save_custom_itinerary()`'s `try...except` block and shown as a red error toast:
     **`"Failed to save itinerary: 'ItineraryItem' object has no attribute 'estimated_cost'"`**!
   - And because `TripDetailView` failed to construct, `content_area.content` is never updated, leaving the user stuck on `CustomBuilderView`!

2. **The `handle_back()` "Discard Changes?" Trap (`REG-03`)**:
   - In `desktop_client/views/custom_builder_view.py:138–167`:
     ```python
     def handle_back(self) -> bool:
         if self.is_dirty:
             self._prompt_discard_changes()
             return True
         if self.active_view == "browse":
             ...
     ```
   - Clicking a budget preset chip (`_set_budget_preset`), changing dates (`_open_date_picker`), toggling a preference (`_toggle_pref`), or adding a stop (`_toggle_place_in_active_day`) sets `self.is_dirty = True`.
   - Because `if self.is_dirty:` runs **before** checking `if self.active_view == "browse":` or `elif self.active_view == "timeline":`, clicking `←` in `browse` or `timeline` never steps back to `timeline` or `form`—it immediately triggers the `"Discard Changes?"` modal and exits to `/home`!

3. **`did_mount()` Calling Non-Existent `self.place_service.list_places()` (`REG-04`)**:
   - `custom_builder_view.py:131` calls `await self.place_service.list_places()`, which raises `AttributeError: 'PlaceService' object has no attribute 'list_places'` (the actual method on `PlaceService` is `get_places(page=1, page_size=250)`).

4. **Off-Grid Custom Venue `"Pin Coordinates"` Button Crash (`REG-04`)**:
   - `custom_builder_view.py:1554` mutates `coords_toggle_btn.text = ...` on an `ft.TextButton`. In Flet 1.1.2, `ft.TextButton` uses `content=ft.Text(...)`, not `.text`.

---

### 2.2 What Happens When Clicking `"✨ Start Trip Here"` After Clicking a POI on the Map

Tracing `"✨ Start Trip Here"` from a Map POI across **Desktop**, **Web**, and **Backend** revealed **4 broken links in the chain**:

1. **Link 1 — Backend `POST /api/v1/itineraries/suggest` Completely Ignores `anchor_place_id` (`REG-06`)**:
   - In `backend/app/schemas/itinerary.py:314–320`, `SuggestedItineraryRequest` defines `anchor_place_id: uuid.UUID | None = None`, and its `@field_validator("anchor_place_id", mode="before")` silently converts any non-UUID string (such as `"dest-minalungao"`, `"curated/..."`, or `"osm-node-..."`) into `None`!
   - Even worse, in `backend/app/algorithms/itinerary_generator.py`, `generate_suggested_itinerary_data()` **never references `request.anchor_place_id` or `request.anchor_place_payload` anywhere in the file**!
   - Result: Whenever the backend is online, clicking `"Start Trip Here"` on **both Web and Desktop** generates a generic municipality itinerary and **never locks the clicked POI as Stop 1 of Day 1**!

2. **Link 2 — Resort / Hotel / Swimming POIs Are Dropped or Moved to the End of the Day (`REG-07`)**:
   - If the user clicks a resort or hotel POI on the map (e.g., *Highland Bali Villas Resort and Spa*, *Lake Farm De La Marre*, *La Casa Prime Cabins*, or any `resort_swimming` / `hotel_accommodation` venue) and clicks `"Start Trip Here"`:
     - On **Web** (`Project/src/app/core/services/itinerary.service.ts:1082–1086`), if the user selects a 1-day trip (`isSingleDay`), `if (!isSingleDay || !this.isAccommodationPlace(anchorPlace))` evaluates to `false` and **completely drops the clicked anchor place**! And on a multi-day trip, line 1148 (`const accommodations = dayPlaces.filter((p) => this.isAccommodationPlace(p));`) **moves the anchor place from Stop 1 to the last stop of the day**!
     - On **Desktop** (`desktop_client/services/itinerary_service.py:387`), `lodging = [p for p in day_places if is_lodging(...)]` also **moves the anchor place from Stop 1 to the end of the day**!

3. **Link 3 — POIs Without `municipality_name` or From Merged API / Live OSM Cache Fail to Match (`REG-07`)**:
   - On **Web** (`Project/src/app/tabs/map/map.page.ts:990`), `startTripHere(place)` sets `destination: place.municipality_name || place.name`. When an OSM POI has no `municipality_name`, `destination` is set to the **venue's name** (e.g., `"Minalungao National Park"`), which causes the municipality filter in `itinerary.service.ts:980` (`(p.municipality_name || '').toLowerCase().includes(targetMuniLower)`) to match 0 places!
   - On **Desktop** (`desktop_client/services/itinerary_service.py:224–236`), `generate_offline_suggested_itinerary()` builds `curated_pool` only from `CANONICAL_OFFLINE_PLACES` and `get_all_offline_places()`, ignoring `get_place_service().get_loaded_places()` (which holds backend-merged UUIDs and Live OSM POIs). And `SuggestedWizardView` (`suggested_wizard_view.py:106–110`) neither resolves `anchor_place` from `anchor_place_id` nor displays an anchor badge on the form.

4. **Link 4 — Clicking `"✓ Accept & Save Itinerary"` on Desktop After `"Start Trip Here"` Crashes (`REG-05`)**:
   - In `desktop_client/views/suggested_wizard_view.py:1302–1338`, `_save_generated_itinerary()` crashes with `AttributeError: 'ItineraryItem' object has no attribute 'start_time'` (and if `TripDetailView` opens, it hits `REG-02` `itm.estimated_cost`).

---

### 2.3 What Happens to Both the Desktop App and the Web App When You Enable Dark Mode

#### A. Desktop App Dark Mode Behavior (`REG-08` & `REG-09`)
1. **Immediate `AttributeError` Crash on Toggle (`desktop_client/main.py:115–122`)**:
   - When you open `Profile -> Settings` and click the **App Appearance (`Light` / `Dark`)** row, `ProfileView._toggle_theme()` calls `main.py:toggle_theme()`:
     ```python
     settings.set_dark_mode(new_is_dark)          # CRASH 1: Settings has no set_dark_mode()
     palette = settings.palette                   # CRASH 2: Settings has no .palette property
     page.bgcolor = palette.bg_primary            # CRASH 3: ThemePalette has .bg_main, NOT .bg_primary
     bottom_tab_bar.refresh_theme()               # CRASH 4: BottomTabBar has no .refresh_theme()
     ```
   - Because line 115 throws `AttributeError: 'Settings' object has no attribute 'set_dark_mode'` *before* `page.theme_mode` is even updated, clicking the Dark Mode toggle on Desktop **completely fails and throws an unhandled exception**!
   - Furthermore, resizing the Desktop window triggers `_on_page_resize` (`main.py:389–392`), which calls `settings.palette` and `palette.bg_primary`, crashing on every window resize!
2. **White-on-White Text Inversions When `ft.ThemeMode.DARK` Is Active (`REG-09`)**:
   - Only `WelcomeView`, `GuestView`, `BottomTabBar`, and `WorkflowHeader` use `ThemePalette`.
   - The other 9 views/dialogs (`DashboardView`, `PlacesView`, `CustomBuilderView`, `SuggestedWizardView`, `SavedTripsView`, `TripDetailView`, `ProfileView`, `LoginView`, `SignupView`, and `dialogs.py`) hardcode `ThemeColors.BG_LIGHT` (`#f8fafc`) and `ft.Colors.WHITE` (`#ffffff`) on cards while leaving dozens of `ft.Text(...)` and `ft.TextField(...)` controls without an explicit `color=`. When Flet switches to `ft.ThemeMode.DARK`, those uncolored texts automatically turn white (`#f8fafc`) on top of hardcoded white (`#ffffff`) cards!

#### B. Web App Dark Mode Behavior (`REG-10`)
1. **Why Dark Mode Breaks Visually Across Web Pages (`Project/src/global.scss:3323–3580`)**:
   - When you toggle Dark Mode in `Profile -> App Settings`, `profile.page.ts:721` adds `.dark` to `document.body` and `document.documentElement`.
   - `Project/src/global.scss:3330` applies `--background: #0b1120 !important; background: #0b1120 !important; color: #f1f5f9 !important` to `ion-content`.
   - **However**, the component stylesheets hardcode `#000000` / `#0f172a` text colors and `#ffffff` / `#f8fafc` card backgrounds, and `global.scss` **used the wrong CSS class names** or omitted the selectors for:
     - **Home (`home.page.scss`)**: `.section-heading` (`"Your Saved Itineraries"`, `"Popular in Nueva Ecija"`), `.dest-title`, and `.custom-card .card-heading` are hardcoded `color: #000000` — rendering **pitch-black text on a `#0b1120` dark navy background**! Also `.search-input` is `color: #0f172a` (`global.scss` targeted `.search-native-input` instead of `.search-input`), and `.result-card` / `.empty-itinerary-card` remain bright white.
     - **Saved Trips (`history.page.scss`)**: `.saved-trips-headline` (`color: #000000`) and `.saved-trips-subheadline` (`color: #1e293b`) sit directly on the `#0b1120` dark background (unreadable!). The trip cards use `.history-itinerary-card` (`background: #fff; color: #000`), whereas `global.scss:3359` targeted `.itinerary-card`! And `.history-toolbar`, `.history-filter-header`, `.search-input-pill`, and `.segment-pill` remain glaring white.
     - **Suggested Wizard (`suggested-wizard.page.scss`), Custom Builder (`custom-builder.page.scss`), & Itinerary Detail (`itinerary-detail.page.scss`)**:
       - `global.scss:3338` targeted `.custom-builder-content`, `.suggested-wizard-content`, and `.itinerary-detail-content`, whereas the actual classes in the templates are `.builder-content`, `.wizard-content`, and `.detail-content`!
       - `.main-heading` (`"Tell us your travel details"`), `.group-label` (`"Destination"`, `"Travel Dates"`, `"Daily Budget"`, `"Preferences"`), `.browse-main-heading`, `.day-bold-heading`, and `.day-italic-sub` have hardcoded `color: #0f172a` on the `#0b1120` dark background (completely invisible!).
       - `.figma-header-bar`, `.figma-input-box`, `.figma-pref-pill`, `.figma-trip-card`, `.figma-stop-card`, `.figma-day-capsule-bar`, `.figma-nearby-card`, `.view-mode-bar`, `.place-browser-card`, `.trip-settings-card`, `.settings-input` (`background-color: #ffffff !important; color: #0f172a !important`), `.active-day-timeline-card`, `.detail-toolbar`, `.trip-details-card`, `.day-selector-pill`, `.timeline-stop-card`, `.expenses-summary-card`, and `.date-picker-modal-card` have no dark mode overrides in `global.scss`!
     - **Map (`map.page.scss`), `PlaceDetailSheet` (`place-detail-sheet.component.scss`), & `DestinationAutocomplete` (`destination-autocomplete.component.scss`)**:
       - `global.scss:3366` targeted `.place-detail-sheet`, whereas `place-detail-sheet.component.html` uses `.detail-sheet-card`!
       - `.poi-list-drawer`, `.drawer-place-card`, `.map-filter-modal .filter-modal-wrap`, `.floating-search-bar`, `.category-chip`, `.autocomplete-input-box`, `.suggestions-dropdown`, and `.regional-explorer-modal` lack dark mode rules in `global.scss`.
     - **Auth Pages (`welcome.page.scss`, `guest.page.scss`, `login.page.scss`, `signup.page.scss`)**:
       - When a user enables Dark Mode and logs out to `/welcome?loggedOut=true` (or visits `/login`, `/signup`, `/guest`), `ion-content` is forced to `#0b1120 !important` by `global.scss:3330`, while `.welcome-container`, `.login-container`, `.signup-container`, and `.guest-container` have hardcoded white backgrounds or black text (`#000000` / `#0f172a`).

---

## 3. Phased File-by-File Implementation Plan for Antigravity

Apply Phases 1 through 5 in order to resolve all 16 regressions (`REG-01` through `REG-16`) and achieve 100% functional, sync, and Dark Mode parity.

### Phase 1: Fix Desktop Startup Crashes, ThemePalette Engine & Cloud Failover (`REG-01`, `REG-08`, `REG-11`, `REG-12`)

#### 1.1 `desktop_client/config/settings.py`
1. At the top of `desktop_client/config/settings.py` (`line 15`), add `from typing import Any, Optional`:
   ```python
   import os
   from pathlib import Path
   import sys
   from dataclasses import dataclass, field
   from typing import Any, Optional
   ```
2. On `ThemeColors` (`line 78`), add `TEXT_PRIMARY_LIGHT: str = "#0f172a"` as an alias alongside `TEXT_MAIN_LIGHT: str = "#0f172a"` so `profile_view.py:1219` (`ThemeColors.TEXT_PRIMARY_LIGHT`) never raises `AttributeError` (`REG-11`).
3. On `Settings` (`line 175`), add `_is_dark_mode: bool = False`, `set_dark_mode(self, is_dark: bool) -> None`, and `@property def palette(self) -> "ThemePalette"`, and on `ThemePalette` (`line 280`), add `@property def bg_primary(self) -> str: return self.bg_main` so `main.py` and all views can access `settings.set_dark_mode(...)`, `settings.palette`, `palette.bg_primary`, and `palette.bg_main` interchangeably (`REG-08`):
   ```python
   # Inside class Settings:
   _is_dark_mode: bool = field(default=False, init=False)

   @property
   def is_dark_mode(self) -> bool:
       return self._is_dark_mode

   def set_dark_mode(self, is_dark: bool) -> None:
       object.__setattr__(self, "_is_dark_mode", bool(is_dark))

   @property
   def palette(self) -> "ThemePalette":
       return ThemePalette.get_palette(self._is_dark_mode)
   ```
   And inside `class ThemePalette`:
   ```python
   @property
   def bg_primary(self) -> str:
       return self.bg_main
   ```
4. Remove the duplicate standalone `resolve_avatar_path(avatar_url: Optional[str])` at `settings.py:390` (or keep a single module-level wrapper that delegates to `get_settings().resolve_avatar_path(avatar_url)`).

#### 1.2 `desktop_client/components/bottom_tab_bar.py`
Add `refresh_theme(self) -> None` to `BottomTabBar` (`line 110`) so `bottom_tab_bar.refresh_theme()` in `main.py:122` succeeds (`REG-08`):
```python
    def refresh_theme(self) -> None:
        """Rebuilds bottom tab bar colors for active Light/Dark theme."""
        self._build_content()
        try:
            self.update()
        except Exception:
            pass
```
Also in `BottomTabBar._build_content()` (`line 125`), use `palette.text_muted` instead of hardcoded `ThemeColors.TEXT_MUTED_LIGHT` for inactive tab icons/labels.

#### 1.3 `desktop_client/main.py`
At line 15 of `desktop_client/main.py`, import `Any` alongside `Optional` (`REG-01`):
```python
from typing import Any, Optional
```

#### 1.4 `desktop_client/core/api_client.py`
Fix the broken localhost -> Cloudflare Worker failover (`REG-12`):
1. At the top of `desktop_client/core/api_client.py`, add:
   ```python
   import logging
   logger = logging.getLogger(__name__)
   ```
2. Add `def set_base_url(self, val: str) -> None:` on `ApiClient` (alongside the `@base_url.setter`):
   ```python
   def set_base_url(self, val: str) -> None:
       self._explicit_base_url = val.rstrip("/") if val else None
   ```

---

### Phase 2: Fix Custom Itinerary Creation, Back-Button Loop & Post-Save Crash (`REG-02`, `REG-03`, `REG-04`, `REG-13`)

#### 2.1 `desktop_client/views/trip_detail_view.py`
1. **Fix the `itm.estimated_cost` Crash (`line 390–395`, `REG-02`)**:
   Replace `float(itm.estimated_cost or 0.0)` with `float(itm.representative_cost)`:
   ```python
   # Estimated activity expenses footer card
   total_activity_expenses = sum(
       float(itm.representative_cost)
       for d in itin.days
       for itm in d.items
   )
   ```
2. **Fix `_add_nearby_to_active_day()` (`lines 467–484`, `REG-13`)**:
   Construct `ItineraryItem` with its actual dataclass fields (`id`, `day_id`, `sort_order`, `place_id`, `place`, `custom_title`, `custom_lat`, `custom_lng`, `planned_time`, `duration_minutes`, `estimated_cost_min`, `estimated_cost_max`) and remove the illegal assignment to the read-only property `self.itinerary.total_stops`:
   ```python
   def _add_nearby_to_active_day(self, place: Place) -> None:
       active_day = self.itinerary.days[self.active_day_index] if self.itinerary.days else None
       if not active_day:
           return
       new_stop = ItineraryItem(
           id=str(uuid.uuid4()),
           day_id=active_day.id,
           sort_order=len(active_day.items) + 1,
           place_id=place.id,
           place=place,
           custom_title=place.name,
           custom_lat=place.latitude,
           custom_lng=place.longitude,
           planned_time="02:00 PM",
           duration_minutes=60,
           estimated_cost_min=place.estimated_cost_min,
           estimated_cost_max=place.estimated_cost_max,
           travel_mode_from_prev="DRIVE",
       )
       active_day.items.append(new_stop)
       self.is_dirty = True
       if self.safe_page:
           show_toast(self.safe_page, f"Added {place.name} to Day {active_day.day_number}!", bgcolor=ThemeColors.SUCCESS)
       self._close_nearby_view()
   ```

#### 2.2 `desktop_client/views/custom_builder_view.py`
1. **Fix `did_mount()` (`lines 128–135`, `REG-04`)**:
   Replace `await self.place_service.list_places()` with `await self.place_service.get_places(page=1, page_size=250)`.
2. **Fix `handle_back()` (`lines 138–167`, `REG-03`)** so internal step transitions (`browse` -> `timeline` -> `form`) NEVER trigger the `"Discard Changes?"` exit dialog—only prompt when actually leaving `CustomBuilderView`:
   ```python
   def handle_back(self) -> bool:
       """Handles back button stepping through state machine with unsaved changes guard (UC-C14)."""
       if self.active_view == "browse":
           self.active_view = "timeline" if self.total_stops_count > 0 else "form"
           self._build_content()
           self._safe_update()
           return True

       if self.active_view == "timeline":
           if self.existing_itinerary is None and not self.is_draft_from_wizard:
               self.active_view = "form"
               self._build_content()
               self._safe_update()
               return True
           if self.is_dirty:
               self._prompt_discard_changes()
               return True
           self._navigate("/home")
           return True

       if self.active_view == "form":
           if self.is_dirty:
               self._prompt_discard_changes()
               return True
           if self.on_back:
               self.on_back()
           else:
               self._navigate("/home")
           return True

       return False
   ```
3. **Fix Off-Grid Venue `"Pin Coordinates"` Toggle (`lines 1551–1558`, `REG-04`)**:
   Use `coords_toggle_btn.content = ft.Text(...)` instead of `coords_toggle_btn.text = ...`:
   ```python
   def _toggle_coords(_):
       coords_expanded[0] = not coords_expanded[0]
       coords_col.visible = coords_expanded[0]
       coords_toggle_btn.content = ft.Text(
           "Hide Coordinates ▲" if coords_expanded[0] else "Pin Coordinates (Lat / Lng) — Optional ▼",
           size=12,
           color=ThemeColors.PRIMARY_BLUE,
           weight=ft.FontWeight.W_600,
       )
       _update_dlg_content()

   coords_toggle_btn = ft.TextButton(
       content=ft.Text("Pin Coordinates (Lat / Lng) — Optional ▼", size=12, color=ThemeColors.PRIMARY_BLUE, weight=ft.FontWeight.W_600),
       on_click=_toggle_coords,
   )
   ```

---

### Phase 3: Fix `"✨ Start Trip Here"` End-to-End Across Map, Wizard, Services & Backend (`REG-05`, `REG-06`, `REG-07`)

#### 3.1 `desktop_client/views/suggested_wizard_view.py`
1. **Resolve `self.anchor_place` & Municipality on Init (`lines 106–115`, `REG-07`)**:
   When `anchor_place_id` is passed (e.g. from `"✨ Start Trip Here"` on the Map), look up the `Place` from `self.place_service.get_loaded_places()`:
   ```python
   self.anchor_place_id = anchor_place_id
   self.anchor_place: Optional[Place] = anchor_place
   if self.anchor_place_id and not self.anchor_place:
       for p in self.place_service.get_loaded_places():
           if str(p.id) == str(self.anchor_place_id):
               self.anchor_place = p
               break
   if self.anchor_place and self.anchor_place.municipality_name and (
       not initial_destination or initial_destination == "Nueva Ecija"
   ):
       self.destination_val = self.anchor_place.municipality_name
   ```
2. **Display an Anchor POI Banner in `_build_wizard_form()`** when `self.anchor_place` is set so the user sees `"✨ Starting Trip at {self.anchor_place.name} (Stop 1, Day 1)"`.
3. **Pass `anchor_place_payload` in `_start_generation()` (`lines 606–618`)**:
   Pass `anchor_place_payload=self.anchor_place.to_dict() if self.anchor_place else None` on `SuggestedItineraryRequest`.
4. **Fix `_save_generated_itinerary()` Crash (`lines 1294–1348`, `REG-05`)**:
   Replace the broken manual dictionary loop (which accessed non-existent `item.start_time`, `item.estimated_cost`, `d.date`, `d.theme`, `self.generated_itinerary.description`, `self.generated_itinerary.total_budget`) with `self.generated_itinerary.to_create_payload()`:
   ```python
   def _save_generated_itinerary(self) -> None:
       if not self.generated_itinerary:
           return

       async def _run():
           try:
               self.generated_itinerary.type = "suggested"
               payload = self.generated_itinerary.to_create_payload()
               saved = await self.itinerary_service.create_itinerary(payload)
               self.itinerary_service.clear_active_draft_itinerary()
               if self.safe_page:
                   show_toast(self.safe_page, "Itinerary saved to your trips!", bgcolor=ThemeColors.SUCCESS)
               if self.on_navigate:
                   self.on_navigate(f"/trips/{saved.id}", saved)
           except Exception as e:
               if self.safe_page:
                   show_toast(self.safe_page, f"Failed to save itinerary: {e}", is_error=True)

       if self.safe_page:
           self.safe_page.run_task(_run)
   ```

#### 3.2 `backend/app/schemas/itinerary.py` & `backend/app/algorithms/itinerary_generator.py` (`REG-06`)
1. In `backend/app/schemas/itinerary.py` (`lines 311–325`), update `SuggestedItineraryRequest` so non-UUID `anchor_place_id` strings (like `"dest-minalungao"` or `"osm-node-123"`) are preserved inside `anchor_place_payload`:
   ```python
   anchor_place_id: uuid.UUID | None = None
   anchor_place_payload: dict | None = None

   @model_validator(mode="before")
   @classmethod
   def normalize_anchor_place(cls, data: Any) -> Any:
       if not isinstance(data, dict):
           return data
       out = dict(data)
       raw_aid = out.get("anchor_place_id")
       if raw_aid is not None and raw_aid != "":
           parsed = _safe_parse_uuid(raw_aid)
           if parsed is None:
               payload = dict(out.get("anchor_place_payload") or {})
               if not payload.get("id"):
                   payload["id"] = str(raw_aid)
               out["anchor_place_payload"] = payload
           out["anchor_place_id"] = parsed
       return out
   ```
2. In `backend/app/algorithms/itinerary_generator.py` (`generate_suggested_itinerary_data`), resolve `anchor_place: Place | None` before the day loop:
   - Check `db.get(Place, request.anchor_place_id)` if `request.anchor_place_id` is set.
   - Else if `request.anchor_place_payload` is set, match by `source_record_id`, `id`, or `name`, or upsert via `google_maps_service.upsert_google_place_to_db(db, request.anchor_place_payload)`.
   - If `anchor_place` is found:
     - Override `(anchor_lat, anchor_lng)` with `(anchor_place.latitude, anchor_place.longitude)` so Day 1 clusters around the clicked POI.
     - On `day_idx == 0` (`slot_idx == 0`), lock `chosen_place = anchor_place` directly as Stop 1 of Day 1!
     - During the 2-Opt permutation step on `day_idx == 0`, keep `day_items[0]` (`anchor_place`) pinned at index 0 (even if `is_accommodation_place(anchor_place)` is `True`) and only permute `day_items[1:]`!

#### 3.3 `desktop_client/services/itinerary_service.py` & `Project/src/app/core/services/itinerary.service.ts` & `Project/src/app/tabs/map/map.page.ts` (`REG-07`)
1. **In `desktop_client/services/itinerary_service.py` (`lines 224–236, 319–323, 387–405`)**:
   - Merge `get_place_service().get_loaded_places()` into `curated_pool` so any POI clicked on the map is found by `request.anchor_place_id` (or `request.anchor_place_payload`).
   - On `d_idx == 0` when `request.anchor_place_id` matched, pin `day_places[0]` at index 0 during the 2-Opt sort (`line 387`) even if `is_lodging(...)` is `True`!
2. **In `Project/src/app/tabs/map/map.page.ts` (`line 987`)**:
   - In `startTripHere(place: Place)`, set `destination: place.municipality_name || 'Nueva Ecija'` instead of `place.municipality_name || place.name` so a missing `municipality_name` never passes a venue name as a municipality filter!
3. **In `Project/src/app/core/services/itinerary.service.ts` (`lines 1082–1086, 1147–1155`)**:
   - On `d === 0 && anchorPlace`, always push `anchorPlace` to `dayPlaces` (removing the `if (!isSingleDay || !this.isAccommodationPlace(anchorPlace))` exclusion that dropped resort/hotel anchors on 1-day trips!), and exclude `anchorPlace` from `accommodations` on Day 1 so it stays locked as Stop 1 of Day 1!

---

### Phase 4: Fix Dark Mode Across Both Desktop and Web (`REG-08`, `REG-09`, `REG-10`)

#### 4.1 Desktop Dark Mode (`desktop_client/`)
1. With Phase 1.1–1.3 in place, `toggle_theme()` in `main.py` and `_on_page_resize()` will no longer crash with `AttributeError`.
2. In `desktop_client/main.py` (`line 72`), configure `page.theme` and `page.dark_theme` with explicit color schemes so Flet controls render consistent readable text and surface colors in both modes, and in `ProfileView`, `DashboardView`, `SavedTripsView`, `CustomBuilderView`, `SuggestedWizardView`, `TripDetailView`, `PlacesView`, `LoginView`, `SignupView`, and `dialogs.py`, bind container backgrounds and text colors to `self.settings.palette` (`palette.bg_main`, `palette.surface_card`, `palette.border_main`, `palette.text_primary`, `palette.text_muted`) instead of hardcoded `ThemeColors.BG_LIGHT` / `ft.Colors.WHITE` / `ThemeColors.TEXT_BLACK`.

#### 4.2 Web Dark Mode (`Project/src/global.scss`)
Append comprehensive dark-mode rules inside `html.dark, body.dark { ... }` in `Project/src/global.scss` (`line 3323`) covering all actual component class names across Home, Saved Trips, Map, Place Detail Sheet, Destination Autocomplete, Suggested Wizard, Custom Builder, Itinerary Detail, and Auth screens:

```scss
html.dark,
body.dark {
  /* Content wrappers using their actual template class names */
  .home-content,
  .history-content,
  .map-content,
  .profile-content,
  .fav-content,
  .wizard-content,
  .builder-content,
  .detail-content,
  .welcome-content,
  .guest-content,
  .login-content,
  .signup-content {
    --background: #0b1120 !important;
    background: #0b1120 !important;
    color: #f1f5f9 !important;
  }

  /* Toolbars & Headers */
  .history-toolbar,
  .builder-toolbar,
  .detail-toolbar,
  .wizard-toolbar,
  .figma-header-bar,
  .history-filter-header,
  .view-mode-bar {
    --background: #0f172a !important;
    --border-color: #1e293b !important;
    background: #0f172a !important;
    border-color: #1e293b !important;
    color: #f8fafc !important;
  }

  /* Headings that were pitch-black #000000 / #0f172a on dark background */
  .header-title,
  .section-heading,
  .dest-title,
  .result-title,
  .itin-title,
  .saved-trips-headline,
  .history-title,
  .builder-title,
  .figma-header-title,
  .main-heading,
  .group-label,
  .browse-main-heading,
  .day-bold-heading,
  .day-headline,
  .trip-destination-title,
  .stop-title-text,
  .card-place-title,
  .stop-name-heading,
  .nearby-card-title,
  .empty-filter-title,
  .empty-state-title,
  .empty-itin-title,
  .sheet-title,
  .drawer-title,
  .drawer-card-name,
  .filter-modal-title,
  .filter-section-title,
  .action-card.custom-card .card-heading {
    color: #f8fafc !important;
  }

  /* Subtitles & Muted Copy */
  .saved-trips-subheadline,
  .itin-destination,
  .itin-dates,
  .day-italic-sub,
  .stop-timing-block,
  .nearby-intro-description,
  .card-place-muni,
  .stop-muni-text,
  .action-card.custom-card .card-copy {
    color: #94a3b8 !important;
  }

  /* Cards, Containers & Sheets */
  .history-itinerary-card,
  .result-card,
  .empty-itinerary-card,
  .figma-trip-card,
  .figma-stop-card,
  .figma-nearby-card,
  .figma-input-box,
  .place-browser-card,
  .trip-settings-card,
  .active-day-timeline-card,
  .places-empty-box,
  .day-empty-stops-box,
  .trip-details-card,
  .timeline-stop-card,
  .expenses-summary-card,
  .detail-sheet-card,
  .poi-bottom-sheet,
  .poi-list-drawer,
  .drawer-place-card,
  .map-filter-modal .filter-modal-wrap,
  .picker-modal-sheet,
  .picker-place-card,
  .date-picker-modal-card,
  .commute-guide-box,
  .autocomplete-input-box,
  .suggestions-dropdown,
  .regional-explorer-modal {
    background: #1e293b !important;
    border-color: #334155 !important;
    color: #f8fafc !important;
  }

  /* Inputs & Search Bars */
  .search-input,
  .history-search-field,
  .search-input-field,
  .core-input,
  .settings-input,
  .modal-input,
  .modal-textarea,
  .picker-search-input,
  .date-picker-trigger-text,
  .autocomplete-native-input {
    background-color: transparent !important;
    color: #f8fafc !important;
  }

  .settings-input,
  .search-input-pill,
  .search-bar-wrap,
  .picker-search-bar {
    background-color: #0f172a !important;
    border-color: #334155 !important;
  }

  .search-icon {
    color: #94a3b8 !important;
  }

  /* Pills, Capsules & Tabs */
  .segment-pill,
  .figma-pref-pill,
  .trip-tag-pill,
  .figma-day-capsule-bar,
  .nearby-category-capsule-bar,
  .timeline-day-tab,
  .target-day-chip,
  .quick-dest-chip,
  .view-mode-tab,
  .days-nights-pill,
  .filter-choice-chip,
  .muni-chip,
  .price-tier-btn {
    background: #0f172a !important;
    border-color: #334155 !important;
    color: #cbd5e1 !important;

    &.active {
      background: #0084ff !important;
      border-color: #0084ff !important;
      color: #ffffff !important;
    }
  }
}
```

---

### Phase 5: Clean Up Dialog Overlay Leaks, Guest Storage Bleed & Scripts (`REG-14`, `REG-15`, `REG-16`)

1. **Dialog Overlay Cleanup (`REG-14`)**:
   - In `desktop_client/views/profile_view.py:1254–1264`, replace `self.page.overlay.append(dlg)` / `dlg.open = False` inside `_show_dialog` and `_close_dialog` with `open_overlay_dialog(self.page, dlg)` and `close_overlay_dialog(self.page, dlg)`.
   - Do the same in `custom_builder_view.py` (`_prompt_discard_changes`, `_delete_active_day`, `_open_date_picker`, `_confirm_remove_stop`, `_open_edit_stop_dialog`, `_open_custom_venue_dialog`) and `main.py:199`.
2. **Prevent Guest Storage Bleed in `SavedTripsView` & `DashboardView` (`REG-15`)**:
   - In `desktop_client/views/saved_trips_view.py:36–40` and `desktop_client/views/dashboard_view.py:49–53`, only pre-populate from `self.itinerary_service.guest_storage.list_itineraries()` when `not get_session_manager().is_authenticated`!
3. **Fix `scripts/run_daemon.py` & `scripts/build_standalone_exe.py` (`REG-16`)**:
   - In `scripts/run_daemon.py:7`, replace `project_root = r"C:\Users\Edward\Desktop\CaseStudy"` with `project_root = str(Path(__file__).resolve().parent.parent)`.
   - In `scripts/build_standalone_exe.py:100–135`, add `--hidden-import` flags for `desktop_client.core.connectivity_service`, `desktop_client.core.offline_data`, `desktop_client.core.polyline`, `desktop_client.core.commute_guide`, `desktop_client.services.favorites_service`, and all `desktop_client.components.*` and `desktop_client.views.*` modules.

---

## 4. Cycle 2 Verification & Regression Test Matrix (`TC-01` to `TC-20`)

| Test ID | Target Area | Steps to Verify | Expected Outcome |
| :--- | :--- | :--- | :--- |
| **TC-01** | Desktop Startup (`REG-01`) | Run `python -m desktop_client.main` or launch `NuevaEcijaTravel.exe`. | Boots cleanly with zero `NameError: name 'Optional' is not defined` or `NameError: name 'Any' is not defined`. |
| **TC-02** | Cloud Failover (`REG-12`) | Stop local port `8000` while Worker tunnel is active, then launch Desktop. | `ApiClient` logs failover with `logger.info`, calls `self.set_base_url(worker_url)`, and connects to `https://ne-itinerary-api.edselrenz0.workers.dev/api/v1` without offline false positives. |
| **TC-03** | Custom Builder Create & Save (`REG-02`) | Create a new Custom Itinerary, add 2 stops, and click `✓ Save` / `💾 View Full Itinerary / Save Trip`. | Saves to cloud/local storage and opens `TripDetailView` (`/trips/{id}`) cleanly **without** throwing `'ItineraryItem' object has no attribute 'estimated_cost'`. |
| **TC-04** | Custom Builder Back Navigation (`REG-03`) | In Custom Builder Step 1 (`form`), select `₱2,500`, click `Start Building Itinerary →`, add 1 stop in `browse`, click `📅 Your Itinerary`, then click `←` in header. | Steps cleanly from `browse` -> `timeline` -> `form` (`View 0`) without popping `"Discard Changes?"`; only prompts `"Discard Changes?"` when clicking `←` from `form` to exit. |
| **TC-05** | Custom Builder Off-Grid Coords (`REG-04`) | In `timeline`, click `🏢 Add Off-Grid Custom Venue` and click `Pin Coordinates (Lat / Lng) — Optional ▼`. | Expands coordinate inputs and updates button text to `Hide Coordinates ▲` without Flet 1.1.2 `.text` errors. |
| **TC-06** | Map `"✨ Start Trip Here"` Online (`REG-06`) | Click any POI on the Map (e.g., *Minalungao National Park* or *Rohi Paperflower Cafe*) and click `✨ Start Trip Here`, then click `Find Itinerary`. | Suggested Wizard pre-fills the POI's municipality, shows the anchor banner, and locks that exact POI as **Stop 1 of Day 1** even when connected to the live FastAPI backend. |
| **TC-07** | Map `"✨ Start Trip Here"` on Resort/Hotel (`REG-07`) | Click a resort/hotel POI on the Map (e.g., *Highland Bali Villas Resort and Spa*), click `✨ Start Trip Here`, and generate a 1-day or 2-day trip. | Keeps the clicked resort/hotel locked as **Stop 1 of Day 1** on both Web and Desktop (not dropped on 1-day trips or moved to the last stop). |
| **TC-08** | Suggested Wizard Save (`REG-05`) | After generating a Suggested Itinerary, click `✓ Accept & Save Itinerary`. | Converts via `to_create_payload()`, saves to cloud/guest storage without `AttributeError: 'ItineraryItem' object has no attribute 'start_time'`, shows toast, and opens `TripDetailView`. |
| **TC-09** | Desktop Dark Mode Toggle (`REG-08`) | Open `Profile -> Settings` on Desktop and click `App Appearance (Light / Dark)`, then resize the window. | Switches between Light and Dark mode while staying inside `Settings` with zero `AttributeError` on `settings.set_dark_mode`, `settings.palette`, `palette.bg_primary`, or `bottom_tab_bar.refresh_theme()`. |
| **TC-10** | Desktop Dark Mode Contrast (`REG-09`) | With Dark Mode enabled on Desktop, navigate through Home, Map, Custom Builder, Suggested Wizard, Saved Trips, Trip Detail, and Profile. | All backgrounds use `#0b0f19`, cards use `#151e2e`, and text uses `#f8fafc` / `#94a3b8` with zero white-on-white invisible text. |
| **TC-11** | Web Dark Mode Contrast (`REG-10`) | Enable Dark Mode in Web `Profile -> App Settings`, then inspect Home, Saved Trips, Map, Place Detail Sheet, Suggested Wizard, Custom Builder, and Itinerary Detail. | All headings (`.section-heading`, `.saved-trips-headline`, `.main-heading`, `.group-label`, `.browse-main-heading`) render in light `#f8fafc` text, and all cards/modals render in `#1e293b` dark slate with zero black-on-dark or white-on-white inversions. |
| **TC-12** | Desktop Logout Modal (`REG-11`) | Click `Log Out` on the Desktop Profile screen. | Opens the Figma-styled Logout modal with `logout_sparkle_accent.png` and `logout_door_icon.png` without throwing `AttributeError: 'ThemeColors' has no attribute 'TEXT_PRIMARY_LIGHT'`. |
| **TC-13** | Trip Detail Add Nearby Stop (`REG-13`) | Open any saved trip in `TripDetailView`, click `Explore Nearby Places`, and click `+` on a restaurant. | Appends the stop to the active day with valid `ItineraryItem` fields and shows a confirmation toast without crashing on `total_stops`. |
| **TC-14** | Authenticated Saved Trips Isolation (`REG-15`) | Create a guest trip, then log into an account on Desktop and view Home & Saved Trips. | Guest trip is migrated to cloud once via `sync_guest_itineraries_to_cloud()`, and unmigrated local guest storage never bleeds into authenticated views. |
| **TC-15** | Portable Daemon & Exe Build (`REG-16`) | Run `python scripts/run_daemon.py` and `python scripts/build_standalone_exe.py`. | `run_daemon.py` resolves `project_root` dynamically and syncs to the Cloudflare Worker; `build_standalone_exe.py` bundles all hidden imports and produces a working `NuevaEcijaTravel.exe`. |
