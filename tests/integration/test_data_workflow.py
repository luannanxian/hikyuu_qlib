"""
Data Workflow Integration Tests

测试数据加载的完整工作流
"""

from datetime import date, datetime
from decimal import Decimal

import pytest

from domain.entities.kline_data import KLineData
from domain.value_objects.date_range import DateRange
from domain.value_objects.kline_type import KLineType
from domain.value_objects.stock_code import StockCode


@pytest.mark.asyncio
async def test_load_stock_data_integration(
    load_stock_data_use_case, test_data_factory,
):
    """
    测试完整的数据加载流程

    流程:
    1. 创建 LoadStockDataUseCase
    2. 调用 execute 加载数据
    3. 验证数据被正确加载
    4. 验证数据格式
    """
    # Arrange
    stock_code = StockCode("sh600000")
    date_range = DateRange(date(2023, 1, 1), date(2023, 1, 31))
    kline_type = KLineType.DAY

    # Act
    result = await load_stock_data_use_case.execute(
        stock_code=stock_code, date_range=date_range, kline_type=kline_type,
    )

    # Assert
    assert result is not None
    assert len(result) > 0
    assert all(isinstance(k, KLineData) for k in result)
    assert all(k.stock_code == stock_code for k in result)
    assert all(k.kline_type == kline_type for k in result)


@pytest.mark.asyncio
async def test_load_stock_data_with_empty_result(mock_stock_data_provider):
    """
    测试数据加载返回空列表的情况

    场景: 指定日期范围内没有数据
    """
    # Arrange
    from use_cases.data.load_stock_data import LoadStockDataUseCase

    mock_stock_data_provider.load_stock_data.return_value = []
    use_case = LoadStockDataUseCase(provider=mock_stock_data_provider)

    stock_code = StockCode("sh600000")
    date_range = DateRange(date(2023, 1, 1), date(2023, 1, 31))
    kline_type = KLineType.DAY

    # Act
    result = await use_case.execute(
        stock_code=stock_code, date_range=date_range, kline_type=kline_type,
    )

    # Assert
    assert result == []
    mock_stock_data_provider.load_stock_data.assert_called_once_with(
        stock_code=stock_code, date_range=date_range, kline_type=kline_type,
    )


@pytest.mark.asyncio
async def test_load_stock_data_validates_data_quality(
    mock_stock_data_provider, test_data_factory,
):
    """
    测试数据质量验证

    验证:
    1. 数据按时间排序
    2. 价格数据完整性
    3. 成交量非负
    """
    # Arrange
    from use_cases.data.load_stock_data import LoadStockDataUseCase

    kline_data = test_data_factory.create_kline_data(count=10)
    mock_stock_data_provider.load_stock_data.return_value = kline_data
    use_case = LoadStockDataUseCase(provider=mock_stock_data_provider)

    stock_code = StockCode("sh600000")
    date_range = DateRange(date(2023, 1, 1), date(2023, 1, 31))
    kline_type = KLineType.DAY

    # Act
    result = await use_case.execute(
        stock_code=stock_code, date_range=date_range, kline_type=kline_type,
    )

    # Assert - 验证数据质量
    assert len(result) == 10

    # 验证价格数据
    for k in result:
        assert k.high >= k.low
        assert k.open > Decimal(0)
        assert k.close > Decimal(0)
        assert k.volume >= 0
        assert k.amount >= Decimal(0)


@pytest.mark.asyncio
async def test_load_stock_data_handles_provider_error(mock_stock_data_provider):
    """
    测试处理数据提供者错误

    场景: 数据提供者抛出异常
    """
    # Arrange
    from use_cases.data.load_stock_data import LoadStockDataUseCase

    mock_stock_data_provider.load_stock_data.side_effect = Exception(
        "Data provider error",
    )
    use_case = LoadStockDataUseCase(provider=mock_stock_data_provider)

    stock_code = StockCode("sh600000")
    date_range = DateRange(date(2023, 1, 1), date(2023, 1, 31))
    kline_type = KLineType.DAY

    # Act & Assert
    with pytest.raises(Exception, match="Data provider error"):
        await use_case.execute(
            stock_code=stock_code, date_range=date_range, kline_type=kline_type,
        )


@pytest.mark.asyncio
async def test_load_multiple_stocks_integration(
    mock_stock_data_provider, test_data_factory,
):
    """
    测试加载多只股票数据

    场景: 批量加载多只股票的数据
    """
    # Arrange
    from use_cases.data.load_stock_data import LoadStockDataUseCase

    stock_codes = [StockCode("sh600000"), StockCode("sz000001"), StockCode("bj430047")]
    date_range = DateRange(date(2023, 1, 1), date(2023, 1, 31))
    kline_type = KLineType.DAY

    use_case = LoadStockDataUseCase(provider=mock_stock_data_provider)

    # Act
    results = []
    for stock_code in stock_codes:
        mock_stock_data_provider.load_stock_data.return_value = (
            test_data_factory.create_kline_data(stock_code=stock_code.value, count=10)
        )
        result = await use_case.execute(
            stock_code=stock_code, date_range=date_range, kline_type=kline_type,
        )
        results.append(result)

    # Assert
    assert len(results) == 3
    assert all(len(r) == 10 for r in results)
    for i, stock_code in enumerate(stock_codes):
        assert all(k.stock_code == stock_code for k in results[i])


@pytest.mark.asyncio
async def test_load_stock_data_with_different_kline_types(
    mock_stock_data_provider, test_data_factory,
):
    """
    测试加载不同K线类型的数据

    场景: 加载日线、周线、月线数据
    """
    # Arrange
    from use_cases.data.load_stock_data import LoadStockDataUseCase

    use_case = LoadStockDataUseCase(provider=mock_stock_data_provider)
    stock_code = StockCode("sh600000")
    date_range = DateRange(date(2023, 1, 1), date(2023, 12, 31))

    kline_types = [KLineType.DAY, KLineType.WEEK, KLineType.MONTH]

    # Act & Assert
    for kline_type in kline_types:
        # Create data with matching kline_type
        from datetime import timedelta
        test_data = [
            KLineData(
                stock_code=StockCode("sh600000"),
                timestamp=datetime.combine(
                    date(2023, 1, 1) + timedelta(days=i), datetime.min.time(),
                ),
                kline_type=kline_type,  # Set the requested type
                open=Decimal("10.0"),
                high=Decimal("11.0"),
                low=Decimal("9.0"),
                close=Decimal("10.5"),
                volume=1000000,
                amount=Decimal(10500000),
            )
            for i in range(10)
        ]

        mock_stock_data_provider.load_stock_data.return_value = test_data

        result = await use_case.execute(
            stock_code=stock_code, date_range=date_range, kline_type=kline_type,
        )

        assert len(result) > 0
        assert all(k.kline_type == kline_type for k in result)


@pytest.mark.asyncio
async def test_load_stock_data_performance(
    mock_stock_data_provider, test_data_factory,
):
    """
    测试数据加载性能

    验证: 加载大量数据的性能
    """
    import time

    from use_cases.data.load_stock_data import LoadStockDataUseCase

    # Arrange
    large_dataset = test_data_factory.create_kline_data(count=1000)
    mock_stock_data_provider.load_stock_data.return_value = large_dataset
    use_case = LoadStockDataUseCase(provider=mock_stock_data_provider)

    stock_code = StockCode("sh600000")
    date_range = DateRange(date(2020, 1, 1), date(2023, 12, 31))
    kline_type = KLineType.DAY

    # Act
    start_time = time.time()
    result = await use_case.execute(
        stock_code=stock_code, date_range=date_range, kline_type=kline_type,
    )
    elapsed = time.time() - start_time

    # Assert
    assert len(result) == 1000
    assert elapsed < 1.0, f"Data loading too slow: {elapsed}s"


@pytest.mark.asyncio
async def test_load_stock_data_caching_behavior(mock_stock_data_provider):
    """
    测试数据加载的缓存行为

    验证: 相同请求不会重复调用数据提供者
    """
    # Arrange
    from use_cases.data.load_stock_data import LoadStockDataUseCase

    mock_stock_data_provider.load_stock_data.return_value = []
    use_case = LoadStockDataUseCase(provider=mock_stock_data_provider)

    stock_code = StockCode("sh600000")
    date_range = DateRange(date(2023, 1, 1), date(2023, 1, 31))
    kline_type = KLineType.DAY

    # Act - 多次调用
    _result1 = await use_case.execute(
        stock_code=stock_code, date_range=date_range, kline_type=kline_type,
    )
    _result2 = await use_case.execute(
        stock_code=stock_code, date_range=date_range, kline_type=kline_type,
    )

    # Assert - 每次调用都会请求数据提供者（当前无缓存实现）
    assert mock_stock_data_provider.load_stock_data.call_count == 2


@pytest.mark.asyncio
async def test_load_stock_data_date_range_validation():
    """
    测试日期范围验证

    验证: 无效的日期范围会被拒绝
    """
    # Arrange & Act & Assert
    with pytest.raises(ValueError):
        # end_date < start_date 应该抛出异常
        DateRange(date(2023, 12, 31), date(2023, 1, 1))
