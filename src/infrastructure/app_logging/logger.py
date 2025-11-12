"""Logging configuration and utilities.

This module provides structured logging capabilities:
- Structured JSON logging
- Trace ID support for distributed tracing
- Multiple log levels
- File and console output
"""
import logging
import logging.handlers
import sys
import uuid
from contextvars import ContextVar
from pathlib import Path
from typing import Optional

# Context variable for trace ID
_trace_id_var: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)


class TraceIDFilter(logging.Filter):
    """Add trace_id to log records."""

    def filter(self, record):
        """Add trace_id to the record."""
        record.trace_id = get_trace_id() or "no-trace-id"
        return True


def configure_logging(
    level: str = "INFO",
    format: str = "json",
    log_file: Optional[str] = None,
    enable_console: bool = True,
) -> None:
    """Configure application logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format: Log format ('json' or 'text')
        log_file: Optional path to log file
        enable_console: Enable console logging
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Create formatter
    if format == "json":
        fmt = "%(asctime)s | %(levelname)s | %(name)s | trace_id=%(trace_id)s | %(message)s"
    else:
        fmt = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

    formatter = logging.Formatter(fmt)

    # Add trace ID filter
    trace_filter = TraceIDFilter()

    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper()))
        console_handler.setFormatter(formatter)
        console_handler.addFilter(trace_filter)
        root_logger.addHandler(console_handler)

    # File handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
        )
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(formatter)
        file_handler.addFilter(trace_filter)
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def set_trace_id(trace_id: str) -> None:
    """Set the trace ID for the current context.

    Args:
        trace_id: Trace ID string
    """
    _trace_id_var.set(trace_id)


def get_trace_id() -> Optional[str]:
    """Get the current trace ID.

    Returns:
        Current trace ID or None
    """
    return _trace_id_var.get()


def clear_trace_id() -> None:
    """Clear the current trace ID."""
    _trace_id_var.set(None)


def generate_trace_id() -> str:
    """Generate a new trace ID.

    Returns:
        UUID-based trace ID
    """
    return str(uuid.uuid4())
