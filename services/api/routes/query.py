"""Query API endpoints for retrieving todos, notes, tracks, and stats.

These endpoints delegate to QueryService for data retrieval.
"""

from typing import Optional, List, Dict, Any

from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel, Field

from shared.common.config import Config
from services.event_store.file_store import FileEventStore
from services.query.service import QueryService

router = APIRouter()


# Response schemas
class TodoResponse(BaseModel):
    """Response schema for a todo item."""

    object_id: str
    title: str
    description: Optional[str]
    status: str
    priority: str
    due_date: Optional[str]
    created_at: str
    completed_at: Optional[str]
    tags: Optional[str]  # JSON string
    source_event_id: str
    last_updated_at: str


class NoteResponse(BaseModel):
    """Response schema for a note."""

    object_id: str
    title: str
    content: str
    created_at: str
    tags: Optional[str]  # JSON string
    source_event_id: str
    last_updated_at: str


class TrackResponse(BaseModel):
    """Response schema for a track item."""

    object_id: str
    title: str
    description: Optional[str]
    status: str
    created_at: str
    last_updated: Optional[str]
    tags: Optional[str]  # JSON string
    source_event_id: str
    check_in_frequency: Optional[str]
    projection_updated_at: str


class StatsResponse(BaseModel):
    """Response schema for system statistics."""

    todos: int
    notes: int
    tracks: int
    total_objects: int
    last_rebuild: str
    total_events: str


# Dependency to get query service
def get_query_service() -> QueryService:
    """Get initialized query service.

    Returns:
        QueryService instance ready to use
    """
    config = Config.from_env()
    event_store = FileEventStore(data_dir=config.EVENT_STORE_PATH)
    return QueryService(event_store, db_path=config.PROJECTIONS_DB_PATH)


@router.get("/todos", response_model=List[Dict[str, Any]])
async def get_todos(
    status: Optional[str] = Query(
        None, description="Filter by status (pending, in_progress, completed, abandoned)"
    ),
    tags: Optional[str] = Query(None, description="Comma-separated list of tags to filter by"),
    query_service: QueryService = Depends(get_query_service),
) -> List[Dict[str, Any]]:
    """Get all todos with optional filters.

    Args:
        status: Optional status filter
        tags: Optional comma-separated tags
        query_service: Injected query service

    Returns:
        List of todos matching filters

    Raises:
        HTTPException: 500 for service errors
    """
    try:
        # Parse tags if provided
        tag_list = [t.strip() for t in tags.split(",")] if tags else None

        # Query todos
        todos = await query_service.get_todos(status=status, tags=tag_list)

        return todos

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve todos: {str(e)}",
        )


@router.get("/notes", response_model=List[Dict[str, Any]])
async def get_notes(
    tags: Optional[str] = Query(None, description="Comma-separated list of tags to filter by"),
    search: Optional[str] = Query(None, description="Text to search in title and content"),
    limit: Optional[int] = Query(
        None, description="Maximum number of results (not yet implemented)"
    ),
    offset: Optional[int] = Query(None, description="Offset for pagination (not yet implemented)"),
    query_service: QueryService = Depends(get_query_service),
) -> List[Dict[str, Any]]:
    """Get all notes with optional filters.

    Args:
        tags: Optional comma-separated tags
        search: Optional text search
        limit: Optional result limit (not implemented yet, accepted for future compatibility)
        offset: Optional result offset (not implemented yet, accepted for future compatibility)
        query_service: Injected query service

    Returns:
        List of notes matching filters

    Raises:
        HTTPException: 500 for service errors
    """
    try:
        # Parse tags if provided
        tag_list = [t.strip() for t in tags.split(",")] if tags else None

        # Query notes
        notes = await query_service.get_notes(tags=tag_list, search=search)

        # TODO: Apply limit/offset when pagination is implemented
        # For now, just accept the parameters for API compatibility

        return notes

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve notes: {str(e)}",
        )


@router.get("/tracks", response_model=List[Dict[str, Any]])
async def get_tracks(
    status: Optional[str] = Query(None, description="Filter by status"),
    query_service: QueryService = Depends(get_query_service),
) -> List[Dict[str, Any]]:
    """Get all tracked items with optional filters.

    Args:
        status: Optional status filter
        query_service: Injected query service

    Returns:
        List of tracks matching filters

    Raises:
        HTTPException: 500 for service errors
    """
    try:
        # Query tracks
        tracks = await query_service.get_tracks(status=status)

        return tracks

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve tracks: {str(e)}",
        )


@router.get("/stats", response_model=Dict[str, Any])
async def get_stats(query_service: QueryService = Depends(get_query_service)) -> Dict[str, Any]:
    """Get system statistics.

    Args:
        query_service: Injected query service

    Returns:
        Statistics about todos, notes, tracks, and system state

    Raises:
        HTTPException: 500 for service errors
    """
    try:
        stats = query_service.get_stats()
        return stats

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve stats: {str(e)}",
        )
