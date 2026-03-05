# Architecture Decision Record

## Title
Milestone 5: Tasks as Canonical Object; Preserve AI Todo Inference

## Status
Accepted

## Context
Helionyx currently infers action items by extracting structured objects from messages.
In practice, this means:
- A message is ingested as a `MessageIngestedEvent`.
- Extraction emits `ObjectExtractedEvent` entries with `object_type="todo"` (and also "note"/"track").
- A SQLite projection materializes those extracted todos into a `todos` table for query + Telegram display.

Milestone 5 introduces a first-class Task system with lifecycle, provenance, idempotent ingest, deduplication, stale detection, and agent-operable commands.

We must preserve the existing user-facing value: **the system infers todos/tasks from conversational messages**.

## Decision
1. **Tasks become the canonical “action item” object going forward.**
   - Task lifecycle changes are recorded as task lifecycle events in the append-only event log.
   - Task state is queryable via projections (rebuildable from events).

2. **Existing AI-driven todo inference is preserved as an ingest surface for Tasks.**
   - The system will continue to extract todo-like items from messages.
   - Each extracted todo is *canonicalized* into a Task via an idempotent ingest pathway.

3. **Legacy `Todo` artifacts and projections remain supported in Milestone 5 (additive transition).**
   - We do not require a big-bang migration.
   - Tasks and legacy todos may coexist during M5 while surfaces are migrated.

4. **Introduce a `needs_review` stage as a label, not a lifecycle status.**
   - Newly inferred tasks MAY be tagged with `needs_review` to preserve a human/agent review gate.
   - M5 does not require blocking on review; review can be “lightweight” (non-halting) initially.

## Rationale
- Preserves the core AI value proposition while making Tasks first-class and operable.
- Maintains append-only integrity and auditability.
- Enables gradual migration of existing surfaces (`/todos` → `/tasks` and Telegram commands) without breaking existing workflows.
- Keeps the “review gate” structure available without forcing UX complexity in Milestone 5.

## Alternatives Considered
- Replace existing todo extraction with Task extraction immediately.
  - Rejected for M5: increases blast radius; risks breaking established ingestion/extraction behavior.

- Keep todos as canonical and build lifecycle features onto todo objects.
  - Rejected: would entrench a model that lacks the required provenance/idempotency/dedup semantics.

## Consequences
- M5 introduces a bridging layer: extracted todos are treated as Task ingest inputs.
- Some duplication exists temporarily (legacy `todos` projection and new `tasks` projection) unless we later unify.
- Future milestones can retire legacy todos once all surfaces read from Tasks.

## Notes / Guidance
- Prompting for missing details (interactive refinement) is explicitly deferred (see M5 idempotency/dedup ADR).