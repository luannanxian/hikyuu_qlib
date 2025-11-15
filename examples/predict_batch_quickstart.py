"""
QlibModelTrainerAdapter predict_batch 快速开始示例

演示如何使用新实现的 predict_batch 方法
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime

from adapters.qlib.qlib_model_trainer_adapter import QlibModelTrainerAdapter
from domain.entities.model import Model, ModelType


async def main():
    print("=== QlibModelTrainerAdapter predict_batch 快速开始 ===\n")

    # 1. 初始化适配器
    print("1. 初始化适配器...")
    adapter = QlibModelTrainerAdapter()

    # 2. 创建模型
    print("2. 创建模型...")
    model = Model(
        model_type=ModelType.LGBM,
        hyperparameters={
            "learning_rate": 0.05,
            "num_leaves": 31,
            "verbose": -1
        }
    )
    print(f"   模型类型: {model.model_type.value}")
    print(f"   模型ID: {model.id[:8]}...")

    # 3. 准备训练数据
    print("\n3. 准备训练数据...")
    np.random.seed(42)
    training_data = pd.DataFrame({
        'stock_code': ['sh600000'] * 100 + ['sz000001'] * 100,
        'feature1': np.random.randn(200),
        'feature2': np.random.randn(200),
        'feature3': np.random.randn(200),
        'label_return': np.random.randn(200) * 0.02,
    })
    print(f"   训练样本数: {len(training_data)}")

    # 4. 训练模型
    print("\n4. 训练模型...")
    trained_model = await adapter.train(model, training_data)
    print(f"   训练状态: {trained_model.status.value}")
    print(f"   训练R²: {trained_model.metrics.get('train_r2', 0):.4f}")
    print(f"   测试R²: {trained_model.metrics.get('test_r2', 0):.4f}")

    # 5. 保存模型（可选）
    print("\n5. 保存模型...")
    model_path = "/tmp/hikyuu_qlib_demo_model.pkl"
    try:
        adapter.save_model(trained_model, model_path)
        print(f"   模型已保存: {model_path}")
        print(f"   模型文件路径: {trained_model.file_path}")
    except Exception as e:
        print(f"   保存失败: {e}")

    # 6. 准备预测数据
    print("\n6. 准备预测数据...")
    prediction_data = pd.DataFrame({
        'stock_code': ['sh600000', 'sz000001', 'sh600519'],
        'date': [datetime(2024, 6, 15)] * 3,
        'feature1': [0.5, 0.3, -0.1],
        'feature2': [0.3, -0.2, 0.4],
        'feature3': [-0.2, 0.1, 0.2],
    })
    print(f"   预测样本数: {len(prediction_data)}")

    # 7. 执行批量预测
    print("\n7. 执行批量预测...")
    batch = await adapter.predict_batch(
        model=trained_model,
        input_data=prediction_data,
        prediction_date=datetime(2024, 6, 15, 10, 0, 0)
    )
    print(f"   批次ID: {batch.id[:8]}...")
    print(f"   预测数量: {batch.size()}")
    print(f"   平均置信度: {batch.average_confidence():.2%}")
    print(f"   生成时间: {batch.generated_at}")

    # 8. 查看预测结果
    print("\n8. 预测结果详情:")
    print("-" * 80)
    for i, pred in enumerate(batch.predictions, 1):
        print(f"   预测 #{i}:")
        print(f"     股票代码: {pred.stock_code.value}")
        print(f"     时间戳: {pred.timestamp}")
        print(f"     预测值: {pred.predicted_value:.4f}")
        print(f"     置信度: {pred.confidence:.2%}")
        print(f"     预测ID: {pred.id[:8]}...")
        print()

    # 9. 转换为 DataFrame
    print("9. 转换为 DataFrame:")
    df = batch.to_dataframe()
    print(df[['stock_code', 'predicted_value', 'confidence']])

    # 10. 测试从文件加载模型预测（如果模型已保存）
    if trained_model.file_path:
        print("\n10. 从文件加载模型进行预测...")
        new_model = Model(
            model_type=ModelType.LGBM,
            hyperparameters={},
            file_path=trained_model.file_path
        )

        # 创建新的适配器实例（模拟新进程）
        new_adapter = QlibModelTrainerAdapter()

        # 使用文件路径的模型进行预测
        batch2 = await new_adapter.predict_batch(
            model=new_model,
            input_data=prediction_data
        )
        print(f"   从文件加载预测成功!")
        print(f"   批次大小: {batch2.size()}")

    print("\n=== 演示完成 ===")


if __name__ == "__main__":
    asyncio.run(main())
