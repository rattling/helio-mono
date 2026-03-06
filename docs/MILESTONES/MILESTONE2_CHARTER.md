# Helionyx -- Milestone 2 Charter

## Service Infrastructure Foundation

**Version:** 0.1\
**Date:** 2026-02-11

**Part of:** Operational Hardening Arc (Milestones 2, 3, 4)

------------------------------------------------------------------------

## 1. Purpose

Milestone 2 establishes the **runtime substrate** for Helionyx as a continuously running service.

This milestone does **not** expand cognitive features.

Its purpose is to transform Helionyx from a script-driven skeleton into a persistent, environment-aware service with clean lifecycle management.

**Unified Arc Context:**
- **Milestone 2** (this): Service infrastructure foundation
- **Milestone 3**: Deployment & CI discipline
- **Milestone 4**: Hardening & security baseline

Milestone 2 prepares the runtime layer. Milestones 3 and 4 build on this foundation.

------------------------------------------------------------------------

## 2. Scope

### 2.1 API Surface (FastAPI Adapter)

Introduce a thin FastAPI layer acting strictly as an adapter.

Requirements:

-   FastAPI must not contain domain logic.
-   Domain logic remains framework-independent.
-   API exposes:
    -   health endpoints
    -   basic state inspection
    -   ingestion endpoints
    -   interaction endpoints used by Telegram adapter

The API is an interface boundary, not the core system.

------------------------------------------------------------------------

### 2.2 Long-Running Service Model

Helionyx must operate as a persistent service.

Requirements:

-   Clean service entrypoint (`services/api/main.py` or similar)
-   Deterministic startup sequence
-   Graceful shutdown handling
-   Resume from durable state
-   No reliance on in-memory session state

System must survive restart without data loss.

------------------------------------------------------------------------

### 2.3 Environment Separation

Introduce explicit environment tiers:

-   `dev`
-   `staging`
-   `live`

Environment must control:

-   configuration
-   credentials
-   storage paths
-   logging level
-   LLM model selection (if applicable)

Environment switching must be:

-   explicit (via `ENV` variable or equivalent)
-   config-file-driven (`.env.dev`, `.env.staging`, `.env.live`)
-   reproducible
-   free of hidden state

------------------------------------------------------------------------

### 2.4 Runnable Service Commands

Provide simple commands to run the service locally:

    make run ENV=dev
    make run ENV=staging
    
Or equivalently:

    .venv/bin/python -m services.api.main --env dev

Service must start, bind to a port, and respond to health checks.

------------------------------------------------------------------------

## 3. Non-Goals

Milestone 2 does NOT include:

-   Deployment automation (Milestone 3)
-   CI/CD pipeline (Milestone 3)
-   Backup/restore procedures (Milestone 4)
-   Security hardening (Milestone 4)
-   New cognitive features
-   Calendar integration
-   Multi-user support
-   UI beyond Telegram
-   Container orchestration

------------------------------------------------------------------------

## 4. Architectural Invariants

The following must remain true:

1.  Domain logic is framework-independent.
2.  FastAPI acts strictly as adapter.
3.  Event log remains append-only.
4.  Decisions remain first-class objects.
5.  All durable state reconstructable from repo + storage.
6.  Environment behavior is explicit and deterministic.
7.  Service boundaries remain intact.

------------------------------------------------------------------------

## 5. Deliverables

Milestone 2 is complete when:

-   FastAPI adapter layer exists
-   Service can start and stop cleanly
-   Health endpoints respond
-   Telegram interface functions through API layer
-   Environment switching works (dev/staging/live)
-   Service can be run locally via `make run ENV=dev`
-   System survives restart without data loss

------------------------------------------------------------------------

## 6. Acceptance Criteria

Milestone 2 is accepted when:

-   Service starts via `make run ENV=dev`
-   Health endpoint returns 200
-   Telegram bot can interact through API
-   Service shuts down gracefully on SIGTERM
-   Event log integrity preserved across restart
-   Environment configuration loads correctly for all three tiers

If any of these fail, milestone is incomplete.

------------------------------------------------------------------------

## 7. Forward Pressure (Non-Binding)

Milestone 2 prepares for:

-   **Milestone 3**: Deployment & CI discipline
-   **Milestone 4**: Hardening & security baseline
-   Future: Todo system expansion, calendar integration, native UI

We ensure forward compatibility without over-architecting for
hypothetical scale.
