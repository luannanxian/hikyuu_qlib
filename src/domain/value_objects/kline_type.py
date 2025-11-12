"""
KLineType Value Object

K线类型值对象,遵循 DDD 值对象原则
"""

from enum import Enum


class KLineType(str, Enum):
    """
    K线类型枚举值对象

    值对象特征:
    - 不可变
    - 值相等性
    - 无副作用

    枚举值:
    - MIN_1: 1分钟K线
    - MIN_5: 5分钟K线
    - DAY: 日K线
    - WEEK: 周K线
    - MONTH: 月K线
    """

    MIN_1 = "1min"
    MIN_5 = "5min"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
