"""Simple shadow-mode ranker for Milestone 6.

This ranker is intentionally interpretable and only used in shadow mode by default.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ShadowRankerResult:
    score: float
    confidence: float
    explanation: str
    usefulness_score: float
    timing_fit_score: float
    interrupt_cost_score: float


class ShadowRanker:
    """Interpretable weighted ranker with deterministic behavior."""

    model_name = "linear_shadow_ranker"
    model_version = "m6-v1"

    def score(self, features: dict[str, float]) -> ShadowRankerResult:
        usefulness_score = 0.0
        usefulness_score += 0.45 * features.get("priority_value", 0.5)
        usefulness_score += 0.30 * features.get("due_overdue", 0.0)
        usefulness_score += 0.20 * features.get("due_in_24h", 0.0)
        usefulness_score += 0.12 * features.get("due_in_72h", 0.0)
        usefulness_score -= 0.18 * features.get("is_blocked", 0.0)

        timing_fit_score = 0.65
        timing_fit_score -= 0.35 * features.get("has_future_start_gate", 0.0)
        timing_fit_score -= 0.20 * features.get("is_snoozed", 0.0)
        timing_fit_score += 0.10 * features.get("due_in_24h", 0.0)

        interrupt_cost_score = 0.30
        interrupt_cost_score += 0.35 * features.get("is_snoozed", 0.0)
        interrupt_cost_score += 0.25 * features.get("has_future_start_gate", 0.0)
        interrupt_cost_score += 0.15 * features.get("is_blocked", 0.0)

        usefulness_score = max(0.0, min(1.0, usefulness_score))
        timing_fit_score = max(0.0, min(1.0, timing_fit_score))
        interrupt_cost_score = max(0.0, min(1.0, interrupt_cost_score))

        score = (
            (usefulness_score * 100.0) + (timing_fit_score * 12.0) - (interrupt_cost_score * 14.0)
        )
        score += 4.0 * min(features.get("age_hours", 0.0) / 24.0, 14.0)

        confidence = 0.55
        if features.get("has_due", 0.0) == 1.0:
            confidence += 0.15
        if features.get("priority_value", 0.5) >= 0.75:
            confidence += 0.1
        if features.get("age_hours", 0.0) > 72:
            confidence += 0.1
        confidence = max(0.05, min(0.99, confidence))

        explanation = (
            "multi_signal(usefulness,timing_fit,interrupt_cost)+age "
            f"=> score={score:.2f}, confidence={confidence:.2f}, "
            f"usefulness={usefulness_score:.2f}, timing_fit={timing_fit_score:.2f}, "
            f"interrupt_cost={interrupt_cost_score:.2f}"
        )
        return ShadowRankerResult(
            score=score,
            confidence=confidence,
            explanation=explanation,
            usefulness_score=usefulness_score,
            timing_fit_score=timing_fit_score,
            interrupt_cost_score=interrupt_cost_score,
        )
