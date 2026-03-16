"""
UI 面板组件

控制台UI的各种面板组件。
"""

from typing import List, Tuple
from datetime import datetime


class LogPanel:
    """日志面板"""
    
    def __init__(self, max_lines: int = 100):
        self.max_lines = max_lines
        self.logs: List[str] = []
    
    def add_log(self, message: str):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        
        # 限制日志数量
        if len(self.logs) > self.max_lines:
            self.logs = self.logs[-self.max_lines:]
    
    def clear(self):
        """清除日志"""
        self.logs.clear()
    
    def get_content(self, lines: int = 20) -> List[Tuple[str, str]]:
        """获取面板内容"""
        recent_logs = self.logs[-lines:] if self.logs else []
        content = []
        
        for log in recent_logs:
            content.append(("class:log", log + "\n"))
        
        if not content:
            content.append(("class:log.empty", "暂无日志\n"))
        
        return content


class TaskPanel:
    """任务面板"""
    
    def __init__(self):
        self.tasks = []
    
    def update_tasks(self, tasks):
        """更新任务列表"""
        self.tasks = tasks
    
    def get_content(self) -> List[Tuple[str, str]]:
        """获取面板内容"""
        content = [("class:panel.header", "任务列表\n")]
        
        if not self.tasks:
            content.append(("class:panel.empty", "暂无任务\n"))
            return content
        
        # 添加表头
        content.append(("class:table.header", "ID\t状态\t命令\n"))
        
        # 添加任务行
        for i, task in enumerate(self.tasks[:10]):  # 只显示前10个
            status_color = self._get_status_color(task.get('status', 'pending'))
            content.append((f"class:task.{task.get('status', 'pending')}", 
                          f"{task.get('id', i)}\t{task.get('status', 'pending')}\t{task.get('command', '')[:30]}...\n"))
        
        return content
    
    def _get_status_color(self, status: str) -> str:
        """根据状态获取颜色类"""
        color_map = {
            'pending': 'yellow',
            'running': 'blue',
            'passed': 'green',
            'failed': 'red',
        }
        return color_map.get(status, 'white')


class StatusPanel:
    """状态面板"""
    
    def __init__(self):
        self.metrics = {}
    
    def update_metrics(self, metrics):
        """更新指标"""
        self.metrics = metrics
    
    def get_content(self) -> List[Tuple[str, str]]:
        """获取面板内容"""
        content = [("class:panel.header", "系统状态\n")]
        
        # 添加指标
        metrics = self.metrics or {
            'task_engine': '运行中',
            'window_size': 5,
            'running_tasks': 0,
            'waiting_queue': 0,
            'available_slots': 5,
        }
        
        # 显示名称映射
        display_names = {
            'task_engine': '任务引擎',
            'window_size': '窗口大小',
            'running_tasks': '运行中任务',
            'waiting_queue': '等待队列',
            'available_slots': '可用槽位',
        }
        
        for key, value in metrics.items():
            display_name = display_names.get(key, key)
            content.append((f"class:metric.{key}", f"{display_name}: {value}\n"))
        
        return content


class MonitorPanel:
    """监控面板"""
    
    def __init__(self):
        self.data = {}
    
    def update_data(self, data):
        """更新监控数据"""
        self.data = data
    
    def get_content(self) -> List[Tuple[str, str]]:
        """获取面板内容"""
        content = [("class:panel.header", "实时监控\n")]
        
        if not self.data:
            content.append(("class:panel.empty", "暂无监控数据\n"))
            return content
        
        # 添加监控数据
        for key, value in self.data.items():
            content.append((f"class:monitor.{key}", f"{key}: {value}\n"))
        
        return content