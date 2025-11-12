"""
Configuration Value Objects

配置值对象,遵循 DDD 原则
"""

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Dict, Any


@dataclass(frozen=True)
class DataSourceConfig:
    """数据源配置值对象"""

    provider: str  # "hikyuu" or "qlib"
    data_path: str

    def __post_init__(self):
        """验证配置有效性"""
        if self.provider not in ("hikyuu", "qlib"):
            raise ValueError(f"Invalid provider: {self.provider}")

        # 验证路径存在(如果是本地路径)
        if not self.data_path.startswith("http"):
            path = Path(self.data_path)
            if not path.exists():
                raise ValueError(f"Data path does not exist: {self.data_path}")


@dataclass(frozen=True)
class ModelConfig:
    """模型配置值对象"""

    model_type: str  # "LGBM", "MLP", "LSTM", etc.
    hyperparameters: Dict[str, Any]

    def __post_init__(self):
        """验证配置有效性"""
        valid_types = ("LGBM", "MLP", "LSTM", "GRU", "TRANSFORMER")
        if self.model_type not in valid_types:
            raise ValueError(f"Invalid model_type: {self.model_type}")


@dataclass(frozen=True)
class BacktestConfig:
    """回测配置值对象"""

    initial_capital: Decimal
    commission_rate: Decimal
    slippage_rate: Decimal

    def __post_init__(self):
        """验证配置有效性"""
        if self.initial_capital <= 0:
            raise ValueError("initial_capital must be > 0")

        if not (Decimal("0") <= self.commission_rate <= Decimal("0.1")):
            raise ValueError("commission_rate must be between 0 and 0.1")

        if not (Decimal("0") <= self.slippage_rate <= Decimal("0.1")):
            raise ValueError("slippage_rate must be between 0 and 0.1")
