# Architecture Decision Record

## Title
Milestone 10 Data Explorer: Read-Only Traceability Read Model and API Boundary

## Status
Accepted

## Context
Milestone 10 introduces a power-user Data Explorer intended for deep
interrogation of Helionyx behavior. Existing UI surfaces (Tasks/Control Room)
show useful summaries but do not yet provide a direct, structured path from
summary signals to underlying event and state evidence.

A raw pass-through of internal storage formats to frontend would create unstable
coupling and make future evolution risky.

## Decision
Data Explorer will be implemented against explicit, operator-facing read models
served by API contracts, not direct storage internals.

The read model boundary will support:
- entity lookup by canonical IDs,
- event timeline retrieval,
- projection/state snapshots,
- decision/rationale evidence views.

Milestone 10 remains read-first: no broad mutation controls are introduced by
Data Explorer APIs.

## Rationale
- Preserves contract-first service boundaries.
- Improves operator trust via explicit evidence views.
- Keeps frontend stable while internals evolve.
- Reduces risk of accidental policy logic duplication in UI.

## Alternatives Considered
- Directly exposing raw event-store/filesystem structures to frontend.
- Building Data Explorer purely client-side from existing mixed endpoints.

## Consequences
- Requires new backend aggregation/read-model endpoints.
- Introduces explicit contract maintenance responsibility.
- Enables future Lab/write milestones to attach to stable evidence surfaces.
