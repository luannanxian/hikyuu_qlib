"""
BacktestResult 和 Trade 实体

回测结果和交易实体,遵循 DDD 原则
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List

from domain.value_objects.stock_code import StockCode


@dataclass
class Trade:
    """
    交易实体

    实体特征:
    - 有唯一标识 (id)

    属性:
    - stock_code: 股票代码
    - direction: 交易方向(BUY/SELL)
    - quantity: 交易数量
    - price: 交易价格
    - trade_date: 交易日期
    - commission: 手续费
    """

    stock_code: StockCode
    direction: str
    quantity: int
    price: Decimal
    trade_date: datetime
    commission: Decimal = Decimal("0")

    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def calculate_profit(self, buy_trade: "Trade") -> Decimal:
        """计算相对于买入交易的盈亏"""
        if self.direction == "SELL":
            return (self.price - buy_trade.price) * Decimal(self.quantity)
        return Decimal("0")

    def calculate_hold_days(self, buy_trade: "Trade") -> int:
        """计算持有天数"""
        return (self.trade_date - buy_trade.trade_date).days


@dataclass
class BacktestResult:
    """
    回测结果聚合根

    聚合根特征:
    - 有唯一标识 (id)
    - 管理 Trade 实体的生命周期

    属性:
    - strategy_name: 策略名称
    - start_date: 开始日期
    - end_date: 结束日期
    - initial_capital: 初始资金
    - final_capital: 最终资金
    - trades: 交易列表
    - equity_curve: 权益曲线
    """

    strategy_name: str
    start_date: datetime
    end_date: datetime
    initial_capital: Decimal
    final_capital: Decimal
    trades: List[Trade] = field(default_factory=list)
    equity_curve: List[Decimal] = field(default_factory=list)

    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def add_trade(self, trade: Trade) -> None:
        """添加交易"""
        self.trades.append(trade)

    def total_return(self) -> Decimal:
        """计算总收益率"""
        if self.initial_capital == 0:
            return Decimal("0")
        return (self.final_capital - self.initial_capital) / self.initial_capital

    def calculate_sharpe_ratio(
        self, risk_free_rate: Decimal = Decimal("0.03")
    ) -> Decimal:
        """计算夏普比率(简化版)"""
        total_ret = self.total_return()
        # 简化计算:假设波动率为收益率的20%
        volatility = (
            abs(total_ret) * Decimal("0.2") if total_ret != 0 else Decimal("0.01")
        )
        return (
            (total_ret - risk_free_rate) / volatility
            if volatility != 0
            else Decimal("0")
        )

    def calculate_max_drawdown(self) -> Decimal:
        """计算最大回撤"""
        if not self.equity_curve:
            return Decimal("0")

        max_value = self.equity_curve[0]
        max_drawdown = Decimal("0")

        for value in self.equity_curve:
            if value > max_value:
                max_value = value
            drawdown = (
                (max_value - value) / max_value if max_value > 0 else Decimal("0")
            )
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        return max_drawdown

    def get_win_rate(self) -> Decimal:
        """计算胜率"""
        if len(self.trades) < 2:
            return Decimal("0")

        # 匹配买卖对
        buy_trades = {}
        wins = 0
        total_pairs = 0

        for trade in self.trades:
            if trade.direction == "BUY":
                buy_trades[trade.stock_code] = trade
            elif trade.direction == "SELL" and trade.stock_code in buy_trades:
                profit = trade.calculate_profit(buy_trades[trade.stock_code])
                if profit > 0:
                    wins += 1
                total_pairs += 1
                del buy_trades[trade.stock_code]

        return Decimal(wins) / Decimal(total_pairs) if total_pairs > 0 else Decimal("0")
