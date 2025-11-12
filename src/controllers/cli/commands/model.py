"""
Model management CLI commands.

Commands:
- train: Train a new model
- list: List all models
- delete: Delete a model
"""

import asyncio
from typing import Optional

import click

from controllers.cli.di.container import Container
from controllers.cli.utils.output import CLIOutput, create_table, format_model_status
from controllers.cli.utils.validators import validate_file_path, validate_model_type
from domain.entities.model import Model, ModelType


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
    help="Path to training data file",
)
@click.option(
    "--config",
    "config_file",
    help="Path to model configuration file",
)
def train_command(
    model_type: str, name: str, training_data_path: Optional[str], config_file: Optional[str]
):
    """
    Train a new model.

    Example:
        hikyuu-qlib model train --type LightGBM --name my_model
        hikyuu-qlib model train --type LightGBM --name my_model --config config.yaml
    """
    output = CLIOutput()

    try:
        # Validate paths if provided
        if training_data_path:
            training_data_path = validate_file_path(training_data_path)

        if config_file:
            config_file = validate_file_path(config_file)

        # Run async function
        asyncio.run(_train_model(model_type, name, training_data_path, config_file, output))
    except Exception as e:
        output.error(f"Failed to train model: {str(e)}")
        raise click.Abort()


async def _train_model(
    model_type_str: str,
    name: str,
    training_data_path: Optional[str],
    config_file: Optional[str],
    output: CLIOutput,
):
    """
    Train a model (async implementation).

    Args:
        model_type_str: Model type string
        name: Model name
        training_data_path: Path to training data
        config_file: Path to config file
        output: CLI output instance
    """
    try:
        # Create model entity
        model_type = ModelType[model_type_str.upper()]
        model = Model(
            model_type=model_type,
            hyperparameters={},  # TODO: Load from config file
        )

        # Get use case from container
        container = Container()
        use_case = container.train_model_use_case

        # Execute training
        output.info(f"Training {model_type_str} model '{name}'...")

        # TODO: Load actual training data
        training_data = {}  # Placeholder

        trained_model = await use_case.execute(model=model, training_data=training_data)

        # Display results
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
    "--status",
    type=click.Choice(["PENDING", "TRAINING", "TRAINED", "FAILED"], case_sensitive=False),
    help="Filter by status",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Show detailed information",
)
def list_command(status: Optional[str], verbose: bool):
    """
    List all models.

    Example:
        hikyuu-qlib model list
        hikyuu-qlib model list --status TRAINED
        hikyuu-qlib model list --verbose
    """
    output = CLIOutput()

    try:
        # TODO: Implement listing logic when repository is ready
        output.warning("Model list command not yet fully implemented")
        output.info("This command will list all models in the system")

        if status:
            output.info(f"Filter: Status = {status.upper()}")

        if verbose:
            output.info("Verbose mode enabled")

        # Example table structure
        table = create_table(
            "Models",
            ["ID", "Name", "Type", "Status", "Created"]
        )
        # table.add_row("1", "my_model", "LightGBM", "TRAINED", "2023-01-01")

        output.print_table(table)

    except Exception as e:
        output.error(f"Failed to list models: {str(e)}")
        raise click.Abort()


@model_group.command(name="delete")
@click.argument("model_id", required=True)
@click.option(
    "--force",
    is_flag=True,
    help="Force deletion without confirmation",
)
def delete_command(model_id: str, force: bool):
    """
    Delete a model.

    Example:
        hikyuu-qlib model delete <model-id>
        hikyuu-qlib model delete <model-id> --force
    """
    output = CLIOutput()

    try:
        # Confirm deletion if not forced
        if not force:
            confirm = click.confirm(f"Are you sure you want to delete model '{model_id}'?")
            if not confirm:
                output.info("Deletion cancelled")
                return

        # TODO: Implement deletion logic when repository is ready
        output.warning("Model delete command not yet fully implemented")
        output.info(f"Would delete model: {model_id}")

        # output.success(f"Model '{model_id}' deleted successfully")

    except Exception as e:
        output.error(f"Failed to delete model: {str(e)}")
        raise click.Abort()
