# 源代码审计报告

**审计日期**: 2025-11-20
**总文件数**: 111 个 Python 源文件
**审计目标**: 识别废弃、未使用或重复的源文件

---

## 审计结果总结

### ✅ 核心源文件 (保留)

**总计**: 99 个必要文件

#### 1. Domain 层 (DDD 核心) - 18 个文件
```
domain/
├── entities/          # 7 个实体
│   ├── backtest.py
│   ├── kline_data.py
│   ├── model.py
│   ├── portfolio.py
│   ├── prediction.py
│   ├── stock.py
│   └── trading_signal.py
├── ports/             # 8 个接口定义
│   ├── backtest_engine.py
│   ├── config_repository.py
│   ├── indicator_calculator.py
│   ├── model_repository.py
│   ├── model_trainer.py
│   ├── signal_converter.py
│   ├── signal_provider.py
│   └── stock_data_provider.py
└── value_objects/     # 6 个值对象
    ├── configuration.py
    ├── date_range.py
    ├── kline_type.py
    ├── market.py
    ├── rebalance_period.py
    └── stock_code.py
```

#### 2. Adapters 层 (接口实现) - 15 个文件
```
adapters/
├── hikyuu/            # 6 个 Hikyuu 适配器
│   ├── custom_sg_qlib_factor.py          ✅ 使用中 (workflow)
│   ├── custom_sg_qlib_factor_optimized.py ⚠️  未使用 (备选优化版本)
│   ├── dynamic_rebalance_sg.py           ⚠️  仅导入未实际使用
│   ├── hikyuu_backtest_adapter.py        ✅ 使用中 (CLI)
│   ├── hikyuu_data_adapter.py            ✅ 使用中
│   └── indicator_calculator_adapter.py   ✅ 使用中
├── qlib/              # 3 个 Qlib 适配器
│   ├── qlib_data_adapter.py              ⚠️  未使用 (已弃用)
│   ├── qlib_model_trainer_adapter.py     ✅ 使用中 (workflow)
│   └── portfolio_adapter.py              ✅ 使用中 (示例)
├── converters/        # 1 个转换器
│   └── signal_converter_adapter.py       ✅ 使用中
└── repositories/      # 2 个仓储
    ├── sqlite_model_repository.py        ✅ 使用中 (CLI)
    └── yaml_config_repository.py         ✅ 使用中 (CLI)
```

#### 3. Use Cases 层 (业务逻辑) - 12 个文件
```
use_cases/
├── analysis/
│   └── analyze_backtest_result.py        ✅ 使用中
├── backtest/
│   └── run_backtest.py                   ✅ 使用中
├── config/
│   ├── load_configuration.py             ✅ 使用中
│   └── save_configuration.py             ✅ 使用中
├── data/
│   └── load_stock_data.py                ✅ 使用中
├── indicators/
│   └── calculate_indicators.py           ✅ 使用中
├── model/
│   ├── generate_predictions.py           ✅ 使用中
│   └── train_model.py                    ✅ 使用中
├── portfolio/
│   └── manage_portfolio.py               ✅ 使用中
├── signals/
│   └── convert_predictions_to_signals.py ✅ 使用中
└── strategies/
    ├── generate_topk_signals.py          ✅ 使用中
    └── run_portfolio_backtest.py         ✅ 使用中
```

#### 4. Infrastructure 层 (基础设施) - 15 个文件
```
infrastructure/
├── app_logging/       # 1 个日志
│   └── logger.py
├── config/            # 5 个配置
│   ├── env.py
│   ├── loader.py
│   ├── settings.py
│   ├── unified_config.py
│   └── validator.py
├── errors/            # 4 个错误处理
│   ├── error_codes.py
│   ├── exceptions.py
│   ├── formatters.py
│   └── handlers.py
└── monitoring/        # 2 个监控
    ├── decorators.py
    └── metrics.py
```

#### 5. Controllers 层 (CLI) - 约 20 个文件
```
controllers/cli/
├── commands/          # 命令实现
├── config/            # CLI 配置
├── di/                # 依赖注入
│   └── container.py   ✅ 使用中
├── utils/             # CLI 工具
└── main.py            ✅ 使用中
```

#### 6. Utils 层 - 4 个文件
```
utils/
├── batch_config.py            ✅ 使用中
├── batch_training.py          ✅ 使用中
├── data_conversion.py         ✅ 使用中
└── index_constituents.py      ✅ 使用中
```

---

### ❌ 可删除的文件和目录

#### 1. 空目录 (3 个)

```bash
# 完全空的目录,只有 __init__.py
src/adapters/controllers/api/         # API 控制器 (未实现)
src/adapters/controllers/cli/         # 重复,应使用 src/controllers/cli/
src/models/                           # 空目录,没有任何内容
```

**建议操作**:
```bash
rm -rf src/adapters/controllers/api/
rm -rf src/adapters/controllers/cli/
rm -rf src/models/
```

#### 2. 废弃的适配器 (1 个)

```python
# src/adapters/qlib/qlib_data_adapter.py
```

**原因**:
- 项目已改为直接使用 Hikyuu 获取数据
- 没有任何文件导入或使用此适配器
- 功能已被 `hikyuu_data_adapter.py` 完全替代

**建议操作**:
```bash
rm -f src/adapters/qlib/qlib_data_adapter.py
```

#### 3. 未使用的优化版本 (1 个)

```python
# src/adapters/hikyuu/custom_sg_qlib_factor_optimized.py
```

**原因**:
- 这是 `custom_sg_qlib_factor.py` 的优化版本
- 但实际工作流中只使用了原始版本
- 没有任何地方导入此文件

**建议**: 保留作为备选方案,或者删除

#### 4. 仅导入未实际使用 (1 个)

```python
# src/adapters/hikyuu/dynamic_rebalance_sg.py
```

**原因**:
- 只在 `__init__.py` 中导入
- 没有实际使用案例
- 可能是计划功能但未实现

**建议**: 保留作为未来功能,或者删除

#### 5. 文档性质文件 (1 个)

```python
# src/adapters/signal/.claude.md
```

**原因**:
- 这是技术方案文档,不是源代码
- 应该移动到 `docs/` 目录

**建议操作**:
```bash
mv src/adapters/signal/.claude.md docs/integration/SIGNAL_ADAPTER_DESIGN.md
rm -rf src/adapters/signal/
```

---

## 清理建议

### 方案 A: 保守清理 (推荐)

只删除明确无用的内容:

```bash
cd /Users/zhenkunliu/project/hikyuu_qlib

# 1. 删除空目录
rm -rf src/adapters/controllers/api/
rm -rf src/adapters/controllers/cli/
rm -rf src/models/

# 2. 删除废弃适配器
rm -f src/adapters/qlib/qlib_data_adapter.py

# 3. 移动文档文件
mkdir -p docs/integration/
mv src/adapters/signal/.claude.md docs/integration/SIGNAL_ADAPTER_DESIGN.md
rm -rf src/adapters/signal/

# 4. 更新 __init__.py 文件
# 移除 qlib_data_adapter 的导入
sed -i '' '/qlib_data_adapter/d' src/adapters/qlib/__init__.py
```

**清理效果**:
- 减少 3 个空目录
- 减少 1 个废弃文件
- 减少 1 个文档文件
- 从 111 个文件 → ~105 个文件

### 方案 B: 激进清理

额外删除未使用的优化版本和计划功能:

```bash
# 在方案 A 基础上额外执行:

# 删除未使用的优化版本
rm -f src/adapters/hikyuu/custom_sg_qlib_factor_optimized.py

# 删除未实现的功能
rm -f src/adapters/hikyuu/dynamic_rebalance_sg.py

# 更新 __init__.py
sed -i '' '/custom_sg_qlib_factor_optimized/d' src/adapters/hikyuu/__init__.py
sed -i '' '/dynamic_rebalance_sg/d' src/adapters/hikyuu/__init__.py
```

**清理效果**:
- 从 111 个文件 → ~103 个文件

---

## 文件使用状态分析

### ✅ 高频使用 (核心文件)

| 文件 | 使用频率 | 依赖项目 |
|------|---------|----------|
| `qlib_model_trainer_adapter.py` | 高 | workflow, CLI |
| `custom_sg_qlib_factor.py` | 高 | workflow, backtest |
| `hikyuu_data_adapter.py` | 中 | workflow, CLI |
| `hikyuu_backtest_adapter.py` | 中 | workflow, CLI |
| `sqlite_model_repository.py` | 中 | CLI |

### ⚠️  低频使用 (可选文件)

| 文件 | 使用频率 | 说明 |
|------|---------|------|
| `portfolio_adapter.py` | 低 | 仅示例使用 |
| `indicator_calculator_adapter.py` | 低 | 工具类 |
| `signal_converter_adapter.py` | 低 | 工具类 |

### ❌ 零使用 (可删除)

| 文件 | 原因 |
|------|------|
| `qlib_data_adapter.py` | 功能已弃用 |
| `custom_sg_qlib_factor_optimized.py` | 备选未使用 |
| `dynamic_rebalance_sg.py` | 计划功能未实现 |
| `src/adapters/signal/.claude.md` | 文档误放 |

---

## 依赖关系分析

### 核心依赖链

```
examples/hikyuu_train_backtest_workflow.py
    ├─ adapters.qlib.qlib_model_trainer_adapter  ✅
    ├─ adapters.hikyuu.custom_sg_qlib_factor     ✅
    └─ adapters.hikyuu.hikyuu_data_adapter       ✅

examples/backtest_workflow_pred.py
    └─ adapters.hikyuu.custom_sg_qlib_factor     ✅

src/controllers/cli/di/container.py
    ├─ adapters.hikyuu.hikyuu_backtest_adapter   ✅
    ├─ adapters.repositories.sqlite_model_repository ✅
    └─ adapters.repositories.yaml_config_repository  ✅
```

### 孤立文件 (无依赖)

```
❌ adapters/qlib/qlib_data_adapter.py
⚠️  adapters/hikyuu/custom_sg_qlib_factor_optimized.py
⚠️  adapters/hikyuu/dynamic_rebalance_sg.py
```

---

## 执行清理

基于以上分析,我建议执行**方案 A: 保守清理**:

### 执行步骤

1. **删除空目录和废弃文件**
2. **移动文档文件到正确位置**
3. **更新相关 import 语句**
4. **验证项目仍可正常运行**

### 验证命令

清理后执行以下命令验证:

```bash
# 1. 检查 Python 语法
python -m py_compile src/**/*.py

# 2. 运行测试
pytest tests/ -v

# 3. 运行工作流
./run_backtest.sh workflow

# 4. 检查导入
python -c "from adapters.qlib import *; from adapters.hikyuu import *"
```

---

## 建议

### 立即执行

✅ **删除明确无用的内容** (方案 A)
- 3 个空目录
- 1 个废弃适配器
- 1 个误放文档

### 后续考虑

⚠️  **评估以下文件**:
- `custom_sg_qlib_factor_optimized.py` - 如果未来不需要优化版本,可删除
- `dynamic_rebalance_sg.py` - 如果不计划实现动态再平衡功能,可删除
- `portfolio_adapter.py` - 如果只用 Hikyuu 回测,可考虑删除

### 文档化

📝 **更新文档**:
- 更新架构图,移除已删除组件
- 更新 README,说明当前使用的适配器
- 创建 CHANGELOG 记录清理历史

---

**审计完成**: 识别出 6-8 个可删除文件/目录,建议执行保守清理方案
