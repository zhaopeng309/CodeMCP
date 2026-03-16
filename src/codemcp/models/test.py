"""
Test 模型

测试单元的模型定义。
"""

import enum
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text, Float, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .feature import FeatureModel


class TestStatus(str, enum.Enum):
    """测试状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ABORTED = "aborted"


class TestModel(BaseModel):
    """Test 模型类"""

    feature_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("feature_model.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="所属功能点 ID",
    )
    command: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="执行的命令",
    )
    exit_code: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        doc="退出码",
    )
    stdout: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="标准输出",
    )
    stderr: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="标准错误",
    )
    duration: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        doc="执行时长（秒）",
    )
    status: Mapped[TestStatus] = mapped_column(
        SQLEnum(TestStatus),
        default=TestStatus.PENDING,
        nullable=False,
        index=True,
        doc="测试状态",
    )
    retry_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="重试次数",
    )
    max_retries: Mapped[int] = mapped_column(
        Integer,
        default=3,
        nullable=False,
        doc="最大重试次数",
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="错误信息",
    )

    # 关系
    feature: Mapped["FeatureModel"] = relationship(
        "FeatureModel",
        back_populates="tests",
        lazy="joined",
        doc="所属功能点",
    )

    def __repr__(self) -> str:
        """对象表示"""
        return f"<TestModel(id={self.id!r}, status={self.status.value}, exit_code={self.exit_code})>"