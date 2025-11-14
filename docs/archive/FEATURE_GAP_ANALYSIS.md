# 产品功能缺口分析报告

**生成时间**: 2025-11-14
**分析对象**: Hikyuu × Qlib 个人量化工作站
**对照文档**: [PRD](prd.md)

---

## 执行摘要

### 总体完成度

| 功能模块 | PRD要求 | 已实现 | 完成度 | 优先级 |
|---------|---------|--------|--------|--------|
| **数据与特征** | 3项 | 2项 | 66% | P0-P1 |
| **机器学习建模** | 4项 | 2项 | 50% | P0-P1 |
| **策略执行与回测** | 3项 | 0项 | 0% | P0-P1 |
| **配置与复盘** | 4项 | 1项 | 25% | P0-P1 |
| **总体** | **14项** | **5项** | **36%** | - |

### 关键发现

✅ **已实现的核心功能**:
- 数据加载（Hikyuu → 训练数据）
- 模型训练（单股票 + 指数批量）
- 技术指标特征工程
- 依赖检查工具
- 批量训练基础架构

❌ **缺失的关键功能**:
- Qlib DataLoader 适配器（P0）
- 信号转换适配器（P0）
- Hikyuu 回测集成（P0）
- 配置文件驱动（P0）
- 端到端示例（P0）
- 实验记录系统（P1）

⚠️ **部分实现的功能**:
- 特征模板（仅基础技术指标，无YAML/JSON配置）
- 日志系统（有基础日志，无完整监控）

---

## 详细功能对比

## 4.1 数据与特征（Qlib 数据加载 / 建模准备）

### 4.1.1 数据接入向导 ⚠️ 部分实现

**PRD要求**:
> 提供脚本/简易 UI 指引用户配置 Hikyuu 数据目录、市场、标的、时间范围。默认支持日线 HDF5 数据。

**当前状态**: ⚠️ **部分实现**

**已实现**:
- ✅ CLI 命令行参数配置（`data load --code --start --end --kline-type`）
- ✅ 支持多种K线类型（DAY, WEEK, MONTH, MIN5等）
- ✅ Hikyuu 数据目录配置（[config/hikyuu.ini](../config/hikyuu.ini)）

**缺失**:
- ❌ 无简易UI引导
- ❌ 无向导式配置流程
- ❌ 无HDF5数据格式支持（仅支持MySQL）
- ❌ 无市场批量配置

**代码位置**:
- [src/controllers/cli/commands/data.py:32-110](../src/controllers/cli/commands/data.py#L32-L110) - `data load` 命令

**改进建议**:
1. 添加 `data init` 命令，向导式配置
2. 支持HDF5数据源
3. 提供配置模板和验证

**优先级**: P0

---

### 4.1.2 Qlib DataLoader 适配 ❌ 未实现

**PRD要求**:
> 提供 **`HikyuuDataLoader`**，默认加载核心字段（开高低收量额、复权因子等）。支持可选的增量加载模式以控制内存占用。

**当前状态**: ❌ **未实现**

**已实现**:
- ✅ 基础数据转换工具（[src/utils/data_conversion.py](../src/utils/data_conversion.py)）
- ✅ K线数据到DataFrame转换
- ✅ 直接集成到训练流程（无需单独DataLoader）

**缺失**:
- ❌ **没有独立的 `HikyuuDataLoader` 类符合Qlib接口规范**
- ❌ 无增量加载模式
- ❌ 无复权因子处理
- ❌ 未遵循Qlib DataLoader接口标准

**影响**:
- 当前实现绕过了Qlib标准数据接口
- 无法使用Qlib原生的数据处理能力
- 无法与Qlib生态工具集成

**代码位置**:
- [src/utils/data_conversion.py](../src/utils/data_conversion.py) - 当前转换工具
- [src/adapters/qlib/qlib_data_adapter.py](../src/adapters/qlib/qlib_data_adapter.py) - 仅用于单元测试，生产未使用

**改进建议**:
创建符合Qlib标准的DataLoader：

```python
# 建议实现
class HikyuuDataLoader(DataLoader):
    """Qlib标准的Hikyuu数据加载器"""

    def __init__(self, config):
        self.hikyuu_config = config

    def load(self, instruments, start_time, end_time, freq, fields):
        """符合Qlib接口的数据加载"""
        # 从Hikyuu加载数据
        # 返回MultiIndex DataFrame (instrument, datetime)

    def load_incremental(self, last_datetime):
        """增量加载模式"""
        pass
```

**优先级**: P0 ⚠️ **高优先级缺失**

---

### 4.1.3 特征模板 ⚠️ 部分实现

**PRD要求**:
> 附带常用技术指标组合（EMA, MACD, RSI, 量价等），导出为 Qlib 特征。支持 YAML/JSON 模板自定义参数。

**当前状态**: ⚠️ **部分实现**

**已实现**:
- ✅ 基础技术指标（MA5/10/20/60, 收益率, 波动率, 成交量变化）
- ✅ 价格位置、振幅、量价相关性
- ✅ 自动特征生成（[data_conversion.py:86-145](../src/utils/data_conversion.py#L86-L145)）

**缺失**:
- ❌ **无YAML/JSON配置文件支持**
- ❌ 缺少EMA, MACD, RSI, KDJ, BOLL等常用指标
- ❌ 无特征模板库
- ❌ 无参数化配置（窗口期、阈值等硬编码）

**代码位置**:
- [src/utils/data_conversion.py:86-145](../src/utils/data_conversion.py#L86-L145) - `add_technical_indicators()`

**改进建议**:
1. 创建特征配置文件：
```yaml
# features.yaml
features:
  - name: ma_cross
    type: moving_average
    params:
      windows: [5, 10, 20, 60]

  - name: macd
    type: macd
    params:
      fast: 12
      slow: 26
      signal: 9

  - name: rsi
    type: rsi
    params:
      period: 14
```

2. 支持配置文件驱动的特征生成
3. 提供预设模板（动量型、趋势型、波动型等）

**优先级**: P1

---

## 4.2 机器学习建模与实验（Qlib 核心职责）

### 4.2.1 快速训练脚本 ✅ 已实现

**PRD要求**:
> 默认 LGBModel + 基础指标数据集，**一键训练并生成 Qlib 预测结果 (`pred.pkl`)**。支持命令行参数指定训练窗口。

**当前状态**: ✅ **已实现**

**已实现**:
- ✅ CLI命令 `model train` ([model.py:35-145](../src/controllers/cli/commands/model.py#L35-L145))
- ✅ 支持LGBM模型训练
- ✅ 命令行参数指定股票代码、日期范围
- ✅ 两种模式：从文件加载 / 从Hikyuu直接加载
- ✅ 自动特征工程和标签生成

**缺失**:
- ❌ **没有生成 `pred.pkl` 预测文件**（当前仅训练，不生成预测）
- ❌ 未实现预测功能

**代码位置**:
- [src/controllers/cli/commands/model.py:35-261](../src/controllers/cli/commands/model.py#L35-L261)
- [src/use_cases/model/train_model.py](../src/use_cases/model/train_model.py)

**改进建议**:
添加预测生成功能：
```bash
# 训练后自动生成预测
hikyuu-qlib model predict --model-id <id> --start 2024-01-01 --end 2024-12-31 --output pred.pkl
```

**优先级**: P0 ⚠️ **核心功能缺失**

---

### 4.2.2 实验记录 ❌ 未实现

**PRD要求**:
> **默认使用 Qlib 内置的 R 模块**，在本地记录参数、指标与预测文件，确保轻量可用。

**当前状态**: ❌ **未实现**

**已实现**:
- ✅ 模型持久化到SQLite（[sqlite_model_repository.py](../src/adapters/repositories/sqlite_model_repository.py)）
- ✅ 记录模型ID、类型、状态、指标

**缺失**:
- ❌ **未集成Qlib的实验记录模块（R模块）**
- ❌ 无实验版本管理
- ❌ 无参数对比
- ❌ 无可视化实验结果

**影响**:
- 无法追溯实验历史
- 难以对比不同参数配置
- 缺少科学的实验管理

**改进建议**:
集成Qlib实验记录：
```python
from qlib.workflow import R

# 记录实验
with R.start(experiment_name="hs300_lgbm"):
    R.log_params(hyperparameters)
    R.log_metrics(metrics)
    R.save_objects(pred=predictions)
```

**优先级**: P1

---

### 4.2.3 约束机制 ⚠️ 部分实现

**PRD要求**:
> 预设训练资源上限、评估指标阈值；记录数据版本与特征编排，确保训练可复现。

**当前状态**: ⚠️ **部分实现**

**已实现**:
- ✅ 评估指标阈值验证（R² > 0.3 for single stock, > 0.1 for multi-stock）
- ✅ 模型状态管理（PENDING/TRAINING/TRAINED/FAILED）

**缺失**:
- ❌ 无训练资源上限（时间、内存）
- ❌ 无数据版本记录
- ❌ 无特征编排记录
- ❌ 训练不可完全复现（缺少随机种子、环境信息）

**代码位置**:
- [src/domain/entities/model.py](../src/domain/entities/model.py)

**改进建议**:
添加训练约束：
```python
@dataclass
class TrainingConstraints:
    max_training_time_seconds: int = 3600
    max_memory_mb: int = 8192
    min_r2_threshold: float = 0.3
    random_seed: int = 42
```

**优先级**: P1

---

### 4.2.4 透明性 ⚠️ 部分实现

**PRD要求**:
> **Qlib 训练后**输出特征重要度、预测区间等可解释信息。

**当前状态**: ⚠️ **部分实现**

**已实现**:
- ✅ 训练指标输出（RMSE, MAE, R²）
- ✅ CLI友好的结果展示

**缺失**:
- ❌ **无特征重要度分析**
- ❌ 无预测区间
- ❌ 无SHAP值等可解释性工具

**代码位置**:
- [src/controllers/cli/commands/model.py:250-256](../src/controllers/cli/commands/model.py#L250-L256)

**改进建议**:
```python
# 添加特征重要度输出
feature_importance = model.get_feature_importance()
output.info("Top 10 features:")
for feat, score in feature_importance[:10]:
    output.info(f"  {feat}: {score:.4f}")
```

**优先级**: P1

---

## 4.3 策略执行与回测（Hikyuu 核心职责）

### 4.3.1 信号转换适配器 ❌ 未实现

**PRD要求**:
> 将 **Qlib 的 `pred.pkl`**（MultiIndex DataFrame）转换为 Hikyuu **内置信号格式**（CSV/JSON），作为 Hikyuu 策略的输入。支持 Top-K 选股与择时信号映射规则。

**当前状态**: ❌ **未实现**

**已实现**:
- ✅ 有信号转换适配器接口定义（[signal_converter.py](../src/domain/ports/signal_converter.py)）
- ✅ 有基础实现骨架（[signal_converter_adapter.py](../src/adapters/converters/signal_converter_adapter.py)）
- ✅ 有TradingSignal实体定义

**缺失**:
- ❌ **无从Qlib预测到Hikyuu信号的实际转换逻辑**
- ❌ 无 `pred.pkl` 解析功能
- ❌ 无Top-K选股规则实现
- ❌ 无择时信号映射
- ❌ 无CSV/JSON输出格式

**影响**:
- **无法将模型预测结果用于回测**
- **无法形成完整的AI策略闭环**

**代码位置**:
- [src/adapters/converters/signal_converter_adapter.py](../src/adapters/converters/signal_converter_adapter.py) - 仅空壳
- [docs/integration/SIGNAL_CONVERSION_SOLUTION.md](integration/SIGNAL_CONVERSION_SOLUTION.md) - 设计文档

**改进建议**:
实现完整的信号转换：
```python
class QlibToHikyuuSignalConverter:
    def convert_predictions_to_signals(
        self,
        pred_pkl_path: str,
        top_k: int = 50,
        output_format: str = "csv"
    ) -> List[TradingSignal]:
        """将Qlib预测转换为Hikyuu信号"""
        # 1. 读取pred.pkl
        predictions = pd.read_pickle(pred_pkl_path)

        # 2. Top-K选股
        top_stocks = predictions.nlargest(top_k, 'score')

        # 3. 生成信号
        signals = []
        for stock, row in top_stocks.iterrows():
            signal = TradingSignal(
                stock_code=stock,
                action=SignalAction.BUY if row['score'] > 0 else SignalAction.SELL,
                strength=abs(row['score']),
                timestamp=row['date']
            )
            signals.append(signal)

        # 4. 导出为Hikyuu格式
        self._export_to_hikyuu_format(signals, output_format)

        return signals
```

**优先级**: P0 ⚠️ **关键缺口**

---

### 4.3.2 回测脚本 ❌ 未实现

**PRD要求**:
> **调用 Hikyuu 内置的 Portfolio/TradeManager** 完成回测，输出收益曲线与关键指标。输出 CSV 或图形结果。

**当前状态**: ❌ **未实现**

**已实现**:
- ✅ 有回测引擎接口定义（[backtest_engine.py](../src/domain/ports/backtest_engine.py)）
- ✅ 有Hikyuu回测适配器（[hikyuu_backtest_adapter.py](../src/adapters/hikyuu/hikyuu_backtest_adapter.py)）
- ✅ 有回测实体定义（[backtest.py](../src/domain/entities/backtest.py)）

**缺失**:
- ❌ **回测适配器为空实现（仅pass）**
- ❌ 无实际的Hikyuu Portfolio/TradeManager调用
- ❌ 无CLI命令
- ❌ 无收益曲线输出
- ❌ 无CSV/图形结果导出

**影响**:
- **无法验证AI策略的实际效果**
- **无法完成从训练到回测的闭环**

**代码位置**:
- [src/adapters/hikyuu/hikyuu_backtest_adapter.py](../src/adapters/hikyuu/hikyuu_backtest_adapter.py) - 空实现
- [src/use_cases/backtest/run_backtest.py](../src/use_cases/backtest/run_backtest.py) - Use Case定义
- [docs/integration/HIKYUU_BACKTEST_INTEGRATION.md](integration/HIKYUU_BACKTEST_INTEGRATION.md) - 设计文档

**改进建议**:
1. 实现Hikyuu回测适配器
2. 添加CLI命令：
```bash
hikyuu-qlib backtest run --signals signals.csv --start 2023-01-01 --end 2023-12-31 --output results.csv
```

**优先级**: P0 ⚠️ **关键缺口**

---

### 4.3.3 半自动执行 ❌ 未实现

**PRD要求**:
> **利用 Hikyuu 的内置功能**在 GUI/命令行中展示格式化调仓建议，用户确认后再执行。设定仓位限制、止损止盈等安全约束。

**当前状态**: ❌ **未实现**

**已实现**:
- ✅ 有Portfolio实体定义（[portfolio.py](../src/domain/entities/portfolio.py)）

**缺失**:
- ❌ 无调仓建议生成
- ❌ 无用户确认流程
- ❌ 无仓位管理
- ❌ 无止损止盈
- ❌ 无风控约束

**优先级**: P1（非MVP必需）

---

## 4.4 配置、日志与复盘

### 4.4.1 配置优先 ❌ 未实现

**PRD要求**:
> 所有可变参数（标的池、时间区间、特征列表、模型参数等）统一抽离至 `config.yaml`。用户 80% 场景仅需修改配置。

**当前状态**: ❌ **未实现**

**已实现**:
- ✅ 有Hikyuu配置文件（[config/hikyuu.ini](../config/hikyuu.ini)）
- ✅ 有配置Repository接口（[config_repository.py](../src/domain/ports/config_repository.py)）
- ✅ 有YAML配置Repository实现（[yaml_config_repository.py](../src/adapters/repositories/yaml_config_repository.py)）

**缺失**:
- ❌ **无统一的 `config.yaml` 文件**
- ❌ 参数分散在命令行参数中
- ❌ 无配置驱动的训练流程
- ❌ 无配置模板

**影响**:
- 用户需要每次输入大量命令行参数
- 无法快速复现实验
- 配置管理混乱

**改进建议**:
创建统一配置文件：
```yaml
# config.yaml
data:
  source: hikyuu
  hikyuu_config: config/hikyuu.ini

training:
  model_type: LGBM
  hyperparameters:
    num_leaves: 31
    learning_rate: 0.05

  data:
    stock_pool: [sh600000, sh600036, sz000001]
    date_range:
      start: 2023-01-01
      end: 2023-12-31
    kline_type: DAY

  features:
    template: momentum
    config: features.yaml

backtest:
  initial_cash: 1000000
  commission_rate: 0.0003
  slippage: 0.001
```

添加命令：
```bash
hikyuu-qlib run --config config.yaml
```

**优先级**: P0 ⚠️ **关键缺口**

---

### 4.4.2 端到端示例 ❌ 未实现

**PRD要求**:
> 提供一套完整的示例策略，包含数据准备、**Qlib 训练/预测**、信号转换、**Hikyuu 回测**与基础报告。

**当前状态**: ❌ **未实现**

**已实现**:
- ✅ 有单独的测试脚本（[test_index_constituents.py](../test_index_constituents.py)）
- ✅ 有文档和指南

**缺失**:
- ❌ **无完整的端到端示例脚本**
- ❌ 无从数据加载→训练→预测→信号转换→回测的完整流程
- ❌ 无示例配置文件
- ❌ 无示例结果展示

**影响**:
- 新用户无法快速上手
- 无法理解完整工作流程

**改进建议**:
创建示例脚本：
```bash
# examples/end_to_end_example.sh

# 1. 数据准备
hikyuu-qlib data load --code sh600036 --start 2023-01-01 --end 2023-12-31 --output data/train.csv

# 2. 模型训练
hikyuu-qlib model train --type LGBM --name example_model --data data/train.csv

# 3. 生成预测
hikyuu-qlib model predict --model-id <id> --output predictions/pred.pkl

# 4. 信号转换
hikyuu-qlib signals convert --predictions predictions/pred.pkl --output signals/signals.csv

# 5. 回测
hikyuu-qlib backtest run --signals signals/signals.csv --output results/backtest_result.csv

# 6. 生成报告
hikyuu-qlib report generate --backtest results/backtest_result.csv --output reports/report.html
```

**优先级**: P0 ⚠️ **关键缺口**

---

### 4.4.3 日志与监控 ⚠️ 部分实现

**PRD要求**:
> 记录数据更新、训练、信号生成、执行结果，提供简易日志管理。

**当前状态**: ⚠️ **部分实现**

**已实现**:
- ✅ 基础日志框架（[app_logging/](../src/infrastructure/app_logging/)）
- ✅ CLI输出工具（[cli/utils/output.py](../src/controllers/cli/utils/output.py)）
- ✅ 错误日志检测脚本（[run_test_with_error_check.sh](../run_test_with_error_check.sh)）

**缺失**:
- ❌ 无统一的日志配置
- ❌ 日志分散，难以追踪
- ❌ 无日志查询工具

**优先级**: P1

---

### 4.4.4 复盘工具 ❌ 未实现

**PRD要求**:
> 自动生成策略**回测结果 CSV** 和**基础收益曲线图表**，支持对比多个实验的回测表现。

**当前状态**: ❌ **未实现**

**已实现**:
- 无

**缺失**:
- ❌ 无回测结果生成（依赖4.3.2）
- ❌ 无收益曲线图表
- ❌ 无实验对比工具

**改进建议**:
```bash
# 生成回测报告
hikyuu-qlib report generate --backtest results/*.csv --output report.html

# 对比多个实验
hikyuu-qlib report compare --experiments exp1,exp2,exp3 --output comparison.html
```

**优先级**: P1

---

## 功能优先级矩阵

### P0 功能（MVP必需）- 7项

| 功能ID | 功能名称 | 当前状态 | 工作量估算 |
|--------|---------|---------|-----------|
| 4.1.2 | Qlib DataLoader 适配 | ❌ 未实现 | 3天 |
| 4.2.1 | 预测生成（pred.pkl） | ❌ 缺失 | 2天 |
| 4.3.1 | 信号转换适配器 | ❌ 未实现 | 5天 |
| 4.3.2 | 回测脚本 | ❌ 未实现 | 5天 |
| 4.4.1 | 配置优先 | ❌ 未实现 | 3天 |
| 4.4.2 | 端到端示例 | ❌ 未实现 | 2天 |
| 4.1.1 | 数据接入向导 | ⚠️ 部分实现 | 2天 |

**总计**: 22人天（约3-4周）

### P1 功能（增强特性）- 7项

| 功能ID | 功能名称 | 当前状态 | 工作量估算 |
|--------|---------|---------|-----------|
| 4.1.3 | 特征模板（YAML配置） | ⚠️ 部分实现 | 3天 |
| 4.2.2 | 实验记录 | ❌ 未实现 | 3天 |
| 4.2.3 | 约束机制 | ⚠️ 部分实现 | 2天 |
| 4.2.4 | 透明性 | ⚠️ 部分实现 | 2天 |
| 4.3.3 | 半自动执行 | ❌ 未实现 | 5天 |
| 4.4.3 | 日志与监控 | ⚠️ 部分实现 | 2天 |
| 4.4.4 | 复盘工具 | ❌ 未实现 | 3天 |

**总计**: 20人天（约2-3周）

---

## 架构完整性评估

### 已实现的架构组件

✅ **Domain Layer (领域层)**:
- Value Objects: StockCode, DateRange, KLineType, Market
- Entities: Model, KLineData, Prediction, TradingSignal, Portfolio, Backtest
- Ports (接口): 全部定义完成

✅ **Use Cases (应用层)**:
- LoadStockData ✅
- TrainModel ✅
- GeneratePredictions ⚠️ (仅定义)
- ConvertPredictionsToSignals ⚠️ (仅定义)
- RunBacktest ⚠️ (仅定义)

✅ **Adapters (适配器层)**:
- HikyuuDataAdapter ✅
- QlibModelTrainerAdapter ✅
- SqliteModelRepository ✅
- YamlConfigRepository ✅
- HikyuuBacktestAdapter ❌ (空实现)
- SignalConverterAdapter ❌ (空实现)

✅ **Controllers (控制器层)**:
- CLI Commands ✅
- DI Container ✅

### 缺失的架构组件

❌ **端到端流程编排**:
- 无工作流引擎
- 各个组件未连接成完整流程

❌ **Qlib集成**:
- 未使用Qlib的数据接口
- 未使用Qlib的实验管理
- 仅使用了Qlib的模型训练

---

## 与PRD用户旅程的差距

### PRD定义的用户旅程

1. ✅ **安装配置** - 已实现依赖检查（[scripts/check_dependencies.py](../scripts/check_dependencies.py)）
2. ⚠️ **数据准备** - 部分实现（可加载数据，但无Qlib Dataset生成）
3. ✅ **模型训练** - 已实现
4. ❌ **信号转换** - 未实现
5. ❌ **策略执行** - 未实现
6. ❌ **复盘迭代** - 未实现

### 当前能完成的旅程

```bash
# 现在用户只能做到：
1. 检查依赖 ✅
2. 加载数据 ✅
3. 训练模型 ✅
4. 查看训练指标 ✅

# 无法完成：
5. 生成预测 ❌
6. 转换信号 ❌
7. 回测验证 ❌
8. 查看收益曲线 ❌
```

**完成度**: 约40%

---

## 关键技术债务

### 1. 未使用Qlib标准接口

**问题**: 当前实现绕过了Qlib的数据和实验管理

**影响**:
- 无法享受Qlib生态的便利
- 难以集成第三方Qlib工具
- 不符合PRD中"融合Qlib能力"的初衷

**解决方案**: 重构数据层，使用Qlib DataHandler

### 2. 信号转换和回测缺失

**问题**: 无法形成完整的AI策略闭环

**影响**:
- **用户无法验证模型实际效果**
- **产品价值无法体现**

**解决方案**: 优先实现4.3.1和4.3.2

### 3. 配置管理混乱

**问题**: 参数分散在命令行、代码、配置文件中

**影响**:
- 用户体验差
- 无法快速迭代
- 难以复现实验

**解决方案**: 实现统一配置文件驱动

---

## 推荐实施路线图

### Phase 1: 完成核心闭环（2周）

**目标**: 实现从训练到回测的完整流程

```
Week 1:
- [ ] 实现预测生成功能（pred.pkl）
- [ ] 实现信号转换适配器
- [ ] 创建统一配置文件

Week 2:
- [ ] 实现Hikyuu回测适配器
- [ ] 创建端到端示例脚本
- [ ] 完善文档
```

**验收标准**:
```bash
# 用户能执行完整流程
hikyuu-qlib run --config examples/config.yaml

# 输出:
# - 训练指标
# - pred.pkl
# - signals.csv
# - backtest_result.csv
# - equity_curve.png
```

### Phase 2: 完善Qlib集成（1周）

```
- [ ] 实现HikyuuDataLoader（符合Qlib接口）
- [ ] 集成Qlib实验记录
- [ ] 添加特征重要度输出
```

### Phase 3: 增强特性（1周）

```
- [ ] YAML特征模板
- [ ] 更多技术指标（MACD, RSI, KDJ）
- [ ] 复盘对比工具
- [ ] 日志管理优化
```

### Phase 4: 优化体验（1周）

```
- [ ] 数据接入向导
- [ ] 交互式配置工具
- [ ] 结果可视化
- [ ] 性能优化
```

---

## 快速赢得用户的最小改进

如果时间有限，**优先实现以下3项**即可让产品基本可用：

### 1. 统一配置文件 (1天)

```yaml
# config.yaml - 让用户80%场景仅需改配置
training:
  code: sh600036
  start: 2023-01-01
  end: 2023-12-31
  model_type: LGBM
```

### 2. 预测生成 (2天)

```bash
# 让训练后能生成预测
hikyuu-qlib model predict --model-id <id> --output pred.pkl
```

### 3. 简化的端到端示例 (2天)

```bash
# examples/quick_start.sh
# 一键完成训练+预测
./quick_start.sh --config examples/config.yaml
```

**总计**: 5天即可让产品从"仅能训练"变为"基本可用"

---

## 总结

### 当前优势

1. ✅ **坚实的领域驱动设计基础** - DDD架构清晰
2. ✅ **模型训练功能完善** - 支持单股票和批量训练
3. ✅ **良好的代码质量** - 有单元测试、依赖检查、文档
4. ✅ **批量训练创新** - 支持指数成分股批量训练

### 关键缺口

1. ❌ **未形成完整闭环** - 无预测→信号→回测
2. ❌ **Qlib集成不足** - 未充分利用Qlib生态
3. ❌ **配置管理缺失** - 用户体验待提升

### 行动建议

**立即行动（本周）**:
1. 实现预测生成功能
2. 创建统一配置文件
3. 编写端到端示例

**短期目标（2周内）**:
1. 完成信号转换适配器
2. 实现Hikyuu回测
3. 形成完整可演示的闭环

**中期目标（1个月内）**:
1. 完善Qlib DataLoader
2. 集成实验管理
3. 优化用户体验

---

**报告完成时间**: 2025-11-14
**下一次审查**: 完成Phase 1后
