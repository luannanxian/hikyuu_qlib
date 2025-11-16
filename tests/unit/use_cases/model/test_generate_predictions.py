"""
GeneratePredictionsUseCase 单元测试

测试 UC-003: Generate Predictions (生成预测) 用例
"""

from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest

from domain.entities.model import Model, ModelStatus, ModelType
from domain.entities.prediction import Prediction, PredictionBatch
from domain.ports.model_repository import IModelRepository
from domain.ports.stock_data_provider import IStockDataProvider
from domain.value_objects.date_range import DateRange
from domain.value_objects.kline_type import KLineType
from domain.value_objects.stock_code import StockCode
from use_cases.model.generate_predictions import GeneratePredictionsUseCase


class TestGeneratePredictionsSuccess:
    """测试成功生成预测"""

    @pytest.mark.asyncio
    async def test_generate_predictions_success(self):
        """测试成功生成预测"""
        # Arrange: 准备 Mock Repository 和 DataProvider
        repository_mock = AsyncMock(spec=IModelRepository)
        data_provider_mock = AsyncMock(spec=IStockDataProvider)

        # 创建已训练的模型,包含 trained_model
        model = Model(
            model_type=ModelType.LGBM,
            hyperparameters={"learning_rate": 0.01},
            status=ModelStatus.TRAINED,
        )
        # 设置 trained_model (模拟 LightGBM 模型)
        trained_lgbm_mock = MagicMock()
        trained_lgbm_mock.predict.return_value = [0.05, -0.02, 0.03]
        object.__setattr__(model, 'trained_model', trained_lgbm_mock)

        model_id = model.id

        # Mock repository 返回模型
        repository_mock.find_by_id.return_value = model

        # Mock data provider 返回K线数据
        mock_kline_data = [
            MagicMock(datetime=datetime(2024, 1, 10), close=10.5, open=10.0, high=10.8, low=9.9, volume=1000000),
            MagicMock(datetime=datetime(2024, 1, 11), close=10.6, open=10.5, high=10.9, low=10.3, volume=1100000),
            MagicMock(datetime=datetime(2024, 1, 12), close=10.4, open=10.6, high=10.7, low=10.2, volume=900000),
        ]
        data_provider_mock.load_stock_data.return_value = mock_kline_data

        # 创建 Use Case
        use_case = GeneratePredictionsUseCase(
            repository=repository_mock,
            data_provider=data_provider_mock,
        )

        # Prepare test data
        stock_codes = [StockCode("sh600000")]
        date_range = DateRange(
            start_date=datetime(2024, 1, 10),
            end_date=datetime(2024, 1, 12),
        )

        # Act: 执行用例 (使用 patch 模拟 convert_kline_to_training_data)
        with patch('use_cases.model.generate_predictions.convert_kline_to_training_data') as mock_convert:
            # Mock convert 返回特征数据
            mock_features = pd.DataFrame({
                'close': [10.5, 10.6, 10.4],
                'volume': [1000000, 1100000, 900000],
            }, index=pd.DatetimeIndex([datetime(2024, 1, 10), datetime(2024, 1, 11), datetime(2024, 1, 12)]))
            mock_convert.return_value = mock_features

            result = await use_case.execute(
                model_id=model_id,
                stock_codes=stock_codes,
                date_range=date_range,
                kline_type=KLineType.DAY,
            )

        # Assert: 验证结果
        assert isinstance(result, PredictionBatch)
        assert result.model_id == model_id
        assert result.size() == 3  # 3条预测记录
        assert len(result.predictions) == 3

        # 验证预测值
        assert result.predictions[0].predicted_value == 0.05
        assert result.predictions[1].predicted_value == -0.02
        assert result.predictions[2].predicted_value == 0.03

        # 验证 repository 被正确调用
        repository_mock.find_by_id.assert_called_once_with(model_id)

        # 验证 data_provider 被调用
        data_provider_mock.load_stock_data.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_predictions_creates_batch(self):
        """测试生成预测时正确创建 PredictionBatch"""
        # Arrange
        repository_mock = AsyncMock(spec=IModelRepository)
        data_provider_mock = AsyncMock(spec=IStockDataProvider)

        model = Model(
            model_type=ModelType.LGBM,
            hyperparameters={},
            status=ModelStatus.TRAINED,
        )
        trained_lgbm_mock = MagicMock()
        trained_lgbm_mock.predict.return_value = [0.05, 0.03]
        object.__setattr__(model, 'trained_model', trained_lgbm_mock)

        repository_mock.find_by_id.return_value = model

        mock_kline_data = [
            MagicMock(datetime=datetime(2024, 1, 10), close=10.5, open=10.0, high=10.8, low=9.9, volume=1000000),
            MagicMock(datetime=datetime(2024, 1, 11), close=10.6, open=10.5, high=10.9, low=10.3, volume=1100000),
        ]
        data_provider_mock.load_stock_data.return_value = mock_kline_data

        use_case = GeneratePredictionsUseCase(
            repository=repository_mock,
            data_provider=data_provider_mock,
        )

        stock_codes = [StockCode("sh600000")]
        date_range = DateRange(
            start_date=datetime(2024, 1, 10),
            end_date=datetime(2024, 1, 11),
        )

        # Act
        with patch('use_cases.model.generate_predictions.convert_kline_to_training_data') as mock_convert:
            mock_features = pd.DataFrame({
                'close': [10.5, 10.6],
                'volume': [1000000, 1100000],
            }, index=pd.DatetimeIndex([datetime(2024, 1, 10), datetime(2024, 1, 11)]))
            mock_convert.return_value = mock_features

            result = await use_case.execute(
                model_id=model.id,
                stock_codes=stock_codes,
                date_range=date_range,
            )

        # Assert
        assert isinstance(result, PredictionBatch)
        assert result.model_id == model.id
        assert result.size() == 2

        # 验证 PredictionBatch 包含正确的预测
        for prediction in result.predictions:
            assert isinstance(prediction, Prediction)
            assert prediction.stock_code == StockCode("sh600000")
            assert prediction.model_id == model.id


class TestGeneratePredictionsValidation:
    """测试预测生成的验证逻辑"""

    @pytest.mark.asyncio
    async def test_generate_predictions_model_not_found(self):
        """测试模型未找到时抛出异常"""
        # Arrange
        repository_mock = AsyncMock(spec=IModelRepository)
        data_provider_mock = AsyncMock(spec=IStockDataProvider)

        # Repository 返回 None (模型不存在)
        repository_mock.find_by_id.return_value = None

        use_case = GeneratePredictionsUseCase(
            repository=repository_mock,
            data_provider=data_provider_mock,
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Model with id .* not found"):
            await use_case.execute(
                model_id="non-existent-id",
                stock_codes=[StockCode("sh600000")],
                date_range=DateRange(
                    start_date=datetime(2024, 1, 10),
                    end_date=datetime(2024, 1, 12),
                ),
            )

    @pytest.mark.asyncio
    async def test_generate_predictions_model_not_ready(self):
        """测试模型未就绪时抛出异常"""
        # Arrange
        repository_mock = AsyncMock(spec=IModelRepository)
        data_provider_mock = AsyncMock(spec=IStockDataProvider)

        # 创建未训练的模型
        model = Model(
            model_type=ModelType.LGBM,
            hyperparameters={},
            status=ModelStatus.UNTRAINED,  # 未训练状态
        )

        repository_mock.find_by_id.return_value = model

        use_case = GeneratePredictionsUseCase(
            repository=repository_mock,
            data_provider=data_provider_mock,
        )

        # Act & Assert
        with pytest.raises(ValueError, match="is not trained"):
            await use_case.execute(
                model_id=model.id,
                stock_codes=[StockCode("sh600000")],
                date_range=DateRange(
                    start_date=datetime(2024, 1, 10),
                    end_date=datetime(2024, 1, 12),
                ),
            )


class TestGeneratePredictionsErrorHandling:
    """测试预测生成的错误处理"""

    @pytest.mark.asyncio
    async def test_generate_predictions_trainer_error(self):
        """测试数据加载失败时继续处理其他股票"""
        # Arrange
        repository_mock = AsyncMock(spec=IModelRepository)
        data_provider_mock = AsyncMock(spec=IStockDataProvider)

        model = Model(
            model_type=ModelType.LGBM,
            hyperparameters={},
            status=ModelStatus.TRAINED,
        )
        trained_lgbm_mock = MagicMock()
        trained_lgbm_mock.predict.return_value = [0.05]
        object.__setattr__(model, 'trained_model', trained_lgbm_mock)

        repository_mock.find_by_id.return_value = model

        # 第一个股票加载失败,第二个成功
        mock_kline_data = [
            MagicMock(datetime=datetime(2024, 1, 10), close=10.5, open=10.0, high=10.8, low=9.9, volume=1000000),
        ]
        data_provider_mock.load_stock_data.side_effect = [
            Exception("Data load failed"),  # 第一个失败
            mock_kline_data,  # 第二个成功
        ]

        use_case = GeneratePredictionsUseCase(
            repository=repository_mock,
            data_provider=data_provider_mock,
        )

        stock_codes = [StockCode("sh600000"), StockCode("sz000001")]
        date_range = DateRange(
            start_date=datetime(2024, 1, 10),
            end_date=datetime(2024, 1, 10),
        )

        # Act
        with patch('use_cases.model.generate_predictions.convert_kline_to_training_data') as mock_convert:
            mock_features = pd.DataFrame({
                'close': [10.5],
                'volume': [1000000],
            }, index=pd.DatetimeIndex([datetime(2024, 1, 10)]))
            mock_convert.return_value = mock_features

            result = await use_case.execute(
                model_id=model.id,
                stock_codes=stock_codes,
                date_range=date_range,
            )

        # Assert: 应该只有第二个股票的预测
        assert isinstance(result, PredictionBatch)
        assert result.size() == 1
        assert result.predictions[0].stock_code == StockCode("sz000001")

    @pytest.mark.asyncio
    async def test_generate_predictions_empty_result(self):
        """测试当数据提供者返回空数据时跳过该股票"""
        # Arrange
        repository_mock = AsyncMock(spec=IModelRepository)
        data_provider_mock = AsyncMock(spec=IStockDataProvider)

        model = Model(
            model_type=ModelType.LGBM,
            hyperparameters={},
            status=ModelStatus.TRAINED,
        )
        trained_lgbm_mock = MagicMock()
        object.__setattr__(model, 'trained_model', trained_lgbm_mock)

        repository_mock.find_by_id.return_value = model

        # 返回空列表
        data_provider_mock.load_stock_data.return_value = []

        use_case = GeneratePredictionsUseCase(
            repository=repository_mock,
            data_provider=data_provider_mock,
        )

        stock_codes = [StockCode("sh600000")]
        date_range = DateRange(
            start_date=datetime(2024, 1, 10),
            end_date=datetime(2024, 1, 12),
        )

        # Act
        result = await use_case.execute(
            model_id=model.id,
            stock_codes=stock_codes,
            date_range=date_range,
        )

        # Assert: 应该返回空的 PredictionBatch
        assert isinstance(result, PredictionBatch)
        assert result.size() == 0
        assert len(result.predictions) == 0
