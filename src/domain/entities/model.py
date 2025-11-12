"""
Model Entity

模型实体,遵循 DDD 实体原则
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Optional


class ModelType(str, Enum):
    """模型类型枚举"""

    LGBM = "LGBM"
    MLP = "MLP"
    LSTM = "LSTM"
    GRU = "GRU"
    TRANSFORMER = "TRANSFORMER"


class ModelStatus(str, Enum):
    """模型状态枚举"""

    UNTRAINED = "UNTRAINED"  # 未训练
    TRAINED = "TRAINED"  # 已训练
    DEPLOYED = "DEPLOYED"  # 已部署
    ARCHIVED = "ARCHIVED"  # 已归档


@dataclass
class Model:
    """
    模型实体

    实体特征:
    - 有唯一标识 (id)
    - 实体相等性基于 ID

    属性:
    - model_type: 模型类型
    - hyperparameters: 超参数字典
    - training_date: 训练日期
    - metrics: 评估指标字典
    - status: 模型状态
    """

    model_type: ModelType
    hyperparameters: Dict[str, any]
    training_date: Optional[datetime] = None
    metrics: Dict[str, float] = field(default_factory=dict)
    status: ModelStatus = ModelStatus.UNTRAINED

    # 实体唯一标识
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def is_trained(self) -> bool:
        """
        判断模型是否已训练

        Returns:
            bool: 是否已训练
        """
        return self.status in [ModelStatus.TRAINED, ModelStatus.DEPLOYED]

    def is_deployed(self) -> bool:
        """
        判断模型是否已部署

        Returns:
            bool: 是否已部署
        """
        return self.status == ModelStatus.DEPLOYED

    def update_metrics(self, metrics: Dict[str, float]) -> None:
        """
        更新模型评估指标

        Args:
            metrics: 新的评估指标
        """
        self.metrics = metrics

    def mark_as_trained(
        self, metrics: Dict[str, float], threshold: float = 0.5
    ) -> None:
        """
        标记模型为已训练状态

        Args:
            metrics: 训练后的评估指标
            threshold: 指标阈值,默认0.5

        Raises:
            ValueError: 如果指标低于阈值
        """
        # 验证指标是否达标
        if not self.validate_metrics(metrics, threshold):
            raise ValueError(
                f"Model metrics below threshold. Required: {threshold}, "
                f"got: {metrics}"
            )

        self.status = ModelStatus.TRAINED
        self.metrics = metrics
        self.training_date = datetime.now()

    def validate_metrics(
        self, metrics: Dict[str, float], threshold: float = 0.5
    ) -> bool:
        """
        验证模型指标是否达标

        Args:
            metrics: 评估指标字典
            threshold: 阈值

        Returns:
            bool: 是否所有指标都达标
        """
        if not metrics:
            return False

        # 检查所有指标是否达到阈值
        return all(value >= threshold for value in metrics.values())

    def is_ready_for_prediction(self) -> bool:
        """
        判断模型是否可以用于预测

        Returns:
            bool: 模型是否已训练且可用于预测
        """
        return self.status in [ModelStatus.TRAINED, ModelStatus.DEPLOYED]

    @property
    def trained_at(self) -> Optional[datetime]:
        """
        获取训练时间 (training_date 的别名)

        Returns:
            Optional[datetime]: 训练时间
        """
        return self.training_date

    def deploy(self) -> None:
        """
        部署模型

        Raises:
            ValueError: 如果模型未训练
        """
        if not self.is_trained():
            raise ValueError("Cannot deploy untrained model")

        self.status = ModelStatus.DEPLOYED

    def archive(self) -> None:
        """归档模型"""
        self.status = ModelStatus.ARCHIVED

    def __eq__(self, other: object) -> bool:
        """
        实体相等性:基于 ID

        不同于值对象,实体即使属性相同也不相等
        """
        if not isinstance(other, Model):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """哈希基于 ID"""
        return hash(self.id)

    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.model_type.value} ({self.status.value})"

    def __repr__(self) -> str:
        """调试表示"""
        return f"Model(type={self.model_type.value}, status={self.status.value}, id={self.id[:8]}...)"
