"""Core event schemas for the Helionyx event log."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Event types in the system."""

    # Ingestion events
    MESSAGE_INGESTED = "message_ingested"
    ARTIFACT_RECORDED = "artifact_recorded"

    # Extraction events
    OBJECT_EXTRACTED = "object_extracted"

    # Decision events (for future milestones)
    DECISION_RECORDED = "decision_recorded"


class SourceType(str, Enum):
    """Input source types."""

    CHATGPT_DUMP = "chatgpt_dump"
    TELEGRAM = "telegram"
    CLI = "cli"
    API = "api"


class ArtifactType(str, Enum):
    """Types of artifacts recorded."""

    RAW_MESSAGE = "raw_message"
    LLM_PROMPT = "llm_prompt"
    LLM_RESPONSE = "llm_response"
    SUMMARY = "summary"
    EXTRACTED_OBJECT = "extracted_object"


class BaseEvent(BaseModel):
    """Base event schema - all events extend this."""

    event_id: UUID = Field(default_factory=uuid4)
    event_type: EventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MessageIngestedEvent(BaseEvent):
    """Event recording a message input from any source."""

    event_type: EventType = EventType.MESSAGE_INGESTED
    source: SourceType
    source_id: str  # Original ID from source system
    content: str
    author: Optional[str] = None  # User or assistant
    conversation_id: Optional[str] = None  # For grouping related messages


class ArtifactRecordedEvent(BaseEvent):
    """Event recording an artifact (prompt, response, summary, etc)."""

    event_type: EventType = EventType.ARTIFACT_RECORDED
    artifact_type: ArtifactType
    content: str
    related_event_id: Optional[UUID] = None  # Link to triggering event
    metadata: dict[str, Any] = Field(default_factory=dict)


class ObjectExtractedEvent(BaseEvent):
    """Event recording extraction of a structured object."""

    event_type: EventType = EventType.OBJECT_EXTRACTED
    object_type: str  # "todo", "note", "track"
    object_data: dict[str, Any]
    source_event_id: UUID  # Event that triggered extraction
    extraction_confidence: Optional[float] = None


class DecisionRecordedEvent(BaseEvent):
    """Event recording a decision (future milestone)."""

    event_type: EventType = EventType.DECISION_RECORDED
    decision_data: dict[str, Any]
    rationale: Optional[str] = None
