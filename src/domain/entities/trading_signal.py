"""
TradingSignal Entity 和 SignalBatch Aggregate

交易信号实体和信号批次聚合根,遵循 DDD 原则
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum

from domain.value_objects.stock_code import StockCode


class SignalType(str, Enum):
    """信号类型枚举"""

    BUY = "BUY"  # 买入
    SELL = "SELL"  # 卖出
    HOLD = "HOLD"  # 持有


class SignalStrength(str, Enum):
    """信号强度枚举"""

    WEAK = "WEAK"  # 弱
    MEDIUM = "MEDIUM"  # 中等
    STRONG = "STRONG"  # 强


@dataclass
class TradingSignal:
    """
    交易信号实体

    实体特征:
    - 有唯一标识 (id)
    - 业务相等性基于股票代码和信号日期

    属性:
    - stock_code: 股票代码值对象
    - signal_date: 信号日期
    - signal_type: 信号类型(买入/卖出/持有)
    - signal_strength: 信号强度(弱/中/强)
    - price: 建议价格
    - reason: 信号原因
    """

    stock_code: StockCode
    signal_date: datetime
    signal_type: SignalType
    signal_strength: SignalStrength = SignalStrength.MEDIUM
    price: Decimal | None = None
    reason: str | None = None

    # 实体唯一标识
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self):
        """验证信号数据有效性"""
        # 价格必须 > 0
        if self.price is not None and self.price <= 0:
            raise ValueError(f"price must be > 0, got price={self.price}")

    def __eq__(self, other: object) -> bool:
        """
        业务相等性:基于股票代码和信号日期

        同一只股票在同一日期只有一个交易信号
        """
        if not isinstance(other, TradingSignal):
            return False
        return (
            self.stock_code == other.stock_code
            and self.signal_date == other.signal_date
        )

    def __hash__(self) -> int:
        """哈希基于股票代码和信号日期"""
        return hash((self.stock_code, self.signal_date))

    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.stock_code.value} {self.signal_date.date()} {self.signal_type.value} ({self.signal_strength.value})"

    def __repr__(self) -> str:
        """调试表示"""
        return f"TradingSignal(stock={self.stock_code.value}, date={self.signal_date}, type={self.signal_type.value}, id={self.id[:8]}...)"


@dataclass
class SignalBatch:
    """
    信号批次聚合根

    聚合根特征:
    - 有唯一标识 (id)
    - 管理 TradingSignal 实体的生命周期
    - 确保聚合内的业务不变性

    属性:
    - strategy_name: 策略名称
    - batch_date: 批次日期
    - signals: 交易信号列表
    """

    strategy_name: str
    batch_date: datetime
    signals: list[TradingSignal] = field(default_factory=list)

    # 聚合根唯一标识
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def add_signal(self, signal: TradingSignal) -> None:
        """
        添加信号到批次

        Args:
            signal: 交易信号实体

        Raises:
            ValueError: 如果信号已存在(相同股票+日期)
        """
        # 检查是否已存在相同信号
        existing = self.get_signal(signal.stock_code, signal.signal_date)
        if existing is not None:
            raise ValueError(
                f"Signal already exists for {signal.stock_code.value} on {signal.signal_date}",
            )

        self.signals.append(signal)

    def remove_signal(self, stock_code: StockCode, signal_date: datetime) -> None:
        """
        从批次移除信号

        Args:
            stock_code: 股票代码
            signal_date: 信号日期
        """
        self.signals = [
            s
            for s in self.signals
            if not (s.stock_code == stock_code and s.signal_date == signal_date)
        ]

    def get_signal(
        self, stock_code: StockCode, signal_date: datetime,
    ) -> TradingSignal | None:
        """
        根据股票代码和日期获取信号

        Args:
            stock_code: 股票代码
            signal_date: 信号日期

        Returns:
            Optional[TradingSignal]: 找到的信号,或 None
        """
        for signal in self.signals:
            if signal.stock_code == stock_code and signal.signal_date == signal_date:
                return signal
        return None

    def filter_by_type(self, signal_type: SignalType) -> list[TradingSignal]:
        """
        按信号类型过滤

        Args:
            signal_type: 信号类型

        Returns:
            List[TradingSignal]: 符合条件的信号列表
        """
        return [s for s in self.signals if s.signal_type == signal_type]

    def filter_by_strength(self, strength: SignalStrength) -> list[TradingSignal]:
        """
        按信号强度过滤

        Args:
            strength: 信号强度

        Returns:
            List[TradingSignal]: 符合条件的信号列表
        """
        return [s for s in self.signals if s.signal_strength == strength]

    def size(self) -> int:
        """
        获取批次大小

        Returns:
            int: 信号数量
        """
        return len(self.signals)

    def count_by_type(self) -> dict[SignalType, int]:
        """
        按类型统计信号数量

        Returns:
            Dict[SignalType, int]: 各类型信号数量
        """
        counts = {
            SignalType.BUY: 0,
            SignalType.SELL: 0,
            SignalType.HOLD: 0,
        }

        for signal in self.signals:
            counts[signal.signal_type] += 1

        return counts

    def __str__(self) -> str:
        """字符串表示"""
        return f"Batch({self.strategy_name}) {self.batch_date.date()} size={len(self.signals)}"

    def __repr__(self) -> str:
        """调试表示"""
        return f"SignalBatch(strategy={self.strategy_name}, date={self.batch_date}, size={len(self.signals)}, id={self.id[:8]}...)"
