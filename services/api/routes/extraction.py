"""Extraction API endpoints.

Milestone 4: explicit extraction trigger for an already-recorded message.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from shared.common.config import Config
from services.event_store.file_store import FileEventStore
from services.extraction.mock_llm import MockLLMService
from services.extraction.openai_client import OpenAILLMService
from services.extraction.service import ExtractionService

router = APIRouter()

audit_logger = logging.getLogger("helionyx.audit")


class ExtractMessageResponse(BaseModel):
    """Response schema for extraction trigger."""

    event_id: str = Field(..., description="Message event ID")
    status: str = Field(..., description="Extraction status")


def get_extraction_service() -> ExtractionService:
    """Get initialized extraction service."""
    config = Config.from_env()
    event_store = FileEventStore(data_dir=config.EVENT_STORE_PATH)

    if config.OPENAI_API_KEY:
        llm_service = OpenAILLMService(
            event_store=event_store,
            api_key=config.OPENAI_API_KEY,
            model=config.OPENAI_MODEL,
            max_tokens=config.OPENAI_MAX_TOKENS,
            temperature=config.OPENAI_TEMPERATURE,
            max_retries=config.LLM_MAX_RETRIES,
            retry_base_delay=config.LLM_RETRY_BASE_DELAY,
        )
    else:
        llm_service = MockLLMService(event_store=event_store)

    return ExtractionService(event_store, llm_service)


@router.post(
    "/message/{event_id}",
    response_model=ExtractMessageResponse,
    status_code=status.HTTP_200_OK,
)
async def extract_message(
    event_id: UUID,
    extraction_service: ExtractionService = Depends(get_extraction_service),
) -> ExtractMessageResponse:
    """Trigger extraction for an already-recorded message event."""

    # Validate message exists
    message_event = await extraction_service.event_store.get_by_id(event_id)
    if message_event is None:
        raise HTTPException(status_code=404, detail="Message event not found")

    audit_logger.info("extraction_triggered event_id=%s", str(event_id))
    extracted_items = await extraction_service.extract_from_message(event_id)

    if extracted_items:
        audit_logger.info(
            "extraction_completed event_id=%s extracted_count=%s",
            str(event_id),
            len(extracted_items),
        )
        return ExtractMessageResponse(event_id=str(event_id), status="extracted")

    return ExtractMessageResponse(event_id=str(event_id), status="no_objects_or_already_extracted")
