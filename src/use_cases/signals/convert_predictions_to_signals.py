"""
ConvertPredictionsToSignalsUseCase - 预测转信号用例

UC-004: Convert Predictions to Signals (预测转信号)
"""


from domain.entities.prediction import PredictionBatch
from domain.entities.trading_signal import SignalBatch
from domain.ports.signal_converter import ISignalConverter


class ConvertPredictionsToSignalsUseCase:
    """
    预测转信号用例

    依赖注入:
    - converter: ISignalConverter (信号转换器接口)

    职责:
    - 验证策略参数
    - 调用转换器将预测转换为交易信号
    - 返回信号批次
    """

    def __init__(self, converter: ISignalConverter):
        """
        初始化用例

        Args:
            converter: 信号转换器接口实现
        """
        self.converter = converter

    async def execute(
        self, predictions: PredictionBatch, strategy_params: dict,
    ) -> SignalBatch:
        """
        执行预测转信号

        Args:
            predictions: 预测批次聚合
            strategy_params: 策略参数字典

        Returns:
            SignalBatch: 信号批次聚合

        Raises:
            ValueError: 策略参数无效
            Exception: 转换失败时传播异常
        """
        # 1. 验证策略参数
        self._validate_strategy_params(strategy_params)

        # 2. 调用转换器进行转换
        signal_batch = await self.converter.convert_to_signals(
            predictions=predictions, strategy_params=strategy_params,
        )

        # 3. 返回信号批次
        return signal_batch

    def _validate_strategy_params(self, strategy_params: dict) -> None:
        """
        验证策略参数

        Args:
            strategy_params: 策略参数字典

        Raises:
            ValueError: 参数无效时抛出异常
        """
        # 检查必要参数
        if "strategy_type" not in strategy_params:
            raise ValueError("strategy_type is required in strategy_params")

        strategy_type = strategy_params["strategy_type"]

        # 根据策略类型验证特定参数
        if strategy_type == "top_k":
            if "k" not in strategy_params:
                raise ValueError("'k' parameter is required for top_k strategy")
        elif strategy_type == "threshold":
            if "threshold" not in strategy_params:
                raise ValueError(
                    "'threshold' parameter is required for threshold strategy",
                )
