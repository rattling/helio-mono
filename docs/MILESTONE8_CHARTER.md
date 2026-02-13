# Milestone 8 --- Contextual Feedback Semantics (Usefulness, Timing Fit, Interrupt Cost)

## Objective

Upgrade Helionyx learning from coarse “good/bad signal” interpretation to a
more human-realistic model that distinguishes:

- whether a reminder/suggestion was useful,
- whether timing was right,
- and how costly the interruption was in that moment.

This milestone exists to prevent mislearning from ambiguous actions
(e.g., dismiss/snooze), and to improve personalization quality without relaxing
existing deterministic safety guardrails.

------------------------------------------------------------------------

## Why This Milestone

Current behavior can learn broad patterns, but many feedback actions are
ambiguous:

- A dismiss may mean “noise” or “thanks, handled”.
- A snooze may mean “not useful” or “very useful, wrong moment”.

If the system treats these as single-label negatives, it can drift toward the
wrong policy. Milestone 8 makes these distinctions first-class so learning is
better calibrated to real operator intent.

------------------------------------------------------------------------

## What the User Gets

By the end of this milestone, a user should experience:

- Fewer false “negative” interpretations of useful reminders
- Better timing adaptation without suppressing genuinely useful nudges
- More stable personalization behavior under ambiguous feedback
- Clear explanations that separate usefulness vs timing vs interruption effects
- Safer adaptation that changes gradually and reversibly

------------------------------------------------------------------------

## User Experience Over Time

### Week 1: Semantics become explicit

- Reminder/suggestion outcomes are interpreted through multi-signal semantics,
  not a single positive/negative axis
- Explanations begin reflecting separate factors (value, timing, interruption)

### Weeks 2--4: Better timing adaptation

- System starts retiming useful-but-badly-timed reminders instead of
  suppressing them
- “Noisy” reminders are reduced with less collateral damage to useful reminders

### Month 2+: More reliable personalization

- Personalization becomes more robust under mixed/ambiguous human behavior
- Operators see fewer surprising ranking shifts from misinterpreted feedback

------------------------------------------------------------------------

## Core Product Semantics

### First-class targets

- **Usefulness**: Did this surface help progress?
- **Timing fit**: Was this the right moment?
- **Interrupt cost**: How disruptive was this interruption in context?

### Policy principle

- These targets influence ranking/timing only inside bounded policy controls.
- Deterministic safety constraints remain authoritative.

------------------------------------------------------------------------

## Product Acceptance Criteria

- Feedback interpretation no longer assumes dismiss/snooze are always negative
- Explanations clearly identify which target(s) drove adaptation
- Useful-but-mistimed reminders are more often retimed than suppressed
- Duplicate/noise guardrails remain non-regressive
- Bounded fallback remains immediate and deterministic
- Replay evaluation includes per-target quality and confidence diagnostics

------------------------------------------------------------------------

## How to Test (Operator Checklist)

1. Validate ambiguous feedback handling
	- Create scenarios for:
	  - dismiss + immediate completion
	  - dismiss + no follow-up
	  - snooze + later completion
	- Confirm interpretations differ by context, not by action label alone

2. Validate target-specific explanations
	- Inspect attention/reminder explanation payloads
	- Confirm each decision can show usefulness/timing/interrupt factors

3. Validate timing adaptation behavior
	- Re-run reminder scenarios across different windows
	- Confirm useful reminders shift timing before suppression

4. Validate bounded safety behavior
	- Confirm deterministic constraints are still never overridden
	- Confirm low-confidence cases fall back safely

5. Validate replay diagnostics
	- Run replay evaluation report
	- Confirm per-target metrics/checks are present and interpretable

6. Regression sanity check
	- Confirm existing task APIs, attention endpoints, and reminder flows still work

------------------------------------------------------------------------

## Implementation Scope (Product-Facing)

### Feedback semantics and evidence model

- Add first-class event/feature interpretation for usefulness, timing fit,
  and interrupt cost
- Introduce context-aware weak-labeling rules for ambiguous actions

### Multi-signal learning outputs

- Produce separate scores/confidence for each target
- Preserve bounded policy integration and deterministic fallback

### Explanations and diagnostics

- Expose target-level explanations in API-visible outputs
- Extend replay reports with per-target diagnostics and readiness checks

------------------------------------------------------------------------

## Non-Goals

- No autonomous task mutation or execution
- No unbounded model authority over ranking/scheduling
- No mandatory explicit user labeling workflow as a prerequisite
- No contextual bandit exploration enablement in this milestone
