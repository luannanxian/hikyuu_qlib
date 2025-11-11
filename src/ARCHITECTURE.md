# Hikyuu × Qlib 架构文档

## 架构概览

本项目采用 **Hexagonal Architecture (六边形架构)** + **Domain-Driven Design (领域驱动设计)** 模式,实现高内聚、低耦合、可测试的量化交易系统。

## 核心架构原则

### 1. 依赖规则 (Dependency Rule)

```
┌─────────────────────────────────────────┐
│   Adapters / Infrastructure            │  ← 外层 (依赖内层)
│   - Hikyuu/Qlib 框架封装                │
│   - 数据库、CLI、API                     │
│   - 配置、日志                           │
└─────────────┬───────────────────────────┘
              │ 依赖
┌─────────────▼───────────────────────────┐
│   Use Cases                              │  ← 中层 (应用逻辑)
│   - 编排业务流程                          │
│   - 只依赖 Domain                        │
└─────────────┬───────────────────────────┘
              │ 依赖
┌─────────────▼───────────────────────────┐
│   Domain (核心)                          │  ← 内层 (业务规则)
│   - Entities, Value Objects              │
│   - Ports (接口定义)                      │
│   - 零外部依赖                            │
└──────────────────────────────────────────┘

规则: 依赖只能向内,内层不知道外层的存在
```

### 2. 端口和适配器 (Ports and Adapters)

```
                  ┌─────────────────┐
                  │   Use Cases     │
                  │  (应用逻辑)      │
                  └────────┬────────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
         Port │       Port │       Port │
  (IDataProvider)  (IModelTrainer)  (IBacktest)
              │            │            │
       ┌──────▼──┐  ┌─────▼────┐  ┌───▼──────┐
       │ Hikyuu  │  │   Qlib   │  │ Hikyuu   │
       │ Adapter │  │ Adapter  │  │ Adapter  │
       └─────────┘  └──────────┘  └──────────┘

特点:
- Domain 定义 Ports (接口)
- Adapters 实现 Ports
- 可轻松替换实现 (Mock/Real)
```

## 目录结构

```
src/
├── domain/                    # 核心领域层 (最内层)
│   ├── entities/              # 实体 (有 ID,可变)
│   │   ├── stock.py           # 股票实体
│   │   ├── model.py           # 模型实体
│   │   └── order.py           # 订单实体
│   ├── value_objects/         # 值对象 (无 ID,不可变)
│   │   ├── stock_code.py      # 股票代码
│   │   ├── price.py           # 价格
│   │   ├── market.py          # 市场
│   │   └── date_range.py      # 日期范围
│   ├── aggregates/            # 聚合根 (一致性边界)
│   │   ├── trading_day.py     # 交易日数据
│   │   └── portfolio.py       # 投资组合
│   ├── events/                # 领域事件
│   │   ├── model_trained.py   # 模型训练完成
│   │   └── bar_added.py       # K线添加
│   ├── ports/                 # 端口接口 (由 Domain 定义)
│   │   ├── stock_data_provider.py      # 数据提供者
│   │   ├── model_trainer.py            # 模型训练器
│   │   ├── backtest_engine.py          # 回测引擎
│   │   └── experiment_recorder.py      # 实验记录器
│   └── services/              # 领域服务
│       ├── price_adjustment_service.py # 价格复权
│       └── indicator_service.py        # 指标计算
│
├── use_cases/                 # 应用层 (业务流程编排)
│   ├── data/
│   │   ├── load_stock_data.py          # UC: 加载股票数据
│   │   └── convert_data_format.py      # UC: 转换数据格式
│   ├── models/
│   │   ├── train_model.py              # UC: 训练模型
│   │   └── generate_predictions.py     # UC: 生成预测
│   ├── strategies/
│   │   ├── run_backtest.py             # UC: 执行回测
│   │   └── generate_signals.py         # UC: 生成信号
│   └── analysis/
│       └── generate_report.py          # UC: 生成报告
│
├── adapters/                  # 适配器层 (技术实现)
│   ├── hikyuu/                # Hikyuu 适配器
│   │   ├── hikyuu_data_adapter.py      # 实现 IStockDataProvider
│   │   ├── hikyuu_backtest_adapter.py  # 实现 IBacktestEngine
│   │   └── hikyuu_indicator_adapter.py # 实现 IIndicatorCalculator
│   ├── qlib/                  # Qlib 适配器
│   │   ├── qlib_data_adapter.py        # 实现 IDataProvider
│   │   ├── qlib_model_adapter.py       # 实现 IModelTrainer
│   │   └── qlib_prediction_adapter.py  # 实现 IPredictionGenerator
│   ├── repositories/          # 数据持久化
│   │   ├── postgres_model_repository.py
│   │   └── redis_cache_repository.py
│   └── controllers/           # 外部接口
│       ├── cli/               # 命令行接口
│       │   ├── data_cli.py
│       │   ├── train_cli.py
│       │   └── backtest_cli.py
│       └── api/               # REST API (可选)
│           └── fastapi_app.py
│
├── infrastructure/            # 基础设施层
│   ├── config/
│   │   ├── settings.py        # 配置管理
│   │   └── config_loader.py   # 配置加载
│   ├── logging/
│   │   └── logger.py          # 日志管理
│   ├── database/
│   │   └── connection.py      # 数据库连接池
│   └── di/
│       └── container.py       # 依赖注入容器
│
└── shared/                    # 共享工具
    ├── exceptions.py          # 自定义异常
    └── utils.py               # 工具函数
```

## 层次职责

### Domain 层 (核心)

**职责**:
- 包含所有业务规则和领域知识
- 定义 Entities, Value Objects, Aggregates
- 定义 Ports 接口
- 实现 Domain Services

**原则**:
- ✅ 零外部依赖 (不依赖任何框架)
- ✅ 纯业务逻辑
- ✅ 高度可测试
- ✅ 技术无关

**示例**:
```python
# domain/entities/stock.py
@dataclass
class Stock:
    """实体: 股票 (无框架依赖)"""
    code: StockCode  # 值对象
    name: str
    market: Market   # 值对象

    def is_tradable(self) -> bool:
        """业务规则"""
        return self.is_active and self.market.is_open()
```

### Use Cases 层 (应用)

**职责**:
- 编排领域对象完成业务流程
- 通过 Ports 与外部交互
- 处理事务和协调

**原则**:
- ✅ 只依赖 Domain 层
- ✅ 通过接口调用外部
- ✅ 无技术细节
- ✅ 单一职责

**示例**:
```python
# use_cases/models/train_model.py
class TrainModelUseCase:
    """Use Case: 训练模型"""

    def __init__(
        self,
        data_provider: IDataProvider,  # Port
        model_trainer: IModelTrainer,  # Port
        recorder: IExperimentRecorder  # Port
    ):
        self.data_provider = data_provider
        self.trainer = model_trainer
        self.recorder = recorder

    async def execute(self, request) -> response:
        # 1. 加载数据
        dataset = await self.data_provider.load(...)

        # 2. 训练模型
        model = await self.trainer.train(...)

        # 3. 记录实验
        await self.recorder.record(...)

        return response
```

### Adapters 层 (技术实现)

**职责**:
- 实现 Domain 定义的 Ports
- 封装外部框架 (Hikyuu, Qlib)
- 提供外部接口 (CLI, API)

**原则**:
- ✅ 实现 Ports 接口
- ✅ 封装技术细节
- ✅ 可替换性
- ✅ 依赖注入

**示例**:
```python
# adapters/hikyuu/hikyuu_data_adapter.py
class HikyuuDataAdapter(IStockDataProvider):
    """Adapter: 实现数据提供者接口"""

    def __init__(self, config_file: str):
        self.hku = hikyuu  # 框架依赖在这里

    async def load_stock_data(
        self,
        code: StockCode,  # Domain 对象
        date_range: DateRange  # Domain 对象
    ) -> pd.DataFrame:
        # 转换 Domain 对象 → Hikyuu 对象
        stock = self.hku.Stock(code.value)
        kdata = stock.getKData(...)

        # 转换 Hikyuu 对象 → DataFrame
        return self._to_dataframe(kdata)
```

### Infrastructure 层 (基础设施)

**职责**:
- 配置管理
- 日志管理
- 数据库连接
- 依赖注入

**原则**:
- ✅ 提供技术支持
- ✅ 跨层服务
- ✅ 统一接口

## 数据流示例

### 完整流程: 从加载数据到训练模型

```
1. CLI Controller (Adapters)
   │
   │ 解析命令行参数
   │
   ▼
2. TrainModelUseCase (Use Cases)
   │
   │ 获取依赖 (通过 DI)
   │  - IDataProvider (Port)
   │  - IModelTrainer (Port)
   │
   ├─► 3a. HikyuuDataAdapter.load_data()
   │        │
   │        │ Hikyuu API 调用
   │        │  - hku.Stock()
   │        │  - getKData()
   │        │
   │        └─► 转换为 DataFrame
   │
   ├─► 3b. QlibModelAdapter.train()
   │        │
   │        │ Qlib API 调用
   │        │  - LGBModel()
   │        │  - fit()
   │        │
   │        └─► 返回 Model (Domain Entity)
   │
   │ 应用业务规则
   │  - model.mark_as_trained()
   │
   ▼
4. 返回 TrainModelResponse
```

## 测试策略

### 1. Domain 层测试

```python
# 纯单元测试,无 Mock,无外部依赖
def test_stock_is_tradable():
    stock = Stock(
        code=StockCode("sh000001"),
        market=Market("SH", ""),
        is_active=True
    )

    assert stock.is_tradable() is True
```

### 2. Use Cases 层测试

```python
# 使用 Mock Ports
@pytest.mark.asyncio
async def test_train_model_use_case():
    # Mock 所有 Ports
    mock_data_provider = Mock(spec=IDataProvider)
    mock_trainer = Mock(spec=IModelTrainer)

    use_case = TrainModelUseCase(
        mock_data_provider,
        mock_trainer
    )

    # 执行测试
    response = await use_case.execute(request)

    # 验证
    assert response.success is True
    mock_trainer.train.assert_called_once()
```

### 3. Adapters 层测试

```python
# Mock 外部框架
@patch('hikyuu.Stock')
@pytest.mark.asyncio
async def test_hikyuu_data_adapter(mock_stock):
    # 配置 Mock
    mock_stock.return_value.getKData.return_value = [...]

    adapter = HikyuuDataAdapter("config.ini")
    df = await adapter.load_stock_data(...)

    assert not df.empty
```

### 4. 架构测试

```python
# 验证依赖规则
def test_domain_has_no_framework_dependencies():
    domain_files = Path("src/domain").rglob("*.py")

    forbidden = ["hikyuu", "qlib", "fastapi"]

    for file in domain_files:
        content = file.read_text()
        for f in forbidden:
            assert f"import {f}" not in content
```

## 开发工作流

### 1. 新增功能流程

```
1. 定义 Domain 对象
   ├─ Entity / Value Object
   ├─ Port 接口
   └─ Domain Service (如需要)

2. 编写 Use Case
   ├─ Request / Response DTO
   ├─ 编排流程
   └─ 单元测试 (Mock Ports)

3. 实现 Adapter
   ├─ 实现 Port 接口
   ├─ 封装外部框架
   └─ 单元测试 (Mock 框架)

4. 创建 Controller
   ├─ CLI / API
   ├─ 依赖注入
   └─ 集成测试
```

### 2. TDD 流程

```
每个层都遵循 Red-Green-Refactor:

🔴 RED: 编写失败的测试
   │
   ├─ Domain: 测试业务规则
   ├─ Use Cases: Mock Ports
   └─ Adapters: Mock 框架
   │
   ▼
🟢 GREEN: 最小实现
   │
   │ 只写足够让测试通过的代码
   │
   ▼
🔵 REFACTOR: 重构优化
   │
   │ 改进代码质量
   │ 确保测试仍然通过
```

## 依赖注入示例

```python
# infrastructure/di/container.py
class Container(containers.DeclarativeContainer):
    """DI 容器"""

    # Adapters (实现 Ports)
    hikyuu_adapter = providers.Singleton(
        HikyuuDataAdapter,
        config_file="hikyuu.ini"
    )

    qlib_adapter = providers.Singleton(
        QlibModelAdapter,
        provider_uri="./data/qlib"
    )

    # Use Cases (注入 Ports)
    train_use_case = providers.Factory(
        TrainModelUseCase,
        data_provider=hikyuu_adapter,  # 注入实现
        model_trainer=qlib_adapter     # 注入实现
    )

# CLI 中使用
container = Container()
use_case = container.train_use_case()
response = await use_case.execute(request)
```

## 架构优势

### 1. 可测试性

- Domain 层: 无依赖,纯单元测试
- Use Cases 层: Mock Ports,隔离测试
- Adapters 层: Mock 框架,集成测试

### 2. 可维护性

- 关注点分离
- 清晰的层次边界
- 业务逻辑集中在 Domain

### 3. 可扩展性

- 轻松替换实现 (Hikyuu ↔ 其他数据源)
- 新增功能只影响相关层
- 支持多种接口 (CLI + API)

### 4. 框架独立性

- Domain 层不依赖框架
- 可以将 Hikyuu 换成其他框架
- 业务逻辑不受影响

## 最佳实践

1. **依赖规则**: 依赖永远向内
2. **接口隔离**: Port 接口小而专注
3. **业务在 Domain**: 业务规则放 Domain 层
4. **测试独立性**: Domain 可独立测试
5. **值对象不可变**: 使用 `frozen=True`
6. **实体相等性**: 只比较 ID
7. **Thin Controllers**: 控制器只做转换
8. **Rich Domain**: 行为和数据一起

## 常见陷阱

❌ **Anemic Domain**: Entities 只有数据没有行为
❌ **Framework Coupling**: Domain 依赖框架
❌ **Fat Controllers**: 业务逻辑在控制器
❌ **Repository Leakage**: 暴露 ORM 对象
❌ **Missing Abstractions**: Domain 直接依赖具体实现

---

**创建时间**: 2025-01-11
**版本**: v1.0.0
**架构模式**: Hexagonal Architecture + DDD
**状态**: ✅ 架构定义完成
