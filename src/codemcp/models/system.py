"""
System 模型

业务领域或项目实例的模型定义。
"""

import enum
from typing import TYPE_CHECKING

from sqlalchemy import String, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .block import BlockModel


class SystemStatus(str, enum.Enum):
    """系统状态枚举"""
    ACTIVE = "active"
    ARCHIVED = "archived"


class SystemModel(BaseModel):
    """System 模型类"""

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        doc="系统名称",
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        doc="系统描述",
    )
    status: Mapped[SystemStatus] = mapped_column(
        SQLEnum(SystemStatus),
        default=SystemStatus.ACTIVE,
        nullable=False,
        index=True,
        doc="系统状态",
    )

    # 关系
    blocks: Mapped[list["BlockModel"]] = relationship(
        "BlockModel",
        back_populates="system",
        cascade="all, delete-orphan",
        lazy="selectin",
        doc="所属模块列表",
    )

    def __repr__(self) -> str:
        """对象表示"""
        return f"<SystemModel(id={self.id!r}, name={self.name!r}, status={self.status.value})>"