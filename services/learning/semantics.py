"""Contextual feedback semantics for Milestone 8.

This module provides deterministic weak-label interpretation rules for
ambiguous feedback signals such as dismiss/snooze.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FeedbackSemanticsResult:
    usefulness: float
    timing_fit: float
    interrupt_cost: float
    rationale: str


def infer_reminder_feedback_semantics(
    *,
    action: str,
    followup_action_within_minutes: int | None = None,
    snooze_minutes: int | None = None,
) -> FeedbackSemanticsResult:
    """Infer weak-label semantics for reminder feedback.

    Returns normalized scores in [0.0, 1.0] for:
    - usefulness: whether reminder likely helped progress
    - timing_fit: whether timing appears right
    - interrupt_cost: disruption at moment of reminder
    """
    action_norm = (action or "").strip().lower()

    if action_norm == "snoozed":
        # Snooze is typically a timing signal rather than pure usefulness negative.
        usefulness = 0.7
        timing_fit = 0.3
        interrupt_cost = 0.7
        if snooze_minutes is not None and snooze_minutes <= 15:
            usefulness = 0.8
            timing_fit = 0.35
            interrupt_cost = 0.8
        return FeedbackSemanticsResult(
            usefulness=usefulness,
            timing_fit=timing_fit,
            interrupt_cost=interrupt_cost,
            rationale="snoozed interpreted as useful-but-mistimed with elevated interrupt cost",
        )

    if action_norm == "dismissed":
        if followup_action_within_minutes is not None and followup_action_within_minutes <= 60:
            return FeedbackSemanticsResult(
                usefulness=0.85,
                timing_fit=0.65,
                interrupt_cost=0.55,
                rationale="dismissed with quick follow-up interpreted as useful completion signal",
            )
        return FeedbackSemanticsResult(
            usefulness=0.25,
            timing_fit=0.45,
            interrupt_cost=0.35,
            rationale="dismissed without quick follow-up interpreted as low usefulness signal",
        )

    # Default neutral semantics when action is unknown.
    return FeedbackSemanticsResult(
        usefulness=0.5,
        timing_fit=0.5,
        interrupt_cost=0.5,
        rationale="neutral fallback semantics",
    )
