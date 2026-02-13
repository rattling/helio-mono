# Milestone 10A --- Data Explorer Guided Insights (Opinionated UX + Ad Hoc Power)

## Objective

Evolve Data Explorer from a raw interrogation tool into an insight-first operator
surface.

Milestone 10A introduces an opinionated “Guided Insights” experience that answers
what matters first, while preserving ad hoc query power for deeper inspection.

------------------------------------------------------------------------

## Why This Milestone

Milestone 10 delivered strong traceability primitives (lookup, timeline, state,
decision), but the default user journey still assumes users already know what to
ask.

Operators need the product to proactively surface notable patterns, risks, and
explanations, then allow one-click drill down into evidence.

------------------------------------------------------------------------

## What the User Gets

By the end of this milestone, a user should experience:

- A default Guided Insights view (not just raw query forms)
- A “System Pulse” summary of current operational posture
- Ranked “Notable Events” cards describing what changed and why it matters
- Structured “Why this happened” evidence summaries for key decisions
- Seamless handoff into ad hoc query mode with full context preserved

------------------------------------------------------------------------

## User Experience Over Time

### Week 1: Insight-first landing

- User lands on Guided Insights and immediately sees system posture
- User can open top notable items and inspect rationale/evidence

### Weeks 2--4: Explainability depth + workflow efficiency

- User can trace insight cards to timeline/state/decision evidence views
- User can pivot from guided cards to ad hoc queries without losing context

### Month 2+: Repeatable operational habits

- User can use saved views for recurring investigations
- Guided Insights becomes primary operational entrypoint for daily checks

------------------------------------------------------------------------

## Core Product Semantics

### Guided-first, not guided-only

- Guided Insights is the default for discoverability and operator ergonomics
- Ad hoc query remains first-class for precision and exploratory debugging

### Evidence-backed interpretation

- Every interpreted insight must link to inspectable underlying evidence
- No opaque “black box” summaries without traceability anchors

### Operator cognition optimization

- Surface high-signal changes first
- Minimize payload scanning by default
- Keep raw payload access available via progressive disclosure

------------------------------------------------------------------------

## Product Acceptance Criteria

- Data Explorer defaults to Guided Insights mode
- System Pulse shows curated, high-value health/status indicators
- Notable Events feed ranks and labels meaningful changes/risks
- Each notable item links to timeline/state/decision evidence context
- Users can switch to ad hoc mode and retain context filters
- Existing Milestone 10 interrogation capabilities remain non-regressive

------------------------------------------------------------------------

## How to Test (Operator Checklist)

1. Validate guided landing value
	- Open Data Explorer and confirm meaningful insights render without manual query
	- Confirm top cards are understandable and actionable

2. Validate notable-item drilldown
	- Open multiple notable cards
	- Confirm each provides explicit evidence links and explanation context

3. Validate ad hoc continuity
	- Pivot from guided card to ad hoc query mode
	- Confirm context (entity/time/filter) is preserved

4. Validate raw evidence access
	- From interpreted view, open raw payload details
	- Confirm user can verify exact underlying records

5. Validate regression coverage
	- Re-run Milestone 10 API/UI checks
	- Confirm lookup/timeline/state/decision behavior remains intact

------------------------------------------------------------------------

## Implementation Scope (Product-Facing)

### Guided Insights shell

- Insight-first default landing view in Data Explorer
- System Pulse panel with curated status metrics
- Notable Events feed with severity/type labeling and ranking

### Explainability + drilldown

- “Why this happened” narrative block generated from explicit contracts
- One-click transitions into timeline/state/decision panes with preserved context

### Ad hoc power lane

- Visible mode switch between Guided Insights and Ad Hoc Query
- Shared context model so guided and ad hoc flows compose cleanly

------------------------------------------------------------------------

## Non-Goals

- No freeform LLM-generated conclusions detached from evidence contracts
- No broad mutation controls added under guise of “insight actions”
- No replacement of Control Room’s role as top-level operational summary
- No heavyweight BI/report-builder scope expansion in this milestone
