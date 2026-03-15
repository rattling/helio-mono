# Architecture Decision Record

## Title
Milestone 15: Projection Rebuildability Is a Safety Property, Not the Normal Operating Mode

## Status
Accepted

## Context

Helionyx treats the append-only event ledger as the durable source of truth and
uses projections/read models for operational querying.

The current implementation rebuilds projections from the ledger during startup.
This is an appropriate early-stage posture because it is simple, easy to reason
about, and reduces the risk of silent divergence while the event model and
projection logic are still evolving quickly.

However, always rebuilding projections from scratch is not the desired long-term
operating model for a heavily used system. As the event log grows and projection
logic becomes richer, full replay on every startup becomes more operationally
expensive and creates pressure around:
- startup time,
- projection freshness,
- schema drift,
- replay boundaries,
- and migration/repair semantics.

## Decision

Helionyx will keep the ledger as the canonical source of truth, but will evolve
toward a more conservative projection model in which:
- projections are durable operational read state,
- projections are updated incrementally in normal operation,
- startup prefers catch-up from the last processed event rather than full
  rebuild,
- and full rebuild remains an explicit maintenance, repair, migration, or
  verification path.

Rebuildability remains required, but rebuildability is treated as a safety and
recovery property rather than the default steady-state behavior.

## Rationale

- Keeps the event ledger authoritative.
- Preserves the ability to recover or reconstitute derived state when needed.
- Avoids locking the system into replay-everything behavior as normal
  operations scale.
- Creates space for future decisions about replay windows, schema evolution,
  projection metadata, and migration tooling without discarding the core
  ledger-first architecture.

## Alternatives Considered

- **Always rebuild projections from scratch on startup**
  - Simple and robust early on.
  - Rejected as the long-term operating posture because it does not scale well
    operationally.

- **Treat projections as primary truth with no guaranteed rebuild path**
  - Faster operationally.
  - Rejected because it undermines ledger authority and reduces recovery and
    auditability.

## Consequences

- The current full-rebuild approach remains acceptable as an early-stage
  implementation.
- Future work should likely introduce:
  - last-processed-event tracking,
  - incremental projection application,
  - explicit rebuild/migration commands,
  - and projection health/status visibility.
- Helionyx will eventually need explicit decisions about:
  - how far back incremental catch-up should replay,
  - how projection schema/version changes are handled,
  - when full rebuild is mandatory,
  - and how to detect or repair projection drift.

This ADR records the intended direction so that future projection work evolves
toward a durable incremental model rather than entrenching full startup replay
as the permanent operating posture.