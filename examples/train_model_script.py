#!/usr/bin/env python
"""
训练机器学习模型脚本

功能：
1. 使用 Qlib 训练 LGBM/XGBoost 等模型
2. 支持不同指数（HS300、CSI500等）
3. 自动保存模型
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# 自动配置 PYTHONPATH
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

print("=" * 70)
print("机器学习模型训练")
print("=" * 70)
print(f"项目路径: {PROJECT_ROOT}")
print()


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="训练机器学习模型")

    parser.add_argument(
        "--model-type",
        type=str,
        default="LGBM",
        choices=["LGBM", "XGBoost", "CatBoost"],
        help="模型类型 (默认: LGBM)"
    )

    parser.add_argument(
        "--index",
        type=str,
        default="HS300",
        choices=["HS300", "CSI500", "ALL"],
        help="股票指数 (默认: HS300)"
    )

    parser.add_argument(
        "--start-date",
        type=str,
        default="2020-01-01",
        help="训练开始日期 (默认: 2020-01-01)"
    )

    parser.add_argument(
        "--end-date",
        type=str,
        default="2023-12-31",
        help="训练结束日期 (默认: 2023-12-31)"
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="models",
        help="模型保存目录 (默认: models)"
    )

    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()

    print(f"📊 模型类型: {args.model_type}")
    print(f"📈 股票指数: {args.index}")
    print(f"📅 训练日期: {args.start_date} ~ {args.end_date}")
    print(f"💾 保存目录: {args.output_dir}")
    print()

    try:
        import qlib
        from qlib.constant import REG_CN
        import os

        # 检查数据目录
        data_path = Path.home() / ".qlib" / "qlib_data" / "cn_data"
        print("🔧 检查 Qlib 数据...")

        if not data_path.exists():
            print(f"❌ 错误: Qlib 数据目录不存在: {data_path}")
            print()
            print("请先下载 Qlib 数据:")
            print("  python -m qlib.run.get_data qlib_data --target_dir ~/.qlib/qlib_data/cn_data --region cn")
            print()
            print("或者使用本地已有的数据目录:")
            print("  export QLIB_DATA_PATH=/path/to/your/qlib/data")
            return 1

        # 检查数据完整性
        instrument_path = data_path / "instruments"
        if not instrument_path.exists():
            print(f"❌ 错误: Qlib 数据不完整，缺少 instruments 目录")
            print(f"   请重新下载数据或检查数据完整性")
            return 1

        print(f"✅ 数据目录: {data_path}")
        print()

        # 初始化 Qlib
        print("🔧 初始化 Qlib...")
        qlib.init(provider_uri=str(data_path), region=REG_CN)
        print("✅ Qlib 初始化成功")
        print()

        # 构建数据集配置
        print("📦 准备数据集...")

        # 这里使用简化的示例配置
        # 实际生产环境需要根据具体需求配置特征和标签
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
                    "train": (args.start_date, "2022-12-31"),
                    "valid": ("2023-01-01", "2023-06-30"),
                    "test": ("2023-07-01", args.end_date),
                },
            },
        }

        print(f"  训练集: {args.start_date} ~ 2022-12-31")
        print(f"  验证集: 2023-01-01 ~ 2023-06-30")
        print(f"  测试集: 2023-07-01 ~ {args.end_date}")
        print()

        # 模型配置
        print(f"🤖 配置 {args.model_type} 模型...")

        if args.model_type == "LGBM":
            model_config = {
                "class": "LGBModel",
                "module_path": "qlib.contrib.model.gbdt",
                "kwargs": {
                    "loss": "mse",
                    "num_leaves": 31,
                    "learning_rate": 0.05,
                    "n_estimators": 100,
                },
            }
        elif args.model_type == "XGBoost":
            model_config = {
                "class": "XGBModel",
                "module_path": "qlib.contrib.model.xgboost",
                "kwargs": {
                    "max_depth": 6,
                    "learning_rate": 0.05,
                    "n_estimators": 100,
                },
            }
        else:
            model_config = {
                "class": "CatBoostModel",
                "module_path": "qlib.contrib.model.catboost_model",
                "kwargs": {
                    "iterations": 100,
                    "learning_rate": 0.05,
                },
            }

        print("✅ 模型配置完成")
        print()

        # 开始训练
        print("🚀 开始训练模型...")
        print("⏳ 这可能需要几分钟时间...")
        print()

        from qlib.workflow import R
        from qlib.workflow.record_temp import SignalRecord
        from qlib.utils import init_instance_by_config

        # 创建数据集
        dataset = init_instance_by_config(dataset_config)

        # 创建模型
        model = init_instance_by_config(model_config)

        # 训练模型
        with R.start(experiment_name=f"{args.model_type}_{args.index}"):
            R.log_params(**{
                "model_type": args.model_type,
                "index": args.index,
                "start_date": args.start_date,
                "end_date": args.end_date,
            })

            # 训练
            model.fit(dataset)

            # 预测（验证集）
            pred = model.predict(dataset)

            # 记录预测结果
            sr = SignalRecord(model, dataset, pred)
            sr.generate()

            print("✅ 模型训练完成!")
            print()

            # 保存模型
            output_path = Path(args.output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            model_name = f"{args.model_type.lower()}_{args.index.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
            model_path = output_path / model_name

            import pickle
            with open(model_path, "wb") as f:
                pickle.dump(model, f)

            print(f"💾 模型已保存: {model_path}")
            print()

            # 显示验证集性能
            print("📊 验证集性能:")
            print(f"  IC (信息系数): {sr.list()[0].get('IC', 'N/A')}")
            print(f"  ICIR (信息比率): {sr.list()[0].get('ICIR', 'N/A')}")
            print()

        print("=" * 70)
        print("✅ 训练完成!")
        print("=" * 70)
        print()
        print("下一步:")
        print(f"  1. 生成预测: ./run_backtest.sh predict --model-name {model_path}")
        print(f"  2. 运行回测: ./run_backtest.sh qlib --predictions pred.pkl")

    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print()
        print("请确保已安装必要依赖:")
        print("  pip install qlib")
        sys.exit(1)

    except Exception as e:
        print(f"❌ 训练失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
