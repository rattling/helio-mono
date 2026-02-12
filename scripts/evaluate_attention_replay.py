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


async def build_report(events_dir: str) -> dict:
    store = FileEventStore(data_dir=events_dir)
    events = await store.stream_events()

    shown = [e for e in events if e.event_type == EventType.SUGGESTION_SHOWN]
    applied = [e for e in events if e.event_type == EventType.SUGGESTION_APPLIED]
    rejected = [e for e in events if e.event_type == EventType.SUGGESTION_REJECTED]
    reminders = [e for e in events if e.event_type == EventType.REMINDER_SENT]
    model_scores = [e for e in events if e.event_type == EventType.MODEL_SCORE_RECORDED]

    acceptance_rate = _safe_rate(len(applied), len(shown))

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

    report = {
        "generated_at": datetime.utcnow().isoformat(),
        "events_dir": events_dir,
        "counts": {
            "events_total": len(events),
            "suggestions_shown": len(shown),
            "suggestions_applied": len(applied),
            "suggestions_rejected": len(rejected),
            "reminders_sent": len(reminders),
            "model_scores_logged": len(model_scores),
        },
        "metrics": {
            "suggestion_acceptance_rate": acceptance_rate,
            "duplicate_reminder_rate": duplicate_reminder_rate,
            "reopen_rate": None,
            "median_time_to_complete_after_suggestion_hours": None,
        },
        "shadow_comparison": {
            "status": "available" if model_scores else "insufficient_data",
            "shadow_scored_candidates": len(model_scores),
        },
        "rollout_gates": {
            "gate_acceptance_rate_nonzero": acceptance_rate is not None and acceptance_rate > 0,
            "gate_duplicate_reminder_rate_below_5pct": duplicate_reminder_rate is not None
            and duplicate_reminder_rate <= 0.05,
            "gate_shadow_data_present": len(model_scores) > 0,
        },
    }

    report["rollout_ready"] = all(report["rollout_gates"].values())
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
    args = parser.parse_args()

    cfg = Config.from_env()
    events_dir = args.events_dir or cfg.EVENT_STORE_PATH

    report = await build_report(events_dir)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2))

    print(f"Wrote replay report: {out_path}")
    print(json.dumps(report["metrics"], indent=2))
    print(f"Rollout ready: {report['rollout_ready']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
