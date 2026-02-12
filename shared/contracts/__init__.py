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
    AttentionBucket,
    AttentionCandidate,
    AttentionScoringComputedEvent,
    ArtifactRecordedEvent,
    ArtifactType,
    BaseEvent,
    DecisionRecordedEvent,
    EventType,
    FeatureSnapshotRecordedEvent,
    MessageIngestedEvent,
    ModelScoreRecordedEvent,
    ObjectExtractedEvent,
    ReminderDismissedEvent,
    ReminderSentEvent,
    ReminderSnoozedEvent,
    SourceType,
    SuggestionAppliedEvent,
    SuggestionEditedEvent,
    SuggestionRejectedEvent,
    SuggestionShownEvent,
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
    SuggestionType,
    TASK_LABEL_NEEDS_REVIEW,
    Task,
    TaskApplySuggestionRequest,
    TaskExplanation,
    TaskIngestRequest,
    TaskIngestResult,
    TaskLinkRequest,
    TaskPatchRequest,
    TaskPriority,
    TaskRejectSuggestionRequest,
    TaskSnoozeRequest,
    TaskSuggestion,
    TaskStatus,
)

__all__ = [
    # Events
    "BaseEvent",
    "EventType",
    "AttentionBucket",
    "AttentionCandidate",
    "SourceType",
    "ArtifactType",
    "MessageIngestedEvent",
    "ArtifactRecordedEvent",
    "ObjectExtractedEvent",
    "DecisionRecordedEvent",
    "AttentionScoringComputedEvent",
    "SuggestionShownEvent",
    "SuggestionAppliedEvent",
    "SuggestionRejectedEvent",
    "SuggestionEditedEvent",
    "ReminderSentEvent",
    "ReminderDismissedEvent",
    "ReminderSnoozedEvent",
    "FeatureSnapshotRecordedEvent",
    "ModelScoreRecordedEvent",
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
    "SuggestionType",
    "TaskStatus",
    "TaskPriority",
    "TaskExplanation",
    "Task",
    "TaskIngestRequest",
    "TaskIngestResult",
    "TaskPatchRequest",
    "TaskSnoozeRequest",
    "TaskLinkRequest",
    "TaskSuggestion",
    "TaskApplySuggestionRequest",
    "TaskRejectSuggestionRequest",
]
