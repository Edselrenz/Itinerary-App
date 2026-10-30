# Known Issues & Technical Limitations

This document tracks identified bugs, intentional technical constraints, and temporary limitations across the application.

---

## 1. Intentional Architectural Constraints (By Design)

### 1.1 Apple Sign-In Disabled State
- **Status**: By Design / Gated.
- **Context**: Apple Sign-In requires an active Apple Developer Program membership (US\$99/year). Per the MVP zero-cost compliance matrix, this feature is gated behind `enableAppleAuth = false` in `environment.ts` and `.env`.
- **User Impact**: The Apple button is rendered disabled with a truthful caption: *"Apple Sign-In is disabled in this pilot build"*. Calling `POST /api/v1/auth/oauth/apple` returns `501 Not Implemented`.

### 1.2 History & Profile Tabs Deferred to v1.1
- **Status**: By Design / Phased Scope.
- **Context**: The MVP blueprint explicitly focuses on Home, Map, and Itinerary Planning flows.
- **User Impact**: In the 4-tab shell, the History tab displays a clean placeholder (*"Planned for a later release — MVP focuses on Home discovery, interactive Map, and Itinerary Planning"*), and the Profile tab serves as a session status / guest mode indicator.

### 1.3 External Directions Hand-Off Instead of Live Transit
- **Status**: By Design / Policy Compliance.
- **Context**: The Figma design sketched a public-transit card with bus departures. However, public transit schedules for provincial routes (jeepneys, tricycles, provincial buses) lack real-time digital feeds. Building a mock transit router would present unverified schedules as fact.
- **Resolution**: Replaced with standard Google Maps directions URLs opening externally in the traveler's browser/maps app without API keys.

---

## 2. Environment & Host Limitations

### 2.1 Local PostgreSQL vs SQLite Configuration
- **Status**: Active Workaround Available.
- **Context**: Local development environments may not have a PostgreSQL daemon running or `psql` on the system PATH.
- **Resolution**: The backend ORM entities and database session manager are architected with dual-engine compatibility (`JsonType`, `sa.Uuid`). Setting `DATABASE_URL=sqlite:///./nueva_ecija_travel.db` in `.env` allows running the complete application locally without starting PostgreSQL.

---

## 3. In-Progress Features (Pending Milestones)

| Feature | Current State | Milestone Target |
| :--- | :--- | :--- |
| **Home Search Bar** | Static UI input in place | Milestone 4 (Connecting to `GET /api/v1/places` with 300ms RxJS debounce) |
| **Popular Destinations** | Static card structure in place | Milestone 4 (Loading `GET /api/v1/places?featured=true`) |
| **Interactive Leaflet Map** | Placeholder shell in `map.page` | Milestone 5 (Leaflet initialization, tile rendering, 16 category filters, bottom sheet) |
| **Custom / Suggested Itinerary** | Card entry points in place | Milestones 6 & 7 (Builder, Haversine engine, BOLA CRUD) |

