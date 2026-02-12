"""Tests for Telegram formatters."""

import pytest
from services.adapters.telegram.formatters import (
    format_todos_list,
    format_notes_list,
    format_tracks_list,
    format_tasks_list,
    format_due_date,
)


def test_format_todos_list_empty():
    """Test formatting empty todo list."""
    result = format_todos_list([])
    assert result == "No todos found."


def test_format_todos_list_with_todos():
    """Test formatting todo list with items."""
    todos = [
        {
            "title": "Complete report",
            "priority": "high",
            "status": "pending",
            "due_date": None,
        },
        {
            "title": "Review code",
            "priority": "medium",
            "status": "pending",
            "due_date": None,
        },
    ]

    result = format_todos_list(todos)

    assert "Your Todos" in result
    assert "Complete report" in result
    assert "Review code" in result
    assert "🟠" in result  # High priority icon
    assert "🟡" in result  # Medium priority icon


def test_format_notes_list_empty():
    """Test formatting empty notes list."""
    result = format_notes_list([])
    assert result == "No notes found."


def test_format_notes_list_with_notes():
    """Test formatting notes list with items."""
    notes = [
        {
            "title": "Meeting notes",
            "content": "Important discussion about Q1 goals",
        },
        {
            "title": "Research",
            "content": "LLM integration patterns",
        },
    ]

    result = format_notes_list(notes)

    assert "Your Notes" in result
    assert "Meeting notes" in result
    assert "Research" in result


def test_format_tracks_list_empty():
    """Test formatting empty tracks list."""
    result = format_tracks_list([])
    assert result == "No tracking items found."


def test_format_tracks_list_with_tracks():
    """Test formatting tracks list with items."""
    tracks = [
        {
            "subject": "Project Alpha progress",
            "status": "active",
        },
        {
            "subject": "Team morale",
            "status": "active",
        },
    ]

    result = format_tracks_list(tracks)

    assert "Your Tracks" in result
    assert "Project Alpha progress" in result
    assert "Team morale" in result


def test_format_due_date_none():
    """Test formatting None due date."""
    result = format_due_date(None)
    assert result is None


def test_format_due_date_invalid():
    """Test formatting invalid due date."""
    result = format_due_date("invalid")
    assert result == "invalid"


def test_format_tasks_list_empty():
    """Test formatting empty task list."""
    result = format_tasks_list([])
    assert result == "No tasks found."


def test_format_tasks_list_with_tasks():
    """Test formatting task list with items."""
    tasks = [
        {
            "task_id": "12345678-1234-1234-1234-1234567890ab",
            "title": "Ship milestone",
            "priority": "p1",
            "status": "open",
            "is_stale": False,
        },
        {
            "task_id": "abcdefab-cdef-cdef-cdef-abcdefabcdef",
            "title": "Review queue",
            "priority": "p0",
            "status": "blocked",
            "is_stale": True,
        },
    ]

    result = format_tasks_list(tasks)

    assert "Your Tasks" in result
    assert "Ship milestone" in result
    assert "Review queue" in result
    assert "⚠️" in result
