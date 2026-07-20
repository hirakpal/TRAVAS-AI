"""Logging configuration for TRAVAS system."""

import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime


def get_logger(name: str, log_level: str = "INFO") -> logging.Logger:
    """Get configured logger instance.

    Args:
        name: Logger name (typically __name__)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Only configure if not already configured
    if logger.handlers:
        return logger

    # Set log level
    log_level = os.getenv("LOG_LEVEL", log_level).upper()
    logger.setLevel(getattr(logging, log_level, logging.INFO))

    # Create logs directory if it doesn't exist
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # File handler with rotation
    log_file = os.path.join(log_dir, "travas.log")
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(getattr(logging, log_level, logging.INFO))

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level, logging.INFO))

    # Formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


class StructuredLogger:
    """Logger with structured logging support."""

    def __init__(self, name: str):
        self.logger = get_logger(name)

    def log_event(self, event_type: str, data: dict, level: str = "INFO"):
        """Log structured event."""
        message = f"[{event_type}] {data}"
        getattr(self.logger, level.lower())(message)

    def log_tool_call(self, tool_name: str, input_data: dict, status: str = "START"):
        """Log tool call event."""
        self.log_event("TOOL_CALL", {
            "tool": tool_name,
            "status": status,
            "data": input_data,
            "timestamp": datetime.now().isoformat()
        }, "DEBUG")

    def log_api_call(self, api_name: str, status: str, latency_ms: float):
        """Log API call event."""
        self.log_event("API_CALL", {
            "api": api_name,
            "status": status,
            "latency_ms": latency_ms,
            "timestamp": datetime.now().isoformat()
        }, "DEBUG")

    def log_error(self, error_type: str, message: str, context: dict = None):
        """Log error event."""
        self.log_event("ERROR", {
            "type": error_type,
            "message": message,
            "context": context or {},
            "timestamp": datetime.now().isoformat()
        }, "ERROR")
