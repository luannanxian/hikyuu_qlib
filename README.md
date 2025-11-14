# Hikyuu-Qlib 量化交易平台

基于 DDD（领域驱动设计）架构的量化交易平台，融合 Hikyuu 的数据能力和 Qlib 的机器学习能力。

## 🚀 快速开始

查看 [快速入门指南](QUICK_START.md) 开始使用。

## 📚 文档

### 核心文档
- [产品需求文档 (PRD)](docs/prd.md) - 产品功能和需求说明
- [系统设计文档](docs/design.md) - 架构设计和技术方案
- [需求规格说明](docs/requirements.md) - 详细需求规格

### 使用指南
- [CLI 用户指南](docs/guides/CLI_USER_GUIDE.md) - 命令行工具使用说明
- [模型训练指南](docs/guides/MODEL_TRAINING_DATA_LOADING_GUIDE.md) - 数据准备和模型训练
- [批量训练指南](docs/guides/BATCH_TRAINING_GUIDE.md) - 批量训练工作流
- [指数成分股指南](docs/guides/INDEX_CONSTITUENTS_GUIDE.md) - 指数数据使用
- [模型存储说明](docs/guides/sqlite_model_repository_usage.md) - SQLite模型仓储

### 集成方案
- [Hikyuu 回测集成](docs/integration/HIKYUU_BACKTEST_INTEGRATION.md)
- [信号转换方案](docs/integration/SIGNAL_CONVERSION_SOLUTION.md)

### 参考文档
- [Hikyuu Python API](docs/hikyuu-manual/hikyuu-python-api-reference.md)
- [完整文档索引](docs/README.md) - 所有文档导航

## 🏗️ 项目结构

```
hikyuu_qlib/
├── src/                    # 源代码
│   ├── domain/            # 领域层（实体、值对象、领域服务）
│   ├── use_cases/         # 用例层（应用服务）
│   ├── adapters/          # 适配器层（Hikyuu、Qlib）
│   ├── controllers/       # 控制器层（CLI、API）
│   └── utils/             # 工具函数
├── tests/                 # 测试代码
│   ├── unit/             # 单元测试
│   └── integration/      # 集成测试
├── docs/                  # 项目文档
│   ├── guides/           # 使用指南
│   ├── integration/      # 集成方案
│   └── archive/          # 归档文档
├── README.md              # 项目说明
└── QUICK_START.md         # 快速入门
```

## 🎯 主要功能

- ✅ **数据管理**: 基于 Hikyuu 的高性能行情数据加载
- ✅ **模型训练**: 支持 LightGBM/MLP/LSTM/GRU/Transformer 多种模型
- ✅ **批量训练**: 指数成分股批量训练，支持沪深300/中证500等
- ✅ **预测生成**: 模型推理和预测结果管理
- ✅ **CLI 工具**: 完整的命令行界面
- 🚧 **回测系统**: Hikyuu 回测引擎集成（开发中）
- 🚧 **信号转换**: 预测结果到交易信号转换（开发中）

## 🛠️ 技术栈

- **框架**: Hikyuu (数据) + Qlib (机器学习)
- **架构**: 领域驱动设计 (DDD) + 清洁架构
- **语言**: Python 3.13+
- **机器学习**: LightGBM, scikit-learn
- **数据库**: SQLite (模型元数据)
- **测试**: pytest + TDD

## 📦 安装

```bash
# 克隆项目
git clone https://github.com/luannanxian/hikyuu_qlib.git
cd hikyuu_qlib

# 安装依赖
pip install -r requirements.txt

# 运行测试
pytest
```

## 🚀 快速使用

```bash
# 加载股票数据
./run_cli.sh data load --code sh600000 --start 2023-01-01 --end 2023-12-31

# 训练模型
./run_cli.sh model train --type LGBM --name my_model \
  --code sh600000 --start 2023-01-01 --end 2023-12-31

# 查看模型列表
./run_cli.sh model list
```

更多示例请参考 [快速入门指南](QUICK_START.md) 和 [CLI 用户指南](docs/guides/CLI_USER_GUIDE.md)。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License
