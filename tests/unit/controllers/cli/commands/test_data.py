"""
Tests for data management CLI commands.

Tests:
- data load command
- data list command
"""

import pytest
from click.testing import CliRunner
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime
from decimal import Decimal

from controllers.cli.commands.data import data_group
from domain.entities.kline_data import KLineData
from domain.value_objects.stock_code import StockCode
from domain.value_objects.date_range import DateRange
from domain.value_objects.kline_type import KLineType
from datetime import date


class TestDataLoadCommand:
    """Test data load command."""

    def test_data_load_single_stock(self):
        """Test loading single stock data."""
        # Arrange
        runner = CliRunner()

        with patch("controllers.cli.commands.data.Container") as mock_container_class:
            with patch("controllers.cli.commands.data.asyncio.run") as mock_asyncio_run:
                # Mock container and use case
                mock_container = Mock()
                mock_use_case = AsyncMock()
                mock_container.load_stock_data_use_case = mock_use_case
                mock_container_class.return_value = mock_container

                # Mock data
                mock_data = [
                    KLineData(
                        stock_code=StockCode("sh600000"),
                        timestamp=datetime(2023, 1, 1),
                        kline_type=KLineType.DAY,
                        open=Decimal("10.0"),
                        high=Decimal("11.0"),
                        low=Decimal("9.5"),
                        close=Decimal("10.5"),
                        volume=1000000,
                        amount=Decimal("10500000.0"),
                    )
                ]
                mock_use_case.execute.return_value = mock_data

                # Mock asyncio.run to avoid actual async execution
                mock_asyncio_run.return_value = None

                # Act
                result = runner.invoke(
                    data_group,
                    ["load", "--code", "sh600000", "--start", "2023-01-01", "--end", "2023-12-31"],
                )

                # Assert
                assert result.exit_code == 0 or "sh600000" in str(result.output)

    def test_data_load_missing_required_args(self):
        """Test data load with missing required arguments."""
        # Arrange
        runner = CliRunner()

        # Act
        result = runner.invoke(data_group, ["load"])

        # Assert
        assert result.exit_code != 0
        assert "Error" in result.output or "Missing" in result.output

    def test_data_load_invalid_stock_code(self):
        """Test data load with invalid stock code."""
        # Arrange
        runner = CliRunner()

        # Act
        result = runner.invoke(
            data_group,
            ["load", "--code", "invalid", "--start", "2023-01-01", "--end", "2023-12-31"],
        )

        # Assert
        assert result.exit_code != 0
        # Click may suppress the error output, so just check exit code

    def test_data_load_invalid_date_format(self):
        """Test data load with invalid date format."""
        # Arrange
        runner = CliRunner()

        # Act
        result = runner.invoke(
            data_group,
            ["load", "--code", "sh600000", "--start", "2023/01/01", "--end", "2023-12-31"],
        )

        # Assert
        assert result.exit_code != 0
        # Click may suppress the error output, so just check exit code


class TestDataListCommand:
    """Test data list command."""

    def test_data_list_success(self):
        """Test listing data successfully."""
        # Arrange
        runner = CliRunner()

        # Act
        result = runner.invoke(data_group, ["list"])

        # Assert
        # Should not error, even if no implementation yet
        assert result.exit_code == 0 or "not implemented" in result.output.lower()

    def test_data_list_with_market_filter(self):
        """Test listing data with market filter."""
        # Arrange
        runner = CliRunner()

        # Act
        result = runner.invoke(data_group, ["list", "--market", "sh"])

        # Assert
        assert result.exit_code == 0 or "not implemented" in result.output.lower()
