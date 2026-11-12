# Nueva Ecija Travel — Desktop Client (Python Flet)

A native-feeling, desktop-first cross-platform application for discovering destinations and crafting multi-day travel itineraries in the province of Nueva Ecija, Philippines. Built with **Python 3.14+** and **Flet 1.1.2** (Flutter Material 3), consuming the existing FastAPI backend and PostgreSQL / SQLite database services.

---

## 🌟 Key Features

1. **2,670+ Curated Destinations**: Explore 32 LGUs across 16 canonical categories with honest pricing, operating hours, and Google Maps integration.
2. **Dual-Mode Operation**:
   - **Guest Mode**: Plan and save itineraries locally on your machine (`desktop_client/storage/guest_storage.json`) without signing in.
   - **Cloud Sync**: Register/Sign in to persist itineraries to your traveler profile across devices.
3. **AI Suggested Itinerary Wizard**: 4-step wizard that clusters nearby venues geographically, eliminating unnecessary driving and backtracking across Nueva Ecija.
4. **Dual-Pane Custom Itinerary Builder**:
   - Left Pane: Instant POI search, category filters, and off-grid custom venue support.
   - Right Pane: Chronological timeline with stop reordering (up/down), duration editing, day switcher, and zero-stop validation guard.
5. **Turn-by-Turn Routing Indicators**: Distance (km) and travel duration (mins) between consecutive stops.
6. **Multi-Format Export**:
   - **iCalendar (.ics)**: One-click export for Google Calendar, Apple Calendar, and Microsoft Outlook.
   - **Travel Dossier (.md)**: Human-readable markdown trip summary with timing and honest cost notes.
   - **Structured Data (.json)**: Complete itinerary representation.
7. **Anti-Generic Visual Design**: Authentic Nueva Ecija identity featuring Deep Emerald Green (`#1b4332`), Travel Azure Blue (`#0084ff`), Warm Sand, and WCAG 2.2 AA contrast standards. Light & Dark mode support.

---

## 📂 Architecture Overview

```text
desktop_client/
├── main.py                     # Desktop application entrypoint & shell manager
├── requirements.txt            # Python dependencies (flet, httpx, pydantic, pytest)
├── .env.example                # Environment configuration template
├── README.md                   # Desktop client documentation
├── config/
│   ├── __init__.py
│   └── settings.py             # Settings, color palette, categories, LGUs
├── core/
│   ├── __init__.py
│   ├── api_client.py           # Async HTTP client with connection pooling & error handling
│   ├── session.py              # Traveler credentials, JWT refresh, guest state manager
│   ├── storage.py              # Local JSON persistence for offline/guest itineraries
│   └── export.py               # RFC 5545 iCalendar, Markdown, and JSON exporters
├── models/
│   ├── __init__.py
│   ├── user.py                 # User, AuthToken, Profile models
│   ├── place.py                # Place, Municipality, PaginatedPlaces models
│   └── itinerary.py            # Itinerary, ItineraryDay, ItineraryItem models
├── services/
│   ├── __init__.py
│   ├── auth_service.py         # Login, register, token refresh, guest mode
│   ├── place_service.py        # POI catalog search, filter, and municipality queries
│   └── itinerary_service.py    # Algorithmic clustering, custom building, stop management
├── components/
│   ├── __init__.py
│   ├── sidebar.py              # Left-hand persistent navigation with active pill highlighting
│   ├── header.py               # Context bar with live backend status indicator
│   ├── place_card.py           # Destination card with honest pricing & "+ Add" button
│   ├── stop_card.py            # Timeline stop with reordering arrows, timing, and route stats
│   └── dialogs.py              # Place details modal, custom venue dialog, export modal
├── views/
│   ├── __init__.py
│   ├── welcome_view.py         # First-time onboarding hero
│   ├── login_view.py           # Secure sign-in form
│   ├── signup_view.py          # Account registration form
│   ├── dashboard_view.py       # Metrics hub, quick actions, featured carousel
│   ├── places_view.py          # 16-category & 32-LGU explorer with pagination
│   ├── suggested_wizard_view.py# 4-step clustered route generator
│   ├── custom_builder_view.py  # Dual-pane interactive schedule builder
│   ├── saved_trips_view.py     # Itinerary management & export hub
│   ├── trip_detail_view.py     # Day-by-day timeline inspector
│   └── profile_view.py         # Traveler settings, theme toggle, cache management
└── tests/
    ├── __init__.py
    ├── test_api_client.py      # HTTP client and error hierarchy tests
    ├── test_auth_service.py    # Auth, session, and guest mode tests
    ├── test_place_service.py   # Place models and pricing formatting tests
    ├── test_itinerary_service.py # Itinerary models and cost accumulation tests
    ├── test_storage_export.py  # Guest storage CRUD and .ics/.md export tests
    └── test_live_integration.py# Live integration tests against FastAPI backend
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.14.3 64-bit on Windows)
- Running FastAPI backend on `http://127.0.0.1:8000`

### 2. Installation
```powershell
# Navigate to desktop_client directory
cd desktop_client

# Install requirements
pip install -r requirements.txt
```

### 3. Running the Desktop Application
```powershell
python -m desktop_client.main
# Or run directly from desktop_client folder:
python main.py
```

### 4. Running Automated Tests
```powershell
python -m pytest desktop_client/tests -v
```

---

## 🔒 Security & Backend Boundary
- The desktop client communicates exclusively with the backend via REST endpoints (`/api/v1`).
- Direct database credentials or raw SQL connections are strictly prohibited in the client layer.
- Bearer access tokens are injected into outbound headers with automatic refresh on HTTP 401.
