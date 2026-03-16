"""
UI 布局管理

prompt-toolkit 布局组件和布局管理器。
"""

from typing import List, Optional

from prompt_toolkit.layout import (
    HSplit,
    VSplit,
    Window,
    WindowAlign,
    FloatContainer,
    Float,
)
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.widgets import Box, Frame


class LayoutManager:
    """布局管理器"""

    def __init__(self):
        self.components = {}

    def create_main_layout(self) -> HSplit:
        """创建主布局"""
        # 标题栏
        title_bar = Window(
            content=FormattedTextControl(text=self._get_title_text),
            height=Dimension.exact(1),
            align=WindowAlign.CENTER,
            style="class:title",
        )

        # 状态栏
        status_bar = Window(
            content=FormattedTextControl(text=self._get_status_text),
            height=Dimension.exact(1),
            style="class:status",
        )

        # 主内容区域（待实现）
        content_area = Window(
            content=FormattedTextControl(text="CodeMCP Console - 交互式界面\n\n功能尚未实现"),
            style="class:content",
        )

        # 构建布局
        layout = HSplit([
            title_bar,
            Box(content_area, padding=1),
            status_bar,
        ])

        return layout

    def _get_title_text(self) -> str:
        """获取标题文本"""
        return "┌─────────────────────────────────────────────────────────────┐\n" \
               "│                    CodeMCP Console                          │\n" \
               "└─────────────────────────────────────────────────────────────┘"

    def _get_status_text(self) -> str:
        """获取状态栏文本"""
        return " 按 Ctrl+C 退出 | 按 F1 显示帮助 | 状态: 就绪"


class DashboardLayout:
    """仪表板布局"""

    def __init__(self):
        self.sections = {}

    def create_dashboard(self) -> HSplit:
        """创建仪表板布局"""
        # 系统状态面板
        system_status = Frame(
            title="系统状态",
            body=Window(
                content=FormattedTextControl(text="• 用户管理系统: 正常\n• 订单系统: 正常\n• 库存系统: 已归档"),
                height=Dimension.exact(4),
            ),
        )

        # 任务队列面板
        task_queue = Frame(
            title="任务队列",
            body=Window(
                content=FormattedTextControl(text="待处理: 12\n处理中: 3\n成功率: 94.7%"),
                height=Dimension.exact(4),
            ),
        )

        # 实时监控面板
        realtime_monitor = Frame(
            title="实时监控",
            body=Window(
                content=FormattedTextControl(text="最近任务:\n• 任务001: 成功\n• 任务002: 运行中\n• 任务003: 失败"),
                height=Dimension.exact(5),
            ),
        )

        # 第一行：系统状态 + 任务队列
        first_row = VSplit([
            Box(system_status, padding=1),
            Box(task_queue, padding=1),
        ], height=Dimension.exact(6))

        # 第二行：实时监控
        second_row = Box(realtime_monitor, padding=1)

        # 底部状态栏
        status_bar = Window(
            content=FormattedTextControl(text="仪表板模式 | 自动刷新: 2秒 | 最后更新: 刚刚"),
            height=Dimension.exact(1),
            style="class:status",
        )

        return HSplit([
            first_row,
            second_row,
            status_bar,
        ])


# 全局布局管理器实例
layout_manager = LayoutManager()
dashboard_layout = DashboardLayout()