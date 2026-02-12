"""Notification scheduler for Milestone 6 attention digests and reminders."""

import logging
import asyncio
import json
from datetime import datetime

from .formatters import (
    format_attention_daily_digest,
    format_attention_weekly_digest,
    format_task_urgent_reminder,
)
from .errors import send_with_retry
from services.query import database
from services.attention import AttentionService
from shared.contracts import ReminderSentEvent

logger = logging.getLogger(__name__)

# Service instances and config (injected from bot.py)
query_service = None
event_store = None
config = None
db_conn = None


async def notification_scheduler(application):
    """Background task for checking and sending notifications."""

    logger.info("Notification scheduler started")

    while True:
        try:
            await check_and_send_daily_digest(application.bot)
            await check_and_send_weekly_digest(application.bot)
            await check_and_send_urgent_reminders(application.bot)

        except Exception as e:
            logger.error(f"Error in notification scheduler: {e}", exc_info=True)

        # Sleep for 1 minute
        await asyncio.sleep(60)


def _attention_service() -> AttentionService:
    return AttentionService(
        event_store=event_store,
        query_service=query_service,
        enable_shadow_ranker=getattr(config, "SHADOW_RANKER_ENABLED", True),
        shadow_confidence_threshold=getattr(config, "SHADOW_RANKER_CONFIDENCE_THRESHOLD", 0.6),
    )


async def check_and_send_urgent_reminders(bot):
    """Check urgent attention items and send deduplicated reminders."""

    now = datetime.now()
    hour = now.hour

    # Only send reminders during reasonable hours
    reminder_start = getattr(config, "REMINDER_WINDOW_START", 8)
    reminder_end = getattr(config, "REMINDER_WINDOW_END", 21)

    if hour < reminder_start or hour > reminder_end:
        return

    try:
        threshold = float(getattr(config, "ATTENTION_URGENT_THRESHOLD", 60.0))
        today = await _attention_service().get_today_attention(limit=20)
        for item in today.get("top_actionable", []):
            if float(item.get("urgency_score", 0.0)) < threshold:
                continue

            task_id = str(item.get("task_id"))
            fingerprint = f"urgent:{task_id}:{item.get('urgency_score')}"
            if db_conn and database.was_notification_sent_recently(
                db_conn,
                notification_type="task_urgent_reminder",
                object_id=task_id,
                within_hours=12,
                metadata_contains=fingerprint,
            ):
                continue

            message = format_task_urgent_reminder(item)
            chat_id = getattr(config, "TELEGRAM_CHAT_ID", None)
            if not chat_id:
                logger.info("Skipping reminder send (TELEGRAM_CHAT_ID not set)")
                return

            await send_with_retry(bot, chat_id=int(chat_id), text=message, parse_mode="Markdown")
            if db_conn:
                database.log_notification(
                    db_conn,
                    notification_type="task_urgent_reminder",
                    object_id=task_id,
                    metadata=json.dumps({"fingerprint": fingerprint}),
                )
            if event_store:
                await event_store.append(
                    ReminderSentEvent(
                        reminder_type="task_urgent_reminder",
                        object_id=task_id,
                        fingerprint=fingerprint,
                        metadata={"urgency_score": item.get("urgency_score")},
                    )
                )

            logger.info(f"Sent urgent task reminder: {item.get('title', task_id)}")

    except Exception as e:
        logger.error(f"Error checking urgent reminders: {e}", exc_info=True)


async def check_and_send_daily_digest(bot):
    """Send daily digest at configured time."""

    now = datetime.now()

    # Check if it's digest time (default: 8 PM)
    summary_hour = getattr(config, "DAILY_SUMMARY_HOUR", 20)

    if now.hour != summary_hour or now.minute > 5:
        # Only send during the configured hour, first 5 minutes
        return

    if db_conn and database.was_notification_sent_recently(
        db_conn, notification_type="task_daily_digest", within_hours=24
    ):
        return

    try:
        payload = await _attention_service().get_today_attention(limit=5)
        message = format_attention_daily_digest(payload)

        # Send
        chat_id = getattr(config, "TELEGRAM_CHAT_ID", None)
        if not chat_id:
            logger.info("Skipping daily digest send (TELEGRAM_CHAT_ID not set)")
            return
        await send_with_retry(bot, chat_id=int(chat_id), text=message, parse_mode="Markdown")

        if db_conn:
            database.log_notification(db_conn, notification_type="task_daily_digest")
        if event_store:
            await event_store.append(ReminderSentEvent(reminder_type="task_daily_digest"))

        logger.info("Sent daily attention digest")

        # Sleep extra to avoid sending multiple times in same hour
        await asyncio.sleep(300)  # 5 minute cooldown

    except Exception as e:
        logger.error(f"Error sending daily digest: {e}", exc_info=True)


async def check_and_send_weekly_digest(bot):
    """Send weekly digest at configured day/hour."""
    now = datetime.now()
    weekly_day = int(getattr(config, "WEEKLY_SUMMARY_DAY", 0))
    weekly_hour = int(getattr(config, "WEEKLY_SUMMARY_HOUR", 9))

    if now.weekday() != weekly_day or now.hour != weekly_hour or now.minute > 5:
        return

    if db_conn and database.was_notification_sent_recently(
        db_conn, notification_type="task_weekly_digest", within_hours=24 * 7
    ):
        return

    try:
        payload = await _attention_service().get_week_attention()
        message = format_attention_weekly_digest(payload)
        chat_id = getattr(config, "TELEGRAM_CHAT_ID", None)
        if not chat_id:
            logger.info("Skipping weekly digest send (TELEGRAM_CHAT_ID not set)")
            return

        await send_with_retry(bot, chat_id=int(chat_id), text=message, parse_mode="Markdown")
        if db_conn:
            database.log_notification(db_conn, notification_type="task_weekly_digest")
        if event_store:
            await event_store.append(ReminderSentEvent(reminder_type="task_weekly_digest"))

        logger.info("Sent weekly attention digest")
        await asyncio.sleep(300)
    except Exception as e:
        logger.error(f"Error sending weekly digest: {e}", exc_info=True)
