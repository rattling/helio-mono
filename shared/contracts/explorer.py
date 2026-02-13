"""Data Explorer contracts (Milestone 10)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class ExplorerEntityType(str, Enum):
    TASK = "task"
    EVENT = "event"


class ExplorerViewMode(str, Enum):
    LOOKUP = "lookup"
    TIMELINE = "timeline"
    STATE = "state"
    DECISION = "decision"


class ExplorerMode(str, Enum):
    GUIDED = "guided"
    AD_HOC = "ad_hoc"


class NotableSeverity(str, Enum):
    CRITICAL = "critical"
    RISK = "risk"
    WARNING = "warning"
    INFO = "info"


class ExplorerIdentifierRef(BaseModel):
    entity_type: ExplorerEntityType
    entity_id: str
    relation: str


class ExplorerLookupResponse(BaseModel):
    entity_type: ExplorerEntityType
    entity_id: str
    canonical: dict[str, Any]
    related_identifiers: list[ExplorerIdentifierRef] = Field(default_factory=list)


class ExplorerTimelineEvent(BaseModel):
    event_id: str
    event_type: str
    timestamp: datetime
    rationale: Optional[str] = None
    links: list[ExplorerIdentifierRef] = Field(default_factory=list)
    payload: dict[str, Any] = Field(default_factory=dict)


class ExplorerTimelineResponse(BaseModel):
    entity_type: ExplorerEntityType
    entity_id: str
    events: list[ExplorerTimelineEvent] = Field(default_factory=list)
    since: Optional[datetime] = None
    until: Optional[datetime] = None


class ExplorerStateSnapshotResponse(BaseModel):
    entity_type: ExplorerEntityType
    entity_id: str
    snapshot: dict[str, Any]
    traceability: dict[str, Any] = Field(default_factory=dict)


class ExplorerDecisionEvidenceResponse(BaseModel):
    entity_type: ExplorerEntityType
    entity_id: str
    decisions: list[ExplorerTimelineEvent] = Field(default_factory=list)


class ExplorerPulseMetric(BaseModel):
    key: str
    label: str
    value: int | float | str
    status: str
    trend: Optional[str] = None
    description: Optional[str] = None


class ExplorerPulse(BaseModel):
    generated_at: datetime
    metrics: list[ExplorerPulseMetric] = Field(default_factory=list)


class ExplorerRankingFactor(BaseModel):
    key: str
    label: str
    value: float


class ExplorerRankingMetadata(BaseModel):
    severity: NotableSeverity
    composite_score: float
    factors: list[ExplorerRankingFactor] = Field(default_factory=list)


class ExplorerEvidenceRef(BaseModel):
    view: ExplorerViewMode
    entity_type: ExplorerEntityType
    entity_id: str
    reason: str


class ExplorerNotableEvent(BaseModel):
    notable_id: str
    title: str
    summary: str
    event_type: str
    event_id: str
    timestamp: datetime
    ranking: ExplorerRankingMetadata
    evidence_refs: list[ExplorerEvidenceRef] = Field(default_factory=list)


class ExplorerGuidedInsightsResponse(BaseModel):
    generated_at: datetime
    pulse: ExplorerPulse
    notable_events: list[ExplorerNotableEvent] = Field(default_factory=list)


class ExplorerDeepLinkContext(BaseModel):
    entity_type: ExplorerEntityType
    entity_id: str
    view: ExplorerViewMode = ExplorerViewMode.LOOKUP
    mode: ExplorerMode = ExplorerMode.GUIDED
    since: Optional[datetime] = None
    until: Optional[datetime] = None
    preset: Optional[str] = None
