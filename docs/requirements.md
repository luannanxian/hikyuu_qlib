# 需求规格说明书 v2.0 - Hikyuu × Qlib 个人量化工作站

**版本**: 2.0.0
**日期**: 2025-11-11
**架构模式**: 六边形架构 + DDD

---

## 1. 项目概述

### 1.1 背景

随着人工智能技术在金融领域的快速发展,个人投资者对量化交易工具的需求日益增长。然而,现有的量化工具存在以下痛点:

- 数据获取和处理门槛高
- 机器学习建模技术复杂
- 策略验证和执行流程割裂
- 缺乏端到端的集成解决方案

为了解决这些问题,需要构建一套融合Hikyuu和Qlib优势的个人量化工作站,为个人投资者提供一站式AI建模与策略执行平台。

### 1.2 目标

**业务目标:**

- 为个人独立投资者提供桌面级量化工作站
- 实现AI建模与策略执行的完整闭环
- 降低机器学习在量化投资中的应用门槛

**技术目标:**

- 构建框架无关的领域模型层
- 实现清晰的依赖倒置(Adapters → Use Cases → Domain)
- 提供高测试覆盖率和可维护性保障

### 1.3 范围

**包含内容:**

- Domain层: 核心业务逻辑和领域模型
- Use Cases层: 应用业务场景编排
- Adapters层: Hikyuu/Qlib框架适配
- 端到端TDD开发流程

**不包含内容:**

- 企业级特性(如多用户管理、权限控制等)
- 实时交易执行(仅支持半自动执行)

### 1.4 开发总约束

**开发工作准则:**

1. **以暗猜接口为耻,以认真查阅为荣**: 所有接口设计必须基于现有文档,禁止猜测接口定义
2. **以模糊执行为耻,以寻求确认为荣**: 所有执行步骤必须明确,模糊需求需主动确认
3. **以盲想业务为耻,以人类确认为荣**: 业务需求必须通过用户确认,禁止主观假设
4. **以创造接口为耻,以复用现有为荣**: 优先复用现有接口,避免创造不必要的接口
5. **以跳过验证为耻,以主动测试为荣**: 所有功能必须经过验证,禁止跳过测试
6. **以破坏架构为耻,以遵循规范为荣**: 遵循现有架构规范,禁止破坏系统架构
7. **以假装理解为耻,以诚实无知为荣**: 遇到不理解的问题要诚实承认,禁止假装理解
8. **以盲目修改为耻,以谨慎重构为荣**: 修改代码要谨慎,禁止盲目修改现有功能

---

## 2. 领域需求 (Domain Requirements)

### 2.1 用户角色

| 角色名称 | 描述 | 主要使用场景 |
|----------|------|------|
| **量化爱好者** | 想体验机器学习择时/选股,降低数据准备与建模门槛的用户 | 学习AI建模,验证技术指标有效性 |
| **技术指标型交易者** | 期望自动化处理更多特征,利用AI提升策略效率的用户 | 批量测试技术指标组合,寻找最优参数 |
| **兼职自营投资者** | 希望快速试验新想法、采信AI信号,但仍保持人工把控的用户 | 快速试验策略,参考AI信号做决策 |

---

## 2.2 Domain层需求 (DR-001 ~ DR-012)

### DR-001: Stock (股票) 领域模型

**业务描述**: 定义股票领域实体及其业务规则

**Domain对象**:

- **Entity**: `Stock`
  - 属性: `code: StockCode`, `name: str`, `market: Market`, `is_active: bool`, `listing_date: date`
  - 业务规则:
    - `is_tradable() -> bool`: 判断股票是否可交易(需要is_active=True且非停牌)
    - `validate_trading_date(date) -> bool`: 验证交易日期是否有效
- **Value Object**: `StockCode`
  - 属性: `value: str`
  - 验证规则: 必须是8位字符格式(如"sh600000")
- **Value Object**: `Market`
  - 枚举值: `SH`, `SZ`, `BJ`

**验收标准**:

- Stock Entity实现完整业务规则
- StockCode格式验证准确无误
- 测试覆盖率 ≥95%

**优先级**: 高
**依赖关系**: 无

---

### DR-002: DateRange (日期范围) 领域模型

**业务描述**: 定义日期范围及其业务规则

**Domain对象**:

- **Value Object**: `DateRange`
  - 属性: `start_date: date`, `end_date: date`
  - 业务规则:
    - `validate() -> bool`: 确保start_date <= end_date
    - `contains(date) -> bool`: 判断日期是否在范围内
    - `overlap_with(other: DateRange) -> bool`: 判断两个日期范围是否重叠

**验收标准**:

- DateRange验证逻辑准确
- 边界条件处理正确
- 测试覆盖率 ≥95%

**优先级**: 高
**依赖关系**: 无

---

### DR-003: KLineData (K线数据) 领域模型

**业务描述**: 定义K线数据实体及其业务规则

**Domain对象**:

- **Entity**: `KLineData`
  - 属性: `stock_code: StockCode`, `timestamp: datetime`, `open: Decimal`, `high: Decimal`, `low: Decimal`, `close: Decimal`, `volume: int`, `amount: Decimal`
  - 业务规则:
    - `validate_ohlc() -> bool`: 验证OHLC关系(high >= max(open, close), low <= min(open, close))
    - `calculate_change_pct() -> Decimal`: 计算涨跌幅
- **Value Object**: `KLineType`
  - 枚举值: `MIN_1`, `MIN_5`, `DAY`, `WEEK`, `MONTH`

**验收标准**:

- KLineData OHLC验证准确
- 价格计算逻辑正确
- 测试覆盖率 ≥95%

**优先级**: 高
**依赖关系**: DR-001, DR-002

---

### DR-004: TechnicalIndicator (技术指标) 领域模型

**业务描述**: 定义技术指标及其计算规则

**Domain对象**:

- **Entity**: `Indicator`
  - 属性: `name: str`, `parameters: Dict[str, Any]`, `values: List[Decimal]`
  - 业务规则:
    - `validate_parameters() -> bool`: 验证参数有效性
- **Value Object**: `IndicatorType`
  - 枚举值: `MA`, `EMA`, `MACD`, `RSI`, `BOLL`, `KDJ`
- **Value Object**: `IndicatorParameters`
  - 属性: 根据不同指标类型定义(如MA的period参数)

**验收标准**:

- 指标参数验证准确
- 支持常用技术指标类型
- 测试覆盖率 ≥95%

**优先级**: 中
**依赖关系**: DR-003

---

### DR-005: Model (模型) 领域模型

**业务描述**: 定义机器学习模型实体及其生命周期管理

**Domain对象**:

- **Entity**: `Model`
  - 属性: `id: ModelId`, `type: ModelType`, `parameters: ModelParameters`, `metrics: ModelMetrics`, `status: ModelStatus`, `created_at: datetime`
  - 业务规则:
    - `mark_as_trained(metrics: ModelMetrics) -> None`: 标记为已训练状态
    - `validate_metrics(threshold: Dict) -> bool`: 验证模型指标是否达标
    - `is_ready_for_prediction() -> bool`: 判断是否可用于预测
- **Value Object**: `ModelId`
  - 属性: `value: str` (UUID格式)
- **Value Object**: `ModelType`
  - 枚举值: `LGB`, `XGB`, `MLP`, `LSTM`, `GRU`
- **Value Object**: `ModelStatus`
  - 枚举值: `UNTRAINED`, `TRAINING`, `TRAINED`, `FAILED`
- **Value Object**: `ModelMetrics`
  - 属性: `ic: Decimal`, `icir: Decimal`, `rank_ic: Decimal`, `mse: Decimal`

**验收标准**:

- Model生命周期状态转换正确
- 指标验证逻辑准确
- 测试覆盖率 ≥95%

**优先级**: 高
**依赖关系**: 无

---

### DR-006: Prediction (预测) 领域模型

**业务描述**: 定义预测结果及其业务规则

**Domain对象**:

- **Entity**: `Prediction`
  - 属性: `model_id: ModelId`, `stock_code: StockCode`, `timestamp: datetime`, `score: Decimal`, `confidence: Decimal`
  - 业务规则:
    - `is_above_threshold(threshold: Decimal) -> bool`: 判断分数是否超过阈值
    - `normalize_score(method: str) -> Decimal`: 标准化预测分数
- **Value Object**: `PredictionScore`
  - 属性: `value: Decimal`
  - 验证规则: -1.0 <= value <= 1.0
- **Aggregate**: `PredictionBatch`
  - 属性: `predictions: List[Prediction]`, `model_id: ModelId`, `generated_at: datetime`
  - 业务规则:
    - `get_top_k(k: int) -> List[Prediction]`: 获取Top-K预测结果
    - `filter_by_threshold(threshold: Decimal) -> List[Prediction]`: 按阈值过滤

**验收标准**:

- Prediction分数验证准确
- PredictionBatch聚合逻辑正确
- 测试覆盖率 ≥95%

**优先级**: 高
**依赖关系**: DR-001, DR-005

---

### DR-007: Signal (信号) 领域模型

**业务描述**: 定义交易信号及其业务规则

**Domain对象**:

- **Entity**: `TradingSignal`
  - 属性: `stock_code: StockCode`, `timestamp: datetime`, `direction: SignalDirection`, `strength: Decimal`, `source: SignalSource`
  - 业务规则:
    - `is_buy_signal() -> bool`: 判断是否为买入信号
    - `is_sell_signal() -> bool`: 判断是否为卖出信号
    - `get_position_size(capital: Decimal) -> Decimal`: 根据信号强度计算持仓量
- **Value Object**: `SignalDirection`
  - 枚举值: `BUY`, `SELL`, `HOLD`
- **Value Object**: `SignalSource`
  - 枚举值: `TECHNICAL`, `ML_PREDICTION`, `HYBRID`
- **Aggregate**: `SignalBatch`
  - 属性: `signals: List[TradingSignal]`, `generated_at: datetime`
  - 业务规则:
    - `filter_by_direction(direction: SignalDirection) -> List[TradingSignal]`
    - `get_buy_signals() -> List[TradingSignal]`

**验收标准**:

- TradingSignal业务规则准确
- SignalBatch聚合逻辑正确
- 测试覆盖率 ≥95%

**优先级**: 高
**依赖关系**: DR-001, DR-006

---

### DR-008: Portfolio (投资组合) 领域模型

**业务描述**: 定义投资组合及其管理规则

**Domain对象**:

- **Entity**: `Portfolio`
  - 属性: `id: PortfolioId`, `name: str`, `positions: List[Position]`, `cash: Decimal`, `total_value: Decimal`
  - 业务规则:
    - `add_position(position: Position) -> None`: 添加持仓
    - `remove_position(stock_code: StockCode) -> None`: 移除持仓
    - `calculate_total_value() -> Decimal`: 计算总市值
    - `get_position_weight(stock_code: StockCode) -> Decimal`: 计算持仓权重
- **Entity**: `Position`
  - 属性: `stock_code: StockCode`, `quantity: int`, `cost_price: Decimal`, `current_price: Decimal`
  - 业务规则:
    - `calculate_profit_loss() -> Decimal`: 计算盈亏
    - `calculate_return_pct() -> Decimal`: 计算收益率
- **Value Object**: `PortfolioId`
  - 属性: `value: str`

**验收标准**:

- Portfolio持仓管理逻辑准确
- Position盈亏计算正确
- 测试覆盖率 ≥95%

**优先级**: 中
**依赖关系**: DR-001

---

### DR-009: BacktestResult (回测结果) 领域模型

**业务描述**: 定义回测结果及其分析规则

**Domain对象**:

- **Entity**: `BacktestResult`
  - 属性: `id: str`, `strategy_name: str`, `start_date: date`, `end_date: date`, `metrics: BacktestMetrics`, `trades: List[Trade]`
  - 业务规则:
    - `calculate_sharpe_ratio() -> Decimal`: 计算夏普比率
    - `calculate_max_drawdown() -> Decimal`: 计算最大回撤
    - `get_win_rate() -> Decimal`: 计算胜率
- **Value Object**: `BacktestMetrics`
  - 属性: `total_return: Decimal`, `annual_return: Decimal`, `volatility: Decimal`, `sharpe: Decimal`, `max_drawdown: Decimal`
- **Entity**: `Trade`
  - 属性: `stock_code: StockCode`, `entry_time: datetime`, `exit_time: datetime`, `entry_price: Decimal`, `exit_price: Decimal`, `quantity: int`
  - 业务规则:
    - `calculate_profit() -> Decimal`: 计算交易盈亏
    - `calculate_hold_days() -> int`: 计算持有天数

**验收标准**:

- BacktestResult指标计算准确
- Trade盈亏计算正确
- 测试覆盖率 ≥95%

**优先级**: 中
**依赖关系**: DR-001, DR-008

---

### DR-010: Configuration (配置) 领域模型

**业务描述**: 定义系统配置及其验证规则

**Domain对象**:

- **Value Object**: `DataSourceConfig`
  - 属性: `hikyuu_data_dir: str`, `qlib_data_dir: str`, `cache_dir: str`
  - 验证规则: 路径必须存在且可访问
- **Value Object**: `ModelConfig`
  - 属性: `model_type: ModelType`, `parameters: Dict`, `training_window: int`
  - 验证规则: 参数必须符合模型类型要求
- **Value Object**: `BacktestConfig`
  - 属性: `initial_capital: Decimal`, `commission_rate: Decimal`, `slippage: Decimal`
  - 验证规则: 所有费率必须在合理范围内(0-1)

**验收标准**:

- Configuration验证逻辑准确
- 支持配置序列化/反序列化
- 测试覆盖率 ≥95%

**优先级**: 中
**依赖关系**: DR-005

---

### DR-011: Domain Events (领域事件)

**业务描述**: 定义领域事件及其发布规则

**Domain对象**:

- **Domain Event**: `ModelTrained`
  - 属性: `model_id: ModelId`, `metrics: ModelMetrics`, `occurred_at: datetime`
- **Domain Event**: `PredictionGenerated`
  - 属性: `model_id: ModelId`, `predictions_count: int`, `occurred_at: datetime`
- **Domain Event**: `SignalGenerated`
  - 属性: `signals_count: int`, `buy_count: int`, `sell_count: int`, `occurred_at: datetime`
- **Domain Event**: `BacktestCompleted`
  - 属性: `result_id: str`, `metrics: BacktestMetrics`, `occurred_at: datetime`

**验收标准**:

- 事件定义清晰
- 事件数据完整
- 测试覆盖率 ≥95%

**优先级**: 低
**依赖关系**: DR-005, DR-006, DR-007, DR-009

---

### DR-012: Domain Ports (领域端口接口)

**业务描述**: 定义Domain层对外部依赖的抽象接口

**Port接口**:

#### IStockDataProvider

```python
class IStockDataProvider(ABC):
    """股票数据提供者接口"""

    @abstractmethod
    async def load_stock_data(
        self,
        code: StockCode,
        date_range: DateRange,
        kline_type: KLineType
    ) -> List[KLineData]:
        """加载股票K线数据"""
        pass

    @abstractmethod
    async def get_stock_list(self, market: Market) -> List[Stock]:
        """获取股票列表"""
        pass
```

#### IModelTrainer

```python
class IModelTrainer(ABC):
    """模型训练接口"""

    @abstractmethod
    async def train(
        self,
        model: Model,
        features: pd.DataFrame,
        labels: pd.Series
    ) -> Model:
        """训练模型"""
        pass

    @abstractmethod
    async def predict(
        self,
        model: Model,
        features: pd.DataFrame
    ) -> List[Prediction]:
        """预测"""
        pass
```

#### IBacktestEngine

```python
class IBacktestEngine(ABC):
    """回测引擎接口"""

    @abstractmethod
    async def run_backtest(
        self,
        signals: SignalBatch,
        config: BacktestConfig,
        date_range: DateRange
    ) -> BacktestResult:
        """运行回测"""
        pass
```

#### ISignalConverter

```python
class ISignalConverter(ABC):
    """信号转换接口"""

    @abstractmethod
    async def convert_predictions_to_signals(
        self,
        predictions: PredictionBatch,
        strategy_params: Dict
    ) -> SignalBatch:
        """将预测转换为交易信号"""
        pass
```

#### IConfigRepository

```python
class IConfigRepository(ABC):
    """配置仓储接口"""

    @abstractmethod
    async def load_config(self, config_type: str) -> Configuration:
        """加载配置"""
        pass

    @abstractmethod
    async def save_config(self, config: Configuration) -> None:
        """保存配置"""
        pass
```

#### IModelRepository

```python
class IModelRepository(ABC):
    """模型仓储接口"""

    @abstractmethod
    async def save(self, model: Model) -> None:
        """保存模型"""
        pass

    @abstractmethod
    async def find_by_id(self, model_id: ModelId) -> Model:
        """根据ID查找模型"""
        pass
```

**验收标准**:

- Port接口定义清晰
- 遵循依赖倒置原则
- 无外部框架依赖

**优先级**: 高
**依赖关系**: DR-001 ~ DR-010

---

## 3. Use Case层需求 (UC-001 ~ UC-010)

### UC-001: Load Stock Data (加载股票数据)

**业务描述**: 从数据源加载股票K线数据到系统

**输入**:

- `stock_code: StockCode`
- `date_range: DateRange`
- `kline_type: KLineType`

**输出**:

- `List[KLineData]`

**业务流程**:

1. 验证StockCode和DateRange
2. 调用IStockDataProvider.load_stock_data()
3. 验证返回数据的完整性
4. 返回KLineData列表

**异常处理**:

- StockCode格式无效 → 抛出ValidationError
- DateRange无效 → 抛出ValidationError
- 数据加载失败 → 抛出DataLoadError

**验收标准**:

- 数据加载准确
- 异常处理完善
- 测试覆盖率 ≥90%

**优先级**: 高
**依赖关系**: DR-001, DR-002, DR-003, DR-012

---

### UC-002: Train Model (训练模型)

**业务描述**: 使用特征数据训练机器学习模型

**输入**:

- `model_config: ModelConfig`
- `features: pd.DataFrame`
- `labels: pd.Series`

**输出**:

- `Model` (trained)

**业务流程**:

1. 验证ModelConfig参数
2. 创建Model Entity (status=UNTRAINED)
3. 调用IModelTrainer.train()
4. 更新Model状态为TRAINED
5. 验证ModelMetrics是否达标
6. 保存Model到IModelRepository
7. 发布ModelTrained事件

**异常处理**:

- 参数验证失败 → 抛出ValidationError
- 训练失败 → 更新Model状态为FAILED
- 指标不达标 → 抛出MetricsThresholdError

**验收标准**:

- 模型训练成功
- 状态转换正确
- 测试覆盖率 ≥90%

**优先级**: 高
**依赖关系**: DR-005, DR-010, DR-012

---

### UC-003: Generate Predictions (生成预测)

**业务描述**: 使用已训练模型生成预测结果

**输入**:

- `model_id: ModelId`
- `features: pd.DataFrame`

**输出**:

- `PredictionBatch`

**业务流程**:

1. 从IModelRepository查找Model
2. 验证Model状态(is_ready_for_prediction)
3. 调用IModelTrainer.predict()
4. 创建PredictionBatch聚合
5. 发布PredictionGenerated事件
6. 返回PredictionBatch

**异常处理**:

- Model未找到 → 抛出ModelNotFoundError
- Model状态不可用 → 抛出ModelNotReadyError
- 预测失败 → 抛出PredictionError

**验收标准**:

- 预测结果准确
- 批量处理正确
- 测试覆盖率 ≥90%

**优先级**: 高
**依赖关系**: DR-005, DR-006, DR-012

---

### UC-004: Convert Predictions to Signals (预测转信号)

**业务描述**: 将模型预测结果转换为交易信号

**输入**:

- `predictions: PredictionBatch`
- `strategy_params: Dict` (如top_k, threshold等)

**输出**:

- `SignalBatch`

**业务流程**:

1. 验证strategy_params
2. 根据策略参数过滤预测(如get_top_k, filter_by_threshold)
3. 调用ISignalConverter.convert_predictions_to_signals()
4. 创建SignalBatch聚合
5. 发布SignalGenerated事件
6. 返回SignalBatch

**异常处理**:

- 参数验证失败 → 抛出ValidationError
- 转换失败 → 抛出SignalConversionError

**验收标准**:

- 信号转换逻辑准确
- 支持多种策略参数
- 测试覆盖率 ≥90%

**优先级**: 高
**依赖关系**: DR-006, DR-007, DR-012

---

### UC-005: Run Backtest (运行回测)

**业务描述**: 使用交易信号运行策略回测

**输入**:

- `signals: SignalBatch`
- `backtest_config: BacktestConfig`
- `date_range: DateRange`

**输出**:

- `BacktestResult`

**业务流程**:

1. 验证BacktestConfig和DateRange
2. 调用IBacktestEngine.run_backtest()
3. 创建BacktestResult Entity
4. 计算各项回测指标
5. 发布BacktestCompleted事件
6. 返回BacktestResult

**异常处理**:

- 配置验证失败 → 抛出ValidationError
- 回测失败 → 抛出BacktestError

**验收标准**:

- 回测指标计算准确
- 支持多种回测参数
- 测试覆盖率 ≥90%

**优先级**: 高
**依赖关系**: DR-007, DR-009, DR-010, DR-012

---

### UC-006: Calculate Indicators (计算技术指标)

**业务描述**: 基于K线数据计算技术指标

**输入**:

- `kline_data: List[KLineData]`
- `indicator_type: IndicatorType`
- `parameters: IndicatorParameters`

**输出**:

- `Indicator`

**业务流程**:

1. 验证IndicatorParameters
2. 根据indicator_type选择计算方法
3. 计算指标值
4. 创建Indicator Entity
5. 返回Indicator

**异常处理**:

- 参数验证失败 → 抛出ValidationError
- 数据不足 → 抛出InsufficientDataError
- 计算失败 → 抛出IndicatorCalculationError

**验收标准**:

- 指标计算准确
- 支持常用技术指标
- 测试覆盖率 ≥90%

**优先级**: 中
**依赖关系**: DR-003, DR-004

---

### UC-007: Manage Portfolio (管理投资组合)

**业务描述**: 根据交易信号管理投资组合

**输入**:

- `portfolio: Portfolio`
- `signals: SignalBatch`
- `current_prices: Dict[StockCode, Decimal]`

**输出**:

- `Portfolio` (updated)

**业务流程**:

1. 遍历signals中的买入信号
2. 根据signal.strength计算持仓量
3. 调用portfolio.add_position()
4. 遍历signals中的卖出信号
5. 调用portfolio.remove_position()
6. 更新portfolio.total_value
7. 返回更新后的Portfolio

**异常处理**:

- 资金不足 → 抛出InsufficientFundsError
- 持仓不存在 → 抛出PositionNotFoundError

**验收标准**:

- 持仓管理逻辑准确
- 资金管理正确
- 测试覆盖率 ≥90%

**优先级**: 中
**依赖关系**: DR-007, DR-008

---

### UC-008: Load Configuration (加载配置)

**业务描述**: 从配置仓储加载系统配置

**输入**:

- `config_type: str` (如"data_source", "model", "backtest")

**输出**:

- `Configuration`

**业务流程**:

1. 调用IConfigRepository.load_config()
2. 验证配置有效性
3. 返回Configuration

**异常处理**:

- 配置不存在 → 抛出ConfigNotFoundError
- 配置验证失败 → 抛出ConfigValidationError

**验收标准**:

- 配置加载准确
- 验证逻辑完善
- 测试覆盖率 ≥90%

**优先级**: 中
**依赖关系**: DR-010, DR-012

---

### UC-009: Save Configuration (保存配置)

**业务描述**: 保存系统配置到配置仓储

**输入**:

- `config: Configuration`

**输出**:

- `None`

**业务流程**:

1. 验证配置有效性
2. 调用IConfigRepository.save_config()
3. 返回成功

**异常处理**:

- 配置验证失败 → 抛出ValidationError
- 保存失败 → 抛出ConfigSaveError

**验收标准**:

- 配置保存成功
- 验证逻辑完善
- 测试覆盖率 ≥90%

**优先级**: 中
**依赖关系**: DR-010, DR-012

---

### UC-010: Analyze Backtest Result (分析回测结果)

**业务描述**: 对回测结果进行详细分析

**输入**:

- `backtest_result: BacktestResult`

**输出**:

- `Dict[str, Any]` (分析报告)

**业务流程**:

1. 计算各项绩效指标(sharpe, max_drawdown, win_rate等)
2. 分析交易分布(买入/卖出次数、持仓时间等)
3. 生成分析报告
4. 返回报告Dict

**异常处理**:

- 数据不足 → 抛出InsufficientDataError

**验收标准**:

- 分析指标准确
- 报告格式清晰
- 测试覆盖率 ≥90%

**优先级**: 中
**依赖关系**: DR-009

---

## 4. Adapter层需求 (AD-001 ~ AD-008)

### AD-001: Hikyuu Data Adapter

**业务描述**: 实现IStockDataProvider接口,适配Hikyuu数据源

**实现**:

- 实现`load_stock_data()`: 调用hikyuu API加载K线数据并转换为Domain对象
- 实现`get_stock_list()`: 调用hikyuu.StockManager获取股票列表

**验收标准**:

- 正确适配Hikyuu API
- 数据转换准确(Hikyuu → Domain)
- 测试覆盖率 ≥85%

**优先级**: 高
**依赖关系**: DR-012

---

### AD-002: Qlib Data Adapter

**业务描述**: 实现IStockDataProvider接口,适配Qlib数据源

**实现**:

- 实现`load_stock_data()`: 调用qlib.data.D加载数据并转换为Domain对象
- 实现`get_stock_list()`: 从Qlib获取股票列表

**验收标准**:

- 正确适配Qlib API
- 数据转换准确(Qlib → Domain)
- 测试覆盖率 ≥85%

**优先级**: 高
**依赖关系**: DR-012

---

### AD-003: Qlib Model Trainer Adapter

**业务描述**: 实现IModelTrainer接口,适配Qlib模型训练

**实现**:

- 实现`train()`: 调用qlib.model训练模型并转换为Domain对象
- 实现`predict()`: 调用qlib.model.predict()并转换为Prediction列表

**验收标准**:

- 正确适配Qlib模型API
- 支持LGBModel、MLP、LSTM等模型
- 测试覆盖率 ≥85%

**优先级**: 高
**依赖关系**: DR-012

---

### AD-004: Hikyuu Backtest Adapter

**业务描述**: 实现IBacktestEngine接口,适配Hikyuu回测引擎

**实现**:

- 实现`run_backtest()`: 调用hikyuu.Portfolio/TradeManager运行回测并转换为Domain对象

**验收标准**:

- 正确适配Hikyuu回测API
- 回测结果转换准确
- 测试覆盖率 ≥85%

**优先级**: 高
**依赖关系**: DR-012

---

### AD-005: Signal Converter Adapter

**业务描述**: 实现ISignalConverter接口,将预测转换为交易信号

**实现**:

- 实现`convert_predictions_to_signals()`: 根据策略参数转换Prediction为TradingSignal

**验收标准**:

- 转换逻辑准确
- 支持多种转换策略(Top-K、阈值过滤等)
- 测试覆盖率 ≥85%

**优先级**: 高
**依赖关系**: DR-012

---

### AD-006: YAML Config Repository

**业务描述**: 实现IConfigRepository接口,使用YAML文件存储配置

**实现**:

- 实现`load_config()`: 从YAML文件加载配置
- 实现`save_config()`: 保存配置到YAML文件

**验收标准**:

- YAML序列化/反序列化准确
- 配置验证完善
- 测试覆盖率 ≥85%

**优先级**: 中
**依赖关系**: DR-012

---

### AD-007: SQLite Model Repository

**业务描述**: 实现IModelRepository接口,使用SQLite存储模型元数据

**实现**:

- 实现`save()`: 保存Model元数据到SQLite
- 实现`find_by_id()`: 根据ModelId查询Model

**验收标准**:

- 持久化逻辑准确
- 支持模型版本管理
- 测试覆盖率 ≥85%

**优先级**: 中
**依赖关系**: DR-012

---

### AD-008: CLI Interface Adapter

**业务描述**: 提供命令行接口调用Use Cases

**实现**:

- 使用Click框架实现CLI
- 支持命令: `train`, `predict`, `backtest`, `analyze`

**验收标准**:

- CLI功能完整
- 参数验证准确
- 测试覆盖率 ≥85%

**优先级**: 高
**依赖关系**: UC-001 ~ UC-010

---

## 5. 用户故事

### 5.1 数据准备流程

**作为** 量化爱好者
**我想要** 通过CLI加载Hikyuu数据到系统
**以便于** 快速开始机器学习建模

**验收条件**:

- 执行`hikyuu-qlib data load --code sh600000 --start 2020-01-01`
- 数据加载成功并显示统计信息
- 数据存储在Domain层可识别的格式

---

### 5.2 模型训练流程

**作为** 技术指标型交易者
**我想要** 使用CLI训练AI模型
**以便于** 验证技术指标的预测能力

**验收条件**:

- 执行`hikyuu-qlib train --config model_config.yaml`
- 模型训练成功并保存
- 显示训练指标(IC, ICIR等)

---

### 5.3 策略验证流程

**作为** 兼职自营投资者
**我想要** 将AI预测转换为交易信号并回测
**以便于** 验证策略有效性

**验收条件**:

- 执行`hikyuu-qlib backtest --model-id xxx --config backtest_config.yaml`
- 回测成功并生成报告
- 显示关键指标(夏普比率、最大回撤等)

---

## 6. 非功能需求

### 6.1 测试覆盖率

- Domain层: ≥95%
- Use Cases层: ≥90%
- Adapters层: ≥85%
- Infrastructure层: ≥88%

### 6.2 架构约束

- Domain层零外部依赖
- Use Cases层只依赖Domain Ports
- Adapters层实现Ports接口
- 严格遵循依赖倒置原则

### 6.3 开发流程

- 所有开发必须遵循TDD (Red-Green-Refactor)
- 先写测试,后写实现
- 测试必须先失败(Red),再通过(Green)

### 6.4 代码质量

- 使用Black格式化代码
- 使用Ruff进行Lint检查
- 使用MyPy进行类型检查
- Pre-commit Hook自动检查

---

## 7. 依赖关系

### 7.1 外部框架

- Hikyuu: 仅在Adapters层使用
- Qlib: 仅在Adapters层使用
- Python 3.8+
- Pytest: 测试框架
- Click: CLI框架

### 7.2 内部依赖

- Domain层: 无内部依赖
- Use Cases层: 依赖Domain层
- Adapters层: 依赖Domain层和Use Cases层
- Infrastructure层: 依赖所有层

---

## 附录

### A. 旧版本需求对照表

| 旧需求ID | 新需求ID | 说明 |
|---------|---------|------|
| FR-001 | DR-001, DR-003, DR-012 | 数据准备转换为Domain模型定义 |
| FR-002 | AD-001, AD-002 | 数据加载器转换为Adapter实现 |
| FR-003 | DR-004, UC-006 | 技术指标转换为Domain对象和Use Case |
| FR-004 | UC-002, UC-003, AD-003 | 模型训练转换为Use Case和Adapter |
| FR-005 | DR-011 | 实验记录转换为Domain Events |
| FR-006 | DR-010 | 配置管理转换为Domain Value Object |
| FR-007 | DR-005 | 模型透明性转换为Domain Entity |
| FR-008 | UC-004, AD-005 | 信号转换为Use Case和Adapter |
| FR-009 | UC-005, AD-004 | 回测转换为Use Case和Adapter |
| FR-010 | UC-007 | 调仓建议转换为Use Case |
| FR-011 | DR-010, UC-008, UC-009, AD-006 | 配置管理转换为Domain + Use Cases + Adapter |
| FR-012 | AD-008 | 示例策略转换为CLI Adapter |
| FR-013 | Infrastructure层 | 日志监控移到Infrastructure层 |
| FR-014 | UC-010 | 复盘工具转换为Use Case |

### B. 参考文档

- [design.md v2.0](./design.md) - 完整架构设计
- [ARCHITECTURE_MIGRATION_SUMMARY.md](./ARCHITECTURE_MIGRATION_SUMMARY.md) - 迁移指南
- [src/.claude.md](../src/.claude.md) - 开发总纲
- [src/ARCHITECTURE.md](../src/ARCHITECTURE.md) - 详细架构文档

---

**负责人**: Architecture Team
**最后更新**: 2025-11-11
**版本**: 2.0.0
