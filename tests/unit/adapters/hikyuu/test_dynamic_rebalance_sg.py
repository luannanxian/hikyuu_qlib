"""
DynamicRebalanceSG 单元测试

测试动态调仓信号器的各种场景,包括:
1. Buy signal generation (enter Top-K)
2. Sell signal generation (exit Top-K)
3. Holding tracking
4. Rebalance date detection
5. Time conversion
6. Reset and clone functionality

遵循 TDD Red-Green-Refactor 流程
"""

from datetime import date
from unittest.mock import MagicMock, call
from typing import List

import pandas as pd
import pytest

from domain.value_objects.date_range import DateRange
from adapters.hikyuu.dynamic_rebalance_sg import DynamicRebalanceSG


class MockDateTime:
    """Mock Hikyuu Datetime"""
    def __init__(self, number: int):
        self.number = number

    def date(self):
        """Convert to Python date"""
        dt_str = str(self.number)
        year = int(dt_str[:4])
        month = int(dt_str[4:6])
        day = int(dt_str[6:8])
        return date(year, month, day)


class MockStock:
    """Mock Hikyuu Stock"""
    def __init__(self, market_code: str):
        self.market_code = market_code


class MockKRecord:
    """Mock Hikyuu KRecord"""
    def __init__(self, datetime: MockDateTime):
        self.datetime = datetime


class MockKData:
    """Mock Hikyuu KData"""
    def __init__(self, stock: MockStock, records: List[MockKRecord]):
        self._stock = stock
        self._records = records

    def getStock(self):
        return self._stock

    def __len__(self):
        return len(self._records)

    def __getitem__(self, index):
        return self._records[index]


class TestDynamicRebalanceSG:
    """DynamicRebalanceSG 测试类"""

    @pytest.fixture
    def mock_portfolio_adapter(self):
        """Mock Portfolio Adapter"""
        adapter = MagicMock()
        adapter._get_rebalance_dates = MagicMock(return_value=[])
        adapter.get_dynamic_stock_pool = MagicMock(return_value={})
        return adapter

    @pytest.fixture
    def signal_generator(self, mock_portfolio_adapter):
        """创建信号器实例"""
        return DynamicRebalanceSG(mock_portfolio_adapter)

    def test_initialization(self, mock_portfolio_adapter):
        """测试初始化"""
        # Arrange & Act
        sg = DynamicRebalanceSG(
            portfolio_adapter=mock_portfolio_adapter,
            name="TestSG"
        )

        # Assert
        assert sg.portfolio_adapter == mock_portfolio_adapter
        assert sg._name == "TestSG"
        assert len(sg._current_holdings) == 0

    def test_initialization_with_default_name(self, mock_portfolio_adapter):
        """测试使用默认名称初始化"""
        # Arrange & Act
        sg = DynamicRebalanceSG(portfolio_adapter=mock_portfolio_adapter)

        # Assert
        assert sg._name == "SG_DynamicRebalance"

    def test_hikyuu_to_pandas_datetime_conversion(self, signal_generator):
        """测试时间转换功能"""
        # Arrange
        hq_dt = MockDateTime(202301011500)  # 2023-01-01 15:00

        # Act
        pd_dt = signal_generator._hikyuu_to_pandas_datetime(hq_dt)

        # Assert
        assert pd_dt == pd.Timestamp(2023, 1, 1)
        assert pd_dt.hour == 0
        assert pd_dt.minute == 0
        assert pd_dt.second == 0

    def test_hikyuu_to_pandas_datetime_various_times(self, signal_generator):
        """测试不同时间的转换"""
        # Test cases
        test_cases = [
            (202301010930, pd.Timestamp(2023, 1, 1)),   # 09:30
            (202312311500, pd.Timestamp(2023, 12, 31)), # 15:00
            (202006150000, pd.Timestamp(2020, 6, 15)),  # 00:00
        ]

        for hq_number, expected_pd_dt in test_cases:
            # Arrange
            hq_dt = MockDateTime(hq_number)

            # Act
            pd_dt = signal_generator._hikyuu_to_pandas_datetime(hq_dt)

            # Assert
            assert pd_dt == expected_pd_dt, f"Failed for {hq_number}"

    def test_calculate_with_empty_kdata(self, signal_generator, mock_portfolio_adapter):
        """测试空 K线数据"""
        # Arrange
        stock = MockStock("SH600000")
        kdata = MockKData(stock, [])

        # Act
        signal_generator._calculate(kdata)

        # Assert
        mock_portfolio_adapter._get_rebalance_dates.assert_not_called()
        mock_portfolio_adapter.get_dynamic_stock_pool.assert_not_called()

    def test_calculate_with_no_rebalance_dates(self, signal_generator, mock_portfolio_adapter):
        """测试没有调仓日的情况"""
        # Arrange
        stock = MockStock("SH600000")
        records = [
            MockKRecord(MockDateTime(202301011500)),
            MockKRecord(MockDateTime(202301021500)),
        ]
        kdata = MockKData(stock, records)

        mock_portfolio_adapter._get_rebalance_dates.return_value = []

        # Act
        signal_generator._calculate(kdata)

        # Assert
        mock_portfolio_adapter._get_rebalance_dates.assert_called_once()
        mock_portfolio_adapter.get_dynamic_stock_pool.assert_not_called()
        assert len(signal_generator._current_holdings) == 0

    def test_buy_signal_when_entering_top_k(self, signal_generator, mock_portfolio_adapter):
        """测试股票进入 Top-K 时生成买入信号"""
        # Arrange
        stock = MockStock("SH600000")
        rebalance_date = pd.Timestamp(2023, 1, 2)
        records = [
            MockKRecord(MockDateTime(202301011500)),  # Non-rebalance day
            MockKRecord(MockDateTime(202301021500)),  # Rebalance day
            MockKRecord(MockDateTime(202301031500)),  # Non-rebalance day
        ]
        kdata = MockKData(stock, records)

        mock_portfolio_adapter._get_rebalance_dates.return_value = [rebalance_date]
        mock_portfolio_adapter.get_dynamic_stock_pool.return_value = {
            rebalance_date: ["SH600000", "SH600001"]
        }

        # Mock _addBuySignal
        signal_generator._addBuySignal = MagicMock()

        # Act
        signal_generator._calculate(kdata)

        # Assert
        signal_generator._addBuySignal.assert_called_once()
        assert "SH600000" in signal_generator._current_holdings

    def test_sell_signal_when_exiting_top_k(self, signal_generator, mock_portfolio_adapter):
        """测试股票退出 Top-K 时生成卖出信号"""
        # Arrange
        stock = MockStock("SH600000")
        rebalance_date1 = pd.Timestamp(2023, 1, 2)
        rebalance_date2 = pd.Timestamp(2023, 1, 9)

        records = [
            MockKRecord(MockDateTime(202301021500)),  # First rebalance: enter Top-K
            MockKRecord(MockDateTime(202301031500)),
            MockKRecord(MockDateTime(202301091500)),  # Second rebalance: exit Top-K
        ]
        kdata = MockKData(stock, records)

        mock_portfolio_adapter._get_rebalance_dates.return_value = [
            rebalance_date1,
            rebalance_date2
        ]
        mock_portfolio_adapter.get_dynamic_stock_pool.side_effect = [
            {rebalance_date1: ["SH600000", "SH600001"]},  # First call: in Top-K
            {rebalance_date2: ["SH600001", "SH600002"]},  # Second call: not in Top-K
        ]

        # Mock signals
        signal_generator._addBuySignal = MagicMock()
        signal_generator._addSellSignal = MagicMock()

        # Act
        signal_generator._calculate(kdata)

        # Assert
        signal_generator._addBuySignal.assert_called_once()
        signal_generator._addSellSignal.assert_called_once()
        assert "SH600000" not in signal_generator._current_holdings

    def test_no_signal_when_staying_in_top_k(self, signal_generator, mock_portfolio_adapter):
        """测试股票持续在 Top-K 时不生成信号"""
        # Arrange
        stock = MockStock("SH600000")
        rebalance_date1 = pd.Timestamp(2023, 1, 2)
        rebalance_date2 = pd.Timestamp(2023, 1, 9)

        records = [
            MockKRecord(MockDateTime(202301021500)),  # First rebalance
            MockKRecord(MockDateTime(202301091500)),  # Second rebalance
        ]
        kdata = MockKData(stock, records)

        mock_portfolio_adapter._get_rebalance_dates.return_value = [
            rebalance_date1,
            rebalance_date2
        ]
        mock_portfolio_adapter.get_dynamic_stock_pool.side_effect = [
            {rebalance_date1: ["SH600000", "SH600001"]},  # In Top-K
            {rebalance_date2: ["SH600000", "SH600001"]},  # Still in Top-K
        ]

        # Mock signals
        signal_generator._addBuySignal = MagicMock()
        signal_generator._addSellSignal = MagicMock()

        # Act
        signal_generator._calculate(kdata)

        # Assert
        signal_generator._addBuySignal.assert_called_once()  # Only first time
        signal_generator._addSellSignal.assert_not_called()
        assert "SH600000" in signal_generator._current_holdings

    def test_no_signal_when_staying_out_of_top_k(self, signal_generator, mock_portfolio_adapter):
        """测试股票持续不在 Top-K 时不生成信号"""
        # Arrange
        stock = MockStock("SH600000")
        rebalance_date1 = pd.Timestamp(2023, 1, 2)
        rebalance_date2 = pd.Timestamp(2023, 1, 9)

        records = [
            MockKRecord(MockDateTime(202301021500)),  # First rebalance
            MockKRecord(MockDateTime(202301091500)),  # Second rebalance
        ]
        kdata = MockKData(stock, records)

        mock_portfolio_adapter._get_rebalance_dates.return_value = [
            rebalance_date1,
            rebalance_date2
        ]
        mock_portfolio_adapter.get_dynamic_stock_pool.side_effect = [
            {rebalance_date1: ["SH600001", "SH600002"]},  # Not in Top-K
            {rebalance_date2: ["SH600001", "SH600002"]},  # Still not in Top-K
        ]

        # Mock signals
        signal_generator._addBuySignal = MagicMock()
        signal_generator._addSellSignal = MagicMock()

        # Act
        signal_generator._calculate(kdata)

        # Assert
        signal_generator._addBuySignal.assert_not_called()
        signal_generator._addSellSignal.assert_not_called()
        assert "SH600000" not in signal_generator._current_holdings

    def test_multiple_rebalance_dates(self, signal_generator, mock_portfolio_adapter):
        """测试多个调仓日的信号生成"""
        # Arrange
        stock = MockStock("SH600000")
        rebalance_dates = [
            pd.Timestamp(2023, 1, 2),
            pd.Timestamp(2023, 1, 9),
            pd.Timestamp(2023, 1, 16),
        ]

        records = [
            MockKRecord(MockDateTime(202301021500)),  # Rebalance 1: enter
            MockKRecord(MockDateTime(202301091500)),  # Rebalance 2: stay in
            MockKRecord(MockDateTime(202301161500)),  # Rebalance 3: exit
        ]
        kdata = MockKData(stock, records)

        mock_portfolio_adapter._get_rebalance_dates.return_value = rebalance_dates
        mock_portfolio_adapter.get_dynamic_stock_pool.side_effect = [
            {rebalance_dates[0]: ["SH600000", "SH600001"]},  # Enter
            {rebalance_dates[1]: ["SH600000", "SH600001"]},  # Stay
            {rebalance_dates[2]: ["SH600001", "SH600002"]},  # Exit
        ]

        # Mock signals
        signal_generator._addBuySignal = MagicMock()
        signal_generator._addSellSignal = MagicMock()

        # Act
        signal_generator._calculate(kdata)

        # Assert
        assert signal_generator._addBuySignal.call_count == 1
        assert signal_generator._addSellSignal.call_count == 1
        assert "SH600000" not in signal_generator._current_holdings

    def test_reset_clears_holdings(self, signal_generator):
        """测试 reset 方法清空持仓"""
        # Arrange
        signal_generator._current_holdings.add("SH600000")
        signal_generator._current_holdings.add("SH600001")

        # Act
        signal_generator._reset()

        # Assert
        assert len(signal_generator._current_holdings) == 0

    def test_clone_creates_new_instance(self, signal_generator, mock_portfolio_adapter):
        """测试 clone 方法创建新实例"""
        # Arrange
        signal_generator._current_holdings.add("SH600000")

        # Act
        cloned = signal_generator._clone()

        # Assert
        assert cloned is not signal_generator
        assert cloned.portfolio_adapter == signal_generator.portfolio_adapter
        assert cloned._name == signal_generator._name
        # Holdings should not be shared
        assert len(cloned._current_holdings) == 0

    def test_get_current_holdings(self, signal_generator):
        """测试获取当前持仓"""
        # Arrange
        signal_generator._current_holdings.add("SH600000")
        signal_generator._current_holdings.add("SH600001")

        # Act
        holdings = signal_generator.get_current_holdings()

        # Assert
        assert holdings == {"SH600000", "SH600001"}
        # Should return a copy
        holdings.add("SH600002")
        assert "SH600002" not in signal_generator._current_holdings

    def test_rebalance_date_query(self, signal_generator, mock_portfolio_adapter):
        """测试调仓日期查询的参数传递"""
        # Arrange
        stock = MockStock("SH600000")
        records = [
            MockKRecord(MockDateTime(202301011500)),
            MockKRecord(MockDateTime(202301101500)),
        ]
        kdata = MockKData(stock, records)

        mock_portfolio_adapter._get_rebalance_dates.return_value = []

        # Act
        signal_generator._calculate(kdata)

        # Assert
        call_args = mock_portfolio_adapter._get_rebalance_dates.call_args[0][0]
        assert call_args.start_date == date(2023, 1, 1)
        assert call_args.end_date == date(2023, 1, 10)

    def test_stock_pool_query_on_rebalance_date(self, signal_generator, mock_portfolio_adapter):
        """测试在调仓日查询股票池"""
        # Arrange
        stock = MockStock("SH600000")
        rebalance_date = pd.Timestamp(2023, 1, 2)
        records = [
            MockKRecord(MockDateTime(202301021500)),
        ]
        kdata = MockKData(stock, records)

        mock_portfolio_adapter._get_rebalance_dates.return_value = [rebalance_date]
        mock_portfolio_adapter.get_dynamic_stock_pool.return_value = {
            rebalance_date: ["SH600000"]
        }

        signal_generator._addBuySignal = MagicMock()

        # Act
        signal_generator._calculate(kdata)

        # Assert
        call_args = mock_portfolio_adapter.get_dynamic_stock_pool.call_args[0][0]
        assert call_args.start_date == date(2023, 1, 2)
        assert call_args.end_date == date(2023, 1, 2)

    def test_empty_stock_pool_on_rebalance_date(self, signal_generator, mock_portfolio_adapter):
        """测试调仓日股票池为空的情况"""
        # Arrange
        stock = MockStock("SH600000")
        rebalance_date = pd.Timestamp(2023, 1, 2)

        # Pre-add to holdings to test sell signal
        signal_generator._current_holdings.add("SH600000")

        records = [
            MockKRecord(MockDateTime(202301021500)),
        ]
        kdata = MockKData(stock, records)

        mock_portfolio_adapter._get_rebalance_dates.return_value = [rebalance_date]
        mock_portfolio_adapter.get_dynamic_stock_pool.return_value = {
            rebalance_date: []  # Empty pool
        }

        signal_generator._addSellSignal = MagicMock()

        # Act
        signal_generator._calculate(kdata)

        # Assert
        signal_generator._addSellSignal.assert_called_once()
        assert "SH600000" not in signal_generator._current_holdings

    def test_non_rebalance_dates_skipped(self, signal_generator, mock_portfolio_adapter):
        """测试非调仓日不处理"""
        # Arrange
        stock = MockStock("SH600000")
        rebalance_date = pd.Timestamp(2023, 1, 5)

        records = [
            MockKRecord(MockDateTime(202301021500)),  # Not rebalance day
            MockKRecord(MockDateTime(202301031500)),  # Not rebalance day
            MockKRecord(MockDateTime(202301041500)),  # Not rebalance day
            MockKRecord(MockDateTime(202301051500)),  # Rebalance day
        ]
        kdata = MockKData(stock, records)

        mock_portfolio_adapter._get_rebalance_dates.return_value = [rebalance_date]
        mock_portfolio_adapter.get_dynamic_stock_pool.return_value = {
            rebalance_date: ["SH600000"]
        }

        signal_generator._addBuySignal = MagicMock()

        # Act
        signal_generator._calculate(kdata)

        # Assert
        # Should only be called once on the rebalance date
        assert signal_generator._addBuySignal.call_count == 1
        assert mock_portfolio_adapter.get_dynamic_stock_pool.call_count == 1


class TestDynamicRebalanceSGIntegration:
    """DynamicRebalanceSG 集成测试"""

    def test_complete_rebalance_scenario(self):
        """测试完整的调仓场景"""
        # Arrange
        mock_adapter = MagicMock()

        # Setup dates
        dates = [
            pd.Timestamp(2023, 1, 2),   # Week 1: SH600000 enters
            pd.Timestamp(2023, 1, 9),   # Week 2: SH600000 stays
            pd.Timestamp(2023, 1, 16),  # Week 3: SH600000 exits
            pd.Timestamp(2023, 1, 23),  # Week 4: SH600000 re-enters
        ]

        mock_adapter._get_rebalance_dates.return_value = dates

        # Setup stock pools
        def get_pool(date_range):
            target_date = pd.Timestamp(date_range.start_date)
            pools = {
                dates[0]: ["SH600000", "SH600001", "SH600002"],
                dates[1]: ["SH600000", "SH600001", "SH600003"],
                dates[2]: ["SH600001", "SH600003", "SH600004"],
                dates[3]: ["SH600000", "SH600003", "SH600004"],
            }
            return {target_date: pools.get(target_date, [])}

        mock_adapter.get_dynamic_stock_pool.side_effect = get_pool

        # Create signal generator
        sg = DynamicRebalanceSG(mock_adapter)
        sg._addBuySignal = MagicMock()
        sg._addSellSignal = MagicMock()

        # Create KData
        stock = MockStock("SH600000")
        records = [
            MockKRecord(MockDateTime(202301021500)),
            MockKRecord(MockDateTime(202301091500)),
            MockKRecord(MockDateTime(202301161500)),
            MockKRecord(MockDateTime(202301231500)),
        ]
        kdata = MockKData(stock, records)

        # Act
        sg._calculate(kdata)

        # Assert
        # Should have 2 buy signals (week 1 and week 4)
        assert sg._addBuySignal.call_count == 2
        # Should have 1 sell signal (week 3)
        assert sg._addSellSignal.call_count == 1
        # Should end with holding
        assert "SH600000" in sg._current_holdings
