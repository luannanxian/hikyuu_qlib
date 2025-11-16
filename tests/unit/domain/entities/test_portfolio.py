"""
Portfolio 和 Position 实体单元测试

测试 DR-007: Portfolio (投资组合) 和 Position (持仓) 领域模型
"""

from datetime import datetime
from decimal import Decimal

import pytest

from domain.entities.portfolio import Portfolio, Position
from domain.value_objects.stock_code import StockCode


class TestPositionCreation:
    """测试 Position 创建"""

    def test_create_position_with_all_fields(self):
        """测试创建完整持仓"""
        position = Position(
            stock_code=StockCode("sh600000"),
            quantity=1000,
            avg_cost=Decimal("10.50"),
            current_price=Decimal("11.20"),
            open_date=datetime(2024, 1, 10),
        )

        assert position.stock_code == StockCode("sh600000")
        assert position.quantity == 1000
        assert position.avg_cost == Decimal("10.50")
        assert position.current_price == Decimal("11.20")
        assert position.open_date == datetime(2024, 1, 10)

    def test_position_quantity_validation(self):
        """测试持仓数量验证"""
        # 数量必须 > 0
        with pytest.raises(ValueError, match="quantity must be > 0"):
            Position(
                stock_code=StockCode("sh600000"),
                quantity=0,
                avg_cost=Decimal("10.50"),
                current_price=Decimal("11.20"),
            )

        with pytest.raises(ValueError, match="quantity must be > 0"):
            Position(
                stock_code=StockCode("sh600000"),
                quantity=-100,
                avg_cost=Decimal("10.50"),
                current_price=Decimal("11.20"),
            )

    def test_position_price_validation(self):
        """测试持仓价格验证"""
        # 成本价必须 > 0
        with pytest.raises(ValueError, match="avg_cost must be > 0"):
            Position(
                stock_code=StockCode("sh600000"),
                quantity=1000,
                avg_cost=Decimal(0),
                current_price=Decimal("11.20"),
            )

        # 当前价必须 > 0
        with pytest.raises(ValueError, match="current_price must be > 0"):
            Position(
                stock_code=StockCode("sh600000"),
                quantity=1000,
                avg_cost=Decimal("10.50"),
                current_price=Decimal(-5),
            )


class TestPositionCalculations:
    """测试 Position 计算方法"""

    def test_calculate_market_value(self):
        """测试市值计算"""
        position = Position(
            stock_code=StockCode("sh600000"),
            quantity=1000,
            avg_cost=Decimal("10.50"),
            current_price=Decimal("11.20"),
        )

        # 市值 = 数量 × 当前价 = 1000 × 11.20 = 11200
        assert position.market_value() == Decimal(11200)

    def test_calculate_cost_value(self):
        """测试成本计算"""
        position = Position(
            stock_code=StockCode("sh600000"),
            quantity=1000,
            avg_cost=Decimal("10.50"),
            current_price=Decimal("11.20"),
        )

        # 成本 = 数量 × 成本价 = 1000 × 10.50 = 10500
        assert position.cost_value() == Decimal(10500)

    def test_calculate_profit_loss(self):
        """测试盈亏计算"""
        position = Position(
            stock_code=StockCode("sh600000"),
            quantity=1000,
            avg_cost=Decimal("10.50"),
            current_price=Decimal("11.20"),
        )

        # 盈亏 = (当前价 - 成本价) × 数量 = (11.20 - 10.50) × 1000 = 700
        assert position.profit_loss() == Decimal(700)

    def test_calculate_profit_loss_negative(self):
        """测试亏损计算"""
        position = Position(
            stock_code=StockCode("sh600000"),
            quantity=1000,
            avg_cost=Decimal("10.50"),
            current_price=Decimal("9.80"),
        )

        # 盈亏 = (9.80 - 10.50) × 1000 = -700
        assert position.profit_loss() == Decimal(-700)

    def test_calculate_return_pct(self):
        """测试收益率计算"""
        position = Position(
            stock_code=StockCode("sh600000"),
            quantity=1000,
            avg_cost=Decimal("10.00"),
            current_price=Decimal("12.00"),
        )

        # 收益率 = (12.00 - 10.00) / 10.00 = 0.20 = 20%
        assert position.return_pct() == Decimal("0.20")

    def test_calculate_return_pct_negative(self):
        """测试负收益率计算"""
        position = Position(
            stock_code=StockCode("sh600000"),
            quantity=1000,
            avg_cost=Decimal("10.00"),
            current_price=Decimal("8.00"),
        )

        # 收益率 = (8.00 - 10.00) / 10.00 = -0.20 = -20%
        assert position.return_pct() == Decimal("-0.20")

    def test_update_current_price(self):
        """测试更新当前价格"""
        position = Position(
            stock_code=StockCode("sh600000"),
            quantity=1000,
            avg_cost=Decimal("10.50"),
            current_price=Decimal("11.20"),
        )

        # 更新价格
        position.update_price(Decimal("12.50"))

        assert position.current_price == Decimal("12.50")
        assert position.market_value() == Decimal(12500)


class TestPositionIdentity:
    """测试 Position 实体身份"""

    def test_position_has_unique_id(self):
        """验证每个持仓有唯一标识"""
        pos1 = Position(
            stock_code=StockCode("sh600000"),
            quantity=1000,
            avg_cost=Decimal("10.50"),
            current_price=Decimal("11.20"),
        )
        pos2 = Position(
            stock_code=StockCode("sh600000"),
            quantity=1000,
            avg_cost=Decimal("10.50"),
            current_price=Decimal("11.20"),
        )

        assert hasattr(pos1, "id")
        assert hasattr(pos2, "id")
        assert pos1.id != pos2.id

    def test_position_equality_based_on_stock_code(self):
        """验证持仓相等性基于股票代码"""
        pos1 = Position(
            stock_code=StockCode("sh600000"),
            quantity=1000,
            avg_cost=Decimal("10.50"),
            current_price=Decimal("11.20"),
        )
        pos2 = Position(
            stock_code=StockCode("sh600000"),
            quantity=2000,  # 不同数量
            avg_cost=Decimal("12.00"),  # 不同成本
            current_price=Decimal("13.00"),  # 不同价格
        )
        pos3 = Position(
            stock_code=StockCode("sz000001"),  # 不同股票
            quantity=1000,
            avg_cost=Decimal("10.50"),
            current_price=Decimal("11.20"),
        )

        # 相同股票代码视为相等
        assert pos1 == pos2

        # 不同股票代码不相等
        assert pos1 != pos3


class TestPortfolioCreation:
    """测试 Portfolio 创建"""

    def test_create_portfolio(self):
        """测试创建投资组合"""
        portfolio = Portfolio(
            name="我的组合",
            initial_cash=Decimal(100000),
        )

        assert portfolio.name == "我的组合"
        assert portfolio.initial_cash == Decimal(100000)
        assert portfolio.available_cash == Decimal(100000)
        assert len(portfolio.positions) == 0

    def test_portfolio_cash_validation(self):
        """测试组合现金验证"""
        # 初始现金必须 >= 0
        with pytest.raises(ValueError, match="initial_cash must be >= 0"):
            Portfolio(
                name="我的组合",
                initial_cash=Decimal(-1000),
            )

    def test_portfolio_has_unique_id(self):
        """验证每个组合有唯一标识"""
        pf1 = Portfolio(name="组合1", initial_cash=Decimal(100000))
        pf2 = Portfolio(name="组合1", initial_cash=Decimal(100000))

        assert hasattr(pf1, "id")
        assert hasattr(pf2, "id")
        assert pf1.id != pf2.id


class TestPortfolioPositionManagement:
    """测试 Portfolio 持仓管理"""

    def test_add_position(self):
        """测试添加持仓"""
        portfolio = Portfolio(name="我的组合", initial_cash=Decimal(100000))

        position = Position(
            stock_code=StockCode("sh600000"),
            quantity=1000,
            avg_cost=Decimal("10.50"),
            current_price=Decimal("11.20"),
        )

        portfolio.add_position(position)

        assert len(portfolio.positions) == 1
        assert portfolio.positions[0] == position

    def test_add_multiple_positions(self):
        """测试添加多个持仓"""
        portfolio = Portfolio(name="我的组合", initial_cash=Decimal(100000))

        pos1 = Position(
            stock_code=StockCode("sh600000"),
            quantity=1000,
            avg_cost=Decimal("10.50"),
            current_price=Decimal("11.20"),
        )
        pos2 = Position(
            stock_code=StockCode("sz000001"),
            quantity=500,
            avg_cost=Decimal("20.00"),
            current_price=Decimal("21.50"),
        )

        portfolio.add_position(pos1)
        portfolio.add_position(pos2)

        assert len(portfolio.positions) == 2

    def test_cannot_add_duplicate_position(self):
        """测试不能添加重复持仓(相同股票代码)"""
        portfolio = Portfolio(name="我的组合", initial_cash=Decimal(100000))

        pos1 = Position(
            stock_code=StockCode("sh600000"),
            quantity=1000,
            avg_cost=Decimal("10.50"),
            current_price=Decimal("11.20"),
        )
        pos2 = Position(
            stock_code=StockCode("sh600000"),  # 相同股票
            quantity=2000,
            avg_cost=Decimal("12.00"),
            current_price=Decimal("13.00"),
        )

        portfolio.add_position(pos1)

        with pytest.raises(ValueError, match="Position already exists"):
            portfolio.add_position(pos2)

    def test_remove_position(self):
        """测试移除持仓"""
        portfolio = Portfolio(name="我的组合", initial_cash=Decimal(100000))

        position = Position(
            stock_code=StockCode("sh600000"),
            quantity=1000,
            avg_cost=Decimal("10.50"),
            current_price=Decimal("11.20"),
        )

        portfolio.add_position(position)
        assert len(portfolio.positions) == 1

        portfolio.remove_position(StockCode("sh600000"))
        assert len(portfolio.positions) == 0

    def test_get_position(self):
        """测试获取持仓"""
        portfolio = Portfolio(name="我的组合", initial_cash=Decimal(100000))

        pos1 = Position(
            stock_code=StockCode("sh600000"),
            quantity=1000,
            avg_cost=Decimal("10.50"),
            current_price=Decimal("11.20"),
        )
        pos2 = Position(
            stock_code=StockCode("sz000001"),
            quantity=500,
            avg_cost=Decimal("20.00"),
            current_price=Decimal("21.50"),
        )

        portfolio.add_position(pos1)
        portfolio.add_position(pos2)

        found = portfolio.get_position(StockCode("sh600000"))
        assert found == pos1

    def test_get_nonexistent_position_returns_none(self):
        """测试获取不存在的持仓返回 None"""
        portfolio = Portfolio(name="我的组合", initial_cash=Decimal(100000))

        found = portfolio.get_position(StockCode("sh600000"))
        assert found is None


class TestPortfolioCalculations:
    """测试 Portfolio 计算方法"""

    def test_calculate_total_market_value(self):
        """测试总市值计算"""
        portfolio = Portfolio(name="我的组合", initial_cash=Decimal(100000))

        pos1 = Position(
            stock_code=StockCode("sh600000"),
            quantity=1000,
            avg_cost=Decimal("10.00"),
            current_price=Decimal("11.00"),
        )
        pos2 = Position(
            stock_code=StockCode("sz000001"),
            quantity=500,
            avg_cost=Decimal("20.00"),
            current_price=Decimal("22.00"),
        )

        portfolio.add_position(pos1)
        portfolio.add_position(pos2)

        # 总市值 = 1000×11 + 500×22 = 11000 + 11000 = 22000
        assert portfolio.total_market_value() == Decimal(22000)

    def test_calculate_total_cost_value(self):
        """测试总成本计算"""
        portfolio = Portfolio(name="我的组合", initial_cash=Decimal(100000))

        pos1 = Position(
            stock_code=StockCode("sh600000"),
            quantity=1000,
            avg_cost=Decimal("10.00"),
            current_price=Decimal("11.00"),
        )
        pos2 = Position(
            stock_code=StockCode("sz000001"),
            quantity=500,
            avg_cost=Decimal("20.00"),
            current_price=Decimal("22.00"),
        )

        portfolio.add_position(pos1)
        portfolio.add_position(pos2)

        # 总成本 = 1000×10 + 500×20 = 10000 + 10000 = 20000
        assert portfolio.total_cost_value() == Decimal(20000)

    def test_calculate_total_value(self):
        """测试总资产计算"""
        portfolio = Portfolio(name="我的组合", initial_cash=Decimal(100000))
        portfolio.available_cash = Decimal(80000)  # 使用了部分现金

        pos1 = Position(
            stock_code=StockCode("sh600000"),
            quantity=1000,
            avg_cost=Decimal("10.00"),
            current_price=Decimal("11.00"),
        )
        pos2 = Position(
            stock_code=StockCode("sz000001"),
            quantity=500,
            avg_cost=Decimal("20.00"),
            current_price=Decimal("22.00"),
        )

        portfolio.add_position(pos1)
        portfolio.add_position(pos2)

        # 总资产 = 可用现金 + 总市值 = 80000 + 22000 = 102000
        assert portfolio.total_value() == Decimal(102000)

    def test_calculate_total_profit_loss(self):
        """测试总盈亏计算"""
        portfolio = Portfolio(name="我的组合", initial_cash=Decimal(100000))

        pos1 = Position(
            stock_code=StockCode("sh600000"),
            quantity=1000,
            avg_cost=Decimal("10.00"),
            current_price=Decimal("11.00"),
        )
        pos2 = Position(
            stock_code=StockCode("sz000001"),
            quantity=500,
            avg_cost=Decimal("20.00"),
            current_price=Decimal("22.00"),
        )

        portfolio.add_position(pos1)
        portfolio.add_position(pos2)

        # 总盈亏 = (11-10)×1000 + (22-20)×500 = 1000 + 1000 = 2000
        assert portfolio.total_profit_loss() == Decimal(2000)

    def test_get_position_weight(self):
        """测试持仓权重计算"""
        portfolio = Portfolio(name="我的组合", initial_cash=Decimal(100000))
        portfolio.available_cash = Decimal(78000)

        pos1 = Position(
            stock_code=StockCode("sh600000"),
            quantity=1000,
            avg_cost=Decimal("10.00"),
            current_price=Decimal("11.00"),  # 市值 11000
        )
        pos2 = Position(
            stock_code=StockCode("sz000001"),
            quantity=500,
            avg_cost=Decimal("20.00"),
            current_price=Decimal("22.00"),  # 市值 11000
        )

        portfolio.add_position(pos1)
        portfolio.add_position(pos2)

        # 总资产 = 78000 + 11000 + 11000 = 100000
        # sh600000 权重 = 11000 / 100000 = 0.11
        weight = portfolio.get_position_weight(StockCode("sh600000"))
        assert weight == Decimal("0.11")

    def test_get_position_weight_zero_total(self):
        """测试总资产为0时的权重"""
        portfolio = Portfolio(name="我的组合", initial_cash=Decimal(0))

        # 总资产为0(无现金无持仓),权重返回0
        weight = portfolio.get_position_weight(StockCode("sh600000"))
        assert weight == Decimal(0)


class TestPortfolioStringRepresentation:
    """测试 Portfolio 字符串表示"""

    def test_portfolio_string_representation(self):
        """验证字符串表示"""
        portfolio = Portfolio(name="我的组合", initial_cash=Decimal(100000))

        pf_str = str(portfolio)
        assert "我的组合" in pf_str

        repr_str = repr(portfolio)
        assert "Portfolio" in repr_str
        assert "我的组合" in repr_str
