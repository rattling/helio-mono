# Milestone 13 --- Calendar + Gmail Digest Integrations

## Objective

Add external integration capabilities for calendar-aware digests and email
notification delivery on top of the Milestone 12 LangGraph orchestration plane.

In this milestone, also mature LangGraph usage from baseline wiring to
full-use orchestration patterns across both existing M12 workflows and new M13
calendar/email flows.

This milestone introduces:
- LangGraph runtime maturation for existing and new workflows
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

Milestone 13 completes the orchestration maturity step by applying richer
LangGraph capabilities (checkpoint/resume, explicit interrupt points, reusable
subgraphs, and richer branching) to real user-facing flows.

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

### LangGraph-first orchestration maturity

- LangGraph remains the sole agentic orchestrator.
- Existing M12 digest/reminder flows and new M13 flows use shared graph
	primitives (not one-off linear wrappers).
- Human interrupt/approval points are supported where policy demands explicit
	intervention.

------------------------------------------------------------------------

## Milestone Scope

### 0) LangGraph Maturation (Existing + New Flows)

- Introduce reusable graph components/subgraphs for common orchestration
	concerns (policy evaluation, delivery execution, terminal/failure handling).
- Add graph checkpointing/resume support for long-running or interrupted runs.
- Add explicit interrupt points for policy-driven human intervention.
- Add richer conditional branching/fan-out patterns where needed for
	multi-source calendar processing and multi-channel delivery.
- Apply these patterns to existing M12 digest/reminder flows and all new M13
	calendar/email flows.

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

- LangGraph orchestration is used as the sole agentic execution engine for
	existing digest/reminder and new M13 flows.
- Reusable subgraphs are used for shared orchestration concerns across flows
	(policy, delivery, terminal handling).
- Checkpoint/resume works for at least one representative interrupted flow.
- Policy-driven interrupt/escalation points are explicit and operator-visible.
- Google and Zoho calendar reads are operational when configured.
- Calendar events are normalized into a single internal contract.
- Monday and weekday digest semantics match declared policy.
- Telegram and email delivery both work when configured.
- Runs remain policy-bounded and fail closed when out-of-scope.
- All integration and delivery outcomes are traceable in durable artifacts/events.

------------------------------------------------------------------------

## How to Test (Operator Checklist)

1. Validate LangGraph maturity behaviors
	- Confirm existing M12 workflows and new M13 workflows run through shared graph
	  components/subgraphs
	- Induce an interrupt path and verify operator-visible pause/escalation
	- Resume from checkpoint and confirm terminal state is correct and evented

2. Validate provider connectivity
	- Configure Google + Zoho credentials
	- Confirm successful reads and explicit failure handling

3. Validate normalization contract
	- Verify merged normalized payload shape and field behavior
	- Verify missing/partial provider fields degrade safely

4. Validate digest schedule semantics
	- Simulate Monday and confirm weekly+day-ahead output
	- Simulate Tue-Fri and confirm day-ahead output

5. Validate delivery channels
	- Confirm Telegram delivery and logging
	- Confirm email delivery and logging
	- Confirm duplicate-send prevention within policy window

6. Validate control-plane enforcement
	- Attempt blocked external operation and verify fail-closed behavior
	- Confirm escalation signals are inspectable

7. Validate replay posture
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
