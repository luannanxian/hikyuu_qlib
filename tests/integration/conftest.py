"""
Integration Test Fixtures

共享的集成测试 fixtures，用于设置测试环境
"""

import sqlite3
import tempfile
import yaml
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path
from typing import List, Dict, Any
from unittest.mock import AsyncMock, Mock

import pytest

from domain.entities.kline_data import KLineData
from domain.entities.model import Model, ModelType, ModelStatus
from domain.entities.prediction import Prediction
from domain.entities.trading_signal import TradingSignal, SignalType, SignalBatch
from domain.value_objects.stock_code import StockCode
from domain.value_objects.kline_type import KLineType
from domain.value_objects.date_range import DateRange


# =============================================================================
# Test Data Factory
# =============================================================================


class TestDataFactory:
    """测试数据工厂"""

    @staticmethod
    def create_kline_data(
        stock_code: str = "sh600000", count: int = 10, start_date: date = None
    ) -> List[KLineData]:
        """
        创建测试 K线数据

        Args:
            stock_code: 股票代码
            count: 数据条数
            start_date: 起始日期

        Returns:
            List[KLineData]: K线数据列表
        """
        from datetime import timedelta

        if start_date is None:
            start_date = date(2023, 1, 1)

        return [
            KLineData(
                stock_code=StockCode(stock_code),
                timestamp=datetime.combine(start_date + timedelta(days=i), datetime.min.time()),
                kline_type=KLineType.DAY,
                open=Decimal("10.0") + Decimal(str(i * 0.1)),
                high=Decimal("11.0") + Decimal(str(i * 0.1)),
                low=Decimal("9.0") + Decimal(str(i * 0.1)),
                close=Decimal("10.5") + Decimal(str(i * 0.1)),
                volume=1000000 + i * 10000,
                amount=Decimal("10500000") + Decimal(str(i * 10000)),
            )
            for i in range(count)
        ]

    @staticmethod
    def create_trained_model(
        model_type: ModelType = ModelType.LGBM,
        metrics: Dict[str, float] = None,
    ) -> Model:
        """
        创建已训练模型

        Args:
            model_type: 模型类型
            metrics: 评估指标

        Returns:
            Model: 已训练模型
        """
        if metrics is None:
            metrics = {"accuracy": 0.85}

        model = Model(
            model_type=model_type, hyperparameters={"learning_rate": 0.01}
        )
        model.mark_as_trained(metrics)
        return model

    @staticmethod
    def create_predictions(count: int = 10) -> List[Prediction]:
        """
        创建测试预测数据

        Args:
            count: 预测条数

        Returns:
            List[Prediction]: 预测列表
        """
        predictions = []
        for i in range(count):
            pred = Prediction(
                stock_code=StockCode("sh600000"),
                prediction_date=datetime(2023, 1, i + 1),
                predicted_value=Decimal(str(0.5 + i * 0.05)),
                confidence=Decimal("0.9"),
            )
            predictions.append(pred)
        return predictions

    @staticmethod
    def create_signals(count: int = 10) -> List[TradingSignal]:
        """
        创建测试交易信号

        Args:
            count: 信号条数

        Returns:
            List[TradingSignal]: 信号列表
        """
        from domain.entities.trading_signal import SignalStrength

        signals = []
        for i in range(count):
            signal = TradingSignal(
                stock_code=StockCode("sh600000"),
                signal_date=datetime(2023, 1, i + 1),
                signal_type=SignalType.BUY if i % 2 == 0 else SignalType.SELL,
                signal_strength=SignalStrength.MEDIUM,
                price=Decimal(str(10.0 + i * 0.1)),
            )
            signals.append(signal)
        return signals


# =============================================================================
# Database Fixtures
# =============================================================================


@pytest.fixture
def in_memory_db():
    """内存 SQLite 数据库"""
    db = sqlite3.connect(":memory:")

    # 创建测试表结构
    cursor = db.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS models (
            id TEXT PRIMARY KEY,
            model_type TEXT NOT NULL,
            hyperparameters TEXT NOT NULL,
            training_date TEXT,
            metrics TEXT,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """
    )
    db.commit()

    yield db

    db.close()


# =============================================================================
# Configuration Fixtures
# =============================================================================


@pytest.fixture
def temp_config_file():
    """临时配置文件"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as f:
        config = {
            "data_source": {
                "hikyuu_path": "/tmp/test/hikyuu",
                "qlib_path": "/tmp/test/qlib",
            },
            "model": {
                "default_type": "LGBM",
                "hyperparameters": {"learning_rate": 0.01, "n_estimators": 100},
            },
            "backtest": {
                "initial_capital": 100000.0,
                "commission_rate": 0.001,
                "slippage_rate": 0.001,
            },
        }
        yaml.dump(config, f)
        f.flush()

        yield f.name

    # Cleanup
    Path(f.name).unlink(missing_ok=True)


@pytest.fixture
def temp_config_dir():
    """临时配置目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


# =============================================================================
# Mock Adapters Fixtures
# =============================================================================


@pytest.fixture
def mock_stock_data_provider():
    """Mock 股票数据提供者"""
    provider = AsyncMock()
    provider.load_stock_data.return_value = TestDataFactory.create_kline_data()
    return provider


@pytest.fixture
def mock_model_trainer():
    """Mock 模型训练器"""
    trainer = AsyncMock()

    async def train_side_effect(model: Model, training_data: Any) -> Model:
        """训练副作用：标记模型为已训练"""
        model.mark_as_trained({"accuracy": 0.85})
        return model

    trainer.train.side_effect = train_side_effect
    return trainer


@pytest.fixture
async def mock_model_repository():
    """Mock 模型仓库（使用真实内存数据库）"""
    from adapters.repositories.sqlite_model_repository import SQLiteModelRepository

    repo = SQLiteModelRepository(db_path=":memory:")
    await repo.initialize()
    yield repo
    await repo.close()


@pytest.fixture
def mock_backtest_engine():
    """Mock 回测引擎"""
    from domain.entities.backtest import BacktestResult

    engine = AsyncMock()

    async def run_backtest_side_effect(signals, config, date_range):
        """回测副作用：返回模拟结果"""
        return BacktestResult(
            strategy_name="test_strategy",
            start_date=datetime.combine(date_range.start_date, datetime.min.time()),
            end_date=datetime.combine(date_range.end_date, datetime.min.time()),
            initial_capital=config.initial_capital,
            final_capital=Decimal("120000"),
            trades=[],
            equity_curve=[Decimal("100000"), Decimal("110000"), Decimal("120000")],
            metrics={
                "total_return": 0.2,
                "sharpe_ratio": 1.5,
                "max_drawdown": 0.05,
                "win_rate": 0.6
            }
        )

    engine.run_backtest.side_effect = run_backtest_side_effect
    return engine


@pytest.fixture
def mock_signal_converter():
    """Mock 信号转换器"""
    from adapters.converters.signal_converter_adapter import SignalConverterAdapter

    converter = SignalConverterAdapter()
    return converter


# =============================================================================
# Use Cases Fixtures
# =============================================================================


@pytest.fixture
def load_stock_data_use_case(mock_stock_data_provider):
    """LoadStockDataUseCase 实例"""
    from use_cases.data.load_stock_data import LoadStockDataUseCase

    return LoadStockDataUseCase(provider=mock_stock_data_provider)


@pytest.fixture
def train_model_use_case(mock_model_trainer, mock_model_repository):
    """TrainModelUseCase 实例"""
    from use_cases.model.train_model import TrainModelUseCase

    return TrainModelUseCase(
        trainer=mock_model_trainer, repository=mock_model_repository
    )


@pytest.fixture
def generate_predictions_use_case(mock_model_trainer, mock_model_repository):
    """GeneratePredictionsUseCase 实例"""
    from use_cases.model.generate_predictions import GeneratePredictionsUseCase

    # Mock trainer to return predictions
    async def predict_side_effect(model, input_data):
        """预测副作用：返回模拟预测"""
        return TestDataFactory.create_predictions(len(input_data))

    mock_model_trainer.predict.side_effect = predict_side_effect

    return GeneratePredictionsUseCase(
        repository=mock_model_repository, trainer=mock_model_trainer
    )


@pytest.fixture
def convert_predictions_to_signals_use_case(mock_signal_converter):
    """ConvertPredictionsToSignalsUseCase 实例"""
    from use_cases.signals.convert_predictions_to_signals import (
        ConvertPredictionsToSignalsUseCase,
    )

    return ConvertPredictionsToSignalsUseCase(converter=mock_signal_converter)


@pytest.fixture
def run_backtest_use_case(mock_backtest_engine):
    """RunBacktestUseCase 实例"""
    from use_cases.backtest.run_backtest import RunBacktestUseCase

    return RunBacktestUseCase(engine=mock_backtest_engine)


# =============================================================================
# Integration Container Fixture
# =============================================================================


@pytest.fixture
def integration_container(
    load_stock_data_use_case,
    train_model_use_case,
    generate_predictions_use_case,
    convert_predictions_to_signals_use_case,
    run_backtest_use_case,
):
    """集成测试容器（组装所有组件）"""

    class IntegrationContainer:
        """集成测试容器"""

        def __init__(self):
            self.load_stock_data_use_case = load_stock_data_use_case
            self.train_model_use_case = train_model_use_case
            self.generate_predictions_use_case = generate_predictions_use_case
            self.convert_predictions_to_signals_use_case = (
                convert_predictions_to_signals_use_case
            )
            self.run_backtest_use_case = run_backtest_use_case

    return IntegrationContainer()


# =============================================================================
# Test Data Fixtures
# =============================================================================


@pytest.fixture
def test_data_factory():
    """测试数据工厂实例"""
    return TestDataFactory()


@pytest.fixture
def sample_kline_data():
    """示例K线数据"""
    return TestDataFactory.create_kline_data(count=30)


@pytest.fixture
def sample_trained_model():
    """示例已训练模型"""
    return TestDataFactory.create_trained_model()


@pytest.fixture
def sample_predictions():
    """示例预测数据"""
    from domain.entities.prediction import PredictionBatch
    from datetime import datetime

    predictions_list = TestDataFactory.create_predictions(count=30)
    batch = PredictionBatch(model_id="test_model", batch_date=datetime(2023, 1, 1))
    for pred in predictions_list:
        batch.add_prediction(pred)
    return batch


@pytest.fixture
def sample_signals():
    """示例交易信号"""
    return TestDataFactory.create_signals(count=30)
