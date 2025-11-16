"""
Prediction Entity 和 PredictionBatch Aggregate 单元测试

测试 DR-005: Prediction (预测结果) 领域模型
"""

from datetime import datetime

import pytest

from domain.entities.prediction import Prediction, PredictionBatch
from domain.value_objects.stock_code import StockCode


class TestPredictionCreation:
    """测试 Prediction 创建"""

    def test_create_prediction_with_all_fields(self):
        """测试创建完整预测结果"""
        prediction = Prediction(
            stock_code=StockCode("sh600000"),
            timestamp=datetime(2024, 1, 15),
            predicted_value=0.05,
            model_id="model-123",
            confidence=0.85,
        )

        assert prediction.stock_code == StockCode("sh600000")
        assert prediction.timestamp == datetime(2024, 1, 15)
        assert prediction.predicted_value == 0.05
        assert prediction.confidence == 0.85

    def test_prediction_confidence_validation(self):
        """测试预测置信度验证"""
        # 置信度必须在 [0, 1] 范围内
        with pytest.raises(ValueError, match="confidence must be between 0 and 1"):
            Prediction(
                stock_code=StockCode("sh600000"),
                timestamp=datetime(2024, 1, 15),
                predicted_value=0.05,
                model_id="model-test",
                confidence=1.5,  # > 1
            )

        with pytest.raises(ValueError, match="confidence must be between 0 and 1"):
            Prediction(
                stock_code=StockCode("sh600000"),
                timestamp=datetime(2024, 1, 15),
                predicted_value=0.05,
                model_id="model-test",
                confidence=-0.1,  # < 0
            )


class TestPredictionIdentity:
    """测试 Prediction 实体身份"""

    def test_prediction_has_unique_id(self):
        """验证每个预测有唯一标识"""
        pred1 = Prediction(
            stock_code=StockCode("sh600000"),
            timestamp=datetime(2024, 1, 15),
            predicted_value=0.05,
            model_id="model-test",
        )
        pred2 = Prediction(
            stock_code=StockCode("sh600000"),
            timestamp=datetime(2024, 1, 15),
            predicted_value=0.05,
            model_id="model-test",
        )

        # 每个实体有唯一 ID
        assert hasattr(pred1, "id")
        assert hasattr(pred2, "id")
        assert pred1.id != pred2.id

    def test_prediction_equality_based_on_stock_and_date(self):
        """验证预测相等性基于股票代码和预测日期"""
        pred1 = Prediction(
            stock_code=StockCode("sh600000"),
            timestamp=datetime(2024, 1, 15),
            predicted_value=0.05,
            model_id="model-test",
        )
        pred2 = Prediction(
            stock_code=StockCode("sh600000"),
            timestamp=datetime(2024, 1, 15),
            predicted_value=0.08,  # 不同的预测值
            model_id="model-test",
        )
        pred3 = Prediction(
            stock_code=StockCode("sh600000"),
            timestamp=datetime(2024, 1, 16),  # 不同的日期
            predicted_value=0.05,
            model_id="model-test",
        )

        # 相同股票相同日期视为相等(业务相等性)
        assert pred1 == pred2

        # 不同日期不相等
        assert pred1 != pred3


class TestPredictionBatchCreation:
    """测试 PredictionBatch 聚合根创建"""

    def test_create_prediction_batch(self):
        """测试创建预测批次"""
        batch = PredictionBatch(
            model_id="model-123",
            generated_at=datetime(2024, 1, 15),
        )

        assert batch.model_id == "model-123"
        assert batch.batch_date == datetime(2024, 1, 15)
        assert len(batch.predictions) == 0

    def test_prediction_batch_has_unique_id(self):
        """验证每个批次有唯一标识"""
        batch1 = PredictionBatch(model_id="model-123", generated_at=datetime(2024, 1, 15))
        batch2 = PredictionBatch(model_id="model-123", generated_at=datetime(2024, 1, 15))

        assert hasattr(batch1, "id")
        assert hasattr(batch2, "id")
        assert batch1.id != batch2.id


class TestPredictionBatchAggregation:
    """测试 PredictionBatch 聚合操作"""

    def test_add_prediction_to_batch(self):
        """测试向批次添加预测"""
        batch = PredictionBatch(model_id="model-123", generated_at=datetime(2024, 1, 15))

        pred = Prediction(
            stock_code=StockCode("sh600000"),
            timestamp=datetime(2024, 1, 15),
            predicted_value=0.05,
            model_id="model-test",
        )

        batch.add_prediction(pred)

        assert len(batch.predictions) == 1
        assert batch.predictions[0] == pred

    def test_add_multiple_predictions(self):
        """测试添加多个预测"""
        batch = PredictionBatch(model_id="model-123", generated_at=datetime(2024, 1, 15))

        pred1 = Prediction(
            stock_code=StockCode("sh600000"),
            timestamp=datetime(2024, 1, 15),
            predicted_value=0.05,
            model_id="model-test",
        )
        pred2 = Prediction(
            stock_code=StockCode("sz000001"),
            timestamp=datetime(2024, 1, 15),
            predicted_value=0.03,
            model_id="model-test",
        )

        batch.add_prediction(pred1)
        batch.add_prediction(pred2)

        assert len(batch.predictions) == 2

    def test_cannot_add_duplicate_prediction(self):
        """测试不能添加重复预测(相同股票相同日期)"""
        batch = PredictionBatch(model_id="model-123", generated_at=datetime(2024, 1, 15))

        pred1 = Prediction(
            stock_code=StockCode("sh600000"),
            timestamp=datetime(2024, 1, 15),
            predicted_value=0.05,
            model_id="model-test",
        )
        pred2 = Prediction(
            stock_code=StockCode("sh600000"),
            timestamp=datetime(2024, 1, 15),
            predicted_value=0.08,  # 不同值,但相同股票+日期
            model_id="model-test",
        )

        batch.add_prediction(pred1)

        with pytest.raises(ValueError, match="Prediction already exists"):
            batch.add_prediction(pred2)

    def test_remove_prediction_from_batch(self):
        """测试从批次移除预测"""
        batch = PredictionBatch(model_id="model-123", generated_at=datetime(2024, 1, 15))

        pred = Prediction(
            stock_code=StockCode("sh600000"),
            timestamp=datetime(2024, 1, 15),
            predicted_value=0.05,
            model_id="model-test",
        )

        batch.add_prediction(pred)
        assert len(batch.predictions) == 1

        batch.remove_prediction(pred.stock_code, pred.timestamp)
        assert len(batch.predictions) == 0

    def test_get_prediction_by_stock(self):
        """测试根据股票代码获取预测"""
        batch = PredictionBatch(model_id="model-123", generated_at=datetime(2024, 1, 15))

        pred1 = Prediction(
            stock_code=StockCode("sh600000"),
            timestamp=datetime(2024, 1, 15),
            predicted_value=0.05,
            model_id="model-test",
        )
        pred2 = Prediction(
            stock_code=StockCode("sz000001"),
            timestamp=datetime(2024, 1, 15),
            predicted_value=0.03,
            model_id="model-test",
        )

        batch.add_prediction(pred1)
        batch.add_prediction(pred2)

        found = batch.get_prediction(StockCode("sh600000"), datetime(2024, 1, 15))
        assert found == pred1

    def test_get_nonexistent_prediction_returns_none(self):
        """测试获取不存在的预测返回 None"""
        batch = PredictionBatch(model_id="model-123", generated_at=datetime(2024, 1, 15))

        found = batch.get_prediction(StockCode("sh600000"), datetime(2024, 1, 15))
        assert found is None


class TestPredictionBatchStatistics:
    """测试 PredictionBatch 统计方法"""

    def test_batch_size(self):
        """测试批次大小"""
        batch = PredictionBatch(model_id="model-123", generated_at=datetime(2024, 1, 15))

        assert batch.size() == 0

        pred1 = Prediction(
            stock_code=StockCode("sh600000"),
            timestamp=datetime(2024, 1, 15),
            predicted_value=0.05,
            model_id="model-test",
        )
        pred2 = Prediction(
            stock_code=StockCode("sz000001"),
            timestamp=datetime(2024, 1, 15),
            predicted_value=0.03,
            model_id="model-test",
        )

        batch.add_prediction(pred1)
        batch.add_prediction(pred2)

        assert batch.size() == 2

    def test_average_confidence(self):
        """测试平均置信度"""
        batch = PredictionBatch(model_id="model-123", generated_at=datetime(2024, 1, 15))

        pred1 = Prediction(
            stock_code=StockCode("sh600000"),
            timestamp=datetime(2024, 1, 15),
            predicted_value=0.05,
            model_id="model-test",
            confidence=0.8,
        )
        pred2 = Prediction(
            stock_code=StockCode("sz000001"),
            timestamp=datetime(2024, 1, 15),
            predicted_value=0.03,
            model_id="model-test",
            confidence=0.6,
        )

        batch.add_prediction(pred1)
        batch.add_prediction(pred2)

        # 平均置信度 = (0.8 + 0.6) / 2 = 0.7
        assert batch.average_confidence() == 0.7

    def test_average_confidence_empty_batch(self):
        """测试空批次的平均置信度"""
        batch = PredictionBatch(model_id="model-123", generated_at=datetime(2024, 1, 15))

        assert batch.average_confidence() is None


class TestPredictionBatchStringRepresentation:
    """测试 PredictionBatch 字符串表示"""

    def test_batch_string_representation(self):
        """验证字符串表示"""
        batch = PredictionBatch(
            model_id="model-123", generated_at=datetime(2024, 1, 15, 10, 30),
        )

        batch_str = str(batch)
        assert "model-123" in batch_str
        assert "2024-01-15" in batch_str

        repr_str = repr(batch)
        assert "PredictionBatch" in repr_str
        assert "model-123" in repr_str
