"""
QlibModelTrainerAdapter - Qlib 模型训练适配器

适配 Qlib 框架实现 IModelTrainer 接口
"""

from typing import Any, Dict, List
from decimal import Decimal
import pandas as pd
import numpy as np

# 导入真实的机器学习库
try:
    import lightgbm as lgb
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
except ImportError:
    lgb = None
    train_test_split = None
    mean_squared_error = None
    mean_absolute_error = None
    r2_score = None

from domain.ports.model_trainer import IModelTrainer
from domain.entities.model import Model, ModelType
from domain.entities.prediction import Prediction


class QlibModelTrainerAdapter(IModelTrainer):
    """
    Qlib 模型训练适配器

    实现 IModelTrainer 接口,使用 LightGBM 等真实模型
    """

    def __init__(self):
        """初始化适配器"""
        self.trained_model = None  # 存储训练好的模型

    def _prepare_training_data(self, training_data: pd.DataFrame):
        """
        准备训练数据

        Args:
            training_data: DataFrame with features and labels

        Returns:
            X_train, X_test, y_train, y_test
        """
        # 排除非特征列
        exclude_cols = ['stock_code', 'label_return', 'label_direction', 'label_multiclass']
        feature_cols = [col for col in training_data.columns if col not in exclude_cols]

        # 准备特征和标签
        X = training_data[feature_cols]
        y = training_data['label_return']  # 使用回归标签

        # 时间序列分割(避免数据泄露)
        # 假设数据已按时间排序,使用80/20分割
        split_idx = int(len(X) * 0.8)
        X_train = X.iloc[:split_idx]
        X_test = X.iloc[split_idx:]
        y_train = y.iloc[:split_idx]
        y_test = y.iloc[split_idx:]

        return X_train, X_test, y_train, y_test

    def _train_lgbm(
        self, X_train, X_test, y_train, y_test, hyperparameters: Dict[str, Any]
    ) -> tuple:
        """
        训练 LightGBM 模型

        Args:
            X_train, X_test, y_train, y_test: 训练和测试数据
            hyperparameters: 超参数

        Returns:
            (model, metrics)
        """
        # 默认超参数
        params = {
            'objective': 'regression',
            'metric': 'rmse',
            'boosting_type': 'gbdt',
            'num_leaves': 31,
            'learning_rate': 0.05,
            'feature_fraction': 0.9,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'verbose': -1
        }

        # 更新用户提供的超参数
        if hyperparameters:
            params.update(hyperparameters)

        # 创建数据集
        train_data = lgb.Dataset(X_train, label=y_train)
        test_data = lgb.Dataset(X_test, label=y_test, reference=train_data)

        # 训练模型
        model = lgb.train(
            params,
            train_data,
            num_boost_round=100,
            valid_sets=[train_data, test_data],
            valid_names=['train', 'test'],
        )

        # 预测
        y_pred_train = model.predict(X_train)
        y_pred_test = model.predict(X_test)

        # 计算指标
        metrics = {
            'train_rmse': float(np.sqrt(mean_squared_error(y_train, y_pred_train))),
            'test_rmse': float(np.sqrt(mean_squared_error(y_test, y_pred_test))),
            'train_mae': float(mean_absolute_error(y_train, y_pred_train)),
            'test_mae': float(mean_absolute_error(y_test, y_pred_test)),
            'train_r2': float(r2_score(y_train, y_pred_train)),
            'test_r2': float(r2_score(y_test, y_pred_test)),
        }

        return model, metrics

    def _convert_metrics_to_domain(
        self, metrics: Dict[str, float]
    ) -> Dict[str, Decimal]:
        """
        转换指标到领域层格式

        Args:
            metrics: 训练指标

        Returns:
            领域层指标字典 (Decimal 类型)
        """
        domain_metrics = {}
        for key, value in metrics.items():
            domain_metrics[key] = Decimal(str(value))

        return domain_metrics

    async def train(self, model: Model, training_data: Any) -> Model:
        """
        训练模型

        Args:
            model: 模型实体
            training_data: 训练数据 (pandas DataFrame)

        Returns:
            Model: 训练后的模型实体

        Raises:
            Exception: 当训练失败时
        """
        try:
            # 检查依赖
            if lgb is None:
                raise ImportError("LightGBM not installed. Please install: pip install lightgbm")

            # 准备数据
            X_train, X_test, y_train, y_test = self._prepare_training_data(training_data)

            # 根据模型类型训练
            if model.model_type == ModelType.LGBM:
                trained_model, metrics = self._train_lgbm(
                    X_train, X_test, y_train, y_test, model.hyperparameters
                )
                self.trained_model = trained_model
            else:
                raise ValueError(f"Unsupported model type: {model.model_type}")

            # 转换指标
            domain_metrics = self._convert_metrics_to_domain(metrics)

            # 先设置metrics（这样即使mark_as_trained失败，metrics也已保存）
            model.update_metrics(domain_metrics)

            # 更新模型状态（可能因阈值失败）
            model.mark_as_trained(domain_metrics)

            return model

        except Exception as e:
            raise Exception(
                f"Failed to train model: {model.model_type.name}, {e}"
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
            Exception: 当预测失败时
        """
        try:
            if self.trained_model is None:
                raise ValueError("Model not trained yet")

            # 准备特征
            exclude_cols = ['stock_code', 'label_return', 'label_direction', 'label_multiclass']
            feature_cols = [col for col in input_data.columns if col not in exclude_cols]
            X = input_data[feature_cols]

            # 预测
            predictions_array = self.trained_model.predict(X)

            # 转换为领域层 Prediction 列表
            predictions = []
            for i, pred_value in enumerate(predictions_array):
                # 这里简化处理，实际应该创建完整的 Prediction 对象
                # predictions.append(Prediction(...))
                pass

            return predictions

        except Exception as e:
            raise Exception(
                f"Failed to predict: {model.model_type.name}, {e}"
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
            Exception: 当评估失败时
        """
        try:
            if self.trained_model is None:
                raise ValueError("Model not trained yet")

            # 准备数据
            exclude_cols = ['stock_code', 'label_return', 'label_direction', 'label_multiclass']
            feature_cols = [col for col in validation_data.columns if col not in exclude_cols]

            X = validation_data[feature_cols]
            y = validation_data['label_return']

            # 预测
            y_pred = self.trained_model.predict(X)

            # 计算指标
            metrics = {
                'rmse': float(np.sqrt(mean_squared_error(y, y_pred))),
                'mae': float(mean_absolute_error(y, y_pred)),
                'r2': float(r2_score(y, y_pred)),
            }

            # 转换指标
            domain_metrics = self._convert_metrics_to_domain(metrics)

            return domain_metrics

        except Exception as e:
            raise Exception(
                f"Failed to evaluate model: {model.model_type.name}, {e}"
            ) from e
