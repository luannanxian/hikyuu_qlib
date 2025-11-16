"""Custom exception classes for infrastructure layer.

This module defines a hierarchy of custom exceptions for the application:
- BaseInfrastructureException: Root exception with context and error codes
- Domain-specific exceptions: Data, Model, Backtest, Configuration
- Specific exceptions for different error scenarios

All exceptions support:
- Error codes for programmatic error handling
- Context dictionaries for additional information
- Exception chaining for preserving the original error
- Timestamps for tracking when errors occurred
"""
from datetime import datetime
from typing import Any


class BaseInfrastructureException(Exception):
    """Base exception for all infrastructure-related errors.

    Attributes:
        message: Human-readable error message
        code: Machine-readable error code (e.g., 'DATA_001')
        context: Additional context information as a dictionary
        timestamp: When the error occurred
        original_exception: The original exception if this wraps another error
    """

    def __init__(
        self,
        message: str,
        code: str,
        context: dict[str, Any] | None = None,
        original_exception: Exception | None = None,
    ):
        """Initialize the exception.

        Args:
            message: Human-readable error message
            code: Machine-readable error code
            context: Additional context information
            original_exception: Original exception if wrapping another error
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.context = context or {}
        self.timestamp = datetime.now()
        self.original_exception = original_exception

        # Set the cause for exception chaining
        if original_exception:
            self.__cause__ = original_exception

    def __str__(self) -> str:
        """Return string representation of the exception."""
        return self.message

    def __repr__(self) -> str:
        """Return detailed string representation."""
        return (
            f"{self.__class__.__name__}("
            f"message='{self.message}', "
            f"code='{self.code}', "
            f"context={self.context})"
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for serialization.

        Returns:
            Dictionary with exception details
        """
        return {
            "exception_type": self.__class__.__name__,
            "message": self.message,
            "code": self.code,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
        }


class DataException(BaseInfrastructureException):
    """Base exception for data-related errors."""



class DataLoadException(DataException):
    """Exception raised when data loading fails."""



class DataValidationException(DataException):
    """Exception raised when data validation fails."""



class ModelException(BaseInfrastructureException):
    """Base exception for model-related errors."""



class ModelTrainingException(ModelException):
    """Exception raised when model training fails."""



class ModelPredictionException(ModelException):
    """Exception raised when model prediction fails."""



class BacktestException(BaseInfrastructureException):
    """Base exception for backtest-related errors."""



class ConfigurationException(BaseInfrastructureException):
    """Base exception for configuration-related errors."""

