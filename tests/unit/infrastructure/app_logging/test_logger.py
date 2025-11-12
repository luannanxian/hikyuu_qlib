"""Tests for logger module.

Tests logger configuration and usage:
- Logger creation and configuration
- Log levels
- Trace ID support
- Structured logging output
"""


def test_get_logger():
    """Test getting a logger instance."""
    from src.infrastructure.app_logging.logger import get_logger

    logger = get_logger("test_module")

    assert logger is not None
    assert logger.name == "test_module"


def test_logger_log_levels():
    """Test different log levels."""
    from src.infrastructure.app_logging.logger import get_logger

    logger = get_logger("test_levels")

    # Should not raise
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")


def test_logger_with_context():
    """Test logging with context."""
    from src.infrastructure.app_logging.logger import get_logger

    logger = get_logger("test_context")

    # Should not raise
    logger.info("Message with context", extra={"user_id": 123, "action": "login"})


def test_configure_logging():
    """Test configuring logging."""
    from src.infrastructure.app_logging.logger import configure_logging

    # Should not raise
    configure_logging(level="INFO", format="json")


def test_logger_captures_trace_id():
    """Test that logger can capture trace_id."""
    from src.infrastructure.app_logging.logger import get_logger, set_trace_id

    logger = get_logger("test_trace")

    trace_id = "test-trace-123"
    set_trace_id(trace_id)

    # Should log with trace_id in context
    logger.info("Test message")


def test_get_current_trace_id():
    """Test getting current trace ID."""
    from src.infrastructure.app_logging.logger import get_trace_id, set_trace_id

    trace_id = "trace-456"
    set_trace_id(trace_id)

    assert get_trace_id() == trace_id


def test_clear_trace_id():
    """Test clearing trace ID."""
    from src.infrastructure.app_logging.logger import (
        clear_trace_id,
        get_trace_id,
        set_trace_id,
    )

    set_trace_id("trace-789")
    clear_trace_id()

    assert get_trace_id() is None
