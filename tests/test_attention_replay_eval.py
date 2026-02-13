"""Tests for attention replay evaluation metrics and rollout gates."""

from __future__ import annotations

import asyncio

from scripts.evaluate_attention_replay import build_report
from services.event_store.file_store import FileEventStore
from shared.contracts import (
    AttentionBucket,
    AttentionCandidate,
    AttentionScoringComputedEvent,
    ModelScoreRecordedEvent,
    BaseEvent,
    ReminderSentEvent,
    SuggestionAppliedEvent,
    SuggestionShownEvent,
)


def _append_events(store: FileEventStore, events: list[BaseEvent]) -> None:
    async def _run() -> None:
        for event in events:
            await store.append(event)

    asyncio.run(_run())


def test_replay_report_computes_metrics_and_gates(tmp_path):
    store = FileEventStore(data_dir=str(tmp_path / "events"))

    events = [
        SuggestionShownEvent(
            task_id="t1",
            suggestion_id="s1",
            suggestion_type="dependency",
            metadata={"personalization_policy": "deterministic_only"},
        ),
        SuggestionShownEvent(
            task_id="t2",
            suggestion_id="s2",
            suggestion_type="dependency",
            metadata={"personalization_policy": "deterministic_only"},
        ),
        SuggestionShownEvent(
            task_id="t3",
            suggestion_id="s3",
            suggestion_type="split",
            metadata={"personalization_policy": "bounded_in_bucket"},
        ),
        SuggestionShownEvent(
            task_id="t4",
            suggestion_id="s4",
            suggestion_type="split",
            metadata={"personalization_policy": "bounded_in_bucket"},
        ),
        SuggestionAppliedEvent(
            task_id="t1",
            suggestion_id="s1",
            suggestion_type="dependency",
        ),
        SuggestionAppliedEvent(
            task_id="t3",
            suggestion_id="s3",
            suggestion_type="split",
        ),
        SuggestionAppliedEvent(
            task_id="t4",
            suggestion_id="s4",
            suggestion_type="split",
        ),
        ReminderSentEvent(reminder_type="urgent", object_id="t1", fingerprint="f1"),
        ReminderSentEvent(reminder_type="urgent", object_id="t2", fingerprint="f2"),
        AttentionScoringComputedEvent(
            queue_name="today",
            candidates=[
                AttentionCandidate(
                    task_id="t1",
                    urgency_score=70,
                    explanation="baseline",
                    deterministic_bucket_id=AttentionBucket.URGENT_DUE_SOON,
                    deterministic_bucket_rank=0,
                    personalization_applied=False,
                ),
                AttentionCandidate(
                    task_id="t2",
                    urgency_score=65,
                    explanation="baseline",
                    deterministic_bucket_id=AttentionBucket.READY_HIGH_PRIORITY,
                    deterministic_bucket_rank=1,
                    personalization_applied=True,
                ),
            ],
        ),
        ModelScoreRecordedEvent(
            candidate_id="t1",
            candidate_type="attention_task",
            model_name="linear_shadow_ranker",
            model_version="m6-v1",
            score=0.91,
            confidence=0.82,
            metadata={
                "usefulness_score": 0.85,
                "timing_fit_score": 0.62,
                "interrupt_cost_score": 0.28,
            },
        ),
        ModelScoreRecordedEvent(
            candidate_id="t2",
            candidate_type="attention_task",
            model_name="linear_shadow_ranker",
            model_version="m6-v1",
            score=0.76,
            confidence=0.78,
            metadata={
                "usefulness_score": 0.72,
                "timing_fit_score": 0.58,
                "interrupt_cost_score": 0.34,
            },
        ),
    ]

    _append_events(store, events)

    report = asyncio.run(build_report(str(tmp_path / "events"), rollback_verified=True))

    assert report["metrics"]["acceptance_uplift_vs_baseline"] == 0.5
    assert report["metrics"]["duplicate_reminder_rate"] == 0.0
    assert report["metrics"]["ordering_shift_rate"] == 0.5
    assert report["metrics"]["confidence_above_threshold_rate"] == 1.0
    assert report["metrics"]["mean_usefulness_score"] == 0.785
    assert report["target_diagnostics"]["timing_fit"]["samples"] == 2
    assert report["rollout_gates"]["acceptance_uplift_non_negative"]["status"] == "pass"
    assert report["rollout_gates"]["duplicate_reminder_rate_below_5pct"]["status"] == "pass"
    assert report["rollout_gates"]["ordering_shift_rate_below_40pct"]["status"] == "fail"
    assert report["stage_b_readiness"]["checks"]["rollback_verified"]["status"] == "pass"
    assert report["stage_b_readiness"]["ready"] is False
    assert report["rollout_ready"] is False


def test_replay_report_handles_insufficient_data(tmp_path):
    store = FileEventStore(data_dir=str(tmp_path / "events"))
    _append_events(
        store,
        [
            SuggestionShownEvent(task_id="t1", suggestion_id="s1", suggestion_type="dependency"),
            ReminderSentEvent(reminder_type="urgent", object_id="t1", fingerprint="f1"),
        ],
    )

    report = asyncio.run(build_report(str(tmp_path / "events")))

    assert report["metrics"]["acceptance_uplift_vs_baseline"] is None
    assert (
        report["rollout_gates"]["acceptance_uplift_non_negative"]["status"] == "insufficient_data"
    )
    assert report["stage_b_readiness"]["checks"]["rollback_verified"]["status"] == "fail"
    assert report["rollout_ready"] is False
