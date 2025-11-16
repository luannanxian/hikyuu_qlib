"""
Tests for enhanced config set command.

Tests:
- config set with YAML persistence
- config set with .env persistence
- config set value validation
- config set invalid keys
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from click.testing import CliRunner

from controllers.cli.commands.config import _parse_config_value, config_group


class TestConfigSetYAML:
    """Test config set command with YAML persistence."""

    @patch("controllers.cli.commands.config.asyncio.run")
    @patch("controllers.cli.commands.config.Container")
    def test_config_set_hikyuu_data_path(self, mock_container_class, mock_asyncio_run):
        """Test setting HIKYUU_DATA_PATH."""
        # Arrange
        runner = CliRunner()

        # Mock container and repository
        mock_container = Mock()
        mock_repository = AsyncMock()
        mock_use_case = AsyncMock()
        mock_container.config_repository = mock_repository
        mock_container.load_configuration_use_case = mock_use_case
        mock_container_class.return_value = mock_container

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
            config_group,
            ["set", "HIKYUU_DATA_PATH", "/path/to/hikyuu"],
        )

        # Assert
        assert result.exit_code == 0
        assert "HIKYUU_DATA_PATH" in result.output
        assert "/path/to/hikyuu" in result.output

    @patch("controllers.cli.commands.config.asyncio.run")
    @patch("controllers.cli.commands.config.Container")
    def test_config_set_initial_capital(self, mock_container_class, mock_asyncio_run):
        """Test setting INITIAL_CAPITAL."""
        # Arrange
        runner = CliRunner()

        # Mock container and repository
        mock_container = Mock()
        mock_repository = AsyncMock()
        mock_use_case = AsyncMock()

        # Mock a proper config object
        from decimal import Decimal
        from unittest.mock import Mock as ConfigMock

        from domain.value_objects.configuration import BacktestConfig

        mock_backtest_config = BacktestConfig(
            initial_capital=Decimal(100000),
            commission_rate=Decimal("0.0003"),
            slippage_rate=Decimal("0.001"),
        )

        mock_config = ConfigMock()
        mock_config.backtest = mock_backtest_config
        mock_config.data_source = None
        mock_config.model = None

        mock_use_case.execute.return_value = mock_config

        mock_container.config_repository = mock_repository
        mock_container.load_configuration_use_case = mock_use_case
        mock_container_class.return_value = mock_container

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
            config_group,
            ["set", "INITIAL_CAPITAL", "200000"],
        )

        # Assert
        assert result.exit_code == 0
        assert "INITIAL_CAPITAL" in result.output

    @patch("controllers.cli.commands.config.asyncio.run")
    @patch("controllers.cli.commands.config.Container")
    def test_config_set_commission_rate(self, mock_container_class, mock_asyncio_run):
        """Test setting COMMISSION_RATE."""
        # Arrange
        runner = CliRunner()

        # Mock container and repository
        mock_container = Mock()
        mock_repository = AsyncMock()
        mock_use_case = AsyncMock()

        # Mock a proper config object
        from decimal import Decimal
        from unittest.mock import Mock as ConfigMock

        from domain.value_objects.configuration import BacktestConfig

        mock_backtest_config = BacktestConfig(
            initial_capital=Decimal(100000),
            commission_rate=Decimal("0.0003"),
            slippage_rate=Decimal("0.001"),
        )

        mock_config = ConfigMock()
        mock_config.backtest = mock_backtest_config
        mock_config.data_source = None
        mock_config.model = None

        mock_use_case.execute.return_value = mock_config

        mock_container.config_repository = mock_repository
        mock_container.load_configuration_use_case = mock_use_case
        mock_container_class.return_value = mock_container

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
            config_group,
            ["set", "COMMISSION_RATE", "0.0005"],
        )

        # Assert
        assert result.exit_code == 0
        assert "COMMISSION_RATE" in result.output


class TestConfigSetEnv:
    """Test config set command with .env persistence."""

    def test_config_set_to_env_file(self, tmp_path, monkeypatch):
        """Test setting config to .env file."""
        # Arrange
        runner = CliRunner()

        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        # Act
        result = runner.invoke(
            config_group,
            ["set", "LOG_LEVEL", "DEBUG", "--persist", "env"],
        )

        # Assert
        assert result.exit_code == 0
        assert "LOG_LEVEL" in result.output

        # Check .env file was created
        env_file = tmp_path / ".env"
        assert env_file.exists()
        content = env_file.read_text()
        assert "LOG_LEVEL=DEBUG" in content

    def test_config_set_updates_existing_env(self, tmp_path, monkeypatch):
        """Test updating existing value in .env file."""
        # Arrange
        runner = CliRunner()

        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        # Create existing .env file
        env_file = tmp_path / ".env"
        env_file.write_text("LOG_LEVEL=INFO\nOTHER_KEY=value\n")

        # Act
        result = runner.invoke(
            config_group,
            ["set", "LOG_LEVEL", "DEBUG", "--persist", "env"],
        )

        # Assert
        assert result.exit_code == 0

        # Check .env file was updated
        content = env_file.read_text()
        assert "LOG_LEVEL=DEBUG" in content
        assert "OTHER_KEY=value" in content  # Other keys preserved


class TestConfigValueParsing:
    """Test config value parsing and validation."""

    def test_parse_string_value(self):
        """Test parsing string configuration value."""
        # Act
        result = _parse_config_value("HIKYUU_DATA_PATH", "/path/to/data")

        # Assert
        assert result == "/path/to/data"
        assert isinstance(result, str)

    def test_parse_float_value(self):
        """Test parsing float configuration value."""
        # Act
        result = _parse_config_value("INITIAL_CAPITAL", "100000.50")

        # Assert
        assert result == 100000.50
        assert isinstance(result, float)

    def test_parse_commission_rate(self):
        """Test parsing commission rate value."""
        # Act
        result = _parse_config_value("COMMISSION_RATE", "0.0003")

        # Assert
        assert result == 0.0003
        assert isinstance(result, float)

    def test_parse_log_level(self):
        """Test parsing log level value."""
        # Act
        result = _parse_config_value("LOG_LEVEL", "debug")

        # Assert
        assert result == "DEBUG"

    def test_parse_environment(self):
        """Test parsing environment value."""
        # Act
        result = _parse_config_value("ENVIRONMENT", "PROD")

        # Assert
        assert result == "prod"

    def test_parse_invalid_key(self):
        """Test parsing with invalid key raises error."""
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid configuration key"):
            _parse_config_value("INVALID_KEY", "value")

    def test_parse_invalid_log_level(self):
        """Test parsing invalid log level raises error."""
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid LOG_LEVEL"):
            _parse_config_value("LOG_LEVEL", "INVALID")

    def test_parse_invalid_environment(self):
        """Test parsing invalid environment raises error."""
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid ENVIRONMENT"):
            _parse_config_value("ENVIRONMENT", "invalid")

    def test_parse_negative_capital(self):
        """Test parsing negative initial capital raises error."""
        # Act & Assert
        with pytest.raises(ValueError, match="must be positive"):
            _parse_config_value("INITIAL_CAPITAL", "-100")

    def test_parse_invalid_commission_rate_too_high(self):
        """Test parsing commission rate > 1 raises error."""
        # Act & Assert
        with pytest.raises(ValueError, match="must be between 0 and 1"):
            _parse_config_value("COMMISSION_RATE", "1.5")

    def test_parse_invalid_commission_rate_negative(self):
        """Test parsing negative commission rate raises error."""
        # Act & Assert
        with pytest.raises(ValueError, match="must be between 0 and 1"):
            _parse_config_value("COMMISSION_RATE", "-0.1")

    def test_parse_invalid_float_format(self):
        """Test parsing invalid float format raises error."""
        # Act & Assert
        with pytest.raises(ValueError):
            _parse_config_value("INITIAL_CAPITAL", "not_a_number")


class TestConfigSetCommandIntegration:
    """Integration tests for config set command."""

    def test_config_set_missing_arguments(self):
        """Test config set with missing arguments."""
        # Arrange
        runner = CliRunner()

        # Act
        result = runner.invoke(config_group, ["set"])

        # Assert
        assert result.exit_code != 0
        assert "Error" in result.output or "Missing" in result.output

    def test_config_set_help(self):
        """Test config set help text."""
        # Arrange
        runner = CliRunner()

        # Act
        result = runner.invoke(config_group, ["set", "--help"])

        # Assert
        assert result.exit_code == 0
        assert "Set configuration value" in result.output
        assert "HIKYUU_DATA_PATH" in result.output
        assert "--persist" in result.output
