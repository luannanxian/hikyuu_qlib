"""Configuration settings using Pydantic.

This module defines application settings using Pydantic BaseSettings:
- Type-safe configuration
- Environment variable support
- Validation rules
- Immutable after creation
"""
from enum import Enum
from typing import Literal, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings as PydanticBaseSettings


class LogLevel(str, Enum):
    """Valid log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Environment(str, Enum):
    """Valid environments."""

    DEV = "dev"
    TEST = "test"
    PROD = "prod"


class DataSourceSettings(PydanticBaseSettings):
    """Data source configuration."""

    HIKYUU_DATA_PATH: str = Field(
        default="./data/hikyuu", description="Hikyuu data path"
    )
    QLIB_DATA_PATH: str = Field(default="./data/qlib", description="Qlib data path")

    model_config = {"frozen": True}


class ModelSettings(PydanticBaseSettings):
    """Model configuration."""

    MODEL_STORAGE_PATH: str = Field(
        default="./models", description="Path to store trained models"
    )
    DEFAULT_MODEL_TYPE: str = Field(
        default="LightGBM", description="Default model type"
    )

    model_config = {"frozen": True}


class BacktestSettings(PydanticBaseSettings):
    """Backtest configuration."""

    INITIAL_CAPITAL: float = Field(
        default=100000.0, description="Initial capital for backtest"
    )
    COMMISSION_RATE: float = Field(
        default=0.0003, description="Commission rate (0.03%)"
    )

    @field_validator("INITIAL_CAPITAL")
    @classmethod
    def validate_initial_capital(cls, v):
        """Validate initial capital is positive."""
        if v <= 0:
            raise ValueError("Initial capital must be positive")
        return v

    @field_validator("COMMISSION_RATE")
    @classmethod
    def validate_commission_rate(cls, v):
        """Validate commission rate is between 0 and 1."""
        if v < 0 or v > 1:
            raise ValueError("Commission rate must be between 0 and 1")
        return v

    model_config = {"frozen": True}


class LoggingSettings(PydanticBaseSettings):
    """Logging configuration."""

    LOG_LEVEL: LogLevel = Field(default=LogLevel.INFO, description="Logging level")
    LOG_FORMAT: Literal["json", "text"] = Field(
        default="json", description="Log format"
    )
    LOG_FILE_PATH: Optional[str] = Field(default=None, description="Path to log file")

    model_config = {"frozen": True}


class DatabaseSettings(PydanticBaseSettings):
    """Database configuration."""

    DATABASE_URL: str = Field(
        default="sqlite:///./app.db", description="Database connection URL"
    )
    DATABASE_ECHO: bool = Field(default=False, description="Echo SQL statements")

    model_config = {"frozen": True}


class Settings(PydanticBaseSettings):
    """Main application settings.

    All settings can be overridden by environment variables.
    """

    # Application settings
    APP_NAME: str = Field(
        default="Hikyuu-Qlib Trading Platform",
        description="Application name",
    )
    APP_VERSION: str = Field(default="0.1.0", description="Application version")
    ENVIRONMENT: Environment = Field(default=Environment.DEV, description="Environment")

    # Logging settings
    LOG_LEVEL: LogLevel = Field(default=LogLevel.INFO, description="Logging level")
    LOG_FORMAT: Literal["json", "text"] = Field(
        default="json", description="Log format"
    )
    LOG_FILE_PATH: Optional[str] = Field(default=None, description="Path to log file")

    # Data source settings
    HIKYUU_DATA_PATH: str = Field(
        default="./data/hikyuu", description="Hikyuu data path"
    )
    HIKYUU_CONFIG_FILE: str = Field(
        default="./config/hikyuu.ini", description="Hikyuu configuration file path"
    )
    QLIB_DATA_PATH: str = Field(default="./data/qlib", description="Qlib data path")

    # Model settings
    MODEL_STORAGE_PATH: str = Field(
        default="./models", description="Path to store trained models"
    )
    DEFAULT_MODEL_TYPE: str = Field(
        default="LightGBM", description="Default model type"
    )

    # Backtest settings
    INITIAL_CAPITAL: float = Field(
        default=100000.0, description="Initial capital for backtest"
    )
    COMMISSION_RATE: float = Field(
        default=0.0003, description="Commission rate (0.03%)"
    )

    # Database settings
    DATABASE_URL: str = Field(
        default="sqlite:///./app.db", description="Database connection URL"
    )
    DATABASE_ECHO: bool = Field(default=False, description="Echo SQL statements")

    @field_validator("LOG_LEVEL", mode="before")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        if isinstance(v, str):
            valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            if v not in valid_levels:
                raise ValueError(
                    f"Invalid log level: {v}. Must be one of {valid_levels}"
                )
        return v

    @field_validator("ENVIRONMENT", mode="before")
    @classmethod
    def validate_environment(cls, v):
        """Validate environment."""
        if isinstance(v, str):
            valid_envs = ["dev", "test", "prod"]
            if v not in valid_envs:
                raise ValueError(
                    f"Invalid environment: {v}. Must be one of {valid_envs}"
                )
        return v

    @field_validator("INITIAL_CAPITAL")
    @classmethod
    def validate_initial_capital(cls, v):
        """Validate initial capital is positive."""
        if v <= 0:
            raise ValueError("Initial capital must be positive")
        return v

    @field_validator("COMMISSION_RATE")
    @classmethod
    def validate_commission_rate(cls, v):
        """Validate commission rate is between 0 and 1."""
        if v < 0 or v > 1:
            raise ValueError("Commission rate must be between 0 and 1")
        return v

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "frozen": True,
    }
