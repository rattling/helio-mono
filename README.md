# Helionyx

Personal decision and execution substrate built on an append-only event log foundation.

## Project Status

**Current Milestone**: Milestone 0 - Architecture Baseline  
**Status**: In Progress

## Quick Start

```bash
# 1. Clone and enter the repository
git clone git@github.com:rattling/helio-mono.git
cd helio-mono

# 2. Set up environment
make setup

# 3. Edit .env with your API keys
# (copy .env.example to .env and fill in values)

# 4. Install dependencies
make install

# 5. Run tests (once implemented)
make test
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
# Run linters
make lint

# Format code
make format

# Run tests
make test

# Clean generated files
make clean
```

## Documentation

- **Project Charter**: [docs/PROJECT_CHARTER.md](docs/PROJECT_CHARTER.md)
- **Architecture Decision**: [docs/ARCHITECTURE_DECISION_M0.md](docs/ARCHITECTURE_DECISION_M0.md)
- **Engineering Constitution**: [.github/ENGINEERING_CONSTITUTION.md](.github/ENGINEERING_CONSTITUTION.md)
- **Workflow**: [.github/WORKFLOW.md](.github/WORKFLOW.md)

## Milestones

- **Milestone 0** (Current): Architecture Baseline
- **Milestone 1** (Planned): Core functionality with Telegram integration

## Contributing

This is a personal project following structured agent-driven development.  
See [.github/WORKFLOW.md](.github/WORKFLOW.md) for execution guidelines.

## License

Private repository - All rights reserved.
