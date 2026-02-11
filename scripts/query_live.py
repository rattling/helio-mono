#!/usr/bin/env python3
"""Query system state interactively.

This script provides an interactive menu for querying todos, notes, and tracks
with optional tag filtering. It rebuilds projections from the event log on
startup to ensure data is current.

Usage:
    python scripts/query_live.py

The script will:
1. Rebuild projections from event log
2. Display system stats
3. Present interactive menu for queries
4. Format results in readable form

Example session:
    $ python scripts/query_live.py
    
    Rebuilding projections...
    ✓ Projections rebuilt
    
    === System Stats ===
    Todos: 15 (5 pending, 3 urgent)
    Notes: 8
    Tracks: 3
    
    What would you like to query?
    1. List all todos
    2. List todos by tag
    3. List all notes
    4. List notes by tag
    5. List all tracks
    6. List tracks by tag
    7. Refresh stats
    8. Exit
    
    Choice [1-8]: 2
    Enter tag: work
    
    📋 Todos tagged 'work' (3):
    ...
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.event_store.file_store import FileEventStore
from services.query.service import QueryService


def format_todo(todo):
    """Format a todo for display."""
    lines = [
        f"  • {todo['title']}",
        f"    Priority: {todo['priority']}, Status: {todo['status']}",
    ]
    if todo['tags']:
        lines.append(f"    Tags: {', '.join(todo['tags'])}")
    if todo.get('due_date'):
        lines.append(f"    Due: {todo['due_date']}")
    return "\n".join(lines)


def format_note(note):
    """Format a note for display."""
    lines = [
        f"  • {note['title']}",
    ]
    if note['tags']:
        lines.append(f"    Tags: {', '.join(note['tags'])}")
    if note.get('content'):
        # Truncate long content
        content = note['content']
        if len(content) > 100:
            content = content[:97] + "..."
        lines.append(f"    Content: {content}")
    return "\n".join(lines)


def format_track(track):
    """Format a track for display."""
    lines = [
        f"  • {track['title']}",
    ]
    if track['tags']:
        lines.append(f"    Tags: {', '.join(track['tags'])}")
    if track.get('value') or track.get('unit'):
        value_str = f"{track.get('value', '?')} {track.get('unit', '')}"
        lines.append(f"    Value: {value_str}")
    return "\n".join(lines)


async def display_stats(query: QueryService):
    """Display system statistics."""
    stats = query.get_stats()
    
    print(f"\n{'='*60}")
    print("System Stats")
    print(f"{'='*60}")
    print(f"Todos: {stats['todos']}")
    print(f"Notes: {stats['notes']}")
    print(f"Tracks: {stats['tracks']}")
    print(f"{'='*60}\n")


async def list_todos(query: QueryService, tag=None):
    """List todos with optional tag filter."""
    if tag:
        print(f"\n📋 Todos tagged '{tag}':\n")
        todos = await query.get_todos(tags=[tag])
    else:
        print(f"\n📋 All Todos:\n")
        todos = await query.get_todos()
    
    if not todos:
        print("  (none)")
    else:
        for todo in todos:
            print(format_todo(todo))
            print()


async def list_notes(query: QueryService, tag=None):
    """List notes with optional tag filter."""
    if tag:
        print(f"\n📝 Notes tagged '{tag}':\n")
        notes = await query.get_notes(tags=[tag])
    else:
        print(f"\n📝 All Notes:\n")
        notes = await query.get_notes()
    
    if not notes:
        print("  (none)")
    else:
        for note in notes:
            print(format_note(note))
            print()


async def list_tracks(query: QueryService, tag=None):
    """List tracks with optional tag filter."""
    if tag:
        print(f"\n📊 Tracks tagged '{tag}':\n")
        tracks = await query.get_tracks(tags=[tag])
    else:
        print(f"\n📊 All Tracks:\n")
        tracks = await query.get_tracks()
    
    if not tracks:
        print("  (none)")
    else:
        for track in tracks:
            print(format_track(track))
            print()


async def interactive_menu(query: QueryService):
    """Run interactive query menu."""
    while True:
        print("\nWhat would you like to query?")
        print("  1. List all todos")
        print("  2. List todos by tag")
        print("  3. List all notes")
        print("  4. List notes by tag")
        print("  5. List all tracks")
        print("  6. List tracks by tag")
        print("  7. Refresh stats")
        print("  8. Exit")
        print()
        
        try:
            choice = input("Choice [1-8]: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nGoodbye!")
            return
        
        if choice == "1":
            await list_todos(query)
        elif choice == "2":
            tag = input("Enter tag: ").strip()
            if tag:
                await list_todos(query, tag)
        elif choice == "3":
            await list_notes(query)
        elif choice == "4":
            tag = input("Enter tag: ").strip()
            if tag:
                await list_notes(query, tag)
        elif choice == "5":
            await list_tracks(query)
        elif choice == "6":
            tag = input("Enter tag: ").strip()
            if tag:
                await list_tracks(query, tag)
        elif choice == "7":
            await display_stats(query)
        elif choice == "8":
            print("\nGoodbye!")
            return
        else:
            print("Invalid choice. Please enter 1-8.")


async def main():
    """Run interactive query session."""
    print("Initializing Helionyx Query Interface...\n")
    
    # Initialize services
    event_store = FileEventStore("./data/events")
    query = QueryService(event_store)
    
    # Rebuild projections to ensure current data
    print("Rebuilding projections from event log...")
    try:
        await query.rebuild_projections()
        print("✓ Projections rebuilt\n")
    except Exception as e:
        print(f"✗ Error rebuilding projections: {e}")
        return 1
    
    # Display initial stats
    await display_stats(query)
    
    # Start interactive menu
    await interactive_menu(query)
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
