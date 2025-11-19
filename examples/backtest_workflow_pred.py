#!/usr/bin/env python
"""
使用工作流生成的预测结果进行回测

这个脚本演示如何使用 hikyuu_train_backtest_workflow.py 生成的
workflow_pred.pkl 文件进行完整的 Hikyuu 回测
"""

import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hikyuu import *
from adapters.hikyuu.custom_sg_qlib_factor import CustomSG_QlibFactor


def run_workflow_backtest():
    """
    使用工作流预测结果运行回测
    """
    print("=" * 70)
    print("使用工作流预测结果进行 Hikyuu 回测")
    print("=" * 70)

    # 1. 初始化 Hikyuu
    print("\n🔧 初始化 Hikyuu 系统...")
    hikyuu_init("./config/hikyuu.ini")
    print("✅ Hikyuu 初始化完成")

    # 2. 设置回测参数
    print("\n⚙️  设置回测参数...")

    # 使用工作流生成的预测文件
    pred_pkl_path = "./outputs/predictions/workflow_pred.pkl"

    # 读取预测文件获取预测日期
    import pickle
    import pandas as pd
    pred_df = pd.read_pickle(pred_pkl_path)
    pred_dates = pred_df.index.get_level_values('timestamp').unique()
    if len(pred_dates) > 0:
        pred_start_date = pred_dates[0]
        print(f"  预测日期: {pred_start_date}")
    else:
        pred_start_date = pd.Timestamp('2024-11-19')

    # 回测时间范围（根据预测日期调整）
    start_date = Datetime(pred_start_date.year, pred_start_date.month, pred_start_date.day)
    end_date = Datetime(pred_start_date.year, 12, 31)  # 当年年底

    # 初始资金
    init_cash = 1000000  # 100万

    # 信号阈值（根据预测值调整）
    buy_threshold = 0.0   # 所有预测值 > 0 的都买入
    sell_threshold = -0.1  # 预测值 < -0.1 的卖出
    top_k = 5  # 只买预测最好的5只股票（工作流只有5只股票）

    print(f"  📁 预测文件: {pred_pkl_path}")
    print(f"  📅 回测时间: {start_date} ~ {end_date}")
    print(f"  💰 初始资金: ¥{init_cash:,.0f}")
    print(f"  📈 买入阈值: {buy_threshold}")
    print(f"  📉 卖出阈值: {sell_threshold}")
    print(f"  🎯 Top-K: {top_k}")

    # 检查预测文件是否存在
    if not Path(pred_pkl_path).exists():
        print(f"\n❌ 错误: 预测文件不存在: {pred_pkl_path}")
        print("请先运行: ./run_backtest.sh workflow")
        return

    # 3. 创建信号指示器
    print("\n🎯 创建 Qlib 因子信号指示器...")
    try:
        sg = CustomSG_QlibFactor(
            pred_pkl_path=pred_pkl_path,
            buy_threshold=buy_threshold,
            sell_threshold=sell_threshold,
            top_k=top_k,
            name="WorkflowQlibFactor"
        )
        print("✅ 信号指示器创建成功")
    except Exception as e:
        print(f"❌ 创建信号指示器失败: {e}")
        print("\n💡 提示: 可能需要调整 pred.pkl 的格式")
        print("   CustomSG_QlibFactor 期望的格式:")
        print("   - MultiIndex DataFrame (datetime, instrument)")
        print("   - score 列包含预测值")
        return

    # 4. 创建交易系统组件
    print("\n🔧 配置交易系统...")

    # 资金管理 - 等权重分配
    mm = MM_FixedCount(n=init_cash * 0.95 / top_k)  # 每只股票分配约等权重

    # 止损策略 - 15% 止损
    st = ST_FixedPercent(p=0.15)

    # 盈利目标策略 - 不设盈利目标（让信号决定）
    pg = PG_NoGoal()

    # 滑点 - 0.05%（比较保守的滑点估计）
    sp = SP_FixedPercent(p=0.0005)

    print("  💼 资金管理: 等权重分配")
    print("  🛡️  止损策略: 15% 固定止损")
    print("  🎪 滑点设置: 0.05%")

    # 5. 定义股票池（工作流使用的5只股票）
    print("\n📊 定义股票池...")

    sm = StockManager.instance()
    stock_codes = ['sh600000', 'sh600016', 'sh600036', 'sh600519', 'sh600887']

    stk_list = []
    for code in stock_codes:
        stock = sm.get_stock(code.upper())
        if stock and not stock.is_null():
            stk_list.append(stock)

    print(f"  ✅ 股票池大小: {len(stk_list)} 只股票")
    for stock in stk_list:
        print(f"     - {stock.market_code}: {stock.name}")

    # 6. 创建交易账户
    print("\n💳 创建交易账户...")

    my_tm = crtTM(
        date=start_date,
        init_cash=init_cash,
        cost_func=TC_FixedA(commission=0.0003, lowest_commission=5),
        name="WorkflowBacktest"
    )

    print(f"  账户名称: {my_tm.name}")
    print(f"  初始资金: ¥{init_cash:,.0f}")
    print(f"  手续费率: 0.03%")

    # 7. 创建交易系统并运行回测
    print("\n" + "=" * 70)
    print("🚀 开始回测...")
    print("=" * 70)

    try:
        # 创建原型系统
        proto_sys = SYS_Simple(
            mm=mm,
            sg=sg,
            st=st,
            sp=sp,
            pg=pg,
        )

        # 创建选股器
        selector = SE_Fixed(stk_list, proto_sys)

        # 创建投资组合
        pf = PF_Simple(
            tm=my_tm,
            se=selector,
        )
        pf.name = "WorkflowBacktest"

        # 执行回测
        pf.run(Query(start_date, end_date))

        # 8. 显示回测结果
        print("\n" + "=" * 70)
        print("📊 回测结果")
        print("=" * 70)

        # 获取最终资产
        final_cash = my_tm.cash
        final_market_value = my_tm.get_market_value(end_date)
        final_total = final_cash + final_market_value

        # 计算收益
        total_return = (final_total - init_cash) / init_cash

        print(f"\n💰 资金情况:")
        print(f"  初始资金: ¥{init_cash:,.2f}")
        print(f"  最终现金: ¥{final_cash:,.2f}")
        print(f"  持仓市值: ¥{final_market_value:,.2f}")
        print(f"  总资产:   ¥{final_total:,.2f}")
        print(f"\n📈 收益指标:")
        print(f"  总收益率: {total_return:.2%}")

        # 获取交易记录
        trade_list = my_tm.get_trade_list()
        print(f"\n📋 交易记录:")
        print(f"  总交易次数: {len(trade_list)}")

        if trade_list:
            print(f"\n  最近10笔交易:")
            for i, trade in enumerate(trade_list[-10:], 1):
                direction = "买入" if trade.business == BUSINESS.BUY else "卖出"
                print(f"    {i}. {trade.datetime} {direction} {trade.stock.market_code} "
                      f"{trade.number}股 @ ¥{trade.real_price:.2f}")

        # 获取持仓
        positions = my_tm.get_position_list()
        if positions:
            print(f"\n💼 当前持仓 ({len(positions)}只):")
            for pos in positions:
                print(f"    {pos.stock.market_code}: {pos.number}股 "
                      f"成本¥{pos.buy_money/pos.number if pos.number > 0 else 0:.2f}")

        print("\n" + "=" * 70)
        print("✅ 回测完成!")
        print("=" * 70)

        # 9. 保存结果（可选）
        print("\n💾 保存回测结果...")
        output_dir = Path("./outputs/backtest_results")
        output_dir.mkdir(parents=True, exist_ok=True)

        # 可以在这里添加结果保存逻辑
        print(f"  结果目录: {output_dir}")

    except Exception as e:
        print(f"\n❌ 回测执行失败: {e}")
        import traceback
        traceback.print_exc()

        print("\n💡 可能的问题:")
        print("  1. pred.pkl 格式不兼容 CustomSG_QlibFactor")
        print("  2. 预测日期与回测日期不匹配")
        print("  3. 股票代码在 Hikyuu 数据库中不存在")


if __name__ == "__main__":
    run_workflow_backtest()
