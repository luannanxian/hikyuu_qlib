"""
RunBacktestUseCase - 运行回测用例

UC-005: Run Backtest (运行回测)
"""

from domain.entities.backtest import BacktestResult
from domain.entities.trading_signal import SignalBatch
from domain.ports.backtest_engine import IBacktestEngine
from domain.value_objects.configuration import BacktestConfig
from domain.value_objects.date_range import DateRange


class RunBacktestUseCase:
    """
    运行回测用例

    依赖注入:
    - engine: IBacktestEngine (回测引擎接口)

    职责:
    - 验证回测配置
    - 调用回测引擎运行回测
    - 返回回测结果
    """

    def __init__(self, engine: IBacktestEngine):
        """
        初始化用例

        Args:
            engine: 回测引擎接口实现
        """
        self.engine = engine

    async def execute(
        self, signals: SignalBatch, config: BacktestConfig, date_range: DateRange,
    ) -> BacktestResult:
        """
        执行运行回测

        Args:
            signals: 信号批次聚合
            config: 回测配置值对象
            date_range: 日期范围值对象

        Returns:
            BacktestResult: 回测结果实体

        Raises:
            Exception: 回测引擎错误时传播异常
        """
        # 1. 配置验证由 BacktestConfig 值对象保证

        # 2. 调用回测引擎运行回测
        result = await self.engine.run_backtest(
            signals=signals, config=config, date_range=date_range,
        )

        # 3. 返回回测结果
        return result
