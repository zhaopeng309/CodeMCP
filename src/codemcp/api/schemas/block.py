"""
Block Pydantic 模型

Block 相关的请求/响应模型。
"""

from typing import Optional

from pydantic import BaseModel, Field

from ...models.block import BlockStatus
from .common import IDMixin, StatusMixin, TimestampMixin, model_config


class BlockBase(BaseModel):
    """Block 基础模型配置"""

    model_config = model_config


class BlockCreate(BlockBase):
    """创建 Block 请求模型"""

    system_id: str = Field(
        ...,
        description="所属系统 ID",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="模块名称",
        examples=["用户认证模块"],
    )
    description: Optional[str] = Field(
        default=None,
        description="模块描述",
        examples=["处理用户登录、注册、权限验证等功能"],
    )
    priority: int = Field(
        default=0,
        ge=-100,
        le=100,
        description="优先级（数字越小优先级越高）",
        examples=[1],
    )
    status: BlockStatus = Field(
        default=BlockStatus.PENDING,
        description="模块状态",
    )


class BlockUpdate(BlockBase):
    """更新 Block 请求模型"""

    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="模块名称",
        examples=["用户认证模块 v2"],
    )
    description: Optional[str] = Field(
        default=None,
        description="模块描述",
    )
    priority: Optional[int] = Field(
        default=None,
        ge=-100,
        le=100,
        description="优先级",
    )
    status: Optional[BlockStatus] = Field(
        default=None,
        description="模块状态",
    )


class BlockResponse(BlockBase, IDMixin, TimestampMixin, StatusMixin):
    """Block 响应模型"""

    system_id: str = Field(description="所属系统 ID")
    name: str = Field(description="模块名称")
    description: Optional[str] = Field(description="模块描述")
    priority: int = Field(description="优先级")
    system_name: Optional[str] = Field(default=None, description="系统名称")
    feature_count: int = Field(default=0, description="功能点数量")


class BlockDetailResponse(BlockResponse):
    """Block 详情响应模型"""

    pass  # 可以添加更多字段，如关联的功能点列表


class BlockListResponse(BlockBase):
    """Block 列表响应模型"""

    blocks: list[BlockResponse] = Field(description="模块列表")
    total: int = Field(description="总数")


# 导出模型
__all__ = [
    "BlockCreate",
    "BlockUpdate",
    "BlockResponse",
    "BlockDetailResponse",
    "BlockListResponse",
]