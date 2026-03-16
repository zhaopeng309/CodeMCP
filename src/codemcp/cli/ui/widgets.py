"""
UI 小部件

各种交互式小部件的实现。
"""

from typing import Callable, List, Optional

from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import (
    Window,
    WindowAlign,
    ConditionalContainer,
    FloatContainer,
    Float,
)
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.widgets import (
    Box,
    Button,
    Checkbox,
    Dialog,
    Label,
    MenuContainer,
    MenuItem,
    ProgressBar,
    RadioList,
    TextArea,
)


class HeaderWidget:
    """标题小部件"""

    def __init__(self, title: str = "CodeMCP Console", subtitle: Optional[str] = None):
        self.title = title
        self.subtitle = subtitle
        self._version = "0.1.0"

    def render(self) -> Window:
        """渲染标题"""
        lines = [
            "┌─────────────────────────────────────────────────────────────┐",
            f"│                    {self.title:^45}                    │",
        ]

        if self.subtitle:
            lines.append(f"│                    {self.subtitle:^45}                    │")

        lines.extend([
            f"│                    v{self._version:^43}                    │",
            "└─────────────────────────────────────────────────────────────┘",
        ])

        content = "\n".join(lines)
        return Window(
            content=FormattedTextControl(text=content),
            height=Dimension.exact(len(lines)),
            align=WindowAlign.CENTER,
            style="class:header",
        )


class StatusBarWidget:
    """状态栏小部件"""

    def __init__(self):
        self.messages = []
        self._mode = "normal"
        self._last_update = "刚刚"

    def set_mode(self, mode: str) -> None:
        """设置模式"""
        self._mode = mode

    def add_message(self, message: str) -> None:
        """添加消息"""
        self.messages.append(message)
        if len(self.messages) > 5:
            self.messages.pop(0)

    def render(self) -> Window:
        """渲染状态栏"""
        mode_text = {
            "normal": "普通模式",
            "monitor": "监控模式",
            "dashboard": "仪表板模式",
            "command": "命令模式",
        }.get(self._mode, self._mode)

        left_text = f" {mode_text} | 最后更新: {self._last_update}"
        right_text = "按 Ctrl+C 退出 | 按 F1 显示帮助 "

        # 计算填充
        total_width = 80  # 假设终端宽度
        padding = total_width - len(left_text) - len(right_text) - 2

        if padding > 0:
            status_text = left_text + " " * padding + right_text
        else:
            status_text = left_text + " " + right_text

        return Window(
            content=FormattedTextControl(text=status_text),
            height=Dimension.exact(1),
            style="class:statusbar",
        )


class ProgressWidget:
    """进度条小部件"""

    def __init__(self, total: int = 100, label: str = "进度"):
        self.total = total
        self.current = 0
        self.label = label
        self._width = 40

    def update(self, value: int) -> None:
        """更新进度"""
        self.current = max(0, min(value, self.total))

    def render(self) -> Window:
        """渲染进度条"""
        percentage = (self.current / self.total) * 100 if self.total > 0 else 0
        filled = int((self.current / self.total) * self._width) if self.total > 0 else 0
        empty = self._width - filled

        progress_bar = "█" * filled + "░" * empty
        text = f"{self.label}: [{progress_bar}] {percentage:.1f}% ({self.current}/{self.total})"

        return Window(
            content=FormattedTextControl(text=text),
            height=Dimension.exact(1),
            style="class:progress",
        )


class MenuWidget:
    """菜单小部件"""

    def __init__(self, items: List[dict], title: Optional[str] = None):
        self.items = items
        self.title = title
        self.selected_index = 0

    def navigate_up(self) -> None:
        """向上导航"""
        self.selected_index = max(0, self.selected_index - 1)

    def navigate_down(self) -> None:
        """向下导航"""
        self.selected_index = min(len(self.items) - 1, self.selected_index + 1)

    def get_selected(self) -> Optional[dict]:
        """获取选中的项"""
        if 0 <= self.selected_index < len(self.items):
            return self.items[self.selected_index]
        return None

    def render(self) -> Window:
        """渲染菜单"""
        lines = []

        if self.title:
            lines.append(f"[ {self.title} ]")
            lines.append("")

        for i, item in enumerate(self.items):
            prefix = "→ " if i == self.selected_index else "  "
            label = item.get("label", f"项目 {i}")
            shortcut = item.get("shortcut", "")
            if shortcut:
                label = f"{label} [{shortcut}]"

            if i == self.selected_index:
                line = f"{prefix}[bold]{label}[/bold]"
            else:
                line = f"{prefix}{label}"

            lines.append(line)

        content = "\n".join(lines)
        return Window(
            content=FormattedTextControl(text=content),
            style="class:menu",
        )


class HelpWidget:
    """帮助小部件"""

    def __init__(self):
        self.sections = {
            "全局快捷键": [
                ("Ctrl+C", "退出程序"),
                ("F1", "显示帮助"),
                ("F2", "切换模式"),
                ("Tab", "切换焦点"),
            ],
            "导航": [
                ("↑↓", "上下移动"),
                ("←→", "左右移动"),
                ("Enter", "选择/确认"),
                ("Esc", "返回/取消"),
            ],
            "模式": [
                ("普通模式", "查看信息和状态"),
                ("监控模式", "实时监控任务执行"),
                ("仪表板模式", "查看系统仪表板"),
                ("命令模式", "输入命令"),
            ],
        }

    def render(self) -> Window:
        """渲染帮助"""
        lines = ["[ 帮助 ]", ""]

        for section, items in self.sections.items():
            lines.append(f"[bold]{section}[/bold]")
            for key, description in items:
                lines.append(f"  {key:15} {description}")
            lines.append("")

        content = "\n".join(lines)
        return Window(
            content=FormattedTextControl(text=content),
            style="class:help",
        )


# 全局小部件实例
header_widget = HeaderWidget()
status_bar_widget = StatusBarWidget()
help_widget = HelpWidget()

# 导入 Dimension
from prompt_toolkit.layout.dimension import Dimension