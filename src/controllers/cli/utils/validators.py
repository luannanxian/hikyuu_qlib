"""
CLI input validators.

Provides validation functions for:
- Dates
- Stock codes
- File paths
- Numeric values
"""

import re
from datetime import date, datetime
from pathlib import Path


def validate_date(date_str: str) -> date:
    """
    Validate and parse date string.

    Args:
        date_str: Date string in format YYYY-MM-DD

    Returns:
        date: Parsed date object

    Raises:
        ValueError: If date format is invalid
    """
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError as e:
        raise ValueError(
            f"Invalid date format: {date_str}. Expected format: YYYY-MM-DD",
        ) from e


def validate_stock_code(code: str) -> str:
    """
    Validate stock code format.

    Args:
        code: Stock code (e.g., sh600000, sz000001)

    Returns:
        str: Validated stock code in lowercase

    Raises:
        ValueError: If stock code format is invalid
    """
    code = code.lower().strip()

    # Check format: should be market prefix + 6 digits
    pattern = r"^(sh|sz)\d{6}$"
    if not re.match(pattern, code):
        raise ValueError(
            f"Invalid stock code format: {code}. "
            f"Expected format: sh/sz followed by 6 digits (e.g., sh600000)",
        )

    # Check market prefix
    if not code.startswith(("sh", "sz")):
        raise ValueError(
            f"Invalid stock code: {code}. Stock code must start with 'sh' or 'sz'",
        )

    return code


def validate_file_path(path_str: str) -> str:
    """
    Validate file path exists and is a file.

    Args:
        path_str: File path string

    Returns:
        str: Validated file path

    Raises:
        ValueError: If path doesn't exist or is not a file
    """
    path = Path(path_str)

    if not path.exists():
        raise ValueError(f"File not found: {path_str}")

    if not path.is_file():
        raise ValueError(f"Path is not a file: {path_str}")

    return str(path.absolute())


def validate_positive_float(value_str: str) -> float:
    """
    Validate and parse positive float value.

    Args:
        value_str: String representation of float

    Returns:
        float: Parsed positive float value

    Raises:
        ValueError: If value is not a positive float
    """
    try:
        value = float(value_str)
    except ValueError as e:
        raise ValueError(f"Invalid number format: {value_str}") from e

    if value <= 0:
        raise ValueError(f"Value must be positive: {value_str}")

    return value


def validate_rate(value_str: str) -> float:
    """
    Validate and parse rate value (between 0 and 1).

    Args:
        value_str: String representation of rate

    Returns:
        float: Parsed rate value

    Raises:
        ValueError: If rate is not between 0 and 1
    """
    try:
        value = float(value_str)
    except ValueError as e:
        raise ValueError(f"Invalid number format: {value_str}") from e

    if value < 0 or value > 1:
        raise ValueError(f"Rate must be between 0 and 1: {value_str}")

    return value


def validate_positive_int(value_str: str) -> int:
    """
    Validate and parse positive integer value.

    Args:
        value_str: String representation of integer

    Returns:
        int: Parsed positive integer value

    Raises:
        ValueError: If value is not a positive integer
    """
    try:
        value = int(value_str)
    except ValueError as e:
        raise ValueError(f"Invalid integer format: {value_str}") from e

    if value <= 0:
        raise ValueError(f"Value must be positive: {value_str}")

    return value


def validate_model_type(model_type: str) -> str:
    """
    Validate model type.

    Args:
        model_type: Model type string

    Returns:
        str: Validated model type in uppercase

    Raises:
        ValueError: If model type is not supported
    """
    valid_types = ["LGBM", "MLP", "LSTM", "GRU", "TRANSFORMER"]
    model_type_upper = model_type.upper()

    if model_type_upper not in valid_types:
        raise ValueError(
            f"Invalid model type: {model_type}. "
            f"Supported types: LGBM, MLP, LSTM, GRU, TRANSFORMER",
        )

    return model_type_upper
