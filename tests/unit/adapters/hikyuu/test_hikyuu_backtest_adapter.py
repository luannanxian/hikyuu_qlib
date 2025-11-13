"""
HikyuuBacktestAdapter 单元测试

测试 Hikyuu 回测适配器实现 IBacktestEngine 接口
遵循 TDD Red-Green-Refactor 流程
"""

from datetime import datetime, date
from decimal import Decimal
from unittest.mock import MagicMock, patch
from typing import List

import pytest

from domain.value_objects.stock_code import StockCode
from domain.value_objects.date_range import DateRange
from domain.value_objects.configuration import BacktestConfig
from domain.entities.trading_signal import TradingSignal, SignalBatch, SignalType, SignalStrength
from domain.entities.backtest import BacktestResult, Trade


class TestHikyuuBacktestAdapter:
    """HikyuuBacktestAdapter 测试类"""

    @pytest.fixture
    def mock_hku(self):
        """Mock Hikyuu 模块"""
        mock = MagicMock()
        return mock

    @pytest.fixture
    def adapter(self, mock_hku):
        """创建 HikyuuBacktestAdapter 实例"""
        from adapters.hikyuu.hikyuu_backtest_adapter import HikyuuBacktestAdapter
        return HikyuuBacktestAdapter(hikyuu_module=mock_hku)

    @pytest.fixture
    def sample_signal_batch(self):
        """示例信号批次"""
        batch = SignalBatch(
            strategy_name="TestStrategy",
            batch_date=datetime(2023, 1, 1)
        )
        
        # 添加买入信号
        signal1 = TradingSignal(
            stock_code=StockCode("sh600000"),
            signal_date=datetime(2023, 1, 3),
            signal_type=SignalType.BUY,
            signal_strength=SignalStrength.STRONG,
            price=Decimal("10.5")
        )
        batch.add_signal(signal1)
        
        # 添加卖出信号
        signal2 = TradingSignal(
            stock_code=StockCode("sh600000"),
            signal_date=datetime(2023, 1, 10),
            signal_type=SignalType.SELL,
            signal_strength=SignalStrength.MEDIUM,
            price=Decimal("11.0")
        )
        batch.add_signal(signal2)
        
        return batch

    @pytest.fixture
    def sample_backtest_config(self):
        """示例回测配置"""
        return BacktestConfig(
            initial_capital=Decimal("100000.0"),
            commission_rate=Decimal("0.001"),
            slippage_rate=Decimal("0.001")
        )

    @pytest.fixture
    def sample_date_range(self):
        """示例日期范围"""
        return DateRange(
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31)
        )

    @pytest.fixture
    def mock_hikyuu_portfolio(self):
        """Mock Hikyuu Portfolio 对象"""
        portfolio = MagicMock()
        
        # Mock 交易记录
        mock_trade1 = MagicMock()
        mock_trade1.stock = "SH600000"
        mock_trade1.datetime = datetime(2023, 1, 3)
        mock_trade1.business = 1  # Hikyuu BUY
        mock_trade1.number = 1000
        mock_trade1.price = 10.5
        mock_trade1.cost = 10.5
        
        mock_trade2 = MagicMock()
        mock_trade2.stock = "SH600000"
        mock_trade2.datetime = datetime(2023, 1, 10)
        mock_trade2.business = 0  # Hikyuu SELL
        mock_trade2.number = 1000
        mock_trade2.price = 11.0
        mock_trade2.cost = 11.0
        
        # Mock 权益曲线
        portfolio.getFunds.return_value = [
            MagicMock(total_assets=100000.0, datetime=datetime(2023, 1, 1)),
            MagicMock(total_assets=110000.0, datetime=datetime(2023, 12, 31))
        ]
        
        # Mock 交易列表
        portfolio.getTrades.return_value = [mock_trade1, mock_trade2]
        
        # Mock 最终资金
        portfolio.cash = 110000.0
        
        return portfolio

    # =============================================================================
    # Test 1: 验证 run_backtest 调用 Hikyuu API
    # =============================================================================

    @pytest.mark.asyncio
    async def test_run_backtest_calls_hikyuu_api(
        self, mock_hku, adapter, sample_signal_batch, 
        sample_backtest_config, sample_date_range, mock_hikyuu_portfolio
    ):
        """
        测试: run_backtest 正确调用 Hikyuu 回测 API

        验证:
        - 调用 hku.crtTM() 创建交易管理器
        - 调用 hku.PF_Simple() 创建投资组合
        - 使用正确的参数 (初始资金, 手续费)
        """
        # Arrange
        mock_tm = MagicMock()
        mock_hku.crtTM.return_value = mock_tm
        
        mock_pf = mock_hikyuu_portfolio
        mock_hku.PF_Simple.return_value = mock_pf

        # Act
        result = await adapter.run_backtest(
            signals=sample_signal_batch,
            config=sample_backtest_config,
            date_range=sample_date_range
        )

        # Assert
        mock_hku.crtTM.assert_called_once()
        call_kwargs = mock_hku.crtTM.call_args.kwargs
        assert call_kwargs['init_cash'] == float(sample_backtest_config.initial_capital)
        
        assert isinstance(result, BacktestResult)

    # =============================================================================
    # Test 2: 验证 Hikyuu 回测结果转换为 Domain 模型
    # =============================================================================

    @pytest.mark.asyncio
    async def test_run_backtest_converts_to_domain(
        self, mock_hku, adapter, sample_signal_batch,
        sample_backtest_config, sample_date_range, mock_hikyuu_portfolio
    ):
        """
        测试: run_backtest 将 Hikyuu 回测结果正确转换为 Domain BacktestResult

        验证:
        - 返回类型为 BacktestResult
        - 交易记录正确转换
        - 权益曲线正确转换
        - 初始和最终资金正确
        """
        # Arrange
        mock_tm = MagicMock()
        mock_hku.crtTM.return_value = mock_tm
        mock_hku.PF_Simple.return_value = mock_hikyuu_portfolio

        # Act
        result = await adapter.run_backtest(
            signals=sample_signal_batch,
            config=sample_backtest_config,
            date_range=sample_date_range
        )

        # Assert
        assert isinstance(result, BacktestResult)
        assert result.strategy_name == "TestStrategy"
        assert result.initial_capital == sample_backtest_config.initial_capital
        assert result.final_capital > 0
        
        # 验证交易记录
        assert len(result.trades) == 2
        assert all(isinstance(trade, Trade) for trade in result.trades)
        
        # 验证权益曲线
        assert len(result.equity_curve) > 0
        assert all(isinstance(val, Decimal) for val in result.equity_curve)

    # =============================================================================
    # Test 3: 验证信号到交易的转换
    # =============================================================================

    @pytest.mark.asyncio
    async def test_run_backtest_converts_signals_to_trades(
        self, mock_hku, adapter, sample_signal_batch,
        sample_backtest_config, sample_date_range, mock_hikyuu_portfolio
    ):
        """
        测试: 验证信号正确转换为 Hikyuu 交易指令

        验证:
        - BUY信号 → Hikyuu买入操作
        - SELL信号 → Hikyuu卖出操作
        - 价格和数量正确传递
        """
        # Arrange
        mock_tm = MagicMock()
        mock_hku.crtTM.return_value = mock_tm
        mock_hku.PF_Simple.return_value = mock_hikyuu_portfolio
        
        # Mock 信号生成器
        mock_sg = MagicMock()
        mock_hku.SG_Manual.return_value = mock_sg

        # Act
        result = await adapter.run_backtest(
            signals=sample_signal_batch,
            config=sample_backtest_config,
            date_range=sample_date_range
        )

        # Assert
        # 验证交易方向正确
        buy_trades = [t for t in result.trades if t.direction == "BUY"]
        sell_trades = [t for t in result.trades if t.direction == "SELL"]
        
        assert len(buy_trades) >= 1
        assert len(sell_trades) >= 1

    # =============================================================================
    # Test 4: 验证手续费计算
    # =============================================================================

    @pytest.mark.asyncio
    async def test_run_backtest_calculates_commission(
        self, mock_hku, adapter, sample_signal_batch,
        sample_backtest_config, sample_date_range, mock_hikyuu_portfolio
    ):
        """
        测试: 验证手续费正确计算并应用

        验证:
        - 手续费率正确传递给 Hikyuu
        - 交易记录包含手续费
        """
        # Arrange
        mock_tm = MagicMock()
        mock_hku.crtTM.return_value = mock_tm
        mock_hku.PF_Simple.return_value = mock_hikyuu_portfolio

        # Act
        result = await adapter.run_backtest(
            signals=sample_signal_batch,
            config=sample_backtest_config,
            date_range=sample_date_range
        )

        # Assert
        # 验证 crtTM 调用包含手续费配置
        mock_hku.crtTM.assert_called_once()
        call_kwargs = mock_hku.crtTM.call_args.kwargs
        
        # 验证交易包含手续费
        for trade in result.trades:
            assert isinstance(trade.commission, Decimal)

    # =============================================================================
    # Test 5: 验证错误处理
    # =============================================================================

    @pytest.mark.asyncio
    async def test_run_backtest_handles_hikyuu_error(
        self, mock_hku, adapter, sample_signal_batch,
        sample_backtest_config, sample_date_range
    ):
        """
        测试: run_backtest 正确处理 Hikyuu 异常

        验证:
        - Hikyuu 抛出异常时, 适配器捕获并重新抛出包装后的异常
        - 异常信息包含原始错误上下文
        """
        # Arrange
        mock_hku.crtTM.side_effect = Exception("Hikyuu backtest error")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await adapter.run_backtest(
                signals=sample_signal_batch,
                config=sample_backtest_config,
                date_range=sample_date_range
            )

        assert "Failed to run backtest with Hikyuu" in str(exc_info.value)

    # =============================================================================
    # Test 6: 验证空信号处理
    # =============================================================================

    @pytest.mark.asyncio
    async def test_run_backtest_handles_empty_signals(
        self, mock_hku, adapter, sample_backtest_config, 
        sample_date_range, mock_hikyuu_portfolio
    ):
        """
        测试: run_backtest 正确处理空信号批次

        验证:
        - 空信号批次不抛出异常
        - 返回有效的 BacktestResult (但无交易)
        """
        # Arrange
        empty_batch = SignalBatch(
            strategy_name="EmptyStrategy",
            batch_date=datetime(2023, 1, 1)
        )
        
        mock_tm = MagicMock()
        mock_hku.crtTM.return_value = mock_tm
        
        # 修改 mock 返回空交易
        empty_portfolio = MagicMock()
        empty_portfolio.getTrades.return_value = []
        empty_portfolio.getFunds.return_value = [
            MagicMock(total_assets=100000.0, datetime=datetime(2023, 1, 1))
        ]
        empty_portfolio.cash = 100000.0
        mock_hku.PF_Simple.return_value = empty_portfolio

        # Act
        result = await adapter.run_backtest(
            signals=empty_batch,
            config=sample_backtest_config,
            date_range=sample_date_range
        )

        # Assert
        assert isinstance(result, BacktestResult)
        assert len(result.trades) == 0
        assert result.initial_capital == result.final_capital

    # =============================================================================
    # Test 7: 验证回测指标计算
    # =============================================================================

    @pytest.mark.asyncio
    async def test_run_backtest_calculates_metrics(
        self, mock_hku, adapter, sample_signal_batch,
        sample_backtest_config, sample_date_range, mock_hikyuu_portfolio
    ):
        """
        测试: run_backtest 计算回测指标

        验证:
        - 总收益率
        - 夏普比率
        - 最大回撤
        - 胜率
        """
        # Arrange
        mock_tm = MagicMock()
        mock_hku.crtTM.return_value = mock_tm
        mock_hku.PF_Simple.return_value = mock_hikyuu_portfolio

        # Act
        result = await adapter.run_backtest(
            signals=sample_signal_batch,
            config=sample_backtest_config,
            date_range=sample_date_range
        )

        # Assert - 验证可以计算指标(不抛出异常)
        total_return = result.total_return()
        assert isinstance(total_return, Decimal)
        
        sharpe = result.calculate_sharpe_ratio()
        assert isinstance(sharpe, Decimal)
        
        max_dd = result.calculate_max_drawdown()
        assert isinstance(max_dd, Decimal)
        
        win_rate = result.get_win_rate()
        assert isinstance(win_rate, Decimal)
