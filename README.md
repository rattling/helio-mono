# Helionyx

Personal decision and execution substrate built on an append-only event log foundation.

## Project Status

**Current Milestone**: Milestone 6 - Attention + Planning Assistant  
**Status**: 🔄 In Progress

## Quick Start

```bash
# 1. Clone and enter the repository
git clone git@github.com:rattling/helio-mono.git
cd helio-mono

# 2. Set up environment (creates .env and data directories)
make setup

# 3. Install dependencies (creates virtual environment)
make install

# 4. Run the Helionyx service (default: dev environment)
make run

# 5. Check system status
make status
```

## Running the Service

Helionyx runs as a unified service that combines:
- FastAPI HTTP server for API endpoints
- Telegram bot (optional, if configured)
- Event store and query projections

### Start the Service

```bash
# Run in development mode (default)
make run

# Run in staging mode
make run ENV=staging

# Run in live mode
make run ENV=live
```

The service will:
1. Load configuration for the specified environment
2. Initialize all services (event store, ingestion, extraction, query)
3. Rebuild projections from the event log
4. Start the Telegram bot (if credentials configured)
5. Start the FastAPI HTTP server on port 8000

Logs are visible on the console. Press Ctrl+C to stop the service cleanly.

### Health Check

While the service is running, verify it's working:

```bash
# Check health endpoint
curl http://localhost:8000/health

# Check readiness
curl http://localhost:8000/health/ready
```

## Configuration

Helionyx supports environment-specific configuration via `.env` files.

### Configuration Files

Three environment-specific example files are provided:

- **`.env.dev.example`** - Development environment (port 8000, verbose logging, local paths)
- **`.env.staging.example`** - Staging environment (port 8001, moderate logging, isolated data)
- **`.env.live.example`** - Production environment (port 8002, minimal logging, production paths)

### Setup

```bash
# For development
cp .env.dev.example .env.dev
# Edit .env.dev and fill in your credentials (OPENAI_API_KEY, TELEGRAM_BOT_TOKEN, etc.)

# For staging
cp .env.staging.example .env.staging
# Edit .env.staging with staging-specific values

# For production
cp .env.live.example .env.live
# Edit .env.live with production values
```

### Key Configuration Points

- **API Ports**: Each environment must use a unique port (8000/8001/8002) for same-host deployment
- **Data Paths**: Environments must have isolated event stores and projection databases
- **Telegram Bots**: Each environment should use a separate Telegram bot (create via @BotFather)
- **Cost Limits**: Adjust LLM cost limits per environment (lower for dev, higher for live)
- **Logging Levels**: Use DEBUG for dev, INFO for staging, WARNING for live

See [`.env.template`](.env.template) for complete documentation of all configuration options.

## Project Structure

```
helio-mono/
├── .github/               # Engineering framework and workflow
│   ├── ENGINEERING_CONSTITUTION.md
│   ├── WORKFLOW.md
│   ├── copilot-instructions.md
│   └── agents/           # Agent role charters and templates
├── docs/                 # Project documentation
│   ├── PROJECT_CHARTER.md
│   └── ARCHITECTURE_DECISION_M0.md
├── services/             # Core services (service-oriented monorepo)
│   ├── event_store/     # Append-only event persistence
│   ├── ingestion/       # Input normalization and artifact recording
│   ├── extraction/      # LLM-based object extraction
│   ├── query/           # Read models and projections
│   └── adapters/        # External interface implementations
├── shared/              # Shared code
│   ├── contracts/       # Inter-service contracts (schemas, interfaces)
│   └── common/          # Common utilities
├── tests/               # Test suite
├── scripts/             # Operational scripts
├── data/                # Runtime data (gitignored)
│   ├── events/         # Event store files
│   └── projections/    # SQLite projection databases
├── pyproject.toml       # Python project configuration
├── Makefile            # Development commands
└── README.md           # This file
```

## Services

### Event Store
Append-only event log serving as the system's source of truth.

### Ingestion
Accepts and normalizes inputs from various sources (ChatGPT dumps, Telegram, CLI).

### Extraction
Extracts structured objects (Todo, Note, Track) from messages using LLMs.

### Query
Builds queryable projections from the event log.

### Adapters
Thin translation layers for external interfaces (Telegram, API, CLI).

## Technology Stack

- **Language**: Python 3.11+
- **API Framework**: FastAPI
- **Event Storage**: File-based JSONL (append-only)
- **Projections**: SQLite
- **Schema Validation**: Pydantic
- **LLM Client**: OpenAI Python SDK
- **Testing**: pytest

## Development

```bash
# Run the Helionyx service
make run

# Run with specific environment
make run ENV=staging

# Run the walking skeleton demo
make demo

# Run Telegram bot (legacy - now integrated into main service)
make telegram

# Rebuild projections from event log
make rebuild

# Generate Milestone 6 attention replay metrics report
.venv/bin/python scripts/evaluate_attention_replay.py --out data/projections/attention_replay_report.json

# Check system status
make status

# Run linters
make lint

# Format code
make format

# Run the same lint/format checks as CI
make precommit

# Run tests
make test

# Clean generated files
make clean
```

## OpenAI Integration

Helionyx uses OpenAI's API for intelligent extraction of todos, notes, and tracking items from natural language messages.

### Setup

1. Get an OpenAI API key from [platform.openai.com](https://platform.openai.com)
2. Add it to your `.env`:
   ```bash
   OPENAI_API_KEY=sk-...
   OPENAI_MODEL=gpt-4o-mini  # or gpt-4o
   ```
3. Optional rate limiting and cost control:
   ```bash
   OPENAI_RATE_LIMIT_RPM=10
   OPENAI_RATE_LIMIT_TPM=150000
   LLM_DAILY_COST_WARNING_USD=1.0
   LLM_DAILY_COST_LIMIT_USD=10.0
   ```

### Cost Tracking

The system automatically tracks:
- Token usage per API call
- Estimated costs (based on current OpenAI pricing)
- Cumulative daily costs

All LLM interactions are recorded as artifacts in the event log for full traceability.

### Mock Mode

Without an OpenAI API key, the system uses a mock LLM service with keyword-based extraction. This is useful for:
- Development and testing
- Running the walking skeleton demo
- Cost-free exploration

## Telegram Bot Setup

1. Create a bot via [@BotFather](https://t.me/botfather) on Telegram
2. Get your bot token
3. Start a conversation with your bot
4. Send `/start` to the bot
5. Get your chat ID:
   - Preferred: check the service/bot logs for a line like `Chat ID: 123456789` after sending `/start`
   - Fallback: call the Telegram Bot API and read `message.chat.id`:
     ```bash
     curl -s "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getUpdates" | jq '.result[-1].message.chat.id'
     ```
     (If you don’t have `jq`, just open the JSON and look for `\"chat\": { \"id\": ... }`.)
6. Add credentials to `.env`:
   ```bash
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   TELEGRAM_CHAT_ID=your_chat_id_here
   ```
7. Run the bot: `make run` (or `make telegram` if you’re using the legacy standalone target)

### Available Commands

- `/start` - Welcome message
- `/help` - List available commands
- `/todos [status]` - Legacy alias for canonical tasks
- `/notes [search]` - List notes (optional: search term)
- `/tracks` - List tracking items
- `/tasks [status]` - List canonical tasks (open/blocked/in_progress/done/cancelled/snoozed)
- `/task_show <task_id>` - Show task details
- `/task_done <task_id>` - Mark task done
- `/task_snooze <task_id> <iso-ts>` - Snooze task until timestamp
- `/task_priority <task_id> <p0|p1|p2|p3>` - Update task priority
- `/stats` - System statistics

You can also send regular messages and the bot will extract todos, notes, and tracks automatically!

## Task API (Milestone 5)

- `POST /api/v1/tasks/ingest` - Idempotent ingest via `(source, source_ref)`
- `GET /api/v1/tasks` - List tasks (optional `status` filter)
- `GET /api/v1/tasks/{task_id}` - Get one task
- `PATCH /api/v1/tasks/{task_id}` - Patch mutable task fields
- `POST /api/v1/tasks/{task_id}/complete` - Mark task done
- `POST /api/v1/tasks/{task_id}/snooze` - Snooze task until timestamp
- `POST /api/v1/tasks/{task_id}/link` - Link blocking task dependencies
- `GET /api/v1/tasks/review/queue` - Deterministic review queue with passive stale detection

## Documentation

- **Project Charter**: [docs/PROJECT_CHARTER.md](docs/PROJECT_CHARTER.md)
- **Architecture Decision**: [docs/ARCHITECTURE_DECISION_M0.md](docs/ARCHITECTURE_DECISION_M0.md)
- **Engineering Constitution**: [.github/ENGINEERING_CONSTITUTION.md](.github/ENGINEERING_CONSTITUTION.md)
- **Workflow**: [.github/WORKFLOW.md](.github/WORKFLOW.md)

## Milestones

- **Milestone 0** (Complete): Architecture Baseline
- **Milestone 1** (Complete): Core functionality with Telegram integration

## Contributing

This is a personal project following structured agent-driven development.  
See [.github/WORKFLOW.md](.github/WORKFLOW.md) for execution guidelines.

## License

Private repository - All rights reserved.
