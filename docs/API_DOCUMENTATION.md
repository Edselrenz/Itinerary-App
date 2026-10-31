# API Documentation: Nueva Ecija Travel Itinerary

All REST API endpoints are served under the versioned prefix `/api/v1`.

Interactive OpenAPI / Swagger documentation is available in development mode at:
- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`

---

## 1. Authentication & Session Endpoints (`/api/v1/auth`)

### 1.1 Register Account
- **Endpoint**: `POST /api/v1/auth/register`
- **Authentication**: None.
- **Request Body**:
  ```json
  {
    "first_name": "Juan",
    "last_name": "Dela Cruz",
    "username": "juandelacruz",
    "email": "juan@example.ph",
    "password": "Password123!"
  }
  ```
- **Responses**:
  - `201 Created`:
    ```json
    {
      "access_token": "eyJhbGciOiJI...",
      "refresh_token": "eyJhbGciOiJI...",
      "token_type": "bearer",
      "user": {
        "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "first_name": "Juan",
        "last_name": "Dela Cruz",
        "username_normalized": "juandelacruz",
        "email_normalized": "juan@example.ph",
        "is_active": true,
        "created_at": "2026-10-30T10:45:00Z"
      }
    }
    ```
  - `409 Conflict`: Username or email already registered.
  - `422 Unprocessable Content`: Validation error (password < 8 chars, invalid email).

### 1.2 Login Account
- **Endpoint**: `POST /api/v1/auth/login`
- **Authentication**: None.
- **Request Body**:
  ```json
  {
    "email": "juan@example.ph",
    "password": "Password123!"
  }
  ```
- **Responses**:
  - `200 OK`: Returns `TokenOut` with new access and refresh tokens.
  - `401 Unauthorized`: `"Invalid email or password"` (generic error prevents enumeration).

### 1.3 Refresh Session
- **Endpoint**: `POST /api/v1/auth/refresh`
- **Authentication**: None (requires valid refresh token).
- **Request Body**:
  ```json
  {
    "refresh_token": "eyJhbGciOiJI..."
  }
  ```
- **Responses**:
  - `200 OK`: Returns fresh `TokenOut`.
  - `401 Unauthorized`: Token expired or invalid type.

### 1.4 Get Profile
- **Endpoint**: `GET /api/v1/auth/me`
- **Authentication**: `Bearer <access_token>`
- **Responses**:
  - `200 OK`: Returns `UserOut`.
  - `401 Unauthorized`: Missing or invalid Bearer token.

### 1.5 Google OAuth Server-Side Verification
- **Endpoint**: `POST /api/v1/auth/oauth/google`
- **Request Body**:
  ```json
  {
    "id_token": "eyJhbGciOiJSUzI1Ni..."
  }
  ```
- **Responses**:
  - `200 OK`: Validates token signature, issues application JWT session, and returns `TokenOut`.
  - `401 Unauthorized`: Token expired, invalid signature, or wrong issuer.

### 1.6 Apple OAuth (Conditional Gate)
- **Endpoint**: `POST /api/v1/auth/oauth/apple`
- **Responses**:
  - `501 Not Implemented`: Returns detailed message explaining Apple Sign-In requires an active US\$99/yr Apple Developer Program membership.

---

## 2. Municipalities & Places Endpoints (`/api/v1`)

### 2.1 List Municipalities
- **Endpoint**: `GET /api/v1/municipalities`
- **Query Parameters**:
  - `q` (string, optional, max 80): Filter by municipality name substring.
- **Responses**:
  - `200 OK`:
    ```json
    [
      {
        "id": "a1b2c3d4-...",
        "name": "Cabanatuan City",
        "slug": "cabanatuan-city",
        "is_city": true,
        "center_lat": 15.4865,
        "center_lng": 120.9734
      }
    ]
    ```

### 2.2 Search & Filter Places
- **Endpoint**: `GET /api/v1/places`
- **Query Parameters**:
  - `q` (string, optional, max 100): Full-text search across name, address, category, and municipality name.
  - `categories` (string or array): Supported as repeated query parameters (`?categories=cafe&categories=restaurant`) or comma-separated (`?categories=cafe,restaurant`).
  - `municipality_id` (UUID, optional): Filter by municipality UUID.
  - `featured` (boolean, optional): Filter by `is_featured = true`.
  - `min_lat`, `max_lat`, `min_lng`, `max_lng` (float, optional): Map viewport bounding box filter.
  - `limit` (integer, default 50, range 1–200).
  - `offset` (integer, default 0).
- **Responses**:
  - `200 OK`:
    ```json
    {
      "total": 17,
      "limit": 50,
      "offset": 0,
      "items": [
        {
          "id": "e4f5a6b7-...",
          "name": "Minalungao National Park",
          "category": "nature_park",
          "latitude": 15.2981,
          "longitude": 121.1223,
          "municipality_id": "c1d2e3f4-...",
          "municipality_name": "General Tinio",
          "address_text": "Brgy. Pias, General Tinio, Nueva Ecija",
          "description": "Protected limestone canyon along the Peñaranda River...",
          "phone": null,
          "website": null,
          "opening_hours": "07:00-17:00",
          "estimated_cost_min": 100.0,
          "estimated_cost_max": 500.0,
          "cost_currency": "PHP",
          "image_url": null,
          "image_license": null,
          "source_name": "CuratedNuevaEcijaMVP",
          "source_record_id": "curated/minalungao-national-park",
          "source_url": "https://www.openstreetmap.org/way/238471920",
          "imported_at": "2026-10-30T10:30:00Z",
          "verified_at": "2026-10-30T10:30:00Z",
          "is_featured": true,
          "tags": ["nature_park", "Nature & Parks", "Family-Friendly"],
          "directions_url": "https://www.google.com/maps/dir/?api=1&destination=15.2981,121.1223"
        }
      ]
    }
    ```
  - `422 Unprocessable Content`: Invalid category query filter.

### 2.3 Get Place Detail
- **Endpoint**: `GET /api/v1/places/{place_id}`
- **Responses**:
  - `200 OK`: Full `PlaceOut` details and provenance.
  - `404 Not Found`: Place not found or inactive.

---

## 3. System Health Check

### 3.1 Health Endpoint
- **Endpoint**: `GET /api/v1/health`
- **Responses**:
  - `200 OK`:
    ```json
    {
      "status": "ok",
      "province_scope": "Nueva Ecija",
      "environment": "development"
    }
    ```

---

## 4. Itinerary Management Endpoints (`/api/v1/itineraries`)

All itinerary endpoints require Bearer authentication:
`Authorization: Bearer <jwt_access_token>`

All operations enforce strict Broken Object Level Authorization (BOLA): querying resources owned by other users returns `404 Not Found` to prevent account reconnaissance or ID enumeration.

### 4.1 Create Itinerary
- **Endpoint**: `POST /api/v1/itineraries`
- **Request Body**:
  ```json
  {
    "title": "Nueva Ecija Heritage & Nature Tour",
    "destination": "Nueva Ecija",
    "start_date": "2026-11-01",
    "end_date": "2026-11-03",
    "daily_budget": 3500.0,
    "preferences": ["nature", "culture"],
    "type": "custom",
    "assumptions": ["Budget excludes inter-city transit"],
    "days": [
      {
        "day_number": 1,
        "travel_date": "2026-11-01",
        "title": "Day 1: Nature Exploration",
        "items": [
          {
            "place_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            "sort_order": 1,
            "duration_minutes": 120,
            "notes": "Bring cash for balsa rafting"
          }
        ]
      }
    ]
  }
  ```
- **Responses**:
  - `201 Created`: Full `ItineraryOut` model with generated day IDs and nested items.
  - `401 Unauthorized`: Missing or invalid bearer token.
  - `422 Unprocessable Content`: Validation failure (end date before start date, negative budget).

### 4.2 List User Itineraries
- **Endpoint**: `GET /api/v1/itineraries`
- **Responses**:
  - `200 OK`: Array of `ItineraryOut` objects belonging exclusively to the authenticated user.

### 4.3 Get Single Itinerary
- **Endpoint**: `GET /api/v1/itineraries/{id}`
- **Responses**:
  - `200 OK`: Full `ItineraryOut` model including all days and eagerly loaded POI places.
  - `404 Not Found`: Itinerary does not exist or belongs to another user (BOLA protected).

### 4.4 Update Itinerary Metadata
- **Endpoint**: `PATCH /api/v1/itineraries/{id}`
- **Request Body**:
  ```json
  {
    "title": "Updated Trip Title",
    "daily_budget": 4000.0
  }
  ```
- **Responses**:
  - `200 OK`: Updated `ItineraryOut`.
  - `404 Not Found`: BOLA gate failure.

### 4.5 Delete Itinerary
- **Endpoint**: `DELETE /api/v1/itineraries/{id}`
- **Responses**:
  - `204 No Content`: Successfully deleted itinerary and cascaded all associated days and items.
  - `404 Not Found`: BOLA gate failure.

### 4.6 Add Day to Itinerary
- **Endpoint**: `POST /api/v1/itineraries/{id}/days`
- **Request Body**:
  ```json
  {
    "day_number": 2,
    "travel_date": "2026-11-02",
    "title": "Day 2: Historical Gapan"
  }
  ```
- **Responses**:
  - `201 Created`: Updated `ItineraryOut` with new day appended.
  - `404 Not Found`: BOLA gate failure.

### 4.7 Add Stop to Day
- **Endpoint**: `POST /api/v1/itineraries/{id}/days/{day_id}/items`
- **Request Body**:
  ```json
  {
    "place_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "duration_minutes": 90,
    "notes": "Afternoon coffee stop"
  }
  ```
  *Or for custom off-grid venue:*
  ```json
  {
    "custom_title": "Lola's Mango Orchard & Campsite",
    "custom_lat": 15.632,
    "custom_lng": 121.144,
    "duration_minutes": 180,
    "estimated_cost_min": 100.0,
    "estimated_cost_max": 250.0
  }
  ```
- **Responses**:
  - `201 Created`: Updated `ItineraryOut`.
  - `400 Bad Request`: `"This destination has already been added to this day."` (duplicate stop guard).
  - `404 Not Found`: Itinerary or day not found or BOLA violation.

### 4.8 Delete Stop
- **Endpoint**: `DELETE /api/v1/itineraries/{id}/days/{day_id}/items/{item_id}`
- **Responses**:
  - `200 OK`: Updated `ItineraryOut` with re-indexed item `sort_order` values.
  - `404 Not Found`: Stop not found or BOLA violation.

### 4.9 Batch Reorder Stops
- **Endpoint**: `POST /api/v1/itineraries/{id}/reorder`
- **Request Body**:
  ```json
  {
    "items": [
      {
        "id": "item-uuid-2",
        "day_id": "day-uuid-1",
        "sort_order": 1
      },
      {
        "id": "item-uuid-1",
        "day_id": "day-uuid-1",
        "sort_order": 2
      }
    ]
  }
  ```
- **Responses**:
  - `200 OK`: Updated `ItineraryOut`.
  - `400 Bad Request`: If any item ID does not belong to the target itinerary.
  - `404 Not Found`: BOLA gate failure.

### 4.10 Generate Suggested Itinerary
- **Endpoint**: `POST /api/v1/itineraries/suggest`
- **Authentication**: Optional. If Bearer token is provided and `save_immediately: true`, the generated itinerary is persisted and assigned to the authenticated user. If unauthenticated or `save_immediately: false`, returns an unpersisted draft (`user_id = null`).
- **Request Body**:
  ```json
  {
    "title": "Suggested Bongabon Trip",
    "destination": "Bongabon",
    "start_date": "2026-11-01",
    "end_date": "2026-11-02",
    "daily_budget": 2500.0,
    "preferences": ["nature", "food"],
    "save_immediately": false
  }
  ```
- **Clustering & Pacing Rules**:
  - Day 1 anchor resolved to destination municipality center (or nearest featured POI). Subsequent days cluster around unvisited geographic clusters to prevent backtracking.
  - Places scored deterministically: +40 for category match, +20 if featured, +30 max proximity bonus, -25 duplicate category penalty, +10 budget fit.
  - Paced realistically with 2-3 stops/day, slotting a morning visit (09:00), lunchtime dining window (12:00 PM for restaurants/cafes), and afternoon activity (14:30).
- **Responses**:
  - `200 OK`: `ItineraryOut` model with `type: "suggested"`, structured multi-day items, and generated transparent assumptions list.
  - `422 Unprocessable Content`: Invalid date range (end date before start date or trip longer than 7 days) or negative daily budget.



