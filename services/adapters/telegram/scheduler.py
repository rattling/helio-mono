"""Notification scheduler for Milestone 6 attention digests and reminders."""

import logging
import asyncio
import json
from datetime import datetime, timedelta

from .formatters import (
    format_attention_daily_digest,
    format_attention_weekly_digest,
    format_task_urgent_reminder,
)
from .errors import send_with_retry
from services.adapters.calendar import GoogleCalendarAdapter, ZohoCalendarAdapter
from services.query import database
from services.attention import AttentionService
from shared.contracts import ReminderSentEvent
from services.control import ControlPolicy, ControlPolicyEvaluator
from services.orchestration import OrchestrationRuntime, build_monday_digest_payload
from services.orchestration import build_weekday_day_ahead_payload

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


def _runtime() -> OrchestrationRuntime:
    allowed_workflows = set(
        filter(
            None,
            str(
                getattr(
                    config,
                    "ORCHESTRATION_ALLOWED_WORKFLOWS",
                    "daily_digest,weekly_digest,urgent_reminder",
                )
            ).split(","),
        )
    )
    allowed_reminder_types = set(
        filter(
            None,
            str(
                getattr(
                    config,
                    "ORCHESTRATION_ALLOWED_REMINDER_TYPES",
                    "task_daily_digest,task_weekly_digest,task_urgent_reminder",
                )
            ).split(","),
        )
    )
    tool_allowlist = set(
        filter(
            None,
            str(getattr(config, "ORCHESTRATION_TOOL_ALLOWLIST", "telegram.send_message")).split(
                ","
            ),
        )
    )
    side_effect_scopes = set(
        filter(
            None,
            str(getattr(config, "ORCHESTRATION_SIDE_EFFECT_SCOPES", "telegram:notify")).split(","),
        )
    )

    policy = ControlPolicy(
        allowed_workflows=allowed_workflows,
        allowed_reminder_types=allowed_reminder_types,
        tool_allowlist=tool_allowlist,
        side_effect_scopes=side_effect_scopes,
        max_runtime_seconds=int(getattr(config, "ORCHESTRATION_MAX_RUNTIME_SECONDS", 60)),
        max_tool_calls=int(getattr(config, "ORCHESTRATION_MAX_TOOL_CALLS", 3)),
        max_estimated_tokens=int(getattr(config, "ORCHESTRATION_MAX_ESTIMATED_TOKENS", 8000)),
        max_estimated_cost_usd=float(getattr(config, "ORCHESTRATION_MAX_ESTIMATED_COST_USD", 0.5)),
    )
    return OrchestrationRuntime(
        event_store=event_store,
        policy_evaluator=ControlPolicyEvaluator(policy=policy),
    )


def _daily_digest_context(payload: dict) -> dict:
    return {
        "top_actionable_count": len(payload.get("top_actionable", [])),
        "day_ahead_count": len(payload.get("day_ahead", [])),
        "calendar_status": (payload.get("calendar") or {}).get("provider_status", {}),
        "calendar_degraded": (payload.get("calendar") or {}).get("degraded", False),
    }


def _daily_digest_delivery_plan(payload: dict) -> dict:
    message = format_attention_daily_digest(payload)
    return {
        "message": message,
        "item_count": len(payload.get("top_actionable", [])),
        "delivery_channel": "telegram",
    }


def _weekly_digest_context(payload: dict) -> dict:
    return {
        "due_this_week_count": len(payload.get("due_this_week", [])),
        "weekly_lookahead_count": len(payload.get("weekly_lookahead", [])),
        "day_ahead_count": len(payload.get("day_ahead", [])),
        "calendar_status": (payload.get("calendar") or {}).get("provider_status", {}),
        "calendar_degraded": (payload.get("calendar") or {}).get("degraded", False),
    }


def _weekly_digest_delivery_plan(payload: dict) -> dict:
    message = format_attention_weekly_digest(payload)
    return {
        "message": message,
        "item_count": len(payload.get("weekly_lookahead", []) or payload.get("due_this_week", [])),
        "delivery_channel": "telegram",
    }


async def _fetch_calendar_reads(time_min: str, time_max: str):
    google = GoogleCalendarAdapter(
        access_token=getattr(config, "GOOGLE_CALENDAR_ACCESS_TOKEN", None),
        calendar_id=getattr(config, "GOOGLE_CALENDAR_ID", None),
        base_url=getattr(
            config, "GOOGLE_CALENDAR_BASE_URL", "https://www.googleapis.com/calendar/v3"
        ),
    )
    zoho = ZohoCalendarAdapter(
        access_token=getattr(config, "ZOHO_CALENDAR_ACCESS_TOKEN", None),
        calendar_id=getattr(config, "ZOHO_CALENDAR_ID", None),
        base_url=getattr(config, "ZOHO_CALENDAR_BASE_URL", "https://calendar.zoho.com/api/v1"),
    )
    return await asyncio.gather(
        google.list_events(time_min=time_min, time_max=time_max),
        zoho.list_events(time_min=time_min, time_max=time_max),
    )


async def _build_monday_digest_payload(now: datetime) -> dict:
    today_attention = await _attention_service().get_today_attention(limit=5)
    week_attention = await _attention_service().get_week_attention()
    tasks = await query_service.get_tasks(limit=25) if query_service else []
    calendar_reads = await _fetch_calendar_reads(
        time_min=now.isoformat(),
        time_max=(now + timedelta(days=7)).isoformat(),
    )
    return build_monday_digest_payload(
        tasks=tasks,
        today_attention=today_attention,
        week_attention=week_attention,
        calendar_reads=calendar_reads,
        now=now,
    )


async def _build_weekday_day_ahead_payload(now: datetime) -> dict:
    today_attention = await _attention_service().get_today_attention(limit=5)
    tasks = await query_service.get_tasks(limit=25) if query_service else []
    calendar_reads = await _fetch_calendar_reads(
        time_min=now.isoformat(),
        time_max=(now + timedelta(days=1)).isoformat(),
    )
    return build_weekday_day_ahead_payload(
        tasks=tasks,
        today_attention=today_attention,
        calendar_reads=calendar_reads,
        now=now,
    )


def _urgent_reminder_context(item: dict) -> dict:
    return {
        "task_id": str(item.get("task_id")),
        "urgency_score": item.get("urgency_score"),
        "priority": item.get("priority"),
    }


def _urgent_reminder_delivery_plan(item: dict) -> dict:
    message = format_task_urgent_reminder(item)
    return {
        "message": message,
        "task_id": str(item.get("task_id")),
        "delivery_channel": "telegram",
    }


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
            delivery_plan = _urgent_reminder_delivery_plan(item)
            if db_conn and database.was_notification_sent_recently(
                db_conn,
                notification_type="task_urgent_reminder",
                object_id=task_id,
                within_hours=12,
                metadata_contains=fingerprint,
            ):
                continue

            async def _execute_delivery() -> dict:
                chat_id = getattr(config, "TELEGRAM_CHAT_ID", None)
                if not chat_id:
                    logger.info("Skipping reminder send (TELEGRAM_CHAT_ID not set)")
                    return {"sent": False, "reason": "chat_id_not_configured"}

                await send_with_retry(
                    bot,
                    chat_id=int(chat_id),
                    text=delivery_plan["message"],
                    parse_mode="Markdown",
                )
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
                return {"sent": True, "task_id": task_id}

            runtime_result = await _runtime().run_flow(
                workflow_name="urgent_reminder",
                reminder_type="task_urgent_reminder",
                execute=_execute_delivery,
                gather_context=lambda item=item: _urgent_reminder_context(item),
                prepare_delivery=lambda delivery_plan=delivery_plan: delivery_plan,
                envelope={
                    "workflow_name": "urgent_reminder",
                    "reminder_type": "task_urgent_reminder",
                    "tool_name": "telegram.send_message",
                    "side_effect_scope": "telegram:notify",
                    "budgets": {
                        "runtime_seconds": 15,
                        "tool_calls": 1,
                        "estimated_tokens": 120,
                        "estimated_cost_usd": 0.01,
                    },
                },
                fingerprint=fingerprint,
            )
            if runtime_result.get("status") != "completed":
                logger.info(
                    "Urgent reminder run halted status=%s reason=%s",
                    runtime_result.get("status"),
                    runtime_result.get("reason"),
                )
                continue

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
        payload = await _build_weekday_day_ahead_payload(now)
        delivery_plan = _daily_digest_delivery_plan(payload)

        async def _execute_delivery() -> dict:
            chat_id = getattr(config, "TELEGRAM_CHAT_ID", None)
            if not chat_id:
                logger.info("Skipping daily digest send (TELEGRAM_CHAT_ID not set)")
                return {"sent": False, "reason": "chat_id_not_configured"}

            await send_with_retry(
                bot,
                chat_id=int(chat_id),
                text=delivery_plan["message"],
                parse_mode="Markdown",
            )

            if db_conn:
                database.log_notification(db_conn, notification_type="task_daily_digest")
            if event_store:
                await event_store.append(ReminderSentEvent(reminder_type="task_daily_digest"))
            return {
                "sent": True,
                "items": delivery_plan["item_count"],
                "digest_type": payload.get("digest_type"),
                "calendar_status": (payload.get("calendar") or {}).get("provider_status", {}),
                "calendar_degraded": (payload.get("calendar") or {}).get("degraded", False),
            }

        runtime_result = await _runtime().run_flow(
            workflow_name="daily_digest",
            reminder_type="task_daily_digest",
            execute=_execute_delivery,
            gather_context=lambda: _daily_digest_context(payload),
            prepare_delivery=lambda: delivery_plan,
            envelope={
                "workflow_name": "daily_digest",
                "reminder_type": "task_daily_digest",
                "tool_name": "telegram.send_message",
                "side_effect_scope": "telegram:notify",
                "budgets": {
                    "runtime_seconds": 20,
                    "tool_calls": 1,
                    "estimated_tokens": 250,
                    "estimated_cost_usd": 0.02,
                },
            },
        )
        if runtime_result.get("status") != "completed":
            logger.info(
                "Daily digest run halted status=%s reason=%s",
                runtime_result.get("status"),
                runtime_result.get("reason"),
            )
            return

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
        payload = await _build_monday_digest_payload(now)
        delivery_plan = _weekly_digest_delivery_plan(payload)

        async def _execute_delivery() -> dict:
            chat_id = getattr(config, "TELEGRAM_CHAT_ID", None)
            if not chat_id:
                logger.info("Skipping weekly digest send (TELEGRAM_CHAT_ID not set)")
                return {"sent": False, "reason": "chat_id_not_configured"}

            await send_with_retry(
                bot,
                chat_id=int(chat_id),
                text=delivery_plan["message"],
                parse_mode="Markdown",
            )
            if db_conn:
                database.log_notification(db_conn, notification_type="task_weekly_digest")
            if event_store:
                await event_store.append(ReminderSentEvent(reminder_type="task_weekly_digest"))
            return {
                "sent": True,
                "items": delivery_plan["item_count"],
                "digest_type": payload.get("digest_type"),
                "calendar_status": (payload.get("calendar") or {}).get("provider_status", {}),
                "calendar_degraded": (payload.get("calendar") or {}).get("degraded", False),
            }

        runtime_result = await _runtime().run_flow(
            workflow_name="weekly_digest",
            reminder_type="task_weekly_digest",
            execute=_execute_delivery,
            gather_context=lambda: _weekly_digest_context(payload),
            prepare_delivery=lambda: delivery_plan,
            envelope={
                "workflow_name": "weekly_digest",
                "reminder_type": "task_weekly_digest",
                "tool_name": "telegram.send_message",
                "side_effect_scope": "telegram:notify",
                "budgets": {
                    "runtime_seconds": 20,
                    "tool_calls": 1,
                    "estimated_tokens": 250,
                    "estimated_cost_usd": 0.02,
                },
            },
        )
        if runtime_result.get("status") != "completed":
            logger.info(
                "Weekly digest run halted status=%s reason=%s",
                runtime_result.get("status"),
                runtime_result.get("reason"),
            )
            return

        logger.info("Sent weekly attention digest")
        await asyncio.sleep(300)
    except Exception as e:
        logger.error(f"Error sending weekly digest: {e}", exc_info=True)


async def run_orchestration_workflow(bot, workflow_name: str, dry_run: bool = False) -> dict:
    """Run a single orchestration workflow on demand via shared runtime boundary."""
    workflow = (workflow_name or "").strip().lower()

    if workflow == "daily_digest":
        payload = await _build_weekday_day_ahead_payload(datetime.now())
        delivery_plan = _daily_digest_delivery_plan(payload)

        async def _execute_daily() -> dict:
            if dry_run:
                return {
                    "sent": True,
                    "dry_run": True,
                    "items": delivery_plan["item_count"],
                    "digest_type": payload.get("digest_type"),
                    "calendar_status": (payload.get("calendar") or {}).get("provider_status", {}),
                    "calendar_degraded": (payload.get("calendar") or {}).get("degraded", False),
                }

            chat_id = getattr(config, "TELEGRAM_CHAT_ID", None)
            if not chat_id:
                return {"sent": False, "reason": "chat_id_not_configured"}
            await send_with_retry(
                bot,
                chat_id=int(chat_id),
                text=delivery_plan["message"],
                parse_mode="Markdown",
            )
            if db_conn:
                database.log_notification(db_conn, notification_type="task_daily_digest")
            if event_store:
                await event_store.append(ReminderSentEvent(reminder_type="task_daily_digest"))
            return {
                "sent": True,
                "items": delivery_plan["item_count"],
                "digest_type": payload.get("digest_type"),
                "calendar_status": (payload.get("calendar") or {}).get("provider_status", {}),
                "calendar_degraded": (payload.get("calendar") or {}).get("degraded", False),
            }

        return await _runtime().run_flow(
            workflow_name="daily_digest",
            reminder_type="task_daily_digest",
            execute=_execute_daily,
            gather_context=lambda: _daily_digest_context(payload),
            prepare_delivery=lambda: delivery_plan,
            envelope={
                "workflow_name": "daily_digest",
                "reminder_type": "task_daily_digest",
                "tool_name": "telegram.send_message",
                "side_effect_scope": "telegram:notify",
                "budgets": {
                    "runtime_seconds": 20,
                    "tool_calls": 1,
                    "estimated_tokens": 250,
                    "estimated_cost_usd": 0.02,
                },
            },
        )

    if workflow == "weekly_digest":
        payload = await _build_monday_digest_payload(datetime.now())
        delivery_plan = _weekly_digest_delivery_plan(payload)

        async def _execute_weekly() -> dict:
            if dry_run:
                return {
                    "sent": True,
                    "dry_run": True,
                    "items": delivery_plan["item_count"],
                    "digest_type": payload.get("digest_type"),
                    "calendar_status": (payload.get("calendar") or {}).get("provider_status", {}),
                    "calendar_degraded": (payload.get("calendar") or {}).get("degraded", False),
                }

            chat_id = getattr(config, "TELEGRAM_CHAT_ID", None)
            if not chat_id:
                return {"sent": False, "reason": "chat_id_not_configured"}
            await send_with_retry(
                bot,
                chat_id=int(chat_id),
                text=delivery_plan["message"],
                parse_mode="Markdown",
            )
            if db_conn:
                database.log_notification(db_conn, notification_type="task_weekly_digest")
            if event_store:
                await event_store.append(ReminderSentEvent(reminder_type="task_weekly_digest"))
            return {
                "sent": True,
                "items": delivery_plan["item_count"],
                "digest_type": payload.get("digest_type"),
                "calendar_status": (payload.get("calendar") or {}).get("provider_status", {}),
                "calendar_degraded": (payload.get("calendar") or {}).get("degraded", False),
            }

        return await _runtime().run_flow(
            workflow_name="weekly_digest",
            reminder_type="task_weekly_digest",
            execute=_execute_weekly,
            gather_context=lambda: _weekly_digest_context(payload),
            prepare_delivery=lambda: delivery_plan,
            envelope={
                "workflow_name": "weekly_digest",
                "reminder_type": "task_weekly_digest",
                "tool_name": "telegram.send_message",
                "side_effect_scope": "telegram:notify",
                "budgets": {
                    "runtime_seconds": 20,
                    "tool_calls": 1,
                    "estimated_tokens": 250,
                    "estimated_cost_usd": 0.02,
                },
            },
        )

    if workflow == "urgent_reminder":
        threshold = float(getattr(config, "ATTENTION_URGENT_THRESHOLD", 60.0))
        today = await _attention_service().get_today_attention(limit=20)
        candidate = None
        for item in today.get("top_actionable", []):
            if float(item.get("urgency_score", 0.0)) >= threshold:
                candidate = item
                break

        if not candidate:
            return {"status": "skipped", "reason": "no_urgent_candidates"}

        task_id = str(candidate.get("task_id"))
        fingerprint = f"urgent:{task_id}:{candidate.get('urgency_score')}"
        delivery_plan = _urgent_reminder_delivery_plan(candidate)

        async def _execute_urgent() -> dict:
            if dry_run:
                return {"sent": True, "dry_run": True, "task_id": task_id}

            chat_id = getattr(config, "TELEGRAM_CHAT_ID", None)
            if not chat_id:
                return {"sent": False, "reason": "chat_id_not_configured"}
            await send_with_retry(
                bot,
                chat_id=int(chat_id),
                text=delivery_plan["message"],
                parse_mode="Markdown",
            )
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
                        metadata={"urgency_score": candidate.get("urgency_score")},
                    )
                )
            return {"sent": True, "task_id": task_id}

        return await _runtime().run_flow(
            workflow_name="urgent_reminder",
            reminder_type="task_urgent_reminder",
            execute=_execute_urgent,
            gather_context=lambda: _urgent_reminder_context(candidate),
            prepare_delivery=lambda: delivery_plan,
            envelope={
                "workflow_name": "urgent_reminder",
                "reminder_type": "task_urgent_reminder",
                "tool_name": "telegram.send_message",
                "side_effect_scope": "telegram:notify",
                "budgets": {
                    "runtime_seconds": 15,
                    "tool_calls": 1,
                    "estimated_tokens": 120,
                    "estimated_cost_usd": 0.01,
                },
            },
            fingerprint=fingerprint,
        )

    return {
        "status": "error",
        "reason": "unsupported_workflow",
        "supported_workflows": ["daily_digest", "weekly_digest", "urgent_reminder"],
    }
