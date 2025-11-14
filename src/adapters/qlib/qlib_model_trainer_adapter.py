"""
QlibModelTrainerAdapter - Qlib 模型训练适配器

适配 Qlib 框架实现 IModelTrainer 接口
"""

from typing import Any, Dict, List
from datetime import datetime
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
from domain.value_objects.stock_code import StockCode


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

            # Metrics 保持为 float 类型，不需要转换为 Decimal
            # 直接使用 metrics (Dict[str, float])

            # 先设置metrics（这样即使mark_as_trained失败，metrics也已保存）
            model.update_metrics(metrics)

            # 更新模型状态（可能因阈值失败）
            model.mark_as_trained(metrics)

            return model

        except Exception as e:
            raise Exception(
                f"Failed to train model: {model.model_type.name}, {e}"
            ) from e

    async def predict(self, model: Model, input_data: pd.DataFrame) -> List[Prediction]:
        """
        生成预测

        Args:
            model: 模型实体
            input_data: 输入数据 (pandas DataFrame)

        Returns:
            预测结果列表

        Raises:
            ValueError: 当模型未训练或输入数据无效时
            Exception: 当预测过程失败时
        """
        try:
            # 验证模型已训练
            self._validate_model_trained()

            # 处理空DataFrame
            if input_data.empty:
                return []

            # 提取特征并预测
            X = self._extract_features(input_data)
            predictions_array = self.trained_model.predict(X)

            # 计算置信度
            confidences = self._calculate_confidence(predictions_array)

            # 转换为领域层 Prediction 列表
            predictions = self._create_predictions(
                input_data, predictions_array, confidences, model.id
            )

            return predictions

        except ValueError as e:
            # 重新抛出验证错误
            raise
        except Exception as e:
            raise Exception(
                f"Failed to predict: {model.model_type.name}, {e}"
            ) from e

    def _validate_model_trained(self) -> None:
        """
        验证模型已训练

        Raises:
            ValueError: 当模型未训练时
        """
        if self.trained_model is None:
            raise ValueError("Model not trained yet")

    def _extract_features(self, input_data: pd.DataFrame) -> pd.DataFrame:
        """
        从输入数据中提取特征

        Args:
            input_data: 输入DataFrame

        Returns:
            特征DataFrame

        Raises:
            ValueError: 当没有找到特征列时
        """
        exclude_cols = [
            'stock_code',
            'date',
            'label_return',
            'label_direction',
            'label_multiclass'
        ]
        feature_cols = [col for col in input_data.columns if col not in exclude_cols]

        if not feature_cols:
            raise ValueError("No feature columns found in input data")

        return input_data[feature_cols]

    def _create_predictions(
        self,
        input_data: pd.DataFrame,
        predictions_array: np.ndarray,
        confidences: np.ndarray,
        model_id: str
    ) -> List[Prediction]:
        """
        创建Prediction实体列表

        Args:
            input_data: 原始输入数据
            predictions_array: 预测值数组
            confidences: 置信度数组
            model_id: 模型ID

        Returns:
            Prediction实体列表
        """
        predictions = []

        for i, pred_value in enumerate(predictions_array):
            stock_code = self._extract_stock_code(input_data, i)
            timestamp = self._extract_timestamp(input_data, i)

            prediction = Prediction(
                stock_code=stock_code,
                timestamp=timestamp,
                predicted_value=float(pred_value),
                confidence=float(confidences[i]),
                model_id=model_id
            )
            predictions.append(prediction)

        return predictions

    def _extract_stock_code(self, input_data: pd.DataFrame, index: int) -> StockCode:
        """
        从输入数据中提取股票代码

        Args:
            input_data: 输入DataFrame
            index: 行索引

        Returns:
            StockCode值对象
        """
        stock_code_str = input_data.iloc[index]['stock_code']
        return StockCode(stock_code_str)

    def _extract_timestamp(self, input_data: pd.DataFrame, index: int) -> datetime:
        """
        从输入数据中提取时间戳

        如果输入数据包含'date'列，使用该列的值；
        否则使用当前时间

        Args:
            input_data: 输入DataFrame
            index: 行索引

        Returns:
            时间戳
        """
        if 'date' in input_data.columns:
            return input_data.iloc[index]['date']
        else:
            return datetime.now()

    def _calculate_confidence(self, predictions_array: np.ndarray) -> np.ndarray:
        """
        计算预测置信度

        置信度计算策略：
        - 使用预测值的绝对值，通过sigmoid函数映射到[0, 1]区间
        - 预测值越极端（离0越远），置信度越高
        - 标准化因子设为5倍标准差，使大部分值在合理范围内

        Args:
            predictions_array: 预测值数组

        Returns:
            置信度数组（范围[0, 1]）
        """
        # 计算预测值的标准差
        std = np.std(predictions_array)
        if std == 0:
            std = 1.0  # 避免除零

        # 使用sigmoid函数：confidence = 1 / (1 + exp(-k * |pred|))
        # k = 5/std 使得在±std范围内的值有合理的置信度分布
        k = 5.0 / std
        abs_predictions = np.abs(predictions_array)
        confidences = 1.0 / (1.0 + np.exp(-k * abs_predictions))

        return confidences

    async def evaluate(self, model: Model, validation_data: Any) -> Dict[str, float]:
        """
        评估模型

        Args:
            model: 模型实体
            validation_data: 验证数据

        Returns:
            评估指标字典 (Dict[str, float])

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

            # 计算并返回指标 (float 类型)
            metrics = {
                'rmse': float(np.sqrt(mean_squared_error(y, y_pred))),
                'mae': float(mean_absolute_error(y, y_pred)),
                'r2': float(r2_score(y, y_pred)),
            }

            return metrics

        except Exception as e:
            raise Exception(
                f"Failed to evaluate model: {model.model_type.name}, {e}"
            ) from e
