"""
CalculateIndicatorsUseCase - 计算技术指标用例

UC-006: Calculate Indicators (计算技术指标)
"""

from typing import Dict, List

from domain.entities.kline_data import KLineData
from domain.ports.indicator_calculator import IIndicatorCalculator


class CalculateIndicatorsUseCase:
    """
    计算技术指标用例

    依赖注入:
    - calculator: IIndicatorCalculator (指标计算器接口)

    职责:
    - 协调指标计算流程
    - 验证输入参数
    - 调用指标计算器Port
    - 返回指标计算结果
    """

    def __init__(self, calculator: IIndicatorCalculator):
        """
        初始化用例

        Args:
            calculator: 指标计算器接口实现
        """
        self.calculator = calculator

    async def execute(
        self,
        kline_data: List[KLineData],
        indicator_names: List[str],
    ) -> Dict[str, List[float]]:
        """
        执行计算技术指标

        Args:
            kline_data: K线数据列表
            indicator_names: 要计算的指标名称列表

        Returns:
            Dict[str, List[float]]: 指标名称 -> 指标值列表的映射

        Raises:
            ValueError: 当输入数据无效时
            Exception: 当计算错误时传播异常
        """
        # 1. 验证输入参数
        if not kline_data:
            raise ValueError("kline_data cannot be empty")

        if not indicator_names:
            raise ValueError("indicator_names cannot be empty")

        # 2. 调用指标计算器Port计算指标
        indicators = await self.calculator.calculate_indicators(
            kline_data=kline_data, indicator_names=indicator_names
        )

        # 3. 返回计算结果
        return indicators
