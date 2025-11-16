"""
Tests for hyperparameter management utilities.

Tests:
- Default hyperparameters loading
- JSON string parsing
- Config file loading (JSON and YAML)
- Hyperparameter merging
- Error handling
"""

import json

import pytest

from controllers.cli.utils.hyperparameters import (
    get_default_hyperparameters,
    load_hyperparameters,
    load_hyperparameters_from_config_file,
    load_hyperparameters_from_json_string,
    merge_hyperparameters,
)
from domain.entities.model import ModelType


class TestGetDefaultHyperparameters:
    """Test getting default hyperparameters."""

    def test_get_default_hyperparameters_lgbm(self):
        """Test getting default hyperparameters for LGBM."""
        # Act
        hyperparams = get_default_hyperparameters(ModelType.LGBM)

        # Assert
        assert hyperparams == {
            "n_estimators": 100,
            "learning_rate": 0.05,
            "max_depth": 7,
            "num_leaves": 31,
        }

    def test_get_default_hyperparameters_mlp(self):
        """Test getting default hyperparameters for MLP."""
        # Act
        hyperparams = get_default_hyperparameters(ModelType.MLP)

        # Assert
        assert hyperparams == {
            "hidden_layers": [64, 32],
            "activation": "relu",
            "learning_rate": 0.001,
        }

    def test_get_default_hyperparameters_lstm(self):
        """Test getting default hyperparameters for LSTM."""
        # Act
        hyperparams = get_default_hyperparameters(ModelType.LSTM)

        # Assert
        assert hyperparams == {
            "hidden_size": 64,
            "num_layers": 2,
            "sequence_length": 20,
        }

    def test_get_default_hyperparameters_returns_copy(self):
        """Test that getting default hyperparameters returns a copy."""
        # Act
        hyperparams1 = get_default_hyperparameters(ModelType.LGBM)
        hyperparams2 = get_default_hyperparameters(ModelType.LGBM)

        # Modify first copy
        hyperparams1["n_estimators"] = 999

        # Assert that second copy is not affected
        assert hyperparams2["n_estimators"] == 100


class TestLoadHyperparametersFromJsonString:
    """Test loading hyperparameters from JSON string."""

    def test_load_valid_json_string(self):
        """Test loading hyperparameters from valid JSON string."""
        # Arrange
        json_string = json.dumps({"n_estimators": 200, "learning_rate": 0.1})

        # Act
        hyperparams = load_hyperparameters_from_json_string(json_string)

        # Assert
        assert hyperparams == {"n_estimators": 200, "learning_rate": 0.1}

    def test_load_invalid_json_string(self):
        """Test loading hyperparameters from invalid JSON string."""
        # Arrange
        invalid_json = "{invalid json}"

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid JSON format"):
            load_hyperparameters_from_json_string(invalid_json)

    def test_load_non_dict_json(self):
        """Test loading hyperparameters from non-dict JSON."""
        # Arrange
        json_string = json.dumps([1, 2, 3])  # List, not dict

        # Act & Assert
        with pytest.raises(ValueError, match="must be a JSON object"):
            load_hyperparameters_from_json_string(json_string)


class TestLoadHyperparametersFromConfigFile:
    """Test loading hyperparameters from config file."""

    def test_load_from_json_file(self, tmp_path):
        """Test loading hyperparameters from JSON config file."""
        # Arrange
        config_file = tmp_path / "config.json"
        config = {"hyperparameters": {"n_estimators": 150, "max_depth": 10}}
        with open(config_file, "w") as f:
            json.dump(config, f)

        # Act
        hyperparams = load_hyperparameters_from_config_file(str(config_file))

        # Assert
        assert hyperparams == {"n_estimators": 150, "max_depth": 10}

    def test_load_from_json_file_without_hyperparameters_key(self, tmp_path):
        """Test loading when config file doesn't have hyperparameters key."""
        # Arrange
        config_file = tmp_path / "config.json"
        config = {"n_estimators": 150, "max_depth": 10}  # No hyperparameters key
        with open(config_file, "w") as f:
            json.dump(config, f)

        # Act
        hyperparams = load_hyperparameters_from_config_file(str(config_file))

        # Assert - should use entire config as hyperparameters
        assert hyperparams == {"n_estimators": 150, "max_depth": 10}

    def test_load_from_nonexistent_file(self):
        """Test loading from nonexistent config file."""
        # Act & Assert
        with pytest.raises(FileNotFoundError):
            load_hyperparameters_from_config_file("/nonexistent/path.json")

    def test_load_from_unsupported_file_format(self, tmp_path):
        """Test loading from unsupported config file format."""
        # Arrange
        config_file = tmp_path / "config.txt"
        config_file.write_text("some content")

        # Act & Assert
        with pytest.raises(ValueError, match="Unsupported configuration file format"):
            load_hyperparameters_from_config_file(str(config_file))

    def test_load_from_invalid_json_file(self, tmp_path):
        """Test loading from invalid JSON file."""
        # Arrange
        config_file = tmp_path / "config.json"
        config_file.write_text("{invalid json}")

        # Act & Assert
        with pytest.raises(Exception):  # json.JSONDecodeError
            load_hyperparameters_from_config_file(str(config_file))


class TestMergeHyperparameters:
    """Test merging hyperparameters."""

    def test_merge_with_override(self):
        """Test merging hyperparameters with override."""
        # Arrange
        base = {"n_estimators": 100, "learning_rate": 0.05, "max_depth": 7}
        override = {"n_estimators": 200, "learning_rate": 0.1}

        # Act
        merged = merge_hyperparameters(base, override)

        # Assert
        assert merged == {
            "n_estimators": 200,  # Overridden
            "learning_rate": 0.1,  # Overridden
            "max_depth": 7,  # From base
        }

    def test_merge_with_none_override(self):
        """Test merging hyperparameters with None override."""
        # Arrange
        base = {"n_estimators": 100, "learning_rate": 0.05}

        # Act
        merged = merge_hyperparameters(base, None)

        # Assert
        assert merged == base

    def test_merge_returns_copy(self):
        """Test that merge returns a copy, not modifying original."""
        # Arrange
        base = {"n_estimators": 100}
        override = {"learning_rate": 0.1}

        # Act
        merged = merge_hyperparameters(base, override)
        merged["new_param"] = 999

        # Assert - original should not be modified
        assert "new_param" not in base
        assert "new_param" not in override


class TestLoadHyperparameters:
    """Test the main load_hyperparameters function."""

    def test_load_with_defaults_only(self):
        """Test loading with defaults only."""
        # Act
        hyperparams = load_hyperparameters(ModelType.LGBM)

        # Assert
        assert hyperparams == {
            "n_estimators": 100,
            "learning_rate": 0.05,
            "max_depth": 7,
            "num_leaves": 31,
        }

    def test_load_with_cli_json_only(self):
        """Test loading with CLI JSON only (merges with defaults)."""
        # Arrange
        cli_json = json.dumps({"n_estimators": 200, "learning_rate": 0.1})

        # Act
        hyperparams = load_hyperparameters(ModelType.LGBM, cli_json=cli_json)

        # Assert
        assert hyperparams["n_estimators"] == 200  # Overridden
        assert hyperparams["learning_rate"] == 0.1  # Overridden
        assert hyperparams["max_depth"] == 7  # Default kept
        assert hyperparams["num_leaves"] == 31  # Default kept

    def test_load_with_config_file_only(self, tmp_path):
        """Test loading with config file only (merges with defaults)."""
        # Arrange
        config_file = tmp_path / "config.json"
        config = {"hyperparameters": {"n_estimators": 150, "max_depth": 10}}
        with open(config_file, "w") as f:
            json.dump(config, f)

        # Act
        hyperparams = load_hyperparameters(
            ModelType.LGBM, config_file=str(config_file),
        )

        # Assert
        assert hyperparams["n_estimators"] == 150  # Overridden
        assert hyperparams["max_depth"] == 10  # Overridden
        assert hyperparams["learning_rate"] == 0.05  # Default kept
        assert hyperparams["num_leaves"] == 31  # Default kept

    def test_load_with_both_cli_and_config(self, tmp_path):
        """Test loading with both CLI and config (CLI takes precedence)."""
        # Arrange
        config_file = tmp_path / "config.json"
        config = {"hyperparameters": {"n_estimators": 150, "max_depth": 10}}
        with open(config_file, "w") as f:
            json.dump(config, f)

        cli_json = json.dumps({"n_estimators": 250, "learning_rate": 0.2})

        # Act
        hyperparams = load_hyperparameters(
            ModelType.LGBM, cli_json=cli_json, config_file=str(config_file),
        )

        # Assert
        assert hyperparams["n_estimators"] == 250  # CLI override
        assert hyperparams["learning_rate"] == 0.2  # CLI override
        assert hyperparams["max_depth"] == 10  # Config override
        assert hyperparams["num_leaves"] == 31  # Default kept

    def test_load_with_invalid_cli_json(self):
        """Test loading with invalid CLI JSON."""
        # Act & Assert
        with pytest.raises(ValueError):
            load_hyperparameters(ModelType.LGBM, cli_json="{invalid json}")

    def test_load_with_invalid_config_file(self):
        """Test loading with invalid config file."""
        # Act & Assert
        with pytest.raises((FileNotFoundError, ValueError)):
            load_hyperparameters(ModelType.LGBM, config_file="/nonexistent/path.json")
