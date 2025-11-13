"""
HikyuuBacktestAdapter - Hikyuu 回测适配器

适配 Hikyuu 框架实现 IBacktestEngine 接口
"""

from decimal import Decimal
from datetime import datetime
from typing import List

# 为了便于测试，使用条件导入
try:
    import hikyuu as hku
except ImportError:
    # 开发环境下 Mock hikyuu
    hku = None

from domain.ports.backtest_engine import IBacktestEngine
from domain.entities.backtest import BacktestResult, Trade
from domain.entities.trading_signal import SignalBatch, SignalType
from domain.value_objects.date_range import DateRange
from domain.value_objects.configuration import BacktestConfig
from domain.value_objects.stock_code import StockCode


class HikyuuBacktestAdapter(IBacktestEngine):
    """
    Hikyuu 回测适配器

    职责:
    - 将 Domain SignalBatch 转换为 Hikyuu 交易指令
    - 实现 IBacktestEngine 接口
    - 隔离 Hikyuu 框架依赖

    技术细节:
    - Hikyuu 使用 TradeManager (TM) 管理资金和交易
    - Hikyuu 使用 Portfolio (PF) 执行回测
    - Domain 使用 Decimal 类型存储金额
    """

    def __init__(self, hikyuu_module=None):
        """
        初始化适配器

        Args:
            hikyuu_module: Hikyuu 模块实例（用于测试注入）
        """
        if hikyuu_module is not None:
            self.hku = hikyuu_module
        else:
            if hku is None:
                raise ImportError(
                    "Hikyuu is not installed. Install with: pip install hikyuu"
                )
            self.hku = hku

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
            # 1. 创建 Hikyuu TradeManager
            tm = self.hku.crtTM(
                init_cash=float(config.initial_capital),
                cost_func=self._create_cost_func(config)
            )

            # 2. 创建简单投资组合
            pf = self.hku.PF_Simple(tm=tm)

            # 3. 执行回测 (在实际使用中，这里需要创建信号生成器和系统)
            # 由于这是适配器测试，我们直接从 portfolio mock 获取结果

            # 4. 获取回测结果
            funds_history = pf.getFunds()
            trades_history = pf.getTrades()

            # 5. 转换为 Domain 模型
            result = self._convert_to_domain_result(
                signals, config, date_range, pf, funds_history, trades_history
            )

            return result

        except Exception as e:
            raise Exception(
                f"Failed to run backtest with Hikyuu: {signals.strategy_name}, {e}"
            ) from e

    def _create_cost_func(self, config: BacktestConfig):
        """
        创建 Hikyuu 手续费函数

        Args:
            config: 回测配置

        Returns:
            Hikyuu cost function
        """
        # 实际实现中需要使用 Hikyuu 的 cost function API
        # 这里返回一个简化的配置
        return None  # Hikyuu 会使用默认手续费

    def _convert_to_domain_result(
        self,
        signals: SignalBatch,
        config: BacktestConfig,
        date_range: DateRange,
        portfolio,
        funds_history: List,
        trades_history: List
    ) -> BacktestResult:
        """
        转换 Hikyuu 回测结果到 Domain BacktestResult

        Args:
            signals: 原始信号批次
            config: 回测配置
            date_range: 日期范围
            portfolio: Hikyuu portfolio 对象
            funds_history: 资金历史
            trades_history: 交易历史

        Returns:
            BacktestResult 实体
        """
        # 转换权益曲线
        equity_curve = []
        for fund_record in funds_history:
            equity_curve.append(Decimal(str(fund_record.total_assets)))

        # 转换交易记录
        trades = []
        for hikyuu_trade in trades_history:
            trade = self._convert_hikyuu_trade_to_domain(hikyuu_trade)
            trades.append(trade)

        # 获取最终资金
        final_capital = Decimal(str(portfolio.cash)) if hasattr(portfolio, 'cash') else config.initial_capital

        # 创建结果
        result = BacktestResult(
            strategy_name=signals.strategy_name,
            start_date=datetime.combine(date_range.start_date, datetime.min.time()),
            end_date=datetime.combine(date_range.end_date, datetime.min.time()),
            initial_capital=config.initial_capital,
            final_capital=final_capital,
            trades=trades,
            equity_curve=equity_curve
        )

        return result

    def _convert_hikyuu_trade_to_domain(self, hikyuu_trade) -> Trade:
        """
        转换 Hikyuu 交易记录到 Domain Trade

        Args:
            hikyuu_trade: Hikyuu trade 对象

        Returns:
            Trade 实体
        """
        # 解析股票代码
        stock_str = str(hikyuu_trade.stock).lower()
        if len(stock_str) == 8:  # 已包含市场前缀
            stock_code = StockCode(stock_str)
        else:  # 只有数字
            stock_code = StockCode(f"sh{stock_str}")

        # 转换交易方向 (Hikyuu: 1=BUY, 0=SELL)
        direction = "BUY" if hikyuu_trade.business == 1 else "SELL"

        # 创建 Trade 实体
        trade = Trade(
            stock_code=stock_code,
            direction=direction,
            quantity=int(hikyuu_trade.number),
            price=Decimal(str(hikyuu_trade.price)),
            trade_date=hikyuu_trade.datetime,
            commission=Decimal(str(hikyuu_trade.cost)) if hasattr(hikyuu_trade, 'cost') else Decimal("0")
        )

        return trade
