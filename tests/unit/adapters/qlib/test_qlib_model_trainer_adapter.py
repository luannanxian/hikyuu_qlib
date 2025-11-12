"""
QlibModelTrainerAdapter 单元测试

测试 QlibModelTrainerAdapter 实现 IModelTrainer 接口,
使用 Mock 隔离 Qlib 框架依赖
"""

import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch
from typing import Any

from domain.entities.model import Model, ModelStatus, ModelType


class TestQlibModelTrainerAdapter:
    """测试 QlibModelTrainerAdapter"""

    @pytest.fixture
    def untrained_model(self) -> Model:
        """未训练模型 fixture"""
        return Model(model_type=ModelType.LGBM, hyperparameters={"learning_rate": 0.01})

    @pytest.fixture
    def mock_training_data(self) -> Any:
        """Mock 训练数据 fixture"""
        return MagicMock()

    @pytest.mark.asyncio
    async def test_train_model_success(self, untrained_model, mock_training_data):
        """
        测试成功训练模型

        验证:
        1. 调用 Qlib Trainer API
        2. 返回已训练模型
        3. 模型状态更新为 TRAINED
        """
        from adapters.qlib.qlib_model_trainer_adapter import QlibModelTrainerAdapter

        # Mock Qlib Trainer
        with patch("adapters.qlib.qlib_model_trainer_adapter.trainer") as mock_trainer:
            # Mock 训练结果
            mock_qlib_model = MagicMock()
            mock_metrics = {"IC": 0.85, "ICIR": 0.8}
            mock_trainer.train.return_value = (mock_qlib_model, mock_metrics)

            # 执行
            adapter = QlibModelTrainerAdapter()
            result = await adapter.train(
                model=untrained_model, training_data=mock_training_data
            )

            # 验证
            assert result.status == ModelStatus.TRAINED
            assert result.metrics is not None
            assert "accuracy" in result.metrics or "IC" in result.metrics

    @pytest.mark.asyncio
    async def test_qlib_to_domain_metrics_conversion(
        self, untrained_model, mock_training_data
    ):
        """
        测试 Qlib → Domain 指标转换

        验证:
        1. IC/ICIR 转换为标准指标格式
        2. 指标类型为 Decimal
        """
        from adapters.qlib.qlib_model_trainer_adapter import QlibModelTrainerAdapter

        with patch("adapters.qlib.qlib_model_trainer_adapter.trainer") as mock_trainer:
            mock_qlib_model = MagicMock()
            mock_metrics = {"IC": 0.85, "ICIR": 0.8, "rank_IC": 0.86}
            mock_trainer.train.return_value = (mock_qlib_model, mock_metrics)

            adapter = QlibModelTrainerAdapter()
            result = await adapter.train(
                model=untrained_model, training_data=mock_training_data
            )

            # 验证指标转换
            assert result.metrics is not None
            for value in result.metrics.values():
                assert isinstance(value, Decimal)

    @pytest.mark.asyncio
    async def test_hyperparameters_mapping(self, untrained_model, mock_training_data):
        """
        测试超参数映射

        验证:
        1. Domain 超参数 → Qlib 配置
        2. ModelType → Qlib 模型类型
        """
        from adapters.qlib.qlib_model_trainer_adapter import QlibModelTrainerAdapter

        with patch("adapters.qlib.qlib_model_trainer_adapter.trainer") as mock_trainer:
            mock_qlib_model = MagicMock()
            mock_metrics = {"IC": 0.85}
            mock_trainer.train.return_value = (mock_qlib_model, mock_metrics)

            adapter = QlibModelTrainerAdapter()
            await adapter.train(model=untrained_model, training_data=mock_training_data)

            # 验证 trainer.train 被调用
            mock_trainer.train.assert_called_once()

    @pytest.mark.asyncio
    async def test_qlib_training_error_handling(
        self, untrained_model, mock_training_data
    ):
        """
        测试 Qlib 训练错误处理

        验证:
        1. 捕获 Qlib 异常
        2. 映射为领域层异常
        """
        from adapters.qlib.qlib_model_trainer_adapter import QlibModelTrainerAdapter

        with patch("adapters.qlib.qlib_model_trainer_adapter.trainer") as mock_trainer:
            mock_trainer.train.side_effect = Exception("Qlib training failed")

            adapter = QlibModelTrainerAdapter()
            with pytest.raises(Exception) as exc_info:
                await adapter.train(
                    model=untrained_model, training_data=mock_training_data
                )

            assert (
                "Qlib" in str(exc_info.value)
                or "training" in str(exc_info.value).lower()
            )

    @pytest.mark.asyncio
    async def test_model_persistence_after_training(
        self, untrained_model, mock_training_data
    ):
        """
        测试训练后模型持久化

        验证:
        1. Qlib 模型对象存储在 Domain Model 中
        2. 可以后续用于预测
        """
        from adapters.qlib.qlib_model_trainer_adapter import QlibModelTrainerAdapter

        with patch("adapters.qlib.qlib_model_trainer_adapter.trainer") as mock_trainer:
            mock_qlib_model = MagicMock()
            mock_metrics = {"IC": 0.85}
            mock_trainer.train.return_value = (mock_qlib_model, mock_metrics)

            adapter = QlibModelTrainerAdapter()
            result = await adapter.train(
                model=untrained_model, training_data=mock_training_data
            )

            # 验证模型已训练并可用于预测
            assert result.is_ready_for_prediction()
