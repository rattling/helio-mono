# Helionyx

Personal decision and execution substrate built on an append-only event log foundation.

## Project Status

**Current Milestone**: Milestone 10 - Data Explorer (Power-User Interrogation and Traceability)  
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

# 4. Start API + UI together (default: dev)
make web-install
make up

# 5. Check comprehensive local status
make status

# 6. Stop both when done
make down
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

### Local Runtime Control (API/UI)

Use these targets for easy local process control in `dev`, `staging`, or `live`.

```bash
# Start API + UI in background for an environment
make up ENV=dev
make up ENV=staging
make up ENV=live

# Start only one surface
make start-api ENV=dev
make start-web ENV=dev

# Stop one or both
make stop-api ENV=dev
make stop-web ENV=dev
make down ENV=dev

# Tail logs
make logs-api ENV=dev
make logs-web ENV=dev

# Comprehensive status (processes + endpoint probes + event data)
make status ENV=dev
```

### Execution Modes (Important)

There are two distinct ways commands run in this repo:

1. **Local process mode (direct host processes, non-systemd)**
   - Uses targets like: `make run`, `make web-run`, `make start-api`, `make start-web`, `make up`, `make down`
   - Intended for local development and quick operator workflows
   - Uses foreground processes (`run`, `web-run`) or background PID/log files in `.run/`

2. **Deployment mode (systemd-oriented on node1)**
   - Uses targets like: `make deploy ENV=<env>`, `make restart ENV=<env>`, `make logs ENV=<env>`, `make stop ENV=<env>`
   - Intended for managed deployed services
   - Delegates to deployment scripts in `scripts/deploy/` and systemd unit management

Defaults by environment:
- `dev`: API `8000`, UI `5173`
- `staging`: API `8001`, UI `5174`
- `live`: API `8002`, UI `5175`

You can override ports and API URL when needed:

```bash
make up ENV=dev API_PORT=8010 UI_PORT=5180 API_BASE_URL=http://localhost:8010
```

### Start the Web UI (Milestone 10)

Run the API service first (`make run`) in one terminal, then in a separate terminal:

```bash
make web-install
make web-run ENV=dev
make web-run ENV=staging
make web-run ENV=live
```

Open the matching UI port (default `5173` for dev) for:
- **Tasks**: list/create/edit/complete/snooze workflows
- **Control Room**: health/readiness + attention transparency views
- **Data Explorer**: lookup/timeline/state/decision interrogation views

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
├── web/                  # Milestone 9+ web UI (React + TypeScript + Vite)
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

# Start API + UI together in background
make up ENV=dev

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

# Stop API + UI background processes
make down ENV=dev

# Run linters
make lint

# Format code
make format

# Run the same lint/format checks as CI
make precommit

# Run tests
make test

# Run web tests
make web-test

# Clean generated files
make clean
```

## Learning Controls and Verification

- Runtime mode control: `ATTENTION_PERSONALIZATION_MODE=deterministic|shadow|bounded`
- Replay diagnostics report: `.venv/bin/python scripts/evaluate_attention_replay.py --out data/projections/attention_replay_report.json`
- Milestone 8 per-target diagnostics: `jq '.target_diagnostics' data/projections/attention_replay_report.json`
- Operational rollout/rollback and QA checklist: `docs/M6_LEARNING_RUNBOOK.md`

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
- `GET /api/v1/tasks` - List tasks (`status`, `project`, `search`, `sort_by`, `sort_dir`, `limit`, `offset`)
- `GET /api/v1/tasks/{task_id}` - Get one task
- `PATCH /api/v1/tasks/{task_id}` - Patch mutable task fields
- `POST /api/v1/tasks/{task_id}/complete` - Mark task done
- `POST /api/v1/tasks/{task_id}/snooze` - Snooze task until timestamp
- `POST /api/v1/tasks/{task_id}/link` - Link blocking task dependencies
- `GET /api/v1/tasks/review/queue` - Deterministic review queue with passive stale detection

## Control Room API (Milestone 9)

- `GET /api/v1/control-room/overview` - Consolidated transparency payload:
   - health and readiness checks
   - attention today/week snapshots
   - explanation-oriented ranking fields for inspectability

## Data Explorer API (Milestone 10)

- `GET /api/v1/explorer/lookup` - Canonical entity lookup by type/id
- `GET /api/v1/explorer/timeline` - Ordered event timeline for selected entity context
- `GET /api/v1/explorer/state` - Projection/state snapshot with traceability refs
- `GET /api/v1/explorer/decision` - Decision/rationale-oriented evidence feed

### Data Explorer Interrogation Workflow

Use this sequence for power-user debugging:

1. Start from a known ID in Control Room (for example a surfaced `task_id`).
2. Open **Data Explorer** and run **Lookup** for canonical object state.
3. Run **Timeline** to inspect ordered event causality.
4. Run **State** to inspect current projection snapshot + traceability links.
5. Run **Decision** to inspect decision/suggestion/reminder rationale evidence.

Deep-link contract for cross-surface reproducibility is URL-based:
- `tab=data-explorer`
- `explorer_entity_type=<task|event>`
- `explorer_entity_id=<id>`
- `explorer_view=<lookup|timeline|state|decision>`

## Documentation

- **Project Charter**: [docs/PROJECT_CHARTER.md](docs/PROJECT_CHARTER.md)
- **Architecture Decision**: [docs/ARCHITECTURE_DECISION_M0.md](docs/ARCHITECTURE_DECISION_M0.md)
- **Engineering Constitution**: [.github/ENGINEERING_CONSTITUTION.md](.github/ENGINEERING_CONSTITUTION.md)
- **Workflow**: [.github/WORKFLOW.md](.github/WORKFLOW.md)

## Milestones

- **Milestone 0** (Complete): Architecture Baseline
- **Milestone 1** (Complete): Core functionality with Telegram integration
- **Milestone 9** (Complete): UI Foundation (Tasks + Control Room)
- **Milestone 10** (In Progress): Data Explorer (Power-User Interrogation and Traceability)
- **Milestone 10A** (Planned): Data Explorer Guided Insights (Opinionated UX + Ad Hoc Power)
- **Milestone 11** (Planned): Helionyx Lab (Learning, LLMs, and Controlled Experimentation)

## Contributing

This is a personal project following structured agent-driven development.  
See [.github/WORKFLOW.md](.github/WORKFLOW.md) for execution guidelines.

## License

Private repository - All rights reserved.
