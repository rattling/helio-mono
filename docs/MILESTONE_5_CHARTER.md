# Milestone 5 --- Task Core + Agent-First Semantics

## Objective

Establish a durable, idempotent, agent-operable task system that
replaces Google Calendar Tasks at the semantic level (not time
allocation yet).

------------------------------------------------------------------------

## Core Capabilities

-   Canonical Task object with lifecycle + provenance
-   Idempotent ingest from Telegram (and future surfaces)
-   Deterministic deduplication with auditability
-   Passive stale detection
-   Fully agent-readable and human-legible state

------------------------------------------------------------------------

## Data Model (Canonical Task)

-   task_id (UUID)
-   title (short human-readable string)
-   body (optional detail)
-   status ∈ {open, blocked, in_progress, done, cancelled, snoozed}
-   priority ∈ {p0, p1, p2, p3}
-   due_at (optional timestamp)
-   do_not_start_before (optional timestamp)
-   created_at, updated_at, completed_at
-   source (telegram \| ui \| api \| other)
-   source_ref (idempotency key)
-   dedup_group_id (optional)
-   labels\[\]
-   project (optional)
-   blocked_by\[\] (task_ids)
-   agent_notes (internal scratchpad)
-   explanations\[\] ({ts, actor, action, rationale})

All changes must be event-logged.

------------------------------------------------------------------------

## APIs

POST /tasks/ingest\
GET /tasks\
GET /tasks/{id}\
PATCH /tasks/{id}\
POST /tasks/{id}/complete\
POST /tasks/{id}/snooze\
POST /tasks/{id}/link\
GET /tasks/review/queue

All ingest operations must be idempotent via source_ref.

------------------------------------------------------------------------

## Telegram Commands

-   done `<id>`{=html}
-   snooze `<id>`{=html} 2d
-   priority `<id>`{=html} p1
-   show today
-   show stale

------------------------------------------------------------------------

## Acceptance Criteria

-   Ingest is idempotent
-   Dedup decisions are logged and explainable
-   Telegram can fully operate lifecycle
-   Review queue produces meaningful ordered output

------------------------------------------------------------------------

## Non-Goals

-   No calendar scheduling
-   No automatic rescheduling
-   No deep dependency inference
