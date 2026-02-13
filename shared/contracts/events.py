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

    # Milestone 6 attention + planning + learning events
    ATTENTION_SCORING_COMPUTED = "attention_scoring_computed"
    SUGGESTION_SHOWN = "suggestion_shown"
    SUGGESTION_APPLIED = "suggestion_applied"
    SUGGESTION_REJECTED = "suggestion_rejected"
    SUGGESTION_EDITED = "suggestion_edited"
    REMINDER_SENT = "reminder_sent"
    REMINDER_DISMISSED = "reminder_dismissed"
    REMINDER_SNOOZED = "reminder_snoozed"
    FEATURE_SNAPSHOT_RECORDED = "feature_snapshot_recorded"
    MODEL_SCORE_RECORDED = "model_score_recorded"
    FEEDBACK_EVIDENCE_RECORDED = "feedback_evidence_recorded"
    LAB_CONTROL_CHANGED = "lab_control_changed"
    LAB_EXPERIMENT_RUN = "lab_experiment_run"
    LAB_EXPERIMENT_APPLIED = "lab_experiment_applied"


class LearningTarget(str, Enum):
    """First-class learning targets for contextual feedback semantics."""

    USEFULNESS = "usefulness"
    TIMING_FIT = "timing_fit"
    INTERRUPT_COST = "interrupt_cost"


class AttentionBucket(str, Enum):
    """Deterministic attention buckets for bounded ranking."""

    URGENT_DUE_SOON = "urgent_due_soon"
    READY_HIGH_PRIORITY = "ready_high_priority"
    READY_NORMAL = "ready_normal"
    BLOCKED = "blocked"
    DEFERRED_OR_GATED = "deferred_or_gated"
    COMPLETED_OR_CANCELLED = "completed_or_cancelled"


class AttentionCandidate(BaseModel):
    """Typed attention candidate payload for queue snapshots and APIs."""

    task_id: str
    urgency_score: float
    explanation: str
    deterministic_bucket_id: AttentionBucket = AttentionBucket.READY_NORMAL
    deterministic_bucket_rank: int = 2
    deterministic_explanation: Optional[str] = None
    model_score: Optional[float] = None
    model_confidence: Optional[float] = None
    learned_explanation: Optional[str] = None
    usefulness_score: Optional[float] = None
    timing_fit_score: Optional[float] = None
    interrupt_cost_score: Optional[float] = None
    recommended_action: Optional[str] = None
    ranking_explanation: Optional[str] = None
    personalization_applied: bool = False
    personalization_policy: str = "deterministic_only"

    # Backward-compatible aliases used in existing M6 payloads.
    shadow_score: Optional[float] = None
    shadow_confidence: Optional[float] = None


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


class AttentionScoringComputedEvent(BaseEvent):
    """Event recording deterministic attention queue scoring output."""

    event_type: EventType = EventType.ATTENTION_SCORING_COMPUTED
    queue_name: str
    candidates: list[AttentionCandidate] = Field(default_factory=list)


class SuggestionShownEvent(BaseEvent):
    """Event recording suggestion candidates shown to user/operator."""

    event_type: EventType = EventType.SUGGESTION_SHOWN
    task_id: str
    suggestion_id: str
    suggestion_type: str
    suggestion_payload: dict[str, Any] = Field(default_factory=dict)
    rationale: Optional[str] = None


class SuggestionAppliedEvent(BaseEvent):
    """Event recording explicit user application of a suggestion."""

    event_type: EventType = EventType.SUGGESTION_APPLIED
    task_id: str
    suggestion_id: str
    suggestion_type: str
    applied_payload: dict[str, Any] = Field(default_factory=dict)
    rationale: Optional[str] = None


class SuggestionRejectedEvent(BaseEvent):
    """Event recording explicit user rejection of a suggestion."""

    event_type: EventType = EventType.SUGGESTION_REJECTED
    task_id: str
    suggestion_id: str
    suggestion_type: str
    rationale: Optional[str] = None


class SuggestionEditedEvent(BaseEvent):
    """Event recording user edits before suggestion apply."""

    event_type: EventType = EventType.SUGGESTION_EDITED
    task_id: str
    suggestion_id: str
    suggestion_type: str
    original_payload: dict[str, Any] = Field(default_factory=dict)
    edited_payload: dict[str, Any] = Field(default_factory=dict)
    rationale: Optional[str] = None


class ReminderSentEvent(BaseEvent):
    """Event recording reminder/digest delivery."""

    event_type: EventType = EventType.REMINDER_SENT
    reminder_type: str
    object_id: Optional[str] = None
    fingerprint: Optional[str] = None
    delivery_channel: str = "telegram"
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReminderDismissedEvent(BaseEvent):
    """Event recording explicit reminder dismissal feedback."""

    event_type: EventType = EventType.REMINDER_DISMISSED
    reminder_type: str
    object_id: Optional[str] = None
    fingerprint: Optional[str] = None
    rationale: Optional[str] = None
    followup_action_within_minutes: Optional[int] = None


class ReminderSnoozedEvent(BaseEvent):
    """Event recording explicit reminder snooze feedback."""

    event_type: EventType = EventType.REMINDER_SNOOZED
    reminder_type: str
    object_id: Optional[str] = None
    fingerprint: Optional[str] = None
    until: Optional[datetime] = None
    rationale: Optional[str] = None
    snooze_minutes: Optional[int] = None


class FeedbackEvidenceRecordedEvent(BaseEvent):
    """Event recording contextual weak-label evidence for learning targets."""

    event_type: EventType = EventType.FEEDBACK_EVIDENCE_RECORDED
    source_event_type: str
    object_id: Optional[str] = None
    evidence_type: str
    target_scores: dict[LearningTarget, float] = Field(default_factory=dict)
    rationale: Optional[str] = None
    context: dict[str, Any] = Field(default_factory=dict)


class FeatureSnapshotRecordedEvent(BaseEvent):
    """Event recording deterministic feature snapshot for replay/evaluation."""

    event_type: EventType = EventType.FEATURE_SNAPSHOT_RECORDED
    candidate_id: str
    candidate_type: str
    feature_version: str = "m6-v1"
    features: dict[str, Any] = Field(default_factory=dict)
    context: dict[str, Any] = Field(default_factory=dict)


class ModelScoreRecordedEvent(BaseEvent):
    """Event recording model score outputs in shadow/eval mode."""

    event_type: EventType = EventType.MODEL_SCORE_RECORDED
    candidate_id: str
    candidate_type: str
    model_name: str
    model_version: str
    score: float
    confidence: float
    explanation: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class LabControlChangedEvent(BaseEvent):
    """Event recording bounded Lab control mutation and rollback metadata."""

    event_type: EventType = EventType.LAB_CONTROL_CHANGED
    actor: str
    rationale: str
    before: dict[str, Any] = Field(default_factory=dict)
    after: dict[str, Any] = Field(default_factory=dict)
    rollback_to: dict[str, Any] = Field(default_factory=dict)


class LabExperimentRunEvent(BaseEvent):
    """Event recording execution of a Lab experiment run (read/compare only)."""

    event_type: EventType = EventType.LAB_EXPERIMENT_RUN
    run_id: str
    actor: str
    experiment_type: str
    candidate_config: dict[str, Any] = Field(default_factory=dict)
    baseline_config: dict[str, Any] = Field(default_factory=dict)
    result: dict[str, Any] = Field(default_factory=dict)


class LabExperimentAppliedEvent(BaseEvent):
    """Event recording explicit apply/rollback decision for a Lab experiment."""

    event_type: EventType = EventType.LAB_EXPERIMENT_APPLIED
    run_id: str
    actor: str
    rationale: str
    action: str
    applied: bool
    reason: Optional[str] = None
