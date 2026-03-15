"""Tests for M13 orchestration checkpoint and resume behavior."""

import pytest

from services.control import ControlPolicyEvaluator
from services.event_store.file_store import FileEventStore
from services.orchestration import OrchestrationRuntime
from shared.contracts import EventType


@pytest.mark.asyncio
async def test_runtime_resumes_interrupted_flow_from_persistent_checkpoint(tmp_path):
    store = FileEventStore(data_dir=str(tmp_path / "events"))
    checkpoint_path = str(tmp_path / "checkpoints" / "runtime.pkl")

    runtime = OrchestrationRuntime(
        event_store=store,
        policy_evaluator=ControlPolicyEvaluator(),
        checkpoint_path=checkpoint_path,
    )

    async def execute():
        return {"sent": True, "delivery_id": "resume-001"}

    interrupted = await runtime.run_flow(
        workflow_name="daily_digest",
        reminder_type="task_daily_digest",
        execute=execute,
        interrupt_before_delivery=True,
        interrupt_payload={"kind": "delivery_approval"},
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

    assert interrupted["status"] == "interrupted"
    run_id = interrupted["run_id"]

    resumed_runtime = OrchestrationRuntime(
        event_store=store,
        policy_evaluator=ControlPolicyEvaluator(),
        checkpoint_path=checkpoint_path,
    )
    resumed = await resumed_runtime.resume_flow(
        run_id=run_id, resume_value="approved", execute=execute
    )

    assert resumed["status"] == "completed"
    assert resumed["run_id"] == run_id

    events = await store.stream_events()
    checkpoints = [
        getattr(event, "checkpoint", "")
        for event in events
        if event.event_type == EventType.ORCHESTRATION_RUN_CHECKPOINT
    ]
    assert "interrupt_requested" in checkpoints
    assert "interrupt_resumed" in checkpoints
    assert EventType.ORCHESTRATION_DELIVERY_SUCCEEDED in [event.event_type for event in events]
