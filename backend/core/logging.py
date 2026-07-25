import logging
import os
import sys
from backend.core.config import settings


from pathlib import Path


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


def write_debug_file(filename: str, content: str) -> None:
    """Saves debug output into files inside debug_logs/ folder, overwriting on each request."""
    try:
        project_root = Path(__file__).resolve().parents[2]
        debug_dir = project_root / "debug_logs"
        debug_dir.mkdir(parents=True, exist_ok=True)
        filepath = debug_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as err:
        logger.error("Failed to write debug file %s: %s", filename, err, exc_info=True)




