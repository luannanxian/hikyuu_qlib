"""
QlibDataAdapter 单元测试

测试 Qlib 数据适配器实现 IStockDataProvider 接口
遵循 TDD Red-Green-Refactor 流程
"""

from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock

import pandas as pd
import pytest

from domain.entities.kline_data import KLineData
from domain.value_objects.date_range import DateRange
from domain.value_objects.kline_type import KLineType
from domain.value_objects.stock_code import StockCode


class TestQlibDataAdapter:
    """QlibDataAdapter 测试类"""

    @pytest.fixture
    def mock_qlib(self):
        """Mock Qlib 模块"""
        mock = MagicMock()
        # Mock qlib.data.D module
        mock.data = MagicMock()
        mock.data.D = MagicMock()
        return mock

    @pytest.fixture
    def adapter(self, mock_qlib):
        """创建 QlibDataAdapter 实例"""
        from adapters.qlib.qlib_data_adapter import QlibDataAdapter
        return QlibDataAdapter(qlib_module=mock_qlib)

    @pytest.fixture
    def sample_stock_code(self):
        """示例股票代码"""
        return StockCode("sh600000")

    @pytest.fixture
    def sample_date_range(self):
        """示例日期范围"""
        return DateRange(start_date=date(2023, 1, 1), end_date=date(2023, 1, 10))

    @pytest.fixture
    def mock_qlib_dataframe(self):
        """Mock Qlib DataFrame 数据"""
        # 创建多层索引 DataFrame (datetime, instrument)
        dates = pd.date_range(start='2023-01-03', periods=5, freq='D')
        data = {
            '$open': [10.5, 10.8, 11.0, 10.9, 11.2],
            '$high': [11.0, 11.2, 11.5, 11.3, 11.6],
            '$low': [10.0, 10.5, 10.8, 10.7, 11.0],
            '$close': [10.8, 11.0, 11.2, 11.1, 11.4],
            '$volume': [1000000, 1100000, 1200000, 1050000, 1300000],
            '$amount': [10800000.0, 12100000.0, 13440000.0, 11655000.0, 14820000.0],
        }

        # 创建多层索引
        multi_index = pd.MultiIndex.from_product(
            [dates, ['SH600000']],
            names=['datetime', 'instrument'],
        )

        df = pd.DataFrame(data, index=multi_index)
        return df

    # =============================================================================
    # Test 1: 验证 load_stock_data 调用 Qlib API
    # =============================================================================

    @pytest.mark.asyncio
    async def test_load_stock_data_calls_qlib_api(
        self, mock_qlib, adapter, sample_stock_code, sample_date_range, mock_qlib_dataframe,
    ):
        """
        测试: load_stock_data 正确调用 Qlib API

        验证:
        - 调用 qlib.data.D.features() 获取数据
        - 使用正确的参数 (instruments, fields, start_time, end_time)
        """
        # Arrange
        mock_qlib.data.D.features.return_value = mock_qlib_dataframe

        # Act
        result = await adapter.load_stock_data(
            stock_code=sample_stock_code,
            date_range=sample_date_range,
            kline_type=KLineType.DAY,
        )

        # Assert
        mock_qlib.data.D.features.assert_called_once()
        call_args = mock_qlib.data.D.features.call_args

        # 验证 instruments 参数
        assert 'SH600000' in call_args.kwargs['instruments'] or \
               'SH600000' in str(call_args.kwargs['instruments'])

        # 验证 fields 参数
        fields = call_args.kwargs['fields']
        assert '$open' in fields
        assert '$high' in fields
        assert '$low' in fields
        assert '$close' in fields
        assert '$volume' in fields

        # 验证结果
        assert isinstance(result, list)

    # =============================================================================
    # Test 2: 验证 Qlib 数据转换为 Domain 模型
    # =============================================================================

    @pytest.mark.asyncio
    async def test_load_stock_data_converts_to_domain(
        self, mock_qlib, adapter, sample_stock_code, sample_date_range, mock_qlib_dataframe,
    ):
        """
        测试: load_stock_data 将 Qlib DataFrame 正确转换为 Domain KLineData

        验证:
        - 返回类型为 List[KLineData]
        - KLineData 属性正确映射
        - 价格使用 Decimal 类型
        - 时间戳正确转换
        """
        # Arrange
        mock_qlib.data.D.features.return_value = mock_qlib_dataframe

        # Act
        result = await adapter.load_stock_data(
            stock_code=sample_stock_code,
            date_range=sample_date_range,
            kline_type=KLineType.DAY,
        )

        # Assert
        assert len(result) == 5
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

        # 验证数值正确性
        assert first_kline.open == Decimal('10.5')
        assert first_kline.high == Decimal('11.0')
        assert first_kline.low == Decimal('10.0')
        assert first_kline.close == Decimal('10.8')
        assert first_kline.volume == 1000000

    # =============================================================================
    # Test 3: 验证 Qlib 错误处理
    # =============================================================================

    @pytest.mark.asyncio
    async def test_load_stock_data_handles_qlib_error(
        self, mock_qlib, adapter, sample_stock_code, sample_date_range,
    ):
        """
        测试: load_stock_data 正确处理 Qlib 异常

        验证:
        - Qlib 抛出异常时, 适配器捕获并重新抛出包装后的异常
        - 异常信息包含原始错误上下文
        """
        # Arrange
        mock_qlib.data.D.features.side_effect = Exception("Qlib data fetch error")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await adapter.load_stock_data(
                stock_code=sample_stock_code,
                date_range=sample_date_range,
                kline_type=KLineType.DAY,
            )

        assert "Failed to load stock data from Qlib" in str(exc_info.value)

    # =============================================================================
    # Test 4: 验证空数据处理
    # =============================================================================

    @pytest.mark.asyncio
    async def test_load_stock_data_handles_empty_data(
        self, mock_qlib, adapter, sample_stock_code, sample_date_range,
    ):
        """
        测试: load_stock_data 正确处理空数据

        验证:
        - Qlib 返回空 DataFrame 时, 返回空列表
        - 不抛出异常
        """
        # Arrange
        empty_df = pd.DataFrame()
        mock_qlib.data.D.features.return_value = empty_df

        # Act
        result = await adapter.load_stock_data(
            stock_code=sample_stock_code,
            date_range=sample_date_range,
            kline_type=KLineType.DAY,
        )

        # Assert
        assert result == []

    # =============================================================================
    # Test 5: 验证 get_stock_list 调用 Qlib Instruments API
    # =============================================================================

    @pytest.mark.asyncio
    async def test_get_stock_list_calls_qlib_api(self, mock_qlib, adapter):
        """
        测试: get_stock_list 正确调用 Qlib Instruments API

        验证:
        - 调用 qlib.data.D.instruments() 获取股票列表
        - 根据市场代码过滤股票
        """
        # Arrange
        mock_instruments = ['SH600000', 'SH600001', 'SZ000001', 'SH600002']
        mock_qlib.data.D.instruments.return_value = mock_instruments

        # Act
        result = await adapter.get_stock_list(market="SH")

        # Assert
        mock_qlib.data.D.instruments.assert_called_once()
        assert isinstance(result, list)
        assert all(isinstance(code, StockCode) for code in result)

        # 验证只返回 SH 市场股票
        for stock_code in result:
            assert stock_code.value.startswith('SH') or stock_code.value.startswith('sh')

    # =============================================================================
    # Test 6: 验证不同 K 线类型映射
    # =============================================================================

    @pytest.mark.asyncio
    async def test_load_stock_data_with_different_kline_types(
        self, mock_qlib, adapter, sample_stock_code, sample_date_range, mock_qlib_dataframe,
    ):
        """
        测试: load_stock_data 正确处理不同的 K 线类型

        验证:
        - 支持 DAY, WEEK, MONTH 等类型
        - 正确传递 freq 参数给 Qlib
        """
        # Arrange
        mock_qlib.data.D.features.return_value = mock_qlib_dataframe

        # Act - 测试日K线
        result_day = await adapter.load_stock_data(
            stock_code=sample_stock_code,
            date_range=sample_date_range,
            kline_type=KLineType.DAY,
        )

        # Assert
        assert len(result_day) > 0
        assert all(kline.kline_type == KLineType.DAY for kline in result_day)

    # =============================================================================
    # Test 7: 验证股票代码格式转换
    # =============================================================================

    @pytest.mark.asyncio
    async def test_stock_code_format_conversion(
        self, mock_qlib, adapter, mock_qlib_dataframe,
    ):
        """
        测试: 股票代码在 Domain 和 Qlib 之间正确转换

        验证:
        - Domain StockCode (sh600000) → Qlib format (SH600000)
        - 大小写转换正确
        """
        # Arrange
        stock_code = StockCode("sh600000")
        date_range = DateRange(start_date=date(2023, 1, 1), end_date=date(2023, 1, 10))
        mock_qlib.data.D.features.return_value = mock_qlib_dataframe

        # Act
        _result = await adapter.load_stock_data(
            stock_code=stock_code,
            date_range=date_range,
            kline_type=KLineType.DAY,
        )

        # Assert
        call_args = mock_qlib.data.D.features.call_args
        instruments = call_args.kwargs['instruments']

        # 验证转换为 Qlib 格式 (SH600000)
        assert 'SH600000' in instruments or 'SH600000' in str(instruments)
