"""Tests for M12 orchestration runtime eventing and guardrail behavior."""

import pytest

from services.control import ControlPolicy, ControlPolicyEvaluator
from services.event_store.file_store import FileEventStore
from services.orchestration import OrchestrationRuntime
from shared.contracts import EventType


@pytest.mark.asyncio
async def test_runtime_emits_lifecycle_policy_node_and_delivery_events(tmp_path):
    store = FileEventStore(data_dir=str(tmp_path / "events"))
    runtime = OrchestrationRuntime(event_store=store, policy_evaluator=ControlPolicyEvaluator())

    async def execute():
        return {"sent": True, "delivery_id": "abc-123"}

    result = await runtime.run_flow(
        workflow_name="daily_digest",
        reminder_type="task_daily_digest",
        execute=execute,
        envelope={
            "workflow_name": "daily_digest",
            "reminder_type": "task_daily_digest",
            "tool_name": "telegram.send_message",
            "side_effect_scope": "telegram:notify",
            "budgets": {
                "runtime_seconds": 10,
                "tool_calls": 1,
                "estimated_tokens": 180,
                "estimated_cost_usd": 0.01,
            },
        },
    )

    assert result["status"] == "completed"

    events = await store.stream_events()
    event_types = [event.event_type for event in events]
    assert EventType.ORCHESTRATION_RUN_STARTED in event_types
    assert EventType.ORCHESTRATION_NODE_ENTERED in event_types
    assert EventType.ORCHESTRATION_NODE_COMPLETED in event_types
    assert EventType.ORCHESTRATION_POLICY_ALLOWED in event_types
    assert EventType.ORCHESTRATION_DELIVERY_ATTEMPTED in event_types
    assert EventType.ORCHESTRATION_DELIVERY_SUCCEEDED in event_types
    assert EventType.ORCHESTRATION_RUN_FINISHED in event_types


@pytest.mark.asyncio
async def test_runtime_blocks_out_of_policy_runs(tmp_path):
    store = FileEventStore(data_dir=str(tmp_path / "events"))
    evaluator = ControlPolicyEvaluator(
        policy=ControlPolicy(tool_allowlist={"telegram.send_message"})
    )
    runtime = OrchestrationRuntime(event_store=store, policy_evaluator=evaluator)

    async def execute():
        return {"sent": True}

    result = await runtime.run_flow(
        workflow_name="daily_digest",
        reminder_type="task_daily_digest",
        execute=execute,
        envelope={
            "workflow_name": "daily_digest",
            "reminder_type": "task_daily_digest",
            "tool_name": "filesystem.write",
            "side_effect_scope": "telegram:notify",
            "budgets": {
                "runtime_seconds": 10,
                "tool_calls": 1,
                "estimated_tokens": 180,
                "estimated_cost_usd": 0.01,
            },
        },
    )

    assert result["status"] == "blocked"
    assert result["reason"] == "tool_not_allowed"

    events = await store.stream_events()
    event_types = [event.event_type for event in events]
    assert EventType.ORCHESTRATION_POLICY_BLOCKED in event_types
    assert EventType.ORCHESTRATION_RUN_FAILED in event_types
    assert EventType.ORCHESTRATION_DELIVERY_SUCCEEDED not in event_types
