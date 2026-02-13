# Architecture Decision Record

## Title
Milestone 10A Data Explorer: Guided Insights as Default, Ad Hoc as Power Lane

## Status
Accepted

## Context
Milestone 10 established traceability APIs and UI panes for power users, but the
experience remains query-first. Operators must already know what to ask, which
slows discovery and increases cognitive overhead.

Helionyx needs a default interrogation flow that proactively surfaces notable
system behavior while preserving direct ad hoc access.

## Decision
Data Explorer will adopt a dual-mode UX:
- **Guided Insights** as the default landing and primary workflow,
- **Ad Hoc Query** as a first-class secondary workflow.

Guided Insights will present curated high-signal system insights and explicit
links into evidence-backed detail panes. Ad hoc mode will remain available for
precision debugging and exploratory investigation.

## Rationale
- Improves day-to-day operator usability and discoverability.
- Preserves transparency by requiring evidence-backed drilldowns.
- Retains power-user flexibility without forcing all users through raw queries.
- Aligns with Control Room → Explorer workflow where summaries lead to detail.

## Alternatives Considered
- Keep query-first UX and add only cosmetic hints/tooltips.
- Replace Data Explorer with only opinionated summaries and hide ad hoc mode.

## Consequences
- Requires explicit mode state and shared context transfer model.
- Introduces UX ranking/summarization logic that must remain deterministic and auditable.
- Increases frontend composition complexity but improves operator outcomes.
