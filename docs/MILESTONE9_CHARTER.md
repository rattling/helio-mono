# Milestone 9 --- Helionyx UI Foundation (Tasks + Control Room)

## Objective

Deliver the first general-purpose Helionyx web UI focused on day-to-day utility
and transparency.

This milestone establishes a practical operator surface for:

- reliable task management (create, view, edit, complete), and
- a read-only Control Room that makes system behavior inspectable.

The goal is to make Helionyx operationally usable from UI while preserving the
existing design principle: core logic remains server-authoritative and shared
across interaction surfaces (UI, Telegram, and future channels).

------------------------------------------------------------------------

## Why This Milestone

Current usage is API/script/Telegram-heavy. That supports power users, but it
does not yet provide a single, transparent, always-available interface for
general operation and interrogation of system behavior.

Milestone 9 creates that foundation without overreaching into experimental Lab
write controls.

------------------------------------------------------------------------

## What the User Gets

By the end of this milestone, a user should experience:

- A usable web UI for core task management workflows
- Clear visibility into system health/readiness and attention outputs
- Explainable ranking visibility (why items are surfaced)
- Confidence that UI behavior remains aligned with Telegram/API behavior
- A stable base for the next milestone’s Lab capabilities

------------------------------------------------------------------------

## User Experience Over Time

### Week 1: UI access to core workflows

- User can list tasks, create tasks, edit tasks, and mark tasks complete
- Core task state transitions are available without scripts

### Weeks 2--4: Transparency-first control room

- User can inspect health/readiness state from one place
- User can inspect attention “today/week” outputs and rationale
- User can interrogate behavior without guessing hidden logic

### Month 2+: Foundation for advanced operator controls

- UI structure supports adding Lab visibility and bounded controls in Milestone 10
- Multi-surface consistency remains preserved through API-first integration

------------------------------------------------------------------------

## Core Product Semantics

### UI architecture posture

- Frontend is thin and API-first
- Domain decisions remain backend-authoritative
- Frontend may derive presentation-only state, not policy decisions

### Transparency principle

- Every surfaced task/attention decision should be inspectable through
  user-visible explanation or traceable API output
- Control Room is read-only in this milestone

------------------------------------------------------------------------

## Product Acceptance Criteria

- User can perform task CRUD-style operations through UI for canonical tasks
- User can complete and snooze tasks from UI flows
- Control Room shows health/readiness and attention snapshots
- Attention/ranking outputs shown in UI include explainability fields
- No divergence of core decision logic between UI and Telegram/API paths
- System remains runnable and stable under existing deployment assumptions

------------------------------------------------------------------------

## How to Test (Operator Checklist)

1. Validate task management end-to-end
	- Create task, edit fields, complete task, and snooze task
	- Confirm task state changes are reflected in API and UI views

2. Validate task consistency with existing surfaces
	- Perform equivalent action via Telegram/API where applicable
	- Confirm resulting task/projection state is consistent

3. Validate Control Room system visibility
	- Inspect health/readiness and verify values are current
	- Inspect attention today/week and confirm data freshness

4. Validate transparency payloads
	- Open surfaced/ranked items and inspect explanation details
	- Confirm rationale aligns with backend ranking factors

5. Validate regression stability
	- Run existing API tests for tasks/attention/health
	- Confirm no regressions in core service behavior

------------------------------------------------------------------------

## Implementation Scope (Product-Facing)

### UI foundation

- Introduce first web application surface and app shell
- Define primary navigation for Tasks and Control Room
- Establish typed API client boundaries for UI integration

### Task management

- Task list + detail views
- Task create/edit/complete/snooze interactions
- Basic filtering/sorting ergonomics required for practical usage

### Control Room (read-only)

- Health/readiness panel
- Attention “today/week” visibility
- Ranking explanation visibility for surfaced items

------------------------------------------------------------------------

## Non-Goals

- No Lab write controls or model configuration editing
- No experiment orchestration UI
- No full auth/RBAC hardening for multi-user internet deployment
- No migration of core policy logic into frontend code
