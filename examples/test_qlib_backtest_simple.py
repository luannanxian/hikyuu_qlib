#!/usr/bin/env python
"""
Qlib 回测引擎 - 简化测试脚本

不依赖预测文件，使用模拟数据测试回测引擎功能
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime, date
from decimal import Decimal

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from adapters.qlib.qlib_backtest_engine_adapter import QlibBacktestEngineAdapter
from domain.entities.trading_signal import SignalBatch, TradingSignal, SignalType
from domain.value_objects.stock_code import StockCode
from domain.value_objects.configuration import BacktestConfig
from domain.value_objects.date_range import DateRange


def create_mock_signals() -> SignalBatch:
    """创建模拟交易信号用于测试"""

    batch = SignalBatch(
        strategy_name="测试策略",
        batch_date=datetime.now()
    )

    # 创建一些模拟信号
    stocks = ["sh600000", "sh600016", "sh600519", "sz000001", "sz000002"]
    dates = [
        date(2024, 1, 5),
        date(2024, 1, 10),
        date(2024, 1, 15),
        date(2024, 2, 1),
        date(2024, 2, 15),
    ]

    for signal_date in dates:
        for stock in stocks:
            signal = TradingSignal(
                stock_code=StockCode(stock),
                signal_date=datetime.combine(signal_date, datetime.min.time()),
                signal_type=SignalType.BUY,
                confidence=0.75 + (hash(stock + str(signal_date)) % 25) / 100,  # 0.75-1.0
            )
            batch.add_signal(signal)

    print(f"创建模拟信号: {batch.size()} 条")
    print(f"信号类型统计: {batch.count_by_type()}")

    return batch


async def main():
    """主函数"""
    print("=" * 70)
    print("Qlib 回测引擎 - 简化测试")
    print("=" * 70)

    # 1. 创建模拟信号
    print("\n创建模拟信号...")
    signals = create_mock_signals()

    # 2. 配置回测
    config = BacktestConfig(
        initial_capital=Decimal("1000000"),
        commission_rate=Decimal("0.0003"),
    )

    date_range = DateRange(
        start_date=date(2024, 1, 1),
        end_date=date(2024, 3, 31),
    )

    print(f"\n回测配置:")
    print(f"  初始资金: {config.initial_capital:,.0f}")
    print(f"  手续费率: {config.commission_rate}")
    print(f"  回测时间: {date_range.start_date} ~ {date_range.end_date}")

    # 3. 创建 Qlib 回测引擎
    print("\n初始化 Qlib 回测引擎...")
    try:
        engine = QlibBacktestEngineAdapter(
            benchmark="SH000300",
            freq="day",
        )

        # 4. 运行回测
        print("\n开始回测...")
        import time
        start_time = time.time()

        result = await engine.run_backtest(
            signals=signals,
            config=config,
            date_range=date_range,
        )

        elapsed_time = time.time() - start_time

        # 5. 显示结果
        print("\n" + "=" * 70)
        print("回测结果")
        print("=" * 70)
        print(f"策略名称: {result.strategy_name}")
        print(f"回测时间: {result.start_date.date()} ~ {result.end_date.date()}")
        print(f"初始资金: {result.initial_capital:,.0f}")
        print(f"最终资金: {result.final_capital:,.0f}")
        print(f"总收益率: {result.total_return:.2%}")
        print(f"年化收益率: {result.annualized_return:.2%}")
        print(f"最大回撤: {result.max_drawdown:.2%}")
        print(f"夏普比率: {result.sharpe_ratio:.2f}")
        print(f"交易次数: {result.total_trades}")
        print(f"\n回测耗时: {elapsed_time:.2f} 秒")

        # 6. 显示前5笔交易
        if result.trades:
            print("\n交易明细 (前5笔):")
            print("-" * 70)
            for i, trade in enumerate(result.trades[:5], 1):
                print(f"{i}. {trade.stock_code.value} {trade.direction} "
                      f"{trade.quantity}股 @ {trade.price:.2f} "
                      f"({trade.trade_date.date()})")

        print("\n" + "=" * 70)
        print("✅ 测试成功!")
        print("=" * 70)

        return 0

    except ImportError as e:
        print(f"\n❌ 错误: Qlib 未正确安装")
        print(f"   {e}")
        print("\n请确保:")
        print("  1. pip install pyqlib")
        print("  2. conda activate qlib_hikyuu")
        return 1

    except Exception as e:
        print(f"\n❌ 回测失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
