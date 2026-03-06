"""Command handlers for Telegram bot."""

import logging
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from shared.contracts import TaskPatchRequest, TaskPriority, TaskSnoozeRequest
from . import scheduler

from .formatters import format_todos_list, format_notes_list, format_tracks_list, format_tasks_list

logger = logging.getLogger(__name__)

# Service instances (injected from bot.py)
query_service = None
task_service = None

LEGACY_TODO_STATUS_MAP = {
    "pending": "open",
    "completed": "done",
}


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

Your chat id is: {chat_id}
    """

    await update.message.reply_text(message.strip())

    # Log chat_id for configuration
    logger.warning(f"User {user.id} ({user.username}) started bot. Chat ID: {chat_id}")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display available commands."""

    help_text = """
📚 Available Commands

Queries
• /todos [status] - Legacy alias for tasks
• /notes [search] - List your notes
• /tracks - List tracking items
• /tasks [status] - List tasks
• /task_show <task_id> - Show one task
• /task_done <task_id> - Mark task done
• /task_snooze <task_id> <iso-ts> - Snooze task
• /task_priority <task_id> <p0|p1|p2|p3> - Update priority
• /orchestrate <daily|weekly|urgent> - Trigger orchestration run
• /stats - System statistics

Information
• /help - Show this message
• /start - Welcome message

Tip: You can also send plain messages and Helionyx will extract objects automatically.
    """

    await update.message.reply_text(help_text.strip())


async def todos_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Legacy alias for canonical task listing."""

    # Parse optional status argument
    status = context.args[0] if context.args else None

    task_status = LEGACY_TODO_STATUS_MAP.get(status, status)

    # Validate status against canonical task statuses (plus legacy aliases)
    valid_statuses = [
        "pending",
        "completed",
        "open",
        "blocked",
        "in_progress",
        "done",
        "cancelled",
        "snoozed",
    ]
    if status and task_status not in valid_statuses:
        await update.message.reply_text(
            f"❌ Invalid status: {status}\n" f"Valid options: {', '.join(valid_statuses)}"
        )
        return

    try:
        tasks = await task_service.list_tasks(status=task_status)

        if not tasks:
            status_text = f" ({status})" if status else ""
            await update.message.reply_text(f"No tasks found{status_text}.")
            return

        await update.message.reply_text(
            "ℹ️ /todos is a legacy alias. Showing canonical tasks.",
        )
        formatted = format_tasks_list(tasks)
        await update.message.reply_text(formatted, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error in todos_command: {e}", exc_info=True)
        await update.message.reply_text("❌ Sorry, something went wrong. Please try again.")


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
        await update.message.reply_text(formatted, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error in notes_command: {e}", exc_info=True)
        await update.message.reply_text("❌ Sorry, something went wrong. Please try again.")


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
        await update.message.reply_text(formatted, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error in tracks_command: {e}", exc_info=True)
        await update.message.reply_text("❌ Sorry, something went wrong. Please try again.")


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

        await update.message.reply_text(message.strip(), parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error in stats_command: {e}", exc_info=True)
        await update.message.reply_text("❌ Sorry, something went wrong. Please try again.")


async def tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List tasks with optional status filter."""
    status = context.args[0] if context.args else None
    valid_statuses = ["open", "blocked", "in_progress", "done", "cancelled", "snoozed"]

    if status and status not in valid_statuses:
        await update.message.reply_text(
            f"❌ Invalid status: {status}\nValid options: {', '.join(valid_statuses)}"
        )
        return

    try:
        tasks = await task_service.list_tasks(status=status)
        if not tasks:
            suffix = f" ({status})" if status else ""
            await update.message.reply_text(f"No tasks found{suffix}.")
            return

        await update.message.reply_text(format_tasks_list(tasks), parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error in tasks_command: {e}", exc_info=True)
        await update.message.reply_text("❌ Sorry, something went wrong. Please try again.")


async def task_show_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show details for a single task."""
    if not context.args:
        await update.message.reply_text("Usage: /task_show <task_id>")
        return

    task_id = context.args[0]
    task = await task_service.get_task(task_id)
    if not task:
        await update.message.reply_text("Task not found.")
        return

    message = (
        "🧩 *Task*\n"
        f"• ID: `{task['task_id']}`\n"
        f"• Title: {task['title']}\n"
        f"• Status: {task['status']}\n"
        f"• Priority: {task['priority']}\n"
        f"• Project: {task.get('project') or '-'}\n"
        f"• Due: {task.get('due_at') or '-'}"
    )
    await update.message.reply_text(message, parse_mode="Markdown")


async def task_done_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mark a task as done."""
    if not context.args:
        await update.message.reply_text("Usage: /task_done <task_id>")
        return

    task_id = context.args[0]
    task = await task_service.complete_task(task_id, rationale="Marked done via Telegram")
    if not task:
        await update.message.reply_text("Task not found.")
        return

    await update.message.reply_text(f"✅ Task `{task_id}` marked done.", parse_mode="Markdown")


async def task_snooze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Snooze a task until a timestamp."""
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /task_snooze <task_id> <YYYY-MM-DDTHH:MM:SS>")
        return

    task_id = context.args[0]
    until_raw = context.args[1]
    try:
        until = datetime.fromisoformat(until_raw)
    except ValueError:
        await update.message.reply_text(
            "Invalid timestamp. Use ISO format, e.g. 2026-02-15T09:00:00"
        )
        return

    task = await task_service.snooze_task(
        task_id,
        TaskSnoozeRequest(until=until, rationale="Snoozed via Telegram"),
    )
    if not task:
        await update.message.reply_text("Task not found.")
        return

    await update.message.reply_text(
        f"⏸ Task `{task_id}` snoozed until `{until_raw}`.", parse_mode="Markdown"
    )


async def task_priority_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Update task priority."""
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /task_priority <task_id> <p0|p1|p2|p3>")
        return

    task_id = context.args[0]
    priority_raw = context.args[1].lower()

    try:
        priority = TaskPriority(priority_raw)
    except ValueError:
        await update.message.reply_text("Invalid priority. Use one of: p0, p1, p2, p3")
        return

    task = await task_service.patch_task(task_id, TaskPatchRequest(priority=priority))
    if not task:
        await update.message.reply_text("Task not found.")
        return

    await update.message.reply_text(
        f"🔁 Task `{task_id}` priority set to `{priority.value}`.",
        parse_mode="Markdown",
    )


async def orchestrate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Trigger a manual orchestration run through shared scheduler boundary."""
    if not context.args:
        await update.message.reply_text("Usage: /orchestrate <daily|weekly|urgent>")
        return

    workflow_alias = context.args[0].strip().lower()
    workflow_map = {
        "daily": "daily_digest",
        "weekly": "weekly_digest",
        "urgent": "urgent_reminder",
    }
    workflow_name = workflow_map.get(workflow_alias)
    if not workflow_name:
        await update.message.reply_text("Invalid workflow. Use one of: daily, weekly, urgent")
        return

    result = await scheduler.run_orchestration_workflow(
        bot=context.bot,
        workflow_name=workflow_name,
        dry_run=False,
    )

    status = result.get("status", "unknown")
    reason = result.get("reason")
    run_id = result.get("run_id")
    response = f"Orchestration workflow `{workflow_name}` status: `{status}`"
    if run_id:
        response += f"\nrun_id: `{run_id}`"
    if reason:
        response += f"\nreason: `{reason}`"
    await update.message.reply_text(response, parse_mode="Markdown")
