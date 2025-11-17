"""Configuration Value Objects 单元测试"""

import tempfile
from decimal import Decimal
from pathlib import Path

import pytest

from domain.value_objects.configuration import (
    BacktestConfig,
    DataSourceConfig,
    ModelConfig,
)


class TestDataSourceConfig:
    """测试 DataSourceConfig"""

    def test_valid_hikyuu_config(self, tmp_path):
        """测试有效的Hikyuu配置"""
        # 使用 tmp_path fixture 提供的临时目录
        config = DataSourceConfig(provider="hikyuu", data_path=str(tmp_path))
        assert config.provider == "hikyuu"
        assert config.data_path == str(tmp_path)

    def test_valid_qlib_config(self, tmp_path):
        """测试有效的Qlib配置"""
        config = DataSourceConfig(provider="qlib", data_path=str(tmp_path))
        assert config.provider == "qlib"

    def test_invalid_provider(self, tmp_path):
        """测试无效的提供商"""
        with pytest.raises(ValueError, match="Invalid provider"):
            DataSourceConfig(provider="invalid", data_path=str(tmp_path))

    def test_invalid_path(self):
        """测试不存在的路径"""
        with pytest.raises(ValueError, match="Data path does not exist"):
            DataSourceConfig(provider="hikyuu", data_path="/nonexistent/path")


class TestModelConfig:
    """测试 ModelConfig"""

    def test_valid_model_config(self):
        """测试有效的模型配置"""
        config = ModelConfig(
            model_type="LGBM",
            hyperparameters={"n_estimators": 100, "learning_rate": 0.1},
        )
        assert config.model_type == "LGBM"
        assert config.hyperparameters["n_estimators"] == 100

    def test_invalid_model_type(self):
        """测试无效的模型类型"""
        with pytest.raises(ValueError, match="Invalid model type"):
            ModelConfig(model_type="INVALID", hyperparameters={})


class TestBacktestConfig:
    """测试 BacktestConfig"""

    def test_valid_backtest_config(self):
        """测试有效的回测配置"""
        config = BacktestConfig(
            initial_capital=Decimal(100000),
            commission_rate=Decimal("0.001"),
            slippage_rate=Decimal("0.001"),
        )
        assert config.initial_capital == Decimal(100000)
        assert config.commission_rate == Decimal("0.001")

    def test_invalid_initial_capital(self):
        """测试无效的初始资金"""
        with pytest.raises(ValueError, match="initial_capital must be > 0"):
            BacktestConfig(
                initial_capital=Decimal(0),
                commission_rate=Decimal("0.001"),
                slippage_rate=Decimal("0.001"),
            )

    def test_invalid_commission_rate(self):
        """测试无效的手续费率"""
        with pytest.raises(ValueError, match="commission_rate must be between"):
            BacktestConfig(
                initial_capital=Decimal(100000),
                commission_rate=Decimal("0.2"),  # > 0.1
                slippage_rate=Decimal("0.001"),
            )

    def test_invalid_slippage_rate(self):
        """测试无效的滑点率"""
        with pytest.raises(ValueError, match="slippage_rate must be between"):
            BacktestConfig(
                initial_capital=Decimal(100000),
                commission_rate=Decimal("0.001"),
                slippage_rate=Decimal("-0.001"),  # < 0
            )
