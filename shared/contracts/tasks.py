"""Task contracts (Milestone 5).

Tasks are first-class, event-sourced objects.
Projections are derived from task lifecycle events in the append-only event log.

This module intentionally defines contracts only (schemas/enums), not persistence logic.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from shared.contracts.events import SourceType


TASK_LABEL_NEEDS_REVIEW = "needs_review"


class TaskStatus(str, Enum):
    OPEN = "open"
    BLOCKED = "blocked"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"
    SNOOZED = "snoozed"


class TaskPriority(str, Enum):
    P0 = "p0"
    P1 = "p1"
    P2 = "p2"
    P3 = "p3"


class TaskExplanation(BaseModel):
    ts: datetime = Field(default_factory=datetime.utcnow)
    actor: str
    action: str
    rationale: str


class Task(BaseModel):
    """Canonical Task read model.

    Note: In Helionyx, the source of truth is the event log.
    This object represents the *canonical* shape that adapters/projections should converge on.
    """

    task_id: UUID = Field(default_factory=uuid4)
    title: str
    body: Optional[str] = None

    status: TaskStatus = TaskStatus.OPEN
    priority: TaskPriority = TaskPriority.P2

    due_at: Optional[datetime] = None
    do_not_start_before: Optional[datetime] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    source: SourceType
    source_ref: str

    dedup_group_id: Optional[str] = None

    # Labels are intentionally free-form.
    # Reserved label(s):
    # - TASK_LABEL_NEEDS_REVIEW: inferred tasks that may warrant review.
    labels: list[str] = Field(default_factory=list)
    project: Optional[str] = None
    blocked_by: list[UUID] = Field(default_factory=list)

    agent_notes: Optional[str] = None
    explanations: list[TaskExplanation] = Field(default_factory=list)


class TaskIngestRequest(BaseModel):
    """Idempotent ingest request.

    Idempotency key is `source_ref` within the given `source` domain.
    
    Note: Milestone 5 explicitly defers any conversational prompting to fill
    missing details; missing fields may remain null and be refined later.
    """

    title: str
    body: Optional[str] = None

    source: SourceType
    source_ref: str

    priority: Optional[TaskPriority] = None
    due_at: Optional[datetime] = None
    do_not_start_before: Optional[datetime] = None

    labels: list[str] = Field(default_factory=list)
    project: Optional[str] = None


class TaskIngestResult(BaseModel):
    """Outcome of ingest.

    `created` indicates whether a new task was created, vs returning an existing task.
    `decision_rationale` is an optional human-legible string for auditability.
    """

    task_id: UUID
    created: bool
    decision_rationale: Optional[str] = None


class TaskPatchRequest(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_at: Optional[datetime] = None
    do_not_start_before: Optional[datetime] = None
    labels: Optional[list[str]] = None
    project: Optional[str] = None


class TaskSnoozeRequest(BaseModel):
    until: datetime
    rationale: Optional[str] = None


class TaskLinkRequest(BaseModel):
    blocked_by: list[UUID] = Field(default_factory=list)
    rationale: Optional[str] = None
