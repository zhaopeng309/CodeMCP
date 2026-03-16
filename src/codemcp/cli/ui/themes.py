"""
UI 主题样式

控制台UI的主题和样式定义。
"""


def get_theme_style():
    """获取主题样式"""
    return {
        # 基础样式
        "title": "bg:#4444ff #ffffff bold",
        "title.text": "#ffffff bold",
        "title.time": "#aaaaaa",
        
        "status": "bg:#333333 #aaaaaa",
        "status.mode": "#00ff00",
        "status.help": "#aaaaaa",
        
        # 面板样式
        "panel": "bg:#1e1e1e #cccccc",
        "panel.frame": "bg:#2d2d2d #ffffff",
        "panel.header": "#ffff00 bold",
        "panel.empty": "#888888 italic",
        
        # 表格样式
        "table.header": "#00ffff bold",
        
        # 任务状态颜色
        "task.pending": "#ffff00",  # 黄色
        "task.running": "#00ffff",  # 青色
        "task.passed": "#00ff00",   # 绿色
        "task.failed": "#ff0000",   # 红色
        
        # 日志样式
        "log": "#cccccc",
        "log.empty": "#888888 italic",
        
        # 指标样式
        "metric.任务引擎": "#00ff00",
        "metric.窗口大小": "#00ffff",
        "metric.运行中任务": "#ffff00",
        "metric.等待队列": "#ffaa00",
        "metric.可用槽位": "#00ff00",
        
        # 监控样式
        "monitor": "#cccccc",
        
        # 输入样式
        "input": "bg:#2d2d2d #ffffff",
        "input.frame": "bg:#3d3d3d #ffffff",
        
        # 错误样式
        "error": "#ff0000",
        
        # 滚动条
        "scrollbar.background": "bg:#333333",
        "scrollbar.button": "bg:#666666",
        "scrollbar.arrow": "#ffffff",
    }


def get_dark_theme():
    """获取深色主题"""
    return get_theme_style()


def get_light_theme():
    """获取浅色主题"""
    style = get_theme_style()
    # 修改为浅色主题
    style.update({
        "title": "bg:#4444ff #000000 bold",
        "status": "bg:#dddddd #333333",
        "panel": "bg:#f0f0f0 #000000",
        "panel.frame": "bg:#e0e0e0 #000000",
        "input": "bg:#ffffff #000000",
        "input.frame": "bg:#f0f0f0 #000000",
    })
    return style


def get_monokai_theme():
    """获取Monokai主题"""
    return {
        "title": "bg:#272822 #f8f8f2 bold",
        "title.text": "#f8f8f2 bold",
        "title.time": "#75715e",
        
        "status": "bg:#3e3d32 #f8f8f2",
        "status.mode": "#a6e22e",
        "status.help": "#75715e",
        
        "panel": "bg:#272822 #f8f8f2",
        "panel.frame": "bg:#3e3d32 #f8f8f2",
        "panel.header": "#f92672 bold",
        "panel.empty": "#75715e italic",
        
        "table.header": "#66d9ef bold",
        
        "task.pending": "#fd971f",
        "task.running": "#66d9ef",
        "task.passed": "#a6e22e",
        "task.failed": "#f92672",
        
        "log": "#f8f8f2",
        "log.empty": "#75715e italic",
        
        "metric.任务引擎": "#a6e22e",
        "metric.窗口大小": "#66d9ef",
        "metric.运行中任务": "#fd971f",
        "metric.等待队列": "#ae81ff",
        "metric.可用槽位": "#a6e22e",
        
        "input": "bg:#3e3d32 #f8f8f2",
        "input.frame": "bg:#49483e #f8f8f2",
        
        "error": "#f92672",
    }