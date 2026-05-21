"""Structured logging with rich formatting and log levels."""
import logging
import sys
from typing import Optional

from backend.config import get_settings

settings = get_settings()

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Returns a configured logger instance.
    Usage: logger = get_logger(__name__)
    """
    logger = logging.getLogger(name or "app")
    if logger.handlers:
        return logger  # Already configured

    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logger.setLevel(level)

    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
    return logger


# Root app logger
app_logger = get_logger("app")
