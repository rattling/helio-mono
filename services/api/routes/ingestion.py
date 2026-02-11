"""Ingestion API endpoints for message recording.

These endpoints delegate to IngestionService for message recording.
"""

from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field

from shared.contracts import SourceType
from shared.common.config import Config
from services.event_store.file_store import FileEventStore
from services.ingestion.service import IngestionService

router = APIRouter()


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


@router.post("/message", response_model=IngestMessageResponse, status_code=status.HTTP_201_CREATED)
async def ingest_message(
    request: IngestMessageRequest,
    ingestion_service: IngestionService = Depends(get_ingestion_service)
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
            metadata=request.metadata or {}
        )
        
        return IngestMessageResponse(
            event_id=str(event_id),
            status="recorded"
        )
    
    except ValueError as e:
        # Validation errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(e)}"
        )
    except Exception as e:
        # Service errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {str(e)}"
        )
