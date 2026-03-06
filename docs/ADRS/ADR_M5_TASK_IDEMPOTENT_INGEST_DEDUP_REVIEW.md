# Architecture Decision Record

## Title
Milestone 5: Task Ingest Idempotency, Deterministic Dedup, and Review Gate

## Status
Accepted

## Context
Milestone 5 requires:
- Idempotent ingest (via `source_ref`)
- Deterministic deduplication with auditability/explainability
- Telegram-operable lifecycle

Helionyx already records message ingestion and extraction events, but extraction idempotency is currently best-effort and bounded (e.g., recent-window checks).
We need strong guarantees that replay/rebuilds and repeated ingest do not create duplicated tasks.

We also want a structure for “needs review” (and potentially prompting) without forcing a heavy conversational workflow in M5.

## Decision
### 1) Idempotency (`source_ref`) — Option A
- **Idempotency is keyed by (`source`, `source_ref`).**
- For tasks inferred from existing extraction events, `source_ref` is derived from **message identity + ordinal**.
  - Canonical form (internal, deterministic):
    - `source=telegram` (or whatever the message source was)
    - `source_ref = "message_event:<message_event_id>:todo:<ordinal>"`
  - `ordinal` is the stable sequence number of todo-like extractions for that message, in event-log order (0-based).

This ensures:
- Replaying the same extraction stream produces the same task identity.
- Repeated “canonicalization” runs are idempotent.

### 2) Deduplication (separate from idempotency)
- Deduplication groups *different* ingests that likely refer to the same underlying task.
- Dedup must be deterministic (same inputs → same dedup group id) and must emit an explicit, human-legible explanation event.
- Dedup does **not** replace idempotency; it’s an additional layer for “same task described twice” cases.

### 3) Explainability events
- For ingest and dedup actions, record an explicit event payload including:
  - inputs used (normalized fields / fingerprint inputs)
  - chosen action (created / returned existing / linked to dedup group)
  - rationale string suitable for audits and agent reasoning

### 4) Review gate (`needs_review`) is a label, not a status
- We reserve a label `needs_review` to represent “inferred / not yet explicitly confirmed”.
- M5 may apply this label on inferred tasks but does not have to block.
  - i.e. the system is not required to halt in a review-only state.

### 5) Prompting for missing details is deferred
- M5 does **not** require interactive prompting for missing details (e.g., due dates, projects).
- Tasks can be refined via Telegram lifecycle commands and/or later UI/API flows.
- A future milestone may introduce a “prompt-to-fill” conversational contract.

## Rationale
- Provides strong idempotency guarantees compatible with append-only event sourcing.
- Keeps dedup deterministic and explainable.
- Avoids prematurely introducing conversational prompting workflows.
- Preserves agent-first semantics (review queue + commands) while leaving room for stricter review enforcement later.

## Alternatives Considered
- Derive `source_ref` from extracted title/body fingerprints.
  - Rejected: changes in wording would break idempotency.

- Add a new Task status `needs_review`.
  - Rejected: status set is specified by M5 charter; label is lighter and composable.

## Consequences
- Task canonicalization logic must compute ordinals deterministically.
- `needs_review` can be used by review queue ordering (e.g., show needs_review first).
- Prompting can be layered later without breaking task identity.