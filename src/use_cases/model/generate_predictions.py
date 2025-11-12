"""
GeneratePredictionsUseCase - 生成预测用例

UC-003: Generate Predictions (生成预测)
"""

from datetime import datetime
from typing import Any

from domain.entities.prediction import PredictionBatch
from domain.ports.model_repository import IModelRepository
from domain.ports.model_trainer import IModelTrainer


class GeneratePredictionsUseCase:
    """
    生成预测用例

    依赖注入:
    - repository: IModelRepository (模型仓储接口)
    - trainer: IModelTrainer (模型训练器接口)

    职责:
    - 从仓储加载模型
    - 验证模型状态是否可用于预测
    - 调用训练器生成预测
    - 创建 PredictionBatch 聚合
    - 返回预测批次
    """

    def __init__(self, repository: IModelRepository, trainer: IModelTrainer):
        """
        初始化用例

        Args:
            repository: 模型仓储接口实现
            trainer: 模型训练器接口实现
        """
        self.repository = repository
        self.trainer = trainer

    async def execute(self, model_id: str, input_data: Any) -> PredictionBatch:
        """
        执行生成预测

        Args:
            model_id: 模型ID
            input_data: 输入数据

        Returns:
            PredictionBatch: 预测批次聚合

        Raises:
            ValueError: 模型未找到或模型未就绪
            Exception: 预测生成失败时传播异常
        """
        # 1. 从仓储加载模型
        model = await self.repository.find_by_id(model_id)
        if model is None:
            raise ValueError(f"Model with id {model_id} not found")

        # 2. 验证模型是否已就绪可用于预测
        if not model.is_ready_for_prediction():
            raise ValueError(
                f"Model {model_id} is not ready for prediction. "
                f"Status: {model.status}"
            )

        # 3. 调用训练器生成预测
        predictions = await self.trainer.predict(model=model, input_data=input_data)

        # 4. 创建 PredictionBatch 聚合
        batch = PredictionBatch(
            model_id=model_id, batch_date=datetime.now(), predictions=predictions
        )

        # 5. 返回预测批次
        return batch
