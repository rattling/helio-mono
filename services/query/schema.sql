-- Helionyx Projection Database Schema
-- Version: 1
-- Date: February 10, 2026
-- Purpose: Durable storage for query service projections

-- =============================================================================
-- TODOS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS todos (
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
CREATE INDEX IF NOT EXISTS idx_todos_status ON todos(status);
CREATE INDEX IF NOT EXISTS idx_todos_priority ON todos(priority);
CREATE INDEX IF NOT EXISTS idx_todos_due_date ON todos(due_date) WHERE due_date IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_todos_created_at ON todos(created_at);
CREATE INDEX IF NOT EXISTS idx_todos_status_priority ON todos(status, priority);

-- =============================================================================
-- NOTES TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS notes (
    object_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,  -- ISO8601 timestamp
    tags TEXT,  -- JSON array
    source_event_id TEXT NOT NULL,
    last_updated_at TEXT NOT NULL  -- ISO8601 timestamp
);

CREATE INDEX IF NOT EXISTS idx_notes_created_at ON notes(created_at);
-- Future M2+: Full-text search via FTS5 virtual table

-- =============================================================================
-- TRACKS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS tracks (
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

CREATE INDEX IF NOT EXISTS idx_tracks_status ON tracks(status);
CREATE INDEX IF NOT EXISTS idx_tracks_created_at ON tracks(created_at);

-- =============================================================================
-- TASKS TABLE (Milestone 5)
-- =============================================================================

CREATE TABLE IF NOT EXISTS tasks (
    task_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    body TEXT,
    status TEXT NOT NULL CHECK(status IN ('open', 'blocked', 'in_progress', 'done', 'cancelled', 'snoozed')),
    priority TEXT NOT NULL CHECK(priority IN ('p0', 'p1', 'p2', 'p3')),
    due_at TEXT,
    do_not_start_before TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    completed_at TEXT,
    source TEXT NOT NULL,
    source_ref TEXT NOT NULL,
    dedup_group_id TEXT,
    labels TEXT,
    project TEXT,
    blocked_by TEXT,
    agent_notes TEXT,
    explanations TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_tasks_source_ref ON tasks(source, source_ref);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
CREATE INDEX IF NOT EXISTS idx_tasks_dedup_group_id ON tasks(dedup_group_id) WHERE dedup_group_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_tasks_due_at ON tasks(due_at) WHERE due_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_tasks_updated_at ON tasks(updated_at);

-- =============================================================================
-- PROJECTION METADATA TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS projection_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL  -- ISO8601 timestamp
);

-- =============================================================================
-- NOTIFICATION LOG TABLE (for Issue #16)
-- =============================================================================

CREATE TABLE IF NOT EXISTS notification_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    notification_type TEXT NOT NULL,  -- 'reminder', 'daily_summary', 'weekly_review'
    object_id TEXT,  -- Optional reference to todo/note/track
    sent_at TEXT NOT NULL,  -- ISO8601 timestamp
    metadata TEXT  -- JSON for additional context
);

CREATE INDEX IF NOT EXISTS idx_notification_log_type_date 
    ON notification_log(notification_type, sent_at);
CREATE INDEX IF NOT EXISTS idx_notification_log_object 
    ON notification_log(object_id) WHERE object_id IS NOT NULL;

-- =============================================================================
-- INITIAL METADATA
-- =============================================================================

-- Schema version tracking (required for migrations)
INSERT OR IGNORE INTO projection_metadata (key, value, updated_at) 
VALUES ('schema_version', '1', datetime('now'));

-- Placeholder for last rebuild timestamp (updated on rebuild)
INSERT OR IGNORE INTO projection_metadata (key, value, updated_at)
VALUES ('last_rebuild_timestamp', '', datetime('now'));

-- Placeholder for last processed event ID (updated incrementally)
INSERT OR IGNORE INTO projection_metadata (key, value, updated_at)
VALUES ('last_event_id_processed', '', datetime('now'));

-- =============================================================================
-- PRAGMAS (recommended settings)
-- =============================================================================

-- Enable foreign keys (if we add FK constraints in future)
PRAGMA foreign_keys = ON;

-- Use Write-Ahead Logging for better concurrency
-- (Applied in application code, not in schema)
-- PRAGMA journal_mode = WAL;

-- =============================================================================
-- NOTES
-- =============================================================================

-- 1. All timestamps stored as TEXT in ISO8601 format (YYYY-MM-DDTHH:MM:SS.mmmmmm)
-- 2. Tags stored as JSON TEXT arrays for simplicity in M1
-- 3. Event log remains source of truth - projections are always rebuildable
-- 4. Notification log added for Issue #16 (reminder tracking)
-- 5. Schema version must be updated when structure changes

