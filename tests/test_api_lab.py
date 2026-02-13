"""API tests for Milestone 11 Lab endpoints."""

from fastapi.testclient import TestClient

from services.api.main import app

client = TestClient(app)


def _set_env(monkeypatch, tmp_path):
    event_store_path = tmp_path / "events"
    event_store_path.mkdir(exist_ok=True)
    db_path = tmp_path / "projections" / "lab.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("EVENT_STORE_PATH", str(event_store_path))
    monkeypatch.setenv("PROJECTIONS_DB_PATH", str(db_path))
    monkeypatch.setenv("ENV", "dev")


def test_lab_overview(monkeypatch, tmp_path):
    _set_env(monkeypatch, tmp_path)

    response = client.get("/api/v1/lab/overview")
    assert response.status_code == 200
    payload = response.json()
    assert "diagnostics" in payload
    assert "config" in payload
    assert "mode" in payload["config"]


def test_lab_controls_and_rollback(monkeypatch, tmp_path):
    _set_env(monkeypatch, tmp_path)

    update = client.post(
        "/api/v1/lab/controls",
        json={
            "actor": "qa",
            "rationale": "enable bounded",
            "mode": "bounded",
            "shadow_confidence_threshold": 0.65,
        },
    )
    assert update.status_code == 200
    assert update.json()["effective_config"]["mode"] == "bounded"

    rollback = client.post(
        "/api/v1/lab/rollback",
        json={
            "actor": "qa",
            "rationale": "restore deterministic",
        },
    )
    assert rollback.status_code == 200
    assert rollback.json()["effective_config"]["mode"] == "deterministic"


def test_lab_experiment_run_history_apply(monkeypatch, tmp_path):
    _set_env(monkeypatch, tmp_path)

    run = client.post(
        "/api/v1/lab/experiments/run",
        json={
            "actor": "qa",
            "rationale": "compare shadow",
            "candidate_mode": "shadow",
            "candidate_shadow_confidence_threshold": 0.7,
        },
    )
    assert run.status_code == 200
    run_payload = run.json()
    run_id = run_payload["run_id"]

    history = client.get("/api/v1/lab/experiments/history")
    assert history.status_code == 200
    assert any(item["run_id"] == run_id for item in history.json()["runs"])

    apply_response = client.post(
        f"/api/v1/lab/experiments/{run_id}/apply",
        json={
            "actor": "qa",
            "rationale": "apply tested candidate",
            "action": "apply",
        },
    )
    assert apply_response.status_code == 200
    assert apply_response.json()["status"] == "updated"


def test_lab_experiment_apply_blocked_by_safety_gate(monkeypatch, tmp_path):
    _set_env(monkeypatch, tmp_path)

    run = client.post(
        "/api/v1/lab/experiments/run",
        json={
            "actor": "qa",
            "rationale": "unsafe candidate",
            "candidate_mode": "bounded",
            "candidate_shadow_confidence_threshold": 0.2,
        },
    )
    assert run.status_code == 200
    run_id = run.json()["run_id"]

    blocked = client.post(
        f"/api/v1/lab/experiments/{run_id}/apply",
        json={
            "actor": "qa",
            "rationale": "attempt unsafe apply",
            "action": "apply",
        },
    )
    assert blocked.status_code == 409
