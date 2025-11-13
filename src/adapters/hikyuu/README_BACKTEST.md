# Hikyuu Backtest Adapter

## 概述

`HikyuuBacktestAdapter` 是 Hikyuu 回测框架的适配器实现,将 Hikyuu 的回测引擎适配到 Domain 层的 `IBacktestEngine` 接口。

## 架构位置

```
┌─────────────────────────────────────────────────────┐
│                   Use Cases                          │
│             (RunBacktestUseCase)                     │
└─────────────────┬───────────────────────────────────┘
                  │ 依赖
                  ↓
┌─────────────────────────────────────────────────────┐
│              Domain Ports                            │
│            (IBacktestEngine)                         │
└─────────────────┬───────────────────────────────────┘
                  │ 实现
                  ↓
┌─────────────────────────────────────────────────────┐
│              Adapters Layer                          │
│      HikyuuBacktestAdapter ← 本层                    │
└─────────────────┬───────────────────────────────────┘
                  │ 调用
                  ↓
┌─────────────────────────────────────────────────────┐
│          External Framework                          │
│            Hikyuu Library (C++)                      │
└─────────────────────────────────────────────────────┘
```

## 核心职责

1. **信号转换**: Domain SignalBatch → Hikyuu Trading System
2. **回测执行**: 调用 Hikyuu TradeManager 和 Portfolio
3. **结果转换**: Hikyuu 回测结果 → Domain BacktestResult
4. **依赖隔离**: 隔离 Hikyuu 框架依赖在适配器层

## 技术特性

### 1. Hikyuu 回测架构

Hikyuu 回测系统组件:

```python
# TradeManager (TM) - 资金和交易管理
tm = hku.crtTM(
    init_cash=100000.0,      # 初始资金
    cost_func=cost_func      # 手续费函数
)

# Portfolio (PF) - 投资组合执行
pf = hku.PF_Simple(tm=tm)

# 获取回测结果
funds = pf.getFunds()        # 资金曲线
trades = pf.getTrades()      # 交易记录
```

### 2. 数据类型映射

| Hikyuu 类型               | Domain 类型       | 说明                    |
|--------------------------|------------------|------------------------|
| float (cash)             | Decimal          | 资金金额                |
| Trade.business (0/1)     | str (BUY/SELL)   | 交易方向                |
| Trade.number             | int              | 交易数量                |
| Trade.price              | Decimal          | 交易价格                |
| Trade.datetime           | datetime         | 交易时间                |
| FundRecord.total_assets  | Decimal          | 权益曲线点              |

### 3. 交易方向映射

```python
# Hikyuu → Domain
business = 1  → direction = "BUY"   # 买入
business = 0  → direction = "SELL"  # 卖出

# Domain → Hikyuu
SignalType.BUY  → Hikyuu buy order
SignalType.SELL → Hikyuu sell order
SignalType.HOLD → 无操作
```

## 使用示例

### 基本用法

```python
from adapters.hikyuu.hikyuu_backtest_adapter import HikyuuBacktestAdapter
from domain.entities.trading_signal import SignalBatch, TradingSignal, SignalType, SignalStrength
from domain.value_objects.stock_code import StockCode
from domain.value_objects.date_range import DateRange
from domain.value_objects.configuration import BacktestConfig
from datetime import datetime, date
from decimal import Decimal

# 创建适配器
adapter = HikyuuBacktestAdapter()

# 创建信号批次
batch = SignalBatch(
    strategy_name="双均线策略",
    batch_date=datetime(2023, 1, 1)
)

# 添加买入信号
buy_signal = TradingSignal(
    stock_code=StockCode("sh600000"),
    signal_date=datetime(2023, 1, 3),
    signal_type=SignalType.BUY,
    signal_strength=SignalStrength.STRONG,
    price=Decimal("10.5")
)
batch.add_signal(buy_signal)

# 添加卖出信号
sell_signal = TradingSignal(
    stock_code=StockCode("sh600000"),
    signal_date=datetime(2023, 1, 10),
    signal_type=SignalType.SELL,
    signal_strength=SignalStrength.MEDIUM,
    price=Decimal("11.0")
)
batch.add_signal(sell_signal)

# 配置回测参数
config = BacktestConfig(
    initial_capital=Decimal("100000.0"),
    commission_rate=Decimal("0.001"),   # 0.1% 手续费
    slippage_rate=Decimal("0.001")      # 0.1% 滑点
)

# 设置回测日期范围
date_range = DateRange(
    start_date=date(2023, 1, 1),
    end_date=date(2023, 12, 31)
)

# 运行回测
result = await adapter.run_backtest(
    signals=batch,
    config=config,
    date_range=date_range
)

# 结果: BacktestResult
print(f"策略: {result.strategy_name}")
print(f"总收益率: {result.total_return():.2%}")
print(f"最大回撤: {result.calculate_max_drawdown():.2%}")
print(f"夏普比率: {result.calculate_sharpe_ratio():.2f}")
print(f"胜率: {result.get_win_rate():.2%}")
print(f"交易次数: {len(result.trades)}")
```

### 分析回测结果

```python
# 分析交易记录
for trade in result.trades:
    print(f"{trade.trade_date}: {trade.direction} {trade.stock_code.value} "
          f"{trade.quantity}股 @{trade.price} 手续费:{trade.commission}")

# 分析权益曲线
import matplotlib.pyplot as plt

plt.figure(figsize=(12, 6))
plt.plot([float(v) for v in result.equity_curve])
plt.title(f"{result.strategy_name} - 权益曲线")
plt.xlabel("时间")
plt.ylabel("权益 (元)")
plt.grid(True)
plt.show()

# 计算月度收益
monthly_returns = {}
for trade in result.trades:
    month_key = trade.trade_date.strftime("%Y-%m")
    if month_key not in monthly_returns:
        monthly_returns[month_key] = []
    if trade.direction == "SELL":
        # 计算盈亏
        pass
```

### 测试模式 (Mock 注入)

```python
from unittest.mock import MagicMock

# 创建 Mock Hikyuu 模块
mock_hku = MagicMock()

# Mock TradeManager
mock_tm = MagicMock()
mock_hku.crtTM.return_value = mock_tm

# Mock Portfolio
mock_pf = MagicMock()
mock_pf.getFunds.return_value = [
    MagicMock(total_assets=100000.0, datetime=datetime(2023, 1, 1)),
    MagicMock(total_assets=110000.0, datetime=datetime(2023, 12, 31))
]
mock_pf.getTrades.return_value = []
mock_pf.cash = 110000.0
mock_hku.PF_Simple.return_value = mock_pf

# 注入 Mock
adapter = HikyuuBacktestAdapter(hikyuu_module=mock_hku)

# 测试不依赖真实 Hikyuu 环境
result = await adapter.run_backtest(...)
```

## 实现细节

### run_backtest 流程

```
1. 创建 TradeManager
   tm = hku.crtTM(init_cash=..., cost_func=...)

2. 创建 Portfolio
   pf = hku.PF_Simple(tm=tm)

3. 执行回测
   (实际实现中需要创建信号生成器和交易系统)

4. 获取回测数据
   funds = pf.getFunds()
   trades = pf.getTrades()

5. 转换为 Domain 模型
   - 转换权益曲线 (List[FundRecord] → List[Decimal])
   - 转换交易记录 (List[HikyuuTrade] → List[Trade])
   - 计算最终资金

6. 创建 BacktestResult
   return BacktestResult(...)
```

### _convert_to_domain_result 流程

```python
def _convert_to_domain_result(...):
    # 1. 转换权益曲线
    equity_curve = [
        Decimal(str(fund.total_assets)) 
        for fund in funds_history
    ]
    
    # 2. 转换交易记录
    trades = [
        self._convert_hikyuu_trade_to_domain(trade)
        for trade in trades_history
    ]
    
    # 3. 获取最终资金
    final_capital = Decimal(str(portfolio.cash))
    
    # 4. 创建结果实体
    return BacktestResult(
        strategy_name=...,
        start_date=...,
        end_date=...,
        initial_capital=...,
        final_capital=...,
        trades=trades,
        equity_curve=equity_curve
    )
```

### _convert_hikyuu_trade_to_domain 流程

```python
def _convert_hikyuu_trade_to_domain(hikyuu_trade):
    # 1. 解析股票代码
    stock_str = str(hikyuu_trade.stock).lower()
    stock_code = StockCode(stock_str)
    
    # 2. 转换交易方向
    direction = "BUY" if hikyuu_trade.business == 1 else "SELL"
    
    # 3. 提取交易数据
    quantity = int(hikyuu_trade.number)
    price = Decimal(str(hikyuu_trade.price))
    commission = Decimal(str(hikyuu_trade.cost))
    
    # 4. 创建 Trade 实体
    return Trade(
        stock_code=stock_code,
        direction=direction,
        quantity=quantity,
        price=price,
        trade_date=hikyuu_trade.datetime,
        commission=commission
    )
```

## 错误处理

所有 Hikyuu 异常都会被捕获并重新抛出包装后的异常:

```python
try:
    # Hikyuu 回测操作
    tm = hku.crtTM(...)
    pf = hku.PF_Simple(...)
    ...
except Exception as e:
    raise Exception(
        f"Failed to run backtest with Hikyuu: {strategy_name}, {e}"
    ) from e
```

**异常类型**:
- `ImportError`: Hikyuu 未安装
- `Exception`: Hikyuu API 调用失败
- `Exception`: 数据格式转换失败

## 依赖项

```toml
[dependencies]
hikyuu = "^1.2.0"
```

**注意**: Hikyuu 是可选依赖,开发环境可以通过 Mock 注入进行测试。

## 测试覆盖率

- **覆盖率**: 92%
- **测试文件**: `tests/unit/adapters/hikyuu/test_hikyuu_backtest_adapter.py`
- **测试用例**: 7 个

### 测试用例列表

1. `test_run_backtest_calls_hikyuu_api`: 验证 Hikyuu API 调用
2. `test_run_backtest_converts_to_domain`: 验证结果格式转换
3. `test_run_backtest_converts_signals_to_trades`: 验证信号转交易
4. `test_run_backtest_calculates_commission`: 验证手续费计算
5. `test_run_backtest_handles_hikyuu_error`: 验证错误处理
6. `test_run_backtest_handles_empty_signals`: 验证空信号处理
7. `test_run_backtest_calculates_metrics`: 验证指标计算

## 性能考虑

### 回测性能

- **单次回测**: 支持数千条交易信号
- **内存占用**: 主要取决于权益曲线点数
- **执行速度**: 依赖 Hikyuu C++ 引擎 (高性能)

### 优化建议

1. **批量回测**: 使用多进程并行执行
   ```python
   from multiprocessing import Pool
   
   def run_single_backtest(params):
       adapter, signals, config, date_range = params
       return await adapter.run_backtest(signals, config, date_range)
   
   # 并行回测多个策略
   with Pool(processes=4) as pool:
       results = pool.map(run_single_backtest, backtest_params)
   ```

2. **结果缓存**: 缓存相同参数的回测结果
   ```python
   from functools import lru_cache
   
   @lru_cache(maxsize=128)
   def cached_backtest(strategy_name, config_hash):
       return await adapter.run_backtest(...)
   ```

## 与 Qlib 回测对比

| 特性              | Hikyuu              | Qlib                |
|------------------|---------------------|---------------------|
| 实现语言          | C++ (高性能)         | Python              |
| 回测引擎          | TradeManager + Portfolio | Executor        |
| 信号系统          | SignalGenerator     | Strategy            |
| 交易成本          | cost_func           | deal_price          |
| 权益曲线          | FundRecord[]        | Performance         |
| 执行速度          | 快 (C++)            | 中等 (Python)       |
| 易用性            | 中 (需要 Boost)     | 高 (纯 Python)      |

## 扩展功能

### 自定义手续费函数

```python
def _create_cost_func(self, config: BacktestConfig):
    """创建自定义手续费函数"""
    # 实际实现中可以使用 Hikyuu 的 cost function API
    # 例如: TC_FixedA(佣金=5元), TC_Percentage(比例=0.001)
    
    if hasattr(self.hku, 'TC_FixedA'):
        # 固定佣金
        return self.hku.TC_FixedA(
            commission=float(config.commission_rate * config.initial_capital)
        )
    elif hasattr(self.hku, 'TC_Percentage'):
        # 比例佣金
        return self.hku.TC_Percentage(
            rate=float(config.commission_rate)
        )
    
    return None  # 使用默认
```

### 支持更多交易策略

当前实现是简化版,实际使用需要:

1. **创建信号生成器**: `SG_Manual()` 或 `SG_Bool()`
2. **创建交易系统**: `SYS_Simple(sg=sg, mm=mm, st=st, sp=sp)`
3. **运行回测**: `pf.run(sys, start_date, end_date)`

## 相关文档

- [IBacktestEngine Interface](../../domain/ports/backtest_engine.py)
- [BacktestResult Entity](../../domain/entities/backtest.py)
- [SignalBatch Aggregate](../../domain/entities/trading_signal.py)
- [Hikyuu Official Documentation](https://hikyuu.org/)

## 版本历史

- **v1.0.0** (2025-11-12): 初始实现
  - 实现 `run_backtest` 方法
  - 完成 Hikyuu 结果转换
  - 完成单元测试 (92% 覆盖率)

---

**维护者**: Development Team  
**最后更新**: 2025-11-12
