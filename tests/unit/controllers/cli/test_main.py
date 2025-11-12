"""
Tests for main CLI entry point.

Tests:
- CLI version
- Command groups integration
- Help messages
"""

import pytest
from click.testing import CliRunner

from controllers.cli.main import cli


class TestCLIMain:
    """Test main CLI entry point."""

    def test_cli_help(self):
        """Test CLI help message."""
        # Arrange
        runner = CliRunner()

        # Act
        result = runner.invoke(cli, ["--help"])

        # Assert
        assert result.exit_code == 0
        assert "Hikyuu" in result.output or "Trading" in result.output
        assert "data" in result.output
        assert "model" in result.output
        assert "config" in result.output

    def test_cli_version(self):
        """Test CLI version command."""
        # Arrange
        runner = CliRunner()

        # Act
        result = runner.invoke(cli, ["--version"])

        # Assert
        assert result.exit_code == 0
        assert "0.1.0" in result.output or "version" in result.output.lower()

    def test_cli_data_command_available(self):
        """Test data command is available."""
        # Arrange
        runner = CliRunner()

        # Act
        result = runner.invoke(cli, ["data", "--help"])

        # Assert
        assert result.exit_code == 0
        assert "data" in result.output.lower() or "load" in result.output.lower()

    def test_cli_model_command_available(self):
        """Test model command is available."""
        # Arrange
        runner = CliRunner()

        # Act
        result = runner.invoke(cli, ["model", "--help"])

        # Assert
        assert result.exit_code == 0
        assert "model" in result.output.lower() or "train" in result.output.lower()

    def test_cli_config_command_available(self):
        """Test config command is available."""
        # Arrange
        runner = CliRunner()

        # Act
        result = runner.invoke(cli, ["config", "--help"])

        # Assert
        assert result.exit_code == 0
        assert "config" in result.output.lower() or "show" in result.output.lower()

    def test_cli_invalid_command(self):
        """Test CLI with invalid command."""
        # Arrange
        runner = CliRunner()

        # Act
        result = runner.invoke(cli, ["invalid-command"])

        # Assert
        assert result.exit_code != 0
        assert "Error" in result.output or "No such command" in result.output
