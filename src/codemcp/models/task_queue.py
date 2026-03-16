"""
Task Queue 模型

任务队列的模型定义。
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .test import TestModel


class QueueStatus(str, enum.Enum):
    """队列状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskQueueModel(BaseModel):
    """任务队列模型类"""

    test_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("test_model.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="关联的测试 ID",
    )
    priority: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        index=True,
        doc="优先级（数字越小优先级越高）",
    )
    status: Mapped[QueueStatus] = mapped_column(
        SQLEnum(QueueStatus),
        default=QueueStatus.PENDING,
        nullable=False,
        index=True,
        doc="队列状态",
    )
    scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="计划执行时间",
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="开始执行时间",
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="完成时间",
    )
    attempts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="尝试次数",
    )
    max_attempts: Mapped[int] = mapped_column(
        Integer,
        default=3,
        nullable=False,
        doc="最大尝试次数",
    )
    error_message: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
        doc="错误信息",
    )

    # 关系
    test: Mapped["TestModel"] = relationship(
        "TestModel",
        lazy="joined",
        doc="关联的测试",
    )

    def __repr__(self) -> str:
        """对象表示"""
        return f"<TaskQueueModel(id={self.id!r}, test_id={self.test_id!r}, status={self.status.value})>"