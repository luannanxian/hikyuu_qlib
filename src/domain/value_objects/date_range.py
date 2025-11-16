"""
DateRange Value Object

日期范围值对象,遵循 DDD 值对象不可变性原则
"""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class DateRange:
    """
    日期范围值对象

    约束:
    - start_date 必须 <= end_date
    - 不可变 (frozen=True)

    示例:
        >>> range1 = DateRange(date(2020, 1, 1), date(2020, 12, 31))
        >>> range1.contains(date(2020, 6, 15))
        True
    """

    start_date: date
    end_date: date

    def __post_init__(self):
        """验证日期范围有效性"""
        if self.start_date > self.end_date:
            raise ValueError(
                f"start_date must be <= end_date, "
                f"got start_date={self.start_date}, end_date={self.end_date}",
            )

    def contains(self, target_date: date) -> bool:
        """
        判断日期是否在范围内

        Args:
            target_date: 目标日期

        Returns:
            bool: 是否在范围内(包含边界)
        """
        return self.start_date <= target_date <= self.end_date

    def overlaps(self, other: "DateRange") -> bool:
        """
        判断两个日期范围是否重叠

        Args:
            other: 另一个日期范围

        Returns:
            bool: 是否重叠
        """
        # 不重叠的情况:一个范围完全在另一个之前或之后
        # 重叠的情况:取反
        return not (
            self.end_date < other.start_date or self.start_date > other.end_date
        )

    def duration_days(self) -> int:
        """
        计算持续天数

        Returns:
            int: 持续天数(包含起始日)
        """
        delta = self.end_date - self.start_date
        return delta.days + 1  # 包含起始日

    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.start_date} to {self.end_date}"

    def __repr__(self) -> str:
        """调试表示"""
        return f"DateRange(start_date={self.start_date}, end_date={self.end_date})"
