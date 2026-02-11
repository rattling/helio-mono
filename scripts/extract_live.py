#!/usr/bin/env python3
"""Run extraction on unprocessed or all messages.

This script identifies messages that haven't been extracted yet and runs
the extraction service on them. Optionally, you can force re-extraction
of all messages.

Usage:
    # Extract only unprocessed messages (default)
    python scripts/extract_live.py
    
    # Force re-extract ALL messages (uses LLM API!)
    python scripts/extract_live.py --all

The script will:
1. Read the event log
2. Find message_ingested events
3. Check which ones have corresponding object_extracted events
4. Extract objects from unprocessed messages
5. Report results

Note: Real extraction requires OPENAI_API_KEY in .env
      Without it, Mock LLM will be used (keyword-based)
"""

import asyncio
import sys
import os
from pathlib import Path
from collections import defaultdict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.contracts import SourceType
from services.event_store.file_store import FileEventStore
from services.ingestion.service import IngestionService
from services.extraction.service import ExtractionService
from services.extraction.openai_client import OpenAILLMService
from services.extraction.mock_llm import MockLLMService


async def main():
    """Run extraction on unprocessed messages."""
    # Check for --all flag
    force_all = "--all" in sys.argv
    
    if force_all:
        print("⚠️  Warning: Re-extracting ALL messages (will use LLM API)")
        confirm = input("Continue? [y/N]: ")
        if confirm.lower() != 'y':
            print("Aborted.")
            return 0
        print()
    
    # Initialize services
    event_store = FileEventStore("./data/events")
    
    # Choose LLM service based on API key
    api_key = os.getenv("OPENAI_API_KEY", "")
    if api_key and api_key.strip():
        print("Using OpenAI LLM for extraction")
        llm_service = OpenAILLMService(event_store, api_key=api_key)
    else:
        print("Using Mock LLM for extraction (set OPENAI_API_KEY for real extraction)")
        llm_service = MockLLMService(event_store)
    
    extraction = ExtractionService(event_store, llm_service)
    
    # Read all events
    print("Reading event log...")
    events = await event_store.stream_events()
    
    # Find all message_ingested events
    ingested_messages = {}
    for event in events:
        if event.event_type == "message_ingested":
            ingested_messages[event.event_id] = {
                "content": event.content,
                "source_id": event.source_id,
                "extracted": False,
            }
    
    # Mark which messages have been extracted
    if not force_all:
        for event in events:
            if event.event_type == "object_extracted":
                source_evt_id = event.source_event_id
                if source_evt_id in ingested_messages:
                    ingested_messages[source_evt_id]["extracted"] = True
    
    # Filter to unprocessed messages
    if force_all:
        to_extract = list(ingested_messages.items())
        print(f"Found {len(to_extract)} total messages")
    else:
        to_extract = [
            (msg_id, data) 
            for msg_id, data in ingested_messages.items() 
            if not data["extracted"]
        ]
        print(f"Found {len(to_extract)} unprocessed messages")
    
    if not to_extract:
        print("No messages to extract.")
        print("\nAll caught up! 🎉")
        return 0
    
    print("Running extraction...\n")
    
    # Extract objects from each message
    extraction_count = 0
    error_count = 0
    
    for msg_id, data in to_extract:
        try:
            # Call extraction service
            result = await extraction.extract_from_message(
                message_event_id=msg_id,
            )
            
            # Count extracted objects
            obj_count = len(result)
            extraction_count += obj_count
            
            # Report
            print(f"✓ {str(msg_id)[:12]}... → {obj_count} objects extracted")
            
        except Exception as e:
            print(f"✗ {str(msg_id)[:12]}... → Error: {e}")
            error_count += 1
    
    print(f"\n{'='*60}")
    print("Extraction Complete")
    print(f"{'='*60}")
    print(f"Messages processed: {len(to_extract)}")
    print(f"Objects extracted: {extraction_count}")
    print(f"Errors: {error_count}")
    print()
    print("Next steps:")
    print("  - View events: python scripts/view_events.py")
    print("  - Query system: python scripts/query_live.py")
    print("  - Rebuild projections: python scripts/rebuild_projections.py")
    
    return 1 if error_count > 0 else 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
