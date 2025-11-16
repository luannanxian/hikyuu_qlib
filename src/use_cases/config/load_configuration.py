"""LoadConfigurationUseCase - 加载配置用例"""

from domain.ports.config_repository import IConfigRepository
from domain.value_objects.configuration import Configuration


class LoadConfigurationUseCase:
    """加载配置用例"""

    def __init__(self, repository: IConfigRepository):
        self.repository = repository

    async def execute(self) -> Configuration:
        """执行加载完整配置"""
        # 加载各部分配置
        data_source = await self.repository.get_data_source_config()
        backtest = await self.repository.get_backtest_config()

        # 尝试加载模型配置(使用默认名称)
        try:
            model = await self.repository.get_model_config("default")
        except Exception:
            # 如果没有default模型配置,返回None或使用默认值
            from domain.value_objects.configuration import ModelConfig
            model = ModelConfig(model_type="LGBM", hyperparameters={}, default_type="LGBM")

        # 组装完整配置
        return Configuration(
            data_source=data_source,
            model=model,
            backtest=backtest,
        )
