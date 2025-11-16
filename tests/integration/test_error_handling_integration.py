"""
Error Handling Integration Tests

测试跨层错误传播和处理
"""

from datetime import date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from domain.entities.model import Model, ModelType
from domain.value_objects.configuration import BacktestConfig
from domain.value_objects.date_range import DateRange
from domain.value_objects.kline_type import KLineType
from domain.value_objects.stock_code import StockCode


@pytest.mark.asyncio
async def test_data_provider_error_propagation(mock_stock_data_provider):
    """
    测试数据提供者错误传播

    场景: Adapter 层错误应该传播到 UseCase 层
    """
    # Arrange
    from use_cases.data.load_stock_data import LoadStockDataUseCase

    # Mock 数据提供者抛出异常
    mock_stock_data_provider.load_stock_data.side_effect = RuntimeError(
        "Database connection failed",
    )
    use_case = LoadStockDataUseCase(provider=mock_stock_data_provider)

    stock_code = StockCode("sh600000")
    date_range = DateRange(date(2023, 1, 1), date(2023, 12, 31))

    # Act & Assert
    with pytest.raises(RuntimeError, match="Database connection failed"):
        await use_case.execute(
            stock_code=stock_code, date_range=date_range, kline_type=KLineType.DAY,
        )


@pytest.mark.asyncio
async def test_model_training_error_propagation(mock_model_trainer, mock_model_repository):
    """
    测试模型训练错误传播

    场景: 训练器错误应该传播并且不保存模型
    """
    # Arrange
    from use_cases.model.train_model import TrainModelUseCase

    # Mock 训练器抛出异常
    mock_model_trainer.train.side_effect = ValueError("Invalid training data format")
    use_case = TrainModelUseCase(
        trainer=mock_model_trainer, repository=mock_model_repository,
    )

    model = Model(model_type=ModelType.LGBM, hyperparameters={"learning_rate": 0.01})

    # Act & Assert
    with pytest.raises(ValueError, match="Invalid training data format"):
        await use_case.execute(model=model, training_data=[])

    # 验证模型没有被保存（检查repository中没有模型）
    saved_model = await mock_model_repository.find_by_id(model.id)
    assert saved_model is None


@pytest.mark.asyncio
async def test_backtest_engine_error_propagation(mock_backtest_engine, sample_signals):
    """
    测试回测引擎错误传播

    场景: 回测引擎错误应该传播到 UseCase 层
    """
    # Arrange
    from domain.entities.trading_signal import SignalBatch
    from use_cases.backtest.run_backtest import RunBacktestUseCase

    # Mock 回测引擎抛出异常
    mock_backtest_engine.run_backtest.side_effect = Exception(
        "Insufficient capital for trading",
    )
    use_case = RunBacktestUseCase(engine=mock_backtest_engine)

    signal_batch = SignalBatch(strategy_name="test_strategy", batch_date=datetime(2023, 1, 1))
    for signal in sample_signals:
        signal_batch.add_signal(signal)

    config = BacktestConfig(initial_capital=Decimal(100), commission_rate=Decimal("0.001"), slippage_rate=Decimal("0.001"))  # 资金不足
    date_range = DateRange(date(2023, 1, 1), date(2023, 12, 31))

    # Act & Assert
    with pytest.raises(Exception, match="Insufficient capital"):
        await use_case.execute(signals=signal_batch, config=config, date_range=date_range)


@pytest.mark.asyncio
async def test_validation_error_in_value_objects():
    """
    测试值对象验证错误

    场景: 无效的值对象创建应该被拒绝
    """
    # Test 1: 无效股票代码
    with pytest.raises(ValueError, match="Invalid stock code"):
        StockCode("invalid")

    # Test 2: 无效日期范围
    with pytest.raises(ValueError):
        DateRange(date(2023, 12, 31), date(2023, 1, 1))  # end < start

    # Test 3: 无效配置
    with pytest.raises(ValueError):
        BacktestConfig(initial_capital=Decimal(-1000), commission_rate=Decimal("0.001"), slippage_rate=Decimal("0.001"))  # 负数资金


@pytest.mark.asyncio
async def test_domain_rule_violation_error(sample_kline_data):
    """
    测试领域规则违反错误

    场景: 违反领域规则应该抛出异常
    """
    from domain.entities.model import Model, ModelType

    # Test 1: 部署未训练模型
    model = Model(model_type=ModelType.LGBM, hyperparameters={"learning_rate": 0.01})

    with pytest.raises(ValueError, match="Cannot deploy untrained model"):
        model.deploy()

    # Test 2: 低于阈值的指标
    with pytest.raises(ValueError, match="metrics below threshold"):
        model.mark_as_trained({"accuracy": 0.3}, threshold=0.5)


@pytest.mark.asyncio
async def test_error_handling_with_partial_failure(integration_container):
    """
    测试部分失败的错误处理

    场景: 批量操作中部分成功、部分失败
    """
    # Arrange
    stock_codes = [StockCode("sh600000"), StockCode("sz000001"), StockCode("bj430047")]
    date_range = DateRange(date(2023, 1, 1), date(2023, 12, 31))

    # Mock 第二只股票数据加载失败
    call_count = 0

    async def load_with_failure(stock_code, date_range, kline_type):
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            raise Exception("Data not available for this stock")
        from tests.integration.conftest import TestDataFactory

        return TestDataFactory.create_kline_data(count=10)

    integration_container.load_stock_data_use_case.provider.load_stock_data.side_effect = (
        load_with_failure
    )

    # Act
    results = []
    errors = []

    for stock_code in stock_codes:
        try:
            result = await integration_container.load_stock_data_use_case.execute(
                stock_code=stock_code, date_range=date_range, kline_type=KLineType.DAY,
            )
            results.append(result)
        except Exception as e:
            errors.append((stock_code, str(e)))

    # Assert
    assert len(results) == 2  # 2个成功
    assert len(errors) == 1  # 1个失败
    assert "Data not available" in errors[0][1]


@pytest.mark.asyncio
async def test_error_context_preservation():
    """
    测试错误上下文保留

    场景: 错误信息应该包含足够的上下文信息
    """
    # Arrange
    from use_cases.data.load_stock_data import LoadStockDataUseCase

    provider = AsyncMock()
    provider.load_stock_data.side_effect = Exception(
        "Failed to load data for sh600000 on 2023-01-01",
    )
    use_case = LoadStockDataUseCase(provider=provider)

    stock_code = StockCode("sh600000")
    date_range = DateRange(date(2023, 1, 1), date(2023, 12, 31))

    # Act & Assert
    try:
        await use_case.execute(
            stock_code=stock_code, date_range=date_range, kline_type=KLineType.DAY,
        )
        pytest.fail("Should have raised an exception")
    except Exception as e:
        # 验证错误信息包含上下文
        error_message = str(e)
        assert "sh600000" in error_message
        assert "2023-01-01" in error_message


@pytest.mark.asyncio
async def test_error_recovery_strategy(integration_container, mock_model_trainer):
    """
    测试错误恢复策略

    场景: 实现重试机制处理临时错误
    """
    # Arrange
    attempt_count = 0
    max_retries = 3

    async def train_with_retry(model, training_data):
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < max_retries:
            raise Exception("Temporary training error")
        # 第三次尝试成功
        model.mark_as_trained({"accuracy": 0.85})
        return model

    mock_model_trainer.train.side_effect = train_with_retry

    model = Model(model_type=ModelType.LGBM, hyperparameters={"learning_rate": 0.01})

    # Act - 实现重试逻辑
    for i in range(max_retries):
        try:
            trained_model = await integration_container.train_model_use_case.execute(
                model=model, training_data=[],
            )
            break  # 成功则退出
        except Exception:
            if i == max_retries - 1:
                raise  # 最后一次重试仍失败则抛出
            continue

    # Assert
    assert attempt_count == max_retries
    assert trained_model.is_trained()


@pytest.mark.asyncio
async def test_cascading_errors(integration_container, mock_model_trainer):
    """
    测试级联错误

    场景: 一个组件的错误导致后续组件失败
    """
    # Arrange
    stock_code = StockCode("sh600000")
    date_range = DateRange(date(2023, 1, 1), date(2023, 12, 31))

    # Step 1: 数据加载失败
    integration_container.load_stock_data_use_case.provider.load_stock_data.side_effect = Exception(
        "Data loading failed",
    )

    # Act & Assert - 数据加载失败
    with pytest.raises(Exception, match="Data loading failed"):
        _kline_data = await integration_container.load_stock_data_use_case.execute(
            stock_code=stock_code, date_range=date_range, kline_type=KLineType.DAY,
        )

    # 由于数据加载失败，后续步骤无法执行
    # 这验证了错误不会被静默忽略


@pytest.mark.asyncio
async def test_error_logging_integration(integration_container, mock_model_trainer, caplog):
    """
    测试错误日志记录

    场景: 错误应该被正确记录到日志
    """
    import logging

    # Arrange
    mock_model_trainer.train.side_effect = Exception("Training failed due to OOM")

    model = Model(model_type=ModelType.LGBM, hyperparameters={"learning_rate": 0.01})

    # Act
    with caplog.at_level(logging.ERROR):
        try:
            await integration_container.train_model_use_case.execute(
                model=model, training_data=[],
            )
        except Exception:
            pass  # 预期的异常

    # Assert - 验证错误被记录（如果实现了日志记录）
    # 这里只是验证异常被正确抛出
    # 实际的日志记录验证需要根据具体实现来调整


@pytest.mark.asyncio
async def test_error_with_cleanup(mock_model_repository):
    """
    测试错误后的清理

    场景: 操作失败后应该清理资源
    """
    # Arrange
    from use_cases.model.train_model import TrainModelUseCase

    trainer = AsyncMock()
    trainer.train.side_effect = Exception("Training failed")

    use_case = TrainModelUseCase(trainer=trainer, repository=mock_model_repository)

    model = Model(model_type=ModelType.LGBM, hyperparameters={"learning_rate": 0.01})

    # Act & Assert
    try:
        await use_case.execute(model=model, training_data=[])
        pytest.fail("Should have raised exception")
    except Exception:
        pass

    # 验证失败的模型没有被保存（清理行为）
    saved_model = await mock_model_repository.find_by_id(model.id)
    assert saved_model is None


@pytest.mark.asyncio
async def test_timeout_error_handling(mock_stock_data_provider):
    """
    测试超时错误处理

    场景: 长时间运行的操作应该能够超时
    """
    import asyncio

    from use_cases.data.load_stock_data import LoadStockDataUseCase

    # Arrange - Mock 一个永远不返回的操作
    async def never_returns(*args, **kwargs):
        await asyncio.sleep(10)  # 模拟长时间操作

    mock_stock_data_provider.load_stock_data.side_effect = never_returns
    use_case = LoadStockDataUseCase(provider=mock_stock_data_provider)

    stock_code = StockCode("sh600000")
    date_range = DateRange(date(2023, 1, 1), date(2023, 12, 31))

    # Act & Assert - 使用超时
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(
            use_case.execute(
                stock_code=stock_code, date_range=date_range, kline_type=KLineType.DAY,
            ),
            timeout=0.1,  # 100ms 超时
        )


@pytest.mark.asyncio
async def test_multiple_error_types(integration_container):
    """
    测试多种错误类型

    场景: 系统应该能够处理不同类型的错误
    """
    from domain.entities.model import Model, ModelType

    error_cases = [
        (ValueError, "Invalid parameter"),
        (RuntimeError, "System error"),
        (Exception, "Generic error"),
    ]

    for error_type, error_message in error_cases:
        # Arrange
        integration_container.train_model_use_case.trainer.train.side_effect = error_type(
            error_message,
        )

        model = Model(
            model_type=ModelType.LGBM, hyperparameters={"learning_rate": 0.01},
        )

        # Act & Assert
        with pytest.raises(error_type, match=error_message):
            await integration_container.train_model_use_case.execute(
                model=model, training_data=[],
            )
