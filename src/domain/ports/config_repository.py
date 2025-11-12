"""配置仓储端口"""

from abc import ABC, abstractmethod
from domain.value_objects.configuration import (
    DataSourceConfig,
    ModelConfig,
    BacktestConfig,
)


class IConfigRepository(ABC):
    """配置仓储接口"""

    @abstractmethod
    async def get_data_source_config(self) -> DataSourceConfig:
        """获取数据源配置"""
        pass

    @abstractmethod
    async def get_model_config(self, model_name: str) -> ModelConfig:
        """获取模型配置"""
        pass

    @abstractmethod
    async def get_backtest_config(self) -> BacktestConfig:
        """获取回测配置"""
        pass

    @abstractmethod
    async def save_config(self, config_type: str, config: any) -> None:
        """保存配置"""
        pass
