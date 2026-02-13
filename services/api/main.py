"""FastAPI application for Helionyx.

FastAPI acts strictly as an adapter layer. No domain logic belongs here.
Domain services remain framework-agnostic.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.common.config import Config
from services.event_store.file_store import FileEventStore
from services.ingestion.service import IngestionService
from services.extraction.service import ExtractionService
from services.extraction.openai_client import OpenAILLMService
from services.extraction.mock_llm import MockLLMService
from services.query.service import QueryService
from services.task.service import TaskService
from services.api.routes import attention, control_room, health, ingestion, query, extraction, tasks

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

    logging.getLogger("helionyx.audit").info("config_loaded env=%s", config.ENV)

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
    task_service = TaskService(event_store=event_store, query_service=query_service)
    logger.info(f"Projections DB: {config.PROJECTIONS_DB_PATH}")

    # Rebuild projections on startup
    logger.info("Rebuilding projections...")
    await query_service.rebuild_projections()
    logger.info("Projections rebuilt")

    # Store services globally
    services["config"] = config
    services["event_store"] = event_store
    services["ingestion"] = ingestion_service
    services["extraction"] = extraction_service
    services["query"] = query_service
    services["task"] = task_service

    # Start Telegram bot if configured
    if config.TELEGRAM_BOT_TOKEN:
        logger.info("Starting Telegram bot...")
        if not config.TELEGRAM_CHAT_ID:
            logger.info(
                "Telegram chat id not configured; reminders/summaries will be disabled until TELEGRAM_CHAT_ID is set"
            )
        try:
            from services.adapters.telegram.bot import start_bot

            telegram_task = asyncio.create_task(
                start_bot(config.TELEGRAM_BOT_TOKEN, services, config)
            )
            logger.info("Telegram bot started")
            if config.TELEGRAM_CHAT_ID:
                logging.getLogger("helionyx.audit").info(
                    "telegram_chat_configured env=%s", config.ENV
                )
        except Exception as e:
            logger.error(f"Failed to start Telegram bot: {e}", exc_info=True)
    else:
        logger.info("Telegram bot disabled (no bot token)")

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
    if "query" in services:
        logger.info("Closing database connection...")
        services["query"].close()
        logger.info("Database closed")

    logger.info("=== Service Shutdown Complete ===")


# Create FastAPI application with lifespan management
app = FastAPI(
    title="Helionyx API",
    description="Personal decision and execution substrate",
    version="0.1.0",
    lifespan=lifespan,
)

runtime_config = Config.from_env()
app.add_middleware(
    CORSMiddleware,
    allow_origins=runtime_config.API_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(ingestion.router, prefix="/api/v1/ingest", tags=["ingestion"])
app.include_router(extraction.router, prefix="/api/v1/extract", tags=["extraction"])
app.include_router(query.router, prefix="/api/v1", tags=["query"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["tasks"])
app.include_router(control_room.router, prefix="/api/v1/control-room", tags=["control-room"])
app.include_router(attention.router, prefix="/attention", tags=["attention"])


@app.get("/")
async def root():
    """Root endpoint - basic API info."""
    return {
        "name": "Helionyx API",
        "version": "0.1.0",
        "status": "running",
        "environment": services.get("config", Config.from_env()).ENV,
    }
