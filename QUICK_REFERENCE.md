# 快速参考

## 常用命令

### 完整工作流

```bash
# 运行完整工作流（数据 → 训练 → 回测）
./run_backtest.sh workflow

# 使用指数成分股训练
./run_backtest.sh workflow --index 沪深300 --max-stocks 50

# 使用自定义股票列表
./run_backtest.sh workflow --stocks sh600000 sh600016 sh600519
```

### 工作流脚本

```bash
# 查看所有可用命令
./run_backtest.sh --help

# 运行 Qlib 生产回测
./run_backtest.sh qlib-backtest --predictions outputs/predictions/workflow_pred.pkl

# 运行 Hikyuu 回测
./run_backtest.sh backtest-workflow
```

### CLI 工具

```bash
# 查看帮助
./run_cli.sh --help

# 数据操作
./run_cli.sh data load --code sh600000
./run_cli.sh data list

# 模型操作
./run_cli.sh model train --type LGBM --name my_model
./run_cli.sh model list
./run_cli.sh model info --name my_model

# 配置操作
./run_cli.sh config show
./run_cli.sh config set training.batch_size 32
```

### Python 脚本

```bash
# 完整工作流
python examples/hikyuu_train_backtest_workflow.py

# 指数训练
python examples/hikyuu_train_backtest_workflow.py --index 沪深300 --max-stocks 50

# Qlib 回测
python examples/qlib_backtest_production.py --predictions outputs/predictions/workflow_pred.pkl

# Hikyuu 回测
python examples/backtest_workflow_pred.py
```

## 文件路径

### 输出文件
- **预测结果**: `outputs/predictions/workflow_pred.pkl`
- **回测结果**: `backtest_results/backtest_result_*.pkl`

### 配置文件
- **Hikyuu 配置**: `config/hikyuu.ini`
- **项目配置**: `config.yaml`

### 示例文件
- **完整工作流**: `examples/hikyuu_train_backtest_workflow.py`
- **Qlib 回测**: `examples/qlib_backtest_production.py`
- **Hikyuu 回测**: `examples/backtest_workflow_pred.py`

## 环境检查

```bash
# 检查 Python 环境和依赖
python check_env.py

# 运行测试
pytest tests/ -v

# 快速测试
./run_quick_tests.sh
```

## 指数列表

### 主要指数
- **沪深300**: 300只市值最大股票
- **中证500**: 500只中小盘股票
- **上证50**: 50只上海龙头股
- **中证100**: 100只市值最大股票

### 行业指数
- **中证银行**: 银行业指数
- **中证医药**: 医药行业指数
- **中证消费**: 消费行业指数
- **中证科技**: 科技行业指数

## 常见问题

**Q: 如何查看回测结果?**
```bash
cat outputs/predictions/workflow_pred.pkl
# 或使用 Python
python -c "import pickle; print(pickle.load(open('outputs/predictions/workflow_pred.pkl', 'rb')))"
```

**Q: 如何修改训练参数?**

编辑 `examples/hikyuu_train_backtest_workflow.py` 中的 hyperparameters 部分

**Q: 训练速度慢怎么办?**
- 使用 `--max-stocks` 限制股票数量
- 减少历史数据天数 (修改 `Query(-500)`)
- 简化模型参数 (减少 `num_leaves`)

## 更多信息

- **完整文档**: [docs/README.md](docs/README.md)
- **工作流指南**: [docs/WORKFLOW_GUIDE.md](docs/WORKFLOW_GUIDE.md)
- **指数训练**: [docs/INDEX_TRAINING_GUIDE.md](docs/INDEX_TRAINING_GUIDE.md)
