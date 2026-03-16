"""
交互式控制台 UI

基于 prompt-toolkit 的交互式控制台界面。
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional

from prompt_toolkit import Application
from prompt_toolkit.application import get_app
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.document import Document
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import (
    HSplit,
    VSplit,
    Window,
    WindowAlign,
    Dimension,
    FormattedTextControl,
    Layout,
)
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import Box, Frame, TextArea

from ..core.task_engine import TaskEngine
from ..core.executor import LocalCommandExecutor
from ..database.session import get_db_session
from ..models.test import TestModel, TestStatus
from .ui.layout import LayoutManager
from .ui.panels import TaskPanel, StatusPanel, LogPanel
from .ui.themes import get_theme_style

logger = logging.getLogger(__name__)


class InteractiveConsole:
    """交互式控制台"""

    def __init__(self):
        """初始化交互式控制台"""
        self.task_engine = TaskEngine(
            executor=LocalCommandExecutor(),
            window_size=5,
            max_retries=3,
        )
        
        # 创建布局管理器
        self.layout_manager = LayoutManager()
        
        # 创建面板
        self.task_panel = TaskPanel()
        self.status_panel = StatusPanel()
        self.log_panel = LogPanel()
        
        # 命令历史
        self.command_history: List[str] = []
        self.history_index = 0
        
        # 应用状态
        self.running = False
        self.refresh_interval = 2.0  # 刷新间隔（秒）
        
        # 创建键盘绑定
        self.kb = KeyBindings()
        self._setup_key_bindings()
        
        # 创建命令补全
        self.command_completer = WordCompleter([
            "help", "tasks", "status", "execute", "cancel", "logs", 
            "clear", "refresh", "quit", "exit", "monitor", "queue"
        ])
        
        # 创建输入缓冲区
        self.input_buffer = Buffer(
            completer=self.command_completer,
            complete_while_typing=True,
        )
        
        # 创建应用
        self.app = self._create_application()

    def _create_application(self) -> Application:
        """创建 prompt-toolkit 应用"""
        
        # 创建布局
        layout = self._create_layout()
        
        # 创建样式
        style = Style.from_dict(get_theme_style())
        
        return Application(
            layout=layout,
            key_bindings=self.kb,
            style=style,
            full_screen=True,
            mouse_support=True,
        )

    def _create_layout(self) -> Layout:
        """创建控制台布局"""
        
        # 标题栏
        title_bar = Window(
            content=FormattedTextControl(self._get_title_text),
            height=Dimension.exact(1),
            align=WindowAlign.CENTER,
            style="class:title",
        )
        
        # 状态栏
        status_bar = Window(
            content=FormattedTextControl(self._get_status_text),
            height=Dimension.exact(1),
            style="class:status",
        )
        
        # 主内容区域 - 分为左右两部分
        left_panel = Frame(
            title="任务列表",
            body=Box(
                Window(
                    content=FormattedTextControl(self._get_tasks_text),
                    style="class:panel",
                ),
                padding=1,
            ),
            style="class:panel.frame",
        )
        
        right_panel = Frame(
            title="状态监控",
            body=Box(
                Window(
                    content=FormattedTextControl(self._get_monitor_text),
                    style="class:panel",
                ),
                padding=1,
            ),
            style="class:panel.frame",
        )
        
        # 日志面板
        log_panel = Frame(
            title="日志输出",
            body=Box(
                Window(
                    content=FormattedTextControl(self._get_logs_text),
                    style="class:panel",
                ),
                padding=1,
            ),
            style="class:panel.frame",
            height=Dimension(min=8),
        )
        
        # 命令输入区域
        command_input = TextArea(
            height=Dimension.exact(3),
            prompt=">>> ",
            multiline=False,
            style="class:input",
        )
        
        # 主布局
        main_content = HSplit([
            # 顶部：左右面板
            VSplit([
                left_panel,
                right_panel,
            ], height=Dimension(min=10)),
            
            # 中部：日志面板
            log_panel,
            
            # 底部：命令输入
            Frame(
                title="命令输入",
                body=command_input,
                style="class:input.frame",
            ),
        ])
        
        # 完整布局
        full_layout = HSplit([
            title_bar,
            main_content,
            status_bar,
        ])
        
        return Layout(full_layout)

    def _setup_key_bindings(self):
        """设置键盘绑定"""
        
        @self.kb.add("c-c")
        @self.kb.add("c-q")
        def _(event):
            """Ctrl+C 或 Ctrl+Q 退出"""
            event.app.exit()
        
        @self.kb.add("c-r")
        def _(event):
            """Ctrl+R 刷新"""
            self.refresh_display()
        
        @self.kb.add("c-l")
        def _(event):
            """Ctrl+L 清屏"""
            self.log_panel.clear()
            self.refresh_display()
        
        @self.kb.add("up")
        def _(event):
            """上箭头 - 命令历史"""
            if self.command_history:
                self.history_index = max(0, self.history_index - 1)
                if self.history_index < len(self.command_history):
                    event.app.current_buffer.text = self.command_history[self.history_index]
        
        @self.kb.add("down")
        def _(event):
            """下箭头 - 命令历史"""
            if self.command_history:
                self.history_index = min(len(self.command_history), self.history_index + 1)
                if self.history_index < len(self.command_history):
                    event.app.current_buffer.text = self.command_history[self.history_index]
                else:
                    event.app.current_buffer.text = ""

    def _get_title_text(self) -> List[tuple]:
        """获取标题文本"""
        return [
            ("class:title.text", " CodeMCP - AI协同编排与执行控制台 "),
            ("class:title.time", f" {datetime.now().strftime('%H:%M:%S')} "),
        ]

    def _get_status_text(self) -> List[tuple]:
        """获取状态栏文本"""
        status = "运行中" if self.running else "已停止"
        return [
            ("class:status.mode", f" 模式: {status} "),
            ("class:status.help", " F1:帮助 | Ctrl+R:刷新 | Ctrl+L:清屏 | Ctrl+Q:退出 "),
        ]

    def _get_tasks_text(self) -> List[tuple]:
        """获取任务列表文本"""
        try:
            # 这里应该从数据库获取任务列表
            # 暂时返回模拟数据
            return [
                ("class:task.header", "ID\t状态\t命令\n"),
                ("class:task.item", "1\tpending\techo 'test'\n"),
                ("class:task.item", "2\trunning\tpython test.py\n"),
                ("class:task.item", "3\tpassed\tls -la\n"),
            ]
        except Exception as e:
            return [("class:error", f"获取任务失败: {str(e)}")]

    def _get_monitor_text(self) -> List[tuple]:
        """获取监控文本"""
        try:
            # 这里应该获取系统状态
            return [
                ("class:monitor.header", "系统状态监控\n"),
                ("class:monitor.item", f"任务引擎: {'运行中' if self.running else '停止'}\n"),
                ("class:monitor.item", f"窗口大小: {self.task_engine.task_window.size}\n"),
                ("class:monitor.item", f"运行中任务: {len(self.task_engine.running_tasks)}\n"),
                ("class:monitor.item", f"等待队列: {len(self.task_engine.task_window.waiting_queue)}\n"),
            ]
        except Exception as e:
            return [("class:error", f"获取监控数据失败: {str(e)}")]

    def _get_logs_text(self) -> List[tuple]:
        """获取日志文本"""
        return self.log_panel.get_content()

    async def refresh_display(self):
        """刷新显示"""
        if self.app:
            self.app.invalidate()

    async def handle_command(self, command: str) -> str:
        """处理命令"""
        command = command.strip()
        if not command:
            return ""
        
        # 添加到历史
        self.command_history.append(command)
        self.history_index = len(self.command_history)
        
        # 记录命令
        self.log_panel.add_log(f"> {command}")
        
        # 解析命令
        parts = command.split()
        cmd = parts[0].lower()
        args = parts[1:]
        
        try:
            if cmd == "help":
                return await self._cmd_help()
            elif cmd == "tasks":
                return await self._cmd_tasks(args)
            elif cmd == "status":
                return await self._cmd_status(args)
            elif cmd == "execute":
                return await self._cmd_execute(args)
            elif cmd == "cancel":
                return await self._cmd_cancel(args)
            elif cmd == "logs":
                return await self._cmd_logs(args)
            elif cmd == "clear":
                return await self._cmd_clear()
            elif cmd == "refresh":
                return await self._cmd_refresh()
            elif cmd == "monitor":
                return await self._cmd_monitor()
            elif cmd == "queue":
                return await self._cmd_queue()
            elif cmd in ["quit", "exit"]:
                return await self._cmd_quit()
            else:
                return f"未知命令: {cmd}。输入 'help' 查看可用命令。"
        except Exception as e:
            error_msg = f"命令执行错误: {str(e)}"
            self.log_panel.add_log(f"错误: {error_msg}")
            return error_msg

    async def _cmd_help(self) -> str:
        """帮助命令"""
        help_text = """
可用命令:
  help                    - 显示此帮助信息
  tasks [status]          - 显示任务列表（可选状态筛选）
  status <task_id>        - 显示任务状态
  execute <task_id>       - 执行任务
  cancel <task_id>        - 取消任务
  logs [lines]           - 显示日志（可选行数）
  clear                  - 清除日志
  refresh                - 刷新显示
  monitor                - 显示监控面板
  queue                  - 显示队列状态
  quit/exit              - 退出程序

快捷键:
  Ctrl+R                 - 刷新
  Ctrl+L                 - 清屏
  Ctrl+Q / Ctrl+C        - 退出
  ↑/↓                    - 命令历史
        """
        return help_text

    async def _cmd_tasks(self, args: List[str]) -> str:
        """任务列表命令"""
        status_filter = args[0] if args else None
        
        async for session in get_db_session():
            query = "SELECT * FROM tests"
            if status_filter:
                query += f" WHERE status = '{status_filter}'"
            query += " ORDER BY created_at DESC LIMIT 20"
            
            # 这里应该执行查询并返回结果
            # 暂时返回模拟数据
            return "任务列表:\n1. test-1 [pending]\n2. test-2 [running]\n3. test-3 [passed]"

    async def _cmd_status(self, args: List[str]) -> str:
        """任务状态命令"""
        if not args:
            return "请提供任务ID"
        
        task_id = args[0]
        status_info = await self.task_engine.get_task_status(task_id)
        
        if status_info:
            return f"任务 {task_id} 状态:\n" + "\n".join(
                f"  {k}: {v}" for k, v in status_info.items()
            )
        else:
            return f"任务 {task_id} 不存在或未在运行中"

    async def _cmd_execute(self, args: List[str]) -> str:
        """执行任务命令"""
        if not args:
            return "请提供任务ID"
        
        task_id = args[0]
        
        # 异步执行任务
        asyncio.create_task(self.task_engine.execute_task(task_id))
        
        return f"任务 {task_id} 已开始执行"

    async def _cmd_cancel(self, args: List[str]) -> str:
        """取消任务命令"""
        if not args:
            return "请提供任务ID"
        
        task_id = args[0]
        cancelled = await self.task_engine.cancel_task(task_id)
        
        if cancelled:
            return f"任务 {task_id} 已取消"
        else:
            return f"任务 {task_id} 未在运行中或不存在"

    async def _cmd_logs(self, args: List[str]) -> str:
        """日志命令"""
        lines = int(args[0]) if args else 10
        return f"显示最近 {lines} 条日志..."

    async def _cmd_clear(self) -> str:
        """清除命令"""
        self.log_panel.clear()
        return "日志已清除"

    async def _cmd_refresh(self) -> str:
        """刷新命令"""
        await self.refresh_display()
        return "显示已刷新"

    async def _cmd_monitor(self) -> str:
        """监控命令"""
        return "监控面板已显示"

    async def _cmd_queue(self) -> str:
        """队列命令"""
        queue_info = {
            "窗口大小": self.task_engine.task_window.size,
            "运行中任务": len(self.task_engine.running_tasks),
            "等待队列": len(self.task_engine.task_window.waiting_queue),
            "可用槽位": self.task_engine.task_window.available_slots,
        }
        
        return "队列状态:\n" + "\n".join(
            f"  {k}: {v}" for k, v in queue_info.items()
        )

    async def _cmd_quit(self) -> str:
        """退出命令"""
        self.running = False
        get_app().exit()
        return "正在退出..."

    async def run(self):
        """运行交互式控制台"""
        self.running = True
        
        try:
            # 启动刷新任务
            refresh_task = asyncio.create_task(self._refresh_loop())
            
            # 运行应用
            await self.app.run_async()
            
            # 取消刷新任务
            refresh_task.cancel()
            try:
                await refresh_task
            except asyncio.CancelledError:
                pass
            
        finally:
            self.running = False
            # 关闭任务引擎
            await self.task_engine.shutdown()

    async def _refresh_loop(self):
        """刷新循环"""
        while self.running:
            try:
                await asyncio.sleep(self.refresh_interval)
                await self.refresh_display()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"刷新循环错误: {e}")


def run_console():
    """运行控制台入口函数"""
    console = InteractiveConsole()
    
    try:
        # 运行事件循环
        asyncio.run(console.run())
    except KeyboardInterrupt:
        print("\n控制台已退出")
    except Exception as e:
        print(f"控制台运行错误: {e}")
        import traceback
        traceback.print_exc()