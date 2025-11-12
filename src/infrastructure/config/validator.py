"""Configuration validation utilities.

This module provides utilities for validating configuration:
- Required field validation
- Type validation
- Value range validation
- Custom validation rules
"""
import os
from typing import Any, Callable, Dict, List, Type
from urllib.parse import urlparse

from ..errors import ConfigurationException
from .settings import Settings


def validate_required_fields(
    config: Dict[str, Any], required_fields: List[str]
) -> None:
    """Validate that required fields are present in configuration.

    Args:
        config: Configuration dictionary
        required_fields: List of required field names

    Raises:
        ConfigurationException: If required fields are missing
    """
    missing = [field for field in required_fields if field not in config]

    if missing:
        raise ConfigurationException(
            f"Missing required configuration fields: {', '.join(missing)}",
            code="CONFIG_MISSING_REQUIRED",
            context={"missing_fields": missing},
        )


def validate_field_type(value: Any, expected_type: Type) -> bool:
    """Validate that a value matches the expected type.

    Args:
        value: Value to validate
        expected_type: Expected type

    Returns:
        True if type matches, False otherwise
    """
    return isinstance(value, expected_type)


def validate_config_types(config: Dict[str, Any], type_specs: Dict[str, Type]) -> None:
    """Validate types for all configuration fields.

    Args:
        config: Configuration dictionary
        type_specs: Dictionary mapping field names to expected types

    Raises:
        ConfigurationException: If any field has wrong type
    """
    errors = []

    for field, expected_type in type_specs.items():
        if field in config:
            value = config[field]
            if not isinstance(value, expected_type):
                errors.append(
                    f"{field}: expected {expected_type.__name__}, "
                    f"got {type(value).__name__}"
                )

    if errors:
        raise ConfigurationException(
            f"Configuration type validation failed: {'; '.join(errors)}",
            code="CONFIG_VALIDATION_FAILED",
            context={"errors": errors},
        )


def validate_path_exists(path: str) -> None:
    """Validate that a path exists.

    Args:
        path: File or directory path

    Raises:
        ConfigurationException: If path does not exist
    """
    if not os.path.exists(path):
        raise ConfigurationException(
            f"Path does not exist: {path}",
            code="CONFIG_INVALID",
            context={"path": path},
        )


def validate_value_range(value: float, min_val: float, max_val: float) -> bool:
    """Validate that a value is within a range.

    Args:
        value: Value to validate
        min_val: Minimum value (inclusive)
        max_val: Maximum value (inclusive)

    Returns:
        True if value is in range, False otherwise
    """
    return min_val <= value <= max_val


def validate_enum_value(value: str, valid_values: List[str]) -> bool:
    """Validate that a value is one of the allowed values.

    Args:
        value: Value to validate
        valid_values: List of valid values

    Returns:
        True if value is valid, False otherwise
    """
    return value in valid_values


def validate_url_format(url: str) -> bool:
    """Validate URL format.

    Args:
        url: URL to validate

    Returns:
        True if URL is valid, False otherwise
    """
    if not url:
        return False

    try:
        result = urlparse(url)
        # URL must have a scheme
        return bool(result.scheme)
    except Exception:
        return False


def validate_settings(settings: Settings) -> None:
    """Validate a Settings object.

    Performs comprehensive validation on a Settings instance.

    Args:
        settings: Settings object to validate

    Raises:
        ConfigurationException: If validation fails
    """
    errors = []

    # Validate log level
    valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if settings.LOG_LEVEL not in valid_log_levels:
        errors.append(f"Invalid log level: {settings.LOG_LEVEL}")

    # Validate environment
    valid_environments = ["dev", "test", "prod"]
    if settings.ENVIRONMENT not in valid_environments:
        errors.append(f"Invalid environment: {settings.ENVIRONMENT}")

    # Validate initial capital
    if settings.INITIAL_CAPITAL <= 0:
        errors.append("Initial capital must be positive")

    # Validate commission rate
    if not (0 <= settings.COMMISSION_RATE <= 1):
        errors.append("Commission rate must be between 0 and 1")

    if errors:
        raise ConfigurationException(
            f"Settings validation failed: {'; '.join(errors)}",
            code="CONFIG_VALIDATION_FAILED",
            context={"errors": errors},
        )


class ConfigValidator:
    """Configuration validator with custom rules."""

    def __init__(self):
        """Initialize validator."""
        self.rules: Dict[str, Callable[[Any], bool]] = {}

    def add_rule(self, name: str, rule: Callable[[Any], bool]) -> None:
        """Add a validation rule.

        Args:
            name: Rule name (usually field name)
            rule: Validation function that returns True if valid
        """
        self.rules[name] = rule

    def validate(self, name: str, value: Any) -> bool:
        """Validate a value using a rule.

        Args:
            name: Rule name
            value: Value to validate

        Returns:
            True if valid, False otherwise
        """
        if name not in self.rules:
            return True

        try:
            return self.rules[name](value)
        except Exception:
            return False

    def validate_config(self, config: Dict[str, Any]) -> None:
        """Validate an entire configuration dictionary.

        Args:
            config: Configuration to validate

        Raises:
            ConfigurationException: If validation fails
        """
        errors = []

        for field, value in config.items():
            if field in self.rules:
                if not self.validate(field, value):
                    errors.append(f"{field}: validation failed for value {value}")

        if errors:
            raise ConfigurationException(
                f"Configuration validation failed: {'; '.join(errors)}",
                code="CONFIG_VALIDATION_FAILED",
                context={"errors": errors},
            )
