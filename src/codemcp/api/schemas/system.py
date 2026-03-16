"""
System Pydantic 模型

System 相关的请求/响应模型。
"""

from typing import Optional

from pydantic import BaseModel, Field

from ...models.system import SystemStatus
from .common import IDMixin, StatusMixin, TimestampMixin, model_config


class SystemBase(BaseModel):
    """System 基础模型配置"""

    model_config = model_config


class SystemCreate(SystemBase):
    """创建 System 请求模型"""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="系统名称",
        examples=["用户管理系统"],
    )
    description: Optional[str] = Field(
        default=None,
        description="系统描述",
        examples=["管理用户信息和权限的系统"],
    )
    status: SystemStatus = Field(
        default=SystemStatus.ACTIVE,
        description="系统状态",
    )


class SystemUpdate(SystemBase):
    """更新 System 请求模型"""

    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="系统名称",
        examples=["用户管理系统 v2"],
    )
    description: Optional[str] = Field(
        default=None,
        description="系统描述",
        examples=["升级版的用户管理系统"],
    )
    status: Optional[SystemStatus] = Field(
        default=None,
        description="系统状态",
    )


class SystemResponse(SystemBase, IDMixin, TimestampMixin, StatusMixin):
    """System 响应模型"""

    name: str = Field(description="系统名称")
    description: Optional[str] = Field(description="系统描述")
    block_count: int = Field(default=0, description="模块数量")


class SystemDetailResponse(SystemResponse):
    """System 详情响应模型"""

    pass  # 可以添加更多字段，如关联的模块列表


class SystemListResponse(SystemBase):
    """System 列表响应模型"""

    systems: list[SystemResponse] = Field(description="系统列表")
    total: int = Field(description="总数")


# 导出模型
__all__ = [
    "SystemCreate",
    "SystemUpdate",
    "SystemResponse",
    "SystemDetailResponse",
    "SystemListResponse",
]