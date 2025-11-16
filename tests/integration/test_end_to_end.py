"""
End-to-End Integration Tests

测试完整的量化交易流程（端到端）
"""

from datetime import date, datetime
from decimal import Decimal

import pytest

from domain.entities.model import Model, ModelStatus, ModelType
from domain.value_objects.configuration import BacktestConfig
from domain.value_objects.date_range import DateRange
from domain.value_objects.kline_type import KLineType
from domain.value_objects.stock_code import StockCode


@pytest.mark.asyncio
async def test_complete_trading_workflow(integration_container):
    """
    测试完整的量化交易工作流

    流程:
    1. 加载股票数据
    2. 训练模型
    3. 生成预测
    4. 转换为交易信号
    5. 运行回测
    6. 验证结果
    """
    # Step 1: 加载股票数据
    stock_code = StockCode("sh600000")
    date_range = DateRange(date(2023, 1, 1), date(2023, 12, 31))

    kline_data = await integration_container.load_stock_data_use_case.execute(
        stock_code=stock_code, date_range=date_range, kline_type=KLineType.DAY,
    )

    assert len(kline_data) > 0, "数据加载失败"

    # Step 2: 训练模型
    model = Model(
        model_type=ModelType.LGBM,
        hyperparameters={"learning_rate": 0.01, "n_estimators": 100},
    )

    trained_model = await integration_container.train_model_use_case.execute(
        model=model, training_data=kline_data,
    )

    assert trained_model.status == ModelStatus.TRAINED, "模型训练失败"
    assert trained_model.is_trained(), "模型状态不正确"

    # Step 3: 生成预测
    prediction_batch = await integration_container.generate_predictions_use_case.execute(
        model_id=trained_model.id, input_data=kline_data[-30:],  # 最近30天
    )

    assert len(prediction_batch.predictions) > 0, "预测生成失败"

    # Step 4: 转换为交易信号
    signals = await integration_container.convert_predictions_to_signals_use_case.execute(
        predictions=prediction_batch
    , strategy_params={"strategy_type": "threshold", "threshold": 0.5})

    assert signals.size() > 0, "信号转换失败"

    # Step 5: 运行回测
    backtest_config = BacktestConfig(
        initial_capital=Decimal(100000),
        commission_rate=Decimal("0.001"),
        slippage_rate=Decimal("0.001"),
    )

    backtest_result = await integration_container.run_backtest_use_case.execute(
        signals=signals, config=backtest_config, date_range=date_range,
    )

    # Step 6: 验证最终结果
    assert backtest_result is not None, "回测执行失败"
    assert backtest_result.final_capital > Decimal(0), "最终资金异常"
    assert backtest_result.total_return() >= 0
    assert backtest_result.calculate_sharpe_ratio() is not None, "缺少夏普比率指标"


@pytest.mark.asyncio
async def test_multi_stock_trading_workflow(integration_container, test_data_factory):
    """
    测试多股票交易工作流

    场景: 同时处理多只股票的完整流程
    """
    stock_codes = [StockCode("sh600000"), StockCode("sz000001"), StockCode("bj430047")]
    date_range = DateRange(date(2023, 1, 1), date(2023, 12, 31))

    all_predictions = []

    # 对每只股票执行完整流程
    for stock_code in stock_codes:
        # 1. 加载数据
        kline_data = await integration_container.load_stock_data_use_case.execute(
            stock_code=stock_code, date_range=date_range, kline_type=KLineType.DAY,
        )

        assert len(kline_data) > 0

        # 2. 训练模型（每只股票一个模型）
        model = Model(
            model_type=ModelType.LGBM, hyperparameters={"learning_rate": 0.01},
        )
        trained_model = await integration_container.train_model_use_case.execute(
            model=model, training_data=kline_data,
        )

        assert trained_model.is_trained()

        # 3. 生成预测
        prediction_batch = await integration_container.generate_predictions_use_case.execute(
        model_id=trained_model.id, input_data=kline_data[-30:],
        )

        all_predictions.extend(prediction_batch.predictions)

    # 4. 合并所有预测并转换为信号
    assert len(all_predictions) > 0

    # 创建预测批次(去重)
    from domain.entities.prediction import PredictionBatch
    merged_batch = PredictionBatch(model_id="multi_stock", batch_date=datetime(2023, 1, 1))
    seen = set()
    for pred in all_predictions:
        key = (pred.stock_code, pred.prediction_date)
        if key not in seen:
            merged_batch.add_prediction(pred)
            seen.add(key)

    signals = await integration_container.convert_predictions_to_signals_use_case.execute(
        predictions=merged_batch
    , strategy_params={"strategy_type": "threshold", "threshold": 0.5})

    # 5. 运行回测
    backtest_config = BacktestConfig(initial_capital=Decimal(300000), commission_rate=Decimal("0.001"), slippage_rate=Decimal("0.001"))

    backtest_result = await integration_container.run_backtest_use_case.execute(
        signals=signals, config=backtest_config, date_range=date_range,
    )

    # 验证
    assert backtest_result is not None
    assert backtest_result.initial_capital == Decimal(300000)


@pytest.mark.asyncio
async def test_model_retraining_workflow(integration_container, sample_kline_data):
    """
    测试模型重训练工作流

    场景: 训练模型后，使用新数据重新训练
    """
    # 1. 初始训练
    model = Model(
        model_type=ModelType.LGBM, hyperparameters={"learning_rate": 0.01},
    )

    trained_model_v1 = await integration_container.train_model_use_case.execute(
        model=model, training_data=sample_kline_data[:20],
    )

    assert trained_model_v1.is_trained()
    first_training_date = trained_model_v1.training_date

    # 2. 使用更多数据重新训练
    trained_model_v2 = await integration_container.train_model_use_case.execute(
        model=trained_model_v1, training_data=sample_kline_data,  # 使用全部数据
    )

    # 验证
    assert trained_model_v2.is_trained()
    assert trained_model_v2.training_date >= first_training_date


@pytest.mark.asyncio
async def test_strategy_comparison_workflow(integration_container, sample_kline_data):
    """
    测试策略比较工作流

    场景: 训练多个模型，比较不同策略的回测结果
    """
    model_types = [ModelType.LGBM, ModelType.MLP, ModelType.LSTM]
    backtest_results = []

    date_range = DateRange(date(2023, 1, 1), date(2023, 12, 31))

    for model_type in model_types:
        # 1. 训练不同类型的模型
        model = Model(model_type=model_type, hyperparameters={"learning_rate": 0.01})

        trained_model = await integration_container.train_model_use_case.execute(
            model=model, training_data=sample_kline_data,
        )

        # 2. 生成预测
        prediction_batch = await integration_container.generate_predictions_use_case.execute(
        model_id=trained_model.id, input_data=sample_kline_data[-30:],
        )

        # 3. 转换信号
        signals = await integration_container.convert_predictions_to_signals_use_case.execute(
            predictions=prediction_batch
        , strategy_params={"strategy_type": "threshold", "threshold": 0.5})

        # 4. 回测
        config = BacktestConfig(initial_capital=Decimal(100000), commission_rate=Decimal("0.001"), slippage_rate=Decimal("0.001"))

        result = await integration_container.run_backtest_use_case.execute(
            signals=signals, config=config, date_range=date_range,
        )

        backtest_results.append((model_type, result))

    # 验证：所有策略都成功执行
    assert len(backtest_results) == 3
    for model_type, result in backtest_results:
        assert result is not None
        assert result.final_capital > Decimal(0)


@pytest.mark.asyncio
async def test_incremental_prediction_workflow(
    integration_container, sample_kline_data, sample_trained_model,
):
    """
    测试增量预测工作流

    场景: 使用已训练模型进行增量预测（模拟实时交易）
    """
    # 使用已训练的模型并保存到repository
    model = sample_trained_model
    await integration_container.generate_predictions_use_case.repository.save(model)

    # 模拟滑动窗口预测
    window_size = 10
    all_predictions = []

    for i in range(0, len(sample_kline_data) - window_size, 5):
        # 使用滑动窗口数据进行预测
        window_data = sample_kline_data[i : i + window_size]

        prediction_batch = await integration_container.generate_predictions_use_case.execute(
        model_id=model.id, input_data=window_data,
        )

        all_predictions.extend(prediction_batch.predictions)

    # 转换所有预测为信号
    # 创建预测批次(去重)
    from domain.entities.prediction import PredictionBatch
    incremental_batch = PredictionBatch(model_id=model.id, batch_date=datetime.now())
    seen = set()
    for pred in all_predictions:
        key = (pred.stock_code, pred.prediction_date)
        if key not in seen:
            incremental_batch.add_prediction(pred)
            seen.add(key)

    signals = await integration_container.convert_predictions_to_signals_use_case.execute(
        predictions=incremental_batch
    , strategy_params={"strategy_type": "threshold", "threshold": 0.5})

    # 回测
    config = BacktestConfig(initial_capital=Decimal(100000), commission_rate=Decimal("0.001"), slippage_rate=Decimal("0.001"))
    date_range = DateRange(date(2023, 1, 1), date(2023, 12, 31))

    result = await integration_container.run_backtest_use_case.execute(
        signals=signals, config=config, date_range=date_range,
    )

    # 验证
    assert len(all_predictions) > 0
    assert signals.size() > 0
    assert result is not None


@pytest.mark.asyncio
async def test_error_recovery_workflow(integration_container, mock_model_trainer):
    """
    测试错误恢复工作流

    场景: 某个环节失败后，系统能够正确处理
    """
    from domain.entities.model import Model, ModelType

    # 1. 加载数据成功
    stock_code = StockCode("sh600000")
    date_range = DateRange(date(2023, 1, 1), date(2023, 12, 31))

    kline_data = await integration_container.load_stock_data_use_case.execute(
        stock_code=stock_code, date_range=date_range, kline_type=KLineType.DAY,
    )

    assert len(kline_data) > 0

    # 2. 训练失败
    mock_model_trainer.train.side_effect = Exception("Training failed")

    model = Model(model_type=ModelType.LGBM, hyperparameters={"learning_rate": 0.01})

    with pytest.raises(Exception, match="Training failed"):
        await integration_container.train_model_use_case.execute(
            model=model, training_data=kline_data,
        )

    # 3. 修复后重试
    async def train_success(model, training_data):
        model.mark_as_trained({"accuracy": 0.85})
        return model

    mock_model_trainer.train.side_effect = train_success

    trained_model = await integration_container.train_model_use_case.execute(
        model=model, training_data=kline_data,
    )

    # 验证恢复成功
    assert trained_model.is_trained()


@pytest.mark.asyncio
async def test_full_workflow_with_validation(integration_container, sample_kline_data):
    """
    测试带验证的完整工作流

    场景: 在每个步骤添加验证，确保数据质量
    """
    # 1. 加载并验证数据
    stock_code = StockCode("sh600000")
    date_range = DateRange(date(2023, 1, 1), date(2023, 12, 31))

    kline_data = await integration_container.load_stock_data_use_case.execute(
        stock_code=stock_code, date_range=date_range, kline_type=KLineType.DAY,
    )

    # 验证数据质量
    assert len(kline_data) > 0
    assert all(k.volume >= 0 for k in kline_data)
    assert all(k.high >= k.low for k in kline_data)

    # 2. 训练并验证模型
    model = Model(
        model_type=ModelType.LGBM, hyperparameters={"learning_rate": 0.01},
    )

    trained_model = await integration_container.train_model_use_case.execute(
        model=model, training_data=kline_data,
    )

    # 验证模型
    assert trained_model.is_trained()
    assert trained_model.metrics is not None
    assert len(trained_model.metrics) > 0

    # 3. 生成并验证预测
    prediction_batch = await integration_container.generate_predictions_use_case.execute(
        model_id=trained_model.id, input_data=kline_data[-30:],
    )

    # 验证预测
    assert len(prediction_batch.predictions) > 0
    assert all(p.predicted_value is not None for p in prediction_batch.predictions)

    # 4. 转换并验证信号
    signals = await integration_container.convert_predictions_to_signals_use_case.execute(
        predictions=prediction_batch
    , strategy_params={"strategy_type": "threshold", "threshold": 0.5})

    # 验证信号
    assert signals.size() > 0
    all_signals = signals.signals
    assert len(all_signals) > 0

    # 5. 回测并验证结果
    config = BacktestConfig(initial_capital=Decimal(100000), commission_rate=Decimal("0.001"), slippage_rate=Decimal("0.001"))

    result = await integration_container.run_backtest_use_case.execute(
        signals=signals, config=config, date_range=date_range,
    )

    # 验证回测结果
    assert result is not None
    assert result.final_capital > Decimal(0)
    assert result.metrics is not None
    assert all(isinstance(v, (int, float)) for v in result.metrics.values())


@pytest.mark.asyncio
async def test_workflow_with_performance_tracking(integration_container, sample_kline_data):
    """
    测试带性能跟踪的工作流

    场景: 记录每个步骤的执行时间
    """
    import time

    timings = {}

    # 1. 数据加载
    start = time.time()
    stock_code = StockCode("sh600000")
    date_range = DateRange(date(2023, 1, 1), date(2023, 12, 31))

    kline_data = await integration_container.load_stock_data_use_case.execute(
        stock_code=stock_code, date_range=date_range, kline_type=KLineType.DAY,
    )
    timings["data_loading"] = time.time() - start

    # 2. 模型训练
    start = time.time()
    model = Model(model_type=ModelType.LGBM, hyperparameters={"learning_rate": 0.01})
    trained_model = await integration_container.train_model_use_case.execute(
        model=model, training_data=kline_data,
    )
    timings["model_training"] = time.time() - start

    # 3. 预测生成
    start = time.time()
    prediction_batch = await integration_container.generate_predictions_use_case.execute(
        model_id=trained_model.id, input_data=kline_data[-30:],
    )
    timings["prediction"] = time.time() - start

    # 4. 信号转换
    start = time.time()
    signals = await integration_container.convert_predictions_to_signals_use_case.execute(
        predictions=prediction_batch
    , strategy_params={"strategy_type": "threshold", "threshold": 0.5})
    timings["signal_conversion"] = time.time() - start

    # 5. 回测
    start = time.time()
    config = BacktestConfig(initial_capital=Decimal(100000), commission_rate=Decimal("0.001"), slippage_rate=Decimal("0.001"))
    _result = await integration_container.run_backtest_use_case.execute(
        signals=signals, config=config, date_range=date_range,
    )
    timings["backtest"] = time.time() - start

    # 验证所有步骤都在合理时间内完成
    total_time = sum(timings.values())
    assert total_time < 10.0, f"Total workflow too slow: {total_time}s"

    # 打印性能统计（用于调试）
    for step, duration in timings.items():
        assert duration < 5.0, f"{step} too slow: {duration}s"
