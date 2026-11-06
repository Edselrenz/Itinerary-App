# Nueva Ecija Travel Itinerary — Technical Documentation

Welcome to the technical documentation repository for the **Nueva Ecija Travel Itinerary Application** (MVP).

This documentation suite is maintained continuously throughout development to provide an accurate, transparent, and reproducible technical record of system architecture, implementation history, database designs, API contracts, and testing verification.

---

## Documentation Navigation Guide

| Document | Purpose | Audience |
| :--- | :--- | :--- |
| [**MASTER_CONTINUOUS_DOCUMENTATION_INSTRUCTIONS.md**](./MASTER_CONTINUOUS_DOCUMENTATION_INSTRUCTIONS.md) | **Continuous Development Protocol & Agent Mandate**: Rules, workflow phases, documentation accuracy standards, and handoff rules for every context reset. | All Developers & Coding Agents |
| [**PROJECT_STATE.md**](./PROJECT_STATE.md) | **Primary handoff document**: current status, completed vs pending features, last verified working state, blockers, and immediate next task. | All Developers & Agents |
| [**PROJECT_OVERVIEW.md**](./PROJECT_OVERVIEW.md) | High-level application purpose, target users, core feature scope, and zero-cost open-data constraints. | Developers, Stakeholders |
| [**SYSTEM_ARCHITECTURE.md**](./SYSTEM_ARCHITECTURE.md) | End-to-end component topology, data flows, client-server separation, security boundaries, and open-data guardrails. | Architects, Fullstack Engineers |
| [**DEVELOPMENT_PLAN.md**](./DEVELOPMENT_PLAN.md) | The 11-step sequential milestone roadmap (Steps 0 to 10), dependencies, and current progress. | Project Leads, Developers |
| [**DEVELOPMENT_LOG.md**](./DEVELOPMENT_LOG.md) | Chronological development session log recording actions, executed commands, errors, resolutions, and verification. | Developers, Auditors |
| [**CHANGELOG.md**](./CHANGELOG.md) | Versioned record of changes categorized into Added, Changed, Fixed, Security, and Architecture. | Developers, Release Managers |
| [**DATABASE_DOCUMENTATION.md**](./DATABASE_DOCUMENTATION.md) | PostgreSQL / SQLite schema specification, 7 relational tables, columns, constraints, foreign keys, indexes, and migrations. | Backend & Database Engineers |
| [**DATABASE_MANAGEMENT_GUIDE.md**](./DATABASE_MANAGEMENT_GUIDE.md) | Operational database handbook: GUI/CLI management, Alembic migrations, seeding, backup/restore drills, and clean resets. | Developers, DBAs, DevOps |
| [**API_DOCUMENTATION.md**](./API_DOCUMENTATION.md) | REST API contract for `/api/v1`, endpoints, payloads, response schemas, error codes, and auth requirements. | Frontend & Backend Engineers |
| [**CONFIGURATION_GUIDE.md**](./CONFIGURATION_GUIDE.md) | Development machine setup, environment variables, local database configuration, and runtime execution instructions. | DevOps, New Developers |
| [**TESTING_DOCUMENTATION.md**](./TESTING_DOCUMENTATION.md) | Test suite strategy, unit/integration tests, in-memory SQLite test harness, build verification, and test outputs. | QA, Test Engineers |
| [**TECHNICAL_DECISIONS.md**](./TECHNICAL_DECISIONS.md) | Architectural Decision Records (ADRs) explaining context, alternatives, trade-offs, and consequences of key choices. | System Architects |
| [**MAP_AND_ROUTING_PROPOSAL.md**](./MAP_AND_ROUTING_PROPOSAL.md) | Full architectural analysis & engineering blueprints from `itinerary_app_map_and_routing_proposal.pdf` (MAP-01 to MAP-03, ROUTE-01 to ROUTE-05). | System Architects, Fullstack Engineers |
| [**UI_UX_EVALUATION_REPORT.md**](./UI_UX_EVALUATION_REPORT.md) | Live UI/UX evaluation & developer template critique from `itinerary_app_ui_ux_evaluation_report.pdf` (UIUX-01 to UIUX-10, P0–P2). | UI/UX Designers, Frontend Engineers |
| [**KNOWN_ISSUES.md**](./KNOWN_ISSUES.md) | Active bugs, intentional limitations, deferred features, and resolution pathways. | Developers, QA |
| [**TODO.md**](./TODO.md) | Granular actionable checklist tracking remaining tasks across all development phases. | Developers |

---

## Where to Start

- **Resuming Development or Context Reset**: Start with [MASTER_CONTINUOUS_DOCUMENTATION_INSTRUCTIONS.md](./MASTER_CONTINUOUS_DOCUMENTATION_INSTRUCTIONS.md) followed by [PROJECT_STATE.md](./PROJECT_STATE.md) and [TODO.md](./TODO.md).
- **New Developers**: Start with [PROJECT_OVERVIEW.md](./PROJECT_OVERVIEW.md) followed by [CONFIGURATION_GUIDE.md](./CONFIGURATION_GUIDE.md).
- **Frontend Development**: Reference [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) and [SYSTEM_ARCHITECTURE.md](./SYSTEM_ARCHITECTURE.md).
- **Backend / Database Development**: Reference [DATABASE_DOCUMENTATION.md](./DATABASE_DOCUMENTATION.md) and [TECHNICAL_DECISIONS.md](./TECHNICAL_DECISIONS.md).

