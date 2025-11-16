"""
IIndicatorCalculator Port - 指标计算器接口

定义计算技术指标的端口接口
"""

from abc import ABC, abstractmethod

from domain.entities.kline_data import KLineData


class IIndicatorCalculator(ABC):
    """
    指标计算器端口接口

    定义计算技术指标的抽象方法
    """

    @abstractmethod
    async def calculate_indicators(
        self,
        kline_data: list[KLineData],
        indicator_names: list[str],
    ) -> dict[str, list[float]]:
        """
        计算技术指标

        Args:
            kline_data: K线数据列表
            indicator_names: 要计算的指标名称列表

        Returns:
            Dict[str, List[float]]: 指标名称 -> 指标值列表的映射

        Raises:
            ValueError: 当输入数据无效时
            Exception: 当计算错误时
        """
