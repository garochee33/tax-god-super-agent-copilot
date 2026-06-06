"""
Tax God - Structured Logging Configuration
JSON logging for production, human-readable for dev. Logs to stdout.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone


class _JsonFormatter(logging.Formatter):
    """JSON log formatter that includes request_id from contextvars."""

    def format(self, record: logging.LogRecord) -> str:
        from app.middleware.request_id import get_request_id

        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "request_id": get_request_id(),
        }
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)
        # Include extra fields
        for key in ("user_id", "path", "method", "status_code", "duration_ms"):
            if hasattr(record, key):
                log_entry[key] = getattr(record, key)
        return json.dumps(log_entry, default=str)


class _DevFormatter(logging.Formatter):
    """Human-readable formatter with request_id for development."""

    def format(self, record: logging.LogRecord) -> str:
        from app.middleware.request_id import get_request_id

        rid = get_request_id()
        prefix = f"[{rid[:8]}] " if rid else ""
        return f"{record.levelname:<7} {prefix}{record.name}: {record.getMessage()}"


def setup_logging(environment: str = "development", log_level: str = "INFO") -> None:
    """Configure root logger. Call once at app startup."""
    root = logging.getLogger()
    root.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Remove existing handlers
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    if environment == "production":
        handler.setFormatter(_JsonFormatter())
    else:
        handler.setFormatter(_DevFormatter())

    root.addHandler(handler)

    # Quiet noisy libraries
    for name in ("uvicorn.access", "sqlalchemy.engine", "httpx"):
        logging.getLogger(name).setLevel(logging.WARNING)
