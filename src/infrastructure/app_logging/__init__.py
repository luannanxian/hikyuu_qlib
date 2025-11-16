"""Infrastructure logging module.

This module provides structured logging capabilities:
- Structured JSON logging
- Trace ID support for distributed tracing
- Multiple log levels
- File and console output
"""
from .logger import (
    clear_trace_id,
    configure_logging,
    generate_trace_id,
    get_logger,
    get_trace_id,
    set_trace_id,
)

__all__ = [
    "clear_trace_id",
    "configure_logging",
    "generate_trace_id",
    "get_logger",
    "get_trace_id",
    "set_trace_id",
]
