# Hikyuu × Qlib 完整工作流指南

## 架构概述

```
Hikyuu 数据 → QlibModelTrainerAdapter (LGBM训练) → predict_batch → Hikyuu 回测
```

### 关键组件

1. **Hikyuu数据适配器** (`HikyuuDataAdapter`)
   - 从 Hikyuu 获取 K线数据
   - 转换为 Domain KLineData 实体

2. **Qlib训练适配器** (`QlibModelTrainerAdapter`)
   - 训练 LGBM/XGBoost 等模型
   - 输入: pandas DataFrame (stock_code, features, label_return)
   - 输出: 训练好的 Model 实体

3. **Hikyuu回测适配器** (`HikyuuBacktestAdapter`)
   - 使用 Hikyuu 回测引擎
   - 输入: SignalBatch 交易信号
   - 输出: BacktestResult 回测结果

## 完整工作流

### 方式1: 一键演示 ⭐ 推荐

```bash
# 运行完整工作流演示
./run_backtest.sh workflow
```

**功能**:
- ✅ 从 Hikyuu 获取5只股票的历史数据
- ✅ 计算技术指标特征 (5/10/20日收益率, 波动率, 相对成交量)
- ✅ 训练 LGBM 模型预测未来5日收益
- ✅ 生成交易信号 (Top-10 做多)
- ✅ Hikyuu 回测验证策略

**输出示例**:
```
======================================================================
Hikyuu → Qlib 训练 → Hikyuu 回测 完整工作流
======================================================================

【步骤1】从 Hikyuu 准备训练数据
  ✅ sh600000: 450 样本
  ✅ sh600016: 450 样本
  ...
✅ 总样本数: 2250

【步骤2】训练 LGBM 模型
✅ 模型训练完成
   训练 R²: 0.8524
   测试 R²: 0.6723

【步骤3】生成预测信号
✅ 预测完成
   批次大小: 5
   平均置信度: 75.3%

【步骤4】转换为交易信号
✅ 生成 10 个交易信号

【步骤5】使用 Hikyuu 回测引擎回测
======================================================================
📊 回测结果
======================================================================
总收益率: 5.23%
年化收益: 45.67%
最大回撤: -3.21%
夏普比率: 1.85
交易次数: 20

✅ 完整工作流执行成功!
```

### 方式2: 分步执行

#### 步骤1: 准备训练数据

```python
import pandas as pd
import numpy as np
from hikyuu import *

def prepare_training_data(stock_list):
    """从 Hikyuu 准备训练数据"""
    sm = StockManager.instance()
    data = []

    for stock_code in stock_list:
        stock = sm.getStock(stock_code.upper())
        kdata = stock.getKData(Query(-500))

        # 计算特征
        close_prices = np.array([k.closePrice for k in kdata])

        for i in range(50, len(kdata)):
            # 特征工程
            ret_5d = (close_prices[i] - close_prices[i-5]) / close_prices[i-5]
            # ... 更多特征

            # 标签: 未来收益
            if i + 5 < len(kdata):
                label = (close_prices[i+5] - close_prices[i]) / close_prices[i]

            data.append({
                'stock_code': stock_code,
                'feature_ret_5d': ret_5d,
                # ... 更多特征
                'label_return': label
            })

    return pd.DataFrame(data)
```

#### 步骤2: 训练模型

```python
from adapters.qlib.qlib_model_trainer_adapter import QlibModelTrainerAdapter
from domain.entities.model import Model, ModelType

# 准备数据
training_df = prepare_training_data(['sh600000', 'sh600016'])

# 创建模型
adapter = QlibModelTrainerAdapter()
model = Model(
    model_type=ModelType.LGBM,
    hyperparameters={"learning_rate": 0.05}
)

# 训练
trained_model = await adapter.train(model, training_df)
print(f"R²: {trained_model.metrics['test_r2']:.4f}")
```

#### 步骤3: 生成预测

```python
# 准备预测数据 (最新特征)
prediction_df = prepare_prediction_data(stock_list)

# 生成预测
predictions = await adapter.predict_batch(
    model=trained_model,
    input_data=prediction_df
)

# 查看结果
print(predictions.to_dataframe())
```

#### 步骤4: 转换为交易信号

```python
from domain.entities.trading_signal import SignalBatch, TradingSignal, SignalType
from domain.value_objects.stock_code import StockCode

signal_batch = SignalBatch(strategy_name="LGBM-Strategy", batch_date=datetime.now())

# Top-N 选股
df = predictions.to_dataframe().sort_values('predicted_value', ascending=False)

for _, row in df.head(10).iterrows():
    signal = TradingSignal(
        stock_code=StockCode(row['stock_code']),
        signal_date=datetime.now(),
        signal_type=SignalType.BUY
    )
    signal_batch.add_signal(signal)
```

#### 步骤5: Hikyuu 回测

```python
from adapters.hikyuu.hikyuu_backtest_adapter import HikyuuBacktestAdapter
from domain.value_objects.configuration import BacktestConfig
from domain.value_objects.date_range import DateRange

adapter = HikyuuBacktestAdapter()

config = BacktestConfig(
    initial_capital=Decimal("1000000"),
    commission_rate=Decimal("0.0003")
)

result = await adapter.run_backtest(
    signals=signal_batch,
    config=config,
    date_range=DateRange(date(2024,1,1), date(2024,12,31))
)

print(f"收益率: {result.total_return:.2%}")
```

## 数据格式要求

### 训练数据 DataFrame

```python
{
    'stock_code': ['sh600000', 'sh600016', ...],  # 股票代码
    'date': [date(2024,1,1), ...],                 # 可选,日期
    'feature_ret_5d': [0.02, -0.01, ...],          # 特征1
    'feature_ret_10d': [0.05, -0.02, ...],         # 特征2
    # ... 更多特征列
    'label_return': [0.03, -0.01, ...]             # 标签(未来收益)
}
```

**必需列**:
- `stock_code`: 股票代码字符串
- `feature_*`: 任意数量的特征列
- `label_return`: 回归标签(连续值)

**可选列**:
- `date`: 日期,用于时间序列分割

### 预测数据 DataFrame

```python
{
    'stock_code': ['sh600000', 'sh600016'],
    'date': [date(2024,11,19), date(2024,11,19)],  # 可选
    'feature_ret_5d': [0.01, -0.005],
    'feature_ret_10d': [0.02, -0.01],
    # ... 与训练数据相同的特征列
}
```

**必需列**:
- `stock_code`: 股票代码
- 所有训练时使用的特征列 (完全相同)

**注意**: 不需要 `label_return` 列

## 特征工程建议

### 常用技术指标

```python
# 价格动量特征
ret_5d = (close[i] - close[i-5]) / close[i-5]
ret_10d = (close[i] - close[i-10]) / close[i-10]
ret_20d = (close[i] - close[i-20]) / close[i-20]

# 波动率特征
volatility = np.std(close[i-20:i])
high_low_range = (high[i] - low[i]) / close[i]

# 成交量特征
rel_volume = volume[i] / np.mean(volume[i-20:i])
volume_price = volume[i] * close[i]

# 技术指标
ma_5 = np.mean(close[i-5:i])
ma_ratio = close[i] / ma_5
```

### 标签设计

```python
# 回归标签: 未来N日收益率
label_return = (close[i+N] - close[i]) / close[i]

# 分类标签: 未来涨跌方向
label_direction = 1 if label_return > 0 else 0

# 多分类标签: 涨幅区间
if label_return > 0.05:
    label_multiclass = 2  # 大涨
elif label_return > 0:
    label_multiclass = 1  # 小涨
else:
    label_multiclass = 0  # 下跌
```

## 性能优化

### 向量化操作

```python
# ✅ 推荐: 使用 SignalBatch.to_dataframe()
df = signal_batch.to_dataframe()
buy_signals = df[df['signal_type'] == 'BUY']

# ❌ 避免: 循环过滤
buy_signals = [s for s in signals if s.signal_type == SignalType.BUY]
```

### 股票对象缓存

`HikyuuBacktestAdapter` 自动缓存股票对象,避免重复查询:

```python
# 自动缓存,第二次访问更快
stock1 = adapter._get_hikyuu_stock(StockCode('sh600000'))
stock2 = adapter._get_hikyuu_stock(StockCode('sh600000'))  # 从缓存读取
```

## 常见问题

### Q: 训练数据量多大合适?

**A**: 建议:
- 最小样本: 每只股票 200+ 天数据
- 推荐样本: 500-1000 天数据
- 股票数量: 10-50 只用于快速实验, 100-300 只用于生产

### Q: 特征数量多少合适?

**A**:
- 初始尝试: 5-10 个技术指标特征
- 生产环境: 20-50 个特征
- 避免过拟合: 特征数 < 样本数 / 10

### Q: 模型超参数如何调整?

**A**: 关键参数:
```python
hyperparameters={
    "learning_rate": 0.01-0.1,    # 学习率,影响收敛速度
    "num_leaves": 15-63,           # 叶子数,影响模型复杂度
    "max_depth": 3-8,              # 深度,防止过拟合
    "min_data_in_leaf": 20-50,     # 叶子最小样本数
}
```

### Q: 如何评估模型质量?

**A**: 关键指标:
- **R² (决定系数)**: >0.6 较好, >0.8 优秀
- **RMSE (均方根误差)**: 越小越好,与标签尺度相关
- **IC (信息系数)**: Qlib 专用,衡量预测与实际相关性

### Q: 回测结果不理想怎么办?

**A**: 排查步骤:
1. 检查特征是否有未来函数(数据泄露)
2. 增加特征工程(更多技术指标)
3. 调整超参数(网格搜索)
4. 增加训练样本量
5. 检查信号选股逻辑(Top-N 数量, 阈值)

## 下一步

- 📖 查看 [examples/hikyuu_train_backtest_workflow.py](../examples/hikyuu_train_backtest_workflow.py) 完整代码
- 🔧 调整特征工程,提升模型效果
- 📊 尝试不同的选股策略 (Top-N, 阈值过滤, 多空组合)
- ⚡ 使用 GPU 加速训练大规模模型
- 🚀 部署到生产环境,实盘验证

---

**版本**: v0.1.1
**更新日期**: 2025-11-19
