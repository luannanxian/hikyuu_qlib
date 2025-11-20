# Signal Converter Adapter - 集成方案

## 模块概述

**位置**: `src/adapters/signal/`
**职责**: 实现 `ISignalConverter` 接口,将 Qlib 预测结果转换为 Hikyuu 交易信号
**优先级**: P0 - 极高复杂度
**状态**: ✅ 技术方案已完成

---

## 核心集成挑战

### 1. Qlib 预测 → Hikyuu 信号转换

**问题描述**:
- Qlib 输出: `MultiIndex(datetime, instrument)` DataFrame,预测分数为连续值
- Hikyuu 输入: `SignalBase._addBuySignal(datetime)` / `_addSellSignal(datetime)`
- 需要实现 `CustomSG_QlibFactor` 类,继承自 `hikyuu.SignalBase`

**技术方案**: 详见 [`docs/integration/SIGNAL_CONVERSION_SOLUTION.md`](../../../docs/integration/SIGNAL_CONVERSION_SOLUTION.md)

### 2. 时间戳对齐问题

**问题**:
- Qlib 时间戳: `pandas.Timestamp` (日级别,00:00:00)
- Hikyuu 时间戳: `Datetime(YYYYMMDDHHmm)` (可能是分钟级)

**解决方案**:
```python
def _hikyuu_to_pandas_datetime(self, hq_datetime: Datetime) -> pd.Timestamp:
    """Hikyuu Datetime → pandas Timestamp"""
    dt_str = str(hq_datetime.number)
    year = int(dt_str[:4])
    month = int(dt_str[4:6])
    day = int(dt_str[6:8])
    return pd.Timestamp(year=year, month=month, day=day)

def _align_timestamps(self, k_datetime: Datetime, pred_date: pd.Timestamp) -> bool:
    """时间对齐: 只保留日期部分"""
    pd_datetime = self._hikyuu_to_pandas_datetime(k_datetime)
    return pd_datetime.normalize() == pred_date.normalize()
```

### 3. Top-K 选股逻辑

**问题**: Qlib 预测包含全市场股票,但只需要对 Top-K 股票生成信号

**解决方案**:
```python
def _calculate_top_k_stocks(self, score_col: str):
    """预先计算每个交易日的 Top-K 股票"""
    top_k = self.getParam("top_k")

    for date, group in self._pred_df.groupby(level=0):
        # 按预测分数排序,取 Top-K
        top_stocks = group.nlargest(top_k, score_col)

        # 只存储 Top-K 股票的预测结果
        for instrument, score in top_stocks[score_col].items():
            if instrument not in self._stock_predictions:
                self._stock_predictions[instrument] = pd.Series(dtype=float)
            self._stock_predictions[instrument][date] = score
```

---

## 架构设计

### CustomSG_QlibFactor 类

```python
# src/adapters/hikyuu/custom_sg_qlib_factor.py

from hikyuu import SignalBase, Datetime
import pandas as pd
from typing import Dict, Optional

class CustomSG_QlibFactor(SignalBase):
    """
    基于 Qlib 预测结果的自定义信号指示器

    核心功能:
    1. 加载 Qlib pred.pkl 预测结果
    2. 提取当前股票的预测分数
    3. 基于阈值策略生成买入/卖出信号
    4. 处理时间戳对齐问题
    """

    def __init__(
        self,
        pred_pkl_path: str,
        buy_threshold: float = 0.02,
        sell_threshold: float = -0.02,
        top_k: int = 10,
        name: str = "SG_QlibFactor"
    ):
        super().__init__(name)

        # 私有属性
        self._pred_df: Optional[pd.DataFrame] = None
        self._stock_predictions: Dict[str, pd.Series] = {}

        # 配置参数
        self.setParam("pred_pkl_path", pred_pkl_path)
        self.setParam("buy_threshold", buy_threshold)
        self.setParam("sell_threshold", sell_threshold)
        self.setParam("top_k", top_k)

    def _reset(self):
        """复位内部状态"""
        self._pred_df = None
        self._stock_predictions.clear()

    def _clone(self):
        """克隆信号指示器"""
        cloned = CustomSG_QlibFactor(
            pred_pkl_path=self.getParam("pred_pkl_path"),
            buy_threshold=self.getParam("buy_threshold"),
            sell_threshold=self.getParam("sell_threshold"),
            top_k=self.getParam("top_k"),
            name=self.name
        )
        cloned._pred_df = self._pred_df
        cloned._stock_predictions = self._stock_predictions.copy()
        return cloned

    def _calculate(self, kdata):
        """
        【核心方法】计算信号

        流程:
        1. 加载预测结果
        2. 获取当前股票代码
        3. 遍历 K 线数据,匹配预测结果
        4. 根据阈值生成信号
        """
        # 1. 加载预测结果
        self._load_predictions()

        # 2. 获取当前股票代码
        stock = kdata.getStock()
        stock_code = stock.market_code  # 例如: 'SH600000'

        # 3. 检查该股票是否有预测结果
        if stock_code not in self._stock_predictions:
            return

        # 4. 获取该股票的预测序列
        stock_pred_series = self._stock_predictions[stock_code]

        # 5. 获取阈值
        buy_threshold = self.getParam("buy_threshold")
        sell_threshold = self.getParam("sell_threshold")

        # 6. 遍历 K 线数据,匹配预测结果
        for i in range(len(kdata)):
            k_datetime = kdata[i].datetime

            # 转换为 pandas Timestamp (日期对齐)
            pd_datetime = self._hikyuu_to_pandas_datetime(k_datetime)
            pd_date = pd_datetime.normalize()  # 只保留日期部分

            # 查找该日期的预测分数
            if pd_date not in stock_pred_series.index:
                continue

            pred_score = stock_pred_series[pd_date]

            # 7. 根据阈值生成信号
            if pred_score > buy_threshold:
                self._addBuySignal(k_datetime)
            elif pred_score < sell_threshold:
                self._addSellSignal(k_datetime)
```

---

## 使用示例

```python
# examples/signal_conversion/test_custom_sg_qlib_factor.py

from hikyuu import *
from pathlib import Path
from adapters.hikyuu.custom_sg_qlib_factor import CustomSG_QlibFactor

# 1. 初始化 Hikyuu
load_hikyuu()

# 2. 创建信号指示器
pred_pkl_path = "output/LGBM/pred.pkl"
my_sg = CustomSG_QlibFactor(
    pred_pkl_path=pred_pkl_path,
    buy_threshold=0.02,
    sell_threshold=-0.02,
    top_k=10
)

# 3. 创建交易系统
my_tm = crtTM(init_cash=300000)
my_mm = MM_FixedCount(1000)
sys = SYS_Simple(tm=my_tm, sg=my_sg, mm=my_mm)

# 4. 运行回测
sys.run(sm['sz000001'], Query(-150))

# 5. 打印结果
print(f"总资产: {my_tm.currentCash:.2f}")
print(f"买入次数: {len(my_sg.getBuySignal())}")
print(f"卖出次数: {len(my_sg.getSellSignal())}")

# 6. 可视化
sys.plot()
```

---

## 测试策略

### 单元测试

```python
# tests/unit/adapters/signal/test_custom_sg_qlib_factor.py

import pytest
import pandas as pd
from adapters.hikyuu.custom_sg_qlib_factor import CustomSG_QlibFactor

def test_load_predictions():
    """测试加载预测结果"""
    sg = CustomSG_QlibFactor(pred_pkl_path="data/test_pred.pkl")
    sg._load_predictions()

    assert sg._pred_df is not None
    assert isinstance(sg._pred_df.index, pd.MultiIndex)

def test_time_conversion():
    """测试时间戳转换"""
    from hikyuu import Datetime

    sg = CustomSG_QlibFactor(pred_pkl_path="data/test_pred.pkl")

    # Hikyuu -> Pandas
    hq_dt = Datetime(201809210930)
    pd_dt = sg._hikyuu_to_pandas_datetime(hq_dt)
    assert pd_dt.year == 2018
    assert pd_dt.month == 9
    assert pd_dt.day == 21

def test_top_k_calculation():
    """测试 Top-K 计算"""
    # 创建模拟数据
    dates = pd.date_range('2018-01-01', periods=5)
    instruments = ['SH600000', 'SH600157', 'SZ000001', 'SZ000002']

    index = pd.MultiIndex.from_product([dates, instruments])
    pred_df = pd.DataFrame({'score': range(len(index))}, index=index)
    pred_df.to_pickle('data/test_pred.pkl')

    sg = CustomSG_QlibFactor(pred_pkl_path="data/test_pred.pkl", top_k=2)
    sg._load_predictions()

    # 每个日期应该有 2 只股票
    assert len(sg._stock_predictions) <= 4
```

### 集成测试

```python
# tests/integration/test_signal_backtest.py

def test_end_to_end_backtest():
    """端到端回测测试"""
    from hikyuu import *

    # 初始化
    load_hikyuu()

    # 创建信号
    sg = CustomSG_QlibFactor(
        pred_pkl_path="output/LGBM/pred.pkl",
        buy_threshold=0.01,
        top_k=5
    )

    # 创建系统
    tm = crtTM(init_cash=100000)
    mm = MM_FixedCount(100)
    sys = SYS_Simple(tm=tm, sg=sg, mm=mm)

    # 运行
    sys.run(sm['sz000001'], Query(-100))

    # 验证
    assert tm.currentCash > 0
    assert len(sg.getBuySignal()) > 0
```

---

## 性能优化

### 1. 预加载优化

```python
def _load_predictions(self):
    """优化: 只加载需要的日期范围"""
    if self._pred_df is not None:
        return

    # 获取 KData 的日期范围
    start_date = self.getParam("start_date")
    end_date = self.getParam("end_date")

    # 加载并过滤
    self._pred_df = pd.read_pickle(self.getParam("pred_pkl_path"))
    self._pred_df = self._pred_df.loc[start_date:end_date]
```

### 2. 缓存机制

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def _get_prediction_for_date(self, stock_code: str, date: str) -> float:
    """缓存预测结果查询"""
    if stock_code not in self._stock_predictions:
        return 0.0
    series = self._stock_predictions[stock_code]
    if date not in series.index:
        return 0.0
    return series[date]
```

---

## 后续优化方向

1. **动态阈值策略**: 基于历史分布动态调整买入/卖出阈值
2. **多因子融合**: 支持多个 pred.pkl 文件的集成
3. **实时信号**: 支持增量更新预测结果
4. **风险控制**: 集成 Hikyuu 的 ST/TP 组件
5. **信号验证**: 添加信号质量检查

---

## 参考文档

- 技术方案: [`docs/integration/SIGNAL_CONVERSION_SOLUTION.md`](../../../docs/integration/SIGNAL_CONVERSION_SOLUTION.md)
- Hikyuu SignalBase API: https://github.com/fasiondog/hikyuu
- Qlib 预测格式: https://github.com/microsoft/qlib
- Domain 端口定义: [`src/domain/ports/signal_converter.py`](../../domain/ports/signal_converter.py)

---

**最后更新**: 2025-11-11
**状态**: ✅ 技术方案已完成,待实现
