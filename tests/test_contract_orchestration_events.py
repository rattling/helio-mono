"""Tests for M12 orchestration transparency event contracts."""

import pytest

from services.event_store.file_store import FileEventStore
from shared.contracts import (
    EventType,
    OrchestrationDeliverySucceededEvent,
    OrchestrationNodeCompletedEvent,
    OrchestrationPolicyAllowedEvent,
    OrchestrationRunFinishedEvent,
    OrchestrationRunStartedEvent,
)


@pytest.mark.asyncio
async def test_orchestration_event_contract_roundtrip(tmp_path):
    store = FileEventStore(data_dir=str(tmp_path / "events"))

    started = OrchestrationRunStartedEvent(
        run_id="run-001",
        workflow_name="daily_digest",
        trigger="scheduler",
    )
    policy = OrchestrationPolicyAllowedEvent(
        run_id="run-001",
        workflow_name="daily_digest",
        reason="policy_check_passed",
        envelope={"workflow_name": "daily_digest"},
    )
    node = OrchestrationNodeCompletedEvent(
        run_id="run-001",
        workflow_name="daily_digest",
        node_id="delivery_execution",
        result={"sent": True},
    )
    delivery = OrchestrationDeliverySucceededEvent(
        run_id="run-001",
        workflow_name="daily_digest",
        reminder_type="task_daily_digest",
        delivery_channel="telegram",
    )
    finished = OrchestrationRunFinishedEvent(
        run_id="run-001",
        workflow_name="daily_digest",
        status="completed",
        output={"sent": True},
    )

    for event in [started, policy, node, delivery, finished]:
        await store.append(event)

    events = await store.stream_events(
        event_types=[
            EventType.ORCHESTRATION_RUN_STARTED,
            EventType.ORCHESTRATION_POLICY_ALLOWED,
            EventType.ORCHESTRATION_NODE_COMPLETED,
            EventType.ORCHESTRATION_DELIVERY_SUCCEEDED,
            EventType.ORCHESTRATION_RUN_FINISHED,
        ]
    )

    assert [event.event_type for event in events] == [
        EventType.ORCHESTRATION_RUN_STARTED,
        EventType.ORCHESTRATION_POLICY_ALLOWED,
        EventType.ORCHESTRATION_NODE_COMPLETED,
        EventType.ORCHESTRATION_DELIVERY_SUCCEEDED,
        EventType.ORCHESTRATION_RUN_FINISHED,
    ]
    assert str(getattr(events[0], "run_id", "")) == "run-001"
    assert str(getattr(events[-1], "workflow_name", "")) == "daily_digest"
