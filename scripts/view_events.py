#!/usr/bin/env python
"""View events from the event log."""

import json
import sys
from pathlib import Path

def main():
    """Display events from the log."""
    data_dir = Path("./data/events")
    
    if not data_dir.exists():
        print("No event log directory found.")
        return
    
    event_files = sorted(data_dir.glob("events-*.jsonl"))
    
    if not event_files:
        print("No event files found.")
        return
    
    print(f"Found {len(event_files)} event file(s)\n")
    
    total_events = 0
    
    for event_file in event_files:
        with open(event_file) as f:
            events = [json.loads(line) for line in f]
            total_events += len(events)
            
            print(f"=== {event_file.name} ({len(events)} events) ===\n")
            
            for event in events[-5:]:  # Show last 5 events from each file
                print(f"[{event['timestamp']}] {event['event_type']}")
                if event['event_type'] == 'message_ingested':
                    print(f"  Source: {event['source']}")
                    print(f"  Content: {event['content'][:80]}...")
                elif event['event_type'] == 'object_extracted':
                    print(f"  Object: {event['object_type']}")
                    print(f"  Data: {event['object_data'].get('title', 'N/A')[:80]}")
                print()
    
    print(f"Total events across all files: {total_events}")

if __name__ == "__main__":
    main()
