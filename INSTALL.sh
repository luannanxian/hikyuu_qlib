#!/bin/bash
# Qlib 回测环境一键安装脚本

set -e

echo "========================================================================"
echo "Qlib 回测环境安装"
echo "========================================================================"

# 检查 conda
if ! command -v conda &> /dev/null; then
    echo "❌ 错误: 未找到 conda"
    echo "请先安装 Anaconda 或 Miniconda"
    exit 1
fi

echo ""
echo "创建 Python 3.12 环境..."
conda create -n qlib_backtest python=3.12 -y

echo ""
echo "激活环境..."
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate qlib_backtest

echo ""
echo "安装依赖..."
pip install --upgrade pip
pip install pyqlib pandas numpy scikit-learn lightgbm

echo ""
echo "验证安装..."
python -c "
import qlib
print('✓ Qlib 版本:', qlib.__version__)
print('✓ Qlib init 可用:', hasattr(qlib, 'init'))

import pandas as pd
import numpy as np
print('✓ Pandas 版本:', pd.__version__)
print('✓ NumPy 版本:', np.__version__)
"

echo ""
echo "========================================================================"
echo "✅ 安装完成!"
echo "========================================================================"
echo ""
echo "下一步:"
echo "  1. 激活环境: conda activate qlib_backtest"
echo "  2. 运行测试: python examples/test_qlib_backtest_simple.py"
echo "  3. 或运行验证: python examples/verify_installation.py"
echo ""
