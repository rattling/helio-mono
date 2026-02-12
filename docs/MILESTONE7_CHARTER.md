# Milestone 7 --- Personalization with Guardrails (Learning That Stays Bounded)

**Architecture ADRs**:
- [ADR_M7_BOUNDED_PERSONALIZATION_POLICY.md](ADR_M7_BOUNDED_PERSONALIZATION_POLICY.md)
- [ADR_M7_LOGIT_THEN_BANDIT_GATING.md](ADR_M7_LOGIT_THEN_BANDIT_GATING.md)

## Objective

Make Helionyx feel increasingly personalized over time while preserving user
control, predictability, and explainability.

This milestone upgrades the assistant from “generally useful” to “useful in my
actual patterns” without allowing opaque or autonomous behavior.

------------------------------------------------------------------------

## What the User Gets

By the end of this milestone, a user should experience:

- Better priority ordering based on what they actually accept, defer, or reject
- Fewer low-value reminders over time
- More relevant planning suggestions for recurring work patterns
- Clear explanations for why something moved up or down
- A stable fallback experience when learning is disabled or uncertain

------------------------------------------------------------------------

## User Experience Over Time

### Week 1: Baseline + Observation

- System behavior remains mostly deterministic
- User sees the same reliable digests/reminders from Milestone 6
- Learning runs in the background (shadow evaluation) with no disruptive changes

### Weeks 2--4: Bounded Influence

- Personalized ranking can adjust ordering only within safe buckets
- Hard rules still win (due-soon, blocked, and urgent constraints)
- User starts noticing that “top items” better match actual behavior

### Month 2+: Continuous Improvement

- Reminder quality improves (less noise, better timing)
- Suggestion quality improves for repeated task shapes and workflow patterns
- If model confidence drops, system automatically leans back to deterministic mode

------------------------------------------------------------------------

## Product Acceptance Criteria

- Personalization improves acceptance rate of surfaced items vs baseline
- Reminder duplicate/noise rate does not increase
- Deterministic safety constraints are never violated
- Every personalized ranking decision is explainable and inspectable
- Learning can be disabled instantly with predictable fallback behavior
- Replay evaluation gates are required before any expansion of model influence

------------------------------------------------------------------------

## How to Test (Operator Checklist)

1. Verify deterministic baseline integrity
	- Run attention queues with learning disabled
	- Confirm outputs match Milestone 6 behavior

2. Verify shadow learning pass
	- Enable shadow mode only
	- Confirm model scores are logged but do not affect final ordering
	- Confirm replay report is generated and metrics are populated

3. Verify bounded influence mode
	- Enable bounded personalization
	- Confirm reordering occurs only within allowed urgency buckets
	- Confirm hard-rule items are never demoted below safety constraints

4. Verify explanation and auditability
	- For a re-ranked item, inspect explanation payload and event trail
	- Confirm operator can identify deterministic factors + learned factors

5. Verify rollback behavior
	- Disable learning flags at runtime
	- Confirm immediate return to deterministic ordering and reminder policy

6. Verify quality gates
	- Run replay evaluation against historical window
	- Confirm gate thresholds pass before enabling broader influence

------------------------------------------------------------------------

## Implementation Scope (Product-Facing)

### Ranking and Attention

- Introduce bounded personalized ranking layer
- Keep deterministic policy as authority and fallback
- Add confidence-aware blending controls

### Suggestions and Reminders

- Improve suggestion relevance from explicit user feedback loops
- Improve reminder timing/noise through guarded adaptation
- Preserve anti-spam and safety invariants from M6

### Evaluation and Controls

- Expand replay metrics for acceptance, regret/noise proxies, and stability
- Add rollout gates and progressive enablement controls
- Add one-command rollback to deterministic-only mode

------------------------------------------------------------------------

## Non-Goals

- No fully autonomous planning or task mutation
- No black-box reordering that cannot be explained
- No replacement of deterministic safety rules with model output
- No multi-user/global personalization scope in this milestone
