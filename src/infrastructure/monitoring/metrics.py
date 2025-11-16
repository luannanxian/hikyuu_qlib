"""Metrics collection module."""
from typing import Any

_metrics: dict[str, Any] = {}


def get_metrics() -> dict[str, Any]:
    """Get collected metrics.

    Returns:
        Dictionary of metrics
    """
    return _metrics.copy()


def record_metric(name: str, value: Any) -> None:
    """Record a metric value.

    Args:
        name: Metric name
        value: Metric value
    """
    _metrics[name] = value


def clear_metrics() -> None:
    """Clear all metrics."""
    _metrics.clear()
