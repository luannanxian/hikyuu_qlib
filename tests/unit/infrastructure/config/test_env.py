"""Tests for environment variable handling.

Tests environment variable utilities:
- Parse environment variables
- Convert types from string
- Handle prefixes
- Handle default values
"""
import os

import pytest


def test_get_env_variable():
    """Test getting environment variable."""
    from src.infrastructure.config.env import get_env

    os.environ["TEST_VAR"] = "test_value"

    try:
        value = get_env("TEST_VAR")
        assert value == "test_value"
    finally:
        del os.environ["TEST_VAR"]


def test_get_env_variable_with_default():
    """Test getting environment variable with default value."""
    from src.infrastructure.config.env import get_env

    value = get_env("NONEXISTENT_VAR", default="default_value")
    assert value == "default_value"


def test_get_env_variable_required():
    """Test getting required environment variable raises if missing."""
    from src.infrastructure.config.env import get_env
    from src.infrastructure.errors import ConfigurationException

    with pytest.raises(ConfigurationException):
        get_env("NONEXISTENT_VAR", required=True)


def test_get_env_as_int():
    """Test getting environment variable as integer."""
    from src.infrastructure.config.env import get_env_as_int

    os.environ["TEST_INT"] = "42"

    try:
        value = get_env_as_int("TEST_INT")
        assert value == 42
        assert isinstance(value, int)
    finally:
        del os.environ["TEST_INT"]


def test_get_env_as_int_invalid():
    """Test getting invalid integer raises error."""
    from src.infrastructure.config.env import get_env_as_int
    from src.infrastructure.errors import ConfigurationException

    os.environ["TEST_INT"] = "not_an_int"

    try:
        with pytest.raises(ConfigurationException):
            get_env_as_int("TEST_INT")
    finally:
        del os.environ["TEST_INT"]


def test_get_env_as_float():
    """Test getting environment variable as float."""
    from src.infrastructure.config.env import get_env_as_float

    os.environ["TEST_FLOAT"] = "3.14"

    try:
        value = get_env_as_float("TEST_FLOAT")
        assert value == 3.14
        assert isinstance(value, float)
    finally:
        del os.environ["TEST_FLOAT"]


def test_get_env_as_bool():
    """Test getting environment variable as boolean."""
    from src.infrastructure.config.env import get_env_as_bool

    # True values
    for true_val in ["true", "True", "TRUE", "1", "yes", "Yes"]:
        os.environ["TEST_BOOL"] = true_val
        try:
            assert get_env_as_bool("TEST_BOOL") is True
        finally:
            del os.environ["TEST_BOOL"]

    # False values
    for false_val in ["false", "False", "FALSE", "0", "no", "No"]:
        os.environ["TEST_BOOL"] = false_val
        try:
            assert get_env_as_bool("TEST_BOOL") is False
        finally:
            del os.environ["TEST_BOOL"]


def test_get_env_as_list():
    """Test getting environment variable as list."""
    from src.infrastructure.config.env import get_env_as_list

    os.environ["TEST_LIST"] = "item1,item2,item3"

    try:
        value = get_env_as_list("TEST_LIST")
        assert value == ["item1", "item2", "item3"]
        assert isinstance(value, list)
    finally:
        del os.environ["TEST_LIST"]


def test_get_env_as_list_with_custom_separator():
    """Test getting list with custom separator."""
    from src.infrastructure.config.env import get_env_as_list

    os.environ["TEST_LIST"] = "item1;item2;item3"

    try:
        value = get_env_as_list("TEST_LIST", separator=";")
        assert value == ["item1", "item2", "item3"]
    finally:
        del os.environ["TEST_LIST"]


def test_get_all_env_with_prefix():
    """Test getting all environment variables with prefix."""
    from src.infrastructure.config.env import get_all_env_with_prefix

    os.environ["APP_NAME"] = "Test App"
    os.environ["APP_VERSION"] = "1.0.0"
    os.environ["OTHER_VAR"] = "other"

    try:
        env_vars = get_all_env_with_prefix("APP_")

        assert "NAME" in env_vars
        assert "VERSION" in env_vars
        assert "OTHER_VAR" not in env_vars
        assert env_vars["NAME"] == "Test App"
    finally:
        del os.environ["APP_NAME"]
        del os.environ["APP_VERSION"]
        del os.environ["OTHER_VAR"]


def test_load_env_file():
    """Test loading environment variables from .env file."""
    from src.infrastructure.config.env import load_env_file
    import tempfile

    env_content = """
APP_NAME=Test App
APP_VERSION=1.0.0
LOG_LEVEL=DEBUG
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write(env_content)
        env_file = f.name

    try:
        load_env_file(env_file)

        assert os.environ.get("APP_NAME") == "Test App"
        assert os.environ.get("APP_VERSION") == "1.0.0"
        assert os.environ.get("LOG_LEVEL") == "DEBUG"
    finally:
        os.unlink(env_file)
        # Cleanup
        for key in ["APP_NAME", "APP_VERSION", "LOG_LEVEL"]:
            if key in os.environ:
                del os.environ[key]


def test_env_to_settings_dict():
    """Test converting environment variables to settings dictionary."""
    from src.infrastructure.config.env import env_to_settings_dict

    os.environ["APP_NAME"] = "Test App"
    os.environ["LOG_LEVEL"] = "INFO"
    os.environ["PORT"] = "8080"

    try:
        settings_dict = env_to_settings_dict(
            prefix="", keys=["APP_NAME", "LOG_LEVEL", "PORT"]
        )

        assert settings_dict["APP_NAME"] == "Test App"
        assert settings_dict["LOG_LEVEL"] == "INFO"
        assert settings_dict["PORT"] == "8080"
    finally:
        for key in ["APP_NAME", "LOG_LEVEL", "PORT"]:
            if key in os.environ:
                del os.environ[key]
