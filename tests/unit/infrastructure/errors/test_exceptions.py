"""Tests for custom exceptions.

Tests the exception hierarchy and functionality:
- Base exception with context and error codes
- Domain-specific exceptions (Data, Model, Backtest, Config)
- Exception chaining and context preservation
"""


def test_base_infrastructure_exception_creation():
    """Test creating base infrastructure exception with message and code."""
    from src.infrastructure.errors.exceptions import BaseInfrastructureException

    exc = BaseInfrastructureException(message="Test error", code="TEST_001")

    assert str(exc) == "Test error"
    assert exc.code == "TEST_001"
    assert exc.context == {}
    assert exc.timestamp is not None


def test_base_infrastructure_exception_with_context():
    """Test exception with additional context information."""
    from src.infrastructure.errors.exceptions import BaseInfrastructureException

    context = {"stock_code": "000001", "date": "2024-01-01"}
    exc = BaseInfrastructureException(
        message="Test error", code="TEST_002", context=context,
    )

    assert exc.context == context
    assert exc.context["stock_code"] == "000001"


def test_base_infrastructure_exception_chaining():
    """Test exception chaining with original exception."""
    from src.infrastructure.errors.exceptions import BaseInfrastructureException

    original = ValueError("Original error")
    exc = BaseInfrastructureException(
        message="Wrapped error", code="TEST_003", original_exception=original,
    )

    assert exc.original_exception is original
    assert exc.__cause__ is original


def test_data_exception_creation():
    """Test creating data-specific exception."""
    from src.infrastructure.errors.exceptions import DataException

    exc = DataException(message="Data error", code="DATA_001")

    assert isinstance(exc, DataException)
    assert str(exc) == "Data error"
    assert exc.code == "DATA_001"


def test_data_load_exception():
    """Test data loading exception."""
    from src.infrastructure.errors.exceptions import DataLoadException

    exc = DataLoadException(
        message="Failed to load stock data",
        code="DATA_001",
        context={"stock_code": "000001", "source": "hikyuu"},
    )

    assert isinstance(exc, DataLoadException)
    assert exc.context["stock_code"] == "000001"
    assert exc.context["source"] == "hikyuu"


def test_data_validation_exception():
    """Test data validation exception."""
    from src.infrastructure.errors.exceptions import DataValidationException

    exc = DataValidationException(
        message="Invalid data format",
        code="DATA_002",
        context={"field": "close_price", "value": -100},
    )

    assert isinstance(exc, DataValidationException)
    assert exc.context["field"] == "close_price"


def test_model_exception_creation():
    """Test creating model-specific exception."""
    from src.infrastructure.errors.exceptions import ModelException

    exc = ModelException(message="Model error", code="MODEL_001")

    assert isinstance(exc, ModelException)
    assert str(exc) == "Model error"


def test_model_training_exception():
    """Test model training exception."""
    from src.infrastructure.errors.exceptions import ModelTrainingException

    exc = ModelTrainingException(
        message="Training failed",
        code="MODEL_001",
        context={"model_name": "LightGBM", "epoch": 10},
    )

    assert isinstance(exc, ModelTrainingException)
    assert exc.context["model_name"] == "LightGBM"


def test_model_prediction_exception():
    """Test model prediction exception."""
    from src.infrastructure.errors.exceptions import ModelPredictionException

    exc = ModelPredictionException(
        message="Prediction failed", code="MODEL_002", context={"model_id": "model_123"},
    )

    assert isinstance(exc, ModelPredictionException)
    assert exc.context["model_id"] == "model_123"


def test_backtest_exception_creation():
    """Test creating backtest-specific exception."""
    from src.infrastructure.errors.exceptions import BacktestException

    exc = BacktestException(message="Backtest error", code="BACKTEST_001")

    assert isinstance(exc, BacktestException)
    assert str(exc) == "Backtest error"


def test_configuration_exception_creation():
    """Test creating configuration-specific exception."""
    from src.infrastructure.errors.exceptions import ConfigurationException

    exc = ConfigurationException(
        message="Invalid configuration",
        code="CONFIG_001",
        context={"config_key": "data_path"},
    )

    assert isinstance(exc, ConfigurationException)
    assert exc.context["config_key"] == "data_path"


def test_exception_repr():
    """Test exception string representation."""
    from src.infrastructure.errors.exceptions import DataException

    exc = DataException(message="Test error", code="DATA_001", context={"key": "value"})

    repr_str = repr(exc)
    assert "DataException" in repr_str
    assert "DATA_001" in repr_str


def test_exception_to_dict():
    """Test converting exception to dictionary."""
    from src.infrastructure.errors.exceptions import DataException

    exc = DataException(message="Test error", code="DATA_001", context={"key": "value"})

    exc_dict = exc.to_dict()
    assert exc_dict["message"] == "Test error"
    assert exc_dict["code"] == "DATA_001"
    assert exc_dict["context"] == {"key": "value"}
    assert "timestamp" in exc_dict
    assert exc_dict["exception_type"] == "DataException"


def test_exception_hierarchy():
    """Test exception class hierarchy."""
    from src.infrastructure.errors.exceptions import (
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

    # Test inheritance
    assert issubclass(DataException, BaseInfrastructureException)
    assert issubclass(DataLoadException, DataException)
    assert issubclass(DataValidationException, DataException)
    assert issubclass(ModelException, BaseInfrastructureException)
    assert issubclass(ModelTrainingException, ModelException)
    assert issubclass(ModelPredictionException, ModelException)
    assert issubclass(BacktestException, BaseInfrastructureException)
    assert issubclass(ConfigurationException, BaseInfrastructureException)
