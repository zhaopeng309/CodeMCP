"""
配置管理命令

管理 CLI 配置的命令。
"""

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ..config import get_config

app = typer.Typer(
    name="config",
    help="管理 CLI 配置",
    no_args_is_help=True,
)

console = Console()


@app.command()
def list():
    """列出所有配置"""
    config = get_config()
    config_dict = config.to_dict()

    console.print("[bold green]CLI 配置[/bold green]")
    console.print(f"配置文件: {config.config_file}")

    def print_config(data: dict, prefix: str = ""):
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                console.print(f"\n[bold]{full_key}:[/bold]")
                print_config(value, full_key)
            else:
                value_str = str(value)
                if value is None:
                    value_str = "[dim]None[/dim]"
                elif isinstance(value, str) and len(value_str) > 50:
                    value_str = value_str[:47] + "..."
                console.print(f"  {full_key}: {value_str}")

    print_config(config_dict)


@app.command()
def get(
    key: str = typer.Argument(..., help="配置键，支持点号分隔"),
):
    """获取配置值"""
    config = get_config()
    value = config.get(key)

    console.print(f"[bold green]获取配置[/bold green] - {key}")
    if value is not None:
        console.print(f"值: {value}")
    else:
        console.print(f"[red]配置键 '{key}' 不存在[/red]")


@app.command()
def set(
    key: str = typer.Argument(..., help="配置键，支持点号分隔"),
    value: str = typer.Argument(..., help="配置值"),
):
    """设置配置值"""
    config = get_config()

    console.print(f"[bold yellow]设置配置[/bold yellow] - {key} = {value}")

    # 尝试解析值类型
    parsed_value = value
    if value.lower() == "true":
        parsed_value = True
    elif value.lower() == "false":
        parsed_value = False
    elif value.isdigit():
        parsed_value = int(value)
    elif value.replace(".", "", 1).isdigit() and value.count(".") == 1:
        parsed_value = float(value)
    elif value.lower() == "null" or value.lower() == "none":
        parsed_value = None

    config.set(key, parsed_value)
    console.print("[green]配置已更新[/green]")


@app.command()
def delete(
    key: str = typer.Argument(..., help="配置键，支持点号分隔"),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="强制删除，不进行确认",
    ),
):
    """删除配置键"""
    config = get_config()
    current_value = config.get(key)

    console.print(f"[bold red]删除配置[/bold red] - {key}")
    if current_value is not None:
        console.print(f"当前值: {current_value}")

    if not force:
        confirm = typer.confirm("确定要删除这个配置吗？")
        if not confirm:
            console.print("[yellow]操作已取消[/yellow]")
            return

    if config.delete(key):
        console.print("[green]配置已删除[/green]")
    else:
        console.print(f"[red]配置键 '{key}' 不存在或无法删除[/red]")


@app.command()
def reset(
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="强制重置，不进行确认",
    ),
):
    """重置所有配置为默认值"""
    console.print("[bold red]重置所有配置[/bold red]")
    console.print("所有自定义配置将被清除，恢复为默认值")

    if not force:
        confirm = typer.confirm("确定要重置所有配置吗？")
        if not confirm:
            console.print("[yellow]操作已取消[/yellow]")
            return

    config = get_config()
    config.clear()
    console.print("[green]配置已重置为默认值[/green]")


@app.command()
def path():
    """显示配置文件路径"""
    config = get_config()
    console.print("[bold green]配置文件信息[/bold green]")
    console.print(f"配置文件: {config.config_file}")
    console.print(f"配置目录: {config.config_dir}")

    if config.config_file.exists():
        import os
        import time

        stat = config.config_file.stat()
        console.print(f"文件大小: {stat.st_size} 字节")
        console.print(f"修改时间: {time.ctime(stat.st_mtime)}")
        console.print(f"权限: {oct(stat.st_mode)[-3:]}")
    else:
        console.print("[yellow]配置文件不存在[/yellow]")