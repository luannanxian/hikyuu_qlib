"""训练配置数据类

用于封装模型训练的配置参数，减少函数参数数量。
"""

from dataclasses import dataclass


@dataclass
class TrainingConfig:
    """模型训练配置

    封装模型训练所需的所有配置参数。
    """

    # 基本配置
    model_type: str
    name: str

    # 数据源配置（二选一）
    training_data_path: str | None = None  # 分离式：直接提供数据文件
    stock_code: str | None = None  # 集成式：从股票代码加载

    # 日期范围（集成式必需）
    start_date: str | None = None
    end_date: str | None = None

    # K线类型
    kline_type: str = "DAY"

    # 超参数配置（优先级递增）
    config_file: str | None = None  # 配置文件路径
    hyperparameters_json: str | None = None  # JSON 字符串
    param_list: tuple[str, ...] = ()  # 单个参数列表

    def validate(self) -> None:
        """验证配置的有效性

        Raises:
            ValueError: 如果配置无效
        """
        # 检查数据源
        has_data_path = self.training_data_path is not None
        has_stock_code = self.stock_code is not None

        if not has_data_path and not has_stock_code:
            raise ValueError("必须提供 training_data_path 或 stock_code 之一")

        if has_data_path and has_stock_code:
            raise ValueError("training_data_path 和 stock_code 不能同时提供")

        # 如果使用集成式，检查日期范围
        if has_stock_code:
            if not self.start_date or not self.end_date:
                raise ValueError("使用 stock_code 时必须提供 start_date 和 end_date")

    @property
    def is_integrated_approach(self) -> bool:
        """是否使用集成式数据加载"""
        return self.stock_code is not None

    @property
    def is_separated_approach(self) -> bool:
        """是否使用分离式数据加载"""
        return self.training_data_path is not None


@dataclass
class BatchTrainingConfig:
    """批量训练配置

    用于指数成分股批量训练的配置。
    """

    # 基本配置
    model_type: str
    index_code: str

    # 日期范围
    start_date: str
    end_date: str

    # K线类型
    kline_type: str = "DAY"

    # 超参数配置
    config_file: str | None = None
    hyperparameters_json: str | None = None
    param_list: tuple[str, ...] = ()

    # 批量处理配置
    batch_size: int = 5
    max_workers: int = 4
    save_path: str | None = None

    def validate(self) -> None:
        """验证配置的有效性

        Raises:
            ValueError: 如果配置无效
        """
        if self.batch_size < 1:
            raise ValueError("batch_size 必须大于 0")

        if self.max_workers < 1:
            raise ValueError("max_workers 必须大于 0")
