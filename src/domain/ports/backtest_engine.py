"""回测引擎端口"""

from abc import ABC, abstractmethod

from domain.entities.backtest import BacktestResult
from domain.entities.trading_signal import SignalBatch
from domain.value_objects.configuration import BacktestConfig
from domain.value_objects.date_range import DateRange


class IBacktestEngine(ABC):
    """回测引擎接口"""

    @abstractmethod
    async def run_backtest(
        self, signals: SignalBatch, config: BacktestConfig, date_range: DateRange,
    ) -> BacktestResult:
        """运行回测"""
