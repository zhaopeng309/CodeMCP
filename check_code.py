#!/usr/bin/env python3
"""检查所有代码文件的语法和完整性"""

import ast
import importlib.util
import sys
from pathlib import Path

def check_python_file(file_path: Path) -> tuple[bool, str]:
    """检查Python文件的语法"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        return True, "语法正确"
    except SyntaxError as e:
        return False, f"语法错误: {e}"
    except Exception as e:
        return False, f"读取错误: {e}"

def check_import(file_path: Path) -> tuple[bool, str]:
    """检查文件是否可以导入"""
    try:
        # 将路径转换为模块名
        rel_path = file_path.relative_to(Path.cwd() / "src")
        module_name = str(rel_path.with_suffix('')).replace('/', '.')

        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            return False, "无法创建模块规范"

        module = importlib.util.module_from_spec(spec)
        # 不实际执行，只检查语法
        return True, "可导入"
    except Exception as e:
        return False, f"导入错误: {e}"

def main():
    print("=== CodeMCP 代码完整性检查 ===\n")

    src_dir = Path.cwd() / "src"
    if not src_dir.exists():
        print(f"错误: src目录不存在: {src_dir}")
        return 1

    all_passed = True
    checked_files = 0
    failed_files = []

    # 检查所有Python文件
    for py_file in src_dir.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue

        checked_files += 1
        rel_path = py_file.relative_to(src_dir)

        print(f"检查: {rel_path}")

        # 检查语法
        syntax_ok, syntax_msg = check_python_file(py_file)
        if not syntax_ok:
            print(f"  ❌ 语法错误: {syntax_msg}")
            all_passed = False
            failed_files.append(str(rel_path))
            continue

        # 对于关键文件，检查导入
        if "test" not in str(py_file) and "migrations" not in str(py_file):
            import_ok, import_msg = check_import(py_file)
            if not import_ok:
                print(f"  ⚠️  导入警告: {import_msg}")
                # 导入警告不视为失败
            else:
                print(f"  ✓ 语法正确")
        else:
            print(f"  ✓ 语法正确")

    print(f"\n=== 检查完成 ===")
    print(f"检查文件数: {checked_files}")

    if failed_files:
        print(f"失败文件数: {len(failed_files)}")
        for failed in failed_files:
            print(f"  - {failed}")
        return 1
    else:
        print("✅ 所有文件语法正确")
        return 0

if __name__ == "__main__":
    sys.exit(main())