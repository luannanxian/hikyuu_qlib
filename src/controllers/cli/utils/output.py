"""
CLI output utilities using Rich library.

Provides formatted console output:
- Success/Error/Warning/Info messages
- Tables
- Progress bars
- Color formatting
"""


from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table


class CLIOutput:
    """
    CLI output manager using Rich.

    Provides methods for:
    - Formatted messages (success, error, warning, info)
    - Tables
    - Progress bars
    """

    def __init__(self):
        """Initialize CLI output with Rich console."""
        self.console = Console()

    def success(self, message: str) -> None:
        """
        Print success message in green.

        Args:
            message: Success message to display
        """
        self.console.print(f"[bold green]✓[/bold green] {message}")

    def error(self, message: str) -> None:
        """
        Print error message in red.

        Args:
            message: Error message to display
        """
        self.console.print(f"[bold red]✗[/bold red] {message}")

    def warning(self, message: str) -> None:
        """
        Print warning message in yellow.

        Args:
            message: Warning message to display
        """
        self.console.print(f"[bold yellow]⚠[/bold yellow] {message}")

    def info(self, message: str) -> None:
        """
        Print info message in blue.

        Args:
            message: Info message to display
        """
        self.console.print(f"[bold blue]ℹ[/bold blue] {message}")

    def print(self, message: str) -> None:
        """
        Print plain message.

        Args:
            message: Message to display
        """
        self.console.print(message)

    def print_table(self, table: Table) -> None:
        """
        Print a Rich table.

        Args:
            table: Rich Table object to display
        """
        self.console.print(table)

    def create_progress(self) -> Progress:
        """
        Create a progress bar.

        Returns:
            Progress: Rich Progress object
        """
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        )


def create_table(
    title: str | None, columns: list[str], show_header: bool = True,
) -> Table:
    """
    Create a Rich table with specified columns.

    Args:
        title: Table title (optional)
        columns: List of column names
        show_header: Whether to show table header

    Returns:
        Table: Rich Table object
    """
    table = Table(title=title, show_header=show_header)

    for column in columns:
        table.add_column(column)

    return table


def format_model_status(status: str) -> str:
    """
    Format model status with color.

    Args:
        status: Model status string

    Returns:
        str: Formatted status with Rich markup
    """
    status_upper = status.upper()

    if status_upper == "TRAINED":
        return "[green]TRAINED[/green]"
    elif status_upper == "TRAINING":
        return "[yellow]TRAINING[/yellow]"
    elif status_upper == "FAILED":
        return "[red]FAILED[/red]"
    elif status_upper == "PENDING":
        return "[blue]PENDING[/blue]"
    else:
        return status


def format_backtest_metric(metric_name: str, value: float) -> str:
    """
    Format backtest metric with appropriate color.

    Args:
        metric_name: Name of the metric
        value: Metric value

    Returns:
        str: Formatted metric with Rich markup
    """
    # Positive metrics - green if > 0
    if metric_name.lower() in ["total_return", "annual_return", "sharpe_ratio"]:
        if value > 0:
            return f"[green]{value:.4f}[/green]"
        else:
            return f"[red]{value:.4f}[/red]"

    # Negative metrics - green if < 0 (like max_drawdown)
    elif metric_name.lower() in ["max_drawdown"]:
        if value < 0:
            return f"[yellow]{value:.4f}[/yellow]"
        else:
            return f"{value:.4f}"

    # Default formatting
    else:
        return f"{value:.4f}"
