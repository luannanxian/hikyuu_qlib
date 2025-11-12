"""Tests for configuration settings.

Tests the settings classes and validation:
- Application settings with defaults
- Environment-specific configuration
- Pydantic validation
- Settings hierarchy (data, model, backtest, logging, database)
"""

import pytest


def test_settings_creation_with_defaults():
    """Test creating settings with default values."""
    from src.infrastructure.config.settings import Settings

    settings = Settings()

    assert settings.APP_NAME == "Hikyuu-Qlib Trading Platform"
    assert settings.APP_VERSION is not None
    assert settings.ENVIRONMENT in ["dev", "test", "prod"]


def test_settings_validation():
    """Test settings validation with pydantic."""
    from src.infrastructure.config.settings import Settings
    from pydantic import ValidationError

    # Test with invalid log level
    with pytest.raises(ValidationError):
        Settings(LOG_LEVEL="INVALID_LEVEL")


def test_data_source_settings():
    """Test data source configuration."""
    from src.infrastructure.config.settings import DataSourceSettings

    data_settings = DataSourceSettings(
        HIKYUU_DATA_PATH="/path/to/hikyuu",
        QLIB_DATA_PATH="/path/to/qlib",
    )

    assert data_settings.HIKYUU_DATA_PATH == "/path/to/hikyuu"
    assert data_settings.QLIB_DATA_PATH == "/path/to/qlib"


def test_model_settings():
    """Test model configuration."""
    from src.infrastructure.config.settings import ModelSettings

    model_settings = ModelSettings(
        MODEL_STORAGE_PATH="/path/to/models",
        DEFAULT_MODEL_TYPE="LightGBM",
    )

    assert model_settings.MODEL_STORAGE_PATH == "/path/to/models"
    assert model_settings.DEFAULT_MODEL_TYPE == "LightGBM"


def test_backtest_settings():
    """Test backtest configuration."""
    from src.infrastructure.config.settings import BacktestSettings

    backtest_settings = BacktestSettings(
        INITIAL_CAPITAL=100000.0,
        COMMISSION_RATE=0.0003,
    )

    assert backtest_settings.INITIAL_CAPITAL == 100000.0
    assert backtest_settings.COMMISSION_RATE == 0.0003


def test_logging_settings():
    """Test logging configuration."""
    from src.infrastructure.config.settings import LoggingSettings

    logging_settings = LoggingSettings(
        LOG_LEVEL="INFO",
        LOG_FORMAT="json",
        LOG_FILE_PATH="/var/log/app.log",
    )

    assert logging_settings.LOG_LEVEL == "INFO"
    assert logging_settings.LOG_FORMAT == "json"
    assert logging_settings.LOG_FILE_PATH == "/var/log/app.log"


def test_database_settings():
    """Test database configuration."""
    from src.infrastructure.config.settings import DatabaseSettings

    db_settings = DatabaseSettings(
        DATABASE_URL="sqlite:///./test.db",
        DATABASE_ECHO=False,
    )

    assert db_settings.DATABASE_URL == "sqlite:///./test.db"
    assert db_settings.DATABASE_ECHO is False


def test_complete_settings_with_all_subsections():
    """Test complete settings with all subsections."""
    from src.infrastructure.config.settings import Settings

    settings = Settings(
        ENVIRONMENT="test",
        HIKYUU_DATA_PATH="/path/to/hikyuu",
        QLIB_DATA_PATH="/path/to/qlib",
        MODEL_STORAGE_PATH="/path/to/models",
        INITIAL_CAPITAL=200000.0,
    )

    assert settings.ENVIRONMENT == "test"
    assert settings.HIKYUU_DATA_PATH == "/path/to/hikyuu"
    assert settings.QLIB_DATA_PATH == "/path/to/qlib"


def test_settings_from_env_variables(monkeypatch):
    """Test loading settings from environment variables."""
    from src.infrastructure.config.settings import Settings

    monkeypatch.setenv("APP_NAME", "Test App")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    settings = Settings()

    assert settings.APP_NAME == "Test App"
    assert settings.ENVIRONMENT == "test"
    assert settings.LOG_LEVEL == "DEBUG"


def test_settings_log_level_validation():
    """Test log level validation."""
    from src.infrastructure.config.settings import Settings
    from pydantic import ValidationError

    # Valid log levels
    for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        settings = Settings(LOG_LEVEL=level)
        assert settings.LOG_LEVEL == level

    # Invalid log level
    with pytest.raises(ValidationError):
        Settings(LOG_LEVEL="INVALID")


def test_settings_environment_validation():
    """Test environment validation."""
    from src.infrastructure.config.settings import Settings
    from pydantic import ValidationError

    # Valid environments
    for env in ["dev", "test", "prod"]:
        settings = Settings(ENVIRONMENT=env)
        assert settings.ENVIRONMENT == env

    # Invalid environment
    with pytest.raises(ValidationError):
        Settings(ENVIRONMENT="invalid")


def test_settings_immutability():
    """Test that settings are immutable after creation."""
    from src.infrastructure.config.settings import Settings

    settings = Settings()

    # Should not be able to modify settings
    with pytest.raises(Exception):  # Pydantic raises ValidationError or AttributeError
        settings.APP_NAME = "New Name"


def test_settings_export_to_dict():
    """Test exporting settings to dictionary."""
    from src.infrastructure.config.settings import Settings

    settings = Settings(
        APP_NAME="Test App",
        ENVIRONMENT="test",
    )

    settings_dict = settings.model_dump()

    assert settings_dict["APP_NAME"] == "Test App"
    assert settings_dict["ENVIRONMENT"] == "test"
