#!/usr/bin/env python3
"""Ingest messages interactively via CLI.

This script allows you to enter messages interactively and ingest them
into the Helionyx event store. Each message is recorded with a unique
event ID for later extraction.

Usage:
    python scripts/ingest_live.py
    
    Then enter messages one per line. Press Ctrl+D (Unix) or Ctrl+Z (Windows)
    when done to complete ingestion.

Example:
    $ python scripts/ingest_live.py
    Enter messages (one per line, Ctrl+D when done):
    > Remind me to review reports tomorrow. This is urgent work stuff.
    > Take note: meeting moved to Friday
    ^D
    
    Ingesting 2 messages...
    ✓ Message 1 ingested: evt_abc123
    ✓ Message 2 ingested: evt_def456
    
    Done! Check events with: python scripts/view_events.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.contracts import SourceType
from services.event_store.file_store import FileEventStore
from services.ingestion.service import IngestionService


async def main():
    """Run interactive message ingestion."""
    print("Enter messages (one per line, Ctrl+D when done):")
    print()
    
    messages = []
    line_num = 0
    
    # Read messages from stdin
    try:
        while True:
            try:
                line = input("> ")
                line_num += 1
                if line.strip():
                    messages.append(line.strip())
            except EOFError:
                # Ctrl+D pressed
                break
    except KeyboardInterrupt:
        # Ctrl+C pressed
        print("\n\nAborted.")
        return 1
    
    if not messages:
        print("\nNo messages entered.")
        return 0
    
    print(f"\nIngesting {len(messages)} messages...")
    
    # Initialize services
    event_store = FileEventStore("./data/events")
    ingestion = IngestionService(event_store)
    
    # Ingest each message
    timestamp = datetime.utcnow().isoformat()
    
    for i, msg in enumerate(messages, 1):
        try:
            event_id = await ingestion.ingest_message(
                content=msg,
                source=SourceType.CLI,
                source_id=f"cli-live-{timestamp}-{i}",
                author="user",
            )
            print(f"✓ Message {i} ingested: {event_id}")
        except Exception as e:
            print(f"✗ Message {i} failed: {e}")
            return 1
    
    print(f"\nDone! {len(messages)} messages ingested.")
    print("Next steps:")
    print("  - Run extraction: python scripts/extract_live.py")
    print("  - View events: python scripts/view_events.py")
    print("  - Query system: python scripts/query_live.py")
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
