"""SaveConfigurationUseCase - 保存配置用例"""

from domain.ports.config_repository import IConfigRepository
from domain.value_objects.configuration import Configuration


class SaveConfigurationUseCase:
    """保存配置用例"""

    def __init__(self, repository: IConfigRepository):
        self.repository = repository

    async def execute(self, configuration: Configuration) -> None:
        """执行保存完整配置"""
        # 保存各部分配置
        await self.repository.save_config("data_source", configuration.data_source)
        await self.repository.save_config("model:default", configuration.model)
        await self.repository.save_config("backtest", configuration.backtest)
