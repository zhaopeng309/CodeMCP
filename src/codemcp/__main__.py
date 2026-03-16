"""
CodeMCP 命令行入口点

使用方法:
    python -m codemcp --help
    或直接使用安装后的命令: codemcp
"""

import sys

def main() -> None:
    """主入口函数"""
    print("CodeMCP - AI协同编排与执行服务器")
    print("请使用安装后的命令:")
    print("  codemcp        - 启动交互式控制台")
    print("  codemcp-server - 启动 Gateway 服务器")
    print()
    print("或使用: python -m codemcp.cli.main")
    return 0

if __name__ == "__main__":
    sys.exit(main())