"""
Model management CLI commands.

Commands:
- train: Train a new model
- list: List all models
- delete: Delete a model
"""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

import click

from controllers.cli.di.container import Container
from controllers.cli.utils.output import CLIOutput, create_table, format_model_status
from controllers.cli.utils.validators import validate_file_path, validate_model_type
from domain.entities.model import Model, ModelType
from domain.value_objects.stock_code import StockCode
from domain.value_objects.date_range import DateRange
from domain.value_objects.kline_type import KLineType
from utils.data_conversion import (
    convert_kline_to_training_data,
    load_from_file,
)


@asynccontextmanager
async def get_repository(ctx):
    """
    Async context manager for repository lifecycle management.

    Args:
        ctx: Click context

    Yields:
        Repository instance
    """
    container = ctx.obj if ctx.obj else Container()
    repository = container.model_repository
    await repository.initialize()
    try:
        yield repository
    finally:
        await repository.close()


@click.group(name="model")
def model_group():
    """Model management commands."""
    pass


@model_group.command(name="train")
@click.option(
    "--type",
    "model_type",
    required=True,
    help="Model type (LightGBM, XGBoost, etc.)",
    callback=lambda ctx, param, value: validate_model_type(value) if value else None,
)
@click.option(
    "--name",
    required=True,
    help="Model name",
)
@click.option(
    "--data",
    "training_data_path",
    help="Path to training data file (for separated approach)",
)
@click.option(
    "--code",
    "stock_code",
    help="Stock code (for integrated approach, e.g., sh600000)",
)
@click.option(
    "--start",
    "start_date",
    help="Start date (for integrated approach, format: YYYY-MM-DD)",
)
@click.option(
    "--end",
    "end_date",
    help="End date (for integrated approach, format: YYYY-MM-DD)",
)
@click.option(
    "--kline-type",
    "kline_type",
    type=click.Choice(["DAY", "WEEK", "MONTH", "MIN", "MIN5", "MIN15", "MIN30", "MIN60"], case_sensitive=False),
    default="DAY",
    help="K-line type (default: DAY)",
)
@click.option(
    "--config",
    "config_file",
    help="Path to model configuration file (JSON or YAML)",
)
@click.option(
    "--hyperparameters",
    "hyperparameters_json",
    help="Hyperparameters as JSON string (overrides config file)",
)
@click.option(
    "--param",
    "param_list",
    multiple=True,
    help="Individual hyperparameter in key=value format (can be used multiple times, highest precedence)",
)
def train_command(
    model_type: str,
    name: str,
    training_data_path: Optional[str],
    stock_code: Optional[str],
    start_date: Optional[str],
    end_date: Optional[str],
    kline_type: str,
    config_file: Optional[str],
    hyperparameters_json: Optional[str],
    param_list: tuple,
):
    """
    Train a new model.

    Supports two approaches:

    1. Separated approach (load from file):
        hikyuu-qlib model train --type LightGBM --name my_model --data train.csv

    2. Integrated approach (load from Hikyuu directly):
        hikyuu-qlib model train --type LightGBM --name my_model \\
            --code sh600000 --start 2023-01-01 --end 2023-12-31

    3. With custom config:
        hikyuu-qlib model train --type LightGBM --name my_model \\
            --data train.csv --config config.yaml

    4. With individual parameters:
        hikyuu-qlib model train --type LightGBM --name my_model \\
            --data train.csv --param n_estimators=200 --param learning_rate=0.1

    5. With JSON hyperparameters:
        hikyuu-qlib model train --type LightGBM --name my_model \\
            --data train.csv --hyperparameters '{"n_estimators": 200, "learning_rate": 0.1}'
    """
    output = CLIOutput()

    try:
        # Validate input: must provide either data file OR stock code parameters
        has_file = training_data_path is not None
        has_stock_params = all([stock_code, start_date, end_date])

        if not has_file and not has_stock_params:
            output.error("Must provide either:")
            output.info("  1. --data <file> (load from file)")
            output.info("  2. --code <code> --start <date> --end <date> (load from Hikyuu)")
            raise click.Abort()

        if has_file and has_stock_params:
            output.warning("Both --data and --code provided, will use --data")

        # Validate paths if provided
        if training_data_path:
            training_data_path = validate_file_path(training_data_path)

        if config_file:
            config_file = validate_file_path(config_file)

        # Run async function
        asyncio.run(
            _train_model(
                model_type,
                name,
                training_data_path,
                stock_code,
                start_date,
                end_date,
                kline_type,
                config_file,
                hyperparameters_json,
                param_list,
                output,
            )
        )
    except Exception as e:
        output.error(f"Failed to train model: {str(e)}")
        raise click.Abort()


async def _train_model(
    model_type_str: str,
    name: str,
    training_data_path: Optional[str],
    stock_code: Optional[str],
    start_date: Optional[str],
    end_date: Optional[str],
    kline_type: str,
    config_file: Optional[str],
    hyperparameters_json: Optional[str],
    param_list: tuple,
    output: CLIOutput,
):
    """
    Train a model (async implementation).

    Args:
        model_type_str: Model type string
        name: Model name
        training_data_path: Path to training data file (separated approach)
        stock_code: Stock code (integrated approach)
        start_date: Start date string (integrated approach)
        end_date: End date string (integrated approach)
        kline_type: K-line type
        config_file: Path to config file
        hyperparameters_json: Hyperparameters as JSON string
        param_list: List of key=value parameter strings
        output: CLI output instance
    """
    try:
        # Get container
        container = Container()

        # Step 1: Load training data
        training_data = None

        if training_data_path:
            # Separated approach: load from file
            output.info(f"Loading training data from file: {training_data_path}")
            training_data = load_from_file(training_data_path)
            output.success(f"Loaded {len(training_data)} records from file")

        elif stock_code and start_date and end_date:
            # Integrated approach: load from Hikyuu
            output.info(
                f"Loading data from Hikyuu: {stock_code} ({start_date} ~ {end_date})"
            )

            # Parse dates
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")

            # Load K-line data
            load_data_use_case = container.load_stock_data_use_case
            kline_data = await load_data_use_case.execute(
                stock_code=StockCode(stock_code),
                date_range=DateRange(start_date=start_dt, end_date=end_dt),
                kline_type=KLineType[kline_type.upper()],
            )

            if not kline_data:
                output.error(
                    f"No data found for {stock_code} in the specified date range"
                )
                raise click.Abort()

            output.success(f"Loaded {len(kline_data)} K-line records from Hikyuu")

            # Convert to training format
            output.info("Converting K-line data to training format...")
            training_data = convert_kline_to_training_data(
                kline_data,
                add_features=True,
                add_labels=True,
                label_horizon=1,
            )
            output.success(
                f"Converted to training data: {len(training_data)} records with features"
            )

        else:
            output.error("No data source provided")
            raise click.Abort()

        # Step 2: Load hyperparameters and create model entity
        model_type = ModelType[model_type_str.upper()]

        # Load hyperparameters from various sources
        from controllers.cli.utils.hyperparameters import load_hyperparameters
        try:
            hyperparameters = load_hyperparameters(
                model_type=model_type,
                cli_json=hyperparameters_json,
                config_file=config_file,
                param_list=param_list
            )
        except ValueError as e:
            output.error(f"Invalid hyperparameters: {str(e)}")
            raise click.Abort()

        # Display hyperparameters being used
        output.info(f"Using hyperparameters: {hyperparameters}")

        model = Model(
            model_type=model_type,
            hyperparameters=hyperparameters,
        )

        # Step 3: Execute training
        output.info(f"Training {model_type_str} model '{name}'...")

        # Initialize repository before training
        repository = container.model_repository
        await repository.initialize()

        train_use_case = container.train_model_use_case
        trained_model = await train_use_case.execute(
            model=model, training_data=training_data
        )

        # Close repository after training
        await repository.close()

        # Step 4: Display results
        output.success(f"Model '{name}' trained successfully!")
        output.info(f"Model ID: {trained_model.id}")
        output.info(f"Status: {trained_model.status.value}")

        if trained_model.metrics:
            output.info(f"Metrics: {trained_model.metrics}")

    except Exception as e:
        output.error(f"Error training model: {str(e)}")
        raise


@model_group.command(name="list")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "csv"], case_sensitive=False),
    default="table",
    help="Output format (default: table)",
)
@click.option(
    "--status",
    type=click.Choice(["TRAINED", "UNTRAINED", "DEPLOYED", "ARCHIVED"], case_sensitive=False),
    help="Filter by status",
)
@click.option(
    "--type",
    "model_type",
    type=click.Choice(["LGBM", "MLP", "LSTM", "GRU", "TRANSFORMER"], case_sensitive=False),
    help="Filter by model type",
)
@click.option(
    "--limit",
    type=int,
    help="Limit number of results",
)
@click.pass_context
def list_command(ctx, output_format: str, status: Optional[str], model_type: Optional[str], limit: Optional[int]):
    """
    List all models.

    Example:
        hikyuu-qlib model list
        hikyuu-qlib model list --status TRAINED
        hikyuu-qlib model list --format json
        hikyuu-qlib model list --type LGBM --limit 10
    """
    asyncio.run(_list_models(ctx, output_format, status, model_type, limit))


async def _list_models(ctx, output_format: str, status: Optional[str], model_type: Optional[str], limit: Optional[int]):
    """
    List models (async implementation).

    Args:
        ctx: Click context
        output_format: Output format (table/json/csv)
        status: Filter by status
        model_type: Filter by model type
        limit: Limit number of results
    """
    output = CLIOutput()

    try:
        async with get_repository(ctx) as repository:
            # Convert string filters to enums
            from domain.entities.model import ModelStatus, ModelType

            status_filter = ModelStatus[status.upper()] if status else None
            type_filter = ModelType[model_type.upper()] if model_type else None

            # Query models
            models = await repository.list_models(
                status=status_filter,
                model_type=type_filter,
                limit=limit
            )

            # Handle empty results
            if not models:
                output.info("No models found")
                return

            # Format output based on requested format
            if output_format == "json":
                _output_json(models, output)
            elif output_format == "csv":
                _output_csv(models, output)
            else:  # table (default)
                _output_table(models, output)

    except Exception as e:
        output.error(f"Failed to list models: {str(e)}")
        raise click.Abort()


def _output_table(models, output: CLIOutput):
    """Output models in table format."""
    import pandas as pd

    # Prepare data for table
    data = []
    for model in models:
        # Format metrics
        metrics_str = ""
        if model.metrics:
            key_metrics = ["train_r2", "test_r2", "train_rmse", "test_rmse"]
            metric_parts = [
                f"{k}={v:.4f}"
                for k, v in model.metrics.items()
                if k in key_metrics
            ]
            metrics_str = ", ".join(metric_parts[:2])  # Show first 2 metrics

        # Format training date
        date_str = model.training_date.strftime("%Y-%m-%d %H:%M") if model.training_date else "N/A"

        data.append({
            "ID": model.id[:8] + "...",  # Truncate ID for display
            "Type": model.model_type.value,
            "Status": model.status.value,
            "Training Date": date_str,
            "Metrics": metrics_str or "N/A"
        })

    # Create DataFrame and output
    df = pd.DataFrame(data)
    output.info(f"\nFound {len(models)} model(s):\n")
    click.echo(df.to_string(index=False))


def _output_json(models, output: CLIOutput):
    """Output models in JSON format."""
    import json

    data = []
    for model in models:
        data.append({
            "id": model.id,
            "model_type": model.model_type.value,
            "status": model.status.value,
            "training_date": model.training_date.isoformat() if model.training_date else None,
            "metrics": model.metrics,
            "hyperparameters": model.hyperparameters
        })

    output.info(f"Found {len(models)} model(s):")
    click.echo(json.dumps(data, indent=2))


def _output_csv(models, output: CLIOutput):
    """Output models in CSV format."""
    import pandas as pd

    # Prepare data for CSV
    data = []
    for model in models:
        # Flatten metrics into separate columns
        row = {
            "id": model.id,
            "model_type": model.model_type.value,
            "status": model.status.value,
            "training_date": model.training_date.isoformat() if model.training_date else "",
        }

        # Add metrics as separate columns
        if model.metrics:
            for key, value in model.metrics.items():
                row[f"metric_{key}"] = value

        data.append(row)

    # Create DataFrame and output as CSV
    df = pd.DataFrame(data)
    output.info(f"Found {len(models)} model(s):")
    click.echo(df.to_csv(index=False))


@model_group.command(name="delete")
@click.argument("model_id", required=True)
@click.option(
    "--force",
    is_flag=True,
    help="Force deletion without confirmation",
)
@click.pass_context
def delete_command(ctx, model_id: str, force: bool):
    """
    Delete a model.

    Example:
        hikyuu-qlib model delete <model-id>
        hikyuu-qlib model delete <model-id> --force
    """
    asyncio.run(_delete_model(ctx, model_id, force))


async def _delete_model(ctx, model_id: str, force: bool):
    """
    Delete a model (async implementation).

    Args:
        ctx: Click context
        model_id: Model ID to delete
        force: Skip confirmation if True
    """
    output = CLIOutput()

    try:
        async with get_repository(ctx) as repository:
            # Check if model exists
            model = await repository.find_by_id(model_id)
            if model is None:
                output.error(f"Model with id '{model_id}' not found")
                raise click.exceptions.Exit(1)

            # Display model info
            output.info(f"Model to delete:")
            output.info(f"  ID: {model.id}")
            output.info(f"  Type: {model.model_type.value}")
            output.info(f"  Status: {model.status.value}")
            if model.training_date:
                output.info(f"  Trained: {model.training_date.strftime('%Y-%m-%d %H:%M')}")

            # Confirm deletion if not forced
            if not force:
                confirm = click.confirm(f"\nAre you sure you want to delete this model?")
                if not confirm:
                    output.info("Deletion cancelled")
                    return

            # Delete model
            await repository.delete(model_id)
            output.success(f"Model '{model_id}' deleted successfully")

    except click.exceptions.Exit:
        # Re-raise Exit exception to preserve exit code
        raise
    except Exception as e:
        output.error(f"Failed to delete model: {str(e)}")
        raise click.exceptions.Exit(1)


@model_group.command(name="train-index")
@click.option(
    "--type",
    "model_type",
    required=True,
    help="Model type (LightGBM, XGBoost, etc.)",
    callback=lambda ctx, param, value: validate_model_type(value) if value else None,
)
@click.option(
    "--name",
    required=True,
    help="Model name",
)
@click.option(
    "--index",
    "index_name",
    required=True,
    help="Index name (e.g., 沪深300, 中证500, 上证50)",
)
@click.option(
    "--start",
    "start_date",
    required=True,
    help="Start date (format: YYYY-MM-DD)",
)
@click.option(
    "--end",
    "end_date",
    required=True,
    help="End date (format: YYYY-MM-DD)",
)
@click.option(
    "--kline-type",
    "kline_type",
    type=click.Choice(["DAY", "WEEK", "MONTH", "MIN", "MIN5", "MIN15", "MIN30", "MIN60"], case_sensitive=False),
    default="DAY",
    help="K-line type (default: DAY)",
)
@click.option(
    "--max-stocks",
    type=int,
    help="Maximum number of stocks to process (for testing)",
)
@click.option(
    "--output",
    "output_file",
    help="Save combined training data to file (optional)",
)
def train_index_command(
    model_type: str,
    name: str,
    index_name: str,
    start_date: str,
    end_date: str,
    kline_type: str,
    max_stocks: Optional[int],
    output_file: Optional[str],
):
    """
    Train a model on index constituents.

    This command will:
    1. Get all constituent stocks of the specified index
    2. Load historical data for each stock
    3. Combine all data into a single training dataset
    4. Train a model on the combined dataset

    Examples:
        # Train on HS300 (all 300 stocks)
        hikyuu-qlib model train-index --type LGBM --name hs300_model \\
            --index 沪深300 --start 2023-01-01 --end 2023-12-31

        # Train on first 50 stocks (for testing)
        hikyuu-qlib model train-index --type LGBM --name hs300_test \\
            --index 沪深300 --start 2023-01-01 --end 2023-12-31 \\
            --max-stocks 50

        # Save training data to file
        hikyuu-qlib model train-index --type LGBM --name hs300_model \\
            --index 沪深300 --start 2023-01-01 --end 2023-12-31 \\
            --output data/hs300_training.csv
    """
    output = CLIOutput()

    try:
        # Parse dates
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        # Run async function
        asyncio.run(
            _train_model_on_index(
                model_type_str=model_type,
                model_name=name,
                index_name=index_name,
                start_dt=start_dt,
                end_dt=end_dt,
                kline_type=kline_type,
                max_stocks=max_stocks,
                output_file=output_file,
                output=output,
            )
        )
    except Exception as e:
        output.error(f"Failed to train model on index: {str(e)}")
        raise click.Abort()


async def _train_model_on_index(
    model_type_str: str,
    model_name: str,
    index_name: str,
    start_dt: datetime,
    end_dt: datetime,
    kline_type: str,
    max_stocks: Optional[int],
    output_file: Optional[str],
    output: CLIOutput,
):
    """
    Train a model on index constituents (async implementation).
    """
    from utils.batch_training import train_model_on_index

    try:
        # Get container
        container = Container()

        # Create date range
        date_range = DateRange(start_date=start_dt, end_date=end_dt)

        # Convert model type
        model_type = ModelType[model_type_str.upper()]

        # Display info
        output.info(f"训练指数模型: {index_name}")
        output.info(f"  模型类型: {model_type_str}")
        output.info(f"  模型名称: {model_name}")
        output.info(f"  日期范围: {start_dt.date()} ~ {end_dt.date()}")
        if max_stocks:
            output.info(f"  最大股票数: {max_stocks}")

        # Train model
        trained_model = await train_model_on_index(
            index_name=index_name,
            model_type=model_type,
            model_name=model_name,
            date_range=date_range,
            kline_type=KLineType[kline_type.upper()],
            data_provider=container.data_provider,
            model_trainer=container.model_trainer,
            model_repository=container.model_repository,
            max_stocks=max_stocks
        )

        # Display results
        output.success(f"模型 '{model_name}' 训练成功!")
        output.info(f"模型ID: {trained_model.id}")
        output.info(f"状态: {trained_model.status.value}")

        if trained_model.metrics:
            output.info("指标:")
            for key, value in trained_model.metrics.items():
                output.info(f"  {key}: {value}")

    except Exception as e:
        output.error(f"训练失败: {str(e)}")
        raise
