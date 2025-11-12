"""
QlibDataAdapter - Qlib 数据源适配器

适配 Qlib 框架实现 IStockDataProvider 接口
"""

from typing import List
from decimal import Decimal

# 为了便于测试，使用条件导入
try:
    from qlib.data import D
except ImportError:
    # 开发环境下 Mock qlib
    D = None

from domain.ports.stock_data_provider import IStockDataProvider
from domain.entities.kline_data import KLineData
from domain.value_objects.stock_code import StockCode
from domain.value_objects.date_range import DateRange
from domain.value_objects.kline_type import KLineType


class QlibDataAdapter(IStockDataProvider):
    """
    Qlib 数据源适配器

    实现 IStockDataProvider 接口,适配 Qlib 框架
    """

    def __init__(self, qlib_data_module=None):
        """
        初始化适配器

        Args:
            qlib_data_module: Qlib 数据模块实例（用于测试注入）
        """
        self.D = qlib_data_module if qlib_data_module is not None else D

    def _convert_stock_code_to_qlib_format(self, stock_code: StockCode) -> str:
        """
        转换股票代码为 Qlib 格式

        Args:
            stock_code: 领域层股票代码 (如 sh600000)

        Returns:
            Qlib 格式股票代码 (如 SH600000)
        """
        # sh600000 → SH600000
        market = stock_code.value[:2].upper()
        code = stock_code.value[2:]
        return f"{market}{code}"

    def _convert_to_kline_data(
        self, row, stock_code: StockCode, kline_type: str
    ) -> KLineData:
        """
        转换 Qlib DataFrame 行到领域层 KLineData

        Args:
            row: Qlib DataFrame 行
            stock_code: 股票代码
            kline_type: K线类型

        Returns:
            KLineData: 领域层 K线数据
        """
        return KLineData(
            stock_code=stock_code,
            timestamp=row.name.to_pydatetime(),  # Qlib uses DatetimeIndex
            kline_type=KLineType(kline_type),
            open=Decimal(str(row["$open"])),
            high=Decimal(str(row["$high"])),
            low=Decimal(str(row["$low"])),
            close=Decimal(str(row["$close"])),
            volume=int(row["$volume"]),
            amount=Decimal(str(row["$amount"])),
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
            Exception: 当 Qlib API 调用失败时
        """
        try:
            # 转换股票代码格式
            qlib_stock_code = self._convert_stock_code_to_qlib_format(stock_code)

            # 转换日期范围
            start_time = date_range.start_date.strftime("%Y-%m-%d")
            end_time = date_range.end_date.strftime("%Y-%m-%d")

            # Qlib 特征列表
            fields = ["$open", "$high", "$low", "$close", "$volume", "$amount"]

            # 调用 Qlib API
            df = self.D.features(
                instruments=[qlib_stock_code],
                fields=fields,
                start_time=start_time,
                end_time=end_time,
            )

            # 转换为领域层数据
            result = []
            if df is not None and not df.empty:
                for idx, row in df.iterrows():
                    kline = self._convert_to_kline_data(row, stock_code, kline_type)
                    result.append(kline)

            return result

        except Exception as e:
            # 将 Qlib 异常映射为领域层异常
            raise Exception(
                f"Failed to load stock data from Qlib: {stock_code.value}, {e}"
            ) from e

    async def get_stock_list(self, market: str) -> List[StockCode]:
        """
        获取股票列表

        Args:
            market: 市场代码 (SH/SZ/BJ)

        Returns:
            List[StockCode]: 股票代码列表

        Raises:
            Exception: 当 Qlib API 调用失败时
        """
        try:
            # Qlib 使用不同的市场代码格式
            # 获取所有股票列表
            instruments = self.D.instruments(market=market.upper())

            # 转换为领域层 StockCode
            result = []
            for instrument in instruments:
                # Qlib 格式: SH600000 → 领域层格式: sh600000
                market_code = instrument[:2].lower()
                code = instrument[2:]
                try:
                    stock_code = StockCode(f"{market_code}{code}")
                    result.append(stock_code)
                except ValueError:
                    # 跳过无效股票代码
                    continue

            return result

        except Exception as e:
            raise Exception(f"Failed to get stock list from Qlib: {market}, {e}") from e
