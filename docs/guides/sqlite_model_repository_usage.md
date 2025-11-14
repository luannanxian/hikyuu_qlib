# SQLiteModelRepository 使用指南

本文档演示如何使用 SQLiteModelRepository 的 list_models() 和 delete() 方法。

## 功能概述

### list_models() 方法

列出模型，支持灵活的筛选和限制：

- 支持按 `status` 筛选（TRAINED/UNTRAINED/DEPLOYED/ARCHIVED）
- 支持按 `model_type` 筛选（LGBM/MLP/LSTM/GRU）
- 支持 `limit` 限制返回数量
- 自动按创建时间倒序排列（最新的在前）

### delete() 方法增强

删除模型，增加了安全检查：

- 删除前检查模型是否存在
- 如果模型不存在，抛出 `ValueError` 异常
- 确保事务安全

## 使用示例

### 1. 初始化仓储

```python
from adapters.repositories.sqlite_model_repository import SQLiteModelRepository

# 使用文件数据库
repo = SQLiteModelRepository(db_path="models.db")
await repo.initialize()

# 或使用内存数据库（测试时）
repo = SQLiteModelRepository(db_path=":memory:")
await repo.initialize()
```

### 2. 列出所有模型

```python
# 获取所有模型
all_models = await repo.list_models()
print(f"Total models: {len(all_models)}")

for model in all_models:
    print(f"- {model.model_type.value}: {model.status.value}")
```

### 3. 按状态筛选模型

```python
from domain.entities.model import ModelStatus

# 获取所有已训练的模型
trained_models = await repo.list_models(status=ModelStatus.TRAINED)
print(f"Trained models: {len(trained_models)}")

# 获取所有已部署的模型
deployed_models = await repo.list_models(status=ModelStatus.DEPLOYED)
print(f"Deployed models: {len(deployed_models)}")

# 获取所有未训练的模型
untrained_models = await repo.list_models(status=ModelStatus.UNTRAINED)
print(f"Untrained models: {len(untrained_models)}")

# 获取所有已归档的模型
archived_models = await repo.list_models(status=ModelStatus.ARCHIVED)
print(f"Archived models: {len(archived_models)}")
```

### 4. 按模型类型筛选

```python
from domain.entities.model import ModelType

# 获取所有 LGBM 模型
lgbm_models = await repo.list_models(model_type=ModelType.LGBM)
print(f"LGBM models: {len(lgbm_models)}")

# 获取所有 MLP 模型
mlp_models = await repo.list_models(model_type=ModelType.MLP)
print(f"MLP models: {len(mlp_models)}")

# 获取所有 LSTM 模型
lstm_models = await repo.list_models(model_type=ModelType.LSTM)
print(f"LSTM models: {len(lstm_models)}")
```

### 5. 限制返回数量

```python
# 获取最新的 10 个模型
recent_10 = await repo.list_models(limit=10)
print(f"Recent 10 models: {len(recent_10)}")

# 获取最新的 5 个已训练模型
recent_trained_5 = await repo.list_models(
    status=ModelStatus.TRAINED,
    limit=5
)
print(f"Recent 5 trained models: {len(recent_trained_5)}")
```

### 6. 组合筛选条件

```python
# 获取最新的 10 个已训练的 LGBM 模型
recent_trained_lgbm = await repo.list_models(
    model_type=ModelType.LGBM,
    status=ModelStatus.TRAINED,
    limit=10
)

print(f"Recent 10 trained LGBM models:")
for model in recent_trained_lgbm:
    print(f"  - ID: {model.id}")
    print(f"    Type: {model.model_type.value}")
    print(f"    Status: {model.status.value}")
    print(f"    Metrics: {model.metrics}")
```

### 7. 安全删除模型

```python
# 删除存在的模型（成功）
model_id = "some-model-id"
try:
    await repo.delete(model_id)
    print(f"Model {model_id} deleted successfully")
except ValueError as e:
    print(f"Error: {e}")

# 删除不存在的模型（抛出异常）
try:
    await repo.delete("nonexistent-model-id")
except ValueError as e:
    print(f"Expected error: {e}")
    # 输出: Expected error: Model with id 'nonexistent-model-id' not found
```

### 8. 完整示例：模型管理工作流

```python
from adapters.repositories.sqlite_model_repository import SQLiteModelRepository
from domain.entities.model import Model, ModelType, ModelStatus

async def manage_models():
    # 初始化仓储
    repo = SQLiteModelRepository(db_path="models.db")
    await repo.initialize()

    try:
        # 1. 创建和保存新模型
        new_model = Model(
            model_type=ModelType.LGBM,
            hyperparameters={"learning_rate": 0.01, "num_leaves": 31}
        )
        await repo.save(new_model)
        print(f"Created model: {new_model.id}")

        # 2. 训练模型并更新
        new_model.mark_as_trained(metrics={"accuracy": 0.85, "f1_score": 0.82})
        await repo.save(new_model)
        print(f"Model trained with accuracy: {new_model.metrics['accuracy']}")

        # 3. 查看所有已训练的模型
        trained_models = await repo.list_models(status=ModelStatus.TRAINED)
        print(f"\nTotal trained models: {len(trained_models)}")

        # 4. 找出最新的5个LGBM模型
        recent_lgbm = await repo.list_models(
            model_type=ModelType.LGBM,
            limit=5
        )
        print(f"\nRecent LGBM models: {len(recent_lgbm)}")

        # 5. 清理旧模型（演示删除）
        if recent_lgbm:
            old_model_id = recent_lgbm[-1].id  # 最旧的一个
            await repo.delete(old_model_id)
            print(f"\nDeleted old model: {old_model_id}")

        # 6. 验证删除
        try:
            await repo.delete(old_model_id)  # 再次尝试删除
        except ValueError as e:
            print(f"Confirmed deletion: {e}")

    finally:
        await repo.close()

# 运行示例
# await manage_models()
```

## 最佳实践

### 1. 使用 limit 避免加载过多数据

```python
# 好的做法：限制返回数量
recent_models = await repo.list_models(limit=100)

# 避免：如果有数千个模型，会很慢
all_models = await repo.list_models()  # 慎用
```

### 2. 组合筛选条件提高查询效率

```python
# 好的做法：精确筛选
target_models = await repo.list_models(
    model_type=ModelType.LGBM,
    status=ModelStatus.DEPLOYED,
    limit=10
)

# 避免：加载所有再过滤
all_models = await repo.list_models()
target_models = [
    m for m in all_models
    if m.model_type == ModelType.LGBM
    and m.status == ModelStatus.DEPLOYED
][:10]
```

### 3. 删除前检查

```python
# 好的做法：利用异常处理
try:
    await repo.delete(model_id)
    print(f"Model {model_id} deleted")
except ValueError:
    print(f"Model {model_id} does not exist")

# 或者先检查
model = await repo.find_by_id(model_id)
if model:
    await repo.delete(model_id)
```

### 4. 按时间排序的优势

```python
# list_models() 自动按创建时间倒序
# 最新的模型总是在列表前面
recent_models = await repo.list_models(limit=10)
latest_model = recent_models[0]  # 最新的模型
oldest_in_set = recent_models[-1]  # 这批中最旧的
```

## 性能建议

1. **使用适当的 limit**：避免一次加载过多数据
2. **利用索引**：数据库已对 `created_at`、`status`、`model_type` 建立索引
3. **批量操作**：如需删除多个模型，考虑批量事务处理
4. **定期清理**：归档或删除过期模型，保持数据库精简

## 错误处理

```python
from adapters.repositories.sqlite_model_repository import SQLiteModelRepository

async def safe_operations(repo: SQLiteModelRepository):
    # 删除操作
    try:
        await repo.delete("some-id")
    except ValueError as e:
        # 模型不存在
        print(f"Model not found: {e}")
    except Exception as e:
        # 其他数据库错误
        print(f"Database error: {e}")

    # 列表操作
    try:
        models = await repo.list_models(
            status=ModelStatus.TRAINED,
            limit=10
        )
    except Exception as e:
        # 查询失败
        print(f"Query error: {e}")
        models = []

    return models
```

## 总结

- `list_models()` 提供灵活的模型查询功能
- 支持多维度筛选（状态、类型）
- 支持限制返回数量
- 自动按时间排序
- `delete()` 提供安全的删除操作
- 删除前检查模型是否存在
- 适当的错误处理和异常类型

这些功能使得模型管理更加安全、高效和易用。
