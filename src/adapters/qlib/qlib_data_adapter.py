"""
Qlib Data Adapter

将 Qlib 数据框架适配到 Domain 层 IStockDataProvider 接口
实现六边形架构的适配器模式
"""

from decimal import Decimal

import pandas as pd

from domain.entities.kline_data import KLineData
from domain.ports.stock_data_provider import IStockDataProvider
from domain.value_objects.date_range import DateRange
from domain.value_objects.stock_code import StockCode

# 条件导入 Qlib (开发环境可能没有安装)
try:
    import qlib
    from qlib.data import D
except ImportError:
    qlib = None
    D = None


class QlibDataAdapter(IStockDataProvider):
    """
    Qlib 数据适配器

    职责:
    - 将 Qlib DataFrame 转换为 Domain KLineData
    - 实现 IStockDataProvider 接口
    - 隔离 Qlib 框架依赖

    技术细节:
    - Qlib 使用 MultiIndex DataFrame (datetime, instrument)
    - Qlib 字段名使用 $ 前缀 (如 $open, $close)
    - Domain 使用 Decimal 类型存储价格
    """

    def __init__(self, qlib_module=None):
        """
        初始化 Qlib 数据适配器

        Args:
            qlib_module: 可选的 qlib 模块注入 (用于测试 Mock)
        """
        if qlib_module is not None:
            self.qlib = qlib_module
        else:
            if qlib is None:
                raise ImportError(
                    "Qlib is not installed. Install with: pip install qlib",
                )
            self.qlib = qlib

    async def load_stock_data(
        self,
        stock_code: StockCode,
        date_range: DateRange,
        kline_type: str,
    ) -> list[KLineData]:
        """
        从 Qlib 加载股票 K 线数据

        Args:
            stock_code: Domain 股票代码 (如 sh600000)
            date_range: 日期范围
            kline_type: K 线类型 (DAY, WEEK, MONTH, etc.)

        Returns:
            KLineData 实体列表

        Raises:
            Exception: Qlib 数据加载失败
        """
        try:
            # 1. 转换 Domain 格式到 Qlib 格式
            qlib_instrument = self._convert_stock_code_to_qlib(stock_code)
            qlib_fields = ['$open', '$high', '$low', '$close', '$volume', '$amount']

            # 2. 调用 Qlib API 获取数据
            df = self.qlib.data.D.features(
                instruments=[qlib_instrument],
                fields=qlib_fields,
                start_time=date_range.start_date,
                end_time=date_range.end_date,
                freq='day',  # Qlib 频率参数
            )

            # 3. 处理空数据
            if df is None or df.empty:
                return []

            # 4. 转换 Qlib DataFrame 到 Domain KLineData
            result = self._convert_dataframe_to_domain(
                df, stock_code, kline_type,
            )

            return result

        except Exception as e:
            raise Exception(
                f"Failed to load stock data from Qlib: {stock_code.value}, {e}",
            ) from e

    async def get_stock_list(self, market: str) -> list[StockCode]:
        """
        获取指定市场的股票列表

        Args:
            market: 市场代码 (SH, SZ, BJ)

        Returns:
            StockCode 列表

        Raises:
            Exception: 获取股票列表失败
        """
        try:
            # 1. 调用 Qlib API 获取所有股票
            instruments = self.qlib.data.D.instruments()

            # 2. 过滤指定市场
            market_upper = market.upper()
            filtered_instruments = [
                inst for inst in instruments
                if inst.upper().startswith(market_upper)
            ]

            # 3. 转换为 Domain StockCode
            stock_codes = [
                StockCode(inst.lower())
                for inst in filtered_instruments
            ]

            return stock_codes

        except Exception as e:
            raise Exception(
                f"Failed to get stock list from Qlib: {market}, {e}",
            ) from e

    # =========================================================================
    # 辅助方法: Domain ↔ Qlib 格式转换
    # =========================================================================

    def _convert_stock_code_to_qlib(self, stock_code: StockCode) -> str:
        """
        转换 Domain StockCode 到 Qlib instrument 格式

        Domain: sh600000 → Qlib: SH600000
        Domain: sz000001 → Qlib: SZ000001

        Args:
            stock_code: Domain 股票代码

        Returns:
            Qlib instrument 字符串
        """
        return stock_code.value.upper()

    def _convert_dataframe_to_domain(
        self,
        df: pd.DataFrame,
        stock_code: StockCode,
        kline_type: str,
    ) -> list[KLineData]:
        """
        转换 Qlib DataFrame 到 Domain KLineData 列表

        Qlib DataFrame 格式:
        - MultiIndex: (datetime, instrument)
        - Columns: $open, $high, $low, $close, $volume, $amount

        Args:
            df: Qlib DataFrame
            stock_code: Domain 股票代码
            kline_type: K 线类型

        Returns:
            KLineData 实体列表
        """
        result = []

        # 重置索引以便访问 datetime
        df_reset = df.reset_index()

        for _, row in df_reset.iterrows():
            # 提取时间戳
            timestamp = row['datetime']
            if isinstance(timestamp, pd.Timestamp):
                timestamp = timestamp.to_pydatetime()

            # 创建 KLineData 实体
            kline = KLineData(
                stock_code=stock_code,
                timestamp=timestamp,
                kline_type=kline_type,
                open=Decimal(str(row['$open'])),
                high=Decimal(str(row['$high'])),
                low=Decimal(str(row['$low'])),
                close=Decimal(str(row['$close'])),
                volume=int(row['$volume']),
                amount=Decimal(str(row['$amount'])),
            )

            result.append(kline)

        return result
