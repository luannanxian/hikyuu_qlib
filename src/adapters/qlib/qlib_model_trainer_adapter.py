"""
QlibModelTrainerAdapter - Qlib 模型训练适配器

适配 Qlib 框架实现 IModelTrainer 接口
"""

from typing import Any, Dict, List
from decimal import Decimal

# 为了便于测试，使用条件导入
try:
    from qlib.contrib.model import trainer
except ImportError:
    # 开发环境下 Mock qlib
    trainer = None

from domain.ports.model_trainer import IModelTrainer
from domain.entities.model import Model, ModelType
from domain.entities.prediction import Prediction


class QlibModelTrainerAdapter(IModelTrainer):
    """
    Qlib 模型训练适配器

    实现 IModelTrainer 接口,适配 Qlib 框架
    """

    def __init__(self, qlib_trainer_module=None):
        """
        初始化适配器

        Args:
            qlib_trainer_module: Qlib trainer 模块实例（用于测试注入）
        """
        self.trainer = (
            qlib_trainer_module if qlib_trainer_module is not None else trainer
        )

    def _map_model_type_to_qlib(self, model_type: ModelType) -> str:
        """
        映射领域层模型类型到 Qlib 模型类型

        Args:
            model_type: 领域层模型类型

        Returns:
            Qlib 模型类型字符串
        """
        mapping = {
            ModelType.LGBM: "LightGBM",
            ModelType.MLP: "MLP",
            ModelType.LSTM: "LSTM",
            ModelType.GRU: "GRU",
            ModelType.TRANSFORMER: "Transformer",
        }
        return mapping.get(model_type, "LightGBM")

    def _convert_metrics_to_domain(
        self, qlib_metrics: Dict[str, float]
    ) -> Dict[str, Decimal]:
        """
        转换 Qlib 指标到领域层格式

        Args:
            qlib_metrics: Qlib 训练指标

        Returns:
            领域层指标字典 (Decimal 类型)
        """
        # 转换为 Decimal 类型
        domain_metrics = {}
        for key, value in qlib_metrics.items():
            domain_metrics[key] = Decimal(str(value))

        return domain_metrics

    async def train(self, model: Model, training_data: Any) -> Model:
        """
        训练模型

        Args:
            model: 模型实体
            training_data: 训练数据

        Returns:
            Model: 训练后的模型实体

        Raises:
            Exception: 当 Qlib 训练失败时
        """
        try:
            # 获取 Qlib 模型类型
            qlib_model_type = self._map_model_type_to_qlib(model.model_type)

            # 调用 Qlib Trainer API
            # 这是一个简化的示例，实际使用需要根据 Qlib API 调整
            qlib_model, qlib_metrics = self.trainer.train(
                model_type=qlib_model_type,
                hyperparameters=model.hyperparameters,
                training_data=training_data,
            )

            # 转换指标
            domain_metrics = self._convert_metrics_to_domain(qlib_metrics)

            # 更新模型状态
            model.mark_as_trained(domain_metrics)

            # 这里可以存储 qlib_model 对象以供后续使用
            # 例如: model.qlib_model = qlib_model (需要扩展 Model 实体)

            return model

        except Exception as e:
            # 将 Qlib 异常映射为领域层异常
            raise Exception(
                f"Failed to train model with Qlib: {model.model_type.name}, {e}"
            ) from e

    async def predict(self, model: Model, input_data: Any) -> List[Prediction]:
        """
        生成预测

        Args:
            model: 模型实体
            input_data: 输入数据

        Returns:
            预测结果列表

        Raises:
            Exception: 当 Qlib 预测失败时
        """
        try:
            # 调用 Qlib 预测 API
            # 实际实现需要根据 Qlib API 调整
            _ = self.trainer.predict(model=model, input_data=input_data)

            # 转换为领域层 Prediction 列表
            # 这里简化处理，实际需要根据具体数据格式转换
            predictions = []
            # 实际转换逻辑省略，由具体业务实现

            return predictions

        except Exception as e:
            raise Exception(
                f"Failed to predict with Qlib: {model.model_type.name}, {e}"
            ) from e

    async def evaluate(self, model: Model, validation_data: Any) -> Dict[str, Decimal]:
        """
        评估模型

        Args:
            model: 模型实体
            validation_data: 验证数据

        Returns:
            评估指标字典

        Raises:
            Exception: 当 Qlib 评估失败时
        """
        try:
            # 调用 Qlib 评估 API
            # 实际实现需要根据 Qlib API 调整
            qlib_metrics = self.trainer.evaluate(
                model=model, validation_data=validation_data
            )

            # 转换指标
            domain_metrics = self._convert_metrics_to_domain(qlib_metrics)

            return domain_metrics

        except Exception as e:
            raise Exception(
                f"Failed to evaluate model with Qlib: {model.model_type.name}, {e}"
            ) from e
