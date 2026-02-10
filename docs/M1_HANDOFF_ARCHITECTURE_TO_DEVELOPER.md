# Milestone 1 - Architectural Phase Handoff

**Date**: February 10, 2026  
**From**: Architect Agent  
**To**: Developer Agent  
**Status**: Phase 1 Complete - Ready for Implementation

---

## Executive Summary

All **three architectural issues** for Milestone 1 have been completed. The architectural foundation is now in place for implementing:
- LLM-based extraction using OpenAI API
- Durable SQLite persistence for projections
- Telegram bot interface with notifications

**All implementation issues (#13, #14, #15) are unblocked and ready to begin.**

---

## What Was Delivered

### 1. Architecture Decision Records (ADRs)

Three comprehensive ADRs created in `docs/`:

| ADR | Issue | Purpose | Status |
|-----|-------|---------|--------|
| `ADR_M1_LLM_INTEGRATION.md` | #10 | LLM integration architecture | ✅ Complete |
| `ADR_M1_SQLITE_PERSISTENCE.md` | #11 | Database schema and patterns | ✅ Complete |
| `ADR_M1_TELEGRAM_ARCHITECTURE.md` | #12 | Bot architecture and flows | ✅ Complete |

Each ADR includes:
- ✅ Context and requirements
- ✅ Key architectural decisions
- ✅ Implementation patterns and code examples
- ✅ Configuration requirements
- ✅ Testing strategy
- ✅ **Implementation checklist** (use this as your guide)

### 2. Contract Extensions

**New Protocols** (`shared/contracts/protocols.py`):
```python
class LLMServiceProtocol(ABC):
    async def extract_objects(message: str, context=None) -> ExtractionResult
```

**New Dataclasses** (`shared/contracts/objects.py`):
```python
@dataclass
class ExtractionResult:
    objects: list[dict]
    confidence: Optional[float]
    model_used: str
    tokens_used: int
    prompt_artifact_id: UUID
    response_artifact_id: UUID
    extraction_metadata: dict
```

**New Exceptions**:
```python
class LLMServiceError(Exception)
```

### 3. Database Schema

Complete SQL schema created: `services/query/schema.sql`

**Tables**:
- `todos` - Todo items with status, priority, due dates
- `notes` - Notes with content
- `tracks` - Tracking items
- `projection_metadata` - System metadata (schema version, rebuild info)
- `notification_log` - Notification tracking (for Issue #16)

**Indexes**: Optimized for common query patterns (see schema comments)

### 4. Configuration

Updated `.env.example` with all M1 variables:
- OpenAI configuration (API key, model, rate limits, cost controls)
- Telegram configuration (bot token, chat ID, notification settings)
- SQLite configuration (database paths, backup settings)

### 5. Documentation Updates

Updated `docs/ARCHITECTURE.md`:
- Enhanced Extraction Service section (LLM integration)
- Enhanced Query Service section (SQLite persistence)
- Enhanced Interface Adapters section (Telegram bot)
- References to ADRs for detailed design

---

## Implementation Roadmap

### Phase 2: Core Implementation (Parallel Work)

You can work on these **in any order** or in parallel:

#### Issue #15: OpenAI Extraction Service
**Complexity**: M (Moderate)  
**Reference**: `docs/ADR_M1_LLM_INTEGRATION.md`

**Files to Create**:
```
services/extraction/
    prompts.py          # Prompt templates (section 4 of ADR)
    llm_client.py       # LLM abstraction
    openai_client.py    # OpenAI implementation (section 5)
    mock_llm.py         # Test mock (section 9)
```

**Files to Modify**:
```
services/extraction/service.py  # Refactor to use LLM client
```

**Key Implementation Points**:
- Use `LLMServiceProtocol` contract
- Record prompt and response as `ArtifactRecordedEvent` before/after API call
- Implement retry logic with exponential backoff (section 5)
- Add rate limiting via token bucket (section 6)
- Calculate and log costs (section 7)
- See full error handling matrix in ADR section 5

**Testing**:
- Unit tests with `MockLLMService`
- Integration tests with real API (gated by env var)
- Cost tracking verification

---

#### Issue #14: SQLite Query Service Persistence
**Complexity**: M (Moderate)  
**Reference**: `docs/ADR_M1_SQLITE_PERSISTENCE.md`

**Files to Create**:
```
services/query/
    database.py         # Connection utilities (section 6)
scripts/
    rebuild_projections.py  # CLI rebuild tool
```

**Files to Modify**:
```
services/query/service.py   # Replace in-memory with SQLite
```

**Schema Already Created**: `services/query/schema.sql`

**Key Implementation Points**:
- Initialize database on startup (section 2)
- Implement `rebuild_projections()` (section 4)
- Implement `update_from_new_events()` for incremental updates (section 4)
- Use parameterized queries (section 5)
- Add connection with WAL mode (section 6)
- Handle database lock errors with retry (section 9)

**Testing**:
- Unit tests with `:memory:` SQLite
- Integration tests with temp DB files
- Test projection rebuild from known event sequence

---

#### Issue #13: Telegram Bot Commands and Handlers
**Complexity**: M (Standard)  
**Reference**: `docs/ADR_M1_TELEGRAM_ARCHITECTURE.md`

**Dependencies**: Install `python-telegram-bot==21.0+`

**Files to Create**:
```
services/adapters/telegram/
    __init__.py
    bot.py              # Main bot setup (section 10)
    handlers.py         # Command handlers (section 5)
    message_handler.py  # Non-command processing (section 6)
    formatters.py       # Message formatting (section 8)
scripts/
    run_telegram_bot.py # Entry point
```

**Key Implementation Points**:
- Implement command handlers: /start, /help, /todos, /notes, /tracks, /stats (section 5)
- Implement message handler for ingestion (section 6)
- Create formatters for todos, notes, tracks (section 8)
- Add error handler (section 9)
- Set up bot application with polling (section 10)

**Configuration**:
- User must create bot via @BotFather
- User must get chat ID (logged on /start)

**Testing**:
- Unit tests with mocked Telegram API
- Manual testing with real bot

---

### Phase 3: Features (After Core)

#### Issue #16: Reminder and Notification Scheduling
**Complexity**: M  
**Blocked by**: #13 (Telegram), #14 (SQLite)

**Files to Create**:
```
services/adapters/telegram/
    scheduler.py        # Background notification scheduler
    notifications.py    # Notification formatters
```

**Reference**: `docs/ADR_M1_TELEGRAM_ARCHITECTURE.md` section 7

---

#### Issue #17: Test Infrastructure
**Complexity**: M  
**Can start during Phase 2**

**Focus**:
- pytest configuration
- Common fixtures (temp event store, temp DB, mock LLM)
- Tests for critical paths

---

#### Issue #18: ChatGPT Import
**Complexity**: M  
**Blocked by**: #15 (needs extraction working)

**Implementation**:
- Parse ChatGPT JSON export format
- Import messages via ingestion service
- Trigger extraction
- Idempotency (track imported conversation IDs)

---

## Critical Implementation Notes

### 1. Artifact Recording Pattern

**Every LLM call must record artifacts**:

```python
# Before API call
prompt_event = ArtifactRecordedEvent(
    artifact_type=ArtifactType.LLM_PROMPT,
    content=full_prompt,
    related_event_id=message_event_id,
    metadata={"model": "gpt-4o-mini", ...}
)
prompt_id = await event_store.append(prompt_event)

# Call OpenAI
response = await openai_client.call(...)

# After API call
response_event = ArtifactRecordedEvent(
    artifact_type=ArtifactType.LLM_RESPONSE,
    content=response.text,
    related_event_id=prompt_id,
    metadata={
        "tokens_used": response.usage.total_tokens,
        "cost_usd": calculate_cost(response),
        ...
    }
)
response_id = await event_store.append(response_event)
```

**This is a system invariant - do not skip.**

### 2. Projection Rebuild

Query service must support full rebuild:

```python
async def rebuild_projections():
    # 1. Clear tables
    conn.execute("DELETE FROM todos")
    # ...
    
    # 2. Stream all ObjectExtractedEvent
    events = await event_store.stream_events(
        event_types=[EventType.OBJECT_EXTRACTED]
    )
    
    # 3. Apply each event
    for event in events:
        await _apply_extraction_event(event)
    
    # 4. Update metadata
    # 5. Commit
```

### 3. Error Handling

All services must handle errors gracefully:
- Network errors: Retry with backoff
- Rate limits: Respect retry-after headers
- API errors: Log and return empty/error result
- User-facing errors: Clear, actionable messages

### 4. Configuration

Services must load configuration from environment:
```python
import os
from pathlib import Path

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not set")
```

See `.env.example` for all variables.

---

## Testing Requirements

### Unit Tests (Required)
- Use mocks for external services (OpenAI, Telegram, database)
- Test error paths explicitly
- Focus on business logic

### Integration Tests (Required)
- Real SQLite database (temp files)
- Real OpenAI API (gated by env var)
- End-to-end flow: message → extraction → query

### Manual Tests (Required)
- Real Telegram bot interaction
- Real ChatGPT import
- Notification timing verification

---

## Makefile Targets to Add

```makefile
# For Issue #13
telegram: ## Run Telegram bot
	python scripts/run_telegram_bot.py

# For Issue #14
rebuild: ## Rebuild projections from event log
	python scripts/rebuild_projections.py

# For Issue #17
test: ## Run tests
	pytest tests/ -v

test-cov: ## Run tests with coverage
	pytest tests/ --cov=services --cov=shared --cov-report=html
```

---

## Success Criteria

**You will know Phase 2 is complete when**:

- [ ] LLM extraction produces real todos, notes, tracks (not keyword-based)
- [ ] All LLM prompts and responses visible in event log
- [ ] Query service survives restart with data intact
- [ ] Can query todos via `/todos` command on Telegram
- [ ] Non-command messages get acknowledged and extracted
- [ ] System runs end-to-end without errors
- [ ] Tests pass for critical paths

---

## Next Steps

1. **Review** all three ADRs to understand architectural decisions
2. **Choose** an issue to start with (#13, #14, or #15)
3. **Follow** the implementation checklist in the relevant ADR
4. **Test** as you go (don't defer testing to the end)
5. **Validate** with manual testing before marking complete
6. **Document** any deviations from architecture (and escalate if major)

---

## Questions or Issues?

- **Unclear architecture?** Re-read relevant ADR section
- **Implementation question?** Check ADR code examples
- **Can't decide approach?** Use the recommended approach in ADR
- **Architecture doesn't fit?** Escalate with blocker template

---

## Final Note

The architecture is **pragmatic**, not **perfect**. 

It's designed to:
- Get M1 working quickly
- Maintain key invariants (append-only log, artifact recording)
- Enable future evolution without rewrites

Follow the patterns established in the ADRs, but don't over-engineer. Clean enough is sufficient.

**Good luck with implementation! 🚀**

---

**Handoff Status**: ✅ Complete  
**Developer Phase**: Ready to begin  
**Next Review**: After Phase 2 implementation complete

