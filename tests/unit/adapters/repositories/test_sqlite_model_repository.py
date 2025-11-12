"""
SQLiteModelRepository 单元测试

测试 SQLiteModelRepository 实现 IModelRepository 接口,
使用 SQLite 数据库存储模型元数据
"""

import pytest

from domain.entities.model import Model, ModelType, ModelStatus


class TestSQLiteModelRepository:
    """测试 SQLiteModelRepository"""

    @pytest.fixture
    async def repository(self):
        """仓储 fixture - 使用内存数据库"""
        from adapters.repositories.sqlite_model_repository import SQLiteModelRepository

        # 使用内存数据库 :memory:
        repo = SQLiteModelRepository(db_path=":memory:")
        await repo.initialize()
        yield repo
        await repo.close()

    @pytest.fixture
    def sample_model(self) -> Model:
        """示例模型 fixture"""
        return Model(
            model_type=ModelType.LGBM,
            hyperparameters={"learning_rate": 0.01, "num_leaves": 31},
        )

    @pytest.fixture
    def trained_model(self) -> Model:
        """已训练模型 fixture"""
        model = Model(
            model_type=ModelType.MLP,
            hyperparameters={"hidden_layers": [64, 32]},
        )
        model.mark_as_trained(metrics={"accuracy": 0.85, "f1_score": 0.82})
        return model

    @pytest.mark.asyncio
    async def test_save_model(self, repository, sample_model):
        """
        测试保存模型

        验证:
        1. 保存模型到数据库
        2. 可以重新查询到
        3. 属性正确保存
        """
        # 执行
        await repository.save(sample_model)

        # 验证
        loaded_model = await repository.find_by_id(sample_model.id)
        assert loaded_model is not None
        assert loaded_model.id == sample_model.id
        assert loaded_model.model_type == ModelType.LGBM
        assert loaded_model.hyperparameters["learning_rate"] == 0.01
        assert loaded_model.status == ModelStatus.UNTRAINED

    @pytest.mark.asyncio
    async def test_find_by_id(self, repository, sample_model):
        """
        测试根据ID查找模型

        验证:
        1. 保存模型
        2. 根据ID查找
        3. 找不到返回 None
        """
        # 保存模型
        await repository.save(sample_model)

        # 验证：找到模型
        found_model = await repository.find_by_id(sample_model.id)
        assert found_model is not None
        assert found_model.id == sample_model.id

        # 验证：找不到模型
        not_found = await repository.find_by_id("nonexistent-id")
        assert not_found is None

    @pytest.mark.asyncio
    async def test_find_all(self, repository, sample_model, trained_model):
        """
        测试查找所有模型

        验证:
        1. 保存多个模型
        2. find_all 返回所有模型
        3. 结果列表正确
        """
        # 保存多个模型
        await repository.save(sample_model)
        await repository.save(trained_model)

        # 执行
        all_models = await repository.find_all()

        # 验证
        assert len(all_models) == 2
        model_ids = [m.id for m in all_models]
        assert sample_model.id in model_ids
        assert trained_model.id in model_ids

    @pytest.mark.asyncio
    async def test_delete_model(self, repository, sample_model):
        """
        测试删除模型

        验证:
        1. 保存模型
        2. 删除模型
        3. 查询不到已删除的模型
        """
        # 保存模型
        await repository.save(sample_model)

        # 验证保存成功
        found = await repository.find_by_id(sample_model.id)
        assert found is not None

        # 执行删除
        await repository.delete(sample_model.id)

        # 验证删除成功
        not_found = await repository.find_by_id(sample_model.id)
        assert not_found is None

    @pytest.mark.asyncio
    async def test_update_model(self, repository, sample_model):
        """
        测试更新模型

        验证:
        1. 保存模型
        2. 修改模型属性
        3. 重新保存（更新）
        4. 查询到更新后的数据
        """
        # 保存初始模型
        await repository.save(sample_model)

        # 修改模型
        sample_model.mark_as_trained(metrics={"accuracy": 0.9, "precision": 0.88})

        # 更新模型
        await repository.save(sample_model)

        # 验证更新
        loaded_model = await repository.find_by_id(sample_model.id)
        assert loaded_model is not None
        assert loaded_model.status == ModelStatus.TRAINED
        assert loaded_model.metrics["accuracy"] == 0.9
        assert loaded_model.training_date is not None

    @pytest.mark.asyncio
    async def test_hyperparameters_serialization(self, repository):
        """
        测试超参数序列化

        验证:
        1. 复杂超参数正确保存
        2. 包含嵌套结构、列表等
        3. 读取时正确反序列化
        """
        # 创建包含复杂超参数的模型
        complex_model = Model(
            model_type=ModelType.TRANSFORMER,
            hyperparameters={
                "layers": [128, 64, 32],
                "attention_heads": 8,
                "dropout_rates": {"encoder": 0.1, "decoder": 0.2},
                "activation": "relu",
            },
        )

        # 保存
        await repository.save(complex_model)

        # 验证
        loaded_model = await repository.find_by_id(complex_model.id)
        assert loaded_model is not None
        assert loaded_model.hyperparameters["layers"] == [128, 64, 32]
        assert loaded_model.hyperparameters["attention_heads"] == 8
        assert loaded_model.hyperparameters["dropout_rates"]["encoder"] == 0.1

    @pytest.mark.asyncio
    async def test_filter_by_status(self, repository, sample_model, trained_model):
        """
        测试按状态过滤模型

        验证:
        1. 保存不同状态的模型
        2. 按状态查询
        3. 返回正确的子集
        """
        # 保存模型
        await repository.save(sample_model)  # UNTRAINED
        await repository.save(trained_model)  # TRAINED

        # 创建并保存已部署的模型
        deployed_model = Model(model_type=ModelType.GRU, hyperparameters={"units": 64})
        deployed_model.mark_as_trained(metrics={"accuracy": 0.87})
        deployed_model.deploy()
        await repository.save(deployed_model)

        # 验证：查找所有已训练的模型
        all_models = await repository.find_all()
        trained_models = [m for m in all_models if m.status == ModelStatus.TRAINED]
        assert len(trained_models) == 1

        # 验证：查找所有未训练的模型
        untrained_models = [m for m in all_models if m.status == ModelStatus.UNTRAINED]
        assert len(untrained_models) == 1

    @pytest.mark.asyncio
    async def test_empty_database(self, repository):
        """
        测试空数据库

        验证:
        1. 初始化后数据库为空
        2. find_all 返回空列表
        3. find_by_id 返回 None
        """
        # 验证 find_all
        all_models = await repository.find_all()
        assert len(all_models) == 0

        # 验证 find_by_id
        not_found = await repository.find_by_id("some-id")
        assert not_found is None
