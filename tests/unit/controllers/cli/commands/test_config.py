"""
Tests for configuration CLI commands.

Tests:
- config show command
- config set command
"""


from click.testing import CliRunner

from controllers.cli.commands.config import config_group


class TestConfigShowCommand:
    """Test config show command."""

    def test_config_show_all(self):
        """Test showing all configuration."""
        # Arrange
        runner = CliRunner()

        # Act
        result = runner.invoke(config_group, ["show"])

        # Assert
        assert result.exit_code == 0
        assert "Configuration" in result.output
        assert "Settings" in result.output or "DATA" in result.output

    def test_config_show_data_section(self):
        """Test showing data configuration section."""
        # Arrange
        runner = CliRunner()

        # Act
        result = runner.invoke(config_group, ["show", "--section", "data"])

        # Assert
        assert result.exit_code == 0
        assert "data" in result.output.lower() or "Configuration" in result.output

    def test_config_show_model_section(self):
        """Test showing model configuration section."""
        # Arrange
        runner = CliRunner()

        # Act
        result = runner.invoke(config_group, ["show", "--section", "model"])

        # Assert
        assert result.exit_code == 0
        assert "model" in result.output.lower() or "Configuration" in result.output

    def test_config_show_backtest_section(self):
        """Test showing backtest configuration section."""
        # Arrange
        runner = CliRunner()

        # Act
        result = runner.invoke(config_group, ["show", "--section", "backtest"])

        # Assert
        assert result.exit_code == 0
        assert "backtest" in result.output.lower() or "Configuration" in result.output


class TestConfigSetCommand:
    """Test config set command."""

    def test_config_set_success(self):
        """Test setting configuration value."""
        # Arrange
        runner = CliRunner()

        # Act
        result = runner.invoke(
            config_group,
            ["set", "--key", "HIKYUU_DATA_PATH", "--value", "/path/to/data"],
        )

        # Assert
        assert result.exit_code == 0
        assert "HIKYUU_DATA_PATH" in result.output
        assert "/path/to/data" in result.output

    def test_config_set_missing_key(self):
        """Test config set with missing key."""
        # Arrange
        runner = CliRunner()

        # Act
        result = runner.invoke(config_group, ["set", "--value", "value"])

        # Assert
        assert result.exit_code != 0
        assert "Error" in result.output or "Missing" in result.output

    def test_config_set_missing_value(self):
        """Test config set with missing value."""
        # Arrange
        runner = CliRunner()

        # Act
        result = runner.invoke(config_group, ["set", "--key", "SOME_KEY"])

        # Assert
        assert result.exit_code != 0
        assert "Error" in result.output or "Missing" in result.output

    def test_config_set_numeric_value(self):
        """Test setting numeric configuration value."""
        # Arrange
        runner = CliRunner()

        # Act
        result = runner.invoke(
            config_group,
            ["set", "--key", "INITIAL_CAPITAL", "--value", "200000"],
        )

        # Assert
        assert result.exit_code == 0
        assert "INITIAL_CAPITAL" in result.output
        assert "200000" in result.output
