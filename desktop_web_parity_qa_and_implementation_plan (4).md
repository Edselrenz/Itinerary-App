# Comprehensive QA Audit, 1:1 Web-Desktop Parity Analysis & Antigravity Implementation Plan
**Project:** Nueva Ecija Travel Itinerary App (*"Trip mo, trip ko"*)  
**Audited Commit:** `d81e6b278f6927b48c6d12379c7f3521f87102f1` (`edselrenz/itinerary-app`)  
**Reference Web Deployment:** [Trip mo, trip ko Live Web App](https://www.google.com/search?q=https://edselrenz.github.io/Itinerary-App/) ([Welcome Route](https://www.google.com/search?q=https://edselrenz.github.io/Itinerary-App/%23/welcome))  
**Cloudflare Worker API Proxy:** [NE Itinerary API Worker](https://www.google.com/search?q=https%3A%2F%2Fwww.google.com%2Furl%3Fsa%3DE%26source%3Dgmail%26q%3Dhttps%3A%2F%2Fne-itinerary-api.edselrenz0.workers.dev%2Fapi%2Fv1) ([Tunnel Status Endpoint](https://www.google.com/search?q=https://ne-itinerary-api.edselrenz0.workers.dev/__status))  
**Permanent Ngrok Fallback:** [Ngrok Tunnel Endpoint](https://www.google.com/search?q=https://anybody-cube-surprise.ngrok-free.dev)

---

## 1. Executive Summary & Complete Defect Matrix

A full-stack static and lifecycle audit of the **Web Application** (`Project/src/app/`, Ionic 8 + Angular 20), **Desktop Application** (`desktop_client/`, Python Flet 1.1.2), **Backend API** (`backend/app/`, FastAPI + SQLAlchemy Async), and **Edge Proxy** (`cloudflare-worker/worker.js` + `scripts/run_daemon.py`) uncovered **24 root-cause defects** across your four QA focus areas:

1. **Close / Back Button Loops & Window/Tab Lifecycle Bugs (6 Critical/High Defects)**: Stale `selected_trip` state in `main.py` permanently traps `CustomBuilderView` and `TripDetailView` into reopening the previously viewed itinerary; `CustomBuilderView.handle_back()` loops infinitely between `browse` and `timeline` whenever `total_stops_count > 0`; `BottomTabBar` destroys active `followRoute` navigation when clicking the Map tab; `DestinationPicker`'s `×` close button selects a destination instead of canceling; `DestinationPicker`'s autocomplete dropdown never closes on outside click; and toggling Dark Mode inside `Profile -> Settings` resets `ProfileView` back to the root Profile screen.
2. **Missing Visual Feedback & Input Focus Defects (5 Critical/High Defects)**: Every `SnackBar` toast across the entire Desktop app uses the removed Flet 0.x `page.snack_bar = ft.SnackBar(...)` API, resulting in **zero visual feedback** on saves, errors, cache clears, and connection retries; typing a single character in `CustomBuilderView` search, `SavedTripsView` search, or `DestinationPicker` rebuilds the `TextField` and drops cursor focus; Login/Signup buttons have no loading spinner or disabled state during network calls; and clicking budget preset chips in Custom Builder Form (`View 0`) fails to update chip highlight state.
3. **Cross-App Account & Saved Itinerary Synchronization Failures (7 Critical/High Defects)**: Clicking **"Find Itinerary"** in Desktop `SuggestedWizardView` crashes with `TypeError` (passing 9 keyword arguments to `generate_suggested_itinerary(request: SuggestedItineraryRequest)`); clicking **"✓ Accept & Save Itinerary"** in Desktop `SuggestedWizardView` sends an `Itinerary` object instead of `ItineraryCreatePayload` (failing FastAPI `place_id` UUID validation with `HTTP 422` and crashing the local fallback with `AttributeError: 'ItineraryDay' object has no attribute 'get'`); FastAPI `ItineraryItemBase` rejects non-UUID curated/OSM `place_id` strings (`"dest-..."`, `"osm-..."`) from **both Web and Desktop** with `HTTP 422`; Desktop `list_itineraries()` mixes local `guest_storage.json` trips into authenticated cloud accounts; Desktop defaults to `127.0.0.1:8000` without immediate request-level failover to [NE Itinerary API Worker](https://www.google.com/search?q=https%3A%2F%2Fwww.google.com%2Furl%3Fsa%3DE%26source%3Dgmail%26q%3Dhttps%3A%2F%2Fne-itinerary-api.edselrenz0.workers.dev%2Fapi%2Fv1); `scripts/run_daemon.py` never calls `POST /__sync_tunnel` on the Cloudflare Worker; and Web `signup.page.ts` concatenates `middleInitial` into `first_name` instead of sending `middle_initial`.
4. **1:1 Functional Parity Violations — Extra Desktop Features & Missing Web Features (6 High/Medium Defects)**: Desktop `TripDetailView` adds extra buttons (`"🛠️ Open in Full Builder"`, `"Export Dossier"`, and a dark-navy `"Local Guest Storage"` card) that do not exist on Web while omitting Web's **Explore Nearby Places** view, **In-App Nav / Google Maps** day header actions, and **Estimated activity expenses** footer; Desktop `LoginView` omits **Explore Demo Account (Pattranite Persona)** and **Continue with Google / Apple**; Desktop `SignupView` omits **Continue with Google / Apple** and uses a side-by-side `M.I.` box instead of Web's vertical stack; Desktop `WelcomeView` shows `logout_skyscrapers_blob.png` on the standard Welcome screen (Web only shows it on the After-Logout screen); Desktop `ProfileView -> Favorites` omits the search bar, category filter scroller, and `Directions` button; and clicking `+ Add to Trip` in `PlacesView` passes `place` as the 2nd positional argument (`trip_data`) to `navigate_to("/builder", place)`, crashing `CustomBuilderView`.

| ID | Category | Severity | Component / File | Summary of Defect |
| :--- | :--- | :--- | :--- | :--- |
| **BUG-01** | Close/Back Loop | **P0 Critical** | `desktop_client/main.py:160, 211–228` | `selected_trip` is never reset to `None` when navigating to `/home`, `/saved`, `/builder`, or `/trips/{new_id}`. Opening Custom Builder or saving a new trip reopens the old saved trip. |
| **BUG-02** | Close/Back Loop | **P0 Critical** | `desktop_client/views/custom_builder_view.py:130–145` | `handle_back()` in `browse` routes to `timeline` whenever `total_stops_count > 0`, trapping users in a `browse <-> timeline` loop and preventing return to `form` (`View 0`) or exit. |
| **BUG-03** | Close/Back Loop | **P1 High** | `desktop_client/components/dialogs.py` & `destination_picker.py:415` | Mixing `page.show_dialog()` / `page.pop_dialog()` with unremoved `page.overlay.append(dlg)` corrupts Flet's dialog stack; Regional Explorer `×` button calls `pick_and_close(self.selected_destination)` instead of canceling. |
| **BUG-04** | Close/Back Loop | **P1 High** | `desktop_client/components/destination_picker.py:67, 257–265` | Floating autocomplete suggestion panel has no close button or blur handler and remains stuck open when clicking outside. |
| **BUG-05** | Close/Back Loop | **P1 High** | `desktop_client/components/bottom_tab_bar.py:93–99` & `places_view.py:725` | Clicking active Map tab calls `on_map_tap_when_active()` AND `on_navigate("/map")`, destroying active `followRoute` navigation; `TripDetailView` back button always routes to `/saved` even when entered from `/home`. |
| **BUG-06** | Close/Back Loop | **P1 High** | `desktop_client/main.py:101–108` & `views/profile_view.py:678` | Toggling Dark Mode in `Profile -> Settings` calls `navigate_to("/profile", force=True)`, destroying `ProfileView` state and kicking user out of `Settings` back to root `Profile`. |
| **BUG-07** | Visual Feedback | **P0 Critical** | All Desktop Views (`custom_builder_view.py`, `suggested_wizard_view.py`, `profile_view.py`, `places_view.py`, `offline_banner.py`) | Uses deprecated Flet 0.x `self.safe_page.snack_bar = ft.SnackBar(...)` instead of Flet 1.1.2 `self.safe_page.show_dialog(ft.SnackBar(...))`. Zero toast notifications ever appear. |
| **BUG-08** | Visual Feedback | **P0 Critical** | `custom_builder_view.py:487`, `saved_trips_view.py:337`, `destination_picker.py:263` | Live search `on_change` handlers call `self._build_content()`, recreating the `ft.TextField` instance on every character typed and stealing cursor focus. |
| **BUG-09** | Visual Feedback | **P1 High** | `desktop_client/views/login_view.py:216` & `signup_view.py:306` | Login and Sign Up submit buttons lack loading spinner / disabled state during async API requests (unlike Web's `<ion-spinner name="crescent">`). |
| **BUG-10** | Visual Feedback | **P2 Medium** | `desktop_client/views/custom_builder_view.py:886–890` | `_set_budget_preset()` updates `self.daily_budget` without rebuilding the preset chip row, so clicked budget chips (`₱1,500`–`₱6,000`) never highlight. |
| **BUG-11** | Visual Feedback | **P2 Medium** | All Desktop Views (`theme_Preference` / `ThemePalette`) | Dark mode only changes `page.bgcolor` and `BottomTabBar`; all views hardcode `ThemeColors.BG_LIGHT` and `SURFACE_LIGHT`. |
| **BUG-12** | Cross-App Sync | **P0 Critical** | `desktop_client/views/suggested_wizard_view.py:463–473` | `_start_generation()` calls `generate_suggested_itinerary(destination=..., ...)` with 9 kwargs, but `ItineraryService.generate_suggested_itinerary(self, request: SuggestedItineraryRequest)` takes 1 positional dataclass. Crashes 100% of the time with `TypeError`. |
| **BUG-13** | Cross-App Sync | **P0 Critical** | `desktop_client/views/suggested_wizard_view.py:875` & `services/itinerary_service.py:422–439` | `_save_generated_itinerary()` passes an `Itinerary` object instead of `ItineraryCreatePayload`. Cloud `POST /itineraries` fails with `HTTP 422`, and the local fallback crashes with `AttributeError: 'ItineraryDay' object has no attribute 'get'`. |
| **BUG-14** | Cross-App Sync | **P0 Critical** | `backend/app/schemas/itinerary.py:14, 33` & `services/itinerary_service.py` | FastAPI `ItineraryItemBase.place_id: uuid.UUID | None` rejects curated/OSM string IDs (`"dest-minalungao"`, `"osm-node-..."`) with `HTTP 422` across both Web and Desktop, and ignores Web's `place` dict when `place_payload` is unset. |
| **BUG-15** | Cross-App Sync | **P1 High** | `desktop_client/services/itinerary_service.py:390–408` | `list_itineraries()` unconditionally appends `self.guest_storage.list_itineraries()` even when `is_authenticated == True`, contaminating cloud accounts with local guest trips. |
| **BUG-16** | Cross-App Sync | **P1 High** | `desktop_client/config/settings.py:157` & `core/api_client.py:113–170` | Desktop defaults to `http://127.0.0.1:8000/api/v1` and marks host offline on initial `ConnectError` before `ConnectivityService` fails over to [NE Itinerary API Worker](https://www.google.com/search?q=https%3A%2F%2Fwww.google.com%2Furl%3Fsa%3DE%26source%3Dgmail%26q%3Dhttps%3A%2F%2Fne-itinerary-api.edselrenz0.workers.dev%2Fapi%2Fv1). |
| **BUG-17** | Cross-App Sync | **P1 High** | `scripts/run_daemon.py:55–66` | `run_daemon.py` writes `CLOUDFLARE_URL` to `scratch/active_tunnel.txt` but never calls `POST https://ne-itinerary-api.edselrenz0.workers.dev/__sync_tunnel` to update the Worker KV store. |
| **BUG-18** | Cross-App Sync | **P2 Medium** | `Project/src/app/features/auth/signup/signup.page.ts:165` | Web signup concatenates `middleInitial` into `first_name` instead of passing `middle_initial` to `POST /api/v1/auth/register`. |
| **BUG-19** | Parity (Crash) | **P0 Critical** | `desktop_client/views/places_view.py:611` & `main.py:110` | `_prompt_add_place_to_trip` calls `self.on_navigate("/builder", place)`, binding `place` to `trip_data` (`existing_itinerary`) instead of `pre_added_place`. Crashes `CustomBuilderView.__init__` with `AttributeError: 'Place' object has no attribute 'title'`. |
| **BUG-20** | Parity (Extra UI) | **P1 High** | `desktop_client/views/trip_detail_view.py:66–145` | Desktop adds extra buttons (`"🛠️ Open in Full Builder"`, `"Export Dossier"`, dark-navy `"Local Guest Storage"` card) not in Web, while missing Web's **Explore Nearby Places** view, **In-App Nav / Google Maps** buttons, **Copy Text Summary**, and **Estimated activity expenses** footer. |
| **BUG-21** | Parity (Extra/Wrong Tab) | **P1 High** | `desktop_client/views/custom_builder_view.py:548, 595–798` | Clicking `"🏢 Add Off-Grid Custom Venue"` opens the modal on `"browse"` (`🔍 Browse Places`) instead of `"custom"` (`🏢 Off-Grid Venue`), and leaves the `+ Add to Day` footer button visible on `"browse"`. |
| **BUG-22** | Parity (Missing UI) | **P1 High** | `desktop_client/views/login_view.py` & `signup_view.py` & `services/auth_service.py` | Missing **Explore Demo Account (Pattranite Persona)** (`loginDemo()`), missing **Continue with Google / Apple** buttons and `"or"` divider on Login & Signup, and Signup `M.I.` field is side-by-side instead of stacked. |
| **BUG-23** | Parity (Missing UI) | **P1 High** | `desktop_client/views/welcome_view.py:83–101` | Standard Welcome screen renders `logout_skyscrapers_blob.png` (on Web, `logout_skyscrapers_blob.png` only renders on the After-Logout screen). |
| **BUG-24** | Parity (Missing UI) | **P1 High** | `desktop_client/views/profile_view.py:495–615` & `components/dialogs.py:44–294` | `Profile -> Favorites` omits search bar, category filter scroller, and `Directions` button; `Profile -> Help` FAQs are static instead of accordions; `show_place_detail_dialog` omits reviews, rating/provenance badges, photo gallery strip, tags, and `show_add_actions` scoping. |

---

## 2. Screen-by-Screen 1:1 Parity Audit (Web vs. Desktop)

The table below compares every screen in the [Trip mo, trip ko Web App](https://www.google.com/search?q=https://edselrenz.github.io/Itinerary-App/) (`Project/src/app/`) against the Python Flet Desktop client (`desktop_client/`):

| Screen / Feature | Web Application (`Project/src/app/`) | Desktop Application (`desktop_client/`) | Parity Status & Action Required |
| :--- | :--- | :--- | :--- |
| **Splash & Offline Host Banner** | `splash-overlay` (`app.component.html`) + `OfflineBannerComponent` (`offline-banner.component.ts`). | `SplashOverlay` (`splash_overlay.py`) + `OfflineHostBanner` (`offline_banner.py`). | **Broken Feedback**: `OfflineHostBanner._on_retry()` uses dead `page.snack_bar` API (**BUG-07**). |
| **Welcome & After-Logout** | `welcome.page.html`: Standard view shows `login_illustration.png`, `"Trip mo, trip ko"`, subtitle, `Log In`, `Sign Up`, `Continue as Guest`. After-Logout view (`?loggedOut=true`) shows `logout_skyscrapers_blob.png` + `"See you again!"`. | `welcome_view.py`: Standard view renders **both** `logout_skyscrapers_blob.png` and `login_illustration.png` (`lines 83–101`). | **Parity Defect (BUG-23)**: Remove `logout_skyscrapers_blob.png` from `_build_standard_view()` in `welcome_view.py`. |
| **Guest Landing** | `guest.page.html`: Shows `guest_illustration.png`, `"Guest"`, `"Limited access mode"`, `Explore App`, `Log In`, `Sign Up`. | `guest_view.py`: Matches Web layout and actions. | **1:1 Parity Verified**. |
| **Log In** | `login.page.html`: Email, Password, Remember Me, Forgot Password modal, `Log In` (with spinner), `"or"` divider, `Continue with Google`, `Continue with Apple`, `✨ Explore Demo Account (Pattranite Persona)`, Sign Up link. | `login_view.py`: Missing spinner on `Log In` (**BUG-09**), missing `"or"` divider, `Continue with Google`, `Continue with Apple`, and `Explore Demo Account` (**BUG-22**). | **Parity Defect (BUG-09, BUG-22)**: Add loading spinner, Google/Apple social buttons, and `login_demo()` (`Pattranite Limpatiyakorn`). |
| **Sign Up** | `signup.page.html`: Stacked `First Name`, `Middle Initial (if applicable)`, `Last Name`, `Email`, `Password` (live strength bar), `Confirm Password`, Terms modal, `Sign Up` (with spinner), Login switch, `"or"` divider, `Continue with Google`, `Continue with Apple`. | `signup_view.py`: `First Name` and `70px` `M.I.` are side-by-side (`line 124`); missing spinner (**BUG-09**); missing `"or"` divider and Google/Apple buttons (**BUG-22**). | **Parity Defect (BUG-09, BUG-18, BUG-22)**: Stack `Middle Initial (if applicable)` full-width, add spinner & Google/Apple buttons, and fix Web `middle_initial` payload. |
| **Home Dashboard** | `home.page.html`: Greeting + avatar + bell badge, 2 CTA cards (`Suggested Itinerary`, `Custom Itinerary`), `Your Saved Itineraries` horizontal scroller, `Popular in Nueva Ecija` 2-card preview + `See all ->` catalog modal, Notifications right drawer. | `dashboard_view.py`: Matches Web layout, catalog modal, and notification drawer, but opens dialogs via `page.overlay.append` without cleanup (**BUG-03**). | **Dialog Cleanup Needed (BUG-03)**. |
| **Map Explorer (`PlacesView`)** | `map.page.html`: Search bar + filter trigger + `[✨ Live OSM]` + category chips + active filter strip; Leaflet map + right legend (`Map Style`, `Route Legend`) + `Recenter` + bottom collapsible drawer (`Show List` / `Hide List`); Filter Modal; Follow-Route mode (`Back to Plan`, Day chips, bottom stop carousel with active stop selection). | `places_view.py`: `+ Add to Trip` crashes `CustomBuilderView` (**BUG-19**); clicking Map tab resets active `followRoute` (**BUG-05**); `[✨ Live OSM]` snackbar silent (**BUG-07**); clicking stop in Follow-Route carousel doesn't update `active_stop_index`. | **Critical Fixes Required (BUG-05, BUG-07, BUG-19)**. |
| **Suggested Itinerary Wizard** | `suggested-wizard.page.html`: View 1 (Form with `DestinationAutocomplete`, Date pickers, Pacing, Budget, 6 Interest chips, Travel Mode, Quality Tier), View 2 (Loading), View 3 (Generated Review with Day tabs, route map, timeline, `Explore Nearby Places` view, `Accept & Save`, `Start Over`). | `suggested_wizard_view.py`: `"Find Itinerary"` crashes with `TypeError` (**BUG-12**); `"✓ Accept & Save Itinerary"` fails cloud `422` & crashes local fallback with `AttributeError` (**BUG-13**); snackbars silent (**BUG-07**). | **Critical Fixes Required (BUG-07, BUG-12, BUG-13, BUG-14)**. |
| **Custom Itinerary Builder** | `custom-builder.page.html`: View 0 (`form`: Trip Info, Destination, Dates, Pacing, Budget + 4 presets, Travel Mode, Notes), View 2 (`browse`: Live search, categories, sort, split cards + map, sticky bottom bar), View 1 (`timeline`: Day tabs, map, reorderable stops, `+ Browse & Add Places`, `🏢 Add Off-Grid Custom Venue`, Edit Stop modal, Clear Day modal, Cancel confirm modal). | `custom_builder_view.py`: Back button traps user in `browse <-> timeline` loop (**BUG-02**); stale `selected_trip` opens old trip instead of blank form (**BUG-01**); typing in search loses focus (**BUG-08**); budget presets don't highlight (**BUG-10**); Off-Grid button opens Browse tab (**BUG-21**). | **Critical Fixes Required (BUG-01, BUG-02, BUG-07, BUG-08, BUG-10, BUG-21)**. |
| **Saved Itineraries** | `saved.page.html`: Header + `+` FAB, Search bar, Filter tabs (`All Trips`, `Upcoming`, `Drafts & Past`, `Suggested`, `Custom`), trip cards with thumbnail, metadata, budget/stops footer, and `🗑️` delete confirm. | `saved_trips_view.py`: Typing in search loses focus on every character (**BUG-08**); `list_itineraries()` mixes guest trips into logged-in cloud user (**BUG-15**). | **Fixes Required (BUG-08, BUG-15)**. |
| **Itinerary Detail (`TripDetailView`)** | `itinerary-detail.page.html`: Header (`←`, Title, Share icon, `Edit` button), White `Trip Details` summary card, `Explore Nearby Places` view (`viewMode === 'nearby'`), Day tabs, Route map (`Full Map`), Day header (`In-App Nav`, `Google Maps`), Timeline cards, `Estimated activity expenses` footer card, Share & Export modal (`.ics`, `Copy Text Summary`, `Print/PDF`), Edit mode (`Done`, `Cancel`, inline title/notes/time/cost, reorder, delete, add stop). | `trip_detail_view.py`: Has extra `"🛠️ Open in Full Builder"` & `"Export Dossier"` header buttons and dark-navy `"Local Guest Storage"` card; missing `Explore Nearby Places` view, `In-App Nav` / `Google Maps` day buttons, `Estimated activity expenses` footer, and `Copy Text Summary` (**BUG-20**). | **Parity Overhaul Required (BUG-01, BUG-20)**. |
| **Profile & 5 Subviews** | `profile.page.html`: Main Profile (Avatar upload, stats, menu), `Edit Profile`, `Saved Places (Favorites)` (with search bar, category pills, `Directions`, `View Details`), `Settings` (Notifications, Dark Mode, Clear Cache, Reset Demo Data), `Help & Support` (interactive FAQ accordions), `About`. | `profile_view.py`: Toggling Dark Mode in Settings kicks user back to root Profile (**BUG-06**); `Favorites` omits search bar, category scroller, and `Directions` button (**BUG-24**); `Help` FAQs are static (**BUG-24**); snackbars silent (**BUG-07**). | **Parity & State Fixes Required (BUG-06, BUG-07, BUG-24)**. |

---

## 3. Deep Root-Cause Diagnostics

### 3.1 Windows, Tabs, Modals & Close/Back Button Loops

1. **Stale `selected_trip` Sticky Loop (`desktop_client/main.py:160, 211–228`)**:
   - In `main.py:160`, `if trip_data: selected_trip = trip_data` assigns the module-scoped `selected_trip` variable whenever a user views or edits any itinerary, **and never resets `selected_trip = None` when navigating to other routes**.
   - When the user subsequently clicks **Custom Itinerary** from Home (`navigate_to("/builder")`) or clicks `+` on Saved Trips (`navigate_to("/builder")`), `main.py:214` passes `existing_itinerary=selected_trip` into `CustomBuilderView(...)`. Instead of starting a new trip in `form` (`View 0`), the user is forced back into editing the old saved trip in `timeline` (`View 1`)!
   - Even worse, when the user saves a brand-new itinerary in `CustomBuilderView` (`line 865`: `self._navigate(f"/trips/{saved.id}")`) or `SuggestedWizardView` (`line 884`: `self.on_navigate(f"/trips/{saved.id}")`), `trip_data` is `None`. In `main.py:224`:
     ```python
     trip_id = base_route.split("/trips/")[1]
     trip_obj = selected_trip
     if not trip_obj:
         trip_obj = await itinerary_service.get_itinerary(trip_id)
     ```
     Because `selected_trip` is still truthy from an earlier view, `TripDetailView` **ignores `trip_id` (`saved.id`) and re-opens the old `selected_trip`**!

2. **`CustomBuilderView.handle_back()` Infinite Loop Between `browse` and `timeline` (`desktop_client/views/custom_builder_view.py:130–145`)**:
   - Look at `custom_builder_view.py:130–145`:
     ```python
     def handle_back(self) -> None:
         if self.active_view == "browse":
             self.active_view = "timeline" if self.total_stops_count > 0 else "form"
             self._build_content()
             return
         if self.active_view == "timeline" and not self.existing_itinerary and not self.is_dirty:
             self.active_view = "form"
             self._build_content()
             return
     ```
   - Once the user adds even 1 stop (`total_stops_count > 0` and `is_dirty = True`), clicking `←` in `browse` sends them to `timeline`. In `timeline`, clicking **Edit Trip Info** is impossible via `←`, and if they go back to `browse` and click `←`, it loops back to `timeline`. Furthermore, on the [Trip mo, trip ko Web App](https://www.google.com/search?q=https://edselrenz.github.io/Itinerary-App/) (`custom-builder.page.ts:446–454`), clicking `←` in `timeline` or `browse` when creating a new trip (`!isEditMode`) returns to `form` (`View 0`) so the user can adjust dates/destination/budget, and clicking `←` from `form` triggers `onCancel()`.

3. **Dialog Overlay Leak & Regional Explorer `×` Button Bug (`desktop_client/components/dialogs.py` & `destination_picker.py:415`)**:
   - `dialogs.py` opens modals using Flet 1.1.2's `page.show_dialog(dialog)` and closes them via `page.pop_dialog()`. Meanwhile, `main.py:148`, `custom_builder_view.py:168, 250, 381, 694, 748, 796, 902`, `dashboard_view.py:567, 686`, `places_view.py:926`, `profile_view.py:809`, `login_view.py:278`, and `destination_picker.py:424` append dialogs to `page.overlay` (`page.overlay.append(dlg); dlg.open = True`) and close them with `dlg.open = False` **without removing `dlg` from `page.overlay`**.
   - In `DestinationPicker._open_regional_explorer()` (`destination_picker.py:415`), the header `×` button has `on_click=lambda _: pick_and_close(self.selected_destination)`, which calls `self._handle_select(name)` and fires `on_change` instead of simply closing the dialog!

4. **Map Tab (`BottomTabBar`) Resets Active `followRoute` Navigation (`desktop_client/components/bottom_tab_bar.py:93–99`)**:
   - In `BottomTabBar._handle_tab_click()`:
     ```python
     def _handle_tab_click(self, route: str) -> None:
         if route == "/map" and self.current_route.startswith("/map"):
             if self.on_map_tap_when_active:
                 self.on_map_tap_when_active()
         if self.on_navigate:
             self.on_navigate(route)
     ```
   - When the user is viewing a route on the Map (`/map?itineraryId=...&followRoute=true`) and clicks the Map tab—or clicks the Map tab while already on `/map`—`self.on_navigate("/map")` runs unconditionally, instantiating a brand-new `PlacesView` (`route_query="/map"`) and wiping out the active route!

5. **Settings Dark Mode Toggle Kicks User Out of Settings (`desktop_client/main.py:101–108` & `views/profile_view.py:678–682`)**:
   - `ProfileView._toggle_theme()` calls `main.py:toggle_theme()`, which calls `navigate_to(current_route, selected_trip, force=True)`. That replaces the current `ProfileView` (where `self.view_mode == "settings"`) with a fresh `ProfileView` (where `self.view_mode == "profile"`).

### 3.2 Cross-App Communication & Synchronization Bugs (Accounts & Saved Itineraries)

1. **`SuggestedWizardView._start_generation()` Keyword Argument Crash (`desktop_client/views/suggested_wizard_view.py:463–473`)**:
   - `SuggestedWizardView._start_generation()` calls:
     ```python
     itinerary = await self.itinerary_service.generate_suggested_itinerary(
         destination=self.destination_val,
         start_date=self.start_date_val,
         ...
     )
     ```
   - `ItineraryService.generate_suggested_itinerary(self, request: SuggestedItineraryRequest)` (`itinerary_service.py:41`) only accepts a single `SuggestedItineraryRequest` object. Calling it with keyword arguments raises `TypeError: ItineraryService.generate_suggested_itinerary() got an unexpected keyword argument 'destination'`.

2. **`SuggestedWizardView._save_generated_itinerary()` Cloud `422` Failure & Local Fallback Crash (`desktop_client/views/suggested_wizard_view.py:875` & `services/itinerary_service.py:422–439`)**:
   - `_save_generated_itinerary()` passes `self.generated_itinerary` (an `Itinerary` instance) into `self.itinerary_service.create_itinerary(payload)`.
   - When authenticated, `payload.to_dict()` sends `Itinerary.to_dict()`, where each item has `"place_id": "dest-..."` (a non-UUID string) and no `"place_payload"`. FastAPI rejects it with `HTTP 422`.
   - `create_itinerary()` catches the `422` and enters the local fallback (`itinerary_service.py:432`), executing `raw_items = d.get("items")` on `ItineraryDay` dataclass objects, crashing with `AttributeError: 'ItineraryDay' object has no attribute 'get'`.

3. **Backend `ItineraryItemBase` Rejects Curated/OSM `place_id` Strings on Both Web & Desktop (`backend/app/schemas/itinerary.py:14–35`)**:
   - Both Web (`custom-builder.page.ts:1166`, `suggested-wizard.page.ts:496`) and Desktop send `place_id: "dest-minalungao"` or `"osm-node-12345"` when saving itineraries containing offline catalog or live OSM places.
   - Because `ItineraryItemBase` defines `place_id: uuid.UUID | None = None`, Pydantic rejects any non-UUID string with `422 Unprocessable Entity` before `itinerary_service.py:_resolve_item_place_id()` even runs! Furthermore, Web sends `place: it.place` on each item while Backend only checks `place_payload: dict | None = None`.

---

## 4. Phased File-by-File Implementation Plan for Antigravity

Execute the following 6 phases in order. Every code block is self-contained and ready to apply.

### Phase 1: Backend Schema & Tunnel Sync Fixes (`BUG-14`, `BUG-17`, `BUG-18`)

#### 1.1 `backend/app/schemas/itinerary.py`
Update `ItineraryItemBase` and `ItineraryItemCreate` so non-UUID `place_id` strings (like `"dest-minalungao"` or `"osm-way-123"`) are automatically coerced to `None` while preserving the raw string inside `place_payload["id"]`, and map Web's `place` field into `place_payload`:

```python
import datetime
import uuid
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.schemas.place import PlaceRead


class ItineraryItemBase(BaseModel):
    place_id: uuid.UUID | None = None
    day_number: int = Field(1, ge=1)
    order_index: int = Field(0, ge=0)
    start_time: datetime.time | None = None
    duration_minutes: int = Field(60, ge=0)
    notes: str | None = None
    estimated_cost: float = Field(0.0, ge=0.0)
    travel_time_from_prev_mins: int = Field(0, ge=0)
    travel_mode: str = Field("driving", max_length=32)


class ItineraryItemCreate(ItineraryItemBase):
    """Supports both known DB UUIDs and dynamic/offline Place Creation."""
    place_payload: dict[str, Any] | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_place_fields(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        out = dict(data)
        # Map Web's 'place' dict into 'place_payload' if 'place_payload' is absent
        if not out.get("place_payload") and isinstance(out.get("place"), dict):
            out["place_payload"] = dict(out["place"])

        raw_pid = out.get("place_id")
        if raw_pid is not None and raw_pid != "":
            try:
                uuid.UUID(str(raw_pid))
            except (ValueError, TypeError):
                # Non-UUID string (e.g. 'dest-minalungao' or 'osm-node-123'):
                # preserve inside place_payload and clear place_id so UUID validation succeeds
                payload = dict(out.get("place_payload") or {})
                if not payload.get("id"):
                    payload["id"] = str(raw_pid)
                out["place_payload"] = payload
                out["place_id"] = None
        else:
            out["place_id"] = None

        # Normalize HH:MM AM/PM or time range strings in start_time if passed
        raw_time = out.get("start_time")
        if isinstance(raw_time, str) and raw_time.strip():
            s = raw_time.strip().split("-")[0].strip()
            for fmt in ("%H:%M:%S", "%H:%M", "%I:%M %p", "%I:%M%p"):
                try:
                    out["start_time"] = datetime.datetime.strptime(s.upper(), fmt).time()
                    break
                except ValueError:
                    continue
            else:
                out["start_time"] = None
        return out
```

#### 1.2 `scripts/run_daemon.py`
Update `start_cloudflare()` in `scripts/run_daemon.py` (`lines 55–66`) so that whenever `cloudflared.exe` outputs a new `trycloudflare.com` URL, it immediately pushes the URL to `https://ne-itinerary-api.edselrenz0.workers.dev/__sync_tunnel`:

```python
                if match and not cf_url:
                    cf_url = match.group(0).strip()
                    log(f"SUCCESS: Captured Live Cloudflare URL: {cf_url}")
                    with open(TUNNEL_FILE, "w", encoding="utf-8") as tf:
                        tf.write(f"CLOUDFLARE_URL={cf_url}\n")
                        tf.write(f"NGROK_STATIC_URL={NGROK_DOMAIN}\n")
                    try:
                        sync_resp = requests.post(
                            "https://ne-itinerary-api.edselrenz0.workers.dev/__sync_tunnel",
                            json={"url": cf_url},
                            timeout=5,
                        )
                        log(f"Synced Cloudflare URL to Worker: HTTP {sync_resp.status_code}")
                    except Exception as sync_err:
                        log(f"WARNING: Worker tunnel sync failed: {sync_err}")
```

#### 1.3 `Project/src/app/features/auth/signup/signup.page.ts` & `Project/src/app/core/services/auth.service.ts`
In `Project/src/app/core/services/auth.service.ts` (`line 110`), accept `middleInitial?: string` and include `middle_initial: middleInitial || null` in `POST /api/v1/auth/register`. In `Project/src/app/features/auth/signup/signup.page.ts` (`lines 163–168`), pass `val.firstName!.trim()`, `val.lastName!.trim()`, and `val.middleInitial?.trim()` separately instead of concatenating `middleInitial` into `firstName`.

---

### Phase 2: Flet 1.1.2 SnackBar Toast Helper, Dialog Lifecycle & Failover API Client (`BUG-03`, `BUG-07`, `BUG-16`)

#### 2.1 `desktop_client/components/dialogs.py`
1. Add a universal `show_toast(page: ft.Page, message: str, bgcolor: str = "#1E293B", duration: int = 3000)` helper at the top of `desktop_client/components/dialogs.py` that uses `page.show_dialog(ft.SnackBar(...))` (Flet 1.1.2 standard) with a safe fallback to `page.overlay`.
2. Add `open_overlay_dialog(page: ft.Page, dialog: ft.AlertDialog)` and `close_overlay_dialog(page: ft.Page, dialog: ft.AlertDialog)` so any dialog opened via `page.overlay` removes itself cleanly on close.
3. Update `show_place_detail_dialog` (`lines 44–294`) to accept `show_add_actions: bool = True` and render the **Provenance Badge** (`🛡️ Google Verified POI` / `Verified Destination`), **Rating & Review Count Row**, **Tags Wrap**, **Photo Gallery Strip**, and **Visitor Reviews Section** matching `place-detail-sheet.component.html`:

```python
def show_toast(
    page: Optional[ft.Page],
    message: str,
    bgcolor: str = "#0F172A",
    text_color: str = "#FFFFFF",
    duration: int = 3000,
) -> None:
    """Flet 1.1.2 compatible SnackBar notification."""
    if not page:
        return
    snack = ft.SnackBar(
        content=ft.Text(message, color=text_color, weight=ft.FontWeight.W_600, size=13),
        bgcolor=bgcolor,
        duration=duration,
    )
    try:
        page.show_dialog(snack)
    except Exception:
        try:
            if snack not in page.overlay:
                page.overlay.append(snack)
            snack.open = True
            page.update()
        except Exception:
            pass


def open_overlay_dialog(page: Optional[ft.Page], dialog: ft.AlertDialog) -> None:
    if not page:
        return
    try:
        page.show_dialog(dialog)
    except Exception:
        if dialog not in page.overlay:
            page.overlay.append(dialog)
        dialog.open = True
        page.update()


def close_overlay_dialog(page: Optional[ft.Page], dialog: ft.AlertDialog) -> None:
    if not page:
        return
    try:
        dialog.open = False
        if dialog in page.overlay:
            page.overlay.remove(dialog)
        page.pop_dialog()
    except Exception:
        try:
            page.update()
        except Exception:
            pass
```

#### 2.2 `desktop_client/core/api_client.py`
Update `ApiClient.request()` (`lines 113–170`) so that if a request to `http://127.0.0.1:8000/api/v1` fails with `httpx.ConnectError` or `httpx.TimeoutException`, `ApiClient` automatically retries the request against `CLOUDFLARE_WORKER_API_URL` (`https://ne-itinerary-api.edselrenz0.workers.dev/api/v1`) and updates `self._base_url` before declaring the host offline:

```python
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            from config.settings import CLOUDFLARE_WORKER_API_URL
            if self._base_url.rstrip("/") != CLOUDFLARE_WORKER_API_URL.rstrip("/"):
                logger.info("Localhost unreachable; failing over ApiClient to Cloudflare Worker proxy...")
                self.set_base_url(CLOUDFLARE_WORKER_API_URL)
                fallback_url = self._build_url(endpoint)
                try:
                    response = await self._client.request(
                        method=method.upper(),
                        url=fallback_url,
                        params=params,
                        json=json_data,
                        data=form_data,
                        headers=request_headers,
                    )
                    if self._connectivity_service is not None:
                        self._connectivity_service.set_host_offline(False)
                    return self._handle_response(response)
                except Exception:
                    pass
            if self._connectivity_service is not None:
                self._connectivity_service.set_host_offline(True, force=True)
            raise NetworkError(
                f"Cannot reach server at {url}. Please check if backend is running."
            ) from exc
```

---

### Phase 3: Fix Navigation State, Back-Button Loops & Input Focus (`BUG-01`, `BUG-02`, `BUG-04`, `BUG-05`, `BUG-06`, `BUG-08`, `BUG-19`)

#### 3.1 `desktop_client/main.py`
Fix the sticky `selected_trip` bug (`BUG-01`), preserve `TripDetailView` origin route (`previous_route`) so clicking `←` returns to `/home` or `/saved` accurately (`BUG-05`), and keep `ProfileView` subview state when toggling Dark Mode (`BUG-06`):

```python
    previous_route: str = "/saved"
    profile_subview_state: str = "profile"

    def toggle_theme() -> None:
        nonlocal is_dark_mode, profile_subview_state
        is_dark_mode = not is_dark_mode
        page.theme_mode = ft.ThemeMode.DARK if is_dark_mode else ft.ThemeMode.LIGHT
        page.bgcolor = ThemeColors.BG_DARK if is_dark_mode else ThemeColors.BG_LIGHT
        bottom_bar.set_dark_mode(is_dark_mode)
        if active_view_instance and hasattr(active_view_instance, "view_mode"):
            profile_subview_state = getattr(active_view_instance, "view_mode", "profile")
        navigate_to(current_route, selected_trip, force=True)
```
And inside `navigate_to()` in `desktop_client/main.py` (`lines 159–230`):
```python
        # Always update or clear selected_trip so stale trips never bleed into /builder or /trips/{new_id}
        if base_route in ("/home", "/saved", "/map", "/profile", "/welcome", "/guest", "/login", "/signup"):
            selected_trip = None
        elif base_route == "/builder" and trip_data is None:
            selected_trip = None
        elif trip_data is not None:
            selected_trip = trip_data

        if base_route.startswith("/trips/") and not current_route.startswith("/trips/"):
            previous_route = "/home" if current_route == "/home" else "/saved"
```
And in `main.py:223–231` (`TripDetailView` instantiation):
```python
            elif base_route.startswith("/trips/"):
                trip_id = base_route.split("/trips/")[1]
                trip_obj = selected_trip if (selected_trip and str(selected_trip.id) == str(trip_id)) else None
                if not trip_obj:
                    trip_obj = await itinerary_service.get_itinerary(trip_id)
                if trip_obj:
                    selected_trip = trip_obj
                    back_target = previous_route if previous_route in ("/home", "/saved") else "/saved"
                    view = TripDetailView(
                        page=page,
                        itinerary=trip_obj,
                        itinerary_service=itinerary_service,
                        places_service=places_service,
                        on_back=lambda bt=back_target: navigate_to(bt),
                        on_navigate=navigate_to,
                    )
```
And when instantiating `ProfileView` (`main.py:249`), restore `profile_subview_state`:
```python
            elif base_route == "/profile":
                view = ProfileView(
                    page=page,
                    auth_service=auth_service,
                    session_manager=session_manager,
                    itinerary_service=itinerary_service,
                    places_service=places_service,
                    on_navigate=navigate_to,
                    on_logout=handle_logout,
                    is_dark_mode=is_dark_mode,
                    on_toggle_theme=toggle_theme,
                    initial_view_mode=profile_subview_state,
                )
                profile_subview_state = "profile"
```

#### 3.2 `desktop_client/components/bottom_tab_bar.py`
In `BottomTabBar._handle_tab_click()` (`lines 93–99`), prevent clicking the active Map tab from overwriting an active `followRoute` session or recreating `PlacesView`:

```python
    def _handle_tab_click(self, route: str) -> None:
        if route == "/map" and self.current_route.startswith("/map"):
            if "followRoute=true" in self.current_route or "itineraryId=" in self.current_route:
                return
            if self.on_map_tap_when_active:
                self.on_map_tap_when_active()
            return
        if self.on_navigate:
            self.on_navigate(route)
```

#### 3.3 `desktop_client/components/destination_picker.py`
Fix the 3 bugs in `DestinationPicker` (`BUG-03`, `BUG-04`, `BUG-08`):
1. Persist `self._text_field` across updates instead of recreating it inside `_build_content()` on every keystroke (`_on_input_change` only refreshes `self._suggestion_panel` and action buttons).
2. Add an `on_blur` handler and a `"Close ✕"` header button on `self._suggestion_panel` so users can dismiss the dropdown without selecting an item.
3. In `_open_regional_explorer()` (`line 415`), change the `×` close button from `on_click=lambda _: pick_and_close(self.selected_destination)` to `on_click=lambda _: close_only()` so clicking `×` closes the modal without mutating the selection.

---

### Phase 4: Fix Suggested Wizard Crash, Save Failure & Guest Contamination (`BUG-12`, `BUG-13`, `BUG-15`)

#### 4.1 `desktop_client/views/suggested_wizard_view.py`
1. **Fix `_start_generation()` (`lines 461–475`)** to construct and pass a `SuggestedItineraryRequest` object to `self.itinerary_service.generate_suggested_itinerary(req)`:

```python
    async def _start_generation(self) -> None:
        self.view_mode = 2
        self._build_content()
        await asyncio.sleep(0.4)
        try:
            from models.itinerary import SuggestedItineraryRequest
            req = SuggestedItineraryRequest(
                destination=self.destination_val,
                start_date=self.start_date_val,
                end_date=self.end_date_val,
                pacing=self.pacing_val,
                daily_budget=self.daily_budget_val,
                preferences=list(self.selected_preferences),
                travel_mode=self.travel_mode_val,
                min_rating=self.min_rating_val,
                anchor_place_id=self.anchor_place_id,
            )
            itinerary = await self.itinerary_service.generate_suggested_itinerary(req)
            self.generated_itinerary = itinerary
            self.selected_day_num = 1
            self.view_mode = 3
            self._build_content()
        except Exception as exc:
            logger.error("Failed to generate suggested itinerary: %s", exc)
            self.view_mode = 1
            self._build_content()
            from components.dialogs import show_toast
            show_toast(self.safe_page, f"Could not generate itinerary: {exc}", bgcolor=ThemeColors.ERROR)
```

2. **Fix `_save_generated_itinerary()` (`lines 870–891`)** to convert `self.generated_itinerary` into an `ItineraryCreatePayload` (including full `place_payload` dicts for every stop) and display feedback with `show_toast()`:

```python
    async def _save_generated_itinerary(self) -> None:
        if not self.generated_itinerary:
            return
        try:
            from models.itinerary import ItineraryCreatePayload
            from components.dialogs import show_toast

            days_payload = []
            for d in self.generated_itinerary.days:
                items_payload = []
                for idx, item in enumerate(d.items):
                    items_payload.append({
                        "place_id": item.place_id or (item.place.id if item.place else None),
                        "day_number": d.day_number,
                        "order_index": idx,
                        "start_time": item.start_time,
                        "duration_minutes": item.duration_minutes,
                        "notes": item.notes,
                        "estimated_cost": item.estimated_cost,
                        "travel_time_from_prev_mins": item.travel_time_from_prev_mins,
                        "travel_mode": item.travel_mode or self.travel_mode_val,
                        "place_payload": item.place.to_dict() if item.place else None,
                    })
                days_payload.append({
                    "day_number": d.day_number,
                    "date": d.date,
                    "theme": d.theme,
                    "items": items_payload,
                })

            payload = ItineraryCreatePayload(
                title=self.generated_itinerary.title,
                description=self.generated_itinerary.description,
                destination=self.generated_itinerary.destination or self.destination_val,
                start_date=self.generated_itinerary.start_date or self.start_date_val,
                end_date=self.generated_itinerary.end_date or self.end_date_val,
                total_budget=self.generated_itinerary.total_budget,
                travel_mode=self.generated_itinerary.travel_mode or self.travel_mode_val,
                is_suggested=True,
                days=days_payload,
            )
            saved = await self.itinerary_service.create_itinerary(payload)
            show_toast(self.safe_page, "Itinerary saved to your trips!", bgcolor=ThemeColors.SUCCESS)
            if self.on_navigate:
                self.on_navigate(f"/trips/{saved.id}", saved)
        except Exception as exc:
            from components.dialogs import show_toast
            show_toast(self.safe_page, f"Failed to save itinerary: {exc}", bgcolor=ThemeColors.ERROR)
```

#### 4.2 `desktop_client/services/itinerary_service.py`
1. In `list_itineraries()` (`lines 390–408`), match Web's `ItineraryService.refreshItineraries()` (`itinerary.service.ts:122–141`): when `self.session_manager.is_authenticated` is `True`, return **only** the authenticated user's cloud itineraries (falling back to `guest_storage` only if the API is unreachable), preventing leftover local guest trips from polluting authenticated accounts (`BUG-15`).
2. In `create_itinerary()` (`lines 422–455`), support both `ItineraryCreatePayload` and `Itinerary` instances cleanly so `d.get("items")` never crashes on `ItineraryDay` objects (`BUG-13`).

---

### Phase 5: Fix Custom Builder, Saved Trips & Places View Parity (`BUG-02`, `BUG-08`, `BUG-10`, `BUG-19`, `BUG-21`)

#### 5.1 `desktop_client/views/custom_builder_view.py`
1. **Fix `handle_back()` (`lines 130–145`, `BUG-02`)** to match Web's `onHeaderBack()` (`custom-builder.page.ts:446–454`):
   - If `self.active_view == "browse"`: return to `"timeline"` if `self.total_stops_count > 0` else `"form"`.
   - If `self.active_view == "timeline"`:
     - If `self.existing_itinerary is None` (creating a new trip): set `self.active_view = "form"` and call `self._build_content()` so the user can always return to Step 1 (`Trip Info`) without getting trapped!
     - If `self.existing_itinerary is not None` (editing an existing trip): if `self.is_dirty`, show the Discard Changes dialog; otherwise navigate back.
   - If `self.active_view == "form"`: if `self.is_dirty`, show the Discard Changes dialog; otherwise call `self.on_back()`.
2. **Fix Live Search Focus Loss (`lines 327, 487–489`, `BUG-08`)**:
   - Store `self._browse_search_field` as an instance attribute and update only `self._browse_results_container.content` and `self._browse_map_container.content` inside `_on_browse_search_live(val)` instead of calling `self._build_content()`.
3. **Fix Budget Preset Chips (`lines 886–890`, `BUG-10`)**:
   - In `_set_budget_preset(val, field_ctrl)`, update `self.daily_budget = val`, set `field_ctrl.value = str(int(val))`, and call `self._build_content()` so the selected preset chip (`₱1,500`, `₱2,500`, `₱4,000`, `₱6,000`) renders with its active blue fill (`ThemeColors.PRIMARY`).
4. **Fix Off-Grid Venue Modal Default Tab (`lines 548, 595–798`, `BUG-21`)**:
   - Change `_open_add_stop_dialog(day_num, initial_tab: str = "custom")` so clicking `"🏢 Add Off-Grid Custom Venue"` opens directly on the `"custom"` (`🏢 Off-Grid Venue`) tab, and hide the bottom `+ Add to Day` action button when `active_tab[0] == "browse"`.

#### 5.2 `desktop_client/views/saved_trips_view.py`
In `SavedTripsView`, persist `self.search_field` across filter updates (`BUG-08`) and update only the cards grid container inside `_on_search_change()` so typing never drops focus.

#### 5.3 `desktop_client/views/places_view.py`
1. **Fix `_prompt_add_place_to_trip()` (`line 611`, `BUG-19`)**:
   ```python
   def _prompt_add_place_to_trip(self, place: Place) -> None:
       if self.on_navigate:
           self.on_navigate("/builder", None, place)
   ```
   Passing `None` as `trip_data` and `place` as `pre_added_place` prevents `CustomBuilderView` from treating `place` as an `Itinerary`.
2. **Fix Follow-Route Stop Selection**: When clicking a stop card in `_build_follow_route_bottom_carousel()`, set `self._active_route_stop_index = idx` and pass `active_stop_index=self._active_route_stop_index` to `SlippyMapCanvas`.

---

### Phase 6: Complete 1:1 UI Parity Across Auth, Welcome, Trip Detail & Profile (`BUG-09`, `BUG-20`, `BUG-22`, `BUG-23`, `BUG-24`)

#### 6.1 `desktop_client/views/welcome_view.py` (`BUG-23`)
In `_build_standard_view()` (`lines 83–101`), remove the `logout_skyscrapers_blob.png` `ft.Image` block so `logout_skyscrapers_blob.png` is rendered **exclusively** in `_build_after_logout_view()`, matching `welcome.page.html`.

#### 6.2 `desktop_client/services/auth_service.py`, `views/login_view.py` & `views/signup_view.py` (`BUG-09`, `BUG-22`)
1. In `desktop_client/services/auth_service.py`, add `async def login_demo(self) -> User`:
   - Attempts `POST /api/v1/auth/login` (or `/register`) with `loverrukk@gmail.com` / `Pattranite Limpatiyakorn`, and if offline, creates the local demo session with avatar `assets/demo_avatar.jpg` and persists it to `SessionManager`—matching Web's `AuthService.loginDemo()` (`auth.service.ts:138–159`).
2. In `login_view.py`:
   - Disable `self.submit_btn` and show a `ft.ProgressRing(width=18, height=18, stroke_width=2, color="#FFFFFF")` while `_handle_login()` is running (`BUG-09`).
   - Below the `Log In` button, add the `"or"` divider, **Continue with Google** (`google_logo.png`), **Continue with Apple**, and **`✨ Explore Demo Account (Pattranite Persona)`** button (`BUG-22`).
3. In `signup_view.py`:
   - Stack `First Name`, `Middle Initial (if applicable)` (full-width), and `Last Name` vertically (`BUG-22`).
   - Add loading spinner on `Sign Up` button (`BUG-09`), plus the `"or"` divider and **Continue with Google / Apple** buttons below the `"Already have an account? Log in"` row (`BUG-22`).

#### 6.3 `desktop_client/views/trip_detail_view.py` (`BUG-20`)
Align `TripDetailView` strictly with `itinerary-detail.page.html`:
1. **Header Bar**: Left `←` back button + Trip Title; Right **Share/Export icon button** (`ft.Icons.SHARE_OUTLINED`) + **`Edit` button** (which toggles the inline Figma Image 3 edit mode, removing the duplicate `"🛠️ Open in Full Builder"` and `"Export Dossier"` header buttons).
2. **Summary Card**: Replace the dark-navy `"Local Guest Storage"` card with Web's clean white **Trip Details** card (`Destination`, `Dates`, `Duration`, `Budget`, `Travel Mode`, `Total Stops`).
3. **Active Day Header Actions**: Add **`In-App Nav`** (navigates to `/map?itineraryId={id}&day={day}&followRoute=true`) and **`Google Maps`** (opens external Google Maps multi-stop directions URL) buttons next to the Day title.
4. **Explore Nearby Places View & Footer**: Add the **Explore Nearby Places** purple gradient banner (`viewMode = "nearby"` subview allowing one-click `+ Add to Day X`) and the **Estimated activity expenses** footer summary card (`₱X,XXX` vs. `Total budget ₱Y,YYY`).
5. **Share & Export Modal (`dialogs.py:469–531`)**: Add **Copy Text Summary** (`page.clipboard.set(...)` + `show_toast("Itinerary summary copied to clipboard!")`) alongside `.ics` Calendar export and Printable summary export.

#### 6.4 `desktop_client/views/profile_view.py` (`BUG-24`)
1. **Saved Places (`Favorites`) Subview (`_build_favorites_subview()`, `lines 495–582`)**:
   - Render the **Search Bar** (`Search saved places...` bound to `self._fav_search_query`) and **Category Horizontal Scroller** (`All Places`, `Nature & Parks`, `Culture & Heritage`, `Cafes & Dining`, `Resorts & Stays`, `Farm & Agri-Tourism` bound to `self._fav_selected_cat`) at the top of the Favorites subview.
   - Add the **`Directions`** button (opening Google Maps directions to `place.latitude, place.longitude`) alongside **`View Details`** on each favorite card.
2. **Help & Support Subview (`_build_help_subview()`, `lines 587–615`)**:
   - Convert the 3 static FAQ blocks into interactive collapsible accordions (`self._open_faq_index = 0` by default) with chevron indicators matching `profile.page.html:299–349`.

---

## 5. End-to-End QA Test Suite & Verification Matrix (`TC-01` to `TC-30`)

Use this checklist to verify full 1:1 parity, cross-app synchronization, visual feedback, and modal/navigation lifecycles after applying Phases 1–6:

| Test ID | Feature Area | Test Procedure | Expected Result (Web & Desktop 1:1 Parity) |
| :--- | :--- | :--- | :--- |
| **TC-01** | Welcome Screen | Launch app fresh (`/#/welcome` on Web, `/welcome` on Desktop). | Shows `login_illustration.png` ONLY (no `logout_skyscrapers_blob.png`), title `"Trip mo, trip ko"`, `Log In`, `Sign Up`, `Continue as Guest`. |
| **TC-02** | After-Logout Screen | Log out from Profile and inspect `/welcome?loggedOut=true`. | Shows `logout_skyscrapers_blob.png` + `login_illustration.png`, `"See you again!"`, `"Log In Again"`, `"Create New Account"`, `"Browse as Guest"`. |
| **TC-03** | Login Parity & Demo | Open Log In screen. Verify social buttons & click `Explore Demo Account`. | Shows `"or"`, `Continue with Google`, `Continue with Apple`, and `Explore Demo Account (Pattranite Persona)`. Clicking Demo logs in as `Pattranite Limpatiyakorn`. |
| **TC-04** | Login Loading State | Enter credentials and click `Log In`. | Button disables and displays loading spinner until response arrives; invalid credentials show red inline alert. |
| **TC-05** | Signup Parity & Sync | Open Sign Up screen. Register a new account with First Name, Middle Initial, Last Name. | Fields are stacked vertically; `POST /api/v1/auth/register` stores `first_name`, `middle_initial`, `last_name` cleanly; user can immediately log in on both Web and Desktop. |
| **TC-06** | Cross-App Account Sync | Edit profile name, bio, phone, and avatar on Web, then open Desktop Profile (and vice versa). | Both apps fetch `GET /api/v1/auth/me` and render identical full name, bio, phone, and avatar image. |
| **TC-07** | Failover Connectivity | Stop local backend (`127.0.0.1:8000`) while Worker tunnel is active, then launch Desktop app. | `ApiClient` automatically fails over to `https://ne-itinerary-api.edselrenz0.workers.dev/api/v1` without getting stuck in false Offline Mode. |
| **TC-08** | Daemon Tunnel Sync | Run `python scripts/run_daemon.py`. | Captures `trycloudflare.com` URL, writes `scratch/active_tunnel.txt`, and `POST`s to `/__sync_tunnel` (`HTTP 200`). |
| **TC-09** | Destination Picker Close | Focus Destination input in Suggested or Custom Builder, type `"Cab"`, then click `Close ✕` or outside. | Typing `"Cab"` keeps cursor focus continuously (`BUG-08`); clicking `Close ✕` closes the suggestion panel cleanly (`BUG-04`). |
| **TC-10** | Regional Explorer `×` | Open `Browse All Nueva Ecija Towns` modal and click the top-right `×` button. | Modal closes without altering the current destination or firing `on_change` (`BUG-03`). |
| **TC-11** | Suggested Wizard Generate | Fill Suggested Wizard (Cabanatuan City, 2 days, Moderate, ₱1,500) and click `Find Itinerary`. | Does NOT raise `TypeError` (`BUG-12`); generates 2-day itinerary and transitions to View 3 (`Suggested Review`). |
| **TC-12** | Suggested Wizard Save & Sync | While logged in on Desktop, click `✓ Accept & Save Itinerary` on a generated trip. | Toast `"Itinerary saved to your trips!"` appears (`BUG-07`); `POST /api/v1/itineraries` succeeds (`HTTP 201`, no `422` UUID error or `AttributeError`, `BUG-13`/`BUG-14`); trip appears in Web Saved Trips too. |
| **TC-13** | Custom Builder Blank Open | View any saved trip in `TripDetailView`, go to Home, and click `Custom Itinerary`. | Opens a **fresh blank** Custom Builder on Step 1 (`form`), NOT the previously viewed saved trip (`BUG-01`). |
| **TC-14** | Custom Builder Presets | On Custom Builder Step 1 (`form`), click `₱1,500`, `₱2,500`, `₱4,000`, `₱6,000`. | Clicked budget preset chip highlights in blue (`ThemeColors.PRIMARY`) and updates the text input (`BUG-10`). |
| **TC-15** | Custom Builder Live Search | Advance to Step 2 (`browse`) and type `"Minalungao"` in the search bar. | Input retains focus across all characters typed (`BUG-08`) and filters cards + map pins live. |
| **TC-16** | Custom Builder Back Loop | Add 2 stops in `browse`, click `View Timeline ->`, then click `←` in header. | Returns to Step 1 (`form`) so user can edit trip info (`BUG-02`), instead of looping endlessly between `browse` and `timeline`. |
| **TC-17** | Off-Grid Custom Venue | In `timeline`, click `🏢 Add Off-Grid Custom Venue`. | Opens modal directly on `🏢 Off-Grid Venue` tab (`BUG-21`); switching to `🔍 Browse Places` hides the bottom `+ Add to Day` footer button. |
| **TC-18** | Custom Builder Cloud Save | Save a Custom Itinerary containing curated (`dest-...`) and OSM (`osm-...`) places while logged in. | Backend `normalize_place_fields` validator coerces string `place_id` and persists new `Place` records (`BUG-14`); trip syncs across Web and Desktop. |
| **TC-19** | Post-Save Redirect | Save a new trip when another trip was viewed earlier in the session. | Navigates to `/trips/{new_saved_id}` and displays the **newly saved trip**, not the old `selected_trip` (`BUG-01`). |
| **TC-20** | Saved Trips Search & Auth | Log in as an authenticated user and search in `/saved`. | Typing in search bar retains cursor focus (`BUG-08`); list shows **only** the authenticated user's cloud trips, unpolluted by local guest storage (`BUG-15`). |
| **TC-21** | Guest-to-Cloud Migration | Create 1 trip as Guest, then log in or sign up. | Guest trip migrates to the user's cloud account via `migrate_guest_itineraries()` and local guest storage is cleared. |
| **TC-22** | Trip Detail Header & Card | Open any trip in `TripDetailView`. | Header shows `←`, Title, Share icon, and single `Edit` button (no extra `"Open in Full Builder"` or `"Export Dossier"` buttons, `BUG-20`); summary card uses clean white Web styling. |
| **TC-23** | Trip Detail Day Navigation | In `TripDetailView`, click `In-App Nav` and `Google Maps` on Day 1. | `In-App Nav` opens `/map?itineraryId=...&day=1&followRoute=true`; `Google Maps` launches external multi-stop Google Maps route (`BUG-20`). |
| **TC-24** | Trip Detail Nearby Places | In `TripDetailView`, click `Explore Nearby Places` banner and add a place to Day 1. | Switches to `nearby` view mode, lists unvisited nearby places, and adds selected stop to Day 1 with toast feedback (`BUG-20`). |
| **TC-25** | Share & Export Copy | Click Share/Export icon in `TripDetailView` and click `Copy Text Summary`. | Copies formatted itinerary text to clipboard and displays toast confirmation (`BUG-07`, `BUG-20`). |
| **TC-26** | Map Add-to-Trip Action | On `/map`, open a place detail dialog and click `+ Add to Trip`. | Opens `CustomBuilderView` with that place pre-added to Day 1 without raising `AttributeError: 'Place' object has no attribute 'title'` (`BUG-19`). |
| **TC-27** | Map Follow-Route Tab Click | While in Follow-Route mode on `/map`, click the Map icon in `BottomTabBar` or click a stop card in the bottom carousel. | Clicking the Map tab preserves active Follow-Route mode (`BUG-05`); clicking a stop card highlights that stop on the map. |
| **TC-28** | Place Detail Dialog Parity | Open any place detail dialog from Home, Map, or Builder. | Displays Provenance badge, Rating & reviews count, Tags, Photo thumbnails, and Visitor Reviews; hides `+ Add to Trip` when opened from `TripDetailView` (`BUG-24`). |
| **TC-29** | Profile Favorites & Help | Open `Profile -> Saved Places` and `Profile -> Help & Support`. | Favorites shows search bar, category filter scroller, `Directions`, and `View Details`; Help & Support FAQs expand/collapse as interactive accordions (`BUG-24`). |
| **TC-30** | Settings Dark Mode Persistence | Open `Profile -> Settings` and click `App Appearance`. | Toggles Light/Dark mode while **staying inside the `Settings` subview** (`BUG-06`), without kicking the user back to the root Profile menu. |
