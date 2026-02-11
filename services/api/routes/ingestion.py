"""Ingestion API endpoints for message recording.

These endpoints delegate to IngestionService for message recording.

Milestone 4: extraction is opt-in on ingestion via `?extract=true`.
"""

from typing import Optional
from uuid import uuid4

import logging

from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel, Field

from shared.contracts import SourceType
from shared.common.config import Config
from services.event_store.file_store import FileEventStore
from services.ingestion.service import IngestionService
from services.extraction.service import ExtractionService
from services.extraction.openai_client import OpenAILLMService
from services.extraction.mock_llm import MockLLMService

router = APIRouter()

audit_logger = logging.getLogger("helionyx.audit")


# Request/Response schemas
class IngestMessageRequest(BaseModel):
    """Request schema for message ingestion."""

    text: str = Field(..., description="Message content", min_length=1)
    source: str = Field(default="api", description="Source type (api, telegram, cli, etc.)")
    timestamp: Optional[str] = Field(None, description="ISO 8601 timestamp (optional)")
    source_id: Optional[str] = Field(None, description="Original ID from source system")
    author: Optional[str] = Field(None, description="Author of the message")
    conversation_id: Optional[str] = Field(None, description="Conversation grouping ID")
    metadata: Optional[dict] = Field(None, description="Additional metadata")


class IngestMessageResponse(BaseModel):
    """Response schema for message ingestion."""

    event_id: str = Field(..., description="Event ID of the ingested message")
    status: str = Field(..., description="Status of ingestion")


# Dependency to get ingestion service
def get_ingestion_service() -> IngestionService:
    """Get initialized ingestion service.

    Returns:
        IngestionService instance ready to use
    """
    config = Config.from_env()
    event_store = FileEventStore(data_dir=config.EVENT_STORE_PATH)
    return IngestionService(event_store)


def get_extraction_service() -> ExtractionService:
    """Get initialized extraction service.

    Returns:
        ExtractionService instance ready to use
    """
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


@router.post("/message", response_model=IngestMessageResponse, status_code=status.HTTP_201_CREATED)
async def ingest_message(
    request: IngestMessageRequest,
    extract: bool = Query(False, description="If true, trigger extraction after recording"),
    ingestion_service: IngestionService = Depends(get_ingestion_service),
    extraction_service: ExtractionService = Depends(get_extraction_service),
) -> IngestMessageResponse:
    """Ingest a message for processing.

    Args:
        request: Message ingestion request with text and metadata
        ingestion_service: Injected ingestion service

    Returns:
        Response with event ID and status

    Raises:
        HTTPException: 400 for validation errors, 500 for service errors
    """
    try:
        # Validate and normalize source type
        try:
            source_type = SourceType(request.source.lower())
        except ValueError:
            # Allow API source type even if not in enum
            source_type = SourceType.API

        # Generate source ID if not provided
        source_id = request.source_id or f"api-{uuid4().hex[:12]}"

        # Ingest message via service
        event_id = await ingestion_service.ingest_message(
            content=request.text,
            source=source_type,
            source_id=source_id,
            author=request.author,
            conversation_id=request.conversation_id,
            metadata=request.metadata or {},
        )

        audit_logger.info(
            "message_ingested event_id=%s source=%s extract=%s",
            str(event_id),
            source_type.value,
            extract,
        )

        if extract:
            extracted_items = await extraction_service.extract_from_message(event_id)
            audit_logger.info(
                "extraction_triggered_on_ingest event_id=%s extracted_count=%s",
                str(event_id),
                len(extracted_items),
            )
            return IngestMessageResponse(event_id=str(event_id), status="recorded_extracted")

        return IngestMessageResponse(event_id=str(event_id), status="recorded")

    except ValueError as e:
        # Validation errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Validation error: {str(e)}"
        )
    except Exception as e:
        # Service errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ingestion failed: {str(e)}"
        )
