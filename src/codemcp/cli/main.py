"""
CodeMCP Console CLI 主入口

Typer CLI 应用主入口点。
"""

import sys
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ..config import settings
from . import __version__

# 创建 Typer 应用
app = typer.Typer(
    name="codemcp",
    help="CodeMCP Console - AI协同编排与执行服务器的交互式控制台",
    add_completion=False,
    no_args_is_help=False,  # 改为False，允许无参数时启动交互式控制台
)

# 创建控制台实例
console = Console()


def version_callback(value: bool):
    """版本回调函数"""
    if value:
        console.print(f"[bold green]CodeMCP Console[/bold green] v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    ctx: typer.Context,
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="显示版本信息",
        callback=version_callback,
        is_eager=True,
    ),
):
    """
    CodeMCP Console - AI协同编排与执行服务器的交互式控制台

    使用子命令管理任务、监控状态和配置系统。
    如果没有提供子命令，将启动交互式控制台。
    """
    # 如果没有提供子命令，启动交互式控制台
    if ctx.invoked_subcommand is None:
        from .console import run_console
        run_console()
        raise typer.Exit()


@app.command()
def interactive():
    """启动交互式控制台"""
    from .console import run_console
    run_console()


@app.command()
def about():
    """关于 CodeMCP"""
    console.print("[bold green]CodeMCP - AI协同编排与执行服务器[/bold green]")
    console.print("基于 MCP (Model Context Protocol) 协议")
    console.print()
    console.print("[bold]核心特性:[/bold]")
    console.print("  • 四层数据模型: System → Block → Feature → Test")
    console.print("  • 任务窗口化执行机制")
    console.print("  • 自我修复和自动重试")
    console.print("  • 实时监控和人工接管")
    console.print()
    console.print(f"[bold]版本:[/bold] {__version__}")
    console.print(f"[bold]配置数据库:[/bold] {settings.database_url}")


@app.command()
def status():
    """显示系统状态"""
    from .api_client import get_api_manager, formatter
    
    console.print("[bold green]系统状态[/bold green]")
    
    try:
        manager = get_api_manager()
        status_data = manager.client.get_system_status()
        
        # 显示状态信息
        table = Table(show_header=False)
        table.add_column("项目", style="cyan")
        table.add_column("值", style="green")
        
        table.add_row("服务状态", status_data.get("status", "未知"))
        table.add_row("服务名称", status_data.get("service", "未知"))
        table.add_row("数据库状态", status_data.get("database", "未知"))
        
        # 显示统计信息
        stats = status_data.get("statistics", {})
        if stats:
            table.add_row("系统数量", str(stats.get("systems", 0)))
            task_stats = stats.get("tasks", {})
            table.add_row("总任务数", str(task_stats.get("total", 0)))
            table.add_row("成功率", f"{task_stats.get('success_rate', 0)}%")
        
        table.add_row("时间戳", status_data.get("timestamp", "未知"))
        
        console.print(table)
        
        # 显示健康状态
        if status_data.get("status") == "operational":
            console.print(formatter.format_success_message("系统运行正常"))
        elif status_data.get("status") == "degraded":
            console.print(formatter.format_warning_message("系统运行降级"))
        else:
            console.print(formatter.format_error_message("系统状态异常"))
            
    except Exception as e:
        console.print(formatter.format_error_message(f"获取系统状态失败: {e}"))
        console.print("请检查API服务器是否正在运行")
        sys.exit(1)


@app.command()
def monitor(
    follow: bool = typer.Option(
        False,
        "--follow",
        "-f",
        help="实时监控模式",
    ),
    interval: float = typer.Option(
        2.0,
        "--interval",
        "-i",
        help="刷新间隔（秒）",
        min=0.5,
        max=60.0,
    ),
):
    """监控任务执行状态"""
    # 待实现 - 实时监控
    console.print(f"[bold yellow]监控模式{' (实时)' if follow else ''}[/bold yellow]")
    console.print(f"刷新间隔: {interval} 秒")
    console.print("功能尚未实现")


@app.command()
def config(
    key: Optional[str] = typer.Argument(None, help="配置键"),
    value: Optional[str] = typer.Argument(None, help="配置值"),
    list_all: bool = typer.Option(
        False,
        "--list",
        "-l",
        help="列出所有配置",
    ),
):
    """管理配置"""
    if list_all:
        console.print("[bold yellow]当前配置:[/bold yellow]")
        table = Table("配置项", "值", "描述")
        table.add_row("database_url", settings.database_url, "数据库连接 URL")
        table.add_row("host", settings.host, "服务器监听地址")
        table.add_row("port", str(settings.port), "服务器监听端口")
        table.add_row("debug", str(settings.debug), "调试模式")
        table.add_row("log_level", settings.log_level, "日志级别")
        table.add_row("task_window_size", str(settings.task_window_size), "任务窗口大小")
        table.add_row("max_retries", str(settings.max_retries), "最大重试次数")
        console.print(table)
    elif key is not None and value is not None:
        console.print(f"[bold yellow]设置配置:[/bold yellow] {key} = {value}")
        console.print("注意：配置设置功能尚未实现")
    elif key is not None:
        # 获取单个配置
        if hasattr(settings, key):
            val = getattr(settings, key)
            console.print(f"[bold yellow]{key}:[/bold yellow] {val}")
        else:
            console.print(f"[bold red]错误:[/bold red] 未知配置项 '{key}'")
            sys.exit(1)
    else:
        console.print("[bold red]错误:[/bold red] 请提供配置键或使用 --list")
        sys.exit(1)


# 导入子命令模块
try:
    from .commands import monitor as monitor_commands
    from .commands import queue as queue_commands
    from .commands import status as status_commands
    from .commands import system as system_commands
    from .commands import task as task_commands

    # 添加子命令
    app.add_typer(
        monitor_commands.app,
        name="monitor",
        help="监控相关命令",
    )
    app.add_typer(
        queue_commands.app,
        name="queue",
        help="队列管理命令",
    )
    app.add_typer(
        status_commands.app,
        name="status",
        help="状态查看命令",
    )
    app.add_typer(
        system_commands.app,
        name="system",
        help="系统管理命令",
    )
    app.add_typer(
        task_commands.app,
        name="task",
        help="任务管理命令",
    )
except ImportError:
    # 子命令模块尚未实现
    pass


if __name__ == "__main__":
    app()