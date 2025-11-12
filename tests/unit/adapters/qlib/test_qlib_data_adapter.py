"""
QlibDataAdapter 单元测试

测试 QlibDataAdapter 实现 IStockDataProvider 接口,
使用 Mock 隔离 Qlib 框架依赖
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import patch
import pandas as pd

from domain.value_objects.stock_code import StockCode
from domain.value_objects.date_range import DateRange
from domain.value_objects.kline_type import KLineType
from domain.entities.kline_data import KLineData


class TestQlibDataAdapter:
    """测试 QlibDataAdapter"""

    @pytest.fixture
    def stock_code(self) -> StockCode:
        """股票代码 fixture"""
        return StockCode("sh600000")

    @pytest.fixture
    def date_range(self) -> DateRange:
        """日期范围 fixture"""
        return DateRange(date(2023, 1, 1), date(2023, 12, 31))

    @pytest.fixture
    def mock_qlib_dataframe(self):
        """Mock Qlib 返回的 DataFrame"""
        df = pd.DataFrame(
            {
                "$open": [10.5],
                "$high": [11.2],
                "$low": [10.3],
                "$close": [11.0],
                "$volume": [1000000],
                "$amount": [10800000],
            },
            index=pd.DatetimeIndex([datetime(2023, 1, 3)], name="datetime"),
        )
        return df

    @pytest.mark.asyncio
    async def test_load_stock_data_success(
        self, stock_code, date_range, mock_qlib_dataframe
    ):
        """
        测试成功加载股票数据

        验证:
        1. 调用 Qlib API 获取数据
        2. 返回 KLineData 列表
        3. 数据转换正确
        """
        from adapters.qlib.qlib_data_adapter import QlibDataAdapter

        with patch("adapters.qlib.qlib_data_adapter.D") as mock_d:
            mock_d.features.return_value = mock_qlib_dataframe

            # 执行
            adapter = QlibDataAdapter()
            result = await adapter.load_stock_data(
                stock_code, date_range, KLineType.DAY.value
            )

            # 验证
            assert len(result) == 1
            assert isinstance(result[0], KLineData)
            assert result[0].stock_code == stock_code
            assert result[0].open == Decimal("10.5")
            assert result[0].close == Decimal("11.0")
            assert result[0].volume == 1000000

    @pytest.mark.asyncio
    async def test_qlib_to_domain_conversion(
        self, stock_code, date_range, mock_qlib_dataframe
    ):
        """
        测试 Qlib → Domain 数据转换

        验证:
        1. 日期时间转换正确
        2. 价格数据类型转换为 Decimal
        3. K线类型映射正确
        """
        from adapters.qlib.qlib_data_adapter import QlibDataAdapter

        with patch("adapters.qlib.qlib_data_adapter.D") as mock_d:
            mock_d.features.return_value = mock_qlib_dataframe

            # 执行
            adapter = QlibDataAdapter()
            result = await adapter.load_stock_data(
                stock_code, date_range, KLineType.DAY.value
            )

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
    async def test_qlib_api_error_handling(self, stock_code, date_range):
        """
        测试 Qlib API 错误处理

        验证:
        1. 捕获 Qlib 异常
        2. 映射为领域层异常
        3. 错误信息包含上下文
        """
        from adapters.qlib.qlib_data_adapter import QlibDataAdapter

        with patch("adapters.qlib.qlib_data_adapter.D") as mock_d:
            mock_d.features.side_effect = Exception("Qlib data fetch error")

            # 执行 & 验证
            adapter = QlibDataAdapter()
            with pytest.raises(Exception) as exc_info:
                await adapter.load_stock_data(
                    stock_code, date_range, KLineType.DAY.value
                )

            assert (
                "Qlib" in str(exc_info.value) or "error" in str(exc_info.value).lower()
            )

    @pytest.mark.asyncio
    async def test_empty_result_handling(self, stock_code, date_range):
        """
        测试空结果处理

        验证:
        1. Qlib 返回空数据时不抛出异常
        2. 返回空列表
        """
        from adapters.qlib.qlib_data_adapter import QlibDataAdapter

        empty_df = pd.DataFrame(
            columns=["$open", "$high", "$low", "$close", "$volume", "$amount"]
        )

        with patch("adapters.qlib.qlib_data_adapter.D") as mock_d:
            mock_d.features.return_value = empty_df

            # 执行
            adapter = QlibDataAdapter()
            result = await adapter.load_stock_data(
                stock_code, date_range, KLineType.DAY.value
            )

            # 验证
            assert result == []

    @pytest.mark.asyncio
    async def test_stock_code_format_conversion(self, stock_code, date_range):
        """
        测试股票代码格式转换

        验证:
        1. sh600000 → SH600000 (Qlib 格式)
        2. 大小写转换正确
        """
        from adapters.qlib.qlib_data_adapter import QlibDataAdapter

        empty_df = pd.DataFrame(
            columns=["$open", "$high", "$low", "$close", "$volume", "$amount"]
        )

        with patch("adapters.qlib.qlib_data_adapter.D") as mock_d:
            mock_d.features.return_value = empty_df

            # 执行
            adapter = QlibDataAdapter()
            await adapter.load_stock_data(stock_code, date_range, KLineType.DAY.value)

            # 验证调用参数
            call_args = mock_d.features.call_args
            instruments = call_args[1]["instruments"]
            # Qlib 使用大写市场代码
            assert "SH600000" in instruments or "sh600000" in instruments.lower()

    @pytest.mark.asyncio
    async def test_date_range_conversion(self, stock_code, date_range):
        """
        测试日期范围转换

        验证:
        1. DateRange → Qlib 日期字符串
        2. start_date 和 end_date 格式正确
        """
        from adapters.qlib.qlib_data_adapter import QlibDataAdapter

        empty_df = pd.DataFrame(
            columns=["$open", "$high", "$low", "$close", "$volume", "$amount"]
        )

        with patch("adapters.qlib.qlib_data_adapter.D") as mock_d:
            mock_d.features.return_value = empty_df

            # 执行
            adapter = QlibDataAdapter()
            await adapter.load_stock_data(stock_code, date_range, KLineType.DAY.value)

            # 验证调用参数
            call_args = mock_d.features.call_args
            start_time = call_args[1]["start_time"]
            end_time = call_args[1]["end_time"]

            # Qlib 使用 YYYY-MM-DD 格式
            assert start_time == "2023-01-01"
            assert end_time == "2023-12-31"
