"""
LoadStockDataUseCase - 加载股票数据用例

UC-001: Load Stock Data (加载股票数据)
"""


from domain.entities.kline_data import KLineData
from domain.ports.stock_data_provider import IStockDataProvider
from domain.value_objects.date_range import DateRange
from domain.value_objects.kline_type import KLineType
from domain.value_objects.stock_code import StockCode


class LoadStockDataUseCase:
    """
    加载股票数据用例

    依赖注入:
    - provider: IStockDataProvider (股票数据提供者接口)

    职责:
    - 协调数据加载流程
    - 验证输入参数(通过Value Objects)
    - 调用数据提供者Port
    - 返回领域对象列表
    """

    def __init__(self, provider: IStockDataProvider):
        """
        初始化用例

        Args:
            provider: 股票数据提供者接口实现
        """
        self.provider = provider

    async def execute(
        self,
        stock_code: StockCode,
        date_range: DateRange,
        kline_type: KLineType,
    ) -> list[KLineData]:
        """
        执行加载股票数据

        Args:
            stock_code: 股票代码值对象
            date_range: 日期范围值对象
            kline_type: K线类型

        Returns:
            List[KLineData]: K线数据列表

        Raises:
            Exception: 数据源错误时传播异常
        """
        # 1. 输入验证由Value Objects保证(StockCode, DateRange已在创建时验证)

        # 2. 调用数据提供者Port加载数据
        kline_data_list = await self.provider.load_stock_data(
            stock_code=stock_code, date_range=date_range, kline_type=kline_type,
        )

        # 3. 返回领域对象列表(可能为空列表)
        return kline_data_list
