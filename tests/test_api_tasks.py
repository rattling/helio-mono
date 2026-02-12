"""Tests for task API endpoints (Milestone 5)."""

import pytest
from fastapi.testclient import TestClient

from services.api.main import app

client = TestClient(app)


class TestTaskEndpoints:
    """Test task lifecycle endpoints."""

    def test_task_ingest_is_idempotent(self, monkeypatch, tmp_path):
        event_store_path = tmp_path / "events"
        event_store_path.mkdir()
        db_path = tmp_path / "projections" / "tasks.db"
        db_path.parent.mkdir(parents=True)

        monkeypatch.setenv("EVENT_STORE_PATH", str(event_store_path))
        monkeypatch.setenv("PROJECTIONS_DB_PATH", str(db_path))
        monkeypatch.setenv("ENV", "dev")

        payload = {
            "title": "Prepare milestone report",
            "body": "Summarize progress and blockers",
            "source": "api",
            "source_ref": "task-ingest-001",
            "priority": "p1",
            "labels": ["work"],
        }

        first = client.post("/api/v1/tasks/ingest", json=payload)
        assert first.status_code == 201
        first_data = first.json()
        assert first_data["created"] is True

        second = client.post("/api/v1/tasks/ingest", json=payload)
        assert second.status_code == 201
        second_data = second.json()
        assert second_data["created"] is False
        assert second_data["task_id"] == first_data["task_id"]

    def test_task_mutation_endpoints(self, monkeypatch, tmp_path):
        event_store_path = tmp_path / "events"
        event_store_path.mkdir()
        db_path = tmp_path / "projections" / "tasks.db"
        db_path.parent.mkdir(parents=True)

        monkeypatch.setenv("EVENT_STORE_PATH", str(event_store_path))
        monkeypatch.setenv("PROJECTIONS_DB_PATH", str(db_path))
        monkeypatch.setenv("ENV", "dev")

        ingest = client.post(
            "/api/v1/tasks/ingest",
            json={
                "title": "Refine API contract",
                "source": "api",
                "source_ref": "task-mutation-001",
            },
        )
        assert ingest.status_code == 201
        task_id = ingest.json()["task_id"]

        patch = client.patch(f"/api/v1/tasks/{task_id}", json={"priority": "p0"})
        assert patch.status_code == 200
        assert patch.json()["priority"] == "p0"

        complete = client.post(f"/api/v1/tasks/{task_id}/complete")
        assert complete.status_code == 200
        assert complete.json()["status"] == "done"

    def test_task_snooze_and_link(self, monkeypatch, tmp_path):
        event_store_path = tmp_path / "events"
        event_store_path.mkdir()
        db_path = tmp_path / "projections" / "tasks.db"
        db_path.parent.mkdir(parents=True)

        monkeypatch.setenv("EVENT_STORE_PATH", str(event_store_path))
        monkeypatch.setenv("PROJECTIONS_DB_PATH", str(db_path))
        monkeypatch.setenv("ENV", "dev")

        parent = client.post(
            "/api/v1/tasks/ingest",
            json={"title": "Parent task", "source": "api", "source_ref": "task-parent"},
        )
        child = client.post(
            "/api/v1/tasks/ingest",
            json={"title": "Child task", "source": "api", "source_ref": "task-child"},
        )

        parent_id = parent.json()["task_id"]
        child_id = child.json()["task_id"]

        snooze = client.post(
            f"/api/v1/tasks/{child_id}/snooze",
            json={"until": "2026-03-01T09:00:00", "rationale": "Waiting on input"},
        )
        assert snooze.status_code == 200
        assert snooze.json()["status"] == "snoozed"

        linked = client.post(
            f"/api/v1/tasks/{child_id}/link",
            json={"blocked_by": [parent_id], "rationale": "Depends on parent"},
        )
        assert linked.status_code == 200
        assert linked.json()["status"] == "blocked"
        assert parent_id in linked.json()["blocked_by"]

    def test_review_queue_prioritizes_needs_review(self, monkeypatch, tmp_path):
        event_store_path = tmp_path / "events"
        event_store_path.mkdir()
        db_path = tmp_path / "projections" / "tasks.db"
        db_path.parent.mkdir(parents=True)

        monkeypatch.setenv("EVENT_STORE_PATH", str(event_store_path))
        monkeypatch.setenv("PROJECTIONS_DB_PATH", str(db_path))
        monkeypatch.setenv("ENV", "dev")

        first = client.post(
            "/api/v1/tasks/ingest",
            json={
                "title": "Investigate flaky test",
                "body": "Intermittent failures in CI",
                "source": "api",
                "source_ref": "dedup-a",
            },
        )
        assert first.status_code == 201

        second = client.post(
            "/api/v1/tasks/ingest",
            json={
                "title": "Investigate flaky test",
                "body": "Intermittent failures in CI",
                "source": "api",
                "source_ref": "dedup-b",
            },
        )
        assert second.status_code == 201

        queue = client.get("/api/v1/tasks/review/queue")
        assert queue.status_code == 200
        data = queue.json()
        assert len(data) >= 2
        assert "needs_review" in data[0].get("labels", [])

    def test_get_task_not_found(self, monkeypatch, tmp_path):
        event_store_path = tmp_path / "events"
        event_store_path.mkdir()
        db_path = tmp_path / "projections" / "tasks.db"
        db_path.parent.mkdir(parents=True)

        monkeypatch.setenv("EVENT_STORE_PATH", str(event_store_path))
        monkeypatch.setenv("PROJECTIONS_DB_PATH", str(db_path))
        monkeypatch.setenv("ENV", "dev")

        response = client.get("/api/v1/tasks/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404

    def test_suggest_dependencies_and_apply(self, monkeypatch, tmp_path):
        event_store_path = tmp_path / "events"
        event_store_path.mkdir()
        db_path = tmp_path / "projections" / "tasks-suggest.db"
        db_path.parent.mkdir(parents=True)

        monkeypatch.setenv("EVENT_STORE_PATH", str(event_store_path))
        monkeypatch.setenv("PROJECTIONS_DB_PATH", str(db_path))
        monkeypatch.setenv("ENV", "dev")

        parent = client.post(
            "/api/v1/tasks/ingest",
            json={
                "title": "Parent dependency",
                "source": "api",
                "source_ref": "suggest-parent-001",
                "project": "proj-a",
                "labels": ["ops"],
                "priority": "p1",
            },
        )
        child = client.post(
            "/api/v1/tasks/ingest",
            json={
                "title": "Child task",
                "source": "api",
                "source_ref": "suggest-child-001",
                "project": "proj-a",
                "labels": ["ops"],
                "priority": "p2",
            },
        )
        parent_id = parent.json()["task_id"]
        child_id = child.json()["task_id"]

        suggest = client.post(f"/api/v1/tasks/{child_id}/suggest-dependencies")
        assert suggest.status_code == 200
        suggestions = suggest.json()
        assert suggestions
        suggestion = suggestions[0]
        assert suggestion["suggestion_type"] == "dependency"

        apply_response = client.post(
            f"/api/v1/tasks/{child_id}/apply-suggestion",
            json={
                "suggestion_id": suggestion["suggestion_id"],
                "suggestion_type": "dependency",
                "payload": suggestion["payload"],
                "rationale": "Looks right",
            },
        )
        assert apply_response.status_code == 200
        updated = apply_response.json()["task"]
        assert updated["status"] == "blocked"
        assert parent_id in updated["blocked_by"]

    def test_suggest_split_apply_and_reject(self, monkeypatch, tmp_path):
        event_store_path = tmp_path / "events"
        event_store_path.mkdir()
        db_path = tmp_path / "projections" / "tasks-split.db"
        db_path.parent.mkdir(parents=True)

        monkeypatch.setenv("EVENT_STORE_PATH", str(event_store_path))
        monkeypatch.setenv("PROJECTIONS_DB_PATH", str(db_path))
        monkeypatch.setenv("ENV", "dev")

        base = client.post(
            "/api/v1/tasks/ingest",
            json={
                "title": "Plan migration",
                "source": "api",
                "source_ref": "split-task-001",
                "project": "proj-m6",
            },
        )
        task_id = base.json()["task_id"]

        suggest = client.post(f"/api/v1/tasks/{task_id}/suggest-split")
        assert suggest.status_code == 200
        split_suggestion = suggest.json()[0]
        assert split_suggestion["suggestion_type"] == "split"

        edited_payload = {
            "subtasks": split_suggestion["payload"]["subtasks"][:2],
            "project": "proj-m6",
        }

        apply_response = client.post(
            f"/api/v1/tasks/{task_id}/apply-suggestion",
            json={
                "suggestion_id": split_suggestion["suggestion_id"],
                "suggestion_type": "split",
                "payload": split_suggestion["payload"],
                "edited_payload": edited_payload,
                "rationale": "Use only two steps",
            },
        )
        assert apply_response.status_code == 200
        body = apply_response.json()
        assert body["applied"] is True
        assert len(body["created_task_ids"]) == 2

        reject_response = client.post(
            f"/api/v1/tasks/{task_id}/reject-suggestion",
            json={
                "suggestion_id": split_suggestion["suggestion_id"],
                "suggestion_type": "split",
                "rationale": "No longer needed",
            },
        )
        assert reject_response.status_code == 200
        assert reject_response.json()["rejected"] is True
