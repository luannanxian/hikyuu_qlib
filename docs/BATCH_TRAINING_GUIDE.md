# 指数成分股批量训练指南

本指南说明如何使用指数成分股进行批量训练模型。

## 功能概述

系统支持对指数成分股（如沪深300的300只股票）进行批量训练：
1. 自动获取指数的所有成分股
2. 批量加载每只股票的历史数据
3. 合并所有数据为一个大型训练集
4. 使用合并后的数据训练模型

## 快速开始

### 1. 使用 CLI 命令训练

```bash
# 训练沪深300（所有300只股票）
./run_cli.sh model train-index \
    --type LGBM \
    --name hs300_model \
    --index 沪深300 \
    --start 2023-01-01 \
    --end 2023-12-31

# 训练中证500
./run_cli.sh model train-index \
    --type LGBM \
    --name zz500_model \
    --index 中证500 \
    --start 2023-01-01 \
    --end 2023-12-31

# 训练上证50
./run_cli.sh model train-index \
    --type LGBM \
    --name sz50_model \
    --index 上证50 \
    --start 2023-01-01 \
    --end 2023-12-31
```

### 2. 测试模式（使用少量股票）

```bash
# 使用前10只股票快速测试
./run_cli.sh model train-index \
    --type LGBM \
    --name hs300_test \
    --index 沪深300 \
    --start 2023-01-01 \
    --end 2023-12-31 \
    --max-stocks 10
```

### 3. 实际测试结果

```bash
$ ./run_cli.sh model train-index --type LGBM --name hs300_test_3 \
    --index 沪深300 --start 2023-01-01 --end 2023-12-31 --max-stocks 3

======================================================================
在 沪深300 成分股上训练 LGBM 模型
======================================================================
开始加载 沪深300 成分股数据...
  成分股数量: 3
  日期范围: 2023-01-01 ~ 2023-12-31

加载完成: 3 成功, 0 失败
合并后总数据量: 546 条

开始训练模型...
  训练数据量: 546 条
  特征数: 27 列

模型训练成功!
  模型ID: a48231a8-7539-4ab9-bcb3-fd7201808833
  状态: TRAINED
  指标:
    train_r2: 0.586
    test_r2: -0.108
    train_rmse: 0.0082
    test_rmse: 0.0127
```

## 命令参数说明

### `model train-index` 命令

```bash
./run_cli.sh model train-index [OPTIONS]
```

**必需参数:**
- `--type <MODEL_TYPE>`: 模型类型 (LGBM, MLP, LSTM, GRU, TRANSFORMER)
- `--name <NAME>`: 模型名称
- `--index <INDEX>`: 指数名称，如 "沪深300", "中证500", "上证50"
- `--start <DATE>`: 开始日期 (格式: YYYY-MM-DD)
- `--end <DATE>`: 结束日期 (格式: YYYY-MM-DD)

**可选参数:**
- `--kline-type <TYPE>`: K线类型 (DAY, WEEK, MONTH, MIN, MIN5, MIN15, MIN30, MIN60)，默认 DAY
- `--max-stocks <N>`: 最大股票数量（用于测试），默认使用全部成分股
- `--output <FILE>`: 保存合并后的训练数据到文件（可选）

## 编程接口

### 1. 基本用法

```python
from utils.batch_training import train_model_on_index
from controllers.cli.di.container import Container
from domain.entities.model import ModelType
from domain.value_objects.date_range import DateRange
from domain.value_objects.kline_type import KLineType
from datetime import datetime

# 初始化容器
container = Container()

# 定义日期范围
date_range = DateRange(
    start_date=datetime(2023, 1, 1),
    end_date=datetime(2023, 12, 31)
)

# 训练模型
model = await train_model_on_index(
    index_name="沪深300",
    model_type=ModelType.LGBM,
    model_name="hs300_lgbm_model",
    date_range=date_range,
    kline_type=KLineType.DAY,
    data_provider=container.data_provider,
    model_trainer=container.model_trainer,
    model_repository=container.model_repository
)

print(f"模型ID: {model.id}")
print(f"模型状态: {model.status}")
print(f"模型指标: {model.metrics}")
```

### 2. 仅加载数据（不训练）

```python
from utils.batch_training import load_index_training_data

# 加载并合并所有数据
training_data = await load_index_training_data(
    index_name="沪深300",
    date_range=date_range,
    kline_type=KLineType.DAY,
    data_provider=container.data_provider,
    add_features=True,
    add_labels=True
)

print(f"总数据量: {len(training_data)} 条")
print(f"特征数: {len(training_data.columns)} 列")

# 保存到文件
training_data.to_csv("hs300_training_data.csv", index=False)
```

### 3. 按股票分别加载

```python
from utils.batch_training import load_index_training_data_by_stock

# 加载数据（按股票分别存储）
data_by_stock = await load_index_training_data_by_stock(
    index_name="沪深300",
    date_range=date_range,
    kline_type=KLineType.DAY,
    data_provider=container.data_provider
)

print(f"加载了 {len(data_by_stock)} 只股票的数据")

# 访问单个股票的数据
if "sh600000" in data_by_stock:
    sh600000_data = data_by_stock["sh600000"]
    print(f"sh600000: {len(sh600000_data)} 条记录")
```

### 4. 批量训练多个指数

```python
from utils.batch_training import train_models_for_multiple_indices

# 为多个指数分别训练模型
models = await train_models_for_multiple_indices(
    indices=["沪深300", "中证500", "上证50"],
    model_type=ModelType.LGBM,
    date_range=date_range,
    kline_type=KLineType.DAY,
    data_provider=container.data_provider,
    model_trainer=container.model_trainer,
    model_repository=container.model_repository
)

# 访问各个模型
hs300_model = models["沪深300"]
zz500_model = models["中证500"]
sz50_model = models["上证50"]
```

## 典型应用场景

### 场景1: 训练沪深300因子模型

```bash
# 1. 加载2023年全年数据训练
./run_cli.sh model train-index \
    --type LGBM \
    --name hs300_factor_2023 \
    --index 沪深300 \
    --start 2023-01-01 \
    --end 2023-12-31

# 预期结果:
# - 300只股票
# - 约54,600条训练数据（300股 × 242个交易日 × 转换率）
# - 27个特征列
```

### 场景2: 对比不同指数的模型效果

```bash
# 训练沪深300
./run_cli.sh model train-index \
    --type LGBM --name hs300_model \
    --index 沪深300 --start 2023-01-01 --end 2023-12-31

# 训练中证500
./run_cli.sh model train-index \
    --type LGBM --name zz500_model \
    --index 中证500 --start 2023-01-01 --end 2023-12-31

# 训练上证50
./run_cli.sh model train-index \
    --type LGBM --name sz50_model \
    --index 上证50 --start 2023-01-01 --end 2023-12-31

# 对比模型指标
# - 沪深300: 300只股票，大中盘
# - 中证500: 424只股票，中小盘
# - 上证50: 50只股票，大盘蓝筹
```

### 场景3: 快速原型验证

```bash
# 使用少量股票和短时间快速测试
./run_cli.sh model train-index \
    --type LGBM --name quick_test \
    --index 沪深300 \
    --start 2023-10-01 --end 2023-12-31 \
    --max-stocks 10

# 验证通过后，扩展到完整训练
./run_cli.sh model train-index \
    --type LGBM --name full_model \
    --index 沪深300 \
    --start 2022-01-01 --end 2023-12-31
```

### 场景4: 保存训练数据供后续使用

```bash
# 加载并保存数据
./run_cli.sh model train-index \
    --type LGBM --name hs300_model \
    --index 沪深300 \
    --start 2023-01-01 --end 2023-12-31 \
    --output data/hs300_training_2023.csv

# 后续可以使用保存的数据快速训练
./run_cli.sh model train \
    --type LGBM --name hs300_model_v2 \
    --data data/hs300_training_2023.csv
```

## 性能考虑

### 训练时间估算

基于实际测试（3只股票，1年数据）：
- 数据加载: 约20秒（含Hikyuu初始化）
- 数据转换: < 1秒
- 模型训练: < 1秒
- **总计: 约20-25秒**

预估完整指数训练时间：
- **沪深300（300只）**: 约5-10分钟
- **中证500（424只）**: 约7-15分钟
- **上证50（50只）**: 约1-2分钟

### 数据量估算

以2023年全年数据为例（242个交易日）：

| 指数 | 成分股数 | 原始K线数 | 训练数据行数* | 数据量估算 |
|------|---------|----------|------------|----------|
| 沪深300 | 300 | 72,600 | ~54,600 | 约15 MB |
| 中证500 | 424 | 102,608 | ~77,100 | 约21 MB |
| 上证50 | 50 | 12,100 | ~9,100 | 约3 MB |

*训练数据行数考虑了特征计算导致的部分数据丢失（如MA需要窗口期）

### 优化建议

1. **使用 `--max-stocks` 测试**: 先用少量股票验证流程
2. **合理选择日期范围**: 数据越多越好，但也会增加训练时间
3. **保存训练数据**: 使用 `--output` 参数保存数据，避免重复加载
4. **批量训练**: 夜间批量训练多个指数模型

## 数据质量

### 自动过滤和处理

批量训练过程会自动处理以下情况：
- **无数据股票**: 自动跳过，不影响其他股票
- **数据缺失**: 特征计算时自动删除NaN行
- **加载失败**: 默认跳过错误股票，继续处理其他股票

### 数据统计

训练过程会输出详细统计：
```
开始加载 沪深300 成分股数据...
  成分股数量: 300
  日期范围: 2023-01-01 ~ 2023-12-31

  进度: 50/300 (48 成功, 2 失败)
  进度: 100/300 (96 成功, 4 失败)
  ...

加载完成: 285 成功, 15 失败
合并后总数据量: 51,300 条
```

## 常见问题

### Q1: 为什么有些股票加载失败？

**A:** 可能原因：
1. 新上市股票，在指定日期范围内无数据
2. 退市股票
3. 数据库中该股票数据缺失

这些情况都会被自动跳过，不影响整体训练。

### Q2: 如何选择合适的日期范围？

**A:** 建议：
- **最短**: 3个月（~60个交易日）- 用于快速测试
- **推荐**: 1年（~242个交易日）- 平衡数据量和训练时间
- **较长**: 2-3年 - 更多数据，但加载时间更长

### Q3: 训练数据量太大怎么办？

**A:** 可以：
1. 缩短日期范围
2. 使用 `--max-stocks` 限制股票数量
3. 先保存数据到文件，然后使用采样或特征选择

### Q4: 可以同时训练多个指数吗？

**A:** 可以，但建议：
- 使用编程接口的 `train_models_for_multiple_indices`
- 或者使用脚本顺序执行多个训练命令

### Q5: 如何评估模型效果？

**A:** 查看训练输出的指标：
- `train_r2`: 训练集R²（> 0.5较好）
- `test_r2`: 测试集R²（正值表示有预测能力）
- `train_rmse`, `test_rmse`: 误差（越小越好）

## 测试脚本

运行提供的测试脚本：

```bash
./test_batch_training.sh
```

该脚本会：
1. 使用5只股票快速测试训练流程
2. 显示完整训练的示例命令

## 相关文档

- [INDEX_CONSTITUENTS_GUIDE.md](INDEX_CONSTITUENTS_GUIDE.md) - 指数成分股获取指南
- [MODEL_TRAINING_DATA_LOADING_GUIDE.md](MODEL_TRAINING_DATA_LOADING_GUIDE.md) - 数据加载指南

## API 参考

### `train_model_on_index`

在指数成分股上训练模型

```python
async def train_model_on_index(
    index_name: str,
    model_type: ModelType,
    model_name: str,
    date_range: DateRange,
    kline_type: KLineType,
    data_provider,
    model_trainer,
    model_repository,
    hyperparameters: Optional[Dict[str, Any]] = None,
    max_stocks: Optional[int] = None,
    skip_errors: bool = True
) -> Model
```

### `load_index_training_data`

加载指数成分股的训练数据（合并为一个DataFrame）

```python
async def load_index_training_data(
    index_name: str,
    date_range: DateRange,
    kline_type: KLineType,
    data_provider,
    add_features: bool = True,
    add_labels: bool = True,
    label_horizon: int = 1,
    max_stocks: Optional[int] = None,
    skip_errors: bool = True
) -> pd.DataFrame
```

### `load_index_training_data_by_stock`

加载指数成分股的训练数据（按股票分别存储）

```python
async def load_index_training_data_by_stock(
    index_name: str,
    date_range: DateRange,
    kline_type: KLineType,
    data_provider,
    add_features: bool = True,
    add_labels: bool = True,
    label_horizon: int = 1,
    max_stocks: Optional[int] = None,
    skip_errors: bool = True
) -> Dict[str, pd.DataFrame]
```

### `train_models_for_multiple_indices`

为多个指数分别训练模型

```python
async def train_models_for_multiple_indices(
    indices: List[str],
    model_type: ModelType,
    date_range: DateRange,
    kline_type: KLineType,
    data_provider,
    model_trainer,
    model_repository,
    hyperparameters: Optional[Dict[str, Any]] = None,
    max_stocks_per_index: Optional[int] = None
) -> Dict[str, Model]
```

## 更新日志

### 2025-11-13
- 初始版本
- 实现指数批量训练功能
- CLI 命令 `model train-index`
- 支持沪深300、中证500、上证50等693个指数
- 测试通过：3只股票，546条数据，训练成功
