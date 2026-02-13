"""Contract tests for Data Explorer shared models (Milestone 10)."""

from shared.contracts import (
    ExplorerGuidedInsightsResponse,
    ExplorerMode,
    ExplorerDeepLinkContext,
    ExplorerEntityType,
    ExplorerLookupResponse,
    ExplorerViewMode,
)


def test_explorer_lookup_contract_shape():
    payload = ExplorerLookupResponse(
        entity_type=ExplorerEntityType.TASK,
        entity_id="abc",
        canonical={"task_id": "abc"},
    )
    assert payload.entity_type == ExplorerEntityType.TASK
    assert payload.canonical["task_id"] == "abc"


def test_deep_link_context_defaults():
    context = ExplorerDeepLinkContext(entity_type=ExplorerEntityType.TASK, entity_id="abc")
    assert context.view == ExplorerViewMode.LOOKUP
    assert context.mode == ExplorerMode.GUIDED


def test_guided_insights_contract_shape():
    payload = ExplorerGuidedInsightsResponse.model_validate(
        {
            "generated_at": "2026-02-13T12:00:00",
            "pulse": {
                "generated_at": "2026-02-13T12:00:00",
                "metrics": [
                    {
                        "key": "open_tasks",
                        "label": "Open Tasks",
                        "value": 12,
                        "status": "elevated",
                    }
                ],
            },
            "notable_events": [
                {
                    "notable_id": "evt-1:decision_recorded",
                    "title": "Decision Recorded",
                    "summary": "because",
                    "event_type": "decision_recorded",
                    "event_id": "evt-1",
                    "timestamp": "2026-02-13T12:00:00",
                    "ranking": {
                        "severity": "info",
                        "composite_score": 5.4,
                        "factors": [
                            {
                                "key": "recency",
                                "label": "Recency",
                                "value": 2.5,
                            }
                        ],
                    },
                    "evidence_refs": [
                        {
                            "view": "timeline",
                            "entity_type": "task",
                            "entity_id": "task-1",
                            "reason": "Inspect timeline",
                        }
                    ],
                }
            ],
        }
    )

    assert payload.pulse.metrics[0].key == "open_tasks"
    assert payload.notable_events[0].ranking.factors[0].key == "recency"
