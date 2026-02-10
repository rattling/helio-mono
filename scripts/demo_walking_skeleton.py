#!/usr/bin/env python
"""
Walking skeleton demonstration script.

This script demonstrates the end-to-end flow:
1. Ingest a message
2. Extract objects from it
3. Rebuild projections
4. Query the extracted objects

Run: python scripts/demo_walking_skeleton.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.contracts import SourceType
from services.event_store.file_store import FileEventStore
from services.ingestion.service import IngestionService
from services.extraction.service import ExtractionService
from services.query.service import QueryService


async def main():
    """Run the walking skeleton demonstration."""
    print("=" * 70)
    print("HELIONYX WALKING SKELETON DEMONSTRATION")
    print("=" * 70)
    print()

    # Initialize services
    print("[ Initializing services... ]")
    event_store = FileEventStore("./data/events")
    ingestion = IngestionService(event_store)
    extraction = ExtractionService(event_store)
    query = QueryService(event_store)
    print("✓ Services initialized")
    print()

    # Step 1: Ingest some messages
    print("[ Step 1: Ingesting messages ]")
    
    messages = [
        {
            "content": "Remind me to review the quarterly reports by end of week. This is high priority.",
            "author": "user",
        },
        {
            "content": "Note: The new API endpoint documentation is available at docs.example.com",
            "author": "user",
        },
        {
            "content": "Track progress on the database migration project",
            "author": "user",
        },
    ]
    
    message_ids = []
    for i, msg in enumerate(messages, 1):
        event_id = await ingestion.ingest_message(
            content=msg["content"],
            source=SourceType.CLI,
            source_id=f"demo-{i}",
            author=msg["author"],
        )
        message_ids.append(event_id)
        print(f"✓ Ingested message {i}: {msg['content'][:50]}...")
    
    print(f"\nIngested {len(message_ids)} messages")
    print()

    # Step 2: Extract objects from messages
    print("[ Step 2: Extracting objects from messages ]")
    
    all_extractions = []
    for i, msg_id in enumerate(message_ids, 1):
        extractions = await extraction.extract_from_message(msg_id)
        all_extractions.extend(extractions)
        print(f"✓ Extracted {len(extractions)} object(s) from message {i}")
    
    print(f"\nExtracted {len(all_extractions)} total objects")
    print()

    # Step 3: Rebuild projections
    print("[ Step 3: Rebuilding projections from event log ]")
    await query.rebuild_projections()
    stats = query.get_stats()
    print(f"✓ Projections rebuilt")
    print(f"  - Todos: {stats['todos']}")
    print(f"  - Notes: {stats['notes']}")
    print(f"  - Tracks: {stats['tracks']}")
    print()

    # Step 4: Query extracted objects
    print("[ Step 4: Querying extracted objects ]")
    
    todos = await query.get_todos()
    print(f"\n📋 Todos ({len(todos)}):")
    for todo in todos:
        print(f"  - {todo['title']}")
        print(f"    Priority: {todo['priority']}, Status: {todo['status']}")
    
    notes = await query.get_notes()
    print(f"\n📝 Notes ({len(notes)}):")
    for note in notes:
        print(f"  - {note['title']}")
        print(f"    {note['content'][:80]}...")
    
    tracks = await query.get_tracks()
    print(f"\n📊 Tracking Items ({len(tracks)}):")
    for track in tracks:
        print(f"  - {track['title']}")
        print(f"    Status: {track['status']}")
    
    print()
    print("=" * 70)
    print("✅ WALKING SKELETON COMPLETE")
    print("=" * 70)
    print()
    print("Next steps:")
    print("  - Check event log files in ./data/events/")
    print("  - Inspect events: cat ./data/events/events-*.jsonl | jq")
    print("  - Run again to see persistence across runs")
    print()


if __name__ == "__main__":
    asyncio.run(main())
