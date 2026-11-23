# 06 — Complete API Reference

All backend REST endpoints are mounted under `/api/v1` (`settings.api_v1_prefix`). All authenticated endpoints expect `Authorization: Bearer <access_token>`. Global rate limit is `120/minute` per IP unless a stricter per-endpoint limit is noted.

---

## 1. Endpoint Summary Table

### System & Edge Proxy
| Method | Path | Auth | Rate Limit | Purpose | Source |
|---|---|---|---|---|---|
| `GET` | `/api/v1/health` | None | 120/min | Backend liveness & environment check | `backend/app/main.py` |
| `GET` | `/__status` *(Worker)* | None | Cloudflare | Cloudflare Worker health & active tunnel state | `cloudflare-worker/worker.js` |
| `POST` | `/__sync_tunnel` *(Worker)* | `X-Admin-Sync-Key` | Cloudflare | Updates `ACTIVE_TUNNELS` in Cloudflare KV | `cloudflare-worker/worker.js` |

### Authentication (`/api/v1/auth`)
| Method | Path | Auth | Rate Limit | Purpose | Source |
|---|---|---|---|---|---|
| `POST` | `/api/v1/auth/register` | None | `30/min` | Register traveler & issue JWT pair | `backend/app/api/v1/auth.py` |
| `POST` | `/api/v1/auth/login` | None | `30/min` | Authenticate email/username + password | `backend/app/api/v1/auth.py` |
| `POST` | `/api/v1/auth/refresh` | None (refresh token in body) | `10/min` | Exchange refresh token for new token pair | `backend/app/api/v1/auth.py` |
| `GET` | `/api/v1/auth/me` | Bearer JWT | 120/min | Get authenticated traveler profile | `backend/app/api/v1/auth.py` |
| `PATCH` | `/api/v1/auth/me` | Bearer JWT | 120/min | Update profile fields and/or password | `backend/app/api/v1/auth.py` |
| `POST` | `/api/v1/auth/oauth/google` | None (Google ID token) | `5/min` | Verify Google ID token & issue JWT pair | `backend/app/api/v1/auth.py` |
| `POST` | `/api/v1/auth/oauth/apple` | None | 120/min | Disabled gate — always returns HTTP `501` | `backend/app/api/v1/auth.py` |

### Municipalities & Places (`/api/v1`)
| Method | Path | Auth | Rate Limit | Purpose | Source |
|---|---|---|---|---|---|
| `GET` | `/api/v1/municipalities` | None | 120/min | List/search Nueva Ecija cities & municipalities | `backend/app/api/v1/places.py` |
| `GET` | `/api/v1/places` | None | 120/min | Paginated, multi-filter POI search | `backend/app/api/v1/places.py` |
| `GET` | `/api/v1/places/{place_id}` | None | 120/min | Get single active POI by UUID | `backend/app/api/v1/places.py` |
| `POST` | `/api/v1/places/discover` | None | 120/min | Live Google Places v1 / cached / local search | `backend/app/api/v1/places.py` |
| `GET` | `/api/v1/places/google/{google_place_id}` | None | 120/min | Fetch rich Google Place details (cached 24h) | `backend/app/api/v1/places.py` |
| `GET` | `/api/v1/places/photos/{photo_name:path}` | None | 120/min | Server-side proxy for Google Place photos | `backend/app/api/v1/places.py` |

### Itineraries & Routing (`/api/v1/itineraries`)
| Method | Path | Auth | Ownership (BOLA) | Purpose | Source |
|---|---|---|---|---|---|
| `POST` | `/api/v1/itineraries/suggest` | Optional Bearer | N/A (or owner if saved) | Generate clustered multi-day suggested itinerary | `backend/app/api/v1/itineraries.py` |
| `POST` | `/api/v1/itineraries` | Bearer JWT | Sets `user_id` | Create custom multi-day itinerary | `backend/app/api/v1/itineraries.py` |
| `GET` | `/api/v1/itineraries` | Bearer JWT | `user_id == current_user.id` | List user's saved itineraries (newest first) | `backend/app/api/v1/itineraries.py` |
| `GET` | `/api/v1/itineraries/{itinerary_id}` | Bearer JWT | Strict BOLA (`404` if not owner) | Retrieve full itinerary with days, stops, places | `backend/app/api/v1/itineraries.py` |
| `PATCH` | `/api/v1/itineraries/{itinerary_id}` | Bearer JWT | Strict BOLA | Update metadata and/or replace days/items | `backend/app/api/v1/itineraries.py` |
| `DELETE` | `/api/v1/itineraries/{itinerary_id}` | Bearer JWT | Strict BOLA | Delete itinerary (cascades days & items) | `backend/app/api/v1/itineraries.py` |
| `POST` | `/api/v1/itineraries/{itinerary_id}/days` | Bearer JWT | Strict BOLA | Append a calendar day (`409` on duplicate day_number) | `backend/app/api/v1/itineraries.py` |
| `POST` | `/api/v1/itineraries/{itinerary_id}/days/{day_id}/items` | Bearer JWT | Strict BOLA | Add POI or custom stop to a day (`409` on dup POI) | `backend/app/api/v1/itineraries.py` |
| `PATCH` | `/api/v1/itineraries/{itinerary_id}/days/{day_id}/items/{item_id}` | Bearer JWT | Strict BOLA | Partially update a single stop | `backend/app/api/v1/itineraries.py` |
| `DELETE` | `/api/v1/itineraries/{itinerary_id}/days/{day_id}/items/{item_id}` | Bearer JWT | Strict BOLA | Remove stop & re-compact `sort_order` | `backend/app/api/v1/itineraries.py` |
| `POST` | `/api/v1/itineraries/{itinerary_id}/reorder` | Bearer JWT | Strict BOLA | Batch reorder stops within or across days | `backend/app/api/v1/itineraries.py` |
| `POST` | `/api/v1/itineraries/compute-day-route` | None | N/A (stateless) | Compute turn-by-turn route & polyline | `backend/app/api/v1/itineraries.py` |
| `POST` | `/api/v1/itineraries/{itinerary_id}/days/{day_id}/compute-route` | Bearer JWT | Strict BOLA | Compute & persist route polyline/legs for a day | `backend/app/api/v1/itineraries.py` |

---

## 2. Detailed Endpoint Specifications

### 2.1 System Health
#### `GET /api/v1/health`
- **Response (`200 OK`)**:
```json
{
  "status": "ok",
  "province_scope": "Nueva Ecija",
  "environment": "development"
}
```

---

### 2.2 Authentication Endpoints

#### `POST /api/v1/auth/register`
- **Rate Limit**: `30/minute` | **Tables**: `users`
- **Request Body (`UserRegisterIn`)**:
```json
{
  "first_name": "Juan",
  "last_name": "Dela Cruz",
  "username": "juandc",
  "email": "juan@example.com",
  "password": "StrongPassword123",
  "middle_initial": "M",
  "phone_number": "+63 917 000 0000",
  "birthday": "2000-05-23",
  "gender": "Male",
  "avatar_url": null,
  "default_daily_budget": 3000.0
}
```
- **Validation**: `first_name`/`last_name` (1–80 chars), `username` (3–50 chars, normalized lowercase), `email` (`EmailStr`, normalized lowercase), `password` (8–128 chars), `default_daily_budget >= 0`.
- **Response (`201 Created` — `TokenOut`)**:
```json
{
  "access_token": "<hs256-jwt-30m>",
  "refresh_token": "<hs256-jwt-7d>",
  "token_type": "bearer",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "first_name": "Juan",
    "last_name": "Dela Cruz",
    "username_normalized": "juandc",
    "email_normalized": "juan@example.com",
    "middle_initial": "M",
    "phone_number": "+63 917 000 0000",
    "birthday": "2000-05-23",
    "gender": "Male",
    "avatar_url": null,
    "default_daily_budget": 3000.0,
    "is_active": true,
    "created_at": "2026-11-20T12:00:00Z"
  }
}
```
- **Errors**: `409 Conflict` (`"Email is already registered"` or `"Username is already taken"`), `422 Unprocessable Entity`, `429 Too Many Requests`.

#### `POST /api/v1/auth/login`
- **Rate Limit**: `30/minute` | **Tables**: `users`
- **Request Body (`UserLoginIn`)**: `{"email": "juan@example.com", "password": "StrongPassword123"}` (`email` field accepts either email or username).
- **Response (`200 OK`)**: `TokenOut`.
- **Errors**: `401 Unauthorized` (`"Invalid email or password"` — anti-enumeration), `403 Forbidden` (`"Account is inactive"`), `429 Too Many Requests`.

#### `POST /api/v1/auth/refresh`
- **Rate Limit**: `10/minute` | **Tables**: `users`
- **Request Body (`RefreshTokenIn`)**: `{"refresh_token": "<jwt>"}`.
- **Response (`200 OK`)**: Fresh `TokenOut`.
- **Errors**: `401 Unauthorized` (expired, wrong token type, malformed UUID, or inactive user).

#### `GET /api/v1/auth/me` & `PATCH /api/v1/auth/me`
- **Auth**: Bearer JWT | **Tables**: `users`
- **`PATCH` Body (`UserUpdateIn`)**: Any subset of `first_name`, `last_name`, `username`, `middle_initial`, `phone_number`, `birthday`, `gender`, `avatar_url`, `default_daily_budget`, plus `current_password` + `new_password` (min 8 chars) to change password.
- **Response (`200 OK`)**: `UserOut`.
- **Errors**: `400 Bad Request` (`"Username is already taken"`, `"Current password is required to set a new password"`, `"Current password is incorrect"`), `401 Unauthorized`.

#### `POST /api/v1/auth/oauth/google`
- **Rate Limit**: `5/minute` | **Tables**: `users`, `auth_identities`
- **Request Body (`GoogleOAuthIn`)**: `{"id_token": "<google-id-token>"}`.
- **Response (`200 OK`)**: `TokenOut`.
- **Errors**: `400 Bad Request` (unverified Google email), `401 Unauthorized` (invalid signature/issuer), `403 Forbidden` (deactivated account), `503 Service Unavailable` (`GOOGLE_OAUTH_CLIENT_ID` not configured).

#### `POST /api/v1/auth/oauth/apple`
- **Response**: Always returns `501 Not Implemented`.

---

### 2.3 Municipalities & Places Endpoints

#### `GET /api/v1/municipalities`
- **Query Params**: `q` (optional, max 80 chars, case-insensitive escaped `ILIKE`).
- **Response (`200 OK`)**: `list[MunicipalityOut]` ordered by `is_city DESC, name ASC`.

#### `GET /api/v1/places`
- **Query Params**:
  - `q` (string, max 100): matches `Place.name`, `address_text`, `category`, or `Municipality.name`.
  - `categories` (`list[str]`): repeated (`?categories=cafe&categories=restaurant`) or comma-separated; must belong to the 16 `CANONICAL_CATEGORIES` else `422`.
  - `municipality_id` (`UUID`), `municipality_name` (string, max 100).
  - `price_tier`: `free` (`min==0 & max==0`), `budget` (`max <= 500` or `min==0 & max IS NULL`), `mid` (`max > 500` or `min > 500`).
  - `featured` (`bool`), `min_lat`, `max_lat`, `min_lng`, `max_lng` (`float`, all 4 required for bounding-box filter).
  - `limit` (`1..5000`, default `50`), `offset` (`>= 0`, default `0`).
- **Response (`200 OK` — `PaginatedPlacesOut`)**: `{"total": 2673, "limit": 50, "offset": 0, "items": [PlaceOut, ...]}`.

#### `GET /api/v1/places/{place_id}`
- **Path Param**: `place_id` (`UUID`).
- **Response (`200 OK`)**: `PlaceOut` | **Errors**: `404 Not Found`.

#### `POST /api/v1/places/discover`
- **Request Body (`LivePlaceSearchRequest`)**: `{"query": "coffee cabanatuan", "latitude": 15.4865, "longitude": 120.9734, "radius_meters": 50000.0, "included_types": ["cafe"], "min_rating": 4.0, "open_now": true}`.
- **Response (`200 OK` — `LivePlaceSearchResponse`)**: `{"places": [PlaceOut, ...], "source": "google_live" | "cache" | "local_db", "total": 12}`.

#### `GET /api/v1/places/google/{google_place_id}`
- **Response (`200 OK`)**: `PlaceOut` enriched with `editorial_summary`, `regular_opening_hours`, `photos`, `reviews`, `business_status`. | **Errors**: `404 Not Found`.

#### `GET /api/v1/places/photos/{photo_name:path}`
- **Validation**: `photo_name` must match `^places/[A-Za-z0-9_-]+/photos/[A-Za-z0-9_-]+$` (returns `400 Bad Request` on invalid format).
- **Response (`200 OK`)**: Binary image (`image/jpeg` with `Cache-Control: public, max-age=86400`), or 1×1 SVG fallback if `GOOGLE_MAPS_API_KEY` is unset or fetch fails.

---

### 2.4 Itineraries & Routing Endpoints

#### `POST /api/v1/itineraries/suggest`
- **Auth**: Optional Bearer JWT (persists immediately only if `save_immediately: true` AND authenticated).
- **Request Body (`SuggestedItineraryRequest`)**:
```json
{
  "title": "Bongabon Weekend Escape",
  "destination": "Bongabon",
  "start_date": "2026-12-05",
  "end_date": "2026-12-06",
  "daily_budget": 2500.0,
  "preferences": ["nature", "food"],
  "save_immediately": false,
  "travel_mode": "DRIVE",
  "pacing": "moderate",
  "include_live_places": false,
  "anchor_place_id": null
}
```
- **Validation**: `end_date >= start_date`; trips > 14 days return `400 Bad Request`.
- **Response (`200 OK`)**: `ItineraryOut` containing `days[]`, `items[]`, `assumptions[]`, `day_overview_polyline`, `total_distance_meters`, `total_travel_duration_seconds`, and `route_legs`.

#### `POST /api/v1/itineraries`
- **Auth**: Bearer JWT | **Tables**: `itineraries`, `itinerary_days`, `itinerary_items`, `places` (upsert if `place_payload` / `google_place_id` provided).
- **Request Body (`ItineraryCreate`)**: `title` (1–160), `destination` (max 120), `start_date`, `end_date`, `daily_budget` (`>= 0`), `preferences[]`, `type` (`custom` | `suggested`), `assumptions[]`, `days[]`.
- **Response (`201 Created`)**: `ItineraryOut`.
- **Errors**: `401 Unauthorized`, `404 Not Found` (explicit UUID `place_id` not found without fallback payload), `422 Unprocessable Entity`.

#### `GET /api/v1/itineraries` & `GET /api/v1/itineraries/{itinerary_id}`
- **Auth**: Bearer JWT | **BOLA**: Scoped strictly to `current_user.id`.
- **Response (`200 OK`)**: `list[ItineraryOut]` or `ItineraryOut`. | **Errors**: `401`, `404`.

#### `PATCH /api/v1/itineraries/{itinerary_id}`
- **Auth**: Bearer JWT | **Body (`ItineraryUpdate`)**: Partial metadata fields and optional full `days[]` replacement (clears existing days and recreates stops).
- **Errors**: `401`, `404`, `422` (`end_date < start_date`).

#### `DELETE /api/v1/itineraries/{itinerary_id}`
- **Auth**: Bearer JWT | **Response**: `204 No Content`. | **Errors**: `401`, `404`.

#### `POST /api/v1/itineraries/{itinerary_id}/days`
- **Auth**: Bearer JWT | **Body (`ItineraryDayCreate`)**: `day_number`, `travel_date`, `title`.
- **Response (`200 OK`)**: Updated `ItineraryOut`. | **Errors**: `404`, `409 Conflict` (duplicate `day_number`).

#### `POST /api/v1/itineraries/{itinerary_id}/days/{day_id}/items`
- **Auth**: Bearer JWT | **Body (`ItineraryItemCreate`)**: Must provide `place_id`, `google_place_id`, `place_payload`, or `custom_title`. Automatically increments `sort_order`.
- **Response (`200 OK`)**: Updated `ItineraryOut`. | **Errors**: `404`, `409 Conflict` (duplicate `place_id` on same day), `422` (`estimated_cost_max < estimated_cost_min`).

#### `PATCH /api/v1/itineraries/{itinerary_id}/days/{day_id}/items/{item_id}`
- **Auth**: Bearer JWT | **Body (`ItineraryItemUpdate`)**: Partial stop update (`notes`, `planned_time`, `duration_minutes`, costs, routing fields).
- **Response (`200 OK`)**: Updated `ItineraryOut`. | **Errors**: `404`.

#### `DELETE /api/v1/itineraries/{itinerary_id}/days/{day_id}/items/{item_id}`
- **Auth**: Bearer JWT | Deletes stop and re-compacts `sort_order` sequentially (`1..N`).
- **Response (`200 OK`)**: Updated `ItineraryOut`. | **Errors**: `404`.

#### `POST /api/v1/itineraries/{itinerary_id}/reorder`
- **Auth**: Bearer JWT | **Body (`ItineraryReorderIn`)**: `{"items": [{"id": "<item-uuid>", "day_id": "<day-uuid>", "sort_order": 1}]}`.
- **Response (`200 OK`)**: Updated `ItineraryOut`. | **Errors**: `400 Bad Request` (stop or day does not belong to itinerary), `404`.

#### `POST /api/v1/itineraries/compute-day-route`
- **Auth**: None (Stateless) | **Body (`RouteComputeRequest`)**:
```json
{
  "origin": {"latitude": 15.4865, "longitude": 120.9734},
  "destination": {"latitude": 15.2981, "longitude": 121.1223},
  "intermediates": [],
  "travel_mode": "DRIVE"
}
```
- **Response (`200 OK` — `RouteComputeResponse`)**: `overview_polyline`, `total_distance_meters`, `total_duration_seconds`, `legs[]` (with `steps[]`), `source` (`"google_routes" | "osrm" | "haversine_direct" | "cache"`).

#### `POST /api/v1/itineraries/{itinerary_id}/days/{day_id}/compute-route`
- **Auth**: Bearer JWT | Computes route across all geocoded stops in the day and persists `day_overview_polyline`, `total_distance_meters`, `total_travel_duration_seconds`, `route_legs`, and per-item leg metrics.
- **Response (`200 OK`)**: Updated `ItineraryOut`. | **Errors**: `404`.

---

## 3. Technical Terms & Concepts Explained (How It Works & What It Is Used For in This System)

| Technical Term | How It Works (Technical & Layman Explanation) | What It Is Used For in This System |
|---|---|---|
| **HTTP Methods (`GET`, `POST`, `PATCH`, `DELETE`, `OPTIONS`)** | **Layman**: Action verbs attached to every web request telling the server what you want to do: `GET` means "Read/Fetch", `POST` means "Create/Calculate", `PATCH` means "Partially Update", and `DELETE` means "Remove".<br>**Technical**: Standard RFC 9110 HTTP request verbs defining idempotency and safety semantics in RESTful APIs. | Governs all 27 endpoints in `backend/app/api/v1/`, such as `GET /api/v1/places` (read catalog), `POST /api/v1/itineraries` (create trip), `PATCH /api/v1/itineraries/{id}` (edit trip), and `DELETE /api/v1/itineraries/{id}` (delete trip). |
| **HTTP Status Codes (`200`, `201`, `204`, `400`, `401`, `403`, `404`, `409`, `422`, `429`, `501`, `502`, `503`)** | **Layman**: 3-digit shorthand reply codes from the server: `2xx` means "Success!", `4xx` means "The client made a mistake or needs to log in", and `5xx` means "The server or tunnel is unavailable".<br>**Technical**: Standardized HTTP response status codes interpreted by `auth.interceptor.ts` and `desktop_client/core/api_client.py`. | `200 OK` / `201 Created` / `204 No Content` signal success; `401 Unauthorized` triggers the automatic JWT refresh queue; `404 Not Found` enforces BOLA privacy; `409 Conflict` flags duplicate emails/usernames/stops; `422 Unprocessable Entity` reports Pydantic validation errors; `429 Too Many Requests` signals SlowAPI rate limiting; `502`/`503` triggers the client offline banner (`ConnectivityService`). |
| **Bearer Authentication (`Authorization: Bearer <token>`)** | **Layman**: Presenting a self-contained digital pass at the door. "Bearer" literally means "give access to whoever is holding (bearing) this signed token."<br>**Technical**: An RFC 6750 HTTP authentication scheme extracted by FastAPI's `OAuth2PasswordBearer` dependency from the `Authorization` request header. | Authenticates `/api/v1/auth/me` and all `/api/v1/itineraries/*` CRUD endpoints using the 30-minute HS256 `access_token`. |
| **Pagination (`limit` & `offset`)** | **Layman**: Instead of forcing a slow phone connection to download all 2,673 places at once when searching, you can ask for "page 1 (first 50 items)" (`limit=50, offset=0`), then "page 2 (items 51–100)" (`limit=50, offset=50`).<br>**Technical**: SQL `LIMIT :limit OFFSET :offset` slicing paired with a `SELECT COUNT(places.id)` query returned inside `PaginatedPlacesOut` (`total`, `limit`, `offset`, `items`). | Powers `GET /api/v1/places`, allowing lightweight 50-item paginated discovery queries or full 5,000-item catalog syncs (`limit=5000`). |
| **Bounding-Box Spatial Query (`min_lat`, `max_lat`, `min_lng`, `max_lng`)** | **Layman**: Drawing an invisible rectangle on the map (from a southern latitude to a northern latitude, and a western longitude to an eastern longitude) and asking the database only for tourist spots inside that rectangle.<br>**Technical**: A SQL range predicate (`latitude >= :min_lat AND latitude <= :max_lat AND longitude >= :min_lng AND longitude <= :max_lng`) accelerated by composite B-tree index `ix_places_lat_lng`. | Used by `GET /api/v1/places` to load pins inside the user's current map viewport and by `itinerary_generator.py` to pre-filter candidate POIs within `25 km + 10 km` of the target municipality. |
| **Stateless vs. Persistent Route Computation** | **Layman**: **Stateless** route computation (`POST /compute-day-route`) is like asking a calculator for driving directions without saving the answer on the server — perfect for Guest Mode or unsaved drafts. **Persistent** route computation (`POST /{id}/days/{day_id}/compute-route`) calculates the route *and* saves the road line into your cloud itinerary.<br>**Technical**: `/compute-day-route` requires no auth and writes only to `geospatial_cache`, whereas `/{itinerary_id}/days/{day_id}/compute-route` enforces BOLA ownership and updates `ItineraryDay.day_overview_polyline`, `route_legs`, and child `ItineraryItem` leg columns in PostgreSQL/SQLite. | Allows both unauthenticated Guest travelers and authenticated cloud travelers to preview accurate turn-by-turn road routes on Web, Android, and Desktop. |
