# P0功能实施进度报告

**开始时间**: 2025-11-14
**实施方案**: 方案B - 完整MVP闭环（2周工作量）

## 实施状态总览

| 功能 | 状态 | 完成度 | 说明 |
|------|------|--------|------|
| 1. 统一配置文件 | ✅ 已完成 | 100% | config.yaml + unified_config.py |
| 2. 预测生成功能 | 🔄 进行中 | 80% | Use Case已实现，需添加CLI命令 |
| 3. Qlib DataLoader | ⏸️ 待实施 | 0% | 需实现符合Qlib标准的DataLoader |
| 4. 信号转换适配器 | ⏸️ 待实施 | 0% | pred.pkl → Hikyuu信号 |
| 5. Hikyuu回测集成 | ⏸️ 待实施 | 0% | 空适配器需实现 |
| 6. 端到端示例 | ⏸️ 待实施 | 0% | Shell脚本 + 文档 |

**总体完成度**: 约30%

---

## 已完成的工作

### 1. 统一配置文件系统 ✅

#### 文件清单
- [config.yaml](../config.yaml) - 统一配置文件
- [src/infrastructure/config/unified_config.py](../src/infrastructure/config/unified_config.py) - 配置管理模块

#### 功能特性
✅ **完整的配置结构**:
- 数据源配置
- 训练参数配置
- 预测配置
- 信号转换配置
- 回测配置
- 实验记录配置
- 日志配置

✅ **预设支持**:
```yaml
presets:
  development:  # 开发环境
  production:   # 生产环境
  testing:      # 测试环境
```

✅ **场景配置**:
```yaml
scenarios:
  single_stock:    # 单股票训练
  index_training:  # 指数批量训练
  quick_test:      # 快速测试
```

✅ **配置管理功能**:
- YAML文件加载
- 预设合并
- 配置验证
- 全局配置实例

#### 使用方式
```python
from infrastructure.config.unified_config import load_config, get_config

# 加载配置
config = load_config("config.yaml", preset="production")

# 获取配置
training_config = config.training
hyperparams = config.get_hyperparameters("LGBM")
```

---

### 2. 预测生成功能 🔄

#### 文件清单
- [src/use_cases/model/generate_predictions.py](../src/use_cases/model/generate_predictions.py) - 预测生成Use Case（已更新）

#### 已实现功能
✅ **核心预测逻辑**:
- 从模型仓储加载已训练模型
- 为多只股票批量生成预测
- 支持自定义日期范围和K线类型
- 错误处理和失败股票跟踪

✅ **多格式输出**:
```python
# Qlib标准格式（pred.pkl）
df_qlib = df.set_index(["stock_code", "timestamp"])
df_qlib = df_qlib.rename(columns={"predicted_value": "score"})
df_qlib.to_pickle(output_path)

# CSV格式
df.to_csv(output_path)

# Parquet格式
df.to_parquet(output_path)
```

✅ **详细信息保存**:
- 模型元数据
- 超参数
- 评估指标
- 特征重要度
- 预测统计信息

#### 待完成
❌ **CLI命令集成**:
需要添加 `model predict` 命令到 [src/controllers/cli/commands/model.py](../src/controllers/cli/commands/model.py)

```bash
# 期望的命令格式
hikyuu-qlib model predict --model-id <id> --code sh600036 --start 2024-01-01 --end 2024-12-31 --output predictions/pred.pkl

# 或使用配置文件
hikyuu-qlib model predict --model-id <id> --config config.yaml
```

❌ **DI容器集成**:
需要在 [src/controllers/cli/di/container.py](../src/controllers/cli/di/container.py) 添加Use Case实例

---

## 下一步工作计划

### 优先级1: 完成预测生成功能

**任务清单**:
1. ✅ 更新GeneratePredictionsUseCase
2. ⏳ 添加CLI命令 `model predict`
3. ⏳ 在DI容器中注册Use Case
4. ⏳ 测试预测生成流程
5. ⏳ 生成示例pred.pkl文件

**预计时间**: 2小时

### 优先级2: 实现信号转换适配器

**设计要点**:
```python
# src/adapters/converters/signal_converter_adapter.py

class QlibToHikyuuSignalConverter:
    def convert(
        self,
        pred_pkl_path: str,
        strategy: Dict[str, Any],  # 从config.yaml读取
        output_path: str
    ) -> List[TradingSignal]:
        """将Qlib pred.pkl转换为Hikyuu信号"""

        # 1. 读取pred.pkl
        predictions = pd.read_pickle(pred_pkl_path)

        # 2. 应用选股策略（top_k | threshold | percentile）
        selected = self._apply_strategy(predictions, strategy)

        # 3. 生成交易信号
        signals = self._generate_signals(selected)

        # 4. 导出为Hikyuu格式（CSV/JSON）
        self._export_to_hikyuu(signals, output_path)

        return signals
```

**预计时间**: 1天

### 优先级3: 实现Hikyuu回测集成

**设计要点**:
```python
# src/adapters/hikyuu/hikyuu_backtest_adapter.py

class HikyuuBacktestAdapter:
    async def run_backtest(
        self,
        signals_path: str,
        config: BacktestConfig,  # 从config.yaml读取
        output_path: str
    ) -> BacktestResult:
        """使用Hikyuu内置引擎运行回测"""

        # 1. 读取信号文件
        signals = self._load_signals(signals_path)

        # 2. 调用Hikyuu Portfolio/TradeManager
        portfolio = hku.Portfolio(
            initial_cash=config.initial_cash,
            commission_rate=config.commission["rate"],
            ...
        )

        # 3. 执行回测
        results = portfolio.run(signals)

        # 4. 生成报告和图表
        self._generate_report(results, output_path)

        return results
```

**预计时间**: 1天

### 优先级4: Qlib DataLoader适配器

**说明**: 这是一个可选优化项，当前已有直接的数据转换流程。如果时间有限，可以暂缓实施。

**预计时间**: 1天

### 优先级5: 端到端示例脚本

**文件**: `examples/quick_start.sh`

```bash
#!/bin/bash
# Hikyuu × Qlib 端到端示例

set -e

echo "=== Hikyuu × Qlib 端到端示例 ==="
echo ""

# 1. 数据加载
echo "[1/5] 加载股票数据..."
./run_cli.sh data load --code sh600036 --start 2023-01-01 --end 2023-12-31 --output data/training.csv --add-features --add-labels

# 2. 模型训练
echo ""
echo "[2/5] 训练模型..."
./run_cli.sh model train --type LGBM --name example_model --data data/training.csv

# 3. 生成预测
echo ""
echo "[3/5] 生成预测..."
./run_cli.sh model predict --model-id <id> --code sh600036 --start 2024-01-01 --end 2024-03-31 --output predictions/pred.pkl

# 4. 转换信号
echo ""
echo "[4/5] 转换交易信号..."
./run_cli.sh signals convert --predictions predictions/pred.pkl --output signals/signals.csv --strategy top_k --top-k 5

# 5. 回测
echo ""
echo "[5/5] 运行回测..."
./run_cli.sh backtest run --signals signals/signals.csv --start 2024-01-01 --end 2024-03-31 --output backtest_results/result.csv

echo ""
echo "=== 完成! ==="
echo "查看结果:"
echo "  - 预测文件: predictions/pred.pkl"
echo "  - 信号文件: signals/signals.csv"
echo "  - 回测结果: backtest_results/result.csv"
```

**预计时间**: 2小时

---

## 技术债务和改进点

### 1. PredictionBatch实体缺少to_dataframe方法

**问题**: [src/domain/entities/prediction.py](../src/domain/entities/prediction.py) 中的 `PredictionBatch` 类缺少 `to_dataframe()` 方法

**修复**:
```python
class PredictionBatch:
    def to_dataframe(self) -> pd.DataFrame:
        """转换为DataFrame格式"""
        records = []
        for pred in self.predictions:
            records.append({
                "stock_code": pred.stock_code.value,
                "timestamp": pred.timestamp,
                "predicted_value": pred.predicted_value,
                "confidence": pred.confidence,
                "model_id": pred.model_id
            })
        return pd.DataFrame(records)
```

### 2. Model实体需要is_ready_for_prediction方法

**问题**: [src/domain/entities/model.py](../src/domain/entities/model.py) 中 `is_ready_for_prediction()` 方法可能不存在

**修复**:
```python
def is_ready_for_prediction(self) -> bool:
    """检查模型是否可用于预测"""
    return self.is_trained() and self.trained_model is not None
```

### 3. 配置文件需要与DI容器集成

**任务**: 在Container中使用统一配置而不是硬编码参数

---

## 时间估算

| 阶段 | 任务 | 预计时间 |
|------|------|---------|
| Phase 1 | ✅ 统一配置文件 | 已完成 |
| Phase 2 | 🔄 预测生成CLI | 2小时 |
| Phase 3 | 信号转换适配器 | 1天 |
| Phase 4 | Hikyuu回测集成 | 1天 |
| Phase 5 | 端到端示例 | 2小时 |
| Phase 6 | 测试和文档 | 4小时 |
| **总计** | | **约3天** |

---

## 建议的继续方案

由于上下文即将耗尽，建议下次从以下任一入口继续：

### 方案A: 快速完成预测功能
1. 添加 `model predict` CLI命令
2. 测试生成pred.pkl
3. 验证Qlib格式正确性

### 方案B: 按顺序完成所有P0功能
1. 完成预测生成（含CLI）
2. 实现信号转换适配器
3. 实现Hikyuu回测集成
4. 创建端到端示例
5. 测试完整流程

### 方案C: 先创建端到端框架
1. 创建占位符命令（signals convert, backtest run）
2. 写好端到端脚本框架
3. 逐个实现适配器填充功能

**推荐**: 方案A，快速完成一个可演示的功能

---

**生成时间**: 2025-11-14
**当前状态**: 已完成30%，配置系统和预测Use Case已就绪
**下一步**: 添加CLI命令集成预测功能
