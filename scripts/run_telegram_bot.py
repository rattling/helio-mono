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
from shared.common.logging import setup_logging
from services.event_store.file_store import FileEventStore
from services.ingestion.service import IngestionService
from services.extraction.service import ExtractionService
from services.extraction.openai_client import OpenAILLMService
from services.extraction.mock_llm import MockLLMService
from services.query.service import QueryService
from services.adapters.telegram.bot import start_bot


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
        logger.error("Please set TELEGRAM_BOT_TOKEN in .env")
        sys.exit(1)
    
    logger.info("Initializing services...")
    
    # Initialize services
    event_store = FileEventStore(data_dir=config.EVENT_STORE_PATH)
    
    # Initialize LLM service (OpenAI or Mock)
    if config.OPENAI_API_KEY:
        logger.info(f"Using OpenAI LLM service (model: {config.OPENAI_MODEL})")
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
        logger.warning("No OpenAI API key found - using Mock LLM service")
        logger.warning("Set OPENAI_API_KEY in .env for real LLM extraction")
        llm_service = MockLLMService(event_store=event_store)
    
    ingestion_service = IngestionService(event_store)
    extraction_service = ExtractionService(event_store, llm_service)
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
    if config.TELEGRAM_CHAT_ID:
        logger.info(f"Chat ID (configured): {config.TELEGRAM_CHAT_ID}")
    else:
        logger.warning("TELEGRAM_CHAT_ID not set; reminders/summaries will be disabled until configured")
        logger.warning("To get your chat id: send /start to the bot, then run:")
        logger.warning("  curl -s \"https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getUpdates\" | jq '.result[-1].message.chat.id'")
    logger.info(f"Notifications enabled flag: {config.NOTIFICATIONS_ENABLED}")
    
    try:
        await start_bot(config.TELEGRAM_BOT_TOKEN, services, config)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
