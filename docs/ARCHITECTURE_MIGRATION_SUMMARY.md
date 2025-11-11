# 架构迁移总结 - 文档适配指南

**日期**: 2025-11-11
**版本**: 2.0.0

## 📋 文档更新状态

| 文档 | 旧版本 | 新版本 | 状态 |
|------|--------|--------|------|
| **design.md** | 传统分层架构 | 六边形架构 v2.0 | ✅ 已更新 |
| **requirements.md** | 面向技术实现 | 面向领域模型 | ✅ 已更新 |
| **tasks.md** | 面向框架API | 面向TDD分层开发 | ✅ 已更新 |

## 📝 已完成更新

### ✅ design.md v2.0

**新文档路径**: [`docs/design.md`](./design.md)
**旧文档备份**: [`docs/design.md.legacy`](./design.md.legacy)

**主要变更**:
1. 架构模式从**传统分层**改为**六边形架构 + DDD**
2. 明确**依赖规则**: Adapters → Use Cases → Domain
3. 新增**Domain层设计** (Entities, Value Objects, Ports)
4. 新增**测试策略** (Domain 95%, Use Cases 90%, Adapters 85%)
5. 提供完整的**代码示例**和**数据流设计**

## 📌 待更新文档指南

### requirements.md 更新要点

**当前问题**:
- FR-001 ~ FR-014 定义的是技术实现需求,非业务需求
- 缺少领域模型定义 (Entities, Value Objects, Aggregates)
- 需求直接耦合框架实现

**应该更新为**:

```markdown
## Domain需求 (DR-001 ~ DR-010)

### DR-001: 股票领域模型
- 定义Stock Entity (code, name, market, is_active)
- 定义StockCode Value Object (validation rules)
- 业务规则: is_tradable() 判断股票可交易性

### DR-002: 模型领域模型
- 定义Model Entity (id, type, parameters, metrics, status)
- 定义ModelMetrics Value Object
- 业务规则: mark_as_trained(), validate_metrics()

### DR-003: Port接口定义
- IStockDataProvider: async load_stock_data()
- IModelTrainer: async train()
- IBacktestEngine: async run_backtest()
```

### tasks.md 更新要点

**当前问题**:
- 任务直接面向框架API调用 (hikyuu.StockManager, qlib.init)
- 违反依赖倒置原则
- 缺少TDD流程 (先写测试,后写代码)

**应该更新为**:

```markdown
## Phase 1: Domain层开发 (Week 1-3)

### Task 1.1: StockCode Value Object
- 🔴 RED: 编写测试 tests/unit/domain/value_objects/test_stock_code.py
  - test_valid_stock_code()
  - test_invalid_stock_code_raises_error()
- 🟢 GREEN: 实现 src/domain/value_objects/stock_code.py
- 🔵 REFACTOR: 优化代码
- 覆盖率: 100%

### Task 1.2: Stock Entity
- 🔴 RED: 编写测试 tests/unit/domain/entities/test_stock.py
  - test_stock_is_tradable_when_active()
  - test_stock_not_tradable_when_inactive()
- 🟢 GREEN: 实现 src/domain/entities/stock.py
- 🔵 REFACTOR: 优化代码
- 覆盖率: ≥95%

### Task 1.3: IStockDataProvider Port
- 定义接口 src/domain/ports/stock_data_provider.py
  - async load_stock_data(code: StockCode, date_range: DateRange)
- 无需测试 (接口定义)

## Phase 2: Use Cases层开发 (Week 4-6)

### Task 2.1: LoadStockDataUseCase
- 🔴 RED: 编写测试 tests/unit/use_cases/data/test_load_stock_data.py
  - Mock IStockDataProvider
  - test_load_stock_data_success()
- 🟢 GREEN: 实现 src/use_cases/data/load_stock_data.py
- 🔵 REFACTOR: 优化代码
- 覆盖率: ≥90%

## Phase 3: Adapters层开发 (Week 7-10)

### Task 3.1: HikyuuDataAdapter
- 🔴 RED: 编写测试 tests/unit/adapters/hikyuu/test_data_adapter.py
  - Mock hikyuu.Stock
  - test_load_stock_data_calls_hikyuu_api()
- 🟢 GREEN: 实现 src/adapters/hikyuu/data_adapter.py
  - 实现IStockDataProvider接口
  - 调用hikyuu API
  - 转换为Domain对象
- 🔵 REFACTOR: 优化代码
- 覆盖率: ≥85%
```

## 🔑 关键变化总结

### 1. 从技术需求到业务需求

**旧方式** (❌):
```
FR-002: 实现HikyuuDataLoader类,使用hikyuu.StockManager加载数据
```

**新方式** (✅):
```
DR-001: 定义Stock领域模型
  - Stock Entity: 包含业务规则 is_tradable()
  - StockCode Value Object: 包含验证规则
  - IStockDataProvider Port: 定义数据加载接口
```

### 2. 从框架调用到接口依赖

**旧方式** (❌):
```python
class DataLoader:
    def load_data(self, code):
        stock = hikyuu.Stock(code)  # 直接依赖框架
        return stock.getKData()
```

**新方式** (✅):
```python
# Domain: 定义接口
class IStockDataProvider(ABC):
    async def load_stock_data(self, code: StockCode):
        pass

# Use Case: 依赖接口
class LoadDataUseCase:
    def __init__(self, provider: IStockDataProvider):  # 依赖抽象
        self.provider = provider

# Adapter: 实现接口
class HikyuuDataAdapter(IStockDataProvider):
    async def load_stock_data(self, code):
        stock = hku.Stock(code.value)  # 在Adapter中调用框架
        return stock.getKData()
```

### 3. 从Code First到Test First (TDD)

**旧方式** (❌):
```
1. 直接编写实现代码
2. (可能)补充测试
```

**新方式** (✅):
```
1. 🔴 RED: 先写失败的测试
2. 🟢 GREEN: 写最小实现让测试通过
3. 🔵 REFACTOR: 重构优化
4. 重复循环
```

## 📚 参考文档

- [design.md v2.0](./design.md) - 完整架构设计
- [src/.claude.md](../src/.claude.md) - 开发总纲
- [src/ARCHITECTURE.md](../src/ARCHITECTURE.md) - 详细架构文档
- [src/MIGRATION_GUIDE.md](../src/MIGRATION_GUIDE.md) - 迁移指南

## ⚠️ 重要提示

1. **旧文档已备份**:
   - `design.md.legacy`
   - `requirements.md.legacy`
   - `tasks.md.legacy`

2. **新文档遵循六边形架构**:
   - Domain层: 零外部依赖
   - Use Cases层: 只依赖Domain Ports
   - Adapters层: 实现Ports,调用框架

3. **所有开发必须遵循TDD**:
   - Domain层覆盖率 ≥95%
   - Use Cases层覆盖率 ≥90%
   - Adapters层覆盖率 ≥85%

---

**负责人**: Architecture Team
**最后更新**: 2025-11-11
