# Hikyuu × Qlib - 源代码

## 📁 目录结构

```
src/
├── domain/              # 核心领域层 (业务规则)
├── use_cases/           # 应用层 (业务流程)
├── adapters/            # 适配器层 (技术实现)
├── infrastructure/      # 基础设施层 (配置/日志/数据库)
├── shared/              # 共享工具
├── ARCHITECTURE.md      # 📖 架构详细文档
└── README.md            # 本文件
```

## 🏗️ 架构模式

本项目采用 **Hexagonal Architecture (六边形架构)** + **DDD (领域驱动设计)**:

```
┌─────────────────────────────────┐
│   Adapters (Hikyuu/Qlib/CLI)   │  ← 外层
└──────────────┬──────────────────┘
               │ 依赖
┌──────────────▼──────────────────┐
│   Use Cases (业务流程编排)       │  ← 中层
└──────────────┬──────────────────┘
               │ 依赖
┌──────────────▼──────────────────┐
│   Domain (核心业务规则)          │  ← 内层
└──────────────────────────────────┘

规则: 依赖只能向内,内层完全独立
```

## 🎯 核心原则

1. **依赖倒置**: Domain 定义接口 (Ports),Adapters 实现
2. **框架独立**: Domain 层零外部依赖
3. **高度可测试**: 每层都可独立测试
4. **关注点分离**: 业务逻辑、技术实现、应用流程分离

## 📚 快速开始

### 1. 阅读文档

**必读**:
- [ARCHITECTURE.md](./ARCHITECTURE.md) - 架构详细说明
- [domain/.claude.md](./domain/.claude.md) - Domain 层开发指南
- [use_cases/.claude.md](./use_cases/.claude.md) - Use Cases 层开发指南
- [adapters/.claude.md](./adapters/.claude.md) - Adapters 层开发指南

### 2. 层次说明

#### Domain 层 (核心)

**职责**: 包含所有业务规则

**内容**:
- `entities/` - 实体 (有 ID,可变)
- `value_objects/` - 值对象 (无 ID,不可变)
- `aggregates/` - 聚合根 (一致性边界)
- `events/` - 领域事件
- `ports/` - 端口接口定义
- `services/` - 领域服务

**示例**:
```python
# domain/entities/stock.py
@dataclass
class Stock:
    code: StockCode  # 值对象
    name: str

    def is_tradable(self) -> bool:
        """业务规则"""
        return self.is_active
```

#### Use Cases 层 (应用)

**职责**: 编排领域对象完成业务流程

**内容**:
- `data/` - 数据相关 Use Cases
- `models/` - 模型相关 Use Cases
- `strategies/` - 策略相关 Use Cases
- `analysis/` - 分析相关 Use Cases

**示例**:
```python
# use_cases/models/train_model.py
class TrainModelUseCase:
    def __init__(
        self,
        data_provider: IDataProvider,  # Port
        model_trainer: IModelTrainer   # Port
    ):
        pass

    async def execute(self, request) -> response:
        # 编排流程
        pass
```

#### Adapters 层 (技术实现)

**职责**: 实现 Ports,封装外部框架

**内容**:
- `hikyuu/` - Hikyuu 框架适配器
- `qlib/` - Qlib 框架适配器
- `repositories/` - 数据持久化
- `controllers/` - CLI/API 控制器

**示例**:
```python
# adapters/hikyuu/hikyuu_data_adapter.py
class HikyuuDataAdapter(IStockDataProvider):
    """实现 Domain Port"""

    async def load_stock_data(self, code, date_range):
        # 调用 Hikyuu API
        # 转换为 Domain 对象
        pass
```

#### Infrastructure 层 (基础设施)

**职责**: 提供技术支持

**内容**:
- `config/` - 配置管理
- `logging/` - 日志管理
- `database/` - 数据库连接
- `di/` - 依赖注入容器

## 🧪 TDD 开发流程

**每个功能都遵循**:

```
1. 🔴 RED: 编写失败的测试
   ├─ Domain: 测试业务规则
   ├─ Use Cases: Mock Ports
   └─ Adapters: Mock 框架

2. 🟢 GREEN: 最小实现
   └─ 只写足够让测试通过的代码

3. 🔵 REFACTOR: 重构优化
   └─ 改进代码,测试仍然通过
```

## 📊 测试覆盖率目标

| 层次 | 覆盖率目标 |
|------|-----------|
| Domain | >= 95% |
| Use Cases | >= 90% |
| Adapters | >= 85% |
| Infrastructure | >= 88% |

## 🔧 开发工具

### 运行测试

```bash
# 运行所有测试
pytest

# 带覆盖率
pytest --cov=src --cov-report=html

# 只测试 Domain 层
pytest tests/unit/domain/

# 架构测试
pytest tests/architecture/
```

### 代码质量检查

```bash
# Type checking
mypy src/

# Linting
ruff check src/

# Formatting
ruff format src/
```

## 📦 依赖注入

使用 `dependency-injector` 管理依赖:

```python
# 使用容器
from infrastructure.di.container import get_container

container = get_container()
use_case = container.train_model_use_case()

# 执行
response = await use_case.execute(request)
```

## 🔗 模块间通信

**Domain → Use Cases → Adapters**

```python
# 1. Domain 定义接口
class IStockDataProvider(ABC):
    @abstractmethod
    async def load_stock_data(self, code, date_range):
        pass

# 2. Adapters 实现接口
class HikyuuDataAdapter(IStockDataProvider):
    async def load_stock_data(self, code, date_range):
        # 实现
        pass

# 3. Use Case 使用接口
class LoadDataUseCase:
    def __init__(self, provider: IStockDataProvider):
        self.provider = provider  # 依赖接口,不依赖实现
```

## 📖 更多资源

- **项目根目录 `.claude.md`**: TDD 总体指南
- **每层 `.claude.md`**: 各层详细开发指南
- **ARCHITECTURE.md**: 完整架构文档
- **tests/**: 测试示例

## ⚠️ 重要提示

1. **Domain 层绝对不能依赖外部框架**
2. **Use Cases 只依赖 Domain**
3. **Adapters 实现 Ports 接口**
4. **测试覆盖率必须达标**
5. **遵循 TDD 流程**

---

**架构**: Hexagonal Architecture + DDD
**语言**: Python 3.8+
**测试框架**: Pytest
**依赖管理**: Poetry / uv
**状态**: ✅ 架构定义完成,待开发
