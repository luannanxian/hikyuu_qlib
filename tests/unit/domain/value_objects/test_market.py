"""
Market Value Object 单元测试

测试 DR-001: Stock (股票) 领域模型 - Market 值对象
"""

import pytest

from domain.value_objects.market import Market


class TestMarketCreation:
    """测试 Market 创建"""

    def test_valid_market_creation(self):
        """测试合法市场代码创建"""
        # 上海证券交易所
        sh_market = Market("SH")
        assert sh_market.code == "SH"
        assert sh_market.name == "上海证券交易所"

        # 深圳证券交易所
        sz_market = Market("SZ")
        assert sz_market.code == "SZ"
        assert sz_market.name == "深圳证券交易所"

        # 北京证券交易所
        bj_market = Market("BJ")
        assert bj_market.code == "BJ"
        assert bj_market.name == "北京证券交易所"

    def test_case_insensitive_market_creation(self):
        """测试不区分大小写创建"""
        # 小写输入应该被标准化为大写
        sh_lower = Market("sh")
        assert sh_lower.code == "SH"

        sz_lower = Market("sz")
        assert sz_lower.code == "SZ"

    def test_invalid_market_raises_error(self):
        """测试非法市场代码抛出异常"""
        # 不支持的市场
        with pytest.raises(ValueError, match="Invalid market code"):
            Market("HK")

        with pytest.raises(ValueError, match="Invalid market code"):
            Market("US")

        # 空字符串
        with pytest.raises(ValueError, match="Invalid market code"):
            Market("")

        # 数字
        with pytest.raises(ValueError, match="Invalid market code"):
            Market("123")


class TestMarketImmutability:
    """测试 Market 不可变性"""

    def test_market_immutability(self):
        """验证 Market 值对象不可变"""
        market = Market("SH")

        # 尝试修改 code 属性应该失败
        with pytest.raises(AttributeError):
            market.code = "SZ"

        # 尝试修改 name 属性应该失败
        with pytest.raises(AttributeError):
            market.name = "深圳证券交易所"


class TestMarketEquality:
    """测试 Market 相等性比较"""

    def test_market_equality(self):
        """验证值对象相等性比较"""
        market1 = Market("SH")
        market2 = Market("sh")  # 小写,但应该等于 SH
        market3 = Market("SZ")

        # 相同值的 Market 应该相等
        assert market1 == market2
        assert market1 is not market2  # 但不是同一个对象

        # 不同值的 Market 不相等
        assert market1 != market3

    def test_market_hash(self):
        """验证 Market 可以作为字典键"""
        market1 = Market("SH")
        market2 = Market("sh")

        # 相同值的 Market 应该有相同的 hash
        assert hash(market1) == hash(market2)

        # 可以作为字典键
        market_dict = {market1: "上海"}
        assert market_dict[market2] == "上海"


class TestMarketStringRepresentation:
    """测试 Market 字符串表示"""

    def test_market_string_representation(self):
        """验证字符串表示"""
        market = Market("SH")

        # __str__() 返回市场代码
        assert str(market) == "SH"

        # __repr__() 返回带类名的表示
        assert repr(market) == "Market('SH')"


class TestMarketProperties:
    """测试 Market 属性"""

    def test_market_name_property(self):
        """验证市场名称属性"""
        sh = Market("SH")
        assert sh.name == "上海证券交易所"

        sz = Market("SZ")
        assert sz.name == "深圳证券交易所"

        bj = Market("BJ")
        assert bj.name == "北京证券交易所"

    def test_market_is_mainland_china(self):
        """验证是否为中国大陆市场"""
        sh = Market("SH")
        assert sh.is_mainland_china() is True

        sz = Market("SZ")
        assert sz.is_mainland_china() is True

        bj = Market("BJ")
        assert bj.is_mainland_china() is True
