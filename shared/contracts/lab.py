"""Lab contracts (Milestone 11)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class LabPersonalizationMode(str, Enum):
    DETERMINISTIC = "deterministic"
    SHADOW = "shadow"
    BOUNDED = "bounded"


class LabDiagnosticMetric(BaseModel):
    key: str
    label: str
    value: int | float | str
    status: str
    description: str | None = None


class LabDiagnostics(BaseModel):
    generated_at: datetime
    metrics: list[LabDiagnosticMetric] = Field(default_factory=list)


class LabConfigSnapshot(BaseModel):
    mode: LabPersonalizationMode
    shadow_ranker_enabled: bool
    bounded_personalization_enabled: bool
    shadow_confidence_threshold: float


class LabOverviewResponse(BaseModel):
    generated_at: datetime
    diagnostics: LabDiagnostics
    config: LabConfigSnapshot
    fallback_state: dict[str, Any] = Field(default_factory=dict)


class LabControlUpdateRequest(BaseModel):
    actor: str
    rationale: str
    mode: LabPersonalizationMode
    shadow_confidence_threshold: float = Field(ge=0.0, le=1.0)


class LabControlUpdateResponse(BaseModel):
    status: str
    effective_config: LabConfigSnapshot
    audit: dict[str, Any] = Field(default_factory=dict)


class LabRollbackRequest(BaseModel):
    actor: str
    rationale: str


class LabExperimentRunRequest(BaseModel):
    actor: str
    rationale: str
    experiment_type: str = "policy_replay"
    candidate_mode: LabPersonalizationMode
    candidate_shadow_confidence_threshold: float = Field(ge=0.0, le=1.0)


class LabExperimentRunResult(BaseModel):
    run_id: str
    status: str
    generated_at: datetime
    baseline: dict[str, Any] = Field(default_factory=dict)
    candidate: dict[str, Any] = Field(default_factory=dict)
    comparison: dict[str, Any] = Field(default_factory=dict)
    apply_allowed: bool
    apply_block_reason: str | None = None


class LabExperimentApplyRequest(BaseModel):
    actor: str
    rationale: str
    action: str = Field(pattern="^(apply|rollback|no_op)$")


class LabExperimentHistoryItem(BaseModel):
    run_id: str
    generated_at: datetime
    actor: str
    experiment_type: str
    candidate: dict[str, Any] = Field(default_factory=dict)
    apply_allowed: bool
    status: str


class LabExperimentHistoryResponse(BaseModel):
    runs: list[LabExperimentHistoryItem] = Field(default_factory=list)
