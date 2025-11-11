"""
StockCode Value Object 单元测试

测试 DR-001: Stock (股票) 领域模型 - StockCode 值对象
"""

import pytest
from domain.value_objects.stock_code import StockCode


class TestStockCodeCreation:
    """测试 StockCode 创建"""

    def test_valid_stock_code_creation(self):
        """测试合法股票代码创建"""
        # 上海证券交易所
        sh_code = StockCode("sh600000")
        assert sh_code.value == "sh600000"

        # 深圳证券交易所
        sz_code = StockCode("sz000001")
        assert sz_code.value == "sz000001"

        # 北京证券交易所
        bj_code = StockCode("bj430047")
        assert bj_code.value == "bj430047"

    def test_invalid_stock_code_raises_error(self):
        """测试非法股票代码抛出异常"""
        # 长度不足 8 位
        with pytest.raises(ValueError, match="Invalid stock code"):
            StockCode("sh6000")

        # 长度超过 8 位
        with pytest.raises(ValueError, match="Invalid stock code"):
            StockCode("sh6000000")

        # 市场代码无效
        with pytest.raises(ValueError, match="Invalid stock code"):
            StockCode("hk600000")

        # 空字符串
        with pytest.raises(ValueError, match="Invalid stock code"):
            StockCode("")

        # 非小写字母开头
        with pytest.raises(ValueError, match="Invalid stock code"):
            StockCode("SH600000")

        # 数字部分非数字
        with pytest.raises(ValueError, match="Invalid stock code"):
            StockCode("sh60000a")


class TestStockCodeImmutability:
    """测试 StockCode 不可变性"""

    def test_stock_code_immutability(self):
        """验证 StockCode 值对象不可变"""
        code = StockCode("sh600000")

        # 尝试修改 value 属性应该失败
        with pytest.raises(AttributeError):
            code.value = "sz000001"


class TestStockCodeEquality:
    """测试 StockCode 相等性比较"""

    def test_stock_code_equality(self):
        """验证值对象相等性比较"""
        code1 = StockCode("sh600000")
        code2 = StockCode("sh600000")
        code3 = StockCode("sz000001")

        # 相同值的 StockCode 应该相等
        assert code1 == code2
        assert code1 is not code2  # 但不是同一个对象

        # 不同值的 StockCode 不相等
        assert code1 != code3

    def test_stock_code_hash(self):
        """验证 StockCode 可以作为字典键"""
        code1 = StockCode("sh600000")
        code2 = StockCode("sh600000")

        # 相同值的 StockCode 应该有相同的 hash
        assert hash(code1) == hash(code2)

        # 可以作为字典键
        stock_dict = {code1: "浦发银行"}
        assert stock_dict[code2] == "浦发银行"


class TestStockCodeStringRepresentation:
    """测试 StockCode 字符串表示"""

    def test_stock_code_string_representation(self):
        """验证字符串表示"""
        code = StockCode("sh600000")

        # __str__() 返回股票代码
        assert str(code) == "sh600000"

        # __repr__() 返回带类名的表示
        assert repr(code) == "StockCode('sh600000')"
