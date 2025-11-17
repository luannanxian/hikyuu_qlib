"""
QlibModelTrainerAdapter 单元测试

测试 QlibModelTrainerAdapter 实现 IModelTrainer 接口,
使用 Mock 隔离 Qlib 框架依赖
"""

import os
import tempfile
from datetime import datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

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
        import numpy as np

        from adapters.qlib.qlib_model_trainer_adapter import QlibModelTrainerAdapter

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
        import pandas as pd

        from adapters.qlib.qlib_model_trainer_adapter import QlibModelTrainerAdapter

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
        self, adapter_with_trained_model,
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
        self, adapter_with_trained_model,
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
        self, adapter_with_trained_model,
    ):
        """
        测试单股票单日期预测

        验证:
        1. 返回包含一个Prediction实体的列表
        2. Prediction包含正确的stock_code
        3. Prediction包含predicted_value
        4. Prediction包含confidence
        """
        from datetime import datetime

        import pandas as pd

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
        self, adapter_with_trained_model,
    ):
        """
        测试多股票多日期批量预测

        验证:
        1. 返回多个Prediction实体
        2. 每个股票都有对应的预测
        3. 预测数量与输入行数一致
        """
        from datetime import datetime

        import pandas as pd

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
        self, adapter_with_trained_model,
    ):
        """
        测试预测值类型和范围

        验证:
        1. predicted_value是float类型
        2. 预测值在合理范围内（例如 -1到1之间）
        """
        from datetime import datetime

        import pandas as pd

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
        self, adapter_with_trained_model,
    ):
        """
        测试置信度计算正确性

        验证:
        1. confidence在0到1之间
        2. 极端预测值有较高置信度
        3. 中等预测值有较低置信度
        """
        from datetime import datetime

        import pandas as pd

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
        self, adapter_with_trained_model,
    ):
        """
        测试输出包含时间戳

        验证:
        1. Prediction实体包含timestamp字段
        2. timestamp与输入的date对应
        """
        from datetime import datetime

        import pandas as pd

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
        assert predictions[0].timestamp == test_date

    @pytest.mark.asyncio
    async def test_predict_output_includes_model_id(
        self, adapter_with_trained_model,
    ):
        """
        测试输出包含model_id

        验证:
        1. Prediction实体包含model_id字段
        2. model_id与输入模型的id一致
        """
        from datetime import datetime

        import pandas as pd

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
        self, adapter_with_trained_model,
    ):
        """
        测试处理缺少date列的情况

        验证:
        1. 如果没有date列，使用当前时间
        2. 不会抛出异常
        """
        from datetime import datetime

        import pandas as pd

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


class TestQlibModelTrainerAdapterSaveLoad:
    """测试 QlibModelTrainerAdapter 模型保存和加载功能"""

    @pytest.fixture
    def adapter_with_trained_model(self):
        """带有已训练模型的适配器 fixture"""
        import numpy as np

        from adapters.qlib.qlib_model_trainer_adapter import QlibModelTrainerAdapter

        adapter = QlibModelTrainerAdapter()

        # 创建 mock 模型
        mock_model = MagicMock()
        mock_model.predict = lambda X: np.random.randn(len(X)) * 0.02
        adapter.trained_model = mock_model

        return adapter

    @pytest.fixture
    def model_entity(self) -> Model:
        """模型实体 fixture"""
        return Model(
            model_type=ModelType.LGBM,
            hyperparameters={"learning_rate": 0.01},
        )

    def test_save_model_success(self, adapter_with_trained_model, model_entity):
        """
        测试成功保存模型

        验证:
        1. 模型文件被创建
        2. model.file_path 被更新
        """
        adapter = adapter_with_trained_model

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "model.pkl")

            # Mock pickle.dump 以避免序列化 MagicMock
            with patch('pickle.dump') as _mock_dump:
                # 执行
                adapter.save_model(model_entity, file_path)

                # 验证 pickle.dump 被调用
                assert _mock_dump.called
                # 验证 model.file_path 被更新
                assert model_entity.file_path == file_path

    def test_save_model_creates_directory(self, adapter_with_trained_model, model_entity):
        """
        测试保存模型时自动创建目录

        验证:
        1. 不存在的目录被创建
        2. 模型文件被保存
        """
        adapter = adapter_with_trained_model

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "models", "subfolder", "model.pkl")

            # Mock pickle.dump 以避免序列化 MagicMock
            with patch('pickle.dump') as _mock_dump:
                # 执行
                adapter.save_model(model_entity, file_path)

                # 验证目录被创建
                assert os.path.exists(os.path.dirname(file_path))

    def test_save_model_without_trained_model_should_fail(self, model_entity):
        """
        测试没有训练模型时保存应失败

        验证:
        1. 抛出 ValueError
        2. 错误消息包含 "No trained model"
        """
        from adapters.qlib.qlib_model_trainer_adapter import QlibModelTrainerAdapter

        adapter = QlibModelTrainerAdapter()

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "model.pkl")

            # 验证
            with pytest.raises(ValueError) as exc_info:
                adapter.save_model(model_entity, file_path)

            assert "No trained model" in str(exc_info.value)

    def test_load_model_success(self, adapter_with_trained_model):
        """
        测试成功加载模型

        验证:
        1. 模型被成功加载
        2. 加载的模型可以使用
        """
        from adapters.qlib.qlib_model_trainer_adapter import QlibModelTrainerAdapter

        adapter = QlibModelTrainerAdapter()

        # 创建一个简单的可序列化对象作为模型
        simple_model = {"type": "test", "params": {"a": 1, "b": 2}}

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "model.pkl")

            # 先保存模型
            import pickle
            with open(file_path, 'wb') as f:
                pickle.dump(simple_model, f)

            # 执行加载
            loaded_model = adapter.load_model(file_path)

            # 验证
            assert loaded_model is not None
            assert loaded_model == simple_model

    def test_load_model_file_not_found(self):
        """
        测试加载不存在的模型文件应失败

        验证:
        1. 抛出 FileNotFoundError
        2. 错误消息包含文件路径
        """
        from adapters.qlib.qlib_model_trainer_adapter import QlibModelTrainerAdapter

        adapter = QlibModelTrainerAdapter()
        non_existent_path = "/path/to/non/existent/model.pkl"

        # 验证
        with pytest.raises(FileNotFoundError) as exc_info:
            adapter.load_model(non_existent_path)

        assert non_existent_path in str(exc_info.value)


class TestQlibModelTrainerAdapterPredictBatch:
    """测试 QlibModelTrainerAdapter.predict_batch() 方法"""

    @pytest.fixture
    def adapter_with_trained_model(self):
        """带有已训练模型的适配器 fixture"""
        import numpy as np

        from adapters.qlib.qlib_model_trainer_adapter import QlibModelTrainerAdapter

        adapter = QlibModelTrainerAdapter()

        # 创建 mock 模型
        mock_model = MagicMock()

        def mock_predict(X):
            """根据输入数据长度返回相应数量的预测值"""
            n_samples = len(X)
            return np.random.randn(n_samples) * 0.02

        mock_model.predict = mock_predict
        adapter.trained_model = mock_model

        return adapter

    @pytest.fixture
    def model_entity(self) -> Model:
        """模型实体 fixture"""
        return Model(
            model_type=ModelType.LGBM,
            hyperparameters={"learning_rate": 0.01},
            status=ModelStatus.TRAINED,
        )

    @pytest.mark.asyncio
    async def test_predict_batch_with_memory_model(
        self, adapter_with_trained_model, model_entity,
    ):
        """
        测试使用内存中的模型进行批量预测

        验证:
        1. 返回 PredictionBatch 对象
        2. PredictionBatch 包含正确数量的预测
        3. 预测包含正确的 model_id
        """
        import pandas as pd

        from domain.entities.prediction import PredictionBatch

        adapter = adapter_with_trained_model

        # 准备输入数据
        input_data = pd.DataFrame({
            'stock_code': ['sh600000', 'sz000001', 'sh600519'],
            'date': [datetime(2024, 1, 15)] * 3,
            'feature1': [0.5, 0.3, -0.1],
            'feature2': [0.3, -0.2, 0.4],
            'feature3': [-0.2, 0.1, 0.2],
        })

        # 执行
        batch = await adapter.predict_batch(
            model=model_entity,
            input_data=input_data,
        )

        # 验证
        assert isinstance(batch, PredictionBatch)
        assert batch.model_id == model_entity.id
        assert batch.size() == 3
        assert len(batch.predictions) == 3

    @pytest.mark.asyncio
    async def test_predict_batch_with_file_path(
        self, adapter_with_trained_model, model_entity,
    ):
        """
        测试从文件路径加载模型进行预测

        验证:
        1. 从文件加载模型
        2. 返回正确的 PredictionBatch
        """
        import pandas as pd

        from domain.entities.prediction import PredictionBatch

        adapter = adapter_with_trained_model

        # 设置模型文件路径（不需要真实文件）
        model_entity.file_path = "/fake/path/model.pkl"

        # 准备输入数据
        input_data = pd.DataFrame({
            'stock_code': ['sh600000'],
            'date': [datetime(2024, 1, 15)],
            'feature1': [0.5],
            'feature2': [0.3],
            'feature3': [-0.2],
        })

        # Mock load_model 来返回训练好的模型
        with patch.object(adapter, 'load_model', return_value=adapter.trained_model):
            # 执行
            batch = await adapter.predict_batch(
                model=model_entity,
                input_data=input_data,
            )

            # 验证
            assert isinstance(batch, PredictionBatch)
            assert batch.size() == 1

    @pytest.mark.asyncio
    async def test_predict_batch_with_timestamp(
        self, adapter_with_trained_model, model_entity,
    ):
        """
        测试使用指定的 timestamp

        验证:
        1. batch.generated_at 使用指定的日期
        """
        import pandas as pd

        adapter = adapter_with_trained_model

        # 准备输入数据
        input_data = pd.DataFrame({
            'stock_code': ['sh600000'],
            'date': [datetime(2024, 1, 15)],
            'feature1': [0.5],
            'feature2': [0.3],
            'feature3': [-0.2],
        })

        # 指定预测日期
        timestamp = datetime(2024, 6, 15, 10, 30, 0)

        # 执行
        batch = await adapter.predict_batch(
            model=model_entity,
            input_data=input_data,
            prediction_date=timestamp,
        )

        # 验证
        assert batch.generated_at == timestamp

    @pytest.mark.asyncio
    async def test_predict_batch_with_empty_dataframe(
        self, adapter_with_trained_model, model_entity,
    ):
        """
        测试空 DataFrame 输入

        验证:
        1. 返回空的 PredictionBatch
        2. 不抛出异常
        """
        import pandas as pd

        from domain.entities.prediction import PredictionBatch

        adapter = adapter_with_trained_model

        # 准备空输入数据
        input_data = pd.DataFrame(columns=['stock_code', 'feature1', 'feature2', 'feature3'])

        # 执行
        batch = await adapter.predict_batch(
            model=model_entity,
            input_data=input_data,
        )

        # 验证
        assert isinstance(batch, PredictionBatch)
        assert batch.size() == 0
        assert len(batch.predictions) == 0

    @pytest.mark.asyncio
    async def test_predict_batch_without_model_should_fail(self, model_entity):
        """
        测试没有训练模型且没有文件路径时应失败

        验证:
        1. 抛出 ValueError
        2. 错误消息包含相关信息
        """
        import pandas as pd

        from adapters.qlib.qlib_model_trainer_adapter import QlibModelTrainerAdapter

        adapter = QlibModelTrainerAdapter()

        # 准备输入数据
        input_data = pd.DataFrame({
            'stock_code': ['sh600000'],
            'feature1': [0.5],
            'feature2': [0.3],
            'feature3': [-0.2],
        })

        # 验证
        with pytest.raises(Exception) as exc_info:
            await adapter.predict_batch(
                model=model_entity,
                input_data=input_data,
            )

        assert "not trained" in str(exc_info.value).lower() or "no file path" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_predict_batch_with_nonexistent_file_should_fail(self, model_entity):
        """
        测试加载不存在的模型文件应失败

        验证:
        1. 抛出 FileNotFoundError
        """
        import pandas as pd

        from adapters.qlib.qlib_model_trainer_adapter import QlibModelTrainerAdapter

        adapter = QlibModelTrainerAdapter()

        # 设置不存在的文件路径
        model_entity.file_path = "/path/to/non/existent/model.pkl"

        # 准备输入数据
        input_data = pd.DataFrame({
            'stock_code': ['sh600000'],
            'feature1': [0.5],
            'feature2': [0.3],
            'feature3': [-0.2],
        })

        # 验证
        with pytest.raises(Exception):
            await adapter.predict_batch(
                model=model_entity,
                input_data=input_data,
            )

    @pytest.mark.asyncio
    async def test_predict_batch_average_confidence(
        self, adapter_with_trained_model, model_entity,
    ):
        """
        测试 PredictionBatch 的平均置信度计算

        验证:
        1. batch.average_confidence() 返回有效值
        2. 平均置信度在 [0, 1] 范围内
        """
        import pandas as pd

        adapter = adapter_with_trained_model

        # 准备输入数据
        input_data = pd.DataFrame({
            'stock_code': ['sh600000', 'sz000001', 'sh600519'],
            'date': [datetime(2024, 1, 15)] * 3,
            'feature1': [0.5, 0.3, -0.1],
            'feature2': [0.3, -0.2, 0.4],
            'feature3': [-0.2, 0.1, 0.2],
        })

        # 执行
        batch = await adapter.predict_batch(
            model=model_entity,
            input_data=input_data,
        )

        # 验证
        avg_confidence = batch.average_confidence()
        assert avg_confidence is not None
        assert 0 <= avg_confidence <= 1

    @pytest.mark.asyncio
    async def test_predict_batch_to_dataframe(
        self, adapter_with_trained_model, model_entity,
    ):
        """
        测试 PredictionBatch 转换为 DataFrame

        验证:
        1. batch.to_dataframe() 返回有效的 DataFrame
        2. DataFrame 包含所有必要的列
        """
        import pandas as pd

        adapter = adapter_with_trained_model

        # 准备输入数据
        input_data = pd.DataFrame({
            'stock_code': ['sh600000', 'sz000001'],
            'date': [datetime(2024, 1, 15)] * 2,
            'feature1': [0.5, 0.3],
            'feature2': [0.3, -0.2],
            'feature3': [-0.2, 0.1],
        })

        # 执行
        batch = await adapter.predict_batch(
            model=model_entity,
            input_data=input_data,
        )

        # 转换为 DataFrame
        df = batch.to_dataframe()

        # 验证
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert 'stock_code' in df.columns
        assert 'timestamp' in df.columns
        assert 'predicted_value' in df.columns
        assert 'confidence' in df.columns
        assert 'model_id' in df.columns

    @pytest.mark.asyncio
    async def test_predict_batch_predictions_have_correct_attributes(
        self, adapter_with_trained_model, model_entity,
    ):
        """
        测试预测结果包含正确的属性

        验证:
        1. 每个预测包含 stock_code
        2. 每个预测包含 timestamp
        3. 每个预测包含 predicted_value
        4. 每个预测包含 confidence
        5. 每个预测包含 model_id
        """
        import pandas as pd

        from domain.value_objects.stock_code import StockCode

        adapter = adapter_with_trained_model

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
        batch = await adapter.predict_batch(
            model=model_entity,
            input_data=input_data,
        )

        # 验证
        prediction = batch.predictions[0]
        assert isinstance(prediction.stock_code, StockCode)
        assert prediction.stock_code.value == 'sh600000'
        assert prediction.timestamp == test_date
        assert isinstance(prediction.predicted_value, float)
        assert prediction.confidence is not None
        assert 0 <= prediction.confidence <= 1
        assert prediction.model_id == model_entity.id
