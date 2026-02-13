#!/usr/bin/env python3
"""Evaluate Milestone 6 attention/planning signals from the event log.

Produces a reproducible JSON report with key product metrics and rollout gates.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.common.config import Config
from shared.contracts import EventType
from services.event_store.file_store import FileEventStore


def _safe_rate(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return round(numerator / denominator, 4)


def _gate(name: str, passed: bool | None, value: float | None, threshold: str) -> dict:
    status = "insufficient_data" if passed is None else ("pass" if passed else "fail")
    return {
        "name": name,
        "status": status,
        "passed": passed,
        "value": value,
        "threshold": threshold,
    }


def _candidate_field(candidate: object, key: str, default=None):
    if hasattr(candidate, key):
        return getattr(candidate, key)
    if isinstance(candidate, dict):
        return candidate.get(key, default)
    return default


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 4)


async def build_report(events_dir: str, rollback_verified: bool = False) -> dict:
    store = FileEventStore(data_dir=events_dir)
    events = await store.stream_events()

    shown = [e for e in events if e.event_type == EventType.SUGGESTION_SHOWN]
    applied = [e for e in events if e.event_type == EventType.SUGGESTION_APPLIED]
    rejected = [e for e in events if e.event_type == EventType.SUGGESTION_REJECTED]
    reminders = [e for e in events if e.event_type == EventType.REMINDER_SENT]
    reminders_dismissed = [e for e in events if e.event_type == EventType.REMINDER_DISMISSED]
    reminders_snoozed = [e for e in events if e.event_type == EventType.REMINDER_SNOOZED]
    model_scores = [e for e in events if e.event_type == EventType.MODEL_SCORE_RECORDED]
    attention_scoring = [e for e in events if e.event_type == EventType.ATTENTION_SCORING_COMPUTED]

    acceptance_rate = _safe_rate(len(applied), len(shown))

    shown_by_id: dict[str, object] = {}
    for event in shown:
        shown_by_id[str(getattr(event, "suggestion_id", ""))] = event

    baseline_shown = 0
    baseline_applied = 0
    personalized_shown = 0
    personalized_applied = 0
    for event in shown:
        policy = str(getattr(event, "metadata", {}).get("personalization_policy", "deterministic_only"))
        if policy == "bounded_in_bucket":
            personalized_shown += 1
        else:
            baseline_shown += 1

    for event in applied:
        suggestion_id = str(getattr(event, "suggestion_id", ""))
        shown_event = shown_by_id.get(suggestion_id)
        policy = "deterministic_only"
        if shown_event is not None:
            policy = str(
                getattr(shown_event, "metadata", {}).get(
                    "personalization_policy", "deterministic_only"
                )
            )
        if policy == "bounded_in_bucket":
            personalized_applied += 1
        else:
            baseline_applied += 1

    baseline_acceptance_rate = _safe_rate(baseline_applied, baseline_shown)
    personalized_acceptance_rate = _safe_rate(personalized_applied, personalized_shown)
    acceptance_uplift_vs_baseline = None
    if baseline_acceptance_rate is not None and personalized_acceptance_rate is not None:
        acceptance_uplift_vs_baseline = round(
            personalized_acceptance_rate - baseline_acceptance_rate, 4
        )

    # Duplicate reminder estimate: same reminder_type + object_id + fingerprint emitted >1x.
    reminder_keys = []
    for event in reminders:
        reminder_keys.append(
            (
                getattr(event, "reminder_type", ""),
                getattr(event, "object_id", None),
                getattr(event, "fingerprint", None),
            )
        )
    duplicate_reminders = max(0, len(reminder_keys) - len(set(reminder_keys)))
    duplicate_reminder_rate = _safe_rate(duplicate_reminders, len(reminders))

    ranked_candidates = 0
    personalized_candidates = 0
    for event in attention_scoring:
        for candidate in getattr(event, "candidates", []):
            ranked_candidates += 1
            if bool(_candidate_field(candidate, "personalization_applied", False)):
                personalized_candidates += 1
    ordering_shift_rate = _safe_rate(personalized_candidates, ranked_candidates)

    confidence_above_threshold = 0
    confidences: list[float] = []
    confidence_threshold = 0.6
    for event in model_scores:
        confidence = getattr(event, "confidence", None)
        if confidence is None:
            continue
        confidence = float(confidence)
        confidences.append(confidence)
        if confidence >= confidence_threshold:
            confidence_above_threshold += 1

    confidence_above_threshold_rate = _safe_rate(confidence_above_threshold, len(confidences))
    mean_model_confidence = round(sum(confidences) / len(confidences), 4) if confidences else None

    usefulness_scores: list[float] = []
    timing_fit_scores: list[float] = []
    interrupt_cost_scores: list[float] = []
    for event in model_scores:
        metadata = getattr(event, "metadata", {}) or {}
        use = metadata.get("usefulness_score")
        timing = metadata.get("timing_fit_score")
        interrupt = metadata.get("interrupt_cost_score")
        if use is not None:
            usefulness_scores.append(float(use))
        if timing is not None:
            timing_fit_scores.append(float(timing))
        if interrupt is not None:
            interrupt_cost_scores.append(float(interrupt))

    mean_usefulness_score = _mean(usefulness_scores)
    mean_timing_fit_score = _mean(timing_fit_scores)
    mean_interrupt_cost_score = _mean(interrupt_cost_scores)

    gate_acceptance_uplift = _gate(
        "acceptance_uplift_non_negative",
        None if acceptance_uplift_vs_baseline is None else acceptance_uplift_vs_baseline >= 0.0,
        acceptance_uplift_vs_baseline,
        ">= 0.0",
    )
    gate_duplicate_rate = _gate(
        "duplicate_reminder_rate_below_5pct",
        None if duplicate_reminder_rate is None else duplicate_reminder_rate <= 0.05,
        duplicate_reminder_rate,
        "<= 0.05",
    )
    gate_ordering_shift = _gate(
        "ordering_shift_rate_below_40pct",
        None if ordering_shift_rate is None else ordering_shift_rate <= 0.40,
        ordering_shift_rate,
        "<= 0.40",
    )
    gate_confidence = _gate(
        "confidence_above_threshold_rate_min_60pct",
        None
        if confidence_above_threshold_rate is None
        else confidence_above_threshold_rate >= 0.60,
        confidence_above_threshold_rate,
        ">= 0.60",
    )
    gate_shadow_data = _gate(
        "shadow_data_present",
        len(model_scores) > 0,
        float(len(model_scores)),
        "> 0",
    )

    gates = {
        gate_acceptance_uplift["name"]: gate_acceptance_uplift,
        gate_duplicate_rate["name"]: gate_duplicate_rate,
        gate_ordering_shift["name"]: gate_ordering_shift,
        gate_confidence["name"]: gate_confidence,
        gate_shadow_data["name"]: gate_shadow_data,
    }

    evaluated_gate_passes = [gate["passed"] for gate in gates.values() if gate["passed"] is not None]
    rollout_ready = bool(evaluated_gate_passes) and all(evaluated_gate_passes)

    interaction_volume = (
        len(shown)
        + len(applied)
        + len(rejected)
        + len(reminders)
        + len(reminders_dismissed)
        + len(reminders_snoozed)
    )
    stage_b_thresholds = {
        "min_interaction_volume": 50,
        "max_duplicate_reminder_rate": 0.05,
        "min_confidence_above_threshold_rate": 0.60,
    }
    stage_b_checks = {
        "interaction_volume": {
            "status": "pass"
            if interaction_volume >= stage_b_thresholds["min_interaction_volume"]
            else "fail",
            "value": interaction_volume,
            "threshold": f">= {stage_b_thresholds['min_interaction_volume']}",
        },
        "acceptance_uplift_non_negative": {
            "status": "insufficient_data"
            if acceptance_uplift_vs_baseline is None
            else ("pass" if acceptance_uplift_vs_baseline >= 0.0 else "fail"),
            "value": acceptance_uplift_vs_baseline,
            "threshold": ">= 0.0",
        },
        "duplicate_reminder_non_regression": {
            "status": "insufficient_data"
            if duplicate_reminder_rate is None
            else (
                "pass"
                if duplicate_reminder_rate <= stage_b_thresholds["max_duplicate_reminder_rate"]
                else "fail"
            ),
            "value": duplicate_reminder_rate,
            "threshold": f"<= {stage_b_thresholds['max_duplicate_reminder_rate']}",
        },
        "calibration_quality": {
            "status": "insufficient_data"
            if confidence_above_threshold_rate is None
            else (
                "pass"
                if confidence_above_threshold_rate
                >= stage_b_thresholds["min_confidence_above_threshold_rate"]
                else "fail"
            ),
            "value": confidence_above_threshold_rate,
            "threshold": f">= {stage_b_thresholds['min_confidence_above_threshold_rate']}",
        },
        "rollback_verified": {
            "status": "pass" if rollback_verified else "fail",
            "value": rollback_verified,
            "threshold": "must be true",
        },
    }

    stage_b_ready = all(check["status"] == "pass" for check in stage_b_checks.values())

    report = {
        "generated_at": datetime.utcnow().isoformat(),
        "events_dir": events_dir,
        "counts": {
            "events_total": len(events),
            "suggestions_shown": len(shown),
            "suggestions_applied": len(applied),
            "suggestions_rejected": len(rejected),
            "reminders_sent": len(reminders),
            "reminders_dismissed": len(reminders_dismissed),
            "reminders_snoozed": len(reminders_snoozed),
            "model_scores_logged": len(model_scores),
            "interaction_volume": interaction_volume,
        },
        "metrics": {
            "suggestion_acceptance_rate": acceptance_rate,
            "baseline_acceptance_rate": baseline_acceptance_rate,
            "personalized_acceptance_rate": personalized_acceptance_rate,
            "acceptance_uplift_vs_baseline": acceptance_uplift_vs_baseline,
            "duplicate_reminder_rate": duplicate_reminder_rate,
            "ordering_shift_rate": ordering_shift_rate,
            "confidence_above_threshold_rate": confidence_above_threshold_rate,
            "mean_model_confidence": mean_model_confidence,
            "mean_usefulness_score": mean_usefulness_score,
            "mean_timing_fit_score": mean_timing_fit_score,
            "mean_interrupt_cost_score": mean_interrupt_cost_score,
            "reopen_rate": None,
            "median_time_to_complete_after_suggestion_hours": None,
        },
        "shadow_comparison": {
            "status": "available" if model_scores else "insufficient_data",
            "shadow_scored_candidates": len(model_scores),
        },
        "rollout_gates": {
            "acceptance_uplift_non_negative": gate_acceptance_uplift,
            "duplicate_reminder_rate_below_5pct": gate_duplicate_rate,
            "ordering_shift_rate_below_40pct": gate_ordering_shift,
            "confidence_above_threshold_rate_min_60pct": gate_confidence,
            "shadow_data_present": gate_shadow_data,
        },
        "rollout_gate_summary": {
            "pass": [name for name, gate in gates.items() if gate["status"] == "pass"],
            "fail": [name for name, gate in gates.items() if gate["status"] == "fail"],
            "insufficient_data": [
                name for name, gate in gates.items() if gate["status"] == "insufficient_data"
            ],
        },
        "gate_thresholds": {
            "acceptance_uplift_vs_baseline": ">= 0.0",
            "duplicate_reminder_rate": "<= 0.05",
            "ordering_shift_rate": "<= 0.40",
            "confidence_above_threshold_rate": ">= 0.60",
            "confidence_threshold": confidence_threshold,
        },
        "stage_b_readiness": {
            "ready": stage_b_ready,
            "checks": stage_b_checks,
            "thresholds": stage_b_thresholds,
            "note": "Readiness report only; contextual bandit exploration remains disabled.",
        },
        "target_diagnostics": {
            "usefulness": {
                "mean_score": mean_usefulness_score,
                "samples": len(usefulness_scores),
            },
            "timing_fit": {
                "mean_score": mean_timing_fit_score,
                "samples": len(timing_fit_scores),
            },
            "interrupt_cost": {
                "mean_score": mean_interrupt_cost_score,
                "samples": len(interrupt_cost_scores),
            },
        },
    }

    report["rollout_ready"] = rollout_ready
    return report


async def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate attention replay metrics")
    parser.add_argument(
        "--events-dir",
        default=None,
        help="Path to event log directory (defaults to Config.EVENT_STORE_PATH)",
    )
    parser.add_argument(
        "--out",
        default="./data/projections/attention_replay_report.json",
        help="Output JSON file path",
    )
    parser.add_argument(
        "--rollback-verified",
        action="store_true",
        help="Mark rollback verification as complete for Stage B readiness evaluation",
    )
    args = parser.parse_args()

    cfg = Config.from_env()
    events_dir = args.events_dir or cfg.EVENT_STORE_PATH

    report = await build_report(events_dir, rollback_verified=args.rollback_verified)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2))

    print(f"Wrote replay report: {out_path}")
    print(json.dumps(report["metrics"], indent=2))
    print(f"Rollout ready: {report['rollout_ready']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
