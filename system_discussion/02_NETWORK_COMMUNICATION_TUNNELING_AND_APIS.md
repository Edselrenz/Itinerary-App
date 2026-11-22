# Chapter 2: How the System Communicates — Tunneling, `ngrok`, Cloudflare Worker, REST APIs, and Offline Failover

This chapter explains **how information travels across the internet** between a traveler's device (Phone, Browser, or Windows PC) and our Backend Server and external Open-Data services. Every networking term—including **`localhost`**, **Port**, **NAT/Firewall**, **Tunneling**, **`ngrok`**, **Cloudflare Worker**, **CORS**, **REST API**, **OSRM**, and **Overpass**—is explained in both technical detail and plain English.

---

## 1. The Core Networking Challenge: Why Can't a Phone Reach `localhost` Directly?

### Technical Terms Explained

#### 1. **`localhost` (`127.0.0.1`) & Network Ports (`:8000`, `:4200`, `:5432`)**
- **Technical**: `127.0.0.1` (aliased as `localhost`) is the **IPv4 Loopback Address**—a virtual network interface inside an operating system that routes traffic strictly back to the same physical machine. A **Port** (an integer from `1` to `65535`) identifies a specific process on that machine:
  - Port `8000`: FastAPI Backend (`http://127.0.0.1:8000`)
  - Port `4200`: Angular Local Dev Server (`http://localhost:4200`)
  - Port `5432`: PostgreSQL 16 Database Container (`localhost:5432`)
- **In Plain English (Layman's Analogy)**: Think of your computer as an **Office Building**. `localhost` (`127.0.0.1`) means **"Inside This Building Only"** (like an internal intercom). The **Port Numbers** are **Room Extensions**: Room `8000` is the FastAPI Brain, Room `5432` is the PostgreSQL Database Vault, and Room `4200` is the Web Designer's room. If someone on a smartphone in another city dials *"Extension 8000"* on their own phone, they will only check Room 8000 inside *their own phone*—they won't reach your computer!

#### 2. **NAT (Network Address Translation), CGNAT, and Firewalls**
- **Technical**: Home and campus routers use **NAT** and **Stateful Firewalls** (and Philippine ISPs commonly use **CGNAT** — *Carrier-Grade NAT*), which block unsolicited inbound TCP connections from the public internet to your computer's private LAN IP (e.g., `192.168.1.x`). Furthermore, our live website on GitHub Pages runs over **HTTPS** (`https://edselrenz.github.io`), and modern web browsers enforce the **Mixed Content Policy**, blocking any HTTPS website from calling an unencrypted `http://` address.
- **In Plain English (Layman's Analogy)**: Your home Wi-Fi router has a **One-Way Security Gate (Firewall)**. Anyone *inside* your house can walk out to visit websites on the internet, but strangers on the outside internet cannot open your front door to talk to your computer. On top of that, secure HTTPS websites refuse to talk to any server that doesn't have an official **SSL/TLS Security Padlock (`https://`)**.

---

## 2. How We Solve It: Tunneling, `ngrok`, and the Cloudflare Worker Edge Proxy

To let any smartphone, any computer, and the public GitHub Pages website securely reach our local FastAPI backend + PostgreSQL database without paying monthly cloud server bills, we use a **2-Stage Hybrid Edge Architecture**: **`ngrok` (Tunneling)** + **Cloudflare Worker (Permanent Edge Gateway)**.

```
[ Any Phone / Web Browser / Desktop App ]
                   │
                   │  HTTPS Request to Permanent URL:
                   │  https://ne-itinerary-api.edselrenz0.workers.dev/api/v1/...
                   ▼
      ┌────────────────────────────────────────┐
      │   STAGE 1: CLOUDFLARE WORKER           │
      │   (cloudflare-worker/worker.js)        │
      │   • Permanent URL that never changes   │
      │   • Verifies CORS security permissions │
      │   • Injects ngrok bypass headers       │
      └────────────────────────────────────────┘
                   │
                   │  Forwards to active ngrok tunnel URL
                   │  (e.g., https://xxxx.ngrok-free.dev)
                   ▼
      ┌────────────────────────────────────────┐
      │   STAGE 2: NGROK SECURE TUNNEL         │
      │   • Encrypted outbound TLS tunnel      │
      │   • Punches safely through NAT/Router  │
      └────────────────────────────────────────┘
                   │
                   │  Delivers to Local Loopback Port 8000
                   ▼
      ┌────────────────────────────────────────┐
      │   LOCAL FASTAPI BACKEND SERVER         │
      │   (http://127.0.0.1:8000)              │
      └────────────────────────────────────────┘
```

### Every Component Explained (Technical + Layman)

#### 1. **What Is Tunneling?**
- **Technical**: **Network Tunneling** (specifically **Reverse TCP/HTTP Tunneling**) is a protocol technique where a machine behind a private NAT/firewall initiates an *outbound* persistent, encrypted TLS connection to a public relay server on the internet. Once that outbound pipe is open, external traffic arriving at the public relay server can travel *backwards* through that already-open pipe directly to the local server port (`127.0.0.1:8000`).
- **In Plain English (Layman's Analogy)**: Remember how your home Wi-Fi router blocks strangers from knocking on your front door from the outside, *but allows you to call out*? **Tunneling** is like your computer placing an outbound phone call to a public switchboard and **never hanging up the phone**. Whenever a user on the internet wants to ask your server a question, the public switchboard speaks into that already-open phone line, and your computer hears it immediately!

#### 2. **What Is `ngrok`?**
- **Technical**: **`ngrok`** is an industry-standard reverse-proxy and tunneling daemon launched by [`scripts/start_server.ps1`](file:///c:/Users/Edward/Desktop/CaseStudy/scripts/start_server.ps1). Running `ngrok http 8000` opens an encrypted TLS tunnel from our local machine's Port `8000` to `ngrok`'s global cloud edge and assigns a public HTTPS URL (such as `https://a1b2-c3d4.ngrok-free.dev`) complete with a valid SSL certificate.
  - *The Catch with Free `ngrok`*: On the free tier, `ngrok` generates a **new random URL** every time the server restarts, and shows an HTML warning page unless the request includes a special HTTP header: `ngrok-skip-browser-warning: true`.
- **In Plain English (Layman's Analogy)**: **`ngrok`** is the company that operates the underground tunnel from the public internet to our computer's Port 8000. It gives us a free secure `https://` address—**but** every time you restart your computer, `ngrok` gives the tunnel a brand-new temporary phone number! If we hardcoded that temporary phone number into our Android APK or Windows `.exe` installer, the app would break the next day when the number changed. That is why we placed **Cloudflare** in front of `ngrok`!

#### 3. **What Is Cloudflare & a Cloudflare Worker (`cloudflare-worker/worker.js`)?**
- **Technical**: **Cloudflare** is one of the world's largest global edge networks (Content Delivery Network, DNS, and serverless computing platform). A **Cloudflare Worker** ([`cloudflare-worker/worker.js`](file:///c:/Users/Edward/Desktop/CaseStudy/cloudflare-worker/worker.js)) is a lightweight serverless JavaScript function deployed across Cloudflare's global edge data centers at a **permanent, fixed HTTPS domain**:
  `https://ne-itinerary-api.edselrenz0.workers.dev`
  When any client (Web, Android, or Windows Desktop) calls `https://ne-itinerary-api.edselrenz0.workers.dev/api/v1/places`, our Cloudflare Worker:
  1. Checks if the request comes from an authorized origin (**CORS validation**).
  2. Reads its `NGROK_ORIGIN` environment variable (which points to the currently active `ngrok` tunnel URL).
  3. Automatically attaches `ngrok-skip-browser-warning: true` so `ngrok`'s interstitial warning screen is bypassed.
  4. Streams the request and response between the user and the FastAPI backend—and if the local computer is turned off, returns a clean JSON `503 Offline` payload (`"offline": true`) so the app gracefully switches to Offline Mode!
- **In Plain English (Layman's Analogy)**: Think of the **Cloudflare Worker** as a **Permanent Toll-Free Business Number (`1-800-TRIP-KO`) with a Smart Receptionist**.
  - Our Web App, Android APK, and Windows Desktop Installer all dial that one permanent number (`ne-itinerary-api.edselrenz0.workers.dev`). They **never** need to know `ngrok`'s temporary number!
  - Whenever we restart our local server and `ngrok` gives us a new temporary tunnel number, we simply tell the Cloudflare Receptionist the new forwarding number (updating `NGROK_ORIGIN` in Cloudflare), and every installed Android phone and Windows PC keeps working without ever needing an app update!

#### 4. **What Is CORS (Cross-Origin Resource Sharing)?**
- **Technical**: Web browsers enforce the **Same-Origin Policy** for security: a script loaded from Origin A (`https://edselrenz.github.io` or Capacitor's `https://localhost`) is forbidden from reading responses from Origin B (`https://ne-itinerary-api.edselrenz0.workers.dev` or `http://127.0.0.1:8000`) unless Origin B explicitly returns an `Access-Control-Allow-Origin` HTTP header matching Origin A. Before sending a `POST`, `PUT`, or `DELETE` request, the browser sends an automatic **`OPTIONS` Preflight Request** asking the server for permission. Both [`cloudflare-worker/worker.js`](file:///c:/Users/Edward/Desktop/CaseStudy/cloudflare-worker/worker.js) and [`backend/app/core/config.py`](file:///c:/Users/Edward/Desktop/CaseStudy/backend/app/core/config.py) explicitly allow `https://edselrenz.github.io`, `http://localhost:4200`, `http://localhost`, and `https://localhost` (Capacitor Android).
- **In Plain English (Layman's Analogy)**: **CORS** is like a **VIP Guest List at a Bank**. Even if a random website knows the URL of our backend server, the user's web browser acts like a security guard and asks our server first (*the `OPTIONS` preflight check*): *"Hey server, is this website on your approved VIP list?"* Our server checks the list (`ALLOWED_ORIGINS`) and replies: *"Yes, `edselrenz.github.io` and the Android App (`https://localhost`) are on the VIP list—let them through!"*

---

## 3. What Is an API & How Our Internal REST API Works (`/api/v1`)

### Technical & Layman Definitions

#### 1. **API (Application Programming Interface) & REST (Representational State Transfer)**
- **Technical**: An **API** is a formal contract defining how two software programs communicate. A **REST API** uses standard **HTTP URLs** to represent resources (like `/api/v1/places` or `/api/v1/itineraries`) and standard **HTTP Methods (Verbs)** to perform actions on them, exchanging data in **JSON** format.
- **In Plain English (Layman's Analogy)**: An **API** is a standardized **Order Counter** between the app on your screen and the server. Instead of speaking human sentences, the app sends short, structured order slips (**JSON**) to specific counter windows (**Endpoints**).

#### 2. **HTTP Methods (The 5 Action Verbs)**
| HTTP Method | Technical Meaning | Layman's Meaning | Example in Our App |
| :--- | :--- | :--- | :--- |
| **`GET`** | Read/retrieve data (idempotent, never changes server state). | *"Please show me this information."* | `GET /api/v1/places?category=nature_park` (Fetch nature parks) |
| **`POST`** | Create a new resource or trigger a computation. | *"Here is new data—please create or calculate this."* | `POST /api/v1/itineraries/generate` (Generate a suggested trip) |
| **`PUT`** | Replace an existing resource completely. | *"Replace my old saved trip with this updated version."* | `PUT /api/v1/itineraries/{id}` (Save full edited itinerary) |
| **`PATCH`** | Partially update specific fields of a resource. | *"Just update my phone number and profile photo."* | `PATCH /api/v1/auth/me` (Update user profile in Edit Profile) |
| **`DELETE`** | Permanently remove a resource. | *"Delete this saved trip."* | `DELETE /api/v1/itineraries/{id}` (Remove a trip) |

#### 3. **HTTP Status Codes (The Server's Quick Reply Codes)**
- **`200 OK` / `201 Created`**: *"Success! Here is your data / Your new account or trip was saved."*
- **`400 Bad Request` / `422 Unprocessable Content`**: *"Something on your form was filled out incorrectly (for example, end date is before start date)."*
- **`401 Unauthorized`**: *"You need to log in first, or your session keycard expired."*
- **`404 Not Found`**: *"That place or itinerary ID doesn't exist."*
- **`429 Too Many Requests`**: *"Whoa, slow down! You tried logging in more than 30 times in one minute (Rate Limit protection)."*
- **`503 Service Unavailable`**: *"The local server is currently turned off—switching to Offline Guest Mode!"*

### Complete Table of Internal `/api/v1` Endpoints ([`backend/app/api/v1/`](file:///c:/Users/Edward/Desktop/CaseStudy/backend/app/api/v1/))

| Endpoint Group | Route Path | What It Does |
| :--- | :--- | :--- |
| **Health Check** | `GET /api/v1/health` | Heartbeat check returning `{"status": "healthy", "province_scope": "Nueva Ecija"}`. Used by the apps to detect whether the backend is online or offline. |
| **Authentication** ([`auth.py`](file:///c:/Users/Edward/Desktop/CaseStudy/backend/app/api/v1/auth.py)) | `POST /api/v1/auth/register`<br>`POST /api/v1/auth/login`<br>`POST /api/v1/auth/refresh`<br>`GET / PATCH /api/v1/auth/me` | Registers new travelers (Argon2id hashing), signs them in (issuing JWT access + refresh tokens), rotates expired tokens, and reads/updates traveler profile details and Base64 avatars. |
| **Municipalities** ([`municipalities.py`](file:///c:/Users/Edward/Desktop/CaseStudy/backend/app/api/v1/municipalities.py)) | `GET /api/v1/municipalities` | Lists Nueva Ecija LGUs with center latitude/longitude coordinates and fuzzy text search. |
| **Places / POIs** ([`places.py`](file:///c:/Users/Edward/Desktop/CaseStudy/backend/app/api/v1/places.py)) | `GET /api/v1/places`<br>`GET /api/v1/places/{id}` | Searches the 2,673 verified Nueva Ecija places by map bounding box (`min_lat`, `max_lat`, `min_lng`, `max_lng`), municipality, category list, price tier, or keyword search. |
| **Itineraries** ([`itineraries.py`](file:///c:/Users/Edward/Desktop/CaseStudy/backend/app/api/v1/itineraries.py)) | `POST /api/v1/itineraries/generate`<br>`GET / POST /api/v1/itineraries`<br>`GET / PUT / DELETE /api/v1/itineraries/{id}` | Runs the deterministic Suggested Itinerary Generator and performs full CRUD (Create, Read, Update, Delete) on saved suggested and custom itineraries. |

---

## 4. External Open-Data APIs Used (100% Free-First Architecture)

How does our app show rich maps, calculate real road driving routes, and know about 2,673 places in Nueva Ecija **without paying a single centavo to Google Maps Platform**?

| External Service / API | How We Use It (Technical) | In Plain English (Layman's Explanation) |
| :--- | :--- | :--- |
| **1. OpenStreetMap (OSM) Raster Tile Servers** (`tile.openstreetmap.org` & France/HOT mirrors) | Both Leaflet (Web/Android) and `SlippyMapCanvas` (Windows Desktop) fetch `256×256` PNG map tiles by zoom level and tile coordinates (`/{z}/{x}/{y}.png`) and cache them to disk (`tiles_cache/`). | **OpenStreetMap** is the *"Wikipedia of World Maps"*. Instead of downloading one massive map image, the app downloads small square puzzle pieces (**tiles**) for the exact town you are looking at and saves them on your device so they load instantly next time. |
| **2. OSRM (Open Source Routing Machine)** (`router.project-osrm.org/route/v1/`) | Given a sequence of stop coordinates `(lng, lat)`, queries OSRM's routing engine (with a strict 2.5s timeout) to retrieve exact road distance (meters), travel time (seconds), and an **Encoded Polyline** string following real provincial highways. If offline, falls back to our local **Geodesic Spline** curve generator. | **OSRM** is a free, open-source GPS navigator. When you schedule 4 stops in a day, we ask OSRM: *"Which actual roads connect Stop 1 -> Stop 2 -> Stop 3 -> Stop 4, and how many minutes does it take?"* OSRM sends back the exact blue road line to draw on the map. |
| **3. Overpass API** (`overpass-api.de/api/interpreter`) | Queried **offline at build/seed time** via [`scripts/fetch_osm_places.py`](file:///c:/Users/Edward/Desktop/CaseStudy/scripts/fetch_osm_places.py) and imported via [`scripts/import_osm.py`](file:///c:/Users/Edward/Desktop/CaseStudy/scripts/import_osm.py) to harvest 2,656 real Nueva Ecija cafes, restaurants, resorts, churches, terminals, hospitals, and parks into our local database and `osm_places.json`. | **Overpass** is OpenStreetMap's bulk search engine. Rather than making users wait for slow internet searches while traveling, we used Overpass ahead of time to download **all 2,656 real places in Nueva Ecija** directly into our database and app bundle! |
| **4. Google Maps Standard URL Deep-Links** (`https://www.google.com/maps/dir/?api=1&...`) | Constructs a standard RFC-3986 URL containing `origin`, `destination`, `waypoints`, and `travelmode` and opens it in the user's native Google Maps app or browser tab. | Instead of paying Google thousands of dollars for an embedded voice-navigation SDK, clicking **"Open in Google Maps"** hands your exact stop coordinates directly to the free Google Maps app already installed on your phone or browser! |

---

## 5. Heartbeat Health Probing & Automatic Offline Failover

What happens when a user opens the app while the backend server or internet connection is down?

1. **Dynamic Host Probing (`ConnectivityService`)**:
   - Both the Web/Android app ([`connectivity.service.ts`](file:///c:/Users/Edward/Desktop/CaseStudy/Project/src/app/core/services/connectivity.service.ts)) and the Windows Desktop app ([`connectivity_service.py`](file:///c:/Users/Edward/Desktop/CaseStudy/desktop_client/core/connectivity_service.py)) send a lightweight background check (`GET /api/v1/health`) with a **2.5-second connection timeout**.
   - It automatically checks if a local backend (`http://127.0.0.1:8000/api/v1`) is running on the same machine, and if not, uses the Cloudflare Worker edge URL (`https://ne-itinerary-api.edselrenz0.workers.dev/api/v1`).
2. **Consecutive Failure Guard ($\ge 2$ Failures)**:
   - To prevent a single brief Wi-Fi hiccup from flashing an error banner, the app only transitions into **Offline Mode** after **2 consecutive failed health checks** (or when an API call times out).
3. **Zero-Crash Local Failover**:
   - When offline, `PlaceService` immediately serves the **2,673 bundled Nueva Ecija places** from memory/local JSON, and `ItineraryService` runs its **client-side Haversine + 2-Opt itinerary generator** and saves trips to local device storage (`IndexedDB` or `guest_storage.json`).

---

👉 **Continue to Chapter 3**: [03_DATABASE_ARCHITECTURE_AND_COMPONENTS.md](file:///c:/Users/Edward/Desktop/CaseStudy/system_discussion/03_DATABASE_ARCHITECTURE_AND_COMPONENTS.md)
