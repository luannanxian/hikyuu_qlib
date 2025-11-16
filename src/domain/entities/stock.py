"""
Stock Entity

股票实体,遵循 DDD 实体原则
"""

import uuid
from dataclasses import dataclass, field

from domain.value_objects.market import Market
from domain.value_objects.stock_code import StockCode


@dataclass
class Stock:
    """
    股票实体

    实体特征:
    - 有唯一标识 (id)
    - 业务相等性基于股票代码
    - 可变 (与值对象不同)

    属性:
    - code: 股票代码值对象
    - market: 市场值对象
    - name: 股票名称 (可选)
    - list_date: 上市日期 (可选)
    """

    code: StockCode
    market: Market
    name: str | None = None
    list_date: str | None = None

    # 实体唯一标识 (自动生成)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self):
        """验证股票代码和市场的一致性"""
        # 提取股票代码的市场前缀
        code_market = self.code.value[:2].upper()  # sh -> SH
        market_code = self.market.code  # 已经是大写

        if code_market != market_code:
            raise ValueError(
                f"Stock code and market mismatch: "
                f"code={self.code.value}, market={market_code}",
            )

    @property
    def market_code(self) -> str:
        """
        获取完整的市场代码

        Returns:
            str: 如 SH600000, SZ000001
        """
        # sh600000 -> SH600000
        return self.code.value.upper()

    def is_valid(self) -> bool:
        """
        验证股票有效性

        Returns:
            bool: 股票是否有效
        """
        # 简单实现:有股票代码即为有效
        # 未来可以扩展:检查是否退市、是否停牌等
        return True

    def __eq__(self, other: object) -> bool:
        """
        业务相等性:基于股票代码

        DDD 原则:实体的相等性由业务标识决定,而不是对象标识
        """
        if not isinstance(other, Stock):
            return False
        return self.code == other.code

    def __hash__(self) -> int:
        """哈希基于股票代码"""
        return hash(self.code)

    def __str__(self) -> str:
        """字符串表示"""
        if self.name:
            return f"{self.code.value} {self.name}"
        return self.code.value

    def __repr__(self) -> str:
        """调试表示"""
        return (
            f"Stock(code={self.code.value}, market={self.market.code}, "
            f"name={self.name}, id={self.id[:8]}...)"
        )
