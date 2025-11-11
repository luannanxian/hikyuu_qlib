# CustomSG_QlibFactor 技术方案

## 文档概述

**文档类型**: 技术方案
**优先级**: P0 - 极高复杂度
**集成难点**: Qlib预测→Hikyuu信号转换
**创建时间**: 2025-11-11
**研究状态**: ✅ 已完成初步调研

---

## 1. 核心挑战

### 1.1 问题描述

需要实现一个自定义信号指示器 `CustomSG_QlibFactor`,用于将 Qlib 机器学习模型的预测结果转换为 Hikyuu 交易系统可用的买入/卖出信号。

### 1.2 技术栈

- **Hikyuu**: C++/Python 量化交易框架,基于 SignalBase 的信号系统
- **Qlib**: Microsoft AI 量化投资框架,基于 DataFrame 的预测输出
- **数据格式差异**:
  - Qlib: `MultiIndex(datetime, instrument)` DataFrame + pred.pkl
  - Hikyuu: `SignalBase._calculate(kdata)` 方法 + `_addBuySignal(datetime)` / `_addSellSignal(datetime)`

---

## 2. Hikyuu SignalBase API 研究

### 2.1 核心接口

根据官方文档,自定义信号指示器需要继承 `SignalBase` 并实现以下方法:

```python
class SignalBase:
    """信号指示器基类"""

    # 核心方法
    def _calculate(self, kdata):
        """【重载接口】子类计算接口 - 必须实现"""
        pass

    def _reset(self):
        """【重载接口】子类复位接口,复位内部私有变量"""
        pass

    def _clone(self):
        """【重载接口】子类克隆接口"""
        pass

    # 信号添加方法
    def _addBuySignal(self, datetime):
        """加入买入信号,在_calculate中调用"""
        pass

    def _addSellSignal(self, datetime):
        """加入卖出信号,在_calculate中调用"""
        pass

    # 参数管理
    def setParam(self, name, value):
        """设置参数"""
        pass

    def getParam(self, name):
        """获取参数"""
        pass
```

### 2.2 官方示例

```python
class SignalPython(SignalBase):
    def __init__(self):
        super(SignalPython, self).__init__("SignalPython")
        self._x = 0  # 私有属性
        self.setParam("test", 30)

    def _reset(self):
        self._x = 0

    def _clone(self):
        p = SignalPython()
        p._x = self._x
        return p

    def _calculate(self, k):
        # k 是 KData 对象,包含 OHLCV 数据
        self._addBuySignal(Datetime(201201210000))
        self._addSellSignal(Datetime(201201300000))
```

### 2.3 关键发现

1. **`_calculate(kdata)` 方法**:
   - 输入: `kdata` 是 Hikyuu 的 KData 对象
   - 包含时间序列的 OHLCV 数据
   - 通过 `kdata[i].datetime` 获取每根 K 线的时间戳

2. **信号添加机制**:
   - 必须使用 `_addBuySignal(datetime)` 添加买入信号
   - 必须使用 `_addSellSignal(datetime)` 添加卖出信号
   - `datetime` 参数是 Hikyuu 的 `Datetime` 对象

3. **参数配置**:
   - 支持通过 `setParam()` 设置自定义参数
   - 参数类型: int, bool, float, string

---

## 3. Qlib 预测结果格式研究

### 3.1 pred.pkl 数据结构

根据官方文档和代码示例,Qlib 的预测结果格式如下:

```python
# pred.pkl 文件结构
pred_df = pd.read_pickle("pred.pkl")

# MultiIndex DataFrame
# Index: MultiIndex([datetime, instrument])
# Columns: ['score'] 或 ['score', 'label'] 或多列预测结果

# 示例数据:
#                          score
# datetime   instrument
# 2018-09-21 SH600000    0.0234
#            SH600157    0.0156
#            SZ000001   -0.0089
# 2018-09-25 SH600000    0.0198
#            SH600157    0.0245
```

### 3.2 时间戳格式

```python
# Qlib 使用 pandas Timestamp
pred_df.index.get_level_values(0)  # DatetimeIndex
# 例: Timestamp('2018-09-21 00:00:00')

# Hikyuu 使用自定义 Datetime 对象
from hikyuu import Datetime
dt = Datetime(201809210000)  # YYYYMMDDHHmm 格式
```

### 3.3 预测分数范围

```python
# Qlib 预测分数通常是连续值,范围不固定
# 常见范围: [-0.1, 0.1] 或经过标准化后的任意范围

# 示例处理:
pred_df['score'].describe()
# count    150000.000
# mean          0.000
# std           0.045
# min          -0.156
# max           0.234
```

### 3.4 关键发现

1. **MultiIndex 结构**:
   - Level 0: datetime (pandas Timestamp)
   - Level 1: instrument (str, 例如 'SH600000')

2. **预测结果列**:
   - 单列: `score` - 预测分数
   - 多列: `score_0`, `score_1`, `score_2` - 多模型集成
   - 可能包含: `label` - 真实标签(用于回测分析)

3. **时间对齐问题**:
   - Qlib 预测时间戳: 日级别 (00:00:00)
   - Hikyuu K 线时间戳: 可能是分钟级/日级
   - **需要时间戳转换和对齐逻辑**

---

## 4. CustomSG_QlibFactor 实现方案

### 4.1 架构设计

```python
# src/adapters/hikyuu/custom_sg_qlib_factor.py

from hikyuu import SignalBase, Datetime, Stock
import pandas as pd
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime as py_datetime


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
        """
        初始化信号指示器

        Args:
            pred_pkl_path: Qlib 预测结果文件路径 (pred.pkl)
            buy_threshold: 买入阈值,预测分数 > buy_threshold 时买入
            sell_threshold: 卖出阈值,预测分数 < sell_threshold 时卖出
            top_k: Top-K 选股,只对预测分数排名前 K 的股票生成买入信号
            name: 信号指示器名称
        """
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

    def _load_predictions(self):
        """加载 Qlib 预测结果"""
        if self._pred_df is not None:
            return

        pred_path = Path(self.getParam("pred_pkl_path"))
        if not pred_path.exists():
            raise FileNotFoundError(f"Prediction file not found: {pred_path}")

        # 加载 pred.pkl
        self._pred_df = pd.read_pickle(pred_path)

        # 确保索引是 MultiIndex(datetime, instrument)
        if not isinstance(self._pred_df.index, pd.MultiIndex):
            raise ValueError("pred.pkl must have MultiIndex(datetime, instrument)")

        # 获取分数列名
        score_col = 'score'
        if score_col not in self._pred_df.columns:
            # 尝试其他可能的列名
            possible_cols = ['score_0', 'pred', 'prediction']
            for col in possible_cols:
                if col in self._pred_df.columns:
                    score_col = col
                    break
            else:
                raise ValueError(f"Score column not found in pred.pkl. Available: {self._pred_df.columns.tolist()}")

        # 按日期分组,计算 Top-K
        self._calculate_top_k_stocks(score_col)

    def _calculate_top_k_stocks(self, score_col: str):
        """
        计算每个交易日的 Top-K 股票

        Args:
            score_col: 预测分数列名
        """
        top_k = self.getParam("top_k")

        # 按日期分组
        for date, group in self._pred_df.groupby(level=0):
            # 按预测分数排序,取 Top-K
            top_stocks = group.nlargest(top_k, score_col)

            # 存储每只股票在该日期的预测分数
            for instrument, score in top_stocks[score_col].items():
                if instrument not in self._stock_predictions:
                    self._stock_predictions[instrument] = pd.Series(dtype=float)
                self._stock_predictions[instrument][date] = score

    def _hikyuu_to_pandas_datetime(self, hq_datetime: Datetime) -> pd.Timestamp:
        """
        将 Hikyuu Datetime 转换为 pandas Timestamp

        Args:
            hq_datetime: Hikyuu Datetime 对象

        Returns:
            pandas Timestamp
        """
        # Hikyuu Datetime 格式: 201809210000 (YYYYMMDDHHmm)
        dt_str = str(hq_datetime.number)
        year = int(dt_str[:4])
        month = int(dt_str[4:6])
        day = int(dt_str[6:8])
        hour = int(dt_str[8:10]) if len(dt_str) >= 10 else 0
        minute = int(dt_str[10:12]) if len(dt_str) >= 12 else 0

        return pd.Timestamp(year=year, month=month, day=day, hour=hour, minute=minute)

    def _pandas_to_hikyuu_datetime(self, pd_timestamp: pd.Timestamp) -> Datetime:
        """
        将 pandas Timestamp 转换为 Hikyuu Datetime

        Args:
            pd_timestamp: pandas Timestamp

        Returns:
            Hikyuu Datetime 对象
        """
        dt_number = (
            pd_timestamp.year * 100000000 +
            pd_timestamp.month * 1000000 +
            pd_timestamp.day * 10000 +
            pd_timestamp.hour * 100 +
            pd_timestamp.minute
        )
        return Datetime(dt_number)

    def _calculate(self, kdata):
        """
        【核心方法】计算信号

        Args:
            kdata: Hikyuu KData 对象,包含股票的 K 线数据
        """
        # 1. 加载预测结果
        self._load_predictions()

        # 2. 获取当前股票代码
        stock = kdata.getStock()
        stock_code = stock.market_code  # 例如: 'SH600000'

        # 3. 检查该股票是否有预测结果
        if stock_code not in self._stock_predictions:
            # 没有预测结果,不生成信号
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
                # 买入信号
                self._addBuySignal(k_datetime)
            elif pred_score < sell_threshold:
                # 卖出信号
                self._addSellSignal(k_datetime)
```

### 4.2 使用示例

```python
# examples/signal_conversion/test_custom_sg_qlib_factor.py

from hikyuu import *
from pathlib import Path
import sys

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from adapters.hikyuu.custom_sg_qlib_factor import CustomSG_QlibFactor


def test_custom_sg_qlib_factor():
    """测试 CustomSG_QlibFactor 信号指示器"""

    # 1. 初始化 Hikyuu
    hku_config_path = Path.home() / ".hikyuu" / "config.ini"
    load_hikyuu(str(hku_config_path))

    # 2. 创建信号指示器
    pred_pkl_path = "output/LGBM/pred.pkl"
    my_sg = CustomSG_QlibFactor(
        pred_pkl_path=pred_pkl_path,
        buy_threshold=0.02,
        sell_threshold=-0.02,
        top_k=10,
        name="SG_QlibFactor"
    )

    # 3. 创建交易账户
    my_tm = crtTM(init_cash=300000)

    # 4. 创建资金管理策略
    my_mm = MM_FixedCount(1000)

    # 5. 创建交易系统
    sys = SYS_Simple(tm=my_tm, sg=my_sg, mm=my_mm)

    # 6. 运行回测
    stock = sm['sz000001']
    query = Query(-150)  # 最近 150 个交易日
    sys.run(stock, query)

    # 7. 打印结果
    print("=" * 50)
    print("回测结果:")
    print("=" * 50)
    print(f"总资产: {my_tm.currentCash:.2f}")
    print(f"买入次数: {len(my_sg.getBuySignal())}")
    print(f"卖出次数: {len(my_sg.getSellSignal())}")

    # 8. 可视化
    sys.plot()


if __name__ == "__main__":
    test_custom_sg_qlib_factor()
```

---

## 5. 技术难点与解决方案

### 5.1 时间戳对齐问题

**问题**: Qlib 预测结果是日级别时间戳 (00:00:00),而 Hikyuu K 线可能是分钟级数据。

**解决方案**:
```python
def _hikyuu_to_pandas_datetime(self, hq_datetime: Datetime) -> pd.Timestamp:
    """转换 Hikyuu 时间戳"""
    # 实现见上文
    pass

def _calculate(self, kdata):
    # 时间对齐: 只保留日期部分
    pd_date = pd_datetime.normalize()  # 2018-09-21 15:00:00 -> 2018-09-21 00:00:00
```

### 5.2 股票代码格式差异

**问题**: Qlib 使用 `SH600000` 格式,Hikyuu 可能使用不同格式。

**解决方案**:
```python
def _normalize_stock_code(self, stock: Stock) -> str:
    """
    标准化股票代码

    Hikyuu: sh600000 -> SH600000
    Qlib:   SH600000
    """
    market_code = stock.market_code
    return market_code.upper()
```

### 5.3 Top-K 选股逻辑

**问题**: Qlib 预测结果包含全市场股票,但只需要对 Top-K 股票生成信号。

**解决方案**:
```python
def _calculate_top_k_stocks(self, score_col: str):
    """预先计算每个交易日的 Top-K 股票"""
    top_k = self.getParam("top_k")
    for date, group in self._pred_df.groupby(level=0):
        top_stocks = group.nlargest(top_k, score_col)
        # 只存储 Top-K 股票的预测结果
```

### 5.4 信号策略灵活性

**问题**: 不同策略可能需要不同的信号生成逻辑 (阈值、动态阈值、排名等)。

**解决方案**:
```python
# 支持通过参数配置
self.setParam("strategy_type", "threshold")  # threshold | ranking | dynamic

def _generate_signal_by_threshold(self, pred_score):
    """基于固定阈值"""
    if pred_score > self.getParam("buy_threshold"):
        return "BUY"
    elif pred_score < self.getParam("sell_threshold"):
        return "SELL"
    return "HOLD"

def _generate_signal_by_ranking(self, pred_score, all_scores):
    """基于排名"""
    ranking = (all_scores > pred_score).sum() + 1
    if ranking <= self.getParam("top_k"):
        return "BUY"
    return "HOLD"
```

---

## 6. 数据流图

```
┌─────────────────────────────────────────────────────────────┐
│                     Qlib 训练与预测流程                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   pred.pkl       │
                    │  MultiIndex DF   │
                    │ (datetime, inst) │
                    └──────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              CustomSG_QlibFactor._load_predictions()         │
│  1. 加载 pred.pkl                                            │
│  2. 提取预测分数列 (score)                                    │
│  3. 计算每日 Top-K 股票                                       │
│  4. 存储到 _stock_predictions Dict                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              CustomSG_QlibFactor._calculate(kdata)           │
│  1. 获取当前股票代码                                          │
│  2. 查找该股票的预测序列                                      │
│  3. 遍历 KData,匹配时间戳                                    │
│  4. 根据阈值策略生成信号                                      │
│  5. 调用 _addBuySignal() / _addSellSignal()                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ Hikyuu 交易系统   │
                    │ SYS_Simple       │
                    │ (SG+MM+TM)       │
                    └──────────────────┘
```

---

## 7. 测试计划

### 7.1 单元测试

```python
# tests/adapters/hikyuu/test_custom_sg_qlib_factor.py

import pytest
import pandas as pd
from pathlib import Path
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
    assert pd_dt.hour == 9
    assert pd_dt.minute == 30

    # Pandas -> Hikyuu
    hq_dt_back = sg._pandas_to_hikyuu_datetime(pd_dt)
    assert hq_dt_back.number == 201809210930


def test_top_k_calculation():
    """测试 Top-K 计算"""
    # 创建模拟数据
    dates = pd.date_range('2018-01-01', periods=5)
    instruments = ['SH600000', 'SH600157', 'SZ000001', 'SZ000002']

    index = pd.MultiIndex.from_product([dates, instruments], names=['datetime', 'instrument'])
    pred_df = pd.DataFrame({'score': range(len(index))}, index=index)

    # 保存为 test_pred.pkl
    pred_df.to_pickle('data/test_pred.pkl')

    sg = CustomSG_QlibFactor(pred_pkl_path="data/test_pred.pkl", top_k=2)
    sg._load_predictions()

    # 每个日期应该有 2 只股票
    assert len(sg._stock_predictions) <= 4  # 最多 4 只股票
```

### 7.2 集成测试

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

## 8. 性能优化

### 8.1 预加载优化

```python
def _load_predictions(self):
    """优化: 只加载需要的日期范围"""
    if self._pred_df is not None:
        return

    # 获取 KData 的日期范围 (需要从外部传入)
    start_date = self.getParam("start_date")
    end_date = self.getParam("end_date")

    # 加载并过滤
    self._pred_df = pd.read_pickle(self.getParam("pred_pkl_path"))
    self._pred_df = self._pred_df.loc[start_date:end_date]
```

### 8.2 缓存机制

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

## 9. 后续优化方向

1. **动态阈值策略**: 基于历史分布动态调整买入/卖出阈值
2. **多因子融合**: 支持多个 pred.pkl 文件的集成
3. **实时信号**: 支持增量更新预测结果,而非全量加载
4. **风险控制**: 集成 Hikyuu 的 ST(止损)、TP(止盈) 组件
5. **信号验证**: 添加信号质量检查和异常检测

---

## 10. 参考文档

- Hikyuu SignalBase API: https://github.com/fasiondog/hikyuu/blob/master/docs/source/trade_sys/signal.rst
- Qlib Prediction Format: https://github.com/microsoft/qlib (examples/workflow_by_code.ipynb)
- 项目需求文档: `docs/requirements.md` (DR-008, UC-004)
- 项目设计文档: `docs/design.md` (Section 3.3 - SignalConverterAdapter)

---

**文档版本**: v1.0
**最后更新**: 2025-11-11
**作者**: Claude Code + 用户协作
