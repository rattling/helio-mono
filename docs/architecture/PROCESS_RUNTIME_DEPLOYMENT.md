# Process Architecture: Runtime + Environment + Deployment

**Status**: Active (M2-M4 baseline)  
**Primary scope**: service lifecycle, env isolation, deployment posture

## Purpose

Capture how Helionyx runs as a unified service with environment-aware
configuration and operational isolation.

## Runtime Model

Helionyx runs as a single long-running service combining:
- FastAPI HTTP API
- Telegram adapter (optional/config-driven)
- background tasks (scheduler/notifications)
- coordinated startup/shutdown lifecycle

**Entry point**:
- `services/api/runner.py`
- `make run ENV=<dev|staging|live>`

## Environment Strategy

Environments are explicit and isolated:
- `dev`
- `staging`
- `live`

Configuration sources:
1. base `.env` (if present)
2. environment overlay `.env.<ENV>`
3. explicit process environment variables (highest precedence)

Primary isolated surfaces:
- event store path
- projections database path
- API host/port
- Telegram credentials
- logging level and cost controls

## Deployment Model

### Current posture

- Same-host multi-environment deployment is supported.
- Each environment uses independent ports, paths, and service units.
- Runtime state is durable and survives process restarts.

### Service management expectations

- deterministic startup sequence
- graceful shutdown (SIGTERM/SIGINT)
- health and readiness probes
- explicit logs per environment

## Health/Readiness Contract

Representative endpoints:
- `GET /health`
- `GET /health/ready`

Readiness includes substrate checks (event path, projection DB path/connectivity)
so orchestration/adapters only run when base dependencies are available.

## Operational Considerations

- Projections are derived and rebuildable.
- Runtime can degrade safely when optional integrations are unavailable.
- Notifications/delivery should be deduplicated and auditable.

## Security and Data Notes

- Treat `.env*` as sensitive.
- Keep secrets out of logs and artifacts.
- Prefer host-level disk encryption and restrictive file permissions.
- Backup/restore and security baselines are documented separately:
  - `docs/DATA_MANAGEMENT.md`
  - `docs/SECURITY.md`
  - ADRs in `docs/ADRS/`
