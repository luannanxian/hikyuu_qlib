"""
Hikyuu 回测示例

演示如何使用 CustomSG_QlibFactor 信号指示器进行回测
"""

import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hikyuu import *
from adapters.hikyuu.custom_sg_qlib_factor import CustomSG_QlibFactor


def run_backtest_example():
    """
    运行回测示例

    使用已生成的预测文件进行回测
    """
    # 1. 初始化 Hikyuu (确保在项目根目录运行)
    print("=" * 70)
    print("初始化 Hikyuu 系统...")
    print("=" * 70)

    hikyuu_init("./config/hikyuu.ini")

    # 2. 设置回测参数
    print("\n设置回测参数...")

    # 预测文件路径
    pred_pkl_path = "./outputs/predictions/hs300_2025_pred.pkl"

    # 回测时间范围 (2025年)
    start_date = Datetime(20250101)
    end_date = Datetime(20251231)

    # 初始资金
    init_cash = 1000000  # 100万

    # 信号阈值
    buy_threshold = 0.01   # 预测收益 > 1% 买入
    sell_threshold = -0.01  # 预测收益 < -1% 卖出
    top_k = 30  # 每日只交易预测最好的30只股票

    print(f"  预测文件: {pred_pkl_path}")
    print(f"  回测时间: {start_date} ~ {end_date}")
    print(f"  初始资金: {init_cash:,.0f}")
    print(f"  买入阈值: {buy_threshold}")
    print(f"  卖出阈值: {sell_threshold}")
    print(f"  Top-K: {top_k}")

    # 3. 创建信号指示器
    print("\n创建 Qlib 因子信号指示器...")
    sg = CustomSG_QlibFactor(
        pred_pkl_path=pred_pkl_path,
        buy_threshold=buy_threshold,
        sell_threshold=sell_threshold,
        top_k=top_k,
        name="QlibFactor"
    )

    # 4. 创建交易系统
    print("\n配置交易系统...")

    # 资金管理 - 固定每只股票投入总资金的 5%
    mm = MM_FixedCount(n=0.05 * init_cash)

    # 止损策略 - 20% 止损
    st = ST_FixedPercent(p=0.20)

    # 盈利目标策略 - 不设盈利目标
    pg = PG_NoGoal()

    # 交易对象选择器 - 沪深300成分股
    se = SE_Fixed()

    # 滑点 - 0.1%
    sp = SP_FixedPercent(p=0.001)

    # 5. 创建投资组合
    print("\n创建投资组合...")

    # 获取沪深300股票列表
    block = get_block("指数板块", "沪深300")
    if not block:
        print("⚠️  警告: 无法加载沪深300板块,使用所有A股")
        stk_list = get_stock_type_list(11)  # 沪深A股
    else:
        stk_list = block.get_stock_list()

    print(f"  股票池大小: {len(stk_list)}")

    # 6. 构建系统并运行回测
    print("\n" + "=" * 70)
    print("开始回测...")
    print("=" * 70 + "\n")

    # 创建原型系统(Proto System)
    proto_sys = SYS_Simple(
        mm=mm,
        sg=sg,
        st=st,
        sp=sp,
        pg=pg,
        se=se,
    )

    # 创建选股器
    selector = SE_Fixed(stk_list, proto_sys)

    # 创建 Portfolio
    pf = PF_Simple(
        tm=crtTM(start_date, init_cash, TC_FixedA2017()),
        se=selector,
    )
    pf.name = "HS300_Qlib_Strategy"

    # 运行回测
    pf.run(Query(start_date, end_date))

    # 获取交易管理器
    tm = pf.tm

    # 7. 显示回测结果
    print("\n" + "=" * 70)
    print("回测结果")
    print("=" * 70)

    print(f"\n📊 资金情况:")
    print(f"  初始资金: {init_cash:,.2f}")
    print(f"  最终资金: {tm.current_cash:,.2f}")

    # 获取最终资产
    final_funds = tm.get_funds(Datetime.max())
    final_asset = final_funds.total_assets
    print(f"  总资产: {final_asset:,.2f}")

    # 计算收益率
    total_return = (final_asset - init_cash) / init_cash * 100
    print(f"  总收益率: {total_return:.2f}%")

    # 交易统计
    position_list = tm.get_position_list()
    trade_list = tm.get_trade_list()

    print(f"\n📈 交易统计:")
    print(f"  总交易次数: {len(trade_list)}")
    print(f"  持仓股票数: {len(position_list)}")

    # 显示前10笔交易
    if trade_list:
        print(f"\n最近10笔交易:")
        for i, tr in enumerate(trade_list[-10:], 1):
            action = "买入" if tr.business == BUSINESS.BUY else "卖出"
            print(f"  {i}. {tr.datetime} {action} {tr.stock.market_code} "
                  f"{tr.number}股 @{tr.real_price:.2f} "
                  f"成本:{tr.cost:.2f}")

    # 显示当前持仓
    if position_list:
        print(f"\n当前持仓 (Top 10):")
        sorted_positions = sorted(position_list,
                                 key=lambda x: x.number * x.buy_money,
                                 reverse=True)
        for i, pos in enumerate(sorted_positions[:10], 1):
            market_value = pos.number * pos.buy_money
            print(f"  {i}. {pos.stock.market_code} "
                  f"{pos.number}股 成本价:{pos.buy_money:.2f} "
                  f"市值:{market_value:.2f}")

    print("\n" + "=" * 70)
    print("回测完成!")
    print("=" * 70)

    # 8. 保存回测报告 (可选)
    print("\n提示: 可以使用以下代码生成详细报告和图表:")
    print("  from hikyuu.trade_sys.portfolio import Performance")
    print("  pf_perf = Performance()")
    print("  pf_perf.report(tm)")

    return pf, sys, tm


if __name__ == "__main__":
    import os

    # 确保在项目根目录运行
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    print(f"工作目录: {os.getcwd()}")
    print()

    try:
        pf, sys, tm = run_backtest_example()
    except Exception as e:
        print(f"\n❌ 回测失败: {e}")
        import traceback
        traceback.print_exc()
