"""Object schemas for extracted structured data."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ObjectType(str, Enum):
    """Types of objects that can be extracted."""

    TODO = "todo"
    NOTE = "note"
    TRACK = "track"


class TodoStatus(str, Enum):
    """Status of a todo item."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TodoPriority(str, Enum):
    """Priority levels for todos."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Todo(BaseModel):
    """A todo item extracted from conversation."""

    object_id: UUID = Field(default_factory=uuid4)
    object_type: ObjectType = ObjectType.TODO
    title: str
    description: Optional[str] = None
    status: TodoStatus = TodoStatus.PENDING
    priority: TodoPriority = TodoPriority.MEDIUM
    due_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    tags: list[str] = Field(default_factory=list)
    source_event_id: Optional[UUID] = None  # Event that created this


class Note(BaseModel):
    """A note extracted from conversation."""

    object_id: UUID = Field(default_factory=uuid4)
    object_type: ObjectType = ObjectType.NOTE
    title: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    tags: list[str] = Field(default_factory=list)
    source_event_id: Optional[UUID] = None


class TrackStatus(str, Enum):
    """Status of a tracking item."""

    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class Track(BaseModel):
    """A tracking item for monitoring something over time."""

    object_id: UUID = Field(default_factory=uuid4)
    object_type: ObjectType = ObjectType.TRACK
    title: str
    description: Optional[str] = None
    status: TrackStatus = TrackStatus.ACTIVE
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: Optional[datetime] = None
    tags: list[str] = Field(default_factory=list)
    source_event_id: Optional[UUID] = None
    check_in_frequency: Optional[str] = None  # "daily", "weekly", etc.


# Union type for all objects
ExtractedObject = Todo | Note | Track
