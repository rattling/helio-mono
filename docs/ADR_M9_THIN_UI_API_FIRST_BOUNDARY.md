# Architecture Decision Record

## Title
Milestone 9 UI Architecture: Thin Web Client with API-First Domain Boundary

## Status
Accepted

## Context
Milestone 9 introduces the first Helionyx web UI with two primary goals:

- reliable task management for daily operation, and
- transparent system interrogation through a Control Room.

Helionyx already serves multiple interaction surfaces (API, Telegram), and core
project principles require transparent behavior, inspectability, and consistent
domain semantics across surfaces.

If the web client owns domain policy logic (task lifecycle rules, ranking
decisions, learning policy interpretation), behavior can drift across surfaces,
reducing trust and increasing maintenance overhead.

## Decision
For Milestone 9, the web UI will be implemented as a thin React client that is
API-first and server-authoritative for domain behavior.

Specifically:

- Domain decisions remain in backend services and contracts.
- Frontend owns presentation concerns and interaction ergonomics only.
- Frontend may compute presentation-only derived state (view filters, local
  grouping, optimistic interaction UX), but may not introduce policy logic.
- API contracts become the integration boundary between UI and backend.

## Rationale
- Preserves behavior parity across UI, Telegram, and future interfaces.
- Keeps policy and explanation logic centralized for auditability.
- Reduces long-term coupling and duplicated decision paths.
- Aligns with Helionyx architecture posture (thin adapters, explicit contracts).

## Alternatives Considered
- Heavier frontend domain logic for task/attention behavior.
- Fully mixed model with duplicated policy heuristics in UI and backend.

## Consequences
- Backend API/read models may need expansion to satisfy UI ergonomics.
- Frontend iteration speed may depend on explicit backend contract evolution.
- Transparency improves because explanations originate from one authority path.
- Future surfaces can reuse the same domain semantics with lower drift risk.
