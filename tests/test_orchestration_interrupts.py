"""Tests for explicit interrupt handling in M13 orchestration flows."""

import pytest

from services.control import ControlPolicy, ControlPolicyEvaluator
from services.event_store.file_store import FileEventStore
from services.orchestration import OrchestrationRuntime
from shared.contracts import EventType


@pytest.mark.asyncio
async def test_runtime_supports_policy_escalation_interrupt_and_rejection(tmp_path):
    store = FileEventStore(data_dir=str(tmp_path / "events"))
    runtime = OrchestrationRuntime(
        event_store=store,
        policy_evaluator=ControlPolicyEvaluator(policy=ControlPolicy(max_tool_calls=1)),
        checkpoint_path=str(tmp_path / "checkpoints" / "runtime.pkl"),
    )

    async def execute():
        return {"sent": True}

    interrupted = await runtime.run_flow(
        workflow_name="urgent_reminder",
        reminder_type="task_urgent_reminder",
        execute=execute,
        interrupt_on_policy_escalation=True,
        interrupt_payload={"kind": "policy_escalation"},
        envelope={
            "workflow_name": "urgent_reminder",
            "reminder_type": "task_urgent_reminder",
            "tool_name": "telegram.send_message",
            "side_effect_scope": "telegram:notify",
            "budgets": {
                "runtime_seconds": 10,
                "tool_calls": 2,
                "estimated_tokens": 120,
                "estimated_cost_usd": 0.01,
            },
        },
    )

    assert interrupted["status"] == "interrupted"

    rejected = await runtime.resume_flow(
        run_id=interrupted["run_id"],
        resume_value={"approved": False},
    )

    assert rejected["status"] == "failed"
    assert rejected["reason"] == "interrupt_rejected"

    events = await store.stream_events()
    event_types = [event.event_type for event in events]
    assert EventType.ORCHESTRATION_POLICY_ESCALATED in event_types
    assert EventType.ORCHESTRATION_RUN_FAILED in event_types
    assert EventType.ORCHESTRATION_DELIVERY_ATTEMPTED not in event_types
