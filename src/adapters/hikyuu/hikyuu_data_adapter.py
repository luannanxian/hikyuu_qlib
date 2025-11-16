"""
HikyuuDataAdapter - Hikyuu 数据适配器

适配 Hikyuu 框架实现 IStockDataProvider 接口
"""

from decimal import Decimal
from pathlib import Path

# 条件导入 Hikyuu - 便于测试和开发
try:
    import hikyuu as hku
    from hikyuu import hikyuu_init
    HIKYUU_AVAILABLE = True
except ImportError:
    # Hikyuu 未安装
    hku = None
    hikyuu_init = None
    HIKYUU_AVAILABLE = False

from domain.entities.kline_data import KLineData
from domain.ports.stock_data_provider import IStockDataProvider
from domain.value_objects.date_range import DateRange
from domain.value_objects.kline_type import KLineType
from domain.value_objects.stock_code import StockCode


class HikyuuDataAdapter(IStockDataProvider):
    """
    Hikyuu 数据适配器

    实现 IStockDataProvider 接口,适配 Hikyuu 框架
    """

    def __init__(self, hikyuu_module=None, config_file: str | None = None):
        """
        初始化适配器

        Args:
            hikyuu_module: Hikyuu 模块实例（用于测试注入）
            config_file: Hikyuu 配置文件路径（如果不指定，使用默认配置）

        Raises:
            ImportError: 当 Hikyuu 未安装且未提供测试模块时
            FileNotFoundError: 当配置文件不存在时
        """
        # 测试注入优先
        if hikyuu_module is not None:
            self.hku = hikyuu_module
        else:
            # 生产环境必须有 Hikyuu
            if not HIKYUU_AVAILABLE:
                raise ImportError(
                    "Hikyuu library is required but not installed.\n"
                    "Please install it using one of the following methods:\n"
                    "  • pip install hikyuu\n"
                    "  • conda install -c conda-forge hikyuu\n"
                    "\n"
                    "For more information, visit: https://hikyuu.org",
                )

            if hku is None:
                raise RuntimeError(
                    "Hikyuu import succeeded but module is None. "
                    "This may indicate a broken installation.",
                )

            self.hku = hku

        # 如果指定了配置文件且 Hikyuu 可用，初始化 Hikyuu
        if config_file and self.hku is not None and hikyuu_init is not None:
            config_path = Path(config_file)
            if config_path.exists():
                hikyuu_init(str(config_path))
            else:
                raise FileNotFoundError(f"Hikyuu config file not found: {config_file}")

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
        self, krecord, stock_code: StockCode, kline_type: KLineType,
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
            open=Decimal(str(krecord.open)),
            high=Decimal(str(krecord.high)),
            low=Decimal(str(krecord.low)),
            close=Decimal(str(krecord.close)),
            volume=int(krecord.volume),
            amount=Decimal(str(krecord.amount)),
        )

    async def load_stock_data(
        self, stock_code: StockCode, date_range: DateRange, kline_type: str,
    ) -> list[KLineData]:
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
            # 解析股票代码: "sh600000" -> market="sh", code="600000"
            code_value = stock_code.value.lower()
            if code_value.startswith("sh"):
                market = "sh"
                code = code_value[2:]
            elif code_value.startswith("sz"):
                market = "sz"
                code = code_value[2:]
            else:
                raise ValueError(f"Invalid stock code format: {code_value}")

            # 使用 StockManager 获取股票对象
            sm = self.hku.StockManager.instance()
            stock = sm.get_stock(f"{market}{code}")

            query = self._build_query(date_range, kline_type)

            # 2. 调用 Hikyuu API
            kdata = stock.get_kdata(query)

            # 3. Hikyuu → Domain 转换
            result = []
            for krecord in kdata:
                domain_kline = self._convert_krecord_to_domain(
                    krecord, stock_code, kline_type,
                )
                result.append(domain_kline)

            return result

        except Exception as e:
            raise Exception(
                f"Failed to load stock data from Hikyuu: {stock_code.value}, {e}",
            ) from e

    async def get_stock_list(self, market: str) -> list[StockCode]:
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
                f"Failed to get stock list from Hikyuu: {market}, {e}",
            ) from e
