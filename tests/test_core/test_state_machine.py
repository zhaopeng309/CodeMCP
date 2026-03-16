"""
StateMachine 单元测试
"""

import pytest
from src.codemcp.core.state_machine import (
    StateMachine,
    SystemStateMachine,
    BlockStateMachine,
    FeatureStateMachine,
    TestStateMachine as CoreTestStateMachine,
    get_state_machine,
)


class TestStateMachine:
    """StateMachine 单元测试类"""

    def test_state_machine_creation(self):
        """测试 StateMachine 创建"""
        valid_transitions = {
            "pending": {"in_progress", "cancelled"},
            "in_progress": {"completed", "failed", "cancelled"},
            "completed": set(),
            "failed": set(),
            "cancelled": set(),
        }
        
        state_machine = StateMachine(valid_transitions)
        
        assert state_machine.valid_transitions == valid_transitions

    def test_can_transition_valid(self):
        """测试有效状态转换"""
        valid_transitions = {
            "pending": {"in_progress", "cancelled"},
            "in_progress": {"completed", "failed", "cancelled"},
        }
        
        state_machine = StateMachine(valid_transitions)
        
        assert state_machine.can_transition("pending", "in_progress") is True
        assert state_machine.can_transition("pending", "cancelled") is True
        assert state_machine.can_transition("in_progress", "completed") is True
        assert state_machine.can_transition("in_progress", "failed") is True

    def test_can_transition_invalid(self):
        """测试无效状态转换"""
        valid_transitions = {
            "pending": {"in_progress", "cancelled"},
            "in_progress": {"completed", "failed", "cancelled"},
        }
        
        state_machine = StateMachine(valid_transitions)
        
        assert state_machine.can_transition("pending", "completed") is False
        assert state_machine.can_transition("in_progress", "pending") is False
        assert state_machine.can_transition("completed", "in_progress") is False

    def test_can_transition_unknown_state(self):
        """测试未知状态转换"""
        valid_transitions = {
            "pending": {"in_progress"},
        }
        
        state_machine = StateMachine(valid_transitions)
        
        # 从未知状态转换应该返回 False
        assert state_machine.can_transition("unknown", "pending") is False
        # 转换到未知状态应该返回 False
        assert state_machine.can_transition("pending", "unknown") is False

    def test_validate_transition_valid(self):
        """测试验证有效状态转换"""
        valid_transitions = {
            "pending": {"in_progress", "cancelled"},
        }
        
        state_machine = StateMachine(valid_transitions)
        
        # 应该不抛出异常
        state_machine.validate_transition("pending", "in_progress")
        state_machine.validate_transition("pending", "cancelled")

    def test_validate_transition_invalid(self):
        """测试验证无效状态转换"""
        valid_transitions = {
            "pending": {"in_progress"},
        }
        
        state_machine = StateMachine(valid_transitions)
        
        # 应该抛出 ValueError
        with pytest.raises(ValueError, match="Invalid transition"):
            state_machine.validate_transition("pending", "completed")

    def test_system_state_machine(self):
        """测试 SystemStateMachine"""
        state_machine = SystemStateMachine()
        
        # 测试有效转换
        assert state_machine.can_transition("active", "archived") is True
        
        # 测试无效转换
        assert state_machine.can_transition("archived", "active") is False
        
        # 测试验证
        state_machine.validate_transition("active", "archived")
        
        with pytest.raises(ValueError):
            state_machine.validate_transition("archived", "active")

    def test_block_state_machine(self):
        """测试 BlockStateMachine"""
        state_machine = BlockStateMachine()
        
        # 测试有效转换
        assert state_machine.can_transition("pending", "in_progress") is True
        assert state_machine.can_transition("pending", "cancelled") is True
        assert state_machine.can_transition("in_progress", "completed") is True
        assert state_machine.can_transition("in_progress", "aborted") is True
        assert state_machine.can_transition("in_progress", "cancelled") is True
        
        # 测试无效转换
        assert state_machine.can_transition("completed", "in_progress") is False
        assert state_machine.can_transition("aborted", "pending") is False
        
        # 测试验证
        state_machine.validate_transition("pending", "in_progress")
        
        with pytest.raises(ValueError):
            state_machine.validate_transition("completed", "in_progress")

    def test_feature_state_machine(self):
        """测试 FeatureStateMachine"""
        state_machine = FeatureStateMachine()
        
        # 测试有效转换
        assert state_machine.can_transition("pending", "running") is True
        assert state_machine.can_transition("pending", "cancelled") is True
        assert state_machine.can_transition("running", "passed") is True
        assert state_machine.can_transition("running", "failed") is True
        assert state_machine.can_transition("running", "aborted") is True
        assert state_machine.can_transition("running", "cancelled") is True
        
        # 测试无效转换
        assert state_machine.can_transition("passed", "running") is False
        assert state_machine.can_transition("failed", "pending") is False
        
        # 测试验证
        state_machine.validate_transition("pending", "running")
        
        with pytest.raises(ValueError):
            state_machine.validate_transition("passed", "running")

    def test_test_state_machine(self):
        """测试 TestStateMachine"""
        state_machine = CoreTestStateMachine()
        
        # 测试有效转换
        assert state_machine.can_transition("pending", "running") is True
        assert state_machine.can_transition("pending", "cancelled") is True
        assert state_machine.can_transition("running", "passed") is True
        assert state_machine.can_transition("running", "failed") is True
        assert state_machine.can_transition("running", "cancelled") is True
        
        # 测试无效转换
        assert state_machine.can_transition("passed", "running") is False
        assert state_machine.can_transition("failed", "pending") is False
        
        # 测试验证
        state_machine.validate_transition("pending", "running")
        
        with pytest.raises(ValueError):
            state_machine.validate_transition("passed", "running")

    def test_get_state_machine(self):
        """测试 get_state_machine 函数"""
        # 测试获取系统状态机
        system_sm = get_state_machine("system")
        assert isinstance(system_sm, SystemStateMachine)
        
        # 测试获取模块状态机
        block_sm = get_state_machine("block")
        assert isinstance(block_sm, BlockStateMachine)
        
        # 测试获取功能点状态机
        feature_sm = get_state_machine("feature")
        assert isinstance(feature_sm, FeatureStateMachine)
        
        # 测试获取测试状态机
        test_sm = get_state_machine("test")
        assert isinstance(test_sm, CoreTestStateMachine)
        
        # 测试未知类型
        with pytest.raises(ValueError, match="不支持的模型类型"):
            get_state_machine("unknown")

    def test_state_machine_immutable_transitions(self):
        """测试状态机转换表不可变"""
        valid_transitions = {
            "pending": {"in_progress"},
        }
        
        state_machine = StateMachine(valid_transitions)
        
        # 尝试修改原始字典不应该影响状态机
        valid_transitions["pending"].add("completed")
        
        # 状态机内部的转换表应该保持不变
        assert "completed" not in state_machine.valid_transitions["pending"]

    def test_state_machine_empty_transitions(self):
        """测试空转换表"""
        state_machine = StateMachine({})
        
        # 任何转换都应该返回 False
        assert state_machine.can_transition("any", "other") is False
        
        # 验证应该抛出异常
        with pytest.raises(ValueError):
            state_machine.validate_transition("any", "other")

    def test_state_machine_self_transition(self):
        """测试自我转换"""
        valid_transitions = {
            "state": {"state"},  # 允许自我转换
        }
        
        state_machine = StateMachine(valid_transitions)
        
        assert state_machine.can_transition("state", "state") is True
        state_machine.validate_transition("state", "state")  # 应该不抛出异常