# 剩余任务清单

**创建日期**: 2025-11-14
**状态**: 🟡 P1/P2优化任务
**优先级**: 中等(不阻塞MVP发布)

---

## 执行概要

基于代码审查,识别出**5个未完全实现的功能**。这些功能不影响核心工作流,但需要在P1阶段完善以提升用户体验。

**完成度评估**:
- ✅ **核心功能**: 100% (数据加载、训练、预测、信号转换、回测)
- 🟡 **CLI辅助命令**: 40% (部分命令仅占位)
- 🟡 **高级特性**: 0% (缓存、批量操作)

---

## 任务列表

### 任务1: `data list` 命令实现 🟡 P2

**位置**: [src/controllers/cli/commands/data.py:205](../src/controllers/cli/commands/data.py#L205)

**当前状态**:
```python
@data_group.command(name="list")
@click.pass_context
def data_list(ctx):
    """列出已有数据"""
    # TODO: 实现列出已有数据的逻辑
    click.echo("✅ 列出已有数据功能尚未实现")
```

**问题描述**:
- 命令只返回占位提示,无实际功能
- 用户无法查看已加载的股票、时间范围或缓存文件

**影响范围**: 🟢 **低**
- 不影响核心工作流
- 用户可通过文件管理器查看输出目录

**建议实现** (预计30分钟):

```python
@data_group.command(name="list")
@click.option('--format', type=click.Choice(['table', 'json', 'csv']), default='table', help='输出格式')
@click.option('--directory', type=click.Path(exists=True), default='data', help='数据目录')
@click.pass_context
def data_list(ctx, format, directory):
    """列出已有数据

    示例:
        ./run_cli.sh data list
        ./run_cli.sh data list --format json
        ./run_cli.sh data list --directory data/cache
    """
    import os
    import pandas as pd
    from pathlib import Path

    data_dir = Path(directory)

    if not data_dir.exists():
        click.echo(f"✗ 数据目录不存在: {data_dir}", err=True)
        return

    # 扫描CSV/Parquet文件
    files = []
    for ext in ['*.csv', '*.parquet', '*.pkl']:
        files.extend(data_dir.glob(ext))

    if not files:
        click.echo(f"✓ 数据目录 {data_dir} 中没有找到数据文件")
        return

    # 收集文件信息
    data_info = []
    for file in files:
        stat = file.stat()
        info = {
            'filename': file.name,
            'size_mb': round(stat.st_size / 1024 / 1024, 2),
            'modified': pd.Timestamp(stat.st_mtime, unit='s').strftime('%Y-%m-%d %H:%M:%S'),
            'type': file.suffix[1:]
        }

        # 尝试读取前几行推断内容
        try:
            if file.suffix == '.csv':
                df = pd.read_csv(file, nrows=1)
                info['rows'] = '(估算)'
                info['columns'] = len(df.columns)
                if 'stock_code' in df.columns:
                    info['stock_code'] = df['stock_code'].iloc[0]
            elif file.suffix == '.parquet':
                df = pd.read_parquet(file)
                info['rows'] = len(df)
                info['columns'] = len(df.columns)
        except:
            pass

        data_info.append(info)

    # 格式化输出
    if format == 'json':
        import json
        click.echo(json.dumps(data_info, indent=2, ensure_ascii=False))
    elif format == 'csv':
        df = pd.DataFrame(data_info)
        click.echo(df.to_csv(index=False))
    else:  # table
        df = pd.DataFrame(data_info)
        click.echo(f"\n📊 数据目录: {data_dir}\n")
        click.echo(df.to_string(index=False))
        click.echo(f"\n总计: {len(files)} 个文件")
```

**验证**:
```bash
./run_cli.sh data list
./run_cli.sh data list --format json
```

---

### 任务2: 模型训练超参数配置 🟡 P2

**位置**: [src/controllers/cli/commands/model.py:232](../src/controllers/cli/commands/model.py#L232)

**当前状态**:
```python
# Line 232: 始终使用空超参字典
model = Model(
    model_type=ModelType(type.upper()),
    hyperparameters={}  # ❌ 硬编码空字典
)
```

**问题描述**:
- 无法从命令行或配置文件传入超参数
- 所有模型使用默认参数训练

**影响范围**: 🟡 **中**
- 影响模型调优能力
- 用户无法实验不同超参数组合

**建议实现** (预计20分钟):

```python
# 添加命令行选项
@model_group.command(name="train")
@click.option('--type', type=click.Choice(['LGBM', 'MLP', 'LSTM', 'GRU']), required=True)
@click.option('--name', required=True, help='模型名称')
@click.option('--code', help='股票代码')
@click.option('--index', help='指数名称')
@click.option('--start', required=True, help='开始日期')
@click.option('--end', required=True, help='结束日期')
@click.option('--max-stocks', type=int, help='最大股票数量')
@click.option('--hyperparameters', type=str, help='超参数JSON字符串')  # ✅ 新增
@click.option('--config', type=click.Path(exists=True), help='配置文件路径')
@click.pass_context
async def model_train(ctx, type, name, code, index, start, end, max_stocks, hyperparameters, config):
    """训练模型"""

    # 加载超参数
    hyperparams = {}

    # 1. 从配置文件加载(如果提供)
    if config:
        config_data = container.config_loader.load_config(config)
        hyperparams = config_data.get('hyperparameters', {})

    # 2. 从命令行覆盖(如果提供)
    if hyperparameters:
        import json
        try:
            cli_hyperparams = json.loads(hyperparameters)
            hyperparams.update(cli_hyperparams)
        except json.JSONDecodeError as e:
            click.echo(f"✗ 超参数JSON解析失败: {e}", err=True)
            return

    # 3. 使用模型类型默认值(如果都没提供)
    if not hyperparams:
        hyperparams = get_default_hyperparameters(type)

    click.echo(f"ℹ 使用超参数: {hyperparams}")

    # 创建模型
    model = Model(
        model_type=ModelType(type.upper()),
        hyperparameters=hyperparams
    )

    # ... 继续训练逻辑

def get_default_hyperparameters(model_type: str) -> dict:
    """获取模型默认超参数"""
    defaults = {
        'LGBM': {
            'n_estimators': 100,
            'learning_rate': 0.05,
            'max_depth': 7,
            'num_leaves': 31,
            'min_child_samples': 20
        },
        'MLP': {
            'hidden_layers': [64, 32],
            'activation': 'relu',
            'learning_rate': 0.001,
            'epochs': 50
        },
        'LSTM': {
            'hidden_size': 64,
            'num_layers': 2,
            'sequence_length': 20,
            'learning_rate': 0.001,
            'epochs': 50
        }
    }
    return defaults.get(model_type.upper(), {})
```

**使用示例**:
```bash
# 使用默认超参数
./run_cli.sh model train --type LGBM --name test1 --code sh600036 --start 2023-01-01 --end 2023-12-31

# 使用自定义超参数
./run_cli.sh model train --type LGBM --name test2 --code sh600036 --start 2023-01-01 --end 2023-12-31 \
  --hyperparameters '{"n_estimators": 200, "learning_rate": 0.03}'

# 使用配置文件
./run_cli.sh model train --type LGBM --name test3 --code sh600036 --start 2023-01-01 --end 2023-12-31 \
  --config config/lgbm_tuned.yaml
```

---

### 任务3: `model list` 和 `model delete` 实现 🟡 P2

**位置**:
- [src/controllers/cli/commands/model.py:287](../src/controllers/cli/commands/model.py#L287) - model list
- [src/controllers/cli/commands/model.py:336](../src/controllers/cli/commands/model.py#L336) - model delete

**当前状态**:
```python
# Line 287
@model_group.command(name="list")
def model_list():
    """列出所有模型"""
    # TODO: 实现列出所有模型的逻辑
    click.echo("✅ 列出所有模型功能尚未实现")

# Line 336
@model_group.command(name="delete")
@click.argument('model_id')
def model_delete(model_id):
    """删除指定模型"""
    # TODO: 实现删除模型的逻辑
    click.echo(f"✅ 删除模型 {model_id} 功能尚未实现")
```

**问题描述**:
- 无法查看已训练的模型列表
- 无法删除旧模型释放存储空间

**影响范围**: 🟡 **中**
- 影响模型管理能力
- 存储空间可能被历史模型占用

**建议实现** (预计30分钟):

```python
@model_group.command(name="list")
@click.option('--format', type=click.Choice(['table', 'json', 'csv']), default='table')
@click.option('--status', type=click.Choice(['TRAINED', 'UNTRAINED', 'DEPLOYED', 'ARCHIVED']), help='筛选状态')
@click.option('--type', type=click.Choice(['LGBM', 'MLP', 'LSTM', 'GRU']), help='筛选模型类型')
@click.option('--limit', type=int, default=20, help='返回数量限制')
@click.pass_context
async def model_list(ctx, format, status, type, limit):
    """列出所有模型

    示例:
        ./run_cli.sh model list
        ./run_cli.sh model list --format json
        ./run_cli.sh model list --status TRAINED --type LGBM
        ./run_cli.sh model list --limit 10
    """
    container = ctx.obj
    model_repository = container.model_repository

    try:
        await model_repository.initialize()

        # 从SQLite数据库读取模型列表
        # TODO: 需要在SQLiteModelRepository添加list_models方法
        models = await model_repository.list_models(
            status=status,
            model_type=type,
            limit=limit
        )

        if not models:
            click.echo("✓ 没有找到模型")
            return

        # 格式化模型信息
        models_info = []
        for model in models:
            info = {
                'id': model.id[:8],  # 显示前8位
                'name': model.name if hasattr(model, 'name') else '-',
                'type': model.model_type.value,
                'status': model.status.value,
                'training_date': model.training_date.strftime('%Y-%m-%d') if model.training_date else '-',
                'train_r2': f"{model.metrics.get('train_r2', 0):.4f}" if model.metrics else '-',
                'valid_r2': f"{model.metrics.get('valid_r2', 0):.4f}" if model.metrics else '-'
            }
            models_info.append(info)

        # 输出
        if format == 'json':
            import json
            click.echo(json.dumps(models_info, indent=2, ensure_ascii=False))
        elif format == 'csv':
            import pandas as pd
            df = pd.DataFrame(models_info)
            click.echo(df.to_csv(index=False))
        else:  # table
            import pandas as pd
            df = pd.DataFrame(models_info)
            click.echo(f"\n📊 已训练模型列表 (共 {len(models)} 个)\n")
            click.echo(df.to_string(index=False))

    except Exception as e:
        click.echo(f"✗ 列出模型失败: {e}", err=True)
    finally:
        await model_repository.close()

@model_group.command(name="delete")
@click.argument('model_id')
@click.option('--force', is_flag=True, help='强制删除,不询问')
@click.pass_context
async def model_delete(ctx, model_id, force):
    """删除指定模型

    示例:
        ./run_cli.sh model delete abc12345
        ./run_cli.sh model delete abc12345 --force
    """
    container = ctx.obj
    model_repository = container.model_repository

    try:
        await model_repository.initialize()

        # 查找模型
        model = await model_repository.get_by_id(model_id)

        if not model:
            click.echo(f"✗ 模型不存在: {model_id}", err=True)
            return

        # 确认删除
        if not force:
            click.echo(f"模型信息:")
            click.echo(f"  ID: {model.id}")
            click.echo(f"  类型: {model.model_type.value}")
            click.echo(f"  状态: {model.status.value}")
            click.echo(f"  训练日期: {model.training_date}")

            if not click.confirm('确认删除此模型?'):
                click.echo("✓ 取消删除")
                return

        # 删除模型
        await model_repository.delete(model_id)
        click.echo(f"✓ 模型 {model_id} 已删除")

    except Exception as e:
        click.echo(f"✗ 删除模型失败: {e}", err=True)
    finally:
        await model_repository.close()
```

**需要在SQLiteModelRepository添加的方法**:

```python
# src/adapters/repositories/sqlite_model_repository.py

async def list_models(
    self,
    status: Optional[str] = None,
    model_type: Optional[str] = None,
    limit: int = 100
) -> List[Model]:
    """列出模型"""
    conn = await self._get_connection()

    query = "SELECT * FROM models WHERE 1=1"
    params = []

    if status:
        query += " AND status = ?"
        params.append(status)

    if model_type:
        query += " AND model_type = ?"
        params.append(model_type)

    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    cursor = await conn.execute(query, params)
    rows = await cursor.fetchall()

    models = []
    for row in rows:
        model = self._deserialize_model(dict(row))
        models.append(model)

    return models

async def delete(self, model_id: str) -> None:
    """删除模型"""
    conn = await self._get_connection()
    await conn.execute("DELETE FROM models WHERE id = ?", (model_id,))
    await conn.commit()
```

---

### 任务4: `config set` 持久化 🟢 P3

**位置**: [src/controllers/cli/commands/config.py:93](../src/controllers/cli/commands/config.py#L93)

**当前状态**:
```python
@config_group.command(name="set")
@click.argument('key')
@click.argument('value')
def config_set(key, value):
    """设置配置项"""
    # TODO: 实现设置配置项的逻辑
    click.echo(f"✅ 设置配置项 {key} = {value} 功能尚未实现")
```

**问题描述**:
- 命令只打印信息,不真正修改配置文件
- 用户无法通过CLI动态修改配置

**影响范围**: 🟢 **低**
- 用户可直接编辑config.yaml
- 不影响核心功能

**建议实现** (预计20分钟):

```python
@config_group.command(name="set")
@click.argument('key')
@click.argument('value')
@click.option('--config', type=click.Path(), default='config.yaml', help='配置文件路径')
@click.option('--type', type=click.Choice(['str', 'int', 'float', 'bool', 'json']), default='str', help='值类型')
def config_set(key, value, config, type):
    """设置配置项

    支持点号分隔的嵌套键,如: data_source.hikyuu_dir

    示例:
        ./run_cli.sh config set data_source.hikyuu_dir /path/to/hikyuu
        ./run_cli.sh config set training.n_estimators 200 --type int
        ./run_cli.sh config set training.learning_rate 0.03 --type float
        ./run_cli.sh config set training.early_stopping true --type bool
        ./run_cli.sh config set training.params '{"a": 1}' --type json
    """
    import yaml
    from pathlib import Path

    config_path = Path(config)

    if not config_path.exists():
        click.echo(f"✗ 配置文件不存在: {config_path}", err=True)
        return

    # 读取配置
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f) or {}
    except Exception as e:
        click.echo(f"✗ 读取配置文件失败: {e}", err=True)
        return

    # 类型转换
    try:
        if type == 'int':
            value = int(value)
        elif type == 'float':
            value = float(value)
        elif type == 'bool':
            value = value.lower() in ('true', 'yes', '1', 'on')
        elif type == 'json':
            import json
            value = json.loads(value)
        # else: str, 保持原样
    except Exception as e:
        click.echo(f"✗ 值类型转换失败: {e}", err=True)
        return

    # 设置嵌套键
    keys = key.split('.')
    current = config_data

    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        current = current[k]

    current[keys[-1]] = value

    # 写回配置文件
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, allow_unicode=True, default_flow_style=False)

        click.echo(f"✓ 已设置 {key} = {value}")
        click.echo(f"✓ 配置已保存到 {config_path}")

    except Exception as e:
        click.echo(f"✗ 保存配置文件失败: {e}", err=True)
```

---

### 任务5: `predict` 方法实现 🟡 P1

**位置**: [src/adapters/qlib/qlib_model_trainer_adapter.py:212-236](../src/adapters/qlib/qlib_model_trainer_adapter.py#L212-L236)

**当前状态**:
```python
async def predict(self, model: Model, input_data: Any) -> List[Prediction]:
    """
    生成预测

    Args:
        model: 训练好的模型
        input_data: 输入数据(可以是DataFrame或KLineData列表)

    Returns:
        List[Prediction]: 预测结果列表
    """
    # TODO: 实现预测逻辑
    return []  # ❌ 空壳实现
```

**问题描述**:
- predict方法完全未实现
- 无法用训练好的模型生成预测
- **阻塞后续信号转换和回测流程**

**影响范围**: 🔴 **高**
- **阻塞完整工作流**
- 预测→信号→回测链条断裂

**建议实现** (预计1小时):

```python
async def predict(self, model: Model, input_data: Any) -> List[Prediction]:
    """
    生成预测

    Args:
        model: 训练好的模型
        input_data: 输入数据(可以是DataFrame或KLineData列表)

    Returns:
        List[Prediction]: 预测结果列表
    """
    if not isinstance(input_data, pd.DataFrame):
        # 如果是KLineData列表,先转换为DataFrame
        from utils.data_conversion import convert_kline_to_training_data
        input_data = convert_kline_to_training_data(
            input_data,
            add_features=True,
            add_labels=False  # 预测时不需要标签
        )

    if input_data.empty:
        raise ValueError("Input data is empty")

    # 检查模型状态
    if model.status != ModelStatus.TRAINED:
        raise ValueError(f"Model status is {model.status}, expected TRAINED")

    # 准备特征
    exclude_cols = ['stock_code', 'timestamp', 'label_return', 'label_direction', 'label_multiclass']
    feature_cols = [col for col in input_data.columns if col not in exclude_cols]

    if not feature_cols:
        raise ValueError("No feature columns found in input data")

    X = input_data[feature_cols].fillna(0)

    # 生成预测
    try:
        predictions_array = self._model.predict(X)
    except Exception as e:
        raise RuntimeError(f"Model prediction failed: {e}")

    # 转换为Prediction实体列表
    from domain.entities.prediction import Prediction
    from domain.value_objects.stock_code import StockCode
    from decimal import Decimal

    predictions = []
    for i, pred_value in enumerate(predictions_array):
        # 获取对应的行信息
        row = input_data.iloc[i]

        prediction = Prediction(
            stock_code=StockCode(row.get('stock_code', 'unknown')),
            prediction_date=row.get('timestamp', pd.Timestamp.now()),
            predicted_value=Decimal(str(pred_value)),
            confidence=self._calculate_confidence(pred_value, predictions_array),
            model_id=model.id,
            features=dict(zip(feature_cols, X.iloc[i].values))  # 保存输入特征
        )
        predictions.append(prediction)

    return predictions

def _calculate_confidence(self, value: float, all_values: np.ndarray) -> Decimal:
    """
    根据预测值在全体分布中的位置计算置信度

    置信度计算逻辑:
    - 预测值越接近极端值(最高或最低),置信度越高
    - 预测值接近中位数,置信度较低
    """
    if len(all_values) < 2:
        return Decimal("0.5")

    # 计算百分位
    percentile = scipy.stats.percentileofscore(all_values, value)

    # 转换为置信度: 0-50%映射到0.5-1.0, 50-100%映射到1.0-0.5
    if percentile <= 50:
        confidence = 0.5 + (50 - percentile) / 100  # 0-50% -> 1.0-0.5
    else:
        confidence = 0.5 + (percentile - 50) / 100  # 50-100% -> 0.5-1.0

    return Decimal(str(round(confidence, 4)))
```

**验证**:
```python
# 测试脚本
import asyncio
from domain.entities.model import Model, ModelType, ModelStatus
from adapters.qlib.qlib_model_trainer_adapter import QlibModelTrainerAdapter
import pandas as pd

async def test_predict():
    # 创建测试模型
    model = Model(
        model_type=ModelType.LGBM,
        hyperparameters={'n_estimators': 50}
    )
    model.status = ModelStatus.TRAINED

    # 创建测试数据
    test_data = pd.DataFrame({
        'stock_code': ['sh600036'] * 10,
        'timestamp': pd.date_range('2024-01-01', periods=10),
        'ma5': [10.0 + i for i in range(10)],
        'ma10': [10.5 + i for i in range(10)],
        'return': [0.01 * i for i in range(10)]
    })

    # 预测
    trainer = QlibModelTrainerAdapter()
    predictions = await trainer.predict(model, test_data)

    print(f"✓ 生成 {len(predictions)} 个预测")
    for pred in predictions[:3]:
        print(f"  {pred.stock_code.value} @ {pred.prediction_date}: {pred.predicted_value} (置信度: {pred.confidence})")

asyncio.run(test_predict())
```

---

### 任务6: 训练数据缓存机制 🟢 P3

**位置**: [docs/model_training_data_flow.py:64-76](../docs/model_training_data_flow.py#L64-L76)

**当前状态**:
```python
# Line 64-76
if use_cache:
    # 从数据库缓存读取训练数据
    cached_data = await training_data_cache.get(
        stock_codes=stock_codes,
        date_range=date_range,
        feature_config=feature_config
    )
    if cached_data:
        return cached_data
    else:
        raise NotImplementedError("缓存功能尚未实现")  # ❌ 未实现
```

**问题描述**:
- 每次训练都重新加载和计算特征
- 大量重复计算,浪费时间
- 对于指数成分股训练尤其耗时

**影响范围**: 🟢 **低**
- 不影响功能正确性
- 影响批量训练效率

**建议实现** (预计2小时):

这个任务较复杂,涉及:
1. 设计缓存表结构
2. 实现缓存DAO(Data Access Object)
3. 实现缓存命中和失效逻辑
4. 集成到训练流程

**建议暂时不实现**,理由:
- P3低优先级
- MVP阶段训练量不大
- 可在P2阶段实现
- 当前用户可手动保存CSV复用

---

## 优先级建议

### 🔴 P1 (必须实施,阻塞核心功能)

1. **任务5: predict方法实现** (1小时)
   - 阻塞预测→信号→回测完整链条
   - 必须在发布MVP前完成

### 🟡 P2 (建议实施,提升用户体验)

2. **任务3: model list/delete** (30分钟)
   - 提升模型管理能力
   - 用户高频使用场景

3. **任务2: 超参数配置** (20分钟)
   - 提升模型调优能力
   - 实验迭代必需

4. **任务1: data list** (30分钟)
   - 方便数据管理
   - 降低学习成本

### 🟢 P3 (可选实施,锦上添花)

5. **任务4: config set持久化** (20分钟)
   - 用户可直接编辑YAML
   - 非刚需

6. **任务6: 训练数据缓存** (2小时+)
   - 仅大规模训练时有价值
   - 可后续优化

---

## 实施计划

### 第一阶段 (立即实施,1小时)

**目标**: 解除P1阻塞,实现完整工作流

- [ ] 任务5: 实现predict方法 (1小时)
- [ ] 验证完整流程: 数据→训练→预测→信号→回测

### 第二阶段 (本周内,1.5小时)

**目标**: 提升用户体验

- [ ] 任务3: 实现model list/delete (30分钟)
- [ ] 任务2: 实现超参数配置 (20分钟)
- [ ] 任务1: 实现data list (30分钟)
- [ ] 更新CLI文档

### 第三阶段 (P2迭代,可选)

**目标**: 完善辅助功能

- [ ] 任务4: config set持久化 (20分钟)
- [ ] 任务6: 训练数据缓存 (2小时+)

---

## 依赖关系

```
任务5 (predict)
  ↓ [阻塞]
CLI集成 (model predict命令)
  ↓ [阻塞]
完整工作流验证
  ↓
MVP发布

任务2/3 (超参数/模型管理)
  ↓ [提升]
用户体验

任务1/4 (data list / config set)
  ↓ [可选]
便利性功能
```

---

## 验收标准

### 任务5 (P1)

- [ ] predict方法返回非空Prediction列表
- [ ] 预测值类型正确(Decimal)
- [ ] 置信度在0-1范围内
- [ ] 单元测试通过
- [ ] 集成到CLI命令

### 任务2 (P2)

- [ ] 支持命令行传入超参数JSON
- [ ] 支持配置文件加载超参数
- [ ] 提供模型类型默认值
- [ ] 文档更新

### 任务3 (P2)

- [ ] model list显示完整模型信息
- [ ] 支持多种输出格式(table/json/csv)
- [ ] model delete功能正常
- [ ] 有确认机制防误删

### 任务1 (P2)

- [ ] data list扫描数据目录
- [ ] 显示文件基本信息(大小、修改时间)
- [ ] 支持多种输出格式

---

## 参考文档

- [P0_COMPLETION_REPORT.md](P0_COMPLETION_REPORT.md) - P0实施报告
- [FEATURE_GAP_ANALYSIS.md](FEATURE_GAP_ANALYSIS.md) - 功能缺口分析
- [BUG_FIXES_SUMMARY.md](BUG_FIXES_SUMMARY.md) - Bug修复总结

---

**文档创建日期**: 2025-11-14
**下一步**: 立即实施任务5 (predict方法),解除P1阻塞
