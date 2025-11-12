"""
KLineData Entity 单元测试

测试 DR-003: KLineData (K线数据) 领域模型
"""

import pytest
from datetime import datetime
from decimal import Decimal

from domain.entities.kline_data import KLineData
from domain.value_objects.kline_type import KLineType
from domain.value_objects.stock_code import StockCode


class TestKLineDataCreation:
    """测试 KLineData 创建"""

    def test_create_kline_data_with_all_fields(self):
        """测试创建完整K线数据"""
        kline = KLineData(
            kline_type=KLineType.DAY,
            stock_code=StockCode("sh600000"),
            timestamp=datetime(2020, 1, 2, 9, 30),
            open=Decimal("11.50"),
            high=Decimal("11.80"),
            low=Decimal("11.40"),
            close=Decimal("11.75"),
            volume=1000000,
            amount=Decimal("11700000.00"),
        )

        assert kline.stock_code == StockCode("sh600000")
        assert kline.timestamp == datetime(2020, 1, 2, 9, 30)
        assert kline.open == Decimal("11.50")
        assert kline.high == Decimal("11.80")
        assert kline.low == Decimal("11.40")
        assert kline.close == Decimal("11.75")
        assert kline.volume == 1000000
        assert kline.amount == Decimal("11700000.00")

    def test_kline_data_validation(self):
        """测试K线数据验证"""
        # high 必须 >= low
        with pytest.raises(ValueError, match="high must be >= low"):
            KLineData(
                kline_type=KLineType.DAY,
                stock_code=StockCode("sh600000"),
                timestamp=datetime(2020, 1, 2),
                open=Decimal("11.50"),
                high=Decimal("11.40"),  # high < low
                low=Decimal("11.50"),
                close=Decimal("11.45"),
                volume=1000000,
                amount=Decimal("11700000"),
            )

        # volume 必须 >= 0
        with pytest.raises(ValueError, match="volume must be >= 0"):
            KLineData(
                kline_type=KLineType.DAY,
                stock_code=StockCode("sh600000"),
                timestamp=datetime(2020, 1, 2),
                open=Decimal("11.50"),
                high=Decimal("11.80"),
                low=Decimal("11.40"),
                close=Decimal("11.75"),
                volume=-1000,  # 负数成交量
                amount=Decimal("11700000"),
            )


class TestKLineDataIdentity:
    """测试 KLineData 实体身份"""

    def test_kline_has_unique_id(self):
        """验证每条K线有唯一标识"""
        kline1 = KLineData(
            kline_type=KLineType.DAY,
            stock_code=StockCode("sh600000"),
            timestamp=datetime(2020, 1, 2),
            open=Decimal("11.50"),
            high=Decimal("11.80"),
            low=Decimal("11.40"),
            close=Decimal("11.75"),
            volume=1000000,
            amount=Decimal("11700000"),
        )
        kline2 = KLineData(
            kline_type=KLineType.DAY,
            stock_code=StockCode("sh600000"),
            timestamp=datetime(2020, 1, 2),
            open=Decimal("11.50"),
            high=Decimal("11.80"),
            low=Decimal("11.40"),
            close=Decimal("11.75"),
            volume=1000000,
            amount=Decimal("11700000"),
        )

        # 每个实体有唯一 ID
        assert hasattr(kline1, "id")
        assert hasattr(kline2, "id")
        assert kline1.id != kline2.id

    def test_kline_equality_based_on_stock_and_time(self):
        """验证K线相等性基于股票代码和时间戳"""
        kline1 = KLineData(
            kline_type=KLineType.DAY,
            stock_code=StockCode("sh600000"),
            timestamp=datetime(2020, 1, 2, 9, 30),
            open=Decimal("11.50"),
            high=Decimal("11.80"),
            low=Decimal("11.40"),
            close=Decimal("11.75"),
            volume=1000000,
            amount=Decimal("11700000"),
        )
        kline2 = KLineData(
            kline_type=KLineType.DAY,
            stock_code=StockCode("sh600000"),
            timestamp=datetime(2020, 1, 2, 9, 30),
            open=Decimal("11.60"),  # 价格不同
            high=Decimal("11.90"),
            low=Decimal("11.50"),
            close=Decimal("11.85"),
            volume=2000000,
            amount=Decimal("23400000"),
        )
        kline3 = KLineData(
            kline_type=KLineType.DAY,
            stock_code=StockCode("sh600000"),
            timestamp=datetime(2020, 1, 3, 9, 30),  # 时间不同
            open=Decimal("11.50"),
            high=Decimal("11.80"),
            low=Decimal("11.40"),
            close=Decimal("11.75"),
            volume=1000000,
            amount=Decimal("11700000"),
        )

        # 相同股票相同时间视为相等
        assert kline1 == kline2

        # 不同时间不相等
        assert kline1 != kline3


class TestKLineDataCalculations:
    """测试K线数据计算"""

    def test_price_change_rate(self):
        """测试涨跌幅计算"""
        kline = KLineData(
            kline_type=KLineType.DAY,
            stock_code=StockCode("sh600000"),
            timestamp=datetime(2020, 1, 2),
            open=Decimal("10.00"),
            high=Decimal("11.00"),
            low=Decimal("9.50"),
            close=Decimal("10.50"),
            volume=1000000,
            amount=Decimal("10250000"),
        )

        # 涨跌幅 = (close - open) / open
        # (10.50 - 10.00) / 10.00 = 0.05 = 5%
        assert kline.price_change_rate() == Decimal("0.05")

    def test_amplitude(self):
        """测试振幅计算"""
        kline = KLineData(
            kline_type=KLineType.DAY,
            stock_code=StockCode("sh600000"),
            timestamp=datetime(2020, 1, 2),
            open=Decimal("10.00"),
            high=Decimal("11.00"),
            low=Decimal("9.00"),
            close=Decimal("10.50"),
            volume=1000000,
            amount=Decimal("10250000"),
        )

        # 振幅 = (high - low) / open
        # (11.00 - 9.00) / 10.00 = 0.2 = 20%
        assert kline.amplitude() == Decimal("0.2")

    def test_average_price(self):
        """测试均价计算"""
        kline = KLineData(
            kline_type=KLineType.DAY,
            stock_code=StockCode("sh600000"),
            timestamp=datetime(2020, 1, 2),
            open=Decimal("10.00"),
            high=Decimal("11.00"),
            low=Decimal("9.00"),
            close=Decimal("10.50"),
            volume=1000000,
            amount=Decimal("10000000"),  # 1000000 * 10.00
        )

        # 均价 = amount / volume
        assert kline.average_price() == Decimal("10.00")


class TestKLineDataStringRepresentation:
    """测试K线字符串表示"""

    def test_kline_string_representation(self):
        """验证字符串表示"""
        kline = KLineData(
            kline_type=KLineType.DAY,
            stock_code=StockCode("sh600000"),
            timestamp=datetime(2020, 1, 2, 9, 30),
            open=Decimal("11.50"),
            high=Decimal("11.80"),
            low=Decimal("11.40"),
            close=Decimal("11.75"),
            volume=1000000,
            amount=Decimal("11700000"),
        )

        kline_str = str(kline)
        assert "sh600000" in kline_str
        assert "2020-01-02" in kline_str

        repr_str = repr(kline)
        assert "KLineData" in repr_str
        assert "sh600000" in repr_str
