# ADR: SQLite Persistence Layer Design and Schema

**Status**: Proposed  
**Date**: February 10, 2026  
**Issue**: #11  
**Milestone**: M1

## Context

Milestone 0 established in-memory projections in the query service as a temporary solution. Milestone 1 requires durable persistence to survive service restarts and enable more sophisticated querying capabilities.

### Requirements
- Replace in-memory dictionaries with SQLite-backed storage
- Maintain event log as source of truth (projections remain derivable)
- Support efficient queries with filtering, sorting, and search
- Enable projection rebuild from event log
- Accommodate future object types without major schema changes
- Single-user system (no multi-tenancy for M1)

### Constraints
- Event log remains immutable source of truth
- Projections must be losslessly rebuildable from events
- Must maintain existing query service API contract
- Single database file approach for simplicity
- Zero external dependencies (SQLite embedded)

---

## Decision

### 1. Database Organization

**Approach**: Single SQLite database file with multiple tables.

**Location**: `./data/projections/helionyx.db`

**Rationale**: 
- Single file simplifies backup and recovery
- Allows cross-table queries if needed later
- Atomic transactions across all projection types
- Standard pattern for embedded database usage

**Alternative Considered**: Separate DB per projection type
- **Rejected**: Adds complexity without clear benefit for single-user system

---

### 2. Schema Design

#### Todos Table

```sql
CREATE TABLE todos (
    object_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL CHECK(status IN ('pending', 'in_progress', 'completed', 'cancelled')),
    priority TEXT NOT NULL CHECK(priority IN ('low', 'medium', 'high', 'urgent')),
    due_date TEXT,  -- ISO8601 timestamp
    created_at TEXT NOT NULL,  -- ISO8601 timestamp
    completed_at TEXT,  -- ISO8601 timestamp
    tags TEXT,  -- JSON array: ["tag1", "tag2"]
    source_event_id TEXT NOT NULL,
    last_updated_at TEXT NOT NULL  -- ISO8601 timestamp
);

-- Indexes for common query patterns
CREATE INDEX idx_todos_status ON todos(status);
CREATE INDEX idx_todos_priority ON todos(priority);
CREATE INDEX idx_todos_due_date ON todos(due_date) WHERE due_date IS NOT NULL;
CREATE INDEX idx_todos_created_at ON todos(created_at);
CREATE INDEX idx_todos_status_priority ON todos(status, priority);
```

**Design Notes**:
- Text for timestamps (ISO8601 format) - SQLite datetime functions compatible
- JSON array as TEXT for tags - simple, sufficient for M1
- Composite index on (status, priority) for common query pattern
- Partial index on due_date (only non-null) for reminder queries

#### Notes Table

```sql
CREATE TABLE notes (
    object_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,  -- ISO8601 timestamp
    tags TEXT,  -- JSON array
    source_event_id TEXT NOT NULL,
    last_updated_at TEXT NOT NULL  -- ISO8601 timestamp
);

CREATE INDEX idx_notes_created_at ON notes(created_at);
-- Future: CREATE VIRTUAL TABLE notes_fts USING fts5(title, content);
```

**Design Notes**:
- Full-text search deferred to M2+ (use simple LIKE queries for M1)
- Content stored as TEXT (sufficient for conversational notes)

#### Tracks Table

```sql
CREATE TABLE tracks (
    object_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL CHECK(status IN ('active', 'paused', 'completed')),
    created_at TEXT NOT NULL,  -- ISO8601 timestamp
    last_updated TEXT,  -- ISO8601 timestamp
    tags TEXT,  -- JSON array
    source_event_id TEXT NOT NULL,
    check_in_frequency TEXT,  -- "daily", "weekly", etc.
    projection_updated_at TEXT NOT NULL  -- ISO8601 timestamp
);

CREATE INDEX idx_tracks_status ON tracks(status);
CREATE INDEX idx_tracks_created_at ON tracks(created_at);
```

#### Projection Metadata Table

```sql
CREATE TABLE projection_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL  -- ISO8601 timestamp
);

-- Initial records:
-- ('schema_version', '1', timestamp)
-- ('last_rebuild_timestamp', timestamp, timestamp)
-- ('last_event_id_processed', event_id, timestamp)
```

**Purpose**: 
- Track schema version for future migrations
- Record last successful rebuild timestamp
- Track incremental update position in event log
- Extensible key-value store for projection system metadata

---

### 3. Migration Strategy

**M1 Approach**: Manual schema creation in code.

**Schema Initialization**:
```python
# services/query/schema.sql
# Contains CREATE TABLE and CREATE INDEX statements

# services/query/database.py
def initialize_database(db_path: Path) -> None:
    """Initialize database with schema if it doesn't exist."""
    if not db_path.exists():
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(db_path)
        
        # Read and execute schema
        schema_path = Path(__file__).parent / "schema.sql"
        with open(schema_path) as f:
            conn.executescript(f.read())
        
        # Set initial metadata
        conn.execute(
            "INSERT INTO projection_metadata (key, value, updated_at) VALUES (?, ?, ?)",
            ("schema_version", "1", datetime.utcnow().isoformat())
        )
        conn.commit()
        conn.close()
```

**Future Evolution (M2+)**: Add Alembic for migrations if schema changes become frequent.

**Rationale**: 
- M1 schema is initial baseline - no migration needed
- Simple approach reduces dependencies
- Easy to bootstrap new environments
- Can add migration tooling when complexity warrants

---

### 4. Projection Rebuild Algorithm

**Full Rebuild Process**:

```python
async def rebuild_projections(self) -> None:
    """Rebuild all projections from event log."""
    
    # 1. Clear all projection tables
    self.conn.execute("DELETE FROM todos")
    self.conn.execute("DELETE FROM notes")
    self.conn.execute("DELETE FROM tracks")
    
    # 2. Stream all ObjectExtractedEvent from event log
    events = await self.event_store.stream_events(
        event_types=[EventType.OBJECT_EXTRACTED]
    )
    
    # 3. Apply each event to appropriate table
    for event in events:
        await self._apply_extraction_event(event)
    
    # 4. Update metadata
    now = datetime.utcnow().isoformat()
    self.conn.execute(
        "INSERT OR REPLACE INTO projection_metadata (key, value, updated_at) "
        "VALUES (?, ?, ?)",
        ("last_rebuild_timestamp", now, now)
    )
    
    if events:
        last_event_id = str(events[-1].event_id)
        self.conn.execute(
            "INSERT OR REPLACE INTO projection_metadata (key, value, updated_at) "
            "VALUES (?, ?, ?)",
            ("last_event_id_processed", last_event_id, now)
        )
    
    # 5. Commit transaction
    self.conn.commit()
```

**Incremental Update Process** (optimization):

```python
async def update_from_new_events(self) -> None:
    """Apply new events since last update."""
    
    # Get last processed event ID
    cursor = self.conn.execute(
        "SELECT value FROM projection_metadata WHERE key = ?",
        ("last_event_id_processed",)
    )
    row = cursor.fetchone()
    last_event_id = UUID(row[0]) if row else None
    
    # Stream events since last processed
    events = await self.event_store.stream_events(
        event_types=[EventType.OBJECT_EXTRACTED]
    )
    
    # Filter to events after last processed
    if last_event_id:
        events = [e for e in events if e.event_id > last_event_id]
    
    if not events:
        return
    
    # Apply new events
    for event in events:
        await self._apply_extraction_event(event)
    
    # Update metadata
    now = datetime.utcnow().isoformat()
    self.conn.execute(
        "INSERT OR REPLACE INTO projection_metadata (key, value, updated_at) "
        "VALUES (?, ?, ?)",
        ("last_event_id_processed", str(events[-1].event_id), now)
    )
    self.conn.commit()
```

**Rationale**:
- Full rebuild ensures projection consistency with event log
- Incremental update optimizes for running system
- Metadata tracking enables resume after interruption

---

### 5. Query Implementation Patterns

**Basic Query with Filters**:
```python
async def get_todos(
    self,
    status: Optional[str] = None,
    tags: Optional[list[str]] = None,
) -> list[dict]:
    """Query todos with filters."""
    
    query = "SELECT * FROM todos WHERE 1=1"
    params = []
    
    if status:
        query += " AND status = ?"
        params.append(status)
    
    if tags:
        # Simple substring match in JSON array (sufficient for M1)
        for tag in tags:
            query += " AND tags LIKE ?"
            params.append(f'%"{tag}"%')
    
    query += " ORDER BY created_at DESC"
    
    cursor = self.conn.execute(query, params)
    rows = cursor.fetchall()
    
    return [dict(row) for row in rows]
```

**Text Search (Simple)**:
```python
async def get_notes(
    self,
    tags: Optional[list[str]] = None,
    search: Optional[str] = None,
) -> list[dict]:
    """Query notes with text search."""
    
    query = "SELECT * FROM notes WHERE 1=1"
    params = []
    
    if search:
        query += " AND (title LIKE ? OR content LIKE ?)"
        search_pattern = f"%{search}%"
        params.extend([search_pattern, search_pattern])
    
    if tags:
        for tag in tags:
            query += " AND tags LIKE ?"
            params.append(f'%"{tag}"%')
    
    query += " ORDER BY created_at DESC"
    
    cursor = self.conn.execute(query, params)
    rows = cursor.fetchall()
    
    return [dict(row) for row in rows]
```

**Stats Query**:
```python
def get_stats(self) -> dict:
    """Get projection statistics."""
    
    cursor = self.conn.execute(
        "SELECT 'todos', COUNT(*) FROM todos "
        "UNION ALL SELECT 'notes', COUNT(*) FROM notes "
        "UNION ALL SELECT 'tracks', COUNT(*) FROM tracks"
    )
    
    stats = dict(cursor.fetchall())
    stats["total_objects"] = sum(stats.values())
    
    # Get last rebuild time
    cursor = self.conn.execute(
        "SELECT value FROM projection_metadata WHERE key = ?",
        ("last_rebuild_timestamp",)
    )
    row = cursor.fetchone()
    if row:
        stats["last_rebuild"] = row[0]
    
    return stats
```

**Design Notes**:
- Parameterized queries prevent SQL injection
- Simple LIKE queries sufficient for M1 text search
- JSON tag matching via substring (upgrade to JSON functions if needed)
- Read-only transactions for queries (default in sqlite3)

---

### 6. Connection Management

**Approach**: Single persistent connection per service instance.

```python
class QueryService:
    def __init__(self, event_store: FileEventStore, db_path: Path):
        self.event_store = event_store
        self.db_path = db_path
        
        # Initialize database if needed
        initialize_database(db_path)
        
        # Open persistent connection
        self.conn = sqlite3.connect(
            db_path,
            check_same_thread=False  # Allow async usage
        )
        self.conn.row_factory = sqlite3.Row  # Dict-like rows
        
        # Enable foreign keys
        self.conn.execute("PRAGMA foreign_keys = ON")
        
        # Set WAL mode for better concurrency
        self.conn.execute("PRAGMA journal_mode = WAL")
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
```

**Rationale**:
- Single connection sufficient for single-user system
- WAL mode enables concurrent reads during writes
- Row factory provides dict-like access

---

### 7. Backup and Recovery Strategy

**Backup Approach**:
```python
def backup_projections(db_path: Path, backup_dir: Path) -> Path:
    """Create timestamped backup of projection database."""
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"helionyx_{timestamp}.db"
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # SQLite backup API
    source = sqlite3.connect(db_path)
    dest = sqlite3.connect(backup_path)
    source.backup(dest)
    source.close()
    dest.close()
    
    return backup_path
```

**Recovery Approach**:
```bash
# Option 1: Restore from backup
cp data/backups/helionyx_20260210_120000.db data/projections/helionyx.db

# Option 2: Rebuild from event log
make rebuild
```

**Scheduled Backups** (future):
- Daily backup before rebuild
- Retain last 7 days
- Backup events and projections together

**Rationale**:
- Projections are always recoverable from event log
- Backups reduce recovery time
- Event log backup is primary concern

---

### 8. Schema Versioning

**Version Tracking**:
```python
def get_schema_version(conn: sqlite3.Connection) -> int:
    """Get current schema version."""
    cursor = conn.execute(
        "SELECT value FROM projection_metadata WHERE key = ?",
        ("schema_version",)
    )
    row = cursor.fetchone()
    return int(row[0]) if row else 0

def check_schema_version(conn: sqlite3.Connection) -> None:
    """Verify schema version matches expected."""
    current = get_schema_version(conn)
    expected = 1  # M1 schema version
    
    if current != expected:
        raise ValueError(
            f"Schema version mismatch: expected {expected}, got {current}. "
            f"Run 'make rebuild' or migrate schema."
        )
```

**Migration Path** (M2+):
- Add schema_migrations table
- Implement Alembic or custom migration system
- Track applied migrations
- Support forward-only migrations

---

### 9. Error Handling

**Database Errors**:

| Error Type | Strategy | Impact |
|------------|----------|--------|
| DB locked | Retry with backoff (max 3 attempts, 100ms delay) | Query delay |
| Disk full | Log error, raise exception | System halt |
| Corruption | Log error, attempt rebuild from events | Service restart |
| Missing DB | Auto-create from schema | Transparent |
| Schema mismatch | Fail with clear message | Manual repair |

**Implementation**:
```python
class DatabaseError(Exception):
    """Database operation failed."""
    pass

async def execute_with_retry(
    conn: sqlite3.Connection,
    query: str,
    params: tuple,
    max_retries: int = 3
) -> Any:
    """Execute query with retry on lock."""
    
    for attempt in range(max_retries):
        try:
            return conn.execute(query, params)
        except sqlite3.OperationalError as e:
            if "locked" in str(e) and attempt < max_retries - 1:
                await asyncio.sleep(0.1 * (2 ** attempt))
            else:
                raise DatabaseError(f"Database operation failed: {e}") from e
```

---

### 10. Configuration

**Environment Variables**:
```bash
PROJECTIONS_DB_PATH=./data/projections/helionyx.db
PROJECTIONS_BACKUP_DIR=./data/backups
PROJECTIONS_AUTO_REBUILD=false
PROJECTIONS_BACKUP_RETENTION_DAYS=7
```

**Defaults**:
- Database in `data/projections/` (relative to repo root)
- Backups in `data/backups/`
- Manual rebuild required (not automatic)

---

### 11. Testing Strategy

**Unit Tests**:
```python
@pytest.fixture
def temp_db():
    """Temporary SQLite database for tests."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    
    yield db_path
    
    db_path.unlink()

async def test_projection_rebuild(temp_db, sample_events):
    """Test projection rebuild from events."""
    event_store = MockEventStore(sample_events)
    query_service = QueryService(event_store, temp_db)
    
    await query_service.rebuild_projections()
    
    todos = await query_service.get_todos()
    assert len(todos) == 2
```

**Integration Tests**:
- Test with real SQLite database (temp file)
- Verify query correctness
- Test projection rebuild
- Test error scenarios

**In-Memory Testing**:
```python
# Use :memory: for fast tests
conn = sqlite3.connect(":memory:")
```

---

## Consequences

### Positive
- ✅ Durable persistence survives service restarts
- ✅ Efficient querying with indexes
- ✅ Zero external dependencies (SQLite embedded)
- ✅ Simple backup and recovery
- ✅ Schema version tracking enables future migrations

### Negative
- ⚠️ More complex than in-memory (but necessary)
- ⚠️ File I/O adds latency (but negligible for single-user)
- ⚠️ SQLite concurrency limits (but sufficient for M1)

### Risks
- **Schema Evolution**: Future changes require migration strategy
  - Mitigation: Version tracking, rebuild capability
- **Disk Space**: Large conversation imports may grow database
  - Mitigation: Monitor size, document cleanup procedures
- **Corruption**: Rare but possible
  - Mitigation: Regular backups, rebuild from events

---

## Implementation Checklist

- [ ] Create `services/query/schema.sql` with full schema
- [ ] Create `services/query/database.py` with connection utilities
- [ ] Refactor `services/query/service.py` to use SQLite
- [ ] Add projection rebuild functionality
- [ ] Add incremental update functionality
- [ ] Create `scripts/rebuild_projections.py` CLI tool
- [ ] Update `Makefile` with `make rebuild` target
- [ ] Add database initialization on startup
- [ ] Implement error handling and retries
- [ ] Add backup utilities
- [ ] Create tests for all query patterns
- [ ] Update `.env.example` with DB configuration
- [ ] Document backup/recovery procedures

---

## Related Issues

- **Blocks**: #14 (Implement SQLite Query Service Persistence)
- **Related**: #9 (Milestone 1 Meta-Issue)

---

## Approval

- [ ] Architect reviewed
- [ ] Schema validated
- [ ] Query patterns verified
- [ ] Ready for developer implementation

