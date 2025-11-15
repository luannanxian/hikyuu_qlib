# Hikyuu-Qlib 量化交易平台完整使用指南

**版本**: v1.0
**更新日期**: 2025-01-16
**适用对象**: 量化交易初学者到高级用户

---

## 📑 目录

1. [快速开始](#1-快速开始)
2. [环境配置](#2-环境配置)
3. [数据准备](#3-数据准备)
4. [模型训练](#4-模型训练)
5. [预测生成](#5-预测生成)
6. [回测评估](#6-回测评估)
7. [实战案例](#7-实战案例)
8. [进阶技巧](#8-进阶技巧)
9. [常见问题](#9-常见问题)
10. [API参考](#10-api参考)

---

## 1. 快速开始

### 1.1 安装平台

```bash
# 克隆项目
git clone https://github.com/luannanxian/hikyuu_qlib.git
cd hikyuu_qlib

# 创建虚拟环境（推荐）
conda create -n qlib_hikyuu python=3.13
conda activate qlib_hikyuu

# 安装依赖
pip install -r requirements.txt

# 验证安装
./run_cli.sh --help
```

### 1.2 30秒快速体验

```bash
# 1. 查看可用数据
./run_cli.sh data list --source hikyuu --market SH | head -10

# 2. 训练一个简单模型（使用招商银行数据）
./run_cli.sh model train \
  --type LGBM \
  --name my_first_model \
  --code sh600036 \
  --start 2023-01-01 \
  --end 2023-12-31

# 3. 查看训练结果
./run_cli.sh model list --status TRAINED
```

**预期输出**:
- RMSE、R² 等模型指标
- 模型保存路径
- 训练时长

---

## 2. 环境配置

### 2.1 Hikyuu 配置

首次使用需要配置 Hikyuu 数据路径：

```bash
# 设置 Hikyuu 数据目录
./run_cli.sh config set HIKYUU_DATA_PATH /path/to/hikyuu/data

# 设置初始资金
./run_cli.sh config set INITIAL_CAPITAL 1000000

# 查看当前配置
./run_cli.sh config show
```

**配置文件位置**: `.hikyuu_qlib_config.yaml`

### 2.2 Qlib 配置

```bash
# Qlib 数据目录（可选）
./run_cli.sh config set QLIB_DATA_PATH ~/.qlib/qlib_data/cn_data

# 日志级别
./run_cli.sh config set LOG_LEVEL INFO

# 并行训练核心数
./run_cli.sh config set N_JOBS 4
```

### 2.3 配置优先级

```
命令行参数 > 环境变量 > 配置文件 > 默认值
```

---

## 3. 数据准备

### 3.1 查看可用数据

#### 方式1: 从本地文件扫描
```bash
./run_cli.sh data list --source files --format table
```

#### 方式2: 从Hikyuu数据库查询（推荐）
```bash
# 查看所有上海市场股票
./run_cli.sh data list --source hikyuu --market SH

# 查看深圳市场股票
./run_cli.sh data list --source hikyuu --market SZ

# 导出为JSON格式
./run_cli.sh data list --source hikyuu --format json > stocks.json
```

**输出示例**:
```
┌──────────┬────────┬─────────────┬─────────────┬─────────┐
│ 股票代码 │ 市场   │ 开始日期    │ 结束日期    │ 记录数  │
├──────────┼────────┼─────────────┼─────────────┼─────────┤
│ sh600000 │ SH     │ 1999-11-10  │ 2024-01-15  │ 5,832   │
│ sh600036 │ SH     │ 2002-04-09  │ 2024-01-15  │ 5,234   │
│ sh600519 │ SH     │ 2001-08-27  │ 2024-01-15  │ 5,412   │
└──────────┴────────┴─────────────┴─────────────┴─────────┘
```

### 3.2 加载单只股票数据

```bash
./run_cli.sh data load \
  --code sh600036 \
  --start 2020-01-01 \
  --end 2023-12-31 \
  --output data/sh600036.csv
```

### 3.3 批量加载（指数成分股）

```bash
# 加载沪深300成分股数据
./run_cli.sh data load-index \
  --index hs300 \
  --start 2020-01-01 \
  --end 2023-12-31 \
  --output-dir data/hs300/
```

**支持的指数**:
- `hs300`: 沪深300
- `sz50`: 上证50
- `zz500`: 中证500
- `zz1000`: 中证1000

---

## 4. 模型训练

### 4.1 基础训练

#### 训练单只股票模型
```bash
./run_cli.sh model train \
  --type LGBM \
  --name cmb_model \
  --code sh600036 \
  --start 2020-01-01 \
  --end 2023-12-31
```

#### 支持的模型类型
- `LGBM`: LightGBM（推荐，速度快）
- `MLP`: 多层感知机
- `LSTM`: 长短期记忆网络
- `GRU`: 门控循环单元
- `TRANSFORMER`: Transformer模型

### 4.2 自定义超参数

#### 方式1: 命令行参数
```bash
./run_cli.sh model train \
  --type LGBM \
  --name tuned_model \
  --code sh600036 \
  --start 2020-01-01 \
  --end 2023-12-31 \
  --param n_estimators=200 \
  --param learning_rate=0.05 \
  --param max_depth=7 \
  --param num_leaves=64
```

#### 方式2: 配置文件
创建 `hyperparams.yaml`:
```yaml
n_estimators: 200
learning_rate: 0.05
max_depth: 7
num_leaves: 64
min_child_samples: 20
subsample: 0.8
colsample_bytree: 0.8
```

使用配置文件训练:
```bash
./run_cli.sh model train \
  --type LGBM \
  --name config_model \
  --code sh600036 \
  --start 2020-01-01 \
  --end 2023-12-31 \
  --hyperparameters hyperparams.yaml
```

### 4.3 批量训练

#### 训练多只股票
```bash
# 准备股票列表 stocks.txt
sh600036
sh600519
sh600000

# 批量训练
./run_cli.sh model batch-train \
  --type LGBM \
  --stocks-file stocks.txt \
  --start 2020-01-01 \
  --end 2023-12-31 \
  --name-prefix batch_
```

#### 训练指数成分股
```bash
./run_cli.sh model batch-train \
  --type LGBM \
  --index hs300 \
  --start 2020-01-01 \
  --end 2023-12-31 \
  --name-prefix hs300_
```

### 4.4 训练监控

#### 查看训练进度
```bash
# 查看所有模型
./run_cli.sh model list

# 查看训练中的模型
./run_cli.sh model list --status TRAINING

# 查看已完成的模型
./run_cli.sh model list --status TRAINED
```

#### 输出示例
```
┌──────────────────────┬─────────────┬────────┬─────────────┬────────┬──────┐
│ 模型ID               │ 名称        │ 类型   │ 训练日期    │ 状态   │ R²   │
├──────────────────────┼─────────────┼────────┼─────────────┼────────┼──────┤
│ model-abc123         │ cmb_model   │ LGBM   │ 2024-01-15  │ TRAINED│ 0.68 │
│ model-def456         │ tuned_model │ LGBM   │ 2024-01-15  │ TRAINED│ 0.72 │
└──────────────────────┴─────────────┴────────┴─────────────┴────────┴──────┘
```

---

## 5. 预测生成

### 5.1 单只股票预测

```bash
./run_cli.sh predict \
  --model-id model-abc123 \
  --code sh600036 \
  --start 2024-01-01 \
  --end 2024-01-31 \
  --output predictions/sh600036_pred.pkl
```

### 5.2 批量预测

```bash
# 使用模型预测多只股票
./run_cli.sh predict-batch \
  --model-id model-abc123 \
  --stocks-file stocks.txt \
  --start 2024-01-01 \
  --end 2024-01-31 \
  --output predictions/batch_pred.pkl
```

### 5.3 Python API 预测

```python
from adapters.qlib import QlibModelTrainerAdapter
from domain.repositories import SQLiteModelRepository
import pandas as pd

# 初始化
repo = SQLiteModelRepository()
adapter = QlibModelTrainerAdapter()

# 加载模型
model = repo.find_by_id("model-abc123")

# 准备预测数据
input_data = pd.read_csv("prediction_data.csv")

# 批量预测
batch = await adapter.predict_batch(
    model=model,
    input_data=input_data,
    prediction_date=datetime(2024, 1, 15)
)

# 查看结果
print(f"预测数量: {batch.size()}")
print(f"平均置信度: {batch.average_confidence()}")

# 导出为DataFrame
df = batch.to_dataframe()
df.to_csv("predictions.csv", index=False)
```

---

## 6. 回测评估

### 6.1 单股票回测

```bash
./run_cli.sh backtest run \
  --pred-file predictions/sh600036_pred.pkl \
  --code sh600036 \
  --start 2024-01-01 \
  --end 2024-01-31 \
  --initial-cash 100000 \
  --output backtest_results.json
```

### 6.2 组合回测（Portfolio）

#### Top-K选股策略
```bash
./run_cli.sh backtest portfolio \
  --pred-file predictions/batch_pred.pkl \
  --top-k 10 \
  --rebalance WEEK \
  --initial-cash 1000000 \
  --output portfolio_results.json
```

**参数说明**:
- `--top-k 10`: 每次选择预测分数最高的10只股票
- `--rebalance WEEK`: 每周调仓一次（可选: DAY, WEEK, MONTH）
- `--initial-cash`: 初始资金

### 6.3 Python API 回测

```python
from adapters.hikyuu import CustomSG_QlibFactor, DynamicRebalanceSG
from adapters.qlib import QlibPortfolioAdapter
from hikyuu import *

# 初始化Hikyuu
load_hikyuu()

# 创建信号生成器
sg = CustomSG_QlibFactor(
    pred_pkl_path="predictions/batch_pred.pkl",
    buy_threshold=0.02,
    sell_threshold=-0.02,
    top_k=10
)

# 创建Portfolio适配器
portfolio_adapter = QlibPortfolioAdapter(
    pred_pkl_path="predictions/batch_pred.pkl",
    top_k=10,
    rebalance_period="WEEK"
)

# 创建动态调仓信号
rebalance_sg = DynamicRebalanceSG(portfolio_adapter)

# 配置交易系统
tm = crtTM(init_cash=1000000)
mm = MM_FixedCount(100)

# 运行回测
sys = SYS_Simple(tm=tm, sg=rebalance_sg, mm=mm)
sys.run(sm['sh600036'], Query(-365))

# 查看结果
print(f"最终资产: {tm.currentCash:.2f}")
print(f"总收益率: {(tm.currentCash / 1000000 - 1) * 100:.2f}%")
```

### 6.4 回测结果分析

#### 查看性能指标
```bash
./run_cli.sh backtest analyze \
  --result-file portfolio_results.json \
  --output-report report.html
```

**主要指标**:
- 总收益率
- 年化收益率
- 夏普比率
- 最大回撤
- 胜率
- 盈亏比
- 交易次数

---

## 7. 实战案例

### 案例1: 单股票量化策略

**目标**: 对招商银行(sh600036)建立预测模型并回测

#### Step 1: 数据准备
```bash
# 查看数据范围
./run_cli.sh data list --source hikyuu | grep sh600036
```

#### Step 2: 训练模型
```bash
./run_cli.sh model train \
  --type LGBM \
  --name cmb_lgbm \
  --code sh600036 \
  --start 2020-01-01 \
  --end 2023-06-30 \
  --param n_estimators=150 \
  --param learning_rate=0.05
```

#### Step 3: 生成预测
```bash
./run_cli.sh predict \
  --model-id <从上一步获取> \
  --code sh600036 \
  --start 2023-07-01 \
  --end 2023-12-31 \
  --output pred_cmb.pkl
```

#### Step 4: 回测评估
```bash
./run_cli.sh backtest run \
  --pred-file pred_cmb.pkl \
  --code sh600036 \
  --start 2023-07-01 \
  --end 2023-12-31 \
  --initial-cash 100000
```

#### Step 5: 分析结果
```bash
./run_cli.sh backtest analyze \
  --result-file backtest_results.json
```

---

### 案例2: 沪深300 Top-10 轮动策略

**目标**: 从沪深300成分股中每周选择Top-10进行轮动

#### Step 1: 批量训练
```bash
./run_cli.sh model batch-train \
  --type LGBM \
  --index hs300 \
  --start 2020-01-01 \
  --end 2023-06-30 \
  --name-prefix hs300_
```

#### Step 2: 批量预测
```bash
./run_cli.sh predict-batch \
  --index hs300 \
  --start 2023-07-01 \
  --end 2023-12-31 \
  --output pred_hs300.pkl
```

#### Step 3: Portfolio回测
```bash
./run_cli.sh backtest portfolio \
  --pred-file pred_hs300.pkl \
  --top-k 10 \
  --rebalance WEEK \
  --initial-cash 1000000 \
  --commission-rate 0.0003
```

#### Step 4: 对比基准
```bash
./run_cli.sh backtest compare \
  --strategy-result portfolio_results.json \
  --benchmark hs300 \
  --output comparison_report.html
```

---

### 案例3: 多模型集成策略

**目标**: 使用多个模型投票提高预测准确性

```python
# train_ensemble.py
from adapters.qlib import QlibModelTrainerAdapter
from domain.value_objects import StockCode, DateRange
import pandas as pd

async def train_ensemble():
    adapter = QlibModelTrainerAdapter()

    # 训练多个模型
    models = []
    for model_type in ['LGBM', 'MLP', 'LSTM']:
        model = await adapter.train(
            model_type=model_type,
            stock_code=StockCode("sh600036"),
            date_range=DateRange(date(2020, 1, 1), date(2023, 6, 30))
        )
        models.append(model)

    # 集成预测
    predictions = []
    for model in models:
        batch = await adapter.predict_batch(
            model=model,
            input_data=test_data
        )
        predictions.append(batch.to_dataframe())

    # 投票或加权平均
    ensemble_pred = pd.concat(predictions).groupby(['stock_code', 'timestamp']).mean()

    return ensemble_pred

# 运行
import asyncio
result = asyncio.run(train_ensemble())
```

---

## 8. 进阶技巧

### 8.1 超参数优化

使用网格搜索找到最佳超参数：

```python
# hyperparameter_tuning.py
from itertools import product
import pandas as pd

# 定义搜索空间
param_grid = {
    'n_estimators': [100, 150, 200],
    'learning_rate': [0.01, 0.05, 0.1],
    'max_depth': [5, 7, 9],
    'num_leaves': [31, 63, 127]
}

best_score = -float('inf')
best_params = None

# 网格搜索
for params in product(*param_grid.values()):
    param_dict = dict(zip(param_grid.keys(), params))

    # 训练模型
    model = await adapter.train(
        model_type='LGBM',
        stock_code=StockCode("sh600036"),
        date_range=date_range,
        hyperparameters=param_dict
    )

    # 评估
    if model.metrics['r2_score'] > best_score:
        best_score = model.metrics['r2_score']
        best_params = param_dict

print(f"最佳参数: {best_params}")
print(f"最佳R²: {best_score}")
```

### 8.2 特征工程

自定义技术指标特征：

```python
# custom_features.py
import pandas as pd
import ta  # 技术分析库

def add_custom_features(df: pd.DataFrame) -> pd.DataFrame:
    """添加自定义技术指标"""

    # 趋势指标
    df['macd'] = ta.trend.macd(df['close'])
    df['macd_signal'] = ta.trend.macd_signal(df['close'])
    df['adx'] = ta.trend.adx(df['high'], df['low'], df['close'])

    # 动量指标
    df['rsi'] = ta.momentum.rsi(df['close'], window=14)
    df['stoch'] = ta.momentum.stoch(df['high'], df['low'], df['close'])

    # 波动性指标
    df['bbands_upper'] = ta.volatility.bollinger_hband(df['close'])
    df['bbands_lower'] = ta.volatility.bollinger_lband(df['close'])
    df['atr'] = ta.volatility.average_true_range(df['high'], df['low'], df['close'])

    # 成交量指标
    df['obv'] = ta.volume.on_balance_volume(df['close'], df['volume'])
    df['vwap'] = (df['volume'] * df['close']).cumsum() / df['volume'].cumsum()

    return df

# 使用自定义特征训练
from utils.data_conversion import convert_kline_to_training_data

kline_data = adapter.load_stock_data(...)
df = convert_kline_to_training_data(kline_data, add_features=False)
df = add_custom_features(df)  # 添加自定义特征
```

### 8.3 风险管理

实现止损止盈策略：

```python
# risk_management.py
class RiskManager:
    def __init__(
        self,
        stop_loss_pct: float = 0.05,  # 5%止损
        take_profit_pct: float = 0.15,  # 15%止盈
        max_position_pct: float = 0.2   # 单只股票最大仓位20%
    ):
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.max_position_pct = max_position_pct

    def should_close_position(
        self,
        entry_price: float,
        current_price: float
    ) -> tuple[bool, str]:
        """判断是否需要平仓"""
        return_pct = (current_price - entry_price) / entry_price

        # 止损
        if return_pct <= -self.stop_loss_pct:
            return True, "STOP_LOSS"

        # 止盈
        if return_pct >= self.take_profit_pct:
            return True, "TAKE_PROFIT"

        return False, "HOLD"

    def calculate_position_size(
        self,
        portfolio_value: float,
        stock_price: float
    ) -> int:
        """计算买入数量"""
        max_investment = portfolio_value * self.max_position_pct
        shares = int(max_investment / stock_price / 100) * 100  # 买入整手
        return shares
```

### 8.4 多周期分析

结合不同时间周期的信号：

```python
# multi_timeframe.py
class MultiTimeframeStrategy:
    def __init__(self):
        self.daily_sg = CustomSG_QlibFactor(
            pred_pkl_path="pred_daily.pkl",
            top_k=10
        )
        self.weekly_sg = CustomSG_QlibFactor(
            pred_pkl_path="pred_weekly.pkl",
            top_k=20
        )

    def get_combined_signal(self, stock_code, date):
        """综合日线和周线信号"""
        daily_signal = self.daily_sg.get_signal_for_stock(stock_code, date)
        weekly_signal = self.weekly_sg.get_signal_for_stock(stock_code, date)

        # 两个周期都是买入信号才买入
        if daily_signal.signal_type == SignalType.BUY and \
           weekly_signal.signal_type == SignalType.BUY:
            return SignalType.BUY

        # 任一周期卖出信号就卖出
        if daily_signal.signal_type == SignalType.SELL or \
           weekly_signal.signal_type == SignalType.SELL:
            return SignalType.SELL

        return SignalType.HOLD
```

---

## 9. 常见问题

### Q1: 训练时显示 "Hikyuu library is required"

**原因**: 未安装 Hikyuu 库

**解决**:
```bash
pip install hikyuu
# 或
conda install -c conda-forge hikyuu
```

### Q2: 数据加载失败 "Stock not found"

**原因**: 股票代码格式错误或Hikyuu数据目录未配置

**解决**:
```bash
# 检查股票代码格式（小写，带市场前缀）
# 正确: sh600036
# 错误: 600036, SH600036

# 配置数据目录
./run_cli.sh config set HIKYUU_DATA_PATH /path/to/hikyuu/data
```

### Q3: 模型训练时显示 "NaN in training data"

**原因**: 数据不足以计算某些技术指标（如MA60需要至少60个数据点）

**解决**:
```bash
# 增加训练数据时间范围
./run_cli.sh model train \
  --start 2019-01-01 \  # 往前推一年
  --end 2023-12-31 \
  ...
```

### Q4: 预测结果置信度都是 None

**原因**: LightGBM 不直接输出置信度

**解决**:
```python
# 使用支持概率输出的模型
model_type = 'MLP'  # 或 'LSTM', 'GRU'
```

### Q5: Portfolio回测时提示 "No stocks in Top-K"

**原因**: 预测文件与回测股票池不匹配

**解决**:
```bash
# 确保预测文件包含回测的股票
./run_cli.sh predict-batch \
  --stocks-file same_stocks.txt \  # 使用相同的股票列表
  ...
```

### Q6: 回测收益率与预期不符

**可能原因**:
1. 未考虑交易成本
2. 未考虑涨跌停限制
3. 数据前视偏差

**检查清单**:
```bash
# 添加交易成本
--commission-rate 0.0003 \  # 千分之三佣金
--slippage-rate 0.001 \     # 千分之一滑点

# 检查预测数据是否有未来函数
# 确保预测日期 <= 训练结束日期 + 1天
```

### Q7: 模型过拟合怎么办？

**解决方案**:
```bash
# 1. 增加训练数据
--start 2018-01-01  # 更长的时间范围

# 2. 调整超参数（减少复杂度）
--param n_estimators=100 \      # 减少树数量
--param max_depth=5 \            # 降低树深度
--param min_child_samples=50 \   # 增加叶子节点最小样本数

# 3. 使用正则化
--param reg_alpha=0.1 \   # L1正则化
--param reg_lambda=0.1    # L2正则化

# 4. 交叉验证
./run_cli.sh model cross-validate \
  --folds 5 \
  --type LGBM \
  ...
```

---

## 10. API参考

### 10.1 命令行接口

#### data 命令组
```bash
# 列出数据
./run_cli.sh data list [--source hikyuu|files] [--market SH|SZ|ALL] [--format table|json|csv]

# 加载数据
./run_cli.sh data load --code CODE --start DATE --end DATE [--output FILE]

# 加载指数成分股
./run_cli.sh data load-index --index INDEX --start DATE --end DATE [--output-dir DIR]
```

#### model 命令组
```bash
# 训练模型
./run_cli.sh model train --type TYPE --name NAME --code CODE --start DATE --end DATE \
  [--param KEY=VALUE]... [--hyperparameters FILE]

# 批量训练
./run_cli.sh model batch-train --type TYPE --index INDEX --start DATE --end DATE \
  [--name-prefix PREFIX]

# 列出模型
./run_cli.sh model list [--status STATUS] [--format table|json]

# 删除模型
./run_cli.sh model delete MODEL_ID [--force]

# 交叉验证
./run_cli.sh model cross-validate --type TYPE --code CODE --folds N --start DATE --end DATE
```

#### predict 命令组
```bash
# 单只股票预测
./run_cli.sh predict --model-id ID --code CODE --start DATE --end DATE [--output FILE]

# 批量预测
./run_cli.sh predict-batch --model-id ID --stocks-file FILE --start DATE --end DATE \
  [--output FILE]

# 指数成分股预测
./run_cli.sh predict-batch --model-id ID --index INDEX --start DATE --end DATE \
  [--output FILE]
```

#### backtest 命令组
```bash
# 单股票回测
./run_cli.sh backtest run --pred-file FILE --code CODE --start DATE --end DATE \
  --initial-cash AMOUNT [--commission-rate RATE] [--output FILE]

# Portfolio回测
./run_cli.sh backtest portfolio --pred-file FILE --top-k K --rebalance PERIOD \
  --initial-cash AMOUNT [--output FILE]

# 分析结果
./run_cli.sh backtest analyze --result-file FILE [--output-report FILE]

# 对比基准
./run_cli.sh backtest compare --strategy-result FILE --benchmark INDEX \
  [--output FILE]
```

#### config 命令组
```bash
# 显示配置
./run_cli.sh config show

# 设置配置
./run_cli.sh config set KEY VALUE [--persist yaml|env]

# 获取配置
./run_cli.sh config get KEY

# 重置配置
./run_cli.sh config reset [--confirm]
```

### 10.2 Python API

#### Domain层
```python
from domain.entities import Model, Prediction, TradingSignal
from domain.value_objects import StockCode, DateRange, Price
from domain.ports import IStockDataProvider, IModelTrainer, ISignalProvider
```

#### Use Cases层
```python
from use_cases.models import TrainModelUseCase, GeneratePredictionsUseCase
from use_cases.strategies import GenerateTopKSignalsUseCase, RunPortfolioBacktestUseCase
```

#### Adapters层
```python
# Hikyuu适配器
from adapters.hikyuu import (
    HikyuuDataAdapter,
    CustomSG_QlibFactor,
    DynamicRebalanceSG,
    HikyuuBacktestAdapter
)

# Qlib适配器
from adapters.qlib import (
    QlibModelTrainerAdapter,
    QlibPortfolioAdapter
)

# 仓储
from adapters.repositories import (
    SQLiteModelRepository,
    SQLiteConfigRepository
)
```

### 10.3 配置项参考

| 配置键 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `HIKYUU_DATA_PATH` | str | `~/.hikyuu` | Hikyuu数据目录 |
| `QLIB_DATA_PATH` | str | `~/.qlib/qlib_data/cn_data` | Qlib数据目录 |
| `INITIAL_CAPITAL` | float | `1000000.0` | 初始资金 |
| `COMMISSION_RATE` | float | `0.0003` | 交易佣金率 |
| `SLIPPAGE_RATE` | float | `0.001` | 滑点率 |
| `LOG_LEVEL` | str | `INFO` | 日志级别 |
| `N_JOBS` | int | `-1` | 并行核心数 |
| `RANDOM_SEED` | int | `42` | 随机种子 |
| `MODEL_SAVE_PATH` | str | `./models` | 模型保存路径 |
| `PREDICTION_SAVE_PATH` | str | `./predictions` | 预测保存路径 |
| `DATABASE_PATH` | str | `./data/hikyuu_qlib.db` | SQLite数据库路径 |

---

## 📚 扩展阅读

### 官方文档
- [产品需求文档](../prd.md)
- [系统设计文档](../design.md)
- [CLI用户指南](CLI_USER_GUIDE.md)
- [模型训练指南](MODEL_TRAINING_DATA_LOADING_GUIDE.md)

### 技术文档
- [Hikyuu Python API](../hikyuu-manual/hikyuu-python-api-reference.md)
- [Hikyuu回测集成](../integration/HIKYUU_BACKTEST_INTEGRATION.md)
- [信号转换方案](../integration/SIGNAL_CONVERSION_SOLUTION.md)

### 示例代码
- [examples/signal_conversion/](../../examples/signal_conversion/)
- [examples/predict_batch_quickstart.py](../../examples/predict_batch_quickstart.py)

---

## 🤝 获取帮助

- **GitHub Issues**: https://github.com/luannanxian/hikyuu_qlib/issues
- **文档索引**: [docs/README.md](../README.md)
- **快速入门**: [QUICK_START.md](../../QUICK_START.md)

---

**版本**: v1.0
**最后更新**: 2025-01-16
**维护者**: Hikyuu-Qlib Team

🤖 Generated with [Claude Code](https://claude.com/claude-code)
