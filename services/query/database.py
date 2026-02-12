"""Database utilities for SQLite persistence."""

import sqlite3
import logging
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Database operation failed."""

    pass


def initialize_database(db_path: Path) -> None:
    """
    Initialize database with schema if it doesn't exist.

    Args:
        db_path: Path to SQLite database file
    """
    # Create parent directories if needed
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Check if database exists
    is_new = not db_path.exists()

    if is_new:
        logger.info(f"Creating new database at {db_path}")

    conn = sqlite3.connect(db_path)

    try:
        # Read and execute schema
        schema_path = Path(__file__).parent / "schema.sql"
        with open(schema_path) as f:
            conn.executescript(f.read())

        conn.commit()
        logger.info(f"Database initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise DatabaseError(f"Database initialization failed: {e}") from e
    finally:
        conn.close()


def create_connection(db_path: Path) -> sqlite3.Connection:
    """
    Create a database connection with recommended settings.

    Args:
        db_path: Path to SQLite database file

    Returns:
        Configured SQLite connection
    """
    conn = sqlite3.connect(db_path, check_same_thread=False)  # Allow async usage

    # Return dict-like rows
    conn.row_factory = sqlite3.Row

    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON")

    # Set WAL mode for better concurrency
    conn.execute("PRAGMA journal_mode = WAL")

    return conn


async def execute_with_retry(
    conn: sqlite3.Connection, query: str, params: tuple = (), max_retries: int = 3
) -> sqlite3.Cursor:
    """
    Execute query with retry on database lock.

    Args:
        conn: Database connection
        query: SQL query
        params: Query parameters
        max_retries: Maximum retry attempts

    Returns:
        Query cursor

    Raises:
        DatabaseError: If query fails after retries
    """
    for attempt in range(max_retries):
        try:
            return conn.execute(query, params)
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower() and attempt < max_retries - 1:
                wait_time = 0.1 * (2**attempt)
                logger.warning(f"Database locked, retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"Database operation failed: {e}")
                raise DatabaseError(f"Database operation failed: {e}") from e


def get_schema_version(conn: sqlite3.Connection) -> int:
    """
    Get current schema version.

    Args:
        conn: Database connection

    Returns:
        Schema version number
    """
    try:
        cursor = conn.execute(
            "SELECT value FROM projection_metadata WHERE key = ?", ("schema_version",)
        )
        row = cursor.fetchone()
        return int(row[0]) if row else 0
    except (sqlite3.Error, ValueError, TypeError):
        return 0


def check_schema_version(conn: sqlite3.Connection, expected: int = 1) -> None:
    """
    Verify schema version matches expected.

    Args:
        conn: Database connection
        expected: Expected schema version

    Raises:
        DatabaseError: If schema version doesn't match
    """
    current = get_schema_version(conn)

    if current != expected:
        raise DatabaseError(
            f"Schema version mismatch: expected {expected}, got {current}. "
            f"Run 'make rebuild' or update schema."
        )


def backup_database(db_path: Path, backup_dir: Path) -> Path:
    """
    Create timestamped backup of database.

    Args:
        db_path: Path to database file
        backup_dir: Directory for backups

    Returns:
        Path to backup file
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"helionyx_{timestamp}.db"
    backup_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Creating backup: {backup_path}")

    # SQLite backup API
    source = sqlite3.connect(db_path)
    dest = sqlite3.connect(backup_path)

    try:
        source.backup(dest)
        logger.info(f"Backup created successfully")
    finally:
        source.close()
        dest.close()

    return backup_path


@contextmanager
def transaction(conn: sqlite3.Connection):
    """
    Context manager for database transactions.

    Args:
        conn: Database connection

    Yields:
        Connection for use in transaction
    """
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Transaction failed, rolled back: {e}")
        raise


# =============================================================================
# Notification Log Functions
# =============================================================================


def was_reminded_today(conn: sqlite3.Connection, object_id: str) -> bool:
    """
    Check if a reminder was sent today for an object.

    Args:
        conn: Database connection
        object_id: ID of object to check

    Returns:
        True if reminder sent today
    """
    today = datetime.utcnow().date().isoformat()

    cursor = conn.execute(
        "SELECT 1 FROM notification_log "
        "WHERE notification_type = ? AND object_id = ? AND DATE(sent_at) = ?",
        ("reminder", object_id, today),
    )

    return cursor.fetchone() is not None


def mark_reminder_sent(conn: sqlite3.Connection, object_id: str) -> None:
    """
    Record that a reminder was sent.

    Args:
        conn: Database connection
        object_id: ID of object reminded about
    """
    conn.execute(
        "INSERT INTO notification_log (notification_type, object_id, sent_at) " "VALUES (?, ?, ?)",
        ("reminder", object_id, datetime.utcnow().isoformat()),
    )
    conn.commit()


def was_daily_summary_sent_today(conn: sqlite3.Connection) -> bool:
    """
    Check if daily summary was sent today.

    Args:
        conn: Database connection

    Returns:
        True if summary sent today
    """
    today = datetime.utcnow().date().isoformat()

    cursor = conn.execute(
        "SELECT 1 FROM notification_log " "WHERE notification_type = ? AND DATE(sent_at) = ?",
        ("daily_summary", today),
    )

    return cursor.fetchone() is not None


def mark_daily_summary_sent(conn: sqlite3.Connection) -> None:
    """
    Record that daily summary was sent.

    Args:
        conn: Database connection
    """
    conn.execute(
        "INSERT INTO notification_log (notification_type, sent_at) " "VALUES (?, ?)",
        ("daily_summary", datetime.utcnow().isoformat()),
    )
    conn.commit()


def was_notification_sent_recently(
    conn: sqlite3.Connection,
    notification_type: str,
    object_id: str | None = None,
    within_hours: int = 24,
    metadata_contains: str | None = None,
) -> bool:
    """Check whether a notification was sent within a recent time window."""
    cutoff = (datetime.utcnow() - timedelta(hours=within_hours)).isoformat()
    query = "SELECT 1 FROM notification_log WHERE notification_type = ? AND sent_at >= ?"
    params: list[str] = [notification_type, cutoff]

    if object_id:
        query += " AND object_id = ?"
        params.append(object_id)
    if metadata_contains:
        query += " AND metadata LIKE ?"
        params.append(f"%{metadata_contains}%")

    cursor = conn.execute(query, tuple(params))
    return cursor.fetchone() is not None


def log_notification(
    conn: sqlite3.Connection,
    notification_type: str,
    object_id: str | None = None,
    metadata: str | None = None,
) -> None:
    """Log notification delivery to durable notification log."""
    conn.execute(
        "INSERT INTO notification_log (notification_type, object_id, sent_at, metadata) "
        "VALUES (?, ?, ?, ?)",
        (notification_type, object_id, datetime.utcnow().isoformat(), metadata),
    )
    conn.commit()
