"""
LoadStockDataUseCase 单元测试

测试 UC-001: Load Stock Data (加载股票数据) 用例
"""

import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock

from domain.entities.kline_data import KLineData
from domain.ports.stock_data_provider import IStockDataProvider
from domain.value_objects.date_range import DateRange
from domain.value_objects.kline_type import KLineType
from domain.value_objects.stock_code import StockCode
from use_cases.data.load_stock_data import LoadStockDataUseCase


class TestLoadStockDataSuccess:
    """测试成功加载股票数据"""

    @pytest.mark.asyncio
    async def test_load_stock_data_success(self):
        """测试成功加载股票数据"""
        # Arrange: 准备 Mock Provider
        provider_mock = AsyncMock(spec=IStockDataProvider)

        # Mock 返回数据
        mock_kline = KLineData(
            stock_code=StockCode("sh600000"),
            timestamp=datetime(2024, 1, 10),
            kline_type=KLineType.DAY,
            open=Decimal("10.00"),
            high=Decimal("10.50"),
            low=Decimal("9.90"),
            close=Decimal("10.20"),
            volume=1000000,
            amount=Decimal("10200000"),
        )
        provider_mock.load_stock_data.return_value = [mock_kline]

        # 创建 Use Case
        use_case = LoadStockDataUseCase(provider=provider_mock)

        # Act: 执行用例
        stock_code = StockCode("sh600000")
        date_range = DateRange(
            start_date=datetime(2024, 1, 1), end_date=datetime(2024, 1, 31)
        )
        kline_type = KLineType.DAY

        result = await use_case.execute(
            stock_code=stock_code, date_range=date_range, kline_type=kline_type
        )

        # Assert: 验证结果
        assert len(result) == 1
        assert result[0].stock_code == StockCode("sh600000")
        assert result[0].close == Decimal("10.20")

        # 验证 provider 被正确调用
        provider_mock.load_stock_data.assert_called_once_with(
            stock_code=stock_code, date_range=date_range, kline_type=kline_type
        )


class TestLoadStockDataValidation:
    """测试输入验证"""

    @pytest.mark.asyncio
    async def test_load_stock_data_invalid_stock_code(self):
        """测试无效股票代码抛出异常"""
        # Act & Assert: 无效股票代码应该在创建 StockCode 时抛出异常
        with pytest.raises(ValueError, match="Invalid stock code"):
            StockCode("invalid")  # 不足8个字符

    @pytest.mark.asyncio
    async def test_load_stock_data_invalid_date_range(self):
        """测试无效日期范围抛出异常"""
        # Act & Assert: 开始日期 > 结束日期应该抛出异常
        with pytest.raises(ValueError, match="start_date must be <= end_date"):
            DateRange(start_date=datetime(2024, 2, 1), end_date=datetime(2024, 1, 1))


class TestLoadStockDataErrorHandling:
    """测试错误处理"""

    @pytest.mark.asyncio
    async def test_load_stock_data_provider_error(self):
        """测试数据源错误处理"""
        # Arrange: Mock provider 抛出异常
        provider_mock = AsyncMock(spec=IStockDataProvider)
        provider_mock.load_stock_data.side_effect = Exception("数据源连接失败")

        use_case = LoadStockDataUseCase(provider=provider_mock)

        # Act & Assert: 应该传播异常
        stock_code = StockCode("sh600000")
        date_range = DateRange(
            start_date=datetime(2024, 1, 1), end_date=datetime(2024, 1, 31)
        )
        kline_type = KLineType.DAY

        with pytest.raises(Exception, match="数据源连接失败"):
            await use_case.execute(
                stock_code=stock_code, date_range=date_range, kline_type=kline_type
            )

    @pytest.mark.asyncio
    async def test_load_stock_data_empty_result(self):
        """测试空结果情况"""
        # Arrange: Mock provider 返回空列表
        provider_mock = AsyncMock(spec=IStockDataProvider)
        provider_mock.load_stock_data.return_value = []

        use_case = LoadStockDataUseCase(provider=provider_mock)

        # Act
        stock_code = StockCode("sh600000")
        date_range = DateRange(
            start_date=datetime(2024, 1, 1), end_date=datetime(2024, 1, 31)
        )
        kline_type = KLineType.DAY

        result = await use_case.execute(
            stock_code=stock_code, date_range=date_range, kline_type=kline_type
        )

        # Assert: 空结果也是有效的
        assert result == []
        assert len(result) == 0
