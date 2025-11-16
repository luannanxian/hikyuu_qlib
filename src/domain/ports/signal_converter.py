"""信号转换器端口"""

from abc import ABC, abstractmethod

from domain.entities.prediction import PredictionBatch
from domain.entities.trading_signal import SignalBatch


class ISignalConverter(ABC):
    """信号转换器接口"""

    @abstractmethod
    async def convert_to_signals(
        self, predictions: PredictionBatch, strategy_params: dict,
    ) -> SignalBatch:
        """将预测转换为交易信号"""
