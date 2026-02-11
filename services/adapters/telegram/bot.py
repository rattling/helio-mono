"""Main Telegram bot setup and configuration."""

import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

from . import handlers, message_handler, errors, scheduler

logger = logging.getLogger(__name__)


def create_application(bot_token: str, services: dict, cfg) -> Application:
    """
    Create and configure Telegram bot application.
    
    Args:
        bot_token: Telegram bot token
        services: Dict with 'ingestion', 'extraction', 'query' services
        cfg: Configuration object
        
    Returns:
        Configured Application instance
    """
    
    # Inject services into handler modules
    handlers.query_service = services['query']
    message_handler.ingestion_service = services['ingestion']
    message_handler.extraction_service = services['extraction']
    scheduler.query_service = services['query']
    scheduler.config = cfg
    scheduler.db_conn = services['query'].conn
    
    # Build application
    application = (
        Application.builder()
        .token(bot_token)
        .build()
    )
    
    # Add command handlers
    application.add_handler(CommandHandler("start", handlers.start_command))
    application.add_handler(CommandHandler("help", handlers.help_command))
    application.add_handler(CommandHandler("todos", handlers.todos_command))
    application.add_handler(CommandHandler("notes", handlers.notes_command))
    application.add_handler(CommandHandler("tracks", handlers.tracks_command))
    application.add_handler(CommandHandler("stats", handlers.stats_command))
    
    # Add message handler (non-commands)
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler.handle_message)
    )
    
    # Add error handler
    application.add_error_handler(errors.error_handler)
    
    logger.info("Telegram bot application created")
    
    return application


async def start_bot(bot_token: str, services: dict, cfg):
    """
    Start the Telegram bot.
    
    Args:
        bot_token: Telegram bot token
        services: Dict with 'ingestion', 'extraction', 'query' services
        cfg: Configuration object
    """
    
    logger.info("Starting Telegram bot...")
    
    # Create application
    application = create_application(bot_token, services, cfg)
    
    # Initialize and start application
    await application.initialize()
    await application.start()
    
    # Start notification scheduler as background task if enabled
    notifications_enabled = getattr(cfg, 'NOTIFICATIONS_ENABLED', True)
    if notifications_enabled and str(notifications_enabled).lower() in ('true', '1', 'yes'):
        application.create_task(scheduler.notification_scheduler(application))
        logger.info("Notification scheduler enabled")
    
    # Start polling
    logger.info("Starting polling...")
    await application.updater.start_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )
    
    # Keep running until interrupted
    logger.info("Bot is running. Press Ctrl+C to stop.")
    try:
        import asyncio
        # Keep the bot running
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Stopping bot...")
    finally:
        # Cleanup
        await application.updater.stop()
        await application.stop()
        await application.shutdown()
