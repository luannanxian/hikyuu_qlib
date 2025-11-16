"""
GeneratePredictionsUseCase - 生成预测用例

UC-003: Generate Predictions (生成预测)
"""

import pickle
from datetime import datetime
from pathlib import Path


from domain.entities.model import Model
from domain.entities.prediction import Prediction, PredictionBatch
from domain.ports.model_repository import IModelRepository
from domain.ports.stock_data_provider import IStockDataProvider
from domain.value_objects.date_range import DateRange
from domain.value_objects.kline_type import KLineType
from domain.value_objects.stock_code import StockCode
from utils.data_conversion import convert_kline_to_training_data


class GeneratePredictionsUseCase:
    """
    生成预测用例

    依赖注入:
    - repository: IModelRepository (模型仓储接口)
    - data_provider: IStockDataProvider (数据提供者接口)

    职责:
    - 从仓储加载模型
    - 验证模型状态是否可用于预测
    - 加载预测数据
    - 生成预测结果
    - 保存预测文件（pred.pkl）
    """

    def __init__(
        self,
        repository: IModelRepository,
        data_provider: IStockDataProvider,
    ):
        """
        初始化用例

        Args:
            repository: 模型仓储接口实现
            data_provider: 数据提供者接口实现
        """
        self.repository = repository
        self.data_provider = data_provider

    async def execute(
        self,
        model_id: str,
        stock_codes: list[StockCode],
        date_range: DateRange,
        kline_type: KLineType = KLineType.DAY,
        output_path: str | None = None,
        output_format: str = "pkl",
        save_details: bool = True,
    ) -> PredictionBatch:
        """
        执行预测生成

        Args:
            model_id: 模型ID
            stock_codes: 股票代码列表
            date_range: 预测日期范围
            kline_type: K线类型
            output_path: 输出文件路径（可选）
            output_format: 输出格式 (pkl | csv | parquet)
            save_details: 是否保存详细信息

        Returns:
            PredictionBatch: 预测批次聚合

        Raises:
            ValueError: 模型未找到或模型未就绪
            Exception: 预测生成失败时传播异常
        """
        # 1. 从仓储加载模型
        model = await self.repository.find_by_id(model_id)
        if model is None:
            raise ValueError(f"Model with id {model_id} not found")

        # 2. 验证模型是否已训练
        if not model.is_trained():
            raise ValueError(
                f"Model {model_id} is not trained. "
                f"Status: {model.status.value}",
            )

        if model.trained_model is None:
            raise ValueError(f"Model {model_id} has no trained model object")

        # 3. 收集所有股票的预测数据
        all_predictions: list[Prediction] = []
        failed_stocks: list[str] = []

        print(f"\n开始为 {len(stock_codes)} 只股票生成预测...")
        print(f"日期范围: {date_range.start_date.date()} ~ {date_range.end_date.date()}")
        print("=" * 70)

        for idx, stock_code in enumerate(stock_codes, 1):
            try:
                print(f"\n[{idx}/{len(stock_codes)}] 处理 {stock_code.value}...")

                # 加载K线数据
                kline_data = await self.data_provider.load_stock_data(
                    stock_code=stock_code,
                    date_range=date_range,
                    kline_type=kline_type,
                )

                if not kline_data:
                    print("  ⚠️  无可用数据，跳过")
                    failed_stocks.append(stock_code.value)
                    continue

                print(f"  ✓ 加载了 {len(kline_data)} 条K线数据")

                # 转换为特征数据（不添加标签，因为是预测未来）
                feature_data = convert_kline_to_training_data(
                    kline_data,
                    add_features=True,
                    add_labels=False,  # 预测时不需要标签
                    label_horizon=1,
                )

                if feature_data.empty:
                    print("  ⚠️  特征数据为空，跳过")
                    failed_stocks.append(stock_code.value)
                    continue

                print(f"  ✓ 生成了 {len(feature_data)} 条特征记录")

                # 准备特征（排除非特征列）
                exclude_cols = ["stock_code", "label_return", "label_direction", "label_multiclass"]
                feature_cols = [col for col in feature_data.columns if col not in exclude_cols]
                X = feature_data[feature_cols]

                # 使用模型预测
                predictions_array = model.trained_model.predict(X)

                # 创建预测对象
                for i, (timestamp, row) in enumerate(X.iterrows()):
                    prediction = Prediction(
                        stock_code=stock_code,
                        timestamp=timestamp,
                        predicted_value=float(predictions_array[i]),
                        confidence=None,  # LightGBM默认不提供置信度
                        model_id=model.id,
                    )
                    all_predictions.append(prediction)

                print(f"  ✓ 生成了 {len(predictions_array)} 个预测值")

            except Exception as e:
                print(f"  ✗ 预测失败: {e!s}")
                failed_stocks.append(stock_code.value)
                continue

        # 4. 创建预测批次
        prediction_batch = PredictionBatch(
            model_id=model.id,
            predictions=all_predictions,
            generated_at=datetime.now(),
        )

        # 5. 打印汇总
        print("\n" + "=" * 70)
        print("预测生成完成!")
        print(f"  成功: {len(stock_codes) - len(failed_stocks)}/{len(stock_codes)} 只股票")
        print(f"  总预测数: {len(all_predictions)} 条")
        if failed_stocks:
            print(f"  失败股票: {', '.join(failed_stocks[:10])}")
            if len(failed_stocks) > 10:
                print(f"            ... 还有 {len(failed_stocks) - 10} 只")

        # 6. 保存预测结果（如果指定了输出路径）
        if output_path:
            self._save_predictions(
                prediction_batch=prediction_batch,
                output_path=output_path,
                output_format=output_format,
                save_details=save_details,
                model=model,
            )

        return prediction_batch

    def _save_predictions(
        self,
        prediction_batch: PredictionBatch,
        output_path: str,
        output_format: str,
        save_details: bool,
        model: Model | None = None,
    ):
        """
        保存预测结果到文件

        Args:
            prediction_batch: 预测批次
            output_path: 输出路径
            output_format: 输出格式
            save_details: 是否保存详细信息
            model: 模型对象（用于保存额外信息）
        """
        # 创建输出目录
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # 转换为DataFrame
        df = prediction_batch.to_dataframe()

        # 保存主预测文件
        if output_format == "pkl":
            # Qlib标准格式：MultiIndex DataFrame (instrument, datetime)
            df_qlib = df.set_index(["stock_code", "timestamp"])
            df_qlib = df_qlib.rename(columns={"predicted_value": "score"})
            df_qlib.to_pickle(output_path)
            print(f"\n✓ 预测结果已保存: {output_path} (Qlib格式)")

        elif output_format == "csv":
            df.to_csv(output_path, index=False)
            print(f"\n✓ 预测结果已保存: {output_path}")

        elif output_format == "parquet":
            df.to_parquet(output_path, index=False)
            print(f"\n✓ 预测结果已保存: {output_path}")

        else:
            raise ValueError(f"Unsupported output format: {output_format}")

        # 保存详细信息（如果需要）
        if save_details and model:
            details_path = output_file.with_name(output_file.stem + "_details.pkl")

            details = {
                "model_id": model.id,
                "model_type": model.model_type.value,
                "hyperparameters": model.hyperparameters,
                "metrics": model.metrics,
                "prediction_count": len(prediction_batch.predictions),
                "stock_count": len(set(p.stock_code.value for p in prediction_batch.predictions)),
                "generated_at": prediction_batch.generated_at,
            }

            # 添加特征重要度（如果模型支持）
            if hasattr(model.trained_model, "feature_importances_"):
                details["feature_importance"] = model.trained_model.feature_importances_.tolist()

            if hasattr(model.trained_model, "feature_name_"):
                details["feature_names"] = model.trained_model.feature_name_

            with open(details_path, "wb") as f:
                pickle.dump(details, f)

            print(f"✓ 详细信息已保存: {details_path}")
