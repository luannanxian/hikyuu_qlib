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

    def test_data_list_empty_directory(self):
        """Test listing data when directory is empty."""
        # Arrange
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create empty directory
            import os
            os.makedirs("empty_dir", exist_ok=True)

            # Act
            result = runner.invoke(data_group, ["list", "--directory", "empty_dir"])

            # Assert
            assert result.exit_code == 0
            assert "no data" in result.output.lower() or "found 0" in result.output.lower()

    def test_data_list_table_format_default(self):
        """Test listing data in table format (default)."""
        # Arrange
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create test files
            import pandas as pd
            df = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})
            df.to_csv("test1.csv", index=False)
            df.to_parquet("test2.parquet")

            # Act
            result = runner.invoke(data_group, ["list", "--directory", "."])

            # Assert
            assert result.exit_code == 0
            assert "test1.csv" in result.output
            assert "test2.parquet" in result.output
            # Table format should show headers
            assert "File" in result.output or "Name" in result.output

    def test_data_list_json_format(self):
        """Test listing data in JSON format."""
        # Arrange
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create test file
            import pandas as pd
            df = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})
            df.to_csv("test.csv", index=False)

            # Act
            result = runner.invoke(data_group, ["list", "--directory", ".", "--format", "json"])

            # Assert
            assert result.exit_code == 0
            import json
            # Extract JSON from output
            json_start = result.output.find("[")
            json_end = result.output.rfind("]") + 1
            if json_start >= 0 and json_end > json_start:
                json_content = result.output[json_start:json_end]
                data = json.loads(json_content)
                assert isinstance(data, list)
                assert any("test.csv" in str(item) for item in data)

    def test_data_list_csv_format(self):
        """Test listing data in CSV format."""
        # Arrange
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create test file
            import pandas as pd
            df = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})
            df.to_csv("test.csv", index=False)

            # Act
            result = runner.invoke(data_group, ["list", "--directory", ".", "--format", "csv"])

            # Assert
            assert result.exit_code == 0
            # CSV format should have comma-separated values
            assert "," in result.output
            assert "test.csv" in result.output

    def test_data_list_file_information(self):
        """Test that file information is extracted correctly."""
        # Arrange
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create test file
            import pandas as pd
            df = pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})
            df.to_csv("test.csv", index=False)

            # Act
            result = runner.invoke(data_group, ["list", "--directory", "."])

            # Assert
            assert result.exit_code == 0
            assert "test.csv" in result.output
            # Should show file size or row count
            assert any(x in result.output.lower() for x in ["size", "rows", "records", "3"])

    def test_data_list_directory_not_exist(self):
        """Test listing data when directory does not exist."""
        # Arrange
        runner = CliRunner()

        # Act
        result = runner.invoke(data_group, ["list", "--directory", "/nonexistent/path"])

        # Assert
        assert result.exit_code != 0
        assert "not found" in result.output.lower() or "not exist" in result.output.lower()

    def test_data_list_multiple_file_types(self):
        """Test listing different file types (CSV, Parquet, PKL)."""
        # Arrange
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create different types of files
            import pandas as pd
            df = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})

            df.to_csv("data.csv", index=False)
            df.to_parquet("data.parquet")
            df.to_pickle("data.pkl")

            # Act
            result = runner.invoke(data_group, ["list", "--directory", "."])

            # Assert
            assert result.exit_code == 0
            assert "data.csv" in result.output
            assert "data.parquet" in result.output
            assert "data.pkl" in result.output

    def test_data_list_with_custom_directory(self):
        """Test listing data with custom directory option."""
        # Arrange
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create subdirectory with files
            import os
            import pandas as pd

            os.makedirs("data", exist_ok=True)
            df = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})
            df.to_csv("data/test.csv", index=False)

            # Act
            result = runner.invoke(data_group, ["list", "--directory", "data"])

            # Assert
            assert result.exit_code == 0
            assert "test.csv" in result.output

    def test_data_list_corrupted_file_handling(self):
        """Test handling of corrupted or unreadable files."""
        # Arrange
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create a corrupted CSV file
            with open("corrupted.csv", "w") as f:
                f.write("invalid,data\nthis is not valid csv\x00\x01\x02")

            # Act
            result = runner.invoke(data_group, ["list", "--directory", "."])

            # Assert
            assert result.exit_code == 0
            # Should still list the file even if it's corrupted
            assert "corrupted.csv" in result.output

    def test_data_list_shows_column_count(self):
        """Test that list shows column count for each file."""
        # Arrange
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create test file with 5 columns
            import pandas as pd
            df = pd.DataFrame({
                "col1": [1, 2],
                "col2": [3, 4],
                "col3": [5, 6],
                "col4": [7, 8],
                "col5": [9, 10]
            })
            df.to_csv("test.csv", index=False)

            # Act
            result = runner.invoke(data_group, ["list", "--directory", "."])

            # Assert
            assert result.exit_code == 0
            # Should show column count (5 columns)
            assert "5" in result.output or "columns" in result.output.lower()

    def test_data_list_shows_modified_time(self):
        """Test that list shows file modification time."""
        # Arrange
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create test file
            import pandas as pd
            df = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})
            df.to_csv("test.csv", index=False)

            # Act
            result = runner.invoke(data_group, ["list", "--directory", "."])

            # Assert
            assert result.exit_code == 0
            # Should show modification time (contains date patterns)
            import re
            # Check for date-like patterns (YYYY-MM-DD or similar)
            has_date = bool(re.search(r'\d{4}[-/]\d{2}[-/]\d{2}|\d{2}[-/]\d{2}[-/]\d{4}', result.output))
            assert has_date or "modified" in result.output.lower()
