"""
交互式控制台 UI

基于 prompt-toolkit 的交互式控制台界面。
"""

import asyncio
import concurrent.futures
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
    ConditionalContainer,
    DynamicContainer,
    ScrollablePane,
)
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.filters import Condition
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
        
        # 日志缓存 - 用于避免不必要的字符串拼接
        self._log_cache = ""
        self._log_cache_timestamp = 0
        
        # 树状图缓存 - 用于避免每次重绘都查询数据库
        self._tree_cache = [("class:tree.empty", "正在加载任务树...\n")]
        
        # 当前窗口宽度 - 用于实时响应窗口大小变化
        self.current_width = self._get_terminal_width()
        
        # 宽度更新节流时间戳
        self._last_width_update = 0.0
        
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
    
    def _get_terminal_width(self) -> int:
        """获取终端宽度"""
        try:
            import shutil
            return shutil.get_terminal_size().columns
        except:
            return 80
    
    def _get_terminal_height(self) -> int:
        """获取终端高度"""
        try:
            import shutil
            return shutil.get_terminal_size().lines
        except:
            return 24
    
    def _is_small_window(self) -> bool:
        """判断是否为小窗口"""
        return self._get_terminal_width() < 80 or self._get_terminal_height() < 24
    
    def _is_medium_window(self) -> bool:
        """判断是否为中等窗口"""
        width = self._get_terminal_width()
        height = self._get_terminal_height()
        return width >= 80 and height >= 24 and (width < 120 or height < 30)
    
    def _is_large_window(self) -> bool:
        """判断是否为大窗口"""
        width = self._get_terminal_width()
        height = self._get_terminal_height()
        return width >= 120 and height >= 30

    def _create_application(self) -> Application:
        """创建 prompt-toolkit 应用"""
        
        # 创建布局
        layout = self._create_layout()
        
        # 创建样式
        style = Style.from_dict(get_theme_style())
        
        # 创建应用
        app = Application(
            layout=layout,
            key_bindings=self.kb,
            style=style,
            full_screen=True,
            mouse_support=True,
            min_redraw_interval=0.01,  # 更快的重绘
        )
        
        # 设置初始焦点到命令输入区域
        # 在应用启动后立即设置焦点
        def set_initial_focus():
            if hasattr(self, 'command_input') and self.command_input:
                try:
                    # 尝试设置焦点到命令输入区域
                    app.layout.focus(self.command_input)
                except Exception as e:
                    logger.warning(f"设置初始焦点失败: {e}")
        
        # 在应用准备好后设置焦点
        app.after_render += lambda app: set_initial_focus()
        
        # 监听窗口大小变化事件 - 实时更新当前宽度
        # on_invalidate 是一个 Event 对象，使用 += 操作符添加事件处理器
        def _on_invalidate(sender=None):
            # 节流逻辑：避免频繁调用
            import time
            current_time = time.time()
            if hasattr(self, '_last_width_update'):
                # 至少间隔 0.1 秒才更新一次
                if current_time - self._last_width_update < 0.1:
                    return
            self._last_width_update = current_time

            # 更新当前宽度
            try:
                if hasattr(app, 'output') and app.output:
                    size = app.output.get_size()
                    if size:
                        self.current_width = size.columns
            except:
                # 如果获取失败，使用默认方法
                self.current_width = self._get_terminal_width()
        
        # 使用 += 操作符添加事件处理器，忽略类型检查错误
        app.on_invalidate += _on_invalidate  # type: ignore
        
        return app

    def _create_layout(self) -> Layout:
        """创建控制台布局 - 仅保留中等布局，使用VSplit嵌套HSplit"""
        
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
        
        # 左侧任务树 - 根据用户建议使用Window + FormattedTextControl，并包装在ScrollablePane中支持滚动
        left_tree_window = Window(
            content=FormattedTextControl(self._get_tree_text),
            width=Dimension(min=20, weight=1),  # 最小宽度20，权重1（占总宽度1/4）
            wrap_lines=False,  # 树状结构不能自动换行
            style="class:tree-panel",
        )
        
        # 将Window包装在ScrollablePane中，支持垂直滚动
        left_tree = ScrollablePane(
            content=left_tree_window,
            height=Dimension(min=10),  # 最小高度10行，实际高度会根据可用空间自动调整
            show_scrollbar=True,       # 显示滚动条
        )
        
        # 日志面板 - 使用TextArea支持滚动
        # TextArea本身就支持滚动功能，使用起来更简单
        self.log_text_area = TextArea(
            text="",  # 初始为空，通过_update_log_text方法更新
            style="class:panel",
            wrap_lines=True,  # 自动换行
            read_only=True,   # 只读模式
            scrollbar=True,   # 显示滚动条
            multiline=True,   # 多行模式
            focusable=True,   # 可聚焦，以便光标位置生效
            focus_on_click=False,  # 点击时不获取焦点
        )
        
        # TextArea本身就是一个容器，可以直接在布局中使用
        log_window = self.log_text_area
        
        # 命令输入区域 - 根据用户建议使用height=1
        self.command_input = TextArea(
            height=1,
            prompt="code_shell> ",
            multiline=False,
            style="class:input",
            accept_handler=self._handle_command_input,
            focusable=True,   # 可聚焦
            focus_on_click=True,  # 点击时获取焦点
        )
        command_input = self.command_input
        
        # 右侧主体布局 - 使用HSplit垂直分割日志区和输入区
        right_body = HSplit([
            # 日志区：权重设为最高，占据剩余所有空间
            log_window,
            
            # 分割线（可选）：增加视觉区分
            Window(height=1, char="-", style="class:line"),
            
            # 输入区：固定高度
            command_input,
        ], width=Dimension(weight=3))  # 日志区宽度占比更大
        
        # 创建条件：窗口宽度大于等于50时才显示左侧树
        # 使用实时更新的 current_width 而不是每次调用 _get_terminal_width()
        def show_left_tree():
            return getattr(self, 'current_width', 80) >= 50
        
        # 焦点管理：当左侧树隐藏时，焦点应该自动转移到右侧日志区
        # 创建一个动态焦点管理器
        from prompt_toolkit.layout import DynamicContainer
        
        def get_main_layout():
            """动态生成主布局，根据窗口宽度决定是否包含左侧树"""
            if show_left_tree():
                # 窗口宽度足够，显示左侧树
                return VSplit([
                    # 左侧树：窗口宽度>=50时显示
                    left_tree,
                    # 右侧主体：始终显示
                    right_body,
                ], width=Dimension(weight=1))
            else:
                # 窗口宽度不足，只显示右侧主体
                # 焦点自动转移到右侧日志区
                return right_body
        
        # 使用DynamicContainer实现动态布局
        main_layout = DynamicContainer(get_main_layout)
        
        # 完整布局：标题 + 主内容 + 状态栏
        full_layout = HSplit([
            title_bar,
            main_layout,
            status_bar,
        ])
        
        # 仅返回中等布局（不再根据窗口大小动态切换）
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
            asyncio.create_task(self.refresh_display())
        
        @self.kb.add("c-l")
        def _(event):
            """Ctrl+L 清屏"""
            self.log_panel.clear()
            asyncio.create_task(self.refresh_display())
        
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
        
        # 检查是否为窄屏模式
        is_narrow = getattr(self, 'current_width', 80) < 50
        
        status_items = [
            ("class:status.mode", f" 模式: {status} "),
        ]
        
        # 如果是窄屏模式，添加警告
        if is_narrow:
            status_items.append(("class:status.warning", " ⚠️窄屏模式 "))
        
        status_items.append(("class:status.help", " F1:帮助 | Ctrl+R:刷新 | Ctrl+L:清屏 | Ctrl+Q:退出 "))
        
        return status_items

    def _get_help_text(self) -> List[tuple]:
        """获取帮助文本"""
        return [
            ("class:help.item", "可用命令: "),
            ("class:help.command", "help "),
            ("class:help.text", "- 显示帮助信息"),
            ("class:help.command", " | tasks "),
            ("class:help.text", "- 任务列表"),
            ("class:help.command", " | status "),
            ("class:help.text", "- 系统状态"),
            ("class:help.command", " | execute "),
            ("class:help.text", "- 执行任务"),
            ("class:help.command", " | cancel "),
            ("class:help.text", "- 取消任务"),
            ("class:help.command", " | logs "),
            ("class:help.text", "- 查看日志"),
            ("class:help.command", " | clear "),
            ("class:help.text", "- 清屏"),
            ("class:help.command", " | refresh "),
            ("class:help.text", "- 刷新"),
            ("class:help.command", " | quit/exit "),
            ("class:help.text", "- 退出\n"),
            ("class:help.item", "提示: 在 "),
            ("class:help.command", "code_shell> "),
            ("class:help.text", "提示符后输入命令，按Enter执行"),
        ]

    async def _get_tasks_text(self) -> List[tuple]:
        """获取任务列表文本 - 使用真实数据库数据"""
        try:
            from sqlalchemy import select, desc
            from ..models.test import TestModel, TestStatus
            from ..database.session import AsyncSessionFactory
            
            # 从数据库获取最近的任务
            tasks = []
            async with AsyncSessionFactory() as session:
                stmt = select(TestModel).order_by(desc(TestModel.created_at)).limit(10)
                result = await session.execute(stmt)
                db_tasks = result.scalars().all()
                
                # 添加表头
                tasks.append(("class:task.header", "ID\t状态\t命令\t创建时间\n"))
                
                # 添加任务数据
                for task in db_tasks:
                    task_id = str(task.id)[:8]  # 缩短ID显示
                    status = task.status.value if task.status else "unknown"
                    command = task.command[:30] + "..." if task.command and len(task.command) > 30 else (task.command or "N/A")
                    created_at = task.created_at.strftime("%H:%M") if task.created_at else "N/A"
                    
                    # 根据状态设置不同的样式类
                    status_class = "class:task.status."
                    if status == "passed":
                        status_class += "success"
                    elif status == "failed":
                        status_class += "error"
                    elif status == "running":
                        status_class += "warning"
                    else:
                        status_class += "info"
                    
                    tasks.append(("class:task.item", f"{task_id}\t"))
                    tasks.append((status_class, f"{status}\t"))
                    tasks.append(("class:task.item", f"{command}\t{created_at}\n"))
            
            if len(tasks) == 1:  # 只有表头，没有任务
                tasks.append(("class:task.empty", "暂无任务\n"))
                
            return tasks
        except Exception as e:
            logger.error(f"获取任务列表失败: {e}")
            return [
                ("class:task.header", "ID\t状态\t命令\t创建时间\n"),
                ("class:error", f"获取任务失败: {str(e)[:50]}...\n")
            ]

    def _run_async_in_thread(self, async_func):
        """在线程中运行异步函数"""
        import asyncio
        return asyncio.run(async_func())
    
    def _get_tasks_text_sync(self) -> List[tuple]:
        """同步包装器，用于 FormattedTextControl"""
        try:
            # 使用线程池执行异步函数，避免事件循环冲突
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self._run_async_in_thread, self._get_tasks_text)
                return future.result(timeout=3)  # 3秒超时
        except concurrent.futures.TimeoutError:
            logger.warning("获取任务列表超时")
            return [
                ("class:task.header", "ID\t状态\t命令\t创建时间\n"),
                ("class:error", "获取超时，请稍后重试...\n")
            ]
        except Exception as e:
            logger.error(f"同步获取任务失败: {e}")
            return [
                ("class:task.header", "ID\t状态\t命令\t创建时间\n"),
                ("class:error", f"获取失败: {str(e)[:30]}...\n")
            ]

    async def _get_monitor_text(self) -> List[tuple]:
        """获取监控文本 - 使用真实数据"""
        try:
            from sqlalchemy import select, func
            from ..models.test import TestModel, TestStatus
            from ..models.system import SystemModel
            from ..models.block import BlockModel
            from ..models.feature import FeatureModel
            from ..database.session import AsyncSessionFactory
            
            monitor_data = []
            async with AsyncSessionFactory() as session:
                # 获取系统统计
                sys_count_result = await session.scalar(select(func.count(SystemModel.id)))
                block_count_result = await session.scalar(select(func.count(BlockModel.id)))
                feature_count_result = await session.scalar(select(func.count(FeatureModel.id)))
                
                # 获取任务统计
                total_tasks_result = await session.scalar(select(func.count(TestModel.id)))
                pending_tasks_result = await session.scalar(
                    select(func.count(TestModel.id)).where(TestModel.status == TestStatus.PENDING)
                )
                running_tasks_result = await session.scalar(
                    select(func.count(TestModel.id)).where(TestModel.status == TestStatus.RUNNING)
                )
                passed_tasks_result = await session.scalar(
                    select(func.count(TestModel.id)).where(TestModel.status == TestStatus.PASSED)
                )
                
                # 处理可能的 None 值
                sys_count = sys_count_result or 0
                block_count = block_count_result or 0
                feature_count = feature_count_result or 0
                total_tasks = total_tasks_result or 0
                pending_tasks = pending_tasks_result or 0
                running_tasks = running_tasks_result or 0
                passed_tasks = passed_tasks_result or 0
                
                # 计算成功率
                success_rate = 0.0
                if total_tasks > 0 and passed_tasks > 0:
                    success_rate = (passed_tasks / total_tasks) * 100
                
                monitor_data = [
                    ("class:monitor.header", "系统状态监控\n"),
                    ("class:monitor.item", f"系统数量: {sys_count}\n"),
                    ("class:monitor.item", f"模块数量: {block_count}\n"),
                    ("class:monitor.item", f"功能数量: {feature_count}\n"),
                    ("class:monitor.item", f"总任务数: {total_tasks}\n"),
                    ("class:monitor.item", f"待处理: {pending_tasks}\n"),
                    ("class:monitor.item", f"运行中: {running_tasks}\n"),
                    ("class:monitor.item", f"成功率: {success_rate:.1f}%\n"),
                ]
                
            return monitor_data
        except Exception as e:
            logger.error(f"获取监控数据失败: {e}")
            return [
                ("class:monitor.header", "系统状态监控\n"),
                ("class:error", f"获取监控数据失败: {str(e)[:50]}...\n")
            ]

    def _get_monitor_text_sync(self) -> List[tuple]:
        """同步包装器，用于 FormattedTextControl"""
        try:
            # 使用线程池执行异步函数，避免事件循环冲突
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self._run_async_in_thread, self._get_monitor_text)
                return future.result(timeout=3)  # 3秒超时
        except concurrent.futures.TimeoutError:
            logger.warning("获取监控数据超时")
            return [
                ("class:monitor.header", "系统状态监控\n"),
                ("class:error", "获取超时，请稍后重试...\n")
            ]
        except Exception as e:
            logger.error(f"同步获取监控数据失败: {e}")
            return [
                ("class:monitor.header", "系统状态监控\n"),
                ("class:error", f"获取失败: {str(e)[:30]}...\n")
            ]

    async def _fetch_tree_data_async(self) -> List[tuple]:
        """异步获取树状图数据 - 用于后台更新缓存"""
        try:
            from sqlalchemy import select
            from ..models.system import SystemModel
            from ..models.block import BlockModel
            from ..models.feature import FeatureModel
            from ..models.test import TestModel
            from ..database.session import AsyncSessionFactory
            
            lines = []
            
            async with AsyncSessionFactory() as session:
                # 获取所有系统
                stmt = select(SystemModel).order_by(SystemModel.name)
                result = await session.execute(stmt)
                systems = result.scalars().all()
                
                for i, system in enumerate(systems):
                    # 系统层
                    is_last_system = i == len(systems) - 1
                    prefix = "└── " if is_last_system else "├── "
                    lines.append(("class:tree.system", f"{prefix}{system.name}\n"))
                    
                    # 获取该系统的所有模块
                    stmt = select(BlockModel).where(BlockModel.system_id == system.id).order_by(BlockModel.name)
                    result = await session.execute(stmt)
                    blocks = result.scalars().all()
                    
                    for j, block in enumerate(blocks):
                        # 模块层
                        is_last_block = j == len(blocks) - 1
                        system_prefix = "    " if is_last_system else "│   "
                        block_prefix = "└── " if is_last_block else "├── "
                        lines.append(("class:tree.block", f"{system_prefix}{block_prefix}{block.name}\n"))
                        
                        # 获取该模块的所有功能点
                        stmt = select(FeatureModel).where(FeatureModel.block_id == block.id).order_by(FeatureModel.name)
                        result = await session.execute(stmt)
                        features = result.scalars().all()
                        
                        for k, feature in enumerate(features):
                            # 功能点层
                            is_last_feature = k == len(features) - 1
                            block_prefix_line = "    " if is_last_block else "│   "
                            feature_prefix = "└── " if is_last_feature else "├── "
                            status_color = self._get_feature_status_color(feature.status.value if feature.status else "pending")
                            lines.append((status_color, f"{system_prefix}{block_prefix_line}{feature_prefix}{feature.name}\n"))
                            
                            # 获取该功能点的所有测试任务
                            stmt = select(TestModel).where(TestModel.feature_id == feature.id).order_by(TestModel.created_at.desc()).limit(3)
                            result = await session.execute(stmt)
                            tests = result.scalars().all()
                            
                            for l, test in enumerate(tests):
                                # 测试任务层
                                is_last_test = l == len(tests) - 1
                                feature_prefix_line = "    " if is_last_feature else "│   "
                                test_prefix = "└── " if is_last_test else "├── "
                                test_status_color = self._get_test_status_color(test.status.value if test.status else "unknown")
                                test_id = str(test.id)[:8]
                                lines.append((test_status_color, f"{system_prefix}{block_prefix_line}{feature_prefix_line}{test_prefix}{test_id}: {test.command[:20] if test.command else 'N/A'}\n"))
            
            if not lines:
                lines.append(("class:tree.empty", "暂无任务数据\n"))
                
            return lines
        except Exception as e:
            logger.error(f"获取任务树数据失败: {e}")
            return [("class:tree.error", f"获取任务树失败: {str(e)[:50]}...\n")]
    
    def _get_tree_text(self) -> List[tuple]:
        """获取任务树文本 - 直接返回缓存数据，避免阻塞UI"""
        return self._tree_cache
    
    def _get_feature_status_color(self, status: str) -> str:
        """根据功能点状态获取颜色类"""
        if status == "passed":
            return "class:tree.status.success"
        elif status == "failed":
            return "class:tree.status.error"
        elif status == "running":
            return "class:tree.status.warning"
        else:
            return "class:tree.status.info"
    
    def _get_test_status_color(self, status: str) -> str:
        """根据测试任务状态获取颜色类"""
        if status == "passed":
            return "class:tree.status.success"
        elif status == "failed":
            return "class:tree.status.error"
        elif status == "running":
            return "class:tree.status.warning"
        else:
            return "class:tree.status.info"
    
    def _get_logs_text(self) -> List[tuple]:
        """获取日志文本 - 返回所有日志以便ScrollablePane正确计算高度"""
        # 返回所有日志，让ScrollablePane能够正确计算内容高度
        # LogPanel默认存储最多100条日志，我们返回所有日志
        return self.log_panel.get_content(lines=100)

    async def refresh_display(self):
        """刷新显示"""
        # 先更新日志TextArea的内容
        self._update_log_text()
        if self.app:
            self.app.invalidate()
            # 在重绘后尝试滚动到底部，防止滚动位置被重置
            async def delayed_scroll():
                await asyncio.sleep(0.05)  # 短暂延迟，等待重绘完成
                self._scroll_log_to_bottom()
            asyncio.create_task(delayed_scroll())
    
    def _update_log_text(self):
        """更新日志TextArea的内容 - 使用缓存避免不必要的字符串拼接"""
        if hasattr(self, 'log_text_area'):
            # 获取所有日志内容
            logs = self.log_panel.get_content(lines=100)

            # 检查日志是否有更新（通过比较长度）
            current_log_count = len(logs)
            # 使用日志数量作为简单的更新检测
            # 如果日志数量发生变化，或者缓存为空，则更新
            if (current_log_count != self._log_cache_timestamp or
                not self._log_cache or
                not hasattr(self, '_log_cache_timestamp')):

                # 将格式化的日志转换为纯文本
                text_lines = []
                for style, content in logs:
                    text_lines.append(content)
                text = ''.join(text_lines)

                # 更新缓存
                self._log_cache = text
                self._log_cache_timestamp = current_log_count

                # 更新TextArea
                self.log_text_area.text = text

                # 自动滚动到底部，显示最新的日志
                # 将光标位置设置为文档末尾，这样TextArea会自动滚动到该位置
                if hasattr(self.log_text_area, 'buffer') and hasattr(self.log_text_area.buffer, 'cursor_position'):
                    self.log_text_area.buffer.cursor_position = len(text)
                # 尝试使用其他方法滚动到底部
                self._scroll_log_to_bottom()
            else:
                # 日志没有变化，使用缓存
                self.log_text_area.text = self._log_cache
                # 即使日志没有变化，也要确保滚动到底部
                if hasattr(self.log_text_area, 'buffer') and hasattr(self.log_text_area.buffer, 'cursor_position'):
                    self.log_text_area.buffer.cursor_position = len(self._log_cache)
                # 尝试使用其他方法滚动到底部
                self._scroll_log_to_bottom()

    def _scroll_log_to_bottom(self):
        """尝试将日志区域滚动到底部"""
        if not hasattr(self, 'log_text_area'):
            return
        try:
            # 方法1：通过buffer光标位置
            if hasattr(self.log_text_area, 'buffer') and hasattr(self.log_text_area.buffer, 'cursor_position'):
                text = self.log_text_area.text
                self.log_text_area.buffer.cursor_position = len(text)
            # 方法2：尝试访问vertical_scroll属性（如果存在）
            if hasattr(self.log_text_area, 'vertical_scroll'):
                # 假设vertical_scroll是一个整数，设置一个较大值
                self.log_text_area.vertical_scroll = 10000  # type: ignore
            # 方法3：尝试调用scroll_to_bottom方法（如果存在）
            if hasattr(self.log_text_area, 'scroll_to_bottom'):
                self.log_text_area.scroll_to_bottom()  # type: ignore
        except Exception:
            pass  # 忽略所有错误，滚动不是关键功能

    def _handle_command_input(self, buffer: Buffer) -> bool:
        """处理命令输入（TextArea accept_handler）"""
        command = buffer.text.strip()
        if command:
            # 异步处理命令
            asyncio.create_task(self._process_command_async(command))
            # 清空输入缓冲区
            buffer.text = ""
        return True  # 保持焦点

    async def _process_command_async(self, command: str):
        """异步处理命令"""
        try:
            result = await self.handle_command(command)
            if result:
                self.log_panel.add_log(result)
        except Exception as e:
            error_msg = f"命令处理错误: {str(e)}"
            self.log_panel.add_log(f"错误: {error_msg}")

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
                # 如果不是已知命令，尝试作为 bash 命令执行
                return await self._execute_bash_command(command)
        except Exception as e:
            error_msg = f"命令执行错误: {str(e)}"
            self.log_panel.add_log(f"错误: {error_msg}")
            return error_msg
    
    async def _execute_bash_command(self, command: str) -> str:
        """执行 bash 命令"""
        import subprocess
        import asyncio
        import os
        
        self.log_panel.add_log(f"执行 bash 命令: {command}")
        
        try:
            # 使用 asyncio 创建子进程执行命令
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.getcwd()  # 使用当前工作目录
            )
            
            # 等待命令完成并获取输出
            stdout, stderr = await process.communicate()
            
            # 解码输出
            output = ""
            if stdout:
                output += stdout.decode('utf-8', errors='replace')
            if stderr:
                output += stderr.decode('utf-8', errors='replace')
            
            # 添加退出码信息
            exit_code = process.returncode
            if exit_code != 0:
                output += f"\n[退出码: {exit_code}]"
            
            # 记录到日志面板
            if output:
                # 限制输出长度，避免界面卡顿
                display_output = output[:500] + "..." if len(output) > 500 else output
                self.log_panel.add_log(display_output)
            
            return output if output else f"命令执行完成 (退出码: {exit_code})"
            
        except Exception as e:
            error_msg = f"执行 bash 命令失败: {str(e)}"
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
        
        try:
            from sqlalchemy import select, desc
            from ..models.test import TestModel, TestStatus
            
            tasks_info = []
            async for session in get_db_session():
                stmt = select(TestModel).order_by(desc(TestModel.created_at)).limit(20)
                if status_filter:
                    # 尝试将状态字符串转换为 TestStatus 枚举
                    try:
                        filter_status = TestStatus(status_filter.lower())
                        stmt = stmt.where(TestModel.status == filter_status)
                    except ValueError:
                        return f"错误: 无效的状态筛选器 '{status_filter}'。可用状态: {', '.join([s.value for s in TestStatus])}"
                
                result = await session.execute(stmt)
                db_tasks = result.scalars().all()
                
                if not db_tasks:
                    return "暂无任务"
                
                tasks_info.append("任务列表:")
                for i, task in enumerate(db_tasks, 1):
                    task_id = str(task.id)
                    status = task.status.value if task.status else "unknown"
                    command = task.command[:50] + "..." if task.command and len(task.command) > 50 else (task.command or "N/A")
                    created_at = task.created_at.strftime("%Y-%m-%d %H:%M") if task.created_at else "N/A"
                    
                    tasks_info.append(f"{i}. {task_id} [{status}] - {command} ({created_at})")
                
                return "\n".join(tasks_info)
            
            return "无法连接到数据库"
        except Exception as e:
            logger.error(f"获取任务列表失败: {e}")
            return f"获取任务列表失败: {str(e)}"

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
            # 启动静默加载任务（后台更新树缓存）
            update_task = asyncio.create_task(self._update_loop())
            # 启动刷新任务（定期刷新显示）
            refresh_task = asyncio.create_task(self._refresh_loop())
            
            # 运行应用
            await self.app.run_async()
            
            # 取消所有后台任务
            refresh_task.cancel()
            update_task.cancel()
            try:
                await asyncio.gather(refresh_task, update_task, return_exceptions=True)
            except asyncio.CancelledError:
                pass
            
        finally:
            self.running = False
            # 关闭任务引擎
            await self.task_engine.shutdown()

    async def _refresh_loop(self):
        """刷新循环 - 仅负责刷新显示，不更新树缓存"""
        while self.running:
            try:
                # 等待刷新间隔
                await asyncio.sleep(self.refresh_interval)
                
                # 刷新显示
                await self.refresh_display()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"刷新循环错误: {e}")

    async def _update_loop(self):
        """静默加载循环 - 独立后台更新树缓存，不阻塞UI"""
        update_interval = 5.0  # 树缓存更新间隔（秒），比显示刷新间隔长
        
        while self.running:
            try:
                # 异步获取数据并更新缓存，不阻塞 UI 渲染
                try:
                    new_tree_data = await self._fetch_tree_data_async()
                    self._tree_cache = new_tree_data
                    logger.debug(f"树缓存已更新，包含 {len(new_tree_data)} 个格式项")
                except Exception as e:
                    logger.error(f"更新树缓存错误: {e}")
                    # 如果更新失败，保持现有缓存
                
                # 等待更新间隔
                await asyncio.sleep(update_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"静默加载循环错误: {e}")


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