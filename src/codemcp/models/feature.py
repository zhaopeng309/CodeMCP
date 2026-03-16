"""
Feature 模型

功能点的模型定义。
"""

import enum
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .block import BlockModel
    from .test import TestModel


class FeatureStatus(str, enum.Enum):
    """功能点状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ABORTED = "aborted"


class FeatureModel(BaseModel):
    """Feature 模型类"""

    block_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("block_model.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="所属模块 ID",
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        doc="功能点名称",
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        doc="功能点描述",
    )
    test_command: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="测试命令",
    )
    status: Mapped[FeatureStatus] = mapped_column(
        SQLEnum(FeatureStatus),
        default=FeatureStatus.PENDING,
        nullable=False,
        index=True,
        doc="功能点状态",
    )

    # 关系
    block: Mapped["BlockModel"] = relationship(
        "BlockModel",
        back_populates="features",
        lazy="joined",
        doc="所属模块",
    )
    tests: Mapped[list["TestModel"]] = relationship(
        "TestModel",
        back_populates="feature",
        cascade="all, delete-orphan",
        lazy="selectin",
        doc="所属测试列表",
    )

    def __repr__(self) -> str:
        """对象表示"""
        return f"<FeatureModel(id={self.id!r}, name={self.name!r}, status={self.status.value})>"