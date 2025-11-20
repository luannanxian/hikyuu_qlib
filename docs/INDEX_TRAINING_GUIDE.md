# 指数成分股训练指南

## 功能概述

现在支持使用指数成分股进行批量训练，无需手动指定股票代码。

## 使用方法

### 1. 使用指数全部成分股

```bash
# 沪深300 全部300只股票
./run_backtest.sh workflow --index 沪深300

# 中证500 全部500只股票
./run_backtest.sh workflow --index 中证500

# 上证50 全部50只股票
./run_backtest.sh workflow --index 上证50
```

### 2. 限制训练股票数量（随机采样）

```bash
# 从沪深300中随机采样50只
./run_backtest.sh workflow --index 沪深300 --max-stocks 50

# 从中证500中随机采样100只
./run_backtest.sh workflow --index 中证500 --max-stocks 100

# 从上证50中随机采样20只
./run_backtest.sh workflow --index 上证50 --max-stocks 20
```

### 3. 手动指定股票代码

```bash
# 指定3只股票
./run_backtest.sh workflow --stocks sh600000 sh600016 sh600519

# 指定多只股票
./run_backtest.sh workflow --stocks sh600000 sh600016 sh600036 sh600519 sh600887
```

### 4. 默认模式（示例股票）

```bash
# 使用默认的5只示例股票
./run_backtest.sh workflow
```

## 支持的指数

Hikyuu 系统支持的常见指数包括：

### 主要指数
- **沪深300**: 沪深两市市值最大、流动性最好的300只股票
- **中证500**: 中小盘代表性指数，500只股票
- **上证50**: 上海市场最具代表性的50只龙头股
- **中证100**: 沪深市场市值最大的100只股票
- **深证100**: 深圳市场规模最大、流动性最好的100只股票

### 行业指数
- **中证银行**: 银行业指数
- **中证证券**: 证券业指数
- **中证白酒**: 白酒行业指数
- **中证医药**: 医药行业指数
- **中证消费**: 消费行业指数
- **中证科技**: 科技行业指数

### 其他指数
- **创业板指**: 创业板市场主要指数
- **科创50**: 科创板最具代表性的50只股票

## 参数说明

### --index <指数名称>
- 指定要使用的指数
- 系统会自动获取该指数的全部成分股
- 名称必须与 Hikyuu 数据库中的指数名称完全匹配

### --max-stocks <数量>
- 限制训练的最大股票数量
- 如果指数成分股超过此数量，将随机采样
- 用于控制训练时间和资源消耗

### --stocks <代码1> <代码2> ...
- 手动指定股票代码列表
- 支持沪深市场股票代码格式：`sh600000`, `sz000001`
- 可以指定任意数量的股票

## 使用示例

### 示例1: 训练沪深300策略

```bash
# 使用全部沪深300成分股
./run_backtest.sh workflow --index 沪深300

# 训练完成后进行回测
./run_backtest.sh backtest-workflow
```

**预期结果**:
- 训练样本: ~135,000 个（300只股票 × 450天）
- 训练时间: 约2-5分钟
- 预测文件: `outputs/predictions/workflow_pred.pkl`

### 示例2: 快速测试（采样50只）

```bash
# 从沪深300随机采样50只股票
./run_backtest.sh workflow --index 沪深300 --max-stocks 50

# 查看训练结果
cat outputs/predictions/workflow_pred.pkl
```

**预期结果**:
- 训练样本: ~22,500 个（50只股票 × 450天）
- 训练时间: 约30-60秒
- 更快的迭代速度，适合参数调优

### 示例3: 行业策略训练

```bash
# 训练银行板块策略
./run_backtest.sh workflow --index 中证银行

# 训练医药板块策略
./run_backtest.sh workflow --index 中证医药 --max-stocks 30
```

### 示例4: 自选股训练

```bash
# 使用自己选择的股票
./run_backtest.sh workflow --stocks sh600519 sh600036 sh601318 sh601888 sz000858
```

## 训练规模建议

### 快速测试（开发阶段）
- **股票数量**: 10-30只
- **训练时间**: < 1分钟
- **适用场景**: 调试代码、测试新特征
- **命令**: `--max-stocks 10`

### 中等规模（参数调优）
- **股票数量**: 50-100只
- **训练时间**: 1-3分钟
- **适用场景**: 超参数搜索、特征选择
- **命令**: `--max-stocks 50`

### 大规模训练（生产环境）
- **股票数量**: 100-300只
- **训练时间**: 3-10分钟
- **适用场景**: 最终模型训练、实盘部署
- **命令**: `--index 沪深300`（全部成分股）

### 完整市场（研究用途）
- **股票数量**: 300-500只
- **训练时间**: 10-30分钟
- **适用场景**: 学术研究、全市场策略
- **命令**: `--index 中证500`

## 性能优化建议

### 1. 数据获取优化
- 使用更长的历史周期: `Query(-2000)` 增加训练样本
- 减少技术指标计算复杂度
- 缓存已提取的特征数据

### 2. 训练优化
- 使用更小的 `num_leaves` 参数（15-31）
- 增加正则化: `lambda_l1`, `lambda_l2`
- 使用时间序列交叉验证

### 3. 并行化
- 多进程数据提取（未实现）
- GPU 加速训练（需要 GPU 版本 LightGBM）
- 分布式训练（多机训练）

## 常见问题

### Q1: 提示"无法加载指数板块"

**原因**: 指数名称不正确或 Hikyuu 数据库中不存在该指数

**解决方案**:
1. 检查指数名称拼写（区分中英文）
2. 确认 Hikyuu 数据库已正确配置
3. 使用 `get_block("指数板块", "沪深300")` 验证

### Q2: 训练时间过长

**原因**: 股票数量过多或历史数据过长

**解决方案**:
1. 使用 `--max-stocks` 限制股票数量
2. 减少 `Query(-500)` 中的天数
3. 优化特征计算代码

### Q3: 测试 R² 为负值

**原因**: 模型严重过拟合

**解决方案**:
1. 增加训练数据: `Query(-2000)`
2. 增加正则化参数
3. 减少模型复杂度: `num_leaves=15`
4. 添加更多有效特征

### Q4: 某些股票无法获取数据

**原因**: 股票停牌、退市或数据缺失

**系统行为**: 自动跳过无数据的股票，继续训练其他股票

## 高级用法

### 1. Python 脚本直接调用

```python
import asyncio
from examples.hikyuu_train_backtest_workflow import main

# 模拟命令行参数
import sys
sys.argv = ['script.py', '--index', '沪深300', '--max-stocks', '50']

# 运行工作流
asyncio.run(main())
```

### 2. 自定义指数

```python
from hikyuu import get_block

# 获取自定义板块
block = get_block("行业板块", "计算机")
stocks = [s.market_code.lower() for s in block.get_stock_list()]

# 传递给训练脚本
sys.argv = ['script.py', '--stocks'] + stocks
asyncio.run(main())
```

### 3. 批量训练多个指数

```bash
#!/bin/bash
# 训练多个指数策略

for index in "沪深300" "中证500" "上证50"; do
    echo "训练 $index 策略..."
    ./run_backtest.sh workflow --index "$index" --max-stocks 50
    mv outputs/predictions/workflow_pred.pkl "outputs/predictions/${index}_pred.pkl"
done
```

## 输出文件

训练完成后会生成以下文件：

```
outputs/
└── predictions/
    └── workflow_pred.pkl      # 预测结果文件（MultiIndex DataFrame）
```

**文件格式**:
- **Index**: (timestamp, stock_code) - MultiIndex
- **Columns**:
  - `score`: 预测分数
  - `confidence`: 预测置信度
  - `model_id`: 模型ID
  - `prediction_id`: 预测ID

## 下一步

训练完成后，可以使用预测结果进行回测：

```bash
# 使用训练生成的预测进行回测
./run_backtest.sh backtest-workflow
```

或者参考 [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md) 了解完整工作流。

---

**版本**: v1.0.0
**更新日期**: 2025-11-19
