"""Deterministic control-plane policy evaluator for bounded orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PolicyOutcome(str, Enum):
    ALLOWED = "allowed"
    BLOCKED = "blocked"
    ESCALATED = "escalated"


@dataclass(frozen=True)
class PolicyEvaluationResult:
    outcome: PolicyOutcome
    reason: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ControlPolicy:
    allowed_workflows: set[str] = field(
        default_factory=lambda: {"daily_digest", "weekly_digest", "urgent_reminder"}
    )
    allowed_reminder_types: set[str] = field(
        default_factory=lambda: {"task_daily_digest", "task_weekly_digest", "task_urgent_reminder"}
    )
    tool_allowlist: set[str] = field(default_factory=lambda: {"telegram.send_message"})
    side_effect_scopes: set[str] = field(default_factory=lambda: {"telegram:notify"})
    max_runtime_seconds: int = 60
    max_tool_calls: int = 3
    max_estimated_tokens: int = 8000
    max_estimated_cost_usd: float = 0.5


class ControlPolicyEvaluator:
    """Pure deterministic policy evaluator with fail-closed behavior."""

    def __init__(self, policy: ControlPolicy | None = None):
        self.policy = policy or ControlPolicy()

    def evaluate(self, envelope: dict[str, Any]) -> PolicyEvaluationResult:
        required_fields = [
            "workflow_name",
            "reminder_type",
            "tool_name",
            "side_effect_scope",
            "budgets",
        ]
        for key in required_fields:
            if envelope.get(key) in (None, ""):
                return PolicyEvaluationResult(
                    outcome=PolicyOutcome.BLOCKED,
                    reason=f"missing_field:{key}",
                    details={"field": key},
                )

        workflow_name = str(envelope["workflow_name"])
        reminder_type = str(envelope["reminder_type"])
        tool_name = str(envelope["tool_name"])
        side_effect_scope = str(envelope["side_effect_scope"])

        if workflow_name not in self.policy.allowed_workflows:
            return PolicyEvaluationResult(
                outcome=PolicyOutcome.BLOCKED,
                reason="workflow_not_allowed",
                details={"workflow_name": workflow_name},
            )

        if reminder_type not in self.policy.allowed_reminder_types:
            return PolicyEvaluationResult(
                outcome=PolicyOutcome.BLOCKED,
                reason="reminder_type_not_allowed",
                details={"reminder_type": reminder_type},
            )

        if tool_name not in self.policy.tool_allowlist:
            return PolicyEvaluationResult(
                outcome=PolicyOutcome.BLOCKED,
                reason="tool_not_allowed",
                details={"tool_name": tool_name},
            )

        if side_effect_scope not in self.policy.side_effect_scopes:
            return PolicyEvaluationResult(
                outcome=PolicyOutcome.BLOCKED,
                reason="scope_not_allowed",
                details={"side_effect_scope": side_effect_scope},
            )

        budgets = envelope.get("budgets")
        if not isinstance(budgets, dict):
            return PolicyEvaluationResult(
                outcome=PolicyOutcome.BLOCKED,
                reason="missing_field:budgets",
                details={"field": "budgets"},
            )

        runtime_seconds = self._coerce_float(budgets.get("runtime_seconds"), "runtime_seconds")
        if runtime_seconds is None:
            return PolicyEvaluationResult(
                outcome=PolicyOutcome.BLOCKED,
                reason="missing_field:budgets.runtime_seconds",
            )
        if runtime_seconds > float(self.policy.max_runtime_seconds):
            return PolicyEvaluationResult(
                outcome=PolicyOutcome.ESCALATED,
                reason="runtime_budget_exceeded",
                details={"runtime_seconds": runtime_seconds},
            )

        tool_calls = self._coerce_float(budgets.get("tool_calls"), "tool_calls")
        if tool_calls is None:
            return PolicyEvaluationResult(
                outcome=PolicyOutcome.BLOCKED,
                reason="missing_field:budgets.tool_calls",
            )
        if tool_calls > float(self.policy.max_tool_calls):
            return PolicyEvaluationResult(
                outcome=PolicyOutcome.ESCALATED,
                reason="tool_call_budget_exceeded",
                details={"tool_calls": tool_calls},
            )

        estimated_tokens = self._coerce_float(budgets.get("estimated_tokens"), "estimated_tokens")
        if estimated_tokens is None:
            return PolicyEvaluationResult(
                outcome=PolicyOutcome.BLOCKED,
                reason="missing_field:budgets.estimated_tokens",
            )
        if estimated_tokens > float(self.policy.max_estimated_tokens):
            return PolicyEvaluationResult(
                outcome=PolicyOutcome.ESCALATED,
                reason="token_budget_exceeded",
                details={"estimated_tokens": estimated_tokens},
            )

        estimated_cost_usd = self._coerce_float(
            budgets.get("estimated_cost_usd"),
            "estimated_cost_usd",
        )
        if estimated_cost_usd is None:
            return PolicyEvaluationResult(
                outcome=PolicyOutcome.BLOCKED,
                reason="missing_field:budgets.estimated_cost_usd",
            )
        if estimated_cost_usd > float(self.policy.max_estimated_cost_usd):
            return PolicyEvaluationResult(
                outcome=PolicyOutcome.ESCALATED,
                reason="cost_budget_exceeded",
                details={"estimated_cost_usd": estimated_cost_usd},
            )

        return PolicyEvaluationResult(
            outcome=PolicyOutcome.ALLOWED,
            reason="policy_check_passed",
            details={"workflow_name": workflow_name, "reminder_type": reminder_type},
        )

    @staticmethod
    def _coerce_float(value: Any, _field_name: str) -> float | None:
        if value in (None, ""):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
