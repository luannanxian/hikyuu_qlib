"""Performance monitoring decorators."""
import functools
import time
from typing import Any, Callable

from ..app_logging import get_logger

logger = get_logger(__name__)


def monitor_performance(func: Callable) -> Callable:
    """Decorator to monitor function performance.

    Args:
        func: Function to monitor

    Returns:
        Wrapped function
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time

            logger.info(
                f"Performance: {func.__name__}",
                extra={"function": func.__name__, "elapsed_seconds": elapsed},
            )

            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(
                f"Performance (with error): {func.__name__}",
                extra={
                    "function": func.__name__,
                    "elapsed_seconds": elapsed,
                    "error": str(e),
                },
            )
            raise

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs) -> Any:
        start_time = time.time()

        try:
            result = await func(*args, **kwargs)
            elapsed = time.time() - start_time

            logger.info(
                f"Performance: {func.__name__}",
                extra={"function": func.__name__, "elapsed_seconds": elapsed},
            )

            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(
                f"Performance (with error): {func.__name__}",
                extra={
                    "function": func.__name__,
                    "elapsed_seconds": elapsed,
                    "error": str(e),
                },
            )
            raise

    # Check if function is async
    import asyncio

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return wrapper
