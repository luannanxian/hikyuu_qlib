"""
SignalConverterAdapter - 信号转换适配器

将模型预测结果转换为交易信号,实现 ISignalConverter 接口
"""

from decimal import Decimal

from domain.ports.signal_converter import ISignalConverter
from domain.entities.prediction import PredictionBatch, Prediction
from domain.entities.trading_signal import (
    SignalBatch,
    TradingSignal,
    SignalType,
    SignalStrength,
)


class SignalConverterAdapter(ISignalConverter):
    """
    信号转换适配器

    实现 ISignalConverter 接口,将预测转换为交易信号
    """

    def _determine_signal_type(
        self, prediction: Prediction, strategy_params: dict
    ) -> SignalType:
        """
        根据预测值和策略参数确定信号类型

        Args:
            prediction: 预测结果
            strategy_params: 策略参数

        Returns:
            SignalType: 信号类型
        """
        # 检查置信度
        min_confidence = Decimal(str(strategy_params.get("min_confidence", 0.6)))
        if prediction.confidence < min_confidence:
            return SignalType.HOLD

        # 检查预测值
        buy_threshold = Decimal(str(strategy_params.get("buy_threshold", 0.02)))
        sell_threshold = Decimal(str(strategy_params.get("sell_threshold", -0.02)))

        if prediction.predicted_value > buy_threshold:
            return SignalType.BUY
        elif prediction.predicted_value < sell_threshold:
            return SignalType.SELL
        else:
            return SignalType.HOLD

    def _determine_signal_strength(
        self, prediction: Prediction, strategy_params: dict
    ) -> SignalStrength:
        """
        根据预测值大小和置信度确定信号强度

        Args:
            prediction: 预测结果
            strategy_params: 策略参数

        Returns:
            SignalStrength: 信号强度
        """
        strong_threshold = Decimal(str(strategy_params.get("strong_threshold", 0.05)))
        abs_predicted_value = abs(prediction.predicted_value)

        # 强信号: 预测值绝对值大且置信度高
        if (
            abs_predicted_value >= strong_threshold
            and prediction.confidence >= Decimal("0.8")
        ):
            return SignalStrength.STRONG

        # 中等信号: 预测值或置信度较高
        if abs_predicted_value >= strong_threshold * Decimal(
            "0.6"
        ) or prediction.confidence >= Decimal("0.7"):
            return SignalStrength.MEDIUM

        # 弱信号
        return SignalStrength.WEAK

    def _generate_signal_reason(
        self, prediction: Prediction, signal_type: SignalType
    ) -> str:
        """
        生成信号原因描述

        Args:
            prediction: 预测结果
            signal_type: 信号类型

        Returns:
            str: 信号原因描述
        """
        predicted_pct = float(prediction.predicted_value) * 100
        confidence_pct = float(prediction.confidence) * 100

        if signal_type == SignalType.BUY:
            return f"预测涨幅 {predicted_pct:.2f}%, 置信度 {confidence_pct:.0f}%"
        elif signal_type == SignalType.SELL:
            return f"预测跌幅 {predicted_pct:.2f}%, 置信度 {confidence_pct:.0f}%"
        else:
            return f"预测变化 {predicted_pct:.2f}%, 置信度 {confidence_pct:.0f}%"

    def _convert_prediction_to_signal(
        self, prediction: Prediction, strategy_params: dict
    ) -> TradingSignal:
        """
        将单个预测转换为交易信号

        Args:
            prediction: 预测结果
            strategy_params: 策略参数

        Returns:
            TradingSignal: 交易信号
        """
        signal_type = self._determine_signal_type(prediction, strategy_params)
        signal_strength = self._determine_signal_strength(prediction, strategy_params)
        reason = self._generate_signal_reason(prediction, signal_type)

        return TradingSignal(
            stock_code=prediction.stock_code,
            signal_date=prediction.prediction_date,
            signal_type=signal_type,
            signal_strength=signal_strength,
            price=None,  # 价格可以在后续步骤中填充
            reason=reason,
        )

    async def convert_to_signals(
        self, predictions: PredictionBatch, strategy_params: dict
    ) -> SignalBatch:
        """
        将预测批次转换为交易信号批次

        Args:
            predictions: 预测批次
            strategy_params: 策略参数

        Returns:
            SignalBatch: 交易信号批次
        """
        # 创建信号批次
        strategy_name = strategy_params.get("strategy_name", "default_strategy")
        signal_batch = SignalBatch(
            strategy_name=strategy_name, batch_date=predictions.batch_date
        )

        # 转换每个预测为信号
        for prediction in predictions.predictions:
            signal = self._convert_prediction_to_signal(prediction, strategy_params)
            signal_batch.add_signal(signal)

        return signal_batch
