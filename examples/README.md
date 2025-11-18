# Hikyuu 回测示例

本目录包含使用 Hikyuu 进行回测的示例脚本。

## 文件说明

### 1. `quick_backtest.py` - 快速回测 ⚡

**最简单的方式**,一键运行回测:

```bash
# 使用默认参数
python examples/quick_backtest.py

# 自定义参数
python examples/quick_backtest.py \
  --pred-file outputs/predictions/hs300_2025_pred.pkl \
  --start 20250101 \
  --end 20251231 \
  --cash 1000000 \
  --buy-threshold 0.01 \
  --sell-threshold -0.01 \
  --top-k 30 \
  --pool 沪深300
```

**输出**: 控制台显示简要回测结果

### 2. `backtest_example.py` - 基础回测 📊

**完整示例**,展示所有回测步骤:

```bash
python examples/backtest_example.py
```

**特点**:
- ✅ 详细的代码注释
- ✅ 完整的配置说明
- ✅ 交易明细展示
- ✅ 持仓分析

**输出**:
- 资金情况汇总
- 交易统计
- 最近 10 笔交易
- 当前持仓 Top 10

### 3. `backtest_advanced.py` - 高级回测 📈

**专业级回测**,包含性能分析和可视化:

```bash
python examples/backtest_advanced.py
```

**特点**:
- ✅ 详细性能指标计算
- ✅ 可视化图表生成
- ✅ 回测报告保存
- ✅ 支持自定义分析

**输出文件**:
```
outputs/backtest/
├── equity_curve.png          # 资金曲线图
├── drawdown_curve.png         # 回撤曲线图
├── returns_distribution.png   # 收益分布图
└── backtest_report_*.txt      # 详细回测报告
```

## 快速开始

### 前提条件

1. **完成模型训练**:
   ```bash
   PYTHONPATH=./src python -m controllers.cli.main model train-index \
     --type LGBM --name hs300_model \
     --index 沪深300 --start 2024-01-01 --end 2024-12-31
   ```

2. **生成预测文件**:
   ```bash
   PYTHONPATH=./src python -m controllers.cli.main model predict \
     --model-id <你的模型ID> \
     --index 沪深300 --start 2025-01-01 --end 2025-12-31 \
     --output outputs/predictions/hs300_2025_pred.pkl
   ```

3. **确保 Hikyuu 数据库已更新**

### 运行回测

#### 方法 1: 快速回测(推荐新手)

```bash
python examples/quick_backtest.py
```

#### 方法 2: 基础回测(学习用)

```bash
python examples/backtest_example.py
```

#### 方法 3: 高级回测(专业分析)

```bash
python examples/backtest_advanced.py
```

## 参数说明

### 回测参数

| 参数 | 说明 | 默认值 | 推荐范围 |
|------|------|--------|----------|
| `pred_file` | 预测文件路径 | `hs300_2025_pred.pkl` | - |
| `start_date` | 开始日期 | `20250101` | YYYYMMDD |
| `end_date` | 结束日期 | `20251231` | YYYYMMDD |
| `init_cash` | 初始资金 | `1000000` | 10万-1000万 |
| `buy_threshold` | 买入阈值 | `0.01` | 0.005-0.03 |
| `sell_threshold` | 卖出阈值 | `-0.01` | -0.03--0.005 |
| `top_k` | 每日最大交易股票数 | `30` | 10-50 |
| `stock_pool` | 股票池名称 | `沪深300` | 沪深300/中证500/上证50 |

### 策略类型

#### 保守策略
```python
buy_threshold = 0.02    # 更高阈值
sell_threshold = -0.02
top_k = 10              # 更少股票
init_cash = 1000000     # 适中资金
```

#### 均衡策略(默认)
```python
buy_threshold = 0.01
sell_threshold = -0.01
top_k = 30
init_cash = 1000000
```

#### 激进策略
```python
buy_threshold = 0.005   # 更低阈值
sell_threshold = -0.005
top_k = 50              # 更多股票
init_cash = 5000000     # 更多资金
```

## 结果解读

### 关键指标

- **总收益率**: 整体盈利情况
- **年化收益率**: 折算为年化的收益
- **最大回撤**: 风险控制指标,越小越好
- **夏普比率**: 风险调整后收益,>1 为好,>2 为优秀
- **胜率**: 盈利交易占比,>50% 为好
- **盈亏比**: 平均盈利/平均亏损,>1.5 为好

### 图表说明

1. **资金曲线图**: 显示总资产随时间变化
   - 上升趋势 → 策略有效
   - 波动剧烈 → 风险较高
   - 平稳上升 → 稳定盈利

2. **回撤曲线图**: 显示从高点的跌幅
   - 越接近 0 越好
   - 深度回撤 → 需要调整策略

3. **收益分布图**: 显示日收益率分布
   - 集中在 0 附近 → 正常
   - 正偏分布 → 策略偏向盈利
   - 长尾 → 存在极端收益

## 调优建议

### 如果收益率低

1. **降低阈值**: 增加交易频率
2. **增加 Top-K**: 分散投资
3. **调整止损止盈**: 更宽松的止损

### 如果回撤大

1. **提高阈值**: 减少交易频率
2. **减少 Top-K**: 集中优质股票
3. **设置更严格止损**: 降低单次亏损

### 如果胜率低

1. **提高买入阈值**: 只选最优股票
2. **优化模型**: 重新训练或调整特征
3. **检查数据质量**: 确保预测数据准确

## 常见问题

### Q: 回测结果不理想怎么办?

A:
1. 检查预测质量(模型 R² 分数)
2. 调整买入/卖出阈值
3. 优化 Top-K 参数
4. 考虑重新训练模型

### Q: 如何对比不同策略?

A:
```bash
# 策略 1: 保守
python examples/quick_backtest.py --buy-threshold 0.02 --top-k 10

# 策略 2: 激进
python examples/quick_backtest.py --buy-threshold 0.005 --top-k 50

# 对比结果
```

### Q: 可以用在其他股票池吗?

A: 可以,修改 `--pool` 参数:
```bash
python examples/quick_backtest.py --pool 中证500
python examples/quick_backtest.py --pool 上证50
```

### Q: 如何保存回测结果?

A: 使用 `backtest_advanced.py`,会自动保存到:
- 图表: `outputs/backtest/*.png`
- 报告: `outputs/backtest/backtest_report_*.txt`

## 下一步

1. **优化模型**: 根据回测结果调整模型参数
2. **策略改进**: 尝试不同的交易策略组合
3. **实盘验证**: 在小资金实盘环境测试
4. **持续监控**: 定期回测和调整策略

## 相关文档

- [回测详细指南](../docs/backtest_guide.md)
- [CustomSG_QlibFactor 说明](../src/adapters/hikyuu/custom_sg_qlib_factor.py)
- [Hikyuu 官方文档](https://hikyuu.org)
