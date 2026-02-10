#!/usr/bin/env python3
"""Entry point for Telegram bot."""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.common.config import Config
from services.event_store.file_store import FileEventStore
from services.ingestion.service import IngestionService
from services.extraction.service import ExtractionService
from services.query.service import QueryService
from services.adapters.telegram.bot import start_bot


def setup_logging(level: str = "INFO"):
    """Configure logging."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


async def main():
    """Main entry point."""
    
    # Load configuration
    config = Config.from_env()
    setup_logging(config.LOG_LEVEL)
    
    logger = logging.getLogger(__name__)
    
    # Validate Telegram config
    try:
        config.validate_telegram()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.error("Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env")
        sys.exit(1)
    
    logger.info("Initializing services...")
    
    # Initialize services
    event_store = FileEventStore(data_dir=config.EVENT_STORE_PATH)
    await event_store.initialize()
    
    ingestion_service = IngestionService(event_store)
    extraction_service = ExtractionService(event_store)
    query_service = QueryService(event_store)
    
    # Rebuild projections on startup
    logger.info("Rebuilding projections...")
    await query_service.rebuild_projections()
    
    services = {
        'ingestion': ingestion_service,
        'extraction': extraction_service,
        'query': query_service,
    }
    
    # Start bot
    logger.info(f"Starting Telegram bot...")
    logger.info(f"Chat ID: {config.TELEGRAM_CHAT_ID}")
    logger.info(f"Notifications: {config.NOTIFICATIONS_ENABLED}")
    
    try:
        await start_bot(config.TELEGRAM_BOT_TOKEN, services, config)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
