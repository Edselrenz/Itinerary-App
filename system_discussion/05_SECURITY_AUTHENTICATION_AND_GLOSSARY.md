# Chapter 5: Security, Authentication & Complete A–Z Technical-to-Layman Glossary

This chapter explains **how the system protects traveler accounts, passwords, API endpoints, and provincial data integrity**, followed by a **Master A–Z Quick-Reference Glossary** of every technical term used across the project.

---

## 1. Security & Authentication Architecture (Technical + Layman)

### 1. **Password Hashing with Argon2id (`pwdlib[argon2]`)**
- **Technical**: When a user registers or updates their password in [`backend/app/core/security.py`](file:///c:/Users/Edward/Desktop/CaseStudy/backend/app/core/security.py), the plaintext password is never stored in the database. Instead, it is passed through **Argon2id** (winner of the Password Hashing Competition and recommended by OWASP), which combines a unique cryptographically random **Salt** with memory-hard and CPU-hard hashing iterations to produce a one-way hash string (`$argon2id$v=19$m=65536,t=3,p=4$...`) stored in `auth_identities.password_hash`.
- **In Plain English (Layman's Analogy)**: Storing plain passwords in a database is like writing everyone's house key combination on a sticky note—if a burglar ever peeks inside the database, every account is compromised.
  - **Hashing** is like a **One-Way Food Blender**: it is easy to blend strawberries and bananas into a smoothie (turn your password into an Argon2id hash), but it is mathematically impossible to "un-blend" the smoothie back into whole strawberries (reverse the hash back into your password).
  - **Salting** means adding a unique pinch of secret spice to every user's smoothie before blending, so even if two users pick the exact same password, their hashes in the database look completely different.
  - **Argon2id (Memory-Hard)** intentionally forces the computer to use a specific chunk of RAM for a fraction of a second during login—imperceptible to a real human logging in once, but crippling to a hacker trying to guess 10 million passwords per second on a graphics card!

### 2. **JWT (JSON Web Tokens) — Access Tokens vs. Refresh Token Rotation**
- **Technical**: Upon successful login (`POST /api/v1/auth/login`), the server issues two signed **JWTs** (`HS256` HMAC-SHA256 signed with `JWT_SECRET_KEY`):
  1. **Short-Lived Access Token** (valid for e.g. 30 minutes): Attached by the client in the HTTP header `Authorization: Bearer <access_token>` on authenticated API requests.
  2. **Longer-Lived Refresh Token** (valid for e.g. 7 days): Used exclusively to call `POST /api/v1/auth/refresh` when the Access Token expires. Our Angular HTTP Interceptor ([`auth.interceptor.ts`](file:///c:/Users/Edward/Desktop/CaseStudy/Project/src/app/core/interceptors/auth.interceptor.ts)) and Desktop API Client ([`api_client.py`](file:///c:/Users/Edward/Desktop/CaseStudy/desktop_client/core/api_client.py)) automatically catch `401 Unauthorized` responses, silently exchange the Refresh Token for a fresh pair of tokens (**Token Rotation**), and retry the original request without interrupting the user!
- **In Plain English (Layman's Analogy)**: Think of **JWTs** like a **Luxury Hotel Check-In**:
  - When you check in at the front desk with your ID and password (`Login`), the receptionist doesn't make you show your passport every time you open your bedroom door. Instead, they hand you a **Plastic Magnetic Room Keycard (the Access Token)**.
  - For safety, that plastic keycard automatically expires after 30 minutes so if you drop it in the hallway, a stranger can't use it tomorrow.
  - When the 30 minutes are up, your app silently shows your **Check-In Receipt (the Refresh Token)** to the front desk in the background and gets a fresh 30-minute keycard automatically—so you stay logged in seamlessly!

### 3. **API Rate Limiting (`SlowAPI` — 30 Requests/Minute)**
- **Technical**: In [`backend/app/api/v1/auth.py`](file:///c:/Users/Edward/Desktop/CaseStudy/backend/app/api/v1/auth.py), authentication endpoints are decorated with **SlowAPI** rate limiters (`@limiter.limit("30/minute")`) keyed by client IP address. Exceeding 30 requests within a 60-second window returns HTTP `429 Too Many Requests`.
- **In Plain English (Layman's Analogy)**: **Rate Limiting** is a **Turnstile at the Front Door**. A real human traveler will never click the *"Log In"* button more than 30 times in a single minute, so they walk right through. Automated hacker bots trying to brute-force thousands of passwords get stopped cold at attempt #31 with a *"429 Too Many Requests"* block.

### 4. **Provincial Geofencing & Honest Pricing Guards**
- **Technical**:
  - **Geofence Guard**: Any place or custom off-grid stop with GPS coordinates is validated against Nueva Ecija's geographic bounding box (`15.15 <= latitude <= 16.15`, `120.70 <= longitude <= 121.40`). Out-of-bounds coordinates are rejected at both the client form and backend schema/importer boundaries.
  - **Honest Pricing Guard**: Cost fields require `0 <= estimated_cost_min <= estimated_cost_max`. Missing pricing in OpenStreetMap records is stored as `NULL` and displayed as `"Cost not provided"` (never fake `₱0.00`).
- **In Plain English (Layman's Analogy)**:
  - **Geofencing** is an **Invisible Digital Fence** around the borders of Nueva Ecija. If someone tries to enter GPS coordinates located in Manila or Cebu—or accidentally swaps latitude and longitude—the system catches it immediately and explains that the coordinates are outside Nueva Ecija.

---

## 2. Master A–Z Technical-to-Layman Glossary (42 Core Terms)

Use this quick-reference dictionary during presentations, code reviews, or thesis/capstone defenses:

| Term | Technical Definition | Layman's Explanation (In Plain English) |
| :--- | :--- | :--- |
| **1. ACID Transaction** | Atomic, Consistent, Isolated, and Durable database write operation. | An "all-or-nothing" database save—either the entire multi-day trip saves 100% intact, or nothing is saved, preventing half-broken data. |
| **2. Alembic** | Python database schema migration tool for SQLAlchemy (`backend/alembic/`). | "Git version control for database tables"—safely upgrades live database tables without deleting existing user data. |
| **3. Angular 22** | TypeScript-based enterprise web application framework by Google (`Project/`). | The structural steel frame and routing brain of our Web and Android applications. |
| **4. API (Application Programming Interface)** | Formal communication contract and endpoints (`/api/v1/...`) between software components. | The standardized order counter where the app sends requests and the server sends back data. |
| **5. APK (Android Package Kit)** | Compiled archive format (`.apk`) used by Android to distribute and install mobile apps. | The single installable app file (`TripMoTripKo-release.apk`) that you tap on an Android phone to install the app. |
| **6. Argon2id** | Memory-hard, salted cryptographic password hashing algorithm (`pwdlib[argon2]`). | A one-way cryptographic "blender" that scrambles passwords so even database administrators cannot read them. |
| **7. ASGI (Asynchronous Server Gateway Interface)** | Standard interface between async Python web servers (Uvicorn) and frameworks (FastAPI). | A multi-lane highway that lets our Python server handle many travelers at the same time without waiting in a single-file line. |
| **8. Base64 Data URI** | Binary-to-text encoding scheme (`data:image/jpeg;base64,...`) used for profile avatars. | A way of turning a profile photo into a text string so it can be saved directly inside a JSON message or database column. |
| **9. Bounding Box (`BBox`)** | Rectangular geographic boundary defined by `(min_lat, min_lng, max_lat, max_lng)`. | A rectangular coordinate fence drawn around Nueva Ecija (`15.15°–16.15° N, 120.70°–121.40° E`) or the currently visible map screen. |
| **10. Capacitor 8** | Cross-platform native runtime wrapping web apps into native Android/iOS packages. | The bridge that packages our Angular/Ionic web app into a real Android APK and connects it to the phone's GPS and hardware back button. |
| **11. Cloudflare Worker** | Serverless JavaScript function running on Cloudflare's global edge network (`worker.js`). | Our permanent public "Front Receptionist" URL (`ne-itinerary-api.edselrenz0.workers.dev`) that forwards traffic into our active `ngrok` tunnel. |
| **12. CORS (Cross-Origin Resource Sharing)** | Browser security mechanism using HTTP headers to control cross-domain API access. | A VIP guest list check where the server tells the browser which websites/apps are allowed to talk to our API. |
| **13. Debounce (300 ms)** | RxJS/event technique delaying execution until a user stops typing for 300 milliseconds. | Waiting a third of a second after you finish typing *"Bongabon"* before searching, instead of firing 8 separate searches for *"B"*, *"Bo"*, *"Bon"*... |
| **14. Docker Container** | Lightweight, isolated OS-level virtualization instance running `postgres:16-alpine`. | A sealed, ready-to-run digital shipping container that runs our PostgreSQL 16 database identically on any computer. |
| **15. Encoded Polyline** | Lossy ASCII compression format representing a sequence of `(lat, lng)` road coordinates. | A compact text shorthand that squeezes hundreds of road bends and turns into a single line of characters. |
| **16. FastAPI** | High-performance asynchronous Python web framework used to build `/api/v1`. | The Python "brain" of our backend server that processes logins, place searches, and itinerary calculations. |
| **17. Flet 1.1.2** | Python UI framework powered by the Google Flutter Desktop rendering engine. | The technology that lets us write our Windows Desktop application in Python while rendering smooth 60 FPS graphics via Flutter. |
| **18. Foreign Key (`FK`)** | Column in one table referencing the Primary Key of another table. | A digital "luggage tag" on a child record (like *Day 1*) that links it to its parent record (the *Trip*). |
| **19. Geodesic Spline** | Smooth mathematical curve interpolated between geographic coordinates on a sphere. | A smooth, curved route line drawn between stops on the map when the user is offline and road servers are unreachable. |
| **20. Gradle 8.13** | Automated build and dependency management system for Android (`Project/android/`). | The factory assembly line that compiles Java code and web assets into an Android `.apk`. |
| **21. Haversine Formula** | Trigonometric equation calculating great-circle distance between two points on a sphere. | A curved-Earth tape measure that calculates the exact kilometer distance between any two GPS pins. |
| **22. IndexedDB** | Transactional browser database used by `@ionic/storage-angular` for offline storage. | A private filing cabinet inside the web browser and Android app that saves Guest Mode itineraries offline. |
| **23. Inno Setup 6** | Script-driven installation builder for Windows (`installer/NuevaEcijaTravel.iss`). | The tool that compresses our desktop app into the standard Windows `NuevaEcijaTravel_Setup_v1.0.0.exe` installation wizard. |
| **24. Ionic Framework 9** | Mobile-first UI component toolkit built on Web Components and Angular. | The polished buttons, tabs, modals, and mobile touch gestures used in our Web and Android interfaces. |
| **25. JSON / `JSONB`** | JavaScript Object Notation (text) and PostgreSQL Binary JSON storage format. | A clean, universal text format (`{"name": "Minalungao", "cost": 100}`) used by apps and databases to exchange structured lists and objects. |
| **26. JWT (JSON Web Token)** | Cryptographically signed token (`Header.Payload.Signature`) used for stateless auth. | A digital hotel keycard issued after login that proves who you are on every API request without re-sending your password. |
| **27. Keystore (`.jks`)** | Encrypted file containing private RSA cryptographic keys for signing Android APKs. | The digital notary stamp used to sign `TripMoTripKo-release.apk` so Android trusts the package. |
| **28. Leaflet 1.9.4** | Open-source JavaScript library for mobile-friendly interactive maps. | The map viewer engine inside the Web and Android apps that displays OpenStreetMap tiles, pins, and road routes. |
| **29. `localhost` (`127.0.0.1`)** | Standard loopback IP address referring strictly to the local computer itself. | A computer's internal intercom address meaning *"this machine right here"*. |
| **30. Marker Clustering** | Spatial grouping of proximate map pins into numbered summary circles at low zoom levels. | Bundling overlapping pins into a single numbered badge when zoomed out so the map stays clean and readable. |
| **31. `ngrok`** | Reverse-proxy tunneling tool exposing local ports to the public internet over HTTPS. | The secure underground tunnel that connects the public internet (and Cloudflare) directly to Port 8000 on our local server. |
| **32. ORM (Object-Relational Mapper)** | Library (SQLAlchemy) mapping database tables to code classes and objects. | A bilingual translator that converts Python objects into SQL database commands automatically and safely. |
| **33. OSRM (Open Source Routing Machine)** | High-performance open-source C++ routing engine for OpenStreetMap road networks. | The free GPS routing service we query to get real driving distances, durations, and highway lines between stops. |
| **34. Overpass API** | Read-only query API for extracting custom geographic data from OpenStreetMap. | The bulk map search engine we used offline to harvest 2,656 real Nueva Ecija venues into our catalog. |
| **35. PostgreSQL 16** | Enterprise open-source client-server relational database system (`ne_postgres`). | Our primary heavy-duty database server running in Docker that stores users, places, and itineraries. |
| **36. Primary Key (`PK`)** | Unique identifier column (`id`) for every row in a database table. | A record's unique Passport Number (`UUID`) ensuring no two rows in a table can ever be confused. |
| **37. PWA (Progressive Web App)** | Web application enhanced with offline storage and home-screen installability. | A website that can be saved to your phone or desktop home screen and used like an installed app, even offline. |
| **38. Pydantic v2** | Python data validation library using type annotations (`backend/app/schemas/`). | The strict security bouncer at the door of our API that checks every incoming form field before letting it touch the database. |
| **39. PyInstaller** | Tool that bundles a Python application and all its dependencies into a standalone `.exe`. | The packager that bundles Python 3.14, Flet, and all our app files into `NuevaEcijaTravel.exe` so users don't have to install Python. |
| **40. Slippy Map (`SlippyMapCanvas`)** | Interactive tile-based map supporting continuous drag-panning and cursor zooming. | Our custom pure-Python/Flet map engine on Windows Desktop that lets you drag and zoom across Nueva Ecija smoothly at 60 FPS. |
| **41. SQLite 3** | Self-contained, serverless, zero-configuration SQL database engine (`nueva_ecija_travel.db`). | Our single-file local database lockbox that automatically takes over whenever Docker PostgreSQL is not running. |
| **42. Tunneling** | Encapsulating and forwarding private network traffic through an outbound encrypted pipe. | Keeping an outbound phone line open from a private computer to a public relay so outside devices can talk back through the open line. |

---

👉 **Return to Master Index**: [README.md](file:///c:/Users/Edward/Desktop/CaseStudy/system_discussion/README.md)
