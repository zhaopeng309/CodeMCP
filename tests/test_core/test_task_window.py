"""
TaskWindow 单元测试
"""

import pytest
import asyncio
from src.codemcp.core.task_window import TaskWindow


class TestTaskWindow:
    """TaskWindow 单元测试类"""

    @pytest.fixture
    def task_window(self):
        """创建 TaskWindow 实例"""
        return TaskWindow(size=3)

    @pytest.mark.asyncio
    async def test_task_window_creation(self, task_window):
        """测试 TaskWindow 创建"""
        assert task_window.size == 3
        assert task_window.running_count == 0
        assert task_window.waiting_count == 0
        assert task_window.available_slots == 3

    @pytest.mark.asyncio
    async def test_acquire_success(self, task_window):
        """测试成功获取窗口槽位"""
        # 第一次获取应该成功
        result = await task_window.acquire("task-1")
        assert result is True
        assert task_window.running_count == 1
        assert task_window.available_slots == 2
        assert task_window.waiting_count == 0

        # 第二次获取应该成功
        result = await task_window.acquire("task-2")
        assert result is True
        assert task_window.running_count == 2
        assert task_window.available_slots == 1

    @pytest.mark.asyncio
    async def test_acquire_full_window(self, task_window):
        """测试窗口满时获取"""
        # 填满窗口
        await task_window.acquire("task-1")
        await task_window.acquire("task-2")
        await task_window.acquire("task-3")
        
        assert task_window.running_count == 3
        assert task_window.available_slots == 0
        
        # 尝试获取第四个任务应该失败
        result = await task_window.acquire("task-4")
        assert result is False
        assert task_window.running_count == 3
        assert task_window.waiting_count == 1  # 任务进入等待队列

    @pytest.mark.asyncio
    async def test_release_slot(self, task_window):
        """测试释放窗口槽位"""
        # 获取并释放
        await task_window.acquire("task-1")
        assert task_window.running_count == 1
        
        await task_window.release("task-1")
        assert task_window.running_count == 0
        assert task_window.available_slots == 3

    @pytest.mark.asyncio
    async def test_release_unknown_task(self, task_window):
        """测试释放未知任务"""
        # 释放未获取的任务应该不报错
        await task_window.release("unknown-task")
        assert task_window.running_count == 0

    @pytest.mark.asyncio
    async def test_promote_from_queue(self, task_window):
        """测试从等待队列提升任务"""
        # 填满窗口
        await task_window.acquire("task-1")
        await task_window.acquire("task-2")
        await task_window.acquire("task-3")
        
        # 尝试获取第四个任务（进入等待队列）
        result = await task_window.acquire("task-4")
        assert result is False
        assert task_window.waiting_count == 1
        
        # 释放一个槽位
        await task_window.release("task-1")
        assert task_window.running_count == 2
        assert task_window.available_slots == 1
        
        # 应该自动从等待队列提升任务
        # promote_from_queue 应该在 release 中调用
        # 检查等待队列是否为空
        assert task_window.waiting_count == 0
        assert task_window.running_count == 3  # 包括提升的任务

    @pytest.mark.asyncio
    async def test_get_status(self, task_window):
        """测试获取状态"""
        status = task_window.get_status()
        
        assert "size" in status
        assert "running_count" in status
        assert "waiting_count" in status
        assert "available_slots" in status
        assert "running_tasks" in status
        assert "waiting_tasks" in status
        
        assert status["size"] == 3
        assert status["running_count"] == 0
        assert status["waiting_count"] == 0
        assert status["available_slots"] == 3

    @pytest.mark.asyncio
    async def test_clear(self, task_window):
        """测试清空窗口"""
        # 获取一些任务
        await task_window.acquire("task-1")
        await task_window.acquire("task-2")
        
        # 填满窗口并添加等待任务
        await task_window.acquire("task-3")
        await task_window.acquire("task-4")  # 进入等待队列
        
        assert task_window.running_count == 3
        assert task_window.waiting_count == 1
        
        # 清空窗口
        await task_window.clear()
        
        assert task_window.running_count == 0
        assert task_window.waiting_count == 0
        assert task_window.available_slots == 3

    @pytest.mark.asyncio
    async def test_resize_increase(self, task_window):
        """测试增大窗口大小"""
        # 获取一些任务
        await task_window.acquire("task-1")
        await task_window.acquire("task-2")
        await task_window.acquire("task-3")
        
        # 添加等待任务
        await task_window.acquire("task-4")
        
        assert task_window.running_count == 3
        assert task_window.waiting_count == 1
        assert task_window.size == 3
        
        # 增大窗口到5
        await task_window.resize(5)
        
        assert task_window.size == 5
        assert task_window.running_count == 4  # 等待任务被提升
        assert task_window.waiting_count == 0
        assert task_window.available_slots == 1

    @pytest.mark.asyncio
    async def test_resize_decrease(self, task_window):
        """测试减小窗口大小"""
        # 先增大窗口并获取任务
        await task_window.resize(5)
        await task_window.acquire("task-1")
        await task_window.acquire("task-2")
        await task_window.acquire("task-3")
        await task_window.acquire("task-4")
        await task_window.acquire("task-5")
        
        assert task_window.running_count == 5
        assert task_window.size == 5
        
        # 减小窗口到2
        await task_window.resize(2)
        
        assert task_window.size == 2
        assert task_window.running_count == 2  # 只保留前2个任务
        assert task_window.waiting_count == 3  # 其他任务进入等待队列
        assert task_window.available_slots == 0

    @pytest.mark.asyncio
    async def test_resize_same_size(self, task_window):
        """测试窗口大小不变"""
        await task_window.acquire("task-1")
        
        original_size = task_window.size
        original_running = task_window.running_count
        
        await task_window.resize(original_size)
        
        assert task_window.size == original_size
        assert task_window.running_count == original_running

    @pytest.mark.asyncio
    async def test_resize_invalid_size(self, task_window):
        """测试无效窗口大小"""
        with pytest.raises(ValueError, match="Window size must be positive"):
            await task_window.resize(0)
        
        with pytest.raises(ValueError, match="Window size must be positive"):
            await task_window.resize(-1)

    @pytest.mark.asyncio
    async def test_concurrent_access(self, task_window):
        """测试并发访问"""
        # 创建多个并发任务
        tasks = []
        for i in range(10):
            task_id = f"task-{i}"
            tasks.append(task_window.acquire(task_id))
        
        # 并发执行
        results = await asyncio.gather(*tasks)
        
        # 只有前3个应该成功
        assert sum(results) == 3
        assert task_window.running_count == 3
        assert task_window.waiting_count == 7

    @pytest.mark.asyncio
    async def test_task_priority_in_waiting_queue(self, task_window):
        """测试等待队列中的任务优先级"""
        # 填满窗口
        await task_window.acquire("task-1")
        await task_window.acquire("task-2")
        await task_window.acquire("task-3")
        
        # 添加多个等待任务
        await task_window.acquire("task-4")
        await task_window.acquire("task-5")
        await task_window.acquire("task-6")
        
        assert task_window.waiting_count == 3
        
        # 释放一个槽位，应该提升第一个等待任务
        await task_window.release("task-1")
        
        # 检查状态
        status = task_window.get_status()
        assert "task-4" in status["running_tasks"]  # 第一个等待任务被提升
        assert task_window.waiting_count == 2

    @pytest.mark.asyncio
    async def test_acquire_same_task_twice(self, task_window):
        """测试重复获取同一任务"""
        # 第一次获取成功
        result1 = await task_window.acquire("task-1")
        assert result1 is True
        
        # 第二次获取同一任务应该失败（任务已在运行）
        result2 = await task_window.acquire("task-1")
        assert result2 is False
        
        assert task_window.running_count == 1
        assert task_window.waiting_count == 0