"""
ManagePortfolioUseCase 单元测试

测试 UC-007: Manage Portfolio (管理投资组合) 用例
"""

from datetime import datetime
from decimal import Decimal

import pytest

from domain.entities.portfolio import Portfolio, Position
from domain.value_objects.stock_code import StockCode
from use_cases.portfolio.manage_portfolio import ManagePortfolioUseCase


class TestAddPosition:
    """测试添加持仓"""

    @pytest.mark.asyncio
    async def test_add_position_success(self):
        """测试成功添加持仓"""
        # Arrange: 创建组合和持仓
        portfolio = Portfolio(name="测试组合", initial_cash=Decimal(100000))

        position = Position(
            stock_code=StockCode("sh600000"),
            quantity=1000,
            avg_cost=Decimal("10.00"),
            current_price=Decimal("10.50"),
            open_date=datetime(2024, 1, 10),
        )

        use_case = ManagePortfolioUseCase()

        # Act: 添加持仓
        updated_portfolio = await use_case.add_position(
            portfolio=portfolio, position=position,
        )

        # Assert: 验证持仓已添加
        assert len(updated_portfolio.positions) == 1
        assert updated_portfolio.get_position(StockCode("sh600000")) is not None
        assert updated_portfolio.get_position(StockCode("sh600000")).quantity == 1000

    @pytest.mark.asyncio
    async def test_add_duplicate_position_raises_error(self):
        """测试添加重复持仓抛出异常"""
        # Arrange: 创建组合并添加一个持仓
        portfolio = Portfolio(name="测试组合", initial_cash=Decimal(100000))

        position1 = Position(
            stock_code=StockCode("sh600000"),
            quantity=1000,
            avg_cost=Decimal("10.00"),
            current_price=Decimal("10.50"),
        )
        portfolio.add_position(position1)

        # 尝试添加相同股票代码的持仓
        position2 = Position(
            stock_code=StockCode("sh600000"),
            quantity=500,
            avg_cost=Decimal("11.00"),
            current_price=Decimal("11.50"),
        )

        use_case = ManagePortfolioUseCase()

        # Act & Assert: 应该抛出异常
        with pytest.raises(ValueError, match="Position already exists"):
            await use_case.add_position(portfolio=portfolio, position=position2)


class TestRemovePosition:
    """测试移除持仓"""

    @pytest.mark.asyncio
    async def test_remove_position_success(self):
        """测试成功移除持仓"""
        # Arrange: 创建组合并添加持仓
        portfolio = Portfolio(name="测试组合", initial_cash=Decimal(100000))

        position = Position(
            stock_code=StockCode("sh600000"),
            quantity=1000,
            avg_cost=Decimal("10.00"),
            current_price=Decimal("10.50"),
        )
        portfolio.add_position(position)

        use_case = ManagePortfolioUseCase()

        # Act: 移除持仓
        updated_portfolio = await use_case.remove_position(
            portfolio=portfolio, stock_code=StockCode("sh600000"),
        )

        # Assert: 验证持仓已移除
        assert len(updated_portfolio.positions) == 0
        assert updated_portfolio.get_position(StockCode("sh600000")) is None


class TestUpdatePosition:
    """测试更新持仓"""

    @pytest.mark.asyncio
    async def test_update_position_price(self):
        """测试更新持仓价格"""
        # Arrange: 创建组合并添加持仓
        portfolio = Portfolio(name="测试组合", initial_cash=Decimal(100000))

        position = Position(
            stock_code=StockCode("sh600000"),
            quantity=1000,
            avg_cost=Decimal("10.00"),
            current_price=Decimal("10.50"),
        )
        portfolio.add_position(position)

        use_case = ManagePortfolioUseCase()

        # Act: 更新价格
        updated_portfolio = await use_case.update_position_price(
            portfolio=portfolio,
            stock_code=StockCode("sh600000"),
            new_price=Decimal("11.00"),
        )

        # Assert: 验证价格已更新
        position = updated_portfolio.get_position(StockCode("sh600000"))
        assert position is not None
        assert position.current_price == Decimal("11.00")

    @pytest.mark.asyncio
    async def test_update_nonexistent_position_raises_error(self):
        """测试更新不存在的持仓抛出异常"""
        # Arrange: 创建空组合
        portfolio = Portfolio(name="测试组合", initial_cash=Decimal(100000))

        use_case = ManagePortfolioUseCase()

        # Act & Assert: 应该抛出异常
        with pytest.raises(ValueError, match="Position not found"):
            await use_case.update_position_price(
                portfolio=portfolio,
                stock_code=StockCode("sh600000"),
                new_price=Decimal("11.00"),
            )


class TestCalculateMetrics:
    """测试计算组合指标"""

    @pytest.mark.asyncio
    async def test_calculate_portfolio_metrics(self):
        """测试计算组合指标"""
        # Arrange: 创建组合并添加多个持仓
        portfolio = Portfolio(name="测试组合", initial_cash=Decimal(100000))

        position1 = Position(
            stock_code=StockCode("sh600000"),
            quantity=1000,
            avg_cost=Decimal("10.00"),
            current_price=Decimal("10.50"),
        )
        position2 = Position(
            stock_code=StockCode("sz000001"),
            quantity=500,
            avg_cost=Decimal("20.00"),
            current_price=Decimal("22.00"),
        )

        portfolio.add_position(position1)
        portfolio.add_position(position2)

        use_case = ManagePortfolioUseCase()

        # Act: 计算指标
        metrics = await use_case.calculate_metrics(portfolio=portfolio)

        # Assert: 验证指标计算结果
        # position1 市值 = 1000 * 10.50 = 10500
        # position2 市值 = 500 * 22.00 = 11000
        # 总市值 = 21500
        # 可用现金 = 100000
        # 总资产 = 121500

        assert metrics["total_market_value"] == Decimal(21500)
        assert metrics["total_value"] == Decimal(121500)
        assert metrics["available_cash"] == Decimal(100000)
        assert metrics["position_count"] == 2

        # position1 盈亏 = (10.50 - 10.00) * 1000 = 500
        # position2 盈亏 = (22.00 - 20.00) * 500 = 1000
        # 总盈亏 = 1500
        assert metrics["total_profit_loss"] == Decimal(1500)
