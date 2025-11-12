"""
Prediction Entity 和 PredictionBatch Aggregate

预测结果实体和预测批次聚合根,遵循 DDD 原则
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from domain.value_objects.stock_code import StockCode


@dataclass
class Prediction:
    """
    预测结果实体

    实体特征:
    - 有唯一标识 (id)
    - 业务相等性基于股票代码和预测日期

    属性:
    - stock_code: 股票代码值对象
    - prediction_date: 预测日期
    - predicted_value: 预测值(如涨跌幅)
    - confidence: 预测置信度 [0, 1]
    """

    stock_code: StockCode
    prediction_date: datetime
    predicted_value: Decimal
    confidence: Decimal = Decimal("1.0")

    # 实体唯一标识
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self):
        """验证预测数据有效性"""
        # 置信度必须在 [0, 1] 范围内
        if not (Decimal("0") <= self.confidence <= Decimal("1")):
            raise ValueError(
                f"confidence must be between 0 and 1, got confidence={self.confidence}"
            )

    def __eq__(self, other: object) -> bool:
        """
        业务相等性:基于股票代码和预测日期

        同一只股票在同一日期只有一个预测结果
        """
        if not isinstance(other, Prediction):
            return False
        return (
            self.stock_code == other.stock_code
            and self.prediction_date == other.prediction_date
        )

    def __hash__(self) -> int:
        """哈希基于股票代码和预测日期"""
        return hash((self.stock_code, self.prediction_date))

    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.stock_code.value} {self.prediction_date.date()} pred={self.predicted_value}"

    def __repr__(self) -> str:
        """调试表示"""
        return f"Prediction(stock={self.stock_code.value}, date={self.prediction_date}, value={self.predicted_value}, id={self.id[:8]}...)"


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
    - batch_date: 批次日期
    - predictions: 预测结果列表
    """

    model_id: str
    batch_date: datetime
    predictions: List[Prediction] = field(default_factory=list)

    # 聚合根唯一标识
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def add_prediction(self, prediction: Prediction) -> None:
        """
        添加预测到批次

        Args:
            prediction: 预测结果实体

        Raises:
            ValueError: 如果预测已存在(相同股票+日期)
        """
        # 检查是否已存在相同预测
        existing = self.get_prediction(
            prediction.stock_code, prediction.prediction_date
        )
        if existing is not None:
            raise ValueError(
                f"Prediction already exists for {prediction.stock_code.value} on {prediction.prediction_date}"
            )

        self.predictions.append(prediction)

    def remove_prediction(
        self, stock_code: StockCode, prediction_date: datetime
    ) -> None:
        """
        从批次移除预测

        Args:
            stock_code: 股票代码
            prediction_date: 预测日期
        """
        self.predictions = [
            p
            for p in self.predictions
            if not (p.stock_code == stock_code and p.prediction_date == prediction_date)
        ]

    def get_prediction(
        self, stock_code: StockCode, prediction_date: datetime
    ) -> Optional[Prediction]:
        """
        根据股票代码和日期获取预测

        Args:
            stock_code: 股票代码
            prediction_date: 预测日期

        Returns:
            Optional[Prediction]: 找到的预测,或 None
        """
        for prediction in self.predictions:
            if (
                prediction.stock_code == stock_code
                and prediction.prediction_date == prediction_date
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

    def average_confidence(self) -> Decimal:
        """
        计算平均置信度

        Returns:
            Decimal: 平均置信度
        """
        if not self.predictions:
            return Decimal("0")

        total = sum(p.confidence for p in self.predictions)
        return total / Decimal(len(self.predictions))

    def __str__(self) -> str:
        """字符串表示"""
        return f"Batch({self.model_id}) {self.batch_date.date()} size={len(self.predictions)}"

    def __repr__(self) -> str:
        """调试表示"""
        return f"PredictionBatch(model={self.model_id}, date={self.batch_date}, size={len(self.predictions)}, id={self.id[:8]}...)"
