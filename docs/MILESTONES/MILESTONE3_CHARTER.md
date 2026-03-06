# Helionyx -- Milestone 3 Charter

## Deployment & CI Discipline

**Version:** 0.1\
**Date:** 2026-02-11

**Part of:** Operational Hardening Arc (Milestones 2, 3, 4)

------------------------------------------------------------------------

## 1. Purpose

Milestone 3 introduces **deployment discipline and continuous integration** to make Helionyx reliably deployable and operationally repeatable.

This milestone does **not** expand cognitive features.

Its purpose is to enable one-command deployment to `node1` with CI enforcement ensuring code quality.

**Unified Arc Context:**
- **Milestone 2**: Service infrastructure foundation (complete)
- **Milestone 3** (this): Deployment & CI discipline
- **Milestone 4**: Hardening & security baseline

Milestone 3 assumes M2's persistent service foundation is in place.

------------------------------------------------------------------------

## 2. Scope

### 2.1 Make-Based Deployment

Introduce deployment commands via Makefile.

Required commands:

    make deploy ENV=dev
    make deploy ENV=staging
    make deploy ENV=live
    make status
    make restart
    make logs
    make stop

**Deployment target:** `node1`

Requirements:

-   Environment-aware deployment
-   Idempotent (safe to run repeatedly)
-   Preserves event log and state
-   Updates code, dependencies, and configuration
-   Restarts service cleanly

------------------------------------------------------------------------

### 2.2 Same-Host Multi-Environment Support

Support running dev, staging, and live environments on the same host (`node1`).

**Requirements:**

-   Each environment must have:
    -   **Distinct API port** (e.g., 8000 dev, 8001 staging, 8002 live)
    -   **Separate data directories** (event store and projections DB)
    -   **Unique systemd service name** (helionyx-dev, helionyx-staging, helionyx)
    -   **Environment-specific Telegram bot** (per section 2.6)
    -   **Independent configuration** (`.env.dev`, `.env.staging`, `.env.live`)

-   Runner must read `API_HOST` and `API_PORT` from config
-   Data paths must be fully isolated (no shared state between envs)
-   Services must not conflict (ports, sockets, file locks)

**Configuration Additions:**

-   Add `API_HOST` to Config (default: `0.0.0.0`)
-   Add `API_PORT` to Config (default: `8000`)
-   Update `.env.template` with same-host deployment examples
-   Update `services/api/runner.py` to use config-driven host/port

**Rationale:**

Single-host deployment is pragmatic for personal use and early stages. Full isolation enables safe testing and gradual rollout without requiring multi-node infrastructure.

------------------------------------------------------------------------

### 2.3 Deployment Scripts

Create deployment scripts in `scripts/deploy/`:

-   `deploy.sh` - Main deployment logic
-   `status.sh` - Service status check
-   `restart.sh` - Clean restart
-   `logs.sh` - Tail service logs

Scripts must:

-   Handle environment selection
-   Validate preconditions
-   Report errors clearly
-   Support rollback if deploy fails

------------------------------------------------------------------------

### 2.4 Service Management

Deploy must:

-   Use systemd or equivalent for service management
-   Enable service auto-start on boot
-   Provide clean stop/start/restart
-   Capture logs to persistent location

**Service Naming Convention:**

-   `helionyx-dev.service` (dev environment)
-   `helionyx-staging.service` (staging environment)
-   `helionyx.service` (live/production environment)

Each service must:

-   Use appropriate `.env.{env}` file
-   Bind to correct port from config
-   Write logs to environment-specific location
-   Run under appropriate user

------------------------------------------------------------------------

### 2.5 CI/CD Pipeline

Introduce CI pipeline (GitHub Actions or equivalent).

CI must run on:

-   All pushes to milestone branches
-   All PRs to main

CI pipeline includes:

1.  **Lint**: Code style enforcement (black, flake8, or ruff)
2.  **Format Check**: Ensure code is formatted
3.  **Tests**: Run test suite
4.  **Type Check** (optional): mypy or similar

CI must pass before merge to main.

------------------------------------------------------------------------

### 2.6 Deployment Documentation

Create `docs/DEPLOYMENT.md` covering:

-   Prerequisites (SSH access, permissions)
-   First-time setup on node1
-   Deployment procedure
-   Troubleshooting common issues
-   Rollback procedure

------------------------------------------------------------------------

### 2.7 Environment-Specific Telegram Bots

Introduce separate Telegram bots for each environment to ensure proper isolation and testing.

Requirements:

-   Human operator creates 3 distinct bots via @BotFather:
    -   `helionyx_dev_bot` (development)
    -   `helionyx_staging_bot` (staging/testing)
    -   `helionyx_bot` (production/live)
-   Human operator updates environment-specific configuration:
    -   `.env.dev` - dev bot token and chat ID
    -   `.env.staging` - staging bot token and chat ID
    -   `.env.live` - live bot token and chat ID
-   Agents must use correct bot credentials for each environment
-   Configuration loading already supports this (M2)

**Benefits:**

-   Development testing doesn't spam production bot
-   Bot username clearly indicates environment
-   Safe testing of notification changes
-   True environment isolation
-   Aligns with environment separation philosophy

**Implementation Note:**

Code already supports this via `Config.from_env(ENV)`. No code changes needed—only configuration setup by human operator.

------------------------------------------------------------------------

## 3. Non-Goals

Milestone 3 does NOT include:

-   Backup/restore procedures (Milestone 4)
-   Security hardening (Milestone 4)
-   Multi-node deployment
-   Container orchestration
-   Cloud deployment
-   Load balancing
-   New cognitive features

------------------------------------------------------------------------

## 4. Architectural Invariants

The following must remain true:

1.  Deployment does not mutate event log history.
2.  Environment configuration remains explicit.
3.  Service boundaries remain intact.
4.  Deployment is reproducible and auditable.

------------------------------------------------------------------------

## 5. Deliverables

Milestone 3 is complete when:

-   `make deploy ENV=dev` successfully deploys to node1
-   Service restarts cleanly after deployment
-   `make status` reports service health
-   `make logs` shows service output
-   CI pipeline runs on all branches
-   CI passes for milestone-3 branch
-   Deployment documentation exists and is validated

------------------------------------------------------------------------

## 6. Acceptance Criteria

Milestone 3 is accepted when:

-   A developer can deploy to node1 with one command
-   Deployment is idempotent (safe to repeat)
-   Service survives deployment without data loss
-   **Multiple environments run simultaneously on node1** without conflict
-   Each environment has **distinct port, data paths, and systemd service**
-   Each environment uses its designated Telegram bot (dev/staging/live)
-   Agents correctly load environment-specific bot credentials
-   `make deploy ENV=X` correctly deploys to appropriate environment
-   CI pipeline catches lint/test failures
-   Documentation allows a new developer to deploy successfully

If any of these fail, milestone is incomplete.

------------------------------------------------------------------------

## 7. Forward Pressure (Non-Binding)

Milestone 3 prepares for:

-   **Milestone 4**: Hardening & security baseline
-   Future: Multi-environment orchestration
-   Future: Automated rollback and canary deployments

We ensure forward compatibility without over-architecting for
hypothetical scale.
