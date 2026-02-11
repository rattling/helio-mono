"""Health check endpoints for service monitoring.

These endpoints verify system health and readiness for handling requests.
"""

import os
from pathlib import Path
from typing import Dict, Any

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from shared.common.config import Config

router = APIRouter()


@router.get("")
async def health() -> Dict[str, Any]:
    """Basic health check - service is running.
    
    Returns 200 OK if the service is alive.
    Does not check dependencies.
    
    Returns:
        Basic status indicating service is running
    """
    return {
        "status": "healthy",
        "service": "helionyx"
    }


@router.get("/ready")
async def health_ready() -> JSONResponse:
    """Readiness check - service can handle requests.
    
    Checks critical dependencies:
    - Event store path is accessible
    - Projections database path is accessible (parent directory exists)
    
    Returns:
        200 OK if all checks pass
        503 Service Unavailable if any check fails
    """
    config = Config.from_env()
    
    checks = {}
    all_healthy = True
    
    # Check event store path
    event_store_path = Path(config.EVENT_STORE_PATH)
    event_store_accessible = event_store_path.exists() or event_store_path.parent.exists()
    checks["event_store"] = {
        "path": str(event_store_path),
        "accessible": event_store_accessible
    }
    if not event_store_accessible:
        all_healthy = False
    
    # Check projections DB path (parent directory must exist)
    projections_db_path = Path(config.PROJECTIONS_DB_PATH)
    projections_accessible = projections_db_path.parent.exists()
    checks["projections_db"] = {
        "path": str(projections_db_path),
        "parent_accessible": projections_accessible
    }
    if not projections_accessible:
        all_healthy = False
    
    # Determine overall status
    response_status = status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return JSONResponse(
        status_code=response_status,
        content={
            "status": "ready" if all_healthy else "not_ready",
            "checks": checks
        }
    )
