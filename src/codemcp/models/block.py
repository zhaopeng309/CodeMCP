"""
Block 模型

功能模块的模型定义。
"""

import enum
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .system import SystemModel
    from .feature import FeatureModel


class BlockStatus(str, enum.Enum):
    """模块状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABORTED = "aborted"


class BlockModel(BaseModel):
    """Block 模型类"""

    system_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("system_model.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="所属系统 ID",
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        doc="模块名称",
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        doc="模块描述",
    )
    priority: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        index=True,
        doc="优先级（数字越小优先级越高）",
    )
    status: Mapped[BlockStatus] = mapped_column(
        SQLEnum(BlockStatus),
        default=BlockStatus.PENDING,
        nullable=False,
        index=True,
        doc="模块状态",
    )

    # 关系
    system: Mapped["SystemModel"] = relationship(
        "SystemModel",
        back_populates="blocks",
        lazy="joined",
        doc="所属系统",
    )
    features: Mapped[list["FeatureModel"]] = relationship(
        "FeatureModel",
        back_populates="block",
        cascade="all, delete-orphan",
        lazy="selectin",
        doc="所属功能点列表",
    )

    def __repr__(self) -> str:
        """对象表示"""
        return f"<BlockModel(id={self.id!r}, name={self.name!r}, status={self.status.value})>"