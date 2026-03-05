# Process Architecture: Message → Extraction → Query

**Status**: Active runtime flow  
**Primary scope**: ingestion, extraction, projections, queryability

## Purpose

Describe the canonical Helionyx pipeline from incoming message to durable,
queryable object state.

## Invariants

1. Event log is append-only source of truth.
2. Derived projections are rebuildable from event history.
3. Adapters contain no domain logic.
4. LLM prompts/responses are recorded as durable artifacts.

## Core Services in this Process

- **Ingestion Service**: normalize input and emit `MESSAGE_INGESTED`.
- **Extraction Service**: create structured objects and artifact events.
- **Query Service**: build/update SQLite projections from events.

## Canonical Flow

```mermaid
sequenceDiagram
    participant User
    participant Telegram
    participant Ingestion
    participant EventStore
    participant Extraction
    participant OpenAI
    participant Query

    User->>Telegram: "Remind me to review reports"
    Telegram->>Ingestion: forward_message()

    Ingestion->>EventStore: append(MessageIngestedEvent)
    EventStore-->>Ingestion: event_id

    Ingestion->>Extraction: trigger_extraction(event_id)
    Extraction->>EventStore: get_by_id(event_id)
    EventStore-->>Extraction: MessageIngestedEvent

    Extraction->>OpenAI: extract_objects(message)
    Extraction->>EventStore: append(ArtifactRecordedEvent [prompt])

    OpenAI-->>Extraction: extracted_objects_json
    Extraction->>EventStore: append(ArtifactRecordedEvent [response])

    Extraction->>EventStore: append(ObjectExtractedEvent [todo])
    EventStore-->>Extraction: event_id

    Extraction-->>Ingestion: extraction_complete

    Note over Query: Asynchronously rebuilds projections
    Query->>EventStore: stream_events(since=last_processed)
    EventStore-->>Query: [new events]
    Query->>Query: update_projections()

    User->>Telegram: "What are my todos?"
    Telegram->>Query: get_todos()
    Query-->>Telegram: [todos list]
    Telegram-->>User: Display todos
```

## Data Flow

```mermaid
graph LR
    MSG[Raw Message] --> E1[MessageIngested\nEvent]
    E1 --> ES[(Event Store)]
    ES --> EXT[Extraction\nService]
    EXT --> LLM[OpenAI API]
    LLM --> ART[Artifact\nEvents]
    ART --> ES
    EXT --> E2[ObjectExtracted\nEvent]
    E2 --> ES
    ES --> PROJ[Query Service\nProjections]
    PROJ --> SQLITE[(SQLite)]
    SQLITE --> USER[User Queries]
```

## Lifecycle State Machines

### Todo

```mermaid
stateDiagram-v2
    [*] --> Pending: Create
    Pending --> InProgress: Start
    Pending --> Cancelled: Cancel
    InProgress --> Completed: Complete
    InProgress --> Cancelled: Cancel
    InProgress --> Pending: Pause
    Completed --> [*]
    Cancelled --> [*]
```

### Track

```mermaid
stateDiagram-v2
    [*] --> Active: Create
    Active --> Paused: Pause
    Active --> Completed: Complete
    Paused --> Active: Resume
    Paused --> Completed: Complete
    Completed --> [*]
```

## Event Families Used

- `MESSAGE_INGESTED`
- `ARTIFACT_RECORDED`
- `OBJECT_EXTRACTED`
- `DECISION_RECORDED` (task lifecycle and audit semantics)

See full schemas: `shared/contracts/events.py` and `shared/contracts/objects.py`.

## Related Docs

- `docs/ADR/ADR_M1_LLM_INTEGRATION.md`
- `docs/ADR/ADR_M1_SQLITE_PERSISTENCE.md`
- `docs/ADR/ADR_M1_TELEGRAM_ARCHITECTURE.md`
