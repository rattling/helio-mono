"""
Shared contracts for inter-service communication.

This package defines:
- Event schemas (events.py)
- Object schemas (objects.py)
- Service protocols/interfaces (protocols.py)

All services must use these contracts for communication.
Contract changes require explicit coordination and versioning.
"""

from shared.contracts.events import (
    ArtifactRecordedEvent,
    ArtifactType,
    BaseEvent,
    DecisionRecordedEvent,
    EventType,
    MessageIngestedEvent,
    ObjectExtractedEvent,
    SourceType,
)
from shared.contracts.objects import (
    ExtractedObject,
    ExtractionResult,
    LLMServiceError,
    Note,
    ObjectType,
    Todo,
    TodoPriority,
    TodoStatus,
    Track,
    TrackStatus,
)
from shared.contracts.protocols import (
    EventStoreProtocol,
    ExtractionServiceProtocol,
    LLMServiceProtocol,
    QueryServiceProtocol,
)
from shared.contracts.tasks import (
    TASK_LABEL_NEEDS_REVIEW,
    Task,
    TaskExplanation,
    TaskIngestRequest,
    TaskIngestResult,
    TaskLinkRequest,
    TaskPatchRequest,
    TaskPriority,
    TaskSnoozeRequest,
    TaskStatus,
)

__all__ = [
    # Events
    "BaseEvent",
    "EventType",
    "SourceType",
    "ArtifactType",
    "MessageIngestedEvent",
    "ArtifactRecordedEvent",
    "ObjectExtractedEvent",
    "DecisionRecordedEvent",
    # Objects
    "ObjectType",
    "TodoStatus",
    "TodoPriority",
    "Todo",
    "Note",
    "TrackStatus",
    "Track",
    "ExtractedObject",
    "ExtractionResult",
    "LLMServiceError",
    # Protocols
    "EventStoreProtocol",
    "ExtractionServiceProtocol",
    "LLMServiceProtocol",
    "QueryServiceProtocol",

    # Tasks (M5)
    "TASK_LABEL_NEEDS_REVIEW",
    "TaskStatus",
    "TaskPriority",
    "TaskExplanation",
    "Task",
    "TaskIngestRequest",
    "TaskIngestResult",
    "TaskPatchRequest",
    "TaskSnoozeRequest",
    "TaskLinkRequest",
]
