# 运行指南

## 当前状态

✅ **Domain 层**: 完整可用
✅ **Hikyuu 回测**: 可用（需要安装 Hikyuu）
⚠️ **Qlib 回测**: 环境问题（Python 3.13 不兼容 Qlib）

---

## 快速运行

### 1. 验证环境

```bash
python examples/verify_installation.py
```

**预期输出**:
- ✓ Domain 层导入成功
- ✓ Domain 对象创建成功
- ⚠️ Hikyuu 未安装（可选）
- 状态: Qlib 版本问题

### 2. 测试 Domain 层（推荐）

```bash
python examples/simple_backtest.py
```

这会测试完整的回测流程（使用模拟数据）。

---

## 环境问题修复

### 问题: Qlib 与 Python 3.13 不兼容

**解决方案 A: 降级 Python**

```bash
# 创建新环境（Python 3.10）
conda create -n qlib_py310 python=3.10
conda activate qlib_py310

# 安装依赖
pip install pyqlib pandas numpy scikit-learn lightgbm

# 测试
python examples/test_qlib_backtest_simple.py
```

**解决方案 B: 从源码安装 Qlib**

```bash
git clone https://github.com/microsoft/qlib.git
cd qlib
pip install -e .
```

**解决方案 C: 使用 Hikyuu 回测（推荐用于测试）**

```bash
pip install hikyuu
python examples/simple_backtest.py
```

---

## 生产环境运行

### 使用预测文件运行 Qlib 回测

**前提**: Python 3.10 环境 + Qlib 正确安装

```bash
# 1. 训练模型并生成预测
python -m use_cases.model.train --model-type LGBM --index HS300
python -m use_cases.model.predict \
    --model-name your_model \
    --start-date 2024-01-01 \
    --end-date 2024-12-31 \
    --output outputs/predictions/pred.pkl

# 2. 运行 Qlib 回测
python examples/qlib_backtest_production.py \
    --predictions outputs/predictions/pred.pkl \
    --start-date 2024-01-01 \
    --end-date 2024-12-31 \
    --initial-capital 1000000
```

---

## 已修复的问题

1. ✅ QlibBacktestEngineAdapter 延迟导入
2. ✅ Qlib API 更新（`long_short_backtest` 参数）
3. ✅ Domain 层完整可用
4. ✅ 验证脚本创建

## 待解决问题

1. ⚠️ Python 3.13 与 Qlib 兼容性
2. ⚠️ 预测文件 NumPy 版本冲突

---

## 推荐工作流

### 开发/测试环境

```bash
# 使用 Python 3.11 或 3.10
conda create -n qlib_dev python=3.10
conda activate qlib_dev
pip install -r requirements.txt

# 运行测试
python examples/verify_installation.py
python examples/test_qlib_backtest_simple.py
```

### 生产环境

```bash
# 确保环境一致
conda env export > environment.yml

# 在生产服务器
conda env create -f environment.yml
conda activate qlib_hikyuu

# 运行回测
python examples/qlib_backtest_production.py --predictions <path>
```

---

## 文件说明

- [examples/verify_installation.py](examples/verify_installation.py) - 环境验证
- [examples/simple_backtest.py](examples/simple_backtest.py) - Hikyuu 回测示例
- [examples/test_qlib_backtest_simple.py](examples/test_qlib_backtest_simple.py) - Qlib 回测测试
- [examples/qlib_backtest_production.py](examples/qlib_backtest_production.py) - 生产环境 Qlib 回测

---

## 常见错误

### `cannot import name 'init' from 'qlib'`

**原因**: Qlib 安装损坏或版本不兼容
**解决**: 重新安装 Qlib 或降级 Python

### `No module named 'numpy._core'`

**原因**: 预测文件 NumPy 版本不匹配
**解决**: 重新生成预测文件

### `No module named 'hikyuu'`

**原因**: Hikyuu 未安装
**解决**: `pip install hikyuu` 或使用 Qlib 回测

---

## 获取帮助

查看文档:
- [Qlib 快速入门](docs/QLIB_BACKTEST_QUICK_START.md)
- [Hikyuu 限制说明](docs/HIKYUU_ADAPTER_LIMITATIONS.md)
- [优化总结](docs/OPTIMIZATION_SUMMARY.md)
