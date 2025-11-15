# QlibModelTrainerAdapter predict_batch 使用示例

## 概述

`QlibModelTrainerAdapter` 新增了 `predict_batch` 方法，支持：
- 从文件路径加载模型进行预测
- 返回 `PredictionBatch` 聚合根
- 指定预测日期
- 完整的错误处理

## 功能特性

### 1. 模型持久化

#### 保存模型
```python
from adapters.qlib.qlib_model_trainer_adapter import QlibModelTrainerAdapter
from domain.entities.model import Model, ModelType

# 创建并训练模型
adapter = QlibModelTrainerAdapter()
model = Model(
    model_type=ModelType.LGBM,
    hyperparameters={"learning_rate": 0.01}
)

# 训练模型（假设training_data已准备好）
trained_model = await adapter.train(model, training_data)

# 保存模型到文件
adapter.save_model(trained_model, "/path/to/models/my_model.pkl")
print(f"Model saved to: {trained_model.file_path}")
```

#### 加载模型
```python
# 从文件加载模型
loaded_model_obj = adapter.load_model("/path/to/models/my_model.pkl")
```

### 2. 批量预测

#### 使用内存中的模型预测
```python
import pandas as pd
from datetime import datetime

# 准备输入数据
input_data = pd.DataFrame({
    'stock_code': ['sh600000', 'sz000001', 'sh600519'],
    'date': [datetime(2024, 1, 15)] * 3,
    'feature1': [0.5, 0.3, -0.1],
    'feature2': [0.3, -0.2, 0.4],
    'feature3': [-0.2, 0.1, 0.2],
})

# 执行预测（返回 PredictionBatch）
batch = await adapter.predict_batch(
    model=trained_model,
    input_data=input_data
)

print(f"预测批次大小: {batch.size()}")
print(f"平均置信度: {batch.average_confidence()}")
```

#### 从文件加载模型进行预测
```python
# 设置模型文件路径
model_with_path = Model(
    model_type=ModelType.LGBM,
    hyperparameters={"learning_rate": 0.01},
    file_path="/path/to/models/my_model.pkl"
)

# 不需要在内存中训练，直接从文件预测
batch = await adapter.predict_batch(
    model=model_with_path,
    input_data=input_data
)
```

#### 指定预测日期
```python
from datetime import datetime

prediction_date = datetime(2024, 6, 15, 10, 30, 0)

batch = await adapter.predict_batch(
    model=trained_model,
    input_data=input_data,
    prediction_date=prediction_date
)

print(f"批次生成时间: {batch.generated_at}")
```

### 3. 处理预测结果

#### 访问单个预测
```python
for prediction in batch.predictions:
    print(f"股票: {prediction.stock_code.value}")
    print(f"时间: {prediction.timestamp}")
    print(f"预测值: {prediction.predicted_value:.4f}")
    print(f"置信度: {prediction.confidence:.2%}")
    print(f"模型ID: {prediction.model_id}")
    print("---")
```

#### 转换为 DataFrame
```python
df = batch.to_dataframe()
print(df)

# 输出示例:
#   stock_code           timestamp  predicted_value  confidence       model_id                          prediction_id
# 0  sh600000 2024-01-15 00:00:00         0.0234       0.65  abc-123-def  pred-001
# 1  sz000001 2024-01-15 00:00:00        -0.0156       0.58  abc-123-def  pred-002
# 2  sh600519 2024-01-15 00:00:00         0.0412       0.72  abc-123-def  pred-003
```

#### 计算统计信息
```python
# 平均置信度
avg_conf = batch.average_confidence()
print(f"平均置信度: {avg_conf:.2%}")

# 批次大小
print(f"预测数量: {batch.size()}")

# 按股票查询
from domain.value_objects.stock_code import StockCode
prediction = batch.get_prediction(
    stock_code=StockCode('sh600000'),
    timestamp=datetime(2024, 1, 15)
)
```

### 4. 错误处理

```python
try:
    batch = await adapter.predict_batch(
        model=model,
        input_data=input_data
    )
except ValueError as e:
    print(f"验证错误: {e}")
    # 例如: "Model not trained and no file path provided"

except FileNotFoundError as e:
    print(f"文件不存在: {e}")
    # 例如: "Model file not found: /path/to/model.pkl"

except Exception as e:
    print(f"预测失败: {e}")
    # 其他预测错误
```

## 完整工作流示例

```python
from adapters.qlib.qlib_model_trainer_adapter import QlibModelTrainerAdapter
from domain.entities.model import Model, ModelType
import pandas as pd
from datetime import datetime

async def complete_workflow():
    # 1. 初始化适配器
    adapter = QlibModelTrainerAdapter()

    # 2. 创建模型
    model = Model(
        model_type=ModelType.LGBM,
        hyperparameters={
            "learning_rate": 0.05,
            "num_leaves": 31
        }
    )

    # 3. 准备训练数据
    training_data = pd.DataFrame({
        'stock_code': ['sh600000'] * 100,
        'feature1': np.random.randn(100),
        'feature2': np.random.randn(100),
        'feature3': np.random.randn(100),
        'label_return': np.random.randn(100) * 0.02,
    })

    # 4. 训练模型
    trained_model = await adapter.train(model, training_data)
    print(f"训练完成，R²: {trained_model.metrics.get('train_r2', 0):.4f}")

    # 5. 保存模型
    model_path = "/tmp/models/lgbm_model.pkl"
    adapter.save_model(trained_model, model_path)
    print(f"模型已保存: {model_path}")

    # 6. 准备预测数据
    prediction_data = pd.DataFrame({
        'stock_code': ['sh600000', 'sz000001', 'sh600519'],
        'date': [datetime(2024, 6, 15)] * 3,
        'feature1': [0.5, 0.3, -0.1],
        'feature2': [0.3, -0.2, 0.4],
        'feature3': [-0.2, 0.1, 0.2],
    })

    # 7. 执行预测
    batch = await adapter.predict_batch(
        model=trained_model,
        input_data=prediction_data,
        prediction_date=datetime(2024, 6, 15, 10, 0, 0)
    )

    # 8. 输出结果
    print(f"\n预测结果:")
    print(f"批次大小: {batch.size()}")
    print(f"平均置信度: {batch.average_confidence():.2%}")
    print(f"\n详细预测:")

    df = batch.to_dataframe()
    print(df[['stock_code', 'predicted_value', 'confidence']])

    return batch

# 运行工作流
batch = await complete_workflow()
```

## 与原有 predict 方法的对比

| 特性 | predict() | predict_batch() |
|------|-----------|-----------------|
| 返回类型 | List[Prediction] | PredictionBatch |
| 模型加载 | 仅内存模型 | 支持文件路径 |
| 预测日期 | 不支持 | 支持指定 |
| 批次管理 | 手动 | 自动 |
| 统计功能 | 需自行计算 | 内置方法 |
| 转换为DF | 需自行转换 | 内置方法 |

## 最佳实践

1. **模型持久化**: 训练后立即保存模型
   ```python
   trained_model = await adapter.train(model, training_data)
   adapter.save_model(trained_model, model_path)
   ```

2. **批量预测**: 优先使用 `predict_batch` 而不是 `predict`
   ```python
   # 推荐
   batch = await adapter.predict_batch(model, input_data)

   # 不推荐（除非需要List[Prediction]）
   predictions = await adapter.predict(model, input_data)
   ```

3. **错误处理**: 始终处理可能的异常
   ```python
   try:
       batch = await adapter.predict_batch(model, input_data)
   except (ValueError, FileNotFoundError) as e:
       logger.error(f"预测失败: {e}")
       # 处理错误
   ```

4. **资源管理**: 大批量预测时注意内存
   ```python
   # 对于大数据集，分批处理
   chunk_size = 1000
   for i in range(0, len(data), chunk_size):
       chunk = data.iloc[i:i+chunk_size]
       batch = await adapter.predict_batch(model, chunk)
       process_batch(batch)
   ```

## 注意事项

1. **模型文件格式**: 使用 pickle 序列化，需要注意版本兼容性
2. **文件路径**: 使用绝对路径以避免路径问题
3. **并发安全**: pickle 文件加载不是线程安全的，需要适当同步
4. **内存管理**: 大模型文件可能占用大量内存
5. **数据格式**: 确保输入数据包含必要的列（stock_code, features）
