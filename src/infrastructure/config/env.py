"""Environment variable handling utilities.

This module provides utilities for working with environment variables:
- Type-safe environment variable access
- Default value handling
- Type conversion (int, float, bool, list)
- Loading from .env files
"""
import os
from typing import Any, Dict, List, Optional

from ..errors import ConfigurationException


def get_env(name: str, default: Optional[str] = None, required: bool = False) -> str:
    """Get environment variable value.

    Args:
        name: Environment variable name
        default: Default value if not found
        required: If True, raise exception if not found

    Returns:
        Environment variable value

    Raises:
        ConfigurationException: If required and not found
    """
    value = os.environ.get(name, default)

    if required and value is None:
        raise ConfigurationException(
            f"Required environment variable '{name}' not found",
            code="CONFIG_MISSING_REQUIRED",
            context={"variable": name},
        )

    return value or ""


def get_env_as_int(
    name: str, default: Optional[int] = None, required: bool = False
) -> int:
    """Get environment variable as integer.

    Args:
        name: Environment variable name
        default: Default value if not found
        required: If True, raise exception if not found

    Returns:
        Integer value

    Raises:
        ConfigurationException: If conversion fails or required and not found
    """
    value = get_env(name, str(default) if default is not None else None, required)

    if not value and not required:
        return default or 0

    try:
        return int(value)
    except ValueError as e:
        raise ConfigurationException(
            f"Cannot convert '{name}' to integer: {value}",
            code="CONFIG_INVALID",
            context={"variable": name, "value": value},
            original_exception=e,
        ) from e


def get_env_as_float(
    name: str, default: Optional[float] = None, required: bool = False
) -> float:
    """Get environment variable as float.

    Args:
        name: Environment variable name
        default: Default value if not found
        required: If True, raise exception if not found

    Returns:
        Float value

    Raises:
        ConfigurationException: If conversion fails or required and not found
    """
    value = get_env(name, str(default) if default is not None else None, required)

    if not value and not required:
        return default or 0.0

    try:
        return float(value)
    except ValueError as e:
        raise ConfigurationException(
            f"Cannot convert '{name}' to float: {value}",
            code="CONFIG_INVALID",
            context={"variable": name, "value": value},
            original_exception=e,
        ) from e


def get_env_as_bool(name: str, default: bool = False, required: bool = False) -> bool:
    """Get environment variable as boolean.

    True values: 'true', 'True', 'TRUE', '1', 'yes', 'Yes'
    False values: 'false', 'False', 'FALSE', '0', 'no', 'No'

    Args:
        name: Environment variable name
        default: Default value if not found
        required: If True, raise exception if not found

    Returns:
        Boolean value
    """
    value = get_env(name, str(default) if default is not None else None, required)

    if not value and not required:
        return default

    true_values = {"true", "True", "TRUE", "1", "yes", "Yes"}
    false_values = {"false", "False", "FALSE", "0", "no", "No"}

    if value in true_values:
        return True
    elif value in false_values:
        return False
    else:
        return default


def get_env_as_list(
    name: str,
    default: Optional[List[str]] = None,
    separator: str = ",",
    required: bool = False,
) -> List[str]:
    """Get environment variable as list.

    Args:
        name: Environment variable name
        default: Default value if not found
        separator: Separator character (default: ',')
        required: If True, raise exception if not found

    Returns:
        List of strings
    """
    value = get_env(name, None, required)

    if not value and not required:
        return default or []

    return [item.strip() for item in value.split(separator)]


def get_all_env_with_prefix(prefix: str) -> Dict[str, str]:
    """Get all environment variables with a specific prefix.

    Args:
        prefix: Prefix to filter by

    Returns:
        Dictionary of environment variables (without prefix in keys)
    """
    result = {}

    for key, value in os.environ.items():
        if key.startswith(prefix):
            # Remove prefix from key
            clean_key = key[len(prefix) :]
            result[clean_key] = value

    return result


def load_env_file(file_path: str) -> None:
    """Load environment variables from .env file.

    Args:
        file_path: Path to .env file

    Raises:
        ConfigurationException: If file not found or parsing fails
    """
    if not os.path.exists(file_path):
        raise ConfigurationException(
            f"Environment file not found: {file_path}",
            code="CONFIG_NOT_FOUND",
            context={"file_path": file_path},
        )

    try:
        with open(file_path, "r") as f:
            for line in f:
                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue

                # Parse KEY=VALUE
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()

                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]

                    os.environ[key] = value

    except Exception as e:
        raise ConfigurationException(
            f"Failed to load environment file: {file_path}",
            code="CONFIG_PARSE_ERROR",
            context={"file_path": file_path},
            original_exception=e,
        ) from e


def env_to_settings_dict(
    prefix: str = "", keys: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Convert environment variables to settings dictionary.

    Args:
        prefix: Prefix to filter by
        keys: Specific keys to include (if None, include all with prefix)

    Returns:
        Dictionary of settings
    """
    if keys:
        return {key: os.environ.get(f"{prefix}{key}", "") for key in keys}
    else:
        return get_all_env_with_prefix(prefix)
