"""
QlibPortfolioAdapter 单元测试

测试 Qlib 组合适配器核心功能
遵循 TDD Red-Green-Refactor 流程
"""

from datetime import date
from pathlib import Path
from typing import List
import pandas as pd
import numpy as np
import pytest
import tempfile
import pickle

from domain.value_objects.date_range import DateRange
from domain.value_objects.stock_code import StockCode
from domain.value_objects.rebalance_period import RebalancePeriod
from adapters.qlib.portfolio_adapter import QlibPortfolioAdapter


class TestQlibPortfolioAdapter:
    """QlibPortfolioAdapter 测试类"""

    # =============================================================================
    # Fixtures
    # =============================================================================

    @pytest.fixture
    def sample_pred_df(self):
        """
        创建示例预测 DataFrame

        格式: MultiIndex(datetime, instrument) + score 列
        日期: 2023-01-03 ~ 2023-02-28 (连续两个月)
        股票: SH600000 ~ SH600009 (10只股票)
        """
        # 创建日期范围 (2个月的交易日)
        dates = pd.date_range(start='2023-01-03', end='2023-02-28', freq='B')  # B = business days

        # 创建股票列表
        instruments = [f'SH60000{i}' for i in range(10)]

        # 创建 MultiIndex
        index = pd.MultiIndex.from_product(
            [dates, instruments],
            names=['datetime', 'instrument']
        )

        # 创建随机预测分数 (模拟真实场景)
        np.random.seed(42)
        scores = np.random.randn(len(index))

        # 创建 DataFrame
        df = pd.DataFrame({'score': scores}, index=index)

        return df

    @pytest.fixture
    def sample_pred_pkl(self, sample_pred_df, tmp_path):
        """创建临时 pred.pkl 文件"""
        pkl_file = tmp_path / "pred.pkl"
        sample_pred_df.to_pickle(pkl_file)
        return str(pkl_file)

    @pytest.fixture
    def adapter(self, sample_pred_pkl):
        """创建 QlibPortfolioAdapter 实例 (WEEK 调仓)"""
        return QlibPortfolioAdapter(
            pred_pkl_path=sample_pred_pkl,
            top_k=5,
            rebalance_period="WEEK"
        )

    @pytest.fixture
    def sample_date_range(self):
        """示例日期范围 (2023年1月)"""
        return DateRange(
            start_date=date(2023, 1, 1),
            end_date=date(2023, 1, 31)
        )

    # =============================================================================
    # Test 1: 初始化验证
    # =============================================================================

    def test_init_with_valid_params(self, sample_pred_pkl):
        """
        测试: 使用有效参数初始化

        验证:
        - 正确设置属性
        - 成功加载预测数据
        - 预计算 Top-K 缓存
        """
        adapter = QlibPortfolioAdapter(
            pred_pkl_path=sample_pred_pkl,
            top_k=10,
            rebalance_period="MONTH"
        )

        assert adapter.pred_pkl_path == sample_pred_pkl
        assert adapter.top_k == 10
        assert adapter.rebalance_period == RebalancePeriod.MONTH
        assert adapter._pred_df is not None
        assert len(adapter._top_k_cache) > 0

    def test_init_with_nonexistent_file(self):
        """
        测试: 使用不存在的文件初始化

        验证:
        - 抛出 FileNotFoundError
        """
        with pytest.raises(FileNotFoundError, match="pred.pkl not found"):
            QlibPortfolioAdapter(
                pred_pkl_path="/nonexistent/pred.pkl",
                top_k=10,
                rebalance_period="WEEK"
            )

    def test_init_with_invalid_top_k(self, sample_pred_pkl):
        """
        测试: 使用无效 top_k 初始化

        验证:
        - 抛出 ValueError
        """
        # top_k = 0
        with pytest.raises(ValueError, match="top_k must be positive integer"):
            QlibPortfolioAdapter(
                pred_pkl_path=sample_pred_pkl,
                top_k=0,
                rebalance_period="WEEK"
            )

        # top_k = -1
        with pytest.raises(ValueError, match="top_k must be positive integer"):
            QlibPortfolioAdapter(
                pred_pkl_path=sample_pred_pkl,
                top_k=-1,
                rebalance_period="WEEK"
            )

        # top_k = 非整数
        with pytest.raises(ValueError, match="top_k must be positive integer"):
            QlibPortfolioAdapter(
                pred_pkl_path=sample_pred_pkl,
                top_k=3.5,
                rebalance_period="WEEK"
            )

    def test_init_with_invalid_rebalance_period(self, sample_pred_pkl):
        """
        测试: 使用无效调仓周期初始化

        验证:
        - 抛出 ValueError
        """
        with pytest.raises(ValueError, match="Invalid rebalance_period"):
            QlibPortfolioAdapter(
                pred_pkl_path=sample_pred_pkl,
                top_k=10,
                rebalance_period="INVALID"
            )

    # =============================================================================
    # Test 2: 加载预测结果
    # =============================================================================

    def test_load_predictions_with_invalid_format(self, tmp_path):
        """
        测试: 加载非 MultiIndex DataFrame

        验证:
        - 抛出 ValueError (必须是 MultiIndex)
        """
        # 创建非 MultiIndex DataFrame
        df = pd.DataFrame({
            'date': ['2023-01-03'],
            'instrument': ['SH600000'],
            'score': [0.5]
        })

        pkl_file = tmp_path / "invalid.pkl"
        df.to_pickle(pkl_file)

        with pytest.raises(ValueError, match="must have MultiIndex"):
            QlibPortfolioAdapter(
                pred_pkl_path=str(pkl_file),
                top_k=10,
                rebalance_period="WEEK"
            )

    def test_load_predictions_without_score_column(self, tmp_path):
        """
        测试: 加载缺少 'score' 列的 DataFrame

        验证:
        - 抛出 ValueError (必须有 score 列)
        """
        # 创建没有 score 列的 DataFrame
        dates = pd.date_range(start='2023-01-03', periods=5, freq='D')
        instruments = ['SH600000', 'SH600001']
        index = pd.MultiIndex.from_product(
            [dates, instruments],
            names=['datetime', 'instrument']
        )
        df = pd.DataFrame({'price': [100.0] * len(index)}, index=index)

        pkl_file = tmp_path / "no_score.pkl"
        df.to_pickle(pkl_file)

        with pytest.raises(ValueError, match="must contain 'score' column"):
            QlibPortfolioAdapter(
                pred_pkl_path=str(pkl_file),
                top_k=10,
                rebalance_period="WEEK"
            )

    def test_load_predictions_with_empty_dataframe(self, tmp_path):
        """
        测试: 加载空 DataFrame

        验证:
        - 抛出 ValueError (不能为空)
        """
        # 创建空 DataFrame
        index = pd.MultiIndex.from_tuples(
            [],
            names=['datetime', 'instrument']
        )
        df = pd.DataFrame({'score': []}, index=index)

        pkl_file = tmp_path / "empty.pkl"
        df.to_pickle(pkl_file)

        with pytest.raises(ValueError, match="contains no data"):
            QlibPortfolioAdapter(
                pred_pkl_path=str(pkl_file),
                top_k=10,
                rebalance_period="WEEK"
            )

    # =============================================================================
    # Test 3: 预计算 Top-K
    # =============================================================================

    def test_precompute_top_k_correctness(self, adapter, sample_pred_df):
        """
        测试: 预计算 Top-K 正确性

        验证:
        - 缓存包含所有日期
        - 每个日期的 Top-K 数量正确
        - Top-K 股票按分数降序排列
        """
        # 获取所有日期
        all_dates = sample_pred_df.index.get_level_values(0).unique()

        # 验证缓存包含所有日期
        assert len(adapter._top_k_cache) == len(all_dates)

        # 随机检查一个日期的 Top-K
        test_date = all_dates[0]
        top_k_stocks = adapter._top_k_cache[test_date]

        # 验证数量
        assert len(top_k_stocks) == adapter.top_k

        # 手动计算该日期的 Top-K,验证正确性
        date_predictions = sample_pred_df.loc[test_date]
        expected_top_k = date_predictions.nlargest(adapter.top_k, 'score')
        expected_stocks = expected_top_k.index.tolist()

        assert top_k_stocks == expected_stocks

    # =============================================================================
    # Test 4: 获取动态股票池
    # =============================================================================

    def test_get_dynamic_stock_pool_week_rebalance(self, adapter, sample_date_range):
        """
        测试: 获取动态股票池 (WEEK 调仓)

        验证:
        - 返回字典格式 {日期: [StockCode]}
        - 只包含每周第一个交易日
        - StockCode 对象格式正确
        """
        stock_pool = adapter.get_dynamic_stock_pool(sample_date_range)

        # 验证返回类型
        assert isinstance(stock_pool, dict)

        # 验证至少有一个调仓日
        assert len(stock_pool) > 0

        # 验证每个值是 StockCode 列表
        for rebalance_date, stock_codes in stock_pool.items():
            assert isinstance(stock_codes, list)
            assert len(stock_codes) == adapter.top_k

            for stock_code in stock_codes:
                assert isinstance(stock_code, StockCode)

    def test_get_dynamic_stock_pool_day_rebalance(self, sample_pred_pkl, sample_date_range):
        """
        测试: 获取动态股票池 (DAY 调仓)

        验证:
        - 每个交易日都是调仓日
        """
        adapter = QlibPortfolioAdapter(
            pred_pkl_path=sample_pred_pkl,
            top_k=5,
            rebalance_period="DAY"
        )

        stock_pool = adapter.get_dynamic_stock_pool(sample_date_range)

        # DAY 调仓应该有更多调仓日
        assert len(stock_pool) > 0

    def test_get_dynamic_stock_pool_month_rebalance(self, sample_pred_pkl, sample_date_range):
        """
        测试: 获取动态股票池 (MONTH 调仓)

        验证:
        - 每月第一个交易日是调仓日
        """
        adapter = QlibPortfolioAdapter(
            pred_pkl_path=sample_pred_pkl,
            top_k=5,
            rebalance_period="MONTH"
        )

        stock_pool = adapter.get_dynamic_stock_pool(sample_date_range)

        # MONTH 调仓应该只有1个调仓日 (1月)
        assert len(stock_pool) >= 1

    # =============================================================================
    # Test 5: 获取调仓日期
    # =============================================================================

    def test_get_rebalance_dates_day(self, sample_pred_pkl, sample_pred_df):
        """
        测试: 获取调仓日期 (DAY)

        验证:
        - 返回所有交易日
        """
        adapter = QlibPortfolioAdapter(
            pred_pkl_path=sample_pred_pkl,
            top_k=5,
            rebalance_period="DAY"
        )

        date_range = DateRange(date(2023, 1, 1), date(2023, 1, 31))
        rebalance_dates = adapter._get_rebalance_dates(date_range)

        # 获取1月的所有交易日
        all_dates = sample_pred_df.index.get_level_values(0).unique()
        jan_dates = all_dates[
            (all_dates >= pd.Timestamp('2023-01-01')) &
            (all_dates <= pd.Timestamp('2023-01-31'))
        ]

        # DAY 调仓应该返回所有交易日
        assert len(rebalance_dates) == len(jan_dates)

    def test_get_rebalance_dates_week(self, adapter, sample_pred_df):
        """
        测试: 获取调仓日期 (WEEK)

        验证:
        - 返回每周第一个交易日
        - 结果按时间升序排列
        """
        date_range = DateRange(date(2023, 1, 1), date(2023, 1, 31))
        rebalance_dates = adapter._get_rebalance_dates(date_range)

        # 验证至少有调仓日
        assert len(rebalance_dates) > 0

        # 验证按时间升序
        assert rebalance_dates == sorted(rebalance_dates)

        # WEEK 调仓应该少于 DAY 调仓
        # 1月大约有 4-5 周
        assert 1 <= len(rebalance_dates) <= 5

    def test_get_rebalance_dates_month(self, sample_pred_pkl, sample_pred_df):
        """
        测试: 获取调仓日期 (MONTH)

        验证:
        - 返回每月第一个交易日
        """
        adapter = QlibPortfolioAdapter(
            pred_pkl_path=sample_pred_pkl,
            top_k=5,
            rebalance_period="MONTH"
        )

        # 测试跨两个月
        date_range = DateRange(date(2023, 1, 1), date(2023, 2, 28))
        rebalance_dates = adapter._get_rebalance_dates(date_range)

        # 应该有 2 个调仓日 (1月和2月的第一个交易日)
        assert len(rebalance_dates) == 2

    def test_get_rebalance_dates_empty_range(self, adapter):
        """
        测试: 获取调仓日期 (日期范围外)

        验证:
        - 返回空列表
        """
        # 2030年 (远超预测数据范围)
        date_range = DateRange(date(2030, 1, 1), date(2030, 1, 31))
        rebalance_dates = adapter._get_rebalance_dates(date_range)

        assert len(rebalance_dates) == 0

    # =============================================================================
    # Test 6: 获取所有股票
    # =============================================================================

    def test_get_all_stocks(self, adapter):
        """
        测试: 获取所有股票列表

        验证:
        - 返回 StockCode 列表
        - 数量正确
        - 格式正确 (小写)
        """
        all_stocks = adapter.get_all_stocks()

        # 验证类型
        assert isinstance(all_stocks, list)
        assert len(all_stocks) > 0

        # 验证 StockCode 类型
        for stock_code in all_stocks:
            assert isinstance(stock_code, StockCode)

        # 验证数量 (应该有10只股票: SH600000 ~ SH600009)
        assert len(all_stocks) == 10

    def test_get_all_stocks_format(self, adapter):
        """
        测试: 获取所有股票格式

        验证:
        - StockCode 是小写格式
        """
        all_stocks = adapter.get_all_stocks()

        # 检查第一只股票
        first_stock = all_stocks[0]
        assert first_stock.value.startswith('sh')

    # =============================================================================
    # Test 7: 获取股票权重
    # =============================================================================

    def test_get_stock_weight_in_top_k(self, adapter, sample_pred_df):
        """
        测试: 获取 Top-K 股票的权重

        验证:
        - 返回等权重 (1.0 / top_k)
        """
        # 选择一个日期
        test_date = sample_pred_df.index.get_level_values(0).unique()[0]

        # 获取该日期的 Top-K 股票
        top_k_stocks = adapter._top_k_cache[test_date]
        test_stock = StockCode(top_k_stocks[0].lower())

        # 获取权重
        weight = adapter.get_stock_weight(test_date, test_stock)

        # 验证等权重
        expected_weight = 1.0 / adapter.top_k
        assert weight == pytest.approx(expected_weight)

    def test_get_stock_weight_not_in_top_k(self, adapter, sample_pred_df):
        """
        测试: 获取非 Top-K 股票的权重

        验证:
        - 返回 0.0
        """
        # 选择一个日期
        test_date = sample_pred_df.index.get_level_values(0).unique()[0]

        # 获取该日期的 Top-K 股票
        top_k_stocks = adapter._top_k_cache[test_date]

        # 找一个不在 Top-K 中的股票
        all_instruments = sample_pred_df.index.get_level_values(1).unique().tolist()
        non_top_k_stock = None
        for inst in all_instruments:
            if inst not in top_k_stocks:
                non_top_k_stock = StockCode(inst.lower())
                break

        if non_top_k_stock:
            # 获取权重
            weight = adapter.get_stock_weight(test_date, non_top_k_stock)

            # 验证权重为 0
            assert weight == 0.0

    def test_get_stock_weight_invalid_date(self, adapter):
        """
        测试: 获取不存在日期的股票权重

        验证:
        - 返回 0.0
        """
        invalid_date = pd.Timestamp('2030-01-01')
        test_stock = StockCode('sh600000')

        weight = adapter.get_stock_weight(invalid_date, test_stock)

        assert weight == 0.0

    # =============================================================================
    # Test 8: 边界情况
    # =============================================================================

    def test_top_k_larger_than_available_stocks(self, tmp_path):
        """
        测试: top_k 大于可用股票数量

        验证:
        - 返回所有可用股票
        """
        # 创建只有3只股票的预测数据
        dates = pd.date_range(start='2023-01-03', periods=5, freq='D')
        instruments = ['SH600000', 'SH600001', 'SH600002']
        index = pd.MultiIndex.from_product(
            [dates, instruments],
            names=['datetime', 'instrument']
        )
        df = pd.DataFrame({'score': np.random.randn(len(index))}, index=index)

        pkl_file = tmp_path / "small.pkl"
        df.to_pickle(pkl_file)

        # 设置 top_k = 10 (大于3)
        adapter = QlibPortfolioAdapter(
            pred_pkl_path=str(pkl_file),
            top_k=10,
            rebalance_period="DAY"
        )

        # 获取第一天的 Top-K
        first_date = dates[0]
        top_k_stocks = adapter._top_k_cache[first_date]

        # 应该只返回3只股票 (全部)
        assert len(top_k_stocks) == 3

    def test_single_day_data(self, tmp_path):
        """
        测试: 只有一天数据

        验证:
        - 正常工作
        """
        # 创建单日数据
        dates = pd.date_range(start='2023-01-03', periods=1, freq='D')
        instruments = [f'SH60000{i}' for i in range(10)]
        index = pd.MultiIndex.from_product(
            [dates, instruments],
            names=['datetime', 'instrument']
        )
        df = pd.DataFrame({'score': np.random.randn(len(index))}, index=index)

        pkl_file = tmp_path / "single_day.pkl"
        df.to_pickle(pkl_file)

        adapter = QlibPortfolioAdapter(
            pred_pkl_path=str(pkl_file),
            top_k=5,
            rebalance_period="DAY"
        )

        # 验证缓存有1天数据
        assert len(adapter._top_k_cache) == 1

    def test_performance_with_large_dataset(self, tmp_path):
        """
        测试: 大数据集性能 (可选)

        验证:
        - 预计算在合理时间内完成
        """
        # 创建大数据集: 1年 × 1000只股票
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='B')
        instruments = [f'SH{i:06d}' for i in range(1000)]
        index = pd.MultiIndex.from_product(
            [dates, instruments],
            names=['datetime', 'instrument']
        )

        # 使用随机种子保证可重复性
        np.random.seed(42)
        df = pd.DataFrame({'score': np.random.randn(len(index))}, index=index)

        pkl_file = tmp_path / "large.pkl"
        df.to_pickle(pkl_file)

        # 初始化应该快速完成 (包括预计算)
        import time
        start_time = time.time()

        adapter = QlibPortfolioAdapter(
            pred_pkl_path=str(pkl_file),
            top_k=50,
            rebalance_period="WEEK"
        )

        end_time = time.time()
        elapsed_time = end_time - start_time

        # 预计算应该在10秒内完成 (根据机器性能调整)
        assert elapsed_time < 10.0

        # 验证缓存大小
        assert len(adapter._top_k_cache) == len(dates)
