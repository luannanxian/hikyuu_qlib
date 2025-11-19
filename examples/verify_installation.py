#!/usr/bin/env python
"""
验证安装 - 检查所有依赖是否正确安装
"""

import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def check_dependencies():
    """检查所有依赖"""

    print("=" * 70)
    print("依赖检查")
    print("=" * 70)

    results = []

    # 检查 Python 版本
    print(f"\n✓ Python 版本: {sys.version}")

    # 检查核心依赖
    deps = [
        ("pandas", "数据处理"),
        ("numpy", "数值计算"),
        ("hikyuu", "数据源"),
        ("qlib", "机器学习框架"),
    ]

    for pkg, desc in deps:
        try:
            mod = __import__(pkg)
            version = getattr(mod, "__version__", "unknown")
            print(f"✓ {pkg:15} {version:15} ({desc})")
            results.append((pkg, True, version))
        except ImportError as e:
            print(f"✗ {pkg:15} {'未安装':15} ({desc}) - {e}")
            results.append((pkg, False, None))

    # 检查 Domain 层
    print("\n" + "=" * 70)
    print("Domain 层检查")
    print("=" * 70)

    try:
        from domain.entities.trading_signal import SignalBatch, TradingSignal, SignalType
        from domain.value_objects.stock_code import StockCode
        from domain.value_objects.configuration import BacktestConfig
        from domain.value_objects.date_range import DateRange
        print("✓ Domain 层导入成功")

        # 测试创建对象
        from datetime import datetime, date
        from decimal import Decimal

        batch = SignalBatch("测试", datetime.now())
        signal = TradingSignal(
            StockCode("sh600000"),
            datetime.now(),
            SignalType.BUY,
            0.85
        )
        batch.add_signal(signal)

        config = BacktestConfig(
            Decimal("1000000"),
            Decimal("0.0003")
        )

        date_range = DateRange(date(2024, 1, 1), date(2024, 12, 31))

        print("✓ Domain 对象创建成功")
        print(f"  - SignalBatch: {batch.size()} 条信号")
        print(f"  - BacktestConfig: 初始资金 {config.initial_capital}")
        print(f"  - DateRange: {date_range.start_date} ~ {date_range.end_date}")

    except Exception as e:
        print(f"✗ Domain 层错误: {e}")
        import traceback
        traceback.print_exc()

    # 总结
    print("\n" + "=" * 70)
    print("总结")
    print("=" * 70)

    total = len(results)
    success = sum(1 for _, ok, _ in results if ok)

    print(f"依赖检查: {success}/{total} 成功")

    if success == total:
        print("\n✓ 所有依赖安装正确!")
        print("\n下一步:")
        print("  1. 使用 Hikyuu 回测测试: python examples/simple_backtest.py")
        print("  2. 或训练模型生成预测文件")
    else:
        print("\n⚠️ 部分依赖缺失，请安装:")
        for pkg, ok, _ in results:
            if not ok:
                print(f"  pip install {pkg}")

    return success == total

if __name__ == "__main__":
    success = check_dependencies()
    sys.exit(0 if success else 1)
