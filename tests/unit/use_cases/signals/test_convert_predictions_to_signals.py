"""
ConvertPredictionsToSignalsUseCase 单元测试

测试 UC-004: Convert Predictions to Signals (预测转信号) 用例
"""

from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from domain.entities.prediction import Prediction, PredictionBatch
from domain.entities.trading_signal import (
    SignalBatch,
    SignalStrength,
    SignalType,
    TradingSignal,
)
from domain.ports.signal_converter import ISignalConverter
from domain.value_objects.stock_code import StockCode
from use_cases.signals.convert_predictions_to_signals import (
    ConvertPredictionsToSignalsUseCase,
)


class TestConvertPredictionsSuccess:
    """测试成功转换预测为信号"""

    @pytest.mark.asyncio
    async def test_convert_predictions_success(self):
        """测试成功转换预测为信号"""
        # Arrange: 准备 Mock Converter
        converter_mock = AsyncMock(spec=ISignalConverter)

        # 创建预测批次
        predictions = PredictionBatch(
            model_id="model-123",
            batch_date=datetime(2024, 1, 10),
            predictions=[
                Prediction(
                    stock_code=StockCode("sh600000"),
                    prediction_date=datetime(2024, 1, 10),
                    predicted_value=Decimal("0.05"),
                    confidence=Decimal("0.85"),
                ),
                Prediction(
                    stock_code=StockCode("sz000001"),
                    prediction_date=datetime(2024, 1, 10),
                    predicted_value=Decimal("-0.02"),
                    confidence=Decimal("0.78"),
                ),
            ],
        )

        # Mock converter 返回信号批次
        mock_signal_batch = SignalBatch(
            strategy_name="top_k",
            batch_date=datetime(2024, 1, 10),
            signals=[
                TradingSignal(
                    stock_code=StockCode("sh600000"),
                    signal_date=datetime(2024, 1, 10),
                    signal_type=SignalType.BUY,
                    signal_strength=SignalStrength.STRONG,
                ),
            ],
        )
        converter_mock.convert_to_signals.return_value = mock_signal_batch

        # 创建 Use Case
        use_case = ConvertPredictionsToSignalsUseCase(converter=converter_mock)

        # 策略参数
        strategy_params = {"strategy_type": "top_k", "k": 5}

        # Act: 执行用例
        result = await use_case.execute(
            predictions=predictions, strategy_params=strategy_params,
        )

        # Assert: 验证结果
        assert isinstance(result, SignalBatch)
        assert result.strategy_name == "top_k"
        assert result.size() == 1

        # 验证 converter 被正确调用
        converter_mock.convert_to_signals.assert_called_once_with(
            predictions=predictions, strategy_params=strategy_params,
        )

    @pytest.mark.asyncio
    async def test_convert_with_top_k_strategy(self):
        """测试 Top-K 策略"""
        # Arrange
        converter_mock = AsyncMock(spec=ISignalConverter)

        predictions = PredictionBatch(
            model_id="model-123",
            batch_date=datetime(2024, 1, 10),
            predictions=[
                Prediction(
                    stock_code=StockCode("sh600000"),
                    prediction_date=datetime(2024, 1, 10),
                    predicted_value=Decimal("0.08"),
                    confidence=Decimal("0.90"),
                ),
                Prediction(
                    stock_code=StockCode("sh600001"),
                    prediction_date=datetime(2024, 1, 10),
                    predicted_value=Decimal("0.05"),
                    confidence=Decimal("0.85"),
                ),
                Prediction(
                    stock_code=StockCode("sh600002"),
                    prediction_date=datetime(2024, 1, 10),
                    predicted_value=Decimal("0.02"),
                    confidence=Decimal("0.70"),
                ),
            ],
        )

        # Mock converter 返回 Top-2 信号
        mock_signal_batch = SignalBatch(
            strategy_name="top_k",
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
        converter_mock.convert_to_signals.return_value = mock_signal_batch

        use_case = ConvertPredictionsToSignalsUseCase(converter=converter_mock)

        # Top-2 策略参数
        strategy_params = {"strategy_type": "top_k", "k": 2}

        # Act
        result = await use_case.execute(
            predictions=predictions, strategy_params=strategy_params,
        )

        # Assert: 验证只返回 Top-2
        assert result.size() == 2

    @pytest.mark.asyncio
    async def test_convert_with_threshold_strategy(self):
        """测试阈值策略"""
        # Arrange
        converter_mock = AsyncMock(spec=ISignalConverter)

        predictions = PredictionBatch(
            model_id="model-123",
            batch_date=datetime(2024, 1, 10),
            predictions=[
                Prediction(
                    stock_code=StockCode("sh600000"),
                    prediction_date=datetime(2024, 1, 10),
                    predicted_value=Decimal("0.08"),
                    confidence=Decimal("0.90"),
                ),
                Prediction(
                    stock_code=StockCode("sh600001"),
                    prediction_date=datetime(2024, 1, 10),
                    predicted_value=Decimal("0.02"),
                    confidence=Decimal("0.70"),
                ),
            ],
        )

        # Mock converter 返回高于阈值的信号
        mock_signal_batch = SignalBatch(
            strategy_name="threshold",
            batch_date=datetime(2024, 1, 10),
            signals=[
                TradingSignal(
                    stock_code=StockCode("sh600000"),
                    signal_date=datetime(2024, 1, 10),
                    signal_type=SignalType.BUY,
                    signal_strength=SignalStrength.STRONG,
                ),
            ],
        )
        converter_mock.convert_to_signals.return_value = mock_signal_batch

        use_case = ConvertPredictionsToSignalsUseCase(converter=converter_mock)

        # 阈值策略参数: 预测值 > 0.05
        strategy_params = {"strategy_type": "threshold", "threshold": 0.05}

        # Act
        result = await use_case.execute(
            predictions=predictions, strategy_params=strategy_params,
        )

        # Assert: 验证只返回高于阈值的信号
        assert result.size() == 1


class TestConvertPredictionsValidation:
    """测试策略参数验证"""

    @pytest.mark.asyncio
    async def test_convert_validates_strategy_params(self):
        """测试策略参数验证"""
        # Arrange
        converter_mock = AsyncMock(spec=ISignalConverter)

        predictions = PredictionBatch(
            model_id="model-123",
            batch_date=datetime(2024, 1, 10),
            predictions=[],
        )

        use_case = ConvertPredictionsToSignalsUseCase(converter=converter_mock)

        # Act & Assert: 缺少必要参数应该抛出异常
        with pytest.raises(ValueError, match="strategy_type.*required"):
            await use_case.execute(predictions=predictions, strategy_params={})

    @pytest.mark.asyncio
    async def test_convert_validates_top_k_params(self):
        """测试 Top-K 策略参数验证"""
        # Arrange
        converter_mock = AsyncMock(spec=ISignalConverter)

        predictions = PredictionBatch(
            model_id="model-123", batch_date=datetime(2024, 1, 10), predictions=[],
        )

        use_case = ConvertPredictionsToSignalsUseCase(converter=converter_mock)

        # Act & Assert: Top-K 策略缺少 k 参数
        with pytest.raises(ValueError, match="'k'.*required|missing"):
            await use_case.execute(
                predictions=predictions,
                strategy_params={"strategy_type": "top_k"},  # 缺少 k
            )


class TestConvertPredictionsErrorHandling:
    """测试错误处理"""

    @pytest.mark.asyncio
    async def test_convert_converter_error(self):
        """测试转换器错误处理"""
        # Arrange: Mock converter 抛出异常
        converter_mock = AsyncMock(spec=ISignalConverter)
        converter_mock.convert_to_signals.side_effect = Exception("转换失败")

        predictions = PredictionBatch(
            model_id="model-123", batch_date=datetime(2024, 1, 10), predictions=[],
        )

        use_case = ConvertPredictionsToSignalsUseCase(converter=converter_mock)

        # Act & Assert: 应该传播异常
        with pytest.raises(Exception, match="转换失败"):
            await use_case.execute(
                predictions=predictions,
                strategy_params={"strategy_type": "top_k", "k": 5},
            )

    @pytest.mark.asyncio
    async def test_convert_empty_predictions(self):
        """测试空预测列表"""
        # Arrange: 空预测批次
        converter_mock = AsyncMock(spec=ISignalConverter)

        predictions = PredictionBatch(
            model_id="model-123",
            batch_date=datetime(2024, 1, 10),
            predictions=[],  # 空预测
        )

        # Mock converter 返回空信号批次
        mock_signal_batch = SignalBatch(
            strategy_name="top_k", batch_date=datetime(2024, 1, 10), signals=[],
        )
        converter_mock.convert_to_signals.return_value = mock_signal_batch

        use_case = ConvertPredictionsToSignalsUseCase(converter=converter_mock)

        # Act
        result = await use_case.execute(
            predictions=predictions, strategy_params={"strategy_type": "top_k", "k": 5},
        )

        # Assert: 空结果也是有效的
        assert result.size() == 0
        assert len(result.signals) == 0
