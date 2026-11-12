# API Integration Guide: Nueva Ecija Travel Desktop Client

**Client:** Python Flet Desktop Application  
**Target Backend:** FastAPI REST Service (`http://127.0.0.1:8000/api/v1`)  
**Network Client:** `httpx.AsyncClient` with connection pooling & Bearer token injection  
**Document Ref:** `DESKTOP_APP_DOCUMENTATION/05_API_INTEGRATION.md`

---

## 1. Network Client Architecture

The desktop application connects to the backend service via `desktop_client/core/api_client.py`.

### 1.1 Outbound Request Headers
Every request emitted by the desktop client includes standard identifying headers:
```http
Accept: application/json
Content-Type: application/json
User-Agent: NuevaEcijaTravel-Desktop/1.0.0
Authorization: Bearer <JWT_ACCESS_TOKEN>  (injected automatically when authenticated)
```

### 1.2 Error Hierarchy & Status Code Mapping
The API client maps HTTP status codes into typed Python exceptions:

| Status Code | Exception Raised | Handled By UI |
| :---: | :--- | :--- |
| **401 / 403** | `AuthenticationError` | Prompts user to log in; triggers automatic token refresh retry if refresh token exists |
| **404** | `NotFoundError` | Displays "Resource not found" feedback banner |
| **422** | `ValidationError` | Surfaces Pydantic validation details in form field errors |
| **Connect / Timeout** | `NetworkError` | Switches TopHeader status pill to "Offline / Local" and falls back to guest storage |
| **500+** | `ApiClientError` | Displays generic user-friendly error dialog with diagnostic code |

---

## 2. Authentication & Traveler Endpoints

### 2.1 Sign In (`POST /api/v1/auth/login`)
- **Request Body:**
  ```json
  {
    "email": "traveler@example.com",
    "password": "SecurePassword123"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "refresh_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "user": {
      "id": "dbd6b696-a9a8-4753-92de-f100b15d38ec",
      "email": "traveler@example.com",
      "full_name": "Maria Clara",
      "role": "traveler",
      "is_active": true,
      "is_verified": true
    }
  }
  ```

### 2.2 Account Registration (`POST /api/v1/auth/register`)
- **Request Body:**
  ```json
  {
    "email": "traveler@example.com",
    "password": "SecurePassword123",
    "full_name": "Maria Clara"
  }
  ```
- **Response (201 Created):** Returns identical `TokenOut` schema containing access and refresh tokens.

### 2.3 Token Refresh (`POST /api/v1/auth/refresh`)
- **Request Body:** `{"refresh_token": "<JWT_REFRESH_TOKEN>"}`
- **Behavior:** Automatically executed by `ApiClient` upon receiving a 401 Unauthorized response before retrying the original request.

### 2.4 Profile Management (`GET /api/v1/auth/me` and `PATCH /api/v1/auth/me`)
- Allows fetching and updating display name and traveler preferences.

---

## 3. Places & Destination Catalog Endpoints

### 3.1 List Municipalities (`GET /api/v1/municipalities`)
- **Query Parameters:** `q` (optional text filter)
- **Response (200 OK):**
  ```json
  [
    {
      "id": "c02a2df2-8272-45aa-b0b3-614e0b714113",
      "name": "Science City of Muñoz",
      "zip_code": "3119",
      "place_count": 142
    },
    {
      "id": "dbd6b696-a9a8-4753-92de-f100b15d38ec",
      "name": "Cabanatuan City",
      "zip_code": "3100",
      "place_count": 512
    }
  ]
  ```

### 3.2 Places Catalog Query (`GET /api/v1/places`)
- **Query Parameters:**
  - `page` (int, default 1)
  - `page_size` (int, default 20)
  - `search` (string, case-insensitive match against name, description, tags)
  - `category` (string, one of 16 canonical categories)
  - `municipality_id` (UUID or LGU name)
  - `is_featured` (boolean)
  - `sort` (string: `name`, `cost_asc`, `cost_desc`, `rating`)
- **Response (200 OK):**
  ```json
  {
    "items": [
      {
        "id": "e81c15c8-1123-455b-80a1-c8b84d4677ee",
        "name": "CLSU Agricultural Museum & Philippine Carabao Center",
        "category": "museum_cultural",
        "latitude": 15.7335,
        "longitude": 120.9324,
        "municipality_id": "c02a2df2-8272-45aa-b0b3-614e0b714113",
        "municipality_name": "Science City of Muñoz",
        "address_text": "CLSU Compound, Science City of Muñoz, Nueva Ecija",
        "opening_hours": "08:00 AM - 05:00 PM (Mon-Fri)",
        "estimated_cost_min": 50.0,
        "estimated_cost_max": 50.0,
        "cost_currency": "PHP",
        "is_featured": true,
        "directions_url": "https://www.google.com/maps/dir/?api=1&destination=15.7335,120.9324"
      }
    ],
    "total": 2673,
    "page": 1,
    "page_size": 20,
    "total_pages": 134
  }
  ```

---

## 4. Itinerary & Scheduling Endpoints

### 4.1 Automated Clustered Suggestion (`POST /api/v1/itineraries/suggest`)
- **Request Body:**
  ```json
  {
    "title": "Suggested Nueva Ecija Itinerary",
    "destination": "Nueva Ecija",
    "start_date": "2026-11-20",
    "end_date": "2026-11-22",
    "daily_budget": 2500.0,
    "preferences": ["nature_park", "restaurant", "tourist_attraction"],
    "pacing": "moderate",
    "travel_mode": "DRIVE",
    "save_immediately": false
  }
  ```
- **Response (200 OK):**
  Returns multi-day itinerary with geographically clustered stops, turn-by-turn routing distances between consecutive stops (`travel_distance_meters`, `travel_duration_seconds`), and honest day costs.

### 4.2 Itinerary CRUD (`POST`, `GET`, `PUT`, `DELETE /api/v1/itineraries`)
- **List User Itineraries:** `GET /api/v1/itineraries`
- **Get Detail by ID:** `GET /api/v1/itineraries/{id}`
- **Create Custom Itinerary:** `POST /api/v1/itineraries`
- **Update Metadata:** `PUT /api/v1/itineraries/{id}`
- **Delete Itinerary:** `DELETE /api/v1/itineraries/{id}`

### 4.3 Days & Stops Management
- **Add Stop:** `POST /api/v1/itineraries/{id}/days/{day_id}/items`
- **Edit Stop:** `PUT /api/v1/itineraries/{id}/days/{day_id}/items/{item_id}`
- **Delete Stop:** `DELETE /api/v1/itineraries/{id}/days/{day_id}/items/{item_id}`
- **Batch Reorder Stops:** `PUT /api/v1/itineraries/{id}/days/{day_id}/reorder` with payload `{"items": [{"id": "...", "day_id": "...", "sort_order": 1}]}`.
