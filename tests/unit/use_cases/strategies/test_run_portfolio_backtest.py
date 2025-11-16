"""
RunPortfolioBacktestUseCase 单元测试

测试 UC-PORTFOLIO-BT: Run Portfolio Backtest (运行Hikyuu投资组合回测) 用例
"""

import pickle
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, Mock

import pandas as pd
import pytest

from domain.entities.backtest import BacktestResult, Trade
from domain.entities.trading_signal import SignalBatch, SignalType, TradingSignal
from domain.ports.backtest_engine import IBacktestEngine
from domain.ports.signal_provider import ISignalProvider
from domain.value_objects.date_range import DateRange
from domain.value_objects.rebalance_period import RebalancePeriod
from domain.value_objects.stock_code import StockCode
from use_cases.strategies.run_portfolio_backtest import (
    RunPortfolioBacktestRequest,
    RunPortfolioBacktestUseCase,
)


class TestRunPortfolioBacktestSuccess:
    """测试成功运行投资组合回测"""

    @pytest.mark.asyncio
    async def test_run_portfolio_backtest_success(self, tmp_path):
        """测试成功运行投资组合回测"""
        # Arrange: 准备测试数据
        backtest_engine_mock = AsyncMock(spec=IBacktestEngine)
        signal_provider_mock = Mock(spec=ISignalProvider)

        # 创建临时预测文件
        pred_data = pd.DataFrame(
            {
                "stock_code": ["sh600000", "sh600001", "sh600002"],
                "timestamp": [datetime(2024, 1, 10)] * 3,
                "predicted_value": [0.08, 0.05, 0.03],
                "model_id": ["qlib_model"] * 3,
                "confidence": [0.9, 0.85, 0.8],
            },
        )

        pred_pkl_path = tmp_path / "predictions.pkl"
        with open(pred_pkl_path, "wb") as f:
            pickle.dump(pred_data, f)

        # Mock signal_provider
        mock_signal_batch = SignalBatch(
            strategy_name="QlibTopK",
            batch_date=datetime(2024, 1, 10),
            signals=[
                TradingSignal(
                    stock_code=StockCode("sh600000"),
                    signal_date=datetime(2024, 1, 10),
                    signal_type=SignalType.BUY,
                ),
                TradingSignal(
                    stock_code=StockCode("sh600001"),
                    signal_date=datetime(2024, 1, 10),
                    signal_type=SignalType.BUY,
                ),
            ],
        )
        signal_provider_mock.generate_signals_from_predictions.return_value = (
            mock_signal_batch
        )

        # Mock backtest_engine
        mock_backtest_result = BacktestResult(
            strategy_name="QlibTopK",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
            initial_capital=Decimal(1000000),
            final_capital=Decimal(1200000),
            trades=[
                Trade(
                    stock_code=StockCode("sh600000"),
                    direction="BUY",
                    quantity=1000,
                    price=Decimal("10.5"),
                    trade_date=datetime(2024, 1, 10),
                ),
            ],
            equity_curve=[
                Decimal(1000000),
                Decimal(1100000),
                Decimal(1200000),
            ],
        )
        backtest_engine_mock.run_backtest.return_value = mock_backtest_result

        # 创建 Use Case
        use_case = RunPortfolioBacktestUseCase(
            backtest_engine=backtest_engine_mock,
            signal_provider=signal_provider_mock,
        )

        # 创建请求
        stock_pool = [
            StockCode("sh600000"),
            StockCode("sh600001"),
            StockCode("sh600002"),
        ]
        date_range = DateRange(start_date=date(2024, 1, 1), end_date=date(2024, 12, 31))

        request = RunPortfolioBacktestRequest(
            pred_pkl_path=str(pred_pkl_path),
            stock_pool=stock_pool,
            date_range=date_range,
            top_k=2,
            rebalance_period=RebalancePeriod.WEEK,
            initial_cash=1000000.0,
        )

        # Act: 执行用例
        response = await use_case.execute(request)

        # Assert: 验证响应
        assert response.success is True
        assert response.error is None
        assert response.total_return == 0.2  # (1200000 - 1000000) / 1000000
        assert response.sharpe_ratio > 0
        assert response.max_drawdown >= 0
        assert response.trade_count == 1

        # 验证 signal_provider 被正确调用
        signal_provider_mock.generate_signals_from_predictions.assert_called_once()

        # 验证 backtest_engine 被正确调用
        backtest_engine_mock.run_backtest.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_with_default_parameters(self, tmp_path):
        """测试使用默认参数运行回测"""
        # Arrange
        backtest_engine_mock = AsyncMock(spec=IBacktestEngine)
        signal_provider_mock = Mock(spec=ISignalProvider)

        # 创建临时预测文件
        pred_data = pd.DataFrame(
            {
                "stock_code": ["sh600000"] * 5,
                "timestamp": [datetime(2024, 1, 10)] * 5,
                "predicted_value": [0.05] * 5,
                "model_id": ["qlib_model"] * 5,
            },
        )

        pred_pkl_path = tmp_path / "predictions.pkl"
        with open(pred_pkl_path, "wb") as f:
            pickle.dump(pred_data, f)

        mock_signal_batch = SignalBatch(
            strategy_name="QlibTopK", batch_date=datetime(2024, 1, 10), signals=[],
        )
        signal_provider_mock.generate_signals_from_predictions.return_value = (
            mock_signal_batch
        )

        mock_backtest_result = BacktestResult(
            strategy_name="QlibTopK",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
            initial_capital=Decimal(1000000),
            final_capital=Decimal(1000000),
        )
        backtest_engine_mock.run_backtest.return_value = mock_backtest_result

        use_case = RunPortfolioBacktestUseCase(
            backtest_engine=backtest_engine_mock,
            signal_provider=signal_provider_mock,
        )

        stock_pool = [StockCode("sh600000")]
        date_range = DateRange(start_date=date(2024, 1, 1), end_date=date(2024, 12, 31))

        # 使用默认参数: top_k=10, rebalance_period=WEEK, initial_cash=1000000.0
        request = RunPortfolioBacktestRequest(
            pred_pkl_path=str(pred_pkl_path),
            stock_pool=stock_pool,
            date_range=date_range,
        )

        # Act
        response = await use_case.execute(request)

        # Assert: 验证使用默认参数
        assert response.success is True
        assert request.top_k == 10
        assert request.rebalance_period == RebalancePeriod.WEEK
        assert request.initial_cash == 1000000.0

    @pytest.mark.asyncio
    async def test_filters_predictions_by_stock_pool(self, tmp_path):
        """测试按股票池过滤预测"""
        # Arrange
        backtest_engine_mock = AsyncMock(spec=IBacktestEngine)
        signal_provider_mock = Mock(spec=ISignalProvider)

        # 创建包含多个股票的预测数据,但股票池只包含部分股票
        pred_data = pd.DataFrame(
            {
                "stock_code": ["sh600000", "sh600001", "sh600002", "sh600003"],
                "timestamp": [datetime(2024, 1, 10)] * 4,
                "predicted_value": [0.08, 0.05, 0.03, 0.02],
                "model_id": ["qlib_model"] * 4,
            },
        )

        pred_pkl_path = tmp_path / "predictions.pkl"
        with open(pred_pkl_path, "wb") as f:
            pickle.dump(pred_data, f)

        # 记录传递给signal_provider的预测批次
        captured_batch = None

        def capture_batch(prediction_batch, **kwargs):
            nonlocal captured_batch
            captured_batch = prediction_batch
            return SignalBatch(
                strategy_name="QlibTopK", batch_date=datetime(2024, 1, 10), signals=[],
            )

        signal_provider_mock.generate_signals_from_predictions.side_effect = (
            capture_batch
        )

        mock_backtest_result = BacktestResult(
            strategy_name="QlibTopK",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
            initial_capital=Decimal(1000000),
            final_capital=Decimal(1000000),
        )
        backtest_engine_mock.run_backtest.return_value = mock_backtest_result

        use_case = RunPortfolioBacktestUseCase(
            backtest_engine=backtest_engine_mock,
            signal_provider=signal_provider_mock,
        )

        # 股票池只包含 sh600000 和 sh600001
        stock_pool = [StockCode("sh600000"), StockCode("sh600001")]
        date_range = DateRange(start_date=date(2024, 1, 1), end_date=date(2024, 12, 31))

        request = RunPortfolioBacktestRequest(
            pred_pkl_path=str(pred_pkl_path),
            stock_pool=stock_pool,
            date_range=date_range,
        )

        # Act
        response = await use_case.execute(request)

        # Assert: 验证只传递了股票池内的预测
        assert response.success is True
        assert captured_batch is not None
        assert captured_batch.size() == 2  # 只有 sh600000 和 sh600001

        stock_codes_in_batch = [
            pred.stock_code for pred in captured_batch.predictions
        ]
        assert StockCode("sh600000") in stock_codes_in_batch
        assert StockCode("sh600001") in stock_codes_in_batch
        assert StockCode("sh600002") not in stock_codes_in_batch


class TestRunPortfolioBacktestRequestValidation:
    """测试请求参数验证"""

    def test_request_validates_prediction_file_exists(self):
        """测试预测文件必须存在"""
        stock_pool = [StockCode("sh600000")]
        date_range = DateRange(start_date=date(2024, 1, 1), end_date=date(2024, 12, 31))

        # Act & Assert: 文件不存在应该抛出异常
        with pytest.raises(ValueError, match="not found"):
            RunPortfolioBacktestRequest(
                pred_pkl_path="/nonexistent/path/predictions.pkl",
                stock_pool=stock_pool,
                date_range=date_range,
            )

    def test_request_validates_top_k_positive(self, tmp_path):
        """测试top_k必须为正数"""
        # 创建临时文件
        pred_pkl_path = tmp_path / "predictions.pkl"
        pred_pkl_path.touch()

        stock_pool = [StockCode("sh600000")]
        date_range = DateRange(start_date=date(2024, 1, 1), end_date=date(2024, 12, 31))

        # Act & Assert: top_k <= 0 应该抛出异常
        with pytest.raises(ValueError, match="top_k must be > 0"):
            RunPortfolioBacktestRequest(
                pred_pkl_path=str(pred_pkl_path),
                stock_pool=stock_pool,
                date_range=date_range,
                top_k=0,
            )

    def test_request_validates_stock_pool_not_empty(self, tmp_path):
        """测试股票池不能为空"""
        # 创建临时文件
        pred_pkl_path = tmp_path / "predictions.pkl"
        pred_pkl_path.touch()

        date_range = DateRange(start_date=date(2024, 1, 1), end_date=date(2024, 12, 31))

        # Act & Assert: 空股票池应该抛出异常
        with pytest.raises(ValueError, match="stock_pool cannot be empty"):
            RunPortfolioBacktestRequest(
                pred_pkl_path=str(pred_pkl_path),
                stock_pool=[],
                date_range=date_range,
            )

    def test_request_validates_initial_cash_positive(self, tmp_path):
        """测试初始资金必须为正数"""
        # 创建临时文件
        pred_pkl_path = tmp_path / "predictions.pkl"
        pred_pkl_path.touch()

        stock_pool = [StockCode("sh600000")]
        date_range = DateRange(start_date=date(2024, 1, 1), end_date=date(2024, 12, 31))

        # Act & Assert: initial_cash <= 0 应该抛出异常
        with pytest.raises(ValueError, match="initial_cash must be > 0"):
            RunPortfolioBacktestRequest(
                pred_pkl_path=str(pred_pkl_path),
                stock_pool=stock_pool,
                date_range=date_range,
                initial_cash=0.0,
            )

        with pytest.raises(ValueError, match="initial_cash must be > 0"):
            RunPortfolioBacktestRequest(
                pred_pkl_path=str(pred_pkl_path),
                stock_pool=stock_pool,
                date_range=date_range,
                initial_cash=-100000.0,
            )


class TestRunPortfolioBacktestErrorHandling:
    """测试错误处理"""

    @pytest.mark.asyncio
    async def test_no_predictions_in_stock_pool_returns_error(self, tmp_path):
        """测试股票池内无预测返回错误"""
        # Arrange
        backtest_engine_mock = AsyncMock(spec=IBacktestEngine)
        signal_provider_mock = Mock(spec=ISignalProvider)

        # 创建预测文件,但股票不在股票池内
        pred_data = pd.DataFrame(
            {
                "stock_code": ["sh600003", "sh600004"],  # 不在股票池内
                "timestamp": [datetime(2024, 1, 10)] * 2,
                "predicted_value": [0.05, 0.03],
                "model_id": ["qlib_model"] * 2,
            },
        )

        pred_pkl_path = tmp_path / "predictions.pkl"
        with open(pred_pkl_path, "wb") as f:
            pickle.dump(pred_data, f)

        use_case = RunPortfolioBacktestUseCase(
            backtest_engine=backtest_engine_mock,
            signal_provider=signal_provider_mock,
        )

        # 股票池只包含其他股票
        stock_pool = [StockCode("sh600000"), StockCode("sh600001")]
        date_range = DateRange(start_date=date(2024, 1, 1), end_date=date(2024, 12, 31))

        request = RunPortfolioBacktestRequest(
            pred_pkl_path=str(pred_pkl_path),
            stock_pool=stock_pool,
            date_range=date_range,
        )

        # Act
        response = await use_case.execute(request)

        # Assert: 应该返回失败响应
        assert response.success is False
        assert response.error is not None
        assert "No predictions found" in response.error

    @pytest.mark.asyncio
    async def test_prediction_file_load_error_returns_error_response(self, tmp_path):
        """测试预测文件加载错误返回错误响应"""
        # Arrange
        backtest_engine_mock = AsyncMock(spec=IBacktestEngine)
        signal_provider_mock = Mock(spec=ISignalProvider)

        # 创建无效的pickle文件
        pred_pkl_path = tmp_path / "invalid.pkl"
        with open(pred_pkl_path, "w") as f:
            f.write("invalid pickle data")

        use_case = RunPortfolioBacktestUseCase(
            backtest_engine=backtest_engine_mock,
            signal_provider=signal_provider_mock,
        )

        stock_pool = [StockCode("sh600000")]
        date_range = DateRange(start_date=date(2024, 1, 1), end_date=date(2024, 12, 31))

        request = RunPortfolioBacktestRequest(
            pred_pkl_path=str(pred_pkl_path),
            stock_pool=stock_pool,
            date_range=date_range,
        )

        # Act
        response = await use_case.execute(request)

        # Assert: 应该返回失败响应
        assert response.success is False
        assert response.error is not None
        assert "Failed to load predictions" in response.error or "Prediction file not found" in response.error

    @pytest.mark.asyncio
    async def test_signal_provider_error_returns_error_response(self, tmp_path):
        """测试信号提供者错误返回错误响应"""
        # Arrange
        backtest_engine_mock = AsyncMock(spec=IBacktestEngine)
        signal_provider_mock = Mock(spec=ISignalProvider)

        # 创建有效的预测文件
        pred_data = pd.DataFrame(
            {
                "stock_code": ["sh600000"],
                "timestamp": [datetime(2024, 1, 10)],
                "predicted_value": [0.05],
                "model_id": ["qlib_model"],
            },
        )

        pred_pkl_path = tmp_path / "predictions.pkl"
        with open(pred_pkl_path, "wb") as f:
            pickle.dump(pred_data, f)

        # Mock signal_provider 抛出异常
        signal_provider_mock.generate_signals_from_predictions.side_effect = Exception(
            "Signal generation failed",
        )

        use_case = RunPortfolioBacktestUseCase(
            backtest_engine=backtest_engine_mock,
            signal_provider=signal_provider_mock,
        )

        stock_pool = [StockCode("sh600000")]
        date_range = DateRange(start_date=date(2024, 1, 1), end_date=date(2024, 12, 31))

        request = RunPortfolioBacktestRequest(
            pred_pkl_path=str(pred_pkl_path),
            stock_pool=stock_pool,
            date_range=date_range,
        )

        # Act
        response = await use_case.execute(request)

        # Assert: 应该返回失败响应
        assert response.success is False
        assert response.error is not None
        assert "Backtest execution failed" in response.error

    @pytest.mark.asyncio
    async def test_backtest_engine_error_returns_error_response(self, tmp_path):
        """测试回测引擎错误返回错误响应"""
        # Arrange
        backtest_engine_mock = AsyncMock(spec=IBacktestEngine)
        signal_provider_mock = Mock(spec=ISignalProvider)

        # 创建有效的预测文件
        pred_data = pd.DataFrame(
            {
                "stock_code": ["sh600000"],
                "timestamp": [datetime(2024, 1, 10)],
                "predicted_value": [0.05],
                "model_id": ["qlib_model"],
            },
        )

        pred_pkl_path = tmp_path / "predictions.pkl"
        with open(pred_pkl_path, "wb") as f:
            pickle.dump(pred_data, f)

        mock_signal_batch = SignalBatch(
            strategy_name="QlibTopK", batch_date=datetime(2024, 1, 10), signals=[],
        )
        signal_provider_mock.generate_signals_from_predictions.return_value = (
            mock_signal_batch
        )

        # Mock backtest_engine 抛出异常
        backtest_engine_mock.run_backtest.side_effect = Exception(
            "Backtest engine error",
        )

        use_case = RunPortfolioBacktestUseCase(
            backtest_engine=backtest_engine_mock,
            signal_provider=signal_provider_mock,
        )

        stock_pool = [StockCode("sh600000")]
        date_range = DateRange(start_date=date(2024, 1, 1), end_date=date(2024, 12, 31))

        request = RunPortfolioBacktestRequest(
            pred_pkl_path=str(pred_pkl_path),
            stock_pool=stock_pool,
            date_range=date_range,
        )

        # Act
        response = await use_case.execute(request)

        # Assert: 应该返回失败响应
        assert response.success is False
        assert response.error is not None
        assert "Backtest execution failed" in response.error


class TestRunPortfolioBacktestRebalancePeriods:
    """测试不同调仓周期"""

    @pytest.mark.asyncio
    async def test_daily_rebalance_period(self, tmp_path):
        """测试每日调仓"""
        # Arrange
        backtest_engine_mock = AsyncMock(spec=IBacktestEngine)
        signal_provider_mock = Mock(spec=ISignalProvider)

        pred_data = pd.DataFrame(
            {
                "stock_code": ["sh600000"],
                "timestamp": [datetime(2024, 1, 10)],
                "predicted_value": [0.05],
                "model_id": ["qlib_model"],
            },
        )

        pred_pkl_path = tmp_path / "predictions.pkl"
        with open(pred_pkl_path, "wb") as f:
            pickle.dump(pred_data, f)

        mock_signal_batch = SignalBatch(
            strategy_name="QlibTopK", batch_date=datetime(2024, 1, 10), signals=[],
        )
        signal_provider_mock.generate_signals_from_predictions.return_value = (
            mock_signal_batch
        )

        mock_backtest_result = BacktestResult(
            strategy_name="QlibTopK",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
            initial_capital=Decimal(1000000),
            final_capital=Decimal(1100000),
        )
        backtest_engine_mock.run_backtest.return_value = mock_backtest_result

        use_case = RunPortfolioBacktestUseCase(
            backtest_engine=backtest_engine_mock,
            signal_provider=signal_provider_mock,
        )

        stock_pool = [StockCode("sh600000")]
        date_range = DateRange(start_date=date(2024, 1, 1), end_date=date(2024, 12, 31))

        request = RunPortfolioBacktestRequest(
            pred_pkl_path=str(pred_pkl_path),
            stock_pool=stock_pool,
            date_range=date_range,
            rebalance_period=RebalancePeriod.DAY,
        )

        # Act
        response = await use_case.execute(request)

        # Assert: 验证成功执行
        assert response.success is True
        assert request.rebalance_period == RebalancePeriod.DAY

    @pytest.mark.asyncio
    async def test_monthly_rebalance_period(self, tmp_path):
        """测试每月调仓"""
        # Arrange
        backtest_engine_mock = AsyncMock(spec=IBacktestEngine)
        signal_provider_mock = Mock(spec=ISignalProvider)

        pred_data = pd.DataFrame(
            {
                "stock_code": ["sh600000"],
                "timestamp": [datetime(2024, 1, 10)],
                "predicted_value": [0.05],
                "model_id": ["qlib_model"],
            },
        )

        pred_pkl_path = tmp_path / "predictions.pkl"
        with open(pred_pkl_path, "wb") as f:
            pickle.dump(pred_data, f)

        mock_signal_batch = SignalBatch(
            strategy_name="QlibTopK", batch_date=datetime(2024, 1, 10), signals=[],
        )
        signal_provider_mock.generate_signals_from_predictions.return_value = (
            mock_signal_batch
        )

        mock_backtest_result = BacktestResult(
            strategy_name="QlibTopK",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
            initial_capital=Decimal(1000000),
            final_capital=Decimal(1050000),
        )
        backtest_engine_mock.run_backtest.return_value = mock_backtest_result

        use_case = RunPortfolioBacktestUseCase(
            backtest_engine=backtest_engine_mock,
            signal_provider=signal_provider_mock,
        )

        stock_pool = [StockCode("sh600000")]
        date_range = DateRange(start_date=date(2024, 1, 1), end_date=date(2024, 12, 31))

        request = RunPortfolioBacktestRequest(
            pred_pkl_path=str(pred_pkl_path),
            stock_pool=stock_pool,
            date_range=date_range,
            rebalance_period=RebalancePeriod.MONTH,
        )

        # Act
        response = await use_case.execute(request)

        # Assert: 验证成功执行
        assert response.success is True
        assert request.rebalance_period == RebalancePeriod.MONTH
