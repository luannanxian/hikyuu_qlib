# Hikyuu 事件驱动回测集成方案

## 概述

**目标**: 将 Qlib 预测结果集成到 Hikyuu 的事件驱动回测框架中
**优先级**: P2 - 中等复杂度
**状态**: ✅ 技术方案已完成

---

## 核心挑战

### 1. Qlib 批量预测 vs Hikyuu 事件驱动

**问题描述**:

| 维度 | Qlib | Hikyuu |
|------|------|--------|
| **执行模式** | 批量预测(全历史) | 事件驱动(逐bar) |
| **预测时间** | T+0 全部预测完成 | T 时刻只能看到 ≤T 的数据 |
| **回测模式** | 向量化回测 | 逐笔成交回测 |
| **数据可见性** | 预测时可见未来数据(需注意未来函数) | 严格时间顺序,不可见未来 |

**示例对比**:

```python
# === Qlib 批量预测 ===
predictions = model.predict(dataset)  # 一次性预测全部
# pred.pkl:
#              score
# datetime   instrument
# 2020-01-02 SH600000    0.05
# 2020-01-03 SH600000    0.03
# ...
# 2024-12-31 SZ000001   -0.02

# === Hikyuu 事件驱动 ===
class MyStrategy(SignalBase):
    def _calculate(self, kdata):
        for i in range(len(kdata)):
            # 在时刻 T,只能访问 <=T 的数据
            current_datetime = kdata[i].datetime

            # 查询预测结果
            pred_score = self._get_prediction(current_datetime)

            if pred_score > threshold:
                self._addBuySignal(current_datetime)
```

**解决方案**: 使用 `CustomSG_QlibFactor` 信号器,将 Qlib 预测结果按时间顺序查询

---

### 2. Portfolio 组合管理集成

**问题**: Qlib Top-K 选股 → Hikyuu Portfolio 多股票回测

**Qlib 选股逻辑**:
```python
# 每日选出 Top-K 只股票
for date in trading_days:
    top_k_stocks = predictions.loc[date].nlargest(K, 'score')
    # 对 Top-K 股票生成交易信号
```

**Hikyuu Portfolio 架构**:
```python
from hikyuu import Portfolio, SYS_Simple

# 1. 创建多个交易系统
sys_list = []
for stock in stock_pool:
    my_sg = CustomSG_QlibFactor(pred_pkl_path="pred.pkl", top_k=10)
    sys = SYS_Simple(sg=my_sg, mm=mm, tm=tm)
    sys_list.append(sys)

# 2. 创建 Portfolio
pf = Portfolio()
pf.run(sys_list, Query(-365))
```

**关键问题**:
1. **动态股票池**: Top-K 股票每日变化,如何动态调整?
2. **资金分配**: 如何在 Top-K 股票间分配资金?
3. **仓位管理**: 如何处理进出 Top-K 的股票?

---

### 3. 回测性能指标对齐

**Qlib 回测指标**:
- IC (信息系数)
- ICIR (信息比率)
- Rank IC
- Annualized Return
- Sharpe Ratio
- Max Drawdown

**Hikyuu 回测指标**:
- 总资产
- 收益率
- 最大回撤
- 交易次数
- 胜率
- 盈亏比

**挑战**: 需要统一两者的性能评估标准

---

## 技术方案

### 方案 1: 基于 CustomSG_QlibFactor 的单股票回测

**适用场景**: 单股票策略测试

```python
# examples/backtest/single_stock_backtest.py

from hikyuu import *
from adapters.hikyuu.custom_sg_qlib_factor import CustomSG_QlibFactor

# 1. 初始化 Hikyuu
load_hikyuu()

# 2. 创建 Qlib 信号器
my_sg = CustomSG_QlibFactor(
    pred_pkl_path="output/LGBM/pred.pkl",
    buy_threshold=0.02,   # 预测分数 > 0.02 买入
    sell_threshold=-0.02,  # 预测分数 < -0.02 卖出
    top_k=10
)

# 3. 创建交易系统
my_tm = crtTM(init_cash=300000)
my_mm = MM_FixedCount(1000)  # 固定每次买 1000 股

my_sys = SYS_Simple(
    tm=my_tm,
    sg=my_sg,
    mm=my_mm
)

# 4. 运行回测
my_sys.run(sm['sh600000'], Query(-365))

# 5. 性能分析
print(f"总资产: {my_tm.currentCash:.2f}")
print(f"买入次数: {len(my_sg.getBuySignal())}")
print(f"卖出次数: {len(my_sg.getSellSignal())}")

# 6. 可视化
my_sys.plot()
```

---

### 方案 2: Portfolio 组合回测 (Top-K 选股)

**适用场景**: 多股票组合策略

```python
# examples/backtest/portfolio_backtest.py

from hikyuu import *
from adapters.hikyuu.custom_sg_qlib_factor import CustomSG_QlibFactor
from adapters.hikyuu.portfolio_adapter import QlibPortfolioAdapter

# 1. 初始化
load_hikyuu()

# 2. 创建 Portfolio 适配器
portfolio_adapter = QlibPortfolioAdapter(
    pred_pkl_path="output/LGBM/pred.pkl",
    top_k=10,
    rebalance_period="WEEK"  # 每周调仓
)

# 3. 获取动态股票池
date_range = DateRange(
    start_date=date(2020, 1, 1),
    end_date=date(2023, 12, 31)
)

stock_pool = portfolio_adapter.get_dynamic_stock_pool(date_range)
# stock_pool = {
#     pd.Timestamp('2020-01-02'): ['SH600000', 'SH600157', ...],  # 10只
#     pd.Timestamp('2020-01-09'): ['SH600000', 'SZ000001', ...],  # 10只
#     ...
# }

# 4. 创建交易系统列表
tm = crtTM(init_cash=1000000)
mm = MM_FixedRisk(0.02)  # 每只股票风险 2%

sys_list = []
for stock_code in portfolio_adapter.get_all_stocks():
    stock = sm[stock_code.lower()]

    sg = CustomSG_QlibFactor(
        pred_pkl_path="output/LGBM/pred.pkl",
        buy_threshold=0.01,
        top_k=10
    )

    sys = SYS_Simple(tm=tm, sg=sg, mm=mm)
    sys_list.append((sys, stock))

# 5. 运行 Portfolio 回测
pf = Portfolio()
pf.run(sys_list, Query(-1095))  # 3年回测

# 6. 性能分析
print(f"组合总资产: {tm.currentCash:.2f}")
print(f"年化收益率: {pf.getAnnualizedReturn():.2%}")
print(f"最大回撤: {pf.getMaxDrawdown():.2%}")
print(f"夏普比率: {pf.getSharpeRatio():.2f}")
```

---

### 方案 3: QlibPortfolioAdapter 实现

```python
# src/adapters/hikyuu/portfolio_adapter.py

import pandas as pd
from typing import Dict, List
from datetime import date
from domain.value_objects.date_range import DateRange


class QlibPortfolioAdapter:
    """
    Qlib → Hikyuu Portfolio 适配器

    核心功能:
    1. 读取 Qlib pred.pkl
    2. 计算每日 Top-K 股票
    3. 生成动态股票池
    4. 管理调仓逻辑
    """

    def __init__(
        self,
        pred_pkl_path: str,
        top_k: int = 10,
        rebalance_period: str = "WEEK"
    ):
        self.pred_pkl_path = pred_pkl_path
        self.top_k = top_k
        self.rebalance_period = rebalance_period

        self._pred_df = None
        self._load_predictions()

    def _load_predictions(self):
        """加载 Qlib 预测结果"""
        self._pred_df = pd.read_pickle(self.pred_pkl_path)

        # 确保 MultiIndex(datetime, instrument)
        if not isinstance(self._pred_df.index, pd.MultiIndex):
            raise ValueError("pred.pkl 必须是 MultiIndex(datetime, instrument) 格式")

    def get_dynamic_stock_pool(
        self,
        date_range: DateRange
    ) -> Dict[pd.Timestamp, List[str]]:
        """
        获取动态股票池

        Args:
            date_range: 日期范围

        Returns:
            {日期: [Top-K 股票列表]}
        """
        stock_pool = {}

        # 获取调仓日期列表
        rebalance_dates = self._get_rebalance_dates(date_range)

        for rebalance_date in rebalance_dates:
            # 获取该日期的预测结果
            try:
                date_predictions = self._pred_df.loc[rebalance_date]
            except KeyError:
                continue

            # 选出 Top-K
            top_k_stocks = date_predictions.nlargest(
                self.top_k,
                'score'
            )

            stock_pool[rebalance_date] = top_k_stocks.index.tolist()

        return stock_pool

    def _get_rebalance_dates(
        self,
        date_range: DateRange
    ) -> List[pd.Timestamp]:
        """
        获取调仓日期列表

        Args:
            date_range: 日期范围

        Returns:
            调仓日期列表
        """
        # 获取所有交易日
        all_dates = self._pred_df.index.get_level_values(0).unique()

        # 过滤日期范围
        start = pd.Timestamp(date_range.start_date)
        end = pd.Timestamp(date_range.end_date)

        dates_in_range = all_dates[
            (all_dates >= start) & (all_dates <= end)
        ]

        # 根据调仓周期筛选
        if self.rebalance_period == "DAY":
            return dates_in_range.tolist()

        elif self.rebalance_period == "WEEK":
            # 每周第一个交易日
            df = pd.DataFrame({'date': dates_in_range})
            df['week'] = df['date'].dt.isocalendar().week
            df['year'] = df['date'].dt.year

            rebalance_dates = df.groupby(['year', 'week'])['date'].first()
            return rebalance_dates.tolist()

        elif self.rebalance_period == "MONTH":
            # 每月第一个交易日
            df = pd.DataFrame({'date': dates_in_range})
            df['month'] = df['date'].dt.to_period('M')

            rebalance_dates = df.groupby('month')['date'].first()
            return rebalance_dates.tolist()

        else:
            raise ValueError(f"不支持的调仓周期: {self.rebalance_period}")

    def get_all_stocks(self) -> List[str]:
        """获取所有出现过的股票列表"""
        return self._pred_df.index.get_level_values(1).unique().tolist()

    def get_stock_weight(
        self,
        date: pd.Timestamp,
        stock_code: str
    ) -> float:
        """
        获取某只股票在某日期的权重

        Args:
            date: 日期
            stock_code: 股票代码

        Returns:
            权重 (0-1)
        """
        try:
            date_predictions = self._pred_df.loc[date]
            top_k_stocks = date_predictions.nlargest(self.top_k, 'score')

            if stock_code not in top_k_stocks.index:
                return 0.0

            # 等权重
            return 1.0 / self.top_k

        except KeyError:
            return 0.0
```

---

## 调仓策略实现

### DynamicRebalanceSG (动态调仓信号器)

```python
# src/adapters/hikyuu/dynamic_rebalance_sg.py

from hikyuu import SignalBase, Datetime
import pandas as pd
from typing import Dict, Set


class DynamicRebalanceSG(SignalBase):
    """
    动态调仓信号器

    功能:
    1. 根据 Qlib Top-K 结果动态调仓
    2. 在调仓日买入新进入 Top-K 的股票
    3. 在调仓日卖出退出 Top-K 的股票
    """

    def __init__(
        self,
        portfolio_adapter,
        name: str = "SG_DynamicRebalance"
    ):
        super().__init__(name)
        self.portfolio_adapter = portfolio_adapter
        self._current_holdings: Set[str] = set()

    def _calculate(self, kdata):
        """计算信号"""
        stock = kdata.getStock()
        stock_code = stock.market_code  # SH600000

        # 获取调仓日期
        rebalance_dates = self.portfolio_adapter._get_rebalance_dates(
            DateRange(
                start_date=kdata[0].datetime.date(),
                end_date=kdata[-1].datetime.date()
            )
        )

        for i in range(len(kdata)):
            k_datetime = kdata[i].datetime
            pd_datetime = self._hikyuu_to_pandas_datetime(k_datetime)

            # 检查是否为调仓日
            if pd_datetime not in rebalance_dates:
                continue

            # 获取该日期的 Top-K 股票池
            top_k_stocks = self.portfolio_adapter.get_dynamic_stock_pool(
                DateRange(pd_datetime.date(), pd_datetime.date())
            ).get(pd_datetime, [])

            # 买入信号: 进入 Top-K
            if stock_code in top_k_stocks and stock_code not in self._current_holdings:
                self._addBuySignal(k_datetime)
                self._current_holdings.add(stock_code)

            # 卖出信号: 退出 Top-K
            elif stock_code not in top_k_stocks and stock_code in self._current_holdings:
                self._addSellSignal(k_datetime)
                self._current_holdings.discard(stock_code)
```

---

## 完整回测流程

### Step 1: Qlib 模型训练与预测

```python
# step1_qlib_training.py

import qlib
from qlib.workflow import R
from qlib.contrib.model.gbdt import LGBModel

# 1. 初始化 Qlib
qlib.init(provider_uri="~/.qlib/qlib_data/cn_data")

# 2. 准备数据集
dataset = ...

# 3. 训练模型
model = LGBModel()
model.fit(dataset)

# 4. 预测
predictions = model.predict(dataset)

# 5. 保存预测结果
predictions.to_pickle("output/LGBM/pred.pkl")
```

### Step 2: Hikyuu 回测

```python
# step2_hikyuu_backtest.py

from hikyuu import *
from adapters.hikyuu.portfolio_adapter import QlibPortfolioAdapter
from adapters.hikyuu.dynamic_rebalance_sg import DynamicRebalanceSG

# 1. 初始化
load_hikyuu()

# 2. 创建 Portfolio 适配器
adapter = QlibPortfolioAdapter(
    pred_pkl_path="output/LGBM/pred.pkl",
    top_k=10,
    rebalance_period="WEEK"
)

# 3. 创建交易系统
tm = crtTM(init_cash=1000000)
mm = MM_EqualWeight(adapter.top_k)  # 等权重分配

sys_list = []
for stock_code in adapter.get_all_stocks():
    stock = sm[stock_code.lower()]

    sg = DynamicRebalanceSG(portfolio_adapter=adapter)
    sys = SYS_Simple(tm=tm, sg=sg, mm=mm)

    sys_list.append((sys, stock))

# 4. 运行回测
pf = Portfolio()
pf.run(sys_list, Query(-1095))

# 5. 导出结果
results = {
    "total_assets": tm.currentCash,
    "trades": tm.getTradeList(),
    "performance": pf.getPerformanceMetrics()
}
```

### Step 3: 结果对比

```python
# step3_compare_results.py

import pandas as pd

# 1. Qlib 回测结果
qlib_results = {
    "IC": 0.05,
    "ICIR": 1.2,
    "Annual Return": 0.15,
    "Sharpe": 1.5,
    "Max Drawdown": -0.18
}

# 2. Hikyuu 回测结果
hikyuu_results = {
    "Annual Return": 0.16,
    "Sharpe": 1.48,
    "Max Drawdown": -0.19,
    "Win Rate": 0.55,
    "Total Trades": 120
}

# 3. 对比分析
comparison = pd.DataFrame({
    "Qlib": qlib_results,
    "Hikyuu": hikyuu_results
}).T

print(comparison)
```

---

## 性能优化

### 1. 预计算 Top-K

```python
class QlibPortfolioAdapterOptimized:
    def __init__(self, pred_pkl_path, top_k):
        self._pred_df = pd.read_pickle(pred_pkl_path)

        # 预计算所有日期的 Top-K
        self._top_k_cache = {}
        for date in self._pred_df.index.get_level_values(0).unique():
            top_k_stocks = self._pred_df.loc[date].nlargest(
                top_k, 'score'
            ).index.tolist()

            self._top_k_cache[date] = top_k_stocks

    def get_top_k_stocks(self, date: pd.Timestamp) -> List[str]:
        return self._top_k_cache.get(date, [])
```

### 2. 并行回测

```python
from concurrent.futures import ThreadPoolExecutor

def run_backtest_parallel(sys_list, query):
    """并行运行多个交易系统回测"""
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [
            executor.submit(sys.run, stock, query)
            for sys, stock in sys_list
        ]

        results = [f.result() for f in futures]

    return results
```

---

## 测试策略

### 单元测试

```python
# tests/unit/adapters/hikyuu/test_portfolio_adapter.py

import pytest
from adapters.hikyuu.portfolio_adapter import QlibPortfolioAdapter

def test_get_dynamic_stock_pool():
    """测试动态股票池生成"""
    adapter = QlibPortfolioAdapter(
        pred_pkl_path="data/test_pred.pkl",
        top_k=5
    )

    stock_pool = adapter.get_dynamic_stock_pool(
        DateRange(date(2020, 1, 1), date(2020, 1, 31))
    )

    # 验证每日有 5 只股票
    for date, stocks in stock_pool.items():
        assert len(stocks) == 5


def test_rebalance_dates():
    """测试调仓日期生成"""
    adapter = QlibPortfolioAdapter(
        pred_pkl_path="data/test_pred.pkl",
        rebalance_period="WEEK"
    )

    dates = adapter._get_rebalance_dates(
        DateRange(date(2020, 1, 1), date(2020, 12, 31))
    )

    # 一年约 52 周
    assert 50 <= len(dates) <= 54
```

---

## 后续优化方向

1. **风险管理**: 集成 Hikyuu 的 ST/TP 组件
2. **交易成本**: 考虑手续费、滑点
3. **市场冲击**: 大单拆分执行
4. **实时信号**: 支持增量更新预测结果
5. **多策略融合**: 支持多个 Qlib 模型的集成

---

## 参考文档

- Hikyuu Portfolio API: https://github.com/fasiondog/hikyuu
- Qlib Backtest: https://qlib.readthedocs.io/en/latest/component/backtest.html
- CustomSG_QlibFactor: [`src/adapters/signal/.claude.md`](../../src/adapters/signal/.claude.md)
- Portfolio Adapter: [`src/adapters/hikyuu/portfolio_adapter.py`](../../src/adapters/hikyuu/)

---

**最后更新**: 2025-11-11
**状态**: ✅ 技术方案已完成,待实现
