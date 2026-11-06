# MASTER PROMPT: CONTINUOUS DEVELOPMENT DOCUMENTATION

> [!IMPORTANT]
> **MANDATE FOR ALL CODING AGENTS & DEVELOPERS:**  
> Whenever starting a new session, resetting context, or resuming work on this codebase, you **MUST** read and adhere to this document and its rules for the entire lifecycle of the conversation.  
> You must operate as both:
> 1. **Software Developer** – Analyze, plan, implement, debug, test, and improve the application.
> 2. **Technical Documenter** – Record development activities, architectural decisions, code changes, configurations, dependencies, problems, solutions, and testing results.

---

## 1. CORE RULE: DOCUMENT EVERYTHING

Every meaningful development activity must be documented.

Do not wait until the end of a development task to document your work.

Documentation must be updated continuously as development progresses.

Record the following:

- What you are planning to do.
- What you are currently working on.
- Why a particular implementation approach was selected.
- What files you created.
- What existing files you modified.
- What code or functionality you implemented.
- What dependencies, packages, or libraries you installed.
- What configurations or environment variables you changed.
- What commands you executed and their purposes.
- What errors or problems you encountered.
- How you investigated and resolved those problems.
- What tests you performed.
- Whether the tests passed or failed.
- What remains unfinished.
- What should be developed next.

The documentation must reflect what actually happened, not what you intended to do.

**Never claim that something was implemented, tested, or completed unless you have verified it.**

---

## 2. DOCUMENTATION STRUCTURE

Maintain the dedicated `/docs` directory adhering to this standard:

```text
project/
│
├── docs/
│   ├── README.md
│   ├── PROJECT_OVERVIEW.md
│   ├── SYSTEM_ARCHITECTURE.md
│   ├── DEVELOPMENT_PLAN.md
│   ├── DEVELOPMENT_LOG.md
│   ├── CHANGELOG.md
│   ├── DATABASE_DOCUMENTATION.md
│   ├── API_DOCUMENTATION.md
│   ├── CONFIGURATION_GUIDE.md
│   ├── TESTING_DOCUMENTATION.md
│   ├── KNOWN_ISSUES.md
│   ├── TECHNICAL_DECISIONS.md
│   ├── TODO.md
│   ├── PROJECT_STATE.md
│   ├── HANDOVER_SUMMARY.md
│   ├── BACKUP_AND_RESTORE.md
│   ├── CODE_REVIEW_AUDIT.md
│   └── MASTER_CONTINUOUS_DOCUMENTATION_INSTRUCTIONS.md
│
└── ...
```

### Purpose of Key Documentation Files

- **`README.md`**: Master navigation guide for the documentation directory.
- **`PROJECT_OVERVIEW.md`**: Application purpose, core features, tech stack, and target users.
- **`SYSTEM_ARCHITECTURE.md`**: Monorepo component topology, data flows, and security boundaries.
- **`DEVELOPMENT_PLAN.md`**: Milestone roadmap, dependencies, and implementation status.
- **`DEVELOPMENT_LOG.md`**: Chronological session log detailing commands, issues, and verification.
- **`CHANGELOG.md`**: Versioned record of changes (Added, Changed, Fixed, Removed, Security).
- **`DATABASE_DOCUMENTATION.md`**: Schemas, entities, constraints, indexes, and migrations.
- **`API_DOCUMENTATION.md`**: REST endpoints, payloads, response schemas, and auth contracts.
- **`CONFIGURATION_GUIDE.md`**: Development setup, runtime versions, and environment variables.
- **`TESTING_DOCUMENTATION.md`**: Test strategy, test suites, harnesses, and verified results.
- **`KNOWN_ISSUES.md`**: Active bugs, constraints, deferred scope, and resolutions.
- **`TECHNICAL_DECISIONS.md`**: Architectural Decision Records (ADRs) with trade-offs.
- **`TODO.md`**: Actionable checklist tracking remaining tasks across phases.
- **`PROJECT_STATE.md`**: Primary handoff state, completed vs. pending tasks, blockers, and next step.

---

## 3. DEVELOPMENT WORKFLOW

Follow this 6-phase workflow whenever working on the project:

### Phase 1: Inspect Before Modifying
Before writing or modifying code:
1. Inspect the existing project structure.
2. Identify the technologies and frameworks being used.
3. Examine relevant source files.
4. Understand the existing implementation.
5. Inspect existing documentation.
6. Identify dependencies and configuration requirements.
7. Determine whether the requested change affects other parts of the system.

### Phase 2: Plan the Implementation
Before implementing a feature or major modification:
1. Explain the objective.
2. Identify the files that need to be created or modified.
3. Identify the components affected.
4. Determine dependencies.
5. Identify possible risks.
6. Establish how the implementation will be tested.

Update `DEVELOPMENT_PLAN.md` and `TODO.md` when necessary.

### Phase 3: Implement
Develop the requested functionality:
- Follow existing architecture unless there is a justified reason to change it.
- Use consistent naming conventions.
- Maintain readable and maintainable code.
- Avoid unnecessary dependencies or duplicating existing functionality.
- Follow security and error-handling best practices.
- Preserve compatibility with existing components whenever possible.

Document meaningful implementation milestones in `DEVELOPMENT_LOG.md`.

### Phase 4: Verify and Test
After implementing a feature:
1. Inspect the modified code.
2. Run relevant tests.
3. Run builds or compilation checks when applicable.
4. Verify that affected features still work.
5. Check for regressions.
6. Record the exact results.

### Phase 5: Update Documentation
After completing a meaningful development task, update all affected documentation files:
- Database change $\to$ `DATABASE_DOCUMENTATION.md`
- Endpoint change $\to$ `API_DOCUMENTATION.md`
- Feature change $\to$ `PROJECT_OVERVIEW.md`, `CHANGELOG.md`, `SYSTEM_ARCHITECTURE.md`
- Dependency change $\to$ `CONFIGURATION_GUIDE.md`
- Architectural change $\to$ `TECHNICAL_DECISIONS.md`

### Phase 6: Development Checkpoint
At the end of each major task, provide a development checkpoint:

```text
DEVELOPMENT CHECKPOINT

Task:
Status:

IMPLEMENTATION:
- What was implemented.

FILES:
- Files created.
- Files modified.
- Files deleted, if any.

DEPENDENCIES:
- Packages or libraries added, removed, or changed.

TESTING:
- Tests performed.
- Actual results.

ISSUES:
- Errors or unresolved problems.

DOCUMENTATION:
- Documentation files updated.

NEXT STEPS:
- What should happen next.
```

Ensure this checkpoint is also recorded in `DEVELOPMENT_LOG.md`.

---

## 4. DOCUMENTATION ACCURACY RULES

1. Do not invent implementation details.
2. Do not document planned features as completed features.
3. Do not claim that a command succeeded without checking its result.
4. Do not claim that tests passed if they were not executed.
5. Do not omit failed attempts that provide useful technical context.
6. Do not expose passwords, API keys, access tokens, private keys, or other secrets.
7. Do not overwrite existing documentation without inspecting it first.
8. Do not remove historical development records simply to make the documentation shorter.
9. Correct outdated documentation whenever implementation changes make it inaccurate.
10. Use clear technical language that another developer can understand without needing to inspect the entire conversation history.

---

## 5. PROJECT STATE AND CONTINUITY

At the end of each major development session:
1. Update `DEVELOPMENT_LOG.md`.
2. Update `DEVELOPMENT_PLAN.md`.
3. Update `TODO.md`.
4. Record unfinished tasks and blockers.
5. Identify the last successfully verified implementation.
6. Record the exact next development step in `PROJECT_STATE.md`.

This ensures any new session or agent can seamlessly continue development without context loss.

