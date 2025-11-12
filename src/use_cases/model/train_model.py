"""
TrainModelUseCase - 训练模型用例

UC-002: Train Model (训练模型)
"""

from typing import Any

from domain.entities.model import Model
from domain.ports.model_repository import IModelRepository
from domain.ports.model_trainer import IModelTrainer


class TrainModelUseCase:
    """
    训练模型用例

    依赖注入:
    - trainer: IModelTrainer (模型训练器接口)
    - repository: IModelRepository (模型仓库接口)

    职责:
    - 协调模型训练流程
    - 调用训练器Port进行训练
    - 验证训练指标
    - 更新模型状态
    - 保存模型到仓库
    """

    def __init__(self, trainer: IModelTrainer, repository: IModelRepository):
        """
        初始化用例

        Args:
            trainer: 模型训练器接口实现
            repository: 模型仓库接口实现
        """
        self.trainer = trainer
        self.repository = repository

    async def execute(self, model: Model, training_data: Any) -> Model:
        """
        执行模型训练

        Args:
            model: 模型实体
            training_data: 训练数据

        Returns:
            Model: 训练后的模型实体

        Raises:
            Exception: 训练失败时传播异常
            ValueError: 训练指标不达标时抛出异常
        """
        # 1. 调用训练器Port训练模型
        trained_model = await self.trainer.train(
            model=model, training_data=training_data
        )

        # 2. 保存训练后的模型到仓库
        await self.repository.save(trained_model)

        # 3. 返回训练后的模型
        return trained_model
