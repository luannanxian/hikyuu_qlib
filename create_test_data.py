"""
创建测试训练数据文件

用于在没有真实Hikyuu数据源的情况下测试训练功能
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from datetime import datetime, timedelta
from decimal import Decimal


from domain.entities.kline_data import KLineData
from domain.value_objects.kline_type import KLineType
from domain.value_objects.stock_code import StockCode
from utils.data_conversion import (
    convert_kline_to_training_data,
    save_to_file,
)


def create_test_data(stock_code: str = "sh600036", days: int = 365):
    """创建测试K线数据"""
    print(f"正在创建 {stock_code} 的测试数据（{days}天）...")

    kline_data = []
    base_date = datetime(2023, 1, 2)
    base_price = 30.0

    for i in range(days):
        # 模拟价格波动
        noise = (i % 10 - 5) * 0.3
        price = base_price + i * 0.05 + noise

        kline = KLineData(
            stock_code=StockCode(stock_code),
            timestamp=base_date + timedelta(days=i),
            kline_type=KLineType.DAY,
            open=Decimal(str(price)),
            high=Decimal(str(price + 1.0)),
            low=Decimal(str(price - 1.0)),
            close=Decimal(str(price + 0.5)),
            volume=1000000 + i * 10000,
            amount=Decimal(str(30000000 + i * 500000)),
        )
        kline_data.append(kline)

    print(f"✅ 创建了 {len(kline_data)} 条K线记录")
    return kline_data


def main():
    # 创建数据目录
    data_dir = Path("data/test")
    data_dir.mkdir(parents=True, exist_ok=True)

    # 为几个股票创建测试数据
    stocks = ["sh600036", "sh600000", "sz000001"]

    for stock_code in stocks:
        print(f"\n{'='*60}")
        print(f"处理 {stock_code}")
        print('='*60)

        # 创建K线数据
        kline_data = create_test_data(stock_code, days=365)

        # 转换为训练格式
        print("正在转换为训练格式（添加特征和标签）...")
        training_data = convert_kline_to_training_data(
            kline_data,
            add_features=True,
            add_labels=True,
            label_horizon=1,
        )

        print(f"✅ 转换完成：{len(training_data)} 条记录")
        print(f"   特征数量：{len(training_data.columns)} 列")
        print(f"   列名：{list(training_data.columns)[:10]}...")

        # 保存为CSV和Parquet
        csv_file = data_dir / f"{stock_code}_train.csv"
        parquet_file = data_dir / f"{stock_code}_train.parquet"

        print("正在保存到文件...")
        save_to_file(training_data, str(csv_file))
        save_to_file(training_data, str(parquet_file))

        print("✅ 已保存:")
        print(f"   CSV:     {csv_file}")
        print(f"   Parquet: {parquet_file}")

    print(f"\n{'='*60}")
    print("✅ 测试数据创建完成！")
    print('='*60)
    print("\n现在您可以使用这些文件测试训练功能：")
    print("\n示例命令:")
    for stock_code in stocks:
        print(f"  ./run_cli.sh model train --type LGBM --name {stock_code}_model \\")
        print(f"      --data data/test/{stock_code}_train.csv\n")


if __name__ == "__main__":
    main()
