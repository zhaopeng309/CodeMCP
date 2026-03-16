"""
状态机系统

管理任务状态流转和状态验证。
"""

from typing import Any, Dict, Optional

from ..exceptions import StateTransitionError
from ..models.block import BlockStatus
from ..models.feature import FeatureStatus
from ..models.system import SystemStatus
from ..models.test import TestStatus


class StateMachine:
    """状态机基类"""

    def __init__(self, valid_transitions: Dict[str, set]) -> None:
        """初始化状态机

        Args:
            valid_transitions: 有效状态转移映射 {from_state: {to_state1, to_state2, ...}}
        """
        self.valid_transitions = valid_transitions

    def can_transition(self, from_state: str, to_state: str) -> bool:
        """检查状态转移是否有效

        Args:
            from_state: 当前状态
            to_state: 目标状态

        Returns:
            是否允许转移
        """
        return to_state in self.valid_transitions.get(from_state, set())

    def validate_transition(self, from_state: str, to_state: str) -> None:
        """验证状态转移，如果无效则抛出异常

        Args:
            from_state: 当前状态
            to_state: 目标状态

        Raises:
            StateTransitionError: 状态转移无效
        """
        if not self.can_transition(from_state, to_state):
            raise StateTransitionError(
                f"无效的状态转移: {from_state} -> {to_state}"
            )


class SystemStateMachine(StateMachine):
    """系统状态机"""

    def __init__(self) -> None:
        valid_transitions = {
            SystemStatus.ACTIVE.value: {SystemStatus.ARCHIVED.value},
            SystemStatus.ARCHIVED.value: {SystemStatus.ACTIVE.value},
        }
        super().__init__(valid_transitions)


class BlockStateMachine(StateMachine):
    """模块状态机"""

    def __init__(self) -> None:
        valid_transitions = {
            BlockStatus.PENDING.value: {
                BlockStatus.IN_PROGRESS.value,
                BlockStatus.ABORTED.value,
            },
            BlockStatus.IN_PROGRESS.value: {
                BlockStatus.COMPLETED.value,
                BlockStatus.ABORTED.value,
            },
            BlockStatus.COMPLETED.value: set(),
            BlockStatus.ABORTED.value: {BlockStatus.PENDING.value},
        }
        super().__init__(valid_transitions)


class FeatureStateMachine(StateMachine):
    """功能点状态机"""

    def __init__(self) -> None:
        valid_transitions = {
            FeatureStatus.PENDING.value: {
                FeatureStatus.RUNNING.value,
                FeatureStatus.ABORTED.value,
            },
            FeatureStatus.RUNNING.value: {
                FeatureStatus.PASSED.value,
                FeatureStatus.FAILED.value,
                FeatureStatus.ABORTED.value,
            },
            FeatureStatus.PASSED.value: set(),
            FeatureStatus.FAILED.value: {
                FeatureStatus.PENDING.value,  # 重试
                FeatureStatus.ABORTED.value,
            },
            FeatureStatus.ABORTED.value: {FeatureStatus.PENDING.value},
        }
        super().__init__(valid_transitions)


class TestStateMachine(StateMachine):
    """测试状态机"""

    def __init__(self) -> None:
        valid_transitions = {
            TestStatus.PENDING.value: {
                TestStatus.RUNNING.value,
            },
            TestStatus.RUNNING.value: {
                TestStatus.PASSED.value,
                TestStatus.FAILED.value,
            },
            TestStatus.PASSED.value: set(),
            TestStatus.FAILED.value: {
                TestStatus.PENDING.value,  # 重试
            },
        }
        super().__init__(valid_transitions)


# 全局状态机实例
system_state_machine = SystemStateMachine()
block_state_machine = BlockStateMachine()
feature_state_machine = FeatureStateMachine()
test_state_machine = TestStateMachine()


def get_state_machine(model_type: str) -> StateMachine:
    """根据模型类型获取对应的状态机

    Args:
        model_type: 模型类型 ('system', 'block', 'feature', 'test')

    Returns:
        对应的状态机实例

    Raises:
        ValueError: 模型类型不支持
    """
    state_machines = {
        "system": system_state_machine,
        "block": block_state_machine,
        "feature": feature_state_machine,
        "test": test_state_machine,
    }
    if model_type not in state_machines:
        raise ValueError(f"不支持的模型类型: {model_type}")
    return state_machines[model_type]