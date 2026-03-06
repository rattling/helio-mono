# Architecture Decision Record

## Title
Milestone 9 Control Room: Explicit Transparency Read Model (Read-Only)

## Status
Accepted

## Context
Milestone 9 requires a Control Room where operators can interrogate system
state and understand why Helionyx surfaces tasks/attention outputs.

Current APIs expose health and attention endpoints, but they are not yet framed
as a consolidated operator transparency model. Exposing raw internals directly
to UI risks unstable coupling and inconsistent interpretation.

Milestone 9 scope also excludes Lab write controls and broader operational
mutation from UI.

## Decision
Milestone 9 introduces/uses an explicit Control Room read model that is
read-only and operator-focused.

The read model must cover:

- service health/readiness,
- current attention snapshots (today/week), and
- ranking/explanation fields required to inspect why items are surfaced.

The web UI will consume this transparency model as a stable API surface.
Write/actuation controls remain out of scope for Milestone 9 and are deferred
to Milestone 10 Lab architecture.

## Rationale
- Makes transparency a first-class product capability, not incidental output.
- Avoids coupling the UI to low-level storage/event internals.
- Supports future extension to Lab surfaces without reworking foundational UI
  navigation and data contracts.
- Preserves scope discipline by separating read transparency from write control.

## Alternatives Considered
- Expose raw event store and internal service payloads directly to frontend.
- Delay Control Room until full Lab/write architecture is available.

## Consequences
- Requires a clear operator-facing API contract for transparency data.
- Some backend aggregation/read-model work is needed in Milestone 9.
- Operators gain earlier trust and inspectability before introducing writes.
- Milestone 10 can build on this model for bounded control operations.
