"""股票数据提供者端口"""

from abc import ABC, abstractmethod

from domain.entities.kline_data import KLineData
from domain.value_objects.date_range import DateRange
from domain.value_objects.stock_code import StockCode


class IStockDataProvider(ABC):
    """股票数据提供者接口"""

    @abstractmethod
    async def load_stock_data(
        self, stock_code: StockCode, date_range: DateRange, kline_type: str,
    ) -> list[KLineData]:
        """加载股票数据"""

    @abstractmethod
    async def get_stock_list(self, market: str) -> list[StockCode]:
        """获取股票列表"""
