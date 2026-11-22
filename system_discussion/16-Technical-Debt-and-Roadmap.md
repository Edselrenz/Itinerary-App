# 16 — Technical Debt, Limitations, and Improvement Roadmap

This architectural review catalogs **recently resolved Phase 61–62 (`v1.0.0`) engineering remediations** alongside **remaining verified technical debt, security gaps, incomplete features, and maintainability improvements**, prioritized into `CRITICAL`, `HIGH`, `MEDIUM`, and `LOW` tiers.

---

## 0. Resolved Engineering & Parity Items (Completed in Phases 61–62 `v1.0.0`)

Before reviewing remaining technical debt, the following issues from earlier reviews have been **resolved and verified by automated tests**:
- **[RESOLVED — `PKG-REV-01` / `TC-35`] Frozen PyInstaller Asset Path & Read-Only `%LOCALAPPDATA%` Fallback**: `desktop_client/components/slippy_map_canvas.py` now resolves `_ASSETS_DIR = get_settings().assets_dir` (which supports `sys._MEIPASS`) and probes `_resolve_writable_tile_cache_dir()` with `.write_probe`, falling back to `%LOCALAPPDATA%\NuevaEcijaTravel\storage` when installed in a read-only folder.
- **[RESOLVED — `PKG-REV-02` / `TC-36`] Desktop In-App Navigation Parity**: `desktop_client/views/trip_detail_view.py` (`_launch_in_app_nav`) and `places_view.py` now launch turn-by-turn itinerary routes directly inside the in-app `SlippyMapCanvas` rather than opening an external browser tab.
- **[RESOLVED — `PKG-REV-03` & PyInstaller Hot-Swap Staging]**: `scripts/build_standalone_exe.py` now calls `flet_desktop.ensure_client_cached()`, stages builds in `build_temp/dist_stage/NuevaEcijaTravel` (bundling `flet/controls/material/icons.json`, `cupertino_icons.json`, `certifi`, `tzdata`), and overlays `dist/NuevaEcijaTravel` with an NTFS `.old` rename fallback so running instances never trigger `FileNotFoundError: icons.json`.
- **[RESOLVED — `PKG-REV-04` & `TC-37`–`TC-40`] Desktop-Web UI & Theme Parity**: Fixed dark-mode tokens in `places_view.py`, centered full-width `Edit Profile` inputs (`TC-37`), eliminated horizontal modal overflow in `Off-Grid Custom Venue` and `Edit Stop` dialogs (`TC-38`), fixed full-screen `SplashOverlay` (`Positioned.fill`, `TC-39`), and updated `WelcomeView` / `GuestView` / `LoginView` / `SignupView` to match the Web App's boxless layout with the seamless 3-tile mirrored cityscape `welcome_hero_buildings_wide.png` (`1848 × 336`, `TC-40`).

---

## CRITICAL Priority (Address Immediately Before Public Cloud Hosting)

### 1. Hardcoded Fallback Admin Sync Secret Committed in Source Control
- **Current Condition**: `scripts/run_daemon.py` (line 77) contains a hardcoded default fallback string for `ADMIN_SYNC_KEY`, and `cloudflare-worker/wrangler.toml` (line 16) commits a default dev value.
- **Why It Is a Problem**: Exposes the tunnel-sync authentication key in a public repository, risking unauthorized traffic redirection via `POST /__sync_tunnel`.
- **Recommended Solution**: Remove all hardcoded fallback keys (raise an error if `WORKER_SYNC_KEY` is unset), remove `[vars] ADMIN_SYNC_KEY` from `wrangler.toml`, and immediately rotate the secret via `npx wrangler secret put ADMIN_SYNC_KEY`.
- **Affected Files**: `scripts/run_daemon.py`, `cloudflare-worker/wrangler.toml`.
- **Expected Benefit**: Eliminates credential leakage and prevents proxy hijacking.

### 2. Startup Auto-Migration Overwrites Blank User Profile Fields with Hardcoded Sample PII
- **Current Condition**: `ensure_user_profile_columns()` in `backend/app/core/database.py` executes an unconditional `UPDATE users SET ...` on every server boot, backfilling `NULL`/empty columns with hardcoded sample values (`'May 23, 2000'`, `'Female'`, `'+66 81 234 5678'`, `'assets/images/pattranite_avatar.jpg'`).
- **Why It Is a Problem**: Corrupts real newly registered user accounts with fabricated personal data on every backend restart.
- **Recommended Solution**: Remove the `UPDATE users` backfill statement immediately; keep optional profile columns `NULL` until the user explicitly fills them in, and rely on Alembic migrations (`0004`) rather than import-time DDL.
- **Affected Files**: `backend/app/core/database.py`.
- **Expected Benefit**: Preserves user data integrity and privacy.

---

## HIGH Priority (Address Before Public Production or Expansion)

### 3. Attribute Bug in `compute_and_save_day_route()` (`day.updated_at`)
- **Current Condition**: `backend/app/api/v1/itineraries.py` sets `day.updated_at = datetime.now(timezone.utc)` inside `compute_and_save_day_route()`, but the `ItineraryDay` ORM model (`backend/app/models/entities.py`) has **no `updated_at` column**.
- **Why It Is a Problem**: Silently sets a non-persisted Python attribute on the ORM instance (misleading maintainers and risking strict-attribute errors in future SQLAlchemy versions).
- **Recommended Solution**: Either remove `day.updated_at = ...` (relying on `itinerary.updated_at`) or add an `updated_at` column to `itinerary_days` via a new Alembic migration.
- **Affected Files**: `backend/app/api/v1/itineraries.py`, `backend/app/models/entities.py`.

### 4. Password Recovery Flow Is UI-Simulated Without Backend Support
- **Current Condition**: `LoginPage.submitRecoveryRequest()` (`Project/`) and `LoginView._send_recovery()` (`desktop_client/`) simulate success locally via timers; no `/api/v1/auth/forgot-password` or email delivery service exists.
- **Why It Is a Problem**: Locked-out users receive a false confirmation message and can never actually recover their accounts.
- **Recommended Solution**: Implement time-limited, single-use hashed password-reset tokens in the database + transactional email dispatch (e.g., Resend/SendGrid/SMTP), or clearly label the modal as contacting support until implemented.
- **Affected Files**: `Project/src/app/features/auth/login/login.page.ts`, `desktop_client/views/login_view.py`, `backend/app/api/v1/auth.py`.

### 5. `docker-compose.prod.yml` Default Passwords & Exposed PostgreSQL Port
- **Current Condition**: `docker-compose.prod.yml` exposes `5432:5432` on all host interfaces and provides weak fallback defaults (`change_me_local_only`).
- **Why It Is a Problem**: Risks exposing the production database port externally and starting with weak credentials.
- **Recommended Solution**: Remove the `ports: ["5432:5432"]` host mapping in production (keep Postgres internal to the Docker network) and use required syntax (`${POSTGRES_PASSWORD:?required}`).
- **Affected Files**: `docker-compose.prod.yml`.

### 6. No JWT Revocation / Token Invalidation on Logout or Password Change
- **Current Condition**: Logout only clears client storage; changing a password does not invalidate previously issued refresh tokens (`7-day` TTL).
- **Recommended Solution**: Add a `token_version` integer column on `users` checked inside `decode_jwt_token()` / `get_current_user()` and incremented on password change or explicit logout-all.
- **Affected Files**: `backend/app/models/entities.py`, `backend/app/services/auth_service.py`.

### 7. Input Hardening on Photo Proxy & Avatar Uploads
- **Current Condition**: `/api/v1/places/photos/{photo_name:path}` interpolates `photo_name` directly into the Google Places URL without strict format validation; `UserUpdateIn.avatar_url` has no size cap or MIME validation.
- **Recommended Solution**: Validate `photo_name` against `^places/[A-Za-z0-9_-]+/photos/[A-Za-z0-9_-]+$`; cap `avatar_url` length and restrict schemes to `https://`, `assets/`, or `data:image/(png|jpeg|webp);base64,`.
- **Affected Files**: `backend/app/api/v1/places.py`, `backend/app/schemas/auth.py`.

---

## MEDIUM Priority (Maintainability, Reliability & Parity)

### 8. Duplicate Code & Oversized Monolithic View/Service Files
- **Current Condition**:
  - `backend/app/core/database.py` and `backend/app/core/limiter.py` contain duplicated module docstrings and duplicate imports at the top of the file.
  - Several UI/service files exceed 1,000 lines: `places_view.py` (1,975 lines), `custom_builder_view.py` (1,845), `custom-builder.page.ts` (1,692), `slippy_map_canvas.py` (1,618), `map.page.ts` (1,563), `itinerary.service.ts` (1,351), `itinerary-detail.page.ts` (1,227).
- **Recommended Solution**: Clean up duplicate headers in `database.py`/`limiter.py` and decompose large pages/views into focused sub-components (filter panel, day editor, budget calculator, route HUD).
- **Expected Benefit**: Faster onboarding, easier unit testing, and fewer regression bugs.

### 9. Local-Only Favorites & Unfinished OAuth UI Integration
- **Current Condition**: Favorites are stored only in `localStorage` / `favorites.json` (lost when switching devices); Google OAuth is implemented on the backend (`POST /api/v1/auth/oauth/google`) but disabled in Web/Desktop UI.
- **Recommended Solution**: Add `user_favorites` table + sync endpoints; wire Google Sign-In SDK on Web/Android when a production `GOOGLE_OAUTH_CLIENT_ID` is provisioned.

### 10. CI Pipeline Gaps (PostgreSQL Integration, Desktop Tests & Playwright E2E)
- **Current Condition**: `.github/workflows/deploy.yml` runs backend Pytest against SQLite only; `desktop_client/tests/` (119 tests) and `Project/e2e/app.spec.ts` are not run in CI.
- **Recommended Solution**: Add a PostgreSQL 16 service container job for Alembic + Pytest, run `desktop_client/tests/` before PyInstaller builds in `release-builds.yml`, and add a scheduled/PR Playwright job.

### 11. Unbounded `geospatial_cache` Growth & Missing Structured Logging
- **Current Condition**: Expired rows in `geospatial_cache` are never purged automatically; backend lacks structured JSON logs and request IDs.
- **Recommended Solution**: Add a periodic cleanup task or CLI command (`DELETE FROM geospatial_cache WHERE expires_at < NOW()`) and adopt structured JSON logging for production diagnostics.

### 11b. ORM-vs-Alembic Index Drift (`ix_places_lat_lng_active`)
- **Current Condition**: `Place.__table_args__` in `backend/app/models/entities.py` declares `Index("ix_places_lat_lng_active", "latitude", "longitude", "is_active")`, which is created on SQLite via `Base.metadata.create_all`, but is missing from Alembic migrations `0001`–`0004`.
- **Why It Is a Problem**: PostgreSQL databases initialized via `alembic upgrade head` do not receive this composite bounding-box index, creating schema parity drift between SQLite and PostgreSQL.
- **Recommended Solution**: Generate a new Alembic migration (`0005`) adding `ix_places_lat_lng_active` on `places (latitude, longitude, is_active)`.
- **Affected Files**: `backend/app/models/entities.py`, `backend/alembic/versions/`.

---

## LOW Priority (Repository Hygiene & Nice-to-Have)

### 12. Repository Clutter (Committed Build Artifacts & Duplicate Historical Docs)
- **Current Condition**: `build/NuevaEcijaTravel/` (PyInstaller intermediate `.toc`/`.pkg`/`.pyz` files) is tracked in Git, along with legacy root-level QA PDFs/plans.
- **Recommended Solution**: Add `build/` and `build_temp/` to `.gitignore`, remove committed PyInstaller intermediates from Git tracking (`git rm -r --cached build/`), and archive historical QA PDFs/plans outside the repository root.
- **Expected Benefit**: Dramatically reduces repository clone size and prevents developer confusion.

### 13. Complete Missing Frontend Unit Specs & Desktop OS Keyring Storage
- **Current Condition**: `guest.page.ts` and `guest-storage.service.ts` lack `.spec.ts` files; `desktop_client/core/session.py` stores JWTs in plaintext `session.json`.
- **Recommended Solution**: Add unit specs for Guest onboarding/storage and migrate desktop token storage to Windows Credential Manager via `keyring`.

---

## Technical Terms & Concepts Explained (How It Works & What It Is Used For in This System)

| Technical Term | How It Works (Technical & Layman Explanation) | What It Is Used For in This System |
|---|---|---|
| **Technical Debt** | **Layman**: Just like financial debt, taking a quick shortcut during software development (like hardcoding a test value or putting 1,900 lines of code in one file) gets a feature working faster today, but adds "interest" (extra maintenance work) that should be paid down before scaling up.<br>**Technical**: Architectural, security, or code-structure trade-offs accumulated during rapid prototyping or pilot phases that require refactoring for long-term production maintainability. | Tracked transparently in this chapter across `CRITICAL`, `HIGH`, `MEDIUM`, and `LOW` tiers so maintainers know exactly what is production-hardened vs. what is pilot-scoped. |
| **Schema Drift (ORM vs. Migrations)** | **Layman**: When the Python blueprint of the database tables (`entities.py`) has a slightly different detail (like an extra search index) compared to the numbered upgrade steps (`alembic/versions/`), causing SQLite and PostgreSQL to end up slightly out of sync.<br>**Technical**: Divergence between declarative SQLAlchemy `Base.metadata` definitions and the cumulative DDL emitted by `alembic upgrade head`. | Identified in Item `11b` (`ix_places_lat_lng_active` present in `Place.__table_args__` on SQLite but not yet added in an Alembic `0005` migration for PostgreSQL). |
| **Token Version Revocation (`token_version`)** | **Layman**: Because JWT login passes don't check a session table by default, how do you cancel an old 7-day pass if a user changes their password? By storing a "badge edition number" (`token_version = 1`) on the user's profile and incrementing it to `2` when they change their password so any old `edition 1` passes are rejected immediately.<br>**Technical**: Embedding an integer `ver` claim inside the signed JWT payload and comparing it against `current_user.token_version` inside `get_current_user()` and `refresh_tokens()`. | Recommended in Item `6` to add instant server-side token revocation on password change or "Log Out of All Devices." |
| **Windows DPAPI / OS Keyring (`keyring`)** | **Layman**: A built-in Windows security service (**Data Protection API**) that encrypts saved passwords and login tokens using your personal Windows user account key so nobody else copying your files can read your saved session.<br>**Technical**: The Win32 `CryptProtectData` API / Windows Credential Locker accessed in Python via the `keyring` library, providing OS-level encryption equivalent to Android's native `KeyStore`. | Recommended in Item `13` to upgrade desktop JWT storage from plaintext `storage/session.json` to encrypted Windows Credential Manager storage. |
| **Content Security Policy (CSP)** | **Layman**: A browser security rule sheet sent with a webpage that tells the browser: "Only run JavaScript code and load images that come from our own trusted servers; block any injected third-party scripts."<br>**Technical**: An HTTP response header or `<meta http-equiv="Content-Security-Policy">` tag restricting `default-src`, `script-src`, `connect-src`, and `img-src` origins to mitigate Cross-Site Scripting (XSS) token theft. | Recommended in [09 — Authentication and Security](./09-Authentication-and-Security.md) to harden Web `localStorage` JWT persistence on GitHub Pages. |
