#!/usr/bin/env python
"""
生成预测信号脚本

功能：
1. 加载训练好的模型
2. 生成股票预测信号
3. 保存预测结果
"""

import sys
import argparse
import pickle
from pathlib import Path
from datetime import datetime

# 自动配置 PYTHONPATH
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

print("=" * 70)
print("生成预测信号")
print("=" * 70)
print(f"项目路径: {PROJECT_ROOT}")
print()


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="生成预测信号")

    parser.add_argument(
        "--model-path",
        type=str,
        required=True,
        help="模型文件路径"
    )

    parser.add_argument(
        "--start-date",
        type=str,
        default="2024-01-01",
        help="预测开始日期 (默认: 2024-01-01)"
    )

    parser.add_argument(
        "--end-date",
        type=str,
        default="2024-12-31",
        help="预测结束日期 (默认: 2024-12-31)"
    )

    parser.add_argument(
        "--output",
        type=str,
        default="predictions.pkl",
        help="预测结果保存路径 (默认: predictions.pkl)"
    )

    parser.add_argument(
        "--index",
        type=str,
        default="HS300",
        choices=["HS300", "CSI500", "ALL"],
        help="股票指数 (默认: HS300)"
    )

    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()

    print(f"🤖 模型文件: {args.model_path}")
    print(f"📅 预测日期: {args.start_date} ~ {args.end_date}")
    print(f"📈 股票指数: {args.index}")
    print(f"💾 输出文件: {args.output}")
    print()

    try:
        import qlib
        from qlib.constant import REG_CN

        # 检查数据目录
        data_path = Path.home() / ".qlib" / "qlib_data" / "cn_data"
        print("🔧 检查 Qlib 数据...")

        if not data_path.exists():
            print(f"❌ 错误: Qlib 数据目录不存在: {data_path}")
            print()
            print("请先下载 Qlib 数据:")
            print("  python -m qlib.run.get_data qlib_data --target_dir ~/.qlib/qlib_data/cn_data --region cn")
            return 1

        print(f"✅ 数据目录: {data_path}")
        print()

        # 初始化 Qlib
        print("🔧 初始化 Qlib...")
        qlib.init(provider_uri=str(data_path), region=REG_CN)
        print("✅ Qlib 初始化成功")
        print()

        # 加载模型
        print(f"📦 加载模型: {args.model_path}")
        model_path = Path(args.model_path)

        if not model_path.exists():
            print(f"❌ 错误: 模型文件不存在: {args.model_path}")
            sys.exit(1)

        with open(model_path, "rb") as f:
            model = pickle.load(f)

        print("✅ 模型加载成功")
        print()

        # 准备预测数据集
        print("📊 准备预测数据...")

        from qlib.utils import init_instance_by_config

        dataset_config = {
            "class": "DatasetH",
            "module_path": "qlib.data.dataset",
            "kwargs": {
                "handler": {
                    "class": "Alpha158",
                    "module_path": "qlib.contrib.data.handler",
                    "kwargs": {
                        "start_time": args.start_date,
                        "end_time": args.end_date,
                        "fit_start_time": args.start_date,
                        "fit_end_time": args.end_date,
                        "instruments": args.index.lower(),
                    },
                },
                "segments": {
                    "test": (args.start_date, args.end_date),
                },
            },
        }

        dataset = init_instance_by_config(dataset_config)
        print("✅ 数据集准备完成")
        print()

        # 生成预测
        print("🚀 生成预测信号...")
        print("⏳ 这可能需要几分钟时间...")
        print()

        predictions = model.predict(dataset)

        print(f"✅ 预测完成! 共 {len(predictions)} 条预测")
        print()

        # 预测统计
        print("📊 预测统计:")
        print(f"  最小值: {predictions.min():.4f}")
        print(f"  最大值: {predictions.max():.4f}")
        print(f"  平均值: {predictions.mean():.4f}")
        print(f"  中位数: {predictions.median():.4f}")
        print()

        # 保存预测结果
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "wb") as f:
            pickle.dump(predictions, f)

        print(f"💾 预测结果已保存: {output_path}")
        print()

        print("=" * 70)
        print("✅ 预测完成!")
        print("=" * 70)
        print()
        print("下一步:")
        print(f"  运行回测: ./run_backtest.sh qlib --predictions {output_path}")

    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print()
        print("请确保已安装必要依赖:")
        print("  pip install qlib")
        sys.exit(1)

    except Exception as e:
        print(f"❌ 预测失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
