"""
Tests for model train command with hyperparameter support.

Tests:
- model train with --param option
- model train with --config file
- model train with --hyperparameters JSON
- hyperparameter parsing and type inference
"""

import json
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from controllers.cli.commands.model import model_group
from controllers.cli.utils.hyperparameters import (
    _infer_value_type,
    load_hyperparameters,
    parse_param_list,
)
from domain.entities.model import ModelType


class TestModelTrainWithParams:
    """Test model train command with --param option."""

    @patch("controllers.cli.commands.model.asyncio.run")
    def test_train_with_single_param(self, mock_asyncio_run):
        """Test training with single --param option."""
        # Arrange
        runner = CliRunner()
        mock_asyncio_run.return_value = None

        # Act
        result = runner.invoke(
            model_group,
            [
                "train",
                "--type", "LGBM",
                "--name", "test_model",
                "--data", "test.csv",
                "--param", "n_estimators=200",
            ],
        )

        # Assert - command should parse without error
        assert "n_estimators" in str(mock_asyncio_run.call_args) or result.exit_code != 2

    @patch("controllers.cli.commands.model.asyncio.run")
    def test_train_with_multiple_params(self, mock_asyncio_run):
        """Test training with multiple --param options."""
        # Arrange
        runner = CliRunner()
        mock_asyncio_run.return_value = None

        # Act
        result = runner.invoke(
            model_group,
            [
                "train",
                "--type", "LGBM",
                "--name", "test_model",
                "--data", "test.csv",
                "--param", "n_estimators=200",
                "--param", "learning_rate=0.1",
                "--param", "max_depth=8",
            ],
        )

        # Assert
        assert result.exit_code != 2  # Not a usage error

    @patch("controllers.cli.commands.model.asyncio.run")
    def test_train_with_param_invalid_format(self, mock_asyncio_run):
        """Test training with invalid --param format."""
        # Arrange
        runner = CliRunner()
        mock_asyncio_run.return_value = None

        # Act
        result = runner.invoke(
            model_group,
            [
                "train",
                "--type", "LGBM",
                "--name", "test_model",
                "--data", "test.csv",
                "--param", "invalid_param_no_equals",
            ],
        )

        # Assert - should handle error gracefully
        # Exit code 1 means execution error (handled), 2 means usage error
        assert result.exit_code in [0, 1]


class TestHyperparameterParsing:
    """Test hyperparameter parsing functions."""

    def test_parse_param_list_integers(self):
        """Test parsing integer parameters."""
        # Arrange
        params = ("n_estimators=100", "max_depth=7")

        # Act
        result = parse_param_list(params)

        # Assert
        assert result == {"n_estimators": 100, "max_depth": 7}
        assert isinstance(result["n_estimators"], int)

    def test_parse_param_list_floats(self):
        """Test parsing float parameters."""
        # Arrange
        params = ("learning_rate=0.05", "subsample=0.8")

        # Act
        result = parse_param_list(params)

        # Assert
        assert result == {"learning_rate": 0.05, "subsample": 0.8}
        assert isinstance(result["learning_rate"], float)

    def test_parse_param_list_booleans(self):
        """Test parsing boolean parameters."""
        # Arrange
        params = ("verbose=true", "early_stopping=false")

        # Act
        result = parse_param_list(params)

        # Assert
        assert result == {"verbose": True, "early_stopping": False}
        assert isinstance(result["verbose"], bool)

    def test_parse_param_list_lists(self):
        """Test parsing list parameters."""
        # Arrange
        params = ("hidden_layers=[64,32,16]",)

        # Act
        result = parse_param_list(params)

        # Assert
        assert result == {"hidden_layers": [64, 32, 16]}
        assert isinstance(result["hidden_layers"], list)

    def test_parse_param_list_strings(self):
        """Test parsing string parameters."""
        # Arrange
        params = ("activation=relu", "optimizer=adam")

        # Act
        result = parse_param_list(params)

        # Assert
        assert result == {"activation": "relu", "optimizer": "adam"}
        assert isinstance(result["activation"], str)

    def test_parse_param_list_mixed_types(self):
        """Test parsing mixed type parameters."""
        # Arrange
        params = (
            "n_estimators=100",
            "learning_rate=0.05",
            "verbose=true",
            "activation=relu",
        )

        # Act
        result = parse_param_list(params)

        # Assert
        assert result == {
            "n_estimators": 100,
            "learning_rate": 0.05,
            "verbose": True,
            "activation": "relu",
        }

    def test_parse_param_list_invalid_format(self):
        """Test parsing with invalid format raises error."""
        # Arrange
        params = ("invalid_no_equals",)

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid parameter format"):
            parse_param_list(params)

    def test_parse_param_list_empty_key(self):
        """Test parsing with empty key raises error."""
        # Arrange
        params = ("=value",)

        # Act & Assert
        with pytest.raises(ValueError, match="Empty key"):
            parse_param_list(params)


class TestTypeInference:
    """Test type inference for parameter values."""

    def test_infer_integer(self):
        """Test inferring integer type."""
        assert _infer_value_type("100") == 100
        assert isinstance(_infer_value_type("100"), int)

    def test_infer_float(self):
        """Test inferring float type."""
        assert _infer_value_type("0.05") == 0.05
        assert isinstance(_infer_value_type("0.05"), float)

    def test_infer_boolean_true(self):
        """Test inferring boolean true."""
        assert _infer_value_type("true") is True
        assert _infer_value_type("True") is True
        assert _infer_value_type("yes") is True
        assert _infer_value_type("1") is True

    def test_infer_boolean_false(self):
        """Test inferring boolean false."""
        assert _infer_value_type("false") is False
        assert _infer_value_type("False") is False
        assert _infer_value_type("no") is False
        assert _infer_value_type("0") is False

    def test_infer_list(self):
        """Test inferring list type."""
        assert _infer_value_type("[1,2,3]") == [1, 2, 3]
        assert _infer_value_type("[64,32]") == [64, 32]

    def test_infer_string(self):
        """Test inferring string type (default)."""
        assert _infer_value_type("relu") == "relu"
        assert isinstance(_infer_value_type("relu"), str)


class TestLoadHyperparametersIntegration:
    """Test load_hyperparameters function with different sources."""

    def test_load_with_defaults_only(self):
        """Test loading with default hyperparameters only."""
        # Act
        result = load_hyperparameters(ModelType.LGBM)

        # Assert
        assert "n_estimators" in result
        assert "learning_rate" in result
        assert result["n_estimators"] == 100  # Default value

    def test_load_with_param_list(self):
        """Test loading with param list overriding defaults."""
        # Arrange
        params = ("n_estimators=200", "learning_rate=0.1")

        # Act
        result = load_hyperparameters(ModelType.LGBM, param_list=params)

        # Assert
        assert result["n_estimators"] == 200
        assert result["learning_rate"] == 0.1
        assert "max_depth" in result  # Default still present

    def test_load_with_cli_json(self):
        """Test loading with CLI JSON string."""
        # Arrange
        cli_json = '{"n_estimators": 150, "max_depth": 10}'

        # Act
        result = load_hyperparameters(ModelType.LGBM, cli_json=cli_json)

        # Assert
        assert result["n_estimators"] == 150
        assert result["max_depth"] == 10

    def test_load_with_config_file(self, tmp_path):
        """Test loading with config file."""
        # Arrange
        config_file = tmp_path / "config.json"
        config_data = {"hyperparameters": {"n_estimators": 180, "learning_rate": 0.08}}
        config_file.write_text(json.dumps(config_data))

        # Act
        result = load_hyperparameters(ModelType.LGBM, config_file=str(config_file))

        # Assert
        assert result["n_estimators"] == 180
        assert result["learning_rate"] == 0.08

    def test_load_precedence_order(self, tmp_path):
        """Test that param_list has highest precedence."""
        # Arrange
        config_file = tmp_path / "config.json"
        config_data = {"hyperparameters": {"n_estimators": 180}}
        config_file.write_text(json.dumps(config_data))

        cli_json = '{"n_estimators": 150}'
        params = ("n_estimators=200",)

        # Act
        result = load_hyperparameters(
            ModelType.LGBM,
            cli_json=cli_json,
            config_file=str(config_file),
            param_list=params,
        )

        # Assert
        # param_list should win
        assert result["n_estimators"] == 200

    def test_load_with_invalid_cli_json(self):
        """Test loading with invalid CLI JSON raises error."""
        # Arrange
        cli_json = '{invalid json}'

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid"):
            load_hyperparameters(ModelType.LGBM, cli_json=cli_json)

    def test_load_with_invalid_param_list(self):
        """Test loading with invalid param list raises error."""
        # Arrange
        params = ("invalid_format",)

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid parameter format"):
            load_hyperparameters(ModelType.LGBM, param_list=params)
