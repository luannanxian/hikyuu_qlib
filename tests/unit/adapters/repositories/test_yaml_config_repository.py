"""
YAMLConfigRepository 单元测试

测试 YAMLConfigRepository 实现 IConfigRepository 接口,
使用 YAML 文件存储配置
"""

import tempfile
from decimal import Decimal
from pathlib import Path

import pytest

from domain.value_objects.configuration import (
    BacktestConfig,
    DataSourceConfig,
    ModelConfig,
)


class TestYAMLConfigRepository:
    """测试 YAMLConfigRepository"""

    @pytest.fixture
    def temp_config_file(self):
        """临时配置文件 fixture"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            config_path = Path(f.name)
        yield config_path
        # 清理
        if config_path.exists():
            config_path.unlink()

    @pytest.fixture
    def temp_data_dir(self):
        """临时数据目录 fixture"""
        import shutil
        import tempfile

        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        # 清理
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

    @pytest.fixture
    def sample_yaml_config(self, temp_data_dir):
        """示例 YAML 配置内容"""
        return f"""
data_source:
  provider: hikyuu
  data_path: {temp_data_dir}

models:
  LGBM:
    model_type: LGBM
    hyperparameters:
      learning_rate: 0.01
      num_leaves: 31
      max_depth: -1

  MLP:
    model_type: MLP
    hyperparameters:
      hidden_layers: [64, 32]
      activation: relu

backtest:
  initial_capital: 100000
  commission_rate: 0.0003
  slippage_rate: 0.0001
"""

    @pytest.mark.asyncio
    async def test_get_data_source_config(
        self, temp_config_file, sample_yaml_config, temp_data_dir,
    ):
        """
        测试获取数据源配置

        验证:
        1. 从 YAML 文件读取配置
        2. 解析为 DataSourceConfig 值对象
        3. 配置属性正确
        """
        from adapters.repositories.yaml_config_repository import YAMLConfigRepository

        # 写入配置文件
        temp_config_file.write_text(sample_yaml_config)

        # 执行
        repo = YAMLConfigRepository(config_path=str(temp_config_file))
        config = await repo.get_data_source_config()

        # 验证
        assert isinstance(config, DataSourceConfig)
        assert config.provider == "hikyuu"
        assert str(temp_data_dir) in config.data_path

    @pytest.mark.asyncio
    async def test_get_model_config(self, temp_config_file, sample_yaml_config):
        """
        测试获取模型配置

        验证:
        1. 根据模型名称读取配置
        2. 解析为 ModelConfig 值对象
        3. 超参数正确解析
        """
        from adapters.repositories.yaml_config_repository import YAMLConfigRepository

        # 写入配置文件
        temp_config_file.write_text(sample_yaml_config)

        # 执行
        repo = YAMLConfigRepository(config_path=str(temp_config_file))
        config = await repo.get_model_config("LGBM")

        # 验证
        assert isinstance(config, ModelConfig)
        assert config.model_type == "LGBM"
        assert config.hyperparameters["learning_rate"] == 0.01
        assert config.hyperparameters["num_leaves"] == 31

    @pytest.mark.asyncio
    async def test_get_backtest_config(self, temp_config_file, sample_yaml_config):
        """
        测试获取回测配置

        验证:
        1. 从 YAML 文件读取回测配置
        2. 解析为 BacktestConfig 值对象
        3. Decimal 类型正确转换
        """
        from adapters.repositories.yaml_config_repository import YAMLConfigRepository

        # 写入配置文件
        temp_config_file.write_text(sample_yaml_config)

        # 执行
        repo = YAMLConfigRepository(config_path=str(temp_config_file))
        config = await repo.get_backtest_config()

        # 验证
        assert isinstance(config, BacktestConfig)
        assert config.initial_capital == Decimal(100000)
        assert config.commission_rate == Decimal("0.0003")
        assert config.slippage_rate == Decimal("0.0001")

    @pytest.mark.asyncio
    async def test_save_config(self, temp_config_file, temp_data_dir):
        """
        测试保存配置

        验证:
        1. 将配置对象序列化为 YAML
        2. 写入文件
        3. 可以重新读取
        """
        from adapters.repositories.yaml_config_repository import YAMLConfigRepository

        # 初始化空配置文件
        temp_config_file.write_text("data_source:\nmodels:\nbacktest:\n")

        # 创建新配置（使用临时目录）
        new_config = DataSourceConfig(provider="qlib", data_path=str(temp_data_dir))

        # 执行
        repo = YAMLConfigRepository(config_path=str(temp_config_file))
        await repo.save_config("data_source", new_config)

        # 验证：重新读取
        loaded_config = await repo.get_data_source_config()
        assert loaded_config.provider == "qlib"
        assert str(temp_data_dir) in loaded_config.data_path

    @pytest.mark.asyncio
    async def test_file_not_found_handling(self):
        """
        测试文件不存在错误处理

        验证:
        1. 捕获文件不存在异常
        2. 返回合适的错误信息
        """
        from adapters.repositories.yaml_config_repository import YAMLConfigRepository

        # 使用不存在的文件路径
        repo = YAMLConfigRepository(config_path="/nonexistent/config.yaml")

        with pytest.raises(Exception) as exc_info:
            await repo.get_data_source_config()

        assert (
            "not found" in str(exc_info.value).lower()
            or "no such file" in str(exc_info.value).lower()
        )
