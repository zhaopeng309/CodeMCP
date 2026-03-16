"""
通用 Pydantic 模型

共享的请求/响应模型和工具函数。
"""

from datetime import datetime
from typing import Any, Generic, List, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """分页参数"""

    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应"""

    items: List[T] = Field(description="数据列表")
    total: int = Field(description="总数量")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页数量")
    total_pages: int = Field(description="总页数")


class ErrorResponse(BaseModel):
    """错误响应"""

    error: str = Field(description="错误类型")
    message: str = Field(description="错误信息")
    details: Optional[dict] = Field(default=None, description="错误详情")


class SuccessResponse(BaseModel, Generic[T]):
    """成功响应"""

    success: bool = Field(default=True, description="是否成功")
    data: Optional[T] = Field(default=None, description="响应数据")
    message: Optional[str] = Field(default=None, description="成功信息")


class TimestampMixin(BaseModel):
    """时间戳混合模型"""

    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")


class IDMixin(BaseModel):
    """ID 混合模型"""

    id: str = Field(description="唯一标识符")


class StatusMixin(BaseModel):
    """状态混合模型"""

    status: str = Field(description="状态")


# 配置 Pydantic 模型
model_config = ConfigDict(
    from_attributes=True,
    populate_by_name=True,
    str_strip_whitespace=True,
    use_enum_values=True,
)