"""
ManagePortfolioUseCase - 管理投资组合用例

UC-007: Manage Portfolio (管理投资组合)
"""

from decimal import Decimal

from domain.entities.portfolio import Portfolio, Position
from domain.value_objects.stock_code import StockCode


class ManagePortfolioUseCase:
    """
    管理投资组合用例

    职责:
    - 添加持仓
    - 移除持仓
    - 更新持仓价格
    - 计算组合指标

    注意:
    - 直接操作 Portfolio 聚合根
    - 确保业务不变性（如不能添加重复持仓）
    """

    async def add_position(self, portfolio: Portfolio, position: Position) -> Portfolio:
        """
        添加持仓到组合

        Args:
            portfolio: 投资组合聚合根
            position: 持仓实体

        Returns:
            Portfolio: 更新后的组合

        Raises:
            ValueError: 如果持仓已存在
        """
        # Portfolio 聚合根负责验证业务规则
        portfolio.add_position(position)

        return portfolio

    async def remove_position(
        self, portfolio: Portfolio, stock_code: StockCode,
    ) -> Portfolio:
        """
        从组合移除持仓

        Args:
            portfolio: 投资组合聚合根
            stock_code: 股票代码

        Returns:
            Portfolio: 更新后的组合
        """
        portfolio.remove_position(stock_code)

        return portfolio

    async def update_position_price(
        self, portfolio: Portfolio, stock_code: StockCode, new_price: Decimal,
    ) -> Portfolio:
        """
        更新持仓价格

        Args:
            portfolio: 投资组合聚合根
            stock_code: 股票代码
            new_price: 新价格

        Returns:
            Portfolio: 更新后的组合

        Raises:
            ValueError: 如果持仓不存在或价格无效
        """
        # 获取持仓
        position = portfolio.get_position(stock_code)
        if position is None:
            raise ValueError(f"Position not found for {stock_code.value}")

        # 更新价格
        position.update_price(new_price)

        return portfolio

    async def calculate_metrics(self, portfolio: Portfolio) -> dict[str, Decimal]:
        """
        计算组合指标

        Args:
            portfolio: 投资组合聚合根

        Returns:
            Dict[str, Decimal]: 组合指标字典
        """
        metrics = {
            "total_market_value": portfolio.total_market_value(),
            "total_cost_value": portfolio.total_cost_value(),
            "total_value": portfolio.total_value(),
            "available_cash": portfolio.available_cash,
            "total_profit_loss": portfolio.total_profit_loss(),
            "position_count": len(portfolio.positions),
        }

        return metrics
