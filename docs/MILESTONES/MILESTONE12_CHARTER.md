# Milestone 12 --- LangGraph Orchestration Plane (Current Capabilities)

## Objective

Establish an explicit **agentic orchestration plane** (LangGraph-centric) that is
safely integrated with the Helionyx event substrate and control plane, using
existing Helionyx capabilities first.

This milestone introduces:
- LangGraph orchestration for existing digest/reminder workflows
- Explicit control-plane guardrails for bounded agent responsibilities
- Ledger-visible run lifecycle and node outcomes
- Strict, inspectable control boundaries for agent responsibilities

The target outcome is not “more autonomy at any cost,” but **bounded autonomy
with durable transparency**.

------------------------------------------------------------------------

## Why This Milestone

Helionyx already has strong event durability, operator authority, and control-room
visibility. However, agentic execution remains implicit and fragmented across
service-level logic.

To scale to richer workflows (planning, proactive support, later calendar/email
integrations), Helionyx needs:
- a first-class orchestration layer,
- first-class policy boundaries for what agents can and cannot do,
- and first-class run traceability in the ledger.

Milestone 12 makes agentic behavior explicit, governable, and auditable.

------------------------------------------------------------------------

## What the User Gets

By the end of this milestone, the user should experience:

- Existing weekly/daily digest and urgent reminder flows executed through
	LangGraph orchestration
- Clear inspection of how each run was produced (inputs, steps, decisions)
- Confidence that agents operate within strict role/task/subtask boundaries

------------------------------------------------------------------------

## Core Product Semantics

### LangGraph as orchestration center (not optional)

- LangGraph is the default orchestration plane for agentic workflows in this and
  future milestone features.
- Deterministic services remain authoritative for I/O, storage, delivery,
  and enforcement.
- Agent nodes coordinate and reason; deterministic adapters execute side effects.

### Ledger-first execution

- Every meaningful orchestration run is durably represented in the event log.
- Graph runs are replayable and inspectable through projections.
- Failure, retry, fallback, and operator override paths are recorded explicitly.

### Bounded autonomy under control-plane policy

- Agents are assigned explicit responsibilities (role profile + tool scope +
  write scope + budget/time constraints).
- Agents may autonomously complete work only inside declared task/subtask bounds.
- Out-of-bounds actions must fail closed and surface clear escalation signals.

### Human authority and reversible operations

- Human remains final authority.
- In this milestone, scope is limited to current Helionyx features.
- Future external integrations and writes require explicit control-plane
	policies and approval gates in subsequent milestones.

------------------------------------------------------------------------

## Milestone Scope

### 1) Orchestration Plane Baseline

- Introduce LangGraph runtime wiring as a first-class service in Helionyx.
- Define graph state contract for scheduled digest workflows.
- Add explicit checkpoints, retries, and deterministic fallback nodes.
- Expose orchestration run visibility to existing read surfaces (Control Room /
  Explorer contracts as appropriate).

### 2) Existing Attention Flows via Graph

- Migrate current daily digest flow to graph orchestration.
- Migrate current weekly digest flow to graph orchestration.
- Migrate urgent reminder flow to graph orchestration.
- Preserve existing user-visible behavior and deterministic output constraints.

### 3) Control Plane for Agent Responsibilities

- Policy surface declaring allowed tools, max autonomy scope, and escalation
  behavior for digest agents.
- Guardrails for task/subtask bounds, time budget, and side-effect permissions.
- Operator-visible explanation of why a run is safe/blocked/escalated.

------------------------------------------------------------------------

## Product Acceptance Criteria

- LangGraph orchestration is used for existing digest/reminder workflows by default.
- Existing schedule semantics remain non-regressive.
- Every run produces inspectable evidence in durable system state.
- Control-plane rules enforce bounded agent behavior and fail closed on violations.
- Existing milestone functionality remains non-regressive.

------------------------------------------------------------------------

## How to Test (Operator Checklist)

1. Validate orchestration-path visibility
	- Trigger scheduled or manual digest run
	- Confirm run state and node-level progression are inspectable
	- Confirm retries/fallbacks are visible when induced

2. Validate current flow parity
	- Validate daily digest behavior parity against pre-graph behavior
	- Validate weekly digest behavior parity against pre-graph behavior
	- Validate urgent reminder behavior parity against pre-graph behavior

3. Validate control-plane guardrails
	- Attempt out-of-policy tool/use path
	- Confirm action is blocked and escalation is recorded
	- Confirm in-policy autonomous completion succeeds

4. Validate ledger and replay posture
	- Rebuild projections from event log
	- Confirm orchestration history remains reconstructable

------------------------------------------------------------------------

## Non-Goals

- No new external integrations (calendar/email) in this milestone
- No autonomous external writes in this milestone
- No broad, unconstrained multi-agent general autonomy
- No hidden control-plane mutation outside explicit, auditable surfaces
- No changes to user-facing semantics beyond orchestration internals

------------------------------------------------------------------------

## Risks and Mitigations

- **Risk: Over-agentification of deterministic workflows**
	- Mitigation: Keep side effects and invariants in deterministic adapters.

- **Risk: Loss of explainability in multi-step orchestration**
	- Mitigation: Require run artifacts and node outcomes to be evented.

- **Risk: Excessive autonomy drift over time**
	- Mitigation: Encode explicit responsibility contracts and fail-closed enforcement.

------------------------------------------------------------------------

## Forward Path (Post-M12)

After this baseline, Helionyx can safely expand to Milestone 13 for calendar
and email capabilities, then later to:
- approval-gated external writes,
- richer planning agents,
- multi-agent task decomposition,
- and deeper Control Room governance over autonomous operations.

Each expansion must preserve ledger durability, inspectability, and human authority.
