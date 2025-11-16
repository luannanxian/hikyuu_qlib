"""
Prediction Entity 和 PredictionBatch Aggregate

预测结果实体和预测批次聚合根,遵循 DDD 原则
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime

import pandas as pd

from domain.value_objects.stock_code import StockCode


@dataclass
class Prediction:
    """
    预测结果实体

    实体特征:
    - 有唯一标识 (id)
    - 业务相等性基于股票代码和时间戳

    属性:
    - stock_code: 股票代码值对象
    - timestamp: 预测时间戳（兼容prediction_date）
    - predicted_value: 预测值(如涨跌幅)
    - confidence: 预测置信度（可选，0-1之间）
    - model_id: 关联的模型ID
    """

    stock_code: StockCode
    timestamp: datetime  # 使用timestamp而非prediction_date
    predicted_value: float  # 使用float以兼容模型输出
    model_id: str  # 关联的模型ID
    confidence: float | None = None  # 可选的置信度

    # 实体唯一标识
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # 兼容性属性
    @property
    def prediction_date(self) -> datetime:
        """兼容旧代码的prediction_date属性"""
        return self.timestamp

    def __post_init__(self):
        """验证预测数据有效性"""
        # 如果提供了置信度，验证其在 [0, 1] 范围内
        if self.confidence is not None:
            if not (0 <= self.confidence <= 1):
                raise ValueError(
                    f"confidence must be between 0 and 1, got confidence={self.confidence}",
                )

    def __eq__(self, other: object) -> bool:
        """
        业务相等性:基于股票代码和时间戳

        同一只股票在同一时刻只有一个预测结果
        """
        if not isinstance(other, Prediction):
            return False
        return (
            self.stock_code == other.stock_code
            and self.timestamp == other.timestamp
        )

    def __hash__(self) -> int:
        """哈希基于股票代码和时间戳"""
        return hash((self.stock_code, self.timestamp))

    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.stock_code.value} {self.timestamp.date()} pred={self.predicted_value}"

    def __repr__(self) -> str:
        """调试表示"""
        return f"Prediction(stock={self.stock_code.value}, time={self.timestamp}, value={self.predicted_value}, id={self.id[:8]}...)"


@dataclass
class PredictionBatch:
    """
    预测批次聚合根

    聚合根特征:
    - 有唯一标识 (id)
    - 管理 Prediction 实体的生命周期
    - 确保聚合内的业务不变性

    属性:
    - model_id: 模型ID
    - predictions: 预测结果列表
    - generated_at: 生成时间（兼容batch_date）
    """

    model_id: str
    predictions: list[Prediction] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)  # 使用generated_at

    # 聚合根唯一标识
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # 兼容性属性
    @property
    def batch_date(self) -> datetime:
        """兼容旧代码的batch_date属性"""
        return self.generated_at

    def add_prediction(self, prediction: Prediction) -> None:
        """
        添加预测到批次

        Args:
            prediction: 预测结果实体

        Raises:
            ValueError: 如果预测已存在(相同股票+时间戳)
        """
        # 检查是否已存在相同预测
        existing = self.get_prediction(
            prediction.stock_code, prediction.timestamp,
        )
        if existing is not None:
            raise ValueError(
                f"Prediction already exists for {prediction.stock_code.value} at {prediction.timestamp}",
            )

        self.predictions.append(prediction)

    def remove_prediction(
        self, stock_code: StockCode, timestamp: datetime,
    ) -> None:
        """
        从批次移除预测

        Args:
            stock_code: 股票代码
            timestamp: 时间戳
        """
        self.predictions = [
            p
            for p in self.predictions
            if not (p.stock_code == stock_code and p.timestamp == timestamp)
        ]

    def get_prediction(
        self, stock_code: StockCode, timestamp: datetime,
    ) -> Prediction | None:
        """
        根据股票代码和时间戳获取预测

        Args:
            stock_code: 股票代码
            timestamp: 时间戳

        Returns:
            Optional[Prediction]: 找到的预测,或 None
        """
        for prediction in self.predictions:
            if (
                prediction.stock_code == stock_code
                and prediction.timestamp == timestamp
            ):
                return prediction
        return None

    def size(self) -> int:
        """
        获取批次大小

        Returns:
            int: 预测数量
        """
        return len(self.predictions)

    def average_confidence(self) -> float | None:
        """
        计算平均置信度

        Returns:
            Optional[float]: 平均置信度，如果没有置信度信息则返回None
        """
        if not self.predictions:
            return None

        confidences = [p.confidence for p in self.predictions if p.confidence is not None]
        if not confidences:
            return None

        return sum(confidences) / len(confidences)

    def to_dataframe(self) -> pd.DataFrame:
        """
        转换为DataFrame格式

        Returns:
            pd.DataFrame: 包含所有预测的DataFrame
        """
        records = []
        for pred in self.predictions:
            records.append({
                "stock_code": pred.stock_code.value,
                "timestamp": pred.timestamp,
                "predicted_value": pred.predicted_value,
                "confidence": pred.confidence,
                "model_id": pred.model_id,
                "prediction_id": pred.id,
            })

        return pd.DataFrame(records)

    def __str__(self) -> str:
        """字符串表示"""
        return f"Batch({self.model_id}) {self.generated_at.date()} size={len(self.predictions)}"

    def __repr__(self) -> str:
        """调试表示"""
        return f"PredictionBatch(model={self.model_id}, generated={self.generated_at}, size={len(self.predictions)}, id={self.id[:8]}...)"
