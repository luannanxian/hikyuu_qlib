# 测试错误检查指南

## 概述

本指南说明如何使用 `run_test_with_error_check.sh` 脚本自动执行测试并过滤错误日志。

## 功能特性

该脚本提供以下功能：

1. **自动错误过滤**: 自动检测并高亮显示错误相关的日志行
2. **详细错误统计**: 统计各类错误关键字的出现次数
3. **日志保存**: 将完整输出保存到时间戳命名的日志文件
4. **彩色输出**: 使用颜色区分成功、失败和警告信息
5. **退出码处理**: 正确处理命令的退出码

## 错误关键字

脚本会检测以下错误关键字（不区分大小写）：

- `error` / `Error` / `ERROR`
- `fail` / `failed` / `Fail` / `Failed` / `FAIL`
- `exception` / `Exception` / `EXCEPTION`
- `traceback` / `Traceback` / `TRACEBACK`
- `abort` / `Abort` / `ABORT` / `aborted` / `Aborted`

## 使用方法

### 基本用法

```bash
./run_test_with_error_check.sh "your test command here"
```

### 示例 1: 测试指数成分股功能

```bash
./run_test_with_error_check.sh "python3 test_index_constituents.py"
```

**输出示例（成功）**:
```
======================================================================
测试执行 with 自动错误过滤
======================================================================
命令: python3 test_index_constituents.py
日志: /tmp/test_output_20251114_002127.log
======================================================================

[执行中...]
[... 测试输出 ...]

======================================================================
错误日志检查
======================================================================
✓ 未发现错误关键字

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
测试通过 ✓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
完整日志: /tmp/test_output_20251114_002127.log
```

### 示例 2: 测试模型训练（单股票）

```bash
./run_test_with_error_check.sh "./run_cli.sh model train \
    --type LGBM --name test_model \
    --code sh600000 --start 2023-01-01 --end 2023-12-31"
```

### 示例 3: 测试批量训练（指数成分股）

```bash
./run_test_with_error_check.sh "./run_cli.sh model train-index \
    --type LGBM --name hs300_test \
    --index 沪深300 --start 2023-01-01 --end 2023-12-31 \
    --max-stocks 5"
```

### 示例 4: 测试数据加载

```bash
./run_test_with_error_check.sh "./run_cli.sh data load \
    --code sh600036 --start 2023-01-01 --end 2023-12-31"
```

## 输出格式

### 成功场景

当测试成功且没有检测到错误关键字时：

```
======================================================================
错误日志检查
======================================================================
✓ 未发现错误关键字

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
测试通过 ✓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
完整日志: /tmp/test_output_20251114_HHMMSS.log
```

### 失败场景

当检测到错误关键字时：

```
======================================================================
错误日志检查
======================================================================
✗ 发现错误:

  → ✗ Error training model: Failed to train model: LGBM, With n_samples=0,
  → ✗ Failed to train model: Failed to train model: LGBM, With n_samples=0,
  → Aborted!

错误统计:
  • Error: 1 次
  • error: 1 次
  • Failed: 1 次
  • failed: 1 次
  • Aborted: 1 次

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
测试失败 - 发现 3 行错误日志
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
完整日志: /tmp/test_output_20251114_HHMMSS.log
```

## 日志文件

### 日志文件命名

日志文件自动保存到 `/tmp/` 目录，命名格式为：

```
/tmp/test_output_YYYYMMDD_HHMMSS.log
```

例如:
- `/tmp/test_output_20251114_002127.log`
- `/tmp/test_output_20251114_153045.log`

### 查看日志

```bash
# 查看最新的日志文件
ls -lt /tmp/test_output_*.log | head -1

# 查看特定日志文件
cat /tmp/test_output_20251114_002127.log

# 搜索日志中的特定内容
grep "train_r2" /tmp/test_output_20251114_002127.log
```

### 清理旧日志

```bash
# 删除所有测试日志
rm /tmp/test_output_*.log

# 删除7天前的日志
find /tmp -name "test_output_*.log" -mtime +7 -delete
```

## 高级用法

### 1. 结合其他命令

```bash
# 运行测试并发送邮件通知
./run_test_with_error_check.sh "python3 test_batch_training.py" && \
    echo "测试通过" | mail -s "Test Success" user@example.com

# 运行多个测试
for test in test_*.py; do
    ./run_test_with_error_check.sh "python3 $test"
done
```

### 2. CI/CD 集成

在 CI/CD 管道中使用：

```yaml
# GitHub Actions 示例
- name: Run tests with error checking
  run: |
    ./run_test_with_error_check.sh "python3 -m pytest tests/"
  continue-on-error: false
```

### 3. 自定义错误关键字

如需添加其他错误关键字，编辑 [run_test_with_error_check.sh](../run_test_with_error_check.sh:26-40) 中的 `ERROR_KEYWORDS` 数组：

```bash
ERROR_KEYWORDS=(
    "error"
    "fail"
    "exception"
    "traceback"
    "abort"
    # 添加自定义关键字
    "warning"
    "deprecated"
)
```

## 实际测试示例

### 示例 1: 快速测试单只股票

```bash
./run_test_with_error_check.sh "./run_cli.sh model train \
    --type LGBM --name quick_test \
    --code sh600036 --start 2023-10-01 --end 2023-12-31"
```

**预期结果**: 由于时间范围较短，可能出现训练数据不足的错误

### 示例 2: 测试完整数据集

```bash
./run_test_with_error_check.sh "./run_cli.sh model train \
    --type LGBM --name full_year_test \
    --code sh600036 --start 2023-01-01 --end 2023-12-31"
```

**预期结果**: 应该成功训练模型

### 示例 3: 测试沪深300批量训练（小规模）

```bash
./run_test_with_error_check.sh "./run_cli.sh model train-index \
    --type LGBM --name hs300_small \
    --index 沪深300 --start 2023-01-01 --end 2023-12-31 \
    --max-stocks 10"
```

**预期结果**:
- 成功加载10只股票数据
- 训练完成但 R² 可能较低（0.1-0.2），会显示自定义阈值验证通过的提示

## 故障排除

### 问题 1: 权限被拒绝

**错误**: `Permission denied`

**解决方案**:
```bash
chmod +x run_test_with_error_check.sh
```

### 问题 2: Conda 环境未激活

**错误**: `ModuleNotFoundError: No module named 'hikyuu'`

**解决方案**: 脚本会自动激活 `qlib_hikyuu` 环境，确保该环境存在：
```bash
conda env list | grep qlib_hikyuu
```

### 问题 3: 日志文件过多占用空间

**解决方案**: 定期清理旧日志：
```bash
# 清理7天前的日志
find /tmp -name "test_output_*.log" -mtime +7 -delete
```

## 最佳实践

### 1. 始终使用错误检查脚本

**推荐**:
```bash
./run_test_with_error_check.sh "python3 my_test.py"
```

**不推荐**:
```bash
python3 my_test.py  # 错误可能被遗漏
```

### 2. 保留重要测试的日志

```bash
# 运行测试
./run_test_with_error_check.sh "python3 important_test.py"

# 复制日志到永久位置
cp /tmp/test_output_20251114_*.log logs/important_test_$(date +%Y%m%d).log
```

### 3. 在自动化脚本中使用

```bash
#!/bin/bash
# daily_test.sh

tests=(
    "python3 test_index_constituents.py"
    "python3 test_data_loading.py"
    "./run_cli.sh model train --type LGBM --name daily_test --code sh600000 --start 2023-01-01 --end 2023-12-31"
)

for test in "${tests[@]}"; do
    echo "Running: $test"
    ./run_test_with_error_check.sh "$test" || {
        echo "Test failed: $test"
        exit 1
    }
done

echo "All tests passed!"
```

## 与其他测试工具比较

| 工具 | 错误过滤 | 彩色输出 | 日志保存 | 统计功能 |
|------|----------|----------|----------|----------|
| `run_test_with_error_check.sh` | ✓ | ✓ | ✓ | ✓ |
| 直接运行命令 | ✗ | ✗ | ✗ | ✗ |
| `tee` 命令 | ✗ | ✗ | ✓ | ✗ |
| pytest | ✓ | ✓ | ✓ | ✗ |

## 相关文档

- [指数成分股获取指南](INDEX_CONSTITUENTS_GUIDE.md)
- [批量训练指南](BATCH_TRAINING_GUIDE.md)
- [模型训练数据加载指南](MODEL_TRAINING_DATA_LOADING_GUIDE.md)

## 更新日志

### 2025-11-14
- 初始版本
- 实现基本的错误过滤功能
- 支持彩色输出和日志保存
- 添加错误统计功能
