#!/usr/bin/env python
"""
Qlib 生产回测脚本

功能：
1. 加载模型预测结果
2. 使用 Qlib 回测引擎进行回测
3. 生成完整的回测报告
"""

import sys
import argparse
import pickle
from pathlib import Path
from datetime import datetime

# 自动配置 PYTHONPATH
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

print("=" * 70)
print("Qlib 生产回测")
print("=" * 70)
print(f"项目路径: {PROJECT_ROOT}")
print()


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="Qlib 生产回测")

    parser.add_argument(
        "--predictions",
        type=str,
        required=True,
        help="预测结果文件路径 (.pkl)"
    )

    parser.add_argument(
        "--start-date",
        type=str,
        default="2024-01-01",
        help="回测开始日期 (默认: 2024-01-01)"
    )

    parser.add_argument(
        "--end-date",
        type=str,
        default="2024-12-31",
        help="回测结束日期 (默认: 2024-12-31)"
    )

    parser.add_argument(
        "--initial-capital",
        type=float,
        default=1000000.0,
        help="初始资金 (默认: 1000000)"
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=30,
        help="每天持仓股票数 (默认: 30)"
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="backtest_results",
        help="回测结果保存目录 (默认: backtest_results)"
    )

    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()

    print(f"📊 预测文件: {args.predictions}")
    print(f"📅 回测日期: {args.start_date} ~ {args.end_date}")
    print(f"💰 初始资金: ¥{args.initial_capital:,.2f}")
    print(f"📈 持仓数量: {args.top_k} 只股票")
    print(f"💾 输出目录: {args.output_dir}")
    print()

    try:
        import qlib
        from qlib.constant import REG_CN
        import pandas as pd
        import numpy as np

        # 初始化 Qlib
        print("🔧 初始化 Qlib...")
        qlib.init(provider_uri="~/.qlib/qlib_data/cn_data", region=REG_CN)
        print("✅ Qlib 初始化成功")
        print()

        # 加载预测结果
        print(f"📦 加载预测结果: {args.predictions}")
        pred_path = Path(args.predictions)

        if not pred_path.exists():
            print(f"❌ 错误: 预测文件不存在: {args.predictions}")
            sys.exit(1)

        with open(pred_path, "rb") as f:
            predictions = pickle.load(f)

        print(f"✅ 加载完成: {len(predictions)} 条预测")
        print()

        # 配置回测策略
        print("⚙️  配置回测策略...")

        from qlib.contrib.strategy.signal_strategy import TopkDropoutStrategy
        from qlib.contrib.evaluate import backtest

        strategy_config = {
            "topk": args.top_k,
            "n_drop": 5,  # 每天最多卖出 5 只
        }

        # 配置回测参数
        backtest_config = {
            "start_time": args.start_date,
            "end_time": args.end_date,
            "account": args.initial_capital,
            "exchange_kwargs": {
                "freq": "day",
                "limit_threshold": 0.095,  # 涨跌停限制
                "deal_price": "close",      # 成交价格
                "open_cost": 0.0005,        # 开仓手续费
                "close_cost": 0.0015,       # 平仓手续费
                "min_cost": 5,              # 最小手续费
            },
        }

        print("✅ 策略配置完成")
        print()

        # 运行回测
        print("🚀 开始回测...")
        print("⏳ 这可能需要几分钟时间...")
        print()

        # 使用 TopkDropoutStrategy 策略
        portfolio_metrics = backtest(
            predictions,
            strategy=TopkDropoutStrategy(**strategy_config),
            **backtest_config
        )

        print("✅ 回测完成!")
        print()

        # 提取回测结果
        if isinstance(portfolio_metrics, tuple):
            portfolio_metrics = portfolio_metrics[0]

        # 显示回测结果
        print("=" * 70)
        print("📊 回测结果")
        print("=" * 70)
        print()

        if hasattr(portfolio_metrics, 'get'):
            # 提取关键指标
            returns = portfolio_metrics.get('return', None)

            if returns is not None and len(returns) > 0:
                total_return = (returns + 1).prod() - 1
                annualized_return = (1 + total_return) ** (252 / len(returns)) - 1
                sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
                max_drawdown = (returns.cumsum().cummax() - returns.cumsum()).max()

                print(f"📈 总收益率: {total_return*100:.2f}%")
                print(f"📊 年化收益率: {annualized_return*100:.2f}%")
                print(f"⚡ 夏普比率: {sharpe_ratio:.3f}")
                print(f"📉 最大回撤: {max_drawdown*100:.2f}%")
                print()

                # 按年统计
                returns_df = pd.DataFrame({'return': returns})
                returns_df['year'] = returns_df.index.year

                print("📅 分年收益:")
                yearly_returns = returns_df.groupby('year')['return'].apply(
                    lambda x: (x + 1).prod() - 1
                )

                for year, ret in yearly_returns.items():
                    print(f"  {year}: {ret*100:>8.2f}%")
                print()

        # 保存结果
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = output_dir / f"backtest_result_{timestamp}.pkl"

        with open(result_file, "wb") as f:
            pickle.dump(portfolio_metrics, f)

        print(f"💾 结果已保存: {result_file}")
        print()

        print("=" * 70)
        print("✅ 回测完成!")
        print("=" * 70)

    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print()
        print("请确保已安装必要依赖:")
        print("  pip install qlib")
        sys.exit(1)

    except Exception as e:
        print(f"❌ 回测失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
