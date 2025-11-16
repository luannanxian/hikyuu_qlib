"""CLI 配置模块

提供用于 CLI 命令的配置数据类。
"""

from .training_config import BatchTrainingConfig, TrainingConfig

__all__ = ["TrainingConfig", "BatchTrainingConfig"]
