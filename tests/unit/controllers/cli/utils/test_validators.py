"""
Tests for CLI input validators.

Tests:
- Date validation
- Stock code validation
- File path validation
- Numeric validation
"""

from datetime import date

import pytest

from controllers.cli.utils.validators import (
    validate_date,
    validate_file_path,
    validate_positive_float,
    validate_rate,
    validate_stock_code,
)


class TestDateValidation:
    """Test date validation."""

    def test_valid_date_format(self):
        """Test valid date format."""
        # Arrange
        date_str = "2023-01-15"

        # Act
        result = validate_date(date_str)

        # Assert
        assert result == date(2023, 1, 15)

    def test_invalid_date_format(self):
        """Test invalid date format."""
        # Arrange
        date_str = "2023/01/15"

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid date format"):
            validate_date(date_str)

    def test_invalid_date_value(self):
        """Test invalid date value."""
        # Arrange
        date_str = "2023-13-32"

        # Act & Assert
        with pytest.raises(ValueError):
            validate_date(date_str)


class TestStockCodeValidation:
    """Test stock code validation."""

    def test_valid_sh_stock_code(self):
        """Test valid Shanghai stock code."""
        # Arrange
        code = "sh600000"

        # Act
        result = validate_stock_code(code)

        # Assert
        assert result == "sh600000"

    def test_valid_sz_stock_code(self):
        """Test valid Shenzhen stock code."""
        # Arrange
        code = "sz000001"

        # Act
        result = validate_stock_code(code)

        # Assert
        assert result == "sz000001"

    def test_uppercase_stock_code(self):
        """Test uppercase stock code is converted to lowercase."""
        # Arrange
        code = "SH600000"

        # Act
        result = validate_stock_code(code)

        # Assert
        assert result == "sh600000"

    def test_invalid_stock_code_format(self):
        """Test invalid stock code format."""
        # Arrange
        code = "invalid"

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid stock code format"):
            validate_stock_code(code)

    def test_invalid_market_prefix(self):
        """Test invalid market prefix."""
        # Arrange
        code = "bj000001"

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid stock code format"):
            validate_stock_code(code)


class TestFilePathValidation:
    """Test file path validation."""

    def test_valid_file_path(self, tmp_path):
        """Test valid file path."""
        # Arrange
        file_path = tmp_path / "test.txt"
        file_path.write_text("test")

        # Act
        result = validate_file_path(str(file_path))

        # Assert
        assert result == str(file_path)

    def test_nonexistent_file_path(self, tmp_path):
        """Test nonexistent file path."""
        # Arrange
        file_path = tmp_path / "nonexistent.txt"

        # Act & Assert
        with pytest.raises(ValueError, match="File not found"):
            validate_file_path(str(file_path))

    def test_directory_path(self, tmp_path):
        """Test directory path."""
        # Arrange
        dir_path = tmp_path

        # Act & Assert
        with pytest.raises(ValueError, match="is not a file"):
            validate_file_path(str(dir_path))


class TestPositiveFloatValidation:
    """Test positive float validation."""

    def test_valid_positive_float(self):
        """Test valid positive float."""
        # Arrange
        value = "100.5"

        # Act
        result = validate_positive_float(value)

        # Assert
        assert result == 100.5

    def test_zero_value(self):
        """Test zero value."""
        # Arrange
        value = "0"

        # Act & Assert
        with pytest.raises(ValueError, match="must be positive"):
            validate_positive_float(value)

    def test_negative_value(self):
        """Test negative value."""
        # Arrange
        value = "-10.5"

        # Act & Assert
        with pytest.raises(ValueError, match="must be positive"):
            validate_positive_float(value)

    def test_invalid_float_format(self):
        """Test invalid float format."""
        # Arrange
        value = "not_a_number"

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid number format"):
            validate_positive_float(value)


class TestRateValidation:
    """Test rate validation."""

    def test_valid_rate(self):
        """Test valid rate."""
        # Arrange
        value = "0.0003"

        # Act
        result = validate_rate(value)

        # Assert
        assert result == 0.0003

    def test_rate_at_zero(self):
        """Test rate at zero."""
        # Arrange
        value = "0"

        # Act
        result = validate_rate(value)

        # Assert
        assert result == 0.0

    def test_rate_at_one(self):
        """Test rate at one."""
        # Arrange
        value = "1"

        # Act
        result = validate_rate(value)

        # Assert
        assert result == 1.0

    def test_rate_above_one(self):
        """Test rate above one."""
        # Arrange
        value = "1.5"

        # Act & Assert
        with pytest.raises(ValueError, match="must be between 0 and 1"):
            validate_rate(value)

    def test_negative_rate(self):
        """Test negative rate."""
        # Arrange
        value = "-0.5"

        # Act & Assert
        with pytest.raises(ValueError, match="must be between 0 and 1"):
            validate_rate(value)
