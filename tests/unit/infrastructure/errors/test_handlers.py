"""Tests for exception handlers.

Tests exception handling utilities:
- Global exception handler
- Context manager for exception handling
- Exception logging and reporting
"""
import pytest
from unittest.mock import patch


def test_handle_exception_basic():
    """Test basic exception handling."""
    from src.infrastructure.errors.handlers import handle_exception
    from src.infrastructure.errors.exceptions import DataException

    exc = DataException("Test error", code="DATA_001")

    # Should not raise, just log and return structured error
    result = handle_exception(exc)

    assert result is not None
    assert "error" in result
    assert result["error"]["code"] == "DATA_001"


def test_handle_exception_with_unknown_exception():
    """Test handling unknown exception types."""
    from src.infrastructure.errors.handlers import handle_exception

    exc = ValueError("Unknown error")
    result = handle_exception(exc)

    assert result is not None
    assert "error" in result
    assert result["error"]["message"] == "Unknown error"


def test_exception_context_manager():
    """Test exception context manager."""
    from src.infrastructure.errors.handlers import exception_handler
    from src.infrastructure.errors.exceptions import DataException

    caught = False
    error_info = None

    with exception_handler() as handler:
        try:
            raise DataException("Test error", code="DATA_001")
        except Exception as e:
            caught = True
            error_info = handler.handle(e)

    assert caught
    assert error_info is not None


def test_exception_handler_with_callback():
    """Test exception handler with callback function."""
    from src.infrastructure.errors.handlers import handle_exception

    callback_called = False
    callback_error = None

    def callback(error):
        nonlocal callback_called, callback_error
        callback_called = True
        callback_error = error

    from src.infrastructure.errors.exceptions import DataException

    exc = DataException("Test error", code="DATA_001")
    handle_exception(exc, on_error=callback)

    assert callback_called
    assert callback_error is not None


def test_exception_handler_decorator():
    """Test exception handler decorator."""
    from src.infrastructure.errors.handlers import handle_exceptions
    from src.infrastructure.errors.exceptions import DataException

    @handle_exceptions()
    def failing_function():
        raise DataException("Test error", code="DATA_001")

    result = failing_function()
    assert result is not None
    assert "error" in result


def test_exception_handler_decorator_with_reraise():
    """Test exception handler decorator with reraise option."""
    from src.infrastructure.errors.handlers import handle_exceptions
    from src.infrastructure.errors.exceptions import DataException

    @handle_exceptions(reraise=True)
    def failing_function():
        raise DataException("Test error", code="DATA_001")

    with pytest.raises(DataException):
        failing_function()


def test_exception_handler_logs_exception():
    """Test that exception handler logs exceptions."""
    from src.infrastructure.errors.handlers import handle_exception
    from src.infrastructure.errors.exceptions import DataException

    with patch("src.infrastructure.errors.handlers.logger") as mock_logger:
        exc = DataException("Test error", code="DATA_001")
        handle_exception(exc)

        assert mock_logger.error.called or mock_logger.exception.called


def test_chain_exception_handlers():
    """Test chaining multiple exception handlers."""
    from src.infrastructure.errors.handlers import ChainedExceptionHandler
    from src.infrastructure.errors.exceptions import DataException, ModelException

    handler = ChainedExceptionHandler()

    data_handled = False
    model_handled = False

    def data_handler(exc):
        nonlocal data_handled
        if isinstance(exc, DataException):
            data_handled = True
            return True
        return False

    def model_handler(exc):
        nonlocal model_handled
        if isinstance(exc, ModelException):
            model_handled = True
            return True
        return False

    handler.add_handler(data_handler)
    handler.add_handler(model_handler)

    # Test DataException
    handler.handle(DataException("Data error", code="DATA_001"))
    assert data_handled
    assert not model_handled

    # Reset and test ModelException
    data_handled = False
    handler.handle(ModelException("Model error", code="MODEL_001"))
    assert not data_handled
    assert model_handled
