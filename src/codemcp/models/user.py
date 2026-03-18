"""
用户数据模型

用户认证和授权相关的数据模型。
支持全局管理员用户和项目级用户。
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class User(Base):
    """用户模型
    
    支持两种类型的用户：
    1. 全局管理员用户：system_id为None，is_superuser为True，可以在任何项目中有效
    2. 项目级用户：system_id不为None，is_superuser为False，仅对特定项目有效
    """
    
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    username: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="用户名",
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="邮箱地址",
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="哈希后的密码",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否激活",
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否超级用户（全局管理员）",
    )
    system_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        nullable=True,
        index=True,
        comment="关联的系统ID（项目ID），为None表示全局用户",
    )
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        nullable=False,
        comment="创建时间",
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="更新时间",
    )
    
    # 复合唯一约束：用户名+系统ID
    # 确保同一系统内用户名唯一，全局用户（system_id为None）用户名也唯一
    __table_args__ = (
        UniqueConstraint('username', 'system_id', name='uq_user_username_system'),
    )


class RevokedToken(Base):
    """已撤销的令牌模型"""
    
    __tablename__ = "revoked_tokens"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    token_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="JWT ID (jti)",
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
        comment="用户ID",
    )
    revoked_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        nullable=False,
        comment="撤销时间",
    )
    reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="撤销原因",
    )