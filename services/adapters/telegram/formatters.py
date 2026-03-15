"""Message formatters for Telegram display."""

from datetime import datetime, timedelta
from typing import Optional


def format_todos_list(todos: list[dict]) -> str:
    """Format todo list for Telegram display."""

    if not todos:
        return "No todos found."

    # Group by priority
    by_priority = {"urgent": [], "high": [], "medium": [], "low": []}

    for todo in todos:
        priority = todo.get("priority", "medium")
        by_priority[priority].append(todo)

    # Build message
    lines = [f"📋 *Your Todos* ({len(todos)})\n"]

    priority_icons = {"urgent": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}

    for priority in ["urgent", "high", "medium", "low"]:
        items = by_priority[priority]
        if not items:
            continue

        icon = priority_icons[priority]
        lines.append(f"\n{icon} *{priority.upper()}*")

        for todo in items:
            title = todo["title"]
            due = format_due_date(todo.get("due_date"))
            due_text = f"\n  📅 {due}" if due else ""
            status = todo.get("status", "pending")
            status_icon = "✅" if status == "completed" else ""
            lines.append(f"• {status_icon}{title}{due_text}")

    return "\n".join(lines)


def format_notes_list(notes: list[dict]) -> str:
    """Format notes list for Telegram display."""

    if not notes:
        return "No notes found."

    lines = [f"📝 *Your Notes* ({len(notes)})\n"]

    for note in notes[:20]:  # Limit to 20 to avoid message too long
        title = note.get("title", "Untitled")
        content = note.get("content", "")

        # Truncate long content
        if len(content) > 100:
            content = content[:97] + "..."

        lines.append(f"• *{title}*")
        if content and content != title:
            lines.append(f"  _{content}_")

    if len(notes) > 20:
        lines.append(f"\n_... and {len(notes) - 20} more_")

    return "\n".join(lines)


def format_tracks_list(tracks: list[dict]) -> str:
    """Format tracks list for Telegram display."""

    if not tracks:
        return "No tracking items found."

    lines = [f"👁 *Your Tracks* ({len(tracks)})\n"]

    for track in tracks:
        subject = track.get("subject", "Unknown")
        status = track.get("status", "active")
        status_icon = "✅" if status == "completed" else "⏸" if status == "paused" else "👁"

        lines.append(f"• {status_icon} {subject}")

    return "\n".join(lines)


def format_due_date(due_date_str: Optional[str]) -> Optional[str]:
    """Format due date for display."""
    if not due_date_str:
        return None

    try:
        # Handle various date formats
        if "T" in due_date_str:
            due = datetime.fromisoformat(due_date_str.replace("Z", "+00:00"))
        else:
            due = datetime.fromisoformat(due_date_str)

        now = datetime.now(due.tzinfo) if due.tzinfo else datetime.now()

        if due.date() == now.date():
            return "Today"
        elif due.date() == (now + timedelta(days=1)).date():
            return "Tomorrow"
        elif due < now:
            days_ago = (now - due).days
            return f"{days_ago}d overdue"
        else:
            return due.strftime("%b %d")
    except (ValueError, AttributeError):
        return due_date_str


def format_tasks_list(tasks: list[dict]) -> str:
    """Format task list for Telegram display."""

    if not tasks:
        return "No tasks found."

    lines = [f"🧩 *Your Tasks* ({len(tasks)})\n"]
    priority_icons = {"p0": "🔴", "p1": "🟠", "p2": "🟡", "p3": "🟢"}

    for task in tasks[:20]:
        task_id = task.get("task_id", "")
        short_id = task_id[:8] if task_id else "unknown"
        title = task.get("title", "Untitled")
        status = task.get("status", "open")
        priority = task.get("priority", "p2")
        priority_icon = priority_icons.get(priority, "⚪")
        stale_icon = " ⚠️" if task.get("is_stale") else ""
        lines.append(f"• `{short_id}` {priority_icon} *{title}* ({status}){stale_icon}")

    if len(tasks) > 20:
        lines.append(f"\n_... and {len(tasks) - 20} more_")

    return "\n".join(lines)


def format_reminder(todo: dict) -> str:
    """Format reminder notification."""

    due = format_due_date(todo.get("due_date"))
    priority = todo.get("priority", "medium")

    message = f"""
🔔 *Reminder*

{todo['title']}

📅 Due: {due}
Priority: {priority.capitalize()}
    """

    return message.strip()


def format_daily_summary(stats: dict, todos: list[dict]) -> str:
    """Format daily summary notification."""

    today = datetime.now().strftime("%B %d, %Y")

    # Find overdue todos
    now = datetime.now()
    overdue = []
    for todo in todos:
        if todo.get("due_date"):
            try:
                due_date = datetime.fromisoformat(todo["due_date"].replace("Z", "+00:00"))
                if due_date < now:
                    overdue.append(todo)
            except (ValueError, AttributeError):
                pass

    message = f"""
📊 *Daily Summary* - {today}

📋 *Todos*
• Pending: {len(todos)}
• Overdue: {len(overdue)}

📝 *System*
• Total objects: {stats.get('total_objects', 0)}
    """

    if overdue:
        message += "\n\n⚠️ *Overdue Items*"
        for todo in overdue[:3]:  # Show max 3
            message += f"\n• {todo['title']}"
        if len(overdue) > 3:
            message += f"\n• ... and {len(overdue) - 3} more"

    return message.strip()


def format_task_urgent_reminder(item: dict) -> str:
    """Format urgent task reminder from attention candidate item."""
    due = format_due_date(item.get("due_at").isoformat() if item.get("due_at") else None)
    title = item.get("title", "Untitled task")
    score = item.get("urgency_score", 0)
    explanation = item.get("urgency_explanation", "")
    due_line = f"📅 Due: {due}\n" if due else ""
    return (
        "🔔 *Urgent Task Reminder*\n\n"
        f"*{title}*\n"
        f"{due_line}"
        f"Urgency score: {score}\n"
        f"Why: {explanation}"
    ).strip()


def format_attention_daily_digest(payload: dict) -> str:
    """Format M6 daily digest payload for Telegram."""
    if payload.get("digest_type") == "weekday_day_ahead":
        top_actionable = payload.get("top_actionable") or []
        day_ahead = payload.get("day_ahead") or []
        due_72h = payload.get("due_next_72h") or []
        calendar = payload.get("calendar") or {}

        lines = ["🧠 *Weekday Day-Ahead Digest*\n"]

        lines.append("*Top actionable*")
        if not top_actionable:
            lines.append("• None")
        else:
            for item in top_actionable[:5]:
                lines.append(f"• {item.get('title', 'Untitled')} ({item.get('priority', 'p2')})")

        lines.append("\n*Day-ahead schedule*")
        if not day_ahead:
            lines.append("• None")
        else:
            for event in day_ahead[:8]:
                start = format_due_date(event.get("starts_at")) or event.get(
                    "starts_at", "scheduled"
                )
                lines.append(f"• {event.get('title', 'Untitled')} ({start})")

        lines.append("\n*Due in next 72h*")
        if not due_72h:
            lines.append("• None")
        else:
            for item in due_72h[:5]:
                due = format_due_date(item.get("due_at"))
                lines.append(f"• {item.get('title', 'Untitled')} ({due or 'due soon'})")

        provider_status = calendar.get("provider_status") or {}
        if provider_status:
            lines.append("\n*Calendar providers*")
            for provider, status in provider_status.items():
                lines.append(f"• {provider}: {status}")

        return "\n".join(lines)

    top_actionable = payload.get("top_actionable") or []
    due_72h = payload.get("due_next_72h") or []
    stale = payload.get("stale_cleanup_candidate")

    lines = ["🧠 *Daily Attention Digest*\n"]
    lines.append("*Top 5 actionable*")
    if not top_actionable:
        lines.append("• None")
    else:
        for item in top_actionable[:5]:
            lines.append(
                f"• `{str(item.get('task_id', ''))[:8]}` {item.get('title', 'Untitled')} "
                f"(score {item.get('urgency_score', 0)})"
            )

    lines.append("\n*Due in next 72h*")
    if not due_72h:
        lines.append("• None")
    else:
        for item in due_72h[:5]:
            due = format_due_date(item.get("due_at").isoformat() if item.get("due_at") else None)
            lines.append(f"• {item.get('title', 'Untitled')} ({due or 'due soon'})")

    lines.append("\n*Stale cleanup candidate*")
    if stale:
        lines.append(f"• {stale.get('title', 'Untitled')} ({stale.get('urgency_explanation', '')})")
    else:
        lines.append("• None")

    return "\n".join(lines)


def format_attention_weekly_digest(payload: dict) -> str:
    """Format M6 weekly digest payload for Telegram."""
    if payload.get("digest_type") == "monday_weekly_day_ahead":
        weekly_lookahead = payload.get("weekly_lookahead") or []
        day_ahead = payload.get("day_ahead") or []
        top_actionable = payload.get("top_actionable") or []
        calendar = payload.get("calendar") or {}

        lines = ["🗓 *Monday Weekly + Day-Ahead Digest*\n"]

        lines.append("*Weekly lookahead*")
        if not weekly_lookahead:
            lines.append("• None")
        else:
            for item in weekly_lookahead[:8]:
                due = format_due_date(item.get("due_at"))
                lines.append(
                    f"• {item.get('title', 'Untitled')} ({due or item.get('priority', 'p2')})"
                )

        lines.append("\n*Today and next 24h schedule*")
        if not day_ahead:
            lines.append("• None")
        else:
            for event in day_ahead[:8]:
                start = format_due_date(event.get("starts_at")) or event.get(
                    "starts_at", "scheduled"
                )
                lines.append(f"• {event.get('title', 'Untitled')} ({start})")

        lines.append("\n*Top actionable tasks*")
        if not top_actionable:
            lines.append("• None")
        else:
            for item in top_actionable[:5]:
                lines.append(f"• {item.get('title', 'Untitled')} ({item.get('priority', 'p2')})")

        provider_status = calendar.get("provider_status") or {}
        if provider_status:
            lines.append("\n*Calendar providers*")
            for provider, status in provider_status.items():
                lines.append(f"• {provider}: {status}")

        warnings = calendar.get("warnings") or []
        if warnings:
            lines.append("\n*Calendar warnings*")
            for warning in warnings[:5]:
                lines.append(f"• {warning}")

        return "\n".join(lines)

    due_this_week = payload.get("due_this_week") or []
    high_priority_without_due = payload.get("high_priority_without_due") or []
    blocked_summary = payload.get("blocked_summary") or []

    lines = ["🗓 *Weekly Attention Lookahead*\n"]

    lines.append("*Due this week*")
    if not due_this_week:
        lines.append("• None")
    else:
        for item in due_this_week[:10]:
            due = format_due_date(item.get("due_at").isoformat() if item.get("due_at") else None)
            lines.append(f"• {item.get('title', 'Untitled')} ({due or 'this week'})")

    lines.append("\n*High priority without due date*")
    if not high_priority_without_due:
        lines.append("• None")
    else:
        for item in high_priority_without_due[:10]:
            lines.append(f"• {item.get('title', 'Untitled')} ({item.get('priority', 'p2')})")

    lines.append("\n*Blocked summary*")
    if not blocked_summary:
        lines.append("• None")
    else:
        for item in blocked_summary[:10]:
            lines.append(f"• {item.get('title', 'Untitled')} (blocked)")

    return "\n".join(lines)
