"""
Unit Tests for CustomSG_QlibFactor Adapter

测试信号提供者的核心功能:
- 时间转换
- Top-K计算
- 信号生成逻辑
- 边缘情况处理
"""

import tempfile
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pandas as pd
import pytest

from adapters.hikyuu.custom_sg_qlib_factor import (
    CustomSG_QlibFactor,
    Datetime,
    Stock,
)
from domain.entities.prediction import Prediction, PredictionBatch
from domain.entities.trading_signal import SignalType, SignalStrength
from domain.value_objects.stock_code import StockCode


class TestTimeConversion:
    """测试时间转换功能"""

    def test_hikyuu_to_pandas_datetime_with_time(self):
        """测试Hikyuu时间戳转pandas时间戳(带时分)"""
        sg = CustomSG_QlibFactor(pred_pkl_path="dummy.pkl")

        # 2018-09-21 09:30
        hq_dt = Datetime(201809210930)
        pd_dt = sg._hikyuu_to_pandas_datetime(hq_dt)

        assert pd_dt.year == 2018
        assert pd_dt.month == 9
        assert pd_dt.day == 21
        assert pd_dt.hour == 9
        assert pd_dt.minute == 30

    def test_hikyuu_to_pandas_datetime_date_only(self):
        """测试Hikyuu时间戳转pandas时间戳(仅日期)"""
        sg = CustomSG_QlibFactor(pred_pkl_path="dummy.pkl")

        # 2018-09-21 00:00
        hq_dt = Datetime(20180921)
        pd_dt = sg._hikyuu_to_pandas_datetime(hq_dt)

        assert pd_dt.year == 2018
        assert pd_dt.month == 9
        assert pd_dt.day == 21
        assert pd_dt.hour == 0
        assert pd_dt.minute == 0

    def test_pandas_to_hikyuu_datetime(self):
        """测试pandas时间戳转Hikyuu时间戳"""
        sg = CustomSG_QlibFactor(pred_pkl_path="dummy.pkl")

        pd_dt = pd.Timestamp(year=2018, month=9, day=21, hour=9, minute=30)
        hq_dt = sg._pandas_to_hikyuu_datetime(pd_dt)

        assert hq_dt.number == 201809210930

    def test_round_trip_conversion(self):
        """测试时间戳往返转换"""
        sg = CustomSG_QlibFactor(pred_pkl_path="dummy.pkl")

        # Hikyuu -> Pandas -> Hikyuu
        original_hq = Datetime(201809210930)
        pd_dt = sg._hikyuu_to_pandas_datetime(original_hq)
        converted_hq = sg._pandas_to_hikyuu_datetime(pd_dt)

        assert original_hq.number == converted_hq.number


class TestStockCodeNormalization:
    """测试股票代码标准化"""

    def test_normalize_stock_code_lowercase_to_uppercase(self):
        """测试小写转大写"""
        sg = CustomSG_QlibFactor(pred_pkl_path="dummy.pkl")

        stock = Stock("sh600000")
        normalized = sg._normalize_stock_code(stock)

        assert normalized == "SH600000"

    def test_normalize_stock_code_already_uppercase(self):
        """测试已经是大写的情况"""
        sg = CustomSG_QlibFactor(pred_pkl_path="dummy.pkl")

        stock = Stock("SZ000001")
        normalized = sg._normalize_stock_code(stock)

        assert normalized == "SZ000001"


class TestLoadPredictions:
    """测试加载预测结果"""

    def create_test_pred_file(self, tmp_path: Path, top_k: int = None) -> Path:
        """创建测试用的pred.pkl文件"""
        dates = pd.date_range("2018-09-21", periods=3, freq="D")
        instruments = ["SH600000", "SH600157", "SZ000001", "SZ000002"]

        # 创建MultiIndex
        index = pd.MultiIndex.from_product(
            [dates, instruments], names=["datetime", "instrument"]
        )

        # 创建预测分数(递增,方便测试Top-K)
        scores = [i * 0.01 for i in range(len(index))]
        pred_df = pd.DataFrame({"score": scores}, index=index)

        # 保存为pickle
        pred_file = tmp_path / "test_pred.pkl"
        pred_df.to_pickle(pred_file)

        return pred_file

    def test_load_predictions_success(self, tmp_path):
        """测试成功加载预测文件"""
        pred_file = self.create_test_pred_file(tmp_path)

        sg = CustomSG_QlibFactor(pred_pkl_path=str(pred_file))
        sg._load_predictions()

        assert sg._pred_df is not None
        assert isinstance(sg._pred_df.index, pd.MultiIndex)
        assert len(sg._stock_predictions) == 4  # 4只股票

    def test_load_predictions_file_not_found(self):
        """测试文件不存在时抛出异常"""
        sg = CustomSG_QlibFactor(pred_pkl_path="/nonexistent/pred.pkl")

        with pytest.raises(FileNotFoundError, match="Prediction file not found"):
            sg._load_predictions()

    def test_load_predictions_invalid_format_no_multiindex(self, tmp_path):
        """测试无效格式:非MultiIndex"""
        # 创建单索引DataFrame
        df = pd.DataFrame({"score": [0.1, 0.2, 0.3]}, index=[0, 1, 2])
        pred_file = tmp_path / "invalid_pred.pkl"
        df.to_pickle(pred_file)

        sg = CustomSG_QlibFactor(pred_pkl_path=str(pred_file))

        with pytest.raises(ValueError, match="must have MultiIndex"):
            sg._load_predictions()

    def test_load_predictions_missing_score_column(self, tmp_path):
        """测试缺少score列"""
        dates = pd.date_range("2018-09-21", periods=2)
        instruments = ["SH600000", "SZ000001"]
        index = pd.MultiIndex.from_product(
            [dates, instruments], names=["datetime", "instrument"]
        )

        # 使用错误的列名
        df = pd.DataFrame({"wrong_column": [0.1, 0.2, 0.3, 0.4]}, index=index)
        pred_file = tmp_path / "no_score.pkl"
        df.to_pickle(pred_file)

        sg = CustomSG_QlibFactor(pred_pkl_path=str(pred_file))

        with pytest.raises(ValueError, match="Score column not found"):
            sg._load_predictions()

    def test_detect_score_column_variations(self, tmp_path):
        """测试检测不同的分数列名"""
        dates = pd.date_range("2018-09-21", periods=2)
        instruments = ["SH600000"]
        index = pd.MultiIndex.from_product(
            [dates, instruments], names=["datetime", "instrument"]
        )

        # 测试不同的列名
        for col_name in ["score", "score_0", "pred", "prediction"]:
            df = pd.DataFrame({col_name: [0.1, 0.2]}, index=index)
            pred_file = tmp_path / f"{col_name}_pred.pkl"
            df.to_pickle(pred_file)

            sg = CustomSG_QlibFactor(pred_pkl_path=str(pred_file))
            sg._load_predictions()

            assert sg._pred_df is not None


class TestTopKCalculation:
    """测试Top-K选股计算"""

    def create_test_pred_file_with_scores(self, tmp_path: Path) -> Path:
        """创建带有明确分数的测试文件"""
        date = pd.Timestamp("2018-09-21")
        instruments = ["SH600000", "SH600157", "SZ000001", "SZ000002", "SH600519"]

        # 创建明确的分数排序
        scores = [0.05, 0.03, 0.08, 0.02, 0.10]  # SH600519最高, SZ000001第二, SH600000第三

        index = pd.MultiIndex.from_arrays(
            [[date] * 5, instruments], names=["datetime", "instrument"]
        )

        pred_df = pd.DataFrame({"score": scores}, index=index)

        pred_file = tmp_path / "topk_pred.pkl"
        pred_df.to_pickle(pred_file)

        return pred_file

    def test_top_k_calculation_basic(self, tmp_path):
        """测试基础Top-K计算"""
        pred_file = self.create_test_pred_file_with_scores(tmp_path)

        sg = CustomSG_QlibFactor(pred_pkl_path=str(pred_file), top_k=3)
        sg._load_predictions()

        # 只有Top-3的股票应该被存储
        assert len(sg._stock_predictions) == 3

        # 验证Top-3股票
        assert "SH600519" in sg._stock_predictions  # 0.10
        assert "SZ000001" in sg._stock_predictions  # 0.08
        assert "SH600000" in sg._stock_predictions  # 0.05

        # 验证不在Top-3的股票
        assert "SH600157" not in sg._stock_predictions  # 0.03
        assert "SZ000002" not in sg._stock_predictions  # 0.02

    def test_top_k_none_means_all_stocks(self, tmp_path):
        """测试top_k=None时包含所有股票"""
        pred_file = self.create_test_pred_file_with_scores(tmp_path)

        sg = CustomSG_QlibFactor(pred_pkl_path=str(pred_file), top_k=None)
        sg._load_predictions()

        # 所有5只股票都应该被存储
        assert len(sg._stock_predictions) == 5

    def test_top_k_by_date(self, tmp_path):
        """测试按日期计算Top-K"""
        # 创建多日期数据
        dates = pd.date_range("2018-09-21", periods=2)
        instruments = ["SH600000", "SZ000001", "SH600157"]

        # 第一天: SZ000001最高, 第二天: SH600157最高
        index = pd.MultiIndex.from_product(
            [dates, instruments], names=["datetime", "instrument"]
        )
        scores = [
            0.05,
            0.08,
            0.03,  # 2018-09-21
            0.02,
            0.04,
            0.09,  # 2018-09-22
        ]
        pred_df = pd.DataFrame({"score": scores}, index=index)

        pred_file = tmp_path / "multidate_pred.pkl"
        pred_df.to_pickle(pred_file)

        sg = CustomSG_QlibFactor(pred_pkl_path=str(pred_file), top_k=2)
        sg._load_predictions()

        # 检查每日Top-K记录
        assert len(sg._top_k_stocks_by_date) == 2

        # 第一天Top-2: SZ000001, SH600000
        date1 = pd.Timestamp("2018-09-21").normalize()
        assert "SZ000001" in sg._top_k_stocks_by_date[date1]
        assert "SH600000" in sg._top_k_stocks_by_date[date1]

        # 第二天Top-2: SH600157, SZ000001
        date2 = pd.Timestamp("2018-09-22").normalize()
        assert "SH600157" in sg._top_k_stocks_by_date[date2]
        assert "SZ000001" in sg._top_k_stocks_by_date[date2]


class TestCalculateSignals:
    """测试信号生成(Hikyuu接口)"""

    def test_calculate_generates_buy_signal(self, tmp_path):
        """测试生成买入信号"""
        # 创建预测数据: SH600000有高预测值
        date = pd.Timestamp("2018-09-21")
        index = pd.MultiIndex.from_arrays(
            [[date], ["SH600000"]], names=["datetime", "instrument"]
        )
        pred_df = pd.DataFrame({"score": [0.05]}, index=index)  # > 0.02 buy_threshold

        pred_file = tmp_path / "buy_signal.pkl"
        pred_df.to_pickle(pred_file)

        sg = CustomSG_QlibFactor(
            pred_pkl_path=str(pred_file), buy_threshold=0.02, sell_threshold=-0.02
        )

        # 模拟KData
        class MockKData:
            def __len__(self):
                return 1

            def __getitem__(self, idx):
                class MockKRecord:
                    datetime = Datetime(20180921)

                return MockKRecord()

            def getStock(self):
                return Stock("SH600000")

        kdata = MockKData()

        # 记录信号调用
        buy_signals = []
        sell_signals = []

        original_add_buy = sg._addBuySignal
        original_add_sell = sg._addSellSignal

        sg._addBuySignal = lambda dt: buy_signals.append(dt)
        sg._addSellSignal = lambda dt: sell_signals.append(dt)

        sg._calculate(kdata)

        # 验证生成了买入信号
        assert len(buy_signals) == 1
        assert len(sell_signals) == 0

    def test_calculate_generates_sell_signal(self, tmp_path):
        """测试生成卖出信号"""
        date = pd.Timestamp("2018-09-21")
        index = pd.MultiIndex.from_arrays(
            [[date], ["SH600000"]], names=["datetime", "instrument"]
        )
        pred_df = pd.DataFrame(
            {"score": [-0.05]}, index=index
        )  # < -0.02 sell_threshold

        pred_file = tmp_path / "sell_signal.pkl"
        pred_df.to_pickle(pred_file)

        sg = CustomSG_QlibFactor(
            pred_pkl_path=str(pred_file), buy_threshold=0.02, sell_threshold=-0.02
        )

        class MockKData:
            def __len__(self):
                return 1

            def __getitem__(self, idx):
                class MockKRecord:
                    datetime = Datetime(20180921)

                return MockKRecord()

            def getStock(self):
                return Stock("SH600000")

        kdata = MockKData()

        buy_signals = []
        sell_signals = []

        sg._addBuySignal = lambda dt: buy_signals.append(dt)
        sg._addSellSignal = lambda dt: sell_signals.append(dt)

        sg._calculate(kdata)

        assert len(buy_signals) == 0
        assert len(sell_signals) == 1

    def test_calculate_no_signal_for_hold(self, tmp_path):
        """测试持有区间不生成信号"""
        date = pd.Timestamp("2018-09-21")
        index = pd.MultiIndex.from_arrays(
            [[date], ["SH600000"]], names=["datetime", "instrument"]
        )
        pred_df = pd.DataFrame(
            {"score": [0.01]}, index=index
        )  # 在[-0.02, 0.02]区间内

        pred_file = tmp_path / "hold_signal.pkl"
        pred_df.to_pickle(pred_file)

        sg = CustomSG_QlibFactor(
            pred_pkl_path=str(pred_file), buy_threshold=0.02, sell_threshold=-0.02
        )

        class MockKData:
            def __len__(self):
                return 1

            def __getitem__(self, idx):
                class MockKRecord:
                    datetime = Datetime(20180921)

                return MockKRecord()

            def getStock(self):
                return Stock("SH600000")

        kdata = MockKData()

        buy_signals = []
        sell_signals = []

        sg._addBuySignal = lambda dt: buy_signals.append(dt)
        sg._addSellSignal = lambda dt: sell_signals.append(dt)

        sg._calculate(kdata)

        assert len(buy_signals) == 0
        assert len(sell_signals) == 0

    def test_calculate_no_prediction_for_stock(self, tmp_path):
        """测试股票无预测数据时不生成信号"""
        date = pd.Timestamp("2018-09-21")
        index = pd.MultiIndex.from_arrays(
            [[date], ["SH600000"]], names=["datetime", "instrument"]
        )
        pred_df = pd.DataFrame({"score": [0.05]}, index=index)

        pred_file = tmp_path / "other_stock.pkl"
        pred_df.to_pickle(pred_file)

        sg = CustomSG_QlibFactor(pred_pkl_path=str(pred_file))

        # 查询不同的股票
        class MockKData:
            def __len__(self):
                return 1

            def __getitem__(self, idx):
                class MockKRecord:
                    datetime = Datetime(20180921)

                return MockKRecord()

            def getStock(self):
                return Stock("SZ000001")  # 不同的股票

        kdata = MockKData()

        buy_signals = []
        sell_signals = []

        sg._addBuySignal = lambda dt: buy_signals.append(dt)
        sg._addSellSignal = lambda dt: sell_signals.append(dt)

        sg._calculate(kdata)

        assert len(buy_signals) == 0
        assert len(sell_signals) == 0


class TestISignalProviderInterface:
    """测试ISignalProvider接口实现"""

    def test_generate_signals_from_predictions_basic(self):
        """测试从预测批次生成信号"""
        sg = CustomSG_QlibFactor(pred_pkl_path="dummy.pkl")

        # 创建预测批次
        batch = PredictionBatch(model_id="test_model")

        # 添加预测
        date1 = datetime(2018, 9, 21)
        batch.add_prediction(
            Prediction(
                stock_code=StockCode("sh600000"),
                timestamp=date1,
                predicted_value=0.05,  # 买入
                model_id="test_model",
            )
        )
        batch.add_prediction(
            Prediction(
                stock_code=StockCode("sz000001"),
                timestamp=date1,
                predicted_value=-0.05,  # 卖出
                model_id="test_model",
            )
        )
        batch.add_prediction(
            Prediction(
                stock_code=StockCode("sh600157"),
                timestamp=date1,
                predicted_value=0.01,  # 持有
                model_id="test_model",
            )
        )

        # 生成信号
        signal_batch = sg.generate_signals_from_predictions(
            batch, buy_threshold=0.02, sell_threshold=-0.02
        )

        assert signal_batch.size() == 3

        # 验证买入信号
        buy_signals = signal_batch.filter_by_type(SignalType.BUY)
        assert len(buy_signals) == 1
        assert buy_signals[0].stock_code == StockCode("sh600000")

        # 验证卖出信号
        sell_signals = signal_batch.filter_by_type(SignalType.SELL)
        assert len(sell_signals) == 1
        assert sell_signals[0].stock_code == StockCode("sz000001")

        # 验证持有信号
        hold_signals = signal_batch.filter_by_type(SignalType.HOLD)
        assert len(hold_signals) == 1
        assert hold_signals[0].stock_code == StockCode("sh600157")

    def test_generate_signals_with_top_k(self):
        """测试Top-K选股"""
        sg = CustomSG_QlibFactor(pred_pkl_path="dummy.pkl")

        batch = PredictionBatch(model_id="test_model")
        date1 = datetime(2018, 9, 21)

        # 添加3个预测,但只选Top-2
        batch.add_prediction(
            Prediction(
                stock_code=StockCode("sh600000"),
                timestamp=date1,
                predicted_value=0.08,
                model_id="test_model",
            )
        )
        batch.add_prediction(
            Prediction(
                stock_code=StockCode("sz000001"),
                timestamp=date1,
                predicted_value=0.05,
                model_id="test_model",
            )
        )
        batch.add_prediction(
            Prediction(
                stock_code=StockCode("sh600157"),
                timestamp=date1,
                predicted_value=0.03,  # 应该被过滤
                model_id="test_model",
            )
        )

        signal_batch = sg.generate_signals_from_predictions(
            batch, buy_threshold=0.02, top_k=2
        )

        # 只有Top-2应该生成买入信号
        buy_signals = signal_batch.filter_by_type(SignalType.BUY)
        assert len(buy_signals) == 2

        buy_stock_codes = {sig.stock_code for sig in buy_signals}
        assert StockCode("sh600000") in buy_stock_codes
        assert StockCode("sz000001") in buy_stock_codes
        assert StockCode("sh600157") not in buy_stock_codes

    def test_generate_signals_with_strength(self):
        """测试信号强度计算"""
        sg = CustomSG_QlibFactor(pred_pkl_path="dummy.pkl")

        batch = PredictionBatch(model_id="test_model")
        date1 = datetime(2018, 9, 21)

        # 强买入信号
        batch.add_prediction(
            Prediction(
                stock_code=StockCode("sh600000"),
                timestamp=date1,
                predicted_value=0.10,  # > 0.02 * 2
                model_id="test_model",
            )
        )

        # 中等买入信号
        batch.add_prediction(
            Prediction(
                stock_code=StockCode("sz000001"),
                timestamp=date1,
                predicted_value=0.035,  # > 0.02 * 1.5
                model_id="test_model",
            )
        )

        # 弱买入信号
        batch.add_prediction(
            Prediction(
                stock_code=StockCode("sh600157"),
                timestamp=date1,
                predicted_value=0.025,  # > 0.02
                model_id="test_model",
            )
        )

        signal_batch = sg.generate_signals_from_predictions(
            batch, buy_threshold=0.02
        )

        # 验证信号强度
        strong_signals = signal_batch.filter_by_strength(SignalStrength.STRONG)
        assert len(strong_signals) == 1
        assert strong_signals[0].stock_code == StockCode("sh600000")

        medium_signals = signal_batch.filter_by_strength(SignalStrength.MEDIUM)
        assert len(medium_signals) == 1
        assert medium_signals[0].stock_code == StockCode("sz000001")

        weak_signals = signal_batch.filter_by_strength(SignalStrength.WEAK)
        assert len(weak_signals) == 1
        assert weak_signals[0].stock_code == StockCode("sh600157")

    def test_get_signal_for_stock(self, tmp_path):
        """测试获取指定股票信号"""
        # 创建预测文件
        date = pd.Timestamp("2018-09-21")
        index = pd.MultiIndex.from_arrays(
            [[date], ["SH600000"]], names=["datetime", "instrument"]
        )
        pred_df = pd.DataFrame({"score": [0.05]}, index=index)

        pred_file = tmp_path / "signal_query.pkl"
        pred_df.to_pickle(pred_file)

        sg = CustomSG_QlibFactor(
            pred_pkl_path=str(pred_file), buy_threshold=0.02
        )

        # 查询信号
        signal = sg.get_signal_for_stock(
            StockCode("sh600000"), datetime(2018, 9, 21)
        )

        assert signal is not None
        assert signal.signal_type == SignalType.BUY
        assert signal.stock_code == StockCode("sh600000")

    def test_get_signal_for_stock_not_found(self, tmp_path):
        """测试查询不存在的股票信号"""
        date = pd.Timestamp("2018-09-21")
        index = pd.MultiIndex.from_arrays(
            [[date], ["SH600000"]], names=["datetime", "instrument"]
        )
        pred_df = pd.DataFrame({"score": [0.05]}, index=index)

        pred_file = tmp_path / "signal_query.pkl"
        pred_df.to_pickle(pred_file)

        sg = CustomSG_QlibFactor(pred_pkl_path=str(pred_file))

        # 查询不存在的股票
        signal = sg.get_signal_for_stock(
            StockCode("sz000001"), datetime(2018, 9, 21)
        )

        assert signal is None

    def test_get_top_k_stocks(self):
        """测试获取Top-K股票"""
        sg = CustomSG_QlibFactor(pred_pkl_path="dummy.pkl")

        batch = PredictionBatch(model_id="test_model")
        date1 = datetime(2018, 9, 21)

        # 添加预测(不同分数)
        batch.add_prediction(
            Prediction(
                stock_code=StockCode("sh600000"),
                timestamp=date1,
                predicted_value=0.05,
                model_id="test_model",
            )
        )
        batch.add_prediction(
            Prediction(
                stock_code=StockCode("sz000001"),
                timestamp=date1,
                predicted_value=0.08,
                model_id="test_model",
            )
        )
        batch.add_prediction(
            Prediction(
                stock_code=StockCode("sh600157"),
                timestamp=date1,
                predicted_value=0.03,
                model_id="test_model",
            )
        )

        # 获取Top-2
        top_k_stocks = sg.get_top_k_stocks(batch, k=2)

        assert len(top_k_stocks) == 2
        assert top_k_stocks[0] == StockCode("sz000001")  # 最高
        assert top_k_stocks[1] == StockCode("sh600000")  # 第二

    def test_get_top_k_stocks_with_duplicates(self):
        """测试Top-K去重(同一股票多个时间点)"""
        sg = CustomSG_QlibFactor(pred_pkl_path="dummy.pkl")

        batch = PredictionBatch(model_id="test_model")

        # 同一股票在不同时间点
        batch.add_prediction(
            Prediction(
                stock_code=StockCode("sh600000"),
                timestamp=datetime(2018, 9, 21),
                predicted_value=0.05,
                model_id="test_model",
            )
        )
        batch.add_prediction(
            Prediction(
                stock_code=StockCode("sh600000"),
                timestamp=datetime(2018, 9, 22),
                predicted_value=0.06,
                model_id="test_model",
            )
        )
        batch.add_prediction(
            Prediction(
                stock_code=StockCode("sz000001"),
                timestamp=datetime(2018, 9, 21),
                predicted_value=0.03,
                model_id="test_model",
            )
        )

        # 应该只返回2个唯一股票
        top_k_stocks = sg.get_top_k_stocks(batch, k=5)

        assert len(top_k_stocks) == 2
        assert StockCode("sh600000") in top_k_stocks
        assert StockCode("sz000001") in top_k_stocks


class TestResetAndClone:
    """测试复位和克隆功能"""

    def test_reset(self, tmp_path):
        """测试复位功能"""
        date = pd.Timestamp("2018-09-21")
        index = pd.MultiIndex.from_arrays(
            [[date], ["SH600000"]], names=["datetime", "instrument"]
        )
        pred_df = pd.DataFrame({"score": [0.05]}, index=index)

        pred_file = tmp_path / "reset_test.pkl"
        pred_df.to_pickle(pred_file)

        sg = CustomSG_QlibFactor(pred_pkl_path=str(pred_file))
        sg._load_predictions()

        # 验证数据已加载
        assert sg._pred_df is not None
        assert len(sg._stock_predictions) > 0

        # 复位
        sg._reset()

        # 验证数据已清空
        assert sg._pred_df is None
        assert len(sg._stock_predictions) == 0
        assert len(sg._top_k_stocks_by_date) == 0

    def test_clone(self, tmp_path):
        """测试克隆功能"""
        date = pd.Timestamp("2018-09-21")
        index = pd.MultiIndex.from_arrays(
            [[date], ["SH600000"]], names=["datetime", "instrument"]
        )
        pred_df = pd.DataFrame({"score": [0.05]}, index=index)

        pred_file = tmp_path / "clone_test.pkl"
        pred_df.to_pickle(pred_file)

        sg = CustomSG_QlibFactor(
            pred_pkl_path=str(pred_file), buy_threshold=0.03, top_k=5
        )
        sg._load_predictions()

        # 克隆
        cloned = sg._clone()

        # 验证参数相同
        assert cloned.getParam("pred_pkl_path") == sg.getParam("pred_pkl_path")
        assert cloned.getParam("buy_threshold") == sg.getParam("buy_threshold")
        assert cloned.getParam("top_k") == sg.getParam("top_k")

        # 验证数据已复制
        assert cloned._pred_df is sg._pred_df  # 共享同一DataFrame
        assert cloned._stock_predictions == sg._stock_predictions


class TestEdgeCases:
    """测试边缘情况"""

    def test_empty_predictions(self, tmp_path):
        """测试空预测文件"""
        # 创建空DataFrame
        index = pd.MultiIndex.from_arrays(
            [[], []], names=["datetime", "instrument"]
        )
        pred_df = pd.DataFrame({"score": []}, index=index)

        pred_file = tmp_path / "empty_pred.pkl"
        pred_df.to_pickle(pred_file)

        sg = CustomSG_QlibFactor(pred_pkl_path=str(pred_file))
        sg._load_predictions()

        assert sg._pred_df is not None
        assert len(sg._stock_predictions) == 0

    def test_single_stock_single_date(self, tmp_path):
        """测试单股票单日期"""
        date = pd.Timestamp("2018-09-21")
        index = pd.MultiIndex.from_arrays(
            [[date], ["SH600000"]], names=["datetime", "instrument"]
        )
        pred_df = pd.DataFrame({"score": [0.05]}, index=index)

        pred_file = tmp_path / "single_pred.pkl"
        pred_df.to_pickle(pred_file)

        sg = CustomSG_QlibFactor(pred_pkl_path=str(pred_file), top_k=1)
        sg._load_predictions()

        assert len(sg._stock_predictions) == 1
        assert "SH600000" in sg._stock_predictions

    def test_multiple_dates_same_stock(self, tmp_path):
        """测试多日期同一股票"""
        dates = pd.date_range("2018-09-21", periods=5)
        instruments = ["SH600000"]

        index = pd.MultiIndex.from_product(
            [dates, instruments], names=["datetime", "instrument"]
        )
        pred_df = pd.DataFrame(
            {"score": [0.01, 0.02, 0.03, 0.04, 0.05]}, index=index
        )

        pred_file = tmp_path / "multidate_single_stock.pkl"
        pred_df.to_pickle(pred_file)

        sg = CustomSG_QlibFactor(pred_pkl_path=str(pred_file))
        sg._load_predictions()

        assert len(sg._stock_predictions) == 1
        assert len(sg._stock_predictions["SH600000"]) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
