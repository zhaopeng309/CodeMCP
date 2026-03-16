"""
任务管理命令

管理单个任务的命令。
"""

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ...cli.api_client import get_api_manager, formatter
from ...utils.validation import validate_and_sanitize_command

app = typer.Typer(
    name="task",
    help="管理单个任务",
    no_args_is_help=True,
)

console = Console()
manager = get_api_manager()


@app.command()
def show(
    task_id: str = typer.Argument(..., help="任务ID"),
):
    """显示任务详情"""
    console.print(f"[bold green]任务详情[/bold green] - {task_id}")
    
    try:
        # 使用API获取任务详情
        task_data = manager.get_task_with_fallback(task_id)
        
        # 使用格式化器显示
        table = formatter.format_task_detail(task_data)
        console.print(table)
        
    except Exception as e:
        console.print(formatter.format_error_message(f"获取任务详情失败: {e}"))
        raise typer.Exit(1)


@app.command()
def retry(
    task_id: str = typer.Argument(..., help="任务ID"),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="强制重试，即使任务不是失败状态",
    ),
):
    """重试失败的任务"""
    console.print(f"[bold yellow]重试任务[/bold yellow] - {task_id}")
    if force:
        console.print("[yellow]强制重试模式[/yellow]")

    # 确认
    if not force:
        confirm = typer.confirm(f"确定要重试任务 {task_id} 吗？")
        if not confirm:
            console.print("[yellow]操作已取消[/yellow]")
            return

    try:
        # 使用API执行任务（重试）
        response = manager.client.execute_task(task_id)
        
        if response.get("status") == "executing":
            console.print(formatter.format_success_message("任务重试成功！"))
            console.print(f"任务 {task_id} 已重新加入到执行队列中")
        else:
            console.print(formatter.format_warning_message(f"任务重试状态: {response.get('status')}"))
            console.print(f"消息: {response.get('message', '未知')}")
            
    except Exception as e:
        console.print(formatter.format_error_message(f"重试任务失败: {e}"))
        console.print("请检查任务ID是否正确，或任务状态是否允许重试")
        raise typer.Exit(1)


@app.command()
def abort(
    task_id: str = typer.Argument(..., help="任务ID"),
    reason: Optional[str] = typer.Option(
        None,
        "--reason",
        "-r",
        help="中止原因",
    ),
):
    """中止正在执行的任务"""
    console.print(f"[bold red]中止任务[/bold red] - {task_id}")
    if reason:
        console.print(f"原因: {reason}")

    confirm = typer.confirm(f"确定要中止任务 {task_id} 吗？")
    if not confirm:
        console.print("[yellow]操作已取消[/yellow]")
        return

    try:
        # 使用API取消任务
        response = manager.client.cancel_task(task_id)
        
        if response.get("status") == "cancelled":
            console.print(formatter.format_success_message("任务中止成功！"))
            console.print(f"任务 {task_id} 已被标记为中止状态")
        else:
            console.print(formatter.format_warning_message(f"任务中止状态: {response.get('status')}"))
            console.print(f"消息: {response.get('message', '未知')}")
            
    except Exception as e:
        console.print(formatter.format_error_message(f"中止任务失败: {e}"))
        console.print("请检查任务ID是否正确，或任务是否正在运行")
        raise typer.Exit(1)


@app.command()
def logs(
    task_id: str = typer.Argument(..., help="任务ID"),
    tail: int = typer.Option(
        50,
        "--tail",
        "-t",
        help="显示最后 N 行日志",
        min=1,
        max=1000,
    ),
    follow: bool = typer.Option(
        False,
        "--follow",
        "-f",
        help="实时跟踪日志",
    ),
):
    """查看任务执行日志"""
    console.print(f"[bold green]任务日志[/bold green] - {task_id}")
    console.print(f"显示最后 {tail} 行日志")
    if follow:
        console.print("[yellow]实时跟踪模式（按 Ctrl+C 停止）[/yellow]")

    # 模拟日志
    import time

    console.print(f"[dim]开始执行: {time.strftime('%Y-%m-%d %H:%M:%S')}[/dim]")
    for i in range(min(tail, 10)):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        console.print(f"[white]{timestamp} [INFO][/white] 日志条目 {i+1}: 任务执行中...")

    console.print(f"[dim]执行完成: {time.strftime('%Y-%m-%d %H:%M:%S')}[/dim]")


@app.command()
def create(
    feature_id: str = typer.Option(
        ...,
        "--feature",
        "-f",
        help="所属功能点ID",
    ),
    command: str = typer.Option(
        ...,
        "--command",
        "-c",
        help="执行的命令",
    ),
    description: Optional[str] = typer.Option(
        None,
        "--description",
        "-d",
        help="任务描述",
    ),
    priority: int = typer.Option(
        0,
        "--priority",
        "-p",
        help="优先级（数字越小优先级越高）",
    ),
    max_retries: int = typer.Option(
        3,
        "--max-retries",
        "-m",
        help="最大重试次数",
        min=0,
        max=10,
    ),
    timeout: int = typer.Option(
        3600,
        "--timeout",
        "-t",
        help="超时时间（秒）",
        min=1,
    ),
):
    """创建新任务"""
    console.print("[bold green]创建新任务[/bold green]")
    
    # 验证命令
    is_valid, error_msg, sanitized_command = validate_and_sanitize_command(command)
    if not is_valid:
        console.print(formatter.format_error_message(f"命令验证失败: {error_msg}"))
        raise typer.Exit(1)
    
    console.print(f"功能点ID: {feature_id}")
    console.print(f"命令: {sanitized_command}")
    if description:
        console.print(f"描述: {description}")
    console.print(f"优先级: {priority}")
    console.print(f"最大重试次数: {max_retries}")
    console.print(f"超时时间: {timeout}秒")

    confirm = typer.confirm("确定要创建任务吗？")
    if not confirm:
        console.print("[yellow]操作已取消[/yellow]")
        return

    try:
        # 使用API创建任务
        response = manager.create_task_with_fallback(
            feature_id=feature_id,
            command=sanitized_command,
            description=description,
            priority=priority,
            max_retries=max_retries,
            timeout=timeout,
        )
        
        console.print(formatter.format_success_message("任务创建成功！"))
        console.print(f"任务ID: {response.get('id', '未知')}")
        console.print(f"状态: {response.get('status', '未知')}")
        console.print("任务已加入到执行队列中")
        
    except Exception as e:
        console.print(formatter.format_error_message(f"创建任务失败: {e}"))
        raise typer.Exit(1)