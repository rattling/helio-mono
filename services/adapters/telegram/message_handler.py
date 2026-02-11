"""Message handler for non-command messages."""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from shared.contracts import SourceType

logger = logging.getLogger(__name__)
audit_logger = logging.getLogger("helionyx.audit")

# Service instances (injected from bot.py)
ingestion_service = None
extraction_service = None


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle non-command messages (ingest and extract)."""

    message = update.message

    if not message.text:
        # Skip non-text messages for M1
        await message.reply_text("I can only process text messages for now.")
        return

    try:
        # Ingest message
        event_id = await ingestion_service.ingest_message(
            content=message.text,
            source=SourceType.TELEGRAM,
            source_id=str(message.message_id),
            author="user",
            conversation_id=str(update.effective_chat.id),
            metadata={
                "telegram_user_id": update.effective_user.id,
                "telegram_username": update.effective_user.username,
                "telegram_chat_id": update.effective_chat.id,
            },
        )

        audit_logger.info("telegram_message_ingested event_id=%s", str(event_id))

        # Trigger extraction (synchronous for M1)
        extracted_items = await extraction_service.extract_from_message(event_id)
        audit_logger.info(
            "telegram_extraction_triggered event_id=%s extracted_count=%s",
            str(event_id),
            len(extracted_items),
        )

        # Acknowledge with details
        if extracted_items:
            lines = ["✅ Got it! Extracted:"]
            for _, obj_type, obj_data in extracted_items:
                if obj_type == "todo":
                    priority = obj_data.get("priority", "medium")
                    lines.append(f"  📋 Todo: {obj_data['title']} [{priority}]")
                elif obj_type == "note":
                    lines.append(f"  📝 Note: {obj_data['title']}")
                elif obj_type == "track":
                    lines.append(f"  📊 Track: {obj_data['title']}")
            await message.reply_text("\n".join(lines))
        else:
            await message.reply_text("✅ Message recorded. No objects extracted.")

    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        await message.reply_text("❌ Sorry, I couldn't process that message. Please try again.")
