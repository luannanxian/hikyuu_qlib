"""Exception handlers for centralized error handling.

This module provides utilities for handling exceptions consistently:
- Global exception handler
- Exception handler decorator
- Context manager for exception handling
- Chained exception handlers
"""
import functools
import logging
from typing import Any
from collections.abc import Callable

from .exceptions import BaseInfrastructureException
from .formatters import format_error_for_logging

# Configure logger
logger = logging.getLogger(__name__)


def handle_exception(
    exception: Exception,
    on_error: Callable[[Exception], None] | None = None,
) -> dict[str, Any]:
    """Handle an exception and return structured error information.

    Args:
        exception: The exception to handle
        on_error: Optional callback function to call with the exception

    Returns:
        Dictionary with structured error information
    """
    # Log the exception
    if isinstance(exception, BaseInfrastructureException):
        log_data = format_error_for_logging(exception)
        logger.error(
            f"Infrastructure error: {exception.code}",
            extra=log_data,
            exc_info=True,
        )
    else:
        logger.exception(f"Unexpected error: {exception!s}")

    # Call error callback if provided
    if on_error:
        try:
            on_error(exception)
        except Exception as callback_error:
            logger.error(f"Error in error callback: {callback_error}")

    # Return structured error information
    if isinstance(exception, BaseInfrastructureException):
        return {"error": exception.to_dict()}
    else:
        return {
            "error": {
                "exception_type": exception.__class__.__name__,
                "message": str(exception),
                "code": "UNKNOWN_ERROR",
            },
        }


class ExceptionHandler:
    """Context manager for exception handling."""

    def __init__(self):
        """Initialize the exception handler."""
        self.caught_exception: Exception | None = None

    def __enter__(self):
        """Enter the context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager."""
        if exc_val:
            self.caught_exception = exc_val
        # Return False to let the exception propagate
        return False

    def handle(self, exception: Exception) -> dict[str, Any]:
        """Handle an exception within the context.

        Args:
            exception: The exception to handle

        Returns:
            Dictionary with structured error information
        """
        return handle_exception(exception)


def exception_handler():
    """Create an exception handler context manager.

    Returns:
        ExceptionHandler instance

    Example:
        with exception_handler() as handler:
            try:
                # risky operation
                pass
            except Exception as e:
                error_info = handler.handle(e)
    """
    return ExceptionHandler()


def handle_exceptions(
    reraise: bool = False,
    on_error: Callable[[Exception], None] | None = None,
):
    """Decorator for automatic exception handling.

    Args:
        reraise: If True, reraise the exception after handling
        on_error: Optional callback function to call with the exception

    Returns:
        Decorated function

    Example:
        @handle_exceptions
        def my_function():
            # code that might raise exceptions
            pass
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                result = handle_exception(e, on_error=on_error)
                if reraise:
                    raise
                return result

        return wrapper

    return decorator


class ChainedExceptionHandler:
    """Handler that chains multiple exception handlers.

    Allows registering multiple handlers that will be called in order.
    If a handler returns True, the chain stops.
    """

    def __init__(self):
        """Initialize the chained handler."""
        self.handlers: list[Callable[[Exception], bool]] = []

    def add_handler(self, handler: Callable[[Exception], bool]):
        """Add a handler to the chain.

        Args:
            handler: Function that takes an exception and returns True if handled
        """
        self.handlers.append(handler)

    def handle(self, exception: Exception) -> bool:
        """Handle an exception using the handler chain.

        Args:
            exception: The exception to handle

        Returns:
            True if any handler handled the exception, False otherwise
        """
        for handler in self.handlers:
            try:
                if handler(exception):
                    return True
            except Exception as handler_error:
                logger.error(
                    f"Error in exception handler: {handler_error}",
                    exc_info=True,
                )
        return False
