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


async def main():
    """完整工作流"""
    print("=" * 70)
    print("Hikyuu → Qlib 训练 → Hikyuu 回测 完整工作流")
    print("=" * 70)

    # ===== 初始化 Hikyuu =====
    print("\n🔧 初始化 Hikyuu 系统...")
    hikyuu_init("./config/hikyuu.ini")
    print("✅ Hikyuu 初始化完成\n")

    # ===== 步骤1: 准备训练数据 (Hikyuu) =====
    print("【步骤1】从 Hikyuu 准备训练数据")

    stock_list = [
        'sh600000',  # 浦发银行
        'sh600016',  # 民生银行
        'sh600036',  # 招商银行
        'sh600519',  # 贵州茅台
        'sh600887',  # 伊利股份
    ]

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
            "num_leaves": 31,
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

    # 使用最新数据生成预测
    prediction_df = training_df.tail(len(stock_list)).copy()  # 每只股票取最新一条
    prediction_df = prediction_df.drop_duplicates(subset=['stock_code'], keep='last')

    print(f"  预测样本: {len(prediction_df)}")

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

    # ===== 步骤5: Hikyuu 回测 =====
    print("\n【步骤5】使用 Hikyuu 回测引擎回测")

    backtest_adapter = HikyuuBacktestAdapter()

    config = BacktestConfig(
        initial_capital=Decimal("1000000"),
        commission_rate=Decimal("0.0003")
    )

    date_range = DateRange(
        start_date=date(2024, 11, 19),
        end_date=date(2024, 12, 31)
    )

    print(f"  初始资金: ¥{config.initial_capital:,}")
    print(f"  回测期间: {date_range.start_date} ~ {date_range.end_date}")
    print(f"  信号数量: {signal_batch.size()}")

    try:
        result = await backtest_adapter.run_backtest(
            signals=signal_batch,
            config=config,
            date_range=date_range
        )

        print("\n" + "=" * 70)
        print("📊 回测结果")
        print("=" * 70)
        print(f"策略名称: {result.strategy_name}")
        print(f"初始资金: ¥{result.initial_capital:,}")
        print(f"最终资金: ¥{result.final_capital:,}")
        print(f"总收益率: {result.total_return:.2%}")
        print(f"年化收益: {result.annualized_return:.2%}")
        print(f"最大回撤: {result.max_drawdown:.2%}")
        print(f"夏普比率: {result.sharpe_ratio:.2f}")
        print(f"交易次数: {result.total_trades}")

        if result.trades:
            print(f"\n交易明细 (前5笔):")
            for i, trade in enumerate(result.trades[:5], 1):
                print(f"  {i}. {trade.stock_code.value} {trade.direction} "
                      f"{trade.quantity}股 @ ¥{trade.price:.2f}")

        print("\n" + "=" * 70)
        print("✅ 完整工作流执行成功!")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ 回测失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
