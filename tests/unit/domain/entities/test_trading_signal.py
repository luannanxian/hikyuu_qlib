"""
TradingSignal Entity 和 SignalBatch Aggregate 单元测试

测试 DR-006: TradingSignal (交易信号) 领域模型
"""

from datetime import datetime
from decimal import Decimal

import pytest

from domain.entities.trading_signal import (
    SignalBatch,
    SignalStrength,
    SignalType,
    TradingSignal,
)
from domain.value_objects.stock_code import StockCode


class TestTradingSignalCreation:
    """测试 TradingSignal 创建"""

    def test_create_signal_with_all_fields(self):
        """测试创建完整交易信号"""
        signal = TradingSignal(
            stock_code=StockCode("sh600000"),
            signal_date=datetime(2024, 1, 15),
            signal_type=SignalType.BUY,
            signal_strength=SignalStrength.STRONG,
            price=Decimal("11.50"),
            reason="技术突破",
        )

        assert signal.stock_code == StockCode("sh600000")
        assert signal.signal_date == datetime(2024, 1, 15)
        assert signal.signal_type == SignalType.BUY
        assert signal.signal_strength == SignalStrength.STRONG
        assert signal.price == Decimal("11.50")
        assert signal.reason == "技术突破"

    def test_create_signal_with_minimal_fields(self):
        """测试创建最小字段交易信号"""
        signal = TradingSignal(
            stock_code=StockCode("sh600000"),
            signal_date=datetime(2024, 1, 15),
            signal_type=SignalType.HOLD,
        )

        assert signal.signal_type == SignalType.HOLD
        assert signal.signal_strength == SignalStrength.MEDIUM  # 默认值
        assert signal.price is None
        assert signal.reason is None

    def test_signal_price_validation(self):
        """测试信号价格验证"""
        # 价格必须 > 0
        with pytest.raises(ValueError, match="price must be > 0"):
            TradingSignal(
                stock_code=StockCode("sh600000"),
                signal_date=datetime(2024, 1, 15),
                signal_type=SignalType.BUY,
                price=Decimal(0),
            )

        with pytest.raises(ValueError, match="price must be > 0"):
            TradingSignal(
                stock_code=StockCode("sh600000"),
                signal_date=datetime(2024, 1, 15),
                signal_type=SignalType.SELL,
                price=Decimal("-10.5"),
            )


class TestSignalType:
    """测试信号类型"""

    def test_signal_types(self):
        """测试不同的信号类型"""
        buy = TradingSignal(
            stock_code=StockCode("sh600000"),
            signal_date=datetime(2024, 1, 15),
            signal_type=SignalType.BUY,
        )
        assert buy.signal_type == SignalType.BUY

        sell = TradingSignal(
            stock_code=StockCode("sh600000"),
            signal_date=datetime(2024, 1, 15),
            signal_type=SignalType.SELL,
        )
        assert sell.signal_type == SignalType.SELL

        hold = TradingSignal(
            stock_code=StockCode("sh600000"),
            signal_date=datetime(2024, 1, 15),
            signal_type=SignalType.HOLD,
        )
        assert hold.signal_type == SignalType.HOLD


class TestSignalStrength:
    """测试信号强度"""

    def test_signal_strengths(self):
        """测试不同的信号强度"""
        weak = TradingSignal(
            stock_code=StockCode("sh600000"),
            signal_date=datetime(2024, 1, 15),
            signal_type=SignalType.BUY,
            signal_strength=SignalStrength.WEAK,
        )
        assert weak.signal_strength == SignalStrength.WEAK

        medium = TradingSignal(
            stock_code=StockCode("sh600000"),
            signal_date=datetime(2024, 1, 15),
            signal_type=SignalType.BUY,
            signal_strength=SignalStrength.MEDIUM,
        )
        assert medium.signal_strength == SignalStrength.MEDIUM

        strong = TradingSignal(
            stock_code=StockCode("sh600000"),
            signal_date=datetime(2024, 1, 15),
            signal_type=SignalType.BUY,
            signal_strength=SignalStrength.STRONG,
        )
        assert strong.signal_strength == SignalStrength.STRONG


class TestTradingSignalIdentity:
    """测试 TradingSignal 实体身份"""

    def test_signal_has_unique_id(self):
        """验证每个信号有唯一标识"""
        signal1 = TradingSignal(
            stock_code=StockCode("sh600000"),
            signal_date=datetime(2024, 1, 15),
            signal_type=SignalType.BUY,
        )
        signal2 = TradingSignal(
            stock_code=StockCode("sh600000"),
            signal_date=datetime(2024, 1, 15),
            signal_type=SignalType.BUY,
        )

        # 每个实体有唯一 ID
        assert hasattr(signal1, "id")
        assert hasattr(signal2, "id")
        assert signal1.id != signal2.id

    def test_signal_equality_based_on_stock_and_date(self):
        """验证信号相等性基于股票代码和日期"""
        signal1 = TradingSignal(
            stock_code=StockCode("sh600000"),
            signal_date=datetime(2024, 1, 15),
            signal_type=SignalType.BUY,
        )
        signal2 = TradingSignal(
            stock_code=StockCode("sh600000"),
            signal_date=datetime(2024, 1, 15),
            signal_type=SignalType.SELL,  # 不同类型
        )
        signal3 = TradingSignal(
            stock_code=StockCode("sh600000"),
            signal_date=datetime(2024, 1, 16),  # 不同日期
            signal_type=SignalType.BUY,
        )

        # 相同股票相同日期视为相等
        assert signal1 == signal2

        # 不同日期不相等
        assert signal1 != signal3


class TestSignalBatchCreation:
    """测试 SignalBatch 聚合根创建"""

    def test_create_signal_batch(self):
        """测试创建信号批次"""
        batch = SignalBatch(
            strategy_name="MA_Cross",
            batch_date=datetime(2024, 1, 15),
        )

        assert batch.strategy_name == "MA_Cross"
        assert batch.batch_date == datetime(2024, 1, 15)
        assert len(batch.signals) == 0

    def test_signal_batch_has_unique_id(self):
        """验证每个批次有唯一标识"""
        batch1 = SignalBatch(strategy_name="MA_Cross", batch_date=datetime(2024, 1, 15))
        batch2 = SignalBatch(strategy_name="MA_Cross", batch_date=datetime(2024, 1, 15))

        assert hasattr(batch1, "id")
        assert hasattr(batch2, "id")
        assert batch1.id != batch2.id


class TestSignalBatchAggregation:
    """测试 SignalBatch 聚合操作"""

    def test_add_signal_to_batch(self):
        """测试向批次添加信号"""
        batch = SignalBatch(strategy_name="MA_Cross", batch_date=datetime(2024, 1, 15))

        signal = TradingSignal(
            stock_code=StockCode("sh600000"),
            signal_date=datetime(2024, 1, 15),
            signal_type=SignalType.BUY,
        )

        batch.add_signal(signal)

        assert len(batch.signals) == 1
        assert batch.signals[0] == signal

    def test_add_multiple_signals(self):
        """测试添加多个信号"""
        batch = SignalBatch(strategy_name="MA_Cross", batch_date=datetime(2024, 1, 15))

        signal1 = TradingSignal(
            stock_code=StockCode("sh600000"),
            signal_date=datetime(2024, 1, 15),
            signal_type=SignalType.BUY,
        )
        signal2 = TradingSignal(
            stock_code=StockCode("sz000001"),
            signal_date=datetime(2024, 1, 15),
            signal_type=SignalType.SELL,
        )

        batch.add_signal(signal1)
        batch.add_signal(signal2)

        assert len(batch.signals) == 2

    def test_cannot_add_duplicate_signal(self):
        """测试不能添加重复信号(相同股票相同日期)"""
        batch = SignalBatch(strategy_name="MA_Cross", batch_date=datetime(2024, 1, 15))

        signal1 = TradingSignal(
            stock_code=StockCode("sh600000"),
            signal_date=datetime(2024, 1, 15),
            signal_type=SignalType.BUY,
        )
        signal2 = TradingSignal(
            stock_code=StockCode("sh600000"),
            signal_date=datetime(2024, 1, 15),
            signal_type=SignalType.SELL,  # 不同类型,但相同股票+日期
        )

        batch.add_signal(signal1)

        with pytest.raises(ValueError, match="Signal already exists"):
            batch.add_signal(signal2)

    def test_remove_signal_from_batch(self):
        """测试从批次移除信号"""
        batch = SignalBatch(strategy_name="MA_Cross", batch_date=datetime(2024, 1, 15))

        signal = TradingSignal(
            stock_code=StockCode("sh600000"),
            signal_date=datetime(2024, 1, 15),
            signal_type=SignalType.BUY,
        )

        batch.add_signal(signal)
        assert len(batch.signals) == 1

        batch.remove_signal(signal.stock_code, signal.signal_date)
        assert len(batch.signals) == 0

    def test_get_signal_by_stock(self):
        """测试根据股票代码获取信号"""
        batch = SignalBatch(strategy_name="MA_Cross", batch_date=datetime(2024, 1, 15))

        signal1 = TradingSignal(
            stock_code=StockCode("sh600000"),
            signal_date=datetime(2024, 1, 15),
            signal_type=SignalType.BUY,
        )
        signal2 = TradingSignal(
            stock_code=StockCode("sz000001"),
            signal_date=datetime(2024, 1, 15),
            signal_type=SignalType.SELL,
        )

        batch.add_signal(signal1)
        batch.add_signal(signal2)

        found = batch.get_signal(StockCode("sh600000"), datetime(2024, 1, 15))
        assert found == signal1

    def test_get_nonexistent_signal_returns_none(self):
        """测试获取不存在的信号返回 None"""
        batch = SignalBatch(strategy_name="MA_Cross", batch_date=datetime(2024, 1, 15))

        found = batch.get_signal(StockCode("sh600000"), datetime(2024, 1, 15))
        assert found is None


class TestSignalBatchFiltering:
    """测试 SignalBatch 过滤方法"""

    def test_filter_by_signal_type(self):
        """测试按信号类型过滤"""
        batch = SignalBatch(strategy_name="MA_Cross", batch_date=datetime(2024, 1, 15))

        buy1 = TradingSignal(
            stock_code=StockCode("sh600000"),
            signal_date=datetime(2024, 1, 15),
            signal_type=SignalType.BUY,
        )
        buy2 = TradingSignal(
            stock_code=StockCode("sh600001"),
            signal_date=datetime(2024, 1, 15),
            signal_type=SignalType.BUY,
        )
        sell = TradingSignal(
            stock_code=StockCode("sz000001"),
            signal_date=datetime(2024, 1, 15),
            signal_type=SignalType.SELL,
        )

        batch.add_signal(buy1)
        batch.add_signal(buy2)
        batch.add_signal(sell)

        buy_signals = batch.filter_by_type(SignalType.BUY)
        assert len(buy_signals) == 2
        assert all(s.signal_type == SignalType.BUY for s in buy_signals)

    def test_filter_by_signal_strength(self):
        """测试按信号强度过滤"""
        batch = SignalBatch(strategy_name="MA_Cross", batch_date=datetime(2024, 1, 15))

        strong1 = TradingSignal(
            stock_code=StockCode("sh600000"),
            signal_date=datetime(2024, 1, 15),
            signal_type=SignalType.BUY,
            signal_strength=SignalStrength.STRONG,
        )
        strong2 = TradingSignal(
            stock_code=StockCode("sh600001"),
            signal_date=datetime(2024, 1, 15),
            signal_type=SignalType.BUY,
            signal_strength=SignalStrength.STRONG,
        )
        weak = TradingSignal(
            stock_code=StockCode("sz000001"),
            signal_date=datetime(2024, 1, 15),
            signal_type=SignalType.SELL,
            signal_strength=SignalStrength.WEAK,
        )

        batch.add_signal(strong1)
        batch.add_signal(strong2)
        batch.add_signal(weak)

        strong_signals = batch.filter_by_strength(SignalStrength.STRONG)
        assert len(strong_signals) == 2
        assert all(s.signal_strength == SignalStrength.STRONG for s in strong_signals)


class TestSignalBatchStatistics:
    """测试 SignalBatch 统计方法"""

    def test_batch_size(self):
        """测试批次大小"""
        batch = SignalBatch(strategy_name="MA_Cross", batch_date=datetime(2024, 1, 15))

        assert batch.size() == 0

        signal1 = TradingSignal(
            stock_code=StockCode("sh600000"),
            signal_date=datetime(2024, 1, 15),
            signal_type=SignalType.BUY,
        )
        signal2 = TradingSignal(
            stock_code=StockCode("sz000001"),
            signal_date=datetime(2024, 1, 15),
            signal_type=SignalType.SELL,
        )

        batch.add_signal(signal1)
        batch.add_signal(signal2)

        assert batch.size() == 2

    def test_count_by_type(self):
        """测试按类型统计"""
        batch = SignalBatch(strategy_name="MA_Cross", batch_date=datetime(2024, 1, 15))

        buy1 = TradingSignal(
            stock_code=StockCode("sh600000"),
            signal_date=datetime(2024, 1, 15),
            signal_type=SignalType.BUY,
        )
        buy2 = TradingSignal(
            stock_code=StockCode("sh600001"),
            signal_date=datetime(2024, 1, 15),
            signal_type=SignalType.BUY,
        )
        sell = TradingSignal(
            stock_code=StockCode("sz000001"),
            signal_date=datetime(2024, 1, 15),
            signal_type=SignalType.SELL,
        )

        batch.add_signal(buy1)
        batch.add_signal(buy2)
        batch.add_signal(sell)

        counts = batch.count_by_type()
        assert counts[SignalType.BUY] == 2
        assert counts[SignalType.SELL] == 1
        assert counts[SignalType.HOLD] == 0


class TestSignalBatchStringRepresentation:
    """测试 SignalBatch 字符串表示"""

    def test_batch_string_representation(self):
        """验证字符串表示"""
        batch = SignalBatch(
            strategy_name="MA_Cross", batch_date=datetime(2024, 1, 15, 10, 30),
        )

        batch_str = str(batch)
        assert "MA_Cross" in batch_str
        assert "2024-01-15" in batch_str

        repr_str = repr(batch)
        assert "SignalBatch" in repr_str
        assert "MA_Cross" in repr_str
