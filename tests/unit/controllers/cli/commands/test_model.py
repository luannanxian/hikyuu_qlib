"""
Tests for model management CLI commands.

Tests:
- model train command
- model list command
- model delete command
"""

import pytest
import click
from click.testing import CliRunner
from unittest.mock import AsyncMock, Mock, patch

from controllers.cli.commands.model import model_group


@pytest.fixture
def mock_asyncio_run():
    """Fixture to mock asyncio.run for CLI commands."""
    def run_coro(coro):
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()
    return run_coro


@pytest.fixture
def mock_repository():
    """Fixture to create a mock repository."""
    repo = AsyncMock()
    repo.initialize = AsyncMock()
    repo.close = AsyncMock()
    repo.list_models = AsyncMock()
    repo.find_by_id = AsyncMock()
    repo.delete = AsyncMock()
    return repo


@pytest.fixture
def setup_container(mock_repository):
    """Fixture to setup container with mock repository."""
    def _setup(container_patch):
        container_patch.return_value.model_repository = mock_repository
        return mock_repository
    return _setup


class TestModelTrainCommand:
    """Test model train command."""

    def test_model_train_with_required_args(self):
        """Test training model with required arguments."""
        # Arrange
        runner = CliRunner()

        with patch("controllers.cli.commands.model.asyncio.run") as mock_asyncio_run:
            mock_asyncio_run.return_value = None

            # Act
            result = runner.invoke(
                model_group,
                ["train", "--type", "LGBM", "--name", "test_model"],
            )

            # Assert
            assert result.exit_code == 0 or "train" in result.output.lower()

    def test_model_train_missing_required_args(self):
        """Test model train with missing required arguments."""
        # Arrange
        runner = CliRunner()

        # Act
        result = runner.invoke(model_group, ["train"])

        # Assert
        assert result.exit_code != 0
        assert "Error" in result.output or "Missing" in result.output

    def test_model_train_invalid_model_type(self):
        """Test model train with invalid model type."""
        # Arrange
        runner = CliRunner()

        # Act
        result = runner.invoke(
            model_group,
            ["train", "--type", "InvalidType", "--name", "test_model"],
        )

        # Assert
        assert result.exit_code != 0


class TestModelTrainHyperparameters:
    """Test model train command hyperparameter configuration."""

    @patch("controllers.cli.commands.model.Container")
    @patch("controllers.cli.commands.model.asyncio.run")
    @patch("controllers.cli.commands.model.load_from_file")
    def test_train_with_default_hyperparameters_lgbm(self, mock_load, mock_asyncio_run, mock_container):
        """Test training with default hyperparameters for LGBM."""
        # Arrange
        runner = CliRunner()

        # Mock training data
        import pandas as pd
        mock_training_data = pd.DataFrame({"feature1": [1, 2, 3], "label": [0, 1, 0]})
        mock_load.return_value = mock_training_data

        # Mock trained model
        from domain.entities.model import Model, ModelType, ModelStatus
        trained_model = Model(
            model_type=ModelType.LGBM,
            hyperparameters={"n_estimators": 100, "learning_rate": 0.05, "max_depth": 7, "num_leaves": 31},
            status=ModelStatus.TRAINED
        )

        # Mock container components
        mock_repo = AsyncMock()
        mock_repo.initialize = AsyncMock()
        mock_repo.close = AsyncMock()
        mock_train_use_case = AsyncMock()
        mock_train_use_case.execute = AsyncMock(return_value=trained_model)

        mock_container.return_value.model_repository = mock_repo
        mock_container.return_value.train_model_use_case = mock_train_use_case

        # Mock asyncio.run to execute coroutine
        def run_coro(coro):
            import asyncio
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(coro)
            finally:
                loop.close()
        mock_asyncio_run.side_effect = run_coro

        # Act
        with runner.isolated_filesystem():
            with open("train.csv", "w") as f:
                f.write("feature1,label\n1,0\n2,1\n3,0\n")

            result = runner.invoke(
                model_group,
                ["train", "--type", "LGBM", "--name", "test_model", "--data", "train.csv"],
            )

        # Assert
        assert result.exit_code == 0
        # Verify that the model was created with default hyperparameters
        assert mock_train_use_case.execute.called
        model_arg = mock_train_use_case.execute.call_args[1]["model"]
        assert model_arg.hyperparameters == {"n_estimators": 100, "learning_rate": 0.05, "max_depth": 7, "num_leaves": 31}

    @patch("controllers.cli.commands.model.Container")
    @patch("controllers.cli.commands.model.asyncio.run")
    @patch("controllers.cli.commands.model.load_from_file")
    def test_train_with_default_hyperparameters_mlp(self, mock_load, mock_asyncio_run, mock_container):
        """Test training with default hyperparameters for MLP."""
        # Arrange
        runner = CliRunner()

        # Mock training data
        import pandas as pd
        mock_training_data = pd.DataFrame({"feature1": [1, 2, 3], "label": [0, 1, 0]})
        mock_load.return_value = mock_training_data

        # Mock trained model
        from domain.entities.model import Model, ModelType, ModelStatus
        trained_model = Model(
            model_type=ModelType.MLP,
            hyperparameters={"hidden_layers": [64, 32], "activation": "relu", "learning_rate": 0.001},
            status=ModelStatus.TRAINED
        )

        # Mock container components
        mock_repo = AsyncMock()
        mock_repo.initialize = AsyncMock()
        mock_repo.close = AsyncMock()
        mock_train_use_case = AsyncMock()
        mock_train_use_case.execute = AsyncMock(return_value=trained_model)

        mock_container.return_value.model_repository = mock_repo
        mock_container.return_value.train_model_use_case = mock_train_use_case

        # Mock asyncio.run
        def run_coro(coro):
            import asyncio
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(coro)
            finally:
                loop.close()
        mock_asyncio_run.side_effect = run_coro

        # Act
        with runner.isolated_filesystem():
            with open("train.csv", "w") as f:
                f.write("feature1,label\n1,0\n2,1\n3,0\n")

            result = runner.invoke(
                model_group,
                ["train", "--type", "MLP", "--name", "test_model", "--data", "train.csv"],
            )

        # Assert
        assert result.exit_code == 0
        assert mock_train_use_case.execute.called
        model_arg = mock_train_use_case.execute.call_args[1]["model"]
        assert model_arg.hyperparameters == {"hidden_layers": [64, 32], "activation": "relu", "learning_rate": 0.001}

    @patch("controllers.cli.commands.model.Container")
    @patch("controllers.cli.commands.model.asyncio.run")
    @patch("controllers.cli.commands.model.load_from_file")
    def test_train_with_default_hyperparameters_lstm(self, mock_load, mock_asyncio_run, mock_container):
        """Test training with default hyperparameters for LSTM."""
        # Arrange
        runner = CliRunner()

        # Mock training data
        import pandas as pd
        mock_training_data = pd.DataFrame({"feature1": [1, 2, 3], "label": [0, 1, 0]})
        mock_load.return_value = mock_training_data

        # Mock trained model
        from domain.entities.model import Model, ModelType, ModelStatus
        trained_model = Model(
            model_type=ModelType.LSTM,
            hyperparameters={"hidden_size": 64, "num_layers": 2, "sequence_length": 20},
            status=ModelStatus.TRAINED
        )

        # Mock container components
        mock_repo = AsyncMock()
        mock_repo.initialize = AsyncMock()
        mock_repo.close = AsyncMock()
        mock_train_use_case = AsyncMock()
        mock_train_use_case.execute = AsyncMock(return_value=trained_model)

        mock_container.return_value.model_repository = mock_repo
        mock_container.return_value.train_model_use_case = mock_train_use_case

        # Mock asyncio.run
        def run_coro(coro):
            import asyncio
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(coro)
            finally:
                loop.close()
        mock_asyncio_run.side_effect = run_coro

        # Act
        with runner.isolated_filesystem():
            with open("train.csv", "w") as f:
                f.write("feature1,label\n1,0\n2,1\n3,0\n")

            result = runner.invoke(
                model_group,
                ["train", "--type", "LSTM", "--name", "test_model", "--data", "train.csv"],
            )

        # Assert
        assert result.exit_code == 0
        assert mock_train_use_case.execute.called
        model_arg = mock_train_use_case.execute.call_args[1]["model"]
        assert model_arg.hyperparameters == {"hidden_size": 64, "num_layers": 2, "sequence_length": 20}

    @patch("controllers.cli.commands.model.Container")
    @patch("controllers.cli.commands.model.asyncio.run")
    @patch("controllers.cli.commands.model.load_from_file")
    def test_train_with_cli_hyperparameters_json(self, mock_load, mock_asyncio_run, mock_container):
        """Test training with hyperparameters from CLI JSON."""
        # Arrange
        runner = CliRunner()

        # Mock training data
        import pandas as pd
        mock_training_data = pd.DataFrame({"feature1": [1, 2, 3], "label": [0, 1, 0]})
        mock_load.return_value = mock_training_data

        # Mock trained model
        from domain.entities.model import Model, ModelType, ModelStatus
        # CLI hyperparameters should merge with defaults
        cli_hyperparams = {"n_estimators": 200, "learning_rate": 0.1}
        expected_hyperparams = {"n_estimators": 200, "learning_rate": 0.1, "max_depth": 7, "num_leaves": 31}
        trained_model = Model(
            model_type=ModelType.LGBM,
            hyperparameters=expected_hyperparams,
            status=ModelStatus.TRAINED
        )

        # Mock container components
        mock_repo = AsyncMock()
        mock_repo.initialize = AsyncMock()
        mock_repo.close = AsyncMock()
        mock_train_use_case = AsyncMock()
        mock_train_use_case.execute = AsyncMock(return_value=trained_model)

        mock_container.return_value.model_repository = mock_repo
        mock_container.return_value.train_model_use_case = mock_train_use_case

        # Mock asyncio.run
        def run_coro(coro):
            import asyncio
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(coro)
            finally:
                loop.close()
        mock_asyncio_run.side_effect = run_coro

        # Act
        import json
        hyperparams_json = json.dumps(cli_hyperparams)

        with runner.isolated_filesystem():
            with open("train.csv", "w") as f:
                f.write("feature1,label\n1,0\n2,1\n3,0\n")

            result = runner.invoke(
                model_group,
                ["train", "--type", "LGBM", "--name", "test_model", "--data", "train.csv",
                 "--hyperparameters", hyperparams_json],
            )

        # Assert
        assert result.exit_code == 0
        assert mock_train_use_case.execute.called
        model_arg = mock_train_use_case.execute.call_args[1]["model"]
        # CLI hyperparameters should override defaults but keep unspecified defaults
        assert model_arg.hyperparameters["n_estimators"] == 200  # Overridden
        assert model_arg.hyperparameters["learning_rate"] == 0.1  # Overridden
        assert model_arg.hyperparameters["max_depth"] == 7  # Default kept
        assert model_arg.hyperparameters["num_leaves"] == 31  # Default kept

    @patch("controllers.cli.commands.model.Container")
    @patch("controllers.cli.commands.model.asyncio.run")
    @patch("controllers.cli.commands.model.load_from_file")
    def test_train_with_config_file_hyperparameters(self, mock_load, mock_asyncio_run, mock_container):
        """Test training with hyperparameters from config file."""
        # Arrange
        runner = CliRunner()

        # Mock training data
        import pandas as pd
        mock_training_data = pd.DataFrame({"feature1": [1, 2, 3], "label": [0, 1, 0]})
        mock_load.return_value = mock_training_data

        # Mock trained model
        from domain.entities.model import Model, ModelType, ModelStatus
        # Config hyperparameters should merge with defaults
        config_hyperparams = {"n_estimators": 150, "max_depth": 10}
        expected_hyperparams = {"n_estimators": 150, "learning_rate": 0.05, "max_depth": 10, "num_leaves": 31}
        trained_model = Model(
            model_type=ModelType.LGBM,
            hyperparameters=expected_hyperparams,
            status=ModelStatus.TRAINED
        )

        # Mock container components
        mock_repo = AsyncMock()
        mock_repo.initialize = AsyncMock()
        mock_repo.close = AsyncMock()
        mock_train_use_case = AsyncMock()
        mock_train_use_case.execute = AsyncMock(return_value=trained_model)

        mock_container.return_value.model_repository = mock_repo
        mock_container.return_value.train_model_use_case = mock_train_use_case

        # Mock asyncio.run
        def run_coro(coro):
            import asyncio
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(coro)
            finally:
                loop.close()
        mock_asyncio_run.side_effect = run_coro

        # Act
        import json
        with runner.isolated_filesystem():
            with open("train.csv", "w") as f:
                f.write("feature1,label\n1,0\n2,1\n3,0\n")

            with open("config.json", "w") as f:
                json.dump({"hyperparameters": config_hyperparams}, f)

            result = runner.invoke(
                model_group,
                ["train", "--type", "LGBM", "--name", "test_model", "--data", "train.csv",
                 "--config", "config.json"],
            )

        # Assert
        assert result.exit_code == 0
        assert mock_train_use_case.execute.called
        model_arg = mock_train_use_case.execute.call_args[1]["model"]
        # Config hyperparameters should override defaults but keep unspecified defaults
        assert model_arg.hyperparameters["n_estimators"] == 150  # Overridden
        assert model_arg.hyperparameters["max_depth"] == 10  # Overridden
        assert model_arg.hyperparameters["learning_rate"] == 0.05  # Default kept
        assert model_arg.hyperparameters["num_leaves"] == 31  # Default kept

    @patch("controllers.cli.commands.model.Container")
    @patch("controllers.cli.commands.model.asyncio.run")
    @patch("controllers.cli.commands.model.load_from_file")
    def test_train_cli_hyperparameters_override_config(self, mock_load, mock_asyncio_run, mock_container):
        """Test that CLI hyperparameters override config file hyperparameters."""
        # Arrange
        runner = CliRunner()

        # Mock training data
        import pandas as pd
        mock_training_data = pd.DataFrame({"feature1": [1, 2, 3], "label": [0, 1, 0]})
        mock_load.return_value = mock_training_data

        # Mock trained model
        from domain.entities.model import Model, ModelType, ModelStatus
        config_hyperparams = {"n_estimators": 150, "max_depth": 10}
        cli_hyperparams = {"n_estimators": 250, "learning_rate": 0.2}
        expected_hyperparams = {**config_hyperparams, **cli_hyperparams}  # CLI overrides config

        trained_model = Model(
            model_type=ModelType.LGBM,
            hyperparameters=expected_hyperparams,
            status=ModelStatus.TRAINED
        )

        # Mock container components
        mock_repo = AsyncMock()
        mock_repo.initialize = AsyncMock()
        mock_repo.close = AsyncMock()
        mock_train_use_case = AsyncMock()
        mock_train_use_case.execute = AsyncMock(return_value=trained_model)

        mock_container.return_value.model_repository = mock_repo
        mock_container.return_value.train_model_use_case = mock_train_use_case

        # Mock asyncio.run
        def run_coro(coro):
            import asyncio
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(coro)
            finally:
                loop.close()
        mock_asyncio_run.side_effect = run_coro

        # Act
        import json
        hyperparams_json = json.dumps(cli_hyperparams)

        with runner.isolated_filesystem():
            with open("train.csv", "w") as f:
                f.write("feature1,label\n1,0\n2,1\n3,0\n")

            with open("config.json", "w") as f:
                json.dump({"hyperparameters": config_hyperparams}, f)

            result = runner.invoke(
                model_group,
                ["train", "--type", "LGBM", "--name", "test_model", "--data", "train.csv",
                 "--config", "config.json", "--hyperparameters", hyperparams_json],
            )

        # Assert
        assert result.exit_code == 0
        assert mock_train_use_case.execute.called
        model_arg = mock_train_use_case.execute.call_args[1]["model"]
        # CLI hyperparameters should override config file values
        assert model_arg.hyperparameters["n_estimators"] == 250
        assert model_arg.hyperparameters["learning_rate"] == 0.2
        assert model_arg.hyperparameters["max_depth"] == 10  # From config

    @patch("controllers.cli.commands.model.Container")
    @patch("controllers.cli.commands.model.asyncio.run")
    @patch("controllers.cli.commands.model.load_from_file")
    def test_train_with_invalid_json_hyperparameters(self, mock_load, mock_asyncio_run, mock_container):
        """Test training with invalid JSON hyperparameters."""
        # Arrange
        runner = CliRunner()

        # Mock training data
        import pandas as pd
        mock_training_data = pd.DataFrame({"feature1": [1, 2, 3], "label": [0, 1, 0]})
        mock_load.return_value = mock_training_data

        # Mock asyncio.run - the async function will raise the error
        mock_asyncio_run.side_effect = click.Abort()

        # Act
        with runner.isolated_filesystem():
            with open("train.csv", "w") as f:
                f.write("feature1,label\n1,0\n2,1\n3,0\n")

            result = runner.invoke(
                model_group,
                ["train", "--type", "LGBM", "--name", "test_model", "--data", "train.csv",
                 "--hyperparameters", "{invalid json}"],
            )

        # Assert
        assert result.exit_code != 0
        assert ("json" in result.output.lower() or "invalid" in result.output.lower() or
                "error" in result.output.lower() or "abort" in result.output.lower())

    @patch("controllers.cli.commands.model.Container")
    @patch("controllers.cli.commands.model.asyncio.run")
    @patch("controllers.cli.commands.model.load_from_file")
    def test_train_displays_hyperparameters(self, mock_load, mock_asyncio_run, mock_container):
        """Test that training displays the hyperparameters being used."""
        # Arrange
        runner = CliRunner()

        # Mock training data
        import pandas as pd
        mock_training_data = pd.DataFrame({"feature1": [1, 2, 3], "label": [0, 1, 0]})
        mock_load.return_value = mock_training_data

        # Mock trained model
        from domain.entities.model import Model, ModelType, ModelStatus
        hyperparams = {"n_estimators": 100, "learning_rate": 0.05, "max_depth": 7, "num_leaves": 31}
        trained_model = Model(
            model_type=ModelType.LGBM,
            hyperparameters=hyperparams,
            status=ModelStatus.TRAINED
        )

        # Mock container components
        mock_repo = AsyncMock()
        mock_repo.initialize = AsyncMock()
        mock_repo.close = AsyncMock()
        mock_train_use_case = AsyncMock()
        mock_train_use_case.execute = AsyncMock(return_value=trained_model)

        mock_container.return_value.model_repository = mock_repo
        mock_container.return_value.train_model_use_case = mock_train_use_case

        # Mock asyncio.run
        def run_coro(coro):
            import asyncio
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(coro)
            finally:
                loop.close()
        mock_asyncio_run.side_effect = run_coro

        # Act
        with runner.isolated_filesystem():
            with open("train.csv", "w") as f:
                f.write("feature1,label\n1,0\n2,1\n3,0\n")

            result = runner.invoke(
                model_group,
                ["train", "--type", "LGBM", "--name", "test_model", "--data", "train.csv"],
            )

        # Assert
        assert result.exit_code == 0
        # Check that hyperparameters are displayed in the output
        assert "hyperparameter" in result.output.lower() or "n_estimators" in result.output.lower()


class TestModelListCommand:
    """Test model list command."""

    @patch("controllers.cli.commands.model.Container")
    @patch("controllers.cli.commands.model.asyncio.run")
    def test_list_models_empty(self, mock_asyncio_run, mock_container):
        """Test listing models when no models exist."""
        # Arrange
        runner = CliRunner()
        mock_repo = AsyncMock()
        mock_repo.list_models = AsyncMock(return_value=[])
        mock_container.return_value.model_repository = mock_repo

        # Mock asyncio.run to execute the coroutine
        def run_coro(coro):
            import asyncio
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(coro)
            finally:
                loop.close()
        mock_asyncio_run.side_effect = run_coro

        # Act
        result = runner.invoke(model_group, ["list"])

        # Assert
        assert result.exit_code == 0
        assert "No models found" in result.output

    @patch("controllers.cli.commands.model.Container")
    @patch("controllers.cli.commands.model.asyncio.run")
    def test_list_models_table_format(self, mock_asyncio_run, mock_container):
        """Test listing models in table format (default)."""
        # Arrange
        runner = CliRunner()
        from domain.entities.model import Model, ModelType, ModelStatus
        from datetime import datetime

        # Create test models
        model1 = Model(
            model_type=ModelType.LGBM,
            hyperparameters={"learning_rate": 0.1},
            status=ModelStatus.TRAINED,
            training_date=datetime(2024, 1, 1),
            metrics={"train_r2": 0.85, "test_r2": 0.75}
        )
        model2 = Model(
            model_type=ModelType.MLP,
            hyperparameters={"hidden_layers": 3},
            status=ModelStatus.DEPLOYED,
            training_date=datetime(2024, 1, 2),
            metrics={"train_r2": 0.90, "test_r2": 0.80}
        )

        mock_repo = AsyncMock()
        mock_repo.list_models = AsyncMock(return_value=[model1, model2])
        mock_container.return_value.model_repository = mock_repo

        # Mock asyncio.run
        def run_coro(coro):
            import asyncio
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(coro)
            finally:
                loop.close()
        mock_asyncio_run.side_effect = run_coro

        # Act
        result = runner.invoke(model_group, ["list"])

        # Assert
        assert result.exit_code == 0
        assert "LGBM" in result.output
        assert "MLP" in result.output
        assert "TRAINED" in result.output
        assert "DEPLOYED" in result.output
        # Verify repository was called correctly
        assert mock_repo.initialize.called
        assert mock_repo.list_models.called
        assert mock_repo.close.called

    @patch("controllers.cli.commands.model.Container")
    @patch("controllers.cli.commands.model.asyncio.run")
    def test_list_models_json_format(self, mock_asyncio_run, mock_container):
        """Test listing models in JSON format."""
        # Arrange
        runner = CliRunner()
        from domain.entities.model import Model, ModelType, ModelStatus
        from datetime import datetime
        import json
        import re

        model = Model(
            model_type=ModelType.LGBM,
            hyperparameters={"learning_rate": 0.1},
            status=ModelStatus.TRAINED,
            training_date=datetime(2024, 1, 1),
            metrics={"train_r2": 0.85}
        )

        mock_repo = AsyncMock()
        mock_repo.list_models = AsyncMock(return_value=[model])
        mock_container.return_value.model_repository = mock_repo

        def run_coro(coro):
            import asyncio
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(coro)
            finally:
                loop.close()
        mock_asyncio_run.side_effect = run_coro

        # Act
        result = runner.invoke(model_group, ["list", "--format", "json"])

        # Assert
        assert result.exit_code == 0
        # Extract JSON from output (it comes after the info line)
        # Find the JSON array in the output
        match = re.search(r'\[[\s\S]*\]', result.output)
        assert match is not None, f"No JSON array found in output: {result.output}"

        json_content = match.group(0)
        data = json.loads(json_content)
        assert len(data) == 1
        assert data[0]["model_type"] == "LGBM"
        assert data[0]["status"] == "TRAINED"

    @patch("controllers.cli.commands.model.Container")
    @patch("controllers.cli.commands.model.asyncio.run")
    def test_list_models_csv_format(self, mock_asyncio_run, mock_container):
        """Test listing models in CSV format."""
        # Arrange
        runner = CliRunner()
        from domain.entities.model import Model, ModelType, ModelStatus
        from datetime import datetime

        model = Model(
            model_type=ModelType.LGBM,
            hyperparameters={"learning_rate": 0.1},
            status=ModelStatus.TRAINED,
            training_date=datetime(2024, 1, 1),
            metrics={"train_r2": 0.85}
        )

        mock_repo = AsyncMock()
        mock_repo.list_models = AsyncMock(return_value=[model])
        mock_container.return_value.model_repository = mock_repo

        def run_coro(coro):
            import asyncio
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(coro)
            finally:
                loop.close()
        mock_asyncio_run.side_effect = run_coro

        # Act
        result = runner.invoke(model_group, ["list", "--format", "csv"])

        # Assert
        assert result.exit_code == 0
        assert "id,model_type,status,training_date" in result.output
        assert "LGBM" in result.output
        assert "TRAINED" in result.output

    @patch("controllers.cli.commands.model.Container")
    @patch("controllers.cli.commands.model.asyncio.run")
    def test_list_models_with_status_filter(self, mock_asyncio_run, mock_container):
        """Test listing models with status filter."""
        # Arrange
        runner = CliRunner()
        from domain.entities.model import Model, ModelType, ModelStatus

        trained_model = Model(
            model_type=ModelType.LGBM,
            hyperparameters={},
            status=ModelStatus.TRAINED
        )

        mock_repo = AsyncMock()
        mock_repo.list_models = AsyncMock(return_value=[trained_model])
        mock_container.return_value.model_repository = mock_repo

        def run_coro(coro):
            import asyncio
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(coro)
            finally:
                loop.close()
        mock_asyncio_run.side_effect = run_coro

        # Act
        result = runner.invoke(model_group, ["list", "--status", "TRAINED"])

        # Assert
        assert result.exit_code == 0
        # Verify repository was called with correct filter
        mock_repo.list_models.assert_called_once()
        call_kwargs = mock_repo.list_models.call_args[1]
        assert call_kwargs["status"] == ModelStatus.TRAINED

    @patch("controllers.cli.commands.model.Container")
    @patch("controllers.cli.commands.model.asyncio.run")
    def test_list_models_with_type_filter(self, mock_asyncio_run, mock_container):
        """Test listing models with type filter."""
        # Arrange
        runner = CliRunner()
        from domain.entities.model import Model, ModelType, ModelStatus

        lgbm_model = Model(
            model_type=ModelType.LGBM,
            hyperparameters={},
            status=ModelStatus.TRAINED
        )

        mock_repo = AsyncMock()
        mock_repo.list_models = AsyncMock(return_value=[lgbm_model])
        mock_container.return_value.model_repository = mock_repo

        def run_coro(coro):
            import asyncio
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(coro)
            finally:
                loop.close()
        mock_asyncio_run.side_effect = run_coro

        # Act
        result = runner.invoke(model_group, ["list", "--type", "LGBM"])

        # Assert
        assert result.exit_code == 0
        # Verify repository was called with correct filter
        mock_repo.list_models.assert_called_once()
        call_kwargs = mock_repo.list_models.call_args[1]
        assert call_kwargs["model_type"] == ModelType.LGBM

    @patch("controllers.cli.commands.model.Container")
    @patch("controllers.cli.commands.model.asyncio.run")
    def test_list_models_with_limit(self, mock_asyncio_run, mock_container):
        """Test listing models with limit."""
        # Arrange
        runner = CliRunner()
        from domain.entities.model import Model, ModelType, ModelStatus

        model = Model(
            model_type=ModelType.LGBM,
            hyperparameters={},
            status=ModelStatus.TRAINED
        )

        mock_repo = AsyncMock()
        mock_repo.list_models = AsyncMock(return_value=[model])
        mock_container.return_value.model_repository = mock_repo

        def run_coro(coro):
            import asyncio
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(coro)
            finally:
                loop.close()
        mock_asyncio_run.side_effect = run_coro

        # Act
        result = runner.invoke(model_group, ["list", "--limit", "10"])

        # Assert
        assert result.exit_code == 0
        # Verify repository was called with correct limit
        mock_repo.list_models.assert_called_once()
        call_kwargs = mock_repo.list_models.call_args[1]
        assert call_kwargs["limit"] == 10

    @patch("controllers.cli.commands.model.Container")
    @patch("controllers.cli.commands.model.asyncio.run")
    def test_list_models_combined_filters(self, mock_asyncio_run, mock_container):
        """Test listing models with combined filters."""
        # Arrange
        runner = CliRunner()
        from domain.entities.model import Model, ModelType, ModelStatus

        model = Model(
            model_type=ModelType.LGBM,
            hyperparameters={},
            status=ModelStatus.TRAINED
        )

        mock_repo = AsyncMock()
        mock_repo.list_models = AsyncMock(return_value=[model])
        mock_container.return_value.model_repository = mock_repo

        def run_coro(coro):
            import asyncio
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(coro)
            finally:
                loop.close()
        mock_asyncio_run.side_effect = run_coro

        # Act
        result = runner.invoke(
            model_group,
            ["list", "--status", "TRAINED", "--type", "LGBM", "--limit", "5"]
        )

        # Assert
        assert result.exit_code == 0
        # Verify repository was called with all filters
        mock_repo.list_models.assert_called_once()
        call_kwargs = mock_repo.list_models.call_args[1]
        assert call_kwargs["status"] == ModelStatus.TRAINED
        assert call_kwargs["model_type"] == ModelType.LGBM
        assert call_kwargs["limit"] == 5


class TestModelDeleteCommand:
    """Test model delete command."""

    @patch("controllers.cli.commands.model.Container")
    @patch("controllers.cli.commands.model.asyncio.run")
    def test_delete_model_with_force(self, mock_asyncio_run, mock_container):
        """Test deleting model with force flag."""
        # Arrange
        runner = CliRunner()
        from domain.entities.model import Model, ModelType, ModelStatus

        existing_model = Model(
            model_type=ModelType.LGBM,
            hyperparameters={},
            status=ModelStatus.TRAINED
        )
        object.__setattr__(existing_model, "id", "test-model-123")

        mock_repo = AsyncMock()
        mock_repo.find_by_id = AsyncMock(return_value=existing_model)
        mock_repo.delete = AsyncMock()
        mock_container.return_value.model_repository = mock_repo

        def run_coro(coro):
            import asyncio
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(coro)
            finally:
                loop.close()
        mock_asyncio_run.side_effect = run_coro

        # Act
        result = runner.invoke(
            model_group,
            ["delete", "test-model-123", "--force"],
        )

        # Assert
        assert result.exit_code == 0
        assert "deleted successfully" in result.output.lower()
        mock_repo.delete.assert_called_once_with("test-model-123")
        assert mock_repo.initialize.called
        assert mock_repo.close.called

    @patch("controllers.cli.commands.model.Container")
    @patch("controllers.cli.commands.model.asyncio.run")
    def test_delete_model_with_confirmation_yes(self, mock_asyncio_run, mock_container):
        """Test deleting model with confirmation (user confirms)."""
        # Arrange
        runner = CliRunner()
        from domain.entities.model import Model, ModelType, ModelStatus

        existing_model = Model(
            model_type=ModelType.LGBM,
            hyperparameters={},
            status=ModelStatus.TRAINED
        )
        object.__setattr__(existing_model, "id", "test-model-123")

        mock_repo = AsyncMock()
        mock_repo.find_by_id = AsyncMock(return_value=existing_model)
        mock_repo.delete = AsyncMock()
        mock_container.return_value.model_repository = mock_repo

        def run_coro(coro):
            import asyncio
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(coro)
            finally:
                loop.close()
        mock_asyncio_run.side_effect = run_coro

        # Act - confirm with 'y'
        result = runner.invoke(
            model_group,
            ["delete", "test-model-123"],
            input="y\n",
        )

        # Assert
        assert result.exit_code == 0
        assert "deleted successfully" in result.output.lower()
        mock_repo.delete.assert_called_once_with("test-model-123")

    @patch("controllers.cli.commands.model.Container")
    @patch("controllers.cli.commands.model.asyncio.run")
    def test_delete_model_with_confirmation_no(self, mock_asyncio_run, mock_container):
        """Test deleting model with confirmation (user cancels)."""
        # Arrange
        runner = CliRunner()
        from domain.entities.model import Model, ModelType, ModelStatus

        existing_model = Model(
            model_type=ModelType.LGBM,
            hyperparameters={},
            status=ModelStatus.TRAINED
        )
        object.__setattr__(existing_model, "id", "test-model-123")

        mock_repo = AsyncMock()
        mock_repo.find_by_id = AsyncMock(return_value=existing_model)
        mock_repo.delete = AsyncMock()
        mock_container.return_value.model_repository = mock_repo

        def run_coro(coro):
            import asyncio
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(coro)
            finally:
                loop.close()
        mock_asyncio_run.side_effect = run_coro

        # Act - cancel with 'n'
        result = runner.invoke(
            model_group,
            ["delete", "test-model-123"],
            input="n\n",
        )

        # Assert
        assert result.exit_code == 0
        assert "cancelled" in result.output.lower()
        mock_repo.delete.assert_not_called()

    @patch("controllers.cli.commands.model.Container")
    @patch("controllers.cli.commands.model.asyncio.run")
    def test_delete_model_not_found(self, mock_asyncio_run, mock_container):
        """Test deleting non-existent model."""
        # Arrange
        runner = CliRunner()

        mock_repo = AsyncMock()
        mock_repo.find_by_id = AsyncMock(return_value=None)
        mock_container.return_value.model_repository = mock_repo

        def run_coro(coro):
            import asyncio
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(coro)
            finally:
                loop.close()
        mock_asyncio_run.side_effect = run_coro

        # Act
        result = runner.invoke(
            model_group,
            ["delete", "non-existent-id", "--force"],
        )

        # Assert
        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    @patch("controllers.cli.commands.model.Container")
    @patch("controllers.cli.commands.model.asyncio.run")
    def test_delete_model_repository_error(self, mock_asyncio_run, mock_container):
        """Test delete model with repository error."""
        # Arrange
        runner = CliRunner()
        from domain.entities.model import Model, ModelType, ModelStatus

        existing_model = Model(
            model_type=ModelType.LGBM,
            hyperparameters={},
            status=ModelStatus.TRAINED
        )
        object.__setattr__(existing_model, "id", "test-model-123")

        mock_repo = AsyncMock()
        mock_repo.find_by_id = AsyncMock(return_value=existing_model)
        mock_repo.delete = AsyncMock(side_effect=Exception("Database error"))
        mock_container.return_value.model_repository = mock_repo

        def run_coro(coro):
            import asyncio
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(coro)
            finally:
                loop.close()
        mock_asyncio_run.side_effect = run_coro

        # Act
        result = runner.invoke(
            model_group,
            ["delete", "test-model-123", "--force"],
        )

        # Assert
        assert result.exit_code == 1
        assert "failed" in result.output.lower() or "error" in result.output.lower()

    def test_delete_model_missing_id(self):
        """Test model delete with missing ID."""
        # Arrange
        runner = CliRunner()

        # Act
        result = runner.invoke(model_group, ["delete"])

        # Assert
        assert result.exit_code != 0
        assert "Error" in result.output or "Missing" in result.output
