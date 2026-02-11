"""Command handlers for Telegram bot."""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from .formatters import format_todos_list, format_notes_list, format_tracks_list

logger = logging.getLogger(__name__)

# Service instances (injected from bot.py)
query_service = None


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message and setup verification."""
    
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    message = f"""
👋 Welcome to Helionyx, {user.first_name}!

I'm your personal decision and execution substrate.

I can help you:
• Track todos, notes, and things to monitor
• Query your data anytime
• Send you reminders and daily summaries

Try /help to see what I can do.
    """
    
    await update.message.reply_text(message.strip())
    
    # Log chat_id for configuration
    logger.info(f"User {user.id} ({user.username}) started bot. Chat ID: {chat_id}")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display available commands."""
    
    help_text = """
📚 *Available Commands*

*Queries*
• `/todos [status]` \\- List your todos
  Example: `/todos pending`
  
• `/notes [search]` \\- List your notes
  Example: `/notes meeting`
  
• `/tracks` \\- List tracking items

• `/stats` \\- System statistics

*Information*
• `/help` \\- Show this message
• `/start` \\- Welcome message

💡 Tip: You can also just send me messages and I'll extract todos, notes, and tracks automatically\\!
    """
    
    await update.message.reply_text(
        help_text.strip(),
        parse_mode='MarkdownV2'
    )


async def todos_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List todos with optional status filter."""
    
    # Parse optional status argument
    status = context.args[0] if context.args else None
    
    # Validate status
    valid_statuses = ['pending', 'in_progress', 'completed', 'cancelled']
    if status and status not in valid_statuses:
        await update.message.reply_text(
            f"❌ Invalid status: {status}\n"
            f"Valid options: {', '.join(valid_statuses)}"
        )
        return
    
    try:
        # Query service
        todos = await query_service.get_todos(status=status)
        
        # Format response
        if not todos:
            status_text = f" ({status})" if status else ""
            await update.message.reply_text(f"No todos found{status_text}.")
            return
        
        # Format and send
        formatted = format_todos_list(todos)
        await update.message.reply_text(formatted, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in todos_command: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Sorry, something went wrong. Please try again."
        )


async def notes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List notes with optional search."""
    
    # Parse optional search argument
    search = " ".join(context.args) if context.args else None
    
    try:
        # Query service
        notes = await query_service.get_notes(search=search)
        
        # Format response
        if not notes:
            search_text = f" matching '{search}'" if search else ""
            await update.message.reply_text(f"No notes found{search_text}.")
            return
        
        # Format and send
        formatted = format_notes_list(notes)
        await update.message.reply_text(formatted, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in notes_command: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Sorry, something went wrong. Please try again."
        )


async def tracks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List tracking items."""
    
    try:
        # Query service
        tracks = await query_service.get_tracks()
        
        # Format response
        if not tracks:
            await update.message.reply_text("No tracking items found.")
            return
        
        # Format and send
        formatted = format_tracks_list(tracks)
        await update.message.reply_text(formatted, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in tracks_command: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Sorry, something went wrong. Please try again."
        )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display system statistics."""
    
    try:
        stats = query_service.get_stats()
        
        message = f"""
📊 *Helionyx Statistics*

*Objects*
• Todos: {stats.get('todos', 0)}
• Notes: {stats.get('notes', 0)}
• Tracks: {stats.get('tracks', 0)}
• Total: {stats.get('total_objects', 0)}

*System*
• Events: {stats.get('total_events', 'N/A')}
• Last rebuild: {stats.get('last_rebuild', 'Never')}
        """
        
        await update.message.reply_text(message.strip(), parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in stats_command: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Sorry, something went wrong. Please try again."
        )
