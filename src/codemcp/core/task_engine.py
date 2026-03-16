"""
任务执行引擎

集成 TaskWindow、FailureHandler 和状态机的核心执行引擎。
"""

import asyncio
import logging
from typing import Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ..database.session import get_db_session
from ..exceptions import TaskError, TaskWindowFullError
from ..models.test import TestModel, TestStatus
from .executor import TaskExecutor
from .failure_handler import FailureHandler
from .state_machine import test_state_machine
from .task_window import TaskWindow

logger = logging.getLogger(__name__)


class TaskEngine:
    """任务执行引擎"""

    def __init__(
        self,
        executor: TaskExecutor,
        window_size: int = 5,
        max_retries: int = 3,
    ) -> None:
        """初始化任务执行引擎

        Args:
            executor: 任务执行器
            window_size: 任务窗口大小
            max_retries: 最大重试次数
        """
        self.executor = executor
        self.task_window = TaskWindow(size=window_size)
        self.failure_handler = FailureHandler(max_retries=max_retries)
        self.running_tasks: Dict[str, asyncio.Task] = {}

    async def execute_task(self, test_id: str) -> None:
        """执行单个任务

        Args:
            test_id: 测试任务ID
        """
        # 获取数据库会话
        async for session in get_db_session():
            try:
                # 获取测试任务
                test = await session.get(TestModel, test_id)
                if not test:
                    logger.error(f"测试任务不存在: {test_id}")
                    return

                # 验证状态转移
                test_state_machine.validate_transition(
                    test.status.value,
                    TestStatus.RUNNING.value,
                )

                # 尝试获取窗口槽位
                try:
                    acquired = await self.task_window.acquire(test_id)
                    if not acquired:
                        logger.warning(f"任务 {test_id} 未能获取窗口槽位")
                        return
                except TaskWindowFullError as e:
                    logger.info(f"任务窗口已满，任务 {test_id} 加入等待队列: {e}")
                    # 更新状态为等待中
                    test.status = TestStatus.PENDING
                    await session.commit()
                    return

                # 更新状态为运行中
                test.status = TestStatus.RUNNING
                test.started_at = asyncio.get_event_loop().time()
                await session.commit()

                # 创建异步任务
                task = asyncio.create_task(
                    self._execute_with_retry(session, test)
                )
                self.running_tasks[test_id] = task

                # 等待任务完成
                await task

            except Exception as e:
                logger.error(f"执行任务 {test_id} 时发生错误: {e}")
                await self._handle_execution_error(session, test_id, str(e))

    async def _execute_with_retry(
        self,
        session: AsyncSession,
        test: TestModel,
    ) -> None:
        """带重试机制的执行逻辑

        Args:
            session: 数据库会话
            test: 测试任务
        """
        try:
            # 执行命令
            exit_code, stdout, stderr, duration = await self.executor.execute(test)

            # 更新测试结果
            test.exit_code = exit_code
            test.stdout = stdout
            test.stderr = stderr
            test.duration = duration
            test.finished_at = asyncio.get_event_loop().time()

            # 根据退出码判断状态
            if exit_code == 0:
                test_state_machine.validate_transition(
                    test.status.value,
                    TestStatus.PASSED.value,
                )
                test.status = TestStatus.PASSED
                logger.info(f"任务 {test.id} 执行成功")
            else:
                # 处理失败
                await self.failure_handler.handle_test_failure(
                    session,
                    test,
                    f"命令执行失败，退出码: {exit_code}\nstderr: {stderr[:500]}",
                )

            await session.commit()

        except TaskError as e:
            # 处理任务执行错误
            await self.failure_handler.handle_test_failure(
                session,
                test,
                str(e),
            )
        except Exception as e:
            # 处理其他错误
            logger.error(f"任务 {test.id} 执行过程中发生未预期错误: {e}")
            await self._handle_unexpected_error(session, test, str(e))
        finally:
            # 释放窗口槽位
            await self.task_window.release(test.id)
            # 从运行任务中移除
            self.running_tasks.pop(test.id, None)

            # 尝试从等待队列中提升下一个任务
            next_task_id = await self.task_window.promote_from_queue()
            if next_task_id:
                logger.info(f"从等待队列中提升任务: {next_task_id}")
                asyncio.create_task(self.execute_task(next_task_id))

    async def _handle_execution_error(
        self,
        session: AsyncSession,
        test_id: str,
        error_message: str,
    ) -> None:
        """处理执行错误

        Args:
            session: 数据库会话
            test_id: 测试任务ID
            error_message: 错误信息
        """
        try:
            test = await session.get(TestModel, test_id)
            if test:
                test_state_machine.validate_transition(
                    test.status.value,
                    TestStatus.FAILED.value,
                )
                test.status = TestStatus.FAILED
                test.error_message = error_message
                await session.commit()
        except Exception as e:
            logger.error(f"处理执行错误时发生异常: {e}")

    async def _handle_unexpected_error(
        self,
        session: AsyncSession,
        test: TestModel,
        error_message: str,
    ) -> None:
        """处理未预期错误

        Args:
            session: 数据库会话
            test: 测试任务
            error_message: 错误信息
        """
        try:
            test_state_machine.validate_transition(
                test.status.value,
                TestStatus.FAILED.value,
            )
            test.status = TestStatus.FAILED
            test.error_message = f"未预期错误: {error_message}"
            await session.commit()
        except Exception as e:
            logger.error(f"处理未预期错误时发生异常: {e}")

    async def cancel_task(self, test_id: str) -> bool:
        """取消正在执行的任务

        Args:
            test_id: 测试任务ID

        Returns:
            是否成功取消
        """
        task = self.running_tasks.get(test_id)
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logger.info(f"任务 {test_id} 已取消")
            return True
        return False

    async def get_task_status(self, test_id: str) -> Optional[Dict]:
        """获取任务状态

        Args:
            test_id: 测试任务ID

        Returns:
            任务状态信息
        """
        async for session in get_db_session():
            test = await session.get(TestModel, test_id)
            if not test:
                return None

            return {
                "id": test.id,
                "status": test.status.value,
                "is_running": test_id in self.running_tasks,
                "is_in_window": test_id in self.task_window.running_tasks,
                "is_in_queue": test_id in self.task_window.waiting_queue,
                "retry_count": test.retry_count,
                "max_retries": test.max_retries,
                "error_message": test.error_message,
            }

    async def shutdown(self) -> None:
        """关闭任务引擎"""
        # 取消所有运行中的任务
        for task_id, task in list(self.running_tasks.items()):
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logger.info(f"任务 {task_id} 已取消")

        # 清空运行任务字典
        self.running_tasks.clear()

        # 清空任务窗口
        self.task_window.running_tasks.clear()
        self.task_window.waiting_queue.clear()