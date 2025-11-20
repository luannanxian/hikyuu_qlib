#!/usr/bin/env python
"""
Hikyuu → Qlib 训练 → Hikyuu 回测 完整工作流示例

展示如何:
1. 使用 Hikyuu 获取数据并准备训练数据
2. 使用 QlibModelTrainerAdapter 训练 LGBM 模型
3. 生成预测信号
4. 使用 HikyuuBacktestAdapter 回测
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime, date
from decimal import Decimal

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pandas as pd
import numpy as np
from hikyuu import *

from adapters.qlib.qlib_model_trainer_adapter import QlibModelTrainerAdapter
from adapters.hikyuu.hikyuu_backtest_adapter import HikyuuBacktestAdapter
from domain.entities.model import Model, ModelType
from domain.entities.trading_signal import SignalBatch, TradingSignal, SignalType
from domain.value_objects.stock_code import StockCode
from domain.value_objects.configuration import BacktestConfig
from domain.value_objects.date_range import DateRange


def prepare_hikyuu_training_data(stock_list, start_date, end_date):
    """
    从 Hikyuu 获取数据并准备训练 DataFrame

    Args:
        stock_list: 股票列表 ['sh600000', 'sh600016', ...]
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        pd.DataFrame: 包含 stock_code, features, label_return 的训练数据
    """
    print("\n📊 准备 Hikyuu 训练数据...")

    sm = StockManager.instance()
    training_data = []

    for stock_code in stock_list:
        try:
            # 获取 Hikyuu 股票对象（注意：方法名是 get_stock 不是 getStock）
            stock = sm.get_stock(stock_code.upper())
            if not stock or stock.is_null():
                print(f"  ⚠️  跳过: {stock_code} (未找到)")
                continue

            # 获取日线数据（注意：方法名是 get_kdata 不是 getKData）
            kdata = stock.get_kdata(Query(-500))  # 获取最近500天数据

            if len(kdata) < 50:  # 至少需要50天数据来计算特征
                print(f"  ⚠️  跳过: {stock_code} (数据不足)")
                continue

            # 提取价格数据（注意：属性名是 close 不是 closePrice）
            close_prices = np.array([k.close for k in kdata])
            high_prices = np.array([k.high for k in kdata])
            low_prices = np.array([k.low for k in kdata])
            volumes = np.array([k.volume for k in kdata])

            # 计算技术指标特征
            for i in range(50, len(kdata)):  # 需要足够历史数据计算指标
                # 特征1: 5日收益率
                ret_5d = (close_prices[i] - close_prices[i-5]) / close_prices[i-5]

                # 特征2: 10日收益率
                ret_10d = (close_prices[i] - close_prices[i-10]) / close_prices[i-10]

                # 特征3: 20日收益率
                ret_20d = (close_prices[i] - close_prices[i-20]) / close_prices[i-20]

                # 特征4: 20日波动率
                volatility_20d = np.std(close_prices[i-20:i])

                # 特征5: 相对成交量 (今日/20日均量)
                vol_avg_20d = np.mean(volumes[i-20:i])
                rel_volume = volumes[i] / vol_avg_20d if vol_avg_20d > 0 else 1.0

                # 标签: 未来5日收益率
                if i + 5 < len(kdata):
                    label_return = (close_prices[i+5] - close_prices[i]) / close_prices[i]
                else:
                    continue  # 没有未来数据,跳过

                training_data.append({
                    'stock_code': stock_code.lower(),
                    'date': kdata[i].datetime.date(),
                    'feature_ret_5d': ret_5d,
                    'feature_ret_10d': ret_10d,
                    'feature_ret_20d': ret_20d,
                    'feature_volatility': volatility_20d,
                    'feature_rel_volume': rel_volume,
                    'label_return': label_return
                })

            print(f"  ✅ {stock_code}: {len(training_data)} 样本")

        except Exception as e:
            print(f"  ❌ {stock_code}: {e}")
            continue

    df = pd.DataFrame(training_data)
    print(f"\n✅ 总样本数: {len(df)}")
    print(f"   特征列: {[c for c in df.columns if c.startswith('feature_')]}")
    print(f"   标签列: label_return")

    return df


def predictions_to_signals(predictions_batch, signal_date):
    """
    将预测结果转换为交易信号

    Args:
        predictions_batch: PredictionBatch 预测批次
        signal_date: 信号日期

    Returns:
        SignalBatch: 交易信号批次
    """
    print("\n🔄 转换预测为交易信号...")

    signal_batch = SignalBatch(
        strategy_name="Hikyuu-Qlib-LGBM",
        batch_date=datetime.now()
    )

    # 按预测值排序,选择 Top-N 做多
    df = predictions_batch.to_dataframe()
    df = df.sort_values('predicted_value', ascending=False)

    top_n = 10  # 做多前10只

    for i, row in df.head(top_n).iterrows():
        signal = TradingSignal(
            stock_code=StockCode(row['stock_code']),
            signal_date=signal_date,
            signal_type=SignalType.BUY,
            price=None,  # 由回测引擎决定
        )
        signal_batch.add_signal(signal)

    print(f"✅ 生成 {signal_batch.size()} 个交易信号")

    return signal_batch


def get_index_stocks(index_name: str, max_stocks: int = None) -> list[str]:
    """
    获取指数成分股列表

    Args:
        index_name: 指数名称，如 "沪深300", "中证500", "上证50"
        max_stocks: 最大股票数量限制（可选）

    Returns:
        股票代码列表
    """
    from hikyuu import get_block, StockManager

    print(f"\n📊 获取 {index_name} 成分股...")

    # 获取指数板块
    block = get_block("指数板块", index_name)

    if not block:
        print(f"⚠️  警告: 无法加载 {index_name} 板块")
        return []

    # 获取成分股列表
    stock_list_obj = block.get_stock_list()

    # 转换为股票代码列表
    stock_codes = []
    sm = StockManager.instance()

    for stock in stock_list_obj:
        if not stock.is_null():
            code = stock.market_code.lower()
            stock_codes.append(code)

    print(f"✅ {index_name} 总成分股: {len(stock_codes)} 只")

    # 如果指定了最大数量，随机采样
    if max_stocks and len(stock_codes) > max_stocks:
        import random
        stock_codes = random.sample(stock_codes, max_stocks)
        print(f"   随机采样: {max_stocks} 只股票")

    return stock_codes


async def main():
    """完整工作流"""
    import argparse

    # 解析命令行参数
    parser = argparse.ArgumentParser(description="Hikyuu → Qlib 训练工作流")
    parser.add_argument(
        "--index",
        type=str,
        default=None,
        help="指数名称（如：沪深300、中证500、上证50）"
    )
    parser.add_argument(
        "--max-stocks",
        type=int,
        default=None,
        help="最大训练股票数量"
    )
    parser.add_argument(
        "--stocks",
        type=str,
        nargs="+",
        default=None,
        help="手动指定股票代码列表（如：sh600000 sh600016）"
    )

    args = parser.parse_args()

    print("=" * 70)
    print("Hikyuu → Qlib 训练 → Hikyuu 回测 完整工作流")
    print("=" * 70)

    # ===== 初始化 Hikyuu =====
    print("\n🔧 初始化 Hikyuu 系统...")
    hikyuu_init("./config/hikyuu.ini")
    print("✅ Hikyuu 初始化完成\n")

    # ===== 步骤1: 准备训练数据 (Hikyuu) =====
    print("【步骤1】从 Hikyuu 准备训练数据")

    # 确定股票列表
    if args.index:
        # 从指数获取成分股
        stock_list = get_index_stocks(args.index, args.max_stocks)
        if not stock_list:
            print("❌ 无法获取指数成分股，退出")
            return
        print(f"\n📈 使用 {args.index} 成分股训练")
    elif args.stocks:
        # 使用手动指定的股票
        stock_list = args.stocks
        print(f"\n📋 使用手动指定的 {len(stock_list)} 只股票")
    else:
        # 默认使用示例股票
        stock_list = [
            'sh600000',  # 浦发银行
            'sh600016',  # 民生银行
            'sh600036',  # 招商银行
            'sh600519',  # 贵州茅台
            'sh600887',  # 伊利股份
        ]
        print(f"\n📋 使用默认示例股票: {len(stock_list)} 只")

    training_df = prepare_hikyuu_training_data(
        stock_list=stock_list,
        start_date=date(2023, 1, 1),
        end_date=date(2024, 10, 31)
    )

    if training_df.empty:
        print("❌ 训练数据为空,退出")
        return

    # ===== 步骤2: 训练模型 (QlibModelTrainerAdapter) =====
    print("\n【步骤2】训练 LGBM 模型")

    adapter = QlibModelTrainerAdapter()

    model = Model(
        model_type=ModelType.LGBM,
        hyperparameters={
            "learning_rate": 0.05,
            "num_leaves": 15,          # 减少叶子数，降低模型复杂度
            "min_data_in_leaf": 50,     # 增加最小叶子样本数
            "lambda_l1": 0.1,           # L1 正则化
            "lambda_l2": 0.1,           # L2 正则化
            "verbose": -1,
        }
    )

    print(f"  模型类型: {model.model_type.value}")
    print(f"  训练样本: {len(training_df)}")

    trained_model = await adapter.train(model, training_df)

    print(f"\n✅ 模型训练完成")
    print(f"   状态: {trained_model.status.value}")
    print(f"   训练 R²: {trained_model.metrics.get('train_r2', 0):.4f}")
    print(f"   测试 R²: {trained_model.metrics.get('test_r2', 0):.4f}")
    print(f"   训练 RMSE: {trained_model.metrics.get('train_rmse', 0):.4f}")
    print(f"   测试 RMSE: {trained_model.metrics.get('test_rmse', 0):.4f}")

    # ===== 步骤3: 生成预测 =====
    print("\n【步骤3】生成预测信号")

    # 使用最新数据生成预测 - 为每只股票取最新一条
    prediction_df = training_df.groupby('stock_code').tail(1).copy()

    print(f"  预测样本: {len(prediction_df)} 只股票")

    predictions_batch = await adapter.predict_batch(
        model=trained_model,
        input_data=prediction_df,
        prediction_date=datetime(2024, 11, 19)
    )

    print(f"\n✅ 预测完成")
    print(f"   批次大小: {predictions_batch.size()}")
    print(f"   平均置信度: {predictions_batch.average_confidence():.2%}")

    # 显示预测结果
    print("\n预测结果:")
    pred_df = predictions_batch.to_dataframe()
    pred_df = pred_df.sort_values('predicted_value', ascending=False)
    print(pred_df[['stock_code', 'predicted_value', 'confidence']].to_string(index=False))

    # ===== 步骤4: 转换为交易信号 =====
    signal_batch = predictions_to_signals(
        predictions_batch,
        datetime(2024, 11, 19)
    )

    # ===== 步骤5: 保存预测结果供回测使用 =====
    print("\n【步骤5】保存预测结果")

    import pickle
    from pathlib import Path

    # 准备预测数据格式（CustomSG_QlibFactor兼容格式）
    # 将 PredictionBatch 转换为 MultiIndex DataFrame
    pred_df = predictions_batch.to_dataframe()

    # 创建 MultiIndex: (timestamp, stock_code)
    pred_df_multiindex = pred_df.set_index(['timestamp', 'stock_code'])

    # 重命名 predicted_value 为 score（CustomSG_QlibFactor期望的列名）
    if 'predicted_value' in pred_df_multiindex.columns:
        pred_df_multiindex = pred_df_multiindex.rename(columns={'predicted_value': 'score'})

    output_path = Path("./outputs/predictions")
    output_path.mkdir(parents=True, exist_ok=True)
    pred_file = output_path / "workflow_pred.pkl"

    # 直接保存DataFrame（不要用dict包装）
    pred_df_multiindex.to_pickle(pred_file)

    print(f"✅ 预测结果已保存: {pred_file}")
    print(f"   格式: MultiIndex DataFrame (timestamp, stock_code)")
    print(f"   列: {list(pred_df_multiindex.columns)}")
    print(f"   样本数: {len(pred_df_multiindex)}")

    # ===== 步骤6: 使用 Hikyuu 进行回测 =====
    print("\n【步骤6】使用 Hikyuu 进行回测")

    # 导入 Hikyuu 回测所需组件
    from hikyuu import (
        Query, crtTM, TC_FixedA,
        MM_FixedCount, ST_FixedPercent, PG_NoGoal, SP_FixedPercent,
        SYS_Simple, SE_Fixed, PF_Simple, BUSINESS
    )
    from adapters.hikyuu.custom_sg_qlib_factor import CustomSG_QlibFactor

    try:
        # 回测参数设置
        # 使用 pred_df_multiindex (已经设置了 MultiIndex)
        pred_start = pred_df_multiindex.index.get_level_values(0).unique()[0]
        start_date = Datetime(pred_start.year, pred_start.month, pred_start.day)
        end_date = Datetime(2024, 12, 31)
        init_cash = 1000000

        print(f"  回测时间: {start_date} ~ {end_date}")
        print(f"  初始资金: ¥{init_cash:,.0f}")
        print(f"  持仓数量: {len(stock_list)} 只股票")

        # 创建信号指示器
        print("\n  🎯 创建 CustomSG_QlibFactor 信号指示器...")
        sg = CustomSG_QlibFactor(
            pred_pkl_path=str(pred_file),
            buy_threshold=0.0,
            sell_threshold=-0.1,
            top_k=min(5, len(stock_list)),
            name="WorkflowQlibFactor"
        )

        # 资金管理
        mm = MM_FixedCount(n=init_cash * 0.95 / min(5, len(stock_list)))

        # 止损策略
        st = ST_FixedPercent(p=0.15)

        # 盈利目标策略
        pg = PG_NoGoal()

        # 滑点
        sp = SP_FixedPercent(p=0.0005)

        # 获取股票对象列表
        sm = StockManager.instance()
        stk_list = []
        for code in stock_list:
            stock = sm.get_stock(code.upper())
            if stock and not stock.is_null():
                stk_list.append(stock)

        print(f"  ✅ 股票池大小: {len(stk_list)} 只")

        # 创建交易账户
        my_tm = crtTM(
            date=start_date,
            init_cash=init_cash,
            cost_func=TC_FixedA(commission=0.0003, lowest_commission=5),
            name="WorkflowBacktest"
        )

        # 创建交易系统
        print("\n  🚀 开始回测...")
        proto_sys = SYS_Simple(mm=mm, sg=sg, st=st, sp=sp, pg=pg)
        selector = SE_Fixed(stk_list, proto_sys)
        pf = PF_Simple(tm=my_tm, se=selector)
        pf.name = "WorkflowBacktest"

        # 执行回测
        pf.run(Query(start_date, end_date))

        # 显示回测结果
        print("\n  " + "=" * 68)
        print("  📊 回测结果")
        print("  " + "=" * 68)

        # 获取最终资产
        final_funds = my_tm.get_funds(Datetime.max())
        final_cash = final_funds.cash
        final_total = final_funds.total_assets
        final_market_value = final_total - final_cash

        # 计算收益
        total_return = (final_total - init_cash) / init_cash

        print(f"\n  💰 资金情况:")
        print(f"    初始资金: ¥{init_cash:,.2f}")
        print(f"    最终现金: ¥{final_cash:,.2f}")
        print(f"    持仓市值: ¥{final_market_value:,.2f}")
        print(f"    总资产:   ¥{final_total:,.2f}")
        print(f"\n  📈 收益指标:")
        print(f"    总收益率: {total_return:.2%}")

        # 获取交易记录
        trade_list = my_tm.get_trade_list()
        print(f"\n  📋 交易记录:")
        print(f"    总交易次数: {len(trade_list)}")

        if trade_list:
            print(f"\n    最近5笔交易:")
            for i, trade in enumerate(trade_list[-5:], 1):
                direction = "买入" if trade.business == BUSINESS.BUY else "卖出"
                print(f"      {i}. {trade.datetime} {direction} {trade.stock.market_code} "
                      f"{trade.number}股 @ ¥{trade.real_price:.2f}")

        # 获取持仓
        positions = my_tm.get_position_list()
        if positions:
            print(f"\n  💼 当前持仓 ({len(positions)}只):")
            for pos in positions:
                print(f"      {pos.stock.market_code}: {pos.number}股 "
                      f"成本¥{pos.buy_money/pos.number if pos.number > 0 else 0:.2f}")

        print("\n  " + "=" * 68)
        print("  ✅ Hikyuu 回测完成!")
        print("  " + "=" * 68)

    except Exception as e:
        print(f"\n  ❌ 回测失败: {e}")
        print("\n  💡 提示: 可以单独运行 backtest_workflow_pred.py 进行回测")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 70)
    print("✅ 完整工作流执行完成!")
    print("=" * 70)
    print("\n📊 执行总结:")
    print(f"  ✅ 数据提取: {len(training_df)} 个训练样本")
    print(f"  ✅ 模型训练: R² = {trained_model.metrics.get('test_r2', 0):.4f}")
    print(f"  ✅ 预测生成: {predictions_batch.size()} 个预测")
    print(f"  ✅ 信号转换: {signal_batch.size()} 个交易信号")
    print(f"  ✅ 结果保存: {pred_file}")
    print(f"  ✅ Hikyuu 回测: 已执行")

    print("\n💡 优化建议:")
    print("  1. 增加训练数据: Query(-2000) 获取更多历史数据")
    print("  2. 增加正则化参数改善过拟合")
    print("  3. 添加更多技术指标特征（MACD, RSI, Bollinger Bands）")


if __name__ == "__main__":
    asyncio.run(main())
