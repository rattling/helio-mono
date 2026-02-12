"""Tests for attention API endpoints (Milestone 6)."""

from fastapi.testclient import TestClient

from services.api.main import app

client = TestClient(app)


def _seed_task(payload: dict):
    response = client.post("/api/v1/tasks/ingest", json=payload)
    assert response.status_code == 201
    return response.json()["task_id"]


class TestAttentionAPI:
    def test_attention_today_and_week(self, monkeypatch, tmp_path):
        event_store_path = tmp_path / "events"
        event_store_path.mkdir()
        db_path = tmp_path / "projections" / "attention.db"
        db_path.parent.mkdir(parents=True)

        monkeypatch.setenv("EVENT_STORE_PATH", str(event_store_path))
        monkeypatch.setenv("PROJECTIONS_DB_PATH", str(db_path))
        monkeypatch.setenv("ENV", "dev")

        _seed_task(
            {
                "title": "Urgent item",
                "source": "api",
                "source_ref": "attn-001",
                "priority": "p0",
                "due_at": "2026-02-13T09:00:00",
            }
        )
        _seed_task(
            {
                "title": "Important no due",
                "source": "api",
                "source_ref": "attn-002",
                "priority": "p1",
            }
        )

        today = client.get("/attention/today")
        assert today.status_code == 200
        payload = today.json()
        assert "top_actionable" in payload
        assert payload["top_actionable"]
        assert "urgency_explanation" in payload["top_actionable"][0]

        week = client.get("/attention/week")
        assert week.status_code == 200
        week_payload = week.json()
        assert "due_this_week" in week_payload
        assert "high_priority_without_due" in week_payload
        assert "blocked_summary" in week_payload

        run = client.post("/attention/run")
        assert run.status_code == 200
        assert run.json()["status"] == "ok"

    def test_attention_shadow_fallback(self, monkeypatch, tmp_path):
        event_store_path = tmp_path / "events"
        event_store_path.mkdir()
        db_path = tmp_path / "projections" / "attention-fallback.db"
        db_path.parent.mkdir(parents=True)

        monkeypatch.setenv("EVENT_STORE_PATH", str(event_store_path))
        monkeypatch.setenv("PROJECTIONS_DB_PATH", str(db_path))
        monkeypatch.setenv("ENV", "dev")

        _seed_task(
            {
                "title": "Shadow fallback task",
                "source": "api",
                "source_ref": "attn-fallback-001",
                "priority": "p2",
            }
        )

        # Monkeypatch ranker method to simulate service failure and verify fallback.
        from services.learning.ranker import ShadowRanker

        original_method = ShadowRanker.score

        def _boom(self, features):
            raise RuntimeError("boom")

        ShadowRanker.score = _boom
        try:
            today = client.get("/attention/today")
            assert today.status_code == 200
            top = today.json()["top_actionable"][0]
            assert top["shadow_score"] is None
        finally:
            ShadowRanker.score = original_method
