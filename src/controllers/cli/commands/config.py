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
@click.option(
    "--key",
    required=True,
    help="Configuration key (e.g., HIKYUU_DATA_PATH)",
)
@click.option(
    "--value",
    required=True,
    help="Configuration value",
)
def set_command(key: str, value: str):
    """
    Set configuration value.

    Example:
        hikyuu-qlib config set --key HIKYUU_DATA_PATH --value /path/to/data
        hikyuu-qlib config set --key INITIAL_CAPITAL --value 200000
    """
    output = CLIOutput()

    try:
        # TODO: Implement persistent configuration updates
        output.warning("Config set command not yet fully implemented")
        output.info(f"Would set: {key} = {value}")

        output.info("\nNote: Configuration changes will not persist between sessions")
        output.info("To make permanent changes, edit the .env file or environment variables")

    except Exception as e:
        output.error(f"Failed to set configuration: {str(e)}")
        raise click.Abort()
