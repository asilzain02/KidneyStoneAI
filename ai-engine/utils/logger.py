"""
logger.py — Structured logging setup using structlog.
"""

from __future__ import annotations

import logging
import sys
from typing import Optional

import structlog


def get_logger(name: Optional[str] = None) -> structlog.BoundLogger:
    """Return a configured structlog logger."""
    if not structlog.is_configured():
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.dev.ConsoleRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
            cache_logger_on_first_use=True,
        )
    logger = structlog.get_logger(name or __name__)
    return logger
