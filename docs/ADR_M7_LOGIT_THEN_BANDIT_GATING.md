# Architecture Decision Record

## Title
Model Progression Strategy: Logit First, Bandit Later (Milestone 7)

## Status
Accepted

## Context
Milestone 7 requires practical personalization now, while avoiding premature
complexity and noisy online exploration. Current telemetry supports supervised
learning from explicit feedback events (shown/applied/rejected/dismissed).

The open architecture choice is whether to start directly with contextual
bandits or begin with a simpler supervised ranker.

## Decision
Adopt a **two-stage progression**:

### Stage A (Now): Logistic/linear ranker in bounded influence mode
- Use interpretable supervised scoring from replayable event features
- Deploy via shadow mode, then bounded in-bucket reordering
- No exploration actions that violate deterministic ordering constraints

### Stage B (Later): Contextual bandit under strict gates
- Introduce exploration only after Stage A quality and calibration stabilize
- Exploration remains bounded inside deterministic safety buckets
- Operator controls can disable exploration independently from scoring

Bandit activation requires passing all gates for at least one stable window.

## Rationale
Starting with logit provides:
- Fast implementation and operational clarity
- Easier calibration and debugging
- Lower risk under sparse or skewed feedback

Deferring bandits avoids premature exploration cost and protects user trust.
Bandits become valuable only once feedback volume and quality are demonstrably
sufficient.

## Alternatives Considered
- Bandit-first rollout
  - Potentially faster adaptation, but higher risk and harder diagnosis early

- Keep only supervised scoring indefinitely
  - Lower operational risk, but misses long-term exploration gains

## Consequences
- Stage A can deliver immediate incremental UX improvements
- Stage B introduces additional infra for exploration policy and regret tracking
- Requires explicit readiness metrics for progression decisions

## Stage B Readiness Gates
All must pass before enabling contextual bandit exploration:

1. Minimum interaction volume in rolling window (suggestion/reminder feedback)
2. Stable or improved acceptance rate vs deterministic baseline
3. No regression in duplicate reminder/noise proxy metrics
4. Confidence calibration within acceptable error bound
5. Verified one-command rollback to Stage A behavior

If any gate fails, remain in Stage A and continue data collection.
