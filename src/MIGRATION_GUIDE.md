# 架构迁移指南

## 从旧架构迁移到六边形架构

**日期**: 2025-11-11
**版本**: 1.0.0

---

## 1. 架构变更概览

### 旧架构 (hikyuu_qlib/)

```
hikyuu_qlib/
├── src/
│   ├── core/
│   │   ├── data/          # 数据处理
│   │   ├── models/        # 模型训练
│   │   ├── strategies/    # 策略执行
│   │   ├── config/        # 配置管理
│   │   └── analysis/      # 分析报告
│   ├── integrations/
│   │   ├── hikyuu/        # Hikyuu 集成
│   │   └── qlib/          # Qlib 集成
│   └── cli/               # CLI 工具
```

**问题**:
- ❌ Core 模块直接依赖外部框架 (Hikyuu, Qlib)
- ❌ 缺少明确的领域模型 (Domain Model)
- ❌ 业务逻辑分散在 CLI、Services、Controllers
- ❌ 难以测试 (框架耦合严重)
- ❌ 难以替换框架实现

### 新架构 (src/)

```
src/
├── domain/              # 领域层 (核心业务规则)
│   ├── entities/        # 实体 (有ID)
│   ├── value_objects/   # 值对象 (不可变)
│   ├── aggregates/      # 聚合根
│   ├── events/          # 领域事件
│   ├── ports/           # 端口接口 (Port)
│   └── services/        # 领域服务
├── use_cases/           # 应用层 (业务流程)
│   ├── data/            # 数据相关用例
│   ├── models/          # 模型相关用例
│   ├── strategies/      # 策略相关用例
│   └── analysis/        # 分析相关用例
├── adapters/            # 适配器层 (技术实现)
│   ├── hikyuu/          # Hikyuu 适配器
│   ├── qlib/            # Qlib 适配器
│   ├── repositories/    # 数据持久化
│   └── controllers/     # CLI/API 控制器
│       ├── cli/
│       └── api/
├── infrastructure/      # 基础设施层
│   ├── config/          # 配置管理
│   ├── logging/         # 日志管理
│   ├── database/        # 数据库连接
│   └── di/              # 依赖注入
└── shared/              # 共享工具
```

**优势**:
- ✅ Domain 层零外部依赖
- ✅ 依赖倒置 (Adapters → Use Cases → Domain)
- ✅ 高度可测试 (每层独立测试)
- ✅ 框架可替换 (只需替换 Adapter)
- ✅ 清晰的边界和职责

---

## 2. 依赖规则变化

### 旧依赖关系

```
CLI → Core Modules → Integrations (Hikyuu/Qlib)
          ↓
     直接依赖框架 ❌
```

### 新依赖关系

```
Controllers → Use Cases → Domain (定义 Ports)
                              ↑
Adapters (实现 Ports) ────────┘

规则: 依赖只能向内 ✅
```

---

## 3. 模块对应关系

### 数据处理模块

| 旧位置 | 新位置 | 说明 |
|--------|--------|------|
| `core/data/hikyuu_loader.py` | `adapters/hikyuu/data_adapter.py` | 实现 `IStockDataProvider` Port |
| `core/data/qlib_converter.py` | `adapters/qlib/data_adapter.py` | 实现 `IDatasetProvider` Port |
| `core/data/data_validator.py` | `use_cases/data/validate_data.py` | Use Case 编排验证流程 |
| - | `domain/entities/stock.py` | **新增** 股票实体 |
| - | `domain/value_objects/stock_code.py` | **新增** 股票代码值对象 |
| - | `domain/ports/stock_data_provider.py` | **新增** 数据提供者接口 |

**迁移步骤**:

1. **提取领域模型** (Domain):
```python
# 新增: domain/entities/stock.py
@dataclass
class Stock:
    """股票实体"""
    code: StockCode  # 值对象
    name: str
    market: Market
    is_active: bool = True

    def is_tradable(self) -> bool:
        """业务规则: 判断是否可交易"""
        return self.is_active and self.market.is_open()
```

2. **定义 Port 接口** (Domain):
```python
# 新增: domain/ports/stock_data_provider.py
class IStockDataProvider(ABC):
    """数据提供者接口 (Port)"""
    @abstractmethod
    async def load_stock_data(
        self,
        code: StockCode,
        date_range: DateRange
    ) -> pd.DataFrame:
        pass
```

3. **重构 Adapter** (Adapters):
```python
# 迁移: adapters/hikyuu/data_adapter.py
class HikyuuDataAdapter(IStockDataProvider):
    """实现 Port 接口"""

    async def load_stock_data(
        self,
        code: StockCode,  # 使用 Domain 对象
        date_range: DateRange
    ) -> pd.DataFrame:
        # 调用 Hikyuu API
        stock = hku.Stock(code.value)
        kdata = stock.getKData(...)
        return self._to_dataframe(kdata)
```

4. **创建 Use Case** (Use Cases):
```python
# 新增: use_cases/data/load_stock_data.py
class LoadStockDataUseCase:
    def __init__(self, provider: IStockDataProvider):
        self.provider = provider  # 依赖接口,不依赖实现

    async def execute(self, request: LoadStockDataRequest):
        # 编排业务流程
        data = await self.provider.load_stock_data(...)
        # 应用业务规则...
        return LoadStockDataResponse(data=data)
```

### 模型训练模块

| 旧位置 | 新位置 | 说明 |
|--------|--------|------|
| `core/models/model_trainer.py` | `adapters/qlib/model_trainer_adapter.py` | 实现 `IModelTrainer` Port |
| `core/models/predictor.py` | `adapters/qlib/predictor_adapter.py` | 实现 `IPredictor` Port |
| - | `use_cases/models/train_model.py` | **新增** 训练模型 Use Case |
| - | `domain/entities/model.py` | **新增** 模型实体 |
| - | `domain/ports/model_trainer.py` | **新增** 模型训练接口 |

**迁移步骤**:

1. **定义模型实体** (Domain):
```python
# 新增: domain/entities/model.py
@dataclass
class Model:
    """模型实体"""
    id: ModelId
    name: str
    model_type: str
    parameters: Dict[str, Any]
    metrics: ModelMetrics
    status: ModelStatus
    trained_at: Optional[datetime] = None

    def mark_as_trained(self):
        """业务规则: 标记为已训练"""
        self.status = ModelStatus.TRAINED
        self.trained_at = datetime.now()
```

2. **定义 Port** (Domain):
```python
# 新增: domain/ports/model_trainer.py
class IModelTrainer(ABC):
    @abstractmethod
    async def train(
        self,
        model_type: str,
        dataset: Any,
        parameters: Dict[str, Any]
    ) -> Model:
        pass
```

3. **实现 Adapter** (Adapters):
```python
# 迁移: adapters/qlib/model_trainer_adapter.py
class QlibModelTrainerAdapter(IModelTrainer):
    """实现模型训练 Port"""

    async def train(self, model_type, dataset, parameters):
        # 调用 Qlib API
        if model_type == "LGBModel":
            qlib_model = LGBModel(**parameters)
        qlib_model.fit(dataset)

        # 转换为 Domain Entity
        return Model(
            id=ModelId.generate(),
            name=f"{model_type}_{timestamp}",
            model_type=model_type,
            parameters=parameters,
            metrics=self._extract_metrics(qlib_model),
            status=ModelStatus.TRAINED
        )
```

4. **创建 Use Case** (Use Cases):
```python
# 新增: use_cases/models/train_model.py
class TrainModelUseCase:
    def __init__(
        self,
        data_provider: IDataProvider,
        model_trainer: IModelTrainer,
        recorder: IExperimentRecorder
    ):
        self.data_provider = data_provider
        self.trainer = model_trainer
        self.recorder = recorder

    async def execute(self, request: TrainModelRequest):
        # 1. 加载数据
        dataset = await self.data_provider.load_dataset(...)

        # 2. 训练模型
        model = await self.trainer.train(...)

        # 3. 应用业务规则
        model.mark_as_trained()

        # 4. 记录实验
        await self.recorder.record(...)

        return TrainModelResponse(model=model)
```

### 策略执行模块

| 旧位置 | 新位置 | 说明 |
|--------|--------|------|
| `core/strategies/signal_converter.py` | `adapters/hikyuu/signal_adapter.py` | 实现 `ISignalProvider` Port |
| `core/strategies/backtest_runner.py` | `adapters/hikyuu/backtest_adapter.py` | 实现 `IBacktestEngine` Port |
| - | `use_cases/strategies/run_backtest.py` | **新增** 执行回测 Use Case |
| - | `domain/entities/trading_signal.py` | **新增** 交易信号实体 |
| - | `domain/aggregates/portfolio.py` | **新增** 投资组合聚合根 |

### CLI 工具模块

| 旧位置 | 新位置 | 说明 |
|--------|--------|------|
| `cli/data.py` | `adapters/controllers/cli/data_cli.py` | CLI 控制器 |
| `cli/train.py` | `adapters/controllers/cli/train_cli.py` | CLI 控制器 |
| `cli/backtest.py` | `adapters/controllers/cli/backtest_cli.py` | CLI 控制器 |

**迁移步骤**:

CLI 控制器现在只负责:
1. 解析命令行参数
2. 构建 Use Case Request
3. 调用 Use Case
4. 格式化输出

```python
# 迁移: adapters/controllers/cli/train_cli.py
@click.command()
@click.option('--config', required=True)
@click.option('--model', required=True)
def train(config, model):
    """训练模型 CLI"""
    # 1. 获取依赖注入容器
    container = get_container()

    # 2. 构建 Request
    request = TrainModelRequest(
        model_type=model,
        config_path=config
    )

    # 3. 执行 Use Case
    use_case = container.train_model_use_case()
    response = asyncio.run(use_case.execute(request))

    # 4. 输出结果
    if response.success:
        click.echo(f"✅ 训练成功: {response.model.id}")
    else:
        click.echo(f"❌ 训练失败: {response.error}")
```

---

## 4. 测试策略变化

### 旧测试方式

```python
# 问题: 需要 Mock 整个框架
@patch('hikyuu.Stock')
@patch('qlib.init')
def test_load_data(mock_qlib, mock_stock):
    loader = HikyuuDataLoader()
    data = loader.load('sh000001')
    assert data is not None
```

### 新测试方式

#### Domain 层测试 (无 Mock)

```python
# 纯业务逻辑测试
def test_stock_is_tradable():
    """测试股票可交易规则"""
    stock = Stock(
        code=StockCode("sh000001"),
        name="上证指数",
        market=Market.SH,
        is_active=True
    )

    assert stock.is_tradable() is True
```

#### Use Case 层测试 (Mock Ports)

```python
# 只 Mock 接口,不 Mock 框架
@pytest.fixture
def mock_data_provider():
    provider = Mock(spec=IStockDataProvider)
    provider.load_stock_data.return_value = pd.DataFrame(...)
    return provider

async def test_load_stock_data_use_case(mock_data_provider):
    """测试加载股票数据 Use Case"""
    use_case = LoadStockDataUseCase(provider=mock_data_provider)

    request = LoadStockDataRequest(
        code=StockCode("sh000001"),
        date_range=DateRange("2020-01-01", "2023-12-31")
    )

    response = await use_case.execute(request)

    assert response.success is True
    mock_data_provider.load_stock_data.assert_called_once()
```

#### Adapter 层测试 (Mock 框架)

```python
# 只在 Adapter 层 Mock 框架
@patch('hikyuu.Stock')
def test_hikyuu_data_adapter(mock_stock):
    """测试 Hikyuu 数据适配器"""
    mock_stock.return_value.getKData.return_value = [...]

    adapter = HikyuuDataAdapter()
    data = await adapter.load_stock_data(
        code=StockCode("sh000001"),
        date_range=DateRange("2020-01-01", "2023-12-31")
    )

    assert isinstance(data, pd.DataFrame)
```

---

## 5. 依赖注入配置

### 旧方式 (手动创建依赖)

```python
# 问题: 依赖关系硬编码
loader = HikyuuDataLoader(config_file="hikyuu.ini")
converter = QlibDataConverter(qlib_dir="./data/qlib")
trainer = ModelTrainer(loader, converter)
```

### 新方式 (依赖注入容器)

```python
# infrastructure/di/container.py
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    # 配置
    config = providers.Configuration()

    # Adapters
    hikyuu_data_adapter = providers.Singleton(
        HikyuuDataAdapter,
        config_file=config.hikyuu.config_file
    )

    qlib_model_trainer = providers.Singleton(
        QlibModelTrainerAdapter,
        qlib_dir=config.qlib.provider_uri
    )

    # Use Cases
    train_model_use_case = providers.Factory(
        TrainModelUseCase,
        data_provider=hikyuu_data_adapter,
        model_trainer=qlib_model_trainer
    )

# 使用
container = Container()
container.config.from_yaml('config.yaml')

use_case = container.train_model_use_case()
response = await use_case.execute(request)
```

---

## 6. 迁移检查清单

### Phase 1: Domain 层 (第 1-2 周)

- [ ] 提取实体 (Stock, Model, Order, TradingSignal)
- [ ] 定义值对象 (StockCode, Price, DateRange, Market)
- [ ] 定义聚合根 (Portfolio, TradingDay)
- [ ] 定义领域事件 (ModelTrained, OrderPlaced)
- [ ] 定义所有 Ports 接口
- [ ] 编写 Domain 层单元测试 (覆盖率 >= 95%)

### Phase 2: Use Cases 层 (第 3-4 周)

- [ ] 创建数据相关 Use Cases
- [ ] 创建模型相关 Use Cases
- [ ] 创建策略相关 Use Cases
- [ ] 创建分析相关 Use Cases
- [ ] 编写 Use Case 测试 (Mock Ports, 覆盖率 >= 90%)

### Phase 3: Adapters 层 (第 5-7 周)

- [ ] 实现 Hikyuu Adapters (数据、指标、回测)
- [ ] 实现 Qlib Adapters (模型、预测、实验记录)
- [ ] 实现 Repository Adapters
- [ ] 重构 CLI Controllers
- [ ] 编写 Adapter 测试 (覆盖率 >= 85%)

### Phase 4: Infrastructure 层 (第 8 周)

- [ ] 配置管理 (Pydantic BaseSettings)
- [ ] 日志管理 (Loguru)
- [ ] 依赖注入容器 (dependency-injector)
- [ ] 数据库连接 (如需要)
- [ ] 编写 Infrastructure 测试 (覆盖率 >= 88%)

### Phase 5: 集成测试 & 文档 (第 9-10 周)

- [ ] 端到端集成测试
- [ ] 架构测试 (验证依赖规则)
- [ ] API 文档
- [ ] 迁移文档
- [ ] 用户手册

---

## 7. 常见问题

### Q1: 为什么要迁移到六边形架构?

**A**:
- 旧架构 Core 模块直接依赖 Hikyuu/Qlib,难以测试和替换
- 缺少清晰的业务规则定义 (Domain Model)
- 业务逻辑分散,难以维护

### Q2: 迁移会影响现有功能吗?

**A**:
- 不会。外部接口 (CLI) 保持不变
- 内部重构,外部行为一致
- 通过充分测试保证功能正确性

### Q3: 迁移需要多长时间?

**A**:
- 预计 10 周 (约 2.5 个月)
- 可分阶段迁移,逐步替换旧代码

### Q4: 如何保证迁移质量?

**A**:
- 严格遵循 TDD (测试驱动开发)
- 每层都有高测试覆盖率要求
- 架构测试验证依赖规则
- Code Review

### Q5: 旧代码如何处理?

**A**:
- 旧代码保留在 `hikyuu_qlib/` 目录
- 新代码在 `src/` 目录
- 功能迁移完成并测试通过后,逐步废弃旧代码

---

## 8. 参考资源

### 架构文档

- [src/ARCHITECTURE.md](./ARCHITECTURE.md) - 完整架构文档
- [src/README.md](./README.md) - 快速开始指南
- [src/domain/.claude.md](./domain/.claude.md) - Domain 层开发指南
- [src/use_cases/.claude.md](./use_cases/.claude.md) - Use Cases 层开发指南
- [src/adapters/.claude.md](./adapters/.claude.md) - Adapters 层开发指南
- [src/infrastructure/.claude.md](./infrastructure/.claude.md) - Infrastructure 层开发指南

### 外部资源

- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)
- [Domain-Driven Design](https://martinfowler.com/tags/domain%20driven%20design.html)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

---

**迁移负责人**: Architecture Team
**开始日期**: 2025-11-11
**预计完成**: 2026-01-20 (10 周)
**当前状态**: ✅ 架构设计完成,待开始实施
