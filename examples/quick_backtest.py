#!/usr/bin/env python
"""
快速回测脚本

一键运行回测,无需修改代码
"""

import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hikyuu import *
from adapters.hikyuu.custom_sg_qlib_factor import CustomSG_QlibFactor


def quick_backtest(
    pred_file="./outputs/predictions/hs300_2025_pred.pkl",
    start_date="20250101",
    end_date="20251231",
    init_cash=1000000,
    buy_threshold=0.01,
    sell_threshold=-0.01,
    top_k=30,
    stock_pool="沪深300"
):
    """
    快速回测函数

    Args:
        pred_file: 预测文件路径
        start_date: 开始日期 (YYYYMMDD)
        end_date: 结束日期 (YYYYMMDD)
        init_cash: 初始资金
        buy_threshold: 买入阈值
        sell_threshold: 卖出阈值
        top_k: 每日交易的最大股票数
        stock_pool: 股票池名称
    """
    print("=" * 70)
    print("快速回测")
    print("=" * 70)

    # 初始化
    hikyuu_init("./config/hikyuu.ini")

    # 显示参数
    print(f"\n回测配置:")
    print(f"  预测文件: {pred_file}")
    print(f"  时间范围: {start_date} ~ {end_date}")
    print(f"  初始资金: {init_cash:,.0f}")
    print(f"  买入阈值: {buy_threshold}")
    print(f"  卖出阈值: {sell_threshold}")
    print(f"  Top-K: {top_k}")
    print(f"  股票池: {stock_pool}")

    # 创建信号指示器
    sg = CustomSG_QlibFactor(
        pred_pkl_path=pred_file,
        buy_threshold=buy_threshold,
        sell_threshold=sell_threshold,
        top_k=top_k,
    )

    # 配置交易系统
    mm = MM_FixedCount(n=0.05 * init_cash)
    st = ST_FixedPercent(p=0.20)
    pg = PG_FixedPercent(p=0.30)
    sp = SP_FixedPercent(p=0.001)

    # 获取股票池
    block = get_block("指数板块", stock_pool)
    stk_list = block.get_stock_list() if block else get_stock_type_list(11)

    print(f"\n股票数量: {len(stk_list)}")
    print("\n开始回测...")

    # 创建原型系统(Proto System)
    proto_sys = SYS_Simple(
        mm=mm,
        sg=sg,
        st=st,
        pg=pg,
        sp=sp,
    )

    # 创建选股器(使用固定的股票池)
    se = SE_Fixed(stk_list, proto_sys)

    # 创建投资组合
    pf = PF_Simple(
        tm=crtTM(Datetime(int(start_date)), init_cash, TC_FixedA2017()),
        se=se,
    )

    # 运行回测
    pf.run(Query(Datetime(int(start_date)), Datetime(int(end_date))))

    tm = pf.tm

    # 显示结果
    print("\n" + "=" * 70)
    print("回测结果")
    print("=" * 70)

    final_funds = tm.get_funds(Datetime.max())
    final_asset = final_funds.total_assets
    total_return = (final_asset - init_cash) / init_cash * 100

    print(f"\n初始资金: {init_cash:,.2f}")
    print(f"最终资金: {tm.current_cash:,.2f}")
    print(f"总资产: {final_asset:,.2f}")
    print(f"总收益率: {total_return:.2f}%")

    trade_list = tm.get_trade_list()
    print(f"\n交易次数: {len(trade_list)}")

    position_list = tm.get_position_list()
    print(f"持仓数量: {len(position_list)}")

    print("\n" + "=" * 70)

    return pf, sys, tm


if __name__ == "__main__":
    import os
    import argparse

    # 解析命令行参数
    parser = argparse.ArgumentParser(description="快速回测脚本")
    parser.add_argument("--pred-file", default="./outputs/predictions/hs300_2025_pred.pkl",
                       help="预测文件路径")
    parser.add_argument("--start", default="20250101", help="开始日期 (YYYYMMDD)")
    parser.add_argument("--end", default="20251231", help="结束日期 (YYYYMMDD)")
    parser.add_argument("--cash", type=float, default=1000000, help="初始资金")
    parser.add_argument("--buy-threshold", type=float, default=0.01, help="买入阈值")
    parser.add_argument("--sell-threshold", type=float, default=-0.01, help="卖出阈值")
    parser.add_argument("--top-k", type=int, default=30, help="每日最大交易股票数")
    parser.add_argument("--pool", default="沪深300", help="股票池名称")

    args = parser.parse_args()

    # 确保在项目根目录运行
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    try:
        pf, sys, tm = quick_backtest(
            pred_file=args.pred_file,
            start_date=args.start,
            end_date=args.end,
            init_cash=args.cash,
            buy_threshold=args.buy_threshold,
            sell_threshold=args.sell_threshold,
            top_k=args.top_k,
            stock_pool=args.pool,
        )
    except Exception as e:
        print(f"\n❌ 回测失败: {e}")
        import traceback
        traceback.print_exc()
