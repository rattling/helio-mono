"""Control Room contracts for operator-facing transparency views (Milestone 9)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ReadinessCheck(BaseModel):
    path: str
    accessible: bool | None = None
    parent_accessible: bool | None = None


class ReadinessPayload(BaseModel):
    status: str
    checks: dict[str, ReadinessCheck]


class ControlRoomOverview(BaseModel):
    health: dict[str, Any]
    readiness: ReadinessPayload
    attention_today: dict[str, Any]
    attention_week: dict[str, Any]
    generated_at: str = Field(description="UTC ISO timestamp for payload generation")
