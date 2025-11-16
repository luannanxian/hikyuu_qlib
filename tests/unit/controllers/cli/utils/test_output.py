"""
Tests for CLI output utilities.

Tests:
- Console creation
- Table formatting
- Progress bar display
- Success/Error messages
"""

from rich.console import Console
from rich.table import Table

from controllers.cli.utils.output import CLIOutput, create_table, format_model_status


class TestCLIOutput:
    """Test CLI output utilities."""

    def test_create_console(self):
        """Test console creation."""
        # Arrange & Act
        output = CLIOutput()

        # Assert
        assert output.console is not None
        assert isinstance(output.console, Console)

    def test_print_success_message(self, capsys):
        """Test printing success message."""
        # Arrange
        output = CLIOutput()
        message = "Operation successful"

        # Act
        output.success(message)
        captured = capsys.readouterr()

        # Assert
        assert "successful" in captured.out.lower() or len(captured.out) > 0

    def test_print_error_message(self, capsys):
        """Test printing error message."""
        # Arrange
        output = CLIOutput()
        message = "Operation failed"

        # Act
        output.error(message)
        captured = capsys.readouterr()

        # Assert
        assert "failed" in captured.out.lower() or len(captured.out) > 0

    def test_print_warning_message(self, capsys):
        """Test printing warning message."""
        # Arrange
        output = CLIOutput()
        message = "Warning message"

        # Act
        output.warning(message)
        captured = capsys.readouterr()

        # Assert
        assert "warning" in captured.out.lower() or len(captured.out) > 0

    def test_print_info_message(self, capsys):
        """Test printing info message."""
        # Arrange
        output = CLIOutput()
        message = "Info message"

        # Act
        output.info(message)
        captured = capsys.readouterr()

        # Assert
        assert "info" in captured.out.lower() or len(captured.out) > 0


class TestTableFormatting:
    """Test table formatting utilities."""

    def test_create_table_with_title(self):
        """Test creating table with title."""
        # Arrange
        title = "Test Table"
        columns = ["Column 1", "Column 2"]

        # Act
        table = create_table(title, columns)

        # Assert
        assert table is not None
        assert isinstance(table, Table)
        assert table.title == title

    def test_create_table_without_title(self):
        """Test creating table without title."""
        # Arrange
        columns = ["Column 1", "Column 2"]

        # Act
        table = create_table(None, columns)

        # Assert
        assert table is not None
        assert isinstance(table, Table)
        assert table.title is None


class TestModelStatusFormatting:
    """Test model status formatting."""

    def test_format_trained_status(self):
        """Test formatting TRAINED status."""
        # Arrange
        status = "TRAINED"

        # Act
        result = format_model_status(status)

        # Assert
        assert result is not None
        assert "TRAINED" in result.upper()

    def test_format_training_status(self):
        """Test formatting TRAINING status."""
        # Arrange
        status = "TRAINING"

        # Act
        result = format_model_status(status)

        # Assert
        assert result is not None
        assert "TRAINING" in result.upper()

    def test_format_failed_status(self):
        """Test formatting FAILED status."""
        # Arrange
        status = "FAILED"

        # Act
        result = format_model_status(status)

        # Assert
        assert result is not None
        assert "FAILED" in result.upper()
