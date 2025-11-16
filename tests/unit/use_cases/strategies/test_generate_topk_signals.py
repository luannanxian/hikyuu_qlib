"""
GenerateTopKSignalsUseCase 单元测试

测试 UC-TOPK: Generate Top-K Trading Signals (从Qlib预测生成Top-K交易信号) 用例
"""

from datetime import datetime
from unittest.mock import Mock

import pytest

from domain.entities.prediction import Prediction, PredictionBatch
from domain.entities.trading_signal import (
    SignalBatch,
    SignalStrength,
    SignalType,
    TradingSignal,
)
from domain.ports.signal_provider import ISignalProvider
from domain.value_objects.stock_code import StockCode
from use_cases.strategies.generate_topk_signals import (
    GenerateTopKSignalsRequest,
    GenerateTopKSignalsUseCase,
)


class TestGenerateTopKSignalsSuccess:
    """测试成功生成Top-K信号"""

    @pytest.mark.asyncio
    async def test_generate_topk_signals_success(self):
        """测试成功生成Top-K信号"""
        # Arrange: 准备 Mock SignalProvider
        signal_provider_mock = Mock(spec=ISignalProvider)

        # 创建预测批次
        prediction_batch = PredictionBatch(
            model_id="qlib_model",
            predictions=[
                Prediction(
                    stock_code=StockCode("sh600000"),
                    timestamp=datetime(2024, 1, 10),
                    predicted_value=0.08,
                    model_id="qlib_model",
                    confidence=0.90,
                ),
                Prediction(
                    stock_code=StockCode("sh600001"),
                    timestamp=datetime(2024, 1, 10),
                    predicted_value=0.05,
                    model_id="qlib_model",
                    confidence=0.85,
                ),
                Prediction(
                    stock_code=StockCode("sh600002"),
                    timestamp=datetime(2024, 1, 10),
                    predicted_value=0.03,
                    model_id="qlib_model",
                    confidence=0.80,
                ),
            ],
            generated_at=datetime(2024, 1, 10),
        )

        # Mock signal_provider 返回Top-2信号批次
        mock_signal_batch = SignalBatch(
            strategy_name="QlibTopK",
            batch_date=datetime(2024, 1, 10),
            signals=[
                TradingSignal(
                    stock_code=StockCode("sh600000"),
                    signal_date=datetime(2024, 1, 10),
                    signal_type=SignalType.BUY,
                    signal_strength=SignalStrength.STRONG,
                ),
                TradingSignal(
                    stock_code=StockCode("sh600001"),
                    signal_date=datetime(2024, 1, 10),
                    signal_type=SignalType.BUY,
                    signal_strength=SignalStrength.MEDIUM,
                ),
            ],
        )
        signal_provider_mock.generate_signals_from_predictions.return_value = (
            mock_signal_batch
        )

        # 创建 Use Case
        use_case = GenerateTopKSignalsUseCase(signal_provider=signal_provider_mock)

        # 创建请求
        request = GenerateTopKSignalsRequest(
            prediction_batch=prediction_batch,
            top_k=2,
            buy_threshold=0.02,
            sell_threshold=-0.02,
            strategy_name="QlibTopK",
        )

        # Act: 执行用例
        response = await use_case.execute(request)

        # Assert: 验证响应
        assert response.success is True
        assert response.error is None
        assert response.signal_batch is not None
        assert response.signal_batch.size() == 2
        assert response.signal_batch.strategy_name == "QlibTopK"

        # 验证 signal_provider 被正确调用
        signal_provider_mock.generate_signals_from_predictions.assert_called_once_with(
            prediction_batch=prediction_batch,
            buy_threshold=0.02,
            sell_threshold=-0.02,
            top_k=2,
        )

    @pytest.mark.asyncio
    async def test_generate_topk_with_default_params(self):
        """测试使用默认参数生成Top-K信号"""
        # Arrange
        signal_provider_mock = Mock(spec=ISignalProvider)

        prediction_batch = PredictionBatch(
            model_id="qlib_model",
            predictions=[
                Prediction(
                    stock_code=StockCode(f"sh{600000 + i:06d}"),
                    timestamp=datetime(2024, 1, 10),
                    predicted_value=0.10 - i * 0.01,
                    model_id="qlib_model",
                )
                for i in range(15)
            ],
            generated_at=datetime(2024, 1, 10),
        )

        mock_signal_batch = SignalBatch(
            strategy_name="TestStrategy",
            batch_date=datetime(2024, 1, 10),
            signals=[
                TradingSignal(
                    stock_code=StockCode(f"sh{600000 + i:06d}"),
                    signal_date=datetime(2024, 1, 10),
                    signal_type=SignalType.BUY,
                )
                for i in range(10)
            ],
        )
        signal_provider_mock.generate_signals_from_predictions.return_value = (
            mock_signal_batch
        )

        use_case = GenerateTopKSignalsUseCase(signal_provider=signal_provider_mock)

        # 使用默认参数: top_k=10, buy_threshold=0.02, sell_threshold=-0.02
        request = GenerateTopKSignalsRequest(prediction_batch=prediction_batch)

        # Act
        response = await use_case.execute(request)

        # Assert: 验证使用默认参数
        assert response.success is True
        assert response.signal_batch is not None
        signal_provider_mock.generate_signals_from_predictions.assert_called_once()

        call_args = signal_provider_mock.generate_signals_from_predictions.call_args
        assert call_args.kwargs["top_k"] == 10
        assert call_args.kwargs["buy_threshold"] == 0.02
        assert call_args.kwargs["sell_threshold"] == -0.02

    @pytest.mark.asyncio
    async def test_generate_topk_adjusts_k_when_exceeds_predictions(self):
        """测试当top_k超过预测数量时自动调整"""
        # Arrange
        signal_provider_mock = Mock(spec=ISignalProvider)

        # 只有3个预测,但请求top_k=10
        prediction_batch = PredictionBatch(
            model_id="qlib_model",
            predictions=[
                Prediction(
                    stock_code=StockCode(f"sh{600000 + i:06d}"),
                    timestamp=datetime(2024, 1, 10),
                    predicted_value=0.05,
                    model_id="qlib_model",
                )
                for i in range(3)
            ],
            generated_at=datetime(2024, 1, 10),
        )

        mock_signal_batch = SignalBatch(
            strategy_name="QlibTopK",
            batch_date=datetime(2024, 1, 10),
            signals=[
                TradingSignal(
                    stock_code=StockCode(f"sh{600000 + i:06d}"),
                    signal_date=datetime(2024, 1, 10),
                    signal_type=SignalType.BUY,
                )
                for i in range(3)
            ],
        )
        signal_provider_mock.generate_signals_from_predictions.return_value = (
            mock_signal_batch
        )

        use_case = GenerateTopKSignalsUseCase(signal_provider=signal_provider_mock)

        request = GenerateTopKSignalsRequest(
            prediction_batch=prediction_batch,
            top_k=10,  # 超过预测数量
        )

        # Act
        response = await use_case.execute(request)

        # Assert: 验证自动调整为实际预测数量(3)
        assert response.success is True
        call_args = signal_provider_mock.generate_signals_from_predictions.call_args
        assert call_args.kwargs["top_k"] == 3  # 调整为3


class TestGenerateTopKSignalsRequestValidation:
    """测试请求参数验证"""

    def test_request_validates_top_k_positive(self):
        """测试top_k必须为正数"""
        prediction_batch = PredictionBatch(
            model_id="qlib_model", predictions=[], generated_at=datetime(2024, 1, 10),
        )

        # Act & Assert: top_k <= 0 应该抛出异常
        with pytest.raises(ValueError, match="top_k must be > 0"):
            GenerateTopKSignalsRequest(
                prediction_batch=prediction_batch,
                top_k=0,
            )

        with pytest.raises(ValueError, match="top_k must be > 0"):
            GenerateTopKSignalsRequest(
                prediction_batch=prediction_batch,
                top_k=-5,
            )

    def test_request_validates_thresholds(self):
        """测试买入阈值必须大于卖出阈值"""
        prediction_batch = PredictionBatch(
            model_id="qlib_model", predictions=[], generated_at=datetime(2024, 1, 10),
        )

        # Act & Assert: buy_threshold <= sell_threshold 应该抛出异常
        with pytest.raises(
            ValueError, match="buy_threshold must be > sell_threshold",
        ):
            GenerateTopKSignalsRequest(
                prediction_batch=prediction_batch,
                buy_threshold=0.02,
                sell_threshold=0.02,  # 相等
            )

        with pytest.raises(
            ValueError, match="buy_threshold must be > sell_threshold",
        ):
            GenerateTopKSignalsRequest(
                prediction_batch=prediction_batch,
                buy_threshold=0.02,
                sell_threshold=0.05,  # buy < sell
            )


class TestGenerateTopKSignalsErrorHandling:
    """测试错误处理"""

    @pytest.mark.asyncio
    async def test_empty_prediction_batch_returns_error(self):
        """测试空预测批次返回错误"""
        # Arrange
        signal_provider_mock = Mock(spec=ISignalProvider)

        # 空预测批次
        prediction_batch = PredictionBatch(
            model_id="qlib_model", predictions=[], generated_at=datetime(2024, 1, 10),
        )

        use_case = GenerateTopKSignalsUseCase(signal_provider=signal_provider_mock)

        request = GenerateTopKSignalsRequest(prediction_batch=prediction_batch)

        # Act
        response = await use_case.execute(request)

        # Assert: 应该返回失败响应
        assert response.success is False
        assert response.error is not None
        assert "empty" in response.error.lower()
        assert response.signal_batch is None

        # signal_provider 不应被调用
        signal_provider_mock.generate_signals_from_predictions.assert_not_called()

    @pytest.mark.asyncio
    async def test_signal_provider_error_returns_error_response(self):
        """测试信号提供者错误返回错误响应"""
        # Arrange: Mock signal_provider 抛出异常
        signal_provider_mock = Mock(spec=ISignalProvider)
        signal_provider_mock.generate_signals_from_predictions.side_effect = Exception(
            "Signal generation failed",
        )

        prediction_batch = PredictionBatch(
            model_id="qlib_model",
            predictions=[
                Prediction(
                    stock_code=StockCode("sh600000"),
                    timestamp=datetime(2024, 1, 10),
                    predicted_value=0.05,
                    model_id="qlib_model",
                ),
            ],
            generated_at=datetime(2024, 1, 10),
        )

        use_case = GenerateTopKSignalsUseCase(signal_provider=signal_provider_mock)

        request = GenerateTopKSignalsRequest(prediction_batch=prediction_batch)

        # Act
        response = await use_case.execute(request)

        # Assert: 应该返回失败响应
        assert response.success is False
        assert response.error is not None
        assert "Failed to generate signals" in response.error
        assert response.signal_batch is None

    @pytest.mark.asyncio
    async def test_value_error_returns_validation_error_response(self):
        """测试值错误返回验证错误响应"""
        # Arrange: Mock signal_provider 抛出ValueError
        signal_provider_mock = Mock(spec=ISignalProvider)
        signal_provider_mock.generate_signals_from_predictions.side_effect = ValueError(
            "Invalid threshold",
        )

        prediction_batch = PredictionBatch(
            model_id="qlib_model",
            predictions=[
                Prediction(
                    stock_code=StockCode("sh600000"),
                    timestamp=datetime(2024, 1, 10),
                    predicted_value=0.05,
                    model_id="qlib_model",
                ),
            ],
            generated_at=datetime(2024, 1, 10),
        )

        use_case = GenerateTopKSignalsUseCase(signal_provider=signal_provider_mock)

        request = GenerateTopKSignalsRequest(prediction_batch=prediction_batch)

        # Act
        response = await use_case.execute(request)

        # Assert: 应该返回验证错误响应
        assert response.success is False
        assert response.error is not None
        assert "Validation error" in response.error
        assert "Invalid threshold" in response.error
        assert response.signal_batch is None


class TestGenerateTopKSignalsStrategyName:
    """测试策略名称处理"""

    @pytest.mark.asyncio
    async def test_custom_strategy_name_is_applied(self):
        """测试自定义策略名称被应用"""
        # Arrange
        signal_provider_mock = Mock(spec=ISignalProvider)

        prediction_batch = PredictionBatch(
            model_id="qlib_model",
            predictions=[
                Prediction(
                    stock_code=StockCode("sh600000"),
                    timestamp=datetime(2024, 1, 10),
                    predicted_value=0.05,
                    model_id="qlib_model",
                ),
            ],
            generated_at=datetime(2024, 1, 10),
        )

        # Mock 返回不同的策略名称
        mock_signal_batch = SignalBatch(
            strategy_name="DefaultStrategy",
            batch_date=datetime(2024, 1, 10),
            signals=[
                TradingSignal(
                    stock_code=StockCode("sh600000"),
                    signal_date=datetime(2024, 1, 10),
                    signal_type=SignalType.BUY,
                ),
            ],
        )
        signal_provider_mock.generate_signals_from_predictions.return_value = (
            mock_signal_batch
        )

        use_case = GenerateTopKSignalsUseCase(signal_provider=signal_provider_mock)

        # 使用自定义策略名称
        request = GenerateTopKSignalsRequest(
            prediction_batch=prediction_batch, strategy_name="MyCustomStrategy",
        )

        # Act
        response = await use_case.execute(request)

        # Assert: 验证策略名称被覆盖
        assert response.success is True
        assert response.signal_batch is not None
        assert response.signal_batch.strategy_name == "MyCustomStrategy"
