# Architecture Decision Record

## Title
Milestone 11 Lab: Guardrailed Write Controls with Explicit Audit and Rollback

## Status
Accepted

## Context
Milestone 11 introduces operator-facing controls for learning and policy posture.
Without hard boundaries, Lab controls could become an unsafe mutation surface
that bypasses deterministic safety principles and erodes operator trust.

## Decision
Lab write operations will be explicitly bounded and guardrailed:
- Only a narrow set of approved control fields is writable in Milestone 11.
- Every write requires actor attribution and rationale.
- Each change records before/after values and rollback metadata.
- Disallowed or out-of-policy changes are rejected server-side with deterministic reasons.

Supported write classes in M11:
- mode toggles (e.g., deterministic-safe, bounded personalization)
- selected threshold/config updates within predefined ranges
- explicit rollback action to deterministic-safe baseline

## Rationale
- Preserves human authority and safety invariants.
- Keeps adaptation reversible and auditable.
- Prevents hidden or accidental policy drift.
- Provides clear operator understanding of what can and cannot be changed.

## Alternatives Considered
- Broad configuration mutation from UI.
- Read-only Lab with no write operations.
- Client-side enforcement only (without server-side guardrails).

## Consequences
- Requires explicit write contract models and validation rules.
- Requires audit event payloads with actor/rationale/before-after schema.
- Increases implementation effort but materially improves operational safety.
