"""
Tests for enhanced data management CLI commands.

Tests:
- data list command with Hikyuu source
- data list command with file source
"""

from unittest.mock import AsyncMock, Mock, patch

from click.testing import CliRunner

from controllers.cli.commands.data import data_group
from domain.value_objects.stock_code import StockCode


class TestDataListHikyuuSource:
    """Test data list command with Hikyuu source."""

    @patch("controllers.cli.commands.data.asyncio.run")
    @patch("controllers.cli.commands.data.Container")
    def test_data_list_hikyuu_all_markets(self, mock_container_class, mock_asyncio_run):
        """Test listing stocks from Hikyuu database for all markets."""
        # Arrange
        runner = CliRunner()

        # Mock container and data provider
        mock_container = Mock()
        mock_data_provider = AsyncMock()
        mock_container.data_provider = mock_data_provider
        mock_container_class.return_value = mock_container

        # Mock stock codes
        mock_sh_codes = [StockCode("sh600000"), StockCode("sh600001")]
        mock_sz_codes = [StockCode("sz000001"), StockCode("sz000002")]

        async def mock_get_stock_list(market):
            if market == "SH":
                return mock_sh_codes
            elif market == "SZ":
                return mock_sz_codes
            return []

        mock_data_provider.get_stock_list = mock_get_stock_list

        # Mock load_stock_data to return empty for now
        mock_data_provider.load_stock_data = AsyncMock(return_value=[])

        # Mock asyncio.run
        def side_effect(coro):
            import asyncio
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(coro)
            finally:
                loop.close()

        mock_asyncio_run.side_effect = side_effect

        # Act
        result = runner.invoke(
            data_group,
            ["list", "--source", "hikyuu", "--market", "ALL"],
        )

        # Assert
        assert result.exit_code == 0
        assert "Querying Hikyuu database" in result.output or "Found" in result.output

    @patch("controllers.cli.commands.data.asyncio.run")
    @patch("controllers.cli.commands.data.Container")
    def test_data_list_hikyuu_single_market(self, mock_container_class, mock_asyncio_run):
        """Test listing stocks from Hikyuu database for single market."""
        # Arrange
        runner = CliRunner()

        # Mock container and data provider
        mock_container = Mock()
        mock_data_provider = AsyncMock()
        mock_container.data_provider = mock_data_provider
        mock_container_class.return_value = mock_container

        # Mock stock codes
        mock_sh_codes = [StockCode("sh600000")]

        async def mock_get_stock_list(market):
            if market == "SH":
                return mock_sh_codes
            return []

        mock_data_provider.get_stock_list = mock_get_stock_list
        mock_data_provider.load_stock_data = AsyncMock(return_value=[])

        # Mock asyncio.run
        def side_effect(coro):
            import asyncio
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(coro)
            finally:
                loop.close()

        mock_asyncio_run.side_effect = side_effect

        # Act
        result = runner.invoke(
            data_group,
            ["list", "--source", "hikyuu", "--market", "SH"],
        )

        # Assert
        assert result.exit_code == 0

    @patch("controllers.cli.commands.data.asyncio.run")
    @patch("controllers.cli.commands.data.Container")
    def test_data_list_hikyuu_json_output(self, mock_container_class, mock_asyncio_run):
        """Test listing stocks from Hikyuu with JSON output."""
        # Arrange
        runner = CliRunner()

        # Mock container and data provider
        mock_container = Mock()
        mock_data_provider = AsyncMock()
        mock_container.data_provider = mock_data_provider
        mock_container_class.return_value = mock_container

        # Mock stock codes
        mock_sh_codes = [StockCode("sh600000")]

        async def mock_get_stock_list(market):
            return mock_sh_codes if market == "SH" else []

        mock_data_provider.get_stock_list = mock_get_stock_list
        mock_data_provider.load_stock_data = AsyncMock(return_value=[])

        # Mock asyncio.run
        def side_effect(coro):
            import asyncio
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(coro)
            finally:
                loop.close()

        mock_asyncio_run.side_effect = side_effect

        # Act
        result = runner.invoke(
            data_group,
            ["list", "--source", "hikyuu", "--market", "SH", "--format", "json"],
        )

        # Assert
        assert result.exit_code == 0
        # JSON output should contain the total count
        assert "total" in result.output.lower() or "Found" in result.output


class TestDataListFileSource:
    """Test data list command with file source."""

    def test_data_list_files_default_directory(self, tmp_path):
        """Test listing data files in default directory."""
        # Arrange
        runner = CliRunner()

        # Create temporary data files
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "test.csv").write_text("col1,col2\n1,2\n")

        # Act
        result = runner.invoke(
            data_group,
            ["list", "--source", "files", "--directory", str(data_dir)],
        )

        # Assert
        assert result.exit_code == 0
        assert "test.csv" in result.output or "Found" in result.output

    def test_data_list_files_empty_directory(self, tmp_path):
        """Test listing data files in empty directory."""
        # Arrange
        runner = CliRunner()

        # Create empty directory
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        # Act
        result = runner.invoke(
            data_group,
            ["list", "--source", "files", "--directory", str(data_dir)],
        )

        # Assert
        assert result.exit_code == 0
        assert "No data files found" in result.output

    def test_data_list_files_nonexistent_directory(self):
        """Test listing data files in nonexistent directory."""
        # Arrange
        runner = CliRunner()

        # Act
        result = runner.invoke(
            data_group,
            ["list", "--source", "files", "--directory", "/nonexistent/directory"],
        )

        # Assert
        assert result.exit_code != 0
        assert "not found" in result.output.lower()

    def test_data_list_files_json_format(self, tmp_path):
        """Test listing data files with JSON output."""
        # Arrange
        runner = CliRunner()

        # Create temporary data files
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "test.csv").write_text("col1,col2\n1,2\n")

        # Act
        result = runner.invoke(
            data_group,
            ["list", "--source", "files", "--directory", str(data_dir), "--format", "json"],
        )

        # Assert
        assert result.exit_code == 0
        assert "test.csv" in result.output or "name" in result.output.lower()
