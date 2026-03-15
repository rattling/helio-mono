"""Tests for shared M13 orchestration graph scaffolding."""

import pytest

from services.control import ControlPolicyEvaluator
from services.event_store.file_store import FileEventStore
from services.orchestration import OrchestrationRuntime
from shared.contracts import EventType


@pytest.mark.asyncio
async def test_runtime_executes_shared_scaffolding_nodes(tmp_path):
    store = FileEventStore(data_dir=str(tmp_path / "events"))
    runtime = OrchestrationRuntime(
        event_store=store,
        policy_evaluator=ControlPolicyEvaluator(),
        checkpoint_path=str(tmp_path / "checkpoints" / "runtime.pkl"),
    )

    async def execute():
        return {"sent": True, "delivery_id": "shared-001"}

    result = await runtime.run_flow(
        workflow_name="daily_digest",
        reminder_type="task_daily_digest",
        execute=execute,
        gather_context=lambda: {"task_count": 3},
        prepare_delivery=lambda: {"rendered": "hello world"},
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
    completed_nodes = [
        getattr(event, "node_id", "")
        for event in events
        if event.event_type == EventType.ORCHESTRATION_NODE_COMPLETED
    ]
    assert "context_gather" in completed_nodes
    assert "policy_evaluation" in completed_nodes
    assert "delivery_prepare" in completed_nodes
    assert "delivery_execution" in completed_nodes
