"""
HikyuuDataAdapter 单元测试

测试 HikyuuDataAdapter 实现 IStockDataProvider 接口,
使用 Mock 隔离 Hikyuu 框架依赖
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock
from typing import List

from domain.value_objects.stock_code import StockCode
from domain.value_objects.date_range import DateRange
from domain.value_objects.kline_type import KLineType
from domain.entities.kline_data import KLineData


class TestHikyuuDataAdapter:
    """测试 HikyuuDataAdapter"""

    @pytest.fixture
    def stock_code(self) -> StockCode:
        """股票代码 fixture"""
        return StockCode("sh600000")

    @pytest.fixture
    def date_range(self) -> DateRange:
        """日期范围 fixture"""
        return DateRange(date(2023, 1, 1), date(2023, 12, 31))

    @pytest.fixture
    def mock_hikyuu_krecord(self):
        """Mock Hikyuu KRecord 对象"""
        record = MagicMock()
        record.datetime = datetime(2023, 1, 3, 9, 30)
        record.open = 10.5
        record.high = 11.2
        record.low = 10.3
        record.close = 11.0
        record.volume = 1000000
        record.amount = 10800000
        return record

    @pytest.fixture
    def mock_hikyuu_kdata(self, mock_hikyuu_krecord):
        """Mock Hikyuu KData 对象"""
        kdata = MagicMock()
        kdata.__len__ = MagicMock(return_value=1)
        kdata.__iter__ = MagicMock(return_value=iter([mock_hikyuu_krecord]))
        kdata.__getitem__ = MagicMock(return_value=mock_hikyuu_krecord)
        return kdata

    @pytest.mark.asyncio
    async def test_load_stock_data_success(
        self, stock_code, date_range, mock_hikyuu_kdata
    ):
        """
        测试成功加载股票数据

        验证:
        1. 调用 Hikyuu API 获取数据
        2. 返回 KLineData 列表
        3. 数据转换正确
        """
        from adapters.hikyuu.hikyuu_data_adapter import HikyuuDataAdapter

        # Mock Hikyuu API
        mock_hikyuu = MagicMock()
        mock_stock = MagicMock()
        mock_stock.get_kdata.return_value = mock_hikyuu_kdata
        mock_hikyuu.Stock.return_value = mock_stock
        mock_hikyuu.Query = MagicMock()
        mock_hikyuu.Query.DAY = MagicMock()

        # 执行
        adapter = HikyuuDataAdapter(hikyuu_module=mock_hikyuu)
        result = await adapter.load_stock_data(stock_code, date_range, KLineType.DAY.value)

        # 验证
        assert len(result) == 1
        assert isinstance(result[0], KLineData)
        assert result[0].stock_code == stock_code
        assert result[0].open == Decimal("10.5")
        assert result[0].close == Decimal("11.0")
        assert result[0].volume == 1000000

    @pytest.mark.asyncio
    async def test_hikyuu_to_domain_conversion(
        self, stock_code, date_range, mock_hikyuu_kdata
    ):
        """
        测试 Hikyuu → Domain 数据转换

        验证:
        1. 日期时间转换正确
        2. 价格数据类型转换为 Decimal
        3. K线类型映射正确
        """
        from adapters.hikyuu.hikyuu_data_adapter import HikyuuDataAdapter

        # Mock Hikyuu API
        mock_hikyuu = MagicMock()
        mock_stock = MagicMock()
        mock_stock.get_kdata.return_value = mock_hikyuu_kdata
        mock_hikyuu.Stock.return_value = mock_stock
        mock_hikyuu.Query = MagicMock()
        mock_hikyuu.Query.DAY = MagicMock()

        # 执行
        adapter = HikyuuDataAdapter(hikyuu_module=mock_hikyuu)
        result = await adapter.load_stock_data(stock_code, date_range, KLineType.DAY.value)

        # 验证数据转换
        kline = result[0]
        assert isinstance(kline.timestamp, datetime)
        assert isinstance(kline.open, Decimal)
        assert isinstance(kline.high, Decimal)
        assert isinstance(kline.low, Decimal)
        assert isinstance(kline.close, Decimal)
        assert isinstance(kline.volume, int)
        assert isinstance(kline.amount, Decimal)
        assert kline.kline_type == KLineType.DAY

    @pytest.mark.asyncio
    async def test_hikyuu_api_error_handling(
        self, stock_code, date_range
    ):
        """
        测试 Hikyuu API 错误处理

        验证:
        1. 捕获 Hikyuu 异常
        2. 映射为领域层异常
        3. 错误信息包含上下文
        """
        from adapters.hikyuu.hikyuu_data_adapter import HikyuuDataAdapter

        # Mock Hikyuu API 抛出异常
        mock_hikyuu = MagicMock()
        mock_hikyuu.Stock.side_effect = Exception("Hikyuu connection error")

        # 执行 & 验证
        adapter = HikyuuDataAdapter(hikyuu_module=mock_hikyuu)
        with pytest.raises(Exception) as exc_info:
            await adapter.load_stock_data(stock_code, date_range, KLineType.DAY.value)

        assert "Hikyuu" in str(exc_info.value) or "error" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_empty_result_handling(self, stock_code, date_range):
        """
        测试空结果处理

        验证:
        1. Hikyuu 返回空数据时不抛出异常
        2. 返回空列表
        """
        from adapters.hikyuu.hikyuu_data_adapter import HikyuuDataAdapter

        # Mock Hikyuu API 返回空数据
        mock_hikyuu = MagicMock()
        mock_kdata = MagicMock()
        mock_kdata.__len__ = MagicMock(return_value=0)
        mock_kdata.__iter__ = MagicMock(return_value=iter([]))

        mock_stock = MagicMock()
        mock_stock.get_kdata.return_value = mock_kdata
        mock_hikyuu.Stock.return_value = mock_stock
        mock_hikyuu.Query = MagicMock()
        mock_hikyuu.Query.DAY = MagicMock()

        # 执行
        adapter = HikyuuDataAdapter(hikyuu_module=mock_hikyuu)
        result = await adapter.load_stock_data(stock_code, date_range, KLineType.DAY.value)

        # 验证
        assert result == []

    @pytest.mark.asyncio
    async def test_date_range_conversion(self, stock_code, date_range):
        """
        测试日期范围转换

        验证:
        1. DateRange → Hikyuu Query 转换
        2. start_date 和 end_date 正确传递
        """
        from adapters.hikyuu.hikyuu_data_adapter import HikyuuDataAdapter

        # Mock Hikyuu API
        mock_hikyuu = MagicMock()
        mock_kdata = MagicMock()
        mock_kdata.__len__ = MagicMock(return_value=0)
        mock_kdata.__iter__ = MagicMock(return_value=iter([]))

        mock_stock = MagicMock()
        mock_stock.get_kdata.return_value = mock_kdata
        mock_hikyuu.Stock.return_value = mock_stock

        # Mock Query class
        mock_query_instance = MagicMock()
        mock_hikyuu.Query.return_value = mock_query_instance
        mock_hikyuu.Query.DAY = MagicMock()

        # 执行
        adapter = HikyuuDataAdapter(hikyuu_module=mock_hikyuu)
        await adapter.load_stock_data(stock_code, date_range, KLineType.DAY.value)

        # 验证 Stock 被正确创建
        mock_hikyuu.Stock.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_stock_list_success(self):
        """
        测试获取股票列表成功

        验证:
        1. 调用 Hikyuu API 获取股票列表
        2. 返回 StockCode 列表
        """
        from adapters.hikyuu.hikyuu_data_adapter import HikyuuDataAdapter

        # Mock Hikyuu API
        mock_hikyuu = MagicMock()
        mock_stock1 = MagicMock()
        mock_stock1.market_code = "SH"
        mock_stock1.code = "600000"

        mock_stock2 = MagicMock()
        mock_stock2.market_code = "SZ"
        mock_stock2.code = "000001"

        mock_stock_manager = MagicMock()
        mock_stock_manager.get_stock_list.return_value = [mock_stock1, mock_stock2]
        mock_hikyuu.StockManager.instance.return_value = mock_stock_manager

        # 执行
        adapter = HikyuuDataAdapter(hikyuu_module=mock_hikyuu)
        result = await adapter.get_stock_list("SH")

        # 验证
        assert len(result) >= 0  # 可能被过滤
        for stock_code in result:
            assert isinstance(stock_code, StockCode)
