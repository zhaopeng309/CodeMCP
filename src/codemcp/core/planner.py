"""
规划器接口

任务规划和调度的抽象定义。
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..models.block import BlockModel
from ..models.feature import FeatureModel
from ..models.system import SystemModel
from ..models.test import TestModel


class TaskPlanner(ABC):
    """任务规划器抽象基类"""

    @abstractmethod
    async def create_plan(
        self,
        system: SystemModel,
        description: str,
    ) -> List[BlockModel]:
        """创建执行计划

        Args:
            system: 系统实例
            description: 计划描述

        Returns:
            创建的模块列表
        """
        pass

    @abstractmethod
    async def breakdown_block(
        self,
        block: BlockModel,
    ) -> List[FeatureModel]:
        """拆解模块为功能点

        Args:
            block: 模块实例

        Returns:
            创建的功能点列表
        """
        pass

    @abstractmethod
    async def breakdown_feature(
        self,
        feature: FeatureModel,
    ) -> List[TestModel]:
        """拆解功能点为测试

        Args:
            feature: 功能点实例

        Returns:
            创建的测试列表
        """
        pass

    @abstractmethod
    async def reprioritize_tasks(
        self,
        system_id: str,
    ) -> None:
        """重新优先级排序任务

        Args:
            system_id: 系统 ID
        """
        pass

    @abstractmethod
    async def estimate_duration(
        self,
        test: TestModel,
    ) -> float:
        """估算测试执行时长

        Args:
            test: 测试实例

        Returns:
            估算的时长（秒）
        """
        pass


class SimplePlanner(TaskPlanner):
    """简单规划器（基础实现）"""

    async def create_plan(
        self,
        system: SystemModel,
        description: str,
    ) -> List[BlockModel]:
        """创建简单的执行计划"""
        # 这是一个基础实现，实际项目需要更复杂的逻辑
        # 这里返回空列表，实际实现应该创建模块
        return []

    async def breakdown_block(
        self,
        block: BlockModel,
    ) -> List[FeatureModel]:
        """拆解模块为功能点"""
        # 基础实现
        return []

    async def breakdown_feature(
        self,
        feature: FeatureModel,
    ) -> List[TestModel]:
        """拆解功能点为测试"""
        # 基础实现
        return []

    async def reprioritize_tasks(
        self,
        system_id: str,
    ) -> None:
        """重新优先级排序任务"""
        # 基础实现
        pass

    async def estimate_duration(
        self,
        test: TestModel,
    ) -> float:
        """估算测试执行时长"""
        # 基础估算：根据命令长度简单估算
        return len(test.command) * 0.01  # 每字符 0.01 秒


# 全局规划器实例
_planner_instance: Optional[TaskPlanner] = None


def get_planner() -> TaskPlanner:
    """获取规划器实例

    Returns:
        规划器实例
    """
    global _planner_instance
    if _planner_instance is None:
        _planner_instance = SimplePlanner()
    return _planner_instance


def set_planner(planner: TaskPlanner) -> None:
    """设置规划器实例

    Args:
        planner: 规划器实例
    """
    global _planner_instance
    _planner_instance = planner