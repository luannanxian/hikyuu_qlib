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


class TestSQLiteModelRepositoryListModels:
    """测试 SQLiteModelRepository.list_models() 方法"""

    @pytest.fixture
    async def repository(self):
        """仓储 fixture - 使用内存数据库"""
        from adapters.repositories.sqlite_model_repository import SQLiteModelRepository

        repo = SQLiteModelRepository(db_path=":memory:")
        await repo.initialize()
        yield repo
        await repo.close()

    @pytest.mark.asyncio
    async def test_list_models_empty_database(self, repository):
        """
        测试空数据库返回空列表

        验证:
        1. 空数据库
        2. list_models() 返回空列表
        """
        # 执行
        models = await repository.list_models()

        # 验证
        assert models == []
        assert len(models) == 0

    @pytest.mark.asyncio
    async def test_list_models_returns_all_models(self, repository):
        """
        测试返回所有模型（无筛选）

        验证:
        1. 保存多个模型
        2. list_models() 返回所有模型
        """
        # 准备数据
        model1 = Model(
            model_type=ModelType.LGBM,
            hyperparameters={"learning_rate": 0.01},
        )
        model2 = Model(
            model_type=ModelType.MLP,
            hyperparameters={"hidden_layers": [64, 32]},
        )
        model3 = Model(
            model_type=ModelType.LSTM,
            hyperparameters={"units": 128},
        )

        await repository.save(model1)
        await repository.save(model2)
        await repository.save(model3)

        # 执行
        models = await repository.list_models()

        # 验证
        assert len(models) == 3
        model_ids = [m.id for m in models]
        assert model1.id in model_ids
        assert model2.id in model_ids
        assert model3.id in model_ids

    @pytest.mark.asyncio
    async def test_list_models_filter_by_status(self, repository):
        """
        测试按status筛选

        验证:
        1. 保存不同状态的模型
        2. 按status筛选
        3. 只返回匹配状态的模型
        """
        # 准备数据：UNTRAINED
        untrained_model = Model(
            model_type=ModelType.LGBM,
            hyperparameters={"learning_rate": 0.01},
        )
        await repository.save(untrained_model)

        # 准备数据：TRAINED
        trained_model = Model(
            model_type=ModelType.MLP,
            hyperparameters={"hidden_layers": [64, 32]},
        )
        trained_model.mark_as_trained(metrics={"accuracy": 0.85})
        await repository.save(trained_model)

        # 准备数据：DEPLOYED
        deployed_model = Model(
            model_type=ModelType.LSTM,
            hyperparameters={"units": 128},
        )
        deployed_model.mark_as_trained(metrics={"accuracy": 0.87})
        deployed_model.deploy()
        await repository.save(deployed_model)

        # 准备数据：ARCHIVED
        archived_model = Model(
            model_type=ModelType.GRU,
            hyperparameters={"units": 64},
        )
        archived_model.archive()
        await repository.save(archived_model)

        # 执行：筛选 TRAINED
        trained_models = await repository.list_models(status=ModelStatus.TRAINED)

        # 验证
        assert len(trained_models) == 1
        assert trained_models[0].id == trained_model.id
        assert trained_models[0].status == ModelStatus.TRAINED

        # 执行：筛选 DEPLOYED
        deployed_models = await repository.list_models(status=ModelStatus.DEPLOYED)

        # 验证
        assert len(deployed_models) == 1
        assert deployed_models[0].id == deployed_model.id
        assert deployed_models[0].status == ModelStatus.DEPLOYED

        # 执行：筛选 UNTRAINED
        untrained_models = await repository.list_models(status=ModelStatus.UNTRAINED)

        # 验证
        assert len(untrained_models) == 1
        assert untrained_models[0].id == untrained_model.id

    @pytest.mark.asyncio
    async def test_list_models_filter_by_model_type(self, repository):
        """
        测试按model_type筛选

        验证:
        1. 保存不同类型的模型
        2. 按model_type筛选
        3. 只返回匹配类型的模型
        """
        # 准备数据：LGBM
        lgbm_model1 = Model(
            model_type=ModelType.LGBM,
            hyperparameters={"learning_rate": 0.01},
        )
        lgbm_model2 = Model(
            model_type=ModelType.LGBM,
            hyperparameters={"learning_rate": 0.02},
        )
        await repository.save(lgbm_model1)
        await repository.save(lgbm_model2)

        # 准备数据：MLP
        mlp_model = Model(
            model_type=ModelType.MLP,
            hyperparameters={"hidden_layers": [64, 32]},
        )
        await repository.save(mlp_model)

        # 准备数据：LSTM
        lstm_model = Model(
            model_type=ModelType.LSTM,
            hyperparameters={"units": 128},
        )
        await repository.save(lstm_model)

        # 执行：筛选 LGBM
        lgbm_models = await repository.list_models(model_type=ModelType.LGBM)

        # 验证
        assert len(lgbm_models) == 2
        model_ids = [m.id for m in lgbm_models]
        assert lgbm_model1.id in model_ids
        assert lgbm_model2.id in model_ids
        assert all(m.model_type == ModelType.LGBM for m in lgbm_models)

        # 执行：筛选 MLP
        mlp_models = await repository.list_models(model_type=ModelType.MLP)

        # 验证
        assert len(mlp_models) == 1
        assert mlp_models[0].id == mlp_model.id
        assert mlp_models[0].model_type == ModelType.MLP

    @pytest.mark.asyncio
    async def test_list_models_with_limit(self, repository):
        """
        测试limit限制返回数量

        验证:
        1. 保存多个模型
        2. 使用limit参数
        3. 只返回指定数量的模型
        """
        # 准备数据：保存5个模型
        models = []
        for i in range(5):
            model = Model(
                model_type=ModelType.LGBM,
                hyperparameters={"learning_rate": 0.01 * (i + 1)},
            )
            await repository.save(model)
            models.append(model)

        # 执行：limit=3
        limited_models = await repository.list_models(limit=3)

        # 验证
        assert len(limited_models) == 3

        # 执行：limit=1
        one_model = await repository.list_models(limit=1)

        # 验证
        assert len(one_model) == 1

        # 执行：limit=10 (超过实际数量)
        all_models = await repository.list_models(limit=10)

        # 验证
        assert len(all_models) == 5

    @pytest.mark.asyncio
    async def test_list_models_ordered_by_created_at_desc(self, repository):
        """
        测试按创建时间倒序排列

        验证:
        1. 按顺序保存多个模型
        2. list_models() 返回按创建时间倒序排列的结果
        3. 最新创建的模型排在最前面
        """
        import asyncio

        # 准备数据：按顺序保存3个模型
        model1 = Model(
            model_type=ModelType.LGBM,
            hyperparameters={"learning_rate": 0.01},
        )
        await repository.save(model1)
        await asyncio.sleep(0.01)  # 确保时间戳不同

        model2 = Model(
            model_type=ModelType.MLP,
            hyperparameters={"hidden_layers": [64, 32]},
        )
        await repository.save(model2)
        await asyncio.sleep(0.01)

        model3 = Model(
            model_type=ModelType.LSTM,
            hyperparameters={"units": 128},
        )
        await repository.save(model3)

        # 执行
        models = await repository.list_models()

        # 验证：倒序排列，最新的在前面
        assert len(models) == 3
        assert models[0].id == model3.id  # 最新
        assert models[1].id == model2.id
        assert models[2].id == model1.id  # 最旧

    @pytest.mark.asyncio
    async def test_list_models_multiple_filters(self, repository):
        """
        测试同时使用多个筛选条件

        验证:
        1. 保存多个不同类型和状态的模型
        2. 同时使用 status、model_type、limit 筛选
        3. 返回同时满足所有条件的模型
        """
        # 准备数据：LGBM TRAINED
        lgbm_trained1 = Model(
            model_type=ModelType.LGBM,
            hyperparameters={"learning_rate": 0.01},
        )
        lgbm_trained1.mark_as_trained(metrics={"accuracy": 0.85})
        await repository.save(lgbm_trained1)

        # 准备数据：LGBM TRAINED
        lgbm_trained2 = Model(
            model_type=ModelType.LGBM,
            hyperparameters={"learning_rate": 0.02},
        )
        lgbm_trained2.mark_as_trained(metrics={"accuracy": 0.86})
        await repository.save(lgbm_trained2)

        # 准备数据：LGBM UNTRAINED
        lgbm_untrained = Model(
            model_type=ModelType.LGBM,
            hyperparameters={"learning_rate": 0.03},
        )
        await repository.save(lgbm_untrained)

        # 准备数据：MLP TRAINED
        mlp_trained = Model(
            model_type=ModelType.MLP,
            hyperparameters={"hidden_layers": [64, 32]},
        )
        mlp_trained.mark_as_trained(metrics={"accuracy": 0.87})
        await repository.save(mlp_trained)

        # 执行：筛选 LGBM + TRAINED
        lgbm_trained_models = await repository.list_models(
            model_type=ModelType.LGBM,
            status=ModelStatus.TRAINED,
        )

        # 验证
        assert len(lgbm_trained_models) == 2
        assert all(m.model_type == ModelType.LGBM for m in lgbm_trained_models)
        assert all(m.status == ModelStatus.TRAINED for m in lgbm_trained_models)

        # 执行：筛选 LGBM + TRAINED + limit=1
        limited_lgbm_trained = await repository.list_models(
            model_type=ModelType.LGBM,
            status=ModelStatus.TRAINED,
            limit=1,
        )

        # 验证
        assert len(limited_lgbm_trained) == 1
        assert limited_lgbm_trained[0].model_type == ModelType.LGBM
        assert limited_lgbm_trained[0].status == ModelStatus.TRAINED


class TestSQLiteModelRepositoryDelete:
    """测试 SQLiteModelRepository.delete() 方法的增强功能"""

    @pytest.fixture
    async def repository(self):
        """仓储 fixture - 使用内存数据库"""
        from adapters.repositories.sqlite_model_repository import SQLiteModelRepository

        repo = SQLiteModelRepository(db_path=":memory:")
        await repo.initialize()
        yield repo
        await repo.close()

    @pytest.mark.asyncio
    async def test_delete_existing_model_success(self, repository):
        """
        测试成功删除存在的模型

        验证:
        1. 保存模型
        2. 删除模型
        3. 删除后无法查询到
        """
        # 准备数据
        model = Model(
            model_type=ModelType.LGBM,
            hyperparameters={"learning_rate": 0.01},
        )
        await repository.save(model)

        # 验证保存成功
        found = await repository.find_by_id(model.id)
        assert found is not None

        # 执行删除
        await repository.delete(model.id)

        # 验证删除成功
        not_found = await repository.find_by_id(model.id)
        assert not_found is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_model_raises_exception(self, repository):
        """
        测试删除不存在的模型抛出异常

        验证:
        1. 尝试删除不存在的模型
        2. 抛出 ValueError 异常
        3. 异常消息包含模型ID
        """
        nonexistent_id = "nonexistent-model-id"

        # 执行并验证
        with pytest.raises(ValueError) as exc_info:
            await repository.delete(nonexistent_id)

        # 验证异常消息
        assert "not found" in str(exc_info.value).lower()
        assert nonexistent_id in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_verifies_model_removed(self, repository):
        """
        测试删除后确实无法查询到模型

        验证:
        1. 保存多个模型
        2. 删除其中一个
        3. 只有被删除的模型查不到
        4. 其他模型仍然存在
        """
        # 准备数据
        model1 = Model(
            model_type=ModelType.LGBM,
            hyperparameters={"learning_rate": 0.01},
        )
        model2 = Model(
            model_type=ModelType.MLP,
            hyperparameters={"hidden_layers": [64, 32]},
        )
        await repository.save(model1)
        await repository.save(model2)

        # 执行：删除 model1
        await repository.delete(model1.id)

        # 验证：model1 不存在
        assert await repository.find_by_id(model1.id) is None

        # 验证：model2 仍然存在
        found_model2 = await repository.find_by_id(model2.id)
        assert found_model2 is not None
        assert found_model2.id == model2.id
