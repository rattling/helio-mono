#!/usr/bin/env python3
"""CLI tool to rebuild projections from event log."""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.common.config import Config
from services.event_store.file_store import FileEventStore
from services.query.service import QueryService


def setup_logging(level: str = "INFO"):
    """Configure logging."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


async def main():
    """Main entry point."""
    
    # Load configuration
    config = Config.from_env()
    setup_logging(config.LOG_LEVEL)
    
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("Rebuilding Projections from Event Log")
    logger.info("=" * 60)
    
    # Initialize services
    logger.info(f"Event store path: {config.EVENT_STORE_PATH}")
    logger.info(f"Database path: {config.PROJECTIONS_DB_PATH}")
    
    event_store = FileEventStore(data_dir=config.EVENT_STORE_PATH)
    await event_store.initialize()
    
    query_service = QueryService(event_store, db_path=Path(config.PROJECTIONS_DB_PATH))
    
    # Rebuild projections
    try:
        await query_service.rebuild_projections()
        
        # Display stats
        stats = query_service.get_stats()
        
        logger.info("=" * 60)
        logger.info("Rebuild Complete!")
        logger.info("=" * 60)
        logger.info(f"Todos:   {stats.get('todos', 0)}")
        logger.info(f"Notes:   {stats.get('notes', 0)}")
        logger.info(f"Tracks:  {stats.get('tracks', 0)}")
        logger.info(f"Total:   {stats.get('total_objects', 0)}")
        logger.info(f"Last rebuild: {stats.get('last_rebuild', 'N/A')}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Rebuild failed: {e}", exc_info=True)
        sys.exit(1)
    finally:
        query_service.close()


if __name__ == "__main__":
    asyncio.run(main())
