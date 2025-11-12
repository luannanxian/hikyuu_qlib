"""
Stock Entity 单元测试

测试 DR-001: Stock (股票) 领域模型 - Stock 实体
"""

import pytest
from domain.entities.stock import Stock
from domain.value_objects.stock_code import StockCode
from domain.value_objects.market import Market


class TestStockCreation:
    """测试 Stock 创建"""

    def test_create_stock_with_all_attributes(self):
        """测试创建完整属性的股票"""
        stock = Stock(
            code=StockCode("sh600000"),
            market=Market("SH"),
            name="浦发银行",
            list_date="2000-01-01",
        )

        assert stock.code == StockCode("sh600000")
        assert stock.market == Market("SH")
        assert stock.name == "浦发银行"
        assert stock.list_date == "2000-01-01"

    def test_create_stock_without_optional_attributes(self):
        """测试创建最小属性的股票"""
        stock = Stock(code=StockCode("sz000001"), market=Market("SZ"))

        assert stock.code == StockCode("sz000001")
        assert stock.market == Market("SZ")
        assert stock.name is None
        assert stock.list_date is None

    def test_stock_code_market_consistency(self):
        """测试股票代码和市场的一致性验证"""
        # 一致的情况应该成功
        stock_sh = Stock(code=StockCode("sh600000"), market=Market("SH"))
        assert stock_sh.code.value.startswith("sh")
        assert stock_sh.market.code == "SH"

        # 不一致的情况应该抛出异常
        with pytest.raises(ValueError, match="Stock code and market mismatch"):
            Stock(code=StockCode("sh600000"), market=Market("SZ"))  # 上海股票  # 深圳市场


class TestStockIdentity:
    """测试 Stock 实体身份"""

    def test_stock_has_unique_id(self):
        """验证每个股票实体有唯一标识"""
        stock1 = Stock(code=StockCode("sh600000"), market=Market("SH"))
        stock2 = Stock(code=StockCode("sh600000"), market=Market("SH"))

        # 每个实体应该有唯一 ID
        assert hasattr(stock1, "id")
        assert hasattr(stock2, "id")
        assert stock1.id != stock2.id

    def test_stock_equality_based_on_code(self):
        """验证股票相等性基于股票代码"""
        stock1 = Stock(code=StockCode("sh600000"), market=Market("SH"), name="浦发银行")
        stock2 = Stock(
            code=StockCode("sh600000"), market=Market("SH"), name="浦发银行 A"  # 名称不同
        )
        stock3 = Stock(code=StockCode("sz000001"), market=Market("SZ"))

        # 相同代码的股票视为相等(业务相等性)
        assert stock1 == stock2

        # 不同代码的股票不相等
        assert stock1 != stock3

    def test_stock_hash_based_on_code(self):
        """验证股票哈希基于股票代码"""
        stock1 = Stock(code=StockCode("sh600000"), market=Market("SH"))
        stock2 = Stock(code=StockCode("sh600000"), market=Market("SH"))

        # 相同代码的股票应该有相同 hash
        assert hash(stock1) == hash(stock2)

        # 可以作为字典键
        stock_dict = {stock1: "浦发银行"}
        assert stock_dict[stock2] == "浦发银行"


class TestStockStringRepresentation:
    """测试 Stock 字符串表示"""

    def test_stock_string_representation(self):
        """验证字符串表示"""
        stock = Stock(code=StockCode("sh600000"), market=Market("SH"), name="浦发银行")

        # __str__() 返回股票代码和名称
        assert str(stock) == "sh600000 浦发银行"

        # 没有名称时只返回代码
        stock_no_name = Stock(code=StockCode("sz000001"), market=Market("SZ"))
        assert str(stock_no_name) == "sz000001"

    def test_stock_repr(self):
        """验证 repr 表示"""
        stock = Stock(code=StockCode("sh600000"), market=Market("SH"), name="浦发银行")

        repr_str = repr(stock)
        assert "Stock" in repr_str
        assert "sh600000" in repr_str


class TestStockProperties:
    """测试 Stock 属性和方法"""

    def test_stock_market_code_property(self):
        """测试获取完整市场代码"""
        stock = Stock(code=StockCode("sh600000"), market=Market("SH"))

        # 应该返回完整的市场代码 (如 SH600000)
        assert stock.market_code == "SH600000"

    def test_stock_is_valid(self):
        """测试股票有效性验证"""
        # 有上市日期的股票是有效的
        valid_stock = Stock(
            code=StockCode("sh600000"), market=Market("SH"), list_date="2000-01-01"
        )
        assert valid_stock.is_valid() is True

        # 没有上市日期的股票视为有效(待补充)
        no_date_stock = Stock(code=StockCode("sz000001"), market=Market("SZ"))
        assert no_date_stock.is_valid() is True
