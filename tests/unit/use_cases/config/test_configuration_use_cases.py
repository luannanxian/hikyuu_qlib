"""LoadConfigurationUseCase 和 SaveConfigurationUseCase 单元测试"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock

from domain.ports.config_repository import IConfigRepository
from domain.value_objects.configuration import (
    BacktestConfig,
    DataSourceConfig,
    ModelConfig,
    Configuration,
)
from use_cases.config.load_configuration import LoadConfigurationUseCase
from use_cases.config.save_configuration import SaveConfigurationUseCase


class TestLoadConfiguration:
    """测试加载配置"""

    @pytest.mark.asyncio
    async def test_load_configuration_success(self):
        """测试成功加载配置"""
        # Arrange
        repository_mock = AsyncMock(spec=IConfigRepository)

        mock_data_source = DataSourceConfig(
            hikyuu_path="./data/hikyuu", qlib_path="./data/qlib"
        )
        mock_model = ModelConfig(
            hyperparameters={"learning_rate": 0.01}, default_type="LGBM"
        )
        mock_backtest = BacktestConfig(
            initial_capital=Decimal("100000"),
            commission_rate=Decimal("0.0003"),
            slippage_rate=Decimal("0.0001"),
        )

        repository_mock.get_data_source_config.return_value = mock_data_source
        repository_mock.get_model_config.return_value = mock_model
        repository_mock.get_backtest_config.return_value = mock_backtest

        use_case = LoadConfigurationUseCase(repository=repository_mock)

        # Act
        result = await use_case.execute()

        # Assert
        assert isinstance(result, Configuration)
        assert result.data_source == mock_data_source
        assert result.model == mock_model
        assert result.backtest == mock_backtest
        repository_mock.get_data_source_config.assert_called_once()
        repository_mock.get_backtest_config.assert_called_once()


class TestSaveConfiguration:
    """测试保存配置"""

    @pytest.mark.asyncio
    async def test_save_configuration_success(self):
        """测试成功保存配置"""
        # Arrange
        repository_mock = AsyncMock(spec=IConfigRepository)

        data_source = DataSourceConfig(
            hikyuu_path="./data/hikyuu", qlib_path="./data/qlib"
        )
        model = ModelConfig(hyperparameters={"learning_rate": 0.01}, default_type="LGBM")
        backtest = BacktestConfig(
            initial_capital=Decimal("100000"),
            commission_rate=Decimal("0.0003"),
            slippage_rate=Decimal("0.0001"),
        )
        configuration = Configuration(
            data_source=data_source, model=model, backtest=backtest
        )

        use_case = SaveConfigurationUseCase(repository=repository_mock)

        # Act
        await use_case.execute(configuration=configuration)

        # Assert
        assert repository_mock.save_config.call_count == 3
        repository_mock.save_config.assert_any_call("data_source", data_source)
        repository_mock.save_config.assert_any_call("model:default", model)
        repository_mock.save_config.assert_any_call("backtest", backtest)

    @pytest.mark.asyncio
    async def test_save_configuration_validates(self):
        """测试配置验证"""
        # Arrange
        repository_mock = AsyncMock(spec=IConfigRepository)

        use_case = SaveConfigurationUseCase(repository=repository_mock)

        # Act & Assert: 无效配置应该在创建时失败
        with pytest.raises(ValueError):
            data_source = DataSourceConfig(
                hikyuu_path="./data/hikyuu", qlib_path="./data/qlib"
            )
            model = ModelConfig(
                hyperparameters={"learning_rate": 0.01}, default_type="LGBM"
            )
            invalid_backtest = BacktestConfig(
                initial_capital=Decimal("0"),  # Invalid
                commission_rate=Decimal("0.0003"),
                slippage_rate=Decimal("0.0001"),
            )
            invalid_config = Configuration(
                data_source=data_source, model=model, backtest=invalid_backtest
            )
