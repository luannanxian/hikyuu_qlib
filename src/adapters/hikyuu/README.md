# Hikyuu Adapter

Hikyuu 数据适配器,实现 `IStockDataProvider` 接口。

## 功能

- ✅ 加载股票 K线数据 (支持日/周/月/分钟线)
- ✅ 获取市场股票列表
- ✅ 数据格式转换 (Hikyuu ↔ Domain)
- ✅ 错误处理和异常包装
- ✅ 测试覆盖率: **96%**

## 使用示例

```python
from adapters.hikyuu.hikyuu_data_adapter import HikyuuDataAdapter
from domain.value_objects.stock_code import StockCode
from domain.value_objects.date_range import DateRange
from domain.value_objects.kline_type import KLineType
from datetime import date

# 创建适配器
adapter = HikyuuDataAdapter()

# 加载K线数据
stock_code = StockCode("sh600000")
date_range = DateRange(start_date=date(2023, 1, 1), end_date=date(2023, 12, 31))

kline_data = await adapter.load_stock_data(
    stock_code=stock_code,
    date_range=date_range,
    kline_type=KLineType.DAY
)

# 获取股票列表
sh_stocks = await adapter.get_stock_list(market="SH")
```

## 架构设计

### 六边形架构

```
Domain (核心)
    ↑
    | IStockDataProvider (端口)
    ↑
HikyuuDataAdapter (适配器)
    ↓
Hikyuu Framework (外部框架)
```

### 数据转换

**Hikyuu KRecord → Domain KLineData:**

| Hikyuu 字段    | Domain 字段  | 转换逻辑                  |
|---------------|-------------|-------------------------|
| datetime      | timestamp   | 直接映射                  |
| openPrice     | open        | 转换为 Decimal           |
| highPrice     | high        | 转换为 Decimal           |
| lowPrice      | low         | 转换为 Decimal           |
| closePrice    | close       | 转换为 Decimal           |
| volume        | volume      | 转换为 int               |
| amount        | amount      | 转换为 Decimal           |

### K线类型映射

| Domain KLineType | Hikyuu Query Type |
|-----------------|-------------------|
| MIN_1           | Query.MIN         |
| MIN_5           | Query.MIN5        |
| DAY             | Query.DAY         |
| WEEK            | Query.WEEK        |
| MONTH           | Query.MONTH       |

## 测试

运行单元测试:

```bash
python -m pytest tests/unit/adapters/hikyuu/test_hikyuu_data_adapter.py -v
```

查看测试覆盖率:

```bash
python -m pytest tests/unit/adapters/hikyuu/test_hikyuu_data_adapter.py --cov=adapters.hikyuu.hikyuu_data_adapter --cov-report=term-missing
```

## 依赖

- `hikyuu`: Hikyuu C++ Python 绑定库
- 如果 Hikyuu 未安装,适配器会优雅降级 (用于测试和开发)

## 开发

### TDD 流程

本适配器严格遵循 TDD Red-Green-Refactor 流程开发:

1. 🔴 **RED**: 编写失败的测试
2. 🟢 **GREEN**: 实现最小功能让测试通过
3. 🔵 **REFACTOR**: 重构和优化代码

### 设计原则

- ✅ 依赖反转: 依赖 Domain 接口,不是具体实现
- ✅ 单一职责: 只负责 Hikyuu 数据适配
- ✅ 开闭原则: 对扩展开放,对修改关闭
- ✅ 可测试性: 依赖注入支持,便于单元测试

## 许可证

待定
