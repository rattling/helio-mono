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

### 2.2 Deployment Scripts

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

### 2.3 Service Management

Deploy must:

-   Use systemd or equivalent for service management
-   Enable service auto-start on boot
-   Provide clean stop/start/restart
-   Capture logs to persistent location

------------------------------------------------------------------------

### 2.4 CI/CD Pipeline

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

### 2.5 Deployment Documentation

Create `docs/DEPLOYMENT.md` covering:

-   Prerequisites (SSH access, permissions)
-   First-time setup on node1
-   Deployment procedure
-   Troubleshooting common issues
-   Rollback procedure

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
