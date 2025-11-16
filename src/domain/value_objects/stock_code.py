"""
StockCode Value Object

股票代码值对象,遵循 DDD 值对象不可变性原则
"""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class StockCode:
    """
    股票代码值对象

    格式: {市场代码}{股票代码}
    - 上海: sh600000 (sh + 6位数字)
    - 深圳: sz000001 (sz + 6位数字)
    - 北京: bj430047 (bj + 6位数字)

    约束:
    - 总长度必须为 8 位
    - 市场代码必须为小写 sh/sz/bj
    - 股票代码必须为 6 位数字
    - 不可变 (frozen=True)
    """

    value: str

    def __post_init__(self):
        """验证股票代码格式"""
        if not self._is_valid():
            raise ValueError(
                f"Invalid stock code: {self.value}. "
                f"Expected format: [sh|sz|bj]XXXXXX (e.g., sh600000)",
            )

    def _is_valid(self) -> bool:
        """
        验证股票代码格式

        Returns:
            bool: 是否为合法股票代码
        """
        # 检查长度
        if len(self.value) != 8:
            return False

        # 检查格式: 市场代码(2位小写字母) + 股票代码(6位数字)
        pattern = r"^(sh|sz|bj)\d{6}$"
        return bool(re.match(pattern, self.value))

    def __str__(self) -> str:
        """字符串表示"""
        return self.value

    def __repr__(self) -> str:
        """调试表示"""
        return f"StockCode('{self.value}')"
