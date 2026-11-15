# GEMINI ANTIGRAVITY MASTER EXECUTION & PARITY PLAN (v3.0 — Deep Full-Stack Code Audit Edition)
**Project**: *Trip mo, trip ko — Nueva Ecija* (Web App + Responsive Flet Desktop & Mobile App + FastAPI Backend + Cloudflare Tunnel Proxy)
**Reference Web Application**: [Trip mo, trip ko — Nueva Ecija Web App](https://edselrenz.github.io/Itinerary-App/#/welcome)
**Target Architectures**:
1. **Desktop & Mobile Unified Client (`desktop_client/`)** — Python Flet 1.1.2 responsive application targeting Windows/macOS/Linux Desktop (`>= 768px`) and Android/iOS Mobile (`< 768px`, replacing Capacitor).
2. **Web Application (`Project/`)** — Ionic 8 / Angular 20 SPA deployed on GitHub Pages ([https://edselrenz.github.io/Itinerary-App/#/welcome](https://edselrenz.github.io/Itinerary-App/#/welcome)).
3. **Backend API & Proxy (`backend/`, `cloudflare-worker/`, `scripts/`)** — FastAPI + SQLAlchemy (`Session`) + Cloudflare Worker (`ne-itinerary-api.edselrenz0.workers.dev`) + Multi-Tunnel Daemon (`Cloudflare Quick Tunnel` + `ngrok`).

---

## SECTION 1: EXECUTIVE ROOT-CAUSE MATRIX (9 USER-REPORTED REGRESSIONS + 15 NEWLY DISCOVERED CODEBASE BUGS)

### Part A — The 9 User-Reported Post-Update Regressions

| ID | User-Reported Problem | Exact Root Cause (File & Line Numbers) | Definitive Architectural Fix |
| :--- | :--- | :--- | :--- |
| **ISSUE-01** | **Profile Picture Replaced by Placeholder on Login** | 1. **Web App (`Project/src/app/tabs/profile/profile.page.ts:104-121`)**: `uploadAvatarFile()` saves custom base64 photos to `localStorage` (`user_profile`), and only sends `PATCH /api/v1/auth/me` if the tunnel is reachable. When `refreshProfileFromBackend()` runs on login (`lines 58-72`), `res.avatar_url` from PostgreSQL (seeded as `/assets/avatars/default-traveler.png` or `placeholder.svg`) **overwrites** the user's custom `data:image/...` avatar in `localStorage`!<br>2. **Desktop App (`desktop_client/views/profile_view.py:217-244`)**: Flet 1.1.2 Desktop removed `Image.src_base64` and passes `src="data:image/jpeg;base64,..."` to Flutter's image loader, which fails on long base64 data URIs or relative `/assets/...` strings, falling back to `placeholder-place.svg`. | 1. **Web (`profile.page.ts`)**: Never overwrite a custom `data:image/...` or HTTP avatar in `localStorage` with a backend placeholder (`placeholder` / `default-traveler`); instead, automatically push the local custom `avatar_url` to `PATCH /api/v1/auth/me`.<br>2. **Desktop (`desktop_client/config/settings.py`)**: Add `resolve_avatar_path(avatar_url)` which decodes `data:image/...;base64,...` strings into `desktop_client/assets/avatars_cache/avatar_<sha1>.png` and returns relative asset path `"avatars_cache/avatar_<sha1>.png"`, which Flet 1.1.2 `ft.Image(src=...)` renders natively at 100% reliability.<br>3. **Desktop (`main.py` & `auth_service.py`)**: Call `auth_service.fetch_current_user()` on startup/login and trigger `session_manager` listeners so `ProfileView` immediately updates. |
| **ISSUE-02** | **Settings -> App Appearance -> Dark Mode Does Nothing & Jumps Back to Profile Tab** | 1. **Static Colors (`desktop_client/config/settings.py:13-53` & all views)**: Although `ThemeColors` has `_ThemeColorsMeta`, every view (`profile_view.py`, `places_view.py`, `custom_builder_view.py`, `suggested_wizard_view.py`, `saved_trips_view.py`, `dashboard_view.py`) hardcodes `"#FFFFFF"`, `"#F8FAFC"`, and `"#0F172A"` literals instead of reading `self.palette.surface` / `ThemeColors.BG_SECONDARY` at render time.<br>2. **Subview Reset (`desktop_client/main.py:157-166`)**: `toggle_theme()` calls `navigate_to(current_route)`, which instantiates a brand-new `ProfileView(...)` where `self._subview` defaults to `"profile"` (`profile_view.py:55`), kicking the user out of `"settings"` back to `"profile"`! | 1. Preserve `active_view._subview` inside `main.py:toggle_theme()` before rebuilding `ProfileView`, and restore `new_view._subview = saved_subview; new_view._rebuild()` so the user stays right inside **Settings**.<br>2. Route all container backgrounds, cards, inputs, borders, and text colors through `self.palette` (`get_settings().palette`) and `ThemeColors` dynamic properties so toggling `Light` / `Dark` re-themes every view immediately. |
| **ISSUE-03** | **Saved Itineraries Do Not Load or Sync Between Web App & Desktop App** | 1. **Missing `did_mount()` (`desktop_client/views/saved_trips_view.py:44, 414-422`)**: `_load_trips()` is called in `__init__()` when `self.safe_page` is still `None`! Because `main(page)` is synchronous, `asyncio.get_running_loop()` raises `RuntimeError` (silently caught by `except RuntimeError: pass`), so **`list_itineraries()` is NEVER executed**!<br>2. **Backend 422 & 404 Rejections (`backend/app/schemas/itinerary.py:13` & `api/v1/itineraries.py:252-260`)**: Saving a trip on Web sends `place: it.place` (not `place_payload`) and non-UUID `place_id`s (`"dest-bongabon-01"`), causing FastAPI to reject Web saves with HTTP `422` or HTTP `404`! | 1. Implement `did_mount()` in `SavedTripsView` and `DashboardView` to run `self.safe_page.run_task(...)` once attached to `page`, while synchronously pre-loading cached trips in `__init__()`.<br>2. Fix `backend/app/schemas/itinerary.py` to coerce non-UUID `place_id` to `None` and map `place` -> `place_payload`, and auto-upsert missing places in `backend/app/api/v1/itineraries.py`.<br>3. Add `sync_guest_itineraries_to_cloud()` on login in both Web and Desktop. |
| **ISSUE-04** | **Web & Desktop Cannot Communicate; Desktop Only Connects to Localhost Instead of Tunneling** | 1. **`desktop_client/core/connectivity_service.py:52-63`**: Reads `scratch/active_tunnel.txt` via `.read_text().strip()` as a single URL, whereas `scripts/run_daemon.py:66-67` writes two `KEY=VALUE` lines (`CLOUDFLARE_URL=...` and `NGROK_URL=...`), producing an invalid URL string!<br>2. **`scripts/run_daemon.py:61-74`**: Starts `cloudflared` and `ngrok`, writes `scratch/active_tunnel.txt`, **and exits without ever calling `POST https://ne-itinerary-api.edselrenz0.workers.dev/__sync_tunnel`**! | 1. Update `scripts/run_daemon.py` to POST `{"cfUrl": cf_url, "ngrokUrl": ngrok_url}` with header `X-Admin-Sync-Key` to `https://ne-itinerary-api.edselrenz0.workers.dev/__sync_tunnel`.<br>2. Update `ConnectivityService` and `ApiClient` to parse `CLOUDFLARE_URL=` and `NGROK_URL=` from `scratch/active_tunnel.txt`, query `https://ne-itinerary-api.edselrenz0.workers.dev/__status`, and automatically fail over across `[active_cf_tunnel, worker_url, ngrok_url, localhost]`. |
| **ISSUE-05** | **Desktop Map Is Laggy, Shows `"API KEY REQUIRED carto.com"` Tiles, & Zooms Out to `Z8`** (`image_1fd17c.jpg`) | 1. **DOM Thrashing (`desktop_client/components/slippy_map_canvas.py:453-654`)**: Every 45ms drag event calls `self.redraw()`, destroying and recreating ~35 `ft.Image` tile controls, all `cv.Path` route vectors, and iterating over all 2,673 `Place` objects to rebuild 250 marker `ft.Container`s while 6 background threads call `img.update()` on detached controls!<br>2. **`API KEY REQUIRED` Tiles & `Z8` Zoom (`slippy_map_canvas.py:390, 622`)**: Zooming out to `Z8` requests unbundled tiles outside Nueva Ecija; CARTO's CDN returns `"API KEY REQUIRED"` watermarks, or `tile_cache` outside `assets_dir` fails to load in Flet desktop. | 1. Wrap `_tile_stack`, `_vector_canvas`, and `_marker_stack` inside `self._pan_layer` with a 1-tile overscan ring. During `_handle_pan_update`, **only** shift `_pan_layer.left` and `_pan_layer.top` (`O(1)` GPU translation at 60 FPS, zero DOM rebuilds during drag) and commit on `_handle_pan_end`.<br>2. Clamp `MIN_ZOOM = 10` (`Z10`–`Z18`), store cached tiles inside `assets/tiles_cache/` using relative asset paths, and use ESRI World Street Map + OSM fallback with image header validation so `"API KEY REQUIRED"` tiles never appear. |
| **ISSUE-06** | **Suggested Itinerary -> `Find Itinerary` Throws `unexpected keyword argument 'destination'`** (`image_1fca7e.png`) | **`desktop_client/views/suggested_wizard_view.py:878-888` vs `desktop_client/services/itinerary_service.py:130-134`**: `SuggestedWizardView._execute_generation()` calls `self.itinerary_service.generate_suggested_itinerary(destination=..., start_date=..., end_date=..., daily_budget=..., preferences=..., pacing=..., travel_mode=..., min_rating=..., anchor_place_id=...)` with 9 keyword arguments, whereas `ItineraryService.generate_suggested_itinerary(self, request: SuggestedItineraryRequest)` only accepts a single `request` object! | Update `ItineraryService.generate_suggested_itinerary(self, request: Optional[SuggestedItineraryRequest] = None, **kwargs)` to accept **either** a `SuggestedItineraryRequest` instance **or** keyword arguments (`destination`, `start_date`, `end_date`, `daily_budget`, `preferences`, `pacing`, `travel_mode`, `min_rating`, `anchor_place_id`), satisfying both `SuggestedWizardView` and all unit tests. |
| **ISSUE-07** | **Custom Itinerary UI Cluttered & Clicking `Save` Does Nothing / Does Not Close** (`image_1fc9fc.jpg`) | 1. **Silent Crash on Save (`desktop_client/views/custom_builder_view.py:47, 1409, 1420` & `main.py:180`)**: `CustomBuilderView.__init__()` never sets `self.is_draft_from_wizard = is_draft_from_wizard`! When `_save_custom_itinerary()` checks `self.is_draft_from_wizard` (or when `main.py` leaks a stale `selected_trip`), Python raises `AttributeError: 'CustomBuilderView' object has no attribute 'is_draft_from_wizard'`!<br>2. **Broken Toast (`custom_builder_view.py:1403`)**: Uses removed `page.snack_bar = ...` in Flet 1.1.2.<br>3. **Cluttered UI (`image_1fc9fc.jpg`)**: Embeds 7 town chips inside the Trip Settings header and shows a `Z8` route preview map with `"API KEY REQUIRED"` tiles. | 1. Assign `self.is_draft_from_wizard = bool(is_draft_from_wizard)` in `CustomBuilderView.__init__()` and reset `selected_trip` in `main.py:navigate_to()`.<br>2. Display a confirmation toast via `show_toast(page, "Itinerary saved successfully!")` (`page.overlay.append(snack)`) and immediately navigate to `self.on_navigate("/trip-detail", saved_itin)`.<br>3. Redesign the Custom Itinerary builder following `@anti-generic-frontend-design`: clean 2-row Trip Settings card (Trip Title + Daily Budget + Date Range + LGU modal trigger without inline chip clutter) and full-width `Z13`–`Z14` Route Preview Map. |
| **ISSUE-08** | **Small Tabs (Profile, Suggested Wizard, Empty Saved) Flush-Left Instead of Centered** (`image_1fca7e.png`) | **`desktop_client/views/suggested_wizard_view.py:424` (`width=600` inside default left-aligned `Column`)**: Narrow views (`width=520` or `width=600`) are placed inside left-aligned parent `Column`/`Container` controls without `alignment=ft.Alignment(0, -1)` or full-width scroll wrappers, pinning them to the left edge with 60% blank space on the right and clipping the scrollbar against the card edge. | Wrap every single-column view (`ProfileView`, `SuggestedWizardView`, `SavedTripsView`, `CustomBuilderView`, `TripDetailView`, `DashboardView`) in a full-width scrollable viewport (`expand=True, width=float("inf")`) containing a centered `ft.Row(alignment=ft.MainAxisAlignment.CENTER)` with responsive `max_width`. |
| **ISSUE-09** | **Dynamic Window & Responsive Desktop + Mobile Layout (Replacing Capacitor)** | **`desktop_client/main.py:63-67`**: Uses fixed desktop metrics without a `page.on_resized` listener or responsive breakpoint helper (`< 600px` Mobile, `600–1023px` Tablet, `>= 1024px` Desktop). | Add `ResponsiveLayout` in `desktop_client/config/settings.py` and attach `page.on_resized` in `main.py` so every view dynamically adapts padding, card grid columns, map sheet height, and centered container widths across Mobile (`< 600px`), Tablet (`600–1023px`), and Desktop (`>= 1024px`). |

---

### Part B — 15 Additional Hidden Bugs Uncovered in the Turn 3 Deep Codebase Audit

| Bug ID | File & Exact Line Numbers | Severity | Detailed Technical Diagnosis |
| :--- | :--- | :--- | :--- |
| **BUG-NEW-01** | `desktop_client/views/saved_trips_view.py:44, 414-422`<br>`desktop_client/views/dashboard_view.py:47, 1030-1057`<br>`desktop_client/views/places_view.py:93, 125-141`<br>`desktop_client/views/custom_builder_view.py:124, 1493-1540` | **CRITICAL** | **`__init__()` Async Bootstrap Black Hole**: In Flet, `self.page` (`self.safe_page`) is `None` inside `__init__()` because the control has not been added to the page tree yet. And because `def main(page: ft.Page)` in `main.py:59` is synchronous, `asyncio.get_running_loop()` always raises `RuntimeError`, which is swallowed by `except RuntimeError: pass`. None of these 4 views implement `did_mount(self)`, so their async data loaders **never execute** in the live app! |
| **BUG-NEW-02** | `desktop_client/views/custom_builder_view.py:47, 1409, 1420`<br>`desktop_client/main.py:82, 180-181` | **CRITICAL** | **Missing `self.is_draft_from_wizard` Attribute + Stale `selected_trip` Leak**: `CustomBuilderView.__init__()` accepts `is_draft_from_wizard: bool = False` as a parameter, **never assigns `self.is_draft_from_wizard`**, and then reads `self.is_draft_from_wizard` on lines 1409 and 1420 inside `_do_save()`, crashing with `AttributeError` whenever `existing_itinerary` is non-`None`! Furthermore, `main.py:180` (`if trip_data: selected_trip = trip_data`) never clears `selected_trip` to `None` when navigating to `/builder` without `trip_data`, permanently contaminating future Custom Itinerary sessions! |
| **BUG-NEW-03** | `desktop_client/views/places_view.py:881-883` | **CRITICAL** | **Wrong Positional Argument in `_prompt_add_place_to_trip`**: Calls `self.on_navigate("/builder", place)`. In `main.py:119`, the 2nd positional parameter is `trip_data: Optional[Itinerary]` (`existing_itinerary`), and the 3rd is `pre_added_place: Optional[Place]`. Passing `place` as the 2nd argument sets `existing_itinerary = place`, crashing `CustomBuilderView.__init__` at line 77 (`AttributeError: 'Place' object has no attribute 'preferences'`). |
| **BUG-NEW-04** | `desktop_client/views/places_view.py:557-562, 921-927, 1067-1089` | **CRITICAL** | **Map Filter Modal `Dropdown(on_change=...)` Crash & Duplicate `_reset_all_filters`**: Lines 1067 and 1083 pass `on_change=` to `ft.Dropdown`, which raises `TypeError: Dropdown.__init__() got an unexpected keyword argument 'on_change'` in Flet 1.1.2 (must be `on_select=`). Additionally, `_reset_all_filters` is defined twice in `places_view.py` (line 557 and line 921), and line 558 calls `self._reset_discovery_filters()` which does not exist! |
| **BUG-NEW-05** | `desktop_client/views/places_view.py:954-968`<br>`desktop_client/components/offline_banner.py:205, 221`<br>`desktop_client/views/custom_builder_view.py:1403`<br>`desktop_client/views/profile_view.py:1296` | **HIGH** | **Removed `page.snack_bar` API in Flet 1.1.2**: All 4 files assign `page.snack_bar = ft.SnackBar(...)` and `page.snack_bar.open = True`, which is a no-op or raises an error in Flet 1.1.2. All toast notifications must use `page.overlay.append(snack); snack.open = True; page.update()`. |
| **BUG-NEW-06** | `desktop_client/views/dashboard_view.py:623-627` | **HIGH** | **Broken Home Search Debounce**: `DashboardView._on_search_change()` only calls `asyncio.get_running_loop().create_task(...)` and never calls `self.safe_page.run_task(self._debounced_search, val)`, so typing in the Home search bar never triggers debounced search results! |
| **BUG-NEW-07** | `desktop_client/views/suggested_wizard_view.py:409`<br>`desktop_client/views/custom_builder_view.py:861` | **HIGH** | **Broken `"Full Map"` Handoff (`selected_trip` Not Passed)**: Clicking `"Full Map"` in `SuggestedWizardView` (`line 409`) or `CustomBuilderView` (`line 861`) calls `self.on_navigate("/map?itineraryId=draft")` **without** passing the 2nd argument (`trip_data=self.generated_itinerary` or `draft_itin`). As a result, `selected_trip` in `main.py` is `None`, and `PlacesView` opens a blank map with no route! |
| **BUG-NEW-08** | `desktop_client/components/itinerary_route_map.py:121-125` | **HIGH** | **Route Preview Map Defaults to `Z8` on Single-Stop Days**: When a day has only 1 stop (`len(lats) == 1`), `min_lat == max_lat` and `ItineraryRouteMap` leaves `zoom=8` (`Z8`) instead of setting `zoom=14` (`Z14`), causing the zoomed-out `Z8` map seen in `image_1fc9fc.jpg`! |
| **BUG-NEW-09** | `backend/app/services/google_maps_service.py:733-803` | **CRITICAL** | **`upsert_google_place_to_db` Drops Venue Costs & Fails on Non-Google Places**: When upserting `place_payload` into PostgreSQL, `upsert_google_place_to_db` completely omits `estimated_cost_min` and `estimated_cost_max` (resetting saved venue costs to `None`/`₱0`) and only queries `Place.source_name == "google_places"` instead of checking `db.get(Place, place_uuid)` or `Place.source_record_id` first! |
| **BUG-NEW-10** | `backend/app/schemas/itinerary.py:13, 52-72`<br>`backend/app/api/v1/itineraries.py:252-260` | **CRITICAL** | **Web Itinerary Save Fails with HTTP 422 / 404**: Web App sends `place: it.place` (instead of `place_payload`) and string `place_id`s (`"dest-bongabon-01"` or unseeded OSM UUIDs). FastAPI rejects non-UUID `place_id`s with `422 Unprocessable Entity` and unseeded UUIDs with `404 Not Found: The following place IDs do not exist`. |
| **BUG-NEW-11** | `desktop_client/services/itinerary_service.py:224-239, 349-364` | **HIGH** | **Desktop Cloud Save Drops `place_payload`**: When `ItineraryService.create_itinerary()` or `update_itinerary()` serializes items for `POST /api/v1/itineraries`, it sends `"place_id": place_id_val` without including `"place_payload": item.place.model_dump(mode="json")`, causing the backend to reject any newly discovered OSM/local place with HTTP 404! |
| **BUG-NEW-12** | `desktop_client/models/user.py:66-109, 179-216` | **HIGH** | **`User.avatar_url` Validator Strips Relative Web Asset Paths & Overwrites Custom Avatars**: `clean_avatar_url()` rejects `/assets/avatars/...` and does not distinguish between placeholder paths (`default-traveler.png`, `placeholder`) and real user-uploaded `data:image/...` avatars when merging backend responses. |
| **BUG-NEW-13** | `desktop_client/views/trip_detail_view.py:424-436` | **MEDIUM** | **Trip Detail Full Map Button Drops `selected_trip`**: Clicking `"Full Interactive Map"` in `TripDetailView` must pass `self.itinerary` as the 2nd argument (`self.on_navigate(f"/map?itineraryId={self.itinerary.id}", self.itinerary)`) so `PlacesView` always receives the active `Itinerary` even if `selected_trip` was cleared. |
| **BUG-NEW-14** | `desktop_client/views/login_view.py:259-280`<br>`desktop_client/views/signup_view.py:320-345` | **MEDIUM** | **Auth Views Do Not Trigger Cloud Itinerary & Profile Sync on Login**: After `auth_service.login()` or `signup()` succeeds, guest itineraries created before logging in are not automatically migrated to PostgreSQL, and the full user profile is not refreshed from `/api/v1/auth/me`. |
| **BUG-NEW-15** | `desktop_client/components/slippy_map_canvas.py:587-616` | **HIGH** | **Background Thread Socket Contention (`img.update()` on Detached Controls)**: `_TILE_EXECUTOR` spawns 6 worker threads that call `img.update()` directly from background threads. If the user pans or zooms while a tile download is in flight, `img` is detached from `_tile_stack.controls`, and calling `img.update()` raises an unhandled Flet control-not-mounted exception or freezes the Flet socket! |

---

## SECTION 2: PHASE 1 — BACKEND & TUNNEL DAEMON FIXES (`backend/` & `scripts/`)

### Step 1.1: Fix `backend/app/schemas/itinerary.py` (Coerce Non-UUID `place_id` & Map `place` -> `place_payload`)
Replace `backend/app/schemas/itinerary.py` with the following implementation, which preserves all existing schema classes (`ItineraryItemBase`, `ItineraryItemCreate`, `ItineraryItemUpdate`, `ItineraryItemOut`, `ItineraryDayBase`, `ItineraryDayCreate`, `ItineraryDayOut`, `ItineraryCreate`, `ItineraryUpdate`, `ItineraryOut`, `SuggestedItineraryRequest`) while adding:
- `@field_validator("place_id", mode="before")` on `ItineraryItemBase` and `ItineraryItemUpdate` so non-UUID strings (`"dest-bongabon-01"`, `"curated/..."`, `"osm-..."`) cleanly coerce to `None` instead of throwing HTTP 422.
- `@model_validator(mode="before")` on `ItineraryItemCreate` and `ItineraryItemUpdate` so when the Web App sends `place: {...}` (or `place_payload: {...}`), it automatically populates `place_payload` and backfills `custom_title`, `custom_lat`, `custom_lng`, and `estimated_cost`!

```python
# File: backend/app/schemas/itinerary.py
from datetime import date, datetime, time
from typing import Any
import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.place import PlaceOut


def _safe_parse_uuid(val: Any) -> uuid.UUID | None:
    if val is None or val == "":
        return None
    if isinstance(val, uuid.UUID):
        return val
    try:
        return uuid.UUID(str(val).strip())
    except (ValueError, TypeError, AttributeError):
        return None


class ItineraryItemBase(BaseModel):
    place_id: uuid.UUID | None = None
    custom_title: str | None = Field(default=None, max_length=255)
    custom_lat: float | None = Field(default=None, ge=-90.0, le=90.0)
    custom_lng: float | None = Field(default=None, ge=-180.0, le=180.0)
    order_index: int = Field(default=0, ge=0)
    start_time: time | None = None
    end_time: time | None = None
    duration_minutes: int | None = Field(default=60, ge=0)
    travel_time_from_prev_minutes: int | None = Field(default=0, ge=0)
    transport_mode: str | None = Field(default="car", max_length=50)
    notes: str | None = None
    estimated_cost: float | None = Field(default=0.0, ge=0.0)

    @field_validator("place_id", mode="before")
    @classmethod
    def coerce_place_id(cls, v: Any) -> uuid.UUID | None:
        return _safe_parse_uuid(v)


class ItineraryItemCreate(ItineraryItemBase):
    place_payload: dict | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_web_and_desktop_payload(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        out = dict(data)
        place_obj = out.get("place_payload") or out.get("place")
        if isinstance(place_obj, dict):
            out["place_payload"] = place_obj
            if not out.get("custom_title") and place_obj.get("name"):
                out["custom_title"] = str(place_obj["name"])[:255]
            if out.get("custom_lat") is None and place_obj.get("lat") is not None:
                try:
                    out["custom_lat"] = float(place_obj["lat"])
                except (ValueError, TypeError):
                    pass
            if out.get("custom_lng") is None and place_obj.get("lng") is not None:
                try:
                    out["custom_lng"] = float(place_obj["lng"])
                except (ValueError, TypeError):
                    pass
            if not out.get("estimated_cost"):
                c_min = place_obj.get("estimated_cost_min") or place_obj.get("estimatedCostMin")
                if c_min is not None:
                    try:
                        out["estimated_cost"] = float(c_min)
                    except (ValueError, TypeError):
                        pass
        return out


class ItineraryItemUpdate(BaseModel):
    place_id: uuid.UUID | None = None
    custom_title: str | None = Field(default=None, max_length=255)
    custom_lat: float | None = Field(default=None, ge=-90.0, le=90.0)
    custom_lng: float | None = Field(default=None, ge=-180.0, le=180.0)
    order_index: int | None = Field(default=None, ge=0)
    start_time: time | None = None
    end_time: time | None = None
    duration_minutes: int | None = Field(default=None, ge=0)
    travel_time_from_prev_minutes: int | None = Field(default=None, ge=0)
    transport_mode: str | None = Field(default=None, max_length=50)
    notes: str | None = None
    estimated_cost: float | None = Field(default=None, ge=0.0)
    place_payload: dict | None = None

    @field_validator("place_id", mode="before")
    @classmethod
    def coerce_place_id(cls, v: Any) -> uuid.UUID | None:
        return _safe_parse_uuid(v)


class ItineraryItemOut(ItineraryItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    day_id: uuid.UUID
    place: PlaceOut | None = None


class ItineraryDayBase(BaseModel):
    day_number: int = Field(ge=1)
    date: date | None = None
    notes: str | None = None


class ItineraryDayCreate(ItineraryDayBase):
    items: list[ItineraryItemCreate] = Field(default_factory=list)


class ItineraryDayOut(ItineraryDayBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    itinerary_id: uuid.UUID
    items: list[ItineraryItemOut] = Field(default_factory=list)


class ItineraryBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    destination: str = Field(default="Nueva Ecija", max_length=120)
    start_date: date | None = None
    end_date: date | None = None
    budget: float | None = Field(default=None, ge=0.0)
    pacing: str = Field(default="moderate", max_length=50)
    preferences: list[str] = Field(default_factory=list)
    is_suggested: bool = False
    is_public: bool = False


class ItineraryCreate(ItineraryBase):
    days: list[ItineraryDayCreate] = Field(default_factory=list)


class ItineraryUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    destination: str | None = Field(default=None, max_length=120)
    start_date: date | None = None
    end_date: date | None = None
    budget: float | None = Field(default=None, ge=0.0)
    pacing: str | None = Field(default=None, max_length=50)
    preferences: list[str] | None = None
    is_public: bool | None = None
    days: list[ItineraryDayCreate] | None = None


class ItineraryOut(ItineraryBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    days: list[ItineraryDayOut] = Field(default_factory=list)


class SuggestedItineraryRequest(BaseModel):
    destination: str = Field(default="Nueva Ecija", max_length=120)
    days_count: int = Field(default=1, ge=1, le=14)
    start_date: date | None = None
    budget: float | None = Field(default=None, ge=0.0)
    pacing: str = Field(default="moderate", pattern="^(relaxed|moderate|packed)$")
    preferences: list[str] = Field(default_factory=list)
    anchor_place_id: uuid.UUID | None = None
    anchor_place_payload: dict | None = None

    @field_validator("anchor_place_id", mode="before")
    @classmethod
    def coerce_anchor_id(cls, v: Any) -> uuid.UUID | None:
        return _safe_parse_uuid(v)
```

---

### Step 1.2: Fix `backend/app/services/google_maps_service.py` (`upsert_google_place_to_db` Preserving Costs & Matching Existing UUIDs)
In `backend/app/services/google_maps_service.py`, replace `upsert_google_place_to_db` (lines 713–803) so that:
1. If `place_data` contains a valid UUID `id`, it checks `db.get(Place, parsed_uuid)` first.
2. It checks `Place.source_record_id == str(source_record_id)` across **any** `source_name` (not just `"google_places"`).
3. It preserves `estimated_cost_min`, `estimated_cost_max`, `image_url`, and `tags` when inserting or updating `Place`.

```python
# File: backend/app/services/google_maps_service.py (Replace upsert_google_place_to_db at lines 713-803)
def upsert_google_place_to_db(db: Session, place_data: dict[str, Any]) -> Place:
    """
    Persist a live Google Places, OSM, or curated result into the local `places` table
    so that itineraries and favorites can reference a permanent UUID foreign key.
    """
    raw_id = place_data.get("id")
    parsed_uuid: uuid.UUID | None = None
    if raw_id:
        try:
            parsed_uuid = uuid.UUID(str(raw_id))
        except (ValueError, TypeError):
            parsed_uuid = None

    if parsed_uuid is not None:
        existing_by_id = db.get(Place, parsed_uuid)
        if existing_by_id is not None:
            return existing_by_id

    source_record_id = (
        place_data.get("source_record_id")
        or place_data.get("google_place_id")
        or (str(raw_id) if raw_id else None)
    )
    source_name = str(place_data.get("source_name") or "google_places")

    if source_record_id:
        existing = db.scalar(
            select(Place).where(Place.source_record_id == str(source_record_id))
        )
        if existing is not None:
            if place_data.get("rating") is not None:
                existing.rating = float(place_data["rating"])
            if place_data.get("review_count") is not None:
                existing.review_count = int(place_data["review_count"])
            if place_data.get("image_url") and not existing.image_url:
                existing.image_url = place_data["image_url"]
            c_min = place_data.get("estimated_cost_min") or place_data.get("estimatedCostMin")
            c_max = place_data.get("estimated_cost_max") or place_data.get("estimatedCostMax")
            if c_min is not None and not existing.estimated_cost_min:
                existing.estimated_cost_min = float(c_min)
            if c_max is not None and not existing.estimated_cost_max:
                existing.estimated_cost_max = float(c_max)
            db.flush()
            return existing

    name = str(place_data.get("name") or "Nueva Ecija Stop").strip()
    city = str(place_data.get("city") or "Cabanatuan City").strip()
    lat = float(place_data.get("lat") or 15.4865)
    lng = float(place_data.get("lng") or 120.9734)

    existing_coords = db.scalar(
        select(Place).where(
            Place.name == name,
            Place.lat.between(lat - 0.002, lat + 0.002),
            Place.lng.between(lng - 0.002, lng + 0.002),
        )
    )
    if existing_coords is not None:
        if source_record_id and not existing_coords.source_record_id:
            existing_coords.source_record_id = str(source_record_id)
            db.flush()
        return existing_coords

    c_min = place_data.get("estimated_cost_min") or place_data.get("estimatedCostMin")
    c_max = place_data.get("estimated_cost_max") or place_data.get("estimatedCostMax")

    place_kwargs: dict[str, Any] = {
        "name": name,
        "category": str(place_data.get("category") or "Tourist Attractions"),
        "description": place_data.get("description") or f"Verified venue in {city}, Nueva Ecija.",
        "address": place_data.get("address") or f"{city}, Nueva Ecija",
        "city": city,
        "province": "Nueva Ecija",
        "lat": lat,
        "lng": lng,
        "rating": float(place_data.get("rating") or 4.3),
        "review_count": int(place_data.get("review_count") or place_data.get("reviewCount") or 10),
        "price_level": int(place_data.get("price_level") or place_data.get("priceLevel") or 2),
        "estimated_cost_min": float(c_min) if c_min is not None else None,
        "estimated_cost_max": float(c_max) if c_max is not None else None,
        "image_url": place_data.get("image_url") or place_data.get("imageUrl"),
        "tags": list(place_data.get("tags") or []),
        "opening_hours": place_data.get("opening_hours") or place_data.get("openingHours"),
        "contact_phone": place_data.get("contact_phone") or place_data.get("contactPhone"),
        "website": place_data.get("website"),
        "is_featured": bool(place_data.get("is_featured", False)),
        "source_name": source_name,
        "source_record_id": str(source_record_id) if source_record_id else None,
    }
    if parsed_uuid is not None:
        place_kwargs["id"] = parsed_uuid

    new_place = Place(**place_kwargs)
    db.add(new_place)
    db.flush()
    return new_place
```

---

### Step 1.3: Fix `backend/app/api/v1/itineraries.py` (Auto-Upsert Unseeded Places Instead of Raising HTTP 404)
In `backend/app/api/v1/itineraries.py`, update `create_itinerary` (lines 240–265) and `update_itinerary` (lines 325–350) so that:
1. Whenever `item_payload.place_payload` is provided (even if `item_payload.place_id` is already a UUID that does not exist in PostgreSQL yet), `upsert_google_place_to_db(db, item_payload.place_payload)` is called if `item_payload.place_id` is `None` or not yet present in `places`!
2. If `item_payload.place_id` is still not found in `places` and has no `place_payload`, it clears `item_payload.place_id = None` (preserving `custom_title`, `custom_lat`, `custom_lng`) instead of throwing `HTTP 404 Not Found`!

```python
# File: backend/app/api/v1/itineraries.py (Replace place validation block in create_itinerary and update_itinerary)
    # Resolve or auto-upsert any place references before inserting ItineraryItems
    for day_payload in payload.days:
        for item_payload in day_payload.items:
            if item_payload.place_id is not None:
                exists_in_db = db.get(Place, item_payload.place_id)
                if exists_in_db is None and item_payload.place_payload:
                    upserted = upsert_google_place_to_db(db, item_payload.place_payload)
                    item_payload.place_id = upserted.id
                elif exists_in_db is None:
                    # Fallback to custom stop coordinates instead of failing the entire save with 404
                    item_payload.place_id = None
            elif item_payload.place_payload:
                upserted = upsert_google_place_to_db(db, item_payload.place_payload)
                item_payload.place_id = upserted.id
```

---

### Step 1.4: Fix `scripts/run_daemon.py` (Sync Active Tunnels to Cloudflare Worker `/__sync_tunnel`)
Update `scripts/run_daemon.py` so that after starting `cloudflared` and `ngrok`, it immediately POSTs `{"cfUrl": cf_url, "ngrokUrl": ngrok_url}` with header `X-Admin-Sync-Key` to `https://ne-itinerary-api.edselrenz0.workers.dev/__sync_tunnel`.

```python
# File: scripts/run_daemon.py (Add Worker sync helper and call it right after writing scratch/active_tunnel.txt)
import urllib.request
import json

WORKER_SYNC_URL = os.environ.get(
    "WORKER_SYNC_URL",
    "https://ne-itinerary-api.edselrenz0.workers.dev/__sync_tunnel",
)
ADMIN_SYNC_KEY = os.environ.get("ADMIN_SYNC_KEY", "ne-itinerary-sync-2026")


def sync_worker_tunnels(cf_url: str | None, ngrok_url: str | None) -> None:
    payload = json.dumps({
        "cfUrl": cf_url or "",
        "ngrokUrl": ngrok_url or "https://anybody-cube-surprise.ngrok-free.dev",
    }).encode("utf-8")
    req = urllib.request.Request(
        WORKER_SYNC_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "X-Admin-Sync-Key": ADMIN_SYNC_KEY,
            "User-Agent": "NE-Tunnel-Daemon/3.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            print(f"[Daemon] Synced tunnels to Cloudflare Worker (HTTP {resp.status})")
    except Exception as exc:
        print(f"[Daemon] Warning: Worker sync failed: {exc}")
```

---

## SECTION 3: PHASE 2 — WEB APP CLOUD SYNC & PROFILE AVATAR AUTO-MIGRATION (`Project/`)

### Step 2.1: Fix `Project/src/app/tabs/profile/profile.page.ts` (Protect Custom Avatar & Auto-Sync to Backend)
In `Project/src/app/tabs/profile/profile.page.ts`, update `refreshProfileFromBackend()` (lines 58–77) so that if the user already has a custom `data:image/...` avatar in `localStorage` and the backend returns `null` or a placeholder (`default-traveler` / `placeholder`), the Web App **keeps** the local custom avatar and pushes it to `PATCH /api/v1/auth/me`:

```typescript
// File: Project/src/app/tabs/profile/profile.page.ts (Replace refreshProfileFromBackend at lines 58-77)
  private isPlaceholderAvatar(url?: string | null): boolean {
    if (!url) return true;
    const lower = url.trim().toLowerCase();
    return (
      lower === '' ||
      lower.includes('default-traveler') ||
      lower.includes('placeholder')
    );
  }

  private refreshProfileFromBackend() {
    if (!this.authService.isAuthenticated()) return;
    const previousAvatar = this.user?.avatar;
    const hadCustomAvatar = !this.isPlaceholderAvatar(previousAvatar);

    this.api.get<any>('/auth/me').subscribe({
      next: (res) => {
        if (res && res.email && this.user) {
          const backendHasCustomAvatar = !this.isPlaceholderAvatar(res.avatar_url);
          this.user.fullName = res.full_name || this.user.fullName;
          this.user.email = res.email || this.user.email;
          this.user.bio = res.bio ?? this.user.bio;
          this.user.phone = res.phone ?? this.user.phone;
          this.user.hometown = res.hometown ?? this.user.hometown;

          if (backendHasCustomAvatar) {
            this.user.avatar = res.avatar_url;
          } else if (hadCustomAvatar && previousAvatar) {
            // Preserve custom local avatar and sync it up to PostgreSQL
            this.user.avatar = previousAvatar;
            this.api.patch<any>('/auth/me', { avatar_url: previousAvatar }).subscribe({
              error: () => {}
            });
          }
          localStorage.setItem('user_profile', JSON.stringify(this.user));
          this.splitFullName();
        }
      },
      error: () => {}
    });
  }
```

### Step 2.2: Fix `Project/src/app/tabs/history/history.page.ts` (Refresh Saved Itineraries on Every Tab Entry)
Ensure `HistoryPage` implements `ionViewWillEnter()` so switching to the **Saved** tab on the Web App always fetches the latest cloud itineraries created on either Web or Desktop:

```typescript
// File: Project/src/app/tabs/history/history.page.ts (Add ionViewWillEnter)
  ionViewWillEnter(): void {
    this.loadItineraries();
  }
```

---

## SECTION 4: PHASE 3 — DESKTOP CORE: REACTIVE DARK MODE, RESPONSIVE BREAKPOINTS, AVATAR RESOLVER & MULTI-TUNNEL FAILOVER

### Step 3.1: Update `desktop_client/config/settings.py` (100% Backwards-Compatible + Base64 Avatar File Resolver + Responsive Layout)
Update `desktop_client/config/settings.py` to add `resolve_avatar_path()`, `is_placeholder_avatar()`, and `ResponsiveLayout` while **strictly preserving** `ThemeColors` (with `TEXT_MUTED_LIGHT = "#475569"`), `ThemePalette`, `Settings`, `get_settings()`, `CANONICAL_CATEGORIES` (16 items), `NUEVA_ECIJA_LGUS` (32 items), `PACING_OPTIONS`, `BUDGET_PRESETS`, and `resolve_place_image()`.

```python
# File: desktop_client/config/settings.py (Append helper functions & ResponsiveLayout class)
import base64
import hashlib
import re


def is_placeholder_avatar(url: Optional[str]) -> bool:
    """Return True if the avatar URL is empty or points to a generic placeholder."""
    if not url or not str(url).strip():
        return True
    s = str(url).strip().lower()
    return (
        "placeholder" in s
        or "default-traveler" in s
        or s.endswith("/default.png")
        or s.endswith("/avatar.png")
    )


def resolve_avatar_path(avatar_url: Optional[str]) -> Optional[str]:
    """
    Resolve an avatar URL (HTTP/HTTPS, base64 data URI, or local path) into a
    source string that Flet 1.1.2 `ft.Image(src=...)` can render reliably on Desktop & Mobile.
    Decodes `data:image/...;base64,...` into `assets/avatars_cache/avatar_<sha1>.<ext>`
    and returns the relative asset path `"avatars_cache/avatar_<sha1>.<ext>"`.
    """
    if is_placeholder_avatar(avatar_url):
        return None

    raw = str(avatar_url).strip()
    if raw.startswith("data:image/"):
        try:
            header, b64_data = raw.split(",", 1)
            ext = "png"
            m = re.search(r"data:image/([a-zA-Z0-9+]+)", header)
            if m:
                fmt = m.group(1).lower()
                if fmt in ("jpeg", "jpg"):
                    ext = "jpg"
                elif fmt == "webp":
                    ext = "webp"
                elif fmt == "gif":
                    ext = "gif"
            img_bytes = base64.b64decode(b64_data)
            digest = hashlib.sha1(img_bytes).hexdigest()[:20]
            st = get_settings()
            avatars_dir = st.assets_dir / "avatars_cache"
            avatars_dir.mkdir(parents=True, exist_ok=True)
            out_file = avatars_dir / f"avatar_{digest}.{ext}"
            if not out_file.exists():
                out_file.write_bytes(img_bytes)
            return f"avatars_cache/avatar_{digest}.{ext}"
        except Exception:
            return None

    if raw.startswith(("http://", "https://")):
        return raw

    cleaned = raw.lstrip("/")
    if cleaned.startswith("assets/"):
        cleaned = cleaned[len("assets/"):]
    st = get_settings()
    if (st.assets_dir / cleaned).exists():
        return cleaned
    return None


class ResponsiveLayout:
    """Dynamic responsive metrics for compiling Flet to Desktop (Windows/macOS/Linux) and Mobile (Android/iOS)."""

    @staticmethod
    def get_metrics(page_width: Optional[float], page_height: Optional[float] = None) -> dict:
        w = float(page_width or 1280.0)
        h = float(page_height or 840.0)
        is_mobile = w < 600
        is_tablet = 600 <= w < 1024
        is_desktop = w >= 1024
        return {
            "width": w,
            "height": h,
            "is_mobile": is_mobile,
            "is_tablet": is_tablet,
            "is_desktop": is_desktop,
            "horizontal_padding": 14 if is_mobile else (24 if is_tablet else 32),
            "narrow_max_width": w - 24 if is_mobile else 560,
            "wizard_max_width": w - 24 if is_mobile else 680,
            "builder_max_width": w - 24 if is_mobile else 980,
            "dashboard_max_width": w - 24 if is_mobile else 1160,
            "grid_columns": 1 if is_mobile else (2 if is_tablet else 3),
        }
```

---

### Step 3.2: Fix `desktop_client/core/connectivity_service.py` (Parse Multi-Line `active_tunnel.txt` & Query Worker `/__status`)
In `desktop_client/core/connectivity_service.py`, replace `_get_candidate_urls()` (lines 48–75) so it properly parses `CLOUDFLARE_URL=...` and `NGROK_URL=...` from `scratch/active_tunnel.txt` instead of reading the entire multi-line file as one malformed URL:

```python
# File: desktop_client/core/connectivity_service.py (Replace _get_candidate_urls at lines 48-75)
    def _get_candidate_urls(self) -> list[str]:
        candidates: list[str] = []
        tunnel_file = self.settings.project_root / "scratch" / "active_tunnel.txt"
        if tunnel_file.exists():
            try:
                for raw_line in tunnel_file.read_text(encoding="utf-8").splitlines():
                    line = raw_line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        _, val = line.split("=", 1)
                        val = val.strip().rstrip("/")
                    else:
                        val = line.rstrip("/")
                    if val.startswith(("http://", "https://")):
                        api_url = val if val.endswith("/api/v1") else f"{val}/api/v1"
                        if api_url not in candidates:
                            candidates.append(api_url)
            except Exception as exc:
                logger.debug("Could not read active_tunnel.txt: %s", exc)

        for fallback in [
            self.settings.api_base_url,
            self.settings.cloudflare_worker_url,
            self.settings.ngrok_tunnel_url,
            self.settings.local_api_url,
        ]:
            if fallback:
                clean = fallback.strip().rstrip("/")
                if clean and clean not in candidates:
                    candidates.append(clean)
        return candidates
```

---

### Step 3.3: Fix `desktop_client/models/user.py` & `desktop_client/services/auth_service.py` (Never Overwrite Custom Avatar with Placeholder)
In `desktop_client/models/user.py`, update `clean_avatar_url` (lines 66–84) and in `desktop_client/services/auth_service.py`, update `fetch_current_user()` (lines 146–170) so that:
1. If the local session has a custom `avatar_url` (`data:image/...` or custom URL) and the backend returns `None` or a placeholder (`default-traveler.png` / `placeholder`), the desktop client preserves the custom avatar and syncs it up via `PATCH /auth/me`.
2. `fetch_current_user()` updates `session_manager` so `ProfileView` refreshes immediately.

```python
# File: desktop_client/services/auth_service.py (Replace fetch_current_user at lines 146-170)
    async def fetch_current_user(self) -> User:
        """Fetch latest profile for the authenticated user and sync custom avatar if needed."""
        previous_user = self.session.user
        data = await self.api.get("/auth/me", authenticated=True)
        user = User.model_validate(data)

        from desktop_client.config.settings import is_placeholder_avatar
        if (
            previous_user
            and not is_placeholder_avatar(previous_user.avatar_url)
            and is_placeholder_avatar(user.avatar_url)
        ):
            user.avatar_url = previous_user.avatar_url
            try:
                await self.api.patch(
                    "/auth/me",
                    json_data={"avatar_url": previous_user.avatar_url},
                    authenticated=True,
                )
            except Exception:
                pass

        if self.session.access_token:
            self.session.update_user(user)
        return user
```

---

### Step 3.4: Fix `desktop_client/main.py` (Clear Stale `selected_trip`, Preserve Settings Subview on Dark Mode Toggle, Sync Cloud Trips & Responsive Resize)
Replace `desktop_client/main.py` lines 115–265 and 330–370 so that:
1. **Stale `selected_trip` Bug Fixed (`BUG-NEW-02`)**: When navigating to `/builder` (or any route other than `/map?itineraryId=...` / `/suggested?restore=draft`), `selected_trip` is explicitly set to `trip_data` (clearing it to `None` when `trip_data is None`)!
2. **`Place` Passed Positionally Guard (`BUG-NEW-03`)**: If `isinstance(trip_data, Place)` is passed positionally to `navigate_to("/builder", place)`, it automatically assigns `pre_added_place = trip_data; trip_data = None`!
3. **Stay in Settings on Theme Toggle (`ISSUE-02`)**: `toggle_theme()` inspects `getattr(content_area.content, "_subview", None)` before rebuilding the view and restores `new_view._subview = saved_subview; new_view._rebuild()` so changing `App Appearance` between `Light` and `Dark` keeps the user right inside **Settings** and re-themes the entire app shell (`root_shell.bgcolor`, `content_area.bgcolor`, `bottom_tab_bar.refresh_theme()`, `offline_banner.refresh_theme()`).
4. **Startup & Post-Login Cloud Sync (`ISSUE-01` & `ISSUE-03`)**: Whenever authenticated on startup or login, runs `auth_service.fetch_current_user()` and `itinerary_service.sync_guest_itineraries_to_cloud()`.

```python
# File: desktop_client/main.py (Key replacements in main(page: ft.Page))
    def navigate_to(
        route: str,
        trip_data: Optional[Itinerary] = None,
        pre_added_place: Optional[Place] = None,
        preserve_profile_subview: Optional[str] = None,
    ) -> None:
        nonlocal current_route, selected_trip

        # Guard against Place passed positionally as 2nd argument (BUG-NEW-03)
        if isinstance(trip_data, Place):
            pre_added_place = trip_data
            trip_data = None

        base_route = route.split("?")[0] if "?" in route else route
        query_str = route.split("?", 1)[1] if "?" in route else ""

        # Explicitly update or clear selected_trip to prevent stale draft leaks (BUG-NEW-02)
        if trip_data is not None:
            selected_trip = trip_data
        elif base_route not in ("/map", "/trip-detail") and "restore=draft" not in query_str:
            selected_trip = None

        current_route = route
        # ... [existing route guard & view construction] ...
        elif base_route == "/profile":
            prof_view = ProfileView(
                auth_service=auth_service,
                itinerary_service=itinerary_service,
                place_service=place_service,
                session=session_manager,
                on_navigate=navigate_to,
                on_toggle_theme=toggle_theme,
            )
            if preserve_profile_subview in ("profile", "edit", "settings"):
                prof_view._subview = preserve_profile_subview
                prof_view._rebuild()
            view = prof_view
```

And in `toggle_theme` (`desktop_client/main.py:157-166`):

```python
    def toggle_theme(is_dark: bool) -> None:
        saved_subview = getattr(content_area.content, "_subview", None)
        settings.set_dark_mode(is_dark)
        palette = settings.palette
        page.theme_mode = ft.ThemeMode.DARK if is_dark else ft.ThemeMode.LIGHT
        page.bgcolor = palette.bg_primary
        root_shell.bgcolor = palette.bg_primary
        content_area.bgcolor = palette.bg_primary
        bottom_tab_bar.refresh_theme()
        offline_banner.refresh_theme()
        navigate_to(
            current_route,
            trip_data=selected_trip,
            preserve_profile_subview=saved_subview,
        )
```

---

## SECTION 5: PHASE 4 — 60-FPS `SlippyMapCanvas`, `ItineraryRouteMap` & `PlacesView` FIXES

### Step 4.1: Fix `desktop_client/components/slippy_map_canvas.py` (60-FPS GPU Layer Panning, Zero `"API KEY REQUIRED"` Watermarks & Thread-Safe Tile Cache)
Here is why the map was laggy and showed `"API KEY REQUIRED"` tiles in `image_1fd17c.jpg`, and how to fix it while keeping 100% compatibility with unit tests `TC-74`, `TC-75`, and `TC-78`:

1. **`O(1)` Panning via `self._pan_layer` Translation**:
   - Wrap `self._tile_stack`, `self._vector_canvas`, and `self._marker_stack` inside `self._pan_layer = ft.Container(left=0, top=0, width=self._map_w, height=self._map_h, content=ft.Stack(controls=[self._tile_stack, self._vector_canvas, self._marker_stack]))`.
   - Render a **1-tile overscan buffer** (`min_tx - 1` to `max_tx + 1`, `min_ty - 1` to `max_ty + 1`).
   - Inside `_handle_pan_update(e)`, **DO NOT call `self.redraw()`** while dragging within the 1-tile overscan buffer (`abs(self._drag_dx) < 256 and abs(self._drag_dy) < 256`)! Instead, only shift `self._pan_layer.left = self._drag_dx; self._pan_layer.top = self._drag_dy; self._pan_layer.update()`!
   - When the user releases the mouse button (`_handle_pan_end`), commit the accumulated pixel delta to `self.center_lat, self.center_lng`, reset `self._drag_dx = 0; self._drag_dy = 0`, and call `self.redraw()` once!
2. **Eliminate `"API KEY REQUIRED"` Tiles & Relative Asset Paths**:
   - Clamp `MIN_ZOOM = 10` (`Z10` to `Z18`) so the map never zooms out to `Z8` where tiles outside central Luzon are unbundled.
   - Store downloaded tiles in `self.settings.assets_dir / "tiles_cache" / f"{zoom}_{x}_{y}.png"` and return relative asset paths (`f"tiles/{zoom}_{x}_{y}.png"` and `f"tiles_cache/{zoom}_{x}_{y}.png"`) so Flet 1.1.2's asset server renders them instantaneously without file-path errors.
   - Use **ESRI World Street Map** (`https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}`) as primary online tile provider and OSM (`https://tile.openstreetmap.org/{z}/{x}/{y}.png`) as fallback, verifying PNG/JPEG magic bytes (`\x89PNG` or `\xff\xd8\xff`) before saving so watermark or error tiles are never cached.
   - Never call `img.update()` directly from background threads (`_TILE_EXECUTOR`); instead, schedule a single debounced `self.safe_page.run_task(self._async_refresh_tiles)` on the main loop!

```python
# File: desktop_client/components/slippy_map_canvas.py (Key replacements for 60-FPS panning & tile resolution)
    MIN_ZOOM = 10
    MAX_ZOOM = 18

    def _resolve_tile_src(self, zoom: int, tx: int, ty: int) -> Optional[str]:
        """Return relative asset path inside assets_dir if bundled or cached, else schedule download."""
        if zoom < self.MIN_ZOOM or zoom > self.MAX_ZOOM:
            return None
        max_idx = (1 << zoom) - 1
        if tx < 0 or ty < 0 or tx > max_idx or ty > max_idx:
            return None

        bundled_file = self.bundled_tiles_dir / f"{zoom}_{tx}_{ty}.png"
        if bundled_file.exists() and bundled_file.stat().st_size > 200:
            return f"tiles/{zoom}_{tx}_{ty}.png"

        cache_dir = self.settings.assets_dir / "tiles_cache"
        cached_file = cache_dir / f"{zoom}_{tx}_{ty}.png"
        if cached_file.exists() and cached_file.stat().st_size > 200:
            return f"tiles_cache/{zoom}_{tx}_{ty}.png"

        tile_key = (zoom, tx, ty)
        with _IN_FLIGHT_LOCK:
            if tile_key not in _IN_FLIGHT_TILES:
                _IN_FLIGHT_TILES.add(tile_key)
                _TILE_EXECUTOR.submit(self._fetch_and_cache_tile, zoom, tx, ty, cached_file)
        return None

    def _fetch_and_cache_tile(self, zoom: int, tx: int, ty: int, target_path: Path) -> None:
        tile_key = (zoom, tx, ty)
        urls = [
            f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{zoom}/{ty}/{tx}",
            f"https://tile.openstreetmap.org/{zoom}/{tx}/{ty}.png",
        ]
        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            for url in urls:
                req = urllib.request.Request(
                    url,
                    headers={
                        "User-Agent": "TripMoTripKo-NuevaEcija/3.0 (Educational Travel App)",
                        "Accept": "image/png,image/*;q=0.8",
                    },
                )
                try:
                    with urllib.request.urlopen(req, timeout=5) as resp:
                        data = resp.read()
                        if len(data) > 250 and (data[:4] == b"\x89PNG" or data[:3] == b"\xff\xd8\xff"):
                            tmp = target_path.with_suffix(".tmp")
                            tmp.write_bytes(data)
                            tmp.replace(target_path)
                            if self.page is not None:
                                try:
                                    self.page.run_task(self._async_refresh_tiles_after_download)
                                except Exception:
                                    pass
                            break
                except Exception:
                    continue
        finally:
            with _IN_FLIGHT_LOCK:
                _IN_FLIGHT_TILES.discard(tile_key)

    def _handle_pan_update(self, e: ft.DragUpdateEvent) -> None:
        raw_dx = getattr(e, "local_delta", None)
        if raw_dx is not None:
            dx = float(getattr(raw_dx, "x", 0.0) or 0.0)
            dy = float(getattr(raw_dx, "y", 0.0) or 0.0)
        else:
            dx = float(getattr(e, "delta_x", 0.0) or 0.0)
            dy = float(getattr(e, "delta_y", 0.0) or 0.0)

        if dx == 0.0 and dy == 0.0:
            return

        self._drag_dx += dx
        self._drag_dy += dy

        # Fast-path O(1) GPU container translation within 1-tile overscan ring (zero DOM rebuilds!)
        if abs(self._drag_dx) < 220 and abs(self._drag_dy) < 220 and hasattr(self, "_pan_layer"):
            self._pan_layer.left = self._drag_dx
            self._pan_layer.top = self._drag_dy
            if self.page is not None:
                try:
                    self._pan_layer.update()
                except Exception:
                    pass
            return

        # Commit shift when crossing overscan boundary
        self._commit_drag_offset()
        self.redraw()

    def _handle_pan_end(self, e: Any = None) -> None:
        if self._drag_dx != 0.0 or self._drag_dy != 0.0:
            self._commit_drag_offset()
            self.redraw()
```

---

### Step 4.2: Fix `desktop_client/components/itinerary_route_map.py` (Prevent `Z8` Zoom on 1-Stop Days & Expand Width)
In `desktop_client/components/itinerary_route_map.py`, update lines 105–135 so that:
1. When a day has 1 stop (`max_span < 0.005`), `zoom` is set to **`14`** (street-level view) instead of staying at `8` (`Z8`)!
2. All zoom levels in `ItineraryRouteMap` are clamped to `>= 11` (`Z11`–`Z14`).

```python
# File: desktop_client/components/itinerary_route_map.py (Replace zoom calculation at lines 105-135)
        center_lat = NUEVA_ECIJA_CENTER_LAT
        center_lng = NUEVA_ECIJA_CENTER_LNG
        zoom = 12
        if lats and lngs:
            center_lat = (min(lats) + max(lats)) / 2.0
            center_lng = (min(lngs) + max(lngs)) / 2.0
            max_span = max(max(lats) - min(lats), max(lngs) - min(lngs))
            if max_span < 0.008:
                zoom = 14
            elif max_span < 0.03:
                zoom = 13
            elif max_span < 0.12:
                zoom = 12
            else:
                zoom = 11
```

---

### Step 4.3: Fix `desktop_client/views/places_view.py` (`did_mount()`, `ft.Dropdown(on_select=...)`, `_prompt_add_place_to_trip`, & `show_toast`)
Apply these 4 surgical fixes in `desktop_client/views/places_view.py`:
1. **Add `did_mount(self)` (`BUG-NEW-01`)**:
   ```python
   def did_mount(self) -> None:
       if self.safe_page is not None:
           self.safe_page.run_task(self._async_bootstrap)
   ```
2. **Fix `_open_filter_modal()` `Dropdown` crash (`BUG-NEW-04` at lines 1067 and 1083)**:
   Replace `on_change=_on_cat_select` with `on_select=_on_cat_select` and `on_change=_on_lgu_select` with `on_select=_on_lgu_select` on both `ft.Dropdown(...)` controls!
3. **Remove duplicate `_reset_all_filters` at line 557 (`BUG-NEW-04`)**:
   Delete lines 557–562 (which call non-existent `self._reset_discovery_filters()`) and keep only the canonical `_reset_all_filters(self, e: Any = None) -> None:` at line 921!
4. **Fix `_prompt_add_place_to_trip` (`BUG-NEW-03` at line 883)**:
   ```python
   def _prompt_add_place_to_trip(self, place: Place) -> None:
       """Navigate to Custom Builder with this place pre-selected as a stop."""
       self.on_navigate("/builder", None, place)
   ```

---

## SECTION 6: PHASE 5 — `SuggestedWizardView`, `CustomBuilderView`, `ProfileView`, `SavedTripsView`, `DashboardView` & `dialogs.py` FIXES

### Step 5.1: Add Universal `show_toast` in `desktop_client/components/dialogs.py`
Add `show_toast(page: Optional[ft.Page], message: str, is_error: bool = False)` in `desktop_client/components/dialogs.py` using `page.overlay.append(snack); snack.open = True; page.update()` so every view displays crisp visual feedback in Flet 1.1.2 without using the removed `page.snack_bar` property:

```python
# File: desktop_client/components/dialogs.py (Add show_toast helper)
def show_toast(page: Optional[ft.Page], message: str, is_error: bool = False) -> None:
    """Display a non-blocking toast notification compatible with Flet 1.1.2."""
    if page is None:
        return
    bg = "#DC2626" if is_error else "#0F172A"
    snack = ft.SnackBar(
        content=ft.Row(
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(
                    ft.Icons.ERROR_OUTLINE_ROUNDED if is_error else ft.Icons.CHECK_CIRCLE_ROUNDED,
                    color="#FFFFFF",
                    size=18,
                ),
                ft.Text(message, size=13, weight=ft.FontWeight.W_600, color="#FFFFFF"),
            ],
        ),
        bgcolor=bg,
        duration=2800,
        behavior=ft.SnackBarBehavior.FLOATING,
        margin=ft.Margin.all(16),
    )
    try:
        if hasattr(page, "show_dialog"):
            page.show_dialog(snack)
        else:
            page.overlay.append(snack)
            snack.open = True
            page.update()
    except Exception:
        try:
            page.overlay.append(snack)
            snack.open = True
            page.update()
        except Exception:
            pass
```

---

### Step 5.2: Fix `desktop_client/services/itinerary_service.py` (Accept Both `SuggestedItineraryRequest` and Keyword Arguments + Cloud Guest Migration + Include `place_payload`)
1. **Fix `generate_suggested_itinerary` signature (`ISSUE-06`)**:
   In `desktop_client/services/itinerary_service.py:130`, update `generate_suggested_itinerary` so it accepts **either** `request: Optional[SuggestedItineraryRequest] = None` **or** the keyword arguments passed by `SuggestedWizardView` (`destination`, `start_date`, `end_date`, `daily_budget`, `preferences`, `pacing`, `travel_mode`, `min_rating`, `anchor_place_id`):

```python
# File: desktop_client/services/itinerary_service.py (Replace generate_suggested_itinerary at lines 130-165)
    async def generate_suggested_itinerary(
        self,
        request: Optional[SuggestedItineraryRequest] = None,
        *,
        destination: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        days_count: Optional[int] = None,
        daily_budget: Optional[float] = None,
        budget: Optional[float] = None,
        preferences: Optional[list[str]] = None,
        pacing: str = "moderate",
        travel_mode: str = "car",
        min_rating: float = 0.0,
        anchor_place_id: Optional[str] = None,
        anchor_place_payload: Optional[dict[str, Any]] = None,
    ) -> Itinerary:
        """
        Generate a smart suggested itinerary.
        Supports both `generate_suggested_itinerary(SuggestedItineraryRequest(...))`
        and keyword arguments from `SuggestedWizardView`.
        """
        if request is None:
            s_date = start_date or date.today()
            e_date = end_date or s_date
            computed_days = days_count or max(1, (e_date - s_date).days + 1)
            eff_budget = daily_budget if daily_budget is not None else (budget if budget is not None else 1500.0)
            request = SuggestedItineraryRequest(
                destination=destination or "Nueva Ecija",
                days_count=computed_days,
                start_date=s_date,
                budget=float(eff_budget),
                pacing=pacing or "moderate",
                preferences=list(preferences or []),
                anchor_place_id=anchor_place_id,
                anchor_place_payload=anchor_place_payload,
            )
```

2. **Include `place_payload` in `create_itinerary` and `update_itinerary` (`BUG-NEW-11`)**:
   In `desktop_client/services/itinerary_service.py` (lines 224–239 and 349–364), include `"place_payload": item.place.model_dump(mode="json") if item.place else None` in each serialized item dict so the backend can auto-upsert any local/OSM place into PostgreSQL.

3. **Add `sync_guest_itineraries_to_cloud()` (`ISSUE-03`)**:
   ```python
   async def sync_guest_itineraries_to_cloud(self) -> int:
       """Push any locally saved guest itineraries to PostgreSQL upon login."""
       if not self.session.is_authenticated:
           return 0
       local_trips = self.guest_storage.list_itineraries()
       synced = 0
       for trip in local_trips:
           if str(trip.id).startswith("guest-") or str(trip.id).startswith("local-"):
               try:
                   await self.create_itinerary(trip)
                   self.guest_storage.delete_itinerary(str(trip.id))
                   synced += 1
               except Exception:
                   pass
       return synced
   ```

---

### Step 5.3: Fix `desktop_client/views/suggested_wizard_view.py` (Centered Responsive Layout + Full Map Handoff + Toast Feedback)
In `desktop_client/views/suggested_wizard_view.py`:
1. **Fix Full-Map Handoff (`BUG-NEW-07` at line 409)**:
   Change `on_open_full_map=lambda: self.on_navigate("/map?itineraryId=draft")` to:
   ```python
   on_open_full_map=lambda: self.on_navigate("/map?itineraryId=draft", self.generated_itinerary),
   ```
2. **Center the Wizard & Results Cards inside Full-Width Scrollable Viewport (`ISSUE-08`)**:
   In `_build_step_1_form()` (line 422) and `_build_step_2_results()`, wrap the `width=640` card inside a centered `ft.Row(alignment=ft.MainAxisAlignment.CENTER, controls=[card_container])` placed inside the outer full-width `ft.Column(expand=True, width=float("inf"), scroll=ft.ScrollMode.AUTO, horizontal_alignment=ft.CrossAxisAlignment.CENTER)`. This puts the scrollbar cleanly at the right window edge and centers the wizard card in the middle of the screen!
3. **Show Confirmation Toast on Save**:
   In `_save_generated_itinerary()` (line 974), call `show_toast(self.safe_page, "Suggested itinerary saved!")` before calling `self.on_navigate("/trip-detail", saved)`.

---

### Step 5.4: Fix `desktop_client/views/custom_builder_view.py` (`self.is_draft_from_wizard`, `did_mount()`, Clean 2-Row Settings Card, Full-Map Handoff & Save Feedback)
In `desktop_client/views/custom_builder_view.py`:
1. **Assign `self.is_draft_from_wizard` in `__init__()` (`BUG-NEW-02` at line 55)**:
   ```python
   self.existing_itinerary = existing_itinerary
   self.is_draft_from_wizard = bool(is_draft_from_wizard)
   self.pre_added_place = pre_added_place
   ```
2. **Pre-load Browse Places Synchronously in `__init__()` and Refresh in `did_mount()` (`BUG-NEW-01` at line 124)**:
   ```python
   # Synchronously populate from cached dataset so Browse tab is immediately ready
   loaded = self.place_service.get_loaded_places()
   self.browse_places = list(loaded[:60]) if loaded else []
   self.browse_loading = False

   def did_mount(self) -> None:
       if self.safe_page is not None:
           self.safe_page.run_task(self._async_load_browse_places)
   ```
3. **Clean Up Trip Settings Header (`ISSUE-07` / `image_1fc9fc.jpg`)**:
   In `_build_trip_settings_card()`, remove the cluttered row of 7 inline town chips (`Bongabon`, `Pantabangan`, `Cabanatuan City`, `Gapan City`, `General Tinio`, `Nueva Ecija`, `All 32 Towns`) from inside the timeline header card. Replace with a clean 2-row card matching the Web App (`custom-builder.page.html`):
   - **Row 1**: `Trip Title` text field (`expand=True`) + `Daily Budget (₱)` field (`width=170`).
   - **Row 2**: `Date Range` pill button (`Nov 14 – Nov 15, 2026`) + `Municipality / City` selector pill button (`📍 Nueva Ecija (All 32 Towns) ▾` which opens the 32-LGU modal picker on click) + `+ Add Places` quick button.
4. **Fix `"Full Map"` Button in Route Preview (`BUG-NEW-07` at line 861)**:
   ```python
   on_open_full_map=lambda: self.on_navigate("/map?itineraryId=draft", self._build_preview_itinerary_object()),
   ```
5. **Show Toast & Navigate to Trip Detail on Save (`ISSUE-07` at lines 1400–1455)**:
   In `_save_custom_itinerary()`:
   ```python
   if not all_days_with_items:
       show_toast(self.safe_page, "Please add at least one stop before saving.", is_error=True)
       return
   # Inside _do_save():
   if self.existing_itinerary and not self.is_draft_from_wizard and str(self.existing_itinerary.id) != "draft":
       saved = await self.itinerary_service.update_itinerary(str(self.existing_itinerary.id), itin_obj)
   else:
       saved = await self.itinerary_service.create_itinerary(itin_obj)
   show_toast(self.safe_page, f"Saved '{saved.title}'!")
   self.on_navigate("/trip-detail", saved)
   ```

---

### Step 5.5: Fix `desktop_client/views/profile_view.py` (Render Custom Uploaded Avatar via `resolve_avatar_path`, Stay in Settings on Dark Mode Toggle, & Center Responsive Layout)
In `desktop_client/views/profile_view.py`:
1. **Avatar Rendering (`_build_avatar_widget` at lines 217–252)**:
   Use `resolve_avatar_path(user.avatar_url)` from `desktop_client.config.settings`:
   ```python
   resolved_src = resolve_avatar_path(user.avatar_url if user else None)
   if resolved_src:
       avatar_inner = ft.Image(
           src=resolved_src,
           width=size,
           height=size,
           fit=ft.BoxFit.COVER,
           border_radius=ft.BorderRadius.all(size / 2),
       )
   ```
2. **Refresh User from Backend on Mount (`did_mount` at line 1385)**:
   In `did_mount(self)`, schedule an async task that calls `await self.auth_service.fetch_current_user()` when `self.session.is_authenticated` is `True`, and then calls `self._rebuild()` so any avatar uploaded on the Web App appears automatically on the Desktop App!
3. **Dark Mode Surface Colors Across All 3 Subviews (`'profile'`, `'edit'`, `'settings'`)**:
   Replace hardcoded `bgcolor="#FFFFFF"` and `color="#0F172A"` inside `_build_main_profile_subview()`, `_build_edit_profile_subview()`, and `_build_settings_subview()` with `self.palette.surface`, `self.palette.bg_primary`, `self.palette.text_primary`, `self.palette.text_secondary`, and `self.palette.border`.

---

### Step 5.6: Fix `desktop_client/views/saved_trips_view.py` & `desktop_client/views/dashboard_view.py` (`did_mount()` Async Fetch + Synchronous Cache Preload)
In `desktop_client/views/saved_trips_view.py`:
1. In `__init__()` (lines 38–46), synchronously initialize from local cache first so there is zero blank flash:
   ```python
   self.itineraries: list[Itinerary] = list(self.itinerary_service.guest_storage.list_itineraries())
   self.is_loading: bool = False
   self._rebuild()
   ```
2. Add `did_mount(self)` so that as soon as `SavedTripsView` is mounted to `page`, it syncs any guest itineraries and fetches the full cloud + local list from `self.itinerary_service.list_itineraries()`:
   ```python
   def did_mount(self) -> None:
       self._load_trips()
   ```

In `desktop_client/views/dashboard_view.py`:
1. Add `did_mount(self)` to call `self._load_data()` once attached to `page`:
   ```python
   def did_mount(self) -> None:
       self._load_data()
   ```
2. Fix `_on_search_change()` (lines 623–627) to use `self.safe_page.run_task` first:
   ```python
   def _on_search_change(self, e: ft.ControlEvent) -> None:
       val = (e.control.value or "").strip()
       if self.safe_page is not None:
           self.safe_page.run_task(self._debounced_search, val)
   ```

---

## SECTION 7: EXHAUSTIVE END-TO-END QA VERIFICATION MATRIX (95 TEST CASES)

Run the following verification commands after applying the updates above:

```bash
# 1. Run full Desktop Client unit & parity test suites (all 8 test files)
pytest desktop_client/tests/ -v

# 2. Run Backend API & Schema unit tests
pytest backend/tests/ -v

# 3. Verify Web App TypeScript compilation & production build
cd Project && npm run build
```

| Test Group | Test Case IDs | What Is Verified | Expected Outcome |
| :--- | :--- | :--- | :--- |
| **Profile & Avatar Parity** | `TC-01` – `TC-12` | Login with existing account that uploaded a profile photo on Web; inspect `Profile`, `Edit Profile` (`image_2d1741.png`), and `Settings` (`image_2d1705.png`). | `resolve_avatar_path()` decodes base64/HTTP avatar into `assets/avatars_cache/` and renders the exact uploaded photo; `Edit Profile` has only the 7 fields + `Change Photo` + `Save Changes`; `Settings` has only the 6 rows (`Account Information`, `Notifications`, `Privacy & Security`, `Language`, `App Appearance`, `Clear Cache`). |
| **Dark Mode & Settings Persistence** | `TC-13` – `TC-22` | Click `Profile -> Settings -> App Appearance` and toggle between `Light` and `Dark`. | Entire UI (`root_shell`, `ProfileView`, `PlacesView`, `SavedTripsView`, `SuggestedWizardView`, `CustomBuilderView`, `BottomTabBar`) switches to dark slate surfaces (`#0F172A` / `#1E293B`), label updates between `Light` and `Dark`, and view **remains inside `Settings`** without jumping back to `Profile`. |
| **Cross-Platform Itinerary Sync** | `TC-23` – `TC-38` | Create and save Suggested or Custom itinerary on Web (`https://edselrenz.github.io/Itinerary-App/`); open Desktop `Saved` tab; create and save on Desktop; open Web `Saved` tab. | `SavedTripsView.did_mount()` runs `list_itineraries()`, `ItineraryItemBase` coerces non-UUID `place_id`s and maps `place` -> `place_payload`, `upsert_google_place_to_db` preserves `estimated_cost_min/max`, and both Web and Desktop display the exact same saved trips. Empty state matches `image_2d1020.png`. |
| **Multi-Tunnel Failover** | `TC-39` – `TC-48` | Run `scripts/run_daemon.py`; inspect Cloudflare Worker `/__status` and `ConnectivityService.check_connectivity()`. | Daemon syncs `cfUrl` & `ngrokUrl` to Worker `/__sync_tunnel` using `X-Admin-Sync-Key`; Desktop parses `CLOUDFLARE_URL=` and `NGROK_URL=` from `scratch/active_tunnel.txt` and connects remotely without requiring localhost. |
| **60-FPS Interactive Map & Filters** | `TC-49` – `TC-64` | Drag/pan around Nueva Ecija, scroll-wheel zoom (`Z10`–`Z18`), click `Filters`, select category/municipality dropdowns, click `Reset All`. | `_pan_layer` translates at 60 FPS (`O(1)` drag update), zero `"API KEY REQUIRED"` tiles appear, `MIN_ZOOM = 10` prevents `Z8` blank areas, and `ft.Dropdown(on_select=...)` opens and filters cleanly with zero errors. |
| **Suggested Itinerary Wizard** | `TC-65` – `TC-78` | Open `Suggested Itinerary`, choose LGU, dates, budget, preferences, travel mode, rating, and click `Find Itinerary`; click `Full Map` and `Save Itinerary`. | `ItineraryService.generate_suggested_itinerary` accepts keyword arguments from `SuggestedWizardView` and `SuggestedItineraryRequest` from tests; wizard card is centered; `Full Map` passes `self.generated_itinerary` to `/map`. |
| **Custom Itinerary Builder** | `TC-79` – `TC-88` | Open `Custom Itinerary`, add places from Browse or Map (`+ Add to Trip`), edit title/budget/dates/town, click `Save`. | `self.is_draft_from_wizard` is initialized in `__init__()`, `selected_trip` is never leaked across routes, `show_toast` displays confirmation, and app navigates immediately to `/trip-detail`. |
| **Responsive Desktop & Mobile Window** | `TC-89` – `TC-95` | Resize window across Mobile (`390x844`), Tablet (`768x1024`), and Desktop (`1440x900`). | `ResponsiveLayout` + `page.on_resized` dynamically center narrow views (`560px`–`980px` max-width on desktop, full width on mobile) with scrollbar at the outer viewport edge. |
