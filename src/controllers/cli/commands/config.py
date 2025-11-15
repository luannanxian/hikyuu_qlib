"""
Configuration CLI commands.

Commands:
- show: Display current configuration
- set: Update configuration settings
"""

import asyncio
from typing import Optional

import click

from controllers.cli.di.container import Container
from controllers.cli.utils.output import CLIOutput


@click.group(name="config")
def config_group():
    """Configuration management commands."""
    pass


@config_group.command(name="show")
@click.option(
    "--section",
    type=click.Choice(["all", "data", "model", "backtest"], case_sensitive=False),
    default="all",
    help="Configuration section to display",
)
def show_command(section: str):
    """
    Display current configuration.

    Example:
        hikyuu-qlib config show
        hikyuu-qlib config show --section data
    """
    output = CLIOutput()

    try:
        # Get container and settings
        container = Container()
        settings = container.settings

        output.info(f"Configuration ({section}):")
        output.print("")

        if section in ["all", "data"]:
            output.print("[bold cyan]Data Source Settings:[/bold cyan]")
            output.print(f"  HIKYUU_DATA_PATH: {settings.HIKYUU_DATA_PATH}")
            output.print(f"  QLIB_DATA_PATH: {settings.QLIB_DATA_PATH}")
            output.print("")

        if section in ["all", "model"]:
            output.print("[bold cyan]Model Settings:[/bold cyan]")
            output.print(f"  MODEL_STORAGE_PATH: {settings.MODEL_STORAGE_PATH}")
            output.print(f"  DEFAULT_MODEL_TYPE: {settings.DEFAULT_MODEL_TYPE}")
            output.print("")

        if section in ["all", "backtest"]:
            output.print("[bold cyan]Backtest Settings:[/bold cyan]")
            output.print(f"  INITIAL_CAPITAL: {settings.INITIAL_CAPITAL}")
            output.print(f"  COMMISSION_RATE: {settings.COMMISSION_RATE}")
            output.print("")

        if section in ["all"]:
            output.print("[bold cyan]Application Settings:[/bold cyan]")
            output.print(f"  APP_NAME: {settings.APP_NAME}")
            output.print(f"  APP_VERSION: {settings.APP_VERSION}")
            output.print(f"  ENVIRONMENT: {settings.ENVIRONMENT}")
            output.print(f"  LOG_LEVEL: {settings.LOG_LEVEL}")

    except Exception as e:
        output.error(f"Failed to show configuration: {str(e)}")
        raise click.Abort()


@config_group.command(name="set")
@click.argument("key", required=True)
@click.argument("value", required=True)
@click.option(
    "--persist",
    type=click.Choice(["env", "yaml"], case_sensitive=False),
    default="yaml",
    help="Persistence method: 'env' (.env file) or 'yaml' (config.yaml)",
)
def set_command(key: str, value: str, persist: str):
    """
    Set configuration value.

    Supports persisting configuration to .env file or config.yaml.

    Valid configuration keys:
    - HIKYUU_DATA_PATH: Path to Hikyuu data directory
    - QLIB_DATA_PATH: Path to Qlib data directory
    - MODEL_STORAGE_PATH: Path to store trained models
    - DEFAULT_MODEL_TYPE: Default model type (LightGBM, LSTM, etc.)
    - INITIAL_CAPITAL: Initial capital for backtesting (float)
    - COMMISSION_RATE: Commission rate for backtesting (float 0-1)
    - LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - ENVIRONMENT: Environment (dev, test, prod)

    Examples:
        # Set Hikyuu data path (saved to YAML by default)
        hikyuu-qlib config set HIKYUU_DATA_PATH /path/to/hikyuu/data

        # Set initial capital (saved to YAML)
        hikyuu-qlib config set INITIAL_CAPITAL 200000

        # Set log level and persist to .env file
        hikyuu-qlib config set LOG_LEVEL DEBUG --persist env

        # Set commission rate
        hikyuu-qlib config set COMMISSION_RATE 0.0005
    """
    output = CLIOutput()

    try:
        # Run async function
        asyncio.run(_set_config(key, value, persist, output))

    except Exception as e:
        output.error(f"Failed to set configuration: {str(e)}")
        raise click.Abort()


async def _set_config(key: str, value: str, persist: str, output: CLIOutput):
    """
    Set configuration value (async implementation).

    Args:
        key: Configuration key
        value: Configuration value
        persist: Persistence method (env or yaml)
        output: CLI output instance
    """
    from pathlib import Path

    # Validate and parse key-value
    try:
        parsed_value = _parse_config_value(key, value)
    except ValueError as e:
        output.error(str(e))
        raise click.Abort()

    # Get container
    container = Container()

    if persist == "yaml":
        # Save to YAML config file
        await _save_to_yaml(key, parsed_value, container, output)
    elif persist == "env":
        # Save to .env file
        _save_to_env(key, value, output)
    else:
        output.error(f"Unknown persist method: {persist}")
        raise click.Abort()

    # Show success message
    output.success(f"Configuration updated: {key} = {parsed_value}")
    output.info(f"Persisted to: {persist}")


def _parse_config_value(key: str, value: str):
    """
    Parse and validate configuration value.

    Args:
        key: Configuration key
        value: Configuration value string

    Returns:
        Parsed value with appropriate type

    Raises:
        ValueError: If key is invalid or value cannot be parsed
    """
    # Define valid keys and their types
    VALID_KEYS = {
        "HIKYUU_DATA_PATH": str,
        "QLIB_DATA_PATH": str,
        "MODEL_STORAGE_PATH": str,
        "DEFAULT_MODEL_TYPE": str,
        "INITIAL_CAPITAL": float,
        "COMMISSION_RATE": float,
        "LOG_LEVEL": str,
        "ENVIRONMENT": str,
        "HIKYUU_CONFIG_FILE": str,
        "DATABASE_URL": str,
        "LOG_FILE_PATH": str,
    }

    if key not in VALID_KEYS:
        raise ValueError(
            f"Invalid configuration key: {key}. "
            f"Valid keys: {', '.join(VALID_KEYS.keys())}"
        )

    expected_type = VALID_KEYS[key]

    # Parse value based on expected type
    try:
        if expected_type == float:
            parsed = float(value)
        elif expected_type == int:
            parsed = int(value)
        elif expected_type == bool:
            parsed = value.lower() in ("true", "yes", "1")
        else:  # str
            parsed = value

        # Additional validation for specific keys
        if key == "LOG_LEVEL":
            valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            if parsed.upper() not in valid_levels:
                raise ValueError(
                    f"Invalid LOG_LEVEL: {parsed}. Must be one of {valid_levels}"
                )
            parsed = parsed.upper()

        elif key == "ENVIRONMENT":
            valid_envs = ["dev", "test", "prod"]
            if parsed.lower() not in valid_envs:
                raise ValueError(
                    f"Invalid ENVIRONMENT: {parsed}. Must be one of {valid_envs}"
                )
            parsed = parsed.lower()

        elif key == "INITIAL_CAPITAL":
            if parsed <= 0:
                raise ValueError("INITIAL_CAPITAL must be positive")

        elif key == "COMMISSION_RATE":
            if parsed < 0 or parsed > 1:
                raise ValueError("COMMISSION_RATE must be between 0 and 1")

        return parsed

    except ValueError as e:
        raise ValueError(f"Invalid value for {key}: {e}")


async def _save_to_yaml(key: str, value, container, output: CLIOutput):
    """
    Save configuration to YAML file.

    Args:
        key: Configuration key
        value: Parsed configuration value
        container: Dependency injection container
        output: CLI output instance
    """
    from domain.value_objects.configuration import (
        DataSourceConfig,
        ModelConfig,
        BacktestConfig,
    )
    from decimal import Decimal

    # Get config repository
    config_repository = container.config_repository

    # Load existing configuration
    use_case = container.load_configuration_use_case
    try:
        config = await use_case.execute()
    except Exception:
        # If no config exists, create default one
        from infrastructure.config.settings import Settings
        settings = Settings()
        config = None

    # Update appropriate section based on key
    if key in ["HIKYUU_DATA_PATH", "QLIB_DATA_PATH"]:
        # Data source config
        if config and config.data_source:
            ds_config = config.data_source
            if key == "HIKYUU_DATA_PATH":
                ds_config = DataSourceConfig(
                    hikyuu_path=value,
                    qlib_path=ds_config.qlib_path
                )
            else:
                ds_config = DataSourceConfig(
                    hikyuu_path=ds_config.hikyuu_path,
                    qlib_path=value
                )
        else:
            if key == "HIKYUU_DATA_PATH":
                ds_config = DataSourceConfig(hikyuu_path=value, qlib_path=None)
            else:
                ds_config = DataSourceConfig(hikyuu_path=None, qlib_path=value)

        await config_repository.save_config("data_source", ds_config)

    elif key in ["MODEL_STORAGE_PATH", "DEFAULT_MODEL_TYPE"]:
        # Model config
        if config and config.model:
            mc_config = config.model
            hyperparams = mc_config.hyperparameters or {}
        else:
            hyperparams = {}

        if key == "DEFAULT_MODEL_TYPE":
            mc_config = ModelConfig(
                default_type=value,
                hyperparameters=hyperparams
            )
        else:
            # MODEL_STORAGE_PATH is handled by settings, not in YAML
            output.warning(f"{key} is typically set via environment variables or .env file")
            return

        await config_repository.save_config("model:default", mc_config)

    elif key in ["INITIAL_CAPITAL", "COMMISSION_RATE"]:
        # Backtest config
        if config and config.backtest:
            bt_config = config.backtest
            if key == "INITIAL_CAPITAL":
                bt_config = BacktestConfig(
                    initial_capital=Decimal(str(value)),
                    commission_rate=bt_config.commission_rate,
                    slippage_rate=bt_config.slippage_rate
                )
            else:
                bt_config = BacktestConfig(
                    initial_capital=bt_config.initial_capital,
                    commission_rate=Decimal(str(value)),
                    slippage_rate=bt_config.slippage_rate
                )
        else:
            if key == "INITIAL_CAPITAL":
                bt_config = BacktestConfig(
                    initial_capital=Decimal(str(value)),
                    commission_rate=Decimal("0.0003"),
                    slippage_rate=Decimal("0.001")
                )
            else:
                bt_config = BacktestConfig(
                    initial_capital=Decimal("100000"),
                    commission_rate=Decimal(str(value)),
                    slippage_rate=Decimal("0.001")
                )

        await config_repository.save_config("backtest", bt_config)

    else:
        # Other settings are typically in .env
        output.warning(f"{key} is typically set via environment variables or .env file")
        output.info(f"Use --persist env to save to .env file")


def _save_to_env(key: str, value: str, output: CLIOutput):
    """
    Save configuration to .env file.

    Args:
        key: Configuration key
        value: Configuration value string
        output: CLI output instance
    """
    from pathlib import Path

    env_path = Path(".env")

    # Read existing .env file
    if env_path.exists():
        with open(env_path, "r") as f:
            lines = f.readlines()
    else:
        lines = []

    # Update or append key-value
    key_found = False
    for i, line in enumerate(lines):
        if line.strip().startswith(f"{key}="):
            lines[i] = f"{key}={value}\n"
            key_found = True
            break

    if not key_found:
        lines.append(f"{key}={value}\n")

    # Write back to .env file
    with open(env_path, "w") as f:
        f.writelines(lines)

    output.info(f"Updated .env file: {env_path.absolute()}")
