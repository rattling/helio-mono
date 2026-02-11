#!/usr/bin/env python3
"""Import ChatGPT conversation history into Helionyx.

This script imports messages from ChatGPT JSON export format and triggers
extraction to create todos, notes, and tracks from the conversation history.

Usage:
    python scripts/import_chatgpt.py <path-to-conversations.json>

The ChatGPT export format has this structure:
{
  "conversations": [
    {
      "id": "conversation-uuid",
      "title": "Conversation title",
      "create_time": 1707580000.0,
      "update_time": 1707590000.0,
      "mapping": {
        "node-id-1": {
          "id": "node-id-1",
          "message": {
            "id": "message-uuid",
            "author": {"role": "user"},
            "content": {"parts": ["message text"]},
            "create_time": 1707580000.0
          }
        },
        ...
      }
    }
  ]
}
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from uuid import uuid5, NAMESPACE_DNS

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.contracts import SourceType
from services.event_store.file_store import FileEventStore
from services.ingestion.service import IngestionService
from services.extraction.service import ExtractionService
from services.extraction.openai_client import OpenAILLMService
from shared.common.config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_chatgpt_export(file_path: Path) -> dict:
    """Load ChatGPT export JSON file."""
    logger.info(f"Loading ChatGPT export from: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if 'conversations' not in data:
        raise ValueError("Invalid ChatGPT export format: missing 'conversations' key")
    
    logger.info(f"Loaded {len(data['conversations'])} conversations")
    return data


def extract_messages_from_conversation(conversation: dict) -> list[dict]:
    """Extract messages from a conversation mapping."""
    messages = []
    
    conversation_id = conversation.get('id', 'unknown')
    conversation_title = conversation.get('title', 'Untitled')
    
    # The mapping contains nodes with messages
    mapping = conversation.get('mapping', {})
    
    for node_id, node in mapping.items():
        message = node.get('message')
        
        if not message:
            continue
        
        # Get message details
        author = message.get('author', {})
        role = author.get('role', 'unknown')
        
        content = message.get('content', {})
        parts = content.get('parts', [])
        
        # Concatenate all parts
        text = '\n'.join(part for part in parts if isinstance(part, str))
        
        if not text.strip():
            continue
        
        create_time = message.get('create_time')
        
        messages.append({
            'conversation_id': conversation_id,
            'conversation_title': conversation_title,
            'message_id': message.get('id', node_id),
            'role': role,
            'text': text,
            'timestamp': datetime.fromtimestamp(create_time) if create_time else None
        })
    
    return messages


def generate_idempotent_source_id(conversation_id: str, message_id: str) -> str:
    """Generate deterministic source ID for idempotency."""
    # Use UUID5 to create deterministic ID from conversation + message ID
    namespace = uuid5(NAMESPACE_DNS, "helionyx.chatgpt.import")
    return str(uuid5(namespace, f"{conversation_id}:{message_id}"))


async def import_messages(
    messages: list[dict],
    ingestion_service: IngestionService,
    extraction_service: ExtractionService
) -> dict:
    """Import messages and trigger extraction."""
    
    stats = {
        'total': len(messages),
        'imported': 0,
        'skipped': 0,
        'extracted': 0,
        'errors': 0
    }
    
    logger.info(f"Starting import of {stats['total']} messages...")
    
    for i, msg in enumerate(messages, 1):
        try:
            # Generate idempotent source ID
            source_id = generate_idempotent_source_id(
                msg['conversation_id'],
                msg['message_id']
            )
            
            # Build message content with context
            content = f"[ChatGPT {msg['role']}] {msg['text']}"
            
            # Ingest message
            message_event_id = await ingestion_service.ingest_message(
                content=content,
                source=SourceType.CHATGPT_DUMP,
                source_id=source_id,
                author=f"chatgpt-{msg['role']}"
            )
            
            if message_event_id:
                stats['imported'] += 1
                
                # Only extract from user messages (not assistant responses)
                if msg['role'] == 'user':
                    # Trigger extraction
                    extracted_ids = await extraction_service.extract_from_message(message_event_id)
                    stats['extracted'] += len(extracted_ids)
                    
                    if extracted_ids:
                        logger.info(f"Message {i}/{stats['total']}: Extracted {len(extracted_ids)} objects")
                else:
                    logger.debug(f"Message {i}/{stats['total']}: Skipped extraction (assistant message)")
            else:
                stats['skipped'] += 1
                logger.debug(f"Message {i}/{stats['total']}: Skipped (duplicate)")
            
            # Progress update every 10 messages
            if i % 10 == 0:
                logger.info(f"Progress: {i}/{stats['total']} messages processed")
        
        except Exception as e:
            stats['errors'] += 1
            logger.error(f"Error processing message {i}: {e}", exc_info=True)
    
    return stats


async def main():
    """Main import process."""
    if len(sys.argv) < 2:
        print("Usage: python import_chatgpt.py <path-to-conversations.json>")
        sys.exit(1)
    
    file_path = Path(sys.argv[1])
    
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        sys.exit(1)
    
    try:
        # Load ChatGPT export
        data = load_chatgpt_export(file_path)
        
        # Extract all messages
        all_messages = []
        for conv in data['conversations']:
            messages = extract_messages_from_conversation(conv)
            all_messages.extend(messages)
        
        logger.info(f"Extracted {len(all_messages)} messages from {len(data['conversations'])} conversations")
        
        # Initialize services
        config = Config()
        event_store = FileEventStore(data_dir=config.EVENTS_DIR)
        ingestion_service = IngestionService(event_store)
        
        # Initialize LLM service for extraction
        llm_service = OpenAILLMService(
            event_store=event_store,
            api_key=config.OPENAI_API_KEY,
            model=config.OPENAI_MODEL,
        )
        extraction_service = ExtractionService(event_store, llm_service)
        
        # Import messages
        stats = await import_messages(all_messages, ingestion_service, extraction_service)
        
        # Print summary
        logger.info("=== Import Complete ===")
        logger.info(f"Total messages: {stats['total']}")
        logger.info(f"Imported: {stats['imported']}")
        logger.info(f"Skipped (duplicates): {stats['skipped']}")
        logger.info(f"Objects extracted: {stats['extracted']}")
        logger.info(f"Errors: {stats['errors']}")
        
        if stats['errors'] > 0:
            logger.warning("Import completed with errors. Check logs above.")
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"Import failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
