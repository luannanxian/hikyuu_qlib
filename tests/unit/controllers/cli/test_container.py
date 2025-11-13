"""
Tests for CLI dependency injection container.

Tests:
- Container creation
- Service registration
- Service resolution
- Singleton pattern
"""

import pytest
from unittest.mock import patch, MagicMock

from controllers.cli.di.container import Container
from infrastructure.config.settings import Settings


class TestContainer:
    """Test CLI dependency injection container."""

    def test_container_creation(self):
        """Test container creation with default settings."""
        # Arrange & Act
        container = Container()

        # Assert
        assert container is not None
        assert isinstance(container.settings, Settings)

    def test_container_creation_with_custom_settings(self):
        """Test container creation with custom settings."""
        # Arrange
        custom_settings = Settings(
            APP_NAME="Test App",
            ENVIRONMENT="test",
            LOG_LEVEL="DEBUG",
        )

        # Act
        container = Container(settings=custom_settings)

        # Assert
        assert container.settings == custom_settings
        assert container.settings.APP_NAME == "Test App"
        assert container.settings.ENVIRONMENT == "test"

    def test_container_provides_load_stock_data_use_case(self):
        """Test container provides LoadStockDataUseCase."""
        # Arrange
        container = Container()

        # Act
        use_case = container.load_stock_data_use_case

        # Assert
        assert use_case is not None
        from use_cases.data.load_stock_data import LoadStockDataUseCase

        assert isinstance(use_case, LoadStockDataUseCase)

    def test_container_provides_train_model_use_case(self):
        """Test container provides TrainModelUseCase."""
        # Arrange
        container = Container()

        # Act
        use_case = container.train_model_use_case

        # Assert
        assert use_case is not None
        from use_cases.model.train_model import TrainModelUseCase

        assert isinstance(use_case, TrainModelUseCase)

    @patch("adapters.hikyuu.hikyuu_backtest_adapter.hku")
    def test_container_provides_run_backtest_use_case(self, mock_hku):
        """Test container provides RunBacktestUseCase."""
        # Arrange
        mock_hku.return_value = MagicMock()
        container = Container()

        # Act
        use_case = container.run_backtest_use_case

        # Assert
        assert use_case is not None
        from use_cases.backtest.run_backtest import RunBacktestUseCase

        assert isinstance(use_case, RunBacktestUseCase)

    def test_container_singleton_pattern(self):
        """Test container returns same instance for multiple calls."""
        # Arrange
        container = Container()

        # Act
        use_case1 = container.load_stock_data_use_case
        use_case2 = container.load_stock_data_use_case

        # Assert - same instance
        assert use_case1 is use_case2

    def test_container_provides_repositories(self):
        """Test container provides repository instances."""
        # Arrange
        container = Container()

        # Act
        model_repo = container.model_repository
        config_repo = container.config_repository

        # Assert
        assert model_repo is not None
        assert config_repo is not None
