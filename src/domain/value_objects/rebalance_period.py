"""
RebalancePeriod Value Object

调仓周期值对象,遵循 DDD 值对象原则
"""

from enum import Enum


class RebalancePeriod(str, Enum):
    """
    调仓周期枚举值对象

    值对象特征:
    - 不可变
    - 值相等性
    - 无副作用

    枚举值:
    - DAY: 每日调仓
    - WEEK: 每周调仓
    - MONTH: 每月调仓
    """

    DAY = "DAY"
    WEEK = "WEEK"
    MONTH = "MONTH"
