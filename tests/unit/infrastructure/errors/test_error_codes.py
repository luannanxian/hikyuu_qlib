"""Tests for error codes definition.

Tests the error code system:
- Error code structure and validation
- Error code categories
- Error code lookup and description
"""


def test_error_codes_data_category():
    """Test data-related error codes."""
    from src.infrastructure.errors.error_codes import ErrorCode

    assert hasattr(ErrorCode, "DATA_LOAD_FAILED")
    assert hasattr(ErrorCode, "DATA_VALIDATION_FAILED")
    assert hasattr(ErrorCode, "DATA_NOT_FOUND")
    assert hasattr(ErrorCode, "DATA_FORMAT_INVALID")


def test_error_codes_model_category():
    """Test model-related error codes."""
    from src.infrastructure.errors.error_codes import ErrorCode

    assert hasattr(ErrorCode, "MODEL_TRAINING_FAILED")
    assert hasattr(ErrorCode, "MODEL_PREDICTION_FAILED")
    assert hasattr(ErrorCode, "MODEL_NOT_FOUND")
    assert hasattr(ErrorCode, "MODEL_INVALID_PARAMETERS")


def test_error_codes_backtest_category():
    """Test backtest-related error codes."""
    from src.infrastructure.errors.error_codes import ErrorCode

    assert hasattr(ErrorCode, "BACKTEST_EXECUTION_FAILED")
    assert hasattr(ErrorCode, "BACKTEST_INVALID_CONFIG")
    assert hasattr(ErrorCode, "BACKTEST_INSUFFICIENT_DATA")


def test_error_codes_config_category():
    """Test configuration-related error codes."""
    from src.infrastructure.errors.error_codes import ErrorCode

    assert hasattr(ErrorCode, "CONFIG_INVALID")
    assert hasattr(ErrorCode, "CONFIG_NOT_FOUND")
    assert hasattr(ErrorCode, "CONFIG_PARSE_ERROR")


def test_error_code_structure():
    """Test error code structure format."""
    from src.infrastructure.errors.error_codes import ErrorCode

    # All error codes should be strings in format CATEGORY_###
    code = ErrorCode.DATA_LOAD_FAILED
    assert isinstance(code, str)
    assert "_" in code
    parts = code.split("_")
    assert len(parts) >= 2


def test_get_error_description():
    """Test getting error description by code."""
    from src.infrastructure.errors.error_codes import ErrorCode, get_error_description

    description = get_error_description(ErrorCode.DATA_LOAD_FAILED)
    assert isinstance(description, str)
    assert len(description) > 0


def test_get_error_description_unknown_code():
    """Test getting description for unknown error code."""
    from src.infrastructure.errors.error_codes import get_error_description

    description = get_error_description("UNKNOWN_999")
    assert "Unknown error" in description or "Not found" in description


def test_is_valid_error_code():
    """Test validating error codes."""
    from src.infrastructure.errors.error_codes import ErrorCode, is_valid_error_code

    assert is_valid_error_code(ErrorCode.DATA_LOAD_FAILED) is True
    assert is_valid_error_code("INVALID_CODE") is False


def test_get_error_category():
    """Test extracting error category from code."""
    from src.infrastructure.errors.error_codes import ErrorCode, get_error_category

    assert get_error_category(ErrorCode.DATA_LOAD_FAILED) == "DATA"
    assert get_error_category(ErrorCode.MODEL_TRAINING_FAILED) == "MODEL"
    assert get_error_category(ErrorCode.BACKTEST_EXECUTION_FAILED) == "BACKTEST"
    assert get_error_category(ErrorCode.CONFIG_INVALID) == "CONFIG"


def test_error_codes_uniqueness():
    """Test that all error codes are unique."""
    from src.infrastructure.errors.error_codes import ErrorCode

    codes = []
    for attr in dir(ErrorCode):
        if not attr.startswith("_"):
            value = getattr(ErrorCode, attr)
            if isinstance(value, str):
                codes.append(value)

    assert len(codes) == len(set(codes)), "Error codes must be unique"
