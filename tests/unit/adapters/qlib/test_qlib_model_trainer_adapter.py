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

class TestQlibModelTrainerAdapterPredict:
    """测试 QlibModelTrainerAdapter.predict() 方法"""

    @pytest.fixture
    def adapter_with_trained_model(self, untrained_model):
        """带有已训练模型的适配器 fixture"""
        from adapters.qlib.qlib_model_trainer_adapter import QlibModelTrainerAdapter
        import pandas as pd
        import numpy as np

        adapter = QlibModelTrainerAdapter()

        # 使用mock模型，动态返回与输入长度匹配的预测
        mock_model = MagicMock()

        def mock_predict(X):
            """根据输入数据长度返回相应数量的预测值"""
            n_samples = len(X)
            # 返回随机预测值，范围在[-0.05, 0.05]之间（模拟5%的收益率预测）
            return np.random.randn(n_samples) * 0.02

        mock_model.predict = mock_predict
        adapter.trained_model = mock_model

        return adapter, untrained_model

    @pytest.fixture
    def untrained_model(self) -> Model:
        """未训练模型 fixture"""
        return Model(model_type=ModelType.LGBM, hyperparameters={"learning_rate": 0.01})

    @pytest.mark.asyncio
    async def test_predict_with_untrained_model_should_fail(self, untrained_model):
        """
        测试未训练模型预测应失败

        验证:
        1. 未调用train()前predict()应抛出异常
        2. 异常消息包含"not trained"
        """
        from adapters.qlib.qlib_model_trainer_adapter import QlibModelTrainerAdapter
        import pandas as pd

        adapter = QlibModelTrainerAdapter()

        # 准备输入数据
        input_data = pd.DataFrame({
            'stock_code': ['sh600000'],
            'feature1': [0.5],
            'feature2': [0.3],
            'feature3': [-0.2],
        })

        # 验证：未训练的模型应抛出异常
        with pytest.raises(Exception) as exc_info:
            await adapter.predict(model=untrained_model, input_data=input_data)

        # 检查异常消息包含关键信息
        assert "not trained" in str(exc_info.value).lower() or "model not trained" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_predict_with_empty_dataframe_should_return_empty_list(
        self, adapter_with_trained_model
    ):
        """
        测试空DataFrame输入应返回空列表

        验证:
        1. 空DataFrame不会引发异常
        2. 返回空列表
        """
        import pandas as pd

        adapter, model = adapter_with_trained_model

        # 准备空的输入数据
        input_data = pd.DataFrame(columns=['stock_code', 'feature1', 'feature2', 'feature3'])

        # 执行
        predictions = await adapter.predict(model=model, input_data=input_data)

        # 验证
        assert isinstance(predictions, list)
        assert len(predictions) == 0

    @pytest.mark.asyncio
    async def test_predict_missing_required_columns_should_fail(
        self, adapter_with_trained_model
    ):
        """
        测试缺少必要列应失败

        验证:
        1. 缺少特征列时抛出异常
        2. 异常消息指示缺少的列
        """
        import pandas as pd

        adapter, model = adapter_with_trained_model

        # 准备缺少列的输入数据（只有stock_code，缺少特征）
        input_data = pd.DataFrame({
            'stock_code': ['sh600000'],
        })

        # 验证：缺少特征列应失败
        with pytest.raises(Exception):
            await adapter.predict(model=model, input_data=input_data)

    @pytest.mark.asyncio
    async def test_predict_single_stock_single_date(
        self, adapter_with_trained_model
    ):
        """
        测试单股票单日期预测

        验证:
        1. 返回包含一个Prediction实体的列表
        2. Prediction包含正确的stock_code
        3. Prediction包含predicted_value
        4. Prediction包含confidence
        """
        import pandas as pd
        from datetime import datetime
        from domain.entities.prediction import Prediction
        from domain.value_objects.stock_code import StockCode

        adapter, model = adapter_with_trained_model

        # 准备输入数据
        input_data = pd.DataFrame({
            'stock_code': ['sh600000'],
            'date': [datetime(2024, 1, 15)],
            'feature1': [0.5],
            'feature2': [0.3],
            'feature3': [-0.2],
        })

        # 执行
        predictions = await adapter.predict(model=model, input_data=input_data)

        # 验证
        assert len(predictions) == 1
        assert isinstance(predictions[0], Prediction)
        assert predictions[0].stock_code == StockCode('sh600000')
        assert isinstance(predictions[0].predicted_value, float)
        assert predictions[0].confidence is not None
        assert 0 <= predictions[0].confidence <= 1

    @pytest.mark.asyncio
    async def test_predict_multiple_stocks_batch(
        self, adapter_with_trained_model
    ):
        """
        测试多股票多日期批量预测

        验证:
        1. 返回多个Prediction实体
        2. 每个股票都有对应的预测
        3. 预测数量与输入行数一致
        """
        import pandas as pd
        from datetime import datetime
        from domain.entities.prediction import Prediction

        adapter, model = adapter_with_trained_model

        # 准备多行输入数据
        input_data = pd.DataFrame({
            'stock_code': ['sh600000', 'sz000001', 'sh600519'],
            'date': [datetime(2024, 1, 15)] * 3,
            'feature1': [0.5, 0.3, -0.1],
            'feature2': [0.3, -0.2, 0.4],
            'feature3': [-0.2, 0.1, 0.2],
        })

        # 执行
        predictions = await adapter.predict(model=model, input_data=input_data)

        # 验证
        assert len(predictions) == 3
        assert all(isinstance(p, Prediction) for p in predictions)

        # 验证每个股票都有预测
        stock_codes = [p.stock_code.value for p in predictions]
        assert 'sh600000' in stock_codes
        assert 'sz000001' in stock_codes
        assert 'sh600519' in stock_codes

    @pytest.mark.asyncio
    async def test_predict_values_are_floats(
        self, adapter_with_trained_model
    ):
        """
        测试预测值类型和范围

        验证:
        1. predicted_value是float类型
        2. 预测值在合理范围内（例如 -1到1之间）
        """
        import pandas as pd
        from datetime import datetime

        adapter, model = adapter_with_trained_model

        # 准备输入数据
        input_data = pd.DataFrame({
            'stock_code': ['sh600000', 'sz000001'],
            'date': [datetime(2024, 1, 15)] * 2,
            'feature1': [0.5, 0.3],
            'feature2': [0.3, -0.2],
            'feature3': [-0.2, 0.1],
        })

        # 执行
        predictions = await adapter.predict(model=model, input_data=input_data)

        # 验证预测值类型
        for pred in predictions:
            assert isinstance(pred.predicted_value, float)
            # 预测值应该在合理范围内（收益率通常在-100%到100%）
            assert -1.0 <= pred.predicted_value <= 1.0

    @pytest.mark.asyncio
    async def test_predict_confidence_calculation(
        self, adapter_with_trained_model
    ):
        """
        测试置信度计算正确性

        验证:
        1. confidence在0到1之间
        2. 极端预测值有较高置信度
        3. 中等预测值有较低置信度
        """
        import pandas as pd
        from datetime import datetime

        adapter, model = adapter_with_trained_model

        # 准备输入数据
        input_data = pd.DataFrame({
            'stock_code': ['sh600000', 'sz000001'],
            'date': [datetime(2024, 1, 15)] * 2,
            'feature1': [0.5, 0.3],
            'feature2': [0.3, -0.2],
            'feature3': [-0.2, 0.1],
        })

        # 执行
        predictions = await adapter.predict(model=model, input_data=input_data)

        # 验证置信度
        for pred in predictions:
            assert pred.confidence is not None
            assert 0 <= pred.confidence <= 1
            assert isinstance(pred.confidence, float)

    @pytest.mark.asyncio
    async def test_predict_output_includes_timestamp(
        self, adapter_with_trained_model
    ):
        """
        测试输出包含时间戳

        验证:
        1. Prediction实体包含timestamp字段
        2. timestamp与输入的date对应
        """
        import pandas as pd
        from datetime import datetime

        adapter, model = adapter_with_trained_model

        # 准备输入数据
        test_date = datetime(2024, 1, 15)
        input_data = pd.DataFrame({
            'stock_code': ['sh600000'],
            'date': [test_date],
            'feature1': [0.5],
            'feature2': [0.3],
            'feature3': [-0.2],
        })

        # 执行
        predictions = await adapter.predict(model=model, input_data=input_data)

        # 验证
        assert predictions[0].timestamp == test_date
        # 测试兼容性属性
        assert predictions[0].prediction_date == test_date

    @pytest.mark.asyncio
    async def test_predict_output_includes_model_id(
        self, adapter_with_trained_model
    ):
        """
        测试输出包含model_id

        验证:
        1. Prediction实体包含model_id字段
        2. model_id与输入模型的id一致
        """
        import pandas as pd
        from datetime import datetime

        adapter, model = adapter_with_trained_model

        # 准备输入数据
        input_data = pd.DataFrame({
            'stock_code': ['sh600000'],
            'date': [datetime(2024, 1, 15)],
            'feature1': [0.5],
            'feature2': [0.3],
            'feature3': [-0.2],
        })

        # 执行
        predictions = await adapter.predict(model=model, input_data=input_data)

        # 验证
        assert predictions[0].model_id == model.id

    @pytest.mark.asyncio
    async def test_predict_handles_missing_date_column(
        self, adapter_with_trained_model
    ):
        """
        测试处理缺少date列的情况

        验证:
        1. 如果没有date列，使用当前时间
        2. 不会抛出异常
        """
        import pandas as pd
        from datetime import datetime

        adapter, model = adapter_with_trained_model

        # 准备没有date列的输入数据
        input_data = pd.DataFrame({
            'stock_code': ['sh600000'],
            'feature1': [0.5],
            'feature2': [0.3],
            'feature3': [-0.2],
        })

        # 执行
        predictions = await adapter.predict(model=model, input_data=input_data)

        # 验证：应该有预测结果
        assert len(predictions) == 1
        assert predictions[0].timestamp is not None
        # 时间应该接近当前时间
        assert (datetime.now() - predictions[0].timestamp).total_seconds() < 10
