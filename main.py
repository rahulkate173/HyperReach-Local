#!/usr/bin/env python3
"""
Cold Outreach Engine - Main Entry Point

Run the application with:
    python main.py

Or for development:
    uvicorn backend.api:app --reload
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.api import run_server
from backend.config import settings

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger = logging.getLogger(__name__)

    try:
        logger.info("=" * 60)
        logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
        logger.info("=" * 60)
        logger.info(f"Host: {settings.HOST}:{settings.PORT}")
        logger.info(f"Model: {settings.MODEL_NAME}")
        logger.info(f"Device: {settings.DEVICE}")
        logger.info("=" * 60)

        run_server()
    except KeyboardInterrupt:
        logger.info("\n⏹ Shutdown requested by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
