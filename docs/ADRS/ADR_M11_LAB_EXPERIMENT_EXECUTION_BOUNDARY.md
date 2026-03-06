# Architecture Decision Record

## Title
Milestone 11 Lab: Two-Phase Experiment Workflow (Run Then Explicit Apply/Rollback)

## Status
Accepted

## Context
Lab needs experiment/replay capabilities so operators can evaluate policy
changes. If experiment execution implicitly mutates production posture, users
lose control over causality and rollback clarity.

## Decision
Experiment operations will follow a strict two-phase workflow:
1. **Run phase**: execute approved replay/evaluation and produce inspectable results.
2. **Decision phase**: operator explicitly chooses apply or rollback/no-op.

Key boundary rules:
- Running experiments does not mutate active policy by default.
- Apply action is explicit, auditable, and reversible.
- Results include baseline comparison fields (before vs candidate outcome).
- Apply eligibility can be blocked when safety thresholds are violated.

## Rationale
- Separates observation from mutation.
- Preserves deterministic control over policy state.
- Makes experiment causality explainable and reviewable.
- Supports safer iteration by requiring explicit operator intent.

## Alternatives Considered
- Auto-apply best-scoring experiment result.
- Manual experiment workflow outside product UI.
- Single-phase run-and-apply operation.

## Consequences
- Requires experiment run/result contracts and status tracking.
- Requires apply/rollback endpoints with policy guards.
- Adds UX steps but improves safety and trust.
