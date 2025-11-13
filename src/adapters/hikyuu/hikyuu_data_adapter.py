"""
HikyuuDataAdapter - Hikyuu 数据适配器

适配 Hikyuu 框架实现 IStockDataProvider 接口
"""

from datetime import datetime
from decimal import Decimal
from typing import List

# 条件导入 Hikyuu - 便于测试和开发
try:
    import hikyuu as hku
except ImportError:
    # 开发环境下 Mock hikyuu
    hku = None

from domain.ports.stock_data_provider import IStockDataProvider
from domain.value_objects.stock_code import StockCode
from domain.value_objects.date_range import DateRange
from domain.value_objects.kline_type import KLineType
from domain.entities.kline_data import KLineData


class HikyuuDataAdapter(IStockDataProvider):
    """
    Hikyuu 数据适配器

    实现 IStockDataProvider 接口,适配 Hikyuu 框架
    """

    def __init__(self, hikyuu_module=None):
        """
        初始化适配器

        Args:
            hikyuu_module: Hikyuu 模块实例（用于测试注入）
        """
        self.hku = hikyuu_module if hikyuu_module is not None else hku

    def _map_kline_type_to_hikyuu(self, kline_type: KLineType) -> int:
        """
        映射领域层 KLineType 到 Hikyuu K线类型

        Args:
            kline_type: 领域层 K线类型

        Returns:
            Hikyuu K线类型常量
        """
        mapping = {
            KLineType.MIN_1: self.hku.Query.MIN,
            KLineType.MIN_5: self.hku.Query.MIN5,
            KLineType.DAY: self.hku.Query.DAY,
            KLineType.WEEK: self.hku.Query.WEEK,
            KLineType.MONTH: self.hku.Query.MONTH,
        }
        return mapping.get(kline_type, self.hku.Query.DAY)

    def _build_query(self, date_range: DateRange, kline_type: KLineType):
        """
        构建 Hikyuu Query 对象

        Args:
            date_range: 日期范围
            kline_type: K线类型

        Returns:
            Hikyuu Query 对象
        """
        hikyuu_ktype = self._map_kline_type_to_hikyuu(kline_type)

        # 构建 Query
        query = self.hku.Query(
            start=self.hku.Datetime(
                date_range.start_date.year,
                date_range.start_date.month,
                date_range.start_date.day,
            ),
            end=self.hku.Datetime(
                date_range.end_date.year,
                date_range.end_date.month,
                date_range.end_date.day,
            ),
            ktype=hikyuu_ktype,
        )

        return query

    def _convert_krecord_to_domain(
        self, krecord, stock_code: StockCode, kline_type: KLineType
    ) -> KLineData:
        """
        将 Hikyuu KRecord 转换为 Domain KLineData

        Args:
            krecord: Hikyuu KRecord 对象
            stock_code: 股票代码
            kline_type: K线类型

        Returns:
            Domain KLineData 实体
        """
        return KLineData(
            stock_code=stock_code,
            timestamp=krecord.datetime,
            kline_type=kline_type,
            open=Decimal(str(krecord.openPrice)),
            high=Decimal(str(krecord.highPrice)),
            low=Decimal(str(krecord.lowPrice)),
            close=Decimal(str(krecord.closePrice)),
            volume=int(krecord.volume),
            amount=Decimal(str(krecord.amount)),
        )

    async def load_stock_data(
        self, stock_code: StockCode, date_range: DateRange, kline_type: str
    ) -> List[KLineData]:
        """
        加载股票数据

        Args:
            stock_code: 股票代码
            date_range: 日期范围
            kline_type: K线类型

        Returns:
            List[KLineData]: K线数据列表

        Raises:
            Exception: 当 Hikyuu 加载失败时
        """
        try:
            # 1. Domain → Hikyuu 转换
            stock = self.hku.Stock(stock_code.value)
            query = self._build_query(date_range, kline_type)

            # 2. 调用 Hikyuu API
            kdata = stock.getKData(query)

            # 3. Hikyuu → Domain 转换
            result = []
            for krecord in kdata:
                domain_kline = self._convert_krecord_to_domain(
                    krecord, stock_code, kline_type
                )
                result.append(domain_kline)

            return result

        except Exception as e:
            raise Exception(
                f"Failed to load stock data from Hikyuu: {stock_code.value}, {e}"
            ) from e

    async def get_stock_list(self, market: str) -> List[StockCode]:
        """
        获取股票列表

        Args:
            market: 市场代码 (如 "SH", "SZ")

        Returns:
            List[StockCode]: 股票代码列表

        Raises:
            Exception: 当 Hikyuu 加载失败时
        """
        try:
            # 1. 获取 StockManager
            sm = self.hku.StockManager.instance()

            # 2. 遍历所有股票,过滤指定市场
            result = []
            for stock in sm:
                if stock.market_code == market.upper():
                    # 构建 StockCode (market_code + code)
                    code_value = f"{market.lower()}{stock.code}"
                    result.append(StockCode(code_value))

            return result

        except Exception as e:
            raise Exception(
                f"Failed to get stock list from Hikyuu: {market}, {e}"
            ) from e
