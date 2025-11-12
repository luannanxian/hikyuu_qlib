"""
TrainModelUseCase 单元测试

测试 UC-002: Train Model (训练模型) 用例
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from domain.entities.model import Model, ModelStatus, ModelType
from domain.ports.model_repository import IModelRepository
from domain.ports.model_trainer import IModelTrainer
from use_cases.model.train_model import TrainModelUseCase


class TestTrainModelSuccess:
    """测试成功训练模型"""

    @pytest.mark.asyncio
    async def test_train_model_success(self):
        """测试成功训练模型"""
        # Arrange: 准备 Mock Trainer 和 Repository
        trainer_mock = AsyncMock(spec=IModelTrainer)
        repository_mock = AsyncMock(spec=IModelRepository)

        # 创建未训练的模型
        model = Model(
            model_type=ModelType.LGBM,
            hyperparameters={"learning_rate": 0.01},
        )
        assert model.status == ModelStatus.UNTRAINED

        # Mock trainer 返回已训练模型
        trained_metrics = {"accuracy": Decimal("0.85"), "f1_score": Decimal("0.82")}
        trainer_mock.train.return_value = model
        # 模拟 mark_as_trained 的行为
        model.mark_as_trained(trained_metrics)

        # 创建 Use Case
        use_case = TrainModelUseCase(trainer=trainer_mock, repository=repository_mock)

        # Mock training data
        training_data = MagicMock()

        # Act: 执行用例
        result = await use_case.execute(model=model, training_data=training_data)

        # Assert: 验证结果
        assert result.status == ModelStatus.TRAINED
        assert result.metrics == trained_metrics
        assert result.trained_at is not None

        # 验证 trainer 被正确调用
        trainer_mock.train.assert_called_once_with(
            model=model, training_data=training_data
        )

        # 验证模型被保存到 repository
        repository_mock.save.assert_called_once_with(result)

    @pytest.mark.asyncio
    async def test_train_model_updates_status(self):
        """测试训练过程正确更新模型状态"""
        # Arrange
        trainer_mock = AsyncMock(spec=IModelTrainer)
        repository_mock = AsyncMock(spec=IModelRepository)

        model = Model(
            model_type=ModelType.LGBM,
            hyperparameters={"learning_rate": 0.01},
        )

        # Mock 训练成功
        trained_metrics = {"accuracy": Decimal("0.90")}
        model.mark_as_trained(trained_metrics)
        trainer_mock.train.return_value = model

        use_case = TrainModelUseCase(trainer=trainer_mock, repository=repository_mock)

        # Act
        result = await use_case.execute(model=model, training_data=MagicMock())

        # Assert: 状态从 UNTRAINED → TRAINED
        assert result.status == ModelStatus.TRAINED


class TestTrainModelValidation:
    """测试训练参数验证"""

    @pytest.mark.asyncio
    async def test_train_model_validates_metrics_threshold(self):
        """测试指标阈值验证"""
        # Arrange
        trainer_mock = AsyncMock(spec=IModelTrainer)
        repository_mock = AsyncMock(spec=IModelRepository)

        model = Model(
            model_type=ModelType.LGBM,
            hyperparameters={"learning_rate": 0.01},
        )

        # Mock 训练返回低于阈值的指标
        low_metrics = {"accuracy": Decimal("0.45")}  # < 0.5 threshold
        trainer_mock.train.return_value = model

        use_case = TrainModelUseCase(trainer=trainer_mock, repository=repository_mock)

        # Act & Assert: 指标不达标应该抛出异常
        with pytest.raises(
            ValueError, match="Model metrics below threshold|accuracy.*0.5"
        ):
            model.mark_as_trained(low_metrics)
            await use_case.execute(model=model, training_data=MagicMock())


class TestTrainModelErrorHandling:
    """测试错误处理"""

    @pytest.mark.asyncio
    async def test_train_model_training_failure(self):
        """测试训练失败处理"""
        # Arrange: Mock trainer 抛出异常
        trainer_mock = AsyncMock(spec=IModelTrainer)
        trainer_mock.train.side_effect = Exception("训练数据不足")

        repository_mock = AsyncMock(spec=IModelRepository)

        model = Model(
            model_type=ModelType.LGBM,
            hyperparameters={"learning_rate": 0.01},
        )

        use_case = TrainModelUseCase(trainer=trainer_mock, repository=repository_mock)

        # Act & Assert: 应该传播训练异常
        with pytest.raises(Exception, match="训练数据不足"):
            await use_case.execute(model=model, training_data=MagicMock())

    @pytest.mark.asyncio
    async def test_train_model_saves_to_repository(self):
        """测试模型保存到仓库"""
        # Arrange
        trainer_mock = AsyncMock(spec=IModelTrainer)
        repository_mock = AsyncMock(spec=IModelRepository)

        model = Model(
            model_type=ModelType.LGBM,
            hyperparameters={"learning_rate": 0.01},
        )

        trained_metrics = {"accuracy": Decimal("0.88")}
        model.mark_as_trained(trained_metrics)
        trainer_mock.train.return_value = model

        use_case = TrainModelUseCase(trainer=trainer_mock, repository=repository_mock)

        # Act
        await use_case.execute(model=model, training_data=MagicMock())

        # Assert: 验证保存到 repository
        repository_mock.save.assert_called_once()
        saved_model = repository_mock.save.call_args[0][0]
        assert saved_model.status == ModelStatus.TRAINED
