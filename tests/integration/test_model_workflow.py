"""
Model Workflow Integration Tests

测试模型训练的完整工作流
"""

from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from domain.entities.model import Model, ModelType, ModelStatus


@pytest.mark.asyncio
async def test_train_model_integration(
    train_model_use_case, sample_kline_data, mock_model_repository
):
    """
    测试完整的模型训练流程

    流程:
    1. 创建未训练模型
    2. 准备训练数据
    3. 调用 TrainModelUseCase
    4. 验证模型被训练
    5. 验证模型被保存到仓库
    """
    # Arrange
    model = Model(
        model_type=ModelType.LGBM,
        hyperparameters={"learning_rate": 0.01, "n_estimators": 100},
    )
    assert model.status == ModelStatus.UNTRAINED

    # Act
    trained_model = await train_model_use_case.execute(
        model=model, training_data=sample_kline_data
    )

    # Assert
    assert trained_model.status == ModelStatus.TRAINED
    assert trained_model.is_trained()
    assert trained_model.metrics is not None
    assert "accuracy" in trained_model.metrics
    assert trained_model.training_date is not None

    # 验证模型被保存到repository
    saved_model = await mock_model_repository.find_by_id(trained_model.id)
    assert saved_model is not None
    assert saved_model.status == trained_model.status


@pytest.mark.asyncio
async def test_train_multiple_models_integration(
    train_model_use_case, sample_kline_data
):
    """
    测试训练多个模型

    场景: 批量训练不同类型的模型
    """
    # Arrange
    model_types = [ModelType.LGBM, ModelType.MLP, ModelType.LSTM]
    trained_models = []

    # Act
    for model_type in model_types:
        model = Model(
            model_type=model_type, hyperparameters={"learning_rate": 0.01}
        )
        trained_model = await train_model_use_case.execute(
            model=model, training_data=sample_kline_data
        )
        trained_models.append(trained_model)

    # Assert
    assert len(trained_models) == 3
    assert all(m.is_trained() for m in trained_models)
    assert [m.model_type for m in trained_models] == model_types


@pytest.mark.asyncio
async def test_train_model_with_validation(mock_model_trainer, mock_model_repository):
    """
    测试模型训练后的指标验证

    场景: 训练后指标不达标应该拒绝
    """
    # Arrange
    from use_cases.model.train_model import TrainModelUseCase

    # Mock 训练器返回低指标模型
    async def train_with_low_metrics(model, training_data):
        try:
            # 使用低于阈值的指标会触发异常
            model.mark_as_trained({"accuracy": 0.3}, threshold=0.5)
        except ValueError:
            # 重新抛出异常
            raise
        return model

    mock_model_trainer.train.side_effect = train_with_low_metrics
    use_case = TrainModelUseCase(
        trainer=mock_model_trainer, repository=mock_model_repository
    )

    model = Model(model_type=ModelType.LGBM, hyperparameters={"learning_rate": 0.01})

    # Act & Assert
    with pytest.raises(ValueError, match="metrics below threshold"):
        await use_case.execute(model=model, training_data=[])


@pytest.mark.asyncio
async def test_train_model_handles_trainer_error(
    mock_model_trainer, mock_model_repository, sample_kline_data
):
    """
    测试处理训练器错误

    场景: 训练器抛出异常
    """
    # Arrange
    from use_cases.model.train_model import TrainModelUseCase

    mock_model_trainer.train.side_effect = Exception("Training failed")
    use_case = TrainModelUseCase(
        trainer=mock_model_trainer, repository=mock_model_repository
    )

    model = Model(model_type=ModelType.LGBM, hyperparameters={"learning_rate": 0.01})

    # Act & Assert
    with pytest.raises(Exception, match="Training failed"):
        await use_case.execute(model=model, training_data=sample_kline_data)

    # 验证模型没有被保存
    saved_model = await mock_model_repository.find_by_id(model.id)
    assert saved_model is None


@pytest.mark.asyncio
async def test_train_model_repository_persistence(
    mock_model_trainer, mock_model_repository, sample_kline_data
):
    """
    测试模型持久化

    验证:
    1. 模型被保存
    2. 模型可以被检索
    """
    # Arrange
    from use_cases.model.train_model import TrainModelUseCase

    use_case = TrainModelUseCase(
        trainer=mock_model_trainer, repository=mock_model_repository
    )

    model = Model(model_type=ModelType.LGBM, hyperparameters={"learning_rate": 0.01})

    # Act
    trained_model = await use_case.execute(model=model, training_data=sample_kline_data)

    # Assert - 验证保存和检索
    saved_model = await mock_model_repository.find_by_id(trained_model.id)
    assert saved_model is not None
    assert saved_model.id == trained_model.id

    # Act - 检索模型
    retrieved_model = await mock_model_repository.find_by_id(trained_model.id)

    # Assert
    assert retrieved_model is not None
    assert retrieved_model.id == trained_model.id
    assert retrieved_model.is_trained()


@pytest.mark.asyncio
async def test_train_model_with_hyperparameter_tuning(
    mock_model_trainer, mock_model_repository, sample_kline_data
):
    """
    测试超参数调优场景

    场景: 训练多个具有不同超参数的模型，选择最佳模型
    """
    # Arrange
    from use_cases.model.train_model import TrainModelUseCase

    use_case = TrainModelUseCase(
        trainer=mock_model_trainer, repository=mock_model_repository
    )

    hyperparameter_sets = [
        {"learning_rate": 0.01, "n_estimators": 100},
        {"learning_rate": 0.05, "n_estimators": 200},
        {"learning_rate": 0.1, "n_estimators": 150},
    ]

    trained_models = []

    # Act
    for i, hyperparams in enumerate(hyperparameter_sets):
        # Mock 不同的准确率
        accuracy = 0.7 + i * 0.05

        async def train_with_specific_accuracy(model, training_data, acc=accuracy):
            model.mark_as_trained({"accuracy": acc})
            return model

        mock_model_trainer.train.side_effect = train_with_specific_accuracy

        model = Model(model_type=ModelType.LGBM, hyperparameters=hyperparams)
        trained_model = await use_case.execute(
            model=model, training_data=sample_kline_data
        )
        trained_models.append(trained_model)

    # Assert
    assert len(trained_models) == 3
    assert all(m.is_trained() for m in trained_models)

    # 验证准确率递增
    accuracies = [m.metrics["accuracy"] for m in trained_models]
    assert accuracies == sorted(accuracies)


@pytest.mark.asyncio
async def test_train_model_with_insufficient_data(
    mock_model_trainer, mock_model_repository
):
    """
    测试训练数据不足的场景

    场景: 训练数据太少应该被拒绝
    """
    # Arrange
    from use_cases.model.train_model import TrainModelUseCase

    mock_model_trainer.train.side_effect = ValueError("Insufficient training data")
    use_case = TrainModelUseCase(
        trainer=mock_model_trainer, repository=mock_model_repository
    )

    model = Model(model_type=ModelType.LGBM, hyperparameters={"learning_rate": 0.01})
    insufficient_data = []  # 空数据

    # Act & Assert
    with pytest.raises(ValueError, match="Insufficient training data"):
        await use_case.execute(model=model, training_data=insufficient_data)


@pytest.mark.asyncio
async def test_train_model_state_transitions(
    mock_model_trainer, mock_model_repository, sample_kline_data
):
    """
    测试模型状态转换

    验证:
    1. UNTRAINED -> TRAINED
    2. TRAINED -> DEPLOYED
    3. DEPLOYED -> ARCHIVED
    """
    # Arrange
    from use_cases.model.train_model import TrainModelUseCase

    use_case = TrainModelUseCase(
        trainer=mock_model_trainer, repository=mock_model_repository
    )

    model = Model(model_type=ModelType.LGBM, hyperparameters={"learning_rate": 0.01})

    # Act - 训练
    assert model.status == ModelStatus.UNTRAINED

    trained_model = await use_case.execute(model=model, training_data=sample_kline_data)

    # Assert - 训练后状态
    assert trained_model.status == ModelStatus.TRAINED

    # Act - 部署
    trained_model.deploy()

    # Assert - 部署后状态
    assert trained_model.status == ModelStatus.DEPLOYED
    assert trained_model.is_deployed()

    # Act - 归档
    trained_model.archive()

    # Assert - 归档后状态
    assert trained_model.status == ModelStatus.ARCHIVED


@pytest.mark.asyncio
async def test_train_model_metrics_tracking(
    mock_model_trainer, mock_model_repository, sample_kline_data
):
    """
    测试训练指标跟踪

    验证: 训练过程中的各种指标被正确记录
    """
    # Arrange
    from use_cases.model.train_model import TrainModelUseCase

    expected_metrics = {
        "accuracy": 0.85,
        "precision": 0.82,
        "recall": 0.88,
        "f1_score": 0.85,
    }

    async def train_with_full_metrics(model, training_data):
        model.mark_as_trained(expected_metrics, threshold=0.5)
        return model

    mock_model_trainer.train.side_effect = train_with_full_metrics
    use_case = TrainModelUseCase(
        trainer=mock_model_trainer, repository=mock_model_repository
    )

    model = Model(model_type=ModelType.LGBM, hyperparameters={"learning_rate": 0.01})

    # Act
    trained_model = await use_case.execute(model=model, training_data=sample_kline_data)

    # Assert
    assert trained_model.metrics == expected_metrics
    assert all(metric in trained_model.metrics for metric in expected_metrics.keys())
