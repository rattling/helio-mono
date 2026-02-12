# Shared Contracts

This package contains the **explicit contracts** between Helionyx services.

## Purpose

Contracts enable services to operate independently and support parallel agent development. Services interact **only** through these contracts, never by reading each other's internal code.

## Contract Types

### Events (`events.py`)
Event schemas for the append-only event log. All system activity is recorded as events.

**Key Events:**
- `MessageIngestedEvent` - Raw input from any source
- `ArtifactRecordedEvent` - LLM prompts, responses, summaries
- `ObjectExtractedEvent` - Structured objects extracted from messages
- `DecisionRecordedEvent` - Decision records (future milestone)
- `AttentionScoringComputedEvent` - Attention queue scoring snapshots (M6)
- `SuggestionShown/Applied/Rejected/EditedEvent` - Planning suggestion lifecycle (M6)
- `ReminderSent/Dismissed/SnoozedEvent` - Reminder lifecycle feedback (M6)
- `FeatureSnapshotRecordedEvent` - Deterministic feature snapshots for replay (M6)
- `ModelScoreRecordedEvent` - Shadow-model outputs for audit/eval (M6)

### Objects (`objects.py`)
Schemas for structured objects extracted from conversations.

**Object Types:**
- `Todo` - Actionable items
- `Note` - Information worth retaining
- `Track` - Items to monitor over time

### Protocols (`protocols.py`)
Abstract interfaces defining service operations.

**Service Protocols:**
- `EventStoreProtocol` - Event persistence operations
- `ExtractionServiceProtocol` - Object extraction operations
- `QueryServiceProtocol` - Query and projection operations

## Contract Principles

### 1. Explicit and Typed
All contracts use Pydantic models for:
- Type safety
- Validation
- Serialization
- Documentation

### 2. Versioned
Contract changes follow semantic versioning:
- Backwards-compatible additions: patch/minor version
- Breaking changes: major version
- Version included in event metadata

Milestone 6 additions are backward-compatible:
- New event types are additive and optional for consumers
- Existing event fields and task contracts are unchanged
- Consumers not aware of M6 events can safely ignore them

### 3. Immutable Events
Events are immutable once written. Corrections occur via new events.

### 4. Service Independence
Services depend on contracts, not on other services' implementation details.

## Making Contract Changes

### Non-Breaking Changes (Allowed)
- Adding optional fields
- Adding new event types
- Adding new object types
- Expanding enums

### Breaking Changes (Requires Coordination)
- Removing fields
- Changing field types
- Renaming fields
- Changing validation rules

**Process:**
1. Propose change in issue or PR
2. Identify affected services
3. Document in ADR if non-trivial
4. Update all affected services in same PR
5. Increment version

## Usage

```python
from shared.contracts import (
    MessageIngestedEvent,
    Todo,
    EventStoreProtocol,
)

# Create an event
event = MessageIngestedEvent(
    source=SourceType.TELEGRAM,
    source_id="12345",
    content="Remember to review the quarterly reports",
)

# Create an object
todo = Todo(
    title="Review quarterly reports",
    priority=TodoPriority.HIGH,
)

# Implement a protocol
class FileEventStore(EventStoreProtocol):
    async def append(self, event: BaseEvent) -> UUID:
        # Implementation here
        pass
```

## Testing Contracts

Contracts should have:
- Schema validation tests
- Serialization/deserialization tests
- Protocol compliance tests (for implementations)

## Future Evolution

- GraphQL schemas (if needed)
- gRPC definitions (if services become distributed)
- OpenAPI specs (for HTTP APIs)
- Event catalog documentation

Current approach is sufficient for M0 and M1.
