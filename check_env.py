#!/usr/bin/env python
"""
环境检查工具 - 自动配置 PYTHONPATH 并验证环境
"""

import sys
import os
from pathlib import Path

# 自动配置 PYTHONPATH
PROJECT_ROOT = Path(__file__).parent
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

print("=" * 70)
print("环境配置检查")
print("=" * 70)
print(f"项目路径: {PROJECT_ROOT}")
print(f"源码路径: {SRC_PATH}")
print(f"Python 版本: {sys.version}")
print(f"PYTHONPATH 已配置: {str(SRC_PATH) in sys.path}")
print()

# 运行验证
try:
    from examples.verify_installation import check_dependencies
    success = check_dependencies()
    sys.exit(0 if success else 1)
except Exception as e:
    print(f"❌ 环境检查失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
