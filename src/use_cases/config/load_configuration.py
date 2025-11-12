"""LoadConfigurationUseCase - 加载配置用例"""

from domain.ports.config_repository import IConfigRepository
from domain.value_objects.configuration import BacktestConfig


class LoadConfigurationUseCase:
    """加载配置用例"""

    def __init__(self, repository: IConfigRepository):
        self.repository = repository

    async def execute(self) -> BacktestConfig:
        """执行加载回测配置"""
        config = await self.repository.get_backtest_config()
        return config
