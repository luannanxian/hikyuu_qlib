"""Tests for monitoring decorators."""
import time


def test_monitor_performance_decorator():
    """Test performance monitoring decorator."""
    from src.infrastructure.monitoring.decorators import monitor_performance

    @monitor_performance
    def sample_function():
        time.sleep(0.01)
        return "result"

    result = sample_function()
    assert result == "result"


def test_monitor_performance_with_async():
    """Test performance monitoring with async function."""
    from src.infrastructure.monitoring.decorators import monitor_performance
    import asyncio

    @monitor_performance
    async def async_function():
        await asyncio.sleep(0.01)
        return "async_result"

    result = asyncio.run(async_function())
    assert result == "async_result"


def test_get_metrics():
    """Test getting collected metrics."""
    from src.infrastructure.monitoring.metrics import get_metrics

    metrics = get_metrics()
    assert isinstance(metrics, dict)
