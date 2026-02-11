"""Error handling utilities for Telegram bot."""

import logging
import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import RetryAfter, TimedOut

logger = logging.getLogger(__name__)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Global error handler."""

    logger.error(f"Update {update} caused error {context.error}", exc_info=context.error)

    # User-friendly error message
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ Sorry, something went wrong. Please try again or contact support."
        )


async def send_with_retry(bot, chat_id: int, text: str, max_retries: int = 3, **kwargs):
    """Send message with retry on rate limit."""

    for attempt in range(max_retries):
        try:
            return await bot.send_message(chat_id, text, **kwargs)

        except RetryAfter as e:
            if attempt < max_retries - 1:
                logger.warning(f"Rate limited. Waiting {e.retry_after}s")
                await asyncio.sleep(e.retry_after)
            else:
                raise

        except TimedOut as e:
            if attempt < max_retries - 1:
                logger.warning(f"Timeout. Retrying...")
                await asyncio.sleep(2**attempt)
            else:
                raise
