"""
Logging configuration for Blueprint Eye application.
"""

import logging
import sys
from backend.core.config import settings


def setup_logging() -> logging.Logger:
    """Configure structured logging for the application."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    logger = logging.getLogger(settings.PROJECT_NAME)
    logger.setLevel(log_level)
    return logger


logger = setup_logging()
