"""
GeneratePredictionsUseCase 单元测试

测试 UC-003: Generate Predictions (生成预测) 用例
"""

import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from domain.entities.model import Model, ModelStatus, ModelType
from domain.entities.prediction import Prediction, PredictionBatch
from domain.ports.model_repository import IModelRepository
from domain.ports.model_trainer import IModelTrainer
from domain.value_objects.stock_code import StockCode
from use_cases.model.generate_predictions import GeneratePredictionsUseCase


class TestGeneratePredictionsSuccess:
    """测试成功生成预测"""

    @pytest.mark.asyncio
    async def test_generate_predictions_success(self):
        """测试成功生成预测"""
        # Arrange: 准备 Mock Repository 和 Trainer
        repository_mock = AsyncMock(spec=IModelRepository)
        trainer_mock = AsyncMock(spec=IModelTrainer)

        # 创建已训练的模型
        model = Model(
            model_type=ModelType.LGBM,
            hyperparameters={"learning_rate": 0.01},
            status=ModelStatus.TRAINED,
        )
        model_id = model.id

        # Mock repository 返回模型
        repository_mock.find_by_id.return_value = model

        # Mock trainer 返回预测结果
        mock_predictions = [
            Prediction(
                stock_code=StockCode("sh600000"),
                prediction_date=datetime(2024, 1, 10),
                predicted_value=Decimal("0.05"),
                confidence=Decimal("0.85"),
            ),
            Prediction(
                stock_code=StockCode("sz000001"),
                prediction_date=datetime(2024, 1, 10),
                predicted_value=Decimal("-0.02"),
                confidence=Decimal("0.78"),
            ),
        ]
        trainer_mock.predict.return_value = mock_predictions

        # 创建 Use Case
        use_case = GeneratePredictionsUseCase(
            repository=repository_mock, trainer=trainer_mock
        )

        # Mock input data
        input_data = MagicMock()

        # Act: 执行用例
        result = await use_case.execute(model_id=model_id, input_data=input_data)

        # Assert: 验证结果
        assert isinstance(result, PredictionBatch)
        assert result.model_id == model_id
        assert result.size() == 2
        assert len(result.predictions) == 2

        # 验证 repository 被正确调用
        repository_mock.find_by_id.assert_called_once_with(model_id)

        # 验证 trainer 被正确调用
        trainer_mock.predict.assert_called_once_with(model=model, input_data=input_data)

    @pytest.mark.asyncio
    async def test_generate_predictions_creates_batch(self):
        """测试创建 PredictionBatch 聚合"""
        # Arrange
        repository_mock = AsyncMock(spec=IModelRepository)
        trainer_mock = AsyncMock(spec=IModelTrainer)

        model = Model(
            model_type=ModelType.LGBM,
            hyperparameters={},
            status=ModelStatus.TRAINED,
        )
        repository_mock.find_by_id.return_value = model

        mock_predictions = [
            Prediction(
                stock_code=StockCode("sh600000"),
                prediction_date=datetime(2024, 1, 10),
                predicted_value=Decimal("0.03"),
                confidence=Decimal("0.90"),
            )
        ]
        trainer_mock.predict.return_value = mock_predictions

        use_case = GeneratePredictionsUseCase(
            repository=repository_mock, trainer=trainer_mock
        )

        # Act
        result = await use_case.execute(model_id=model.id, input_data=MagicMock())

        # Assert: 验证创建了 PredictionBatch
        assert isinstance(result, PredictionBatch)
        assert result.model_id == model.id
        assert result.batch_date is not None
        assert result.size() == 1


class TestGeneratePredictionsValidation:
    """测试输入验证"""

    @pytest.mark.asyncio
    async def test_generate_predictions_model_not_found(self):
        """测试模型未找到异常"""
        # Arrange: Mock repository 返回 None
        repository_mock = AsyncMock(spec=IModelRepository)
        repository_mock.find_by_id.return_value = None
        trainer_mock = AsyncMock(spec=IModelTrainer)

        use_case = GeneratePredictionsUseCase(
            repository=repository_mock, trainer=trainer_mock
        )

        # Act & Assert: 模型未找到应该抛出异常
        with pytest.raises(ValueError, match="Model.*not found"):
            await use_case.execute(model_id="non-existent-id", input_data=MagicMock())

    @pytest.mark.asyncio
    async def test_generate_predictions_model_not_ready(self):
        """测试模型状态不可用异常"""
        # Arrange: 创建未训练的模型
        repository_mock = AsyncMock(spec=IModelRepository)
        trainer_mock = AsyncMock(spec=IModelTrainer)

        model = Model(
            model_type=ModelType.LGBM,
            hyperparameters={},
            status=ModelStatus.UNTRAINED,  # 未训练状态
        )
        repository_mock.find_by_id.return_value = model

        use_case = GeneratePredictionsUseCase(
            repository=repository_mock, trainer=trainer_mock
        )

        # Act & Assert: 未训练模型不应该用于预测
        with pytest.raises(ValueError, match="Model.*not ready|not trained"):
            await use_case.execute(model_id=model.id, input_data=MagicMock())


class TestGeneratePredictionsErrorHandling:
    """测试错误处理"""

    @pytest.mark.asyncio
    async def test_generate_predictions_trainer_error(self):
        """测试训练器错误处理"""
        # Arrange: Mock trainer 抛出异常
        repository_mock = AsyncMock(spec=IModelRepository)
        trainer_mock = AsyncMock(spec=IModelTrainer)

        model = Model(
            model_type=ModelType.LGBM,
            hyperparameters={},
            status=ModelStatus.TRAINED,
        )
        repository_mock.find_by_id.return_value = model
        trainer_mock.predict.side_effect = Exception("预测失败")

        use_case = GeneratePredictionsUseCase(
            repository=repository_mock, trainer=trainer_mock
        )

        # Act & Assert: 应该传播异常
        with pytest.raises(Exception, match="预测失败"):
            await use_case.execute(model_id=model.id, input_data=MagicMock())

    @pytest.mark.asyncio
    async def test_generate_predictions_empty_result(self):
        """测试空预测结果"""
        # Arrange: Mock trainer 返回空列表
        repository_mock = AsyncMock(spec=IModelRepository)
        trainer_mock = AsyncMock(spec=IModelTrainer)

        model = Model(
            model_type=ModelType.LGBM,
            hyperparameters={},
            status=ModelStatus.TRAINED,
        )
        repository_mock.find_by_id.return_value = model
        trainer_mock.predict.return_value = []  # 空预测列表

        use_case = GeneratePredictionsUseCase(
            repository=repository_mock, trainer=trainer_mock
        )

        # Act
        result = await use_case.execute(model_id=model.id, input_data=MagicMock())

        # Assert: 空结果也是有效的
        assert isinstance(result, PredictionBatch)
        assert result.size() == 0
        assert len(result.predictions) == 0
