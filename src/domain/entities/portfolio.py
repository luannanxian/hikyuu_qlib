"""
Portfolio 和 Position 实体

投资组合和持仓实体,遵循 DDD 原则
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from domain.value_objects.stock_code import StockCode


@dataclass
class Position:
    """
    持仓实体

    实体特征:
    - 有唯一标识 (id)
    - 业务相等性基于股票代码

    属性:
    - stock_code: 股票代码值对象
    - quantity: 持仓数量
    - avg_cost: 平均成本
    - current_price: 当前价格
    - open_date: 开仓日期
    """

    stock_code: StockCode
    quantity: int
    avg_cost: Decimal
    current_price: Decimal
    open_date: Optional[datetime] = None

    # 实体唯一标识
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self):
        """验证持仓数据有效性"""
        # 数量必须 > 0
        if self.quantity <= 0:
            raise ValueError(f"quantity must be > 0, got quantity={self.quantity}")

        # 成本价必须 > 0
        if self.avg_cost <= 0:
            raise ValueError(f"avg_cost must be > 0, got avg_cost={self.avg_cost}")

        # 当前价必须 > 0
        if self.current_price <= 0:
            raise ValueError(
                f"current_price must be > 0, got current_price={self.current_price}"
            )

    def market_value(self) -> Decimal:
        """
        计算市值

        Returns:
            Decimal: 市值 = 数量 × 当前价
        """
        return Decimal(self.quantity) * self.current_price

    def cost_value(self) -> Decimal:
        """
        计算成本

        Returns:
            Decimal: 成本 = 数量 × 成本价
        """
        return Decimal(self.quantity) * self.avg_cost

    def profit_loss(self) -> Decimal:
        """
        计算盈亏

        Returns:
            Decimal: 盈亏 = (当前价 - 成本价) × 数量
        """
        return (self.current_price - self.avg_cost) * Decimal(self.quantity)

    def return_pct(self) -> Decimal:
        """
        计算收益率

        Returns:
            Decimal: 收益率 = (当前价 - 成本价) / 成本价
        """
        if self.avg_cost == 0:
            return Decimal("0")
        return (self.current_price - self.avg_cost) / self.avg_cost

    def update_price(self, new_price: Decimal) -> None:
        """
        更新当前价格

        Args:
            new_price: 新价格
        """
        if new_price <= 0:
            raise ValueError(f"new_price must be > 0, got {new_price}")
        self.current_price = new_price

    def __eq__(self, other: object) -> bool:
        """
        业务相等性:基于股票代码

        同一个组合中同一只股票只有一个持仓
        """
        if not isinstance(other, Position):
            return False
        return self.stock_code == other.stock_code

    def __hash__(self) -> int:
        """哈希基于股票代码"""
        return hash(self.stock_code)

    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.stock_code.value} qty={self.quantity} price={self.current_price}"

    def __repr__(self) -> str:
        """调试表示"""
        return f"Position(stock={self.stock_code.value}, qty={self.quantity}, price={self.current_price}, id={self.id[:8]}...)"


@dataclass
class Portfolio:
    """
    投资组合聚合根

    聚合根特征:
    - 有唯一标识 (id)
    - 管理 Position 实体的生命周期
    - 确保聚合内的业务不变性

    属性:
    - name: 组合名称
    - initial_cash: 初始现金
    - available_cash: 可用现金
    - positions: 持仓列表
    """

    name: str
    initial_cash: Decimal
    available_cash: Decimal = field(init=False)
    positions: List[Position] = field(default_factory=list)

    # 聚合根唯一标识
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self):
        """初始化和验证"""
        # 初始现金必须 >= 0
        if self.initial_cash < 0:
            raise ValueError(
                f"initial_cash must be >= 0, got initial_cash={self.initial_cash}"
            )

        # 初始可用现金等于初始现金
        self.available_cash = self.initial_cash

    def add_position(self, position: Position) -> None:
        """
        添加持仓

        Args:
            position: 持仓实体

        Raises:
            ValueError: 如果持仓已存在(相同股票代码)
        """
        # 检查是否已存在相同持仓
        existing = self.get_position(position.stock_code)
        if existing is not None:
            raise ValueError(f"Position already exists for {position.stock_code.value}")

        self.positions.append(position)

    def remove_position(self, stock_code: StockCode) -> None:
        """
        移除持仓

        Args:
            stock_code: 股票代码
        """
        self.positions = [p for p in self.positions if p.stock_code != stock_code]

    def get_position(self, stock_code: StockCode) -> Optional[Position]:
        """
        根据股票代码获取持仓

        Args:
            stock_code: 股票代码

        Returns:
            Optional[Position]: 找到的持仓,或 None
        """
        for position in self.positions:
            if position.stock_code == stock_code:
                return position
        return None

    def total_market_value(self) -> Decimal:
        """
        计算总市值

        Returns:
            Decimal: 所有持仓的市值总和
        """
        return sum((p.market_value() for p in self.positions), Decimal("0"))

    def total_cost_value(self) -> Decimal:
        """
        计算总成本

        Returns:
            Decimal: 所有持仓的成本总和
        """
        return sum((p.cost_value() for p in self.positions), Decimal("0"))

    def total_value(self) -> Decimal:
        """
        计算总资产

        Returns:
            Decimal: 可用现金 + 总市值
        """
        return self.available_cash + self.total_market_value()

    def total_profit_loss(self) -> Decimal:
        """
        计算总盈亏

        Returns:
            Decimal: 所有持仓的盈亏总和
        """
        return sum((p.profit_loss() for p in self.positions), Decimal("0"))

    def get_position_weight(self, stock_code: StockCode) -> Decimal:
        """
        计算持仓权重

        Args:
            stock_code: 股票代码

        Returns:
            Decimal: 持仓市值 / 总资产
        """
        total = self.total_value()
        if total == 0:
            return Decimal("0")

        position = self.get_position(stock_code)
        if position is None:
            return Decimal("0")

        return position.market_value() / total

    def __str__(self) -> str:
        """字符串表示"""
        return f"Portfolio({self.name}) positions={len(self.positions)} value={self.total_value()}"

    def __repr__(self) -> str:
        """调试表示"""
        return f"Portfolio(name={self.name}, positions={len(self.positions)}, value={self.total_value()}, id={self.id[:8]}...)"
