"""
Index Constituents Utilities

提供获取指数成分股的工具函数
"""

from typing import List, Optional
import hikyuu as hku
from domain.value_objects.stock_code import StockCode


def get_index_constituents(
    index_name: str,
    category: str = "指数板块",
    return_stock_codes: bool = True
) -> List[StockCode] | List[str]:
    """
    获取指数成分股列表

    Args:
        index_name: 指数名称，如 "沪深300", "中证500", "上证50" 等
        category: 板块类别，默认 "指数板块"
        return_stock_codes: 是否返回 StockCode 对象，False 则返回字符串代码

    Returns:
        List[StockCode] 或 List[str]: 成分股代码列表

    Examples:
        >>> # 获取沪深300成分股
        >>> stocks = get_index_constituents("沪深300")
        >>> print(f"沪深300成分股数量: {len(stocks)}")

        >>> # 获取上证50成分股
        >>> stocks = get_index_constituents("上证50")

        >>> # 返回字符串代码
        >>> stock_codes = get_index_constituents("沪深300", return_stock_codes=False)
    """
    # 直接使用数据库查询，因为 Hikyuu API 的板块功能可能未加载
    return get_index_constituents_from_db(
        index_name, category, return_stock_codes
    )


def get_index_constituents_from_db(
    index_name: str,
    category: str = "指数板块",
    return_stock_codes: bool = True
) -> List[StockCode] | List[str]:
    """
    从 MySQL 数据库直接获取指数成分股

    Args:
        index_name: 指数名称
        category: 板块类别
        return_stock_codes: 是否返回 StockCode 对象

    Returns:
        成分股代码列表
    """
    import pymysql

    # 连接数据库（后续可以改为从配置读取）
    conn = pymysql.connect(
        host='192.168.3.46',
        port=3306,
        user='remote',
        password='remote123456',
        database='hku_base'
    )

    try:
        cursor = conn.cursor()

        # 查询成分股代码
        cursor.execute("""
            SELECT DISTINCT market_code
            FROM block
            WHERE category = %s AND name = %s
            ORDER BY market_code
        """, (category, index_name))

        rows = cursor.fetchall()

        stocks = []
        for (market_code,) in rows:
            # market_code 格式: SH600000, SZ000001
            code_str = market_code.lower()  # sh600000, sz000001
            if return_stock_codes:
                stocks.append(StockCode(code_str))
            else:
                stocks.append(code_str)

        return stocks

    finally:
        conn.close()


def list_available_indices(category: str = "指数板块") -> List[tuple[str, int]]:
    """
    列出可用的指数及其成分股数量

    Args:
        category: 板块类别，默认 "指数板块"

    Returns:
        List[tuple[str, int]]: (指数名称, 成分股数量) 列表

    Examples:
        >>> indices = list_available_indices()
        >>> for name, count in indices[:10]:
        ...     print(f"{name}: {count}只")
    """
    import pymysql

    conn = pymysql.connect(
        host='192.168.3.46',
        port=3306,
        user='remote',
        password='remote123456',
        database='hku_base'
    )

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT name, COUNT(DISTINCT market_code) as count
            FROM block
            WHERE category = %s
            GROUP BY name
            ORDER BY name
        """, (category,))

        return cursor.fetchall()

    finally:
        conn.close()


def search_indices(keyword: str, category: str = "指数板块") -> List[tuple[str, int]]:
    """
    搜索包含关键词的指数

    Args:
        keyword: 搜索关键词
        category: 板块类别

    Returns:
        List[tuple[str, int]]: (指数名称, 成分股数量) 列表

    Examples:
        >>> # 搜索所有包含"300"的指数
        >>> indices = search_indices("300")
        >>> for name, count in indices:
        ...     print(f"{name}: {count}只")
    """
    import pymysql

    conn = pymysql.connect(
        host='192.168.3.46',
        port=3306,
        user='remote',
        password='remote123456',
        database='hku_base'
    )

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT name, COUNT(DISTINCT market_code) as count
            FROM block
            WHERE category = %s AND name LIKE %s
            GROUP BY name
            ORDER BY count DESC, name
        """, (category, f"%{keyword}%"))

        return cursor.fetchall()

    finally:
        conn.close()


# 常用指数快捷函数

def get_hs300() -> List[StockCode]:
    """获取沪深300成分股"""
    return get_index_constituents("沪深300")


def get_zz500() -> List[StockCode]:
    """获取中证500成分股"""
    return get_index_constituents("中证500")


def get_sz50() -> List[StockCode]:
    """获取上证50成分股"""
    return get_index_constituents("上证50")


def get_cyb50() -> List[StockCode]:
    """获取创业板50成分股"""
    return get_index_constituents("创业板50")


def get_kc50() -> List[StockCode]:
    """获取科创50成分股"""
    return get_index_constituents("科创50")
