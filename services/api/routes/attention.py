"""Attention API endpoints (Milestone 6)."""

from pathlib import Path
from collections.abc import Generator

from fastapi import APIRouter, Depends, Query

from shared.common.config import Config
from services.attention import AttentionService
from services.event_store.file_store import FileEventStore
from services.query.service import QueryService

router = APIRouter()


def get_attention_service() -> Generator[AttentionService, None, None]:
    """Get initialized attention service."""
    config = Config.from_env()
    event_store = FileEventStore(data_dir=config.EVENT_STORE_PATH)
    query_service = QueryService(event_store, db_path=Path(config.PROJECTIONS_DB_PATH))
    try:
        yield AttentionService(
            event_store=event_store,
            query_service=query_service,
            enable_shadow_ranker=getattr(config, "SHADOW_RANKER_ENABLED", True),
            shadow_confidence_threshold=getattr(config, "SHADOW_RANKER_CONFIDENCE_THRESHOLD", 0.6),
            enable_bounded_personalization=getattr(
                config, "ATTENTION_BOUNDED_PERSONALIZATION_ENABLED", False
            ),
        )
    finally:
        query_service.close()


@router.get("/today", response_model=dict)
async def attention_today(
    limit: int = Query(5, ge=1, le=20),
    attention_service: AttentionService = Depends(get_attention_service),
) -> dict:
    """Get today's attention queue."""
    return await attention_service.get_today_attention(limit=limit)


@router.get("/week", response_model=dict)
async def attention_week(
    attention_service: AttentionService = Depends(get_attention_service),
) -> dict:
    """Get weekly lookahead attention queue."""
    return await attention_service.get_week_attention()


@router.post("/run", response_model=dict)
async def attention_run(
    attention_service: AttentionService = Depends(get_attention_service),
) -> dict:
    """Run attention computations and return queue summary counts."""
    return await attention_service.run()
