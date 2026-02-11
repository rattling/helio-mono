# Helionyx User Guide - Milestone 1

**Version**: 1.0  
**Date**: February 11, 2026  
**Audience**: Business users and QA agents

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Configuration Reference](#configuration-reference)
3. [Interaction Methods](#interaction-methods)
4. [Core Workflows](#core-workflows)
5. [Inspection and Verification](#inspection-and-verification)
6. [Troubleshooting](#troubleshooting)
7. [Data Management](#data-management)
8. [Performance and Costs](#performance-and-costs)
9. [Known Limitations](#known-limitations)
10. [Quick Reference](#quick-reference)

---

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Git
- OpenAI API key (optional, for real LLM extraction)
- Telegram bot token (optional, for Telegram interface)

### First-Time Setup

```bash
# 1. Clone the repository
git clone git@github.com:rattling/helio-mono.git
cd helio-mono

# 2. Set up environment
make setup

# 3. Install dependencies
make install

# 4. Configure environment (see Configuration section)
cp .env.example .env
# Edit .env with your API keys

# 5. Verify installation
make test
```

If tests pass, you're ready to use the system!

---

## Configuration Reference

All configuration is done through environment variables in the `.env` file.

### Event Store

```bash
# Where events are stored (append-only log)
EVENTS_DIR=./data/events
```

### OpenAI (for LLM extraction)

```bash
# Required for real LLM extraction
OPENAI_API_KEY=sk-...

# Model to use (recommended: gpt-4o-mini)
OPENAI_MODEL=gpt-4o-mini

# Max tokens per extraction request
OPENAI_MAX_TOKENS=1000

# Temperature for extraction (lower = more deterministic)
OPENAI_TEMPERATURE=0.0
```

**Note**: If `OPENAI_API_KEY` is not set, the system will use Mock LLM (keyword-based extraction, free but lower quality).

### Telegram Bot

```bash
# Bot token from @BotFather
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...

# Your Telegram chat ID (for notifications)
TELEGRAM_CHAT_ID=123456789
```

**To get your chat ID**:
1. Open Telegram and search for your bot (use the username you created with @BotFather)
2. **Send any message to your bot** (e.g., "hello" or "/start")
3. Visit in your browser: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Replace `<YOUR_BOT_TOKEN>` with your actual token
4. Look for `"chat":{"id":123456789}` in the JSON response
5. Copy that number (e.g., `123456789`) - this is your chat ID

**Example**:
```json
{
  "ok": true,
  "result": [{
    "message": {
      "chat": {
        "id": 123456789,    <-- This is your chat ID
        "first_name": "John",
        "type": "private"
      }
    }
  }]
}
```

### Notifications

```bash
# Enable/disable push notifications
NOTIFICATIONS_ENABLED=true

# What time to send daily summary (24-hour format)
DAILY_SUMMARY_HOUR=20

# Time window for sending reminders (24-hour format)
REMINDER_WINDOW_START=8
REMINDER_WINDOW_END=21

# How many hours before due date to remind
REMINDER_ADVANCE_HOURS=24
```

### Projections Database

```bash
# Where SQLite database is stored
PROJECTIONS_DB_PATH=./data/projections/helionyx.db
```

---

## Interaction Methods

Helionyx provides three ways to interact with the system.

### Method 1: Interactive CLI Scripts

#### Ingesting Messages

Use this to enter messages manually:

```bash
python scripts/ingest_live.py
```

**Example session**:
```
$ python scripts/ingest_live.py
Enter messages (one per line, Ctrl+D when done):

> Remind me to review reports tomorrow. This is urgent work stuff.
> Take note: meeting moved to Friday
> Track: ran 5k today
^D

Ingesting 3 messages...
✓ Message 1 ingested: evt_abc123
✓ Message 2 ingested: evt_def456
✓ Message 3 ingested: evt_ghi789

Done! 3 messages ingested.
Next steps:
  - Run extraction: python scripts/extract_live.py
  - View events: python scripts/view_events.py
  - Query system: python scripts/query_live.py
```

**Tips**:
- One message per line
- Press Enter after each message
- Press Ctrl+D (Unix) or Ctrl+Z (Windows) when done
- Press Ctrl+C to abort

#### Running Extraction

After ingesting messages, extract structured objects:

```bash
# Extract from new/unprocessed messages only
python scripts/extract_live.py

# Force re-extract ALL messages (uses API!)
python scripts/extract_live.py --all
```

**Example output**:
```
$ python scripts/extract_live.py
Using OpenAI LLM for extraction
Reading event log...
Found 3 unprocessed messages
Running extraction...

✓ evt_abc123... → 1 todo
✓ evt_def456... → 1 note
✓ evt_ghi789... → 1 track

============================================================
Extraction Complete
============================================================
Messages processed: 3
Objects extracted: 3
Errors: 0

Next steps:
  - View events: python scripts/view_events.py
  - Query system: python scripts/query_live.py
```

#### Querying Data

Query todos, notes, and tracks interactively:

```bash
python scripts/query_live.py
```

**Example session**:
```
$ python scripts/query_live.py
Initializing Helionyx Query Interface...

Rebuilding projections from event log...
✓ Projections rebuilt

============================================================
System Stats
============================================================
Todos: 15
Notes: 8
Tracks: 3
============================================================

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

📋 Todos tagged 'work':

  • Review reports tomorrow
    Priority: urgent, Status: pending
    Tags: work, urgent
    Due: 2026-02-12

  • Prepare slides
    Priority: medium, Status: pending
    Tags: work, presentations

...

Choice [1-8]: 8

Goodbye!
```

### Method 2: Telegram Bot

The Telegram bot allows you to interact with Helionyx from your phone or desktop Telegram app.

#### Setup

1. **Get bot token from @BotFather**:
   - Message @BotFather on Telegram
   - Send `/newbot` and follow instructions
   - Copy your bot token

2. **Add token to .env**:
   ```bash
   TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
   TELEGRAM_CHAT_ID=your_chat_id
   ```

3. **Start the bot**:
   ```bash
   make telegram
   ```
   
   Keep this running in a terminal.

#### Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/start` | Welcome message | `/start` |
| `/help` | List all commands | `/help` |
| `/status` | Show system stats | `/status` |
| `/todos [tag]` | List todos (optional filter) | `/todos work` |
| `/notes [tag]` | List notes (optional filter) | `/notes` |
| `/tracks [tag]` | List tracks (optional filter) | `/tracks fitness` |
| Send any text | Ingest and extract | `Remind me to call John` |

#### Example Telegram Session

```
You: /start
Bot: 👋 Welcome to Helionyx!
     Your personal decision and execution substrate.
     
     Send me any message to ingest it.
     Use /help to see available commands.

You: Remind me to review reports tomorrow. This is urgent work stuff.
Bot: ✓ Message received and processed

You: /todos work
Bot: 📋 Todos tagged 'work' (1):
     
     • Review reports tomorrow
       Priority: urgent, Status: pending
       Tags: work, urgent
       Due: 2026-02-12

You: /status
Bot: 📊 System Status
     
     Todos: 15 (5 pending, 3 urgent)
     Notes: 8
     Tracks: 3
     
     Last updated: 2026-02-11 14:30:00
```

#### Notifications

If `NOTIFICATIONS_ENABLED=true`, you'll receive:

- **Due date reminders**: 24 hours before a todo is due (during reminder window)
- **Daily summary**: Overview of pending todos at configured time

### Method 3: Bulk Import (ChatGPT History)

Import your ChatGPT conversation history:

```bash
make import-chatgpt FILE=conversations.json
```

**How to export from ChatGPT**:
1. Go to ChatGPT Settings
2. Click "Data Controls" → "Export Data"
3. Wait for email with download link (can take hours)
4. Download and extract the archive
5. Find `conversations.json` file
6. Import: `make import-chatgpt FILE=/path/to/conversations.json`

**Example output**:
```
$ make import-chatgpt FILE=conversations.json
Loading ChatGPT export from: conversations.json
Loaded 5 conversations
Extracted 127 messages from 5 conversations
Starting import of 127 messages...
Progress: 10/127 messages processed
Progress: 20/127 messages processed
...
Progress: 120/127 messages processed

=== Import Complete ===
Total messages: 127
Imported: 127
Skipped (duplicates): 0
Objects extracted: 45
Errors: 0
```

---

## Core Workflows

### Workflow 1: Daily Usage via Telegram

**Best for**: Daily capture of todos, notes, and thoughts.

1. **One-time setup**:
   ```bash
   # Configure bot token in .env
   TELEGRAM_BOT_TOKEN=...
   TELEGRAM_CHAT_ID=...
   NOTIFICATIONS_ENABLED=true
   
   # Start bot (leave running)
   make telegram
   ```

2. **Daily usage**: Just message your bot throughout the day
   - `Remind me to review reports tomorrow`
   - `Note: new process for expense reports`
   - `Track: meditated 10 minutes`

3. **Query when needed**:
   - `/todos` - See all pending todos
   - `/todos work` - Filter by tag
   - `/notes` - Review notes
   - `/tracks fitness` - Check fitness tracking

4. **Receive reminders**: Automatic notifications for due todos

### Workflow 2: Manual Entry and Analysis

**Best for**: Focused entry sessions or when Telegram isn't accessible.

1. **Ingest messages**:
   ```bash
   python scripts/ingest_live.py
   # Enter messages, Ctrl+D when done
   ```

2. **Extract objects**:
   ```bash
   python scripts/extract_live.py
   ```

3. **Query results**:
   ```bash
   python scripts/query_live.py
   # Interactive menu for querying
   ```

4. **Inspect raw data**:
   ```bash
   python scripts/view_events.py
   ```

### Workflow 3: Historical Data Bootstrap

**Best for**: Starting with existing ChatGPT conversations.

1. **Export ChatGPT data** (see Method 3 above)

2. **Import conversations**:
   ```bash
   make import-chatgpt FILE=conversations.json
   ```

3. **Verify import**:
   ```bash
   make status
   # Should show increased event counts
   ```

4. **Query imported data**:
   ```bash
   python scripts/query_live.py
   ```

5. **Continue with daily workflows** (Workflow 1 or 2)

### Workflow 4: System Inspection and Debugging

**Best for**: Understanding what's happening under the hood.

1. **Check system status**:
   ```bash
   make status
   ```

2. **View all events**:
   ```bash
   python scripts/view_events.py
   ```

3. **Filter events by type**:
   ```bash
   cat ./data/events/events-*.jsonl | jq 'select(.event_type == "object_extracted")'
   ```

4. **View extraction artifacts**:
   ```bash
   cat ./data/events/events-*.jsonl | jq 'select(.event_type == "extraction_artifact")'
   ```

5. **Rebuild projections** (if needed):
   ```bash
   make rebuild
   ```

---

## Inspection and Verification

### Checking System Status

```bash
make status
```

Shows:
- Event counts by type
- Projection statistics
- Database location and size

### Viewing Event Log

**All events**:
```bash
python scripts/view_events.py
```

**Raw JSON**:
```bash
cat ./data/events/events-*.jsonl | jq
```

**Filter by event type**:
```bash
# Only message ingestions
cat ./data/events/events-*.jsonl | jq 'select(.event_type == "message_ingested")'

# Only extractions
cat ./data/events/events-*.jsonl | jq 'select(.event_type == "object_extracted")'

# Only extraction artifacts (LLM responses)
cat ./data/events/events-*.jsonl | jq 'select(.event_type == "extraction_artifact")'
```

**View tags from extractions**:
```bash
cat ./data/events/events-*.jsonl | \
  jq 'select(.event_type == "object_extracted") | {type: .object_type, tags: .object_data.tags}'
```

### Rebuilding Projections

The projection database (SQLite) is derived from the event log. If it gets out of sync or corrupted:

```bash
# Rebuild from event log
make rebuild

# Or manually
python scripts/rebuild_projections.py
```

This is safe to do anytime—it replays all events.

### Verifying Extraction Quality

1. **View extraction artifacts** to see LLM responses:
   ```bash
   cat ./data/events/events-*.jsonl | \
     jq 'select(.event_type == "extraction_artifact") | .llm_response' | less
   ```

2. **Compare input to extracted objects**:
   ```bash
   # View message
   cat ./data/events/events-*.jsonl | jq 'select(.event_id == "evt_abc123")'
   
   # View resulting extraction
   cat ./data/events/events-*.jsonl | jq 'select(.source_message_id == "evt_abc123")'
   ```

---

## Troubleshooting

### Bot Not Responding

**Symptoms**: Messages to bot show as delivered but no response.

**Checks**:
1. Is bot running?
   ```bash
   ps aux | grep run_telegram_bot
   ```

2. Is `TELEGRAM_BOT_TOKEN` set in `.env`?
   ```bash
   grep TELEGRAM_BOT_TOKEN .env
   ```

3. Check bot logs in terminal where you ran `make telegram`

**Solutions**:
- Restart bot: Kill process and run `make telegram` again
- Verify token is correct (test with @BotFather)
- Check chat ID is correct (for notifications)

### Extraction Not Working

**Symptoms**: Messages ingested but no objects extracted.

**Check extraction ran**:
```bash
python scripts/extract_live.py
```

**If using OpenAI**:
1. Verify API key is set:
   ```bash
   grep OPENAI_API_KEY .env
   ```

2. Check API key is valid by testing:
   ```bash
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer $OPENAI_API_KEY"
   ```

3. Check extraction artifacts for errors:
   ```bash
   cat ./data/events/events-*.jsonl | \
     jq 'select(.event_type == "extraction_artifact") | .error_message'
   ```

**Solutions**:
- Set valid `OPENAI_API_KEY` in `.env`
- Or remove to use Mock LLM (free, keyword-based)
- Check OpenAI account has credits

### Queries Return Empty Results

**Symptoms**: `query_live.py` or Telegram commands return no results.

**Checks**:
1. Have messages been ingested?
   ```bash
   python scripts/view_events.py
   # Should show message_ingested events
   ```

2. Has extraction been run?
   ```bash
   cat ./data/events/events-*.jsonl | grep "object_extracted"
   ```

3. Have projections been rebuilt?
   ```bash
   ls -lh ./data/projections/helionyx.db
   ```

**Solutions**:
1. Ingest messages: `python scripts/ingest_live.py`
2. Run extraction: `python scripts/extract_live.py`
3. Rebuild projections: `make rebuild`
4. Query again: `python scripts/query_live.py`

### Notifications Not Sending

**Symptoms**: No reminder or daily summary messages from bot.

**Checks**:
1. Is `NOTIFICATIONS_ENABLED=true`?
2. Is bot running (not just started and stopped)?
3. Are time windows configured correctly?
4. Do todos have due dates?

**Solutions**:
- Keep bot running: `make telegram` (don't close terminal)
- Check `.env` notification settings
- Verify todos have `due_date` fields
- Check current time is within reminder window

### Database Issues

**Symptoms**: Query errors, crashes, or corrupted data.

**Solution**: Rebuild projections (safe, non-destructive):
```bash
rm ./data/projections/helionyx.db
make rebuild
```

The event log is the source of truth—projections can always be rebuilt.

---

## Data Management

### Backup

**Event log** (source of truth):
```bash
# Create timestamped backup
tar -czvf backup-events-$(date +%Y%m%d).tar.gz ./data/events/
```

**Projections** (optional, rebuildable):
```bash
# Backup SQLite database
cp ./data/projections/helionyx.db ./backups/helionyx-$(date +%Y%m%d).db
```

**Recommended**: Only back up event log. Projections can be rebuilt anytime.

### Restore

```bash
# Restore events from backup
tar -xzvf backup-events-20260211.tar.gz

# Rebuild projections
make rebuild
```

### Fresh Start (Testing)

To completely reset the system:

```bash
# Remove all data
rm -rf ./data/events/*.jsonl
rm -rf ./data/projections/*.db

# System is now empty
```

⚠️ **Warning**: This deletes all your data. Back up first!

---

## Performance and Costs

### LLM API Costs

**Using OpenAI** (gpt-4o-mini):
- Input: ~$0.15 per 1M tokens
- Output: ~$0.60 per 1M tokens
- Average message: ~200 input tokens, ~150 output tokens
- **Cost per message**: ~$0.05 USD
- **1000 messages**: ~$50 USD

**Using Mock LLM**:
- Free (no API calls)
- Keyword-based extraction
- Lower quality but functional

**To switch**:
- Set `OPENAI_API_KEY` in `.env` for real extraction
- Unset or remove for Mock LLM

### Storage Requirements

- **Event log**: ~1-2 KB per message
- **SQLite projections**: ~500 bytes per object
- **10,000 messages**: ~20 MB total

Storage is minimal. Event log grows linearly with usage.

### Extraction Speed

- **With OpenAI**: 1-3 seconds per message (API latency)
- **With Mock LLM**: Instant (local processing)
- **Bulk extraction**: Can process hundreds of messages in minutes

---

## Known Limitations (M1)

Milestone 1 intentionally excludes certain features:

**Not Supported**:
- ❌ Web UI (Telegram and CLI only)
- ❌ HTTP REST API
- ❌ Multi-user support
- ❌ Email or calendar integrations
- ❌ Complex scheduling (just basic due dates)
- ❌ Autonomous task execution
- ❌ Real-time extraction (must trigger manually via script or bot)

**Why**: M1 focuses on core functionality and correctness. These features are planned for future milestones.

**What Works**:
- ✅ Message ingestion (CLI, Telegram, ChatGPT import)
- ✅ LLM-based extraction
- ✅ Durable persistence
- ✅ Tag-based querying
- ✅ Telegram bot interface
- ✅ Push notifications (reminders, daily summary)
- ✅ Event log inspection

---

## Quick Reference

### Daily Commands

```bash
# Start Telegram bot (keep running)
make telegram

# Ingest messages interactively
python scripts/ingest_live.py

# Extract objects from new messages
python scripts/extract_live.py

# Query system interactively
python scripts/query_live.py

# Check system status
make status

# Run tests
make test
```

### Maintenance Commands

```bash
# Rebuild projections from event log
make rebuild

# View event log
python scripts/view_events.py

# Import ChatGPT conversations
make import-chatgpt FILE=conversations.json

# Clean Python cache
make clean

# Backup event log
tar -czvf backup-$(date +%Y%m%d).tar.gz ./data/events/
```

### Telegram Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message |
| `/help` | Show all commands |
| `/status` | System stats |
| `/todos` | List all todos |
| `/todos <tag>` | Todos filtered by tag |
| `/notes` | List all notes |
| `/notes <tag>` | Notes filtered by tag |
| `/tracks` | List all tracks |
| `/tracks <tag>` | Tracks filtered by tag |

### Key Files

| File | Purpose |
|------|---------|
| `.env` | Configuration (API keys, settings) |
| `./data/events/*.jsonl` | Event log (source of truth) |
| `./data/projections/helionyx.db` | SQLite database (rebuildable) |
| `docs/PROJECT_CHARTER.md` | Project vision and principles |
| `docs/ARCHITECTURE.md` | System architecture |

### Getting Help

**For technical issues**:
- Check this guide's Troubleshooting section
- Review event log: `python scripts/view_events.py`
- Check system status: `make status`
- Review architecture docs in `docs/`

**For questions about the system**:
- Read `docs/PROJECT_CHARTER.md` for vision and principles
- Read `docs/ARCHITECTURE.md` for system design
- Review ADRs in `docs/` for specific technical decisions

---

## Summary

You now have everything you need to use Helionyx M1:

1. **Three interaction methods**: CLI scripts, Telegram bot, ChatGPT import
2. **Complete workflows**: Daily usage, manual entry, historical bootstrap
3. **Inspection tools**: View events, query data, check stats
4. **Troubleshooting guide**: Solutions to common issues
5. **Data management**: Backup, restore, fresh start

**Next steps**:
1. Configure your `.env` file
2. Choose your primary interaction method
3. Start ingesting messages
4. Run extraction
5. Query your data

Welcome to Helionyx! 🚀
