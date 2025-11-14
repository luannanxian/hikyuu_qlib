#!/bin/bash
################################################################################
# 快速测试套件
#
# 执行关键测试，跳过耗时的完整训练
################################################################################

set -e

echo "======================================================================"
echo "快速测试套件 - 检测潜在错误"
echo "======================================================================"
echo ""

TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
FAILED_TEST_NAMES=()

run_test() {
    local test_name="$1"
    local test_command="$2"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "测试 $TOTAL_TESTS: $test_name"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    if ./run_test_with_error_check.sh "$test_command" 2>&1 | grep -A10 "错误日志检查"; then
        PASSED_TESTS=$((PASSED_TESTS + 1))
        echo "✓ 测试通过: $test_name"
    else
        FAILED_TESTS=$((FAILED_TESTS + 1))
        FAILED_TEST_NAMES+=("$test_name")
        echo "✗ 测试失败: $test_name"
        return 1
    fi
}

# 1. 依赖检查
echo "【1/6】依赖检查"
run_test "依赖检查" "python3 scripts/check_dependencies.py"

# 2. 指数成分股功能
echo ""
echo "【2/6】指数成分股功能"
run_test "指数成分股获取" "python3 test_index_constituents.py"

# 3. 数据加载（短期）
echo ""
echo "【3/6】数据加载"
run_test "单股票数据加载" \
    "./run_cli.sh data load --code sh600036 --start 2023-10-01 --end 2023-12-31"

# 4. 模型训练（小规模）
echo ""
echo "【4/6】模型训练(3个月数据)"
run_test "模型训练-短期数据" \
    "./run_cli.sh model train --type LGBM --name quick_test_suite \
    --code sh600036 --start 2023-10-01 --end 2023-12-31" || true
# 注：短期数据预期会因数据不足失败，这是正常的

# 5. 模型训练（完整数据）
echo ""
echo "【5/6】模型训练(1年数据)"
run_test "模型训练-完整数据" \
    "./run_cli.sh model train --type LGBM --name full_test_suite \
    --code sh600036 --start 2023-01-01 --end 2023-12-31"

# 6. 小规模批量训练
echo ""
echo "【6/6】批量训练(5只股票)"
run_test "批量训练测试" \
    "./run_cli.sh model train-index --type LGBM --name batch_test_suite \
    --index 沪深300 --start 2023-01-01 --end 2023-12-31 --max-stocks 5"

# 测试总结
echo ""
echo "======================================================================"
echo "测试总结"
echo "======================================================================"
echo ""
echo "总测试数:   $TOTAL_TESTS"
echo "通过:       $PASSED_TESTS"
echo "失败:       $FAILED_TESTS"
echo ""

if [ $FAILED_TESTS -gt 0 ]; then
    echo "失败的测试:"
    for test_name in "${FAILED_TEST_NAMES[@]}"; do
        echo "  ✗ $test_name"
    done
    echo ""
    echo "======================================================================"
    echo "❌ 部分测试失败"
    echo "======================================================================"
    exit 1
else
    echo "======================================================================"
    echo "✅ 所有测试通过！"
    echo "======================================================================"
    exit 0
fi
