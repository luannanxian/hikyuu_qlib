"""Infrastructure errors module.

This module provides a comprehensive error handling system:
- Custom exception hierarchy
- Standardized error codes
- Exception handlers and formatters
"""
from .error_codes import ErrorCode, get_error_description, is_valid_error_code
from .exceptions import (
    BacktestException,
    BaseInfrastructureException,
    ConfigurationException,
    DataException,
    DataLoadException,
    DataValidationException,
    ModelException,
    ModelPredictionException,
    ModelTrainingException,
)
from .formatters import (
    format_error_as_json,
    format_error_for_developer,
    format_error_for_logging,
    format_error_for_user,
    format_error_response,
    format_error_with_suggestions,
    format_exception_chain,
    format_validation_errors,
)
from .handlers import (
    ChainedExceptionHandler,
    exception_handler,
    handle_exception,
    handle_exceptions,
)

__all__ = [
    # Exceptions
    "BaseInfrastructureException",
    "DataException",
    "DataLoadException",
    "DataValidationException",
    "ModelException",
    "ModelTrainingException",
    "ModelPredictionException",
    "BacktestException",
    "ConfigurationException",
    # Error codes
    "ErrorCode",
    "get_error_description",
    "is_valid_error_code",
    # Handlers
    "handle_exception",
    "exception_handler",
    "handle_exceptions",
    "ChainedExceptionHandler",
    # Formatters
    "format_error_for_user",
    "format_error_for_developer",
    "format_error_as_json",
    "format_validation_errors",
    "format_error_response",
    "format_error_with_suggestions",
    "format_exception_chain",
    "format_error_for_logging",
]
