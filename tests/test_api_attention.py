"""Tests for attention API endpoints (Milestone 6)."""

from fastapi.testclient import TestClient

from services.api.main import app

client = TestClient(app)


def _seed_task(payload: dict):
    response = client.post("/api/v1/tasks/ingest", json=payload)
    assert response.status_code == 201
    return response.json()["task_id"]


def _result(score: float, confidence: float, explanation: str):
    from services.learning.ranker import ShadowRankerResult

    return ShadowRankerResult(
        score=score,
        confidence=confidence,
        explanation=explanation,
        usefulness_score=max(0.0, min(1.0, score)),
        timing_fit_score=max(0.0, min(1.0, score - 0.1)),
        interrupt_cost_score=max(0.0, min(1.0, 1.0 - score)),
    )


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
        assert "deterministic_bucket_id" in payload["top_actionable"][0]
        assert "deterministic_bucket_rank" in payload["top_actionable"][0]
        assert "ranking_explanation" in payload["top_actionable"][0]
        assert "deterministic-only" in payload["top_actionable"][0]["ranking_explanation"]
        assert "personalization_applied" in payload["top_actionable"][0]
        assert payload["top_actionable"][0]["personalization_applied"] is False
        assert "usefulness_score" in payload["top_actionable"][0]
        assert "timing_fit_score" in payload["top_actionable"][0]
        assert "interrupt_cost_score" in payload["top_actionable"][0]

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
            assert top["model_score"] is None
            assert top["personalization_policy"] == "deterministic_only"
        finally:
            ShadowRanker.score = original_method

    def test_attention_bounded_personalization_reorders_in_bucket_only(self, monkeypatch, tmp_path):
        event_store_path = tmp_path / "events"
        event_store_path.mkdir()
        db_path = tmp_path / "projections" / "attention-bounded.db"
        db_path.parent.mkdir(parents=True)

        monkeypatch.setenv("EVENT_STORE_PATH", str(event_store_path))
        monkeypatch.setenv("PROJECTIONS_DB_PATH", str(db_path))
        monkeypatch.setenv("ENV", "dev")
        monkeypatch.setenv("ATTENTION_BOUNDED_PERSONALIZATION_ENABLED", "true")
        monkeypatch.setenv("SHADOW_RANKER_ENABLED", "true")
        monkeypatch.setenv("SHADOW_RANKER_CONFIDENCE_THRESHOLD", "0.6")

        first_id = _seed_task(
            {
                "title": "High priority far due",
                "source": "api",
                "source_ref": "attn-bounded-001",
                "priority": "p1",
                "due_at": "2026-03-20T09:00:00",
            }
        )
        second_id = _seed_task(
            {
                "title": "High priority no due",
                "source": "api",
                "source_ref": "attn-bounded-002",
                "priority": "p1",
            }
        )

        from services.learning.ranker import ShadowRanker

        original_method = ShadowRanker.score

        def _score(self, features):
            if features.get("has_due") == 0.0:
                return _result(score=0.95, confidence=0.9, explanation="high relevance")
            return _result(score=0.20, confidence=0.9, explanation="lower relevance")

        ShadowRanker.score = _score
        try:
            today = client.get("/attention/today")
            assert today.status_code == 200
            items = today.json()["top_actionable"]
            ids = [item["task_id"] for item in items]
            assert ids.index(second_id) < ids.index(first_id)

            assert any(item["personalization_applied"] is True for item in items)
            assert all(item["personalization_policy"] == "bounded_in_bucket" for item in items)
            assert any(
                "deterministic=" in item["ranking_explanation"]
                and "learned=" in item["ranking_explanation"]
                for item in items
            )
        finally:
            ShadowRanker.score = original_method

    def test_attention_bounded_personalization_low_confidence_falls_back(
        self, monkeypatch, tmp_path
    ):
        event_store_path = tmp_path / "events"
        event_store_path.mkdir()
        db_path = tmp_path / "projections" / "attention-bounded-low-confidence.db"
        db_path.parent.mkdir(parents=True)

        monkeypatch.setenv("EVENT_STORE_PATH", str(event_store_path))
        monkeypatch.setenv("PROJECTIONS_DB_PATH", str(db_path))
        monkeypatch.setenv("ENV", "dev")
        monkeypatch.setenv("ATTENTION_BOUNDED_PERSONALIZATION_ENABLED", "true")
        monkeypatch.setenv("SHADOW_RANKER_ENABLED", "true")
        monkeypatch.setenv("SHADOW_RANKER_CONFIDENCE_THRESHOLD", "0.95")

        _seed_task(
            {
                "title": "Low confidence candidate 1",
                "source": "api",
                "source_ref": "attn-bounded-low-001",
                "priority": "p1",
            }
        )
        _seed_task(
            {
                "title": "Low confidence candidate 2",
                "source": "api",
                "source_ref": "attn-bounded-low-002",
                "priority": "p1",
            }
        )

        from services.learning.ranker import ShadowRanker

        original_method = ShadowRanker.score

        def _score(self, features):
            return _result(
                score=0.99,
                confidence=0.6,
                explanation="below threshold",
            )

        ShadowRanker.score = _score
        try:
            today = client.get("/attention/today")
            assert today.status_code == 200
            items = today.json()["top_actionable"]
            assert all(item["personalization_applied"] is False for item in items)
            assert all(item["personalization_policy"] == "bounded_in_bucket" for item in items)
        finally:
            ShadowRanker.score = original_method

    def test_attention_personalization_mode_deterministic_rollback(self, monkeypatch, tmp_path):
        event_store_path = tmp_path / "events"
        event_store_path.mkdir()
        db_path = tmp_path / "projections" / "attention-mode-rollback.db"
        db_path.parent.mkdir(parents=True)

        monkeypatch.setenv("EVENT_STORE_PATH", str(event_store_path))
        monkeypatch.setenv("PROJECTIONS_DB_PATH", str(db_path))
        monkeypatch.setenv("ENV", "dev")
        monkeypatch.setenv("ATTENTION_PERSONALIZATION_MODE", "bounded")
        monkeypatch.setenv("SHADOW_RANKER_CONFIDENCE_THRESHOLD", "0.6")

        _seed_task(
            {
                "title": "Rollback candidate A",
                "source": "api",
                "source_ref": "attn-mode-001",
                "priority": "p1",
                "due_at": "2026-03-20T09:00:00",
            }
        )
        _seed_task(
            {
                "title": "Rollback candidate B",
                "source": "api",
                "source_ref": "attn-mode-002",
                "priority": "p1",
            }
        )

        from services.learning.ranker import ShadowRanker

        original_method = ShadowRanker.score

        def _score(self, features):
            if features.get("has_due") == 0.0:
                return _result(score=0.95, confidence=0.95, explanation="prefer B")
            return _result(score=0.10, confidence=0.95, explanation="deprioritize A")

        ShadowRanker.score = _score
        try:
            bounded = client.get("/attention/today")
            assert bounded.status_code == 200
            bounded_items = bounded.json()["top_actionable"]
            assert any(item["personalization_applied"] is True for item in bounded_items)
            assert all(
                item["personalization_policy"] == "bounded_in_bucket" for item in bounded_items
            )

            # One-command rollback path via mode switch.
            monkeypatch.setenv("ATTENTION_PERSONALIZATION_MODE", "deterministic")
            monkeypatch.setenv("SHADOW_RANKER_ENABLED", "true")
            monkeypatch.setenv("ATTENTION_BOUNDED_PERSONALIZATION_ENABLED", "true")

            deterministic = client.get("/attention/today")
            assert deterministic.status_code == 200
            deterministic_items = deterministic.json()["top_actionable"]
            assert all(
                item["personalization_policy"] == "deterministic_only"
                for item in deterministic_items
            )
            assert all(item["personalization_applied"] is False for item in deterministic_items)
            assert all(item["model_score"] is None for item in deterministic_items)
        finally:
            ShadowRanker.score = original_method
