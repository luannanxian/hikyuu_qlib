"""模型训练器端口"""

from abc import ABC, abstractmethod
from domain.entities.model import Model
from domain.entities.prediction import Prediction
from typing import List


class IModelTrainer(ABC):
    """模型训练器接口"""

    @abstractmethod
    async def train(self, model: Model, training_data: any) -> Model:
        """训练模型"""
        pass

    @abstractmethod
    async def predict(self, model: Model, input_data: any) -> List[Prediction]:
        """生成预测"""
        pass
