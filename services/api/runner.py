#!/usr/bin/env python3
"""Unified service runner for Helionyx.

Runs FastAPI server with integrated Telegram bot and full lifecycle management.
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.common.config import Config
from shared.common.logging import setup_logging


def main():
    """Main entry point for Helionyx service."""
    # Load configuration first
    config = Config.from_env()

    # Setup logging
    setup_logging(config.LOG_LEVEL)
    logger = logging.getLogger(__name__)

    logger.info(f"Starting Helionyx service (env: {config.ENV})")

    # Import uvicorn here to ensure logging is configured first
    import uvicorn

    # Run the FastAPI application
    # Lifespan events will handle service initialization and Telegram bot
    uvicorn.run(
        "services.api.main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        log_level=config.LOG_LEVEL.lower(),
        reload=False,  # Reload disabled for production stability
    )


if __name__ == "__main__":
    main()
