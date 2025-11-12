"""
HikyuuBacktestAdapter - Hikyuu 回测适配器

适配 Hikyuu 框架实现 IBacktestEngine 接口
"""

from decimal import Decimal
from datetime import datetime
from typing import List

# 为了便于测试，使用条件导入
try:
    import hikyuu
except ImportError:
    # 开发环境下 Mock hikyuu
    hikyuu = None

from domain.ports.backtest_engine import IBacktestEngine
from domain.entities.backtest import BacktestResult, Trade
from domain.entities.trading_signal import SignalBatch, SignalType
from domain.value_objects.date_range import DateRange
from domain.value_objects.configuration import BacktestConfig
from domain.value_objects.stock_code import StockCode


class HikyuuBacktestAdapter(IBacktestEngine):
    """
    Hikyuu 回测适配器

    实现 IBacktestEngine 接口,适配 Hikyuu 回测框架
    """

    def __init__(self, hikyuu_module=None):
        """
        初始化适配器

        Args:
            hikyuu_module: Hikyuu 模块实例（用于测试注入）
        """
        self.hikyuu = hikyuu_module if hikyuu_module is not None else hikyuu

    def _map_signal_type_to_hikyuu(self, signal_type: SignalType) -> str:
        """
        映射领域层信号类型到 Hikyuu 交易方向

        Args:
            signal_type: 领域层信号类型

        Returns:
            Hikyuu 交易方向字符串
        """
        mapping = {
            SignalType.BUY: "BUY",
            SignalType.SELL: "SELL",
            SignalType.HOLD: "HOLD",
        }
        return mapping.get(signal_type, "HOLD")

    def _convert_trade_to_domain(
        self, hikyuu_trade: dict, stock_code: StockCode
    ) -> Trade:
        """
        转换 Hikyuu 交易到领域层格式

        Args:
            hikyuu_trade: Hikyuu 交易记录
            stock_code: 股票代码

        Returns:
            领域层 Trade 实体
        """
        return Trade(
            stock_code=stock_code,
            direction=hikyuu_trade.get("type", "BUY"),
            quantity=hikyuu_trade.get("quantity", 0),
            price=Decimal(str(hikyuu_trade.get("price", 0))),
            trade_date=hikyuu_trade.get("date", datetime.now()),
            commission=Decimal(str(hikyuu_trade.get("commission", 0))),
        )

    def _convert_equity_curve(self, hikyuu_curve: List) -> List[Decimal]:
        """
        转换权益曲线到领域层格式

        Args:
            hikyuu_curve: Hikyuu 权益曲线

        Returns:
            领域层权益曲线（Decimal 列表）
        """
        return [Decimal(str(value)) for value in hikyuu_curve]

    async def run_backtest(
        self, signals: SignalBatch, config: BacktestConfig, date_range: DateRange
    ) -> BacktestResult:
        """
        运行回测

        Args:
            signals: 交易信号批次
            config: 回测配置
            date_range: 回测日期范围

        Returns:
            BacktestResult: 回测结果聚合根

        Raises:
            Exception: 当 Hikyuu 回测失败时
        """
        try:
            # 创建 Hikyuu Portfolio
            # 注意：这是简化的实现，实际使用需要根据 Hikyuu API 调整
            portfolio = self.hikyuu.Portfolio(
                name=signals.strategy_name,
                init_cash=float(config.initial_capital),
                commission=float(config.commission_rate),
                slippage=float(config.slippage_rate),
            )

            # 处理交易信号
            for signal in signals.signals:
                if signal.signal_type != SignalType.HOLD:
                    # 在实际实现中，这里需要调用 Hikyuu 交易 API
                    # portfolio.order(...)
                    pass

            # 获取回测结果
            performance = portfolio.get_performance()
            trade_list = portfolio.get_trade_list()
            equity_curve = portfolio.get_equity_curve()

            # 计算最终资金
            final_capital = config.initial_capital * Decimal(
                str(1 + performance.get("total_return", 0))
            )

            # 创建回测结果
            result = BacktestResult(
                strategy_name=signals.strategy_name,
                start_date=date_range.start_date,
                end_date=date_range.end_date,
                initial_capital=config.initial_capital,
                final_capital=final_capital,
                trades=[],
                equity_curve=self._convert_equity_curve(equity_curve),
            )

            # 转换交易记录
            for hikyuu_trade in trade_list:
                # 提取股票代码
                stock_str = hikyuu_trade.get("stock", "sz000001")
                # 简化处理：假设 stock_str 已经是正确格式
                if len(stock_str) == 6:
                    stock_str = "sz" + stock_str  # 添加市场前缀
                stock_code = StockCode(stock_str)

                trade = self._convert_trade_to_domain(hikyuu_trade, stock_code)
                result.add_trade(trade)

            return result

        except Exception as e:
            # 将 Hikyuu 异常映射为领域层异常
            raise Exception(
                f"Failed to run backtest with Hikyuu: {signals.strategy_name}, {e}"
            ) from e
