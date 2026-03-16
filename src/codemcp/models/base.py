"""
SQLAlchemy 模型基类

定义所有模型的共享基类和混合类。
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

# SQLAlchemy 2.0 风格的基础类
Base = declarative_base()


class TimestampMixin:
    """时间戳混合类"""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class UUIDMixin:
    """UUID 主键混合类"""

    @declared_attr
    def id(cls) -> Mapped[str]:
        """UUID 主键"""
        return mapped_column(
            String(36),
            primary_key=True,
            default=lambda: str(uuid.uuid4()),
            index=True,
        )


class TableNameMixin:
    """表名混合类"""

    @declared_attr
    def __tablename__(cls) -> str:
        """自动生成表名（驼峰转蛇形）"""
        import re
        name = cls.__name__
        # 驼峰转蛇形
        name = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
        # 移除尾部的 '_model' 或 '_mixin'
        if name.endswith(('_model', '_mixin')):
            name = name.rsplit('_', 1)[0]
        return name


class BaseModel(Base, UUIDMixin, TimestampMixin, TableNameMixin):
    """基础模型类，包含所有通用字段"""

    __abstract__ = True

    def to_dict(self, exclude: set = None) -> dict[str, Any]:
        """将模型转换为字典

        Args:
            exclude: 要排除的字段集合

        Returns:
            模型字段字典
        """
        if exclude is None:
            exclude = set()

        result = {}
        for column in self.__table__.columns:
            if column.name in exclude:
                continue
            value = getattr(self, column.name)
            # 处理 datetime 对象
            if hasattr(value, 'isoformat'):
                value = value.isoformat()
            result[column.name] = value
        return result

    def __repr__(self) -> str:
        """对象表示"""
        class_name = self.__class__.__name__
        attrs = []
        for column in self.__table__.columns:
            if column.primary_key:
                value = getattr(self, column.name)
                attrs.append(f"{column.name}={value!r}")
                break
        return f"<{class_name}({', '.join(attrs)})>"