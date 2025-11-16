"""
SignalConverterAdapter 单元测试

测试 SignalConverterAdapter 实现 ISignalConverter 接口,
将模型预测转换为交易信号
"""

from datetime import datetime
from decimal import Decimal

import pytest

from domain.entities.prediction import Prediction, PredictionBatch
from domain.entities.trading_signal import SignalStrength, SignalType
from domain.value_objects.stock_code import StockCode


class TestSignalConverterAdapter:
    """测试 SignalConverterAdapter"""

    @pytest.fixture
    def prediction_batch(self) -> PredictionBatch:
        """预测批次 fixture"""
        batch = PredictionBatch(model_id="test_model", generated_at=datetime(2024, 1, 1))

        # 添加强烈看涨预测（predicted_value > 0.05, confidence > 0.8）
        batch.add_prediction(
            Prediction(
                model_id="test_model",
                stock_code=StockCode("sz000001"),
                timestamp=datetime(2024, 1, 2),
                predicted_value=Decimal("0.08"),  # 8%涨幅
                confidence=Decimal("0.9"),
            ),
        )

        # 添加看涨预测（predicted_value > 0.02, confidence > 0.6）
        batch.add_prediction(
            Prediction(
                model_id="test_model",
                stock_code=StockCode("sz000002"),
                timestamp=datetime(2024, 1, 2),
                predicted_value=Decimal("0.03"),  # 3%涨幅
                confidence=Decimal("0.7"),
            ),
        )

        # 添加看跌预测（predicted_value < -0.05, confidence > 0.8）
        batch.add_prediction(
            Prediction(
                model_id="test_model",
                stock_code=StockCode("sz000003"),
                timestamp=datetime(2024, 1, 2),
                predicted_value=Decimal("-0.07"),  # -7%跌幅
                confidence=Decimal("0.85"),
            ),
        )

        # 添加持有预测（predicted_value 接近 0）
        batch.add_prediction(
            Prediction(
                model_id="test_model",
                stock_code=StockCode("sz000004"),
                timestamp=datetime(2024, 1, 2),
                predicted_value=Decimal("0.01"),  # 1%涨幅（不够买入阈值）
                confidence=Decimal("0.5"),
            ),
        )

        return batch

    @pytest.fixture
    def strategy_params(self) -> dict:
        """策略参数 fixture"""
        return {
            "buy_threshold": 0.02,  # 买入阈值: 预测涨幅 > 2%
            "sell_threshold": -0.02,  # 卖出阈值: 预测跌幅 < -2%
            "strong_threshold": 0.05,  # 强信号阈值: 预测涨跌幅绝对值 > 5%
            "min_confidence": 0.6,  # 最小置信度
            "strategy_name": "test_strategy",
        }

    @pytest.mark.asyncio
    async def test_convert_predictions_to_signals(
        self, prediction_batch, strategy_params,
    ):
        """
        测试成功转换预测为信号

        验证:
        1. PredictionBatch → SignalBatch
        2. 根据阈值生成 BUY/SELL/HOLD 信号
        3. 信号强度基于预测值大小
        """
        from adapters.converters.signal_converter_adapter import SignalConverterAdapter

        adapter = SignalConverterAdapter()
        signal_batch = await adapter.convert_to_signals(
            predictions=prediction_batch, strategy_params=strategy_params,
        )

        # 验证
        assert signal_batch is not None
        assert signal_batch.strategy_name == "test_strategy"
        assert signal_batch.size() == 4  # 4个预测 -> 4个信号

        # 验证买入信号
        buy_signals = signal_batch.filter_by_type(SignalType.BUY)
        assert len(buy_signals) == 2  # sz000001 和 sz000002

        # 验证强烈买入信号
        strong_buy = [
            s for s in buy_signals if s.signal_strength == SignalStrength.STRONG
        ]
        assert len(strong_buy) == 1  # sz000001

        # 验证卖出信号
        sell_signals = signal_batch.filter_by_type(SignalType.SELL)
        assert len(sell_signals) == 1  # sz000003

        # 验证持有信号
        hold_signals = signal_batch.filter_by_type(SignalType.HOLD)
        assert len(hold_signals) == 1  # sz000004

    @pytest.mark.asyncio
    async def test_threshold_logic(self, prediction_batch, strategy_params):
        """
        测试阈值逻辑

        验证:
        1. predicted_value > buy_threshold -> BUY
        2. predicted_value < sell_threshold -> SELL
        3. 其他 -> HOLD
        """
        from adapters.converters.signal_converter_adapter import SignalConverterAdapter

        adapter = SignalConverterAdapter()
        signal_batch = await adapter.convert_to_signals(
            predictions=prediction_batch, strategy_params=strategy_params,
        )

        # 检查具体股票的信号
        signal_001 = signal_batch.get_signal(
            StockCode("sz000001"), datetime(2024, 1, 2),
        )
        assert signal_001 is not None
        assert signal_001.signal_type == SignalType.BUY

        signal_003 = signal_batch.get_signal(
            StockCode("sz000003"), datetime(2024, 1, 2),
        )
        assert signal_003 is not None
        assert signal_003.signal_type == SignalType.SELL

        signal_004 = signal_batch.get_signal(
            StockCode("sz000004"), datetime(2024, 1, 2),
        )
        assert signal_004 is not None
        assert signal_004.signal_type == SignalType.HOLD

    @pytest.mark.asyncio
    async def test_signal_strength_calculation(self, prediction_batch, strategy_params):
        """
        测试信号强度计算

        验证:
        1. |predicted_value| > strong_threshold -> STRONG
        2. confidence > 0.8 -> 增强信号强度
        3. 其他 -> MEDIUM/WEAK
        """
        from adapters.converters.signal_converter_adapter import SignalConverterAdapter

        adapter = SignalConverterAdapter()
        signal_batch = await adapter.convert_to_signals(
            predictions=prediction_batch, strategy_params=strategy_params,
        )

        # 强烈买入信号（predicted_value=0.08, confidence=0.9）
        signal_001 = signal_batch.get_signal(
            StockCode("sz000001"), datetime(2024, 1, 2),
        )
        assert signal_001.signal_strength == SignalStrength.STRONG

        # 中等买入信号（predicted_value=0.03, confidence=0.7）
        signal_002 = signal_batch.get_signal(
            StockCode("sz000002"), datetime(2024, 1, 2),
        )
        assert signal_002.signal_strength == SignalStrength.MEDIUM

    @pytest.mark.asyncio
    async def test_confidence_filtering(self, strategy_params):
        """
        测试置信度过滤

        验证:
        1. confidence < min_confidence -> 生成 HOLD 信号
        2. 低置信度预测不产生交易信号
        """
        from adapters.converters.signal_converter_adapter import SignalConverterAdapter

        # 创建低置信度预测批次
        low_confidence_batch = PredictionBatch(
            model_id="test_model", generated_at=datetime(2024, 1, 1),
        )
        low_confidence_batch.add_prediction(
            Prediction(
                model_id="test_model",
                stock_code=StockCode("sz000005"),
                timestamp=datetime(2024, 1, 2),
                predicted_value=Decimal("0.08"),  # 高涨幅
                confidence=Decimal("0.3"),  # 低置信度（< 0.6）
            ),
        )

        adapter = SignalConverterAdapter()
        signal_batch = await adapter.convert_to_signals(
            predictions=low_confidence_batch, strategy_params=strategy_params,
        )

        # 验证：低置信度应该生成 HOLD 信号
        signal = signal_batch.get_signal(StockCode("sz000005"), datetime(2024, 1, 2))
        assert signal is not None
        assert signal.signal_type == SignalType.HOLD

    @pytest.mark.asyncio
    async def test_empty_predictions(self, strategy_params):
        """
        测试空预测批次

        验证:
        1. 接受空预测批次
        2. 返回空信号批次
        """
        from adapters.converters.signal_converter_adapter import SignalConverterAdapter

        empty_batch = PredictionBatch(
            model_id="test_model", generated_at=datetime(2024, 1, 1),
        )

        adapter = SignalConverterAdapter()
        signal_batch = await adapter.convert_to_signals(
            predictions=empty_batch, strategy_params=strategy_params,
        )

        # 验证
        assert signal_batch is not None
        assert signal_batch.size() == 0

    @pytest.mark.asyncio
    async def test_signal_reason_generation(self, prediction_batch, strategy_params):
        """
        测试信号原因生成

        验证:
        1. 信号包含预测值和置信度信息
        2. 原因描述清晰易懂
        """
        from adapters.converters.signal_converter_adapter import SignalConverterAdapter

        adapter = SignalConverterAdapter()
        signal_batch = await adapter.convert_to_signals(
            predictions=prediction_batch, strategy_params=strategy_params,
        )

        # 检查信号原因
        signal = signal_batch.get_signal(StockCode("sz000001"), datetime(2024, 1, 2))
        assert signal is not None
        assert signal.reason is not None
        assert "0.08" in signal.reason or "8" in signal.reason  # 包含预测值
        assert "0.9" in signal.reason or "90" in signal.reason  # 包含置信度
