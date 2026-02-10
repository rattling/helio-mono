"""Database utilities for SQLite persistence."""

import sqlite3
import logging
import asyncio
from pathlib import Path
from datetime import datetime
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
    conn = sqlite3.connect(
        db_path,
        check_same_thread=False  # Allow async usage
    )
    
    # Return dict-like rows
    conn.row_factory = sqlite3.Row
    
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON")
    
    # Set WAL mode for better concurrency
    conn.execute("PRAGMA journal_mode = WAL")
    
    return conn


async def execute_with_retry(
    conn: sqlite3.Connection,
    query: str,
    params: tuple = (),
    max_retries: int = 3
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
                wait_time = 0.1 * (2 ** attempt)
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
            "SELECT value FROM projection_metadata WHERE key = ?",
            ("schema_version",)
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
