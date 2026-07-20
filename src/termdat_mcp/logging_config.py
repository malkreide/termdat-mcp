"""Structured logging via structlog, pinned to stderr (OBS-003 / OBS-004).

stdout is reserved for the MCP JSON-RPC stream, so every log record goes to
stderr as a JSON line. Import `log` for a module logger, or bind per-call
context with `log.bind(tool=..., ...)`.
"""

from __future__ import annotations

import logging
import sys

import structlog

_CONFIGURED = False


def configure_logging(level: str = "INFO") -> None:
    """Configure structlog to emit JSON to stderr. Idempotent."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    numeric = getattr(logging, level.upper(), logging.INFO)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(numeric),
        logger_factory=structlog.WriteLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )
    _CONFIGURED = True


def get_logger(name: str = "termdat_mcp") -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)


# Module-level logger; safe to import before configure_logging (uses defaults).
log = get_logger()
