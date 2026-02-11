"""FastAPI application for Helionyx.

FastAPI acts strictly as an adapter layer. No domain logic belongs here.
Domain services remain framework-agnostic.
"""

from fastapi import FastAPI
from services.api.routes import health, ingestion, query

# Create FastAPI application
app = FastAPI(
    title="Helionyx API",
    description="Personal decision and execution substrate",
    version="0.1.0",
)

# Register routes
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(ingestion.router, prefix="/api/v1/ingest", tags=["ingestion"])
app.include_router(query.router, prefix="/api/v1", tags=["query"])


@app.get("/")
async def root():
    """Root endpoint - basic API info."""
    return {
        "name": "Helionyx API",
        "version": "0.1.0",
        "status": "running"
    }
