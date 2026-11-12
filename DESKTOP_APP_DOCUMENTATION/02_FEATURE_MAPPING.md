# 02. Feature Mapping: Web Client vs. Python Flet Desktop Client

**Target System**: Nueva Ecija Travel Itinerary Planner ("Trip mo, trip ko")  
**Existing Web Client**: Ionic 9 / Angular 22 (`Project/`)  
**Desktop Client**: Python Flet (`desktop_client/`)  
**Backend API**: FastAPI (`http://127.0.0.1:8000/api/v1`)  
**Document**: `DESKTOP_APP_DOCUMENTATION/02_FEATURE_MAPPING.md`  

---

## 1. Feature Comparison & Implementation Matrix

| Existing Web Feature | Desktop Implementation (Flet) | Backend Integration | Status |
| :--- | :--- | :--- | :---: |
| **1. Splash & Brand Onboarding** | Native desktop launch window with Nueva Ecija branding (*"Trip mo, trip ko"*), skyline graphic, and version badge. | None (Client startup) | Staged |
| **2. User Registration** | Desktop form with first name, last name, username, email, password strength indicator, matching validation, and error banner. | `POST /api/v1/auth/register` | Staged |
| **3. User Login** | Desktop login dialog/view with email, password, password eye toggle, remember me checkbox, and immediate error banner feedback. | `POST /api/v1/auth/login` | Staged |
| **4. Demo Account (Pattranite Persona)** | One-tap `[Explore Demo Account]` button that activates the verified Pattranite Limpatiyakorn demo session without credentials. | Client state + Mock/API token | Staged |
| **5. Guest Mode Access** | One-tap `[Continue as Guest]` button granting immediate desktop access with local offline storage (`guest_storage.json`). | Local storage + Optional API sync | Staged |
| **6. User Logout & Confirmation** | Logout confirmation dialog alerting the user if unsynced guest trips exist before clearing local tokens. | Client session invalidation | Staged |
| **7. Profile Management** | Desktop profile view displaying traveler identity, username, email, and modal for editing profile/credentials. | `GET /api/v1/auth/me`<br>`PATCH /api/v1/auth/me` | Staged |
| **8. App Settings** | Desktop settings panel with theme toggle (Light / Dark mode), default daily budget preference, API Base URL override, and cache clear. | Local settings persistence | Staged |
| **9. Home Dashboard & Quick Entry** | Desktop wide-screen dashboard featuring hero banner, debounced search bar, side-by-side Suggested & Custom planner action cards, and popular carousel. | `GET /api/v1/places?featured=true`<br>`GET /api/v1/places?q=...` | Staged |
| **10. 300ms Debounced Destination Search** | Real-time desktop search input with 300ms debounce querying places across name, address, category, and municipality. | `GET /api/v1/places?q={query}&limit=50` | Staged |
| **11. Popular Destinations Grid** | Multi-column responsive desktop cards displaying photography, category tags, municipality, and honest pricing. | `GET /api/v1/places?featured=true` | Staged |
| **12. 16-Category Catalog Browser** | Desktop catalog browser with 16 category filter pills/chips (`Tourist Spots`, `Food & Cafes`, `Resorts & Stays`, `Culture`, etc.) and search. | `GET /api/v1/places?categories=...` | Staged |
| **13. Municipality Filter (32 LGUs)** | Municipality dropdown filter covering Cabanatuan, Gapan, San Jose, Muñoz, Palayan, Bongabon, Pantabangan, Gabaldon, etc. | `GET /api/v1/municipalities` | Staged |
| **14. Destination Detail Dialog** | Desktop modal/sheet with venue photos, opening hours, honest pricing (`₱min - ₱max` or "Cost not provided"), description, and directions action. | `GET /api/v1/places/{id}` | Staged |
| **15. Keyless Google Maps Directions Link** | One-tap external directions launcher opening standard browser directions URL without paid API keys. | Standard URL: `https://www.google.com/maps/dir/?api=1&destination=lat,lng` | Staged |
| **16. Interactive Provincial Map & Stops** | Desktop spatial explorer plotting places and itinerary stops with coordinate badges, zoom/pan controls, and deep-link launcher. | OpenStreetMap tile links + `places` coordinates | Staged |
| **17. Suggested Itinerary Questionnaire** | Form collecting Destination (with 32-LGU autocomplete), Travel Dates, Daily Budget presets, Pacing (Relaxed, Moderate, Fast), and Preferences. | Form state validation | Staged |
| **18. Algorithmic Suggested Generation** | Triggers backend Haversine clustering engine with 2-Opt road optimization, midday lunch anchor (12:00 PM), and lodging exclusion on 1-day trips. | `POST /api/v1/itineraries/suggest` | Staged |
| **19. Suggested Itinerary Preview & Review** | Desktop timeline display with day tabs, stop cards, transparent assumptions, verified budget math, and one-tap save. | Backend response / Client preview | Staged |
| **20. Custom Itinerary Setup** | Step 1 setup: Trip Title input, Destination, Date range picker, Daily budget allowance, and initial travel preferences. | Form state validation | Staged |
| **21. Custom Builder Catalog Browser** | Step 2: Multi-category place browser with skeleton shimmer cards, "+ Add to Day X" toggle, and duplicate-stop indicator. | `GET /api/v1/places` + local cache | Staged |
| **22. Custom Builder Off-Grid Venue Modal** | Modal allowing travelers to add custom stops (Title, address, geofenced latitude/longitude, estimated cost, notes). | Validated against NE bounding box | Staged |
| **23. Custom Builder Timeline & Schedule** | Step 3: Interactive timeline with reordering (move up/down), auto-calculated sequential times with travel buffers, and stop deletion. | Client scheduling math | Staged |
| **24. Edit Scheduled Stop Modal** | Modal to edit a stop's planned time, duration minutes, cost range (`min <= max`), personal notes, or move to another day. | `PATCH /days/{d}/items/{i}` or in-memory | Staged |
| **25. Zero-Stop & Date Truncation Guards** | Guards that disable save if 0 stops are added, and prompt confirmation before shortening dates when discarded days have stops. | Client validation & dialogs | Staged |
| **26. Itinerary Save & Cloud Synchronization** | Synchronizes multi-day custom and suggested plans to the backend database (or local JSON in Guest mode). | `POST /api/v1/itineraries`<br>`PATCH /api/v1/itineraries/{id}` | Staged |
| **27. Saved Itineraries (History) View** | Desktop collection view of saved trips with filter tabs (All, Suggested, Custom, Upcoming), budget summary, and trip cards. | `GET /api/v1/itineraries` | Staged |
| **28. Saved Trip Detail & In-Place Editor** | Comprehensive multi-day itinerary view with day switcher, stop details, leg transit badges, and in-place editing. | `GET /api/v1/itineraries/{id}` | Staged |
| **29. Trip Export Suite** | Export itinerary as RFC 5545 `.ics` calendar file, text clipboard summary, and printable summary. | Client utility (`desktop_client/core/export.py`) | Staged |
| **30. Trip Deletion with Confirmation** | Destructive trip deletion protected by a confirmation dialog with immediate reactive UI removal. | `DELETE /api/v1/itineraries/{id}` | Staged |
| **31. Connection Health & Offline Detection** | Real-time connectivity monitor detecting backend reachability, showing non-intrusive status pills without crashing. | `GET /api/v1/health` polling | Staged |

---

## 2. Desktop-Specific Layout Enhancements

1. **Persistent Desktop Navigation Rail / Sidebar**:
   - Modern, collapsible sidebar on the left containing:
     - Header: *"Trip mo, trip ko"* logo & brand title.
     - Primary Navigation: **Dashboard / Home**, **Explore Places**, **Suggested Itinerary**, **Custom Builder**, **Saved Trips**, **Profile & Settings**.
     - Footer: Server Connectivity Status Pill (`● Online (FastAPI)` / `○ Offline Mode`) and Current User badge.
2. **Spacious Multi-Column Workspaces**:
   - On wide desktop screens, places and itineraries will be displayed in clean 2-column or 3-column responsive card grids rather than narrow mobile lists.
   - Itinerary Builder will utilize a side-by-side **Dual-Pane View**: Left pane displays the Curated Places Catalog with filters, Right pane displays the Active Day Timeline with live budget calculation.
3. **Responsive Window Sizing**:
   - Minimum window dimensions: `1024 × 700` px.
   - Default window dimensions: `1280 × 800` px (resizable and maximizable).
