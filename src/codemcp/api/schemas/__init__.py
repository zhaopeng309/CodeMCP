"""
Pydantic 模型层

API 请求和响应的 Pydantic 模型定义。
"""

from .common import (
    PaginationParams,
    PaginatedResponse,
    ErrorResponse,
    SuccessResponse,
    TimestampMixin,
    IDMixin,
    StatusMixin,
    model_config,
)
from .system import (
    SystemCreate,
    SystemUpdate,
    SystemResponse,
    SystemDetailResponse,
    SystemListResponse,
)
from .block import (
    BlockCreate,
    BlockUpdate,
    BlockResponse,
    BlockDetailResponse,
    BlockListResponse,
)
from .feature import (
    FeatureCreate,
    FeatureUpdate,
    FeatureResponse,
    FeatureDetailResponse,
    FeatureListResponse,
)
from .task import (
    TestCreate,
    TestUpdate,
    TestResponse,
    TestDetailResponse,
    TestListResponse,
    TestExecuteRequest,
    TestExecuteResponse,
    TaskQueueRequest,
    TaskQueueResponse,
)
from .auth import (
    Token,
    TokenPayload,
    UserLogin,
    UserRegister,
    UserResponse,
    UserUpdate,
    PasswordResetRequest,
    PasswordResetConfirm,
    LogoutRequest,
)

__all__ = [
    # 通用模型
    "PaginationParams",
    "PaginatedResponse",
    "ErrorResponse",
    "SuccessResponse",
    "TimestampMixin",
    "IDMixin",
    "StatusMixin",
    "model_config",
    # 系统模型
    "SystemCreate",
    "SystemUpdate",
    "SystemResponse",
    "SystemDetailResponse",
    "SystemListResponse",
    # 模块模型
    "BlockCreate",
    "BlockUpdate",
    "BlockResponse",
    "BlockDetailResponse",
    "BlockListResponse",
    # 功能点模型
    "FeatureCreate",
    "FeatureUpdate",
    "FeatureResponse",
    "FeatureDetailResponse",
    "FeatureListResponse",
    # 任务和测试模型
    "TestCreate",
    "TestUpdate",
    "TestResponse",
    "TestDetailResponse",
    "TestListResponse",
    "TestExecuteRequest",
    "TestExecuteResponse",
    "TaskQueueRequest",
    "TaskQueueResponse",
    # 认证模型
    "Token",
    "TokenPayload",
    "UserLogin",
    "UserRegister",
    "UserResponse",
    "UserUpdate",
    "PasswordResetRequest",
    "PasswordResetConfirm",
    "LogoutRequest",
]