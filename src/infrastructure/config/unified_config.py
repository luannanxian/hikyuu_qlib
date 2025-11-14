"""
统一配置管理模块

提供配置文件加载、验证、合并预设等功能
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml


@dataclass
class DataConfig:
    """数据源配置"""
    source: str = "hikyuu"
    hikyuu_config: str = "config/hikyuu.ini"
    default_kline_type: str = "DAY"
    cache: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": True,
        "directory": "data/cache",
        "max_size_gb": 10
    })


@dataclass
class TrainingConfig:
    """训练配置"""
    model_type: str = "LGBM"
    hyperparameters: Dict[str, Any] = field(default_factory=dict)
    data: Dict[str, Any] = field(default_factory=lambda: {
        "test_size": 0.2,
        "time_series_split": True,
        "label_horizon": 1
    })
    features: Dict[str, Any] = field(default_factory=lambda: {
        "add_technical_indicators": True,
        "technical_indicators": {
            "ma_windows": [5, 10, 20, 60],
            "return_periods": [1, 5, 10],
            "volatility_window": 20,
            "volume_ma_window": 5,
            "price_position_window": 20
        }
    })
    validation: Dict[str, Any] = field(default_factory=lambda: {
        "metrics_threshold": {
            "single_stock_r2": 0.3,
            "multi_stock_r2": 0.1,
            "max_training_time": 3600
        },
        "adaptive_threshold": True
    })


@dataclass
class PredictionConfig:
    """预测配置"""
    output_dir: str = "predictions"
    output_format: str = "pkl"
    save_details: bool = True
    top_k: int = 50


@dataclass
class SignalConfig:
    """信号转换配置"""
    output_dir: str = "signals"
    output_format: str = "csv"
    strategy: Dict[str, Any] = field(default_factory=lambda: {
        "method": "top_k",
        "top_k": 30,
        "threshold": 0.05,
        "percentile": 0.2
    })
    strength_mapping: Dict[str, Any] = field(default_factory=lambda: {
        "method": "linear",
        "normalize": True
    })


@dataclass
class BacktestConfig:
    """回测配置"""
    engine: str = "hikyuu"
    initial_cash: float = 1000000
    commission: Dict[str, Any] = field(default_factory=lambda: {
        "rate": 0.0003,
        "min_commission": 5
    })
    slippage: float = 0.001
    position: Dict[str, Any] = field(default_factory=lambda: {
        "max_stocks": 30,
        "max_position_per_stock": 0.1,
        "total_position_ratio": 0.95
    })
    risk_control: Dict[str, Any] = field(default_factory=lambda: {
        "stop_loss": 0.1,
        "stop_profit": 0.3,
        "max_drawdown": 0.2
    })
    output: Dict[str, Any] = field(default_factory=lambda: {
        "directory": "backtest_results",
        "generate_charts": True,
        "chart_format": "png"
    })


@dataclass
class ExperimentConfig:
    """实验记录配置"""
    enabled: bool = True
    directory: str = "experiments"
    name_template: str = "{model_type}_{timestamp}"
    auto_log: List[str] = field(default_factory=lambda: [
        "hyperparameters",
        "metrics",
        "predictions",
        "feature_importance",
        "training_data_stats"
    ])


@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = "INFO"
    directory: str = "logs"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    console: bool = True
    file: bool = True
    rotation: Dict[str, Any] = field(default_factory=lambda: {
        "max_bytes": 10485760,
        "backup_count": 5
    })


@dataclass
class UnifiedConfig:
    """统一配置类"""
    data: DataConfig = field(default_factory=DataConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    prediction: PredictionConfig = field(default_factory=PredictionConfig)
    signals: SignalConfig = field(default_factory=SignalConfig)
    backtest: BacktestConfig = field(default_factory=BacktestConfig)
    experiment: ExperimentConfig = field(default_factory=ExperimentConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    # 额外的原始配置数据（用于访问预设和场景）
    _raw_config: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_yaml(cls, config_path: str, preset: Optional[str] = None) -> "UnifiedConfig":
        """
        从YAML文件加载配置

        Args:
            config_path: 配置文件路径
            preset: 预设名称 (development | production | testing)

        Returns:
            UnifiedConfig: 配置对象
        """
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_file, 'r', encoding='utf-8') as f:
            raw_config = yaml.safe_load(f)

        # 如果指定了预设，合并预设配置
        if preset and "presets" in raw_config and preset in raw_config["presets"]:
            preset_config = raw_config["presets"][preset]
            raw_config = cls._merge_configs(raw_config, preset_config)

        # 创建配置对象
        config = cls(
            data=cls._create_data_config(raw_config.get("data", {})),
            training=cls._create_training_config(raw_config.get("training", {})),
            prediction=cls._create_prediction_config(raw_config.get("prediction", {})),
            signals=cls._create_signal_config(raw_config.get("signals", {})),
            backtest=cls._create_backtest_config(raw_config.get("backtest", {})),
            experiment=cls._create_experiment_config(raw_config.get("experiment", {})),
            logging=cls._create_logging_config(raw_config.get("logging", {})),
            _raw_config=raw_config
        )

        return config

    @staticmethod
    def _merge_configs(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        深度合并配置字典

        Args:
            base: 基础配置
            override: 覆盖配置

        Returns:
            合并后的配置
        """
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = UnifiedConfig._merge_configs(result[key], value)
            else:
                result[key] = value

        return result

    @staticmethod
    def _create_data_config(data: Dict[str, Any]) -> DataConfig:
        """创建数据配置对象"""
        return DataConfig(
            source=data.get("source", "hikyuu"),
            hikyuu_config=data.get("hikyuu_config", "config/hikyuu.ini"),
            default_kline_type=data.get("default_kline_type", "DAY"),
            cache=data.get("cache", {})
        )

    @staticmethod
    def _create_training_config(training: Dict[str, Any]) -> TrainingConfig:
        """创建训练配置对象"""
        return TrainingConfig(
            model_type=training.get("model_type", "LGBM"),
            hyperparameters=training.get("hyperparameters", {}),
            data=training.get("data", {}),
            features=training.get("features", {}),
            validation=training.get("validation", {})
        )

    @staticmethod
    def _create_prediction_config(prediction: Dict[str, Any]) -> PredictionConfig:
        """创建预测配置对象"""
        return PredictionConfig(
            output_dir=prediction.get("output_dir", "predictions"),
            output_format=prediction.get("output_format", "pkl"),
            save_details=prediction.get("save_details", True),
            top_k=prediction.get("top_k", 50)
        )

    @staticmethod
    def _create_signal_config(signals: Dict[str, Any]) -> SignalConfig:
        """创建信号配置对象"""
        return SignalConfig(
            output_dir=signals.get("output_dir", "signals"),
            output_format=signals.get("output_format", "csv"),
            strategy=signals.get("strategy", {}),
            strength_mapping=signals.get("strength_mapping", {})
        )

    @staticmethod
    def _create_backtest_config(backtest: Dict[str, Any]) -> BacktestConfig:
        """创建回测配置对象"""
        return BacktestConfig(
            engine=backtest.get("engine", "hikyuu"),
            initial_cash=backtest.get("initial_cash", 1000000),
            commission=backtest.get("commission", {}),
            slippage=backtest.get("slippage", 0.001),
            position=backtest.get("position", {}),
            risk_control=backtest.get("risk_control", {}),
            output=backtest.get("output", {})
        )

    @staticmethod
    def _create_experiment_config(experiment: Dict[str, Any]) -> ExperimentConfig:
        """创建实验配置对象"""
        return ExperimentConfig(
            enabled=experiment.get("enabled", True),
            directory=experiment.get("directory", "experiments"),
            name_template=experiment.get("name_template", "{model_type}_{timestamp}"),
            auto_log=experiment.get("auto_log", [])
        )

    @staticmethod
    def _create_logging_config(logging: Dict[str, Any]) -> LoggingConfig:
        """创建日志配置对象"""
        return LoggingConfig(
            level=logging.get("level", "INFO"),
            directory=logging.get("directory", "logs"),
            format=logging.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            console=logging.get("console", True),
            file=logging.get("file", True),
            rotation=logging.get("rotation", {})
        )

    def get_scenario(self, scenario_name: str) -> Optional[Dict[str, Any]]:
        """
        获取场景配置

        Args:
            scenario_name: 场景名称

        Returns:
            场景配置字典，如果不存在返回None
        """
        scenarios = self._raw_config.get("scenarios", {})
        return scenarios.get(scenario_name)

    def get_hyperparameters(self, model_type: Optional[str] = None) -> Dict[str, Any]:
        """
        获取模型超参数

        Args:
            model_type: 模型类型，如果为None则使用配置中的默认类型

        Returns:
            超参数字典
        """
        if model_type is None:
            model_type = self.training.model_type

        model_key = model_type.lower()
        all_hyperparameters = self.training.hyperparameters

        # 如果直接有该模型的超参数
        if model_key in all_hyperparameters:
            return all_hyperparameters[model_key]

        # 如果没有，返回默认值
        return {}

    def validate(self) -> List[str]:
        """
        验证配置的有效性

        Returns:
            错误列表，如果为空则配置有效
        """
        errors = []

        # 验证数据源配置
        if self.data.source not in ["hikyuu", "qlib"]:
            errors.append(f"Invalid data source: {self.data.source}")

        # 验证模型类型
        if self.training.model_type not in ["LGBM", "XGBOOST", "LINEAR"]:
            errors.append(f"Invalid model type: {self.training.model_type}")

        # 验证文件路径
        hikyuu_config_path = Path(self.data.hikyuu_config)
        if self.data.source == "hikyuu" and not hikyuu_config_path.exists():
            errors.append(f"Hikyuu config file not found: {self.data.hikyuu_config}")

        # 验证阈值
        thresholds = self.training.validation.get("metrics_threshold", {})
        if "single_stock_r2" in thresholds:
            r2 = thresholds["single_stock_r2"]
            if not 0 <= r2 <= 1:
                errors.append(f"Invalid single_stock_r2: {r2} (must be between 0 and 1)")

        # 验证回测配置
        if self.backtest.initial_cash <= 0:
            errors.append(f"Invalid initial_cash: {self.backtest.initial_cash}")

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式

        Returns:
            配置字典
        """
        return {
            "data": self.data.__dict__,
            "training": self.training.__dict__,
            "prediction": self.prediction.__dict__,
            "signals": self.signals.__dict__,
            "backtest": self.backtest.__dict__,
            "experiment": self.experiment.__dict__,
            "logging": self.logging.__dict__
        }


# 全局配置实例
_global_config: Optional[UnifiedConfig] = None


def load_config(config_path: str = "config.yaml", preset: Optional[str] = None) -> UnifiedConfig:
    """
    加载全局配置

    Args:
        config_path: 配置文件路径
        preset: 预设名称

    Returns:
        UnifiedConfig: 配置对象
    """
    global _global_config
    _global_config = UnifiedConfig.from_yaml(config_path, preset)

    # 验证配置
    errors = _global_config.validate()
    if errors:
        raise ValueError(f"Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors))

    return _global_config


def get_config() -> Optional[UnifiedConfig]:
    """
    获取全局配置实例

    Returns:
        UnifiedConfig或None
    """
    return _global_config
