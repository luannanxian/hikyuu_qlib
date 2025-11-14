"""
GenerateTopKSignalsUseCase - 生成Top-K交易信号用例

UC-TOPK: Generate Top-K Trading Signals (从Qlib预测生成Top-K交易信号)
"""

from dataclasses import dataclass
from typing import Optional

from domain.entities.prediction import PredictionBatch
from domain.entities.trading_signal import SignalBatch
from domain.ports.signal_provider import ISignalProvider


@dataclass
class GenerateTopKSignalsRequest:
    """
    生成Top-K信号请求DTO

    Attributes:
        prediction_batch: 预测批次聚合根
        top_k: Top-K选股数量,默认10只
        buy_threshold: 买入阈值,预测值 > threshold 时买入,默认0.02 (2%)
        sell_threshold: 卖出阈值,预测值 < threshold 时卖出,默认-0.02 (-2%)
        strategy_name: 策略名称,默认"QlibTopK"
    """

    prediction_batch: PredictionBatch
    top_k: int = 10
    buy_threshold: float = 0.02
    sell_threshold: float = -0.02
    strategy_name: str = "QlibTopK"

    def __post_init__(self):
        """验证请求参数有效性"""
        if self.top_k <= 0:
            raise ValueError(f"top_k must be > 0, got top_k={self.top_k}")

        if self.buy_threshold <= self.sell_threshold:
            raise ValueError(
                f"buy_threshold must be > sell_threshold, "
                f"got buy_threshold={self.buy_threshold}, sell_threshold={self.sell_threshold}"
            )


@dataclass
class GenerateTopKSignalsResponse:
    """
    生成Top-K信号响应DTO

    Attributes:
        signal_batch: 信号批次聚合根
        success: 是否成功
        error: 错误信息(如果失败)
    """

    signal_batch: Optional[SignalBatch] = None
    success: bool = False
    error: Optional[str] = None


class GenerateTopKSignalsUseCase:
    """
    生成Top-K交易信号用例

    职责:
    - 验证请求参数
    - 从预测批次生成Top-K交易信号
    - 处理异常并返回响应

    依赖注入:
    - signal_provider: ISignalProvider (信号提供者接口)

    业务规则:
    - 按预测值降序排序,选择Top-K股票
    - 对Top-K股票应用买入/卖出阈值生成信号
    - 预测值 > buy_threshold 生成买入信号
    - 预测值 < sell_threshold 生成卖出信号
    - 其他情况生成持有信号
    """

    def __init__(self, signal_provider: ISignalProvider):
        """
        初始化用例

        Args:
            signal_provider: 信号提供者接口实现
        """
        self.signal_provider = signal_provider

    async def execute(
        self, request: GenerateTopKSignalsRequest
    ) -> GenerateTopKSignalsResponse:
        """
        执行生成Top-K交易信号

        Args:
            request: 生成Top-K信号请求

        Returns:
            GenerateTopKSignalsResponse: 包含信号批次的响应

        业务流程:
        1. 验证预测批次不为空
        2. 调用信号提供者生成信号
        3. 返回成功响应

        异常处理:
        - ValueError: 参数验证失败
        - Exception: 信号生成失败
        """
        try:
            # 1. 验证预测批次不为空
            if request.prediction_batch.size() == 0:
                return GenerateTopKSignalsResponse(
                    success=False,
                    error="Prediction batch is empty, cannot generate signals",
                )

            # 2. 验证 top_k 不超过预测数量
            actual_k = min(request.top_k, request.prediction_batch.size())
            if actual_k < request.top_k:
                # 记录警告但继续执行
                pass

            # 3. 调用信号提供者生成Top-K信号
            signal_batch = self.signal_provider.generate_signals_from_predictions(
                prediction_batch=request.prediction_batch,
                buy_threshold=request.buy_threshold,
                sell_threshold=request.sell_threshold,
                top_k=actual_k,
            )

            # 4. 设置策略名称
            # 注意: 这里假设 SignalBatch 是可变的
            # 如果不可变,需要创建新的 SignalBatch
            if signal_batch.strategy_name != request.strategy_name:
                # 创建新的 SignalBatch with 自定义策略名称
                from datetime import datetime

                signal_batch = SignalBatch(
                    strategy_name=request.strategy_name,
                    batch_date=request.prediction_batch.generated_at,
                    signals=signal_batch.signals.copy(),
                )

            # 5. 返回成功响应
            return GenerateTopKSignalsResponse(
                signal_batch=signal_batch,
                success=True,
            )

        except ValueError as e:
            # 参数验证失败
            return GenerateTopKSignalsResponse(
                success=False,
                error=f"Validation error: {str(e)}",
            )

        except Exception as e:
            # 其他异常
            return GenerateTopKSignalsResponse(
                success=False,
                error=f"Failed to generate signals: {str(e)}",
            )
