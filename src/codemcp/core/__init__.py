"""
核心业务逻辑层

状态机实现，任务窗口化执行，失败处理和重试逻辑，执行器接口。
"""

from .state_machine import (
    StateMachine,
    SystemStateMachine,
    BlockStateMachine,
    FeatureStateMachine,
    TestStateMachine,
    system_state_machine,
    block_state_machine,
    feature_state_machine,
    test_state_machine,
    get_state_machine,
)
from .task_window import TaskWindow
from .executor import TaskExecutor, LocalCommandExecutor, MockExecutor, get_executor, set_executor
from .planner import TaskPlanner, SimplePlanner, get_planner, set_planner
from .failure_handler import FailureHandler, get_failure_handler, set_failure_handler
from .task_engine import TaskEngine

__all__ = [
    # 状态机
    "StateMachine",
    "SystemStateMachine",
    "BlockStateMachine",
    "FeatureStateMachine",
    "TestStateMachine",
    "system_state_machine",
    "block_state_machine",
    "feature_state_machine",
    "test_state_machine",
    "get_state_machine",
    # 任务窗口
    "TaskWindow",
    # 执行器
    "TaskExecutor",
    "LocalCommandExecutor",
    "MockExecutor",
    "get_executor",
    "set_executor",
    # 规划器
    "TaskPlanner",
    "SimplePlanner",
    "get_planner",
    "set_planner",
    # 失败处理器
    "FailureHandler",
    "get_failure_handler",
    "set_failure_handler",
    # 任务引擎
    "TaskEngine",
]