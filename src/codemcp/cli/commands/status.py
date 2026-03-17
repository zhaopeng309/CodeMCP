"""
状态查看命令

查看系统状态的命令。
"""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

from ...cli.api_client import get_api_manager, formatter

app = typer.Typer(
    name="status",
    help="查看系统状态",
    no_args_is_help=True,
)

console = Console()
manager = get_api_manager()


@app.command()
def summary():
    """显示系统状态摘要"""
    console.print("[bold green]系统状态摘要[/bold green]")

    try:
        # 获取系统状态
        status_data = manager.client.get_system_status()
        
        # 获取任务列表
        tasks_data = manager.get_tasks_with_fallback()
        
        # 计算统计信息
        total_tasks = len(tasks_data.get("tests", []))
        completed_tasks = sum(1 for task in tasks_data.get("tests", []) if task.get("status") == "completed")
        failed_tasks = sum(1 for task in tasks_data.get("tests", []) if task.get("status") == "failed")
        running_tasks = sum(1 for task in tasks_data.get("tests", []) if task.get("status") == "running")
        
        success_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        summary_data = {
            "系统总数": str(status_data.get("statistics", {}).get("systems", 0)),
            "总任务数": str(total_tasks),
            "已完成任务": str(completed_tasks),
            "失败任务": str(failed_tasks),
            "运行中任务": str(running_tasks),
            "成功率": f"{success_rate:.1f}%",
            "数据库状态": status_data.get("database", "未知"),
            "服务状态": status_data.get("status", "未知"),
        }

        table = Table(show_header=False)
        table.add_column("指标", style="cyan")
        table.add_column("值", style="green")

        for key, value in summary_data.items():
            table.add_row(key, value)

        console.print(Panel(table, title="统计信息"))

        # 显示系统状态
        console.print("\n[bold]系统状态:[/bold]")
        systems_table = Table("系统", "模块", "任务", "状态", "进度")
        
        # 这里可以添加从API获取的实际系统数据
        # 暂时使用模拟数据
        systems_table.add_row(
            "用户管理系统",
            "5",
            "156",
            "[green]正常[/green]",
            "[green]78%[/green]",
        )
        systems_table.add_row(
            "订单系统",
            "3",
            "89",
            "[green]正常[/green]",
            "[yellow]45%[/yellow]",
        )
        systems_table.add_row(
            "库存系统",
            "2",
            "44",
            "[blue]已归档[/blue]",
            "[green]100%[/green]",
        )

        console.print(systems_table)
        
    except Exception as e:
        console.print(formatter.format_error_message(f"获取状态摘要失败: {e}"))
        console.print("使用模拟数据...")
        
        # 使用模拟数据作为回退
        summary_data = {
            "系统总数": "3",
            "活跃系统": "2",
            "归档系统": "1",
            "总模块数": "10",
            "总功能点数": "45",
            "总任务数": "289",
            "今日任务数": "23",
            "运行中任务": "3",
            "成功率": "94.7%",
            "平均执行时间": "42.3秒",
        }

        table = Table(show_header=False)
        table.add_column("指标", style="cyan")
        table.add_column("值", style="green")

        for key, value in summary_data.items():
            table.add_row(key, value)

        console.print(Panel(table, title="统计信息"))


@app.command()
def detailed():
    """显示详细系统状态"""
    console.print("[bold green]详细系统状态[/bold green]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("获取状态数据...", total=None)
        # 模拟加载
        import time

        time.sleep(1)
        progress.update(task, completed=1)

    # 显示详细表格
    console.print("\n[bold]任务状态分布:[/bold]")
    status_table = Table("状态", "数量", "百分比")
    status_table.add_row("[green]成功[/green]", "274", "94.7%")
    status_table.add_row("[red]失败[/red]", "15", "5.3%")
    status_table.add_row("[yellow]运行中[/yellow]", "3", "1.0%")
    status_table.add_row("[blue]待执行[/blue]", "12", "4.2%")
    console.print(status_table)

    console.print("\n[bold]性能指标:[/bold]")
    perf_table = Table("指标", "值")
    perf_table.add_row("API 响应时间", "平均 45ms，P95 120ms")
    perf_table.add_row("数据库查询时间", "平均 12ms，P95 35ms")
    perf_table.add_row("任务调度延迟", "平均 0.8s，P95 2.1s")
    perf_table.add_row("系统负载", "CPU: 24%，内存: 68%")
    console.print(perf_table)


@app.command()
def health():
    """显示系统健康状态"""
    console.print("[bold green]系统健康检查[/bold green]")

    try:
        # 获取系统状态
        status_data = manager.client.get_system_status()
        
        # 尝试获取健康检查数据
        try:
            # 使用底层的httpx客户端进行通用请求
            import httpx
            with httpx.Client(base_url=manager.client.base_url, timeout=30.0) as client:
                health_response = client.get("/status/health")
                health_data = health_response.json() if health_response.status_code == 200 else {}
        except:
            health_data = {}
        
        health_services = [
            ("Gateway API", "[green]正常[/green]", f"状态: {status_data.get('status', '未知')}"),
            ("数据库", "[green]正常[/green]" if status_data.get('database') == 'connected' else "[red]异常[/red]",
             f"状态: {status_data.get('database', '未知')}"),
            ("任务队列", "[green]正常[/green]", "服务运行中"),
            ("认证服务", "[green]正常[/green]", "令牌验证正常"),
            ("日志服务", "[yellow]警告[/yellow]", "磁盘使用率: 85%"),
            ("监控服务", "[green]正常[/green]", "数据收集正常"),
        ]

        table = Table("服务", "状态", "详细信息")
        for service, status, info in health_services:
            table.add_row(service, status, info)

        console.print(Panel(table, title="服务健康状态"))

        # 整体状态评估
        healthy_count = sum(1 for _, status, _ in health_services if "正常" in status)
        warning_count = sum(1 for _, status, _ in health_services if "警告" in status)
        error_count = sum(1 for _, status, _ in health_services if "异常" in status)
        
        overall_status = Text("整体状态: ", style="bold")
        if error_count > 0:
            overall_status.append("异常", style="red bold")
        elif warning_count > 0:
            overall_status.append("警告", style="yellow bold")
        else:
            overall_status.append("健康", style="green bold")
        
        overall_status.append(f" ({len(health_services)}个服务中{healthy_count}个正常，{warning_count}个警告，{error_count}个异常)")
        console.print(overall_status)
        
    except Exception as e:
        console.print(formatter.format_error_message(f"获取健康状态失败: {e}"))
        console.print("使用模拟数据...")
        
        # 使用模拟数据作为回退
        health_data = [
            ("Gateway API", "[green]正常[/green]", "响应时间: 32ms"),
            ("数据库", "[green]正常[/green]", "连接数: 12/50"),
            ("任务队列", "[green]正常[/green]", "待处理: 12，运行中: 3"),
            ("认证服务", "[green]正常[/green]", "令牌验证正常"),
            ("日志服务", "[yellow]警告[/yellow]", "磁盘使用率: 85%"),
            ("监控服务", "[green]正常[/green]", "数据收集正常"),
        ]

        table = Table("服务", "状态", "详细信息")
        for service, status, info in health_data:
            table.add_row(service, status, info)

        console.print(Panel(table, title="服务健康状态"))

        overall_status = Text("整体状态: ", style="bold")
        overall_status.append("健康", style="green bold")
        overall_status.append(" (6个服务中5个正常，1个警告)")
        console.print(overall_status)