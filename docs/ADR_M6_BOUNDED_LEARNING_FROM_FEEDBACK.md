# Architecture Decision Record

## Title
Bounded Learning Loop for Attention and Planning (Milestone 6)

## Status
Accepted

## Context
Milestone 6 combines attention workflows (daily/weekly digests, urgent reminders,
stale prompts) with planning assistance (dependency and split suggestions).

The system currently relies on bounded LLM interpretation and deterministic task
logic. We need to improve relevance over time from user feedback without creating
opaque, brittle, or autonomous behavior.

Key constraints from project and architecture posture:
- Human authority remains absolute
- Event log is append-only source of truth
- Decision surfaces must be explicit and inspectable
- Existing runnable entry points and APIs remain stable

## Decision
Adopt a **bounded learning architecture** where models influence ranking and
suggestion ordering, while deterministic policy and explicit user acceptance
control state mutation.

Specifically:
1. LLMs generate bounded, explainable candidate suggestions
2. Deterministic guards enforce hard constraints (acyclic deps, explicit apply,
   anti-spam rules, no autonomous state mutation)
3. A learned scorer/ranker personalizes ordering and reminder relevance from
   event-log feedback
4. Low-confidence or conflicting cases fall back to deterministic heuristics
5. Model rollout is staged: offline replay → shadow mode → gated production

## Rationale
This preserves Helionyx principles while adding learning value:
- Safety: models cannot directly execute or mutate tasks
- Durability: all training and evaluation data derives from append-only events
- Debuggability: every score and suggestion remains explainable and replayable
- Adaptation: ranking quality can improve as user preferences emerge over time

This avoids brittle "all-ML" task automation while still improving usefulness.

## Alternatives Considered
- Pure deterministic heuristics only
  - Pros: simplest, highly predictable
  - Cons: weak personalization, plateaus in relevance

- End-to-end autonomous LLM planning/execution
  - Pros: potentially powerful automation
  - Cons: violates authority/safety posture, low reproducibility, hard rollback

- Full RL/recommender stack from day one
  - Pros: long-term potential optimization
  - Cons: high complexity, delayed value, unstable under sparse feedback

## Architecture and Boundaries

### Decision Surface Matrix
- **Extraction/Proposal (LLM + prompts)**
  - Output: candidate structured suggestions + rationale
  - Authority: propose only

- **Policy/Guards (deterministic service logic)**
  - Output: allowed/disallowed, conflict checks, anti-spam gating
  - Authority: enforce invariants

- **Learning Ranker (ML service/module)**
  - Output: score, rank, confidence, feature attribution summary
  - Authority: reorder candidate presentation only

- **Apply Action (explicit user/API command)**
  - Output: event-log mutation via accepted command only
  - Authority: final state transition

### Contract Expectations
For each suggestion/reminder candidate, include:
- `candidate_id`
- `candidate_type` (reminder, dependency_suggestion, split_suggestion, etc.)
- `deterministic_reason`
- `model_score` (optional if model enabled)
- `model_confidence` (optional)
- `explanation` (human-readable)
- `policy_flags` (guard checks)

## Learning Data Model

### Feedback Events (append-only)
Record as first-class events:
- suggestion_shown
- suggestion_applied
- suggestion_rejected
- suggestion_edited_before_apply
- reminder_sent
- reminder_dismissed
- reminder_snoozed
- task_completed
- task_reopened

Each event must capture timestamp, actor, task/suggestion reference, and context
needed for replay.

### Initial Feature Families
- Task features: priority, due proximity, age, blocked state, stale indicators
- Behavioral features: prior acceptance/rejection rates by suggestion type
- Temporal features: time-of-day/day-of-week interactions
- Workload features: queue depth, overdue count, blocked ratio

No hidden feature sources are allowed in v1. Feature extraction must be
reconstructable from event/API-visible state.

## Model Strategy

### Phase 0 (Baseline)
Deterministic urgency + static ranking, already explainable.

### Phase 1 (Personalized Ranking)
Use a simple interpretable ranker (logistic regression or gradient-boosted trees)
for:
- attention queue ordering
- reminder eligibility ranking
- suggestion ordering

### Phase 2 (Optional)
Segment-specific models or contextual bandit exploration under strict gates.

Deep RL and opaque sequence planning are explicitly out of scope for this
milestone.

## Evaluation and Rollout

### Offline Evaluation (required)
Replay historical event windows and compare against deterministic baseline.

Primary product metrics:
- suggestion acceptance rate
- duplicate reminder rate
- median time-to-complete after reminder/suggestion
- reopen rate after suggestion apply
- backlog burn-down trend

### Shadow Mode (required)
Run model scoring in production without affecting ordering; log deltas and
counterfactual outcomes.

### Production Gates
Enable model influence only when:
- no regression on duplicate reminder rate
- no material drop in acceptance rate
- deterministic fallback path verified
- observability dashboards and rollback switch are in place

## Safety and Failure Handling
- If feature extraction fails, use deterministic ranking only
- If model service is unavailable, use deterministic ranking only
- If confidence below threshold, do not override deterministic ordering
- Never auto-apply task changes from model outputs
- Record all model versions and scoring decisions for audit and replay

## Consequences

### Positive
- Improves relevance over time with bounded risk
- Preserves human control and explicit decision boundaries
- Keeps behavior explainable for debugging and QA

### Costs / Risks
- Additional complexity in telemetry and evaluation pipeline
- Need ongoing monitoring to avoid behavior drift
- Sparse feedback periods may limit learning signal quality

### Follow-on Work
- Define event schema additions in contracts
- Add shadow-mode instrumentation and replay tooling
- Add operator runbook for model rollout/rollback
