# Milestone 13 --- Calendar + Gmail Digest Integrations

## Objective

Add external integration capabilities for calendar-aware digests and email
notification delivery on top of the Milestone 12 LangGraph orchestration plane.

This milestone introduces:
- Google Calendar and Zoho Calendar ingestion (read-first)
- Digest policy expansion for calendar-aware weekly/day-ahead views
- Email delivery channel (Gmail SMTP-compatible path)
- Full ledger traceability and control-plane enforcement for external calls

------------------------------------------------------------------------

## Why This Milestone

Milestone 12 makes orchestration explicit and bounded for existing Helionyx
workflows. Milestone 13 applies that orchestration capability to high-value
external integrations while preserving human authority and inspectability.

This sequencing reduces risk: first stabilize orchestration internals, then add
external systems and side effects.

------------------------------------------------------------------------

## What the User Gets

By the end of this milestone, the user should experience:

- Monday morning digest with weekly lookahead + day-ahead context
- Tuesday-Friday morning day-ahead digest
- Digest delivery through Telegram and email
- Inputs merged from Google and Zoho calendars under one normalized contract
- Clear evidence of how each digest was generated and delivered

------------------------------------------------------------------------

## Core Product Semantics

### Read-first external integration

- Calendar access is read-only in this milestone.
- No autonomous event creation/edits/deletes.
- Any future write scope requires explicit policy and approvals.

### Control-plane bounded autonomy

- External adapter calls are policy-gated and auditable.
- Out-of-policy operations fail closed.
- Recovery/escalation paths are explicit and inspectable.

### Ledger-first traceability

- Calendar fetches, normalization outcomes, digest composition decisions,
  and delivery results are durably represented via events/artifacts.

------------------------------------------------------------------------

## Milestone Scope

### 1) Google + Zoho Calendar Adapters

- Add adapters for Google Calendar and Zoho Calendar.
- Introduce normalized internal calendar-event contract.
- Implement provider error handling with explicit degradation states.

### 2) Calendar-Aware Digest Composition

- Merge normalized events into digest context.
- Monday schedule: weekly+day-ahead digest.
- Tuesday-Friday schedule: day-ahead digest.
- Preserve deterministic fallback templates if enrichment fails.

### 3) Delivery Channels

- Continue Telegram delivery path.
- Add email delivery via SMTP with Gmail-compatible setup.
- Keep channel rendering explicit and testable per contract.

### 4) Control/Visibility Surfaces

- Expose external-integration run visibility in read surfaces.
- Record policy boundary checks and escalation reasons.
- Keep replay/rebuild posture intact from append-only history.

------------------------------------------------------------------------

## Product Acceptance Criteria

- Google and Zoho calendar reads are operational when configured.
- Calendar events are normalized into a single internal contract.
- Monday and weekday digest semantics match declared policy.
- Telegram and email delivery both work when configured.
- Runs remain policy-bounded and fail closed when out-of-scope.
- All integration and delivery outcomes are traceable in durable artifacts/events.

------------------------------------------------------------------------

## How to Test (Operator Checklist)

1. Validate provider connectivity
	- Configure Google + Zoho credentials
	- Confirm successful reads and explicit failure handling

2. Validate normalization contract
	- Verify merged normalized payload shape and field behavior
	- Verify missing/partial provider fields degrade safely

3. Validate digest schedule semantics
	- Simulate Monday and confirm weekly+day-ahead output
	- Simulate Tue-Fri and confirm day-ahead output

4. Validate delivery channels
	- Confirm Telegram delivery and logging
	- Confirm email delivery and logging
	- Confirm duplicate-send prevention within policy window

5. Validate control-plane enforcement
	- Attempt blocked external operation and verify fail-closed behavior
	- Confirm escalation signals are inspectable

6. Validate replay posture
	- Rebuild projections from event log and confirm run reconstruction

------------------------------------------------------------------------

## Non-Goals

- No autonomous calendar writes (create/update/delete)
- No broad unconstrained autonomous multi-agent behavior
- No hidden integration behavior outside auditable control-plane policy

------------------------------------------------------------------------

## Risks and Mitigations

- **Risk: Provider auth/config complexity**
	- Mitigation: Strong config validation + explicit degraded mode.

- **Risk: Inconsistent provider payloads**
	- Mitigation: Strict normalization contract + robust missing-field handling.

- **Risk: Delivery reliability variance across channels**
	- Mitigation: Shared retry/dedup contract + durable delivery outcome events.

------------------------------------------------------------------------

## Forward Path (Post-M13)

After this milestone, Helionyx can evaluate:
- approval-gated calendar write actions,
- richer planning agents using calendar/task context,
- broader external tool ecosystem under the same control-plane model.
