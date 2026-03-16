"""
失败处理机制

处理任务失败、重试和级联中止逻辑。
"""

import asyncio
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ..exceptions import RetryExhaustedError, TaskError
from ..models.block import BlockModel, BlockStatus
from ..models.feature import FeatureModel, FeatureStatus
from ..models.test import TestModel, TestStatus
from .state_machine import block_state_machine, feature_state_machine, test_state_machine


class FailureHandler:
    """失败处理器"""

    def __init__(self, max_retries: int = 3) -> None:
        """初始化失败处理器

        Args:
            max_retries: 最大重试次数
        """
        self.max_retries = max_retries

    async def handle_test_failure(
        self,
        session: AsyncSession,
        test: TestModel,
        error_message: Optional[str] = None,
    ) -> None:
        """处理测试失败

        Args:
            session: 数据库会话
            test: 失败的测试实例
            error_message: 错误信息

        Raises:
            RetryExhaustedError: 重试次数用尽
        """
        # 更新测试状态和错误信息
        test.status = TestStatus.FAILED
        test.error_message = error_message
        test.retry_count += 1

        # 检查是否还可以重试
        if test.retry_count >= test.max_retries:
            # 重试次数用尽，标记为重试耗尽
            test.error_message = f"重试次数用尽（{test.retry_count}/{test.max_retries}）"
            if error_message:
                test.error_message += f": {error_message}"

            # 级联中止所属功能点
            await self._cascade_abort_feature(session, test.feature)
            raise RetryExhaustedError(test.error_message)

        # 还可以重试，将测试状态重置为 PENDING
        test_state_machine.validate_transition(
            TestStatus.FAILED.value,
            TestStatus.PENDING.value,
        )
        test.status = TestStatus.PENDING

        await session.commit()

    async def handle_feature_failure(
        self,
        session: AsyncSession,
        feature: FeatureModel,
        error_message: Optional[str] = None,
    ) -> None:
        """处理功能点失败

        Args:
            session: 数据库会话
            feature: 失败的功能点实例
            error_message: 错误信息
        """
        # 更新功能点状态
        feature_state_machine.validate_transition(
            feature.status.value,
            FeatureStatus.FAILED.value,
        )
        feature.status = FeatureStatus.FAILED

        # 级联中止所属模块
        await self._cascade_abort_block(session, feature.block)

        await session.commit()

    async def _cascade_abort_feature(
        self,
        session: AsyncSession,
        feature: FeatureModel,
    ) -> None:
        """级联中止功能点"""
        # 验证状态转移
        feature_state_machine.validate_transition(
            feature.status.value,
            FeatureStatus.ABORTED.value,
        )
        feature.status = FeatureStatus.ABORTED

        # 中止所有关联的测试
        for test in feature.tests:
            if test.status in [TestStatus.PENDING, TestStatus.RUNNING]:
                test_state_machine.validate_transition(
                    test.status.value,
                    TestStatus.FAILED.value,
                )
                test.status = TestStatus.FAILED
                test.error_message = "由于功能点中止而失败"

        await session.commit()

    async def _cascade_abort_block(
        self,
        session: AsyncSession,
        block: BlockModel,
    ) -> None:
        """级联中止模块"""
        # 验证状态转移
        block_state_machine.validate_transition(
            block.status.value,
            BlockStatus.ABORTED.value,
        )
        block.status = BlockStatus.ABORTED

        # 中止所有关联的功能点
        for feature in block.features:
            if feature.status in [FeatureStatus.PENDING, FeatureStatus.RUNNING]:
                feature_state_machine.validate_transition(
                    feature.status.value,
                    FeatureStatus.ABORTED.value,
                )
                feature.status = FeatureStatus.ABORTED

        await session.commit()

    async def retry_test(
        self,
        session: AsyncSession,
        test: TestModel,
    ) -> TestModel:
        """重试测试

        Args:
            session: 数据库会话
            test: 要重试的测试实例

        Returns:
            更新后的测试实例
        """
        # 检查是否可以重试
        if test.retry_count >= test.max_retries:
            raise RetryExhaustedError(
                f"重试次数已用尽: {test.retry_count}/{test.max_retries}"
            )

        # 验证状态转移
        test_state_machine.validate_transition(
            test.status.value,
            TestStatus.PENDING.value,
        )

        # 重置测试状态
        test.status = TestStatus.PENDING
        test.exit_code = None
        test.stdout = None
        test.stderr = None
        test.duration = None
        test.error_message = None

        await session.commit()
        return test

    async def retry_feature(
        self,
        session: AsyncSession,
        feature: FeatureModel,
    ) -> FeatureModel:
        """重试功能点及其所有测试

        Args:
            session: 数据库会话
            feature: 要重试的功能点实例

        Returns:
            更新后的功能点实例
        """
        # 验证状态转移
        feature_state_machine.validate_transition(
            feature.status.value,
            FeatureStatus.PENDING.value,
        )

        # 重置功能点状态
        feature.status = FeatureStatus.PENDING

        # 重置所有关联的测试
        for test in feature.tests:
            await self.retry_test(session, test)

        await session.commit()
        return feature

    async def retry_block(
        self,
        session: AsyncSession,
        block: BlockModel,
    ) -> BlockModel:
        """重试模块及其所有功能点

        Args:
            session: 数据库会话
            block: 要重试的模块实例

        Returns:
            更新后的模块实例
        """
        # 验证状态转移
        block_state_machine.validate_transition(
            block.status.value,
            BlockStatus.PENDING.value,
        )

        # 重置模块状态
        block.status = BlockStatus.PENDING

        # 重置所有关联的功能点
        for feature in block.features:
            await self.retry_feature(session, feature)

        await session.commit()
        return block


# 全局失败处理器实例
_failure_handler_instance: Optional[FailureHandler] = None


def get_failure_handler(max_retries: Optional[int] = None) -> FailureHandler:
    """获取失败处理器实例

    Args:
        max_retries: 最大重试次数，如果为 None 则使用默认值

    Returns:
        失败处理器实例
    """
    global _failure_handler_instance
    if _failure_handler_instance is None:
        _failure_handler_instance = FailureHandler(
            max_retries=max_retries or 3
        )
    return _failure_handler_instance


def set_failure_handler(handler: FailureHandler) -> None:
    """设置失败处理器实例

    Args:
        handler: 失败处理器实例
    """
    global _failure_handler_instance
    _failure_handler_instance = handler