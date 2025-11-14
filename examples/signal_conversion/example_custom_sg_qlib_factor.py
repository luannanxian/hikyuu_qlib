"""
Example: Using CustomSG_QlibFactor for Signal Conversion

演示如何使用CustomSG_QlibFactor将Qlib预测转换为Hikyuu交易信号
"""

from datetime import datetime
from pathlib import Path

from adapters.hikyuu import CustomSG_QlibFactor
from domain.entities.prediction import Prediction, PredictionBatch
from domain.entities.trading_signal import SignalType
from domain.value_objects.stock_code import StockCode


def example_1_basic_usage():
    """示例1: 基础使用 - 加载pred.pkl并生成信号"""
    print("=" * 60)
    print("Example 1: Basic Usage")
    print("=" * 60)

    # 创建信号提供者(假设有pred.pkl文件)
    pred_pkl_path = "output/LGBM/pred.pkl"

    sg = CustomSG_QlibFactor(
        pred_pkl_path=pred_pkl_path,
        buy_threshold=0.02,  # 预测值 > 0.02 时买入
        sell_threshold=-0.02,  # 预测值 < -0.02 时卖出
        top_k=10,  # 只对预测排名前10的股票生成买入信号
        name="SG_QlibFactor",
    )

    print(f"Signal Provider: {sg.name}")
    print(f"Buy Threshold: {sg.getParam('buy_threshold')}")
    print(f"Sell Threshold: {sg.getParam('sell_threshold')}")
    print(f"Top-K: {sg.getParam('top_k')}")
    print()


def example_2_hikyuu_backtest():
    """示例2: Hikyuu回测集成"""
    print("=" * 60)
    print("Example 2: Hikyuu Backtest Integration")
    print("=" * 60)

    try:
        from hikyuu import (
            MM_FixedCount,
            Query,
            SYS_Simple,
            crtTM,
            load_hikyuu,
            sm,
        )

        # 初始化Hikyuu
        hku_config_path = Path.home() / ".hikyuu" / "config.ini"
        if hku_config_path.exists():
            load_hikyuu(str(hku_config_path))

            # 创建信号指示器
            sg = CustomSG_QlibFactor(
                pred_pkl_path="output/LGBM/pred.pkl",
                buy_threshold=0.02,
                sell_threshold=-0.02,
                top_k=10,
            )

            # 创建交易系统
            tm = crtTM(init_cash=100000)  # 初始资金10万
            mm = MM_FixedCount(100)  # 每次买入100股
            sys = SYS_Simple(tm=tm, sg=sg, mm=mm)

            # 运行回测
            stock = sm["sz000001"]  # 平安银行
            query = Query(-100)  # 最近100个交易日

            print(f"Running backtest for {stock.name}...")
            sys.run(stock, query)

            # 输出结果
            print(f"Final Cash: {tm.currentCash:.2f}")
            print(f"Buy Signals: {len(sg.getBuySignal())}")
            print(f"Sell Signals: {len(sg.getSellSignal())}")

        else:
            print("Hikyuu not configured. Skipping backtest example.")

    except ImportError:
        print("Hikyuu not installed. Skipping backtest example.")
    except Exception as e:
        print(f"Error running backtest: {e}")

    print()


def example_3_domain_interface():
    """示例3: 使用ISignalProvider接口"""
    print("=" * 60)
    print("Example 3: ISignalProvider Interface")
    print("=" * 60)

    # 创建信号提供者
    sg = CustomSG_QlibFactor(
        pred_pkl_path="dummy.pkl",  # 实际使用时替换为真实路径
        buy_threshold=0.02,
        sell_threshold=-0.02,
        top_k=5,
    )

    # 创建预测批次
    batch = PredictionBatch(model_id="LGBM_Model")
    date1 = datetime(2018, 9, 21)

    # 添加预测数据
    predictions = [
        Prediction(
            stock_code=StockCode("sh600000"),
            timestamp=date1,
            predicted_value=0.08,  # 强买入
            model_id="LGBM_Model",
        ),
        Prediction(
            stock_code=StockCode("sh600519"),
            timestamp=date1,
            predicted_value=0.05,  # 买入
            model_id="LGBM_Model",
        ),
        Prediction(
            stock_code=StockCode("sz000001"),
            timestamp=date1,
            predicted_value=0.01,  # 持有
            model_id="LGBM_Model",
        ),
        Prediction(
            stock_code=StockCode("sz000002"),
            timestamp=date1,
            predicted_value=-0.05,  # 卖出
            model_id="LGBM_Model",
        ),
    ]

    for pred in predictions:
        batch.add_prediction(pred)

    print(f"Prediction Batch: {batch.size()} predictions")
    print()

    # 生成信号批次
    signal_batch = sg.generate_signals_from_predictions(
        batch, buy_threshold=0.02, sell_threshold=-0.02, top_k=5
    )

    print(f"Signal Batch: {signal_batch.size()} signals")
    print(f"Strategy: {signal_batch.strategy_name}")
    print()

    # 按类型统计
    counts = signal_batch.count_by_type()
    print("Signal Distribution:")
    for signal_type, count in counts.items():
        print(f"  {signal_type.value}: {count}")
    print()

    # 显示买入信号
    buy_signals = signal_batch.filter_by_type(SignalType.BUY)
    print(f"Buy Signals ({len(buy_signals)}):")
    for signal in buy_signals:
        print(f"  {signal}")
    print()

    # 显示卖出信号
    sell_signals = signal_batch.filter_by_type(SignalType.SELL)
    print(f"Sell Signals ({len(sell_signals)}):")
    for signal in sell_signals:
        print(f"  {signal}")
    print()


def example_4_top_k_selection():
    """示例4: Top-K选股策略"""
    print("=" * 60)
    print("Example 4: Top-K Stock Selection")
    print("=" * 60)

    sg = CustomSG_QlibFactor(pred_pkl_path="dummy.pkl")

    # 创建预测批次
    batch = PredictionBatch(model_id="LGBM_Model")
    date1 = datetime(2018, 9, 21)

    # 添加10只股票的预测
    stocks_data = [
        ("sh600000", 0.08),
        ("sh600519", 0.07),
        ("sh600036", 0.06),
        ("sz000001", 0.05),
        ("sz000002", 0.04),
        ("sh600157", 0.03),
        ("sz000063", 0.02),
        ("sh600887", 0.01),
        ("sz002594", -0.01),
        ("sh601888", -0.02),
    ]

    for code, value in stocks_data:
        batch.add_prediction(
            Prediction(
                stock_code=StockCode(code),
                timestamp=date1,
                predicted_value=value,
                model_id="LGBM_Model",
            )
        )

    print(f"Total Predictions: {batch.size()}")
    print()

    # 获取Top-5股票
    top_5_stocks = sg.get_top_k_stocks(batch, k=5)

    print("Top-5 Stocks:")
    for i, stock_code in enumerate(top_5_stocks, 1):
        # 找到对应的预测
        pred = batch.get_prediction(stock_code, date1)
        print(f"  {i}. {stock_code.value}: {pred.predicted_value:.4f}")
    print()

    # 生成信号(仅Top-5生成买入信号)
    signal_batch = sg.generate_signals_from_predictions(
        batch, buy_threshold=0.02, sell_threshold=-0.02, top_k=5
    )

    buy_signals = signal_batch.filter_by_type(SignalType.BUY)
    print(f"Buy Signals Generated: {len(buy_signals)} (from Top-5)")
    for signal in buy_signals:
        print(f"  {signal}")
    print()


def example_5_query_specific_signal():
    """示例5: 查询特定股票信号"""
    print("=" * 60)
    print("Example 5: Query Specific Stock Signal")
    print("=" * 60)

    sg = CustomSG_QlibFactor(
        pred_pkl_path="dummy.pkl", buy_threshold=0.02, sell_threshold=-0.02
    )

    # 创建预测批次
    batch = PredictionBatch(model_id="LGBM_Model")
    date1 = datetime(2018, 9, 21)

    batch.add_prediction(
        Prediction(
            stock_code=StockCode("sh600000"),
            timestamp=date1,
            predicted_value=0.05,
            model_id="LGBM_Model",
        )
    )

    # 生成信号
    sg.generate_signals_from_predictions(batch)

    # 查询特定股票信号
    stock_code = StockCode("sh600000")
    signal = sg.get_signal_for_stock(stock_code, date1)

    if signal:
        print(f"Signal for {stock_code.value} on {date1.date()}:")
        print(f"  Type: {signal.signal_type.value}")
        print(f"  Strength: {signal.signal_strength.value}")
        print(f"  Reason: {signal.reason}")
    else:
        print(f"No signal found for {stock_code.value} on {date1.date()}")

    print()


def example_6_parameter_tuning():
    """示例6: 参数调优"""
    print("=" * 60)
    print("Example 6: Parameter Tuning")
    print("=" * 60)

    # 创建预测批次
    batch = PredictionBatch(model_id="LGBM_Model")
    date1 = datetime(2018, 9, 21)

    for i, code in enumerate(
        ["sh600000", "sh600519", "sz000001", "sz000002", "sh600036"]
    ):
        batch.add_prediction(
            Prediction(
                stock_code=StockCode(code),
                timestamp=date1,
                predicted_value=0.05 - i * 0.02,  # 0.05, 0.03, 0.01, -0.01, -0.03
                model_id="LGBM_Model",
            )
        )

    # 测试不同阈值
    thresholds = [(0.01, -0.01), (0.02, -0.02), (0.03, -0.03)]

    for buy_th, sell_th in thresholds:
        sg = CustomSG_QlibFactor(pred_pkl_path="dummy.pkl")

        signal_batch = sg.generate_signals_from_predictions(
            batch, buy_threshold=buy_th, sell_threshold=sell_th
        )

        counts = signal_batch.count_by_type()
        print(
            f"Threshold (buy={buy_th}, sell={sell_th}): "
            f"BUY={counts[SignalType.BUY]}, "
            f"SELL={counts[SignalType.SELL]}, "
            f"HOLD={counts[SignalType.HOLD]}"
        )

    print()


def main():
    """运行所有示例"""
    print("\n")
    print("*" * 60)
    print("CustomSG_QlibFactor Usage Examples")
    print("*" * 60)
    print("\n")

    example_1_basic_usage()
    # example_2_hikyuu_backtest()  # 需要Hikyuu环境
    example_3_domain_interface()
    example_4_top_k_selection()
    example_5_query_specific_signal()
    example_6_parameter_tuning()

    print("*" * 60)
    print("All examples completed!")
    print("*" * 60)


if __name__ == "__main__":
    main()
