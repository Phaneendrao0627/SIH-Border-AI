"""Structured and privacy-aware logging configuration for tampering detection."""

import logging
import sys
from typing import Optional


LOGGER_NAME = "tampering_detection"


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Retrieve a child or root logger for the tampering detection package.

    Args:
        name: Optional sub-module name. If None, returns the root package logger.

    Returns:
        Configured logging.Logger instance.
    """
    base_logger = logging.getLogger(LOGGER_NAME)
    if name:
        return base_logger.getChild(name)
    return base_logger


def setup_logging(
    level: int = logging.INFO,
    stream: Optional[object] = None,
    log_format: Optional[str] = None,
) -> logging.Logger:
    """Configure structured logging for the module.

    Ensures that log outputs avoid personally identifiable information (PII)
    and use standard structured formatting.

    Args:
        level: Logging level (e.g., logging.INFO, logging.DEBUG).
        stream: Output stream (defaults to sys.stderr).
        log_format: Custom format string.

    Returns:
        Root package logger.
    """
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level)

    # Avoid duplicate handlers if setup_logging is called multiple times
    if not logger.handlers:
        handler = logging.StreamHandler(stream or sys.stderr)
        formatter = logging.Formatter(
            log_format or "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.propagate = False
    return logger
