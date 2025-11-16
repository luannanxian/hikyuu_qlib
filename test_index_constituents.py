#!/usr/bin/env python3
"""
测试指数成分股获取功能
"""

import sys

sys.path.insert(0, 'src')

from utils.index_constituents import (
    get_hs300,
    get_index_constituents,
    list_available_indices,
    search_indices,
)


def main():
    print("=" * 70)
    print("指数成分股功能测试")
    print("=" * 70)

    # 1. 搜索包含"300"的指数
    print("\n【1】搜索包含'300'的指数:")
    print("-" * 70)
    indices = search_indices("300")
    print(f"找到 {len(indices)} 个指数\n")
    print("前20个:")
    for i, (name, count) in enumerate(indices[:20], 1):
        print(f"  {i:2d}. {name:30s} - {count:3d}只")

    # 2. 获取沪深300成分股
    print("\n【2】获取沪深300成分股:")
    print("-" * 70)
    hs300_stocks = get_hs300()
    print(f"沪深300成分股数量: {len(hs300_stocks)}\n")
    print("前30只:")
    for i, stock in enumerate(hs300_stocks[:30], 1):
        print(f"  {i:2d}. {stock.value}")

    # 3. 获取字符串格式的股票代码
    print("\n【3】获取字符串格式的股票代码:")
    print("-" * 70)
    codes = get_index_constituents("沪深300", return_stock_codes=False)
    print(f"前10只: {codes[:10]}")

    # 4. 搜索主要指数
    print("\n【4】主要指数成分股数量:")
    print("-" * 70)
    major_indices = ["沪深300", "中证500", "上证50", "创业板50", "科创50"]
    for index_name in major_indices:
        try:
            stocks = get_index_constituents(index_name)
            print(f"  {index_name:10s}: {len(stocks):3d}只")
        except Exception as e:
            print(f"  {index_name:10s}: 获取失败 - {e}")

    # 5. 列出所有可用指数（仅显示前20个）
    print("\n【5】所有可用指数（前20个）:")
    print("-" * 70)
    all_indices = list_available_indices()
    print(f"总共 {len(all_indices)} 个指数\n")
    for i, (name, count) in enumerate(all_indices[:20], 1):
        print(f"  {i:2d}. {name:40s} - {count:3d}只")

    print("\n" + "=" * 70)
    print("测试完成！")
    print("=" * 70)


if __name__ == "__main__":
    main()
