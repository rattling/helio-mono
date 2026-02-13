"""Contract tests for Milestone 11 Lab models."""

from shared.contracts import (
    LabControlUpdateRequest,
    LabExperimentRunRequest,
    LabOverviewResponse,
    LabPersonalizationMode,
)


def test_lab_overview_contract_shape():
    payload = LabOverviewResponse.model_validate(
        {
            "generated_at": "2026-02-13T12:00:00",
            "diagnostics": {
                "generated_at": "2026-02-13T12:00:00",
                "metrics": [
                    {
                        "key": "open_tasks",
                        "label": "Open Tasks",
                        "value": 12,
                        "status": "normal",
                    }
                ],
            },
            "config": {
                "mode": "shadow",
                "shadow_ranker_enabled": True,
                "bounded_personalization_enabled": False,
                "shadow_confidence_threshold": 0.6,
            },
            "fallback_state": {"deterministic_fallback_active": False},
        }
    )
    assert payload.config.mode == LabPersonalizationMode.SHADOW


def test_lab_control_request_bounds():
    req = LabControlUpdateRequest(
        actor="operator",
        rationale="test",
        mode=LabPersonalizationMode.BOUNDED,
        shadow_confidence_threshold=0.75,
    )
    assert req.shadow_confidence_threshold == 0.75


def test_lab_experiment_request_shape():
    req = LabExperimentRunRequest(
        actor="operator",
        rationale="compare",
        candidate_mode=LabPersonalizationMode.DETERMINISTIC,
        candidate_shadow_confidence_threshold=0.5,
    )
    assert req.candidate_mode == LabPersonalizationMode.DETERMINISTIC
