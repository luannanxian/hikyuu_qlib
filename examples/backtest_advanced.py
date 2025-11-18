"""
Hikyuu 高级回测示例 - 包含性能分析和可视化

演示如何:
1. 运行回测
2. 计算详细的性能指标
3. 生成可视化图表
4. 保存回测报告
"""

import sys
from pathlib import Path
from datetime import datetime

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hikyuu import *
from adapters.hikyuu.custom_sg_qlib_factor import CustomSG_QlibFactor


def calculate_performance_metrics(tm, init_cash):
    """
    计算详细的性能指标

    Args:
        tm: 交易管理器
        init_cash: 初始资金

    Returns:
        dict: 性能指标字典
    """
    # 获取资金曲线
    funds_list = tm.get_funds_curve(Query.ASSET)

    if not funds_list:
        return {}

    # 转换为 numpy 数组便于计算
    import numpy as np

    assets = np.array([f.value for f in funds_list])
    dates = [f.datetime for f in funds_list]

    # 计算收益率序列
    returns = np.diff(assets) / assets[:-1]

    # 1. 总收益率
    total_return = (assets[-1] - init_cash) / init_cash

    # 2. 年化收益率 (假设252个交易日)
    trading_days = len(assets)
    years = trading_days / 252
    annual_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0

    # 3. 最大回撤
    cummax = np.maximum.accumulate(assets)
    drawdowns = (assets - cummax) / cummax
    max_drawdown = abs(drawdowns.min())

    # 4. 夏普比率 (假设无风险利率 3%)
    risk_free_rate = 0.03
    if len(returns) > 1:
        annual_volatility = np.std(returns, ddof=1) * np.sqrt(252)
        sharpe_ratio = (annual_return - risk_free_rate) / annual_volatility if annual_volatility > 0 else 0
    else:
        sharpe_ratio = 0

    # 5. 胜率
    trade_list = tm.get_trade_list()
    buy_trades = {}
    wins = 0
    losses = 0

    for tr in trade_list:
        if tr.business == BUSINESS.BUY:
            buy_trades[tr.stock.market_code] = tr
        elif tr.business == BUSINESS.SELL:
            stock_code = tr.stock.market_code
            if stock_code in buy_trades:
                buy_price = buy_trades[stock_code].real_price
                sell_price = tr.real_price
                profit = (sell_price - buy_price) / buy_price

                if profit > 0:
                    wins += 1
                else:
                    losses += 1

                del buy_trades[stock_code]

    win_rate = wins / (wins + losses) if (wins + losses) > 0 else 0

    # 6. 盈亏比
    winning_trades = []
    losing_trades = []
    buy_trades_temp = {}

    for tr in trade_list:
        if tr.business == BUSINESS.BUY:
            buy_trades_temp[tr.stock.market_code] = tr
        elif tr.business == BUSINESS.SELL:
            stock_code = tr.stock.market_code
            if stock_code in buy_trades_temp:
                buy_price = buy_trades_temp[stock_code].real_price
                sell_price = tr.real_price
                profit = sell_price - buy_price

                if profit > 0:
                    winning_trades.append(profit)
                else:
                    losing_trades.append(abs(profit))

                del buy_trades_temp[stock_code]

    avg_win = np.mean(winning_trades) if winning_trades else 0
    avg_loss = np.mean(losing_trades) if losing_trades else 0
    profit_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 0

    return {
        "总收益率": f"{total_return * 100:.2f}%",
        "年化收益率": f"{annual_return * 100:.2f}%",
        "最大回撤": f"{max_drawdown * 100:.2f}%",
        "夏普比率": f"{sharpe_ratio:.2f}",
        "交易次数": len(trade_list),
        "胜率": f"{win_rate * 100:.2f}%",
        "盈亏比": f"{profit_loss_ratio:.2f}",
        "回测天数": trading_days,
        "最终资产": f"{assets[-1]:,.2f}",
    }


def plot_backtest_results(tm, init_cash, output_dir="outputs/backtest"):
    """
    绘制回测结果图表

    Args:
        tm: 交易管理器
        init_cash: 初始资金
        output_dir: 输出目录
    """
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib import font_manager
    import numpy as np

    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']
    plt.rcParams['axes.unicode_minus'] = False

    # 创建输出目录
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # 获取资金曲线
    funds_list = tm.get_funds_curve(Query.ASSET)

    if not funds_list:
        print("⚠️  没有资金曲线数据,无法绘图")
        return

    dates = [f.datetime.datetime() for f in funds_list]
    assets = [f.value for f in funds_list]

    # 1. 资金曲线图
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(dates, assets, label='总资产', linewidth=2)
    ax.axhline(y=init_cash, color='r', linestyle='--', label='初始资金')
    ax.set_xlabel('日期')
    ax.set_ylabel('资产 (元)')
    ax.set_title('资金曲线')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/equity_curve.png", dpi=300)
    print(f"✓ 已保存资金曲线图: {output_dir}/equity_curve.png")
    plt.close()

    # 2. 回撤图
    assets_array = np.array(assets)
    cummax = np.maximum.accumulate(assets_array)
    drawdowns = (assets_array - cummax) / cummax * 100

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.fill_between(dates, drawdowns, 0, alpha=0.3, color='red')
    ax.plot(dates, drawdowns, color='red', linewidth=1)
    ax.set_xlabel('日期')
    ax.set_ylabel('回撤 (%)')
    ax.set_title('回撤曲线')
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/drawdown_curve.png", dpi=300)
    print(f"✓ 已保存回撤曲线图: {output_dir}/drawdown_curve.png")
    plt.close()

    # 3. 日收益分布图
    returns = np.diff(assets_array) / assets_array[:-1] * 100

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(returns, bins=50, alpha=0.7, edgecolor='black')
    ax.axvline(x=0, color='r', linestyle='--', linewidth=2)
    ax.set_xlabel('日收益率 (%)')
    ax.set_ylabel('频数')
    ax.set_title('日收益率分布')
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/returns_distribution.png", dpi=300)
    print(f"✓ 已保存收益分布图: {output_dir}/returns_distribution.png")
    plt.close()


def save_backtest_report(metrics, tm, output_dir="outputs/backtest"):
    """
    保存回测报告到文件

    Args:
        metrics: 性能指标字典
        tm: 交易管理器
        output_dir: 输出目录
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = f"{output_dir}/backtest_report_{timestamp}.txt"

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write("Hikyuu 回测报告\n")
        f.write("=" * 70 + "\n\n")

        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write("性能指标:\n")
        f.write("-" * 70 + "\n")
        for key, value in metrics.items():
            f.write(f"  {key}: {value}\n")

        f.write("\n" + "=" * 70 + "\n")
        f.write("交易明细 (最近50笔):\n")
        f.write("=" * 70 + "\n\n")

        trade_list = tm.get_trade_list()
        for i, tr in enumerate(trade_list[-50:], 1):
            action = "买入" if tr.business == BUSINESS.BUY else "卖出"
            f.write(f"{i}. {tr.datetime} {action} {tr.stock.market_code} "
                   f"{tr.number}股 @{tr.real_price:.2f} "
                   f"成本:{tr.cost:.2f}\n")

        f.write("\n" + "=" * 70 + "\n")

    print(f"✓ 已保存回测报告: {report_path}")


def run_advanced_backtest():
    """运行高级回测并生成分析报告"""

    # 1. 初始化 Hikyuu
    print("=" * 70)
    print("Hikyuu 高级回测示例")
    print("=" * 70 + "\n")

    hikyuu_init("./config/hikyuu.ini")

    # 2. 配置参数
    pred_pkl_path = "./outputs/predictions/hs300_2025_pred.pkl"
    start_date = Datetime(20250101)
    end_date = Datetime(20251231)
    init_cash = 1000000

    # 3. 创建信号指示器
    sg = CustomSG_QlibFactor(
        pred_pkl_path=pred_pkl_path,
        buy_threshold=0.01,
        sell_threshold=-0.01,
        top_k=30,
    )

    # 4. 配置交易系统
    mm = MM_FixedCount(n=0.05 * init_cash)
    st = ST_FixedPercent(p=0.20)
    pg = PG_FixedPercent(p=0.30)
    sp = SP_FixedPercent(p=0.001)

    # 5. 获取股票池
    block = get_block("指数板块", "沪深300")
    stk_list = block.get_stock_list() if block else get_stock_type_list(11)

    print(f"股票池大小: {len(stk_list)}")
    print(f"回测时间: {start_date} ~ {end_date}")
    print(f"初始资金: {init_cash:,.0f}\n")

    # 6. 创建交易系统并运行
    print("运行回测...\n")

    # 创建原型系统
    proto_sys = SYS_Simple(
        mm=mm,
        sg=sg,
        st=st,
        pg=pg,
        sp=sp,
    )

    # 创建选股器
    selector = SE_Fixed(stk_list, proto_sys)

    # 创建投资组合
    pf = PF_Simple(
        tm=crtTM(start_date, init_cash, TC_FixedA2017()),
        se=selector,
    )

    # 运行回测
    pf.run(Query(start_date, end_date))

    tm = pf.tm

    # 7. 计算性能指标
    print("计算性能指标...\n")
    metrics = calculate_performance_metrics(tm, init_cash)

    print("=" * 70)
    print("回测结果")
    print("=" * 70)
    for key, value in metrics.items():
        print(f"  {key}: {value}")
    print("=" * 70 + "\n")

    # 8. 生成图表
    print("生成可视化图表...\n")
    plot_backtest_results(tm, init_cash)

    # 9. 保存报告
    print("\n保存回测报告...\n")
    save_backtest_report(metrics, tm)

    print("=" * 70)
    print("回测完成!")
    print("=" * 70)

    return pf, sys, tm, metrics


if __name__ == "__main__":
    import os

    # 确保在项目根目录运行
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    try:
        pf, sys, tm, metrics = run_advanced_backtest()
    except Exception as e:
        print(f"\n❌ 回测失败: {e}")
        import traceback
        traceback.print_exc()
