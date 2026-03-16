"""
Feature Pydantic 模型

Feature 相关的请求/响应模型。
"""

from typing import Optional

from pydantic import BaseModel, Field

from ...models.feature import FeatureStatus
from .common import IDMixin, StatusMixin, TimestampMixin, model_config


class FeatureBase(BaseModel):
    """Feature 基础模型配置"""

    model_config = model_config


class FeatureCreate(FeatureBase):
    """创建 Feature 请求模型"""

    block_id: str = Field(
        ...,
        description="所属模块 ID",
        examples=["550e8400-e29b-41d4-a716-446655440001"],
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="功能点名称",
        examples=["用户登录功能"],
    )
    description: Optional[str] = Field(
        default=None,
        description="功能点描述",
        examples=["实现用户通过用户名密码登录的功能"],
    )
    test_command: str = Field(
        ...,
        description="测试命令",
        examples=["pytest tests/test_auth.py::test_login -xvs"],
    )
    status: FeatureStatus = Field(
        default=FeatureStatus.PENDING,
        description="功能点状态",
    )


class FeatureUpdate(FeatureBase):
    """更新 Feature 请求模型"""

    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="功能点名称",
    )
    description: Optional[str] = Field(
        default=None,
        description="功能点描述",
    )
    test_command: Optional[str] = Field(
        default=None,
        description="测试命令",
    )
    status: Optional[FeatureStatus] = Field(
        default=None,
        description="功能点状态",
    )


class FeatureResponse(FeatureBase, IDMixin, TimestampMixin, StatusMixin):
    """Feature 响应模型"""

    block_id: str = Field(description="所属模块 ID")
    name: str = Field(description="功能点名称")
    description: Optional[str] = Field(description="功能点描述")
    test_command: str = Field(description="测试命令")
    block_name: Optional[str] = Field(default=None, description="模块名称")
    test_count: int = Field(default=0, description="测试数量")


class FeatureDetailResponse(FeatureResponse):
    """Feature 详情响应模型"""

    pass  # 可以添加更多字段，如关联的测试列表


class FeatureListResponse(FeatureBase):
    """Feature 列表响应模型"""

    features: list[FeatureResponse] = Field(description="功能点列表")
    total: int = Field(description="总数")


# 导出模型
__all__ = [
    "FeatureCreate",
    "FeatureUpdate",
    "FeatureResponse",
    "FeatureDetailResponse",
    "FeatureListResponse",
]