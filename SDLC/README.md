# SDLC Docs Index

This directory contains the software delivery process artifacts grouped by audience.

## Human-facing

- `human/SDLC_HUMAN_PROCESS_GUIDE.md`
  - Overview of how the process works, why it exists, and how to update it safely.
- `human/SDLC_HUMAN_DRIVER_PROMPTS.md`
  - Copy/paste prompts humans use to drive ARCH/DEV→QA/process-check sessions.

## Agent-facing

- `agent/SDLC_AGENT_AUTHORITY_MAP.md`
  - Instruction precedence and conflict resolution.
- `agent/SDLC_AGENT_SESSION_BOOTSTRAP.md`
  - Startup and rehydration checklist.
- `agent/SDLC_AGENT_EXECUTION_RUNBOOK.md`
  - Per-issue execution loop, PR preflight, CI polling posture.

## Shared

- `SDLC_PROCESS_CHANGELOG.md`
  - Durable changelog for process-documentation updates.
- `SDLC_GITHUB_BRIDGE_POLICY.md`
  - Defines what remains in `.github/` for platform discovery and what stays canonical in SDLC docs.

## Naming convention

- `SDLC_HUMAN_*` files are intended for operators/reviewers.
- `SDLC_AGENT_*` files are intended for execution behavior in agent sessions.
- Shared process state/history remains at the `SDLC/` root.
- `.github/` keeps only required bridge/discovery entrypoints; canonical process rules remain in SDLC docs.
