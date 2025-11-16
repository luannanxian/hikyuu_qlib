"""
Hyperparameter management utilities.

Provides default hyperparameters for different model types and utilities
for loading hyperparameters from various sources.
"""

import json
from pathlib import Path
from typing import Any

from domain.entities.model import ModelType

# Default hyperparameters for each model type
DEFAULT_HYPERPARAMETERS: dict[ModelType, dict[str, Any]] = {
    ModelType.LGBM: {
        "n_estimators": 100,
        "learning_rate": 0.05,
        "max_depth": 7,
        "num_leaves": 31,
    },
    ModelType.MLP: {
        "hidden_layers": [64, 32],
        "activation": "relu",
        "learning_rate": 0.001,
    },
    ModelType.LSTM: {
        "hidden_size": 64,
        "num_layers": 2,
        "sequence_length": 20,
    },
    ModelType.GRU: {
        "hidden_size": 64,
        "num_layers": 2,
        "sequence_length": 20,
    },
    ModelType.TRANSFORMER: {
        "hidden_size": 64,
        "num_heads": 4,
        "num_layers": 2,
        "sequence_length": 20,
    },
}


def get_default_hyperparameters(model_type: ModelType) -> dict[str, Any]:
    """
    Get default hyperparameters for a model type.

    Args:
        model_type: The type of model

    Returns:
        Dictionary of default hyperparameters
    """
    return DEFAULT_HYPERPARAMETERS.get(model_type, {}).copy()


def load_hyperparameters_from_json_string(json_string: str) -> dict[str, Any]:
    """
    Load hyperparameters from a JSON string.

    Args:
        json_string: JSON string containing hyperparameters

    Returns:
        Dictionary of hyperparameters

    Raises:
        ValueError: If JSON string is invalid
    """
    try:
        hyperparams = json.loads(json_string)
        if not isinstance(hyperparams, dict):
            raise ValueError("Hyperparameters must be a JSON object")
        return hyperparams
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e!s}")


def load_hyperparameters_from_config_file(config_file_path: str) -> dict[str, Any]:
    """
    Load hyperparameters from a configuration file.

    Supports JSON and YAML formats (based on file extension).
    The configuration file should have a "hyperparameters" key containing
    the hyperparameters dictionary.

    Args:
        config_file_path: Path to the configuration file

    Returns:
        Dictionary of hyperparameters

    Raises:
        ValueError: If file format is unsupported or invalid
        FileNotFoundError: If file does not exist
    """
    config_path = Path(config_file_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_file_path}")

    suffix = config_path.suffix.lower()

    if suffix == ".json":
        with open(config_path) as f:
            config = json.load(f)
    elif suffix in [".yaml", ".yml"]:
        try:
            import yaml
            with open(config_path) as f:
                config = yaml.safe_load(f)
        except ImportError:
            raise ValueError("YAML support requires PyYAML library. Install with: pip install pyyaml")
    else:
        raise ValueError(f"Unsupported configuration file format: {suffix}. Use .json or .yaml")

    if not isinstance(config, dict):
        raise ValueError("Configuration file must contain a JSON/YAML object")

    # Extract hyperparameters from config
    if "hyperparameters" in config:
        hyperparams = config["hyperparameters"]
        if not isinstance(hyperparams, dict):
            raise ValueError("'hyperparameters' field must be a dictionary")
        return hyperparams

    # If no 'hyperparameters' key, assume entire config is hyperparameters
    return config


def merge_hyperparameters(
    base: dict[str, Any],
    override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Merge hyperparameters, with override taking precedence.

    Args:
        base: Base hyperparameters
        override: Hyperparameters to override base with

    Returns:
        Merged hyperparameters dictionary
    """
    if override is None:
        return base.copy()

    result = base.copy()
    result.update(override)
    return result


def load_hyperparameters(
    model_type: ModelType,
    cli_json: str | None = None,
    config_file: str | None = None,
    param_list: tuple | None = None,
) -> dict[str, Any]:
    """
    Load hyperparameters from multiple sources with proper precedence.

    Precedence order (highest to lowest):
    1. CLI params (--param key=value)
    2. CLI JSON string (--hyperparameters)
    3. Configuration file (--config)
    4. Default hyperparameters for model type

    Args:
        model_type: The type of model
        cli_json: Optional JSON string from CLI
        config_file: Optional configuration file path
        param_list: Optional list of key=value parameter strings

    Returns:
        Dictionary of hyperparameters

    Raises:
        ValueError: If any source has invalid format
    """
    # Start with defaults
    hyperparams = get_default_hyperparameters(model_type)

    # Override with config file if provided
    if config_file:
        try:
            config_hyperparams = load_hyperparameters_from_config_file(config_file)
            hyperparams = merge_hyperparameters(hyperparams, config_hyperparams)
        except FileNotFoundError:
            raise
        except Exception as e:
            raise ValueError(f"Error loading configuration file: {e!s}")

    # Override with CLI JSON if provided
    if cli_json:
        try:
            cli_hyperparams = load_hyperparameters_from_json_string(cli_json)
            hyperparams = merge_hyperparameters(hyperparams, cli_hyperparams)
        except Exception as e:
            raise ValueError(f"Error loading CLI hyperparameters: {e!s}")

    # Override with individual params (highest precedence)
    if param_list:
        try:
            param_hyperparams = parse_param_list(param_list)
            hyperparams = merge_hyperparameters(hyperparams, param_hyperparams)
        except Exception as e:
            raise ValueError(f"Error parsing --param options: {e!s}")

    return hyperparams


def parse_param_list(param_list: tuple) -> dict[str, Any]:
    """
    Parse a list of key=value strings into a dictionary.

    Supports type inference for common types:
    - Integers: "n_estimators=100"
    - Floats: "learning_rate=0.05"
    - Booleans: "verbose=true"
    - Lists: "hidden_layers=[64,32]"
    - Strings: "activation=relu"

    Args:
        param_list: Tuple of key=value strings

    Returns:
        Dictionary of parsed parameters

    Raises:
        ValueError: If any parameter has invalid format

    Examples:
        >>> parse_param_list(("n_estimators=100", "learning_rate=0.05"))
        {'n_estimators': 100, 'learning_rate': 0.05}
    """
    params = {}

    for param_str in param_list:
        if "=" not in param_str:
            raise ValueError(
                f"Invalid parameter format: '{param_str}'. Expected 'key=value'",
            )

        key, value_str = param_str.split("=", 1)
        key = key.strip()
        value_str = value_str.strip()

        if not key:
            raise ValueError(f"Empty key in parameter: '{param_str}'")

        # Try to infer type
        value = _infer_value_type(value_str)
        params[key] = value

    return params


def _infer_value_type(value_str: str) -> Any:
    """
    Infer the type of a value string and convert it.

    Args:
        value_str: String representation of a value

    Returns:
        Converted value with appropriate type
    """
    value_str = value_str.strip()

    # Boolean
    if value_str.lower() in ("true", "yes", "1"):
        return True
    if value_str.lower() in ("false", "no", "0"):
        return False

    # List (JSON-like)
    if value_str.startswith("[") and value_str.endswith("]"):
        try:
            return json.loads(value_str)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid list format: {value_str}")

    # Dict (JSON-like)
    if value_str.startswith("{") and value_str.endswith("}"):
        try:
            return json.loads(value_str)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid dict format: {value_str}")

    # Integer
    try:
        return int(value_str)
    except ValueError:
        pass

    # Float
    try:
        return float(value_str)
    except ValueError:
        pass

    # String (default)
    return value_str
