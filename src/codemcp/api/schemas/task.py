"""
Task Pydantic 模型

Task 和 Test 相关的请求/响应模型。
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from ...models.test import TestStatus
from .common import IDMixin, StatusMixin, TimestampMixin, model_config


class TaskBase(BaseModel):
    """Task 基础模型配置"""

    model_config = model_config


class TestCreate(TaskBase):
    """创建 Test 请求模型"""

    feature_id: str = Field(
        ...,
        description="所属功能点 ID",
        examples=["550e8400-e29b-41d4-a716-446655440002"],
    )
    command: str = Field(
        ...,
        description="执行的命令",
        examples=["python -m pytest tests/test_login.py::test_valid_login"],
    )
    description: Optional[str] = Field(
        default=None,
        description="任务描述",
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="最大重试次数",
    )
    timeout: int = Field(
        default=3600,
        ge=1,
        le=86400,
        description="执行超时时间（秒）",
    )
    status: TestStatus = Field(
        default=TestStatus.PENDING,
        description="测试状态",
    )


class TestUpdate(TaskBase):
    """更新 Test 请求模型"""

    command: Optional[str] = Field(
        default=None,
        description="执行的命令",
    )
    description: Optional[str] = Field(
        default=None,
        description="任务描述",
    )
    max_retries: Optional[int] = Field(
        default=None,
        ge=0,
        le=10,
        description="最大重试次数",
    )
    timeout: Optional[int] = Field(
        default=None,
        ge=1,
        le=86400,
        description="执行超时时间（秒）",
    )
    status: Optional[TestStatus] = Field(
        default=None,
        description="测试状态",
    )


class TestResponse(TaskBase, IDMixin, TimestampMixin, StatusMixin):
    """Test 响应模型"""

    feature_id: str = Field(description="所属功能点 ID")
    command: str = Field(description="执行的命令")
    exit_code: Optional[int] = Field(description="退出码")
    stdout: Optional[str] = Field(description="标准输出")
    stderr: Optional[str] = Field(description="标准错误")
    duration: Optional[float] = Field(description="执行时长（秒）")
    retry_count: int = Field(description="重试次数")
    max_retries: int = Field(description="最大重试次数")
    error_message: Optional[str] = Field(description="错误信息")
    feature_name: Optional[str] = Field(default=None, description="功能点名称")


class TestDetailResponse(TestResponse):
    """Test 详情响应模型"""

    pass  # 可以添加更多字段


class TestListResponse(TaskBase):
    """Test 列表响应模型"""

    tests: list[TestResponse] = Field(description="测试列表")
    total: int = Field(description="总数")


class TestExecuteRequest(TaskBase):
    """执行 Test 请求模型"""

    timeout: Optional[int] = Field(
        default=3600,
        ge=1,
        le=86400,
        description="执行超时时间（秒）",
    )


class TestExecuteResponse(TaskBase):
    """执行 Test 响应模型"""

    task_id: str = Field(description="任务 ID")
    status: str = Field(description="执行状态")
    message: str = Field(description="状态消息")


class TaskQueueRequest(TaskBase):
    """任务队列请求模型"""

    test_id: str = Field(description="测试 ID")
    priority: int = Field(default=0, ge=-100, le=100, description="优先级")
    scheduled_at: Optional[datetime] = Field(default=None, description="计划执行时间")


class TaskQueueResponse(TaskBase, IDMixin, TimestampMixin, StatusMixin):
    """任务队列响应模型"""

    test_id: str = Field(description="测试 ID")
    priority: int = Field(description="优先级")
    scheduled_at: Optional[datetime] = Field(description="计划执行时间")
    started_at: Optional[datetime] = Field(description="开始执行时间")
    completed_at: Optional[datetime] = Field(description="完成时间")
    attempts: int = Field(description="尝试次数")
    max_attempts: int = Field(description="最大尝试次数")
    error_message: Optional[str] = Field(description="错误信息")


# 导出模型
__all__ = [
    "TestCreate",
    "TestUpdate",
    "TestResponse",
    "TestDetailResponse",
    "TestExecuteRequest",
    "TestExecuteResponse",
    "TaskQueueRequest",
    "TaskQueueResponse",
]