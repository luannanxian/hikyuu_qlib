"""Tests for configuration loader.

Tests configuration loading from different sources:
- Load from files (.env, yaml, json)
- Load with environment overrides
- Load from multiple sources with priority
- Configuration caching
"""
import os
import tempfile

import pytest


def test_load_config_from_env_file():
    """Test loading configuration from .env file."""
    from src.infrastructure.config.loader import load_config_from_file

    # Create a temporary .env file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("APP_NAME=Test App\n")
        f.write("ENVIRONMENT=test\n")
        f.write("LOG_LEVEL=DEBUG\n")
        env_file = f.name

    try:
        config = load_config_from_file(env_file)
        assert "APP_NAME" in config
        assert config["APP_NAME"] == "Test App"
    finally:
        os.unlink(env_file)


def test_load_config_from_yaml_file():
    """Test loading configuration from YAML file."""
    from src.infrastructure.config.loader import load_config_from_file

    yaml_content = """
app_name: Test App
environment: test
log_level: DEBUG
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        yaml_file = f.name

    try:
        config = load_config_from_file(yaml_file)
        assert "app_name" in config
        assert config["app_name"] == "Test App"
    finally:
        os.unlink(yaml_file)


def test_load_config_from_json_file():
    """Test loading configuration from JSON file."""
    from src.infrastructure.config.loader import load_config_from_file
    import json

    config_data = {"app_name": "Test App", "environment": "test"}

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config_data, f)
        json_file = f.name

    try:
        config = load_config_from_file(json_file)
        assert config["app_name"] == "Test App"
    finally:
        os.unlink(json_file)


def test_load_config_with_nonexistent_file():
    """Test loading configuration from nonexistent file."""
    from src.infrastructure.config.loader import load_config_from_file

    with pytest.raises(FileNotFoundError):
        load_config_from_file("nonexistent.env")


def test_load_config_with_invalid_format():
    """Test loading configuration with invalid format."""
    from src.infrastructure.config.loader import load_config_from_file

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("invalid content")
        txt_file = f.name

    try:
        with pytest.raises(ValueError):
            load_config_from_file(txt_file)
    finally:
        os.unlink(txt_file)


def test_get_config_loader():
    """Test getting configuration loader singleton."""
    from src.infrastructure.config.loader import get_config_loader

    loader1 = get_config_loader()
    loader2 = get_config_loader()

    assert loader1 is loader2


def test_config_loader_load_from_env():
    """Test ConfigLoader loading from environment variables."""
    from src.infrastructure.config.loader import ConfigLoader

    loader = ConfigLoader()

    # Set environment variables
    os.environ["TEST_VAR"] = "test_value"

    config = loader.load_from_env(prefix="TEST_")

    assert "VAR" in config
    assert config["VAR"] == "test_value"

    # Cleanup
    del os.environ["TEST_VAR"]


def test_config_loader_merge_configs():
    """Test merging multiple configurations."""
    from src.infrastructure.config.loader import ConfigLoader

    loader = ConfigLoader()

    config1 = {"key1": "value1", "key2": "value2"}
    config2 = {"key2": "new_value2", "key3": "value3"}

    merged = loader.merge_configs([config1, config2])

    assert merged["key1"] == "value1"
    assert merged["key2"] == "new_value2"  # Later config overrides
    assert merged["key3"] == "value3"


def test_config_loader_with_environment_override():
    """Test configuration loading with environment variable override."""
    from src.infrastructure.config.loader import ConfigLoader

    loader = ConfigLoader()

    base_config = {"key1": "value1", "key2": "value2"}

    os.environ["KEY1"] = "overridden"

    try:
        final_config = loader.load_with_overrides(base_config, prefix="")
        assert final_config["KEY1"] == "overridden"
    finally:
        del os.environ["KEY1"]


def test_config_loader_cache():
    """Test configuration caching."""
    from src.infrastructure.config.loader import ConfigLoader

    loader = ConfigLoader(enable_cache=True)

    # Load config first time
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("KEY=value\n")
        env_file = f.name

    try:
        config1 = loader.load_config(env_file)
        config2 = loader.load_config(env_file)

        # Should return cached config
        assert config1 is config2
    finally:
        os.unlink(env_file)
