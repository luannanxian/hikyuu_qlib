"""
Data management CLI commands.

Commands:
- load: Load stock data
- list: List available stock data
"""

import asyncio
from typing import List, Optional

import click

from controllers.cli.di.container import Container
from controllers.cli.utils.output import CLIOutput
from controllers.cli.utils.validators import validate_date, validate_stock_code
from domain.value_objects.date_range import DateRange
from domain.value_objects.kline_type import KLineType
from domain.value_objects.stock_code import StockCode
from utils.data_conversion import (
    convert_kline_to_training_data,
    save_to_file,
)


@click.group(name="data")
def data_group():
    """Data management commands."""
    pass


@data_group.command(name="load")
@click.option(
    "--code",
    required=True,
    help="Stock code (e.g., sh600000)",
    callback=lambda ctx, param, value: validate_stock_code(value) if value else None,
)
@click.option(
    "--start",
    required=True,
    help="Start date (YYYY-MM-DD)",
    callback=lambda ctx, param, value: validate_date(value) if value else None,
)
@click.option(
    "--end",
    required=True,
    help="End date (YYYY-MM-DD)",
    callback=lambda ctx, param, value: validate_date(value) if value else None,
)
@click.option(
    "--kline-type",
    default="DAY",
    type=click.Choice(["DAY", "WEEK", "MONTH", "MIN5", "MIN15", "MIN30", "MIN60"], case_sensitive=False),
    help="K-line type (default: DAY)",
)
@click.option(
    "--output",
    "-o",
    "output_file",
    help="Output file path (supports .csv or .parquet)",
)
@click.option(
    "--add-features",
    is_flag=True,
    default=False,
    help="Add technical indicator features",
)
@click.option(
    "--add-labels",
    is_flag=True,
    default=False,
    help="Add training labels",
)
def load_command(
    code: str,
    start,
    end,
    kline_type: str,
    output_file: Optional[str],
    add_features: bool,
    add_labels: bool,
):
    """
    Load stock data.

    Examples:

    1. Basic usage (display only):
        hikyuu-qlib data load --code sh600000 --start 2023-01-01 --end 2023-12-31

    2. Save to CSV file:
        hikyuu-qlib data load --code sh600000 --start 2023-01-01 --end 2023-12-31 --output train.csv

    3. Save with features and labels (ready for training):
        hikyuu-qlib data load --code sh600000 --start 2023-01-01 --end 2023-12-31 \\
            --output train.csv --add-features --add-labels
    """
    output = CLIOutput()

    try:
        # Run async function in event loop
        asyncio.run(
            _load_stock_data(
                code, start, end, kline_type, output_file, add_features, add_labels, output
            )
        )
    except Exception as e:
        output.error(f"Failed to load data: {str(e)}")
        raise click.Abort()


async def _load_stock_data(
    code_str: str,
    start_date,
    end_date,
    kline_type_str: str,
    output_file: Optional[str],
    add_features: bool,
    add_labels: bool,
    output: CLIOutput,
):
    """
    Load stock data (async implementation).

    Args:
        code_str: Stock code string
        start_date: Start date
        end_date: End date
        kline_type_str: K-line type string
        output_file: Output file path (optional)
        add_features: Whether to add technical indicators
        add_labels: Whether to add training labels
        output: CLI output instance
    """
    try:
        # Create value objects
        stock_code = StockCode(code_str)
        date_range = DateRange(start_date=start_date, end_date=end_date)
        kline_type = KLineType[kline_type_str.upper()]

        # Get use case from container
        container = Container()
        use_case = container.load_stock_data_use_case

        # Execute use case
        output.info(f"Loading data for {code_str} from {start_date} to {end_date}...")

        kline_data_list = await use_case.execute(
            stock_code=stock_code, date_range=date_range, kline_type=kline_type
        )

        # Display results
        if kline_data_list:
            output.success(
                f"Successfully loaded {len(kline_data_list)} K-line records for {code_str}"
            )
            output.info(
                f"Date range: {kline_data_list[0].timestamp.date()} to {kline_data_list[-1].timestamp.date()}"
            )

            # Save to file if requested
            if output_file:
                output.info(f"Converting data to training format...")

                # Convert to training data
                training_data = convert_kline_to_training_data(
                    kline_data_list,
                    add_features=add_features,
                    add_labels=add_labels,
                    label_horizon=1,
                )

                output.info(f"Saving to file: {output_file}")
                save_to_file(training_data, output_file)

                output.success(
                    f"Data saved to {output_file} ({len(training_data)} records)"
                )

                # Show column info
                output.info(f"Columns: {list(training_data.columns)}")
                if add_features:
                    output.info("✓ Technical indicators added")
                if add_labels:
                    output.info("✓ Training labels added")

        else:
            output.warning(f"No data found for {code_str} in the specified date range")

    except Exception as e:
        output.error(f"Error loading data: {str(e)}")
        raise


@data_group.command(name="list")
@click.option(
    "--market",
    type=click.Choice(["sh", "sz"], case_sensitive=False),
    help="Filter by market (sh or sz)",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Show detailed information",
)
def list_command(market: Optional[str], verbose: bool):
    """
    List available stock data.

    Example:
        hikyuu-qlib data list --market sh
        hikyuu-qlib data list --verbose
    """
    output = CLIOutput()

    try:
        # TODO: Implement listing logic when data storage is available
        output.warning("Data list command not yet implemented")
        output.info("This command will list all available stock data in the system")

        if market:
            output.info(f"Filter: Market = {market.upper()}")

        if verbose:
            output.info("Verbose mode enabled")

    except Exception as e:
        output.error(f"Failed to list data: {str(e)}")
        raise click.Abort()
