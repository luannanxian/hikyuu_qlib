"""批量训练配置数据类

用于封装批量训练工具函数的配置参数。
"""

from dataclasses import dataclass
from typing import Any

from domain.value_objects.date_range import DateRange
from domain.value_objects.kline_type import KLineType


@dataclass
class IndexDataLoadConfig:
    """指数数据加载配置

    封装加载指数成分股数据所需的参数。
    """

    index_name: str
    date_range: DateRange
    kline_type: KLineType
    add_features: bool = True
    add_labels: bool = True
    label_horizon: int = 1
    max_stocks: int | None = None
    skip_errors: bool = True


@dataclass
class IndexModelTrainingConfig:
    """指数模型训练配置

    封装在指数成分股上训练模型所需的参数。
    """

    index_name: str
    model_type: Any  # ModelType enum
    model_name: str
    date_range: DateRange
    kline_type: KLineType
    hyperparameters: dict[str, Any] | None = None
    max_stocks: int | None = None
    skip_errors: bool = True
    save_training_data: bool = False
    output_file: str | None = None
