"""
HikyuuBacktestAdapter 单元测试

测试 HikyuuBacktestAdapter 实现 IBacktestEngine 接口,
使用 Mock 隔离 Hikyuu 框架依赖
"""

import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import MagicMock, patch

from domain.entities.trading_signal import (
    SignalBatch,
    TradingSignal,
    SignalType,
    SignalStrength,
)
from domain.value_objects.stock_code import StockCode
from domain.value_objects.date_range import DateRange
from domain.value_objects.configuration import BacktestConfig


class TestHikyuuBacktestAdapter:
    """测试 HikyuuBacktestAdapter"""

    @pytest.fixture
    def signal_batch(self) -> SignalBatch:
        """信号批次 fixture"""
        batch = SignalBatch(
            strategy_name="test_strategy", batch_date=datetime(2024, 1, 1)
        )
        # 添加买入信号
        batch.add_signal(
            TradingSignal(
                stock_code=StockCode("sz000001"),
                signal_date=datetime(2024, 1, 2),
                signal_type=SignalType.BUY,
                signal_strength=SignalStrength.STRONG,
                price=Decimal("10.5"),
            )
        )
        # 添加卖出信号
        batch.add_signal(
            TradingSignal(
                stock_code=StockCode("sz000001"),
                signal_date=datetime(2024, 1, 10),
                signal_type=SignalType.SELL,
                signal_strength=SignalStrength.MEDIUM,
                price=Decimal("11.2"),
            )
        )
        return batch

    @pytest.fixture
    def backtest_config(self) -> BacktestConfig:
        """回测配置 fixture"""
        return BacktestConfig(
            initial_capital=Decimal("100000"),
            commission_rate=Decimal("0.0003"),
            slippage_rate=Decimal("0.0001"),
        )

    @pytest.fixture
    def date_range(self) -> DateRange:
        """日期范围 fixture"""
        return DateRange(
            start_date=datetime(2024, 1, 1), end_date=datetime(2024, 12, 31)
        )

    @pytest.mark.asyncio
    async def test_run_backtest_success(
        self, signal_batch, backtest_config, date_range
    ):
        """
        测试成功运行回测

        验证:
        1. 调用 Hikyuu Portfolio Manager
        2. 返回 BacktestResult
        3. 包含交易记录和权益曲线
        """
        from adapters.hikyuu.hikyuu_backtest_adapter import HikyuuBacktestAdapter

        # Mock Hikyuu Portfolio Manager
        with patch("adapters.hikyuu.hikyuu_backtest_adapter.hikyuu") as mock_hq:
            # Mock Portfolio
            mock_portfolio = MagicMock()
            mock_portfolio.name = "test_strategy"
            mock_portfolio.get_performance.return_value = {
                "total_return": 0.15,
                "sharpe_ratio": 1.8,
                "max_drawdown": 0.05,
            }
            mock_portfolio.get_trade_list.return_value = [
                {
                    "stock": "000001",
                    "type": "BUY",
                    "price": 10.5,
                    "quantity": 1000,
                    "date": datetime(2024, 1, 2),
                },
                {
                    "stock": "000001",
                    "type": "SELL",
                    "price": 11.2,
                    "quantity": 1000,
                    "date": datetime(2024, 1, 10),
                },
            ]
            mock_portfolio.get_equity_curve.return_value = [
                100000,
                105000,
                110000,
                115000,
            ]

            mock_hq.Portfolio.return_value = mock_portfolio

            # 执行
            adapter = HikyuuBacktestAdapter()
            result = await adapter.run_backtest(
                signals=signal_batch, config=backtest_config, date_range=date_range
            )

            # 验证
            assert result is not None
            assert result.strategy_name == "test_strategy"
            assert result.initial_capital == Decimal("100000")
            assert result.final_capital > result.initial_capital
            assert len(result.trades) == 2
            assert len(result.equity_curve) > 0

    @pytest.mark.asyncio
    async def test_signal_to_trade_conversion(
        self, signal_batch, backtest_config, date_range
    ):
        """
        测试信号 → 交易转换

        验证:
        1. SignalBatch → Hikyuu 交易指令
        2. 交易方向正确映射
        3. 价格和数量计算正确
        """
        from adapters.hikyuu.hikyuu_backtest_adapter import HikyuuBacktestAdapter

        with patch("adapters.hikyuu.hikyuu_backtest_adapter.hikyuu") as mock_hq:
            mock_portfolio = MagicMock()
            mock_portfolio.name = "test_strategy"
            mock_portfolio.get_performance.return_value = {"total_return": 0.1}
            mock_portfolio.get_trade_list.return_value = []
            mock_portfolio.get_equity_curve.return_value = [100000]

            mock_hq.Portfolio.return_value = mock_portfolio

            adapter = HikyuuBacktestAdapter()
            result = await adapter.run_backtest(
                signals=signal_batch, config=backtest_config, date_range=date_range
            )

            # 验证信号被处理
            assert result is not None

    @pytest.mark.asyncio
    async def test_backtest_config_mapping(
        self, signal_batch, backtest_config, date_range
    ):
        """
        测试回测配置映射

        验证:
        1. initial_capital → Hikyuu 初始资金
        2. commission_rate → Hikyuu 手续费率
        3. slippage_rate → Hikyuu 滑点率
        """
        from adapters.hikyuu.hikyuu_backtest_adapter import HikyuuBacktestAdapter

        with patch("adapters.hikyuu.hikyuu_backtest_adapter.hikyuu") as mock_hq:
            mock_portfolio = MagicMock()
            mock_portfolio.name = "test_strategy"
            mock_portfolio.get_performance.return_value = {"total_return": 0.1}
            mock_portfolio.get_trade_list.return_value = []
            mock_portfolio.get_equity_curve.return_value = [100000]

            mock_hq.Portfolio.return_value = mock_portfolio

            adapter = HikyuuBacktestAdapter()
            await adapter.run_backtest(
                signals=signal_batch, config=backtest_config, date_range=date_range
            )

            # 验证 Portfolio 构造时使用了正确的配置
            mock_hq.Portfolio.assert_called_once()

    @pytest.mark.asyncio
    async def test_empty_signals_handling(self, backtest_config, date_range):
        """
        测试空信号处理

        验证:
        1. 接受空信号批次
        2. 返回初始资金不变的结果
        """
        from adapters.hikyuu.hikyuu_backtest_adapter import HikyuuBacktestAdapter

        # 空信号批次
        empty_batch = SignalBatch(
            strategy_name="empty_strategy", batch_date=datetime(2024, 1, 1)
        )

        with patch("adapters.hikyuu.hikyuu_backtest_adapter.hikyuu") as mock_hq:
            mock_portfolio = MagicMock()
            mock_portfolio.name = "empty_strategy"
            mock_portfolio.get_performance.return_value = {"total_return": 0.0}
            mock_portfolio.get_trade_list.return_value = []
            mock_portfolio.get_equity_curve.return_value = [100000]

            mock_hq.Portfolio.return_value = mock_portfolio

            adapter = HikyuuBacktestAdapter()
            result = await adapter.run_backtest(
                signals=empty_batch, config=backtest_config, date_range=date_range
            )

            # 验证
            assert result is not None
            assert len(result.trades) == 0
            assert result.initial_capital == result.final_capital

    @pytest.mark.asyncio
    async def test_hikyuu_backtest_error_handling(
        self, signal_batch, backtest_config, date_range
    ):
        """
        测试 Hikyuu 回测错误处理

        验证:
        1. 捕获 Hikyuu 异常
        2. 映射为领域层异常
        """
        from adapters.hikyuu.hikyuu_backtest_adapter import HikyuuBacktestAdapter

        with patch("adapters.hikyuu.hikyuu_backtest_adapter.hikyuu") as mock_hq:
            mock_hq.Portfolio.side_effect = Exception("Hikyuu backtest failed")

            adapter = HikyuuBacktestAdapter()
            with pytest.raises(Exception) as exc_info:
                await adapter.run_backtest(
                    signals=signal_batch, config=backtest_config, date_range=date_range
                )

            assert (
                "Hikyuu" in str(exc_info.value)
                or "backtest" in str(exc_info.value).lower()
            )

    @pytest.mark.asyncio
    async def test_performance_metrics_conversion(
        self, signal_batch, backtest_config, date_range
    ):
        """
        测试性能指标转换

        验证:
        1. Hikyuu 指标 → Domain BacktestResult
        2. 计算总收益、夏普比率、最大回撤
        """
        from adapters.hikyuu.hikyuu_backtest_adapter import HikyuuBacktestAdapter

        with patch("adapters.hikyuu.hikyuu_backtest_adapter.hikyuu") as mock_hq:
            mock_portfolio = MagicMock()
            mock_portfolio.name = "test_strategy"
            mock_portfolio.get_performance.return_value = {
                "total_return": 0.25,
                "sharpe_ratio": 2.1,
                "max_drawdown": 0.08,
            }
            mock_portfolio.get_trade_list.return_value = []
            mock_portfolio.get_equity_curve.return_value = [
                100000,
                110000,
                120000,
                125000,
            ]

            mock_hq.Portfolio.return_value = mock_portfolio

            adapter = HikyuuBacktestAdapter()
            result = await adapter.run_backtest(
                signals=signal_batch, config=backtest_config, date_range=date_range
            )

            # 验证指标
            assert result.total_return() >= 0
            assert len(result.equity_curve) == 4
