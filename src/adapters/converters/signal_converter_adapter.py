"""
SignalConverterAdapter - 信号转换适配器

将模型预测结果转换为交易信号,实现 ISignalConverter 接口
"""

import json
import logging
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pandas as pd

from domain.entities.prediction import Prediction, PredictionBatch
from domain.entities.trading_signal import (
    SignalBatch,
    SignalStrength,
    SignalType,
    TradingSignal,
)
from domain.ports.signal_converter import ISignalConverter
from domain.value_objects.stock_code import StockCode

logger = logging.getLogger(__name__)


class SignalConverterAdapter(ISignalConverter):
    """
    信号转换适配器

    实现 ISignalConverter 接口,将预测转换为交易信号
    """

    def _determine_signal_type(
        self, prediction: Prediction, strategy_params: dict,
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
        self, prediction: Prediction, strategy_params: dict,
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
            "0.6",
        ) or prediction.confidence >= Decimal("0.7"):
            return SignalStrength.MEDIUM

        # 弱信号
        return SignalStrength.WEAK

    def _generate_signal_reason(
        self, prediction: Prediction, signal_type: SignalType,
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
        self, prediction: Prediction, strategy_params: dict,
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
        self, predictions: PredictionBatch, strategy_params: dict,
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
            strategy_name=strategy_name, batch_date=predictions.batch_date,
        )

        # 转换每个预测为信号
        for prediction in predictions.predictions:
            signal = self._convert_prediction_to_signal(prediction, strategy_params)
            signal_batch.add_signal(signal)

        return signal_batch


class QlibToHikyuuSignalConverter:
    """
    Qlib预测转Hikyuu信号转换器

    直接读取Qlib的pred.pkl文件,应用选股策略,转换为Hikyuu交易信号
    """

    def __init__(self):
        """初始化转换器"""
        self.logger = logging.getLogger(self.__class__.__name__)

    def _normalize_stock_code(self, qlib_code: str) -> str:
        """
        规范化股票代码,将Qlib格式转换为Hikyuu格式

        Qlib格式示例: SH600036, SZ000001
        Hikyuu格式: sh600036, sz000001

        Args:
            qlib_code: Qlib股票代码

        Returns:
            str: Hikyuu股票代码
        """
        if not isinstance(qlib_code, str):
            qlib_code = str(qlib_code)

        # 移除可能的空格
        qlib_code = qlib_code.strip()

        # 转换为小写
        return qlib_code.lower()

    def _read_predictions(self, pred_path: Path) -> pd.DataFrame:
        """
        读取Qlib预测结果文件

        Args:
            pred_path: pred.pkl文件路径

        Returns:
            pd.DataFrame: 预测结果DataFrame, MultiIndex (datetime, instrument)

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式不正确
        """
        if not pred_path.exists():
            raise FileNotFoundError(f"Prediction file not found: {pred_path}")

        try:
            df = pd.read_pickle(pred_path)
            self.logger.info(f"Loaded predictions from {pred_path}, shape: {df.shape}")

            # 验证DataFrame格式
            if not isinstance(df.index, pd.MultiIndex):
                raise ValueError("Expected MultiIndex DataFrame with (datetime, instrument)")

            if len(df.index.names) != 2:
                raise ValueError(f"Expected 2 index levels, got {len(df.index.names)}")

            return df

        except Exception as e:
            self.logger.error(f"Failed to read predictions from {pred_path}: {e}")
            raise ValueError(f"Invalid prediction file format: {e}")

    def _apply_selection_strategy(
        self,
        df: pd.DataFrame,
        strategy_config: dict,
    ) -> pd.DataFrame:
        """
        应用选股策略过滤预测结果

        支持三种策略:
        - top_k: 选择预测值最高的K只股票
        - threshold: 选择预测值超过阈值的股票
        - percentile: 选择预测值在指定百分位以上的股票

        Args:
            df: 预测结果DataFrame
            strategy_config: 策略配置

        Returns:
            pd.DataFrame: 过滤后的预测结果
        """
        method = strategy_config.get("method", "top_k")

        if method == "top_k":
            top_k = strategy_config.get("top_k", 30)
            # 对每个日期选择top_k只股票
            selected = df.groupby(level=0).apply(
                lambda x: x.nlargest(top_k, x.columns[0]),
            )
            self.logger.info(f"Applied top_k strategy: selecting top {top_k} stocks per date")

        elif method == "threshold":
            threshold = strategy_config.get("threshold", 0.05)
            # 选择预测值超过阈值的股票
            selected = df[df.iloc[:, 0] > threshold]
            self.logger.info(f"Applied threshold strategy: threshold={threshold}")

        elif method == "percentile":
            percentile = strategy_config.get("percentile", 0.2)
            # 对每个日期选择预测值在指定百分位以上的股票
            threshold_value = df.groupby(level=0).apply(
                lambda x: x.iloc[:, 0].quantile(1 - percentile),
            )
            # 过滤每个日期的预测值
            selected_list = []
            for date, threshold in threshold_value.items():
                date_df = df.xs(date, level=0)
                selected_date = date_df[date_df.iloc[:, 0] >= threshold]
                selected_list.append(selected_date)

            if selected_list:
                selected = pd.concat(selected_list)
            else:
                selected = pd.DataFrame()

            self.logger.info(f"Applied percentile strategy: percentile={percentile}")

        else:
            raise ValueError(f"Unknown selection method: {method}")

        self.logger.info(f"Selected {len(selected)} predictions after applying {method} strategy")
        return selected

    def _calculate_signal_strength(self, predicted_value: float) -> SignalStrength:
        """
        根据预测值计算信号强度

        Args:
            predicted_value: 预测值

        Returns:
            SignalStrength: 信号强度
        """
        abs_value = abs(predicted_value)

        if abs_value >= 0.05:  # 5%以上
            return SignalStrength.STRONG
        elif abs_value >= 0.02:  # 2%-5%
            return SignalStrength.MEDIUM
        else:  # 2%以下
            return SignalStrength.WEAK

    def _determine_signal_type(self, predicted_value: float) -> SignalType:
        """
        根据预测值确定信号类型

        Args:
            predicted_value: 预测值

        Returns:
            SignalType: 信号类型
        """
        if predicted_value > 0.02:  # 涨幅大于2%
            return SignalType.BUY
        elif predicted_value < -0.02:  # 跌幅大于2%
            return SignalType.SELL
        else:
            return SignalType.HOLD

    def _create_trading_signal(
        self,
        stock_code: str,
        timestamp: datetime,
        predicted_value: float,
    ) -> TradingSignal:
        """
        创建交易信号实体

        Args:
            stock_code: 股票代码
            timestamp: 时间戳
            predicted_value: 预测值

        Returns:
            TradingSignal: 交易信号实体
        """
        # 规范化股票代码
        normalized_code = self._normalize_stock_code(stock_code)

        try:
            stock_code_vo = StockCode(normalized_code)
        except ValueError as e:
            self.logger.warning(f"Invalid stock code: {normalized_code}, skipping. Error: {e}")
            raise

        # 确定信号类型和强度
        signal_type = self._determine_signal_type(predicted_value)
        signal_strength = self._calculate_signal_strength(predicted_value)

        # 生成信号原因
        predicted_pct = predicted_value * 100
        reason = f"Qlib预测: {predicted_pct:+.2f}%"

        return TradingSignal(
            stock_code=stock_code_vo,
            signal_date=timestamp,
            signal_type=signal_type,
            signal_strength=signal_strength,
            price=None,  # 价格需要从行情数据获取
            reason=reason,
        )

    def convert_predictions_to_signals(
        self,
        pred_path: Path,
        strategy_config: dict,
        output_path: Path | None = None,
    ) -> list[TradingSignal]:
        """
        将Qlib预测结果转换为Hikyuu交易信号

        Args:
            pred_path: pred.pkl文件路径
            strategy_config: 选股策略配置
            output_path: 输出文件路径 (可选)

        Returns:
            List[TradingSignal]: 交易信号列表

        Raises:
            FileNotFoundError: 预测文件不存在
            ValueError: 文件格式或配置错误
        """
        # 读取预测结果
        predictions_df = self._read_predictions(pred_path)

        # 应用选股策略
        selected_df = self._apply_selection_strategy(predictions_df, strategy_config)

        # 转换为交易信号
        signals = []
        skipped_count = 0

        for (timestamp, instrument), row in selected_df.iterrows():
            predicted_value = float(row.iloc[0])  # 第一列是预测值

            try:
                signal = self._create_trading_signal(
                    stock_code=instrument,
                    timestamp=timestamp,
                    predicted_value=predicted_value,
                )
                signals.append(signal)
            except (ValueError, Exception) as e:
                skipped_count += 1
                self.logger.debug(f"Skipped signal creation for {instrument}: {e}")
                continue

        self.logger.info(
            f"Created {len(signals)} trading signals "
            f"({skipped_count} skipped due to invalid codes)",
        )

        # 导出信号到文件
        if output_path:
            self._export_signals(signals, output_path, strategy_config)

        return signals

    def _export_signals(
        self,
        signals: list[TradingSignal],
        output_path: Path,
        strategy_config: dict,
    ) -> None:
        """
        导出信号到文件

        Args:
            signals: 交易信号列表
            output_path: 输出文件路径
            strategy_config: 策略配置
        """
        # 创建输出目录
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 根据文件扩展名选择格式
        if output_path.suffix == ".csv":
            self._export_to_csv(signals, output_path)
        elif output_path.suffix == ".json":
            self._export_to_json(signals, output_path, strategy_config)
        else:
            raise ValueError(f"Unsupported output format: {output_path.suffix}")

        self.logger.info(f"Exported {len(signals)} signals to {output_path}")

    def _export_to_csv(self, signals: list[TradingSignal], output_path: Path) -> None:
        """
        导出信号到CSV文件

        CSV格式:
        stock_code,timestamp,action,strength,predicted_value
        sh600036,2024-01-01 00:00:00,BUY,STRONG,0.023

        Args:
            signals: 交易信号列表
            output_path: CSV文件路径
        """
        records = []
        for signal in signals:
            # 从reason中提取预测值
            predicted_value = self._extract_predicted_value_from_reason(signal.reason)

            records.append({
                "stock_code": signal.stock_code.value,
                "timestamp": signal.signal_date.strftime("%Y-%m-%d %H:%M:%S"),
                "action": signal.signal_type.value,
                "strength": signal.signal_strength.value,
                "predicted_value": f"{predicted_value:.6f}",
                "reason": signal.reason,
            })

        df = pd.DataFrame(records)
        df.to_csv(output_path, index=False, encoding="utf-8")

    def _export_to_json(
        self,
        signals: list[TradingSignal],
        output_path: Path,
        strategy_config: dict,
    ) -> None:
        """
        导出信号到JSON文件

        JSON格式:
        {
            "strategy": {...},
            "signals": [
                {
                    "stock_code": "sh600036",
                    "timestamp": "2024-01-01T00:00:00",
                    "action": "BUY",
                    "strength": "STRONG",
                    "predicted_value": 0.023,
                    "reason": "Qlib预测: +2.30%"
                }
            ]
        }

        Args:
            signals: 交易信号列表
            output_path: JSON文件路径
            strategy_config: 策略配置
        """
        records = []
        for signal in signals:
            predicted_value = self._extract_predicted_value_from_reason(signal.reason)

            records.append({
                "stock_code": signal.stock_code.value,
                "timestamp": signal.signal_date.isoformat(),
                "action": signal.signal_type.value,
                "strength": signal.signal_strength.value,
                "predicted_value": predicted_value,
                "reason": signal.reason,
                "signal_id": signal.id,
            })

        output_data = {
            "strategy": strategy_config,
            "generated_at": datetime.now().isoformat(),
            "total_signals": len(signals),
            "signals": records,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

    def _extract_predicted_value_from_reason(self, reason: str | None) -> float:
        """
        从信号原因中提取预测值

        Args:
            reason: 信号原因字符串, 例如 "Qlib预测: +2.30%"

        Returns:
            float: 预测值 (小数形式, 例如 0.023)
        """
        if not reason:
            return 0.0

        try:
            # 提取百分比数字
            import re
            match = re.search(r'([+-]?\d+\.?\d*)%', reason)
            if match:
                percentage = float(match.group(1))
                return percentage / 100.0
        except Exception:
            pass

        return 0.0
