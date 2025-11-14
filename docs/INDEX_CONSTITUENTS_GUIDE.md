# 指数成分股获取指南

本指南说明如何使用 `utils.index_constituents` 模块获取指数成分股。

## 功能概述

该模块提供了获取指数成分股的工具函数，支持：
- 沪深300、中证500、上证50等主要指数
- 693个指数板块，包括概念、行业、地域等分类
- 返回 StockCode 对象或字符串代码
- 搜索和列出可用指数

## 快速开始

### 1. 获取沪深300成分股

```python
from utils.index_constituents import get_hs300

# 获取沪深300成分股（返回 StockCode 对象）
stocks = get_hs300()
print(f"沪深300成分股数量: {len(stocks)}")  # 300

# 遍历成分股
for stock in stocks[:10]:
    print(stock.value)  # sh600000, sh600009, ...
```

### 2. 使用通用函数获取任意指数

```python
from utils.index_constituents import get_index_constituents

# 获取中证500
zz500 = get_index_constituents("中证500")
print(f"中证500成分股数量: {len(zz500)}")  # 424

# 获取上证50
sz50 = get_index_constituents("上证50")
print(f"上证50成分股数量: {len(sz50)}")  # 50

# 获取创业板50
cyb50 = get_index_constituents("创业板50")
print(f"创业板50成分股数量: {len(cyb50)}")  # 50

# 返回字符串代码而非 StockCode 对象
codes = get_index_constituents("沪深300", return_stock_codes=False)
print(codes[:5])  # ['sh600000', 'sh600009', 'sh600010', 'sh600011', 'sh600015']
```

### 3. 搜索指数

```python
from utils.index_constituents import search_indices

# 搜索包含"300"的指数
indices = search_indices("300")
print(f"找到 {len(indices)} 个指数")

for name, count in indices[:10]:
    print(f"{name}: {count}只")

# 输出示例:
# 300分层: 300只
# 300等权: 300只
# 上证F300: 300只
# 沪深300: 300只
# 国证300: 281只
```

### 4. 列出所有可用指数

```python
from utils.index_constituents import list_available_indices

# 获取所有指数及成分股数量
all_indices = list_available_indices()
print(f"共 {len(all_indices)} 个指数")

for name, count in all_indices[:20]:
    print(f"{name}: {count}只")
```

## API 参考

### 主要函数

#### `get_index_constituents(index_name, category="指数板块", return_stock_codes=True)`

获取指数成分股列表

**参数:**
- `index_name` (str): 指数名称，如 "沪深300", "中证500", "上证50"
- `category` (str): 板块类别，默认 "指数板块"
  - "指数板块": 指数成分股
  - "概念板块": 概念板块
  - "行业板块": 行业板块
  - "地域板块": 地域板块
- `return_stock_codes` (bool): 是否返回 StockCode 对象，False 则返回字符串代码

**返回:**
- `List[StockCode]` 或 `List[str]`: 成分股代码列表

#### `search_indices(keyword, category="指数板块")`

搜索包含关键词的指数

**参数:**
- `keyword` (str): 搜索关键词
- `category` (str): 板块类别

**返回:**
- `List[tuple[str, int]]`: (指数名称, 成分股数量) 列表

#### `list_available_indices(category="指数板块")`

列出所有可用指数

**参数:**
- `category` (str): 板块类别

**返回:**
- `List[tuple[str, int]]`: (指数名称, 成分股数量) 列表

### 快捷函数

以下函数提供了常用指数的快捷访问：

```python
from utils.index_constituents import (
    get_hs300,    # 沪深300
    get_zz500,    # 中证500
    get_sz50,     # 上证50
    get_cyb50,    # 创业板50
    get_kc50,     # 科创50
)
```

## 实际应用示例

### 1. 批量加载指数成分股数据

```python
from utils.index_constituents import get_hs300
from use_cases.data.load_stock_data import LoadStockDataUseCase
from domain.value_objects.date_range import DateRange
from domain.value_objects.kline_type import KLineType
from datetime import datetime

# 获取沪深300成分股
hs300 = get_hs300()

# 批量加载数据
date_range = DateRange(
    start_date=datetime(2023, 1, 1),
    end_date=datetime(2023, 12, 31)
)

for stock_code in hs300:
    try:
        data = await load_use_case.execute(
            stock_code=stock_code,
            date_range=date_range,
            kline_type=KLineType.DAY
        )
        print(f"{stock_code.value}: {len(data)} 条记录")
    except Exception as e:
        print(f"{stock_code.value}: 加载失败 - {e}")
```

### 2. 创建指数组合

```python
from utils.index_constituents import get_hs300, get_zz500

# 获取沪深300和中证500
hs300 = set(s.value for s in get_hs300())
zz500 = set(s.value for s in get_zz500())

# 找出只在中证500中的股票（不在沪深300中）
zz500_only = zz500 - hs300
print(f"仅在中证500中的股票: {len(zz500_only)}只")

# 找出同时在两个指数中的股票
overlap = hs300 & zz500
print(f"同时在沪深300和中证500中的股票: {len(overlap)}只")
```

### 3. 按指数训练模型

```python
from utils.index_constituents import get_hs300
from utils.data_conversion import convert_kline_to_training_data

# 获取沪深300成分股
hs300_stocks = get_hs300()

# 为每只股票准备训练数据
all_training_data = []
for stock_code in hs300_stocks:
    # 加载K线数据
    kline_data = await load_data_use_case.execute(...)

    # 转换为训练数据
    training_data = convert_kline_to_training_data(
        kline_data,
        add_features=True,
        add_labels=True
    )
    all_training_data.append(training_data)

# 合并所有数据用于训练
combined_data = pd.concat(all_training_data, ignore_index=True)
print(f"总训练数据: {len(combined_data)} 条")
```

### 4. CLI 命令示例

可以在 CLI 命令中集成指数成分股功能：

```bash
# 为沪深300所有成分股下载数据（需要实现相应的CLI命令）
./run_cli.sh data load-index --index hs300 \
    --start 2023-01-01 --end 2023-12-31 \
    --output data/hs300_2023.csv

# 使用沪深300数据训练模型
./run_cli.sh model train-index --index hs300 \
    --type LGBM --name hs300_model \
    --start 2023-01-01 --end 2023-12-31
```

## 数据源

指数成分股数据来自 Hikyuu 的 MySQL 数据库，存储在以下表中：
- `block`: 板块成分股明细表
- `BlockIndex`: 板块索引表

数据库配置位于 `config/hikyuu.ini` 的 `[block]` 部分。

## 可用指数列表

系统支持 693 个指数，主要类别包括：

**主要指数:**
- 沪深300 (300只)
- 中证500 (424只)
- 上证50 (50只)
- 创业板50 (50只)
- 科创50 (50只)

**行业指数:**
- 沪深300医药卫生指数
- 沪深300信息技术指数
- 沪深300金融地产指数
- 沪深300工业指数
- 等等...

**风格指数:**
- 300价值
- 300成长
- 300红利
- 300低波
- 等等...

完整指数列表可以通过 `list_available_indices()` 查看。

## 注意事项

1. **数据库连接**: 当前直接连接 MySQL (192.168.3.46)，生产环境建议从配置文件读取
2. **指数名称**: 必须使用准确的指数名称，如 "沪深300" 而非 "HS300"
3. **成分股更新**: 指数成分股会定期调整，请注意数据的时效性
4. **性能**: 批量查询时建议使用数据库连接池

## 测试

运行测试脚本验证功能：

```bash
python3 test_index_constituents.py
```

该脚本会：
1. 搜索包含"300"的指数
2. 获取沪深300成分股
3. 获取主要指数成分股数量
4. 列出所有可用指数

## 相关文档

- [MODEL_TRAINING_DATA_LOADING_GUIDE.md](MODEL_TRAINING_DATA_LOADING_GUIDE.md) - 模型训练数据加载指南
- [PROJECT_CONFIG_FINAL_REPORT.md](PROJECT_CONFIG_FINAL_REPORT.md) - 项目配置集成报告

## 更新日志

### 2025-11-13
- 初始版本
- 实现基本的指数成分股获取功能
- 支持沪深300、中证500等主要指数
- 提供搜索和列表功能
