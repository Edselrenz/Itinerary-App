# Known Limitations & Technical Constraints: Nueva Ecija Travel Desktop Client

**Client:** Python Flet Desktop Application  
**Document Ref:** `DESKTOP_APP_DOCUMENTATION/09_KNOWN_LIMITATIONS.md`  
**Date:** November 2026

---

## 1. Authentication & OAuth Constraints

### 1.1 Apple Sign-In Gating
- **Limitation:** Apple OAuth is strictly gated with HTTP 501 Not Implemented in the backend pilot build.
- **Root Cause:** Apple Developer Program membership (US$99/yr) and Service ID domain verification are pending institutional configuration.
- **Truth in Advertising:** The desktop client presents clear email/password authentication and Guest Mode without advertising non-functional Apple buttons.

### 1.2 Google OAuth on Desktop
- **Limitation:** On mobile and web, Google Sign-In operates via popup windows (`window.open`). In a native desktop shell, OAuth requires spawning a local loopback web server (`http://127.0.0.1:port/callback`) and opening the system browser.
- **Current Mitigation:** Email and password registration, plus friction-free Guest Mode, are the primary supported desktop authentication paths in version 1.0.

---

## 2. Geospatial & Map Rendering

### 2.1 Interactive Map Tile Embedding
- **Limitation:** Native Flutter embedded WebViews for MapLibre / Leaflet tiles have cross-platform compilation quirks on certain Windows graphics drivers without hardware acceleration.
- **Desktop Solution:** The desktop client displays GIS coordinates, turn-by-turn routing distances (`travel_distance_meters`), estimated driving duration (`travel_duration_seconds`), and one-click "Get Directions" buttons that open the venue directly in Google Maps in the user's default browser.

### 2.2 Hardware GPS Sensor Availability
- **Limitation:** Standard desktop computers and workstations do not feature dedicated GPS/GNSS satellite receiver hardware.
- **Mitigation:** The AI Wizard and Custom Builder default the trip origin to Nueva Ecija central coordinates (Cabanatuan City: `15.4865, 120.9734`) or allow the traveler to specify an entry municipality.

---

## 3. Offline Capabilities & Scope

### 3.1 Offline Catalog Browsing
- **Limitation:** When disconnected from the FastAPI backend, querying new search terms or paginating through un-cached portions of the 2,670+ POI database requires server connectivity.
- **Mitigation:** In-memory caching stores previously queried municipalities and categories. Saved and draft itineraries stored in `desktop_client/storage/guest_storage.json` are 100% readable and exportable offline.

---

## 4. Multi-Window & Display Behavior

### 4.1 Single-Window Desktop Model
- **Limitation:** The application is architected around a single cohesive desktop window shell with modal dialogs rather than detached floating tool windows.
- **Rationale:** Prevents window sprawl, minimizes taskbar clutter, and ensures consistent state synchronization across itinerary builders.
- **Minimum Resolution:** The window requires at least 1024x720 pixels to ensure dual-pane builder columns render without horizontal clipping.
