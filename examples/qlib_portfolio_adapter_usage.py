"""
QlibPortfolioAdapter Usage Examples

示例代码展示如何使用 QlibPortfolioAdapter
"""

from datetime import date

import pandas as pd

# Import adapter
from adapters.qlib.portfolio_adapter import QlibPortfolioAdapter

# Import domain objects
from domain.value_objects.date_range import DateRange
from domain.value_objects.stock_code import StockCode


def example_basic_usage():
    """
    示例 1: 基本用法

    加载 Qlib 预测结果,获取动态股票池
    """
    # 1. 初始化适配器
    adapter = QlibPortfolioAdapter(
        pred_pkl_path="path/to/pred.pkl",
        top_k=10,                        # 选择 Top-10 股票
        rebalance_period="WEEK",          # 每周调仓
    )

    # 2. 定义回测日期范围
    date_range = DateRange(
        start_date=date(2023, 1, 1),
        end_date=date(2023, 12, 31),
    )

    # 3. 获取动态股票池
    stock_pool = adapter.get_dynamic_stock_pool(date_range)

    # 输出格式: {调仓日期: [Top-K StockCode 列表]}
    for rebalance_date, stock_codes in stock_pool.items():
        print(f"{rebalance_date}: {[s.value for s in stock_codes]}")


def example_different_rebalance_periods():
    """
    示例 2: 不同调仓周期

    展示 DAY, WEEK, MONTH 三种调仓周期
    """
    pred_pkl_path = "path/to/pred.pkl"
    date_range = DateRange(date(2023, 1, 1), date(2023, 1, 31))

    # 每日调仓 (最频繁)
    adapter_day = QlibPortfolioAdapter(
        pred_pkl_path=pred_pkl_path,
        top_k=10,
        rebalance_period="DAY",
    )
    stock_pool_day = adapter_day.get_dynamic_stock_pool(date_range)
    print(f"DAY rebalance: {len(stock_pool_day)} 调仓日")

    # 每周调仓 (中等频率)
    adapter_week = QlibPortfolioAdapter(
        pred_pkl_path=pred_pkl_path,
        top_k=10,
        rebalance_period="WEEK",
    )
    stock_pool_week = adapter_week.get_dynamic_stock_pool(date_range)
    print(f"WEEK rebalance: {len(stock_pool_week)} 调仓日")

    # 每月调仓 (最低频)
    adapter_month = QlibPortfolioAdapter(
        pred_pkl_path=pred_pkl_path,
        top_k=10,
        rebalance_period="MONTH",
    )
    stock_pool_month = adapter_month.get_dynamic_stock_pool(date_range)
    print(f"MONTH rebalance: {len(stock_pool_month)} 调仓日")


def example_stock_weight():
    """
    示例 3: 获取股票权重

    计算某只股票在某日期的权重
    """
    adapter = QlibPortfolioAdapter(
        pred_pkl_path="path/to/pred.pkl",
        top_k=10,
        rebalance_period="WEEK",
    )

    # 获取某个日期的股票权重
    test_date = pd.Timestamp('2023-01-03')
    test_stock = StockCode('sh600000')

    weight = adapter.get_stock_weight(test_date, test_stock)

    if weight > 0:
        print(f"{test_stock.value} 在 {test_date} 的权重: {weight:.2%}")
        print(f"(等权重: 1/{adapter.top_k} = {1/adapter.top_k:.2%})")
    else:
        print(f"{test_stock.value} 不在 {test_date} 的 Top-{adapter.top_k} 中")


def example_get_all_stocks():
    """
    示例 4: 获取所有股票列表

    获取预测数据中出现过的所有股票
    """
    adapter = QlibPortfolioAdapter(
        pred_pkl_path="path/to/pred.pkl",
        top_k=10,
        rebalance_period="WEEK",
    )

    # 获取所有股票
    all_stocks = adapter.get_all_stocks()

    print(f"预测数据包含 {len(all_stocks)} 只股票")
    print(f"前10只: {[s.value for s in all_stocks[:10]]}")


def example_integration_with_hikyuu():
    """
    示例 5: 与 Hikyuu 回测集成

    完整流程: Qlib 预测 → 动态股票池 → Hikyuu 回测
    """
    # 1. 初始化 Qlib 适配器
    adapter = QlibPortfolioAdapter(
        pred_pkl_path="path/to/pred.pkl",
        top_k=30,
        rebalance_period="WEEK",
    )

    # 2. 获取动态股票池
    date_range = DateRange(date(2023, 1, 1), date(2023, 12, 31))
    stock_pool = adapter.get_dynamic_stock_pool(date_range)

    # 3. 转换为 Hikyuu 格式 (示意)
    # 注意: 实际集成需要使用 HikyuuBacktestAdapter
    for rebalance_date, stock_codes in stock_pool.items():
        # 获取每只股票的权重
        weights = {}
        for stock_code in stock_codes:
            weight = adapter.get_stock_weight(rebalance_date, stock_code)
            weights[stock_code.value] = weight

        print(f"\n{rebalance_date} 调仓:")
        print(f"  持仓: {len(stock_codes)} 只股票")
        print(f"  权重: {weights}")

        # TODO: 传递给 Hikyuu 回测引擎
        # hikyuu_portfolio.rebalance(rebalance_date, weights)


def example_performance_optimization():
    """
    示例 6: 性能优化 (预计算)

    展示预计算 Top-K 的性能优势
    """
    import time

    # 初始化时会自动预计算所有日期的 Top-K
    start_time = time.time()

    adapter = QlibPortfolioAdapter(
        pred_pkl_path="path/to/pred.pkl",
        top_k=50,
        rebalance_period="DAY",
    )

    init_time = time.time() - start_time
    print(f"初始化 (包括预计算): {init_time:.2f} 秒")

    # 后续查询非常快 (直接从缓存读取)
    date_range = DateRange(date(2023, 1, 1), date(2023, 12, 31))

    start_time = time.time()
    stock_pool = adapter.get_dynamic_stock_pool(date_range)
    query_time = time.time() - start_time

    print(f"查询动态股票池: {query_time:.4f} 秒")
    print(f"查询 {len(stock_pool)} 个调仓日的数据")


if __name__ == "__main__":
    # 运行示例
    print("=" * 60)
    print("QlibPortfolioAdapter 使用示例")
    print("=" * 60)

    print("\n示例 1: 基本用法")
    # example_basic_usage()  # 需要真实的 pred.pkl 文件

    print("\n示例 2: 不同调仓周期")
    # example_different_rebalance_periods()

    print("\n示例 3: 获取股票权重")
    # example_stock_weight()

    print("\n示例 4: 获取所有股票列表")
    # example_get_all_stocks()

    print("\n示例 5: 与 Hikyuu 回测集成")
    # example_integration_with_hikyuu()

    print("\n示例 6: 性能优化")
    # example_performance_optimization()

    print("\n" + "=" * 60)
    print("提示: 需要提供真实的 pred.pkl 文件才能运行示例")
    print("=" * 60)
