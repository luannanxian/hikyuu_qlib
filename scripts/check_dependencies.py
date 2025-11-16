#!/usr/bin/env python3
"""
依赖检查脚本

检查项目运行所需的所有依赖是否正确安装
"""

import sys


def check_dependency(name: str, import_name: str = None) -> tuple[bool, str]:
    """
    检查单个依赖是否安装

    Args:
        name: 依赖包名称（用于显示）
        import_name: Python import 名称（如果与包名不同）

    Returns:
        (是否安装, 版本信息或错误信息)
    """
    module_name = import_name or name

    try:
        module = __import__(module_name)
        version = getattr(module, "__version__", "unknown")
        return True, version
    except ImportError as e:
        return False, str(e)


def main():
    """检查所有依赖"""
    print("=" * 70)
    print("依赖检查")
    print("=" * 70)
    print()

    # 定义所有依赖
    dependencies = [
        # 核心依赖
        ("Hikyuu", "hikyuu"),
        ("LightGBM", "lightgbm"),
        ("Pandas", "pandas"),
        ("NumPy", "numpy"),

        # 数据库
        ("PyMySQL", "pymysql"),
        ("aiosqlite", "aiosqlite"),

        # 异步
        ("asyncio", "asyncio"),

        # 配置
        ("PyYAML", "yaml"),
        ("Click", "click"),

        # 测试（可选）
        ("pytest", "pytest"),
    ]

    missing = []
    installed = []

    print("检查依赖...")
    print("-" * 70)

    for name, import_name in dependencies:
        sys.stdout.write(f"  {name:20s} ... ")
        sys.stdout.flush()

        is_installed, info = check_dependency(name, import_name)

        if is_installed:
            print(f"✓ {info}")
            installed.append((name, info))
        else:
            print("✗ NOT INSTALLED")
            missing.append(name)

    print()
    print("=" * 70)

    # 显示结果
    if missing:
        print(f"❌ 缺少 {len(missing)} 个依赖:")
        print()
        for name in missing:
            print(f"  • {name}")

        print()
        print("安装命令:")
        print("-" * 70)

        # 区分核心依赖和可选依赖
        core_deps = ["hikyuu", "lightgbm", "pandas", "numpy", "pymysql", "aiosqlite", "pyyaml", "click"]
        optional_deps = ["pytest"]

        missing_core = [dep.lower().replace(" ", "") for dep in missing if dep.lower().replace(" ", "") in core_deps]
        missing_optional = [dep.lower() for dep in missing if dep.lower() in optional_deps]

        if missing_core:
            print("核心依赖（必需）:")
            print(f"  pip install {' '.join(missing_core)}")
            print()

        if missing_optional:
            print("可选依赖（测试）:")
            print(f"  pip install {' '.join(missing_optional)}")
            print()

        print("或者安装所有依赖:")
        print("  pip install -r requirements.txt")
        print()

        sys.exit(1)
    else:
        print(f"✅ 所有 {len(installed)} 个依赖已正确安装!")
        print()

        # 显示已安装的版本
        print("已安装版本:")
        print("-" * 70)
        for name, version in installed:
            print(f"  {name:20s} {version}")

        print()
        sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n检查被中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 检查过程出错: {e}")
        sys.exit(1)
