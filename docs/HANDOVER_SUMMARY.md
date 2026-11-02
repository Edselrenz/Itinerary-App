# Context Reset Handover Summary

**Application**: Nueva Ecija Travel Itinerary (MVP)  
**Date**: October 31, 2026  
**Repository Branch**: `main` (clean working tree, pushed to `origin/main` at commit `1839ecf`)  
**Target Milestone**: Phase 11 — Priority 1: Critical Security & Data-Loss Fixes

---

## 1. Active Task & Immediate Goal

### Current State
- The 24-Point MVP Acceptance Gate ([scripts/verify_acceptance_gate.py](file:///c:/Users/Edward/Desktop/CaseStudy/scripts/verify_acceptance_gate.py)) is **100% verified** (24/24 checks passed).
- All unit and integration test suites are green: **98/98 frontend Vitest tests** across 16 files, and **6/6 backend Pytest suites**.
- An independent comprehensive code review ([nueva_ecija_itinerary_app_code_review.md](file:///c:/Users/Edward/Desktop/CaseStudy/nueva_ecija_itinerary_app_code_review.md)) was completed, finding 16 issues (`CR-001` through `CR-016`) across 4 priority tiers.
- All 16 findings were documented in [docs/CODE_REVIEW_AUDIT.md](file:///c:/Users/Edward/Desktop/CaseStudy/docs/CODE_REVIEW_AUDIT.md) and appended as Phases 11–14 in [docs/TODO.md](file:///c:/Users/Edward/Desktop/CaseStudy/docs/TODO.md).

### Immediate Goal (Next Active Step)
Execute **Phase 11: Priority 1 — Critical Security & Data-Loss Fixes** from [docs/TODO.md](file:///c:/Users/Edward/Desktop/CaseStudy/docs/TODO.md):
1. **CR-001**: Fix cross-itinerary Broken Object Level Authorization (BOLA) in `POST /api/v1/itineraries/{id}/reorder` by verifying `item.day_id in {d.id for d in itinerary.days}`.
2. **CR-002**: Fix cross-itinerary BOLA / IDOR in `DELETE /api/v1/itineraries/{id}/days/{day_id}/items/{item_id}` by asserting `day.itinerary_id == itinerary.id` and `item.day_id == day.id`.
3. **CR-003**: Fix silent data loss when saving an edited itinerary in `CustomBuilderPage` (`custom-builder.page.ts`), `ItineraryService` (`itinerary.service.ts`), and `PATCH /api/v1/itineraries/{id}` by supporting composite updates that preserve all days and stops.
4. **CR-004**: Enforce strong JWT secret configuration outside development mode, enforce non-empty Google OAuth client ID audience validation, and restrict CORS origin to `https://edselrenz.github.io`.
5. **CR-005**: Assert `email_verified is True` in Google OAuth account linking and reject deactivated users (`is_active = False`).
6. Write negative regression tests in `backend/tests/test_itineraries.py` and `backend/tests/test_auth.py` verifying all BOLA and auth fixes.

---

## 2. Key Architectural & Design Decisions

- **Dual-Mode Persistence (API + Offline Guest Mode)**:
  - Authenticated travelers store itineraries in PostgreSQL via FastAPI REST endpoints.
  - Guests and offline users store itineraries locally in IndexedDB using `@ionic/storage-angular` (`ne_guest_itineraries_v1`).
  - Seamless account migration (`GuestMigrationService`) migrates local guest itineraries into the backend upon register or login.
- **Relational Data Model & Multi-Engine Compatibility**:
  - 7 SQLAlchemy 2.0 ORM models (`User`, `AuthIdentity`, `Municipality`, `Place`, `Itinerary`, `ItineraryDay`, `ItineraryItem`).
  - Strict database engine abstraction: Uses `JsonType` and `sa.Uuid` compatible with both PostgreSQL (production) and SQLite (in-memory test harness).
- **Deterministic Suggested Itinerary Engine**:
  - Haversine distance-based geographic clustering prevents cross-province backtracking.
  - Transparent assumptions banner (honest admission costs, dining time slotting, meal/fuel disclaimers). Zero hallucinated POIs.
- **Server Orchestration & Cloudflare Tunnel**:
  - `start_server.bat` / `scripts/start_server.ps1`: Automated single-click startup booting PostgreSQL container `ne_postgres`, starting FastAPI (port 8000), launching portable `cloudflared.exe`, extracting the public `https://*.trycloudflare.com` URL, and automatically copying it to the Windows clipboard.
  - `stop_server.bat` / `scripts/stop_server.ps1`: Cleanly terminates Cloudflare Tunnel, FastAPI, frontend dev servers, and the PostgreSQL container.
- **GitHub Pages Frontend Hosting**:
  - Hosted at [https://edselrenz.github.io/Itinerary-App/](https://edselrenz.github.io/Itinerary-App/).
  - Connects to the local server via the dynamic Cloudflare Tunnel URL set through the frontend offline banner modal (`ConnectivityService.setCustomApiUrl`).
- **Data Honesty & Policy Compliance**:
  - Venues with unverified prices display "Cost not provided / Not verified" rather than guessing.
  - Apple Sign-In is intentionally gated behind `enableAppleAuth = false` with a truthful 501 gate to comply with zero-cost constraints.

---

## 3. Exact File Paths Modified or Currently Relevant

### Documentation & Audit References
- [docs/CODE_REVIEW_AUDIT.md](file:///c:/Users/Edward/Desktop/CaseStudy/docs/CODE_REVIEW_AUDIT.md) — Comprehensive technical report for CR-001 through CR-016.
- [docs/TODO.md](file:///c:/Users/Edward/Desktop/CaseStudy/docs/TODO.md) — Active checklist (Phases 11–14).
- [docs/PROJECT_STATE.md](file:///c:/Users/Edward/Desktop/CaseStudy/docs/PROJECT_STATE.md) — Handoff state, completed features, and verification records.
- [docs/KNOWN_ISSUES.md](file:///c:/Users/Edward/Desktop/CaseStudy/docs/KNOWN_ISSUES.md) — Technical constraints and tracked audit issues.
- [docs/DEVELOPMENT_PLAN.md](file:///c:/Users/Edward/Desktop/CaseStudy/docs/DEVELOPMENT_PLAN.md) — Milestones 0–14 roadmap.
- [docs/TESTING_DOCUMENTATION.md](file:///c:/Users/Edward/Desktop/CaseStudy/docs/TESTING_DOCUMENTATION.md) — Verified test results and planned security test specifications.
- [nueva_ecija_itinerary_app_code_review.md](file:///c:/Users/Edward/Desktop/CaseStudy/nueva_ecija_itinerary_app_code_review.md) — Raw independent code review report.

### Files Targeted for Phase 11 Remediation
- **Backend API & Schemas**:
  - [backend/app/api/v1/itineraries.py](file:///c:/Users/Edward/Desktop/CaseStudy/backend/app/api/v1/itineraries.py) (Lines 464–474 for CR-002 deletion check; lines 519–529 for CR-001 reorder check; lines 382–397 for CR-003 composite PATCH).
  - [backend/app/schemas/itinerary.py](file:///c:/Users/Edward/Desktop/CaseStudy/backend/app/schemas/itinerary.py) (Lines 31–36: extend `ItineraryUpdate` to accept `days`, `preferences`, `assumptions`).
  - [backend/app/core/config.py](file:///c:/Users/Edward/Desktop/CaseStudy/backend/app/core/config.py) (Line 17: JWT secret validation; Line 35: CORS origin tightening).
  - [backend/app/services/auth_service.py](file:///c:/Users/Edward/Desktop/CaseStudy/backend/app/services/auth_service.py) (Lines 165–216: OAuth audience check, `email_verified` check, `user.is_active` check).
- **Backend Test Suites**:
  - [backend/tests/test_itineraries.py](file:///c:/Users/Edward/Desktop/CaseStudy/backend/tests/test_itineraries.py) (Add negative BOLA tests and edit-mode retention tests).
  - [backend/tests/test_auth.py](file:///c:/Users/Edward/Desktop/CaseStudy/backend/tests/test_auth.py) (Add unverified email and inactive user rejection tests).
- **Frontend Custom Builder & Itinerary Service**:
  - [Project/src/app/features/itinerary/custom-builder/custom-builder.page.ts](file:///c:/Users/Edward/Desktop/CaseStudy/Project/src/app/features/itinerary/custom-builder/custom-builder.page.ts) (Lines 326–340: pass `days` in edit mode).
  - [Project/src/app/core/services/itinerary.service.ts](file:///c:/Users/Edward/Desktop/CaseStudy/Project/src/app/core/services/itinerary.service.ts) (Lines 133–146 & `updateGuestItinerary`: include `days` in update payload).
  - [Project/src/app/core/services/itinerary.service.spec.ts](file:///c:/Users/Edward/Desktop/CaseStudy/Project/src/app/core/services/itinerary.service.spec.ts) (Unit tests verifying edit-mode persistence).

### Server & Infrastructure Scripts
- [start_server.bat](file:///c:/Users/Edward/Desktop/CaseStudy/start_server.bat) / [scripts/start_server.ps1](file:///c:/Users/Edward/Desktop/CaseStudy/scripts/start_server.ps1)
- [stop_server.bat](file:///c:/Users/Edward/Desktop/CaseStudy/stop_server.bat) / [scripts/stop_server.ps1](file:///c:/Users/Edward/Desktop/CaseStudy/scripts/stop_server.ps1)
- [scripts/verify_acceptance_gate.py](file:///c:/Users/Edward/Desktop/CaseStudy/scripts/verify_acceptance_gate.py)

---

## 4. Things to Read and Understand Before Coding

1. **[docs/CODE_REVIEW_AUDIT.md](file:///c:/Users/Edward/Desktop/CaseStudy/docs/CODE_REVIEW_AUDIT.md)**:
   - Read Section 3 for exact descriptions, reproduction conditions, and code remediation snippets for `CR-001` through `CR-005`.
2. **[docs/TODO.md](file:///c:/Users/Edward/Desktop/CaseStudy/docs/TODO.md)**:
   - Review Phase 11 checkboxes to track tasks methodically.
3. **[backend/app/api/v1/itineraries.py](file:///c:/Users/Edward/Desktop/CaseStudy/backend/app/api/v1/itineraries.py)**:
   - Understand how `itinerary.days` and `day.items` relationships are loaded and cascade-managed.
   - Note that `ItineraryItem` has a foreign key to `ItineraryDay.id`, NOT directly to `Itinerary.id`.
4. **[Project/src/app/core/services/itinerary.service.ts](file:///c:/Users/Edward/Desktop/CaseStudy/Project/src/app/core/services/itinerary.service.ts)**:
   - Understand the dual-path persistence logic in `createItinerary()` and `updateItinerary()` (API first with fallback).

---

## 5. Blocking Errors & Behavioral Constraints to Keep in Mind

1. **Git Sandbox Permissions on Windows**:
   - Running `git` commands that modify the index (`git add`, `git commit`, `git checkout`) inside the standard sandbox will fail with `Permission denied` on `.git/index.lock`.
   - **Rule**: Always execute `git` write/commit/push commands with `BypassSandbox: true`.
2. **Pytest & Loopback Sockets in Sandbox**:
   - `pytest` or `TestClient` runs can hang or fail when executing inside the Windows AppContainer sandbox.
   - **Rule**: Always execute `pytest` and acceptance verification scripts with `BypassSandbox: true`.
3. **Angular Dependency Injection Tokens (NG2003)**:
   - Do **NOT** use TypeScript `import type` for Angular dependency injection tokens (e.g., `HttpClient`, `Router`, services). Angular requires runtime symbols for decorator reflection.
   - ESLint rule `@angular-eslint/prefer-inject` is configured `off` to maintain constructor injection compatibility.
4. **Angular Component Style Budget (<10kB)**:
   - Angular builds strictly enforce a `maximumError: 10kB` limit on individual component SCSS bundles. Keep component styles scoped and compact; put shared design tokens in `variables.scss` or `global.scss`.
5. **SlowAPI & Cloudflare Tunnel Consideration (CR-013)**:
   - Remote requests through `cloudflared` proxy originate from `127.0.0.1`. When running auth endpoints through the tunnel, SlowAPI rate-limits all remote users together unless keyed on `CF-Connecting-IP`. Keep this in mind when testing auth under tunnel traffic.
6. **Documentation Truthfulness**:
   - Never report unverified assumptions as fact. Keep documentation synchronized across `TODO.md`, `PROJECT_STATE.md`, and `KNOWN_ISSUES.md`.

