# Console CLI 管理工具实现

## 概述
Console CLI 是基于 Typer 和 prompt-toolkit 构建的交互式管理工具，提供"常驻终端"体验。本文档详细描述其实现细节。

## 架构设计

### 组件结构
```
Console CLI
├── Typer CLI 框架
│   ├── 命令定义
│   ├── 参数解析
│   ├── 帮助系统
│   └── 错误处理
├── Interactive UI (prompt-toolkit)
│   ├── 布局管理器
│   ├── 面板组件
│   ├── 键盘绑定
│   └── 主题系统
├── API 客户端
│   ├── HTTP 客户端
│   ├── WebSocket 连接
│   └── 事件处理
└── 配置管理
    ├── 配置文件
    ├── 环境变量
    └── 用户设置
```

## Typer CLI 实现

### 主应用入口
```python
# src/codemcp/cli/main.py
import typer
from typing import Optional
from pathlib import Path

from .config import load_config, save_config
from .ui.interactive import InteractiveConsole
from .commands import (
    monitor, queue, task, system, status, config as config_cmd
)

app = typer.Typer(
    name="codemcp",
    help="CodeMCP 管理控制台",
    add_completion=False,
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)

# 添加子命令
app.add_typer(monitor.app, name="monitor", help="实时监控")
app.add_typer(queue.app, name="queue", help="队列管理")
app.add_typer(task.app, name="task", help="任务管理")
app.add_typer(system.app, name="system", help="系统管理")
app.add_typer(status.app, name="status", help="状态统计")
app.add_typer(config_cmd.app, name="config", help="配置管理")


@app.callback()
def main_callback(
    ctx: typer.Context,
    config_file: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="配置文件路径",
        envvar="CODEMCP_CONFIG",
    ),
    server_url: Optional[str] = typer.Option(
        None,
        "--server",
        "-s",
        help="Gateway 服务器地址",
        envvar="CODEMCP_SERVER_URL",
    ),
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key",
        "-k",
        help="API 密钥",
        envvar="CODEMCP_API_KEY",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="详细输出",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="安静模式",
    ),
):
    """CodeMCP 管理控制台
    
    一个用于管理 CodeMCP 系统的交互式命令行工具。
    支持常驻终端模式和传统命令行模式。
    """
    # 加载配置
    config = load_config(config_file)
    
    # 覆盖配置
    if server_url:
        config.server.url = server_url
    if api_key:
        config.server.api_key = api_key
    if verbose:
        config.logging.level = "DEBUG"
    if quiet:
        config.logging.level = "WARNING"
    
    # 保存到上下文
    ctx.obj = {
        "config": config,
        "client": None,  # 延迟初始化
    }


@app.command()
def interactive(
    ctx: typer.Context,
    full_screen: bool = typer.Option(
        True,
        "--full-screen/--no-full-screen",
        help="全屏模式",
    ),
    theme: str = typer.Option(
        "dark",
        "--theme",
        help="主题 (dark, light, solarized)",
    ),
):
    """启动交互式控制台（常驻终端模式）"""
    from rich.console import Console
    from rich.panel import Panel
    
    console = Console()
    
    # 检查终端大小
    if full_screen and console.size.width < 80:
        console.print(
            Panel(
                "[yellow]终端宽度不足 80 列，建议调整终端大小或使用命令行模式[/yellow]",
                title="警告",
                border_style="yellow",
            )
        )
        full_screen = False
    
    # 启动交互式控制台
    interactive_ui = InteractiveConsole(
        config=ctx.obj["config"],
        full_screen=full_screen,
        theme=theme,
    )
    
    try:
        interactive_ui.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]已退出交互式控制台[/yellow]")
    except Exception as e:
        console.print(f"[red]错误: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def version(ctx: typer.Context):
    """显示版本信息"""
    from .. import __version__
    
    console = Console()
    console.print(f"CodeMCP Console v{__version__}")
    console.print(f"配置文件: {ctx.obj['config'].config_file}")


if __name__ == "__main__":
    app()
```

## 交互式界面实现

### InteractiveConsole 类
```python
# src/codemcp/cli/ui/interactive.py
import asyncio
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from prompt_toolkit import Application
from prompt_toolkit.layout import Layout, HSplit, VSplit
from prompt_toolkit.widgets import (
    TextArea, Label, Frame, Box, Button, Checkbox
)
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.formatted_text import HTML

from ...config import Config
from ..api_client import APIClient


@dataclass
class UIState:
    """UI 状态"""
    current_system: Optional[int] = None
    follow_mode: bool = True
    auto_refresh: bool = True
    refresh_interval: int = 2
    filter_status: Optional[str] = None
    show_details: bool = False
    last_update: Optional[datetime] = None


class InteractiveConsole:
    """交互式控制台"""
    
    def __init__(
        self,
        config: Config,
        full_screen: bool = True,
        theme: str = "dark",
    ):
        self.config = config
        self.full_screen = full_screen
        self.theme = theme
        
        # 状态
        self.state = UIState()
        self.running = True
        
        # API 客户端
        self.client = APIClient(config.server.url, config.server.api_key)
        
        # UI 组件
        self.components = self._create_components()
        
        # 键盘绑定
        self.kb = self._create_key_bindings()
        
        # 样式
        self.style = self._create_style()
        
        # 布局
        self.layout = self._create_layout()
        
        # 应用
        self.app = Application(
            layout=self.layout,
            key_bindings=self.kb,
            style=self.style,
            full_screen=self.full_screen,
            mouse_support=True,
            refresh_interval=self.state.refresh_interval,
        )
        
        # 异步任务
        self.tasks = []
    
    def _create_components(self) -> Dict[str, Any]:
        """创建 UI 组件"""
        return {
            # 头部
            "header": Label(
                "CodeMCP Console - 按 [Q] 退出, [H] 帮助, [R] 刷新",
                style="class:header",
            ),
            
            # 状态栏
            "status_bar": Label(
                "正在连接...",
                style="class:status",
            ),
            
            # 任务队列面板
            "task_panel": TextArea(
                text="加载中...",
                read_only=True,
                scrollbar=True,
                line_numbers=False,
                style="class:panel",
            ),
            
            # 实时日志面板
            "log_panel": TextArea(
                text="等待事件...",
                read_only=True,
                scrollbar=True,
                line_numbers=False,
                style="class:panel",
            ),
            
            # 统计面板
            "stats_panel": TextArea(
                text="统计信息加载中...",
                read_only=True,
                scrollbar=True,
                line_numbers=False,
                style="class:panel",
            ),
            
            # 命令栏
            "command_bar": TextArea(
                text="",
                multiline=False,
                style="class:command",
            ),
            
            # 帮助面板（隐藏）
            "help_panel": TextArea(
                text=self._get_help_text(),
                read_only=True,
                style="class:help",
            ),
        }
    
    def _create_key_bindings(self) -> KeyBindings:
        """创建键盘绑定"""
        kb = KeyBindings()
        
        @kb.add("q")
        def _(event):
            """退出应用程序"""
            self.running = False
            event.app.exit()
        
        @kb.add("h")
        def _(event):
            """显示/隐藏帮助"""
            self._toggle_help()
        
        @kb.add("r")
        def _(event):
            """手动刷新"""
            asyncio.create_task(self.refresh_all())
        
        @kb.add("f")
        def _(event):
            """切换跟随模式"""
            self.state.follow_mode = not self.state.follow_mode
            self._update_status_bar()
        
        @kb.add("a")
        def _(event):
            """切换自动刷新"""
            self.state.auto_refresh = not self.state.auto_refresh
            self._update_status_bar()
        
        @kb.add("tab")
        def _(event):
            """切换焦点面板"""
            self._cycle_focus()
        
        @kb.add("c")
        def _(event):
            """清空日志"""
            self.components["log_panel"].text = ""
        
        @kb.add("s")
        def _(event):
            """选择系统"""
            self._show_system_selector()
        
        @kb.add("p")
        def _(event):
            """暂停队列"""
            asyncio.create_task(self.pause_queue())
        
        @kb.add("u")
        def _(event):
            """恢复队列"""
            asyncio.create_task(self.resume_queue())
        
        @kb.add("1")
        def _(event):
            """选择任务 1"""
            self._select_task(1)
        
        @kb.add("2")
        def _(event):
            """选择任务 2"""
            self._select_task(2)
        
        # 更多快捷键...
        
        return kb
    
    def _create_style(self) -> Style:
        """创建样式"""
        if self.theme == "dark":
            return Style.from_dict({
                "header": "bg:#0044ff #ffffff bold",
                "status": "bg:#333333 #ffffff",
                "panel": "bg:#1e1e1e #cccccc",
                "command": "bg:#222222 #ffff00",
                "help": "bg:#000044 #ffffff",
                "success": "#00ff00",
                "error": "#ff0000",
                "warning": "#ffff00",
                "info": "#00ffff",
                "selected": "bg:#444444 #ffffff",
            })
        else:
            return Style.from_dict({
                "header": "bg:#0044ff #ffffff bold",
                "status": "bg:#eeeeee #000000",
                "panel": "bg:#ffffff #000000",
                "command": "bg:#ffffcc #000000",
                "help": "bg:#e8f4f8 #000000",
                "success": "#008800",
                "error": "#cc0000",
                "warning": "#ff8800",
                "info": "#0088cc",
                "selected": "bg:#e0e0e0 #000000",
            })
    
    def _create_layout(self) -> Layout:
        """创建布局"""
        # 创建面板框架
        task_frame = Frame(
            title="任务队列",
            body=self.components["task_panel"],
        )
        
        log_frame = Frame(
            title="实时日志",
            body=self.components["log_panel"],
        )
        
        stats_frame = Frame(
            title="统计信息",
            body=self.components["stats_panel"],
        )
        
        # 主内容区域
        content = VSplit([
            Box(task_frame, width=30),
            Box(log_frame),
            Box(stats_frame, width=40),
        ])
        
        # 完整布局
        root_container = HSplit([
            self.components["header"],
            self.components["status_bar"],
            content,
            self.components["command_bar"],
        ])
        
        return Layout(root_container)
    
    async def refresh_all(self) -> None:
        """刷新所有面板"""
        try:
            # 并行获取数据
            tasks = [
                self._refresh_task_panel(),
                self._refresh_stats_panel(),
                self._refresh_status_bar(),
            ]
            
            await asyncio.gather(*tasks)
            
            self.state.last_update = datetime.now()
            
        except Exception as e:
            self._log_error(f"刷新失败: {e}")
    
    async def _refresh_task_panel(self) -> None:
        """刷新任务队列面板"""
        try:
            # 获取队列状态
            queue_status = await self.client.get_queue_status()
            
            # 格式化显示
            lines = []
            lines.append(f"窗口: {queue_status['window_used']}/{queue_status['window_size']}")
            lines.append(f"队列: {queue_status['queue_size']} 个任务")
            lines.append("")
            
            # 显示窗口中的任务
            for slot in queue_status.get("slots", []):
                status_icon = {
                    "empty": "○",
                    "reserved": "◐",
                    "running": "●",
                    "completed": "✓",
                    "failed": "✗",
                }.get(slot["status"], "?")
                
                color = {
                    "empty": "gray",
                    "reserved": "yellow",
                    "running": "green",
                    "completed": "blue",
                    "failed": "red",
                }.get(slot["status"], "white")
                
                if slot["feature_name"]:
                    line = f"{status_icon} [{color}]{slot['slot_id']:2d}. {slot['feature_name']}[/{color}]"
                    if slot["duration"]:
                        line += f" ({slot['duration']:.1f}s)"
                    lines.append(line)
                else:
                    lines.append(f"{status_icon} [{color}]{slot['slot_id']:2d}. 空闲[/{color}]")
            
            # 更新面板
            self.components["task_panel"].text = "\n".join(lines)
            
        except Exception as e:
            self.components["task_panel"].text = f"错误: {e}"
    
    async def _refresh_stats_panel(self) -> None:
        """刷新统计面板"""
        try:
            # 获取系统状态
            systems = await self.client.list_systems()
            
            lines = []
            lines.append("[bold]系统统计[/bold]")
            lines.append("")
            
            for system in systems[:5]:  # 显示前5个系统
                stats = system.get("stats", {})
                completion = stats.get("completion_rate", 0) * 100
                
                lines.append(f"{system['name']}:")
                lines.append(f"  完成率: {completion:.1f}%")
                lines.append(f"  模块: {stats.get('completed_blocks', 0)}/{stats.get('total_blocks', 0)}")
                lines.append(f"  功能点: {stats.get('completed_features', 0)}/{stats.get('total_features', 0)}")
                lines.append("")
            
            # 全局统计
            global_stats = await self.client.get_global_stats()
            lines.append("[bold]全局统计[/bold]")
            lines.append(f"总任务: {global_stats.get('total_tasks', 0)}")
            lines.append(f"成功率: {global_stats.get('success_rate', 0)*100:.1f}%")
            lines.append(f"平均时长: {global_stats.get('avg_duration', 0):.1f}s")
            
            self.components["stats_panel"].text = "\n".join(lines)
            
        except Exception as e:
            self.components["stats_panel"].text = f"错误: {e}"
    
    def _update_status_bar(self) -> None:
        """更新状态栏"""
        status_parts = []
        
        if self.state.current_system:
            status_parts.append(f"系统: {self.state.current_system}")
        
        status_parts.append("跟随" if self.state.follow_mode else "固定")
        status_parts.append("自动刷新" if self.state.auto_refresh else "手动刷新")
        
        if self.state.last_update:
            status_parts.append(f"更新: {self.state.last_update.strftime('%H:%M:%S')}")
        
        self.components["status_bar"].text = " | ".join(status_parts)
    
    def _log_message(self, message: str, level: str = "info") -> None:
        """记录日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        color_map = {
            "info": "info",
            "success": "success",
            "warning": "warning",
            "error": "error",
        }
        
        color = color_map.get(level, "info")
        formatted = f"[{timestamp}] [{color}]{message}[/{color}]"
        
        # 添加到日志面板
        current = self.components["log_panel"].text
        if current:
            new_text = current + "\n" + formatted
        else:
            new_text = formatted
        
        # 限制日志行数
        lines = new_text.split("\n")
        if len(lines) > 100:
