"""FastAPI application for Helionyx.

FastAPI acts strictly as an adapter layer. No domain logic belongs here.
Domain services remain framework-agnostic.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI

from shared.common.config import Config
from services.event_store.file_store import FileEventStore
from services.ingestion.service import IngestionService
from services.extraction.service import ExtractionService
from services.extraction.openai_client import OpenAILLMService
from services.extraction.mock_llm import MockLLMService
from services.query.service import QueryService
from services.api.routes import health, ingestion, query

logger = logging.getLogger(__name__)

# Global services container
services = {}
telegram_task: Optional[asyncio.Task] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage service lifecycle - startup and shutdown."""
    global services, telegram_task
    
    # STARTUP
    logger.info("=== Service Startup ===")
    
    # Load configuration
    config = Config.from_env()
    logger.info(f"Environment: {config.ENV}")
    logger.info(f"Log level: {config.LOG_LEVEL}")
    
    # Initialize event store
    event_store = FileEventStore(data_dir=config.EVENT_STORE_PATH)
    logger.info(f"Event store: {config.EVENT_STORE_PATH}")
    
    # Initialize LLM service
    if config.OPENAI_API_KEY:
        logger.info(f"LLM: OpenAI ({config.OPENAI_MODEL})")
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
        logger.warning("LLM: Mock (no OpenAI API key)")
        llm_service = MockLLMService(event_store=event_store)
    
    # Initialize domain services
    ingestion_service = IngestionService(event_store)
    extraction_service = ExtractionService(event_store, llm_service)
    query_service = QueryService(event_store, db_path=config.PROJECTIONS_DB_PATH)
    logger.info(f"Projections DB: {config.PROJECTIONS_DB_PATH}")
    
    # Rebuild projections on startup
    logger.info("Rebuilding projections...")
    await query_service.rebuild_projections()
    logger.info("Projections rebuilt")
    
    # Store services globally
    services['config'] = config
    services['event_store'] = event_store
    services['ingestion'] = ingestion_service
    services['extraction'] = extraction_service
    services['query'] = query_service
    
    # Start Telegram bot if configured
    if config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID:
        logger.info("Starting Telegram bot...")
        try:
            from services.adapters.telegram.bot import start_bot
            telegram_task = asyncio.create_task(
                start_bot(config.TELEGRAM_BOT_TOKEN, services, config)
            )
            logger.info(f"Telegram bot started (chat: {config.TELEGRAM_CHAT_ID})")
        except Exception as e:
            logger.error(f"Failed to start Telegram bot: {e}", exc_info=True)
    else:
        logger.info("Telegram bot disabled (no credentials)")
    
    logger.info("=== Service Ready ===")
    
    yield  # Application runs
    
    # SHUTDOWN
    logger.info("=== Service Shutdown ===")
    
    # Stop Telegram bot
    if telegram_task and not telegram_task.done():
        logger.info("Stopping Telegram bot...")
        telegram_task.cancel()
        try:
            await telegram_task
        except asyncio.CancelledError:
            pass
        logger.info("Telegram bot stopped")
    
    # Close query service database connection
    if 'query' in services:
        logger.info("Closing database connection...")
        services['query'].close()
        logger.info("Database closed")
    
    logger.info("=== Service Shutdown Complete ===")


# Create FastAPI application with lifespan management
app = FastAPI(
    title="Helionyx API",
    description="Personal decision and execution substrate",
    version="0.1.0",
    lifespan=lifespan
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
        "status": "running",
        "environment": services.get('config', Config.from_env()).ENV
    }
