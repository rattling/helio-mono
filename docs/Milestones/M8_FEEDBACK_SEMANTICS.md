# M8 Feedback Semantics (First-Class Targets)

## Purpose

Define deterministic, context-aware weak-label semantics for ambiguous feedback.
These semantics avoid collapsing all actions into a single positive/negative axis.

## Targets

- **Usefulness**: did the reminder/suggestion help progress?
- **Timing fit**: was this the right moment?
- **Interrupt cost**: how disruptive was this at that moment?

## Rule Philosophy

- Actions are not labels; they are evidence.
- Evidence interpretation must include context (follow-up action timing, snooze intent).
- Outputs should be replayable from event-visible state.

## Baseline Weak-Label Rules

### Dismissed

- **Dismiss + quick follow-up action** (e.g., complete/update within 60m)
  - usefulness: high
  - timing fit: medium/high
  - interrupt cost: medium
  - interpretation: likely useful reminder leading to action

- **Dismiss + no follow-up action**
  - usefulness: low
  - timing fit: medium/low
  - interrupt cost: low/medium
  - interpretation: likely low-value reminder

### Snoozed

- usefulness: medium/high by default
- timing fit: low
- interrupt cost: medium/high
- interpretation: useful-but-mistimed signal (retime preferred before suppress)

Short snoozes (e.g., <=15m) increase likelihood of usefulness and high interrupt cost.

## Policy Guidance

- Keep deterministic guardrails authoritative.
- Prefer **retime** action when usefulness is high but timing fit is low.
- Prefer **deprioritize/suppress** only when usefulness remains low and interrupt cost is high over repeated observations.

## Non-Goals

- No assumption that explicit user actions are ground truth labels.
- No autonomous mutation of task state.
- No unbounded policy authority from model outputs.
