# Project Overview: Nueva Ecija Travel Itinerary

## 1. Executive Summary

The **Nueva Ecija Travel Itinerary Application** is a specialized hybrid mobile and web application designed to help travelers discover, plan, organize, and navigate trips across the province of **Nueva Ecija, Central Luzon, Philippines**.

The project translates the official **Product and Engineering Blueprint** (dated 27 October 2026) and the **Figma UI/UX Specifications** (`Travel Itinerary App.fig`) into a production-grade, zero-cost architecture that avoids paid APIs (such as Google Maps Platform, Google Places API, paid routing APIs, or paid generative AI endpoints).

---

## 2. Core Objectives

1. **Province-Focused Discovery**: Provide comprehensive, verified discovery of destinations across Nueva Ecija's cities and municipalities (Cabanatuan, Gapan, Science City of Muñoz, Palayan, San Jose, Bongabon, Pantabangan, General Tinio, Gabaldon, Laur, Santa Rosa, and Talavera).
2. **Flexible Traveler Entry**: Support both authenticated travelers (email/password with Argon2id and Google OAuth) and anonymous guest travelers with local-first device storage.
3. **Dual Planning Modes**:
   - **Suggested Itinerary Generator**: An algorithmic, deterministic scoring engine that clusters nearby destinations using Haversine distance, respects travel dates, accounts for daily PHP budgets, and applies traveler preference tags without hallucinating venues.
   - **Custom Itinerary Builder**: An interactive builder allowing travelers to add database POIs or custom off-grid stops, reorder schedules, calculate honest budgets, and edit notes.
4. **Interactive Exploration Map**: An interactive Leaflet map bounded to Nueva Ecija with 16 canonical category filters, POI clustering, and bottom-sheet details.
5. **Zero-Cost & Open-Data Compliance**: Fully compliant with OpenStreetMap Tile Usage Policy, Nominatim Usage Policies, and ODbL guidelines.

---

## 3. Technology Stack

| Layer | Technology | Version / Specification | Role in System |
| :--- | :--- | :--- | :--- |
| **Mobile / Web Client** | Ionic Framework + Angular | Ionic 9, Angular 22, Capacitor 8 | Hybrid mobile shell for Web, Android, and iOS packaging. |
| **Local Client Storage** | `@ionic/storage-angular` | v4.0.0 (IndexedDB / LocalStorage) | Local-first persistence for guest travelers under `ne_guest_itineraries_v1`. |
| **Interactive Map** | Leaflet + Leaflet MarkerCluster | Leaflet v1.9.4 | Bounded OpenStreetMap raster tile viewer and marker clustering. |
| **Backend REST API** | Python + FastAPI | Python 3.11+ / 3.14, FastAPI 0.136+ | Asynchronous REST backend exposing versioned `/api/v1` routes. |
| **Data Validation & Typing** | Pydantic v2 | Pydantic 2.13+ | Request/response schema validation and settings management. |
| **ORM & Persistence** | SQLAlchemy 2.0 | SQLAlchemy 2.0.50 | Type-annotated relational models and database abstraction. |
| **Database Migrations** | Alembic | Alembic 1.20+ | Version-controlled schema migrations for relational tables. |
| **Primary Database** | PostgreSQL / SQLite | PostgreSQL 15+ (Production) / SQLite (Dev/Test) | Relational database persisting users, POIs, and itineraries. |
| **Authentication & Crypto** | Argon2id + PyJWT + Google Auth | `pwdlib[argon2]`, `pyjwt`, `google-auth` | Secure password hashing, short-lived JWT sessions, Google OAuth server-side verification. |

---

## 4. Target Users

1. **Day-trippers & Weekend Travelers**: Seeking curated popular destinations (e.g., Minalungao National Park, Pantabangan Lake, Lumang Gapan Heritage District) with reliable hours and price estimates.
2. **Multi-day Vacationers**: Requiring organized, geographically clustered daily itineraries (e.g., "Day 1 - Bongabon" featuring local dining, heritage sites, and cabins).
3. **Guest / Privacy-Conscious Users**: Users who want to plan trips without creating an account or storing data on remote servers.

---

## 5. Non-Negotiable System Constraints (Free-First Architecture)

- **No Paid Maps API**: Navigation is handed off to external standard Google Maps URLs (`https://www.google.com/maps/dir/?api=1&destination=lat,lng`), requiring zero Google Maps Platform API billing.
- **No Client-Side Nominatim Geocoding**: Keystroke search queries local PostgreSQL/SQLite database records with a 300ms RxJS debounce. Nominatim public servers are never queried by client devices.
- **No Live Overpass Queries**: OpenStreetMap data is imported and curated offline via `scripts/import_osm.py` and `scripts/seed_featured_places.py`.
- **Honest Cost Presentation**: Missing venue prices are rendered as `"Cost not provided"` rather than defaulting to `₱0.00`.
- **Gated Apple Sign-In**: Apple Developer Program membership costs US\$99/year. Until an active paid membership exists, Apple Sign-In is disabled and displays: *"Apple Sign-In is disabled in this pilot build"*.

