# Hikyuu × Qlib 量化交易平台 - 快速开始

**版本**: 0.1.0
**更新日期**: 2025-11-13

---

## 📋 目录

1. [系统要求](#系统要求)
2. [安装步骤](#安装步骤)
3. [运行CLI](#运行cli)
4. [基本使用](#基本使用)
5. [常见问题](#常见问题)
6. [下一步](#下一步)

---

## 🖥️ 系统要求

### 必需环境
- **Python**: 3.11+ (推荐 3.11.4)
- **操作系统**: macOS / Linux / Windows
- **内存**: 最少 4GB RAM
- **磁盘**: 最少 2GB 可用空间

### 必需依赖
```bash
# 核心依赖
pydantic>=2.5.0
pydantic-settings>=2.1.0
click>=8.1.7
rich>=13.7.0
aiosqlite>=0.19.0
PyYAML>=6.0.1

# 数据和模型 (可选但推荐)
hikyuu>=2.0.0    # 股票数据和回测引擎
qlib>=0.9.0      # Microsoft量化投资平台
```

---

## 🚀 安装步骤

### 步骤 1: 克隆项目

```bash
# 如果您还没有项目代码
git clone https://github.com/your-username/hikyuu_qlib.git
cd hikyuu_qlib
```

### 步骤 2: 创建虚拟环境 (推荐)

```bash
# 使用 venv
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate  # Windows

# 使用 conda
conda create -n hikyuu_qlib python=3.11
conda activate hikyuu_qlib
```

### 步骤 3: 安装依赖

**选项 A: 使用 requirements.txt (推荐)**
```bash
# 首先生成 requirements.txt (如果还没有)
pip freeze > requirements.txt

# 安装核心依赖
pip install pydantic pydantic-settings click rich aiosqlite PyYAML

# 安装可选依赖
pip install pytest pytest-asyncio pytest-cov  # 测试工具
```

**选项 B: 手动安装**
```bash
pip install pydantic>=2.5.0 \
            pydantic-settings>=2.1.0 \
            click>=8.1.7 \
            rich>=13.7.0 \
            aiosqlite>=0.19.0 \
            PyYAML>=6.0.1
```

### 步骤 4: 安装 Hikyuu 和 Qlib (可选)

```bash
# Hikyuu (C++库,安装可能需要编译)
pip install hikyuu

# Qlib (Microsoft量化平台)
pip install qlib

# 初始化 Qlib 数据
python -m qlib.run.get_data qlib_data --target_dir ./data/qlib --region cn
```

**注意**: Hikyuu 和 Qlib 不是必需的。项目使用适配器模式,即使没有这些库也可以运行测试。

### 步骤 5: 验证安装

```bash
# 运行测试验证一切正常
python -m pytest tests/ -v

# 预期输出: 462 passed, 2 warnings
```

---

## 🎮 运行 CLI

### 基本命令格式

```bash
# 从项目根目录运行
PYTHONPATH=src python -m controllers.cli.main [COMMAND] [OPTIONS]
```

### 查看帮助

```bash
# 主帮助
PYTHONPATH=src python -m controllers.cli.main --help

# 查看特定命令帮助
PYTHONPATH=src python -m controllers.cli.main data --help
PYTHONPATH=src python -m controllers.cli.main model --help
PYTHONPATH=src python -m controllers.cli.main config --help
```

### 版本信息

```bash
PYTHONPATH=src python -m controllers.cli.main --version
# 输出: python -m controllers.cli.main, version 0.1.0
```

---

## 📖 基本使用

### 1. 数据管理

#### 加载股票数据

```bash
# 加载单只股票数据
PYTHONPATH=src python -m controllers.cli.main data load \
  --code sh600000 \
  --start 2023-01-01 \
  --end 2023-12-31 \
  --kline-type DAY
```

**参数说明**:
- `--code`: 股票代码 (格式: sh/sz + 6位数字,如 sh600000, sz000001)
- `--start`: 开始日期 (格式: YYYY-MM-DD)
- `--end`: 结束日期 (格式: YYYY-MM-DD)
- `--kline-type`: K线类型 (DAY, WEEK, MONTH, MIN5, MIN15, MIN30, MIN60)

#### 列出可用股票

```bash
# 列出所有股票
PYTHONPATH=src python -m controllers.cli.main data list

# 按市场筛选
PYTHONPATH=src python -m controllers.cli.main data list --market sh
PYTHONPATH=src python -m controllers.cli.main data list --market sz

# 详细输出
PYTHONPATH=src python -m controllers.cli.main data list --verbose
```

---

### 2. 模型管理

#### 训练模型

```bash
# 训练LightGBM模型
PYTHONPATH=src python -m controllers.cli.main model train \
  --type LGBM \
  --name my_lgbm_model \
  --data-path ./data/training_data.csv

# 使用自定义超参数
PYTHONPATH=src python -m controllers.cli.main model train \
  --type LGBM \
  --name my_model \
  --learning-rate 0.05 \
  --max-depth 8 \
  --n-estimators 200
```

**参数说明**:
- `--type`: 模型类型 (LGBM, MLP, LSTM, GRU, TRANSFORMER)
- `--name`: 模型名称 (唯一标识)
- `--data-path`: 训练数据路径
- `--learning-rate`: 学习率 (默认: 0.01)
- `--max-depth`: 树的最大深度 (默认: 6)
- `--n-estimators`: 树的数量 (默认: 100)

#### 列出已训练模型

```bash
# 列出所有模型
PYTHONPATH=src python -m controllers.cli.main model list

# 按状态筛选
PYTHONPATH=src python -m controllers.cli.main model list --status trained
PYTHONPATH=src python -m controllers.cli.main model list --status deployed

# 详细输出
PYTHONPATH=src python -m controllers.cli.main model list --verbose
```

#### 删除模型

```bash
# 删除模型(需要确认)
PYTHONPATH=src python -m controllers.cli.main model delete --model-id <model_id>

# 强制删除(跳过确认)
PYTHONPATH=src python -m controllers.cli.main model delete --model-id <model_id> --force
```

---

### 3. 配置管理

#### 查看配置

```bash
# 查看所有配置
PYTHONPATH=src python -m controllers.cli.main config show

# 查看特定部分
PYTHONPATH=src python -m controllers.cli.main config show --section data
PYTHONPATH=src python -m controllers.cli.main config show --section model
PYTHONPATH=src python -m controllers.cli.main config show --section backtest
```

#### 更新配置

```bash
# 更新配置值
PYTHONPATH=src python -m controllers.cli.main config set \
  --key INITIAL_CAPITAL \
  --value 200000

PYTHONPATH=src python -m controllers.cli.main config set \
  --key LOG_LEVEL \
  --value DEBUG
```

**常用配置项**:
- `INITIAL_CAPITAL`: 初始资金 (默认: 100000.0)
- `COMMISSION_RATE`: 佣金费率 (默认: 0.0003)
- `LOG_LEVEL`: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `LOG_FORMAT`: 日志格式 (json, text)
- `MODEL_STORAGE_PATH`: 模型存储路径 (默认: ./models)

---

## 🔧 配置文件

### 环境变量配置

创建 `.env` 文件在项目根目录:

```bash
# .env 文件示例
APP_NAME="Hikyuu-Qlib Trading Platform"
APP_VERSION="0.1.0"
ENVIRONMENT=dev

# 日志配置
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE_PATH=./logs/app.log

# 数据源配置
HIKYUU_DATA_PATH=./data/hikyuu
QLIB_DATA_PATH=./data/qlib

# 模型配置
MODEL_STORAGE_PATH=./models
DEFAULT_MODEL_TYPE=LGBM

# 回测配置
INITIAL_CAPITAL=100000.0
COMMISSION_RATE=0.0003

# 数据库配置
DATABASE_URL=sqlite:///./app.db
DATABASE_ECHO=False
```

### YAML配置文件

创建 `config.yaml`:

```yaml
# config.yaml 示例
data_source:
  hikyuu_path: "./data/hikyuu"
  qlib_path: "./data/qlib"
  provider: "hikyuu"

model:
  default_type: "LGBM"
  hyperparameters:
    learning_rate: 0.01
    max_depth: 6
    n_estimators: 100

backtest:
  initial_capital: 100000.0
  commission_rate: 0.0003
  slippage_rate: 0.0001
```

---

## 🐛 常见问题

### Q1: ModuleNotFoundError: No module named 'domain'

**原因**: 未设置 PYTHONPATH

**解决方案**:
```bash
# 确保从项目根目录运行,并设置 PYTHONPATH
export PYTHONPATH=src  # macOS/Linux
set PYTHONPATH=src     # Windows

# 或每次运行时指定
PYTHONPATH=src python -m controllers.cli.main --help
```

### Q2: ImportError: Hikyuu is not installed

**原因**: 未安装 Hikyuu 库

**解决方案**:
```bash
# 选项 1: 安装 Hikyuu (推荐用于生产环境)
pip install hikyuu

# 选项 2: 跳过数据加载功能,仅运行测试
# 项目使用适配器模式,测试会自动 mock 外部依赖
python -m pytest tests/ -v
```

### Q3: 所有测试都失败

**原因**: Python 版本不兼容

**解决方案**:
```bash
# 检查 Python 版本
python --version  # 应该是 3.11+

# 如果版本过低,升级 Python
conda install python=3.11
# 或
pyenv install 3.11.4
pyenv local 3.11.4
```

### Q4: SyntaxError in tests

**原因**: 使用了 Python 3.10+ 的语法特性

**解决方案**: 确保使用 Python 3.11+

### Q5: Database locked error

**原因**: SQLite 数据库被其他进程占用

**解决方案**:
```bash
# 删除数据库文件重新创建
rm app.db

# 或检查是否有其他进程在使用
lsof app.db
```

---

## 📊 运行测试

### 运行所有测试

```bash
# 运行全部 462 个测试
python -m pytest tests/ -v

# 快速运行(不显示详细输出)
python -m pytest tests/ -q

# 显示覆盖率
python -m pytest tests/ --cov=src --cov-report=html
```

### 运行特定测试

```bash
# 运行单个测试文件
python -m pytest tests/unit/domain/entities/test_trading_signal.py -v

# 运行单个测试类
python -m pytest tests/unit/domain/entities/test_trading_signal.py::TestSignalBatch -v

# 运行单个测试方法
python -m pytest tests/unit/domain/entities/test_trading_signal.py::TestSignalBatch::test_add_signal -v
```

### 按类型运行测试

```bash
# 只运行单元测试
python -m pytest tests/unit/ -v

# 只运行集成测试
python -m pytest tests/integration/ -v

# 只运行特定层的测试
python -m pytest tests/unit/domain/ -v
python -m pytest tests/unit/use_cases/ -v
python -m pytest tests/unit/adapters/ -v
```

---

## 📝 开发工作流

### 典型的开发流程

```bash
# 1. 激活虚拟环境
source venv/bin/activate

# 2. 设置 PYTHONPATH
export PYTHONPATH=src

# 3. 运行测试确保一切正常
python -m pytest tests/ -v

# 4. 进行代码修改
# ... 编辑代码 ...

# 5. 再次运行测试
python -m pytest tests/ -v

# 6. 运行 CLI 测试新功能
python -m controllers.cli.main data list --verbose

# 7. 提交代码
git add .
git commit -m "feat: add new feature"
git push
```

---

## 🎯 下一步

### 学习资源

1. **架构文档**
   - [架构审查报告](./ARCHITECTURE_REVIEW_REPORT.md) - 了解系统架构
   - [架构改进计划](./ARCHITECTURE_IMPROVEMENT_PLAN.md) - 未来改进方向

2. **性能优化**
   - [性能分析报告](./PERFORMANCE_ANALYSIS.md) - 性能优化建议

3. **CLI用户指南**
   - [CLI详细文档](./docs/CLI_USER_GUIDE.md) - 完整的CLI命令参考

4. **开发指南**
   - [任务列表](./docs/tasks.md) - 项目开发计划

### 推荐步骤

1. **熟悉 CLI** (1小时)
   ```bash
   # 探索所有命令
   PYTHONPATH=src python -m controllers.cli.main --help
   PYTHONPATH=src python -m controllers.cli.main data --help
   PYTHONPATH=src python -m controllers.cli.main model --help
   ```

2. **运行测试** (30分钟)
   ```bash
   # 了解测试覆盖范围
   python -m pytest tests/ -v
   python -m pytest tests/ --cov=src --cov-report=term-missing
   ```

3. **阅读架构文档** (2小时)
   - 理解六边形架构
   - 学习 DDD 概念
   - 了解 TDD 实践

4. **尝试开发新功能** (根据需求)
   - 参考 [架构改进计划](./ARCHITECTURE_IMPROVEMENT_PLAN.md)
   - 遵循 TDD 实践
   - 保持测试覆盖率 >85%

---

## 📞 获取帮助

### 项目资源

- **GitHub Issues**: 报告bug或请求功能
- **文档目录**: `/docs` - 完整的项目文档
- **代码审查报告**: 根目录下的 `.md` 文件

### 快速命令参考

```bash
# 帮助命令
PYTHONPATH=src python -m controllers.cli.main --help

# 运行测试
python -m pytest tests/ -v

# 查看覆盖率
python -m pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux

# 代码格式化 (如果安装了 black)
black src/ tests/

# 类型检查 (如果安装了 mypy)
mypy src/
```

---

## ✅ 验证清单

运行前确认:

- [ ] Python 3.11+ 已安装
- [ ] 虚拟环境已激活
- [ ] 依赖已安装 (`pip list` 检查)
- [ ] PYTHONPATH 已设置 (`echo $PYTHONPATH`)
- [ ] 测试全部通过 (`pytest tests/ -v`)
- [ ] CLI 帮助命令可运行

---

**祝您使用愉快！** 🚀

如有问题,请查看 [常见问题](#常见问题) 或提交 GitHub Issue。
