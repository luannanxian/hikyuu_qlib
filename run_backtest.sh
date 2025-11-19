#!/bin/bash
# 回测运行脚本 - 自动配置 PYTHONPATH

set -e

# 获取脚本所在目录（项目根目录）
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 配置 PYTHONPATH
export PYTHONPATH="${PROJECT_ROOT}/src:${PYTHONPATH}"

echo "========================================================================"
echo "Hikyuu/Qlib 回测系统"
echo "========================================================================"
echo "项目路径: ${PROJECT_ROOT}"
echo "PYTHONPATH: ${PYTHONPATH}"
echo ""

# 检查 Python 环境
if ! command -v python &> /dev/null; then
    echo "❌ 错误: 未找到 Python"
    exit 1
fi

echo "Python 版本: $(python --version)"
echo ""

# 显示使用方法
show_usage() {
    echo "使用方法:"
    echo "  $0 [命令] [参数]"
    echo ""
    echo "可用命令:"
    echo "  verify           - 验证环境安装"
    echo "  benchmark        - 运行性能基准测试"
    echo "  simple           - 简单回测示例"
    echo "  advanced         - 高级回测示例"
    echo "  workflow         - 完整工作流（Hikyuu数据 → 训练 → 回测）⭐"
    echo "  train [参数]     - 训练机器学习模型"
    echo "  predict [参数]   - 生成预测信号"
    echo "  qlib-test        - Qlib 回测测试（模拟数据）"
    echo "  qlib [参数]      - Qlib 回测（真实预测）"
    echo ""
    echo "示例:"
    echo "  $0 verify"
    echo "  $0 benchmark"
    echo "  $0 workflow      # 完整工作流演示"
    echo "  $0 train --model-type LGBM --index HS300"
    echo "  $0 qlib --predictions pred.pkl --start-date 2024-01-01"
    echo ""
}

# 主命令处理
case "${1:-help}" in
    verify)
        echo "运行环境验证..."
        python "${PROJECT_ROOT}/examples/verify_installation.py"
        ;;

    benchmark)
        echo "运行性能基准测试..."
        python "${PROJECT_ROOT}/examples/performance_benchmark.py"
        ;;

    simple)
        echo "运行简单回测示例..."
        python "${PROJECT_ROOT}/examples/simple_backtest.py"
        ;;

    advanced)
        echo "运行高级回测示例..."
        python "${PROJECT_ROOT}/examples/backtest_advanced.py"
        ;;

    train)
        shift  # 移除 'train' 参数
        echo "训练机器学习模型..."
        python "${PROJECT_ROOT}/examples/train_model_script.py" "$@"
        ;;

    predict)
        shift  # 移除 'predict' 参数
        echo "生成预测信号..."
        python "${PROJECT_ROOT}/examples/predict_script.py" "$@"
        ;;

    qlib-test)
        echo "运行 Qlib 回测测试（模拟数据）..."
        python "${PROJECT_ROOT}/examples/test_qlib_backtest_simple.py"
        ;;

    qlib)
        shift  # 移除 'qlib' 参数
        echo "运行 Qlib 回测..."
        python "${PROJECT_ROOT}/examples/qlib_backtest_production.py" "$@"
        ;;

    workflow)
        echo "运行完整工作流（Hikyuu数据 → 训练 → 预测）..."
        python "${PROJECT_ROOT}/examples/hikyuu_train_backtest_workflow.py"
        ;;

    backtest-workflow)
        echo "使用工作流预测结果进行回测..."
        python "${PROJECT_ROOT}/examples/backtest_workflow_pred.py"
        ;;

    help|--help|-h|"")
        show_usage
        ;;

    *)
        echo "❌ 未知命令: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac
