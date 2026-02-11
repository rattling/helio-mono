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
]
