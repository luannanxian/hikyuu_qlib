#!/usr/bin/env python
"""
测试项目配置文件是否正常工作

验证:
1. Hikyuu能否使用项目配置文件初始化
2. StockManager能否加载股票数据
3. 能否成功查询K线数据
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from adapters.hikyuu.hikyuu_data_adapter import HikyuuDataAdapter
from domain.value_objects.stock_code import StockCode
from domain.value_objects.date_range import DateRange
from domain.value_objects.kline_type import KLineType
from datetime import datetime
import asyncio


async def test_project_config():
    """测试项目配置文件"""
    print("=" * 60)
    print("测试项目配置文件")
    print("=" * 60)

    # 1. 创建使用项目配置的适配器
    config_file = "./config/hikyuu.ini"
    print(f"\n📄 使用配置文件: {config_file}")

    try:
        adapter = HikyuuDataAdapter(config_file=config_file)
        print("✅ 适配器创建成功")
    except Exception as e:
        print(f"❌ 适配器创建失败: {e}")
        return False

    # 2. 测试股票数据加载
    try:
        import hikyuu as hku

        sm = hku.StockManager.instance()
        stock_count = len(sm)
        print(f"\n📊 股票总数: {stock_count}")

        if stock_count == 0:
            print("⚠️  没有加载到股票数据")
            print("\n可能的原因:")
            print("1. MySQL服务器连接失败")
            print("2. 数据库配置不正确")
            print("3. 配置文件格式有误")
            return False

        print("✅ 股票数据加载成功")

        # 显示示例股票
        print(f"\n📈 示例股票 (前5只):")
        count = 0
        for stock in sm:
            if count >= 5:
                break
            print(f"  {stock.market_code}{stock.code:6s} - {stock.name}")
            count += 1

        # 3. 测试K线数据加载
        print("\n" + "=" * 60)
        print("测试K线数据加载")
        print("=" * 60)

        # 使用第一只上海或深圳股票测试
        test_stock = None
        for stock in sm:
            # 跳过北交所股票，使用上海或深圳的股票
            if stock.market_code.upper() in ["SH", "SZ"]:
                test_stock = stock
                break

        if test_stock:
            stock_code = StockCode(f"{test_stock.market_code.lower()}{test_stock.code}")
            date_range = DateRange(
                start_date=datetime(2024, 1, 1), end_date=datetime(2024, 1, 31)
            )

            print(f"\n测试股票: {stock_code.value}")

            kline_data = await adapter.load_stock_data(
                stock_code=stock_code,
                date_range=date_range,
                kline_type=KLineType.DAY,
            )

            if kline_data:
                print(f"✅ 成功加载 {len(kline_data)} 条K线数据")
                print(f"\n第一条数据:")
                first = kline_data[0]
                print(f"  日期: {first.timestamp}")
                print(f"  开盘: {first.open}")
                print(f"  最高: {first.high}")
                print(f"  最低: {first.low}")
                print(f"  收盘: {first.close}")
                print(f"  成交量: {first.volume}")
            else:
                print("⚠️  返回数据为空")

        print("\n" + "=" * 60)
        print("✅ 测试完成")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_project_config())
    sys.exit(0 if success else 1)
