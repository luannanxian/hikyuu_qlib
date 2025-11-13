# Qlib Data Adapter

## 概述

`QlibDataAdapter` 是 Qlib 量化框架的适配器实现,将 Qlib 的数据接口适配到 Domain 层的 `IStockDataProvider` 接口。

## 架构位置

```
┌─────────────────────────────────────────────────────┐
│                   Use Cases                          │
│            (LoadStockDataUseCase)                    │
└─────────────────┬───────────────────────────────────┘
                  │ 依赖
                  ↓
┌─────────────────────────────────────────────────────┐
│              Domain Ports                            │
│          (IStockDataProvider)                        │
└─────────────────┬───────────────────────────────────┘
                  │ 实现
                  ↓
┌─────────────────────────────────────────────────────┐
│              Adapters Layer                          │
│          QlibDataAdapter ← 本层                      │
└─────────────────┬───────────────────────────────────┘
                  │ 调用
                  ↓
┌─────────────────────────────────────────────────────┐
│          External Framework                          │
│               Qlib Library                           │
└─────────────────────────────────────────────────────┘
```

## 核心职责

1. **数据格式转换**: Qlib DataFrame ↔ Domain KLineData
2. **接口适配**: 实现 `IStockDataProvider` 接口
3. **依赖隔离**: 隔离 Qlib 框架依赖在适配器层

## 技术特性

### 1. Qlib 数据结构

Qlib 使用 pandas MultiIndex DataFrame 存储 K 线数据:

```python
# Qlib DataFrame 结构
MultiIndex: (datetime, instrument)
Columns: ['$open', '$high', '$low', '$close', '$volume', '$amount']

# 示例数据
                        $open   $high    $low  $close   $volume      $amount
datetime   instrument                                                      
2023-01-03 SH600000     10.5    11.0    10.0    10.8  1000000.0  10800000.0
2023-01-04 SH600000     10.8    11.2    10.5    11.0  1100000.0  12100000.0
```

### 2. 数据类型映射

| Qlib 类型        | Domain 类型    | 说明                    |
|-----------------|---------------|------------------------|
| float           | Decimal       | 价格数据 (保证精度)      |
| int64           | int           | 成交量                  |
| pd.Timestamp    | datetime      | 时间戳                  |
| str (SH600000)  | StockCode     | 股票代码 (小写转换)      |

### 3. 股票代码格式转换

```python
# Domain → Qlib
StockCode("sh600000") → "SH600000"  # 转大写
StockCode("sz000001") → "SZ000001"

# Qlib → Domain
"SH600000" → StockCode("sh600000")  # 转小写
"SZ000001" → StockCode("sz000001")
```

## 使用示例

### 基本用法

```python
from adapters.qlib.qlib_data_adapter import QlibDataAdapter
from domain.value_objects.stock_code import StockCode
from domain.value_objects.date_range import DateRange
from domain.value_objects.kline_type import KLineType
from datetime import date

# 创建适配器
adapter = QlibDataAdapter()

# 加载股票数据
stock_code = StockCode("sh600000")
date_range = DateRange(
    start_date=date(2023, 1, 1),
    end_date=date(2023, 12, 31)
)

kline_data = await adapter.load_stock_data(
    stock_code=stock_code,
    date_range=date_range,
    kline_type=KLineType.DAY
)

# 结果: List[KLineData]
for kline in kline_data:
    print(f"{kline.timestamp}: {kline.close}")
```

### 获取股票列表

```python
# 获取上海市场所有股票
sh_stocks = await adapter.get_stock_list(market="SH")

# 结果: List[StockCode]
for stock_code in sh_stocks:
    print(stock_code.value)  # sh600000, sh600001, ...
```

### 测试模式 (Mock 注入)

```python
from unittest.mock import MagicMock

# 创建 Mock Qlib 模块
mock_qlib = MagicMock()
mock_qlib.data.D.features.return_value = mock_dataframe

# 注入 Mock
adapter = QlibDataAdapter(qlib_module=mock_qlib)

# 测试不依赖真实 Qlib 环境
result = await adapter.load_stock_data(...)
```

## 实现细节

### load_stock_data 流程

```
1. 转换格式
   Domain StockCode → Qlib instrument

2. 调用 Qlib API
   qlib.data.D.features(
       instruments=[instrument],
       fields=['$open', '$high', ...],
       start_time=start_date,
       end_time=end_date
   )

3. 处理空数据
   if df.empty: return []

4. 数据转换
   Qlib DataFrame → List[KLineData]
   - 重置 MultiIndex
   - 遍历行创建 KLineData 实体
   - 转换数据类型 (float→Decimal)

5. 返回结果
   return List[KLineData]
```

### get_stock_list 流程

```
1. 调用 Qlib API
   instruments = qlib.data.D.instruments()

2. 市场过滤
   filtered = [inst for inst in instruments 
               if inst.startswith(market)]

3. 格式转换
   Qlib "SH600000" → Domain StockCode("sh600000")

4. 返回结果
   return List[StockCode]
```

## 错误处理

所有 Qlib 异常都会被捕获并重新抛出包装后的异常:

```python
try:
    # Qlib 操作
    df = qlib.data.D.features(...)
except Exception as e:
    raise Exception(
        f"Failed to load stock data from Qlib: {stock_code.value}, {e}"
    ) from e
```

**异常类型**:
- `ImportError`: Qlib 未安装
- `Exception`: Qlib API 调用失败
- `Exception`: 数据格式转换失败

## 依赖项

```toml
[dependencies]
qlib = "^0.9.0"
pandas = "^2.0.0"
numpy = "^1.24.0"
```

**注意**: Qlib 是可选依赖,开发环境可以通过 Mock 注入进行测试。

## 测试覆盖率

- **覆盖率**: 85%
- **测试文件**: `tests/unit/adapters/qlib/test_qlib_data_adapter.py`
- **测试用例**: 7 个

### 测试用例列表

1. `test_load_stock_data_calls_qlib_api`: 验证 Qlib API 调用
2. `test_load_stock_data_converts_to_domain`: 验证数据格式转换
3. `test_load_stock_data_handles_qlib_error`: 验证错误处理
4. `test_load_stock_data_handles_empty_data`: 验证空数据处理
5. `test_get_stock_list_calls_qlib_api`: 验证股票列表获取
6. `test_load_stock_data_with_different_kline_types`: 验证不同 K 线类型
7. `test_stock_code_format_conversion`: 验证代码格式转换

## 性能考虑

### 数据量处理

- **单次查询**: 支持数万条 K 线数据
- **批量查询**: 建议分批加载 (按年份或季度)
- **内存占用**: DataFrame → List 转换有内存开销

### 优化建议

1. **分批加载**: 大数据量分多次查询
   ```python
   # 不推荐: 一次加载 10 年数据
   date_range = DateRange(date(2013, 1, 1), date(2023, 12, 31))
   
   # 推荐: 按年分批加载
   for year in range(2013, 2024):
       date_range = DateRange(date(year, 1, 1), date(year, 12, 31))
       kline_data = await adapter.load_stock_data(...)
   ```

2. **缓存机制**: 在 Use Case 层实现缓存
   ```python
   # Use Case 层缓存
   @lru_cache(maxsize=128)
   async def load_stock_data_cached(stock_code, date_range):
       return await adapter.load_stock_data(...)
   ```

## 与其他适配器对比

| 特性              | QlibDataAdapter      | HikyuuDataAdapter    |
|------------------|---------------------|---------------------|
| 数据结构          | DataFrame (pandas)   | KData (C++ 对象)    |
| 数据格式          | MultiIndex          | 迭代器              |
| 字段命名          | $ 前缀 ($open)      | 驼峰命名 (openPrice)|
| 查询接口          | D.features()        | Stock.getKData()    |
| 性能              | 中等 (Python)       | 高 (C++)            |
| 易用性            | 高 (pandas 生态)    | 中 (需要 Boost)     |

## 扩展功能

### 自定义字段

如需加载自定义因子字段:

```python
# 扩展 _convert_dataframe_to_domain 方法
def _convert_with_custom_fields(self, df, stock_code, kline_type):
    # 添加自定义字段
    fields = ['$open', '$high', '$low', '$close', '$volume', 
              '$factor1', '$factor2']  # 自定义因子
    
    # ... 转换逻辑
```

### 支持更多频率

当前支持日线 (freq='day'),可扩展:

```python
FREQ_MAPPING = {
    KLineType.MIN_1: '1min',
    KLineType.MIN_5: '5min',
    KLineType.DAY: 'day',
    KLineType.WEEK: 'week',
    KLineType.MONTH: 'month'
}
```

## 相关文档

- [IStockDataProvider Interface](../../domain/ports/stock_data_provider.py)
- [KLineData Entity](../../domain/entities/kline_data.py)
- [Qlib Official Documentation](https://qlib.readthedocs.io/)

## 版本历史

- **v1.0.0** (2025-11-12): 初始实现
  - 实现 `load_stock_data` 方法
  - 实现 `get_stock_list` 方法
  - 完成单元测试 (85% 覆盖率)

---

**维护者**: Development Team  
**最后更新**: 2025-11-12
