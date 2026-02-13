# Milestone 11 --- Helionyx Lab (Learning, LLMs, and Controlled Experimentation)

## Objective

Extend the UI foundation with a dedicated Lab that makes learning behavior,
model influence, and configuration observable and operable under explicit
guardrails.

This milestone introduces Lab read visibility first and bounded write controls
second, preserving the project’s core principle: transparent, human-authorized,
reversible adaptation.

------------------------------------------------------------------------

## Why This Milestone

After Milestone 10 and 10A, users can deeply interrogate system behavior via
Data Explorer (including guided insights), but still cannot fully inspect and
govern learning internals from a dedicated operator Lab.

Milestone 11 turns learning and model behavior into first-class operator
surfaces so users can understand and shape adaptation rather than treating it as
a black box.

------------------------------------------------------------------------

## What the User Gets

By the end of this milestone, a user should experience:

- A Lab view of personalization and feedback-semantic outcomes over time
- Visibility into model influence, confidence, and bounded fallback behavior
- Visibility into LLM operating configuration and active policy mode
- Carefully scoped write controls for safe operator-driven changes
- Controlled experiment runs with inspectable outcomes and audit trail
- A clear rollback path back to deterministic-safe operating posture

------------------------------------------------------------------------

## User Experience Over Time

### Week 1: Lab visibility baseline

- User can inspect key learning metrics and trend views
- User can inspect mode/config snapshots and model-influence diagnostics
- User can identify where deterministic fallback is currently active

### Weeks 2--4: Bounded operator controls

- User can apply limited write operations (mode toggles and selected thresholds)
- Changes are explicit, auditable, and reversible
- Safety invariants are enforced on every write path

### Month 2+: Experiment-assisted optimization

- User can trigger approved replay/experiment workflows from UI
- User can inspect results and decide whether to keep or roll back changes
- Experiment outputs are compared against baseline policy posture before apply

------------------------------------------------------------------------

## Core Product Semantics

### Human authority

- Learning remains assistive, not autonomous
- Operator remains final authority on enabling, changing, and rolling back
  learning influence

### Bounded adaptation

- Deterministic safety constraints remain authoritative
- Low-confidence paths must remain conservative and fall back predictably

### Write control discipline

- Lab write actions are narrow, intentional, and auditable
- No hidden background policy mutation outside approved control surface
- Each write action must publish an auditable event with actor, before/after,
  rationale, and rollback metadata

------------------------------------------------------------------------

## Product Acceptance Criteria

- Lab presents interpretable learning and behavior diagnostics over time
- Active personalization mode and key controls are clearly visible
- Bounded write actions can be executed and are durably audited
- Experiment/replay execution results are visible and comparable
- Rollback to safe deterministic posture remains immediate and reliable
- Existing tasks/control-room/data-explorer functionality remains non-regressive
- Lab actions expose explicit “why this is safe” constraints to operators

------------------------------------------------------------------------

## How to Test (Operator Checklist)

1. Validate Lab read visibility
	- Inspect usefulness/timing/interrupt trends and confidence indicators
	- Confirm displayed values align with backend outputs/events

2. Validate config transparency
	- Inspect current learning mode and key runtime control values
	- Confirm UI reflects effective backend configuration

3. Validate bounded write controls
	- Toggle approved mode/control values through UI
	- Confirm changes take effect, are logged, and can be reverted
	- Confirm disallowed values are rejected with clear reason

4. Validate experiment workflow
	- Trigger approved replay/experiment run from UI
	- Confirm run status and resulting diagnostics are visible and interpretable
	- Confirm apply/rollback decision point exists after run

5. Validate safety/rollback behavior
	- Force conservative mode/fallback and verify deterministic behavior
	- Confirm no safety-constraint violations under changed settings

6. Validate regression coverage
	- Re-run Milestone 10/10A Data Explorer checks and Milestone 9 task/control-room checks
	- Confirm no regressions in existing surfaces

------------------------------------------------------------------------

## Implementation Scope (Product-Facing)

### Lab read dashboards

- Learning outcome trends and confidence visibility
- Model influence diagnostics and bounded-vs-deterministic indicators
- LLM/config snapshot visibility relevant to operator decisions

### Lab write controls (bounded)

- Safe mode toggles and selected parameter adjustments
- Explicit change confirmation and audit/event capture
- One-step rollback path to deterministic-safe baseline
- Server-side policy guardrails with deterministic rejection reasons

### Experiment operations

- UI-triggered execution for approved replay/evaluation workflows
- Run history and result inspection surfaces
- Explicit apply/rollback decision point after experiment completion

------------------------------------------------------------------------

## Non-Goals

- No unrestricted arbitrary model/code execution from UI
- No unbounded policy mutation or autonomous planning authority
- No multi-tenant policy management or enterprise RBAC expansion
- No replacement of deterministic safety rules with opaque model decisions
