"""
性能优化版的 CustomSG_QlibFactor

主要优化:
1. 预先构建日期索引,避免重复转换
2. 缓存Top-K查找结果
3. 向量化日期匹配
"""

from pathlib import Path
import pandas as pd
from hikyuu import SignalBase, Datetime, Stock
from typing import Dict


class CustomSG_QlibFactorOptimized(SignalBase):
    """
    性能优化版 - 基于Qlib预测的信号指示器
    """

    def __init__(
        self,
        pred_pkl_path,
        buy_threshold=0.02,
        sell_threshold=-0.02,
        top_k=None,
        name="SG_QlibFactor_Opt",
    ):
        super().__init__()
        self.name = name

        # 参数
        self.set_param("pred_pkl_path", pred_pkl_path)
        self.set_param("buy_threshold", buy_threshold)
        self.set_param("sell_threshold", sell_threshold)
        self.set_param("top_k", top_k if top_k is not None else -1)

        # 存储
        self._pred_df = None
        self._stock_predictions = {}
        self._top_k_stocks_by_date = {}

        # ✅ 性能优化: 缓存
        self._date_index_cache = {}  # 缓存K线日期索引
        self._top_k_cache = {}  # 缓存Top-K查找结果

    def _load_predictions(self):
        """加载预测结果(只执行一次)"""
        if self._pred_df is not None:
            return

        pred_path = Path(self.get_param("pred_pkl_path"))
        if not pred_path.exists():
            raise FileNotFoundError(f"Prediction file not found: {pred_path}")

        # 加载pred.pkl
        self._pred_df = pd.read_pickle(pred_path)

        # 确保索引格式
        if not isinstance(self._pred_df.index, pd.MultiIndex):
            raise ValueError("pred.pkl must have MultiIndex(datetime, instrument)")

        # 检查索引顺序并修正
        if self._pred_df.index.names == ["stock_code", "timestamp"]:
            self._pred_df = self._pred_df.swaplevel(0, 1).sort_index()
        elif self._pred_df.index.names != ["timestamp", "stock_code"]:
            self._pred_df.index.names = ["timestamp", "stock_code"]

        # 预处理预测数据
        self._preprocess_predictions("score")

    def _preprocess_predictions(self, score_col: str):
        """
        预处理预测结果,存储所有预测数据并计算每日Top-K股票
        """
        top_k_param = self.get_param("top_k")
        top_k = top_k_param if top_k_param != -1 else None

        # 按日期分组处理
        for date, group in self._pred_df.groupby(level=0):
            date = pd.Timestamp(date).normalize()

            # 存储所有股票的预测数据
            for instrument in group.index.get_level_values(1):
                if instrument not in self._stock_predictions:
                    self._stock_predictions[instrument] = pd.Series(dtype=float)
                score_value = group.loc[(date, instrument), score_col]
                self._stock_predictions[instrument][date] = score_value

            # 记录Top-K股票列表
            if top_k is not None:
                top_stocks = group.nlargest(top_k, score_col)
                self._top_k_stocks_by_date[date] = set(
                    top_stocks.index.get_level_values(1).tolist()
                )  # ✅ 使用set提升查找速度

    def _normalize_stock_code(self, stock: Stock) -> str:
        """标准化股票代码格式(小写)"""
        return stock.market_code.lower()

    def _hikyuu_to_pandas_datetime(self, hikyuu_dt: Datetime) -> pd.Timestamp:
        """Hikyuu Datetime转pandas Timestamp"""
        return pd.Timestamp(
            year=hikyuu_dt.year,
            month=hikyuu_dt.month,
            day=hikyuu_dt.day,
            hour=hikyuu_dt.hour,
            minute=hikyuu_dt.minute,
        )

    def _build_kdata_date_index(self, kdata) -> Dict[pd.Timestamp, tuple]:
        """
        ✅ 性能优化: 预先构建K线日期索引

        Returns:
            dict: {pd_date: (k_index, k_datetime)}
        """
        cache_key = id(kdata)  # 使用kdata对象ID作为缓存key
        if cache_key in self._date_index_cache:
            return self._date_index_cache[cache_key]

        date_index = {}
        for i in range(len(kdata)):
            k_datetime = kdata[i].datetime
            pd_datetime = self._hikyuu_to_pandas_datetime(k_datetime)
            pd_date = pd_datetime.normalize()
            date_index[pd_date] = (i, k_datetime)

        self._date_index_cache[cache_key] = date_index
        return date_index

    def _is_in_top_k(self, stock_code: str, date: pd.Timestamp) -> bool:
        """
        ✅ 性能优化: 缓存的Top-K检查
        """
        cache_key = (stock_code, date)
        if cache_key in self._top_k_cache:
            return self._top_k_cache[cache_key]

        top_k_param = self.get_param("top_k")
        top_k = top_k_param if top_k_param != -1 else None

        if top_k is None:
            result = True
        else:
            result = (
                date in self._top_k_stocks_by_date
                and stock_code in self._top_k_stocks_by_date[date]
            )

        self._top_k_cache[cache_key] = result
        return result

    def _calculate(self, kdata):
        """
        [核心方法] 计算信号 - Hikyuu回调接口

        ✅ 性能优化版本:
        - 单次加载预测数据
        - 预先构建日期索引
        - 缓存Top-K查找
        - 直接在预测数据上迭代
        """
        # 1. 确保预测已加载
        if self._pred_df is None:
            self._load_predictions()

        # 2. 获取当前股票代码
        stock = kdata.get_stock()
        stock_code = self._normalize_stock_code(stock)

        # 3. 检查该股票是否有预测结果
        if stock_code not in self._stock_predictions:
            return

        # 4. 获取该股票的预测序列
        stock_pred_series = self._stock_predictions[stock_code]

        # 5. 获取阈值
        buy_threshold = self.get_param("buy_threshold")
        sell_threshold = self.get_param("sell_threshold")

        # ✅ 6. 预先构建K线日期索引(避免重复转换)
        date_index = self._build_kdata_date_index(kdata)

        # ✅ 7. 直接在预测数据上迭代(减少查找次数)
        for pred_date, pred_score in stock_pred_series.items():
            # 检查该日期是否在K线数据中
            if pred_date not in date_index:
                continue

            k_index, k_datetime = date_index[pred_date]

            # ✅ 8. 使用缓存的Top-K检查
            if not self._is_in_top_k(stock_code, pred_date):
                # 不在Top-K中,只生成卖出信号
                if pred_score < sell_threshold:
                    self._add_sell_signal(k_datetime)
                continue

            # 9. 根据阈值生成信号
            if pred_score > buy_threshold:
                self._add_buy_signal(k_datetime)
            elif pred_score < sell_threshold:
                self._add_sell_signal(k_datetime)

    def _reset(self):
        """复位内部状态"""
        self._pred_df = None
        self._stock_predictions.clear()
        self._top_k_stocks_by_date.clear()
        self._date_index_cache.clear()
        self._top_k_cache.clear()

    def _clone(self):
        """克隆信号指示器"""
        top_k_value = self.get_param("top_k")
        cloned = CustomSG_QlibFactorOptimized(
            pred_pkl_path=self.get_param("pred_pkl_path"),
            buy_threshold=self.get_param("buy_threshold"),
            sell_threshold=self.get_param("sell_threshold"),
            top_k=top_k_value if top_k_value != -1 else None,
            name=self.name,
        )
        cloned._pred_df = self._pred_df
        cloned._stock_predictions = self._stock_predictions.copy()
        cloned._top_k_stocks_by_date = self._top_k_stocks_by_date.copy()
        return cloned
