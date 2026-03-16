"""
队列管理命令

管理任务队列的命令。
"""

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ...cli.api_client import get_api_manager, formatter

app = typer.Typer(
    name="queue",
    help="管理任务队列",
    no_args_is_help=True,
)

console = Console()
manager = get_api_manager()


@app.command()
def list(
    status: Optional[str] = typer.Option(
        None,
        "--status",
        "-s",
        help="按状态筛选 (pending, running, completed, failed, aborted)",
    ),
    feature_id: Optional[str] = typer.Option(
        None,
        "--feature",
        "-f",
        help="按功能点 ID 筛选",
    ),
    page: int = typer.Option(
        1,
        "--page",
        "-p",
        help="页码",
        min=1,
    ),
    page_size: int = typer.Option(
        20,
        "--page-size",
        help="每页数量",
        min=1,
        max=100,
    ),
):
    """列出队列中的任务"""
    console.print("[bold green]任务队列[/bold green]")
    if status:
        console.print(f"状态筛选: {status}")
    if feature_id:
        console.print(f"功能点筛选: {feature_id}")

    try:
        # 使用API获取任务列表
        response = manager.get_tasks_with_fallback(
            status=status,
            feature_id=feature_id,
            page=page,
            page_size=page_size,
        )
        
        tasks = response.get("tests", [])
        total = response.get("total", 0)
        
        if tasks:
            # 使用格式化器显示表格
            table = formatter.format_task_table(tasks)
            console.print(table)
            console.print(f"总计: {total} 个任务 (第 {page} 页，每页 {page_size} 条)")
        else:
            console.print(formatter.format_info_message("没有找到任务"))
            
    except Exception as e:
        console.print(formatter.format_error_message(f"获取任务列表失败: {e}"))
        raise typer.Exit(1)


@app.command()
def pause():
    """暂停任务队列"""
    console.print("[bold yellow]暂停任务队列[/bold yellow]")
    console.print("功能尚未实现")
    console.print("队列暂停后，新任务将不会被调度执行")


@app.command()
def resume():
    """恢复任务队列"""
    console.print("[bold green]恢复任务队列[/bold green]")
    console.print("功能尚未实现")
    console.print("队列恢复后，任务将恢复正常调度")


@app.command()
def clear(
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="强制清空，不进行确认",
    ),
    status: Optional[str] = typer.Option(
        None,
        "--status",
        "-s",
        help="只清空指定状态的任务",
    ),
):
    """清空任务队列"""
    console.print("[bold red]清空任务队列[/bold red]")
    if status:
        console.print(f"只清空状态为 '{status}' 的任务")

    if not force:
        confirm = typer.confirm("确定要清空任务队列吗？")
        if not confirm:
            console.print("[yellow]操作已取消[/yellow]")
            return

    console.print("功能尚未实现")
    console.print("队列清空后，所有待处理任务将被移除")


@app.command()
def stats():
    """显示队列统计信息"""
    console.print("[bold green]队列统计信息[/bold green]")

    try:
        # 使用API获取队列状态
        response = manager.client.get_queue_status()
        
        stats_table = Table("统计项", "值")
        
        # 任务统计
        task_stats = response.get("task_stats", {})
        stats_table.add_row("总任务数", str(task_stats.get("total", 0)))
        stats_table.add_row("待处理", str(task_stats.get("pending", 0)))
        stats_table.add_row("处理中", str(task_stats.get("running", 0)))
        stats_table.add_row("已完成", str(task_stats.get("completed", 0)))
        stats_table.add_row("失败", str(task_stats.get("failed", 0)))
        stats_table.add_row("已中止", str(task_stats.get("aborted", 0)))
        
        # 成功率
        total_completed = task_stats.get("completed", 0)
        total_failed = task_stats.get("failed", 0)
        total_processed = total_completed + total_failed
        
        if total_processed > 0:
            success_rate = (total_completed / total_processed) * 100
            stats_table.add_row("成功率", f"{success_rate:.1f}%")
        else:
            stats_table.add_row("成功率", "0.0%")
        
        # 性能统计
        perf_stats = response.get("performance_stats", {})
        avg_time = perf_stats.get("average_execution_time", 0)
        if avg_time > 0:
            stats_table.add_row("平均处理时间", f"{avg_time:.1f}秒")
        else:
            stats_table.add_row("平均处理时间", "N/A")
        
        # 队列状态
        queue_status = response.get("queue_status", {})
        stats_table.add_row("队列状态", queue_status.get("status", "未知"))
        stats_table.add_row("窗口大小", str(queue_status.get("window_size", 0)))
        stats_table.add_row("活跃任务", str(queue_status.get("active_tasks", 0)))
        
        console.print(stats_table)
        
    except Exception as e:
        console.print(formatter.format_warning_message(f"获取队列统计失败，使用模拟数据: {e}"))
        
        # 回退到模拟数据
        stats_table = Table("统计项", "值")
        stats_table.add_row("总任务数", "42")
        stats_table.add_row("待处理", "12")
        stats_table.add_row("处理中", "3")
        stats_table.add_row("已完成", "25")
        stats_table.add_row("失败", "2")
        stats_table.add_row("成功率", "92.9%")
        stats_table.add_row("平均处理时间", "45.2秒")
        stats_table.add_row("队列状态", "运行中")
        stats_table.add_row("窗口大小", "5")
        stats_table.add_row("活跃任务", "3")

        console.print(stats_table)