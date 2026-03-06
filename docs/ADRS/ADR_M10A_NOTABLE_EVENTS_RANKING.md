# Architecture Decision Record

## Title
Milestone 10A Data Explorer: Deterministic Notable-Events Ranking for Guided Insights

## Status
Accepted

## Context
Guided Insights requires an ordering mechanism for “what matters now.” If this
ordering is opaque or unstable, operators may lose trust and cannot reliably
audit why one insight was shown above another.

## Decision
Notable Events ranking will use deterministic, contract-based scoring with
explicit factors and tie-break rules.

Initial ranking factors:
- Severity class (error/risk/warning/info)
- Recency window weighting
- Blast radius (affected entities/components count)
- Novelty/regression indicator
- Operator relevance tags (e.g., tasking, reminders, learning drift)

Tie-break policy:
1. Higher severity
2. Higher composite score
3. More recent timestamp
4. Stable deterministic ID ordering

Ranking metadata (score components and labels) will be exposed in explorer
contracts so users can inspect why an item was ranked where it was.

## Rationale
- Keeps prioritization explainable and reproducible.
- Enables QA and operator verification of ranking behavior.
- Avoids hidden model-dependent sorting logic in core operator workflows.
- Provides extensible baseline for future bounded personalization.

## Alternatives Considered
- Purely timestamp-ordered feed.
- Opaque heuristic ranking implemented only in frontend.
- LLM-generated prioritization without explicit contract factors.

## Consequences
- Requires backend scoring/read-model assembly endpoint(s).
- Requires contract evolution for ranking metadata and reasoning labels.
- Introduces calibration work to tune factor weights over time.
