# Hikyuu × Qlib CLI 使用指南 (qlib_hikyuu环境)

**环境**: anaconda qlib_hikyuu 虚拟环境
**Python版本**: 3.13.7
**项目版本**: 0.1.0
**测试状态**: ✅ 462个测试全部通过

---

## 🚀 快速开始

### 方法1: 使用便捷脚本 (推荐)

```bash
# 直接运行
./run_cli.sh --help

# 查看版本
./run_cli.sh --version

# 数据管理
./run_cli.sh data list
./run_cli.sh data load --code sh600000 --start 2023-01-01 --end 2023-12-31

# 模型管理
./run_cli.sh model list
./run_cli.sh model train --type LGBM --name my_model

# 配置管理
./run_cli.sh config show
./run_cli.sh config set --key INITIAL_CAPITAL --value 200000
```

### 方法2: 使用完整命令

```bash
PYTHONPATH=src /Users/zhenkunliu/anaconda3/envs/qlib_hikyuu/bin/python -m controllers.cli.main --help
```

---

## 📋 当前环境配置

### 已安装的核心依赖
```
✅ pydantic==2.12.2          # 类型安全配置
✅ pydantic-settings==2.11.0 # 环境变量配置
✅ click==8.3.0              # CLI框架
✅ rich==14.2.0              # 终端美化
✅ pytest==8.4.2             # 测试框架
✅ pytest-asyncio            # 异步测试
✅ pytest-cov==7.0.0         # 覆盖率
✅ aiosqlite                 # 异步SQLite
✅ PyYAML                    # YAML配置
✅ hikyuu==2.6.8             # 股票数据和回测
```

### 当前配置值
```
数据源:
  HIKYUU_DATA_PATH: ./data/hikyuu
  QLIB_DATA_PATH: ./data/qlib

模型:
  MODEL_STORAGE_PATH: ./models
  DEFAULT_MODEL_TYPE: LightGBM

回测:
  INITIAL_CAPITAL: 100000.0
  COMMISSION_RATE: 0.0003

应用:
  APP_NAME: Hikyuu-Qlib Trading Platform
  APP_VERSION: 0.1.0
  ENVIRONMENT: DEV
  LOG_LEVEL: INFO
```

---

## 📚 CLI命令参考

### 1. 数据管理 (data)

#### 列出可用股票
```bash
# 列出所有股票
./run_cli.sh data list

# 按市场筛选
./run_cli.sh data list --market sh  # 上海证券交易所
./run_cli.sh data list --market sz  # 深圳证券交易所

# 详细输出
./run_cli.sh data list --verbose
```

#### 加载股票数据
```bash
# 加载单只股票日线数据
./run_cli.sh data load \
  --code sh600000 \
  --start 2023-01-01 \
  --end 2023-12-31 \
  --kline-type DAY

# 加载5分钟K线
./run_cli.sh data load \
  --code sz000001 \
  --start 2024-01-01 \
  --end 2024-03-31 \
  --kline-type MIN5

# K线类型选项:
# - DAY: 日线
# - WEEK: 周线
# - MONTH: 月线
# - MIN5: 5分钟
# - MIN15: 15分钟
# - MIN30: 30分钟
# - MIN60: 60分钟
```

---

### 2. 模型管理 (model)

#### 列出模型
```bash
# 列出所有模型
./run_cli.sh model list

# 按状态筛选
./run_cli.sh model list --status trained
./run_cli.sh model list --status deployed

# 详细输出
./run_cli.sh model list --verbose
```

#### 训练模型
```bash
# 训练LightGBM模型
./run_cli.sh model train \
  --type LGBM \
  --name my_lgbm_model \
  --data-path ./data/training_data.csv

# 使用自定义超参数
./run_cli.sh model train \
  --type LGBM \
  --name custom_model \
  --learning-rate 0.05 \
  --max-depth 8 \
  --n-estimators 200

# 支持的模型类型:
# - LGBM: LightGBM (推荐)
# - MLP: 多层感知机
# - LSTM: 长短期记忆网络
# - GRU: 门控循环单元
# - TRANSFORMER: Transformer模型
```

#### 删除模型
```bash
# 删除模型 (需要确认)
./run_cli.sh model delete --model-id <model_id>

# 强制删除 (跳过确认)
./run_cli.sh model delete --model-id <model_id> --force
```

---

### 3. 配置管理 (config)

#### 查看配置
```bash
# 查看所有配置
./run_cli.sh config show

# 查看特定部分
./run_cli.sh config show --section data
./run_cli.sh config show --section model
./run_cli.sh config show --section backtest
```

#### 更新配置
```bash
# 更新初始资金
./run_cli.sh config set --key INITIAL_CAPITAL --value 200000

# 更新佣金费率
./run_cli.sh config set --key COMMISSION_RATE --value 0.0005

# 更新日志级别
./run_cli.sh config set --key LOG_LEVEL --value DEBUG

# 可配置项:
# - INITIAL_CAPITAL: 初始资金
# - COMMISSION_RATE: 佣金费率
# - LOG_LEVEL: 日志级别 (DEBUG/INFO/WARNING/ERROR/CRITICAL)
# - MODEL_STORAGE_PATH: 模型存储路径
# - HIKYUU_DATA_PATH: Hikyuu数据路径
# - QLIB_DATA_PATH: Qlib数据路径
```

---

## 🧪 测试命令

### 运行所有测试
```bash
# 使用qlib_hikyuu环境的Python
/Users/zhenkunliu/anaconda3/envs/qlib_hikyuu/bin/python -m pytest tests/ -v

# 简洁输出
/Users/zhenkunliu/anaconda3/envs/qlib_hikyuu/bin/python -m pytest tests/ -q

# 查看覆盖率
/Users/zhenkunliu/anaconda3/envs/qlib_hikyuu/bin/python -m pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html  # 打开覆盖率报告
```

### 运行特定测试
```bash
# 运行单个测试文件
/Users/zhenkunliu/anaconda3/envs/qlib_hikyuu/bin/python -m pytest tests/unit/domain/entities/test_trading_signal.py -v

# 运行特定测试类
/Users/zhenkunliu/anaconda3/envs/qlib_hikyuu/bin/python -m pytest tests/unit/domain/entities/test_trading_signal.py::TestSignalBatch -v

# 按目录运行
/Users/zhenkunliu/anaconda3/envs/qlib_hikyuu/bin/python -m pytest tests/unit/domain/ -v
```

---

## 📊 测试结果

**最新测试状态** (2025-11-13):
```
✅ 462个测试全部通过
⏱️ 运行时间: 2.15秒
📦 测试覆盖率: >85%
```

**测试分布**:
- Domain层: ~150个测试
- Use Cases层: ~120个测试
- Adapters层: ~100个测试
- Infrastructure层: ~50个测试
- Controllers (CLI)层: ~42个测试

---

## 🔧 常见问题

### Q1: 如何切换到qlib_hikyuu环境?
```bash
# 如果需要手动激活环境
conda activate qlib_hikyuu

# 或使用conda run
conda run -n qlib_hikyuu python --version
```

### Q2: 如何更新Hikyuu到最新版本?
```bash
# Hikyuu建议升级到2.7.0
/Users/zhenkunliu/anaconda3/envs/qlib_hikyuu/bin/pip install hikyuu --upgrade
```

### Q3: ModuleNotFoundError怎么办?
```bash
# 确保PYTHONPATH已设置
export PYTHONPATH=src

# 或使用run_cli.sh脚本(已内置PYTHONPATH)
./run_cli.sh --help
```

### Q4: 如何查看详细日志?
```bash
# 设置日志级别为DEBUG
./run_cli.sh config set --key LOG_LEVEL --value DEBUG

# 或临时启用详细输出
./run_cli.sh data list --verbose
```

---

## 📝 环境信息

```bash
# Python版本
/Users/zhenkunliu/anaconda3/envs/qlib_hikyuu/bin/python --version
# Output: Python 3.13.7

# 查看已安装的包
/Users/zhenkunliu/anaconda3/envs/qlib_hikyuu/bin/pip list

# 检查项目路径
pwd
# Output: /Users/zhenkunliu/project/hikyuu_qlib
```

---

## 🎯 下一步

### 1. 开始使用
```bash
# 查看帮助
./run_cli.sh --help

# 列出可用功能
./run_cli.sh data --help
./run_cli.sh model --help
./run_cli.sh config --help
```

### 2. 学习更多
- **快速开始**: [QUICK_START.md](./QUICK_START.md) - 完整使用指南
- **架构文档**: [ARCHITECTURE_REVIEW_REPORT.md](./ARCHITECTURE_REVIEW_REPORT.md) - 架构分析
- **性能优化**: [PERFORMANCE_ANALYSIS.md](./PERFORMANCE_ANALYSIS.md) - 性能建议
- **改进计划**: [ARCHITECTURE_IMPROVEMENT_PLAN.md](./ARCHITECTURE_IMPROVEMENT_PLAN.md) - 未来路线图

### 3. 开发工作流
```bash
# 1. 运行测试确保一切正常
/Users/zhenkunliu/anaconda3/envs/qlib_hikyuu/bin/python -m pytest tests/ -v

# 2. 进行代码修改
# ... 编辑代码 ...

# 3. 再次运行测试
/Users/zhenkunliu/anaconda3/envs/qlib_hikyuu/bin/python -m pytest tests/ -v

# 4. 使用CLI测试新功能
./run_cli.sh data list --verbose

# 5. 提交代码
git add .
git commit -m "feat: add new feature"
```

---

## ✨ 成功验证

所有关键功能已在qlib_hikyuu环境中验证:
- ✅ 所有462个测试通过
- ✅ CLI主命令可用
- ✅ data子命令可用
- ✅ model子命令可用
- ✅ config子命令可用
- ✅ 版本信息正确显示
- ✅ 配置信息正确显示

**环境状态**: 🟢 完全就绪，可以开始使用！

---

**最后更新**: 2025-11-13
**环境**: qlib_hikyuu (Python 3.13.7)
**项目路径**: /Users/zhenkunliu/project/hikyuu_qlib
