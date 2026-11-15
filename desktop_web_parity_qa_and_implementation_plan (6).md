# Cycle 3 Full-Stack QA Audit, 1:1 Web-Desktop Parity Verification & Antigravity Implementation Plan
**Project:** Nueva Ecija Travel Itinerary App (*"Trip mo, trip ko"*)  
**Audited Commit:** `40507f51c34620caea48eb5cc758ce7fffdaa7e0` (`edselrenz/itinerary-app`)  
**Reference Web Deployment:** [Trip mo, trip ko Live Web App](https://www.google.com/search?q=https://edselrenz.github.io/Itinerary-App/) ([Welcome Route](https://www.google.com/search?q=https://edselrenz.github.io/Itinerary-App/%23/welcome))  
**Cloudflare Worker API Proxy:** [NE Itinerary API Worker](https://www.google.com/search?q=https%3A%2F%2Fwww.google.com%2Furl%3Fsa%3DE%26source%3Dgmail%26q%3Dhttps%3A%2F%2Fne-itinerary-api.edselrenz0.workers.dev%2Fapi%2Fv1) ([Tunnel Status Endpoint](https://www.google.com/search?q=https://ne-itinerary-api.edselrenz0.workers.dev/__status))  
**Permanent Ngrok Fallback:** [Ngrok Tunnel Endpoint](https://www.google.com/search?q=https://anybody-cube-surprise.ngrok-free.dev)

---

## 1. Executive Summary & Complete Cycle 3 Defect Matrix (20 Root-Cause Bugs)

An end-to-end static, AST, and UI lifecycle audit of both the **Desktop Application** (`desktop_client/`, Python Flet 1.1.2) and the **Web Application** (`Project/src/app/`, Ionic 8 + Angular 20), plus **Backend API** (`backend/app/`, FastAPI) and **Scripts** (`scripts/`), identified **20 root-cause bugs** explaining every symptom you observed as well as underlying full-stack regressions:

| ID | Category | Severity | File & Line Numbers | Root-Cause Summary |
| :--- | :--- | :--- | :--- | :--- |
| **BUG-01** | **Map Texture Seam & Gray Placeholder Background** | **P0 Critical** | `desktop_client/components/slippy_map_canvas.py:48–102, 653–656` | (1) **Mixed Tile Providers**: Inside Nueva Ecija (zooms 10–14), `_resolve_tile_source()` loads pre-bundled **CartoDB Voyager / OSM** tiles from `assets/tiles/`, but outside Nueva Ecija (or at zooms 15–18) lines 71 & 101 fetch **ESRI ArcGIS World Street Map** tiles (`server.arcgisonline.com`), which have a completely different khaki/shaded-relief texture and font! (2) **Zero Overscan Ring**: `_render_tiles()` only renders `min_tx..max_tx` for the exact viewport; dragging `_pan_layer` by even 10px exposes the raw `#e2e8f0` gray container background around the edges. |
| **BUG-02** | **Map Extreme Pan/Zoom Lag** | **P0 Critical** | `desktop_client/components/slippy_map_canvas.py:386–426, 581–640, 725–814` | (1) **Duplicate Nested `GestureDetector`s** (`lines 386 & 418`): Two nested `GestureDetector`s with `drag_interval=16` fire duplicate competing pan/scroll events every 16ms. (2) **Dual Unthrottled IPC `.update()` Calls** (`lines 596–601`): `_handle_pan_update` calls both `_pan_layer.update()` and `_marker_stack.update()` unthrottled. (3) **180-Widget Rebuild on Every Pan Commit** (`lines 728, 766–814`): `cell_size = 58.0` creates ~150 cluster/pin widget trees from scratch on every `redraw()`. |
| **BUG-03** | **Desktop Notification Button & 11 Other Modals Do Not Open** | **P0 Blocker** | `desktop_client/views/dashboard_view.py:688–811, 932`, `places_view.py:1259`, `profile_view.py:1257`, `custom_builder_view.py:191, 302, 623, 1362, 1447, 1502, 1706`, `main.py:199` | Clicking the Notification Bell (`_on_bell_clicked()` at `dashboard_view.py:688`) sets `self.unread_notifications = 0` (hiding the badge) and calls `self.safe_page.overlay.append(dlg); dlg.open = True`. **In Flet 1.1.2, `page.overlay.append(dlg); dlg.open = True` does NOT display `ft.AlertDialog`**—`page.show_dialog(dlg)` (via `open_overlay_dialog`) is required! Also, Desktop notifications lack Web's `"Mark all read"` button, `✕` close button, and clickable route actions. |
| **BUG-04** | **Desktop UI Stuck on Left Side (`ProfileView`, `CustomBuilderView`) & Not Resizing Dynamically** | **P0 Critical** | `desktop_client/main.py:389–393`, `views/profile_view.py:303–323, 567–595, 741–757, 925–943, 1018, 1071`, `views/custom_builder_view.py:551–576`, `views/places_view.py:301, 424` | (1) In Flet 1.1.2, an `ft.Column(expand=True, horizontal_alignment=CENTER)` inside an `ft.Container` shrinks horizontally to its child's width (`560px` in `ProfileView`, `640px` in `CustomBuilderView` Step 1) unless `width=float("inf")` is set on the `Column` or the card is wrapped in `ft.Row(alignment=ft.MainAxisAlignment.CENTER)`—leaving `ProfileView` and `CustomBuilderView` stuck on the left! (2) `_on_page_resize` in `main.py:389` crashes on `settings.palette` and never calls `on_resize()` on the active view, while `ResponsiveLayout.get_metrics()` (`settings.py:438`) is never called anywhere, and `PlacesView` hardcodes `width=1366, height=768` and `left=530`! |
| **BUG-05** | **Desktop Dark Mode Toggle Crash & White-on-White Views** | **P0 Blocker** | `desktop_client/main.py:107–129, 389–392`, `config/settings.py`, `components/bottom_tab_bar.py`, and all 9 Desktop views/cards | (1) Clicking **App Appearance** in `Profile -> Settings` calls `main.py:toggle_theme()`, which crashes at line 115 (`settings.set_dark_mode` -> `AttributeError`), line 116 (`settings.palette` -> `AttributeError`), line 118 (`palette.bg_primary` -> `AttributeError`), and line 122 (`bottom_tab_bar.refresh_theme()` -> `AttributeError`) before `page.theme_mode` is even updated! (2) Even when `ft.ThemeMode.DARK` is active, 8 views (`DashboardView`, `PlacesView`, `CustomBuilderView`, `SuggestedWizardView`, `SavedTripsView`, `TripDetailView`, `ProfileView`, `LoginView`, `SignupView`) and 3 card components (`PlaceCard`, `StopCard`, `ItineraryRouteMap`) hardcode `ThemeColors.BG_LIGHT` and `ft.Colors.WHITE` while Flet flips uncolored text to white (`#f8fafc`), causing white-on-white invisible text. |
| **BUG-06** | **Web Dark Mode Broken on Login, Signup, Welcome & Guest** | **P1 High** | `Project/src/global.scss:3323–3580` & `Project/src/app/features/auth/{login,signup,welcome,guest}/*.scss` | `global.scss:3330` forces `ion-content { --background: #0b1120 !important }`, turning `<ion-content class="login-content">` and `<ion-content class="signup-content">` dark navy (`#0b1120`), **but** `login.page.scss` and `signup.page.scss` hardcode `color: #000000` on `.brand-title`, `.welcome-title`, `.signup-title`, `.remember-text`, `.footer-prompt`, and `.switch-prompt` (making all titles and labels **black-on-dark-navy invisible**!), while `.field-container` (`background: #ffffff`) and `.social-pill-btn` (`background: #ffffff`) stay glaring white, and `.welcome-screen-wrapper` / `.guest-screen-container` hardcode `background: #ffffff` with `#000000` text. |
| **BUG-07** | **Creating / Saving Custom Itinerary Throws `'ItineraryItem' object has no attribute 'estimated_cost'`** | **P0 Blocker** | `desktop_client/views/custom_builder_view.py:1786–1789` & `desktop_client/views/trip_detail_view.py:390–395` | When `_save_custom_itinerary()` finishes saving a Custom Itinerary, it calls `self.on_navigate(f"/trips/{saved.id}", saved)` **inside** its `try...except` block. That instantiates `TripDetailView`, which evaluates `float(itm.estimated_cost or 0.0)` at `trip_detail_view.py:391`. Because `ItineraryItem` only has `.representative_cost` (not `.estimated_cost`), `TripDetailView` throws `AttributeError`, which `_save_custom_itinerary()` catches and displays as `"Failed to save itinerary: 'ItineraryItem' object has no attribute 'estimated_cost'"`! |
| **BUG-08** | **Custom Builder Back Button Traps User in "Discard Changes?" Loop** | **P0 Critical** | `desktop_client/views/custom_builder_view.py:138–167` | `if self.is_dirty: self._prompt_discard_changes(); return True` is at the **very top** of `handle_back()` before checking `self.active_view`. Selecting a budget preset, changing dates, or adding 1 stop sets `is_dirty = True`, so clicking `←` in `browse` or `timeline` refuses to step back to `timeline` or `form` (`View 0`) and instead pops `"Discard Changes?"` (exiting to `/home`). |
| **BUG-09** | **Custom Builder `did_mount` & Off-Grid Coordinates Bugs** | **P1 High** | `desktop_client/views/custom_builder_view.py:131, 1553–1557` | `did_mount()` calls `await self.place_service.list_places()`, which does not exist on `PlaceService` (`AttributeError`, should be `get_places(page=1, page_size=250)`). In `_open_custom_venue_dialog()`, `_toggle_coords` sets `coords_toggle_btn.text = ...` instead of `.content = ft.Text(...)`. |
| **BUG-10** | **"Start Trip Here" Ignored by Backend When Online** | **P0 Critical** | `backend/app/algorithms/itinerary_generator.py:216–470` & `backend/app/schemas/itinerary.py:314–320` | `backend/app/algorithms/itinerary_generator.py` **never reads `request.anchor_place_id` or `request.anchor_place_payload` at all**! And `SuggestedItineraryRequest.coerce_anchor_id` (`schemas/itinerary.py:317`) wipes any non-UUID string (`"dest-minalungao"`, `"osm-..."`) to `None`. When online, clicking `"✨ Start Trip Here"` on a Map POI on both Web and Desktop ignores the clicked POI! |
| **BUG-11** | **"Start Trip Here" Offline & Resort/Hotel Anchor Bugs** | **P1 High** | `desktop_client/services/itinerary_service.py:224–236, 319–323, 387` & `Project/src/app/core/services/itinerary.service.ts:1082–1086, 1148` & `Project/src/app/tabs/map/map.page.ts:990` | (1) On Desktop, `curated_pool` omits API-merged/Live-OSM places from `place_service.get_loaded_places()`. (2) On both Web and Desktop, clicking `"Start Trip Here"` on a resort/hotel (`resort_swimming` / `hotel_accommodation`) drops the anchor on 1-day Web trips (`itinerary.service.ts:1083`) or moves it from Stop 1 to the **last stop of Day 1** (`itinerary_service.py:387`, `itinerary.service.ts:1148`). (3) On Web `map.page.ts:990`, if `place.municipality_name` is missing, `destination: place.name` is passed as the municipality filter, causing `muniMatches` to be empty. |
| **BUG-12** | **Suggested Wizard Save Crashes 100% of the Time on Desktop** | **P0 Blocker** | `desktop_client/views/suggested_wizard_view.py:1302–1338` | `_save_generated_itinerary()` accesses non-existent attributes `item.start_time`, `item.estimated_cost`, `item.travel_time_from_prev_mins`, `item.travel_mode`, `d.date`, `d.theme`, `self.generated_itinerary.description`, `self.generated_itinerary.total_budget`, and passes invalid kwargs (`description`, `total_budget`, `travel_mode`, `is_suggested`) to `ItineraryCreatePayload(...)`. Crashes immediately with `AttributeError: 'ItineraryItem' object has no attribute 'start_time'`. |
| **BUG-13** | **Desktop Startup Import Crashes (`NameError`)** | **P0 Blocker** | `desktop_client/config/settings.py:376, 390, 442` & `desktop_client/main.py:133` | `settings.py` uses `Optional[str]` and `Optional[float]` without `from typing import Optional` (`NameError` on import). `main.py:133` uses `Optional[Any]` without importing `Any` (`NameError` on boot). Also `resolve_avatar_path` is defined twice in `settings.py` (`line 217` and `line 390`). |
| **BUG-14** | **Desktop Logout Button Crashes (`AttributeError`)** | **P0 Blocker** | `desktop_client/views/profile_view.py:1219` | `_confirm_logout()` references `ThemeColors.TEXT_PRIMARY_LIGHT`, which does not exist on `ThemeColors` (`TEXT_MAIN_LIGHT`), crashing before the Logout modal opens. |
| **BUG-15** | **Desktop Cloud Failover Silently Aborts on Localhost ConnectError** | **P0 Critical** | `desktop_client/core/api_client.py:169–170, 182` | When `127.0.0.1:8000` is unreachable, `ApiClient.request()` tries to fail over to `CLOUDFLARE_WORKER_API_URL`, but line 169 calls undefined `logger.info(...)` (`NameError`) and line 170 calls non-existent `self.set_base_url(worker_url)` (`AttributeError`). Both errors are swallowed by `except Exception: pass` on line 182, aborting failover! |
| **BUG-16** | **`TripDetailView` Adding Nearby Place Crashes** | **P1 High** | `desktop_client/views/trip_detail_view.py:471–480` | `_add_nearby_to_active_day()` passes invalid kwargs (`day_number`, `order_index`, `travel_mode`) and omits required args (`id`, `day_id`, `sort_order`) on `ItineraryItem(...)`, then assigns to read-only `@property` `self.itinerary.total_stops`. |
| **BUG-17** | **`TripDetailView` Nearby View Uses Narrow Category Filter Instead of `place_service.get_nearby_places()`** | **P2 Medium** | `desktop_client/views/trip_detail_view.py:537–543` | `_build_nearby_view()` filters `all_loaded` by exact `p.category == self.nearby_category` across the whole province instead of calling `self.place_service.get_nearby_places(municipality, self.nearby_category)` (which groups `restaurant`+`cafe`, `hospital_clinic`+`pharmacy`, `convenience_store`+`shopping_market`+`fuel_station`+`bank_atm` scoped to the active day's municipality, matching Web). |
| **BUG-18** | **Desktop `SavedTripsView` & `DashboardView` Flash Guest Trips When Logged In** | **P2 Medium** | `desktop_client/views/saved_trips_view.py:37` & `views/dashboard_view.py:50` | Both `__init__` constructors pre-load `self.itinerary_service.guest_storage.list_itineraries()` even when `session_manager.is_authenticated` is `True`. |
| **BUG-19** | **Profile Favorites Live Search Loses Focus on Every Keystroke** | **P1 High** | `desktop_client/views/profile_view.py:759–762, 806–813` | `ProfileView._on_fav_search_change()` calls `self._build_content()`, recreating `fav_search_field = ft.TextField(...)` on every character typed and dropping cursor focus. |
| **BUG-20** | **Scripts Hardcoded Path & Missing PyInstaller Hidden Imports** | **P2 Medium** | `scripts/run_daemon.py:7` & `scripts/build_standalone_exe.py:100–135` | `run_daemon.py:7` hardcodes `r"C:\Users\Edward\Desktop\CaseStudy"` instead of `Path(__file__).resolve().parent.parent`; `build_standalone_exe.py` omits `--hidden-import` flags for `connectivity_service`, `offline_data`, `polyline`, `commute_guide`, `favorites_service`, and view/component modules. |

---

## 2. Detailed Root-Cause Analysis of Your Observations

### 2.1 Why the Map Is Extremely Laggy & Why the Texture Changes Outside Nueva Ecija (`BUG-01`, `BUG-02`)

1. **Why the Map Texture Changes Outside Nueva Ecija (`desktop_client/components/slippy_map_canvas.py:48–102`)**:
   - Look at `_resolve_tile_source(zoom, x, y)` in `slippy_map_canvas.py`:
     - **Step 1 (`lines 49–55`)**: Checks `desktop_client/assets/tiles/{zoom}_{x}_{y}.png`. Those bundled PNGs were downloaded from **CartoDB Voyager / OpenStreetMap** covering only the bounding box of Nueva Ecija at zooms 10–14.
     - **Step 3 & 4 (`lines 71 & 101`)**: For any tile outside the bundled Nueva Ecija grid (or at zooms 15–18), `_resolve_tile_source()` returns:
       ```python
       f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{zoom}/{y}/{x}"
       ```
     - **ESRI ArcGIS World Street Map** has a khaki/shaded-relief background, heavy highway shields, and serif/Arial labels that clash sharply with CartoDB Voyager's clean light-slate vector style!
   - **Why a Gray Placeholder Appears Around the Edges When Dragging (`lines 590, 653–656`)**:
     - During drag (`_handle_pan_update`), `self._pan_layer.left = self._drag_dx` shifts the tile layer by up to `220px` before calling `redraw()`.
     - However, `_render_tiles()` (`lines 653–656`) only renders tiles from `min_tx` to `max_tx` and `min_ty` to `max_ty` (0 overscan tiles!). Shifting `_pan_layer` by even 20px immediately exposes the `#e2e8f0` gray container background (`self.bgcolor = "#e2e8f0"`), making the background look like a blank placeholder!

2. **Why the Map Is Extremely Laggy (`desktop_client/components/slippy_map_canvas.py:386–426, 581–640, 725–814`)**:
   - **Bottleneck 1 — Duplicate Nested `GestureDetector`s (`lines 386 & 418`)**: `gesture_surface` (inside `inner_stack`) and `self.content` (wrapping `inner_stack`) **both** attach `on_pan_start`, `on_pan_update`, `on_pan_end`, and `on_scroll` with `drag_interval=16`. Every mouse movement fires **two competing drag events per 16ms frame**!
   - **Bottleneck 2 — Unthrottled Dual `.update()` IPC Calls (`lines 596–601`)**: On every drag event, `_handle_pan_update` calls `self._pan_layer.update()` AND `self._marker_stack.update()` (two separate WebSocket round-trips to the Flutter client every 16ms).
   - **Bottleneck 3 — Recreating up to 180 Nested Marker Controls on Every Pan Commit (`lines 728, 766–814`)**: At `cell_size = 58.0`, zoom levels 10–13 produce ~130–180 clusters/markers. Every time drag crosses the overscan threshold or ends (`_handle_pan_end`), `_render_markers_and_clusters()` constructs 180 brand-new `ft.Container` trees and serializes all of them over Flet IPC!

---

### 2.2 Why the Desktop Notification Button Does Not Work (`BUG-03`)

In `desktop_client/views/dashboard_view.py:688–811` (`_on_bell_clicked`):
```python
    def _on_bell_clicked(self) -> None:
        self.unread_notifications = 0
        self._build_content()
        self._safe_update()
        if not self.safe_page:
            return
        ...
        self.safe_page.overlay.append(dlg)
        dlg.open = True
        self.safe_page.update()
```
1. **In Flet 1.1.2, `page.overlay.append(dlg); dlg.open = True` does NOT display an `ft.AlertDialog`!** Flet 1.1.2 requires `page.show_dialog(dlg)` (wrapped by `open_overlay_dialog(self.safe_page, dlg)` in `desktop_client/components/dialogs.py:43`). Because `_on_bell_clicked()` used `self.safe_page.overlay.append(dlg)`, clicking the bell hid the red `"1"` badge (`self.unread_notifications = 0`) and then **failed silently without opening any window or drawer**!
2. The exact same `page.overlay.append(dlg)` bug also breaks **11 other modals** across `dashboard_view.py` (`_open_popular_catalog_modal`), `places_view.py` (`_open_filter_modal`), `profile_view.py` (`_show_dialog` for Privacy, Clear Cache, and Log Out), `custom_builder_view.py` (all 7 builder modals), and `main.py` (`Discard Unsaved Changes?`).
3. Furthermore, on the [Trip mo, trip ko Web App](https://www.google.com/search?q=https://edselrenz.github.io/Itinerary-App/) (`home.page.html:240–335` & `home.page.ts:138–220`), the Notifications drawer includes a **`"Mark all read"`** button, an **`✕`** close button, unread blue indicator dots, timestamps, and **clickable notification cards** that navigate to `/suggested`, `/trips/{id}`, or `/map` when clicked.

---

### 2.3 Why the Desktop UI Does Not Change With Screen Size & Why `ProfileView` Is Stuck on the Left (`BUG-04`)

1. **Why `ProfileView` (and `CustomBuilderView` Step 1 `form`) Is Stuck on the Left Side**:
   - Look at `desktop_client/views/profile_view.py:303–323` (and `lines 567, 741, 925, 1018, 1071`):
     ```python
     return ft.Column(
         controls=[
             ft.Container(
                 width=560,
                 content=ft.Column(...),
             )
         ],
         horizontal_alignment=ft.CrossAxisAlignment.CENTER,
         scroll=ft.ScrollMode.AUTO,
         expand=True,
     )
     ```
   - In Flet 1.1.2 / Flutter, an `ft.Column(expand=True)` expands **vertically** along its main axis, **not horizontally**! Unless the `ft.Column` has `width=float("inf")` OR its child card is wrapped in `ft.Row(alignment=ft.MainAxisAlignment.CENTER, controls=[...])` (like `SuggestedWizardView` did at `suggested_wizard_view.py:528–537`), the `Column`'s width shrinks to `560px` and `ProfileView` places that `560px` column flush against the **top-left corner** of the screen!
   - The exact same bug exists in `CustomBuilderView._build_form_view()` (`custom_builder_view.py:572–577`), where `form_card` (`width=640`) is inside an `ft.Column` without `width=float("inf")` or `ft.Row(alignment=ft.MainAxisAlignment.CENTER)`.
2. **Why the Desktop UI Does Not Resize Dynamically With Window Size**:
   - In `desktop_client/main.py:389–393`:
     ```python
     def _on_page_resize(e):
         palette = settings.palette
         page.bgcolor = palette.bg_primary
         page.update()
     ```
     First, `_on_page_resize` crashes on `settings.palette` (`AttributeError`). Second, it **never notifies `content_area.content`** of the new `page.width` and `page.height`!
   - Meanwhile, `ResponsiveLayout.get_metrics(page_width, page_height)` in `desktop_client/config/settings.py:438–460` is **never called anywhere in any view**, and `PlacesView` (`places_view.py:301, 424`) hardcodes `SlippyMapCanvas(width=1366, height=768)` and `left=530`!

---

### 2.4 Why Dark Mode Fails on Desktop & On Web Login/Signup (`BUG-05`, `BUG-06`)

1. **Desktop Dark Mode (`BUG-05`)**:
   - Clicking **App Appearance** in `Profile -> Settings` calls `main.py:toggle_theme()`, which crashes at `main.py:115` (`settings.set_dark_mode(new_is_dark)` -> `AttributeError: 'Settings' object has no attribute 'set_dark_mode'`), `line 116` (`settings.palette`), `line 118` (`palette.bg_primary`), and `line 122` (`bottom_tab_bar.refresh_theme()`) **before `page.theme_mode` is ever changed**!
   - Even when `page.theme_mode = ft.ThemeMode.DARK` is set, `DashboardView`, `PlacesView`, `CustomBuilderView`, `SuggestedWizardView`, `SavedTripsView`, `TripDetailView`, `ProfileView`, `LoginView`, `SignupView`, `PlaceCard`, `StopCard`, `ItineraryRouteMap`, and `dialogs.py` all hardcode `ThemeColors.BG_LIGHT` (`#f8fafc`), `ThemeColors.SURFACE_LIGHT` / `ft.Colors.WHITE` (`#ffffff`), and `ThemeColors.TEXT_BLACK` (`#000000`) instead of using `ThemePalette.get_palette(is_dark)`!
2. **Web Dark Mode on Login, Signup, Welcome & Guest (`BUG-06`)**:
   - On the [Trip mo, trip ko Web App](https://www.google.com/search?q=https://edselrenz.github.io/Itinerary-App/), `Project/src/global.scss:3330` sets `ion-content { --background: #0b1120 !important; background: #0b1120 !important; color: #f1f5f9 !important }`, which turns the background of `<ion-content class="login-content">` and `<ion-content class="signup-content">` dark navy (`#0b1120`).
   - However, `login.page.scss` and `signup.page.scss` have **zero dark mode rules** and hardcode:
     - `.brand-title` (`"Trip mo, trip ko"`): `color: #000000;` (black text on `#0b1120` dark background — invisible!)
     - `.welcome-title` (`"Welcome Back!"`) & `.signup-title` (`"Create Your Account"`): `color: #000000;` (invisible!)
     - `.welcome-subtitle` & `.signup-subtitle`: `color: #475569;` (low contrast on `#0b1120`)
     - `.remember-text` (`"Remember me"`), `.footer-prompt` (`"Don't have an account?"`), & `.switch-prompt` (`"Already have an account?"`): `color: #000000;` (invisible!)
     - `.field-container`: `background: #ffffff; border: 1.2px solid #cbd5e1;` with `.native-field-input { color: #0f172a; }` (glaring white input boxes on dark navy!)
     - `.social-pill-btn`: `background: #ffffff; border: 1.2px solid #cbd5e1;` with `.social-btn-text { color: #000000; }` and `.apple-logo-icon { color: #000000; }` (glaring white buttons!)
   - And `welcome.page.scss` (`.welcome-screen-wrapper { background: #ffffff; }`) and `guest.page.scss` (`.guest-screen-container { background: #ffffff; }`, `.guest-content-section { background: #ffffff; }`) stay blinding white in Dark Mode!

---

## 3. Phased File-by-File Implementation Plan for Antigravity

Execute Phases 1 through 7 in order. Every code block is self-contained and ready to apply.

### Phase 1: Fix Map Texture Seam, Gray Placeholder Edges & Pan/Zoom Lag (`BUG-01`, `BUG-02`)

#### 1.1 `desktop_client/components/slippy_map_canvas.py`
1. **Unify Tile Provider to CartoDB Voyager / OpenStreetMap (`_resolve_tile_source`, `lines 37–102`)** so tiles inside and outside Nueva Ecija have the **exact same cartographic texture, colors, and typography** (matching the bundled `assets/tiles/` and the Web App's default CartoDB Voyager layer), and trigger an optional callback when a background tile finishes caching:

```python
def _resolve_tile_source(
    zoom: int,
    x: int,
    y: int,
    on_tile_cached: Optional[Callable[[str, str], None]] = None,
) -> str:
    """Returns local path to bundled/cached CartoDB Voyager/OSM tile or matching CDN URL."""
    tile_key = f"{zoom}_{x}_{y}"
    cached_src = _TILE_PATH_CACHE.get(tile_key)
    if cached_src:
        return cached_src

    settings = get_settings()

    # 1. Bundled assets (Zooms 10-14 pre-downloaded in desktop_client/assets/tiles)
    direct_cand = settings.assets_dir / "tiles" / f"{zoom}_{x}_{y}.png"
    if direct_cand.exists():
        cand_str = str(direct_cand)
        _TILE_PATH_CACHE[tile_key] = cand_str
        return cand_str

    # 2. Local disk cache inside assets_dir
    cache_dir = settings.assets_dir / "tiles_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"{zoom}_{x}_{y}.png"
    if cache_file.exists():
        c_str = str(cache_file)
        _TILE_PATH_CACHE[tile_key] = c_str
        return c_str

    # 3. Schedule background download from CartoDB Voyager (matching bundled Nueva Ecija tiles & Web app!)
    sub = ("a", "b", "c")[(x + y) % 3]
    voyager_url = f"https://{sub}.basemaps.cartocdn.com/rastertiles/voyager/{zoom}/{x}/{y}.png"

    if tile_key not in _QUEUED_TILES:
        _QUEUED_TILES.add(tile_key)

        def _fetch():
            urls = [
                voyager_url,
                f"https://tile.openstreetmap.org/{zoom}/{x}/{y}.png",
            ]
            for url in urls:
                req = urllib.request.Request(
                    url,
                    headers={
                        "User-Agent": "TripMoTripKo-NuevaEcija/3.0 (+https://edselrenz.github.io/Itinerary-App)",
                        "Accept": "image/png,image/*;q=0.8",
                    },
                )
                try:
                    with urllib.request.urlopen(req, timeout=5) as resp:
                        if resp.status == 200:
                            data = resp.read()
                            if len(data) > 250 and (data[:4] == b"\x89PNG" or data[:3] == b"\xff\xd8\xff"):
                                tmp = cache_file.with_suffix(".tmp")
                                tmp.write_bytes(data)
                                tmp.replace(cache_file)
                                c_path = str(cache_file)
                                _TILE_PATH_CACHE[tile_key] = c_path
                                if on_tile_cached:
                                    try:
                                        on_tile_cached(tile_key, c_path)
                                    except Exception:
                                        pass
                                break
                except Exception:
                    continue
            _QUEUED_TILES.discard(tile_key)

        _TILE_EXECUTOR.submit(_fetch)

    # 4. Return CartoDB Voyager direct URL immediately so texture never changes outside Nueva Ecija
    return voyager_url
```

2. **Add 1-Tile Overscan Ring in `_render_tiles()` (`lines 648–700`) & Warm Map Background (`#f4f1ea`)**:
   - Set `self.bgcolor = "#f4f1ea"` (matching CartoDB Voyager land tone instead of `#e2e8f0` slate gray).
   - Render `for tx in range(min_tx - 1, max_tx + 2):` and `for ty in range(min_ty - 1, max_ty + 2):` (a 1-tile overscan ring on all 4 sides!) so dragging `self._pan_layer` by up to `240px` never exposes blank edges!

3. **Eliminate Map Lag in `SlippyMapCanvas` (`lines 386–426, 581–640, 725–814`)**:
   - **Remove the inner duplicate `gesture_surface` (`lines 386–400`)**: Keep **only** the single outer `ft.GestureDetector` on `self.content` with `drag_interval=24`, eliminating competing gesture recognizers.
   - **Wrap `_pan_layer` and `_marker_stack` inside a single `self._viewport_mover = ft.Stack(left=0, top=0, width=self._map_w, height=self._map_h, controls=[self._pan_layer, self._marker_stack])`**:
     During `_handle_pan_update`, update only `self._viewport_mover.left = self._drag_dx`, `self._viewport_mover.top = self._drag_dy`, and call a **single** throttled `self._viewport_mover.update()` (at most once every `28ms` / ~35 FPS):
     ```python
     def _handle_pan_update(self, e: Any) -> None:
         dx, dy = _extract_pan_delta(e)
         if dx == 0.0 and dy == 0.0:
             return

         self._drag_dx += dx
         self._drag_dy += dy

         now = time.monotonic()
         if abs(self._drag_dx) < 240 and abs(self._drag_dy) < 240 and hasattr(self, "_viewport_mover"):
             self._viewport_mover.left = round(self._drag_dx, 1)
             self._viewport_mover.top = round(self._drag_dy, 1)
             if self.page is not None and (now - self._last_pan_redraw >= 0.028):
                 self._last_pan_redraw = now
                 try:
                     self._viewport_mover.update()
                 except Exception:
                     pass
             return

         cx, cy = latlon_to_world_px(self.center_lat, self.center_lng, self.zoom)
         new_lat, new_lng = world_px_to_latlon(cx - self._drag_dx, cy - self._drag_dy, self.zoom)
         self.center_lat, self.center_lng = self._clamp_center(new_lat, new_lng)
         self._drag_dx = 0.0
         self._drag_dy = 0.0
         self._viewport_mover.left = 0
         self._viewport_mover.top = 0
         self._last_pan_redraw = now
         self.redraw()
     ```
   - **Increase Cluster Grid `cell_size` from `58.0` to `84.0` (`line 728`) and Cap Rendered Markers at `64` (`line 789`)**: Reduces active marker controls per frame by ~70% while matching Web Leaflet's `maxClusterRadius: 80`.
   - **Add `resize_canvas(self, new_w: int, new_h: int) -> None`** on `SlippyMapCanvas` so `PlacesView` can resize the map dynamically when the window resizes!

---

### Phase 2: Fix Desktop Notification Bell Modal & All 11 `page.overlay.append` Modals (`BUG-03`)

#### 2.1 `desktop_client/views/dashboard_view.py`
1. At the top of `desktop_client/views/dashboard_view.py`, import `open_overlay_dialog`, `close_overlay_dialog`, and `show_toast` from `desktop_client.components.dialogs`.
2. Replace `_on_bell_clicked()` (`lines 688–811`) so it opens reliably via `open_overlay_dialog(self.safe_page, dlg)` (`page.show_dialog(dlg)`) and matches Web's Notifications drawer (`"Mark all read"`, `✕` close button, unread badges, and clickable notification cards that navigate to `/suggested`, `/trips/{id}`, or `/map`):

```python
    def _on_bell_clicked(self) -> None:
        """Opens Travel Advisories & Notifications Modal matching Web home.page.html (UI-19)."""
        if not self.safe_page:
            return

        self.unread_notifications = 0
        self._build_content()
        self._safe_update()

        from desktop_client.components.dialogs import close_overlay_dialog, open_overlay_dialog
        from desktop_client.core.storage import get_guest_storage

        palette = self.settings.palette
        guest_count = len(get_guest_storage().list_itineraries())
        is_guest = self.session_manager.is_guest

        def _close_notif(_=None):
            close_overlay_dialog(self.safe_page, dlg)

        def _nav_from_notif(target_route: str, trip_obj: Optional[Itinerary] = None):
            close_overlay_dialog(self.safe_page, dlg)
            if self.on_navigate:
                if trip_obj is not None:
                    self.on_navigate(target_route, trip_obj)
                else:
                    self.on_navigate(target_route)

        def _notif_card(icon, icon_color, icon_bg, title, message, timestamp, action_label, on_click):
            return ft.Container(
                bgcolor=palette.surface_card_hover if palette.is_dark else "#f8fafc",
                border=ft.Border.all(1, palette.border_main),
                border_radius=14,
                padding=12,
                ink=True,
                on_click=lambda _: on_click(),
                content=ft.Row(
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    controls=[
                        ft.Container(
                            width=36,
                            height=36,
                            border_radius=10,
                            bgcolor=icon_bg,
                            alignment=ft.Alignment(0, 0),
                            content=ft.Icon(icon, color=icon_color, size=19),
                        ),
                        ft.Column(
                            spacing=3,
                            expand=True,
                            controls=[
                                ft.Row(
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    controls=[
                                        ft.Text(title, size=13, weight=ft.FontWeight.BOLD, color=palette.text_primary, expand=True),
                                        ft.Text(timestamp, size=10, color=palette.text_faint),
                                    ],
                                ),
                                ft.Text(message, size=11.5, color=palette.text_muted),
                                ft.Row(
                                    spacing=4,
                                    controls=[
                                        ft.Text(action_label, size=11, weight=ft.FontWeight.BOLD, color=ThemeColors.PRIMARY_BLUE),
                                        ft.Icon(ft.Icons.ARROW_FORWARD_ROUNDED, size=12, color=ThemeColors.PRIMARY_BLUE),
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
            )

        notif_items: list[ft.Control] = [
            _notif_card(
                icon=ft.Icons.WB_SUNNY_ROUNDED,
                icon_color=ThemeColors.WARM_GOLD,
                icon_bg=ThemeColors.AMBER_LIGHT,
                title="Pantabangan & Upland Travel Advisory",
                message="Prepare cash when visiting Pantabangan Lake & Highland Bali. Cellular signals and ATM availability in upland barangays are limited.",
                timestamp="Just now",
                action_label="Plan Upland Trip",
                on_click=lambda: _nav_from_notif("/suggested?destination=Pantabangan"),
            ),
            _notif_card(
                icon=ft.Icons.MAP_ROUNDED,
                icon_color=ThemeColors.EMERALD_PRIMARY,
                icon_bg=ThemeColors.SUCCESS_BG,
                title="Offline Map & 2,673 POIs Ready",
                message="All 32 Nueva Ecija municipalities and curated landmarks are cached locally for offline mountain and rural navigation.",
                timestamp="15m ago",
                action_label="Explore Interactive Map",
                on_click=lambda: _nav_from_notif("/map"),
            ),
        ]

        if self.saved_itineraries:
            upcoming = self.saved_itineraries[0]
            notif_items.insert(
                0,
                _notif_card(
                    icon=ft.Icons.AIRPLANEMODE_ACTIVE,
                    icon_color=ThemeColors.PRIMARY_BLUE,
                    icon_bg=ThemeColors.AZURE_SOFT,
                    title=f"Upcoming Trip: {upcoming.title}",
                    message=f"Scheduled for {upcoming.start_date or 'soon'} in {upcoming.destination or 'Nueva Ecija'} ({len(upcoming.days)} days).",
                    timestamp="Active Plan",
                    action_label="Open Itinerary",
                    on_click=lambda: _nav_from_notif(f"/trips/{upcoming.id}", upcoming),
                ),
            )

        if is_guest and guest_count > 0:
            notif_items.append(
                _notif_card(
                    icon=ft.Icons.CLOUD_OFF,
                    icon_color=ThemeColors.ERROR,
                    icon_bg=ThemeColors.ERROR_BG,
                    title=f"{guest_count} Itinerar{'ies' if guest_count > 1 else 'y'} in Local Guest Mode",
                    message="Your itineraries are stored on this device only. Log in or sign up to sync them permanently to your cloud account.",
                    timestamp="Sync Notice",
                    action_label="Sign In to Sync",
                    on_click=lambda: _nav_from_notif("/login"),
                )
            )

        dlg = ft.AlertDialog(
            bgcolor=palette.surface_card,
            title=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Row(
                        spacing=8,
                        controls=[
                            ft.Icon(ft.Icons.NOTIFICATIONS_ACTIVE, color=ThemeColors.PRIMARY_BLUE, size=20),
                            ft.Column(
                                spacing=1,
                                controls=[
                                    ft.Text("Notifications", size=16, weight=ft.FontWeight.W_800, color=palette.text_primary),
                                    ft.Text("Travel reminders & itinerary updates", size=11, color=palette.text_muted),
                                ],
                            ),
                        ],
                    ),
                    ft.IconButton(icon=ft.Icons.CLOSE_ROUNDED, icon_color=palette.text_muted, on_click=_close_notif),
                ],
            ),
            content=ft.Container(
                width=460,
                content=ft.Column(controls=notif_items, spacing=10, tight=True, scroll=ft.ScrollMode.AUTO),
            ),
            actions=[
                ft.TextButton("Close", on_click=_close_notif),
            ],
        )
        open_overlay_dialog(self.safe_page, dlg)
```

3. Replace `self.safe_page.overlay.append(dlg); dlg.open = True` and `dlg.open = False` with `open_overlay_dialog(self.safe_page, dlg)` and `close_overlay_dialog(self.safe_page, dlg)` in:
   - `DashboardView._open_popular_catalog_modal()` (`dashboard_view.py:908, 932`)
   - `PlacesView._open_filter_modal()` (`places_view.py:1187, 1259`)
   - `ProfileView._show_dialog()` and `_close_dialog()` (`profile_view.py:1255–1264`)
   - `CustomBuilderView` (`custom_builder_view.py:173, 191, 278, 302, 600, 623, 1338, 1362, 1395, 1447, 1483, 1502, 1612, 1706`)
   - `main.py` (`main.py:175, 180, 199`)

---

### Phase 3: Fix Desktop Responsive Layout & Left-Stuck Views (`ProfileView`, `CustomBuilderView`, `DashboardView`, `PlacesView`, `SavedTripsView`, `TripDetailView`) (`BUG-04`)

#### 3.1 `desktop_client/main.py`
Update `_on_page_resize(e)` (`lines 389–393`) so resizing the window never crashes and immediately calls `on_resize(w, h)` (or `_rebuild()`) on the active view in `content_area.content`:

```python
    def _on_page_resize(e: Any = None) -> None:
        palette = settings.palette
        page.bgcolor = palette.bg_main
        if content_area:
            content_area.bgcolor = palette.bg_main
            active_ctrl = content_area.content
            if active_ctrl is not None:
                if hasattr(active_ctrl, "on_resize") and callable(active_ctrl.on_resize):
                    try:
                        active_ctrl.on_resize(float(page.width or 1280), float(page.height or 840))
                    except Exception:
                        pass
                elif hasattr(active_ctrl, "_build_content") and callable(active_ctrl._build_content):
                    try:
                        active_ctrl._build_content()
                        active_ctrl.update()
                    except Exception:
                        pass
        page.update()

    page.on_resized = _on_page_resize
```

#### 3.2 `desktop_client/views/profile_view.py`
Fix the **left-stuck layout** and **responsive width scaling** across all 6 subviews (`profile`, `edit`, `settings`, `favorites`, `help`, `about`) in `ProfileView`:
1. In `ProfileView.__init__`, set `self.alignment = ft.Alignment(0, -1)` and add a helper `_get_card_width(self, narrow: bool = False) -> float`:
   ```python
   def _get_card_width(self, narrow: bool = False) -> float:
       from desktop_client.config.settings import ResponsiveLayout
       pw = float(self.safe_page.width) if (self.safe_page and self.safe_page.width) else 1280.0
       metrics = ResponsiveLayout.get_metrics(pw)
       if metrics["is_mobile"]:
           return max(300.0, pw - 36.0)
       if narrow:
           return min(520.0, max(420.0, pw * 0.46))
       return min(720.0, max(560.0, pw * 0.56))
   ```
2. Add a helper `_wrap_centered_scroll(self, inner_card: ft.Control) -> ft.Control` and use it as the return value of `_build_main_profile_view()`, `_build_edit_profile_subview()`, `_build_settings_subview()`, `_build_favorites_subview()`, `_build_help_subview()`, and `_build_about_subview()`:
   ```python
   def _wrap_centered_scroll(self, inner_card: ft.Control) -> ft.Control:
       return ft.Column(
           controls=[
               ft.Row(
                   alignment=ft.MainAxisAlignment.CENTER,
                   controls=[inner_card],
               )
           ],
           horizontal_alignment=ft.CrossAxisAlignment.CENTER,
           scroll=ft.ScrollMode.AUTO,
           expand=True,
           width=float("inf"),
       )
   ```
   Wrapping `inner_card` inside `ft.Row(alignment=ft.MainAxisAlignment.CENTER)` + `ft.Column(..., width=float("inf"), expand=True)` guarantees `ProfileView` is **always horizontally centered** and scales smoothly from `560px` up to `720px` as the window widens (and down to `pw - 36` on narrow windows)!
3. Also in `ProfileView._build_favorites_subview()` (`line 806`), persist `self._fav_search_field` across updates and only refresh `self._fav_cards_col.controls` inside `_on_fav_search_change()` so typing in the Favorites search bar never loses cursor focus (`BUG-19`).

#### 3.3 `desktop_client/views/custom_builder_view.py`, `views/dashboard_view.py`, `views/saved_trips_view.py`, `views/trip_detail_view.py` & `views/places_view.py`
1. **`CustomBuilderView._build_form_view()` (`custom_builder_view.py:551–577`)**: Wrap `form_card` inside `ft.Row(alignment=ft.MainAxisAlignment.CENTER, controls=[form_card])` inside `ft.Column(..., width=float("inf"), expand=True)` so Step 1 (`form`) is centered instead of stuck on the left, and compute `form_card.width` via `ResponsiveLayout.get_metrics()`.
2. **`DashboardView` (`dashboard_view.py:140–160`) & `TripDetailView` (`trip_detail_view.py:415–435`)**: Wrap `main_column` in a centered responsive container (`max_width = metrics["dashboard_max_width"]` on Dashboard, `min(860, pw - 48)` on TripDetailView) inside `ft.Row(alignment=ft.MainAxisAlignment.CENTER)` so content centers cleanly and scales with window width.
3. **`PlacesView` (`places_view.py:301, 424`)**:
   - Compute `map_w = int(self.safe_page.width or 1280)` and `map_h = int((self.safe_page.height or 840) - 60)` dynamically instead of hardcoding `1366x768`.
   - Center the bottom `"List View"` pill dynamically using `left=0, right=0, alignment=ft.Alignment(0, 0)` (or `left=max(16, int((map_w - 160) / 2))`) instead of hardcoded `left=530`!
   - Implement `on_resize(self, width: float, height: float) -> None` on `PlacesView` to call `self.map_component.resize_canvas(int(width), int(height - 60))` and update the `"List View"` pill position.

---

### Phase 4: Fix Dark Mode Across Both Desktop and Web (Including Web Login & Signup!) (`BUG-05`, `BUG-06`)

#### 4.1 Web Dark Mode for Login, Signup, Welcome & Guest (`Project/src/global.scss` & `login.page.scss`, `signup.page.scss`, `welcome.page.scss`, `guest.page.scss`) (`BUG-06`)
Add the following rules inside `html.dark, body.dark { ... }` in `Project/src/global.scss` (and in `login.page.scss`, `signup.page.scss`, `welcome.page.scss`, `guest.page.scss`) so **Login, Signup, Welcome, and Guest** render with crisp dark surfaces and light text in Dark Mode:

```scss
html.dark,
body.dark {
  /* Auth & Onboarding Containers (Login, Signup, Welcome, Guest) */
  .login-content,
  .signup-content,
  .welcome-content,
  .guest-page-content,
  .login-screen-container,
  .signup-screen-container,
  .welcome-screen-wrapper,
  .guest-screen-container,
  .guest-content-section {
    --background: #0b1120 !important;
    background: #0b1120 !important;
    color: #f8fafc !important;
  }

  /* Auth Titles & Prompts that were hardcoded #000000 */
  .brand-title,
  .welcome-title,
  .signup-title,
  .hero-headline,
  .guest-title,
  .remember-text,
  .footer-prompt,
  .switch-prompt {
    color: #f8fafc !important;
  }

  .welcome-subtitle,
  .signup-subtitle,
  .hero-subtitle,
  .guest-subtitle,
  .or-divider-text,
  .divider-text {
    color: #94a3b8 !important;
  }

  .or-divider-line,
  .divider-line {
    background: #334155 !important;
    background-color: #334155 !important;
  }

  /* Login & Signup Input Fields */
  .field-container {
    background: #1e293b !important;
    border-color: #334155 !important;

    &:focus-within {
      border-color: #38bdf8 !important;
      box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.18) !important;
    }
  }

  .native-field-input {
    color: #f8fafc !important;

    &::placeholder {
      color: #64748b !important;
    }
  }

  /* Google / Apple Social Pill Buttons & Guest Outline Buttons */
  .social-pill-btn,
  .guest-pill-btn,
  .outline-pill-btn {
    background: #1e293b !important;
    border-color: #334155 !important;
    color: #f8fafc !important;

    .social-btn-text {
      color: #f8fafc !important;
    }

    .apple-logo-icon {
      color: #f8fafc !important;
    }

    &:active {
      background: #0f172a !important;
    }
  }

  .floating-back-btn {
    background: rgba(15, 23, 42, 0.65) !important;
    color: #f8fafc !important;
  }
}
```

#### 4.2 Desktop Dark Mode Engine & All Views/Cards (`BUG-05`, `BUG-13`, `BUG-14`)
1. **In `desktop_client/config/settings.py`**:
   - Add `from typing import Any, Optional` at the top (`BUG-13`).
   - Add `TEXT_PRIMARY_LIGHT: str = "#0f172a"` to `ThemeColors` (`BUG-14`).
   - Add `_is_dark_mode: bool = field(default=False, init=False)`, `set_dark_mode(self, is_dark: bool) -> None`, and `@property def palette(self) -> "ThemePalette"` on `Settings`.
   - Add `@property def bg_primary(self) -> str: return self.bg_main` on `ThemePalette`.
2. **In `desktop_client/components/bottom_tab_bar.py`**:
   - Add `def refresh_theme(self) -> None:` calling `self._build_content()` and `self.update()`.
   - Use `palette.text_muted` for inactive tab icon/text color.
3. **In `desktop_client/main.py`**:
   - Import `Any` alongside `Optional` (`from typing import Any, Optional`).
4. **Update All Desktop Views & Components to Read `palette = get_settings().palette`**:
   - In `DashboardView`, `ProfileView`, `SavedTripsView`, `TripDetailView`, `CustomBuilderView`, `SuggestedWizardView`, `PlacesView`, `LoginView`, `SignupView`, `PlaceCard`, `StopCard`, `ItineraryRouteMap`, and `dialogs.py`:
     - Replace `self.bgcolor = ThemeColors.BG_LIGHT` with `self.bgcolor = palette.bg_main` inside `_build_content()`.
     - Replace card `bgcolor=ThemeColors.SURFACE_LIGHT` / `ft.Colors.WHITE` with `bgcolor=palette.surface_card` and `border=ft.Border.all(1, palette.border_main)`.
     - Replace heading/body `color=ThemeColors.TEXT_BLACK` / `ThemeColors.TEXT_MAIN_LIGHT` with `color=palette.text_primary`, and `ThemeColors.TEXT_MUTED_LIGHT` with `color=palette.text_muted`.
     - Replace `ft.TextField` `bgcolor=ft.Colors.WHITE` with `bgcolor=palette.input_bg`, `border_color=palette.input_border`, and `text_style=ft.TextStyle(color=palette.text_primary)`.

---

### Phase 5: Fix Custom Itinerary Creation, Back-Button Loop & Post-Save Crash (`BUG-07`, `BUG-08`, `BUG-09`, `BUG-16`, `BUG-17`)

1. **`desktop_client/views/trip_detail_view.py` (`BUG-07`, `BUG-16`, `BUG-17`)**:
   - At line 391, change `float(itm.estimated_cost or 0.0)` to `float(itm.representative_cost)` so opening `TripDetailView` after saving a Custom or Suggested Itinerary never throws `AttributeError: 'ItineraryItem' object has no attribute 'estimated_cost'`!
   - In `_add_nearby_to_active_day()` (`lines 467–484`), construct `ItineraryItem` using valid fields (`id=str(uuid.uuid4())`, `day_id=active_day.id`, `sort_order=len(active_day.items) + 1`, `place_id=place.id`, `place=place`, `custom_title=place.name`, `custom_lat=place.latitude`, `custom_lng=place.longitude`, `planned_time="02:00 PM"`, `duration_minutes=60`, `estimated_cost_min=place.estimated_cost_min`, `estimated_cost_max=place.estimated_cost_max`) and remove `self.itinerary.total_stops = ...`.
   - In `_build_nearby_view()` (`lines 537–543`), use `matching = self.place_service.get_nearby_places(self.itinerary.destination, self.nearby_category)` instead of exact `p.category == self.nearby_category`.
2. **`desktop_client/views/custom_builder_view.py` (`BUG-08`, `BUG-09`)**:
   - In `did_mount()` (`line 131`), replace `await self.place_service.list_places()` with `await self.place_service.get_places(page=1, page_size=250)`.
   - In `handle_back()` (`lines 138–167`), check `if self.active_view == "browse":` (step to `"timeline"` if `total_stops_count > 0` else `"form"`) and `elif self.active_view == "timeline" and self.existing_itinerary is None and not self.is_draft_from_wizard:` (step to `"form"`) **before** checking `if self.is_dirty: self._prompt_discard_changes()` so clicking `←` steps cleanly back through the builder views without popping the exit modal!
   - In `_open_custom_venue_dialog()` (`line 1554`), update `coords_toggle_btn.content = ft.Text(...)` instead of `coords_toggle_btn.text = ...`.

---

### Phase 6: Fix `"✨ Start Trip Here"` End-to-End Across Map, Wizard, Services & Backend (`BUG-10`, `BUG-11`, `BUG-12`)

1. **`desktop_client/views/suggested_wizard_view.py` (`BUG-11`, `BUG-12`)**:
   - In `__init__` (`lines 106–112`), resolve `self.anchor_place` from `self.place_service.get_loaded_places()` when `anchor_place_id` is passed, and if `self.anchor_place.municipality_name` is present, set `self.destination_val = self.anchor_place.municipality_name`.
   - Render an anchor badge in `_build_wizard_form()` when `self.anchor_place` is set (`"✨ Starting Trip at {self.anchor_place.name} (Locked as Stop 1, Day 1)"`).
   - In `_save_generated_itinerary()` (`lines 1294–1348`), replace the broken manual dictionary loop (which crashed on `item.start_time`, `item.estimated_cost`, `d.date`, `d.theme`, `self.generated_itinerary.description`, `self.generated_itinerary.total_budget`) with `payload = self.generated_itinerary.to_create_payload()`.
2. **`backend/app/schemas/itinerary.py` & `backend/app/algorithms/itinerary_generator.py` (`BUG-10`)**:
   - In `SuggestedItineraryRequest` (`backend/app/schemas/itinerary.py:314–322`), preserve non-UUID `anchor_place_id` strings inside `anchor_place_payload["id"]` before coercing `anchor_place_id` to `uuid.UUID | None`.
   - In `generate_suggested_itinerary_data()` (`backend/app/algorithms/itinerary_generator.py:216–395`), resolve `anchor_place` from `request.anchor_place_id` or `request.anchor_place_payload` (matching by `id`, `source_record_id`, `google_place_id`, or `name`, or upserting via `google_maps_service.upsert_google_place_to_db`), center `(anchor_lat, anchor_lng)` on `(anchor_place.latitude, anchor_place.longitude)`, lock `anchor_place` into **Day 1 Slot 0 (Stop 1)**, and keep `day_items[0]` pinned at index 0 during the 2-Opt permutation!
3. **`desktop_client/services/itinerary_service.py`, `Project/src/app/core/services/itinerary.service.ts` & `Project/src/app/tabs/map/map.page.ts` (`BUG-11`)**:
   - In `desktop_client/services/itinerary_service.py:224–236`, merge `get_place_service().get_loaded_places()` into `curated_pool`, and on `d_idx == 0` when `request.anchor_place_id` is set, keep `day_places[0]` pinned as Stop 1 even if `is_lodging` is `True`.
   - In `Project/src/app/tabs/map/map.page.ts:990`, set `destination: place.municipality_name || 'Nueva Ecija'` instead of `place.municipality_name || place.name`.
   - In `Project/src/app/core/services/itinerary.service.ts:1082–1086, 1147–1155`, always push `anchorPlace` on Day 1 (even on 1-day trips for resorts/hotels) and keep `anchorPlace` pinned at index 0 rather than moving it to `accommodations` at the end of the day.

---

### Phase 7: Fix Cloud Failover, Guest Storage Isolation & Scripts (`BUG-15`, `BUG-18`, `BUG-20`)

1. **`desktop_client/core/api_client.py` (`BUG-15`)**:
   - Add `import logging; logger = logging.getLogger(__name__)` at the top of `api_client.py` and add `def set_base_url(self, val: str) -> None: self._explicit_base_url = val.rstrip("/") if val else None` on `ApiClient` so automatic failover from `127.0.0.1:8000` to [NE Itinerary API Worker](https://www.google.com/search?q=https%3A%2F%2Fwww.google.com%2Furl%3Fsa%3DE%26source%3Dgmail%26q%3Dhttps%3A%2F%2Fne-itinerary-api.edselrenz0.workers.dev%2Fapi%2Fv1) succeeds!
2. **`desktop_client/views/saved_trips_view.py:37` & `views/dashboard_view.py:50` (`BUG-18`)**:
   - Only pre-load `guest_storage.list_itineraries()` in `__init__` when `not self.session_manager.is_authenticated`.
3. **`scripts/run_daemon.py` & `scripts/build_standalone_exe.py` (`BUG-20`)**:
   - In `scripts/run_daemon.py:7`, use `project_root = str(Path(__file__).resolve().parent.parent)` instead of hardcoded `r"C:\Users\Edward\Desktop\CaseStudy"`.
   - In `scripts/build_standalone_exe.py:100–135`, include `--hidden-import` flags for `desktop_client.core.connectivity_service`, `desktop_client.core.offline_data`, `desktop_client.core.polyline`, `desktop_client.core.commute_guide`, `desktop_client.services.favorites_service`, and all `desktop_client.components.*` and `desktop_client.views.*` modules.

---

## 4. Cycle 3 End-to-End QA Verification Checklist (`TC-01` to `TC-20`)

| Test ID | Focus Area | Verification Steps | Expected Result |
| :--- | :--- | :--- | :--- |
| **TC-01** | Map Tile Uniformity (`BUG-01`) | Open Map tab on Desktop, pan across the borders of Nueva Ecija, and zoom from Z10 to Z16. | Uses CartoDB Voyager tiles uniformly inside and outside Nueva Ecija; texture never switches to ESRI World Street Map, and 1-tile overscan prevents gray placeholder edges during drag. |
| **TC-02** | Map 60 FPS Pan/Zoom (`BUG-02`) | Drag the map rapidly and scroll-wheel zoom in/out with 2,673 POIs loaded. | Single `GestureDetector` + throttled `_viewport_mover.update()` + `84px` cluster grid delivers smooth, lag-free panning and zooming. |
| **TC-03** | Desktop Notification Bell (`BUG-03`) | Click the Notification Bell icon on the Home tab (`DashboardView`). | Opens the Notifications modal via `open_overlay_dialog` (`page.show_dialog`), clears the red badge, and clicking any notification card navigates to its target route. |
| **TC-04** | All Desktop Modals (`BUG-03`) | Test Popular Catalog (`See all`), Map `Filters`, Profile `Privacy` / `Clear Cache` / `Log Out`, and Custom Builder `Add Off-Grid Venue` / `Edit Stop`. | All 12 modals open and close cleanly via `open_overlay_dialog` / `close_overlay_dialog` (`page.show_dialog` / `page.pop_dialog`). |
| **TC-05** | Centered & Responsive `ProfileView` (`BUG-04`) | Open the `Profile` tab and its 5 subviews (`Edit`, `Settings`, `Favorites`, `Help`, `About`), and resize the Desktop window from `1080px` to `1920px`. | Profile and all subviews are horizontally centered (`ft.Row(alignment=CENTER)`)—never stuck on the left—and scale card widths smoothly via `ResponsiveLayout`. |
| **TC-06** | Responsive Map & Builder (`BUG-04`) | Resize the Desktop window while on `/map` and `/builder`. | `_on_page_resize` resizes `SlippyMapCanvas` to fill the window, keeps the `"List View"` pill centered, and centers the Custom Builder Step 1 form. |
| **TC-07** | Desktop Dark Mode (`BUG-05`) | Open `Profile -> Settings` and toggle `App Appearance (Light / Dark)`, then inspect all views and cards. | Switches themes without `AttributeError`; all 9 views and cards (`PlaceCard`, `StopCard`, `ItineraryRouteMap`) switch to dark slate surfaces (`#0b0f19` / `#151e2e`) with light readable text (`#f8fafc`). |
| **TC-08** | Web Dark Mode on Login, Signup, Welcome & Guest (`BUG-06`) | Enable Dark Mode on Web, then log out and inspect `/welcome`, `/guest`, `/login`, and `/signup`. | All titles (`.brand-title`, `.welcome-title`, `.signup-title`, `.guest-title`), checkboxes (`.remember-text`), and prompts render in `#f8fafc` light text, and input boxes/social buttons use `#1e293b` dark slate. |
| **TC-09** | Custom Itinerary Create & Save (`BUG-07`) | Create a Custom Itinerary, add 2 stops, and click `✓ Save` / `💾 View Full Itinerary / Save Trip`. | Saves and navigates to `TripDetailView` (`/trips/{id}`) without throwing `'ItineraryItem' object has no attribute 'estimated_cost'`. |
| **TC-10** | Custom Builder Back Button (`BUG-08`) | Select a budget preset on Step 1 (`form`), advance to `browse`, add a stop, go to `timeline`, and click `←`. | Steps cleanly from `browse` -> `timeline` -> `form` (`View 0`) without popping `"Discard Changes?"`; only prompts when leaving `form`. |
| **TC-11** | Map `"✨ Start Trip Here"` Online & Offline (`BUG-10`, `BUG-11`) | Click any POI on the Map (including a resort/hotel or OSM POI), click `✨ Start Trip Here`, and click `Find Itinerary`. | Pre-fills the POI's municipality, shows the anchor banner, and locks that exact POI as **Stop 1 of Day 1** both online (FastAPI generator) and offline. |
| **TC-12** | Suggested Wizard Save (`BUG-12`) | Click `✓ Accept & Save Itinerary` on a generated Suggested Itinerary on Desktop. | Converts via `to_create_payload()`, saves to cloud/guest storage without `AttributeError: 'ItineraryItem' object has no attribute 'start_time'`, and opens `TripDetailView`. |
| **TC-13** | Cloud Failover & Account/Trip Sync (`BUG-15`, `BUG-18`) | Log in and create/edit/delete an itinerary on Web and verify on Desktop (with local port 8000 stopped so Desktop fails over to Cloudflare Worker). | `ApiClient` fails over to `https://ne-itinerary-api.edselrenz0.workers.dev/api/v1` and syncs accounts and saved itineraries 1:1 across both apps. |
