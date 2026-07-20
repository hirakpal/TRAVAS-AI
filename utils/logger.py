"""Logging Utilities"""

import logging
from config.settings import Settings


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, Settings.LOG_LEVEL))
    return logger
