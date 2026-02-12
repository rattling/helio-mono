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


class ShadowRanker:
    """Interpretable weighted ranker with deterministic behavior."""

    model_name = "linear_shadow_ranker"
    model_version = "m6-v1"

    def score(self, features: dict[str, float]) -> ShadowRankerResult:
        score = 0.0
        score += 18.0 * features.get("priority_value", 0.5)
        score += 14.0 * features.get("due_overdue", 0.0)
        score += 9.0 * features.get("due_in_24h", 0.0)
        score += 6.0 * features.get("due_in_72h", 0.0)
        score += 4.0 * min(features.get("age_hours", 0.0) / 24.0, 14.0)
        score -= 8.0 * features.get("is_blocked", 0.0)
        score -= 6.0 * features.get("has_future_start_gate", 0.0)

        confidence = 0.55
        if features.get("has_due", 0.0) == 1.0:
            confidence += 0.15
        if features.get("priority_value", 0.5) >= 0.75:
            confidence += 0.1
        if features.get("age_hours", 0.0) > 72:
            confidence += 0.1
        confidence = max(0.05, min(0.99, confidence))

        explanation = (
            "weighted(priority,due_proximity,age,blocked,start_gate) "
            f"=> score={score:.2f}, confidence={confidence:.2f}"
        )
        return ShadowRankerResult(score=score, confidence=confidence, explanation=explanation)
