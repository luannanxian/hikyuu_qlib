"""
CustomSG_QlibFactor Adapter

基于Qlib预测结果的自定义Hikyuu信号指示器
职责:将Qlib预测转换为Hikyuu交易信号,同时实现ISignalProvider接口
"""

from datetime import datetime
from pathlib import Path

import pandas as pd

try:
    from hikyuu import Datetime, SignalBase, Stock
except ImportError:
    # 如果Hikyuu未安装,提供Mock类用于测试
    class SignalBase:
        def __init__(self, name: str):
            self.name = name
            self._params: dict = {}

        def setParam(self, name: str, value):
            self._params[name] = value

        def getParam(self, name: str):
            return self._params.get(name)

        def _addBuySignal(self, datetime):
            pass

        def _addSellSignal(self, datetime):
            pass

    class Datetime:
        def __init__(self, number: int):
            self.number = number

        def __str__(self):
            return str(self.number)

    class Stock:
        def __init__(self, market_code: str):
            self.market_code = market_code


from domain.entities.prediction import Prediction, PredictionBatch
from domain.entities.trading_signal import (
    SignalBatch,
    SignalStrength,
    SignalType,
    TradingSignal,
)
from domain.ports.signal_provider import ISignalProvider
from domain.value_objects.stock_code import StockCode


class CustomSG_QlibFactor(SignalBase, ISignalProvider):
    """
    基于Qlib预测结果的自定义信号指示器

    核心功能:
    1. 加载Qlib pred.pkl预测结果
    2. 提取当前股票的预测分数
    3. 基于阈值策略生成买入/卖出信号
    4. 处理时间戳对齐问题(日级别匹配)
    5. 支持Top-K选股策略

    实现接口:
    - SignalBase: Hikyuu信号指示器基类
    - ISignalProvider: 领域层信号提供者接口
    """

    def __init__(
        self,
        pred_pkl_path: str,
        buy_threshold: float = 0.02,
        sell_threshold: float = -0.02,
        top_k: int | None = None,
        name: str = "SG_QlibFactor",
    ):
        """
        初始化信号指示器

        Args:
            pred_pkl_path: Qlib预测结果文件路径(pred.pkl)
            buy_threshold: 买入阈值,预测分数 > buy_threshold时买入
            sell_threshold: 卖出阈值,预测分数 < sell_threshold时卖出
            top_k: Top-K选股,仅对预测分数排名前K的股票生成买入信号
            name: 信号指示器名称
        """
        super().__init__(name)

        # 私有属性(用于Hikyuu _calculate)
        self._pred_df: pd.DataFrame | None = None
        self._stock_predictions: dict[str, pd.Series] = {}
        self._top_k_stocks_by_date: dict[pd.Timestamp, list[str]] = {}

        # 缓存信号批次(用于ISignalProvider接口)
        self._cached_signal_batch: SignalBatch | None = None

        # 配置参数
        self.setParam("pred_pkl_path", pred_pkl_path)
        self.setParam("buy_threshold", buy_threshold)
        self.setParam("sell_threshold", sell_threshold)
        self.setParam("top_k", top_k)

    def _reset(self):
        """复位内部状态"""
        self._pred_df = None
        self._stock_predictions.clear()
        self._top_k_stocks_by_date.clear()
        self._cached_signal_batch = None

    def _clone(self):
        """克隆信号指示器"""
        cloned = CustomSG_QlibFactor(
            pred_pkl_path=self.getParam("pred_pkl_path"),
            buy_threshold=self.getParam("buy_threshold"),
            sell_threshold=self.getParam("sell_threshold"),
            top_k=self.getParam("top_k"),
            name=self.name,
        )
        cloned._pred_df = self._pred_df
        cloned._stock_predictions = self._stock_predictions.copy()
        cloned._top_k_stocks_by_date = self._top_k_stocks_by_date.copy()
        return cloned

    def _load_predictions(self):
        """
        加载Qlib预测结果

        Raises:
            FileNotFoundError: 预测文件不存在
            ValueError: 预测文件格式错误
        """
        if self._pred_df is not None:
            return

        pred_path = Path(self.getParam("pred_pkl_path"))
        if not pred_path.exists():
            raise FileNotFoundError(f"Prediction file not found: {pred_path}")

        # 加载pred.pkl
        self._pred_df = pd.read_pickle(pred_path)

        # 确保索引是MultiIndex(datetime, instrument)
        if not isinstance(self._pred_df.index, pd.MultiIndex):
            raise ValueError("pred.pkl must have MultiIndex(datetime, instrument)")

        if len(self._pred_df.index.levels) != 2:
            raise ValueError(
                f"pred.pkl must have 2-level MultiIndex, got {len(self._pred_df.index.levels)} levels",
            )

        # 获取分数列名
        score_col = self._detect_score_column()

        # 计算Top-K股票(如果指定)
        self._preprocess_predictions(score_col)

    def _detect_score_column(self) -> str:
        """
        检测预测分数列名

        Returns:
            str: 分数列名

        Raises:
            ValueError: 找不到分数列
        """
        possible_cols = ["score", "score_0", "pred", "prediction"]
        for col in possible_cols:
            if col in self._pred_df.columns:
                return col

        raise ValueError(
            f"Score column not found in pred.pkl. Available columns: {self._pred_df.columns.tolist()}",
        )

    def _preprocess_predictions(self, score_col: str):
        """
        预处理预测结果,计算Top-K股票

        Args:
            score_col: 预测分数列名
        """
        top_k = self.getParam("top_k")

        # 按日期分组处理
        for date, group in self._pred_df.groupby(level=0):
            # 确保date是pandas Timestamp并标准化为日级别
            date = pd.Timestamp(date).normalize()

            if top_k is not None:
                # 按预测分数排序,取Top-K
                top_stocks = group.nlargest(top_k, score_col)
                # 记录该日期的Top-K股票
                self._top_k_stocks_by_date[date] = top_stocks.index.get_level_values(
                    1,
                ).tolist()

                # 只存储Top-K股票的预测
                for instrument in top_stocks.index.get_level_values(1):
                    if instrument not in self._stock_predictions:
                        self._stock_predictions[instrument] = pd.Series(dtype=float)
                    score_value = group.loc[(date, instrument), score_col]
                    self._stock_predictions[instrument][date] = score_value
            else:
                # 如果不限制Top-K,存储所有股票预测
                for instrument in group.index.get_level_values(1):
                    if instrument not in self._stock_predictions:
                        self._stock_predictions[instrument] = pd.Series(dtype=float)
                    score_value = group.loc[(date, instrument), score_col]
                    self._stock_predictions[instrument][date] = score_value

    def _normalize_stock_code(self, stock: Stock) -> str:
        """
        标准化股票代码格式

        Hikyuu可能使用小写,Qlib使用大写
        例: sh600000 -> SH600000

        Args:
            stock: Hikyuu Stock对象

        Returns:
            str: 标准化的股票代码
        """
        market_code = stock.market_code
        return market_code.upper()

    def _hikyuu_to_pandas_datetime(self, hq_datetime: Datetime) -> pd.Timestamp:
        """
        将Hikyuu Datetime转换为pandas Timestamp

        Args:
            hq_datetime: Hikyuu Datetime对象 (格式: YYYYMMDDHHmm)

        Returns:
            pandas Timestamp
        """
        dt_str = str(hq_datetime.number)

        # 确保至少有8位(YYYYMMdd)
        if len(dt_str) < 8:
            dt_str = dt_str.zfill(12)  # 补齐到12位

        year = int(dt_str[:4])
        month = int(dt_str[4:6])
        day = int(dt_str[6:8])
        hour = int(dt_str[8:10]) if len(dt_str) >= 10 else 0
        minute = int(dt_str[10:12]) if len(dt_str) >= 12 else 0

        return pd.Timestamp(year=year, month=month, day=day, hour=hour, minute=minute)

    def _pandas_to_hikyuu_datetime(self, pd_timestamp: pd.Timestamp) -> Datetime:
        """
        将pandas Timestamp转换为Hikyuu Datetime

        Args:
            pd_timestamp: pandas Timestamp

        Returns:
            Hikyuu Datetime对象
        """
        dt_number = (
            pd_timestamp.year * 100000000
            + pd_timestamp.month * 1000000
            + pd_timestamp.day * 10000
            + pd_timestamp.hour * 100
            + pd_timestamp.minute
        )
        return Datetime(dt_number)

    def _calculate(self, kdata):
        """
        [核心方法] 计算信号 - Hikyuu回调接口

        Args:
            kdata: Hikyuu KData对象,包含股票的K线数据
        """
        # 1. 加载预测结果
        self._load_predictions()

        # 2. 获取当前股票代码
        stock = kdata.getStock()
        stock_code = self._normalize_stock_code(stock)

        # 3. 检查该股票是否有预测结果
        if stock_code not in self._stock_predictions:
            # 没有预测结果,不生成信号
            return

        # 4. 获取该股票的预测序列
        stock_pred_series = self._stock_predictions[stock_code]

        # 5. 获取阈值
        buy_threshold = self.getParam("buy_threshold")
        sell_threshold = self.getParam("sell_threshold")
        top_k = self.getParam("top_k")

        # 6. 遍历K线数据,匹配预测结果
        for i in range(len(kdata)):
            k_datetime = kdata[i].datetime

            # 转换为pandas Timestamp(日期对齐)
            pd_datetime = self._hikyuu_to_pandas_datetime(k_datetime)
            pd_date = pd_datetime.normalize()  # 只保留日期部分

            # 查找该日期的预测分数
            if pd_date not in stock_pred_series.index:
                continue

            pred_score = stock_pred_series[pd_date]

            # 7. Top-K过滤(仅对买入信号生效)
            if (
                top_k is not None
                and pd_date in self._top_k_stocks_by_date
                and stock_code not in self._top_k_stocks_by_date[pd_date]
            ):
                # 不在Top-K中,只生成卖出信号,不生成买入信号
                if pred_score < sell_threshold:
                    self._addSellSignal(k_datetime)
                continue

            # 8. 根据阈值生成信号
            if pred_score > buy_threshold:
                # 买入信号
                self._addBuySignal(k_datetime)
            elif pred_score < sell_threshold:
                # 卖出信号
                self._addSellSignal(k_datetime)

    # ========== ISignalProvider Interface Implementation ==========

    def generate_signals_from_predictions(
        self,
        prediction_batch: PredictionBatch,
        buy_threshold: float = 0.02,
        sell_threshold: float = -0.02,
        top_k: int | None = None,
    ) -> SignalBatch:
        """
        从预测批次生成交易信号批次

        Args:
            prediction_batch: 预测结果批次
            buy_threshold: 买入阈值
            sell_threshold: 卖出阈值
            top_k: Top-K选股

        Returns:
            SignalBatch: 交易信号批次
        """
        # 创建信号批次
        signal_batch = SignalBatch(
            strategy_name=f"QlibFactor_{prediction_batch.model_id}",
            batch_date=prediction_batch.generated_at,
        )

        # 按日期分组预测
        predictions_by_date: dict[datetime, list[Prediction]] = {}
        for pred in prediction_batch.predictions:
            date_key = pred.timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
            if date_key not in predictions_by_date:
                predictions_by_date[date_key] = []
            predictions_by_date[date_key].append(pred)

        # 处理每个日期的预测
        for date, preds in predictions_by_date.items():
            # 按预测值排序
            sorted_preds = sorted(preds, key=lambda p: p.predicted_value, reverse=True)

            # 应用Top-K
            if top_k is not None:
                top_k_preds = sorted_preds[:top_k]
            else:
                top_k_preds = sorted_preds

            # 生成信号
            for pred in preds:
                signal_type = SignalType.HOLD
                signal_strength = SignalStrength.MEDIUM

                # 判断信号类型
                if pred.predicted_value > buy_threshold:
                    # 检查是否在Top-K中
                    if top_k is None or pred in top_k_preds:
                        signal_type = SignalType.BUY
                        # 根据预测值确定信号强度
                        if pred.predicted_value > buy_threshold * 2:
                            signal_strength = SignalStrength.STRONG
                        elif pred.predicted_value > buy_threshold * 1.5:
                            signal_strength = SignalStrength.MEDIUM
                        else:
                            signal_strength = SignalStrength.WEAK
                elif pred.predicted_value < sell_threshold:
                    signal_type = SignalType.SELL
                    # 根据预测值确定信号强度
                    if pred.predicted_value < sell_threshold * 2:
                        signal_strength = SignalStrength.STRONG
                    elif pred.predicted_value < sell_threshold * 1.5:
                        signal_strength = SignalStrength.MEDIUM
                    else:
                        signal_strength = SignalStrength.WEAK

                # 创建交易信号
                signal = TradingSignal(
                    stock_code=pred.stock_code,
                    signal_date=date,
                    signal_type=signal_type,
                    signal_strength=signal_strength,
                    reason=f"pred_value={pred.predicted_value:.4f}",
                )

                signal_batch.add_signal(signal)

        # 缓存信号批次
        self._cached_signal_batch = signal_batch

        return signal_batch

    def get_signal_for_stock(
        self,
        stock_code: StockCode,
        signal_date: datetime,
    ) -> TradingSignal | None:
        """
        获取指定股票在指定日期的交易信号

        Args:
            stock_code: 股票代码
            signal_date: 信号日期

        Returns:
            Optional[TradingSignal]: 交易信号,如果不存在则返回None
        """
        # 如果有缓存的信号批次,直接查询
        if self._cached_signal_batch is not None:
            return self._cached_signal_batch.get_signal(stock_code, signal_date)

        # 否则,从预测数据动态生成信号
        self._load_predictions()

        stock_code_str = stock_code.value.upper()
        if stock_code_str not in self._stock_predictions:
            return None

        stock_pred_series = self._stock_predictions[stock_code_str]
        date_key = pd.Timestamp(signal_date).normalize()

        if date_key not in stock_pred_series.index:
            return None

        pred_score = stock_pred_series[date_key]
        buy_threshold = self.getParam("buy_threshold")
        sell_threshold = self.getParam("sell_threshold")

        # 判断信号类型
        signal_type = SignalType.HOLD
        if pred_score > buy_threshold:
            signal_type = SignalType.BUY
        elif pred_score < sell_threshold:
            signal_type = SignalType.SELL

        # 创建信号
        return TradingSignal(
            stock_code=stock_code,
            signal_date=signal_date,
            signal_type=signal_type,
            reason=f"pred_value={pred_score:.4f}",
        )

    def get_top_k_stocks(
        self,
        prediction_batch: PredictionBatch,
        k: int,
    ) -> list[StockCode]:
        """
        从预测批次中选出Top-K股票

        Args:
            prediction_batch: 预测结果批次
            k: 选股数量

        Returns:
            List[StockCode]: Top-K股票代码列表(按预测值降序)
        """
        # 按预测值降序排序
        sorted_predictions = sorted(
            prediction_batch.predictions,
            key=lambda p: p.predicted_value,
            reverse=True,
        )

        # 取前K个,去重(同一股票可能有多个时间点的预测)
        top_k_stocks = []
        seen_stocks = set()

        for pred in sorted_predictions:
            if pred.stock_code not in seen_stocks:
                top_k_stocks.append(pred.stock_code)
                seen_stocks.add(pred.stock_code)

            if len(top_k_stocks) >= k:
                break

        return top_k_stocks
