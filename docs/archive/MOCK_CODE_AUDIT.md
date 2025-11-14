# Mock 代码审计报告

## 概述

本报告详细列出了项目中所有使用 Mock 的位置，包括生产代码和测试代码。

生成时间：2025-11-14

## 执行摘要

### Mock 使用统计

| 类别 | Mock 位置数 | 目的 | 状态 |
|------|-------------|------|------|
| **生产代码** | 4 | 条件导入，便于开发和测试 | ⚠️ 需审查 |
| **单元测试** | 30+ | 隔离外部依赖 | ✅ 正常 |

### 关键发现

1. ✅ **单元测试中的 Mock 使用正常**：用于隔离外部依赖（Qlib、Hikyuu）
2. ⚠️ **生产代码中存在条件 Mock**：用于开发环境缺少依赖时的降级处理
3. ❌ **潜在问题**：生产适配器中的条件 Mock 可能导致运行时失败不明显

## 详细审计

---

## 1. 生产代码中的 Mock

### 1.1 Hikyuu Data Adapter

**文件**: [src/adapters/hikyuu/hikyuu_data_adapter.py](../src/adapters/hikyuu/hikyuu_data_adapter.py:1-15)

**Mock 代码**:
```python
# 条件导入 Hikyuu - 便于测试和开发
try:
    import hikyuu as hku
    from hikyuu import hikyuu_init
except ImportError:
    # 开发环境下 Mock hikyuu
    hku = None
    hikyuu_init = None
```

**影响范围**: 整个 HikyuuDataAdapter 类

**用途**:
- 允许在没有安装 Hikyuu 的环境中导入模块
- 便于开发和单元测试

**风险等级**: ⚠️ **中等**

**问题**:
1. 如果 `hku = None`，运行时会在首次使用时抛出 `AttributeError`
2. 错误信息不够清晰，难以定位问题
3. 生产环境不应该有 `hku = None` 的情况

**建议**:
```python
# 改进方案
try:
    import hikyuu as hku
    from hikyuu import hikyuu_init
    HIKYUU_AVAILABLE = True
except ImportError:
    hku = None
    hikyuu_init = None
    HIKYUU_AVAILABLE = False

class HikyuuDataAdapter(IStockDataProvider):
    def __init__(self, config_file: str):
        if not HIKYUU_AVAILABLE:
            raise ImportError(
                "Hikyuu is not installed. "
                "Please install it with: pip install hikyuu"
            )
        # ... 正常初始化
```

---

### 1.2 Hikyuu Backtest Adapter

**文件**: [src/adapters/hikyuu/hikyuu_backtest_adapter.py](../src/adapters/hikyuu/hikyuu_backtest_adapter.py:1-10)

**Mock 代码**:
```python
# 为了便于测试，使用条件导入
try:
    import hikyuu as hku
except ImportError:
    # 开发环境下 Mock hikyuu
    hku = None
```

**影响范围**: HikyuuBacktestAdapter 类

**风险等级**: ⚠️ **中等**

**问题**: 同 1.1

**建议**: 同 1.1

---

### 1.3 Indicator Calculator Adapter

**文件**: [src/adapters/hikyuu/indicator_calculator_adapter.py](../src/adapters/hikyuu/indicator_calculator_adapter.py:1-10)

**Mock 代码**:
```python
# 为了便于测试，使用条件导入
try:
    import hikyuu
except ImportError:
    # 开发环境下 Mock hikyuu
    hikyuu = None
```

**影响范围**: IndicatorCalculatorAdapter 类

**风险等级**: ⚠️ **中等**

**问题**: 同 1.1

**建议**: 同 1.1

---

### 1.4 Qlib Data Adapter

**文件**: [src/adapters/qlib/qlib_data_adapter.py](../src/adapters/qlib/qlib_data_adapter.py:30-40)

**Mock 代码**:
```python
def __init__(self, qlib_module=None):
    """
    初始化 Qlib 数据适配器

    Args:
        qlib_module: 可选的 qlib 模块注入 (用于测试 Mock)
    """
    if qlib_module is not None:
        self.qlib = qlib_module
    else:
        if qlib is None:
            raise ImportError("qlib not installed...")
        self.qlib = qlib
```

**影响范围**: QlibDataAdapter 类

**风险等级**: ✅ **低**（设计良好）

**优点**:
1. 明确的依赖注入接口
2. 用于测试的显式参数
3. 生产环境有明确的错误提示

**用途**:
- 单元测试时注入 Mock 对象
- 生产环境使用真实的 qlib 模块

---

## 2. 单元测试中的 Mock

### 2.1 Qlib Model Trainer Adapter 测试

**文件**: [tests/unit/adapters/qlib/test_qlib_model_trainer_adapter.py](../tests/unit/adapters/qlib/test_qlib_model_trainer_adapter.py)

**Mock 使用**:
```python
from unittest.mock import MagicMock, patch

@pytest.fixture
def mock_training_data(self) -> Any:
    """Mock 训练数据 fixture"""
    return MagicMock()

async def test_train_model_success(self, untrained_model, mock_training_data):
    with patch("adapters.qlib.qlib_model_trainer_adapter.trainer") as mock_trainer:
        mock_qlib_model = MagicMock()
        mock_metrics = {"IC": 0.85, "ICIR": 0.8}
        mock_trainer.train.return_value = (mock_qlib_model, mock_metrics)
        # ... 测试逻辑
```

**风险等级**: ✅ **正常**

**用途**: 隔离 Qlib 训练器依赖，进行单元测试

---

### 2.2 Qlib Data Adapter 测试

**文件**: [tests/unit/adapters/qlib/test_qlib_data_adapter.py](../tests/unit/adapters/qlib/test_qlib_data_adapter.py)

**Mock 使用**:
```python
from unittest.mock import MagicMock, patch, PropertyMock

@pytest.fixture
def mock_qlib(self):
    """Mock Qlib 模块"""
    mock = MagicMock()
    mock.data = MagicMock()
    mock.data.D = MagicMock()
    return mock

@pytest.fixture
def adapter(self, mock_qlib):
    return QlibDataAdapter(qlib_module=mock_qlib)
```

**风险等级**: ✅ **正常**

**用途**: 通过依赖注入测试适配器逻辑

---

### 2.3 其他测试文件中的 Mock

**涉及文件**:
- `tests/unit/adapters/hikyuu/test_hikyuu_data_adapter.py`
- `tests/unit/adapters/hikyuu/test_hikyuu_backtest_adapter.py`
- `tests/unit/adapters/hikyuu/test_indicator_calculator_adapter.py`
- `tests/unit/adapters/repositories/test_sqlite_model_repository.py`
- `tests/unit/adapters/repositories/test_yaml_config_repository.py`
- `tests/unit/adapters/converters/test_signal_converter_adapter.py`
- `tests/unit/use_cases/*/test_*.py` (多个用例测试)

**Mock 使用统计**:
- 使用 `@pytest.fixture` 定义 Mock fixtures: ~30个
- 使用 `MagicMock`: ~50次
- 使用 `@patch` 装饰器: ~20次

**风险等级**: ✅ **正常**

**用途**: 标准的单元测试隔离外部依赖

---

## 3. 当前实际使用的适配器

### 3.1 正在使用的适配器

根据 DI 容器配置 ([src/controllers/cli/di/container.py](../src/controllers/cli/di/container.py)):

```python
class Container:
    def __init__(self):
        # 数据提供者 - 使用 Hikyuu ✅
        self.data_provider = HikyuuDataAdapter(
            config_file="config/hikyuu.ini"
        )

        # 模型训练器 - 使用 Qlib ✅
        self.model_trainer = QlibModelTrainerAdapter()

        # 回测引擎 - 使用 Hikyuu ✅
        self.backtest_engine = HikyuuBacktestAdapter(
            config_file="config/hikyuu.ini"
        )
```

**结论**:
- ✅ **生产环境使用真实的 Hikyuu 和 Qlib**
- ✅ **不依赖 Mock 对象**
- ⚠️ **但条件导入仍存在潜在风险**

---

## 4. Mock 使用最佳实践

### 4.1 单元测试中的 Mock ✅

**推荐做法**:
```python
# 1. 使用 pytest fixtures
@pytest.fixture
def mock_data_provider():
    """Mock 数据提供者"""
    mock = MagicMock(spec=IStockDataProvider)
    mock.load_stock_data.return_value = [...]
    return mock

# 2. 使用 patch 装饰器
@patch('module.external_dependency')
async def test_something(mock_dependency):
    mock_dependency.return_value = expected_value
    # ... 测试逻辑

# 3. 依赖注入
class MyAdapter:
    def __init__(self, dependency=None):
        self.dependency = dependency or real_dependency
```

### 4.2 生产代码中应避免 Mock ❌

**不推荐**:
```python
# ❌ 不好的做法
try:
    import some_library
except ImportError:
    some_library = None  # 生产代码中使用 None
```

**推荐**:
```python
# ✅ 好的做法
try:
    import some_library
    LIBRARY_AVAILABLE = True
except ImportError:
    some_library = None
    LIBRARY_AVAILABLE = False

class MyClass:
    def __init__(self):
        if not LIBRARY_AVAILABLE:
            raise ImportError(
                "Required library not installed. "
                "Install with: pip install some_library"
            )
        self.lib = some_library
```

---

## 5. 改进建议

### 5.1 立即改进（高优先级）

#### 问题 1: Hikyuu 适配器的条件导入

**影响文件**:
- `src/adapters/hikyuu/hikyuu_data_adapter.py`
- `src/adapters/hikyuu/hikyuu_backtest_adapter.py`
- `src/adapters/hikyuu/indicator_calculator_adapter.py`

**建议改进**:

```python
# 当前代码
try:
    import hikyuu as hku
    from hikyuu import hikyuu_init
except ImportError:
    hku = None
    hikyuu_init = None

# 改进后
try:
    import hikyuu as hku
    from hikyuu import hikyuu_init
    HIKYUU_AVAILABLE = True
except ImportError:
    hku = None
    hikyuu_init = None
    HIKYUU_AVAILABLE = False

class HikyuuDataAdapter(IStockDataProvider):
    def __init__(self, config_file: str):
        if not HIKYUU_AVAILABLE:
            raise ImportError(
                "Hikyuu library is required but not installed.\n"
                "Install with: pip install hikyuu\n"
                "Or: conda install -c conda-forge hikyuu"
            )

        if not hku:
            raise RuntimeError("Hikyuu imported but module is None")

        self.hku = hku
        # ... 继续初始化
```

**收益**:
- ✅ 更清晰的错误提示
- ✅ 在初始化时而非运行时检测依赖
- ✅ 提供安装指导

---

### 5.2 中期改进（中优先级）

#### 添加依赖检查脚本

创建 `scripts/check_dependencies.py`:

```python
#!/usr/bin/env python3
"""检查项目依赖是否安装"""

import sys

def check_dependencies():
    """检查所有必需的依赖"""
    missing = []

    try:
        import hikyuu
        print("✓ Hikyuu installed")
    except ImportError:
        print("✗ Hikyuu NOT installed")
        missing.append("hikyuu")

    try:
        import lightgbm
        print("✓ LightGBM installed")
    except ImportError:
        print("✗ LightGBM NOT installed")
        missing.append("lightgbm")

    # ... 检查其他依赖

    if missing:
        print(f"\n缺少依赖: {', '.join(missing)}")
        print("请运行: pip install " + " ".join(missing))
        sys.exit(1)
    else:
        print("\n✓ 所有依赖已安装")
        sys.exit(0)

if __name__ == "__main__":
    check_dependencies()
```

**使用方式**:
```bash
# 在运行应用前检查
python scripts/check_dependencies.py

# 在 CI/CD 中检查
./scripts/check_dependencies.py || exit 1
```

---

### 5.3 长期改进（低优先级）

#### 1. 使用依赖注入框架

考虑使用 `dependency-injector` 等框架，完全消除对 Mock 的依赖：

```python
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    data_provider = providers.Singleton(
        HikyuuDataAdapter,
        config_file=config.hikyuu.config_file
    )

    model_trainer = providers.Singleton(QlibModelTrainerAdapter)
```

#### 2. 添加健康检查端点

如果是 Web 应用，添加健康检查：

```python
@app.get("/health")
async def health_check():
    """健康检查端点"""
    checks = {
        "hikyuu": HIKYUU_AVAILABLE,
        "lightgbm": LIGHTGBM_AVAILABLE,
        "database": await check_database(),
    }

    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503

    return JSONResponse(
        status_code=status_code,
        content={"status": "healthy" if all_healthy else "unhealthy", "checks": checks}
    )
```

---

## 6. 总结

### 当前状态

| 方面 | 评分 | 说明 |
|------|------|------|
| **单元测试 Mock 使用** | ✅ 9/10 | 规范，符合最佳实践 |
| **生产代码 Mock 使用** | ⚠️ 5/10 | 存在条件导入，有改进空间 |
| **依赖管理** | ⚠️ 6/10 | 缺少明确的依赖检查 |
| **错误处理** | ⚠️ 5/10 | 运行时错误不够清晰 |
| **整体代码质量** | ✅ 7/10 | 良好，但需要改进生产代码中的 Mock |

### 关键行动项

1. **高优先级** ⚠️
   - [ ] 改进 Hikyuu 适配器的条件导入，添加明确的错误提示
   - [ ] 在适配器初始化时检查依赖是否可用

2. **中优先级**
   - [ ] 创建依赖检查脚本
   - [ ] 添加 CI/CD 依赖检查步骤
   - [ ] 更新文档说明依赖安装方式

3. **低优先级**
   - [ ] 考虑使用依赖注入框架
   - [ ] 添加健康检查机制（如果适用）

---

## 附录

### A. 完整的 Mock 位置列表

#### 生产代码
1. `src/adapters/hikyuu/hikyuu_data_adapter.py:5-10`
2. `src/adapters/hikyuu/hikyuu_backtest_adapter.py:3-8`
3. `src/adapters/hikyuu/indicator_calculator_adapter.py:3-8`
4. `src/adapters/qlib/qlib_data_adapter.py:30-40` (依赖注入)

#### 测试代码
1. `tests/unit/adapters/qlib/test_qlib_data_adapter.py`
2. `tests/unit/adapters/qlib/test_qlib_model_trainer_adapter.py`
3. `tests/unit/adapters/hikyuu/test_*.py`
4. `tests/unit/adapters/repositories/test_*.py`
5. `tests/unit/adapters/converters/test_*.py`
6. `tests/unit/use_cases/*/test_*.py`

### B. 相关文档

- [项目配置指南](PROJECT_CONFIG_FINAL_REPORT.md)
- [依赖管理指南](../requirements.txt)
- [测试指南](../tests/README.md)

---

**报告生成**: 2025-11-14
**审计者**: Claude Code
**版本**: 1.0
