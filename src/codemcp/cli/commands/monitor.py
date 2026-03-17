"""
监控命令

实时监控任务执行状态的命令。
"""

import asyncio
import time
from typing import Optional

import typer
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.text import Text

from ..config import get_config
from ...cli.api_client import get_api_manager, formatter

app = typer.Typer(
    name="monitor",
    help="实时监控任务执行状态",
    no_args_is_help=True,
)

console = Console()
manager = get_api_manager()


@app.command()
def dashboard(
    refresh: float = typer.Option(
        2.0,
        "--refresh",
        "-r",
        help="刷新间隔（秒）",
        min=0.5,
        max=60.0,
    ),
    system_id: Optional[str] = typer.Option(
        None,
        "--system",
        "-s",
        help="只监控指定系统的任务",
    ),
):
    """显示监控仪表板"""
    config = get_config()
    refresh_interval = config.get("ui.refresh_interval", refresh)

    console.print(f"[bold green]监控仪表板[/bold green] (刷新间隔: {refresh_interval}秒)")
    console.print("[yellow]按 Ctrl+C 停止监控[/yellow]")

    refresh_count = 0
    try:
        with Live(console=console, refresh_per_second=1) as live:
            while True:
                refresh_count += 1
                
                try:
                    # 获取系统状态
                    status_data = manager.client.get_system_status()
                    
                    # 获取运行中的任务
                    tasks_data = manager.client.get_tasks(status="running", page_size=10)
                    running_tasks = tasks_data.get("tests", [])
                    
                    # 获取队列状态
                    queue_data = manager.client.get_queue_status()
                    
                    # 创建监控表格
                    table = Table(title=f"监控仪表板 - 第 {refresh_count} 次刷新")
                    table.add_column("指标", style="cyan")
                    table.add_column("值", style="green")
                    table.add_column("状态", justify="center")
                    
                    # 系统状态
                    sys_status = status_data.get("status", "unknown")
                    status_color = "green" if sys_status == "operational" else "red" if sys_status == "degraded" else "yellow"
                    table.add_row("系统状态", sys_status, f"[{status_color}]{sys_status}[/{status_color}]")
                    
                    # 数据库状态
                    db_status = status_data.get("database", "unknown")
                    db_color = "green" if db_status == "connected" else "red"
                    table.add_row("数据库", db_status, f"[{db_color}]{db_status}[/{db_color}]")
                    
                    # 运行中任务数
                    running_count = len(running_tasks)
                    table.add_row("运行中任务", str(running_count),
                                 f"[{'yellow' if running_count > 0 else 'green'}]{running_count}[/{'yellow' if running_count > 0 else 'green'}]")
                    
                    # 队列状态
                    pending_count = queue_data.get("pending", 0)
                    table.add_row("待处理任务", str(pending_count),
                                 f"[{'blue' if pending_count > 0 else 'green'}]{pending_count}[/{'blue' if pending_count > 0 else 'green'}]")
                    
                    # 成功率
                    stats = status_data.get("statistics", {}).get("tasks", {})
                    success_rate = stats.get("success_rate", 0)
                    success_color = "green" if success_rate >= 90 else "yellow" if success_rate >= 70 else "red"
                    table.add_row("成功率", f"{success_rate}%", f"[{success_color}]{success_rate}%[/{success_color}]")
                    
                    # 显示运行中的任务详情
                    if running_tasks:
                        table.add_row("", "", "")
                        table.add_row("[bold]运行中的任务:[/bold]", "", "")
                        
                        for i, task in enumerate(running_tasks[:3]):  # 只显示前3个
                            task_id = task.get("id", "")[:8] + "..."
                            feature_name = task.get("feature", {}).get("name", "未知")
                            table.add_row(f"  {i+1}. {feature_name}", task_id, "[yellow]运行中[/yellow]")
                        
                        if len(running_tasks) > 3:
                            table.add_row(f"  ... 还有 {len(running_tasks) - 3} 个任务", "", "")
                    
                    live.update(table)
                    
                except Exception as e:
                    # 如果API调用失败，显示错误信息
                    error_table = Table(title=f"监控仪表板 - 第 {refresh_count} 次刷新 (API错误)")
                    error_table.add_column("错误信息", style="red")
                    error_table.add_row(f"无法获取监控数据: {str(e)[:50]}...")
                    error_table.add_row("请检查API服务器连接")
                    live.update(error_table)
                
                time.sleep(refresh_interval)
                
    except KeyboardInterrupt:
        console.print("\n[yellow]监控已停止[/yellow]")
        console.print(f"总共刷新了 {refresh_count} 次")


@app.command()
def logs(
    follow: bool = typer.Option(
        True,
        "--follow",
        "-f",
        help="实时跟踪日志",
    ),
    tail: int = typer.Option(
        20,
        "--tail",
        "-t",
        help="显示最后 N 行日志",
        min=1,
        max=1000,
    ),
    task_id: Optional[str] = typer.Option(
        None,
        "--task",
        help="只显示指定任务的日志",
    ),
    system_id: Optional[str] = typer.Option(
        None,
        "--system",
        "-s",
        help="只显示指定系统的日志",
    ),
):
    """查看执行日志"""
    console.print(f"[bold green]执行日志[/bold green]")
    if task_id:
        console.print(f"任务 ID: {task_id}")
    if system_id:
        console.print(f"系统 ID: {system_id}")
    console.print(f"显示最后 {tail} 行日志")
    if follow:
        console.print("[yellow]实时跟踪模式（按 Ctrl+C 停止）[/yellow]")

    try:
        # 获取系统日志
        if task_id:
            # 获取特定任务的日志
            console.print(formatter.format_info_message("获取任务日志..."))
            # 这里可以调用API获取任务日志
            # 暂时使用模拟数据
            pass
        elif system_id:
            # 获取系统日志
            console.print(formatter.format_info_message("获取系统日志..."))
            # 这里可以调用API获取系统日志
            # 暂时使用模拟数据
            pass
        
        # 模拟日志（实际实现中应该从API获取）
        log_count = 0
        try:
            for i in range(min(tail, 20)):
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                level = "INFO" if i % 3 == 0 else "ERROR" if i % 5 == 0 else "DEBUG"
                message = f"日志条目 {i+1} - 这是{level}级别的日志消息"
                color = "green" if level == "INFO" else "red" if level == "ERROR" else "white"
                console.print(f"[{color}]{timestamp} [{level}][/{color}] {message}")
                log_count += 1

            if follow:
                console.print("\n[yellow]开始实时日志跟踪...[/yellow]")
                follow_count = 0
                while True:
                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                    # 模拟实时日志
                    if follow_count % 5 == 0:
                        console.print(f"[green]{timestamp} [INFO][/green] 系统运行正常")
                    elif follow_count % 7 == 0:
                        console.print(f"[red]{timestamp} [ERROR][/red] 检测到潜在问题")
                    else:
                        console.print(f"[white]{timestamp} [DEBUG][/white] 处理任务中...")
                    
                    follow_count += 1
                    time.sleep(1)
                    
        except KeyboardInterrupt:
            console.print("\n[yellow]日志查看已停止[/yellow]")
            console.print(f"总共显示了 {log_count} 条日志")
            
    except Exception as e:
        console.print(formatter.format_error_message(f"获取日志失败: {e}"))
        console.print("使用模拟日志数据...")
        
        # 使用模拟日志作为回退
        for i in range(min(tail, 10)):
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            level = "INFO" if i % 3 == 0 else "ERROR" if i % 5 == 0 else "DEBUG"
            message = f"模拟日志条目 {i+1} - 这是{level}级别的日志消息"
            color = "green" if level == "INFO" else "red" if level == "ERROR" else "white"
            console.print(f"[{color}]{timestamp} [{level}][/{color}] {message}")


@app.command()
def alerts():
    """查看系统告警"""
    console.print("[bold green]系统告警[/bold green]")
    console.print("[yellow]功能尚未实现[/yellow]")

    table = Table("时间", "级别", "系统", "消息")
    table.add_row(
        "2026-03-15 10:30:00",
        "[red]CRITICAL[/red]",
        "用户管理系统",
        "数据库连接失败",
    )
    table.add_row(
        "2026-03-15 10:25:00",
        "[yellow]WARNING[/yellow]",
        "订单系统",
        "API 响应时间超过阈值",
    )
    table.add_row(
        "2026-03-15 10:20:00",
        "[blue]INFO[/blue]",
        "库存系统",
        "自动重试任务成功",
    )

    console.print(table)