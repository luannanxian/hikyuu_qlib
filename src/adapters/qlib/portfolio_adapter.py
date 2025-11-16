"""
Qlib Portfolio Adapter

将 Qlib 预测结果适配到组合管理层
实现动态股票池、调仓逻辑等核心功能
"""

from pathlib import Path

import pandas as pd

from domain.value_objects.date_range import DateRange
from domain.value_objects.rebalance_period import RebalancePeriod
from domain.value_objects.stock_code import StockCode


class QlibPortfolioAdapter:
    """
    Qlib → Hikyuu Portfolio 适配器

    核心功能:
    1. 读取 Qlib pred.pkl 预测结果
    2. 计算每日 Top-K 股票
    3. 生成动态股票池
    4. 管理调仓逻辑

    性能优化:
    - 预计算所有日期的 Top-K 股票 (在 __init__ 中)
    - 缓存结果到 _top_k_cache
    - 避免重复计算

    技术细节:
    - Qlib pred.pkl 格式: MultiIndex DataFrame (datetime, instrument)
    - 预测分数列名: 'score'
    - Domain 集成: 使用 DateRange, StockCode, RebalancePeriod
    """

    def __init__(
        self,
        pred_pkl_path: str,
        top_k: int = 10,
        rebalance_period: str = "WEEK",
    ):
        """
        初始化 Qlib Portfolio 适配器

        Args:
            pred_pkl_path: Qlib 预测结果文件路径 (pred.pkl)
            top_k: 选择 Top-K 股票数量
            rebalance_period: 调仓周期 (DAY, WEEK, MONTH)

        Raises:
            FileNotFoundError: pred.pkl 文件不存在
            ValueError: pred.pkl 格式不正确或参数无效
        """
        # 验证参数
        self._validate_init_params(pred_pkl_path, top_k, rebalance_period)

        self.pred_pkl_path = pred_pkl_path
        self.top_k = top_k
        self.rebalance_period = RebalancePeriod(rebalance_period)

        # 预测数据
        self._pred_df: pd.DataFrame = None

        # Top-K 缓存 (性能优化)
        self._top_k_cache: dict[pd.Timestamp, list[str]] = {}

        # 加载预测结果
        self._load_predictions()

        # 预计算所有日期的 Top-K (性能优化)
        self._precompute_top_k()

    def _validate_init_params(
        self,
        pred_pkl_path: str,
        top_k: int,
        rebalance_period: str,
    ) -> None:
        """
        验证初始化参数

        Args:
            pred_pkl_path: 预测文件路径
            top_k: Top-K 数量
            rebalance_period: 调仓周期

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 参数无效
        """
        # 验证文件存在
        if not Path(pred_pkl_path).exists():
            raise FileNotFoundError(f"pred.pkl not found: {pred_pkl_path}")

        # 验证 top_k
        if not isinstance(top_k, int) or top_k <= 0:
            raise ValueError(f"top_k must be positive integer, got: {top_k}")

        # 验证 rebalance_period
        valid_periods = [p.value for p in RebalancePeriod]
        if rebalance_period not in valid_periods:
            raise ValueError(
                f"Invalid rebalance_period: {rebalance_period}. "
                f"Must be one of {valid_periods}",
            )

    def _load_predictions(self) -> None:
        """
        加载 Qlib 预测结果

        Raises:
            ValueError: pred.pkl 格式不正确
        """
        try:
            self._pred_df = pd.read_pickle(self.pred_pkl_path)
        except Exception as e:
            raise ValueError(
                f"Failed to load pred.pkl: {self.pred_pkl_path}",
            ) from e

        # 验证 DataFrame 格式
        if not isinstance(self._pred_df.index, pd.MultiIndex):
            raise ValueError(
                "pred.pkl must have MultiIndex(datetime, instrument) format",
            )

        # 验证必须有 'score' 列
        if 'score' not in self._pred_df.columns:
            raise ValueError("pred.pkl must contain 'score' column")

        # 验证至少有一条数据
        if self._pred_df.empty:
            raise ValueError("pred.pkl contains no data")

    def _precompute_top_k(self) -> None:
        """
        预计算所有日期的 Top-K 股票 (性能优化)

        遍历所有交易日,计算每日 Top-K 股票,存入缓存
        """
        # 获取所有唯一日期
        all_dates = self._pred_df.index.get_level_values(0).unique()

        # 对每个日期计算 Top-K
        for date in all_dates:
            try:
                # 获取该日期的所有预测
                date_predictions = self._pred_df.loc[date]

                # 选出 Top-K 股票
                top_k_stocks = date_predictions.nlargest(
                    self.top_k,
                    'score',
                )

                # 存入缓存
                self._top_k_cache[date] = top_k_stocks.index.tolist()

            except (KeyError, AttributeError):
                # 某些日期可能没有数据,跳过
                continue

    def get_dynamic_stock_pool(
        self,
        date_range: DateRange,
    ) -> dict[pd.Timestamp, list[StockCode]]:
        """
        获取动态股票池

        根据调仓周期,返回每个调仓日的 Top-K 股票列表

        Args:
            date_range: 日期范围

        Returns:
            {调仓日期: [Top-K StockCode 列表]}

        Example:
            >>> adapter = QlibPortfolioAdapter("pred.pkl", top_k=5, rebalance_period="WEEK")
            >>> date_range = DateRange(date(2023, 1, 1), date(2023, 1, 31))
            >>> stock_pool = adapter.get_dynamic_stock_pool(date_range)
            >>> # {Timestamp('2023-01-02'): [StockCode('sh600000'), ...], ...}
        """
        stock_pool = {}

        # 获取调仓日期列表
        rebalance_dates = self._get_rebalance_dates(date_range)

        # 对每个调仓日,从缓存中获取 Top-K 股票
        for rebalance_date in rebalance_dates:
            if rebalance_date in self._top_k_cache:
                # 转换为 StockCode 对象
                stock_codes = [
                    StockCode(code.lower())
                    for code in self._top_k_cache[rebalance_date]
                ]
                stock_pool[rebalance_date] = stock_codes

        return stock_pool

    def _get_rebalance_dates(
        self,
        date_range: DateRange,
    ) -> list[pd.Timestamp]:
        """
        获取调仓日期列表

        根据调仓周期,从所有交易日中筛选出调仓日期

        Args:
            date_range: 日期范围

        Returns:
            调仓日期列表 (按时间升序)

        调仓规则:
        - DAY: 所有交易日
        - WEEK: 每周第一个交易日
        - MONTH: 每月第一个交易日
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
        if self.rebalance_period == RebalancePeriod.DAY:
            return sorted(dates_in_range.tolist())

        elif self.rebalance_period == RebalancePeriod.WEEK:
            # 每周第一个交易日
            df = pd.DataFrame({'date': dates_in_range})
            df['week'] = df['date'].dt.isocalendar().week
            df['year'] = df['date'].dt.year

            rebalance_dates = df.groupby(['year', 'week'])['date'].first()
            return sorted(rebalance_dates.tolist())

        elif self.rebalance_period == RebalancePeriod.MONTH:
            # 每月第一个交易日
            df = pd.DataFrame({'date': dates_in_range})
            df['month'] = df['date'].dt.to_period('M')

            rebalance_dates = df.groupby('month')['date'].first()
            return sorted(rebalance_dates.tolist())

        else:
            # 不应该到达这里 (已在初始化时验证)
            raise ValueError(
                f"Unsupported rebalance_period: {self.rebalance_period}",
            )

    def get_all_stocks(self) -> list[StockCode]:
        """
        获取所有出现过的股票列表

        Returns:
            所有 StockCode 列表 (去重,不保证顺序)

        Example:
            >>> adapter = QlibPortfolioAdapter("pred.pkl")
            >>> all_stocks = adapter.get_all_stocks()
            >>> # [StockCode('sh600000'), StockCode('sz000001'), ...]
        """
        all_instruments = self._pred_df.index.get_level_values(1).unique().tolist()

        # 转换为 StockCode 对象
        stock_codes = [
            StockCode(inst.lower())
            for inst in all_instruments
        ]

        return stock_codes

    def get_stock_weight(
        self,
        date: pd.Timestamp,
        stock_code: StockCode,
    ) -> float:
        """
        获取某只股票在某日期的权重

        权重计算:
        - Top-K 股票: 等权重 (1.0 / top_k)
        - 非 Top-K 股票: 0.0

        Args:
            date: 日期 (pandas Timestamp)
            stock_code: 股票代码

        Returns:
            权重 (0.0 ~ 1.0)

        Example:
            >>> adapter = QlibPortfolioAdapter("pred.pkl", top_k=10)
            >>> weight = adapter.get_stock_weight(
            ...     pd.Timestamp('2023-01-03'),
            ...     StockCode('sh600000')
            ... )
            >>> # 0.1 (if in Top-10) or 0.0 (if not)
        """
        # 从缓存中获取 Top-K 股票
        if date not in self._top_k_cache:
            return 0.0

        top_k_stocks = self._top_k_cache[date]

        # 转换 StockCode 到 Qlib instrument 格式 (大写)
        instrument = stock_code.value.upper()

        # 判断是否在 Top-K 中
        if instrument in top_k_stocks:
            # 等权重
            return 1.0 / self.top_k
        else:
            return 0.0
