"""
Signal Provider Port Interface

定义信号提供者的接口,由Adapters层实现
"""

from abc import ABC, abstractmethod
from datetime import datetime

from domain.entities.prediction import PredictionBatch
from domain.entities.trading_signal import SignalBatch, TradingSignal
from domain.value_objects.stock_code import StockCode


class ISignalProvider(ABC):
    """
    信号提供者接口(Port)

    职责:
    - 从预测结果生成交易信号
    - 支持Top-K选股策略
    - 处理信号强度计算

    实现者:
    - CustomSG_QlibFactor: 基于Qlib预测的Hikyuu信号指示器
    - DynamicRebalanceSG: 动态调仓信号指示器
    """

    @abstractmethod
    def generate_signals_from_predictions(
        self,
        prediction_batch: PredictionBatch,
        buy_threshold: float = 0.02,
        sell_threshold: float = -0.02,
        top_k: int | None = None,
    ) -> SignalBatch:
        """
        从预测批次生成交易信号批次

        Args:
            prediction_batch: 预测结果批次
            buy_threshold: 买入阈值(预测值 > threshold 时买入)
            sell_threshold: 卖出阈值(预测值 < threshold 时卖出)
            top_k: Top-K选股(只对排名前K的股票生成买入信号)

        Returns:
            SignalBatch: 交易信号批次
        """

    @abstractmethod
    def get_signal_for_stock(
        self,
        stock_code: StockCode,
        signal_date: datetime,
    ) -> TradingSignal | None:
        """
        获取指定股票在指定日期的交易信号

        Args:
            stock_code: 股票代码
            signal_date: 信号日期

        Returns:
            Optional[TradingSignal]: 交易信号,如果不存在则返回None
        """

    @abstractmethod
    def get_top_k_stocks(
        self,
        prediction_batch: PredictionBatch,
        k: int,
    ) -> list[StockCode]:
        """
        从预测批次中选出Top-K股票

        Args:
            prediction_batch: 预测结果批次
            k: 选股数量

        Returns:
            List[StockCode]: Top-K股票代码列表(按预测值降序)
        """
