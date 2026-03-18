"""
服务器管理命令

启动和停止CodeMCP API服务器的命令。
"""

import os
import signal
import subprocess
import sys
from typing import Optional

import typer
from rich.console import Console

app = typer.Typer(
    name="server",
    help="管理CodeMCP API服务器",
    no_args_is_help=True,
)

console = Console()


def _get_server_process_pattern() -> str:
    """获取服务器进程匹配模式"""
    return "uvicorn.*codemcp.api.server:app"


def _is_server_running() -> bool:
    """检查服务器是否正在运行"""
    try:
        result = subprocess.run(
            ["pgrep", "-f", _get_server_process_pattern()],
            capture_output=True,
            text=True
        )
        return result.returncode == 0 and result.stdout.strip() != ""
    except Exception:
        return False


def _get_running_pids() -> list:
    """获取运行中的服务器进程ID"""
    try:
        result = subprocess.run(
            ["pgrep", "-f", _get_server_process_pattern()],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            pids = result.stdout.strip().split()
            return [int(pid) for pid in pids]
    except Exception:
        pass
    return []


@app.command()
def status():
    """检查服务器状态"""
    console.print("[bold green]检查CodeMCP API服务器状态...[/bold green]")
    
    if _is_server_running():
        pids = _get_running_pids()
        if pids:
            console.print(f"[bold green]✅ 服务器正在运行[/bold green]")
            console.print(f"[dim]运行进程: {', '.join(map(str, pids))}[/dim]")
        else:
            console.print("[bold green]✅ 服务器正在运行[/bold green]")
        
        # 尝试获取API状态
        try:
            import requests
            response = requests.get("http://localhost:8000/api/v1/status", timeout=2)
            if response.status_code == 200:
                data = response.json()
                console.print(f"[dim]API状态: {data.get('status', '未知')}[/dim]")
                console.print(f"[dim]服务名称: {data.get('service', '未知')}[/dim]")
        except Exception:
            console.print("[dim]无法连接到API端点[/dim]")
    else:
        console.print("[bold yellow]⚠️  服务器未运行[/bold yellow]")
        console.print("[dim]使用 'codemcp server start' 启动服务器[/dim]")


@app.command()
def start(
    host: str = typer.Option(
        "0.0.0.0",
        "--host",
        "-h",
        help="服务器监听地址",
    ),
    port: int = typer.Option(
        8000,
        "--port",
        "-p",
        help="服务器监听端口",
    ),
    reload: bool = typer.Option(
        False,
        "--reload",
        "-r",
        help="开发模式热重载",
    ),
    background: bool = typer.Option(
        False,
        "--background",
        "-b",
        help="后台运行模式",
    ),
):
    """启动CodeMCP API服务器"""
    console.print("[bold green]启动CodeMCP API服务器...[/bold green]")
    console.print(f"监听地址: {host}:{port}")
    console.print(f"热重载模式: {'启用' if reload else '禁用'}")
    console.print(f"后台运行: {'是' if background else '否'}")
    
    # 检查是否已运行
    if _is_server_running():
        console.print("[bold yellow]⚠️  服务器已在运行[/bold yellow]")
        console.print("[dim]使用 'codemcp server status' 查看状态[/dim]")
        console.print("[dim]使用 'codemcp server stop' 停止服务器[/dim]")
        return
    
    try:
        # 构建uvicorn命令
        cmd = [
            sys.executable, "-m", "uvicorn",
            "codemcp.api.server:app",
            "--host", host,
            "--port", str(port),
            "--log-level", "info"
        ]
        
        if reload:
            cmd.append("--reload")
        
        if background:
            # 后台运行
            # 创建子进程
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )
            
            # 保存进程ID到文件
            pid_file = os.path.join(os.getcwd(), ".codemcp-server.pid")
            with open(pid_file, "w") as f:
                f.write(str(process.pid))
            
            console.print(f"[bold green]✅ 服务器已在后台启动 (PID: {process.pid})[/bold green]")
            console.print(f"[dim]PID文件: {pid_file}[/dim]")
            console.print("[dim]使用 'codemcp server stop' 停止服务器[/dim]")
            console.print("[dim]使用 'codemcp server status' 查看状态[/dim]")
        else:
            # 前台运行
            console.print("[dim]按Ctrl+C停止服务器[/dim]")
            console.print("-" * 60)
            subprocess.run(cmd)
            
    except KeyboardInterrupt:
        console.print("\n[bold yellow]服务器已停止[/bold yellow]")
    except Exception as e:
        console.print(f"[bold red]服务器启动失败: {e}[/bold red]")
        sys.exit(1)


@app.command()
def stop(
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="强制停止（使用SIGKILL）",
    ),
):
    """停止CodeMCP API服务器"""
    console.print("[bold yellow]停止CodeMCP API服务器...[/bold yellow]")
    
    # 检查是否在运行
    if not _is_server_running():
        console.print("[bold yellow]⚠️  服务器未运行[/bold yellow]")
        return
    
    try:
        # 方法1: 检查PID文件
        pid_file = os.path.join(os.getcwd(), ".codemcp-server.pid")
        if os.path.exists(pid_file):
            with open(pid_file, "r") as f:
                pid = int(f.read().strip())
            
            try:
                signal_type = signal.SIGKILL if force else signal.SIGTERM
                os.kill(pid, signal_type)
                os.remove(pid_file)
                console.print(f"[bold green]✅ 已停止服务器进程 (PID: {pid})[/bold green]")
                return
            except ProcessLookupError:
                console.print(f"[bold yellow]⚠️  进程 {pid} 不存在，删除PID文件[/bold yellow]")
                os.remove(pid_file)
            except Exception as e:
                console.print(f"[bold yellow]⚠️  停止进程失败: {e}[/bold yellow]")
        
        # 方法2: 查找并停止所有codemcp服务器进程
        pids = _get_running_pids()
        if not pids:
            console.print("[bold yellow]⚠️  未找到运行中的服务器进程[/bold yellow]")
            return
        
        signal_type = signal.SIGKILL if force else signal.SIGTERM
        stopped_count = 0
        
        for pid in pids:
            try:
                os.kill(pid, signal_type)
                console.print(f"[bold green]✅ 已停止进程 (PID: {pid})[/bold green]")
                stopped_count += 1
            except ProcessLookupError:
                console.print(f"[dim]进程 {pid} 已不存在[/dim]")
            except Exception as e:
                console.print(f"[bold yellow]⚠️  停止进程 {pid} 失败: {e}[/bold yellow]")
        
        if stopped_count > 0:
            console.print(f"[bold green]✅ 已停止 {stopped_count} 个服务器进程[/bold green]")
        else:
            console.print("[bold yellow]⚠️  未能停止任何进程[/bold yellow]")
        
    except Exception as e:
        console.print(f"[bold red]停止服务器失败: {e}[/bold red]")
        sys.exit(1)


@app.command()
def restart(
    host: str = typer.Option(
        "0.0.0.0",
        "--host",
        "-h",
        help="服务器监听地址",
    ),
    port: int = typer.Option(
        8000,
        "--port",
        "-p",
        help="服务器监听端口",
    ),
    reload: bool = typer.Option(
        False,
        "--reload",
        "-r",
        help="开发模式热重载",
    ),
    background: bool = typer.Option(
        False,
        "--background",
        "-b",
        help="后台运行模式",
    ),
):
    """重启CodeMCP API服务器"""
    console.print("[bold green]重启CodeMCP API服务器...[/bold green]")
    
    # 先停止
    try:
        # 直接调用stop函数
        stop(force=False)
    except SystemExit:
        pass  # 忽略退出
    
    # 等待一下
    import time
    time.sleep(1)
    
    # 再启动
    try:
        start(host=host, port=port, reload=reload, background=background)
    except SystemExit:
        pass


@app.command()
def logs(
    follow: bool = typer.Option(
        False,
        "--follow",
        "-f",
        help="实时跟踪日志",
    ),
    lines: int = typer.Option(
        50,
        "--lines",
        "-n",
        help="显示最后N行日志",
    ),
):
    """查看服务器日志"""
    console.print("[bold green]查看服务器日志...[/bold green]")
    
    # 检查是否在运行
    if not _is_server_running():
        console.print("[bold yellow]⚠️  服务器未运行，无日志可查看[/bold yellow]")
        return
    
    # 尝试获取进程输出
    pids = _get_running_pids()
    if not pids:
        console.print("[bold yellow]⚠️  未找到运行中的服务器进程[/bold yellow]")
        return
    
    # 显示进程信息
    console.print(f"[dim]服务器进程: {', '.join(map(str, pids))}[/dim]")
    console.print("[dim]日志输出:[/dim]")
    console.print("-" * 60)
    
    # 简单提示，实际实现需要更复杂的日志收集
    console.print("[yellow]日志查看功能正在开发中...[/yellow]")
    console.print("[dim]目前可以通过以下方式查看日志:[/dim]")
    console.print("[dim]1. 直接查看终端输出（如果在前台运行）[/dim]")
    console.print("[dim]2. 查看日志文件（如果配置了文件日志）[/dim]")
    console.print("[dim]3. 使用系统日志工具（如 journalctl）[/dim]")