from __future__ import annotations

import json
import logging
import sys
import time
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from ..core.config import get_settings

# Sensitive patterns to redact
SENSITIVE_PATTERNS = {
    "api_key": r"(api[_-]?key[\"']?\s*[:=]\s*)[\"']?([^\"'\s,}]+)",
    "authorization": r"(authorization[\"']?\s*[:=]\s*)[\"']?([^\"'\s,}]+)",
    "x-api-key": r"(x-api-key[\"']?\s*[:=]\s*)[\"']?([^\"'\s,}]+)",
    "password": r"(password[\"']?\s*[:=]\s*)[\"']?([^\"'\s,}]+)",
    "token": r"(token[\"']?\s*[:=]\s*)[\"']?([^\"'\s,}]+)",
}


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add request context if available
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "method"):
            log_data["method"] = record.method
        if hasattr(record, "path"):
            log_data["path"] = record.path
        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add any additional fields
        for key in record.__dict__:
            if key not in (
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "message",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "thread",
                "threadName",
                "exc_info",
                "exc_text",
                "stack_info",
                "asctime",
                "request_id",
                "method",
                "path",
                "status_code",
                "duration_ms",
            ):
                log_data[key] = getattr(record, key)

        return json.dumps(log_data)


def redact_sensitive_data(data: str) -> str:
    """Redact sensitive information from strings."""
    import re

    redacted = data
    for pattern_name, pattern in SENSITIVE_PATTERNS.items():
        redacted = re.sub(
            pattern, r"\1[REDACTED]", redacted, flags=re.IGNORECASE
        )
    return redacted


def setup_logging(log_dir: str = "backend/logs") -> None:
    """Configure structured logging with file rotation."""
    settings = get_settings()

    # Create logs directory
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # JSON file handler with rotation
    file_handler = RotatingFileHandler(
        log_path / "app.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10,
    )
    file_handler.setFormatter(JSONFormatter())
    file_handler.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)

    # Console handler (plain text for development)
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)

    # Suppress verbose third-party logs
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.LoggerAdapter:
    """Get a logger instance with redaction support."""
    base_logger = logging.getLogger(name)
    return logging.LoggerAdapter(base_logger, {})


class LogContext:
    """Thread-local context for request-scoped logging."""

    _instance_data: dict[str, Any] = {}

    @classmethod
    def set(cls, key: str, value: Any) -> None:
        cls._instance_data[key] = value

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        return cls._instance_data.get(key, default)

    @classmethod
    def clear(cls) -> None:
        cls._instance_data.clear()

    @classmethod
    def get_all(cls) -> dict[str, Any]:
        return cls._instance_data.copy()
