"""Tests for deterministic control-policy guardrails (M12)."""

from services.control import ControlPolicyEvaluator, PolicyOutcome


def test_policy_allows_in_scope_envelope():
    evaluator = ControlPolicyEvaluator()

    result = evaluator.evaluate(
        {
            "workflow_name": "daily_digest",
            "reminder_type": "task_daily_digest",
            "tool_name": "telegram.send_message",
            "side_effect_scope": "telegram:notify",
            "budgets": {
                "runtime_seconds": 10,
                "tool_calls": 1,
                "estimated_tokens": 120,
                "estimated_cost_usd": 0.01,
            },
        }
    )

    assert result.outcome == PolicyOutcome.ALLOWED
    assert result.reason == "policy_check_passed"


def test_policy_fail_closed_on_missing_fields():
    evaluator = ControlPolicyEvaluator()

    result = evaluator.evaluate(
        {
            "workflow_name": "daily_digest",
            "reminder_type": "task_daily_digest",
            "tool_name": "telegram.send_message",
            "budgets": {
                "runtime_seconds": 10,
                "tool_calls": 1,
                "estimated_tokens": 120,
                "estimated_cost_usd": 0.01,
            },
        }
    )

    assert result.outcome == PolicyOutcome.BLOCKED
    assert result.reason == "missing_field:side_effect_scope"


def test_policy_blocks_tool_outside_allowlist():
    evaluator = ControlPolicyEvaluator()

    result = evaluator.evaluate(
        {
            "workflow_name": "weekly_digest",
            "reminder_type": "task_weekly_digest",
            "tool_name": "filesystem.write",
            "side_effect_scope": "telegram:notify",
            "budgets": {
                "runtime_seconds": 10,
                "tool_calls": 1,
                "estimated_tokens": 120,
                "estimated_cost_usd": 0.01,
            },
        }
    )

    assert result.outcome == PolicyOutcome.BLOCKED
    assert result.reason == "tool_not_allowed"


def test_policy_escalates_budget_breach():
    evaluator = ControlPolicyEvaluator()

    result = evaluator.evaluate(
        {
            "workflow_name": "urgent_reminder",
            "reminder_type": "task_urgent_reminder",
            "tool_name": "telegram.send_message",
            "side_effect_scope": "telegram:notify",
            "budgets": {
                "runtime_seconds": 10,
                "tool_calls": 99,
                "estimated_tokens": 120,
                "estimated_cost_usd": 0.01,
            },
        }
    )

    assert result.outcome == PolicyOutcome.ESCALATED
    assert result.reason == "tool_call_budget_exceeded"
