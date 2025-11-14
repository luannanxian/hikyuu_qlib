"""
Tests for data conversion utilities.
"""

from datetime import datetime
from decimal import Decimal

import pandas as pd
import pytest

from domain.entities.kline_data import KLineData
from domain.value_objects.stock_code import StockCode
from domain.value_objects.kline_type import KLineType
from utils.data_conversion import (
    convert_kline_to_training_data,
    kline_data_to_dataframe,
    add_technical_indicators,
    add_training_labels,
    load_from_file,
    save_to_file,
    prepare_features_and_labels,
)


@pytest.fixture
def sample_kline_data():
    """Create sample K-line data for testing."""
    from datetime import timedelta

    data = []
    base_date = datetime(2023, 1, 2)
    for i in range(100):
        kline = KLineData(
            stock_code=StockCode("sh600000"),
            timestamp=base_date + timedelta(days=i),
            kline_type=KLineType.DAY,
            open=Decimal("30.0") + Decimal(str(i * 0.1)),
            high=Decimal("31.0") + Decimal(str(i * 0.1)),
            low=Decimal("29.0") + Decimal(str(i * 0.1)),
            close=Decimal("30.5") + Decimal(str(i * 0.1)),
            volume=1000000 + i * 10000,
            amount=Decimal("30500000") + Decimal(str(i * 100000)),
        )
        data.append(kline)
    return data


class TestKLineDataToDataFrame:
    """Tests for kline_data_to_dataframe function."""

    def test_convert_basic_fields(self, sample_kline_data):
        """Test conversion of basic OHLCV fields."""
        df = kline_data_to_dataframe(sample_kline_data)

        assert len(df) == 100
        assert "stock_code" in df.columns
        assert "open" in df.columns
        assert "high" in df.columns
        assert "low" in df.columns
        assert "close" in df.columns
        assert "volume" in df.columns
        assert "amount" in df.columns

    def test_timestamp_as_index(self, sample_kline_data):
        """Test that timestamp is set as index."""
        df = kline_data_to_dataframe(sample_kline_data)

        assert df.index.name == "timestamp"
        assert isinstance(df.index[0], datetime)

    def test_sorted_by_timestamp(self, sample_kline_data):
        """Test that data is sorted by timestamp."""
        df = kline_data_to_dataframe(sample_kline_data)

        timestamps = df.index.tolist()
        assert timestamps == sorted(timestamps)

    def test_empty_list(self):
        """Test conversion of empty list."""
        df = kline_data_to_dataframe([])

        assert len(df) == 0


class TestAddTechnicalIndicators:
    """Tests for add_technical_indicators function."""

    def test_add_moving_averages(self, sample_kline_data):
        """Test that moving averages are added."""
        df = kline_data_to_dataframe(sample_kline_data)
        df = add_technical_indicators(df)

        assert "ma5" in df.columns
        assert "ma10" in df.columns
        assert "ma20" in df.columns
        assert "ma60" in df.columns

    def test_add_returns(self, sample_kline_data):
        """Test that return features are added."""
        df = kline_data_to_dataframe(sample_kline_data)
        df = add_technical_indicators(df)

        assert "return" in df.columns
        assert "return_5d" in df.columns
        assert "return_10d" in df.columns

    def test_add_volatility(self, sample_kline_data):
        """Test that volatility is calculated."""
        df = kline_data_to_dataframe(sample_kline_data)
        df = add_technical_indicators(df)

        assert "volatility" in df.columns

    def test_add_volume_features(self, sample_kline_data):
        """Test that volume features are added."""
        df = kline_data_to_dataframe(sample_kline_data)
        df = add_technical_indicators(df)

        assert "volume_change" in df.columns
        assert "volume_ma5" in df.columns

    def test_add_price_position(self, sample_kline_data):
        """Test that price position is calculated."""
        df = kline_data_to_dataframe(sample_kline_data)
        df = add_technical_indicators(df)

        assert "price_position" in df.columns
        assert "high_20d" in df.columns
        assert "low_20d" in df.columns


class TestAddTrainingLabels:
    """Tests for add_training_labels function."""

    def test_add_return_label(self, sample_kline_data):
        """Test that return label is added."""
        df = kline_data_to_dataframe(sample_kline_data)
        df = add_training_labels(df, horizon=1)

        assert "label_return" in df.columns

    def test_add_direction_label(self, sample_kline_data):
        """Test that direction label is added."""
        df = kline_data_to_dataframe(sample_kline_data)
        df = add_training_labels(df, horizon=1)

        assert "label_direction" in df.columns
        assert df["label_direction"].dtype == int

    def test_add_multiclass_label(self, sample_kline_data):
        """Test that multiclass label is added."""
        df = kline_data_to_dataframe(sample_kline_data)
        df = add_training_labels(df, horizon=1)

        assert "label_multiclass" in df.columns

    def test_label_horizon(self, sample_kline_data):
        """Test different label horizons."""
        df = kline_data_to_dataframe(sample_kline_data)

        df_1d = add_training_labels(df, horizon=1)
        df_5d = add_training_labels(df, horizon=5)

        # Labels should be different for different horizons
        assert not df_1d["label_return"].equals(df_5d["label_return"])


class TestConvertKlineToTrainingData:
    """Tests for convert_kline_to_training_data function."""

    def test_basic_conversion(self, sample_kline_data):
        """Test basic conversion without features or labels."""
        df = convert_kline_to_training_data(
            sample_kline_data, add_features=False, add_labels=False
        )

        assert len(df) > 0
        assert "close" in df.columns

    def test_with_features(self, sample_kline_data):
        """Test conversion with technical indicators."""
        df = convert_kline_to_training_data(
            sample_kline_data, add_features=True, add_labels=False
        )

        assert "ma5" in df.columns
        assert "return" in df.columns

    def test_with_labels(self, sample_kline_data):
        """Test conversion with training labels."""
        df = convert_kline_to_training_data(
            sample_kline_data, add_features=False, add_labels=True
        )

        assert "label_return" in df.columns
        assert "label_direction" in df.columns

    def test_with_features_and_labels(self, sample_kline_data):
        """Test full conversion with both features and labels."""
        df = convert_kline_to_training_data(
            sample_kline_data, add_features=True, add_labels=True
        )

        assert len(df) > 0
        assert "ma5" in df.columns
        assert "label_return" in df.columns

    def test_nan_removal(self, sample_kline_data):
        """Test that NaN values are removed."""
        df = convert_kline_to_training_data(
            sample_kline_data, add_features=True, add_labels=True
        )

        # Should have fewer rows due to NaN removal from indicators
        assert len(df) < len(sample_kline_data)

        # Should have no NaN values
        assert df.isna().sum().sum() == 0

    def test_empty_input(self):
        """Test with empty input."""
        df = convert_kline_to_training_data([])

        assert len(df) == 0


class TestFileSaveLoad:
    """Tests for file save/load functions."""

    def test_save_load_csv(self, sample_kline_data, tmp_path):
        """Test saving and loading CSV files."""
        df = convert_kline_to_training_data(sample_kline_data)

        file_path = tmp_path / "test_data.csv"
        save_to_file(df, str(file_path))

        assert file_path.exists()

        loaded_df = load_from_file(str(file_path))
        assert len(loaded_df) == len(df)

    def test_save_load_parquet(self, sample_kline_data, tmp_path):
        """Test saving and loading Parquet files."""
        df = convert_kline_to_training_data(sample_kline_data)

        file_path = tmp_path / "test_data.parquet"
        save_to_file(df, str(file_path))

        assert file_path.exists()

        loaded_df = load_from_file(str(file_path))
        assert len(loaded_df) == len(df)

    def test_unsupported_format_save(self, sample_kline_data, tmp_path):
        """Test error for unsupported file format in save."""
        df = convert_kline_to_training_data(sample_kline_data)

        file_path = tmp_path / "test_data.txt"

        with pytest.raises(ValueError, match="Unsupported file format"):
            save_to_file(df, str(file_path))

    def test_unsupported_format_load(self, tmp_path):
        """Test error for unsupported file format in load."""
        file_path = tmp_path / "test_data.txt"
        file_path.write_text("test")

        with pytest.raises(ValueError, match="Unsupported file format"):
            load_from_file(str(file_path))


class TestPrepareFeaturesAndLabels:
    """Tests for prepare_features_and_labels function."""

    def test_automatic_feature_selection(self, sample_kline_data):
        """Test automatic feature column selection."""
        df = convert_kline_to_training_data(
            sample_kline_data, add_features=True, add_labels=True
        )

        X, y = prepare_features_and_labels(df)

        # Should exclude label columns and stock_code
        assert "label_return" not in X.columns
        assert "label_direction" not in X.columns
        assert "stock_code" not in X.columns

        # Should include features
        assert "ma5" in X.columns
        assert "close" in X.columns

    def test_manual_feature_selection(self, sample_kline_data):
        """Test manual feature column selection."""
        df = convert_kline_to_training_data(
            sample_kline_data, add_features=True, add_labels=True
        )

        feature_cols = ["close", "volume", "ma5"]
        X, y = prepare_features_and_labels(df, feature_cols=feature_cols)

        assert list(X.columns) == feature_cols

    def test_label_selection(self, sample_kline_data):
        """Test different label column selection."""
        df = convert_kline_to_training_data(
            sample_kline_data, add_features=True, add_labels=True
        )

        X, y_return = prepare_features_and_labels(df, label_col="label_return")
        X, y_direction = prepare_features_and_labels(df, label_col="label_direction")

        assert not y_return.equals(y_direction)
        assert y_return.name == "label_return"
        assert y_direction.name == "label_direction"

    def test_output_types(self, sample_kline_data):
        """Test output types."""
        df = convert_kline_to_training_data(
            sample_kline_data, add_features=True, add_labels=True
        )

        X, y = prepare_features_and_labels(df)

        assert isinstance(X, pd.DataFrame)
        assert isinstance(y, pd.Series)
