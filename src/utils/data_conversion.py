"""
数据转换工具模块

提供K线数据到训练数据格式的转换功能
"""

from typing import List, Any
from decimal import Decimal
import pandas as pd

from domain.entities.kline_data import KLineData


def convert_kline_to_training_data(
    kline_data: List[KLineData],
    add_features: bool = True,
    add_labels: bool = True,
    label_horizon: int = 1,
) -> pd.DataFrame:
    """
    将K线数据转换为模型训练格式

    Args:
        kline_data: K线数据列表
        add_features: 是否添加技术指标特征
        add_labels: 是否添加训练标签
        label_horizon: 预测未来多少天的收益

    Returns:
        pd.DataFrame: 训练数据（包含特征和标签）
    """
    if not kline_data:
        return pd.DataFrame()

    # 1. 转换为DataFrame基础格式
    df = kline_data_to_dataframe(kline_data)

    # 2. 添加技术指标特征（可选）
    if add_features:
        df = add_technical_indicators(df)

    # 3. 添加训练标签（可选）
    if add_labels:
        df = add_training_labels(df, horizon=label_horizon)

    # 4. 智能处理NaN：优先保留数据，而不是删除
    if add_labels:
        # 对于标签，只删除最后 horizon 行（它们的标签必然是 NaN，无法训练）
        df = df.iloc[:-label_horizon] if len(df) > label_horizon else df

        # 如果还有标签为NaN的（不应该发生，但防御性编程），删除它们
        label_cols = ["label_return", "label_direction", "label_multiclass"]
        existing_label_cols = [col for col in label_cols if col in df.columns]
        if existing_label_cols:
            df = df.dropna(subset=existing_label_cols)

    # 对于特征列的NaN，先前向填充，再后向填充，最后填充0
    df = df.ffill().bfill().fillna(0)

    return df


def kline_data_to_dataframe(kline_data: List[KLineData]) -> pd.DataFrame:
    """
    将K线数据转换为DataFrame基础格式

    Args:
        kline_data: K线数据列表

    Returns:
        pd.DataFrame: 包含基础OHLCV数据的DataFrame
    """
    records = []
    for kline in kline_data:
        record = {
            "timestamp": kline.timestamp,
            "stock_code": kline.stock_code.value,
            "open": float(kline.open),
            "high": float(kline.high),
            "low": float(kline.low),
            "close": float(kline.close),
            "volume": kline.volume,
            "amount": float(kline.amount) if kline.amount else 0.0,
        }
        records.append(record)

    df = pd.DataFrame(records)

    # 设置timestamp为索引（方便时间序列操作）
    if not df.empty:
        df = df.set_index("timestamp")
        df = df.sort_index()

    return df


def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    添加技术指标特征

    包括：
    - 移动平均线 (MA5, MA10, MA20, MA60)
    - 收益率 (return)
    - 波动率 (volatility)
    - 成交量变化率 (volume_change)
    - 价格位置 (price_position)
    - 振幅 (amplitude)

    Args:
        df: 包含OHLCV数据的DataFrame

    Returns:
        pd.DataFrame: 添加了技术指标列的DataFrame
    """
    df = df.copy()

    # 移动平均线
    df["ma5"] = df["close"].rolling(window=5).mean()
    df["ma10"] = df["close"].rolling(window=10).mean()
    df["ma20"] = df["close"].rolling(window=20).mean()
    df["ma60"] = df["close"].rolling(window=60).mean()

    # MA差值特征
    df["ma5_ma10_diff"] = df["ma5"] - df["ma10"]
    df["ma10_ma20_diff"] = df["ma10"] - df["ma20"]

    # 收益率
    df["return"] = df["close"].pct_change()
    df["return_5d"] = df["close"].pct_change(periods=5)
    df["return_10d"] = df["close"].pct_change(periods=10)

    # 波动率（滚动标准差）
    df["volatility"] = df["return"].rolling(window=20).std()

    # 成交量变化
    df["volume_change"] = df["volume"].pct_change()
    df["volume_ma5"] = df["volume"].rolling(window=5).mean()

    # 价格位置（收盘价在最近20日价格区间中的位置）
    df["high_20d"] = df["high"].rolling(window=20).max()
    df["low_20d"] = df["low"].rolling(window=20).min()
    df["price_position"] = (df["close"] - df["low_20d"]) / (
        df["high_20d"] - df["low_20d"] + 1e-8
    )

    # 振幅
    df["amplitude"] = (df["high"] - df["low"]) / df["close"]

    # 量价关系
    df["volume_price_corr"] = (
        df["close"]
        .rolling(window=20)
        .corr(df["volume"].rolling(window=20).mean())
    )

    return df


def add_training_labels(df: pd.DataFrame, horizon: int = 1) -> pd.DataFrame:
    """
    添加训练标签

    Args:
        df: 包含价格数据的DataFrame
        horizon: 预测未来多少天的收益

    Returns:
        pd.DataFrame: 添加了标签列的DataFrame
    """
    df = df.copy()

    # 1. 连续标签：未来收益率
    df["label_return"] = df["close"].shift(-horizon) / df["close"] - 1

    # 2. 分类标签：涨/跌
    df["label_direction"] = (df["label_return"] > 0).astype(int)

    # 3. 多分类标签：大涨/小涨/小跌/大跌
    # 使用20%分位数作为阈值
    if len(df) > 0:
        q80 = df["label_return"].quantile(0.8)
        q20 = df["label_return"].quantile(0.2)

        df["label_multiclass"] = 1  # 默认为小涨
        df.loc[df["label_return"] > q80, "label_multiclass"] = 2  # 大涨
        df.loc[df["label_return"] < 0, "label_multiclass"] = 0  # 小跌
        df.loc[df["label_return"] < q20, "label_multiclass"] = -1  # 大跌

    return df


def load_from_file(file_path: str) -> pd.DataFrame:
    """
    从文件加载训练数据

    支持的格式:
    - CSV (.csv)
    - Parquet (.parquet)

    Args:
        file_path: 文件路径

    Returns:
        pd.DataFrame: 训练数据

    Raises:
        ValueError: 不支持的文件格式
    """
    if file_path.endswith(".csv"):
        df = pd.read_csv(file_path)
        # 如果有timestamp列，转换为datetime并设置为索引
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.set_index("timestamp")
        return df
    elif file_path.endswith(".parquet"):
        df = pd.read_parquet(file_path)
        return df
    else:
        raise ValueError(f"Unsupported file format: {file_path}")


def save_to_file(df: pd.DataFrame, file_path: str) -> None:
    """
    保存训练数据到文件

    支持的格式:
    - CSV (.csv)
    - Parquet (.parquet)

    Args:
        df: 训练数据
        file_path: 文件路径

    Raises:
        ValueError: 不支持的文件格式
    """
    if file_path.endswith(".csv"):
        df.to_csv(file_path)
    elif file_path.endswith(".parquet"):
        df.to_parquet(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_path}")


def prepare_features_and_labels(
    df: pd.DataFrame, feature_cols: List[str] = None, label_col: str = "label_return"
) -> tuple[pd.DataFrame, pd.Series]:
    """
    准备特征和标签用于模型训练

    Args:
        df: 训练数据
        feature_cols: 特征列名列表（如果为None，自动选择所有非标签列）
        label_col: 标签列名

    Returns:
        tuple[pd.DataFrame, pd.Series]: (特征DataFrame, 标签Series)
    """
    df = df.copy()

    # 如果未指定特征列，使用除标签外的所有数值列
    if feature_cols is None:
        # 排除标签相关列
        exclude_cols = [
            "label_return",
            "label_direction",
            "label_multiclass",
            "stock_code",
        ]
        feature_cols = [
            col for col in df.columns if col not in exclude_cols and df[col].dtype in ["float64", "int64"]
        ]

    X = df[feature_cols]
    y = df[label_col]

    return X, y
