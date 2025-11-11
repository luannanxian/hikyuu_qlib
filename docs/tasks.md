# 任务规划文档 v2.0 - Hikyuu × Qlib 个人量化工作站

**版本**: 2.0.0
**日期**: 2025-11-11
**架构模式**: 六边形架构 + DDD + TDD

---

## 🎯 开发原则

### TDD 工作流程

所有任务必须严格遵循 **Red-Green-Refactor** 循环:

1. 🔴 **RED**: 先写失败的测试
2. 🟢 **GREEN**: 写最小实现让测试通过
3. 🔵 **REFACTOR**: 重构优化代码
4. 🔁 重复循环

### 架构分层开发顺序

严格按照以下顺序开发,确保依赖关系正确:

1. **Phase 1: Domain层** (Week 1-3) - 零外部依赖
2. **Phase 2: Use Cases层** (Week 4-6) - 依赖Domain Ports
3. **Phase 3: Adapters层** (Week 7-10) - 实现Ports接口

### 测试覆盖率要求

- Domain层: ≥95%
- Use Cases层: ≥90%
- Adapters层: ≥85%
- Infrastructure层: ≥88%

---

## Phase 1: Domain层开发 (Week 1-3)

### 📦 Task 1.1: StockCode Value Object

**需求**: [DR-001](./requirements.md#dr-001-stock-股票-领域模型)

#### 🔴 RED: 编写测试

**文件**: `tests/unit/domain/value_objects/test_stock_code.py`

**测试用例**:
- `test_valid_stock_code_creation()`: 验证合法股票代码创建
- `test_invalid_stock_code_raises_error()`: 验证非法代码抛出异常
- `test_stock_code_immutability()`: 验证StockCode不可变性
- `test_stock_code_equality()`: 验证值对象相等性比较
- `test_stock_code_string_representation()`: 验证字符串表示

#### 🟢 GREEN: 实现代码

**文件**: `src/domain/value_objects/stock_code.py`

**实现**:
```python
from dataclasses import dataclass
from typing import Final

@dataclass(frozen=True)
class StockCode:
    """股票代码值对象"""
    value: str

    def __post_init__(self):
        if not isinstance(self.value, str):
            raise ValueError("Stock code must be a string")
        if len(self.value) != 8:
            raise ValueError("Stock code must be 8 characters")
        if self.value[:2] not in ('sh', 'sz', 'bj'):
            raise ValueError("Stock code must start with sh/sz/bj")
```

#### 🔵 REFACTOR: 优化代码

- 提取验证逻辑到单独方法
- 添加更多验证规则(如数字部分验证)
- 优化错误消息

**完成标准**:
- ✅ 所有测试通过
- ✅ 测试覆盖率 = 100%
- ✅ 代码通过Black/Ruff/MyPy检查

---

### 📦 Task 1.2: Market Value Object

**需求**: [DR-001](./requirements.md#dr-001-stock-股票-领域模型)

#### 🔴 RED: 编写测试

**文件**: `tests/unit/domain/value_objects/test_market.py`

**测试用例**:
- `test_valid_market_values()`: 验证有效市场枚举值
- `test_invalid_market_raises_error()`: 验证无效市场抛出异常
- `test_market_from_string()`: 验证从字符串创建Market

#### 🟢 GREEN: 实现代码

**文件**: `src/domain/value_objects/market.py`

**实现**:
```python
from enum import Enum

class Market(str, Enum):
    """市场枚举"""
    SH = "sh"
    SZ = "sz"
    BJ = "bj"
```

#### 🔵 REFACTOR: 优化代码

**完成标准**:
- ✅ 所有测试通过
- ✅ 测试覆盖率 ≥95%

---

### 📦 Task 1.3: Stock Entity

**需求**: [DR-001](./requirements.md#dr-001-stock-股票-领域模型)

#### 🔴 RED: 编写测试

**文件**: `tests/unit/domain/entities/test_stock.py`

**测试用例**:
- `test_stock_creation()`: 验证股票实体创建
- `test_stock_is_tradable_when_active()`: 验证活跃股票可交易
- `test_stock_not_tradable_when_inactive()`: 验证非活跃股票不可交易
- `test_validate_trading_date()`: 验证交易日期验证

#### 🟢 GREEN: 实现代码

**文件**: `src/domain/entities/stock.py`

**实现**:
```python
from dataclasses import dataclass
from datetime import date
from domain.value_objects.stock_code import StockCode
from domain.value_objects.market import Market

@dataclass
class Stock:
    """股票实体"""
    code: StockCode
    name: str
    market: Market
    is_active: bool
    listing_date: date

    def is_tradable(self) -> bool:
        """判断是否可交易"""
        return self.is_active

    def validate_trading_date(self, trading_date: date) -> bool:
        """验证交易日期是否有效"""
        return trading_date >= self.listing_date
```

#### 🔵 REFACTOR: 优化代码

**完成标准**:
- ✅ 所有测试通过
- ✅ 测试覆盖率 ≥95%

---

### 📦 Task 1.4: DateRange Value Object

**需求**: [DR-002](./requirements.md#dr-002-daterange-日期范围-领域模型)

#### 🔴 RED: 编写测试

**文件**: `tests/unit/domain/value_objects/test_date_range.py`

**测试用例**:
- `test_valid_date_range()`: 验证有效日期范围
- `test_invalid_date_range_raises_error()`: start_date > end_date 抛出异常
- `test_date_range_contains()`: 验证日期是否在范围内
- `test_date_range_overlap()`: 验证日期范围重叠判断

#### 🟢 GREEN: 实现代码

**文件**: `src/domain/value_objects/date_range.py`

#### 🔵 REFACTOR: 优化代码

**完成标准**:
- ✅ 所有测试通过
- ✅ 测试覆盖率 ≥95%

---

### 📦 Task 1.5: KLineData Entity

**需求**: [DR-003](./requirements.md#dr-003-klinedata-k线数据-领域模型)

#### 🔴 RED: 编写测试

**文件**: `tests/unit/domain/entities/test_kline_data.py`

**测试用例**:
- `test_kline_data_creation()`: 验证K线数据创建
- `test_validate_ohlc_valid()`: 验证合法OHLC关系
- `test_validate_ohlc_invalid_high()`: high < max(open, close) 抛出异常
- `test_validate_ohlc_invalid_low()`: low > min(open, close) 抛出异常
- `test_calculate_change_pct()`: 验证涨跌幅计算

#### 🟢 GREEN: 实现代码

**文件**: `src/domain/entities/kline_data.py`

#### 🔵 REFACTOR: 优化代码

**完成标准**:
- ✅ 所有测试通过
- ✅ 测试覆盖率 ≥95%

---

### 📦 Task 1.6: Model Entity

**需求**: [DR-005](./requirements.md#dr-005-model-模型-领域模型)

#### 🔴 RED: 编写测试

**文件**: `tests/unit/domain/entities/test_model.py`

**测试用例**:
- `test_model_creation()`: 验证模型创建(初始状态UNTRAINED)
- `test_mark_as_trained()`: 验证标记为已训练状态
- `test_validate_metrics_above_threshold()`: 验证指标达标
- `test_validate_metrics_below_threshold()`: 验证指标不达标
- `test_is_ready_for_prediction_when_trained()`: TRAINED状态可预测
- `test_is_not_ready_for_prediction_when_untrained()`: UNTRAINED状态不可预测

#### 🟢 GREEN: 实现代码

**文件**: `src/domain/entities/model.py`

#### 🔵 REFACTOR: 优化代码

**完成标准**:
- ✅ 所有测试通过
- ✅ 测试覆盖率 ≥95%

---

### 📦 Task 1.7: Prediction Entity and PredictionBatch Aggregate

**需求**: [DR-006](./requirements.md#dr-006-prediction-预测-领域模型)

#### 🔴 RED: 编写测试

**文件**: `tests/unit/domain/entities/test_prediction.py`

**测试用例**:
- `test_prediction_creation()`: 验证预测实体创建
- `test_is_above_threshold()`: 验证分数阈值判断
- `test_normalize_score()`: 验证分数标准化
- `test_prediction_batch_get_top_k()`: 验证Top-K获取
- `test_prediction_batch_filter_by_threshold()`: 验证阈值过滤

#### 🟢 GREEN: 实现代码

**文件**: `src/domain/entities/prediction.py`, `src/domain/aggregates/prediction_batch.py`

#### 🔵 REFACTOR: 优化代码

**完成标准**:
- ✅ 所有测试通过
- ✅ 测试覆盖率 ≥95%

---

### 📦 Task 1.8: TradingSignal Entity and SignalBatch Aggregate

**需求**: [DR-007](./requirements.md#dr-007-signal-信号-领域模型)

#### 🔴 RED: 编写测试

**文件**: `tests/unit/domain/entities/test_trading_signal.py`

**测试用例**:
- `test_trading_signal_creation()`: 验证交易信号创建
- `test_is_buy_signal()`: 验证买入信号判断
- `test_is_sell_signal()`: 验证卖出信号判断
- `test_get_position_size()`: 验证持仓量计算
- `test_signal_batch_filter_by_direction()`: 验证方向过滤
- `test_signal_batch_get_buy_signals()`: 验证买入信号获取

#### 🟢 GREEN: 实现代码

**文件**: `src/domain/entities/trading_signal.py`, `src/domain/aggregates/signal_batch.py`

#### 🔵 REFACTOR: 优化代码

**完成标准**:
- ✅ 所有测试通过
- ✅ 测试覆盖率 ≥95%

---

### 📦 Task 1.9: Portfolio and Position Entities

**需求**: [DR-008](./requirements.md#dr-008-portfolio-投资组合-领域模型)

#### 🔴 RED: 编写测试

**文件**: `tests/unit/domain/entities/test_portfolio.py`

**测试用例**:
- `test_portfolio_creation()`: 验证投资组合创建
- `test_add_position()`: 验证添加持仓
- `test_remove_position()`: 验证移除持仓
- `test_calculate_total_value()`: 验证总市值计算
- `test_get_position_weight()`: 验证持仓权重计算
- `test_position_calculate_profit_loss()`: 验证盈亏计算
- `test_position_calculate_return_pct()`: 验证收益率计算

#### 🟢 GREEN: 实现代码

**文件**: `src/domain/entities/portfolio.py`, `src/domain/entities/position.py`

#### 🔵 REFACTOR: 优化代码

**完成标准**:
- ✅ 所有测试通过
- ✅ 测试覆盖率 ≥95%

---

### 📦 Task 1.10: BacktestResult and Trade Entities

**需求**: [DR-009](./requirements.md#dr-009-backtestresult-回测结果-领域模型)

#### 🔴 RED: 编写测试

**文件**: `tests/unit/domain/entities/test_backtest_result.py`

**测试用例**:
- `test_backtest_result_creation()`: 验证回测结果创建
- `test_calculate_sharpe_ratio()`: 验证夏普比率计算
- `test_calculate_max_drawdown()`: 验证最大回撤计算
- `test_get_win_rate()`: 验证胜率计算
- `test_trade_calculate_profit()`: 验证交易盈亏计算
- `test_trade_calculate_hold_days()`: 验证持有天数计算

#### 🟢 GREEN: 实现代码

**文件**: `src/domain/entities/backtest_result.py`, `src/domain/entities/trade.py`

#### 🔵 REFACTOR: 优化代码

**完成标准**:
- ✅ 所有测试通过
- ✅ 测试覆盖率 ≥95%

---

### 📦 Task 1.11: Configuration Value Objects

**需求**: [DR-010](./requirements.md#dr-010-configuration-配置-领域模型)

#### 🔴 RED: 编写测试

**文件**: `tests/unit/domain/value_objects/test_configuration.py`

**测试用例**:
- `test_data_source_config_valid()`: 验证数据源配置有效性
- `test_data_source_config_invalid_path()`: 验证路径不存在抛出异常
- `test_model_config_valid()`: 验证模型配置有效性
- `test_backtest_config_valid()`: 验证回测配置有效性
- `test_backtest_config_invalid_rate()`: 验证费率范围检查

#### 🟢 GREEN: 实现代码

**文件**: `src/domain/value_objects/configuration.py`

#### 🔵 REFACTOR: 优化代码

**完成标准**:
- ✅ 所有测试通过
- ✅ 测试覆盖率 ≥95%

---

### 📦 Task 1.12: Domain Ports (接口定义)

**需求**: [DR-012](./requirements.md#dr-012-domain-ports-领域端口接口)

**注意**: Port接口无需测试(仅定义),但需确保:
- ✅ 接口定义清晰
- ✅ 使用ABC抽象基类
- ✅ 所有方法标记@abstractmethod
- ✅ 无任何外部框架依赖

**文件列表**:
- `src/domain/ports/stock_data_provider.py`: IStockDataProvider
- `src/domain/ports/model_trainer.py`: IModelTrainer
- `src/domain/ports/backtest_engine.py`: IBacktestEngine
- `src/domain/ports/signal_converter.py`: ISignalConverter
- `src/domain/ports/config_repository.py`: IConfigRepository
- `src/domain/ports/model_repository.py`: IModelRepository

**完成标准**:
- ✅ 所有Port接口定义完成
- ✅ 接口符合Domain需求规范
- ✅ 通过MyPy类型检查

---

## Phase 2: Use Cases层开发 (Week 4-6)

### 📦 Task 2.1: LoadStockDataUseCase

**需求**: [UC-001](./requirements.md#uc-001-load-stock-data-加载股票数据)

#### 🔴 RED: 编写测试

**文件**: `tests/unit/use_cases/data/test_load_stock_data.py`

**测试用例**:
- `test_load_stock_data_success()`: Mock IStockDataProvider,验证成功加载
- `test_load_stock_data_invalid_stock_code()`: 验证StockCode验证失败
- `test_load_stock_data_invalid_date_range()`: 验证DateRange验证失败
- `test_load_stock_data_provider_error()`: 验证数据源错误处理

**Mock对象**:
```python
from unittest.mock import AsyncMock
provider_mock = AsyncMock(spec=IStockDataProvider)
```

#### 🟢 GREEN: 实现代码

**文件**: `src/use_cases/data/load_stock_data.py`

**实现**:
```python
from domain.ports.stock_data_provider import IStockDataProvider
from domain.value_objects.stock_code import StockCode
from domain.value_objects.date_range import DateRange
from domain.entities.kline_data import KLineData

class LoadStockDataUseCase:
    def __init__(self, provider: IStockDataProvider):
        self.provider = provider

    async def execute(
        self,
        stock_code: StockCode,
        date_range: DateRange,
        kline_type: KLineType
    ) -> List[KLineData]:
        # 1. 验证输入
        # 2. 调用provider
        # 3. 验证输出
        # 4. 返回结果
        pass
```

#### 🔵 REFACTOR: 优化代码

**完成标准**:
- ✅ 所有测试通过
- ✅ 测试覆盖率 ≥90%
- ✅ 正确使用依赖注入

---

### 📦 Task 2.2: TrainModelUseCase

**需求**: [UC-002](./requirements.md#uc-002-train-model-训练模型)

#### 🔴 RED: 编写测试

**文件**: `tests/unit/use_cases/model/test_train_model.py`

**测试用例**:
- `test_train_model_success()`: Mock IModelTrainer,验证训练成功
- `test_train_model_validates_config()`: 验证配置参数验证
- `test_train_model_updates_status()`: 验证状态转换(UNTRAINED → TRAINING → TRAINED)
- `test_train_model_saves_to_repository()`: 验证保存到IModelRepository
- `test_train_model_publishes_event()`: 验证发布ModelTrained事件
- `test_train_model_metrics_below_threshold()`: 验证指标不达标处理
- `test_train_model_training_failure()`: 验证训练失败处理(状态→FAILED)

**Mock对象**:
```python
trainer_mock = AsyncMock(spec=IModelTrainer)
repository_mock = AsyncMock(spec=IModelRepository)
```

#### 🟢 GREEN: 实现代码

**文件**: `src/use_cases/model/train_model.py`

#### 🔵 REFACTOR: 优化代码

**完成标准**:
- ✅ 所有测试通过
- ✅ 测试覆盖率 ≥90%
- ✅ 事件发布机制正确

---

### 📦 Task 2.3: GeneratePredictionsUseCase

**需求**: [UC-003](./requirements.md#uc-003-generate-predictions-生成预测)

#### 🔴 RED: 编写测试

**文件**: `tests/unit/use_cases/model/test_generate_predictions.py`

**测试用例**:
- `test_generate_predictions_success()`: 验证预测生成成功
- `test_generate_predictions_model_not_found()`: 验证模型未找到异常
- `test_generate_predictions_model_not_ready()`: 验证模型状态不可用异常
- `test_generate_predictions_creates_batch()`: 验证创建PredictionBatch聚合
- `test_generate_predictions_publishes_event()`: 验证发布PredictionGenerated事件

#### 🟢 GREEN: 实现代码

**文件**: `src/use_cases/model/generate_predictions.py`

#### 🔵 REFACTOR: 优化代码

**完成标准**:
- ✅ 所有测试通过
- ✅ 测试覆盖率 ≥90%

---

### 📦 Task 2.4: ConvertPredictionsToSignalsUseCase

**需求**: [UC-004](./requirements.md#uc-004-convert-predictions-to-signals-预测转信号)

#### 🔴 RED: 编写测试

**文件**: `tests/unit/use_cases/signal/test_convert_predictions_to_signals.py`

**测试用例**:
- `test_convert_predictions_success()`: 验证转换成功
- `test_convert_with_top_k_strategy()`: 验证Top-K策略
- `test_convert_with_threshold_strategy()`: 验证阈值策略
- `test_convert_validates_strategy_params()`: 验证策略参数验证
- `test_convert_publishes_event()`: 验证发布SignalGenerated事件

#### 🟢 GREEN: 实现代码

**文件**: `src/use_cases/signal/convert_predictions_to_signals.py`

#### 🔵 REFACTOR: 优化代码

**完成标准**:
- ✅ 所有测试通过
- ✅ 测试覆盖率 ≥90%

---

### 📦 Task 2.5: RunBacktestUseCase

**需求**: [UC-005](./requirements.md#uc-005-run-backtest-运行回测)

#### 🔴 RED: 编写测试

**文件**: `tests/unit/use_cases/backtest/test_run_backtest.py`

**测试用例**:
- `test_run_backtest_success()`: Mock IBacktestEngine,验证回测成功
- `test_run_backtest_validates_config()`: 验证BacktestConfig验证
- `test_run_backtest_calculates_metrics()`: 验证回测指标计算
- `test_run_backtest_publishes_event()`: 验证发布BacktestCompleted事件
- `test_run_backtest_engine_error()`: 验证回测引擎错误处理

#### 🟢 GREEN: 实现代码

**文件**: `src/use_cases/backtest/run_backtest.py`

#### 🔵 REFACTOR: 优化代码

**完成标准**:
- ✅ 所有测试通过
- ✅ 测试覆盖率 ≥90%

---

### 📦 Task 2.6 ~ 2.10: 其他Use Cases

按照相同的TDD流程实现:
- Task 2.6: [CalculateIndicatorsUseCase](./requirements.md#uc-006-calculate-indicators-计算技术指标)
- Task 2.7: [ManagePortfolioUseCase](./requirements.md#uc-007-manage-portfolio-管理投资组合)
- Task 2.8: [LoadConfigurationUseCase](./requirements.md#uc-008-load-configuration-加载配置)
- Task 2.9: [SaveConfigurationUseCase](./requirements.md#uc-009-save-configuration-保存配置)
- Task 2.10: [AnalyzeBacktestResultUseCase](./requirements.md#uc-010-analyze-backtest-result-分析回测结果)

**每个Use Case完成标准**:
- ✅ 所有测试通过
- ✅ 测试覆盖率 ≥90%
- ✅ 正确使用Domain Ports
- ✅ 无直接框架依赖

---

## Phase 3: Adapters层开发 (Week 7-10)

### 📦 Task 3.1: HikyuuDataAdapter

**需求**: [AD-001](./requirements.md#ad-001-hikyuu-data-adapter)

#### 🔴 RED: 编写测试

**文件**: `tests/unit/adapters/hikyuu/test_data_adapter.py`

**测试用例**:
- `test_load_stock_data_calls_hikyuu_api()`: Mock hikyuu.Stock,验证API调用
- `test_load_stock_data_converts_to_domain()`: 验证Hikyuu → Domain转换
- `test_load_stock_data_handles_hikyuu_error()`: 验证Hikyuu错误处理
- `test_get_stock_list_calls_stock_manager()`: Mock hikyuu.StockManager
- `test_get_stock_list_converts_to_domain()`: 验证股票列表转换

**Mock对象**:
```python
from unittest.mock import MagicMock, patch

@patch('hikyuu.Stock')
def test_load_stock_data_calls_hikyuu_api(mock_stock):
    # Setup mock
    mock_stock.return_value.getKData.return_value = mock_kdata
    # Test adapter
    adapter = HikyuuDataAdapter()
    result = await adapter.load_stock_data(...)
    # Assertions
    mock_stock.assert_called_once_with("sh600000")
```

#### 🟢 GREEN: 实现代码

**文件**: `src/adapters/hikyuu/data_adapter.py`

**实现**:
```python
import hikyuu as hku
from domain.ports.stock_data_provider import IStockDataProvider
from domain.value_objects.stock_code import StockCode
from domain.entities.kline_data import KLineData

class HikyuuDataAdapter(IStockDataProvider):
    """Hikyuu数据适配器"""

    async def load_stock_data(
        self,
        code: StockCode,
        date_range: DateRange,
        kline_type: KLineType
    ) -> List[KLineData]:
        # 1. Domain → Hikyuu 转换
        stock = hku.Stock(code.value)
        query = self._build_query(date_range, kline_type)

        # 2. 调用Hikyuu API
        kdata = stock.getKData(query)

        # 3. Hikyuu → Domain 转换
        return self._to_domain_kline_data(kdata)

    def _to_domain_kline_data(self, kdata) -> List[KLineData]:
        """将Hikyuu KData转换为Domain KLineData"""
        pass
```

#### 🔵 REFACTOR: 优化代码

**完成标准**:
- ✅ 所有测试通过
- ✅ 测试覆盖率 ≥85%
- ✅ 正确实现IStockDataProvider接口
- ✅ Hikyuu依赖仅在Adapter层

---

### 📦 Task 3.2: QlibDataAdapter

**需求**: [AD-002](./requirements.md#ad-002-qlib-data-adapter)

#### 🔴 RED: 编写测试

**文件**: `tests/unit/adapters/qlib/test_data_adapter.py`

**测试用例**:
- `test_load_stock_data_calls_qlib_api()`: Mock qlib.data.D
- `test_load_stock_data_converts_to_domain()`: 验证Qlib → Domain转换
- `test_load_stock_data_handles_qlib_error()`: 验证Qlib错误处理

#### 🟢 GREEN: 实现代码

**文件**: `src/adapters/qlib/data_adapter.py`

**实现**:
```python
import qlib
from qlib.data import D
from domain.ports.stock_data_provider import IStockDataProvider

class QlibDataAdapter(IStockDataProvider):
    """Qlib数据适配器"""

    async def load_stock_data(
        self,
        code: StockCode,
        date_range: DateRange,
        kline_type: KLineType
    ) -> List[KLineData]:
        # 1. Domain → Qlib 转换
        instrument = code.value
        fields = ["$open", "$high", "$low", "$close", "$volume"]

        # 2. 调用Qlib API
        df = D.features(
            instruments=[instrument],
            fields=fields,
            start_time=date_range.start_date,
            end_time=date_range.end_date
        )

        # 3. Qlib DataFrame → Domain 转换
        return self._to_domain_kline_data(df)
```

#### 🔵 REFACTOR: 优化代码

**完成标准**:
- ✅ 所有测试通过
- ✅ 测试覆盖率 ≥85%

---

### 📦 Task 3.3: QlibModelTrainerAdapter

**需求**: [AD-003](./requirements.md#ad-003-qlib-model-trainer-adapter)

#### 🔴 RED: 编写测试

**文件**: `tests/unit/adapters/qlib/test_model_trainer_adapter.py`

**测试用例**:
- `test_train_calls_qlib_model()`: Mock qlib.model.LGBModel
- `test_train_converts_domain_to_qlib()`: 验证Domain Model → Qlib转换
- `test_train_converts_qlib_to_domain()`: 验证Qlib → Domain Model转换
- `test_predict_calls_qlib_model()`: Mock qlib.model.predict()
- `test_predict_converts_to_predictions()`: 验证预测结果转换

#### 🟢 GREEN: 实现代码

**文件**: `src/adapters/qlib/model_trainer_adapter.py`

**实现**:
```python
from qlib.model.gbdt import LGBModel
from domain.ports.model_trainer import IModelTrainer
from domain.entities.model import Model
from domain.entities.prediction import Prediction

class QlibModelTrainerAdapter(IModelTrainer):
    """Qlib模型训练适配器"""

    async def train(
        self,
        model: Model,
        features: pd.DataFrame,
        labels: pd.Series
    ) -> Model:
        # 1. 根据model.type创建Qlib模型
        qlib_model = self._create_qlib_model(model.type)

        # 2. 训练Qlib模型
        qlib_model.fit(features, labels)

        # 3. 计算指标并更新Domain Model
        metrics = self._calculate_metrics(qlib_model, features, labels)
        model.mark_as_trained(metrics)

        # 4. 保存Qlib模型状态到model
        model.qlib_model_state = qlib_model  # 需要序列化

        return model
```

#### 🔵 REFACTOR: 优化代码

**完成标准**:
- ✅ 所有测试通过
- ✅ 测试覆盖率 ≥85%
- ✅ 支持多种Qlib模型(LGBModel, MLP, LSTM)

---

### 📦 Task 3.4: HikyuuBacktestAdapter

**需求**: [AD-004](./requirements.md#ad-004-hikyuu-backtest-adapter)

#### 🔴 RED: 编写测试

**文件**: `tests/unit/adapters/hikyuu/test_backtest_adapter.py`

**测试用例**:
- `test_run_backtest_calls_hikyuu_portfolio()`: Mock hikyuu.Portfolio
- `test_run_backtest_converts_signals()`: 验证SignalBatch → Hikyuu信号转换
- `test_run_backtest_converts_result()`: 验证Hikyuu → BacktestResult转换
- `test_run_backtest_calculates_metrics()`: 验证回测指标计算

#### 🟢 GREEN: 实现代码

**文件**: `src/adapters/hikyuu/backtest_adapter.py`

**实现**:
```python
import hikyuu as hku
from domain.ports.backtest_engine import IBacktestEngine
from domain.aggregates.signal_batch import SignalBatch
from domain.entities.backtest_result import BacktestResult

class HikyuuBacktestAdapter(IBacktestEngine):
    """Hikyuu回测引擎适配器"""

    async def run_backtest(
        self,
        signals: SignalBatch,
        config: BacktestConfig,
        date_range: DateRange
    ) -> BacktestResult:
        # 1. 创建Hikyuu TradeManager
        tm = hku.crtTM(
            init_cash=float(config.initial_capital),
            cost_func=self._create_cost_func(config)
        )

        # 2. 将SignalBatch转换为Hikyuu信号
        sg = self._create_signal_generator(signals)

        # 3. 构建交易系统
        sys = hku.SYS_Simple(sg=sg, mm=mm, st=st, sp=sp)

        # 4. 运行回测
        pf = hku.PF_Simple(tm=tm)
        pf.run(sys, date_range.start_date, date_range.end_date)

        # 5. 转换为Domain BacktestResult
        return self._to_domain_backtest_result(pf)
```

#### 🔵 REFACTOR: 优化代码

**完成标准**:
- ✅ 所有测试通过
- ✅ 测试覆盖率 ≥85%

---

### 📦 Task 3.5 ~ 3.8: 其他Adapters

按照相同的TDD流程实现:
- Task 3.5: [SignalConverterAdapter](./requirements.md#ad-005-signal-converter-adapter)
- Task 3.6: [YAMLConfigRepository](./requirements.md#ad-006-yaml-config-repository)
- Task 3.7: [SQLiteModelRepository](./requirements.md#ad-007-sqlite-model-repository)
- Task 3.8: [CLI Interface Adapter](./requirements.md#ad-008-cli-interface-adapter)

**每个Adapter完成标准**:
- ✅ 所有测试通过
- ✅ 测试覆盖率 ≥85%
- ✅ 正确实现Port接口
- ✅ 框架依赖仅在Adapter层
- ✅ 数据转换准确(Framework ↔ Domain)

---

## Phase 4: Infrastructure层开发 (Week 11-12)

### 📦 Task 4.1: Dependency Injection Container

**文件**: `src/infrastructure/di/container.py`

**功能**:
- 使用dependency-injector实现DI容器
- 注册所有Adapters和Use Cases
- 提供容器初始化和配置

**测试**:
- `test_container_registers_all_adapters()`: 验证所有Adapter注册
- `test_container_registers_all_use_cases()`: 验证所有Use Case注册
- `test_container_resolves_dependencies()`: 验证依赖解析

**完成标准**:
- ✅ 所有测试通过
- ✅ 测试覆盖率 ≥88%

---

### 📦 Task 4.2: Logging Infrastructure

**文件**: `src/infrastructure/logging/logger.py`

**功能**:
- 使用Loguru实现日志管理
- 支持多级别日志(DEBUG/INFO/WARN/ERROR)
- 日志文件自动轮转和清理
- 敏感信息自动脱敏

**完成标准**:
- ✅ 所有测试通过
- ✅ 测试覆盖率 ≥88%

---

### 📦 Task 4.3: Configuration Management

**文件**: `src/infrastructure/config/settings.py`

**功能**:
- 使用Pydantic BaseSettings加载配置
- 支持环境变量覆盖
- 配置验证和类型检查

**完成标准**:
- ✅ 所有测试通过
- ✅ 测试覆盖率 ≥88%

---

### 📦 Task 4.4: Event Bus Infrastructure

**文件**: `src/infrastructure/events/event_bus.py`

**功能**:
- 实现简单的内存事件总线
- 支持Domain Events发布和订阅
- 异步事件处理

**完成标准**:
- ✅ 所有测试通过
- ✅ 测试覆盖率 ≥88%

---

## Phase 5: CLI开发 (Week 13)

### 📦 Task 5.1: CLI Entry Point

**文件**: `src/cli/main.py`

**功能**:
- 使用Click框架实现CLI
- 主命令: `hikyuu-qlib`
- 子命令: `data`, `train`, `predict`, `backtest`, `analyze`, `config`

**完成标准**:
- ✅ 所有CLI命令可用
- ✅ 参数验证准确
- ✅ 帮助文档完整

---

### 📦 Task 5.2 ~ 5.7: CLI子命令

按照相同的TDD流程实现:
- Task 5.2: `hikyuu-qlib data load`: 加载股票数据
- Task 5.3: `hikyuu-qlib train`: 训练模型
- Task 5.4: `hikyuu-qlib predict`: 生成预测
- Task 5.5: `hikyuu-qlib backtest`: 运行回测
- Task 5.6: `hikyuu-qlib analyze`: 分析结果
- Task 5.7: `hikyuu-qlib config`: 配置管理

**每个子命令完成标准**:
- ✅ 功能测试通过
- ✅ 参数验证准确
- ✅ 错误处理完善

---

## Phase 6: 集成测试 (Week 14)

### 📦 Task 6.1: Domain + Use Cases集成测试

**文件**: `tests/integration/test_domain_use_cases.py`

**测试用例**:
- `test_train_and_predict_workflow()`: 训练→预测完整流程
- `test_predict_and_convert_workflow()`: 预测→信号转换流程
- `test_convert_and_backtest_workflow()`: 信号→回测流程

**完成标准**:
- ✅ 所有集成测试通过
- ✅ 无跨层依赖泄漏

---

### 📦 Task 6.2: Use Cases + Adapters集成测试

**文件**: `tests/integration/test_use_cases_adapters.py`

**测试用例**:
- `test_load_data_with_hikyuu_adapter()`: Use Case + Hikyuu Adapter
- `test_load_data_with_qlib_adapter()`: Use Case + Qlib Adapter
- `test_train_with_qlib_adapter()`: Use Case + Qlib Model Trainer
- `test_backtest_with_hikyuu_adapter()`: Use Case + Hikyuu Backtest

**完成标准**:
- ✅ 所有集成测试通过
- ✅ Adapters正确实现Ports接口

---

### 📦 Task 6.3: End-to-End测试

**文件**: `tests/e2e/test_full_workflow.py`

**测试用例**:
- `test_full_workflow_hikyuu_to_qlib()`: Hikyuu数据→Qlib训练→Hikyuu回测
- `test_full_workflow_with_real_data()`: 使用真实数据测试(可选)

**完成标准**:
- ✅ 端到端流程测试通过
- ✅ 所有层协作正确

---

## Phase 7: 文档和部署 (Week 15)

### 📦 Task 7.1: API文档

**文件**: `docs/api/`

**内容**:
- Domain层API文档
- Use Cases层API文档
- Adapters层API文档

---

### 📦 Task 7.2: 用户手册

**文件**: `docs/user_guide.md`

**内容**:
- 安装指南
- 快速开始
- CLI命令参考
- 配置文件说明

---

### 📦 Task 7.3: 部署配置

**文件**: `pyproject.toml`, `setup.py`

**内容**:
- 依赖管理
- CLI entry points
- 打包配置

---

## 🎯 总体进度跟踪

### Domain层 (Week 1-3)

- [ ] Task 1.1: StockCode Value Object
- [ ] Task 1.2: Market Value Object
- [ ] Task 1.3: Stock Entity
- [ ] Task 1.4: DateRange Value Object
- [ ] Task 1.5: KLineData Entity
- [ ] Task 1.6: Model Entity
- [ ] Task 1.7: Prediction Entity and PredictionBatch Aggregate
- [ ] Task 1.8: TradingSignal Entity and SignalBatch Aggregate
- [ ] Task 1.9: Portfolio and Position Entities
- [ ] Task 1.10: BacktestResult and Trade Entities
- [ ] Task 1.11: Configuration Value Objects
- [ ] Task 1.12: Domain Ports

### Use Cases层 (Week 4-6)

- [ ] Task 2.1: LoadStockDataUseCase
- [ ] Task 2.2: TrainModelUseCase
- [ ] Task 2.3: GeneratePredictionsUseCase
- [ ] Task 2.4: ConvertPredictionsToSignalsUseCase
- [ ] Task 2.5: RunBacktestUseCase
- [ ] Task 2.6: CalculateIndicatorsUseCase
- [ ] Task 2.7: ManagePortfolioUseCase
- [ ] Task 2.8: LoadConfigurationUseCase
- [ ] Task 2.9: SaveConfigurationUseCase
- [ ] Task 2.10: AnalyzeBacktestResultUseCase

### Adapters层 (Week 7-10)

- [ ] Task 3.1: HikyuuDataAdapter
- [ ] Task 3.2: QlibDataAdapter
- [ ] Task 3.3: QlibModelTrainerAdapter
- [ ] Task 3.4: HikyuuBacktestAdapter
- [ ] Task 3.5: SignalConverterAdapter
- [ ] Task 3.6: YAMLConfigRepository
- [ ] Task 3.7: SQLiteModelRepository
- [ ] Task 3.8: CLI Interface Adapter

### Infrastructure层 (Week 11-12)

- [ ] Task 4.1: Dependency Injection Container
- [ ] Task 4.2: Logging Infrastructure
- [ ] Task 4.3: Configuration Management
- [ ] Task 4.4: Event Bus Infrastructure

### CLI层 (Week 13)

- [ ] Task 5.1: CLI Entry Point
- [ ] Task 5.2 ~ 5.7: CLI子命令

### 集成测试 (Week 14)

- [ ] Task 6.1: Domain + Use Cases集成测试
- [ ] Task 6.2: Use Cases + Adapters集成测试
- [ ] Task 6.3: End-to-End测试

### 文档和部署 (Week 15)

- [ ] Task 7.1: API文档
- [ ] Task 7.2: 用户手册
- [ ] Task 7.3: 部署配置

---

## 附录

### A. 旧版本任务对照表

| 旧任务模块 | 新Phase | 说明 |
|----------|--------|------|
| 数据流通模块 | Phase 1 (Domain) + Phase 3 (Adapters) | 拆分为Domain模型定义和Adapter实现 |
| 机器学习建模模块 | Phase 1 (Domain) + Phase 2 (Use Cases) + Phase 3 (Adapters) | 拆分为三层实现 |
| 策略执行模块 | Phase 1 (Domain) + Phase 2 (Use Cases) + Phase 3 (Adapters) | 拆分为三层实现 |
| 配置管理模块 | Phase 1 (Domain) + Phase 4 (Infrastructure) | 配置作为Domain Value Object |
| 复盘分析模块 | Phase 2 (Use Cases) | 分析作为Use Case |

### B. 参考文档

- [requirements.md v2.0](./requirements.md) - 需求规格说明书
- [design.md v2.0](./design.md) - 完整架构设计
- [ARCHITECTURE_MIGRATION_SUMMARY.md](./ARCHITECTURE_MIGRATION_SUMMARY.md) - 迁移指南
- [src/.claude.md](../src/.claude.md) - 开发总纲
- [src/ARCHITECTURE.md](../src/ARCHITECTURE.md) - 详细架构文档

---

**负责人**: Development Team
**最后更新**: 2025-11-11
**版本**: 2.0.0
