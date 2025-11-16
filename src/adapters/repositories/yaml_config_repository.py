"""
YAMLConfigRepository - YAML 配置仓储

使用 YAML 文件存储和读取配置,实现 IConfigRepository 接口
"""

from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml

from domain.ports.config_repository import IConfigRepository
from domain.value_objects.configuration import (
    BacktestConfig,
    DataSourceConfig,
    ModelConfig,
)


class YAMLConfigRepository(IConfigRepository):
    """
    YAML 配置仓储

    实现 IConfigRepository 接口,使用 YAML 文件存储配置
    """

    def __init__(self, config_path: str):
        """
        初始化仓储

        Args:
            config_path: YAML 配置文件路径
        """
        self.config_path = Path(config_path)
        self._config_cache: dict[str, Any] = {}

    def _load_config(self) -> dict[str, Any]:
        """
        从 YAML 文件加载配置

        Returns:
            Dict[str, Any]: 配置字典

        Raises:
            Exception: 当文件不存在或解析失败时
        """
        try:
            if not self.config_path.exists():
                raise FileNotFoundError(f"Config file not found: {self.config_path}")

            with open(self.config_path, encoding="utf-8") as f:
                config = yaml.safe_load(f)

            return config if config is not None else {}

        except Exception as e:
            raise Exception(
                f"Failed to load config from {self.config_path}: {e}",
            ) from e

    def _save_config(self, config: dict[str, Any]) -> None:
        """
        保存配置到 YAML 文件

        Args:
            config: 配置字典

        Raises:
            Exception: 当保存失败时
        """
        try:
            # 确保目录存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(config, f, default_flow_style=False, allow_unicode=True)

        except Exception as e:
            raise Exception(f"Failed to save config to {self.config_path}: {e}") from e

    async def get_data_source_config(self) -> DataSourceConfig:
        """
        获取数据源配置

        Returns:
            DataSourceConfig: 数据源配置值对象

        Raises:
            Exception: 当配置不存在或无效时
        """
        try:
            config = self._load_config()

            if "data_source" not in config:
                raise ValueError("data_source section not found in config")

            data_source = config["data_source"]

            # 支持新格式 (hikyuu_path/qlib_path) 和旧格式 (provider/data_path)
            if "hikyuu_path" in data_source or "qlib_path" in data_source:
                return DataSourceConfig(
                    hikyuu_path=data_source.get("hikyuu_path"),
                    qlib_path=data_source.get("qlib_path"),
                )
            else:
                return DataSourceConfig(
                    provider=data_source["provider"],
                    data_path=data_source["data_path"],
                )

        except Exception as e:
            raise Exception(f"Failed to get data source config: {e}") from e

    async def get_model_config(self, model_name: str = "default") -> ModelConfig:
        """
        获取模型配置

        Args:
            model_name: 模型名称 (默认 "default")

        Returns:
            ModelConfig: 模型配置值对象

        Raises:
            Exception: 当配置不存在或无效时
        """
        try:
            config = self._load_config()

            # 尝试新格式: 顶层 "model" section
            if "model" in config:
                model_config = config["model"]
                return ModelConfig(
                    default_type=model_config.get("default_type"),
                    hyperparameters=model_config.get("hyperparameters", {}),
                )

            # 旧格式: "models" dict
            if "models" not in config:
                raise ValueError("model or models section not found in config")

            if model_name not in config["models"]:
                raise ValueError(f"Model config not found: {model_name}")

            model_config = config["models"][model_name]
            return ModelConfig(
                model_type=model_config["model_type"],
                hyperparameters=model_config["hyperparameters"],
            )

        except Exception as e:
            raise Exception(f"Failed to get model config for {model_name}: {e}") from e

    async def get_backtest_config(self) -> BacktestConfig:
        """
        获取回测配置

        Returns:
            BacktestConfig: 回测配置值对象

        Raises:
            Exception: 当配置不存在或无效时
        """
        try:
            config = self._load_config()

            if "backtest" not in config:
                raise ValueError("backtest section not found in config")

            backtest = config["backtest"]
            return BacktestConfig(
                initial_capital=Decimal(str(backtest["initial_capital"])),
                commission_rate=Decimal(str(backtest.get("commission_rate", 0.001))),
                slippage_rate=Decimal(str(backtest.get("slippage_rate", 0.001))),
            )

        except Exception as e:
            raise Exception(f"Failed to get backtest config: {e}") from e

    async def save_config(self, config_type: str, config: Any) -> None:
        """
        保存配置

        Args:
            config_type: 配置类型 ("data_source", "model", "backtest")
            config: 配置对象

        Raises:
            Exception: 当保存失败时
        """
        try:
            # 加载现有配置
            try:
                full_config = self._load_config()
            except FileNotFoundError:
                full_config = {}

            # 转换配置对象为字典
            if config_type == "data_source":
                if isinstance(config, DataSourceConfig):
                    # 支持新格式和旧格式
                    if config.hikyuu_path or config.qlib_path:
                        full_config["data_source"] = {
                            "hikyuu_path": config.hikyuu_path,
                            "qlib_path": config.qlib_path,
                        }
                    else:
                        full_config["data_source"] = {
                            "provider": config.provider,
                            "data_path": config.data_path,
                        }
            elif config_type == "backtest":
                if isinstance(config, BacktestConfig):
                    full_config["backtest"] = {
                        "initial_capital": float(config.initial_capital),
                        "commission_rate": float(config.commission_rate),
                        "slippage_rate": float(config.slippage_rate),
                    }
            elif config_type.startswith("model:"):
                # 格式: "model:default" -> 保存为顶层 "model" section
                model_name = config_type.split(":")[1]
                if isinstance(config, ModelConfig):
                    if model_name == "default":
                        # 新格式: 顶层 "model"
                        full_config["model"] = {
                            "default_type": config.default_type or config.model_type,
                            "hyperparameters": config.hyperparameters,
                        }
                    else:
                        # 旧格式: "models" dict
                        if "models" not in full_config:
                            full_config["models"] = {}
                        full_config["models"][model_name] = {
                            "model_type": config.model_type,
                            "hyperparameters": config.hyperparameters,
                        }

            # 保存配置
            self._save_config(full_config)

        except Exception as e:
            raise Exception(f"Failed to save config ({config_type}): {e}") from e
