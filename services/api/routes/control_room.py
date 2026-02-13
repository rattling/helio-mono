"""Control Room read-only transparency endpoints (Milestone 9)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from collections.abc import Generator

from fastapi import APIRouter, Depends

from shared.common.config import Config
from shared.contracts import ControlRoomOverview, ReadinessCheck, ReadinessPayload
from services.attention import AttentionService
from services.event_store.file_store import FileEventStore
from services.query.service import QueryService

router = APIRouter()


def get_control_room_services() -> Generator[tuple[Config, AttentionService], None, None]:
    """Get configured services used for control room payloads."""
    config = Config.from_env()
    event_store = FileEventStore(data_dir=config.EVENT_STORE_PATH)
    query_service = QueryService(event_store, db_path=Path(config.PROJECTIONS_DB_PATH))
    try:
        attention_service = AttentionService(
            event_store=event_store,
            query_service=query_service,
            enable_shadow_ranker=getattr(config, "SHADOW_RANKER_ENABLED", True),
            shadow_confidence_threshold=getattr(config, "SHADOW_RANKER_CONFIDENCE_THRESHOLD", 0.6),
            enable_bounded_personalization=getattr(
                config, "ATTENTION_BOUNDED_PERSONALIZATION_ENABLED", False
            ),
        )
        yield config, attention_service
    finally:
        query_service.close()


def _readiness_from_config(config: Config) -> ReadinessPayload:
    event_store_path = Path(config.EVENT_STORE_PATH)
    projections_db_path = Path(config.PROJECTIONS_DB_PATH)

    checks = {
        "event_store": ReadinessCheck(
            path=str(event_store_path),
            accessible=event_store_path.exists() or event_store_path.parent.exists(),
        ),
        "projections_db": ReadinessCheck(
            path=str(projections_db_path),
            parent_accessible=projections_db_path.parent.exists(),
        ),
    }

    all_ready = bool(
        checks["event_store"].accessible and checks["projections_db"].parent_accessible
    )
    return ReadinessPayload(status="ready" if all_ready else "not_ready", checks=checks)


@router.get("/overview", response_model=ControlRoomOverview)
async def get_control_room_overview(
    services: tuple[Config, AttentionService] = Depends(get_control_room_services),
) -> ControlRoomOverview:
    """Return consolidated read-only operator transparency payload."""
    config, attention_service = services

    readiness = _readiness_from_config(config)
    today = await attention_service.get_today_attention(limit=10)
    week = await attention_service.get_week_attention()

    return ControlRoomOverview(
        health={"status": "healthy", "service": "helionyx"},
        readiness=readiness,
        attention_today=today,
        attention_week=week,
        generated_at=datetime.utcnow().isoformat(),
    )
