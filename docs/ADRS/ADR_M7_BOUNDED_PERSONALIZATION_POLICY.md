# Architecture Decision Record

## Title
Bounded Personalized Ranking Policy (Milestone 7)

## Status
Accepted

## Context
Milestone 6 introduced attention queues and suggestion workflows with deterministic
authority and shadow scoring telemetry. Milestone 7 aims to improve relevance
over time from user feedback without violating Helionyx invariants:

- Human authority remains absolute
- Deterministic policy remains inspectable and reproducible
- Event log remains the source of truth
- Model behavior must be explainable and reversible

We need a production policy for when and how learned scoring can influence user-
facing ordering.

## Decision
Adopt a **bounded personalization policy**:

1. Deterministic policy remains the primary authority for eligibility and safety
2. Learned score can reorder items only within predefined deterministic buckets
3. Hard constraints (urgent/due-soon/blocked safety rules) are non-overridable
4. Confidence threshold is required before any learned reordering
5. On failure, timeout, or low confidence, fallback is deterministic-only
6. Every personalized rank decision must include explanation fields and model
   metadata in the event trail

## Rationale
This maximizes user value while preserving control:

- Personalization improves ranking quality over time
- Deterministic buckets keep behavior predictable and safe
- Explainable bounded influence supports trust and QA
- Rollback to deterministic mode is immediate and low-risk

## Alternatives Considered
- Deterministic-only forever
  - Simpler operations but no long-term adaptation

- Unbounded model-first ranking
  - Higher potential adaptation but violates safety/inspectability posture

- Full autonomous planning and mutation
  - Out of scope and incompatible with authority model

## Consequences
- Requires explicit bucket definitions and invariant tests
- Requires model confidence calibration and runtime controls
- Improves acceptance relevance if feedback volume is sufficient
- Maintains stable user experience under degraded model conditions
