#!/bin/bash
# 测试指数批量训练功能

echo "=========================================="
echo "测试1: 使用5只股票快速测试"
echo "=========================================="

./run_cli.sh model train-index \
    --type LGBM \
    --name hs300_test_5 \
    --index 沪深300 \
    --start 2023-01-01 \
    --end 2023-03-31 \
    --max-stocks 5

echo ""
echo "=========================================="
echo "测试完成!"
echo "=========================================="
echo ""
echo "如果测试成功，可以尝试以下完整训练:"
echo ""
echo "# 训练沪深300（全部300只股票）"
echo "./run_cli.sh model train-index \\"
echo "    --type LGBM \\"
echo "    --name hs300_full_model \\"
echo "    --index 沪深300 \\"
echo "    --start 2023-01-01 \\"
echo "    --end 2023-12-31"
echo ""
echo "# 训练中证500"
echo "./run_cli.sh model train-index \\"
echo "    --type LGBM \\"
echo "    --name zz500_model \\"
echo "    --index 中证500 \\"
echo "    --start 2023-01-01 \\"
echo "    --end 2023-12-31"
echo ""
echo "# 训练上证50"
echo "./run_cli.sh model train-index \\"
echo "    --type LGBM \\"
echo "    --name sz50_model \\"
echo "    --index 上证50 \\"
echo "    --start 2023-01-01 \\"
echo "    --end 2023-12-31"
