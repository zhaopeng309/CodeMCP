"""
执行器接口

任务执行器的抽象定义和基础实现。
"""

import asyncio
import shlex
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Tuple

from ..exceptions import TaskError
from ..models.test import TestModel, TestStatus


class TaskExecutor(ABC):
    """任务执行器抽象基类"""

    @abstractmethod
    async def execute(self, test: TestModel) -> Tuple[int, str, str, float]:
        """执行测试命令

        Args:
            test: 测试模型实例

        Returns:
            元组 (exit_code, stdout, stderr, duration)

        Raises:
            TaskError: 任务执行失败
        """
        pass

    @abstractmethod
    async def validate_command(self, command: str) -> bool:
        """验证命令是否合法

        Args:
            command: 待验证的命令

        Returns:
            命令是否合法
        """
        pass


class LocalCommandExecutor(TaskExecutor):
    """本地命令执行器"""

    def __init__(self, timeout: int = 3600) -> None:
        """初始化本地命令执行器

        Args:
            timeout: 命令执行超时时间（秒）
        """
        self.timeout = timeout

    async def validate_command(self, command: str) -> bool:
        """验证命令是否合法

        当前实现仅进行基本的安全性检查
        """
        # 简单检查：命令不能为空
        if not command or not command.strip():
            return False

        # 可以添加更多安全检查，如禁止某些危险命令
        dangerous_prefixes = ["rm -rf", "dd if=", "mkfs", ":(){ :|:& };:"]
        for prefix in dangerous_prefixes:
            if command.strip().startswith(prefix):
                return False

        return True

    async def execute(self, test: TestModel) -> Tuple[int, str, str, float]:
        """执行测试命令

        Args:
            test: 测试模型实例

        Returns:
            元组 (exit_code, stdout, stderr, duration)

        Raises:
            TaskError: 任务执行失败
        """
        command = test.command.strip()
        if not await self.validate_command(command):
            raise TaskError(f"命令验证失败: {command}")

        start_time = datetime.now()

        try:
            # 使用 asyncio 创建子进程执行命令
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                shell=True,
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout,
                )
            except asyncio.TimeoutError:
                # 超时，终止进程
                process.terminate()
                await process.wait()
                raise TaskError(f"命令执行超时: {command}")

            exit_code = process.returncode
            stdout = stdout_bytes.decode("utf-8", errors="replace")
            stderr = stderr_bytes.decode("utf-8", errors="replace")

        except (OSError, ValueError, asyncio.CancelledError) as e:
            raise TaskError(f"命令执行失败: {command}, 错误: {e}")

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        return exit_code, stdout, stderr, duration


class MockExecutor(TaskExecutor):
    """模拟执行器（用于测试）"""

    def __init__(self, success: bool = True, exit_code: int = 0) -> None:
        """初始化模拟执行器

        Args:
            success: 是否模拟成功
            exit_code: 模拟的退出码
        """
        self.success = success
        self.exit_code = exit_code if success else 1

    async def validate_command(self, command: str) -> bool:
        """验证命令（总是返回 True）"""
        return True

    async def execute(self, test: TestModel) -> Tuple[int, str, str, float]:
        """模拟执行命令"""
        await asyncio.sleep(0.1)  # 模拟执行时间

        if self.success:
            return (
                self.exit_code,
                f"Mock stdout for command: {test.command}",
                "",
                0.1,
            )
        else:
            return (
                self.exit_code,
                "",
                f"Mock stderr for command: {test.command}",
                0.1,
            )


# 全局执行器实例（可根据配置选择）
_executor_instance: Optional[TaskExecutor] = None


def get_executor() -> TaskExecutor:
    """获取执行器实例

    Returns:
        执行器实例
    """
    global _executor_instance
    if _executor_instance is None:
        _executor_instance = LocalCommandExecutor()
    return _executor_instance


def set_executor(executor: TaskExecutor) -> None:
    """设置执行器实例

    Args:
        executor: 执行器实例
    """
    global _executor_instance
    _executor_instance = executor