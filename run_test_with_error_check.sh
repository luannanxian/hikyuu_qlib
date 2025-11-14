#!/bin/bash
################################################################################
# Test Execution with Automatic Error Filtering
#
# 自动执行测试并过滤错误日志的标准脚本
#
# Usage:
#   ./run_test_with_error_check.sh "your test command here"
#
# Examples:
#   ./run_test_with_error_check.sh "./run_cli.sh model train --type LGBM --name test --code sh600036 --start 2023-01-01 --end 2023-12-31"
#   ./run_test_with_error_check.sh "python3 test_index_constituents.py"
#
################################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if command provided
if [ $# -eq 0 ]; then
    echo -e "${RED}错误: 请提供要执行的测试命令${NC}"
    echo "用法: $0 \"your test command\""
    echo ""
    echo "示例:"
    echo "  $0 \"./run_cli.sh model train --type LGBM --name test --code sh600036 --start 2023-01-01 --end 2023-12-31\""
    echo "  $0 \"python3 test_index_constituents.py\""
    exit 1
fi

TEST_COMMAND="$*"
LOG_FILE="/tmp/test_output_$(date +%Y%m%d_%H%M%S).log"

echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE}测试执行 with 自动错误过滤${NC}"
echo -e "${BLUE}======================================================================${NC}"
echo -e "${YELLOW}命令:${NC} $TEST_COMMAND"
echo -e "${YELLOW}日志:${NC} $LOG_FILE"
echo -e "${BLUE}======================================================================${NC}"
echo ""

# Activate conda environment if needed
if [ -f ~/anaconda3/bin/activate ]; then
    source ~/anaconda3/bin/activate qlib_hikyuu
fi

# Execute command and capture output
echo -e "${BLUE}[执行中...]${NC}"
set +e  # Don't exit on command failure
eval "$TEST_COMMAND" 2>&1 | tee "$LOG_FILE"
EXIT_CODE=${PIPESTATUS[0]}
set -e

echo ""
echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE}错误日志检查${NC}"
echo -e "${BLUE}======================================================================${NC}"

# Error keywords to search for
ERROR_KEYWORDS=(
    "error"
    "Error"
    "ERROR"
    "fail"
    "failed"
    "Fail"
    "Failed"
    "FAIL"
    "exception"
    "Exception"
    "EXCEPTION"
    "traceback"
    "Traceback"
    "TRACEBACK"
    "abort"
    "Abort"
    "ABORT"
    "aborted"
    "Aborted"
)

# Build grep pattern
PATTERN=$(IFS='|'; echo "${ERROR_KEYWORDS[*]}")

# Search for errors
ERROR_LINES=$(grep -E "($PATTERN)" "$LOG_FILE" 2>/dev/null || true)

if [ -n "$ERROR_LINES" ]; then
    echo -e "${RED}✗ 发现错误:${NC}"
    echo ""
    echo "$ERROR_LINES" | while IFS= read -r line; do
        echo -e "  ${RED}→${NC} $line"
    done
    echo ""

    # Count error occurrences
    ERROR_COUNT=$(echo "$ERROR_LINES" | wc -l | tr -d ' ')
    echo -e "${YELLOW}错误统计:${NC}"
    for keyword in "${ERROR_KEYWORDS[@]}"; do
        count=$(echo "$ERROR_LINES" | grep -c "$keyword" 2>/dev/null || true)
        if [ "$count" -gt 0 ]; then
            echo -e "  • ${keyword}: ${count} 次"
        fi
    done

    echo ""
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}测试失败 - 发现 ${ERROR_COUNT} 行错误日志${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}完整日志:${NC} $LOG_FILE"
    exit 1
else
    echo -e "${GREEN}✓ 未发现错误关键字${NC}"

    if [ $EXIT_CODE -eq 0 ]; then
        echo ""
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${GREEN}测试通过 ✓${NC}"
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${YELLOW}完整日志:${NC} $LOG_FILE"
        exit 0
    else
        echo ""
        echo -e "${YELLOW}⚠ 命令返回非零退出码: $EXIT_CODE${NC}"
        echo -e "${YELLOW}但未检测到标准错误关键字，请手动检查日志${NC}"
        echo -e "${YELLOW}完整日志:${NC} $LOG_FILE"
        exit $EXIT_CODE
    fi
fi
