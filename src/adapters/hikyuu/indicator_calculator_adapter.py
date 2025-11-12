"""
IndicatorCalculatorAdapter - Hikyuu 指标计算适配器

适配 Hikyuu 技术指标计算,实现 IIndicatorCalculator 接口
"""

from typing import Dict, List
import re

# 为了便于测试，使用条件导入
try:
    import hikyuu
except ImportError:
    # 开发环境下 Mock hikyuu
    hikyuu = None

from domain.ports.indicator_calculator import IIndicatorCalculator
from domain.entities.kline_data import KLineData


class IndicatorCalculatorAdapter(IIndicatorCalculator):
    """
    Hikyuu 指标计算适配器

    实现 IIndicatorCalculator 接口,适配 Hikyuu 技术指标计算
    """

    def __init__(self, hikyuu_module=None):
        """
        初始化适配器

        Args:
            hikyuu_module: Hikyuu 模块实例（用于测试注入）
        """
        self.hikyuu = hikyuu_module if hikyuu_module is not None else hikyuu

    def _parse_indicator_name(self, indicator_name: str) -> tuple[str, list]:
        """
        解析指标名称和参数

        Args:
            indicator_name: 指标名称（如 "MA5", "RSI14", "MACD_12_26_9"）

        Returns:
            tuple: (指标类型, 参数列表)
        """
        # 匹配常见模式
        # MA5 -> ("MA", [5])
        # RSI14 -> ("RSI", [14])
        # MACD_12_26_9 -> ("MACD", [12, 26, 9])

        # 先尝试匹配下划线分隔的参数
        if "_" in indicator_name:
            parts = indicator_name.split("_")
            name = parts[0]
            params = [int(p) for p in parts[1:] if p.isdigit()]
            return (name, params)

        # 尝试匹配名称+数字的模式
        match = re.match(r"([A-Z]+)(\d+)", indicator_name)
        if match:
            name = match.group(1)
            param = int(match.group(2))
            return (name, [param])

        # 默认返回原始名称，无参数
        return (indicator_name, [])

    def _convert_kline_to_hikyuu(self, kline_data: List[KLineData]):
        """
        转换 Domain K 线数据到 Hikyuu 格式

        Args:
            kline_data: Domain K 线数据列表

        Returns:
            Hikyuu KData 对象
        """
        # 简化实现：在实际使用中需要根据 Hikyuu API 调整
        # 这里假设使用 Hikyuu 的 Stock 和 KData API

        if not kline_data:
            return None

        # 获取股票代码
        stock_code = kline_data[0].stock_code.value

        # 创建 Hikyuu Stock 对象
        # 注意：实际实现需要根据 Hikyuu API 调整
        stock = self.hikyuu.Stock(stock_code)
        kdata = stock.get_kdata()

        return kdata

    async def calculate_indicators(
        self, kline_data: List[KLineData], indicator_names: List[str]
    ) -> Dict[str, List[float]]:
        """
        计算技术指标

        Args:
            kline_data: K 线数据列表
            indicator_names: 要计算的指标名称列表

        Returns:
            Dict[str, List[float]]: 指标名称 -> 指标值列表的映射

        Raises:
            Exception: 当计算错误时
        """
        try:
            result = {}

            # 如果没有数据，返回空结果
            if not kline_data:
                for indicator_name in indicator_names:
                    result[indicator_name] = []
                return result

            # 转换 K 线数据（简化版，实际使用需要根据 Hikyuu API 调整）
            # kdata = self._convert_kline_to_hikyuu(kline_data)

            # 计算每个指标
            for indicator_name in indicator_names:
                name, params = self._parse_indicator_name(indicator_name)

                # 调用对应的 Hikyuu 指标函数
                if name == "MA":
                    period = params[0] if params else 5
                    indicator = self.hikyuu.MA(period)
                elif name == "RSI":
                    period = params[0] if params else 14
                    indicator = self.hikyuu.RSI(period)
                elif name == "MACD":
                    fast = params[0] if len(params) > 0 else 12
                    slow = params[1] if len(params) > 1 else 26
                    signal = params[2] if len(params) > 2 else 9
                    indicator = self.hikyuu.MACD(fast, slow, signal)
                else:
                    # 默认尝试直接调用
                    indicator_func = getattr(self.hikyuu, name, None)
                    if indicator_func:
                        indicator = (
                            indicator_func(*params) if params else indicator_func()
                        )
                    else:
                        raise ValueError(f"Unknown indicator: {name}")

                # 提取指标值
                values = []
                for i in range(len(indicator)):
                    values.append(float(indicator[i]))

                result[indicator_name] = values

            return result

        except Exception as e:
            raise Exception(f"Failed to calculate indicators with Hikyuu: {e}") from e
