# Architectural Decision: Helionyx Service Boundaries (Milestone 0)

## Context

Helionyx is a personal decision and execution substrate built on an append-only event log foundation. It must:
- Record all artifacts (messages, LLM interactions, extracted objects, decisions)
- Extract structured objects from conversations using LLMs
- Support queries and push notifications
- Handle multiple input sources (ChatGPT dumps, Telegram)
- Enable parallel agent development
- Remain pragmatic and modifiable

## Service Architecture

### Core Services

#### 1. Event Store Service
**Responsibility**: Foundational append-only event persistence

- Append events to immutable log
- Retrieve events by ID, time range, type
- Stream events for processing
- **Technology**: File-based append-only log (JSONL format)
- **Rationale**: Simple, reliable, inspectable, no external dependencies

**Key Design Decisions**:
- Events are immutable once written
- Each event has: ID, timestamp, type, payload, metadata
- File-based for M0/M1 (sufficient for single user, can migrate later)

---

#### 2. Ingestion Service
**Responsibility**: Accept and normalize inputs from various sources

- Accept raw messages from ChatGPT dumps, Telegram, CLI
- Normalize to standard message format
- Record raw input as artifact
- Write ingestion events to event store
- **Technology**: Python service with multiple adapters

**Key Design Decisions**:
- Source-agnostic core with pluggable adapters
- All raw inputs preserved as artifacts
- Synchronous for M0 (async can be added later)

---

#### 3. Extraction Service
**Responsibility**: Extract structured objects from messages using LLMs

- Consume message events from event store
- Use LLM to identify and extract: Todo, Note, Track
- Record LLM prompts and responses as artifacts
- Write extracted objects as events
- **Technology**: Python service with LLM client (OpenAI API)

**Key Design Decisions**:
- Stateless extraction logic (state in event store)
- Prompt engineering for object extraction
- Each extraction creates artifact events
- Can be triggered on-demand or via event stream

---

#### 4. Query Service
**Responsibility**: Provide read models and projections

- Build projections from event log (todos, notes, tracks)
- Provide query API for current state
- Support filtering, search, time ranges
- Trigger push notifications based on rules
- **Technology**: Python service with SQLite for projections

**Key Design Decisions**:
- Projections are derived, can be rebuilt
- Event store is source of truth
- SQLite for pragmatic queryability
- Rebuild projections from event log if needed

---

#### 5. Interface Adapters
**Responsibility**: External interface implementations

- Telegram bot adapter
- HTTP API adapter
- CLI adapter (for development)
- **Technology**: Python adapters calling core services

**Key Design Decisions**:
- Adapters are thin translation layers
- Core logic stays in services
- Minimal for M0 (CLI and basic API)

---

## Service Interaction Patterns

### Synchronous Flow (M0)
```
Input → Ingestion → Event Store → Extraction → Event Store → Query
```

For M0, services can call each other directly. M1+ may introduce async messaging.

### Data Ownership
- **Event Store**: Owns all events (immutable)
- **Extraction Service**: Owns extraction logic and LLM interactions
- **Query Service**: Owns derived projections
- No shared databases between services

---

## Technology Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Language | Python 3.11+ | Project default, good ecosystem |
| API Framework | FastAPI | Lightweight, modern, async support |
| Event Storage | File-based JSONL | Simple, inspectable, sufficient for single-user |
| Projections DB | SQLite | Embedded, reliable, zero-config |
| Schema Validation | Pydantic | Type-safe, validation, serialization |
| LLM Client | OpenAI Python SDK | Primary LLM provider for M1 |
| Testing | pytest | Standard Python testing |

---

## Configuration Management

- Environment variables for secrets (API keys)
- Config files for service settings
- `.env` file for local development
- No hardcoded secrets in repo

---

## Architectural Principles Applied

✅ **Service boundaries enable parallel work**: Each service has clear responsibility
✅ **Contract-first**: Services interact through defined schemas
✅ **Pragmatic structure**: Simple for now, can evolve
✅ **Runnable and testable**: Each service can run independently
✅ **Event sourcing-lite**: Append-only log without full CQRS complexity
✅ **Clean enough**: Core logic separated from adapters, but not over-engineered

---

## Future Evolution (M1+)

Potential changes as system grows:
- Async messaging between services (e.g., message queue)
- Event store migration to dedicated database
- Service deployment separation
- Caching layer for queries
- Multi-user support with auth

These are **not** commitments, just awareness of possible directions.

---

## Non-Decisions (Deferred)

- Exact API specifications (issue #7)
- Database schemas (implementation detail)
- Deployment strategy (beyond local dev)
- CI/CD pipeline

---

## Acceptance

This architecture satisfies Milestone 0 requirements:
- ✅ Service boundaries identified
- ✅ Interaction patterns defined
- ✅ Data ownership clear
- ✅ Technology stack decided
- ✅ Enables parallel agent work
- ✅ Pragmatic and modifiable
