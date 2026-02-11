# Helionyx

Personal decision and execution substrate built on an append-only event log foundation.

## Project Status

**Current Milestone**: Milestone 1 - Core Functionality and LLM Integration  
**Status**: ✅ Complete (QA Approved)

## Quick Start

```bash
# 1. Clone and enter the repository
git clone git@github.com:rattling/helio-mono.git
cd helio-mono

# 2. Set up environment (creates .env and data directories)
make setup

# 3. Install dependencies (creates virtual environment)
make install

# 4. Run the walking skeleton demonstration
make run

# 5. Check system status
make status
```

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
# Run the walking skeleton
make run

# Run Telegram bot
make telegram

# Rebuild projections from event log
make rebuild

# Check system status
make status

# Run linters
make lint

# Format code
make format

# Run tests (when implemented)
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
4. Send `/start` to get your chat ID (logged in console)
5. Add credentials to `.env`:
   ```bash
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   TELEGRAM_CHAT_ID=your_chat_id_here
   ```
6. Run the bot: `make telegram`

### Available Commands

- `/start` - Welcome message
- `/help` - List available commands
- `/todos [status]` - List todos (optional: pending, completed, etc.)
- `/notes [search]` - List notes (optional: search term)
- `/tracks` - List tracking items
- `/stats` - System statistics

You can also send regular messages and the bot will extract todos, notes, and tracks automatically!

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
