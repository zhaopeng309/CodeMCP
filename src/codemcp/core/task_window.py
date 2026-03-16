"""
任务窗口化执行机制

管理固定大小的执行窗口，限制并发任务数量。
"""

import asyncio
from collections import deque
from typing import Deque, Optional, Set

from ..exceptions import TaskWindowFullError


class TaskWindow:
    """任务窗口管理器"""

    def __init__(self, size: int = 5) -> None:
        """初始化任务窗口

        Args:
            size: 窗口大小（最大并发任务数）
        """
        self.size = size
        self.running_tasks: Set[str] = set()  # 正在运行的任务 ID 集合
        self.waiting_queue: Deque[str] = deque()  # 等待队列
        self._lock = asyncio.Lock()

    @property
    def available_slots(self) -> int:
        """可用窗口槽位数量"""
        return self.size - len(self.running_tasks)

    @property
    def is_full(self) -> bool:
        """窗口是否已满"""
        return len(self.running_tasks) >= self.size

    @property
    def is_empty(self) -> bool:
        """窗口是否为空"""
        return len(self.running_tasks) == 0

    async def acquire(self, task_id: str) -> bool:
        """尝试获取窗口槽位

        Args:
            task_id: 任务 ID

        Returns:
            是否成功获取槽位

        Raises:
            TaskWindowFullError: 窗口已满且任务不在等待队列中
        """
        async with self._lock:
            # 如果任务已经在运行中，直接返回成功
            if task_id in self.running_tasks:
                return True

            # 如果窗口有空闲槽位，直接获取
            if not self.is_full:
                self.running_tasks.add(task_id)
                return True

            # 窗口已满，将任务加入等待队列
            if task_id not in self.waiting_queue:
                self.waiting_queue.append(task_id)
            raise TaskWindowFullError(
                f"任务窗口已满（size={self.size}），任务 {task_id} 已加入等待队列"
            )

    async def release(self, task_id: str) -> None:
        """释放窗口槽位

        Args:
            task_id: 任务 ID
        """
        async with self._lock:
            # 从运行集合中移除
            if task_id in self.running_tasks:
                self.running_tasks.remove(task_id)

            # 从等待队列中移除（如果存在）
            if task_id in self.waiting_queue:
                self.waiting_queue.remove(task_id)

            # 如果有等待任务且窗口有空闲槽位，自动触发下一个任务获取
            # 注意：实际调用者需要处理这个逻辑

    async def promote_from_queue(self) -> Optional[str]:
        """从等待队列中提升一个任务到运行窗口

        Returns:
            被提升的任务 ID，如果没有等待任务则返回 None
        """
        async with self._lock:
            if self.waiting_queue and not self.is_full:
                task_id = self.waiting_queue.popleft()
                self.running_tasks.add(task_id)
                return task_id
            return None

    def get_status(self) -> dict:
        """获取窗口状态"""
        return {
            "size": self.size,
            "running_count": len(self.running_tasks),
            "waiting_count": len(self.waiting_queue),
            "available_slots": self.available_slots,
            "running_tasks": list(self.running_tasks),
            "waiting_queue": list(self.waiting_queue),
        }

    async def clear(self) -> None:
        """清空窗口和等待队列"""
        async with self._lock:
            self.running_tasks.clear()
            self.waiting_queue.clear()

    async def resize(self, new_size: int) -> None:
        """调整窗口大小

        Args:
            new_size: 新的窗口大小

        Raises:
            ValueError: 新大小小于当前运行任务数
        """
        async with self._lock:
            if new_size < len(self.running_tasks):
                raise ValueError(
                    f"新窗口大小 {new_size} 小于当前运行任务数 {len(self.running_tasks)}"
                )
            self.size = new_size
            # 尝试提升等待队列中的任务到新窗口
            while not self.is_full and self.waiting_queue:
                task_id = self.waiting_queue.popleft()
                self.running_tasks.add(task_id)