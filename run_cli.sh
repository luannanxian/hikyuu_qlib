#!/bin/bash
# Hikyuu × Qlib CLI 便捷启动脚本
# 使用 qlib_hikyuu conda 环境

# 设置 Python 路径
PYTHON_BIN="/Users/zhenkunliu/anaconda3/envs/qlib_hikyuu/bin/python"

# 设置 PYTHONPATH
export PYTHONPATH=src

# 运行 CLI
$PYTHON_BIN -m controllers.cli.main "$@"
