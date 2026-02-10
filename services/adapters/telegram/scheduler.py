"""Notification scheduler for reminders and daily summaries."""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional

from .formatters import format_reminder, format_daily_summary
from .errors import send_with_retry
from services.query import database

logger = logging.getLogger(__name__)

# Service instances and config (injected from bot.py)
query_service = None
config = None
db_conn = None


async def notification_scheduler(application):
    """Background task for checking and sending notifications."""
    
    logger.info("Notification scheduler started")
    
    while True:
        try:
            # Check reminders
            await check_and_send_reminders(application.bot)
            
            # Check daily summary
            await check_and_send_daily_summary(application.bot)
            
        except Exception as e:
            logger.error(f"Error in notification scheduler: {e}", exc_info=True)
        
        # Sleep for 1 minute
        await asyncio.sleep(60)


async def check_and_send_reminders(bot):
    """Check for due todos and send reminders."""
    
    now = datetime.now()
    hour = now.hour
    
    # Only send reminders during reasonable hours
    reminder_start = getattr(config, 'REMINDER_WINDOW_START', 8)
    reminder_end = getattr(config, 'REMINDER_WINDOW_END', 21)
    
    if hour < reminder_start or hour > reminder_end:
        return
    
    try:
        # Get todos due soon (next 24 hours)
        advance_hours = getattr(config, 'REMINDER_ADVANCE_HOURS', 24)
        future = now + timedelta(hours=advance_hours)
        
        todos = await query_service.get_todos(status="pending")
        
        # Filter to due soon
        due_soon = []
        for t in todos:
            if t.get('due_date'):
                try:
                    due_date = datetime.fromisoformat(t['due_date'].replace('Z', '+00:00'))
                    if due_date <= future and due_date >= now:
                        due_soon.append(t)
                except (ValueError, AttributeError):
                    pass
        
        for todo in due_soon:
            # Check if already reminded today
            if db_conn and database.was_reminded_today(db_conn, todo['object_id']):
                continue
            
            # Format and send reminder
            message = format_reminder(todo)
            chat_id = config.TELEGRAM_CHAT_ID
            
            await send_with_retry(
                bot,
                chat_id=int(chat_id),
                text=message,
                parse_mode='Markdown'
            )
            
            # Mark as reminded
            if db_conn:
                database.mark_reminder_sent(db_conn, todo['object_id'])
            
            logger.info(f"Sent reminder for todo: {todo['title']}")
            
    except Exception as e:
        logger.error(f"Error checking reminders: {e}", exc_info=True)


async def check_and_send_daily_summary(bot):
    """Send daily summary at configured time."""
    
    now = datetime.now()
    
    # Check if it's summary time (default: 8 PM)
    summary_hour = getattr(config, 'DAILY_SUMMARY_HOUR', 20)
    
    if now.hour != summary_hour or now.minute > 5:
        # Only send during the configured hour, first 5 minutes
        return
    
    # Check if already sent today
    if db_conn and database.was_daily_summary_sent_today(db_conn):
        return
    
    try:
        # Get stats and pending todos
        stats = query_service.get_stats()
        todos = await query_service.get_todos(status="pending")
        
        # Format summary
        message = format_daily_summary(stats, todos)
        
        # Send
        chat_id = config.TELEGRAM_CHAT_ID
        await send_with_retry(
            bot,
            chat_id=int(chat_id),
            text=message,
            parse_mode='Markdown'
        )
        
        # Mark as sent
        if db_conn:
            database.mark_daily_summary_sent(db_conn)
        
        logger.info("Sent daily summary")
        
        # Sleep extra to avoid sending multiple times in same hour
        await asyncio.sleep(300)  # 5 minute cooldown
        
    except Exception as e:
        logger.error(f"Error sending daily summary: {e}", exc_info=True)
