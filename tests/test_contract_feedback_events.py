import asyncio

from services.event_store.file_store import FileEventStore
from shared.contracts import EventType, FeedbackEvidenceRecordedEvent, LearningTarget


def test_feedback_evidence_event_roundtrip(tmp_path):
    store = FileEventStore(data_dir=str(tmp_path / "events"))

    event = FeedbackEvidenceRecordedEvent(
        source_event_type=EventType.REMINDER_DISMISSED.value,
        object_id="task-1",
        evidence_type="weak_label",
        target_scores={
            LearningTarget.USEFULNESS: 0.8,
            LearningTarget.TIMING_FIT: 0.4,
            LearningTarget.INTERRUPT_COST: 0.7,
        },
        rationale="dismissed with quick follow-up",
        context={"followup_action_within_minutes": 20},
    )

    async def _run():
        await store.append(event)
        return await store.stream_events(event_types=[EventType.FEEDBACK_EVIDENCE_RECORDED])

    events = asyncio.run(_run())

    assert len(events) == 1
    stored = events[0]
    assert stored.event_type == EventType.FEEDBACK_EVIDENCE_RECORDED
    assert stored.target_scores[LearningTarget.USEFULNESS] == 0.8
