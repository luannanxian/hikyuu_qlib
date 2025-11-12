"""LoadConfigurationUseCase 和 SaveConfigurationUseCase 单元测试"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock

from domain.ports.config_repository import IConfigRepository
from domain.value_objects.configuration import BacktestConfig
from use_cases.config.load_configuration import LoadConfigurationUseCase
from use_cases.config.save_configuration import SaveConfigurationUseCase


class TestLoadConfiguration:
    """测试加载配置"""

    @pytest.mark.asyncio
    async def test_load_configuration_success(self):
        """测试成功加载配置"""
        # Arrange
        repository_mock = AsyncMock(spec=IConfigRepository)

        mock_config = BacktestConfig(
            initial_capital=Decimal("100000"),
            commission_rate=Decimal("0.0003"),
            slippage_rate=Decimal("0.0001"),
        )
        repository_mock.get_backtest_config.return_value = mock_config

        use_case = LoadConfigurationUseCase(repository=repository_mock)

        # Act
        result = await use_case.execute()

        # Assert
        assert result == mock_config
        repository_mock.get_backtest_config.assert_called_once()


class TestSaveConfiguration:
    """测试保存配置"""

    @pytest.mark.asyncio
    async def test_save_configuration_success(self):
        """测试成功保存配置"""
        # Arrange
        repository_mock = AsyncMock(spec=IConfigRepository)

        config = BacktestConfig(
            initial_capital=Decimal("100000"),
            commission_rate=Decimal("0.0003"),
            slippage_rate=Decimal("0.0001"),
        )

        use_case = SaveConfigurationUseCase(repository=repository_mock)

        # Act
        await use_case.execute(config=config)

        # Assert
        repository_mock.save_config.assert_called_once_with("backtest", config)

    @pytest.mark.asyncio
    async def test_save_configuration_validates(self):
        """测试配置验证"""
        # Arrange
        repository_mock = AsyncMock(spec=IConfigRepository)

        use_case = SaveConfigurationUseCase(repository=repository_mock)

        # Act & Assert: 无效配置应该在创建时失败
        with pytest.raises(ValueError):
            invalid_config = BacktestConfig(
                initial_capital=Decimal("0"),  # Invalid
                commission_rate=Decimal("0.0003"),
                slippage_rate=Decimal("0.0001"),
            )
            await use_case.execute(config=invalid_config)
