"""Error formatters for different output formats.

This module provides functions to format errors for different audiences:
- User-friendly messages for end users
- Detailed technical information for developers
- JSON format for API responses
- Log format for logging systems
"""
import json
from typing import Any

from .error_codes import get_error_description
from .exceptions import BaseInfrastructureException


def format_error_for_user(exception: BaseInfrastructureException) -> str:
    """Format error message for end users.

    Provides a user-friendly error message without technical details.

    Args:
        exception: The exception to format

    Returns:
        User-friendly error message
    """
    base_message = exception.message

    # For data errors, provide helpful context
    if "stock_code" in exception.context:
        if "load" in base_message.lower():
            return "Unable to load stock data. Please try again."
        elif "validation" in base_message.lower():
            return "The stock data contains invalid values. Please check your data."

    # For model errors
    if "model" in base_message.lower():
        if "training" in base_message.lower():
            return (
                "Model training encountered an error. Please check your configuration."
            )
        elif "prediction" in base_message.lower():
            return "Unable to generate predictions. Please try again."

    # For configuration errors
    if "config" in base_message.lower():
        return "Configuration error detected. Please check your settings."

    # Default: return the base message
    return base_message


def format_error_for_developer(
    exception: BaseInfrastructureException,
) -> dict[str, Any]:
    """Format error with full technical details for developers.

    Args:
        exception: The exception to format

    Returns:
        Dictionary with complete error information
    """
    return {
        "exception_type": exception.__class__.__name__,
        "message": exception.message,
        "code": exception.code,
        "context": exception.context,
        "timestamp": exception.timestamp.isoformat(),
        "description": get_error_description(exception.code),
    }


def format_error_as_json(exception: BaseInfrastructureException) -> str:
    """Format error as JSON string.

    Args:
        exception: The exception to format

    Returns:
        JSON string representation
    """
    return json.dumps(exception.to_dict(), default=str)


def format_validation_errors(errors: list[dict[str, str]]) -> str:
    """Format multiple validation errors.

    Args:
        errors: List of validation error dictionaries

    Returns:
        Formatted error message
    """
    if not errors:
        return "No validation errors"

    lines = ["Validation errors:"]
    for error in errors:
        field = error.get("field", "unknown")
        message = error.get("message", "validation failed")
        lines.append(f"  - {field}: {message}")

    return "\n".join(lines)


def format_error_response(
    exception: BaseInfrastructureException,
) -> dict[str, Any]:
    """Format error as HTTP API response.

    Args:
        exception: The exception to format

    Returns:
        Dictionary suitable for HTTP response
    """
    # Determine HTTP status code based on error type
    status_code = 500  # Default to internal server error

    if hasattr(exception, "__class__"):
        class_name = exception.__class__.__name__
        if "NotFound" in class_name or "DATA_NOT_FOUND" in exception.code:
            status_code = 404
        elif "Validation" in class_name or "VALIDATION" in exception.code:
            status_code = 400
        elif "Configuration" in class_name:
            status_code = 500

    return {
        "error": {
            "code": exception.code,
            "message": format_error_for_user(exception),
            "details": exception.context,
        },
        "status_code": status_code,
    }


def format_error_with_suggestions(
    exception: BaseInfrastructureException,
) -> dict[str, Any]:
    """Format error with helpful suggestions.

    Args:
        exception: The exception to format

    Returns:
        Dictionary with error and suggestions
    """
    suggestions = []

    # Generate suggestions based on error type
    if "DATA_LOAD_FAILED" in exception.code:
        suggestions.append("Check that the data source is accessible")
        suggestions.append("Verify the data path configuration")
    elif "DATA_VALIDATION_FAILED" in exception.code:
        suggestions.append("Check the data format and schema")
        suggestions.append("Ensure all required fields are present")
    elif "MODEL_TRAINING_FAILED" in exception.code:
        suggestions.append("Check model hyperparameters")
        suggestions.append("Ensure sufficient training data is available")
    elif "CONFIG_INVALID" in exception.code:
        suggestions.append("Review the configuration file syntax")
        suggestions.append("Check for missing required configuration values")
    elif "config_key" in exception.context:
        config_key = exception.context["config_key"]
        suggestions.append(f"Check the '{config_key}' configuration value")
        suggestions.append("Refer to the configuration documentation")

    return {
        "message": exception.message,
        "code": exception.code,
        "suggestions": suggestions,
        "context": exception.context,
    }


def format_exception_chain(
    exception: BaseInfrastructureException,
) -> list[dict[str, Any]]:
    """Format the exception chain (exception and all causes).

    Args:
        exception: The exception to format

    Returns:
        List of exception dictionaries, from most recent to original
    """
    chain = []
    current = exception

    # Add the main exception
    chain.append(
        {
            "exception_type": current.__class__.__name__,
            "message": current.message,
            "code": current.code,
        },
    )

    # Add original exception if present
    if hasattr(current, "original_exception") and current.original_exception:
        original = current.original_exception
        chain.append(
            {
                "exception_type": original.__class__.__name__,
                "message": str(original),
                "code": getattr(original, "code", "N/A"),
            },
        )

    return chain


def format_error_for_logging(exception: BaseInfrastructureException) -> dict[str, Any]:
    """Format error for structured logging.

    Args:
        exception: The exception to format

    Returns:
        Dictionary with logging-friendly format
    """
    return {
        "error_type": exception.__class__.__name__,
        "error_code": exception.code,
        "error_message": exception.message,
        "context": exception.context,
        "timestamp": exception.timestamp.isoformat(),
    }
