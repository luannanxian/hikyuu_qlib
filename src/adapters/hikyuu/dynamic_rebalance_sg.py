"""
Dynamic Rebalance Signal Generator for Hikyuu

动态调仓信号器,根据 Qlib Top-K 预测结果生成买卖信号
"""

from typing import Set, Protocol
import pandas as pd

try:
    from hikyuu import SignalBase, Datetime
except ImportError:
    # For testing without Hikyuu installed
    class SignalBase:
        """Mock SignalBase for testing"""
        def __init__(self, name: str = "SG_Mock"):
            self._name = name

        def _addBuySignal(self, datetime):
            """Mock buy signal"""
            pass

        def _addSellSignal(self, datetime):
            """Mock sell signal"""
            pass

        def _reset(self):
            """Mock reset"""
            pass

    class Datetime:
        """Mock Datetime for testing"""
        def __init__(self, number: int):
            self.number = number


from domain.value_objects.date_range import DateRange


class PortfolioAdapterProtocol(Protocol):
    """
    Portfolio Adapter Protocol

    定义 DynamicRebalanceSG 需要的 Portfolio Adapter 接口
    """

    def get_dynamic_stock_pool(
        self,
        date_range: DateRange
    ) -> dict[pd.Timestamp, list[str]]:
        """
        获取动态股票池

        Args:
            date_range: 日期范围

        Returns:
            {日期: [Top-K 股票列表]}
        """
        ...

    def _get_rebalance_dates(
        self,
        date_range: DateRange
    ) -> list[pd.Timestamp]:
        """
        获取调仓日期列表

        Args:
            date_range: 日期范围

        Returns:
            调仓日期列表
        """
        ...


class DynamicRebalanceSG(SignalBase):
    """
    动态调仓信号器

    功能:
    1. 根据 Qlib Top-K 结果动态调仓
    2. 在调仓日买入新进入 Top-K 的股票
    3. 在调仓日卖出退出 Top-K 的股票

    信号生成逻辑:
    - BUY 信号: 股票进入 Top-K 且当前未持有
    - SELL 信号: 股票退出 Top-K 且当前持有

    使用示例:
        >>> portfolio_adapter = QlibPortfolioAdapter("pred.pkl", top_k=10)
        >>> sg = DynamicRebalanceSG(portfolio_adapter)
        >>> # 在 Hikyuu 回测系统中使用
        >>> sys = System()
        >>> sys.sg = sg

    属性:
        portfolio_adapter: Portfolio 适配器,提供 Top-K 股票池
        _current_holdings: 当前持仓集合,用于跟踪持仓状态
    """

    def __init__(
        self,
        portfolio_adapter: PortfolioAdapterProtocol,
        name: str = "SG_DynamicRebalance"
    ):
        """
        初始化动态调仓信号器

        Args:
            portfolio_adapter: Portfolio 适配器实例
            name: 信号器名称
        """
        super().__init__(name)
        self.portfolio_adapter = portfolio_adapter
        self._current_holdings: Set[str] = set()

    def _calculate(self, kdata) -> None:
        """
        计算信号

        Args:
            kdata: Hikyuu K线数据对象

        处理流程:
        1. 获取股票代码
        2. 获取调仓日期列表
        3. 遍历 K线数据,在调仓日检查 Top-K 变化
        4. 生成买入/卖出信号
        """
        if not kdata or len(kdata) == 0:
            return

        stock = kdata.getStock()
        stock_code = stock.market_code  # 格式: SH600000

        # 获取调仓日期
        rebalance_dates = self.portfolio_adapter._get_rebalance_dates(
            DateRange(
                start_date=kdata[0].datetime.date(),
                end_date=kdata[-1].datetime.date()
            )
        )

        # 转换为集合以加速查找
        rebalance_dates_set = set(rebalance_dates)

        # 遍历 K线数据
        for i in range(len(kdata)):
            k_datetime = kdata[i].datetime
            pd_datetime = self._hikyuu_to_pandas_datetime(k_datetime)

            # 检查是否为调仓日
            if pd_datetime not in rebalance_dates_set:
                continue

            # 获取该日期的 Top-K 股票池
            top_k_stocks = self.portfolio_adapter.get_dynamic_stock_pool(
                DateRange(pd_datetime.date(), pd_datetime.date())
            ).get(pd_datetime, [])

            # 买入信号: 进入 Top-K 且当前未持有
            if stock_code in top_k_stocks and stock_code not in self._current_holdings:
                self._addBuySignal(k_datetime)
                self._current_holdings.add(stock_code)

            # 卖出信号: 退出 Top-K 且当前持有
            elif stock_code not in top_k_stocks and stock_code in self._current_holdings:
                self._addSellSignal(k_datetime)
                self._current_holdings.discard(stock_code)

    def _reset(self) -> None:
        """
        重置信号器状态

        在回测重新运行时调用,清空持仓状态
        """
        super()._reset()
        self._current_holdings.clear()

    def _clone(self) -> "DynamicRebalanceSG":
        """
        克隆信号器

        Returns:
            新的信号器实例
        """
        return DynamicRebalanceSG(
            portfolio_adapter=self.portfolio_adapter,
            name=self._name
        )

    def _hikyuu_to_pandas_datetime(self, hq_datetime: Datetime) -> pd.Timestamp:
        """
        转换 Hikyuu Datetime 到 pandas Timestamp

        Hikyuu 时间格式: YYYYMMDDHHmm (如 202301011500)
        pandas Timestamp: 标准时间戳 (只保留日期部分)

        Args:
            hq_datetime: Hikyuu Datetime 对象

        Returns:
            pandas Timestamp (日期部分)

        示例:
            >>> hq_dt = Datetime(202301011500)
            >>> pd_dt = self._hikyuu_to_pandas_datetime(hq_dt)
            >>> print(pd_dt)
            2023-01-01 00:00:00
        """
        dt_str = str(hq_datetime.number)

        # 提取年月日
        year = int(dt_str[:4])
        month = int(dt_str[4:6])
        day = int(dt_str[6:8])

        # 返回日期级别的时间戳(00:00:00)
        return pd.Timestamp(year=year, month=month, day=day)

    def get_current_holdings(self) -> Set[str]:
        """
        获取当前持仓

        Returns:
            当前持仓股票代码集合

        注意:
            此方法主要用于测试和调试
        """
        return self._current_holdings.copy()
