"""
Market Value Object

市场值对象,遵循 DDD 值对象不可变性原则
"""

from dataclasses import dataclass
from typing import Dict


# 市场名称映射(模块级常量)
_MARKET_NAMES: Dict[str, str] = {
    "SH": "上海证券交易所",
    "SZ": "深圳证券交易所",
    "BJ": "北京证券交易所",
}


@dataclass(frozen=True)
class Market:
    """
    市场值对象

    支持的市场:
    - SH: 上海证券交易所
    - SZ: 深圳证券交易所
    - BJ: 北京证券交易所

    约束:
    - 市场代码必须为 SH/SZ/BJ (不区分大小写)
    - 不可变 (frozen=True)
    """

    code: str

    def __post_init__(self):
        """验证并标准化市场代码"""
        # 标准化为大写
        normalized_code = self.code.upper()

        # 验证市场代码
        if normalized_code not in _MARKET_NAMES:
            raise ValueError(
                f"Invalid market code: {self.code}. "
                f"Supported markets: {', '.join(_MARKET_NAMES.keys())}"
            )

        # 使用 object.__setattr__ 绕过 frozen 限制,标准化 code
        object.__setattr__(self, "code", normalized_code)

    @property
    def name(self) -> str:
        """
        获取市场名称

        Returns:
            str: 市场中文名称
        """
        return _MARKET_NAMES[self.code]

    def is_mainland_china(self) -> bool:
        """
        判断是否为中国大陆市场

        Returns:
            bool: 是否为中国大陆市场
        """
        return self.code in ("SH", "SZ", "BJ")

    def __str__(self) -> str:
        """字符串表示"""
        return self.code

    def __repr__(self) -> str:
        """调试表示"""
        return f"Market('{self.code}')"
