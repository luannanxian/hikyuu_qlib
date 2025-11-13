"""
HikyuuDataAdapter 单元测试

测试 Hikyuu 数据适配器实现 IStockDataProvider 接口
遵循 TDD Red-Green-Refactor 流程
"""

from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock
from typing import List

import pytest

from domain.value_objects.stock_code import StockCode
from domain.value_objects.date_range import DateRange
from domain.value_objects.kline_type import KLineType
from domain.entities.kline_data import KLineData


class TestHikyuuDataAdapter:
    """HikyuuDataAdapter 测试类"""

    @pytest.fixture
    def mock_hku(self):
        """Mock Hikyuu 模块"""
        mock = MagicMock()
        # Mock Query 常量
        mock.Query.DAY = 0
        mock.Query.WEEK = 1
        mock.Query.MONTH = 2
        mock.Query.MIN = 3
        mock.Query.MIN5 = 4
        return mock

    @pytest.fixture
    def adapter(self, mock_hku):
        """创建 HikyuuDataAdapter 实例"""
        from adapters.hikyuu.hikyuu_data_adapter import HikyuuDataAdapter
        return HikyuuDataAdapter(hikyuu_module=mock_hku)

    @pytest.fixture
    def sample_stock_code(self):
        """示例股票代码"""
        return StockCode("sh600000")

    @pytest.fixture
    def sample_date_range(self):
        """示例日期范围"""
        return DateRange(start_date=date(2023, 1, 1), end_date=date(2023, 1, 10))

    @pytest.fixture
    def mock_hikyuu_krecord(self):
        """Mock Hikyuu KRecord 对象"""
        record = MagicMock()
        record.datetime = datetime(2023, 1, 3, 0, 0, 0)
        record.openPrice = 10.5
        record.highPrice = 11.0
        record.lowPrice = 10.0
        record.closePrice = 10.8
        record.volume = 1000000
        record.amount = 10800000.0
        return record

    @pytest.fixture
    def mock_hikyuu_stock(self, mock_hikyuu_krecord):
        """Mock Hikyuu Stock 对象"""
        stock = MagicMock()

        # Mock get_kdata 返回 KData 列表
        kdata = MagicMock()
        kdata.__len__ = MagicMock(return_value=10)
        kdata.__getitem__ = MagicMock(return_value=mock_hikyuu_krecord)
        kdata.__iter__ = MagicMock(return_value=iter([mock_hikyuu_krecord] * 10))

        stock.get_kdata.return_value = kdata
        return stock

    # =============================================================================
    # Test 1: 验证 load_stock_data 调用 Hikyuu API
    # =============================================================================

    @pytest.mark.asyncio
    async def test_load_stock_data_calls_hikyuu_api(
        self, mock_hku, adapter, sample_stock_code, sample_date_range, mock_hikyuu_stock
    ):
        """
        测试: load_stock_data 正确调用 Hikyuu API

        验证:
        - 调用 StockManager.get_stock() 获取股票对象
        - 调用 stock.get_kdata() 获取 K线数据
        - 使用正确的参数 (股票代码, Query对象)
        """
        # Arrange
        mock_stock_manager = MagicMock()
        mock_stock_manager.get_stock.return_value = mock_hikyuu_stock
        mock_hku.StockManager.instance.return_value = mock_stock_manager

        mock_query = MagicMock()
        mock_hku.Query.return_value = mock_query
        mock_hku.Datetime.return_value = MagicMock()

        # Act
        result = await adapter.load_stock_data(
            stock_code=sample_stock_code,
            date_range=sample_date_range,
            kline_type=KLineType.DAY
        )

        # Assert
        mock_stock_manager.get_stock.assert_called_once_with("sh600000")
        mock_hikyuu_stock.get_kdata.assert_called_once()
        assert isinstance(result, list)

    # =============================================================================
    # Test 2: 验证 Hikyuu 数据转换为 Domain 模型
    # =============================================================================

    @pytest.mark.asyncio
    async def test_load_stock_data_converts_to_domain(
        self, mock_hku, adapter, sample_stock_code, sample_date_range, mock_hikyuu_stock
    ):
        """
        测试: load_stock_data 将 Hikyuu 数据正确转换为 Domain KLineData

        验证:
        - 返回类型为 List[KLineData]
        - KLineData 属性正确映射
        - 价格使用 Decimal 类型
        - 时间戳正确转换
        """
        # Arrange
        mock_stock_manager = MagicMock()
        mock_stock_manager.get_stock.return_value = mock_hikyuu_stock
        mock_hku.StockManager.instance.return_value = mock_stock_manager

        mock_query = MagicMock()
        mock_hku.Query.return_value = mock_query
        mock_hku.Datetime.return_value = MagicMock()

        # Act
        result = await adapter.load_stock_data(
            stock_code=sample_stock_code,
            date_range=sample_date_range,
            kline_type=KLineType.DAY
        )

        # Assert
        assert len(result) == 10
        assert all(isinstance(kline, KLineData) for kline in result)

        # 验证第一条数据
        first_kline = result[0]
        assert first_kline.stock_code == sample_stock_code
        assert first_kline.kline_type == KLineType.DAY
        assert isinstance(first_kline.open, Decimal)
        assert isinstance(first_kline.high, Decimal)
        assert isinstance(first_kline.low, Decimal)
        assert isinstance(first_kline.close, Decimal)
        assert isinstance(first_kline.timestamp, datetime)

    # =============================================================================
    # Test 3: 验证 Hikyuu 错误处理
    # =============================================================================

    @pytest.mark.asyncio
    async def test_load_stock_data_handles_hikyuu_error(
        self, mock_hku, adapter, sample_stock_code, sample_date_range
    ):
        """
        测试: load_stock_data 正确处理 Hikyuu 异常

        验证:
        - Hikyuu 抛出异常时, 适配器捕获并重新抛出包装后的异常
        - 异常信息包含原始错误上下文
        """
        # Arrange
        mock_stock_manager = MagicMock()
        mock_stock_manager.get_stock.side_effect = Exception("Hikyuu connection error")
        mock_hku.StockManager.instance.return_value = mock_stock_manager

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await adapter.load_stock_data(
                stock_code=sample_stock_code,
                date_range=sample_date_range,
                kline_type=KLineType.DAY
            )

        assert "Failed to load stock data from Hikyuu" in str(exc_info.value)

    # =============================================================================
    # Test 4: 验证空数据处理
    # =============================================================================

    @pytest.mark.asyncio
    async def test_load_stock_data_handles_empty_data(
        self, mock_hku, adapter, sample_stock_code, sample_date_range
    ):
        """
        测试: load_stock_data 正确处理空数据

        验证:
        - Hikyuu 返回空数据时, 返回空列表
        - 不抛出异常
        """
        # Arrange
        mock_stock = MagicMock()
        empty_kdata = MagicMock()
        empty_kdata.__len__ = MagicMock(return_value=0)
        empty_kdata.__iter__ = MagicMock(return_value=iter([]))
        mock_stock.get_kdata.return_value = empty_kdata

        mock_stock_manager = MagicMock()
        mock_stock_manager.get_stock.return_value = mock_stock
        mock_hku.StockManager.instance.return_value = mock_stock_manager

        mock_query = MagicMock()
        mock_hku.Query.return_value = mock_query
        mock_hku.Datetime.return_value = MagicMock()

        # Act
        result = await adapter.load_stock_data(
            stock_code=sample_stock_code,
            date_range=sample_date_range,
            kline_type=KLineType.DAY
        )

        # Assert
        assert result == []

    # =============================================================================
    # Test 5: 验证 get_stock_list 调用 Hikyuu StockManager
    # =============================================================================

    @pytest.mark.asyncio
    async def test_get_stock_list_calls_stock_manager(self, mock_hku, adapter):
        """
        测试: get_stock_list 正确调用 Hikyuu StockManager

        验证:
        - 调用 hku.StockManager.instance() 获取管理器
        - 调用相关方法获取股票列表
        - 根据市场代码过滤股票
        """
        # Arrange
        mock_sm = MagicMock()
        mock_hku.StockManager.instance.return_value = mock_sm

        # Mock 股票列表
        mock_stock1 = MagicMock()
        mock_stock1.market_code = "SH"
        mock_stock1.code = "600000"

        mock_stock2 = MagicMock()
        mock_stock2.market_code = "SH"
        mock_stock2.code = "600001"

        mock_sm.__iter__ = MagicMock(return_value=iter([mock_stock1, mock_stock2]))

        # Act
        result = await adapter.get_stock_list(market="SH")

        # Assert
        mock_hku.StockManager.instance.assert_called_once()
        assert isinstance(result, list)
        assert all(isinstance(code, StockCode) for code in result)
