"""Tests for configuration validator.

Tests configuration validation:
- Validate required fields
- Validate field types and formats
- Validate value ranges
- Custom validation rules
"""
import pytest


def test_validate_required_fields():
    """Test validating required configuration fields."""
    from src.infrastructure.config.validator import validate_required_fields

    config = {"field1": "value1", "field2": "value2"}
    required = ["field1", "field2"]

    # Should not raise
    validate_required_fields(config, required)


def test_validate_required_fields_missing():
    """Test validation fails when required fields are missing."""
    from src.infrastructure.config.validator import validate_required_fields
    from src.infrastructure.errors import ConfigurationException

    config = {"field1": "value1"}
    required = ["field1", "field2"]

    with pytest.raises(ConfigurationException):
        validate_required_fields(config, required)


def test_validate_field_type():
    """Test validating field types."""
    from src.infrastructure.config.validator import validate_field_type

    # Valid types
    assert validate_field_type("test", str) is True
    assert validate_field_type(123, int) is True
    assert validate_field_type(123.45, float) is True
    assert validate_field_type(True, bool) is True

    # Invalid types
    assert validate_field_type("test", int) is False
    assert validate_field_type(123, str) is False


def test_validate_config_types():
    """Test validating all config field types."""
    from src.infrastructure.config.validator import validate_config_types

    config = {"port": 8080, "host": "localhost", "debug": True}

    type_specs = {"port": int, "host": str, "debug": bool}

    # Should not raise
    validate_config_types(config, type_specs)


def test_validate_config_types_invalid():
    """Test validation fails for invalid types."""
    from src.infrastructure.config.validator import validate_config_types
    from src.infrastructure.errors import ConfigurationException

    config = {"port": "8080"}  # Should be int
    type_specs = {"port": int}

    with pytest.raises(ConfigurationException):
        validate_config_types(config, type_specs)


def test_validate_path_exists():
    """Test validating that paths exist."""
    import os
    import tempfile

    from src.infrastructure.config.validator import validate_path_exists

    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False) as f:
        temp_file = f.name

    try:
        # Should not raise for existing path
        validate_path_exists(temp_file)
    finally:
        os.unlink(temp_file)


def test_validate_path_exists_nonexistent():
    """Test validation fails for nonexistent paths."""
    from src.infrastructure.config.validator import validate_path_exists
    from src.infrastructure.errors import ConfigurationException

    with pytest.raises(ConfigurationException):
        validate_path_exists("/nonexistent/path")


def test_validate_value_range():
    """Test validating values within range."""
    from src.infrastructure.config.validator import validate_value_range

    # Valid ranges
    assert validate_value_range(5, 1, 10) is True
    assert validate_value_range(1, 1, 10) is True
    assert validate_value_range(10, 1, 10) is True

    # Invalid ranges
    assert validate_value_range(0, 1, 10) is False
    assert validate_value_range(11, 1, 10) is False


def test_validate_enum_value():
    """Test validating enum values."""
    from src.infrastructure.config.validator import validate_enum_value

    valid_values = ["dev", "test", "prod"]

    assert validate_enum_value("dev", valid_values) is True
    assert validate_enum_value("test", valid_values) is True
    assert validate_enum_value("invalid", valid_values) is False


def test_validate_url_format():
    """Test validating URL format."""
    from src.infrastructure.config.validator import validate_url_format

    # Valid URLs
    assert validate_url_format("http://localhost:8080") is True
    assert validate_url_format("https://example.com") is True
    assert validate_url_format("sqlite:///./test.db") is True

    # Invalid URLs
    assert validate_url_format("not a url") is False
    assert validate_url_format("") is False


def test_validate_settings_object():
    """Test validating a Settings object."""
    from src.infrastructure.config.settings import Settings
    from src.infrastructure.config.validator import validate_settings

    settings = Settings(
        ENVIRONMENT="test",
        LOG_LEVEL="INFO",
    )

    # Should not raise
    validate_settings(settings)


def test_custom_validator():
    """Test custom validation function."""
    from src.infrastructure.config.validator import ConfigValidator

    def custom_rule(value):
        return value > 0

    validator = ConfigValidator()
    validator.add_rule("positive_number", custom_rule)

    assert validator.validate("positive_number", 10) is True
    assert validator.validate("positive_number", -10) is False


def test_config_validator_with_multiple_rules():
    """Test validator with multiple rules."""
    from src.infrastructure.config.validator import ConfigValidator

    validator = ConfigValidator()

    config = {"port": 8080, "host": "localhost", "workers": 4}

    # Add rules
    validator.add_rule("port", lambda x: 1 <= x <= 65535)
    validator.add_rule("host", lambda x: isinstance(x, str) and len(x) > 0)
    validator.add_rule("workers", lambda x: x > 0)

    # Should not raise
    validator.validate_config(config)
