"""
RunBacktestUseCase 单元测试

测试 UC-005: Run Backtest (运行回测) 用例
"""

from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from domain.entities.backtest import BacktestResult
from domain.entities.trading_signal import SignalBatch, SignalType, TradingSignal
from domain.ports.backtest_engine import IBacktestEngine
from domain.value_objects.configuration import BacktestConfig
from domain.value_objects.date_range import DateRange
from domain.value_objects.stock_code import StockCode
from use_cases.backtest.run_backtest import RunBacktestUseCase


class TestRunBacktestSuccess:
    """测试成功运行回测"""

    @pytest.mark.asyncio
    async def test_run_backtest_success(self):
        """测试成功运行回测"""
        # Arrange: 准备 Mock Engine
        engine_mock = AsyncMock(spec=IBacktestEngine)

        # 创建信号批次
        signals = SignalBatch(
            strategy_name="test_strategy",
            batch_date=datetime(2024, 1, 10),
            signals=[
                TradingSignal(
                    stock_code=StockCode("sh600000"),
                    signal_date=datetime(2024, 1, 10),
                    signal_type=SignalType.BUY,
                ),
            ],
        )

        # 创建回测配置
        config = BacktestConfig(
            initial_capital=Decimal(100000),
            commission_rate=Decimal("0.0003"),
            slippage_rate=Decimal("0.0001"),
        )

        # 创建日期范围
        date_range = DateRange(
            start_date=datetime(2024, 1, 1), end_date=datetime(2024, 12, 31),
        )

        # Mock engine 返回回测结果
        mock_result = BacktestResult(
            strategy_name="test_strategy",
            start_date=date_range.start_date,
            end_date=date_range.end_date,
            initial_capital=config.initial_capital,
            final_capital=Decimal(120000),
            trades=[],
        )
        engine_mock.run_backtest.return_value = mock_result

        # 创建 Use Case
        use_case = RunBacktestUseCase(engine=engine_mock)

        # Act: 执行用例
        result = await use_case.execute(
            signals=signals, config=config, date_range=date_range,
        )

        # Assert: 验证结果
        assert isinstance(result, BacktestResult)
        assert result.strategy_name == "test_strategy"
        assert result.total_return() == Decimal("0.20")

        # 验证 engine 被正确调用
        engine_mock.run_backtest.assert_called_once_with(
            signals=signals, config=config, date_range=date_range,
        )

    @pytest.mark.asyncio
    async def test_run_backtest_calculates_metrics(self):
        """测试回测指标计算"""
        # Arrange
        engine_mock = AsyncMock(spec=IBacktestEngine)

        signals = SignalBatch(
            strategy_name="test_strategy", batch_date=datetime(2024, 1, 10), signals=[],
        )

        config = BacktestConfig(
            initial_capital=Decimal(100000),
            commission_rate=Decimal("0.0003"),
            slippage_rate=Decimal("0.0001"),
        )

        date_range = DateRange(
            start_date=datetime(2024, 1, 1), end_date=datetime(2024, 12, 31),
        )

        # Mock 返回包含完整指标的结果
        mock_result = BacktestResult(
            strategy_name="test_strategy",
            start_date=date_range.start_date,
            end_date=date_range.end_date,
            initial_capital=config.initial_capital,
            final_capital=Decimal(115000),
            trades=[],
        )
        engine_mock.run_backtest.return_value = mock_result

        use_case = RunBacktestUseCase(engine=engine_mock)

        # Act
        result = await use_case.execute(
            signals=signals, config=config, date_range=date_range,
        )

        # Assert: 验证指标计算
        assert result.total_return() == Decimal("0.15")
        assert result.final_capital == Decimal(115000)


class TestRunBacktestValidation:
    """测试配置验证"""

    @pytest.mark.asyncio
    async def test_run_backtest_validates_config(self):
        """测试回测配置验证"""
        # Arrange
        engine_mock = AsyncMock(spec=IBacktestEngine)

        signals = SignalBatch(
            strategy_name="test_strategy", batch_date=datetime(2024, 1, 10), signals=[],
        )

        date_range = DateRange(
            start_date=datetime(2024, 1, 1), end_date=datetime(2024, 12, 31),
        )

        use_case = RunBacktestUseCase(engine=engine_mock)

        # Act & Assert: 无效配置(initial_capital <= 0)应该抛出异常
        with pytest.raises(ValueError, match="initial_capital|must be positive"):
            invalid_config = BacktestConfig(
                initial_capital=Decimal(0),  # 无效
                commission_rate=Decimal("0.0003"),
                slippage_rate=Decimal("0.0001"),
            )
            await use_case.execute(
                signals=signals, config=invalid_config, date_range=date_range,
            )


class TestRunBacktestErrorHandling:
    """测试错误处理"""

    @pytest.mark.asyncio
    async def test_run_backtest_engine_error(self):
        """测试回测引擎错误处理"""
        # Arrange: Mock engine 抛出异常
        engine_mock = AsyncMock(spec=IBacktestEngine)
        engine_mock.run_backtest.side_effect = Exception("回测引擎错误")

        signals = SignalBatch(
            strategy_name="test_strategy", batch_date=datetime(2024, 1, 10), signals=[],
        )

        config = BacktestConfig(
            initial_capital=Decimal(100000),
            commission_rate=Decimal("0.0003"),
            slippage_rate=Decimal("0.0001"),
        )

        date_range = DateRange(
            start_date=datetime(2024, 1, 1), end_date=datetime(2024, 12, 31),
        )

        use_case = RunBacktestUseCase(engine=engine_mock)

        # Act & Assert: 应该传播异常
        with pytest.raises(Exception, match="回测引擎错误"):
            await use_case.execute(
                signals=signals, config=config, date_range=date_range,
            )

    @pytest.mark.asyncio
    async def test_run_backtest_empty_signals(self):
        """测试空信号列表"""
        # Arrange: 空信号批次
        engine_mock = AsyncMock(spec=IBacktestEngine)

        signals = SignalBatch(
            strategy_name="test_strategy",
            batch_date=datetime(2024, 1, 10),
            signals=[],  # 空信号
        )

        config = BacktestConfig(
            initial_capital=Decimal(100000),
            commission_rate=Decimal("0.0003"),
            slippage_rate=Decimal("0.0001"),
        )

        date_range = DateRange(
            start_date=datetime(2024, 1, 1), end_date=datetime(2024, 12, 31),
        )

        # Mock 返回无交易的结果
        mock_result = BacktestResult(
            strategy_name="test_strategy",
            start_date=date_range.start_date,
            end_date=date_range.end_date,
            initial_capital=config.initial_capital,
            final_capital=config.initial_capital,  # 无变化
            trades=[],
        )
        engine_mock.run_backtest.return_value = mock_result

        use_case = RunBacktestUseCase(engine=engine_mock)

        # Act
        result = await use_case.execute(
            signals=signals, config=config, date_range=date_range,
        )

        # Assert: 空信号也是有效的
        assert result.total_return() == Decimal(0)
        assert len(result.trades) == 0
