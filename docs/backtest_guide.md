# Hikyuu 回测指南

本指南介绍如何使用 Hikyuu 对 Qlib 预测结果进行回测。

## 工作流程

整个工作流程分为三个主要步骤:

```
1. 训练模型 → 2. 生成预测 → 3. 回测验证
```

### 步骤 1: 训练模型

使用历史数据(如 2024 年)训练模型:

```bash
# 从项目根目录运行
PYTHONPATH=./src python -m controllers.cli.main model train-index \
  --type LGBM \
  --name hs300_2024_model \
  --index 沪深300 \
  --start 2024-01-01 \
  --end 2024-12-31
```

训练完成后,记录模型 ID (例如: `c18e2c6f-940a-4390-9099-7e2dbe469f37`)

### 步骤 2: 生成预测

使用训练好的模型对未来数据(如 2025 年)生成预测:

```bash
PYTHONPATH=./src python -m controllers.cli.main model predict \
  --model-id c18e2c6f-940a-4390-9099-7e2dbe469f37 \
  --index 沪深300 \
  --start 2025-01-01 \
  --end 2025-12-31 \
  --output outputs/predictions/hs300_2025_pred.pkl
```

**输出文件**:
- `hs300_2025_pred.pkl`: Qlib 格式的预测文件 (MultiIndex DataFrame)
- `hs300_2025_pred_details.pkl`: 模型详细信息(特征重要度等)

### 步骤 3: 运行回测

#### 方式 1: 基础回测

使用简单的回测脚本:

```bash
python examples/backtest_example.py
```

**输出**:
- 控制台显示回测结果摘要
- 资金情况、收益率、交易统计

#### 方式 2: 高级回测(带可视化)

使用包含性能分析和图表的高级脚本:

```bash
python examples/backtest_advanced.py
```

**输出**:
- `outputs/backtest/equity_curve.png`: 资金曲线图
- `outputs/backtest/drawdown_curve.png`: 回撤曲线图
- `outputs/backtest/returns_distribution.png`: 日收益分布图
- `outputs/backtest/backtest_report_*.txt`: 详细回测报告

## 核心组件说明

### CustomSG_QlibFactor 信号指示器

这是连接 Qlib 预测和 Hikyuu 回测的桥梁。

**主要参数**:

```python
sg = CustomSG_QlibFactor(
    pred_pkl_path="./outputs/predictions/hs300_2025_pred.pkl",  # 预测文件路径
    buy_threshold=0.01,    # 买入阈值:预测收益 > 1% 时买入
    sell_threshold=-0.01,  # 卖出阈值:预测收益 < -1% 时卖出
    top_k=30,              # 每日只交易预测最好的 30 只股票
    name="QlibFactor"      # 信号器名称
)
```

**工作原理**:
1. 加载 `pred.pkl` 预测文件
2. 对于每只股票的每个交易日,查找对应的预测分数
3. 根据阈值和 Top-K 规则生成买入/卖出信号
4. Hikyuu 根据信号执行交易

### 交易系统组件

#### 资金管理 (MM - Money Management)

```python
# 固定金额:每只股票投入固定金额
mm = MM_FixedCount(num=50000)  # 每只股票 5 万元

# 固定比例:每只股票投入总资金的百分比
mm = MM_FixedCount(num=0.05 * init_cash)  # 每只股票占总资金 5%
```

#### 止损策略 (ST - Stop Loss)

```python
# 固定百分比止损
st = ST_FixedPercent(p=0.20)  # 亏损 20% 止损

# 不止损
st = ST_Null()
```

#### 止盈策略 (TP - Take Profit)

```python
# 固定百分比止盈
tp = TP_FixedPercent(p=0.30)  # 盈利 30% 止盈

# 不止盈
tp = TP_Null()
```

#### 滑点 (SP - Slippage)

```python
# 固定百分比滑点
sp = SP_FixedPercent(p=0.001)  # 0.1% 滑点

# 固定价格滑点
sp = SP_FixedValue(value=0.01)  # 每股 0.01 元滑点
```

#### 交易成本 (CN - Cost)

```python
# 以开盘价买入,收盘价卖出
cn = CN_OC()

# 以收盘价买入和卖出
cn = CN_CC()
```

## 回测参数调优

### 阈值调整

**买入/卖出阈值**:

```python
# 保守策略:更高的阈值,交易次数少
buy_threshold = 0.02   # 预测收益 > 2%
sell_threshold = -0.02

# 激进策略:更低的阈值,交易次数多
buy_threshold = 0.005  # 预测收益 > 0.5%
sell_threshold = -0.005
```

### Top-K 调整

```python
# 集中投资:只交易最优的少数股票
top_k = 10

# 分散投资:交易更多股票
top_k = 50

# 不限制:所有满足阈值的股票都交易
top_k = None
```

### 资金管理调整

```python
# 保守:每只股票投入少
mm = MM_FixedCount(num=0.02 * init_cash)  # 2%

# 激进:每只股票投入多
mm = MM_FixedCount(num=0.10 * init_cash)  # 10%
```

## 性能指标说明

回测完成后会计算以下指标:

- **总收益率**: (最终资产 - 初始资金) / 初始资金
- **年化收益率**: 折算为年化的收益率
- **最大回撤**: 从最高点到最低点的最大跌幅
- **夏普比率**: (年化收益率 - 无风险利率) / 年化波动率
- **胜率**: 盈利交易次数 / 总交易次数
- **盈亏比**: 平均盈利 / 平均亏损
- **交易次数**: 总买卖次数

## 常见问题

### Q1: 如何查看模型列表?

```bash
PYTHONPATH=./src python -m controllers.cli.main model list
```

### Q2: 预测文件格式要求?

必须是 Qlib 标准格式:
- MultiIndex DataFrame
- 索引: `['stock_code', 'timestamp']`
- 列: `'score'` (必须) + 其他可选列

### Q3: 如何修改回测时间范围?

编辑 `backtest_example.py`:

```python
start_date = Datetime(20250101)  # 修改开始日期
end_date = Datetime(20251231)    # 修改结束日期
```

### Q4: 如何调整初始资金?

```python
init_cash = 1000000  # 100 万
init_cash = 5000000  # 500 万
```

### Q5: 回测失败,提示找不到股票?

确保:
1. Hikyuu 数据库已更新到最新
2. 股票池设置正确(沪深300板块存在)
3. 预测文件中的股票代码格式正确(如 `sh600000`)

### Q6: 如何对比不同策略?

运行多次回测,每次修改参数:

```python
# 策略 1
sg1 = CustomSG_QlibFactor(buy_threshold=0.01, top_k=30)

# 策略 2
sg2 = CustomSG_QlibFactor(buy_threshold=0.02, top_k=10)
```

## 进阶使用

### 自定义信号过滤

在 `CustomSG_QlibFactor` 中可以添加更多过滤逻辑:

```python
def _calculate(self, stock, query):
    # ... 原有逻辑 ...

    # 添加自定义过滤
    for i in range(len(kdata)):
        pred_score = # ... 获取预测分数

        # 示例:只在收盘价 > 5 元时交易
        if kdata[i].close_price < 5.0:
            continue

        # 示例:只在成交量 > 100万时交易
        if kdata[i].volume < 1000000:
            continue

        # 原有的阈值判断
        if pred_score > buy_threshold:
            self._add_buy_signal(k_datetime)
```

### 多模型集成

可以使用多个模型的预测进行投票:

```python
# 加载多个预测文件
sg1 = CustomSG_QlibFactor("model1_pred.pkl")
sg2 = CustomSG_QlibFactor("model2_pred.pkl")

# 使用 OR 或 AND 组合
sg_combined = sg1 | sg2  # OR: 任一模型看好就买
sg_combined = sg1 & sg2  # AND: 两个模型都看好才买
```

### 保存回测结果到数据库

可以将回测结果保存到 SQLite:

```python
import sqlite3
import json

conn = sqlite3.connect('backtest_results.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS backtests (
        id INTEGER PRIMARY KEY,
        timestamp TEXT,
        strategy_name TEXT,
        metrics TEXT
    )
''')

cursor.execute('''
    INSERT INTO backtests (timestamp, strategy_name, metrics)
    VALUES (?, ?, ?)
''', (
    datetime.now().isoformat(),
    "HS300_Qlib_Strategy",
    json.dumps(metrics)
))

conn.commit()
conn.close()
```

## 参考资料

- [Hikyuu 官方文档](https://hikyuu.org)
- [Qlib 官方文档](https://qlib.readthedocs.io)
- [CustomSG_QlibFactor 源码](../src/adapters/hikyuu/custom_sg_qlib_factor.py)
- [回测示例源码](./backtest_example.py)
