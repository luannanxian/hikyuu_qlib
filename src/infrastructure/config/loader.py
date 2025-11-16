"""Configuration loader for loading from multiple sources.

This module provides utilities for loading configuration from:
- .env files
- YAML files
- JSON files
- Environment variables with priority handling
"""
import json
import os
from pathlib import Path
from typing import Any

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

from ..errors import ConfigurationException


def load_config_from_file(file_path: str) -> dict[str, Any]:
    """Load configuration from a file.

    Supports .env, .yaml, .yml, and .json files.

    Args:
        file_path: Path to configuration file

    Returns:
        Configuration dictionary

    Raises:
        FileNotFoundError: If file not found
        ValueError: If file format is not supported
        ConfigurationException: If parsing fails
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {file_path}")

    suffix = path.suffix.lower()

    try:
        if suffix == ".env":
            return _load_env_file(file_path)
        elif suffix in [".yaml", ".yml"]:
            if not YAML_AVAILABLE:
                raise ConfigurationException(
                    "PyYAML is required to load YAML files",
                    code="CONFIG_PARSE_ERROR",
                    context={"file_path": file_path},
                )
            return _load_yaml_file(file_path)
        elif suffix == ".json":
            return _load_json_file(file_path)
        else:
            raise ValueError(
                f"Unsupported configuration file format: {suffix}. "
                "Supported formats: .env, .yaml, .yml, .json",
            )
    except Exception as e:
        if isinstance(e, (FileNotFoundError, ValueError, ConfigurationException)):
            raise
        raise ConfigurationException(
            f"Failed to parse configuration file: {file_path}",
            code="CONFIG_PARSE_ERROR",
            context={"file_path": file_path},
            original_exception=e,
        ) from e


def _load_env_file(file_path: str) -> dict[str, Any]:
    """Load configuration from .env file."""
    config = {}

    with open(file_path) as f:
        for line in f:
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            # Parse KEY=VALUE
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()

                # Remove quotes if present
                if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]

                config[key] = value

    return config


def _load_yaml_file(file_path: str) -> dict[str, Any]:
    """Load configuration from YAML file."""
    with open(file_path) as f:
        config = yaml.safe_load(f)

    return config or {}


def _load_json_file(file_path: str) -> dict[str, Any]:
    """Load configuration from JSON file."""
    with open(file_path) as f:
        config = json.load(f)

    return config or {}


class ConfigLoader:
    """Configuration loader with caching and merging support."""

    def __init__(self, enable_cache: bool = False):
        """Initialize the config loader.

        Args:
            enable_cache: If True, cache loaded configurations
        """
        self.enable_cache = enable_cache
        self._cache: dict[str, dict[str, Any]] = {}

    def load_config(self, file_path: str) -> dict[str, Any]:
        """Load configuration from file with optional caching.

        Args:
            file_path: Path to configuration file

        Returns:
            Configuration dictionary
        """
        if self.enable_cache and file_path in self._cache:
            return self._cache[file_path]

        config = load_config_from_file(file_path)

        if self.enable_cache:
            self._cache[file_path] = config

        return config

    def load_from_env(self, prefix: str = "") -> dict[str, Any]:
        """Load configuration from environment variables.

        Args:
            prefix: Environment variable prefix to filter by

        Returns:
            Configuration dictionary
        """
        config = {}

        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Remove prefix from key
                clean_key = key[len(prefix) :]
                config[clean_key] = value

        return config

    def merge_configs(self, configs: list[dict[str, Any]]) -> dict[str, Any]:
        """Merge multiple configuration dictionaries.

        Later configs override earlier ones.

        Args:
            configs: List of configuration dictionaries

        Returns:
            Merged configuration dictionary
        """
        merged = {}

        for config in configs:
            merged.update(config)

        return merged

    def load_with_overrides(
        self, base_config: dict[str, Any], prefix: str = "",
    ) -> dict[str, Any]:
        """Load configuration with environment variable overrides.

        Args:
            base_config: Base configuration
            prefix: Environment variable prefix

        Returns:
            Configuration with environment overrides applied
        """
        env_config = self.load_from_env(prefix)
        return self.merge_configs([base_config, env_config])

    def clear_cache(self) -> None:
        """Clear the configuration cache."""
        self._cache.clear()


# Singleton instance
_config_loader: ConfigLoader | None = None


def get_config_loader(enable_cache: bool = True) -> ConfigLoader:
    """Get the singleton ConfigLoader instance.

    Args:
        enable_cache: If True, enable configuration caching

    Returns:
        ConfigLoader instance
    """
    global _config_loader

    if _config_loader is None:
        _config_loader = ConfigLoader(enable_cache=enable_cache)

    return _config_loader
