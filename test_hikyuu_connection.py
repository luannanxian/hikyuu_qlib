#!/usr/bin/env python
"""
测试Hikyuu连接和数据可用性

此脚本检查:
1. Hikyuu是否正确安装
2. 数据源是否配置
3. 是否有可用的股票数据
4. 能否成功加载K线数据
"""

import hikyuu as hku
from datetime import datetime


def check_hikyuu_status():
    """检查Hikyuu状态"""
    print("=" * 60)
    print("Hikyuu 状态检查")
    print("=" * 60)

    # 1. 检查StockManager
    sm = hku.StockManager.instance()
    stock_count = len(sm)
    print(f"\n📊 股票总数: {stock_count}")

    if stock_count == 0:
        print("⚠️  警告: 没有加载任何股票数据")
        print("\n可能的原因:")
        print("1. 数据库连接失败 (配置文件: ~/.hikyuu/hikyuu.ini)")
        print("2. 本地数据目录为空")
        print("3. Hikyuu未正确初始化")
        return False

    # 2. 显示市场信息
    markets = sm.get_market_list()
    print(f"\n🏛️  可用市场: {markets}")

    # 3. 显示示例股票
    print(f"\n📈 示例股票 (前10只):")
    count = 0
    for stock in sm:
        if count >= 10:
            break
        print(f"  {stock.market_code}{stock.code:6s} - {stock.name}")
        count += 1

    return True


def test_data_load():
    """测试数据加载"""
    print("\n" + "=" * 60)
    print("测试K线数据加载")
    print("=" * 60)

    sm = hku.StockManager.instance()

    if len(sm) == 0:
        print("⚠️  跳过: 没有可用的股票数据")
        return

    # 获取第一只股票
    stock = None
    for s in sm:
        stock = s
        break

    if stock is None:
        print("⚠️  无法获取股票对象")
        return

    print(f"\n测试股票: {stock.market_code}{stock.code} - {stock.name}")

    # 尝试加载日线数据
    try:
        query = hku.Query(
            start=hku.Datetime(2024, 1, 1),
            end=hku.Datetime(2024, 1, 31),
            ktype=hku.Query.DAY
        )

        kdata = stock.get_kdata(query)
        print(f"✅ 成功加载 {len(kdata)} 条K线数据")

        if len(kdata) > 0:
            first = kdata[0]
            print(f"\n第一条数据:")
            print(f"  日期: {first.datetime}")
            print(f"  开盘: {first.openPrice}")
            print(f"  最高: {first.highPrice}")
            print(f"  最低: {first.lowPrice}")
            print(f"  收盘: {first.closePrice}")
            print(f"  成交量: {first.volume}")
        else:
            print("⚠️  返回数据为空 (该时间段可能没有交易)")

    except Exception as e:
        print(f"❌ 加载失败: {e}")


def test_cli_integration():
    """测试CLI集成"""
    print("\n" + "=" * 60)
    print("CLI命令测试建议")
    print("=" * 60)

    sm = hku.StockManager.instance()

    if len(sm) == 0:
        print("\n⚠️  由于没有数据，CLI命令将返回空结果")
        print("\n需要配置Hikyuu数据源:")
        print("1. 方式1: 连接到远程MySQL数据库")
        print("   - 编辑 ~/.hikyuu/hikyuu.ini")
        print("   - 配置baseinfo和kdata部分")
        print("\n2. 方式2: 下载本地数据")
        print("   - 使用Hikyuu的数据下载工具")
        print("   - 或使用importdata导入数据")
        return

    # 获取一个有效的股票代码
    stock = None
    for s in sm:
        if s.market_code in ['SH', 'SZ']:
            stock = s
            break

    if stock:
        code = f"{stock.market_code.lower()}{stock.code}"
        print(f"\n✅ 可以测试的CLI命令:")
        print(f"\n1. 加载数据:")
        print(f"PYTHONPATH=src python -m controllers.cli.main data load \\")
        print(f"  --code {code} \\")
        print(f"  --start 2024-01-01 \\")
        print(f"  --end 2024-01-31 \\")
        print(f"  --kline-type DAY")

        print(f"\n2. 使用便捷脚本:")
        print(f"./run_cli.sh data load \\")
        print(f"  --code {code} \\")
        print(f"  --start 2024-01-01 \\")
        print(f"  --end 2024-01-31 \\")
        print(f"  --kline-type DAY")


if __name__ == "__main__":
    try:
        has_data = check_hikyuu_status()

        if has_data:
            test_data_load()
            test_cli_integration()
        else:
            print("\n" + "=" * 60)
            print("配置建议")
            print("=" * 60)
            print("\n要使用Hikyuu CLI功能，需要配置数据源:")
            print("\n1. 检查配置文件: ~/.hikyuu/hikyuu.ini")
            print("2. 确保数据库连接正确")
            print("3. 或下载本地数据文件")
            print("\n当前配置: ~/.hikyuu/hikyuu.ini")
            print("数据目录: 参见配置文件中的datadir设置")

        print("\n" + "=" * 60)
        print("✅ 检查完成")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()
