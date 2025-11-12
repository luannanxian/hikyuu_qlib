"""
BacktestResult 和 Trade 实体单元测试

测试 DR-008: BacktestResult (回测结果) 和 Trade (交易) 领域模型
"""

from datetime import datetime
from decimal import Decimal

from domain.entities.backtest import BacktestResult, Trade
from domain.value_objects.stock_code import StockCode


class TestTradeCreation:
    """测试 Trade 创建"""

    def test_create_trade_with_all_fields(self):
        """测试创建完整交易"""
        trade = Trade(
            stock_code=StockCode("sh600000"),
            direction="BUY",
            quantity=1000,
            price=Decimal("10.50"),
            trade_date=datetime(2024, 1, 10),
            commission=Decimal("5.25"),
        )

        assert trade.stock_code == StockCode("sh600000")
        assert trade.direction == "BUY"
        assert trade.quantity == 1000
        assert trade.price == Decimal("10.50")
        assert trade.commission == Decimal("5.25")

    def test_calculate_profit(self):
        """测试交易盈亏计算"""
        buy_trade = Trade(
            stock_code=StockCode("sh600000"),
            direction="BUY",
            quantity=1000,
            price=Decimal("10.00"),
            trade_date=datetime(2024, 1, 10),
        )
        sell_trade = Trade(
            stock_code=StockCode("sh600000"),
            direction="SELL",
            quantity=1000,
            price=Decimal("12.00"),
            trade_date=datetime(2024, 1, 20),
        )

        profit = sell_trade.calculate_profit(buy_trade)
        # 盈亏 = (12.00 - 10.00) * 1000 = 2000
        assert profit == Decimal("2000")

    def test_calculate_hold_days(self):
        """测试持有天数计算"""
        buy_trade = Trade(
            stock_code=StockCode("sh600000"),
            direction="BUY",
            quantity=1000,
            price=Decimal("10.00"),
            trade_date=datetime(2024, 1, 10),
        )
        sell_trade = Trade(
            stock_code=StockCode("sh600000"),
            direction="SELL",
            quantity=1000,
            price=Decimal("12.00"),
            trade_date=datetime(2024, 1, 20),
        )

        days = sell_trade.calculate_hold_days(buy_trade)
        assert days == 10


class TestBacktestResultCreation:
    """测试 BacktestResult 创建"""

    def test_create_backtest_result(self):
        """测试创建回测结果"""
        result = BacktestResult(
            strategy_name="MA_Cross",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
            initial_capital=Decimal("100000"),
            final_capital=Decimal("120000"),
        )

        assert result.strategy_name == "MA_Cross"
        assert result.initial_capital == Decimal("100000")
        assert result.final_capital == Decimal("120000")

    def test_calculate_total_return(self):
        """测试总收益率计算"""
        result = BacktestResult(
            strategy_name="MA_Cross",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
            initial_capital=Decimal("100000"),
            final_capital=Decimal("120000"),
        )

        # 收益率 = (120000 - 100000) / 100000 = 0.20 = 20%
        assert result.total_return() == Decimal("0.20")

    def test_calculate_sharpe_ratio(self):
        """测试夏普比率计算"""
        result = BacktestResult(
            strategy_name="MA_Cross",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
            initial_capital=Decimal("100000"),
            final_capital=Decimal("120000"),
        )

        # 简化的夏普比率计算
        sharpe = result.calculate_sharpe_ratio(risk_free_rate=Decimal("0.03"))
        assert sharpe > Decimal("0")

    def test_calculate_max_drawdown(self):
        """测试最大回撤计算"""
        result = BacktestResult(
            strategy_name="MA_Cross",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
            initial_capital=Decimal("100000"),
            final_capital=Decimal("120000"),
        )

        # 添加一些权益曲线数据
        result.equity_curve = [
            Decimal("100000"),
            Decimal("110000"),
            Decimal("105000"),  # 回撤
            Decimal("120000"),
        ]

        max_dd = result.calculate_max_drawdown()
        # 最大回撤 = (110000 - 105000) / 110000 ≈ 0.0454
        assert max_dd > Decimal("0.04")

    def test_get_win_rate(self):
        """测试胜率计算"""
        result = BacktestResult(
            strategy_name="MA_Cross",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
            initial_capital=Decimal("100000"),
            final_capital=Decimal("120000"),
        )

        # 添加交易记录
        trade1 = Trade(
            stock_code=StockCode("sh600000"),
            direction="BUY",
            quantity=1000,
            price=Decimal("10.00"),
            trade_date=datetime(2024, 1, 10),
        )
        trade2 = Trade(
            stock_code=StockCode("sh600000"),
            direction="SELL",
            quantity=1000,
            price=Decimal("12.00"),  # 盈利
            trade_date=datetime(2024, 1, 20),
        )
        trade3 = Trade(
            stock_code=StockCode("sz000001"),
            direction="BUY",
            quantity=500,
            price=Decimal("20.00"),
            trade_date=datetime(2024, 2, 10),
        )
        trade4 = Trade(
            stock_code=StockCode("sz000001"),
            direction="SELL",
            quantity=500,
            price=Decimal("18.00"),  # 亏损
            trade_date=datetime(2024, 2, 20),
        )

        result.add_trade(trade1)
        result.add_trade(trade2)
        result.add_trade(trade3)
        result.add_trade(trade4)

        # 2笔交易,1笔盈利,胜率 = 50%
        win_rate = result.get_win_rate()
        assert win_rate == Decimal("0.5")
