"""Tests for error formatters.

Tests error message formatting:
- User-friendly error messages
- Technical error details
- Error response formatting
"""


def test_format_error_for_user():
    """Test formatting error for end users."""
    from src.infrastructure.errors.formatters import format_error_for_user
    from src.infrastructure.errors.exceptions import DataException

    exc = DataException(
        "Failed to load data", code="DATA_001", context={"stock_code": "000001"}
    )

    formatted = format_error_for_user(exc)

    assert isinstance(formatted, str)
    # Should provide user-friendly message
    assert "load" in formatted.lower() or "data" in formatted.lower()
    # Should not expose technical details like stock code
    assert "000001" not in formatted


def test_format_error_for_developer():
    """Test formatting error for developers with full details."""
    from src.infrastructure.errors.formatters import format_error_for_developer
    from src.infrastructure.errors.exceptions import DataException

    exc = DataException(
        "Failed to load data",
        code="DATA_001",
        context={"stock_code": "000001", "source": "hikyuu"},
    )

    formatted = format_error_for_developer(exc)

    assert isinstance(formatted, dict)
    assert formatted["code"] == "DATA_001"
    assert formatted["message"] == "Failed to load data"
    assert formatted["context"]["stock_code"] == "000001"


def test_format_error_as_json():
    """Test formatting error as JSON."""
    from src.infrastructure.errors.formatters import format_error_as_json
    from src.infrastructure.errors.exceptions import DataException
    import json

    exc = DataException(
        "Failed to load data", code="DATA_001", context={"stock_code": "000001"}
    )

    json_str = format_error_as_json(exc)

    assert isinstance(json_str, str)
    parsed = json.loads(json_str)
    assert parsed["code"] == "DATA_001"
    assert parsed["message"] == "Failed to load data"


def test_format_validation_errors():
    """Test formatting validation errors."""
    from src.infrastructure.errors.formatters import format_validation_errors

    errors = [
        {"field": "price", "message": "Price must be positive"},
        {"field": "date", "message": "Invalid date format"},
    ]

    formatted = format_validation_errors(errors)

    assert isinstance(formatted, str)
    assert "price" in formatted.lower()
    assert "date" in formatted.lower()


def test_format_error_response():
    """Test formatting error as HTTP response."""
    from src.infrastructure.errors.formatters import format_error_response
    from src.infrastructure.errors.exceptions import DataException

    exc = DataException(
        "Failed to load data", code="DATA_001", context={"stock_code": "000001"}
    )

    response = format_error_response(exc)

    assert isinstance(response, dict)
    assert "error" in response
    assert response["error"]["code"] == "DATA_001"
    assert "status_code" in response
    assert isinstance(response["status_code"], int)


def test_format_error_with_suggestions():
    """Test formatting error with helpful suggestions."""
    from src.infrastructure.errors.formatters import format_error_with_suggestions
    from src.infrastructure.errors.exceptions import ConfigurationException

    exc = ConfigurationException(
        "Invalid configuration", code="CONFIG_001", context={"config_key": "data_path"}
    )

    formatted = format_error_with_suggestions(exc)

    assert isinstance(formatted, dict)
    assert "message" in formatted
    assert "suggestions" in formatted
    assert isinstance(formatted["suggestions"], list)


def test_format_exception_chain():
    """Test formatting exception chain."""
    from src.infrastructure.errors.formatters import format_exception_chain
    from src.infrastructure.errors.exceptions import DataException

    original = ValueError("Original error")
    exc = DataException("Wrapped error", code="DATA_001", original_exception=original)

    formatted = format_exception_chain(exc)

    assert isinstance(formatted, list)
    assert len(formatted) >= 2
    assert formatted[0]["message"] == "Wrapped error"
    assert formatted[-1]["message"] == "Original error"


def test_format_error_for_logging():
    """Test formatting error for logging."""
    from src.infrastructure.errors.formatters import format_error_for_logging
    from src.infrastructure.errors.exceptions import ModelException

    exc = ModelException(
        "Training failed",
        code="MODEL_001",
        context={"model_name": "LightGBM", "epoch": 10},
    )

    formatted = format_error_for_logging(exc)

    assert isinstance(formatted, dict)
    assert "error_code" in formatted
    assert "error_message" in formatted
    assert "context" in formatted
    assert "timestamp" in formatted
