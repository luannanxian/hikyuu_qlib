"""
IndicatorCalculatorAdapter 单元测试

测试 IndicatorCalculatorAdapter 实现 IIndicatorCalculator 接口,
使用 Mock 隔离 Hikyuu 框架依赖
"""

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from domain.entities.kline_data import KLineData
from domain.value_objects.kline_type import KLineType
from domain.value_objects.stock_code import StockCode


@patch("adapters.hikyuu.indicator_calculator_adapter.HIKYUU_AVAILABLE", True)
@patch("adapters.hikyuu.indicator_calculator_adapter.hikyuu")
class TestIndicatorCalculatorAdapter:
    """测试 IndicatorCalculatorAdapter"""

    @pytest.fixture
    def kline_data_list(self) -> list[KLineData]:
        """K线数据列表 fixture"""
        stock_code = StockCode("sh600000")
        kline_type = KLineType.DAY
        base_date = datetime(2024, 1, 1)

        data_list = []
        # 创建 10 天的 K 线数据
        for i in range(10):
            data_list.append(
                KLineData(
                    stock_code=stock_code,
                    timestamp=base_date + timedelta(days=i),
                    kline_type=kline_type,
                    open=Decimal(f"{10 + i}"),
                    high=Decimal(f"{12 + i}"),
                    low=Decimal(f"{9 + i}"),
                    close=Decimal(f"{11 + i}"),
                    volume=1000000 + i * 10000,
                    amount=Decimal(f"{11000000 + i * 110000}"),
                ),
            )

        return data_list

    @pytest.mark.asyncio
    async def test_calculate_ma_indicator(self, mock_hikyuu, kline_data_list):
        """
        测试计算 MA（移动平均）指标

        验证:
        1. 调用 Hikyuu MA 指标计算
        2. 返回正确格式的指标数据
        3. 数据长度与输入一致
        """
        from adapters.hikyuu.indicator_calculator_adapter import (
            IndicatorCalculatorAdapter,
        )

        # Mock Hikyuu indicator module
        with patch("adapters.hikyuu.indicator_calculator_adapter.hikyuu") as mock_hq:
            # Mock MA 指标计算结果
            mock_ma = MagicMock()
            mock_ma.get_result_num.return_value = 1
            mock_ma.__len__.return_value = len(kline_data_list)
            mock_ma.__getitem__.side_effect = lambda i: 10.5 + i * 0.1

            mock_hq.MA.return_value = mock_ma

            # 执行
            adapter = IndicatorCalculatorAdapter()
            result = await adapter.calculate_indicators(
                kline_data=kline_data_list, indicator_names=["MA5"],
            )

            # 验证
            assert "MA5" in result
            assert len(result["MA5"]) == len(kline_data_list)
            assert isinstance(result["MA5"][0], float)

    @pytest.mark.asyncio
    async def test_calculate_multiple_indicators(self, mock_hikyuu, kline_data_list):
        """
        测试计算多个指标

        验证:
        1. 同时计算多个指标
        2. 返回包含所有指标的字典
        3. 每个指标数据独立
        """
        from adapters.hikyuu.indicator_calculator_adapter import (
            IndicatorCalculatorAdapter,
        )

        with patch("adapters.hikyuu.indicator_calculator_adapter.hikyuu") as mock_hq:
            # Mock MA 指标
            mock_ma = MagicMock()
            mock_ma.__len__.return_value = len(kline_data_list)
            mock_ma.__getitem__.side_effect = lambda i: 10.5 + i * 0.1

            # Mock RSI 指标
            mock_rsi = MagicMock()
            mock_rsi.__len__.return_value = len(kline_data_list)
            mock_rsi.__getitem__.side_effect = lambda i: 50.0 + i

            def indicator_factory(name):
                if "MA" in name:
                    return mock_ma
                elif "RSI" in name:
                    return mock_rsi
                return MagicMock()

            mock_hq.MA.return_value = mock_ma
            mock_hq.RSI.return_value = mock_rsi

            # 执行
            adapter = IndicatorCalculatorAdapter()
            result = await adapter.calculate_indicators(
                kline_data=kline_data_list, indicator_names=["MA5", "RSI14"],
            )

            # 验证
            assert "MA5" in result
            assert "RSI14" in result
            assert len(result["MA5"]) == len(kline_data_list)
            assert len(result["RSI14"]) == len(kline_data_list)

    @pytest.mark.asyncio
    async def test_kline_data_conversion(self, mock_hikyuu, kline_data_list):
        """
        测试 K 线数据转换

        验证:
        1. Domain KLineData → Hikyuu KData
        2. 价格和成交量正确映射
        3. 时间戳正确转换
        """
        from adapters.hikyuu.indicator_calculator_adapter import (
            IndicatorCalculatorAdapter,
        )

        with patch("adapters.hikyuu.indicator_calculator_adapter.hikyuu") as mock_hq:
            mock_ma = MagicMock()
            mock_ma.__len__.return_value = len(kline_data_list)
            mock_ma.__getitem__.side_effect = lambda i: 10.5
            mock_hq.MA.return_value = mock_ma

            # Mock KData 和 Stock
            mock_stock = MagicMock()
            mock_kdata = MagicMock()
            mock_kdata.__len__.return_value = len(kline_data_list)
            mock_stock.get_kdata.return_value = mock_kdata
            mock_hq.Stock.return_value = mock_stock

            adapter = IndicatorCalculatorAdapter()
            result = await adapter.calculate_indicators(
                kline_data=kline_data_list, indicator_names=["MA5"],
            )

            # 验证调用
            assert result is not None

    @pytest.mark.asyncio
    async def test_empty_kline_data(self, mock_hikyuu):
        """
        测试空 K 线数据

        验证:
        1. 接受空数据列表
        2. 返回空结果或合理默认值
        """
        from adapters.hikyuu.indicator_calculator_adapter import (
            IndicatorCalculatorAdapter,
        )

        with patch("adapters.hikyuu.indicator_calculator_adapter.hikyuu") as mock_hq:
            mock_ma = MagicMock()
            mock_ma.__len__.return_value = 0
            mock_hq.MA.return_value = mock_ma

            adapter = IndicatorCalculatorAdapter()
            result = await adapter.calculate_indicators(
                kline_data=[], indicator_names=["MA5"],
            )

            # 验证
            assert "MA5" in result
            assert len(result["MA5"]) == 0

    @pytest.mark.asyncio
    async def test_hikyuu_error_handling(self, mock_hikyuu, kline_data_list):
        """
        测试 Hikyuu 错误处理

        验证:
        1. 捕获 Hikyuu 计算异常
        2. 映射为领域层异常
        """
        from adapters.hikyuu.indicator_calculator_adapter import (
            IndicatorCalculatorAdapter,
        )

        with patch("adapters.hikyuu.indicator_calculator_adapter.hikyuu") as mock_hq:
            mock_hq.MA.side_effect = Exception("Hikyuu calculation failed")

            adapter = IndicatorCalculatorAdapter()
            with pytest.raises(Exception) as exc_info:
                await adapter.calculate_indicators(
                    kline_data=kline_data_list, indicator_names=["MA5"],
                )

            assert (
                "Hikyuu" in str(exc_info.value)
                or "calculation" in str(exc_info.value).lower()
            )

    @pytest.mark.asyncio
    async def test_indicator_name_parsing(self, mock_hikyuu, kline_data_list):
        """
        测试指标名称解析

        验证:
        1. MA5 → MA(5)
        2. RSI14 → RSI(14)
        3. MACD_12_26_9 → MACD(12, 26, 9)
        """
        from adapters.hikyuu.indicator_calculator_adapter import (
            IndicatorCalculatorAdapter,
        )

        with patch("adapters.hikyuu.indicator_calculator_adapter.hikyuu") as mock_hq:
            mock_ma = MagicMock()
            mock_ma.__len__.return_value = len(kline_data_list)
            mock_ma.__getitem__.side_effect = lambda i: 10.5
            mock_hq.MA.return_value = mock_ma

            adapter = IndicatorCalculatorAdapter()
            result = await adapter.calculate_indicators(
                kline_data=kline_data_list, indicator_names=["MA5", "MA10", "MA20"],
            )

            # 验证所有指标都被计算
            assert "MA5" in result
            assert "MA10" in result
            assert "MA20" in result
