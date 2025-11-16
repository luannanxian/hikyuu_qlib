"""
Dependency injection container for CLI.

Provides centralized management of dependencies:
- Settings
- Repositories
- Adapters
- Use Cases
"""

from functools import cached_property

from adapters.hikyuu.hikyuu_backtest_adapter import HikyuuBacktestAdapter
from adapters.hikyuu.hikyuu_data_adapter import HikyuuDataAdapter
from adapters.qlib.qlib_model_trainer_adapter import QlibModelTrainerAdapter
from adapters.repositories.sqlite_model_repository import SQLiteModelRepository
from adapters.repositories.yaml_config_repository import YAMLConfigRepository
from infrastructure.config.settings import Settings
from use_cases.backtest.run_backtest import RunBacktestUseCase
from use_cases.config.load_configuration import LoadConfigurationUseCase
from use_cases.config.save_configuration import SaveConfigurationUseCase
from use_cases.data.load_stock_data import LoadStockDataUseCase
from use_cases.model.train_model import TrainModelUseCase


class Container:
    """
    Dependency injection container for CLI.

    Manages creation and lifecycle of:
    - Configuration settings
    - Repository instances
    - Adapter instances
    - Use case instances

    Uses lazy initialization with cached properties.
    """

    def __init__(self, settings: Settings | None = None):
        """
        Initialize container.

        Args:
            settings: Optional settings instance. If None, creates default settings.
        """
        self._settings = settings

    @cached_property
    def settings(self) -> Settings:
        """Get or create Settings instance."""
        if self._settings is None:
            self._settings = Settings()
        return self._settings

    # Repositories

    @cached_property
    def model_repository(self) -> SQLiteModelRepository:
        """Get SQLite model repository instance."""
        return SQLiteModelRepository(db_path=self.settings.DATABASE_URL)

    @cached_property
    def config_repository(self) -> YAMLConfigRepository:
        """Get YAML config repository instance."""
        # Use a default config file path
        config_path = "config.yaml"
        return YAMLConfigRepository(config_path=config_path)

    # Adapters

    @cached_property
    def data_provider(self) -> HikyuuDataAdapter:
        """Get Hikyuu data adapter instance."""
        return HikyuuDataAdapter(config_file=self.settings.HIKYUU_CONFIG_FILE)

    @cached_property
    def model_trainer(self) -> QlibModelTrainerAdapter:
        """Get Qlib model trainer adapter instance."""
        return QlibModelTrainerAdapter()

    @cached_property
    def backtest_engine(self) -> HikyuuBacktestAdapter:
        """Get Hikyuu backtest adapter instance."""
        return HikyuuBacktestAdapter()

    # Use Cases

    @cached_property
    def load_stock_data_use_case(self) -> LoadStockDataUseCase:
        """Get LoadStockDataUseCase instance."""
        return LoadStockDataUseCase(provider=self.data_provider)

    @cached_property
    def train_model_use_case(self) -> TrainModelUseCase:
        """Get TrainModelUseCase instance."""
        return TrainModelUseCase(
            trainer=self.model_trainer, repository=self.model_repository,
        )

    @cached_property
    def run_backtest_use_case(self) -> RunBacktestUseCase:
        """Get RunBacktestUseCase instance."""
        return RunBacktestUseCase(engine=self.backtest_engine)

    @cached_property
    def load_configuration_use_case(self) -> LoadConfigurationUseCase:
        """Get LoadConfigurationUseCase instance."""
        return LoadConfigurationUseCase(repository=self.config_repository)

    @cached_property
    def save_configuration_use_case(self) -> SaveConfigurationUseCase:
        """Get SaveConfigurationUseCase instance."""
        return SaveConfigurationUseCase(repository=self.config_repository)
