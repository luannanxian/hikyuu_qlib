"""Error code definitions for the application.

This module defines standardized error codes for different categories:
- DATA_xxx: Data loading and validation errors
- MODEL_xxx: Model training and prediction errors
- BACKTEST_xxx: Backtesting errors
- CONFIG_xxx: Configuration errors

Error codes follow the format: CATEGORY_###
"""


class ErrorCode:
    """Standard error codes for the application."""

    # Data-related error codes (DATA_001 - DATA_099)
    DATA_LOAD_FAILED = "DATA_001"
    DATA_VALIDATION_FAILED = "DATA_002"
    DATA_NOT_FOUND = "DATA_003"
    DATA_FORMAT_INVALID = "DATA_004"
    DATA_CONVERSION_FAILED = "DATA_005"
    DATA_MISSING_REQUIRED_FIELDS = "DATA_006"
    DATA_DUPLICATE_ENTRY = "DATA_007"
    DATA_OUT_OF_RANGE = "DATA_008"

    # Model-related error codes (MODEL_001 - MODEL_099)
    MODEL_TRAINING_FAILED = "MODEL_001"
    MODEL_PREDICTION_FAILED = "MODEL_002"
    MODEL_NOT_FOUND = "MODEL_003"
    MODEL_INVALID_PARAMETERS = "MODEL_004"
    MODEL_LOAD_FAILED = "MODEL_005"
    MODEL_SAVE_FAILED = "MODEL_006"
    MODEL_INCOMPATIBLE_VERSION = "MODEL_007"
    MODEL_INSUFFICIENT_DATA = "MODEL_008"

    # Backtest-related error codes (BACKTEST_001 - BACKTEST_099)
    BACKTEST_EXECUTION_FAILED = "BACKTEST_001"
    BACKTEST_INVALID_CONFIG = "BACKTEST_002"
    BACKTEST_INSUFFICIENT_DATA = "BACKTEST_003"
    BACKTEST_CALCULATION_ERROR = "BACKTEST_004"
    BACKTEST_INVALID_SIGNAL = "BACKTEST_005"

    # Configuration-related error codes (CONFIG_001 - CONFIG_099)
    CONFIG_INVALID = "CONFIG_001"
    CONFIG_NOT_FOUND = "CONFIG_002"
    CONFIG_PARSE_ERROR = "CONFIG_003"
    CONFIG_MISSING_REQUIRED = "CONFIG_004"
    CONFIG_VALIDATION_FAILED = "CONFIG_005"


# Error code descriptions
ERROR_DESCRIPTIONS: dict[str, str] = {
    # Data errors
    ErrorCode.DATA_LOAD_FAILED: "Failed to load data from source",
    ErrorCode.DATA_VALIDATION_FAILED: "Data validation failed",
    ErrorCode.DATA_NOT_FOUND: "Requested data not found",
    ErrorCode.DATA_FORMAT_INVALID: "Invalid data format",
    ErrorCode.DATA_CONVERSION_FAILED: "Failed to convert data format",
    ErrorCode.DATA_MISSING_REQUIRED_FIELDS: "Required data fields are missing",
    ErrorCode.DATA_DUPLICATE_ENTRY: "Duplicate data entry detected",
    ErrorCode.DATA_OUT_OF_RANGE: "Data value out of valid range",
    # Model errors
    ErrorCode.MODEL_TRAINING_FAILED: "Model training failed",
    ErrorCode.MODEL_PREDICTION_FAILED: "Model prediction failed",
    ErrorCode.MODEL_NOT_FOUND: "Model not found",
    ErrorCode.MODEL_INVALID_PARAMETERS: "Invalid model parameters",
    ErrorCode.MODEL_LOAD_FAILED: "Failed to load model",
    ErrorCode.MODEL_SAVE_FAILED: "Failed to save model",
    ErrorCode.MODEL_INCOMPATIBLE_VERSION: "Incompatible model version",
    ErrorCode.MODEL_INSUFFICIENT_DATA: "Insufficient data for model operation",
    # Backtest errors
    ErrorCode.BACKTEST_EXECUTION_FAILED: "Backtest execution failed",
    ErrorCode.BACKTEST_INVALID_CONFIG: "Invalid backtest configuration",
    ErrorCode.BACKTEST_INSUFFICIENT_DATA: "Insufficient data for backtest",
    ErrorCode.BACKTEST_CALCULATION_ERROR: "Error in backtest calculations",
    ErrorCode.BACKTEST_INVALID_SIGNAL: "Invalid trading signal",
    # Configuration errors
    ErrorCode.CONFIG_INVALID: "Invalid configuration",
    ErrorCode.CONFIG_NOT_FOUND: "Configuration not found",
    ErrorCode.CONFIG_PARSE_ERROR: "Failed to parse configuration",
    ErrorCode.CONFIG_MISSING_REQUIRED: "Required configuration is missing",
    ErrorCode.CONFIG_VALIDATION_FAILED: "Configuration validation failed",
}


def get_error_description(code: str) -> str:
    """Get human-readable description for an error code.

    Args:
        code: Error code

    Returns:
        Description string, or a default message if code not found
    """
    return ERROR_DESCRIPTIONS.get(code, f"Unknown error code: {code}")


def is_valid_error_code(code: str) -> bool:
    """Check if an error code is valid.

    Args:
        code: Error code to validate

    Returns:
        True if the code is valid, False otherwise
    """
    return code in ERROR_DESCRIPTIONS


def get_error_category(code: str) -> str | None:
    """Extract the category from an error code.

    Args:
        code: Error code (e.g., 'DATA_001')

    Returns:
        Category string (e.g., 'DATA'), or None if invalid format
    """
    parts = code.split("_")
    if len(parts) >= 2:
        return parts[0]
    return None
