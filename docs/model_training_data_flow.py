"""
模型训练数据加载流程 - 设计方案

这个文档展示如何集成数据加载到模型训练流程中
"""

from datetime import datetime
from typing import Optional, List, Any
import pandas as pd

from domain.value_objects.stock_code import StockCode
from domain.value_objects.date_range import DateRange
from domain.value_objects.kline_type import KLineType
from domain.entities.kline_data import KLineData
from domain.entities.model import Model, ModelType


# ============================================================================
# 方案A: train命令集成数据加载（推荐用于快速实验）
# ============================================================================

async def train_with_integrated_data_loading(
    container,
    model_type: ModelType,
    name: str,
    # 数据来源选项1: 从Hikyuu/Qlib实时加载
    stock_code: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    # 数据来源选项2: 从文件加载
    data_file: Optional[str] = None,
    # 数据来源选项3: 从数据库加载
    use_cached_data: bool = False,
):
    """
    集成数据加载的训练流程

    支持三种数据来源:
    1. 实时从Hikyuu/Qlib加载
    2. 从CSV/Parquet文件加载
    3. 从数据库缓存加载
    """

    # 步骤1: 加载训练数据
    training_data = None

    if stock_code and start_date and end_date:
        # 选项1: 实时加载
        print(f"📊 从Hikyuu加载数据: {stock_code} ({start_date} ~ {end_date})")

        load_data_use_case = container.load_stock_data_use_case
        kline_data = await load_data_use_case.execute(
            stock_code=StockCode(stock_code),
            date_range=DateRange(
                start_date=datetime.strptime(start_date, "%Y-%m-%d"),
                end_date=datetime.strptime(end_date, "%Y-%m-%d")
            ),
            kline_type=KLineType.DAY
        )

        # 转换为训练格式
        training_data = convert_kline_to_training_data(kline_data)
        print(f"✅ 加载完成: {len(training_data)} 条记录")

    elif data_file:
        # 选项2: 从文件加载
        print(f"📂 从文件加载数据: {data_file}")
        training_data = load_from_file(data_file)
        print(f"✅ 加载完成: {len(training_data)} 条记录")

    elif use_cached_data:
        # 选项3: 从数据库加载（之前保存的数据）
        print(f"💾 从缓存加载数据...")
        # TODO: 实现数据库缓存读取
        raise NotImplementedError("Database cache not yet implemented")

    else:
        raise ValueError("必须提供数据源: --code + --start + --end 或 --data-file")

    # 步骤2: 创建模型实体
    model = Model(
        model_type=model_type,
        hyperparameters={"learning_rate": 0.01, "max_depth": 6}
    )

    # 步骤3: 训练模型
    print(f"🤖 开始训练 {model_type.value} 模型...")
    train_use_case = container.train_model_use_case
    trained_model = await train_use_case.execute(
        model=model,
        training_data=training_data
    )

    print(f"✅ 训练完成!")
    print(f"   模型ID: {trained_model.id}")
    print(f"   状态: {trained_model.status.value}")
    if trained_model.metrics:
        print(f"   指标: {trained_model.metrics}")

    return trained_model


# ============================================================================
# 方案B: 分离的数据加载和训练（推荐用于生产环境）
# ============================================================================

async def load_and_save_training_data(
    container,
    stock_code: str,
    start_date: str,
    end_date: str,
    output_file: str,
):
    """
    加载数据并保存到文件

    用法:
        data load --code sh600000 --start 2023-01-01 --end 2023-12-31 --output train.csv
    """
    print(f"📊 加载数据: {stock_code} ({start_date} ~ {end_date})")

    # 1. 加载K线数据
    load_data_use_case = container.load_stock_data_use_case
    kline_data = await load_data_use_case.execute(
        stock_code=StockCode(stock_code),
        date_range=DateRange(
            start_date=datetime.strptime(start_date, "%Y-%m-%d"),
            end_date=datetime.strptime(end_date, "%Y-%m-%d")
        ),
        kline_type=KLineType.DAY
    )

    # 2. 转换为DataFrame
    df = kline_data_to_dataframe(kline_data)

    # 3. 特征工程（可选）
    df = add_technical_indicators(df)

    # 4. 保存到文件
    df.to_csv(output_file, index=False)
    print(f"✅ 数据已保存: {output_file} ({len(df)} 条记录)")

    return output_file


async def train_from_saved_data(
    container,
    model_type: ModelType,
    name: str,
    data_file: str,
):
    """
    使用已保存的数据训练模型

    用法:
        model train --type LGBM --name my_model --data train.csv
    """
    print(f"📂 加载训练数据: {data_file}")

    # 1. 从文件加载
    training_data = load_from_file(data_file)
    print(f"✅ 数据加载完成: {len(training_data)} 条记录")

    # 2. 创建模型
    model = Model(
        model_type=model_type,
        hyperparameters={"learning_rate": 0.01}
    )

    # 3. 训练
    print(f"🤖 开始训练...")
    train_use_case = container.train_model_use_case
    trained_model = await train_use_case.execute(
        model=model,
        training_data=training_data
    )

    print(f"✅ 训练完成!")
    return trained_model


# ============================================================================
# 辅助函数
# ============================================================================

def convert_kline_to_training_data(kline_data: List[KLineData]) -> Any:
    """
    将K线数据转换为模型训练格式

    这里需要根据具体模型需求实现，例如:
    - LightGBM: 需要DataFrame格式
    - PyTorch: 需要Tensor格式
    - Sklearn: 需要numpy数组
    """
    # 转换为DataFrame
    df = pd.DataFrame([
        {
            'date': kline.timestamp,
            'open': float(kline.open),
            'high': float(kline.high),
            'low': float(kline.low),
            'close': float(kline.close),
            'volume': kline.volume,
            'amount': float(kline.amount) if kline.amount else 0,
        }
        for kline in kline_data
    ])

    # 添加技术指标作为特征
    df = add_technical_indicators(df)

    # 添加标签（例如：未来收益率）
    df = add_labels(df)

    return df


def kline_data_to_dataframe(kline_data: List[KLineData]) -> pd.DataFrame:
    """K线数据转DataFrame"""
    return pd.DataFrame([
        {
            'timestamp': kline.timestamp,
            'stock_code': kline.stock_code.value,
            'open': float(kline.open),
            'high': float(kline.high),
            'low': float(kline.low),
            'close': float(kline.close),
            'volume': kline.volume,
            'amount': float(kline.amount) if kline.amount else 0,
        }
        for kline in kline_data
    ])


def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    添加技术指标特征

    例如: MA, MACD, RSI, Bollinger Bands等
    """
    # 移动平均线
    df['ma5'] = df['close'].rolling(window=5).mean()
    df['ma10'] = df['close'].rolling(window=10).mean()
    df['ma20'] = df['close'].rolling(window=20).mean()

    # 收益率
    df['return'] = df['close'].pct_change()

    # 波动率
    df['volatility'] = df['return'].rolling(window=20).std()

    # 成交量变化
    df['volume_change'] = df['volume'].pct_change()

    return df


def add_labels(df: pd.DataFrame, horizon: int = 1) -> pd.DataFrame:
    """
    添加训练标签

    Args:
        horizon: 预测未来多少天的收益
    """
    # 未来收益率作为标签
    df['label'] = df['close'].shift(-horizon) / df['close'] - 1

    # 或者分类标签 (涨/跌)
    df['label_class'] = (df['label'] > 0).astype(int)

    return df


def load_from_file(file_path: str) -> Any:
    """从文件加载训练数据"""
    if file_path.endswith('.csv'):
        return pd.read_csv(file_path)
    elif file_path.endswith('.parquet'):
        return pd.read_parquet(file_path)
    else:
        raise ValueError(f"不支持的文件格式: {file_path}")


# ============================================================================
# CLI命令示例
# ============================================================================

"""
方案A使用示例（集成方式）:
---------------------------------

# 直接从Hikyuu加载并训练
./run_cli.sh model train \\
    --type LGBM \\
    --name my_model \\
    --code sh600000 \\
    --start 2023-01-01 \\
    --end 2023-12-31

# 或从文件训练
./run_cli.sh model train \\
    --type LGBM \\
    --name my_model \\
    --data-file train_data.csv


方案B使用示例（分离方式）:
---------------------------------

# 步骤1: 加载并保存数据
./run_cli.sh data load \\
    --code sh600000 \\
    --start 2023-01-01 \\
    --end 2023-12-31 \\
    --output train_data.csv

# 步骤2: 使用保存的数据训练
./run_cli.sh model train \\
    --type LGBM \\
    --name my_model \\
    --data train_data.csv

# 优点: 数据可重用，训练多个模型
./run_cli.sh model train --type MLP --name mlp_model --data train_data.csv
./run_cli.sh model train --type LSTM --name lstm_model --data train_data.csv
"""


# ============================================================================
# 推荐方案：混合方式
# ============================================================================

"""
同时支持两种方式，让用户选择:

1. 快速实验: 一条命令完成（方案A）
   ./run_cli.sh model train --type LGBM --name quick_test --code sh600000 --start 2023-01-01 --end 2023-12-31

2. 生产流程: 数据复用（方案B）
   ./run_cli.sh data load --code sh600000 --start 2020-01-01 --end 2023-12-31 --output prod_data.csv
   ./run_cli.sh model train --type LGBM --name prod_model --data prod_data.csv

3. 批量训练: 预先准备多个数据集
   ./run_cli.sh data load --code sh600000 --start 2020-01-01 --end 2023-12-31 --output sh600000.csv
   ./run_cli.sh data load --code sz000001 --start 2020-01-01 --end 2023-12-31 --output sz000001.csv

   # 对每个股票训练模型
   for stock in sh600000 sz000001; do
       ./run_cli.sh model train --type LGBM --name ${stock}_model --data ${stock}.csv
   done
"""
