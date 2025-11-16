"""
KLineData Entity

K线数据实体,遵循 DDD 实体原则
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from domain.value_objects.kline_type import KLineType
from domain.value_objects.stock_code import StockCode


@dataclass
class KLineData:
    """
    K线数据实体

    实体特征:
    - 有唯一标识 (id)
    - 业务相等性基于股票代码和时间戳

    属性:
    - stock_code: 股票代码值对象
    - timestamp: 时间戳
    - kline_type: K线类型
    - open: 开盘价
    - high: 最高价
    - low: 最低价
    - close: 收盘价
    - volume: 成交量
    - amount: 成交额
    """

    stock_code: StockCode
    timestamp: datetime
    kline_type: KLineType
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    amount: Decimal

    # 实体唯一标识
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self):
        """验证K线数据有效性"""
        # 最高价必须 >= 最低价
        if self.high < self.low:
            raise ValueError(
                f"high must be >= low, got high={self.high}, low={self.low}",
            )

        # 成交量必须 >= 0
        if self.volume < 0:
            raise ValueError(f"volume must be >= 0, got volume={self.volume}")

    def price_change_rate(self) -> Decimal:
        """
        计算涨跌幅

        Returns:
            Decimal: 涨跌幅 = (收盘价 - 开盘价) / 开盘价
        """
        if self.open == 0:
            return Decimal(0)
        return (self.close - self.open) / self.open

    def amplitude(self) -> Decimal:
        """
        计算振幅

        Returns:
            Decimal: 振幅 = (最高价 - 最低价) / 开盘价
        """
        if self.open == 0:
            return Decimal(0)
        return (self.high - self.low) / self.open

    def average_price(self) -> Decimal:
        """
        计算均价

        Returns:
            Decimal: 均价 = 成交额 / 成交量
        """
        if self.volume == 0:
            return Decimal(0)
        return self.amount / Decimal(self.volume)

    def __eq__(self, other: object) -> bool:
        """
        业务相等性:基于股票代码和时间戳

        同一只股票在同一时间点只有一条K线数据
        """
        if not isinstance(other, KLineData):
            return False
        return self.stock_code == other.stock_code and self.timestamp == other.timestamp

    def __hash__(self) -> int:
        """哈希基于股票代码和时间戳"""
        return hash((self.stock_code, self.timestamp))

    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.stock_code.value} {self.timestamp.date()} OHLC({self.open}/{self.high}/{self.low}/{self.close})"

    def __repr__(self) -> str:
        """调试表示"""
        return f"KLineData(stock={self.stock_code.value}, time={self.timestamp}, close={self.close}, id={self.id[:8]}...)"
