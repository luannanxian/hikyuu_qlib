"""
Model Entity 单元测试

测试 DR-004: Model (模型) 领域模型
"""

from datetime import datetime

import pytest

from domain.entities.model import Model, ModelStatus, ModelType


class TestModelCreation:
    """测试 Model 创建"""

    def test_create_model_with_all_fields(self):
        """测试创建完整模型"""
        hyperparams = {"n_estimators": 100, "learning_rate": 0.1}
        metrics = {"accuracy": 0.95, "f1_score": 0.92}

        model = Model(
            model_type=ModelType.LGBM,
            hyperparameters=hyperparams,
            training_date=datetime(2024, 1, 15),
            metrics=metrics,
            status=ModelStatus.TRAINED,
        )

        assert model.model_type == ModelType.LGBM
        assert model.hyperparameters == hyperparams
        assert model.training_date == datetime(2024, 1, 15)
        assert model.metrics == metrics
        assert model.status == ModelStatus.TRAINED

    def test_create_model_with_minimal_fields(self):
        """测试创建最小字段模型"""
        model = Model(
            model_type=ModelType.MLP,
            hyperparameters={},
        )

        assert model.model_type == ModelType.MLP
        assert model.hyperparameters == {}
        assert model.training_date is None
        assert model.metrics == {}
        assert model.status == ModelStatus.UNTRAINED


class TestModelIdentity:
    """测试 Model 实体身份"""

    def test_model_has_unique_id(self):
        """验证每个模型有唯一标识"""
        model1 = Model(model_type=ModelType.LGBM, hyperparameters={})
        model2 = Model(model_type=ModelType.LGBM, hyperparameters={})

        # 每个实体有唯一 ID
        assert hasattr(model1, "id")
        assert hasattr(model2, "id")
        assert model1.id != model2.id

    def test_model_equality_based_on_id(self):
        """验证模型相等性基于 ID"""
        model1 = Model(model_type=ModelType.LGBM, hyperparameters={"lr": 0.1})
        model2 = Model(model_type=ModelType.LGBM, hyperparameters={"lr": 0.1})

        # 不同实体不相等(即使参数相同)
        assert model1 != model2

        # 相同实例相等
        assert model1 == model1

    def test_model_hash_based_on_id(self):
        """验证模型哈希基于 ID"""
        model1 = Model(model_type=ModelType.LGBM, hyperparameters={})
        model2 = Model(model_type=ModelType.LGBM, hyperparameters={})

        # 不同 ID 应该有不同 hash
        assert hash(model1) != hash(model2)

        # 可以作为字典键
        model_dict = {model1: "Model A"}
        assert model_dict[model1] == "Model A"


class TestModelStatus:
    """测试模型状态"""

    def test_model_status_types(self):
        """测试不同的模型状态"""
        untrained = Model(
            model_type=ModelType.LGBM,
            hyperparameters={},
            status=ModelStatus.UNTRAINED,
        )
        assert untrained.status == ModelStatus.UNTRAINED

        trained = Model(
            model_type=ModelType.MLP,
            hyperparameters={},
            status=ModelStatus.TRAINED,
        )
        assert trained.status == ModelStatus.TRAINED

        deployed = Model(
            model_type=ModelType.GRU,
            hyperparameters={},
            status=ModelStatus.DEPLOYED,
        )
        assert deployed.status == ModelStatus.DEPLOYED

        archived = Model(
            model_type=ModelType.LSTM,
            hyperparameters={},
            status=ModelStatus.ARCHIVED,
        )
        assert archived.status == ModelStatus.ARCHIVED


class TestModelType:
    """测试模型类型"""

    def test_supported_model_types(self):
        """测试支持的模型类型"""
        # LGBM
        lgbm = Model(model_type=ModelType.LGBM, hyperparameters={})
        assert lgbm.model_type == ModelType.LGBM

        # MLP
        mlp = Model(model_type=ModelType.MLP, hyperparameters={})
        assert mlp.model_type == ModelType.MLP

        # LSTM
        lstm = Model(model_type=ModelType.LSTM, hyperparameters={})
        assert lstm.model_type == ModelType.LSTM

        # GRU
        gru = Model(model_type=ModelType.GRU, hyperparameters={})
        assert gru.model_type == ModelType.GRU

        # Transformer
        transformer = Model(model_type=ModelType.TRANSFORMER, hyperparameters={})
        assert transformer.model_type == ModelType.TRANSFORMER


class TestModelMethods:
    """测试模型方法"""

    def test_is_trained(self):
        """测试模型是否已训练"""
        untrained = Model(
            model_type=ModelType.LGBM,
            hyperparameters={},
            status=ModelStatus.UNTRAINED,
        )
        assert untrained.is_trained() is False

        trained = Model(
            model_type=ModelType.LGBM,
            hyperparameters={},
            status=ModelStatus.TRAINED,
        )
        assert trained.is_trained() is True

        deployed = Model(
            model_type=ModelType.LGBM,
            hyperparameters={},
            status=ModelStatus.DEPLOYED,
        )
        assert deployed.is_trained() is True

    def test_is_deployed(self):
        """测试模型是否已部署"""
        trained = Model(
            model_type=ModelType.LGBM,
            hyperparameters={},
            status=ModelStatus.TRAINED,
        )
        assert trained.is_deployed() is False

        deployed = Model(
            model_type=ModelType.LGBM,
            hyperparameters={},
            status=ModelStatus.DEPLOYED,
        )
        assert deployed.is_deployed() is True

    def test_update_metrics(self):
        """测试更新模型指标"""
        model = Model(model_type=ModelType.LGBM, hyperparameters={})

        # 初始指标为空
        assert model.metrics == {}

        # 更新指标
        new_metrics = {"accuracy": 0.95, "precision": 0.92}
        model.update_metrics(new_metrics)

        assert model.metrics == new_metrics

    def test_deploy(self):
        """测试部署模型"""
        model = Model(
            model_type=ModelType.LGBM,
            hyperparameters={},
            status=ModelStatus.TRAINED,
        )

        # 部署前是 TRAINED 状态
        assert model.status == ModelStatus.TRAINED

        # 部署模型
        model.deploy()

        # 部署后是 DEPLOYED 状态
        assert model.status == ModelStatus.DEPLOYED

    def test_cannot_deploy_untrained_model(self):
        """测试不能部署未训练的模型"""
        model = Model(
            model_type=ModelType.LGBM,
            hyperparameters={},
            status=ModelStatus.UNTRAINED,
        )

        # 部署未训练模型应该抛出异常
        with pytest.raises(ValueError, match="Cannot deploy untrained model"):
            model.deploy()

    def test_archive(self):
        """测试归档模型"""
        model = Model(
            model_type=ModelType.LGBM,
            hyperparameters={},
            status=ModelStatus.TRAINED,
        )

        # 归档前是 TRAINED 状态
        assert model.status == ModelStatus.TRAINED

        # 归档模型
        model.archive()

        # 归档后是 ARCHIVED 状态
        assert model.status == ModelStatus.ARCHIVED


class TestModelStringRepresentation:
    """测试模型字符串表示"""

    def test_model_string_representation(self):
        """验证字符串表示"""
        model = Model(
            model_type=ModelType.LGBM,
            hyperparameters={"n_estimators": 100},
            status=ModelStatus.TRAINED,
        )

        model_str = str(model)
        assert "LGBM" in model_str
        assert "TRAINED" in model_str

        repr_str = repr(model)
        assert "Model" in repr_str
        assert "LGBM" in repr_str
