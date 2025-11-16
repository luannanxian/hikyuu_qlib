"""
Configuration Value Objects

配置值对象,遵循 DDD 原则
"""

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DataSourceConfig:
    """数据源配置值对象"""

    hikyuu_path: str | None = None
    qlib_path: str | None = None
    provider: str | None = None  # "hikyuu" or "qlib" (legacy)
    data_path: str | None = None  # (legacy)

    def __post_init__(self):
        """验证配置有效性"""
        # 新格式验证
        if self.hikyuu_path or self.qlib_path:
            return  # 新格式不需要额外验证

        # 旧格式验证
        if self.provider and self.provider not in ("hikyuu", "qlib"):
            raise ValueError(f"Invalid provider: {self.provider}")

        # 验证路径存在(如果是本地路径)
        if self.data_path and not self.data_path.startswith("http"):
            path = Path(self.data_path)
            if not path.exists():
                raise ValueError(f"Data path does not exist: {self.data_path}")


@dataclass(frozen=True)
class ModelConfig:
    """模型配置值对象"""

    hyperparameters: dict[str, Any]
    default_type: str | None = None
    model_type: str | None = None  # Legacy field

    def __post_init__(self):
        """验证配置有效性"""
        valid_types = ("LGBM", "MLP", "LSTM", "GRU", "TRANSFORMER")

        # 使用default_type或model_type进行验证
        type_to_check = self.default_type or self.model_type
        if type_to_check and type_to_check not in valid_types:
            raise ValueError(f"Invalid model type: {type_to_check}")


@dataclass(frozen=True)
class BacktestConfig:
    """回测配置值对象"""

    initial_capital: Decimal
    commission_rate: Decimal
    slippage_rate: Decimal = Decimal("0.001")

    def __post_init__(self):
        """验证配置有效性"""
        if self.initial_capital <= 0:
            raise ValueError("initial_capital must be > 0")

        if not (Decimal(0) <= self.commission_rate <= Decimal("0.1")):
            raise ValueError("commission_rate must be between 0 and 0.1")

        if not (Decimal(0) <= self.slippage_rate <= Decimal("0.1")):
            raise ValueError("slippage_rate must be between 0 and 0.1")


@dataclass(frozen=True)
class Configuration:
    """
    配置聚合根

    整合所有配置值对象
    """

    data_source: DataSourceConfig
    model: ModelConfig
    backtest: BacktestConfig
