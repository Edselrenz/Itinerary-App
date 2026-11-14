# Antigravity Execution Plan: Full Desktop-to-Web Functional, API & UI Parity

**Target Repository**: `Edselrenz/Itinerary-App` (`feature/flet-desktop-app`)  
**Reference Web Application**: `Project/` (Ionic 9 / Angular 22 / Leaflet 1.9 / TypeScript)  
**Target Desktop Application**: `desktop_client/` (Python 3.12+ / Flet 1.1.2 / `httpx` / PyInstaller)  
**Shared Backend & Edge Proxy**: `backend/app/` (FastAPI / SQLAlchemy / PostgreSQL) & `cloudflare-worker/worker.js`

---

## 1. Executive Summary & Current Codebase State

An end-to-end audit of `backend/`, `cloudflare-worker/`, `Project/`, and `desktop_client/` shows that while earlier parity passes implemented the 4-tab bottom bar (`BottomTabBar`), non-expanding `OfflineHostBanner`, `SlippyMapCanvas`, and 3-view skeletons for `SuggestedWizardView` and `CustomBuilderView`, **9 critical runtime crashes / API contract mismatches** and **11 functional & workflow parity gaps** still prevent the Desktop App from working identically to the Web App.

### Important Guardrails for Antigravity Before Editing
1. **Do NOT break existing unit tests in `desktop_client/tests/`**:
   - In particular, `test_def_06_place_service_query_parameter_mapping` (`desktop_client/tests/test_qa_remediation.py:114`) passes `municipality_id="muni-pan"` and asserts `params["municipality_id"] == "muni-pan"`. Keep the `is_known_town_name` check in `PlaceService.get_places()` (`desktop_client/services/place_service.py:139–146`) intact while fixing the undefined `muni_name_resolved` variable on line 183.
2. **Preserve all 2,673 bundled OSM places (`desktop_client/assets/data/osm_places.json`) and 42 destination photos**.
3. **Verify all changes with `pytest desktop_client/tests/ -v`** after applying the edits below.

---

## 2. Backend, Server Communication & API Parity Matrix

| Layer / Endpoint | Web App (`Project/src/app/core/`) | Desktop App (`desktop_client/`) | Current Discrepancy & Required Fix |
| :--- | :--- | :--- | :--- |
| **Default Production Base URL & Failover** | `environment.prod.ts` routes to `https://ne-itinerary-api.edselrenz0.workers.dev/api/v1` (Cloudflare Worker proxy with KV tunnel lookup & 24h edge cache); `environment.ts` uses `http://127.0.0.1:8000/api/v1`. | `config/settings.py:157` hardcodes `http://127.0.0.1:8000/api/v1`. | **GAP**: When `127.0.0.1:8000` is unreachable and no custom URL is set, `ConnectivityService` never fails over to `https://ne-itinerary-api.edselrenz0.workers.dev/api/v1`. |
| **ngrok Interstitial Bypass Header** | `auth.interceptor.ts:27` sets `'ngrok-skip-browser-warning': 'true'` on every API & `/health` request. | `core/api_client.py:72` & `connectivity_service.py:194` omit `'ngrok-skip-browser-warning'`. | **BUG**: Direct ngrok tunnel URLs return an HTML interstitial warning page instead of JSON. Add `'ngrok-skip-browser-warning': 'true'` to both `ApiClient._get_headers()` and `ConnectivityService`. |
| **Gateway Error (`502/503/504`) Detection** | `auth.interceptor.ts:53–68` treats HTTP `0`, `502`, `503`, `504` as gateway offline errors and calls `setHostOffline(true)`. | `core/api_client.py:138–141` calls `set_host_offline(False)` **before** checking `response.status_code`. | **BUG**: When Cloudflare Worker returns `502 Bad Gateway` (`{"detail": "Host laptop backend offline..."}`), `ApiClient` falsely marks the offline server as **online**! Only call `set_host_offline(False)` when `response.status_code < 500`, and call `set_host_offline(True)` on `502`/`503`/`504`. |
| **401 Token Refresh & Concurrency Lock** | `auth.interceptor.ts:71–130` skips `/auth/login`, `/auth/register`, and `/auth/refresh` on `401` and serializes concurrent refreshes behind `isRefreshing`. | `core/api_client.py:162–173` calls `_refresh_handler()` on **any** `401` without endpoint filtering or an `asyncio.Lock`. | **BUG**: A `401` on `/auth/login` or `/auth/refresh` triggers recursive refresh calls, and concurrent `401` responses race to rotate the refresh token. Add endpoint exclusion and an `asyncio.Lock`. |
| **`POST /api/v1/auth/login` & `/auth/register`** | `LoginPage` & `SignupPage` invoke `GuestMigrationService.migrateGuestData()` after authentication. | `views/login_view.py:258` & `views/signup_view.py:343` navigate directly to `/dashboard` without migrating local guest trips. | **GAP**: Call `await self.auth_service.migrate_guest_trips()` after login and registration when local guest trips exist. |
| **`PATCH /api/v1/auth/me`** | `AuthService.updateProfile()` supports `{first_name, last_name, username, current_password, new_password}`. | `UserUpdatePayload.to_backend_dict()` supports password fields, but `ProfileView._open_edit_profile_dialog()` has no password inputs. | **GAP**: Add optional `Current Password` and `New Password` fields in `ProfileView._open_edit_profile_dialog()`. |
| **`GET /api/v1/places`** | `PlaceService.searchPlaces()` sends `q`, `categories` (comma-joined), `municipality_id`, `municipality_name`, `price_tier`, `featured`, bbox (`min_lat..max_lng`), `limit`, `offset` and falls back to 2,673 offline places. | `services/place_service.py:183` references undefined `muni_name_resolved` inside `except Exception:`. | **CRASH BUG**: Every offline call to `PlaceService.get_places()` crashes with `NameError: name 'muni_name_resolved' is not defined`. |
| **`POST /api/v1/places/discover` & Live Overpass API** | `OsmOverpassService.fetchLiveOsmPlaces(bounds)` & backend `/places/discover` fetch live POIs within map bounds and merge into cache. | `places_view.py:534` only calls `get_places(page=1, page_size=250)` with no bbox or Overpass query. | **GAP**: Add `PlaceService.fetch_live_osm_places()` (querying backend `/places/discover` + Overpass API) and wire it to `[✨ Live OSM]` on `PlacesView`. |
| **`POST /api/v1/itineraries` & `PATCH /api/v1/itineraries/{id}`** | Sends `toBackendIsoTime(planned_time)` (`"HH:MM:00"`), sets `place_id: null` + `place_payload` for non-DB places, and includes `custom_lat` / `custom_lng`. | Sends raw `"dest-*"` / `"osm-*"` strings as `place_id` (causing FastAPI `422` UUID error), sends `"place"` instead of `"place_payload"`, and omits `custom_lat`/`custom_lng` in Wizard & Builder saves. | **CRITICAL API BUG**: Sanitize `place_id` (only send valid UUIDs; otherwise `place_id: None` + `place_payload`), normalize `planned_time` to `"HH:MM:00"`, and include `custom_lat`/`custom_lng`. |
| **`POST /api/v1/itineraries/{id}/days/{day_id}/items`** | `ItineraryService.addStop()` parses the returned `ItineraryOut` object and replaces the itinerary in state. | `services/itinerary_service.py:440` parses `ItineraryOut` as `ItineraryItem.from_dict(data)` and appends it to `target_day.items`. | **CRITICAL BUG**: Corrupts `target_day.items` with a fake `ItineraryItem` whose `id` is the itinerary UUID. Parse `return Itinerary.from_dict(data)`. |
| **`PATCH /api/v1/itineraries/{id}/days/{day_id}/items/{item_id}`** | `ItineraryService.updateStop()` updates a single stop in place. | Missing in `desktop_client/services/itinerary_service.py`. | **GAP**: Add `update_stop()` to `ItineraryService`. |
| **`POST /api/v1/itineraries/compute-day-route`** | Used for Google Routes v2 / cached turn-by-turn polylines and leg distances. | `SlippyMapCanvas` only calls public OSRM directly (`router.project-osrm.org`). | **GAP**: Query backend `POST /api/v1/itineraries/compute-day-route` first, falling back to OSRM and geodesic arcs. |

---

## 3. Step-by-Step Code Fixes by File

### Step 1: Fix `desktop_client/core/api_client.py` & `desktop_client/core/connectivity_service.py`

#### 1A. In `desktop_client/core/api_client.py`
1. Add `self._refresh_lock = asyncio.Lock()` in `ApiClient.__init__()`.
2. Add `"ngrok-skip-browser-warning": "true"` to `ApiClient._get_headers()`:
   ```python
   def _get_headers(self, custom_headers: Optional[dict[str, str]] = None) -> dict[str, str]:
       headers = {
           "Accept": "application/json",
           "Content-Type": "application/json",
           "User-Agent": "NuevaEcijaTravel-Desktop/1.0.0",
           "ngrok-skip-browser-warning": "true",
       }
       if self._token_getter:
           token = self._token_getter()
           if token:
               headers["Authorization"] = f"Bearer {token}"
       if custom_headers:
           headers.update(custom_headers)
       return headers
   ```
3. In `ApiClient.request()`, fix gateway offline detection (`502/503/504`) and guard `401` token refresh:
   ```python
        try:
            response = await client.request(
                method=method.upper(),
                url=url,
                params=params,
                json=json_data,
                headers=req_headers,
                timeout=req_timeout,
            )
            try:
                from desktop_client.core.connectivity_service import get_connectivity_service
                if response.status_code in (502, 503, 504):
                    get_connectivity_service().set_host_offline(True, force=True)
                elif response.status_code < 500:
                    get_connectivity_service().set_host_offline(False)
            except Exception:
                pass
        except httpx.ConnectError as err:
            ...
   ```
4. Still in `ApiClient.request()`, exclude auth endpoints from triggering `_refresh_handler` on `401` and serialize refresh attempts with `self._refresh_lock`:
   ```python
        clean_ep = endpoint.lstrip("/").lower()
        is_auth_endpoint = any(
            clean_ep.startswith(p)
            for p in ("auth/login", "auth/register", "auth/refresh")
        )

        # Handle 401 Token Expiry with single automatic refresh retry
        if (
            response.status_code == 401
            and not retried
            and not is_auth_endpoint
            and self._refresh_handler
        ):
            async with self._refresh_lock:
                refreshed = await self._refresh_handler()
            if refreshed:
                return await self.request(
                    method=method,
                    endpoint=endpoint,
                    params=params,
                    json_data=json_data,
                    headers=headers,
                    timeout=timeout,
                    retried=True,
                )
   ```

#### 1B. In `desktop_client/core/connectivity_service.py`
1. Include `"ngrok-skip-browser-warning": "true"` in `check_host_health()` and `check_host_health_sync()`.
2. If the default local URL (`http://127.0.0.1:8000/api/v1`) is unreachable and `self._custom_api_url` is not set, automatically probe the Cloudflare Worker proxy (`https://ne-itinerary-api.edselrenz0.workers.dev/api/v1/health`) and use it as the active fallback URL when reachable:
   ```python
    CLOUDFLARE_WORKER_API_URL = "https://ne-itinerary-api.edselrenz0.workers.dev/api/v1"

    async def check_host_health(self) -> bool:
        self._is_checking_health = True
        self._notify_listeners()

        req_headers = {"ngrok-skip-browser-warning": "true", "Accept": "application/json"}
        health_url = f"{self.active_api_base_url}/health"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(health_url, headers=req_headers)
                if res.status_code == 200:
                    self._is_checking_health = False
                    self.set_host_offline(False)
                    return True
        except Exception:
            pass

        # If default localhost is down and no custom URL is set, try Cloudflare Worker proxy
        if not self._custom_api_url and "127.0.0.1" in self.settings.api_base_url:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    cf_res = await client.get(f"{self.CLOUDFLARE_WORKER_API_URL}/health", headers=req_headers)
                    if cf_res.status_code == 200:
                        self.settings.api_base_url = self.CLOUDFLARE_WORKER_API_URL
                        self._is_checking_health = False
                        self.set_host_offline(False)
                        return True
            except Exception:
                pass

        self._is_checking_health = False
        self.set_host_offline(True, force=True)
        return False
   ```

---

### Step 2: Fix `desktop_client/services/place_service.py` (Fix Offline `NameError`, Add Live Overpass & Nearby Places)

1. **Fix `NameError: name 'muni_name_resolved' is not defined` on line 183**:
   In `PlaceService.get_places()` (`desktop_client/services/place_service.py:135–190`), initialize `muni_name_resolved = municipality_name` before the `if municipality_id` block, and update it when `is_known_town_name` is True:
   ```python
        # Resolve municipality_id vs municipality_name safely (prevents FastAPI 422 on non-UUID town names)
        muni_name_resolved = municipality_name
        if municipality_id and municipality_id.strip() and municipality_id != "all":
            raw_m = municipality_id.strip()
            # If a town name was passed (e.g. "Bongabon", "Pantabangan"), route to municipality_name
            is_known_town_name = (
                raw_m in ALL_32_LGUS_METADATA
                or any(raw_m.lower() == k.lower() for k in ALL_32_LGUS_METADATA)
            )
            if is_known_town_name:
                muni_name_resolved = raw_m
            else:
                params["municipality_id"] = raw_m

        if muni_name_resolved and muni_name_resolved.strip() and muni_name_resolved.lower() != "all":
            params["municipality_name"] = muni_name_resolved.strip()
   ```
   *(Note: Keeping `is_known_town_name` ensures `test_def_06_place_service_query_parameter_mapping` with `municipality_id="muni-pan"` continues to pass while fixing the `NameError` in the `except Exception:` block on line 183!)*

2. **Add `fetch_live_osm_places()` and `discover_places()` to `PlaceService`**:
   Port `OsmOverpassService.fetchLiveOsmPlaces()` (`Project/src/app/core/services/osm-overpass.service.ts`) into `PlaceService` so clicking `[✨ Live OSM]` on the Map tab queries both `POST /api/v1/places/discover` (or `GET /api/v1/places` with bbox) and the live OpenStreetMap Overpass API (`https://overpass-api.de/api/interpreter`), maps OSM tags to the 16 canonical categories, and merges results via `self.merge_places_into_cache(discovered)`:
   ```python
    @staticmethod
    def map_osm_tags_to_category(tags: dict[str, Any]) -> str:
        amenity = str(tags.get("amenity", ""))
        tourism = str(tags.get("tourism", ""))
        leisure = str(tags.get("leisure", ""))
        shop = str(tags.get("shop", ""))
        historic = str(tags.get("historic", ""))

        if amenity == "cafe":
            return "cafe"
        if amenity in ("restaurant", "fast_food", "food_court"):
            return "restaurant"
        if tourism in ("hotel", "motel", "guest_house", "hostel"):
            return "hotel_accommodation"
        if tourism in ("attraction", "viewpoint") or historic in ("monument", "memorial"):
            return "tourist_attraction"
        if tourism == "museum" or historic == "archaeological_site":
            return "museum_cultural"
        if amenity == "place_of_worship":
            return "church_religious"
        if leisure in ("park", "nature_reserve", "garden"):
            return "nature_park"
        if leisure in ("water_park", "swimming_pool") or tourism == "resort":
            return "resort_swimming"
        if amenity in ("hospital", "clinic", "doctors"):
            return "hospital_clinic"
        if amenity == "pharmacy":
            return "pharmacy"
        if amenity in ("bank", "atm"):
            return "bank_atm"
        if amenity == "fuel":
            return "fuel_station"
        if amenity in ("bus_station", "taxi") or tags.get("railway") == "station":
            return "transport_terminal"
        if shop in ("supermarket", "convenience"):
            return "convenience_store"
        if shop or amenity == "marketplace":
            return "shopping_market"
        if amenity in ("townhall", "police", "post_office"):
            return "public_facility"
        return "tourist_attraction"

    async def fetch_live_osm_places(
        self,
        min_lat: float = 15.15,
        max_lat: float = 16.15,
        min_lng: float = 120.70,
        max_lng: float = 121.40,
    ) -> list[Place]:
        """Queries backend /places and live OpenStreetMap Overpass API within bounds and merges into cache."""
        import httpx

        discovered: list[Place] = []
        # 1. Try backend bbox query first
        try:
            res = await self.get_places(
                page=1,
                page_size=500,
                min_lat=min_lat,
                max_lat=max_lat,
                min_lng=min_lng,
                max_lng=max_lng,
            )
            if res.items:
                discovered.extend(res.items)
        except Exception:
            pass

        # 2. Query live Overpass API for viewport bbox
        bbox = f"{min_lat},{min_lng},{max_lat},{max_lng}"
        overpass_query = f"""
        [out:json][timeout:12];
        (
          node["amenity"~"cafe|restaurant|fast_food|bank|atm|pharmacy|hospital|clinic|fuel|place_of_worship|bus_station|townhall"]({bbox});
          node["tourism"~"attraction|hotel|motel|guest_house|museum|viewpoint|resort"]({bbox});
          node["leisure"~"park|resort|water_park|nature_reserve|swimming_pool"]({bbox});
          way["tourism"~"attraction|hotel|resort|museum"]({bbox});
        );
        out center body;
        """
        endpoints = [
            "https://overpass-api.de/api/interpreter",
            "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
        ]
        for ep in endpoints:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(ep, params={"data": overpass_query})
                    if resp.status_code == 200:
                        payload = resp.json()
                        for el in payload.get("elements", []):
                            tags = el.get("tags") or {}
                            name = tags.get("name") or tags.get("name:en") or tags.get("alt_name")
                            if not name:
                                continue
                            lat = el.get("lat") or (el.get("center") or {}).get("lat")
                            lng = el.get("lon") or (el.get("center") or {}).get("lon")
                            if lat is None or lng is None:
                                continue
                            cat = self.map_osm_tags_to_category(tags)
                            city = tags.get("addr:city") or tags.get("addr:municipality") or "Nueva Ecija"
                            street = tags.get("addr:street") or ""
                            address = f"{street}, {city}" if street else city
                            osm_id = f"{el.get('type', 'node')}-{el.get('id')}"
                            discovered.append(
                                Place(
                                    id=f"osm-{osm_id}",
                                    name=str(name).strip(),
                                    category=cat,
                                    latitude=float(lat),
                                    longitude=float(lng),
                                    municipality_name=city,
                                    address_text=address,
                                    description=tags.get("description") or tags.get("tourism:description") or "",
                                    phone=tags.get("phone") or tags.get("contact:phone"),
                                    website=tags.get("website") or tags.get("contact:website"),
                                    opening_hours=tags.get("opening_hours"),
                                    directions_url=f"https://www.google.com/maps/dir/?api=1&destination={lat},{lng}",
                                )
                            )
                        break
            except Exception:
                continue

        if discovered:
            self.merge_places_into_cache(discovered)
        return discovered
   ```

3. **Add `get_nearby_places(municipality: str, category_tab: str = "restaurant") -> list[Place]` to `PlaceService`**:
   Filter `self.get_loaded_places(municipality)` (falling back to all Nueva Ecija places if fewer than 3 matches in that municipality) by category group:
   - `"restaurant"` / `"restaurants"`: `{"restaurant", "cafe"}`
   - `"hospital"` / `"hospitals"`: `{"hospital_clinic", "pharmacy"}`
   - `"store"` / `"stores"`: `{"convenience_store", "shopping_market", "fuel_station", "bank_atm"}`

---

### Step 3: Fix `desktop_client/models/itinerary.py` & `desktop_client/services/itinerary_service.py`

#### 3A. In `desktop_client/models/itinerary.py`
1. Add `to_backend_iso_time()` and `_is_valid_uuid()` helpers at the top of `desktop_client/models/itinerary.py` so `planned_time` and `place_id` always conform to `backend/app/schemas/itinerary.py`:
   ```python
   import re

   def _is_valid_uuid(val: Any) -> bool:
       if not val:
           return False
       try:
           uuid.UUID(str(val))
           return True
       except Exception:
           return False

   def to_backend_iso_time(time_str: Optional[str]) -> Optional[str]:
       """Normalizes user-facing time strings ('09:30 AM - 11:30 AM', '2:00 PM') into 'HH:MM:00' for FastAPI."""
       if not time_str:
           return None
       clean = str(time_str).strip()
       if not clean:
           return None
       first_part = clean.split("-")[0].strip() if "-" in clean else clean
       if re.match(r"^\d{2}:\d{2}:\d{2}$", first_part):
           return first_part
       if re.match(r"^\d{2}:\d{2}$", first_part):
           return f"{first_part}:00"
       m = re.match(r"^(\d{1,2}):(\d{2})(?::\d{2})?\s*(AM|PM)?$", first_part, re.IGNORECASE)
       if m:
           h = int(m.group(1))
           mins = m.group(2)
           meridiem = (m.group(3) or "").upper()
           if meridiem == "PM" and h < 12:
               h += 12
           elif meridiem == "AM" and h == 12:
               h = 0
           return f"{h:02d}:{mins}:00"
       return None
   ```
2. Update `Itinerary.to_create_payload()` (`desktop_client/models/itinerary.py:249–269`) so non-UUID `place_id` values (`"dest-*"`, `"osm-*"`) are sent with `"place_id": None` and `"place_payload": it.place.to_dict()` (which FastAPI's `resolve_or_upsert_item_place()` upserts into PostgreSQL automatically!), while preserving `"place"` for offline guest storage:
   ```python
    def to_create_payload(self) -> "ItineraryCreatePayload":
        days_data = []
        for d in self.days:
            items_data = []
            for it in d.items:
                valid_uuid = _is_valid_uuid(it.place_id)
                place_dict = it.place.to_dict() if it.place else None
                items_data.append({
                    "place_id": it.place_id if valid_uuid else None,
                    "custom_title": it.custom_title or it.display_title,
                    "custom_lat": it.custom_lat if it.custom_lat is not None else (it.place.latitude if it.place else None),
                    "custom_lng": it.custom_lng if it.custom_lng is not None else (it.place.longitude if it.place else None),
                    "sort_order": it.sort_order,
                    "planned_time": to_backend_iso_time(it.planned_time) or it.planned_time,
                    "duration_minutes": it.duration_minutes or 90,
                    "notes": it.notes,
                    "estimated_cost_min": it.estimated_cost_min,
                    "estimated_cost_max": it.estimated_cost_max,
                    "place_payload": place_dict,
                    "place": place_dict,
                })
            days_data.append({
                "day_number": d.day_number,
                "travel_date": d.travel_date or self.start_date,
                "title": d.title or f"Day {d.day_number}",
                "items": items_data,
            })
        return ItineraryCreatePayload(
            title=self.title,
            destination=self.destination,
            start_date=self.start_date,
            end_date=self.end_date,
            daily_budget=self.daily_budget,
            preferences=self.preferences,
            type=self.type,
            assumptions=self.assumptions,
            days=days_data,
        )
   ```

#### 3B. In `desktop_client/services/itinerary_service.py`
1. **Add `calculate_budget_summary(self, itinerary: Itinerary) -> dict[str, Any]`** matching `itinerary.service.ts:393–432`:
   ```python
    def calculate_budget_summary(self, itinerary: Itinerary) -> dict[str, Any]:
        """Transparently calculates verified min/max stop costs and unpriced stop count."""
        verified_min = 0.0
        verified_max = 0.0
        unverified_count = 0

        for day in itinerary.days or []:
            for item in day.items or []:
                c_min = item.estimated_cost_min
                c_max = item.estimated_cost_max
                if c_min is None and c_max is None and item.place:
                    c_min = item.place.estimated_cost_min
                    c_max = item.place.estimated_cost_max
                if c_min is not None or c_max is not None:
                    verified_min += float(c_min if c_min is not None else c_max or 0.0)
                    verified_max += float(c_max if c_max is not None else c_min or 0.0)
                else:
                    unverified_count += 1

        if verified_min > 0 or verified_max > 0:
            if abs(verified_min - verified_max) < 0.01:
                formatted_range = f"₱{verified_min:,.0f}"
            else:
                formatted_range = f"₱{verified_min:,.0f} - ₱{verified_max:,.0f}"
            display_text = (
                f"{formatted_range} (+ {unverified_count} unpriced)"
                if unverified_count > 0
                else formatted_range
            )
        elif unverified_count > 0:
            display_text = f"{unverified_count} unpriced stops"
        else:
            display_text = "No stops added"

        return {
            "verified_min": verified_min,
            "verified_max": verified_max,
            "unverified_count": unverified_count,
            "display_text": display_text,
        }
   ```
2. **Fix `add_stop()` (`itinerary_service.py:435–444`)**:
   `POST /api/v1/itineraries/{id}/days/{day_id}/items` returns `ItineraryOut` (the full updated itinerary). Replace lines 435–444 with:
   ```python
        if not itinerary.is_guest and self.session_manager.is_authenticated:
            try:
                req_dict = payload.to_dict()
                if not _is_valid_uuid(req_dict.get("place_id")):
                    req_dict["place_id"] = None
                    if place:
                        req_dict["place_payload"] = place.to_dict()
                data = await self.api_client.post(
                    f"itineraries/{itinerary.id}/days/{day_id}/items",
                    json_data=req_dict,
                )
                if isinstance(data, dict) and "days" in data:
                    return Itinerary.from_dict(data)
            except Exception:
                pass
   ```
3. **Add `update_stop()` to `ItineraryService`**:
   ```python
    async def update_stop(
        self,
        itinerary: Itinerary,
        day_id: str,
        stop_id: str,
        patch_data: dict[str, Any],
    ) -> Itinerary:
        """Partially updates a stop via PATCH /api/v1/itineraries/{id}/days/{day_id}/items/{stop_id}."""
        if not itinerary.is_guest and self.session_manager.is_authenticated:
            try:
                data = await self.api_client.patch(
                    f"itineraries/{itinerary.id}/days/{day_id}/items/{stop_id}",
                    json_data=patch_data,
                )
                if isinstance(data, dict) and "days" in data:
                    return Itinerary.from_dict(data)
            except Exception:
                pass

        target_day = next((d for d in itinerary.days if d.id == day_id), None)
        if target_day:
            target_item = next((i for i in target_day.items if i.id == stop_id), None)
            if target_item:
                for k, v in patch_data.items():
                    if hasattr(target_item, k):
                        setattr(target_item, k, v)
        if itinerary.is_guest or not self.session_manager.is_authenticated:
            self.guest_storage.save_itinerary(itinerary)
        return itinerary
   ```

---

### Step 4: Fix `desktop_client/views/dashboard_view.py` (Fix Saved Itinerary Card Click `TypeError`)

In `desktop_client/views/dashboard_view.py`:
1. Update `__init__` type hint (line 26):
   ```python
   def __init__(self, on_navigate: Optional[Callable[..., None]] = None):
   ```
2. Update `_navigate` (line 890) so it accepts the optional `trip_data` passed by `_create_itinerary_card` on line 579 (`on_click=lambda _, it=itin: self._navigate(f"/trips/{it.id}", it)`):
   ```python
   def _navigate(self, route: str, trip_data: Optional[Itinerary] = None) -> None:
       if self.on_navigate:
           if trip_data is not None:
               try:
                   self.on_navigate(route, trip_data)
                   return
               except TypeError:
                   pass
           self.on_navigate(route)
   ```

---

### Step 5: Fix `desktop_client/components/place_card.py` & `desktop_client/views/places_view.py` (Fix Map Drawer Crash, Filter Modal & Live OSM)

#### 5A. In `desktop_client/components/place_card.py`
Update `PlaceCard.__init__()` (lines 16–36) to accept `compact: bool = False` and `on_click: Optional[Callable[[Place], None]] = None` (aliasing `on_click` to `on_view_details` and adjusting image/card height when `compact=True`):
```python
    def __init__(
        self,
        place: Place,
        on_view_details: Optional[Callable[[Place], None]] = None,
        on_add_to_day: Optional[Callable[[Place], None]] = None,
        on_click: Optional[Callable[[Place], None]] = None,
        compact: bool = False,
        width: Optional[float] = 300,
    ):
        super().__init__()
        self.place = place
        self.on_view_details = on_view_details or on_click
        self.on_add_to_day = on_add_to_day
        self.compact = compact

        self.width = 236 if compact else width
        self.border_radius = 14
        self.bgcolor = ThemeColors.SURFACE_LIGHT
        self.border = ft.Border.all(1.2, ThemeColors.BORDER_LIGHT)
        self.clip_behavior = ft.ClipBehavior.HARD_EDGE
        self.ink = True
        self.on_click = lambda _: self._view_details()

        self._build_content()
```
Inside `PlaceCard._build_content()`, use `img_h = 92 if self.compact else 140` for `image_widget` height so compact drawer cards fit cleanly inside the 220px bottom POI drawer in `PlacesView`.

#### 5B. In `desktop_client/views/places_view.py`
1. **Fix `_open_filter_modal()` (lines 525–575)**:
   - Add a **Municipality dropdown** populated with `"all"` (`"All 32 Municipalities"`) + `NUEVA_ECIJA_LGUS` from `desktop_client.config.settings`.
   - Replace the broken `self.safe_page.pop_dialog(); self.safe_page.dialog = dlg` lines with:
     ```python
     self.safe_page.overlay.append(dlg)
     dlg.open = True
     self.safe_page.update()
     ```
2. **Upgrade `_refresh_live_places()` (lines 489–502)**:
   - Call `discovered = await self.place_service.fetch_live_osm_places()` and refresh `self.all_places = self.place_service.get_loaded_places()`, then show a `SnackBar` confirming how many POIs are now loaded in the map cache.
3. **Preserve source route in `_exit_follow_route_to_plan()` (lines 518–525)**:
   - Check `source_param = urllib.parse.parse_qs(urllib.parse.urlparse(self.route_query).query).get("source", [None])[0]`.
   - If `source_param == "builder"`, call `self.on_navigate("/builder?draft=true", self.route_itinerary)`.
   - Else if `self.route_query.startswith("/map?itineraryId=draft")` or `"draft" in self.route_query`, call `self.on_navigate("/suggested", self.route_itinerary)`.
   - Else if `self.route_itinerary`, call `self.on_navigate(f"/trips/{self.route_itinerary.id}", self.route_itinerary)`.

---

### Step 6: Fix `desktop_client/views/profile_view.py`, `login_view.py`, & `signup_view.py`

1. **In `desktop_client/views/profile_view.py:456` (`_open_settings_dialog`)**:
   Replace `self._run_async(_do_test)` (which raises `AttributeError`) with:
   ```python
   if self.safe_page:
       self.safe_page.run_task(_do_test)
   else:
       try:
           loop = asyncio.get_running_loop()
           loop.create_task(_do_test())
       except RuntimeError:
           pass
   ```
2. **In `desktop_client/views/profile_view.py` (`_open_edit_profile_dialog`)**:
   Add optional `current_pwd_input = ft.TextField(label="Current Password (optional)", password=True, can_reveal_password=True, border_radius=10, dense=True)` and `new_pwd_input = ft.TextField(label="New Password (min 8 chars)", password=True, can_reveal_password=True, border_radius=10, dense=True)` and pass `current_password=current_pwd_input.value or None, new_password=new_pwd_input.value or None` into `UserUpdatePayload(...)`.
3. **In `desktop_client/views/login_view.py:258` & `desktop_client/views/signup_view.py:343`**:
   After `await self.auth_service.login(...)` and `await self.auth_service.register(...)`, automatically migrate any unsynced local guest itineraries (matching `GuestMigrationService` on Web):
   ```python
   try:
       await self.auth_service.migrate_guest_trips()
   except Exception:
       pass
   ```

---

### Step 7: Fix `desktop_client/components/dialogs.py`, `desktop_client/components/stop_card.py`, `desktop_client/views/suggested_wizard_view.py`, `desktop_client/views/custom_builder_view.py`, & `desktop_client/views/trip_detail_view.py`

#### 7A. In `desktop_client/components/dialogs.py`
In `show_place_detail_dialog()` (lines 42–45), pass the place's municipality and ID when `[✨ Start Trip Here]` is clicked:
```python
    def handle_start_trip(_=None):
        import urllib.parse
        page.pop_dialog()
        if on_navigate:
            dest_q = urllib.parse.quote(place.municipality_name or "Nueva Ecija")
            pid_q = urllib.parse.quote(str(place.id))
            on_navigate(f"/suggested?destination={dest_q}&placeId={pid_q}")
```

#### 7B. In `desktop_client/components/stop_card.py`
Add `on_click: Optional[Callable[[ItineraryItem], None]] = None` to `StopCard.__init__()`:
```python
        self.on_click_card = on_click
        if self.on_click_card:
            self.ink = True
            self.on_click = lambda _: self.on_click_card(self.item)
```

#### 7C. In `desktop_client/views/suggested_wizard_view.py`
1. **Restore active draft when returning from Full Map (`__init__`)**:
   - In `SuggestedWizardView.__init__()`, hydrate `self.budget_val` from `get_session_manager().current_user.default_daily_budget` if available (`3000.0` default).
   - Check `existing_draft = self.itinerary_service.get_active_draft_itinerary()`: if `existing_draft and existing_draft.days and not anchor_place_id`:
     ```python
     self.generated_itinerary = existing_draft
     self.view_mode = "itinerary"
     ```
2. **Add Minimum Place Rating Chips (`All Ratings`, `4.0+ ★`, `4.5+ ★`) to `_build_wizard_form()`**:
   - Render a 3-chip selector row updating `self.min_rating_val` (`0.0`, `4.0`, `4.5`).
3. **Add Verified Place Costs Card, Collapsible Assumptions & Clickable StopCards to `_build_result_view()`**:
   - Call `summary = self.itinerary_service.calculate_budget_summary(itin)` and display a green badge card (`Verified Place Costs: {summary['display_text']}`).
   - Make `assumptions_box` expandable (`self.is_assumptions_expanded = not self.is_assumptions_expanded`) listing `itin.assumptions`.
   - Pass `on_click=lambda itm: show_place_detail_dialog(self.safe_page, itm.place, on_navigate=self.on_navigate) if (itm.place and self.safe_page) else None` into `StopCard(...)`.
4. **Filter Nearby Amenities by Active Day Municipality (`_load_nearby_amenities`)**:
   - Determine `active_day = self.generated_itinerary.days[self.active_day_index]` and `muni = next((it.place.municipality_name for it in active_day.items if it.place and it.place.municipality_name), self.generated_itinerary.destination)`.
   - Use `self.place_service.get_nearby_places(muni, self.nearby_category)` so `"restaurant"`, `"hospital"`, and `"store"` tabs each display relevant local amenities in that municipality.
5. **Fix `_save_generated_itinerary()`**:
   - Call `payload = self.generated_itinerary.to_create_payload()` (which sanitizes `place_id` and `planned_time`), `saved = await self.itinerary_service.create_itinerary(payload)`, `self.itinerary_service.set_active_draft_itinerary(None)`, and navigate to `self.on_navigate(f"/trips/{saved.id}", saved)`.

#### 7D. In `desktop_client/views/custom_builder_view.py`
1. **Add Traveler Preferences Pills in `_build_form_view()`**:
   - Render selectable pills for `["Nature & Parks", "Food Trip", "Culture & History", "Shopping", "Resort"]` updating `self.preferences`.
2. **Add `✨ Recommended for You` & Destination Priority Sorting in `_build_browse_view()` / `_load_browse_places()`**:
   - Include `("recommended", "✨ Recommended for You")` in `cats` when `self.preferences` is non-empty.
   - Sort `self.browse_places` so places matching `self.destination` appear first (`C-BUG-03`).
3. **Add Editable Trip Settings Card & Verified Place Costs Card in `_build_timeline_view()`**:
   - Above `day_bar`, render a compact card with inline inputs for `Trip Title`, `Destination`, `Daily Budget`, and clickable `Travel Dates` button (`_open_date_picker`), plus the `Verified Place Costs` badge from `self.itinerary_service.calculate_budget_summary(...)`.
4. **Fix `_open_full_map_draft()` & `_save_custom_itinerary()`**:
   - In `_open_full_map_draft()`, navigate to `f"/map?itineraryId=draft&day={day_num}&source=builder"`.
   - In `_save_custom_itinerary()`, build an `Itinerary` instance and call `.to_create_payload()`. If `self.existing_itinerary and not self.is_draft_from_wizard and self.existing_itinerary.id != "draft"`, update `self.existing_itinerary` fields and call `saved = await self.itinerary_service.update_itinerary(self.existing_itinerary)` (`PATCH /api/v1/itineraries/{id}`) instead of creating a duplicate itinerary!

#### 7E. In `desktop_client/views/trip_detail_view.py`
1. **Fix `_open_add_custom_stop()` (lines 500–523)**:
   Pass `custom_lat=venue_data.get("latitude")` and `custom_lng=venue_data.get("longitude")` when constructing `ItineraryItem(...)`.
2. **Fix `_edit_stop()` (lines 442–455)**:
   Pass `available_days=[d.day_number for d in self.itinerary.days]` and `current_day=self.itinerary.days[self.active_day_index].day_number` into `show_edit_stop_dialog()`, and move `item` to `target_day` when `data.get("target_day")` differs from `current_day`.
3. **Make `StopCard` clickable in View Mode (`_build_view_mode`)**:
   Pass `on_click=lambda itm: show_place_detail_dialog(self.safe_page, itm.place, on_navigate=self.on_navigate) if (itm.place and self.safe_page) else None` to `StopCard(...)`.

---

## 4. Verification & Acceptance Commands

Run the following verification commands from the repository root after applying all fixes:

```bash
# 1. Run full Desktop Client unit & parity test suite
PYTHONPATH=. pytest desktop_client/tests/ -v

# 2. Run Backend API & schema test suite
PYTHONPATH=backend pytest backend/tests/ -v

# 3. Verify zero syntax errors across all desktop_client Python modules
python3 -m compileall desktop_client/
```
