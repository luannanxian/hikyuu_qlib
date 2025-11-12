"""
HikyuuDataAdapter - Hikyuu 数据源适配器

适配 Hikyuu 框架实现 IStockDataProvider 接口
"""

from typing import List
from datetime import datetime
from decimal import Decimal

# 为了便于测试，将 hikyuu 作为模块级变量
try:
    import hikyuu
except ImportError:
    # 开发环境下 Mock hikyuu
    hikyuu = None

from domain.ports.stock_data_provider import IStockDataProvider
from domain.entities.kline_data import KLineData
from domain.value_objects.stock_code import StockCode
from domain.value_objects.date_range import DateRange
from domain.value_objects.kline_type import KLineType


class HikyuuDataAdapter(IStockDataProvider):
    """
    Hikyuu 数据源适配器

    实现 IStockDataProvider 接口,适配 Hikyuu 框架
    """

    def __init__(self, hikyuu_module=None):
        """
        初始化适配器

        Args:
            hikyuu_module: Hikyuu 模块实例（用于测试注入）
        """
        self.hikyuu = hikyuu_module if hikyuu_module is not None else hikyuu

    def _map_kline_type(self, kline_type: str):
        """
        映射 K线类型到 Hikyuu Query 类型

        Args:
            kline_type: 领域层 K线类型

        Returns:
            Hikyuu Query 类型
        """
        if self.hikyuu is None:
            return None

        mapping = {
            KLineType.MIN_1.value: self.hikyuu.Query.MIN,
            KLineType.MIN_5.value: self.hikyuu.Query.MIN5,
            KLineType.DAY.value: self.hikyuu.Query.DAY,
            KLineType.WEEK.value: self.hikyuu.Query.WEEK,
            KLineType.MONTH.value: self.hikyuu.Query.MONTH,
        }
        return mapping.get(kline_type, self.hikyuu.Query.DAY)

    def _convert_to_kline_data(
        self, hikyuu_record, stock_code: StockCode, kline_type: str
    ) -> KLineData:
        """
        转换 Hikyuu KRecord 到领域层 KLineData

        Args:
            hikyuu_record: Hikyuu KRecord 对象
            stock_code: 股票代码
            kline_type: K线类型

        Returns:
            KLineData: 领域层 K线数据
        """
        return KLineData(
            stock_code=stock_code,
            timestamp=hikyuu_record.datetime,
            kline_type=KLineType(kline_type),
            open=Decimal(str(hikyuu_record.open)),
            high=Decimal(str(hikyuu_record.high)),
            low=Decimal(str(hikyuu_record.low)),
            close=Decimal(str(hikyuu_record.close)),
            volume=int(hikyuu_record.volume),
            amount=Decimal(str(hikyuu_record.amount)),
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
            Exception: 当 Hikyuu API 调用失败时
        """
        try:
            # 获取 Hikyuu Stock 对象
            # Hikyuu 使用大写市场代码和股票代码
            market = stock_code.value[:2].upper()
            code = stock_code.value[2:]
            hikyuu_stock_code = f"{market}{code}"

            stock = self.hikyuu.Stock(hikyuu_stock_code)

            # 创建查询
            query_type = self._map_kline_type(kline_type)
            query = self.hikyuu.Query(query_type)

            # 获取 K线数据
            kdata = stock.get_kdata(query)

            # 转换为领域层数据
            result = []
            for record in kdata:
                # 过滤日期范围
                record_date = record.datetime.date()
                if date_range.contains(record_date):
                    kline = self._convert_to_kline_data(record, stock_code, kline_type)
                    result.append(kline)

            return result

        except Exception as e:
            # 将 Hikyuu 异常映射为领域层异常
            raise Exception(
                f"Failed to load stock data from Hikyuu: {stock_code.value}, {e}"
            ) from e

    async def get_stock_list(self, market: str) -> List[StockCode]:
        """
        获取股票列表

        Args:
            market: 市场代码 (SH/SZ/BJ)

        Returns:
            List[StockCode]: 股票代码列表

        Raises:
            Exception: 当 Hikyuu API 调用失败时
        """
        try:
            # 获取股票管理器
            sm = self.hikyuu.StockManager.instance()

            # 获取所有股票
            stocks = sm.get_stock_list()

            # 过滤并转换
            result = []
            for stock in stocks:
                if stock.market_code.upper() == market.upper():
                    # 转换为领域层 StockCode
                    code = f"{stock.market_code.lower()}{stock.code}"
                    try:
                        stock_code = StockCode(code)
                        result.append(stock_code)
                    except ValueError:
                        # 跳过无效股票代码
                        continue

            return result

        except Exception as e:
            raise Exception(f"Failed to get stock list from Hikyuu: {market}, {e}") from e
