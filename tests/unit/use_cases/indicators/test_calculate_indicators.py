"""
CalculateIndicatorsUseCase 单元测试

测试 UC-006: Calculate Indicators (计算技术指标) 用例
"""

from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from domain.entities.kline_data import KLineData
from domain.ports.indicator_calculator import IIndicatorCalculator
from domain.value_objects.kline_type import KLineType
from domain.value_objects.stock_code import StockCode
from use_cases.indicators.calculate_indicators import CalculateIndicatorsUseCase


class TestCalculateIndicatorsSuccess:
    """测试成功计算技术指标"""

    @pytest.mark.asyncio
    async def test_calculate_indicators_success(self):
        """测试成功计算技术指标"""
        # Arrange: 准备 Mock Calculator
        calculator_mock = AsyncMock(spec=IIndicatorCalculator)

        # Mock 返回的指标数据
        mock_indicators = {
            "MA5": [10.0, 10.5, 11.0, 11.5, 12.0],
            "MA10": [9.5, 10.0, 10.5, 11.0, 11.5],
        }
        calculator_mock.calculate_indicators.return_value = mock_indicators

        # 创建 Use Case
        use_case = CalculateIndicatorsUseCase(calculator=calculator_mock)

        # 准备测试数据
        kline_data = [
            KLineData(
                stock_code=StockCode("sh600000"),
                timestamp=datetime(2024, 1, 10),
                kline_type=KLineType.DAY,
                open=Decimal("10.00"),
                high=Decimal("10.50"),
                low=Decimal("9.90"),
                close=Decimal("10.20"),
                volume=1000000,
                amount=Decimal(10200000),
            ),
            KLineData(
                stock_code=StockCode("sh600000"),
                timestamp=datetime(2024, 1, 11),
                kline_type=KLineType.DAY,
                open=Decimal("10.20"),
                high=Decimal("10.80"),
                low=Decimal("10.10"),
                close=Decimal("10.50"),
                volume=1200000,
                amount=Decimal(12600000),
            ),
        ]
        indicator_names = ["MA5", "MA10"]

        # Act: 执行用例
        result = await use_case.execute(
            kline_data=kline_data, indicator_names=indicator_names,
        )

        # Assert: 验证结果
        assert "MA5" in result
        assert "MA10" in result
        assert len(result["MA5"]) == 5
        assert result["MA5"][0] == 10.0

        # 验证 calculator 被正确调用
        calculator_mock.calculate_indicators.assert_called_once_with(
            kline_data=kline_data, indicator_names=indicator_names,
        )


class TestCalculateIndicatorsValidation:
    """测试输入验证"""

    @pytest.mark.asyncio
    async def test_calculate_indicators_invalid_kline_data(self):
        """测试无效K线数据抛出异常"""
        # Arrange
        calculator_mock = AsyncMock(spec=IIndicatorCalculator)
        use_case = CalculateIndicatorsUseCase(calculator=calculator_mock)

        # Act & Assert: 空K线数据应该抛出异常
        with pytest.raises(ValueError, match="kline_data cannot be empty"):
            await use_case.execute(kline_data=[], indicator_names=["MA5"])

    @pytest.mark.asyncio
    async def test_calculate_indicators_empty_indicator_names(self):
        """测试空指标名称列表抛出异常"""
        # Arrange
        calculator_mock = AsyncMock(spec=IIndicatorCalculator)
        use_case = CalculateIndicatorsUseCase(calculator=calculator_mock)

        kline_data = [
            KLineData(
                stock_code=StockCode("sh600000"),
                timestamp=datetime(2024, 1, 10),
                kline_type=KLineType.DAY,
                open=Decimal("10.00"),
                high=Decimal("10.50"),
                low=Decimal("9.90"),
                close=Decimal("10.20"),
                volume=1000000,
                amount=Decimal(10200000),
            ),
        ]

        # Act & Assert: 空指标名称应该抛出异常
        with pytest.raises(ValueError, match="indicator_names cannot be empty"):
            await use_case.execute(kline_data=kline_data, indicator_names=[])


class TestCalculateIndicatorsErrorHandling:
    """测试错误处理"""

    @pytest.mark.asyncio
    async def test_calculate_indicators_calculator_error(self):
        """测试计算器错误处理"""
        # Arrange: Mock calculator 抛出异常
        calculator_mock = AsyncMock(spec=IIndicatorCalculator)
        calculator_mock.calculate_indicators.side_effect = Exception("计算指标失败")

        use_case = CalculateIndicatorsUseCase(calculator=calculator_mock)

        kline_data = [
            KLineData(
                stock_code=StockCode("sh600000"),
                timestamp=datetime(2024, 1, 10),
                kline_type=KLineType.DAY,
                open=Decimal("10.00"),
                high=Decimal("10.50"),
                low=Decimal("9.90"),
                close=Decimal("10.20"),
                volume=1000000,
                amount=Decimal(10200000),
            ),
        ]

        # Act & Assert: 应该传播异常
        with pytest.raises(Exception, match="计算指标失败"):
            await use_case.execute(kline_data=kline_data, indicator_names=["MA5"])
