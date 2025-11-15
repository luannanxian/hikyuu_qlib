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
    "--source",
    type=click.Choice(["files", "hikyuu"], case_sensitive=False),
    default="files",
    help="Data source to list: 'files' (scan data files) or 'hikyuu' (query Hikyuu database)",
)
@click.option(
    "--directory",
    default="data",
    help="Directory to scan for data files (only for --source files, default: data)",
)
@click.option(
    "--market",
    type=click.Choice(["SH", "SZ", "ALL"], case_sensitive=False),
    default="ALL",
    help="Market filter (only for --source hikyuu, default: ALL)",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "csv"], case_sensitive=False),
    default="table",
    help="Output format (default: table)",
)
def list_command(source: str, directory: str, market: str, output_format: str):
    """
    List available data.

    Two modes supported:
    1. Files mode (default): Scans directory for CSV/Parquet/PKL files
    2. Hikyuu mode: Lists stocks available in Hikyuu database

    Examples:
        # List data files in default directory
        hikyuu-qlib data list

        # List data files in custom directory
        hikyuu-qlib data list --source files --directory custom_data

        # List all stocks in Hikyuu database
        hikyuu-qlib data list --source hikyuu

        # List Shanghai stocks in Hikyuu database
        hikyuu-qlib data list --source hikyuu --market SH

        # Output as JSON
        hikyuu-qlib data list --source hikyuu --format json
    """
    output = CLIOutput()

    try:
        if source.lower() == "files":
            _list_data_files(directory, output_format, output)
        elif source.lower() == "hikyuu":
            asyncio.run(_list_hikyuu_stocks(market, output_format, output))
        else:
            output.error(f"Unknown source: {source}")
            raise click.Abort()

    except click.Abort:
        raise
    except Exception as e:
        output.error(f"Failed to list data: {str(e)}")
        raise click.Abort()


def _list_data_files(directory: str, output_format: str, output: CLIOutput):
    """
    List data files in a directory.

    Args:
        directory: Directory to scan
        output_format: Output format (table/json/csv)
        output: CLI output instance
    """
    from pathlib import Path
    from datetime import datetime
    import pandas as pd

    # Validate directory
    data_dir = Path(directory)
    if not data_dir.exists():
        output.error(f"Directory not found: {directory}")
        raise click.Abort()

    if not data_dir.is_dir():
        output.error(f"Path is not a directory: {directory}")
        raise click.Abort()

    # Scan for data files
    file_patterns = ["*.csv", "*.parquet", "*.pkl"]
    data_files = []

    for pattern in file_patterns:
        for file_path in data_dir.glob(pattern):
            if file_path.is_file():
                data_files.append(file_path)

    # Check if directory is empty
    if not data_files:
        output.info(f"No data files found in directory: {directory}")
        return

    # Extract file information
    file_infos = []
    for file_path in sorted(data_files, key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            # Get basic file info
            stat = file_path.stat()
            file_size = stat.st_size
            modified_time = datetime.fromtimestamp(stat.st_mtime)

            # Try to read file to get dimensions
            rows = None
            cols = None
            try:
                suffix = file_path.suffix.lower()
                if suffix == ".csv":
                    # Read only first few rows to infer structure
                    df = pd.read_csv(file_path, nrows=0)
                    cols = len(df.columns)
                    # Get row count efficiently
                    with open(file_path, 'r') as f:
                        rows = sum(1 for _ in f) - 1  # Subtract header
                elif suffix == ".parquet":
                    df = pd.read_parquet(file_path)
                    rows = len(df)
                    cols = len(df.columns)
                elif suffix == ".pkl":
                    df = pd.read_pickle(file_path)
                    if isinstance(df, pd.DataFrame):
                        rows = len(df)
                        cols = len(df.columns)
            except Exception:
                # If we can't read the file, just skip dimensions
                pass

            file_infos.append({
                "name": file_path.name,
                "path": str(file_path),
                "type": file_path.suffix[1:].upper(),  # Remove dot and uppercase
                "size": file_size,
                "size_mb": file_size / (1024 * 1024),
                "rows": rows if rows is not None else "N/A",
                "cols": cols if cols is not None else "N/A",
                "modified": modified_time,
            })

        except Exception as e:
            # Log error but continue with other files
            output.warning(f"Error reading {file_path.name}: {str(e)}")

    # Output results
    if output_format == "json":
        _output_data_list_json(file_infos, output)
    elif output_format == "csv":
        _output_data_list_csv(file_infos, output)
    else:  # table (default)
        _output_data_list_table(file_infos, output)


async def _list_hikyuu_stocks(market: str, output_format: str, output: CLIOutput):
    """
    List stocks available in Hikyuu database.

    Args:
        market: Market filter (SH/SZ/ALL)
        output_format: Output format (table/json/csv)
        output: CLI output instance
    """
    try:
        # Get container and data provider
        container = Container()
        data_provider = container.data_provider

        # Determine which markets to query
        markets_to_query = []
        if market.upper() == "ALL":
            markets_to_query = ["SH", "SZ"]
        else:
            markets_to_query = [market.upper()]

        # Collect stock information
        stock_infos = []
        total_stocks = 0

        output.info(f"Querying Hikyuu database for markets: {', '.join(markets_to_query)}...")

        for mkt in markets_to_query:
            try:
                # Get stock list for this market
                stock_codes = await data_provider.get_stock_list(mkt)
                total_stocks += len(stock_codes)

                output.info(f"Found {len(stock_codes)} stocks in {mkt} market")

                # For each stock, try to get data range (sample first few for performance)
                for i, stock_code in enumerate(stock_codes):
                    # Only sample first 10 stocks for data range to avoid long query time
                    if i < 10:
                        try:
                            # Query a wide date range to find actual data range
                            from datetime import datetime, timedelta
                            end_date = datetime.now()
                            start_date = end_date - timedelta(days=365 * 10)  # 10 years back

                            date_range = DateRange(start_date=start_date, end_date=end_date)
                            kline_data = await data_provider.load_stock_data(
                                stock_code=stock_code,
                                date_range=date_range,
                                kline_type=KLineType.DAY
                            )

                            if kline_data:
                                data_start = kline_data[0].timestamp.date()
                                data_end = kline_data[-1].timestamp.date()
                                record_count = len(kline_data)
                            else:
                                data_start = None
                                data_end = None
                                record_count = 0

                        except Exception as e:
                            # If we can't load data for this stock, skip it
                            data_start = None
                            data_end = None
                            record_count = None
                    else:
                        # For remaining stocks, don't query data range
                        data_start = None
                        data_end = None
                        record_count = None

                    stock_infos.append({
                        "code": stock_code.value,
                        "market": mkt,
                        "data_start": data_start,
                        "data_end": data_end,
                        "records": record_count if record_count is not None else "N/A"
                    })

            except Exception as e:
                output.warning(f"Error querying {mkt} market: {str(e)}")

        if not stock_infos:
            output.info("No stocks found in Hikyuu database")
            return

        # Output results
        if output_format == "json":
            _output_hikyuu_stocks_json(stock_infos, total_stocks, output)
        elif output_format == "csv":
            _output_hikyuu_stocks_csv(stock_infos, total_stocks, output)
        else:  # table (default)
            _output_hikyuu_stocks_table(stock_infos, total_stocks, output)

    except Exception as e:
        output.error(f"Error listing Hikyuu stocks: {str(e)}")
        raise


def _output_data_list_table(file_infos: list, output: CLIOutput):
    """Output data file list in table format."""
    import pandas as pd

    # Prepare data for table
    data = []
    for info in file_infos:
        data.append({
            "File": info["name"],
            "Type": info["type"],
            "Size (MB)": f"{info['size_mb']:.2f}",
            "Rows": info["rows"],
            "Cols": info["cols"],
            "Modified": info["modified"].strftime("%Y-%m-%d %H:%M"),
        })

    # Create DataFrame and output
    df = pd.DataFrame(data)
    output.info(f"\nFound {len(file_infos)} data file(s) in directory:\n")
    click.echo(df.to_string(index=False))


def _output_data_list_json(file_infos: list, output: CLIOutput):
    """Output data file list in JSON format."""
    import json

    # Prepare data for JSON
    data = []
    for info in file_infos:
        data.append({
            "name": info["name"],
            "path": info["path"],
            "type": info["type"],
            "size_bytes": info["size"],
            "size_mb": round(info["size_mb"], 2),
            "rows": info["rows"] if isinstance(info["rows"], int) else None,
            "cols": info["cols"] if isinstance(info["cols"], int) else None,
            "modified": info["modified"].isoformat(),
        })

    output.info(f"Found {len(file_infos)} data file(s):")
    click.echo(json.dumps(data, indent=2))


def _output_data_list_csv(file_infos: list, output: CLIOutput):
    """Output data file list in CSV format."""
    import pandas as pd

    # Prepare data for CSV
    data = []
    for info in file_infos:
        data.append({
            "name": info["name"],
            "path": info["path"],
            "type": info["type"],
            "size_bytes": info["size"],
            "size_mb": round(info["size_mb"], 2),
            "rows": info["rows"] if isinstance(info["rows"], int) else "",
            "cols": info["cols"] if isinstance(info["cols"], int) else "",
            "modified": info["modified"].isoformat(),
        })

    # Create DataFrame and output as CSV
    df = pd.DataFrame(data)
    output.info(f"Found {len(file_infos)} data file(s):")
    click.echo(df.to_csv(index=False))


def _output_hikyuu_stocks_table(stock_infos: list, total_stocks: int, output: CLIOutput):
    """Output Hikyuu stock list in table format."""
    import pandas as pd

    # Prepare data for table (show sample)
    data = []
    for info in stock_infos[:20]:  # Show first 20 stocks with details
        data.append({
            "Code": info["code"],
            "Market": info["market"],
            "Data Start": info["data_start"].strftime("%Y-%m-%d") if info["data_start"] else "N/A",
            "Data End": info["data_end"].strftime("%Y-%m-%d") if info["data_end"] else "N/A",
            "Records": info["records"],
        })

    # Create DataFrame and output
    df = pd.DataFrame(data)
    output.info(f"\nFound {total_stocks} stock(s) in Hikyuu database")
    if len(stock_infos) > 20:
        output.info(f"Showing first 20 stocks with data details:\n")
    else:
        output.info(f"\n")
    click.echo(df.to_string(index=False))

    if len(stock_infos) > 20:
        output.info(f"\n... and {len(stock_infos) - 20} more stocks")
        output.info("Use --format json or --format csv to see all stocks")


def _output_hikyuu_stocks_json(stock_infos: list, total_stocks: int, output: CLIOutput):
    """Output Hikyuu stock list in JSON format."""
    import json

    data = []
    for info in stock_infos:
        data.append({
            "code": info["code"],
            "market": info["market"],
            "data_start": info["data_start"].isoformat() if info["data_start"] else None,
            "data_end": info["data_end"].isoformat() if info["data_end"] else None,
            "records": info["records"] if isinstance(info["records"], int) else None,
        })

    output.info(f"Found {total_stocks} stock(s):")
    click.echo(json.dumps({"total": total_stocks, "stocks": data}, indent=2))


def _output_hikyuu_stocks_csv(stock_infos: list, total_stocks: int, output: CLIOutput):
    """Output Hikyuu stock list in CSV format."""
    import pandas as pd

    # Prepare data for CSV
    data = []
    for info in stock_infos:
        data.append({
            "code": info["code"],
            "market": info["market"],
            "data_start": info["data_start"].isoformat() if info["data_start"] else "",
            "data_end": info["data_end"].isoformat() if info["data_end"] else "",
            "records": info["records"] if isinstance(info["records"], int) else "",
        })

    # Create DataFrame and output as CSV
    df = pd.DataFrame(data)
    output.info(f"Found {total_stocks} stock(s):")
    click.echo(df.to_csv(index=False))
