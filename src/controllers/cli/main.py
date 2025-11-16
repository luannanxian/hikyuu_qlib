"""
Main CLI entry point for Hikyuu × Qlib Trading Platform.

Integrates all command groups:
- data: Data management commands
- model: Model management commands
- config: Configuration commands
"""

import click

from controllers.cli.commands.config import config_group
from controllers.cli.commands.data import data_group
from controllers.cli.commands.model import model_group


@click.group()
@click.version_option(version="0.1.0", prog_name="hikyuu-qlib")
def cli():
    """
    Hikyuu × Qlib Trading Platform CLI

    A command-line interface for quantitative trading with Hikyuu and Qlib.

    Commands:
        data    - Load and manage stock data
        model   - Train and manage trading models
        config  - View and update configuration

    Examples:
        hikyuu-qlib data load --code sh600000 --start 2023-01-01 --end 2023-12-31
        hikyuu-qlib model train --type LGBM --name my_model
        hikyuu-qlib config show
    """


# Register command groups
cli.add_command(data_group)
cli.add_command(model_group)
cli.add_command(config_group)


if __name__ == "__main__":
    cli()
