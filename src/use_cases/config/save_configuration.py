"""SaveConfigurationUseCase - 保存配置用例"""

from domain.ports.config_repository import IConfigRepository
from domain.value_objects.configuration import BacktestConfig


class SaveConfigurationUseCase:
    """保存配置用例"""

    def __init__(self, repository: IConfigRepository):
        self.repository = repository

    async def execute(self, config: BacktestConfig) -> None:
        """执行保存配置"""
        await self.repository.save_config("backtest", config)
