# Hikyuu-Qlib 量化交易平台

基于 DDD（领域驱动设计）架构的量化交易平台，**融合 Hikyuu 数据和回测引擎与 Qlib 机器学习能力**。

实现完整的 **Hikyuu → Qlib → Hikyuu** 工作流：Hikyuu 获取数据 → Qlib 训练模型 → Hikyuu 真实回测。

## 🚀 快速开始

**3 步开始使用**:

```bash
# 1. 运行完整工作流（数据 → 训练 → 回测）
./run_backtest.sh workflow

# 2. 使用指数成分股训练（沪深300）
./run_backtest.sh workflow --index 沪深300 --max-stocks 50

# 3. 查看回测结果
cat outputs/predictions/workflow_pred.pkl
```

查看 [快速入门指南](QUICK_START.md) 了解详细步骤。

## 📚 文档

### 🎯 核心指南
- **[完整工作流指南](docs/WORKFLOW_GUIDE.md)** - Hikyuu → Qlib → Hikyuu 完整流程
- **[指数训练指南](docs/INDEX_TRAINING_GUIDE.md)** - 使用沪深300/中证500等指数成分股训练
- **[快速参考](QUICK_REFERENCE.md)** - 常用命令速查
- **[运行说明](RUN.md)** - 环境配置和运行脚本

### 📖 设计文档
- [系统设计文档](docs/design.md) - 架构设计和技术方案
- [产品需求文档 (PRD)](docs/prd.md) - 产品功能和需求说明
- [需求规格说明](docs/requirements.md) - 详细技术需求

### 🔧 使用指南
- [CLI 用户指南](docs/guides/CLI_USER_GUIDE.md) - 命令行工具使用
- [批量训练指南](docs/guides/BATCH_TRAINING_GUIDE.md) - 批量训练工作流
- [完整用户指南](docs/guides/COMPLETE_USER_GUIDE.md) - 详细功能说明

### 🔗 集成方案
- [Hikyuu 回测集成](docs/integration/HIKYUU_BACKTEST_INTEGRATION.md) - 真实回测引擎集成
- [信号转换方案](docs/integration/SIGNAL_CONVERSION_SOLUTION.md) - Qlib → Hikyuu 信号转换

### 📊 项目状态
- **[项目状态总览](docs/PROJECT_STATUS.md)** - 完整功能状态、性能指标、代码质量报告
- [源代码审计](docs/SOURCE_CODE_AUDIT.md) - 详细代码质量审计
- [清理总结](docs/CLEANUP_SUMMARY.md) - 项目清理工作记录

### 📚 参考文档
- [Hikyuu Python API](docs/hikyuu-manual/hikyuu-python-api-reference.md) - API 参考手册
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

- ✅ **完整工作流**: Hikyuu 获取数据 → Qlib 训练模型 → Hikyuu 真实回测
- ✅ **指数训练**: 支持沪深300/中证500等指数成分股批量训练
- ✅ **数据管理**: 基于 Hikyuu 的高性能行情数据加载
- ✅ **模型训练**: LightGBM 模型训练，支持正则化和超参数优化
- ✅ **真实回测**: Hikyuu Portfolio 组合回测，真实模拟交易环境
- ✅ **信号转换**: CustomSG_QlibFactor 信号指示器，Qlib 预测 → Hikyuu 交易信号
- ✅ **CLI 工具**: 完整的命令行界面

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

### 完整工作流（推荐）

```bash
# 运行完整工作流（数据提取 → 训练 → 回测）
./run_backtest.sh workflow

# 使用指数成分股训练（50只股票采样）
./run_backtest.sh workflow --index 沪深300 --max-stocks 50

# 使用全量指数成分股训练
./run_backtest.sh workflow --index 沪深300
```

### CLI 工具

```bash
# 查看帮助
./run_cli.sh --help

# 加载股票数据
./run_cli.sh data load --code sh600000

# 训练模型
./run_cli.sh model train --type LGBM --name my_model
```

更多示例请参考:
- [完整工作流指南](docs/WORKFLOW_GUIDE.md) - 详细的工作流说明
- [指数训练指南](docs/INDEX_TRAINING_GUIDE.md) - 指数成分股训练
- [CLI 用户指南](docs/guides/CLI_USER_GUIDE.md) - CLI 工具使用

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License
