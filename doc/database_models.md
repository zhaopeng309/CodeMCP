# 数据库模型与ORM层实现

## 概述
本文档详细描述 CodeMCP 的数据库模型设计、SQLAlchemy ORM 实现、以及相关的数据访问模式。

## 基础模型

### Base 模型
```python
# src/codemcp/models/base.py
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import DateTime, MetaData
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, declared_attr
from sqlalchemy.sql import func

# 使用命名约定规范
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=convention)


class Base(DeclarativeBase):
    """所有模型的基类"""
    
    metadata = metadata
    
    @declared_attr.directive
    def __tablename__(cls) -> str:
        """自动生成表名：将类名转换为小写复数形式"""
        import re
        name = re.sub(r'(?<!^)(?=[A-Z])', '_', cls.__name__).lower()
        if name.endswith('y'):
            return name[:-1] + 'ies'
        elif name.endswith('s'):
            return name + 'es'
        else:
            return name + 's'
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    def to_dict(self, exclude: set = None) -> Dict[str, Any]:
        """将模型实例转换为字典"""
        if exclude is None:
            exclude = set()
        
        result = {}
        for column in self.__table__.columns:
            if column.name in exclude:
                continue
            result[column.name] = getattr(self, column.name)
        
        return result
    
    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """从字典更新模型属性"""
        for key, value in data.items():
            if hasattr(self, key) and not key.startswith('_'):
                setattr(self, key, value)
```

## 核心模型

### System 模型
```python
# src/codemcp/models/system.py
from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import String, Text, Enum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .block import Block


class System(Base):
    """系统/业务领域模型"""
    
    __tablename__ = "systems"
    
    # 覆盖自动生成的表名
    __tablename__ = "systems"
    
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="系统名称"
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="系统描述"
    )
    status: Mapped[str] = mapped_column(
        Enum("active", "archived", name="system_status"),
        default="active",
        nullable=False,
        comment="系统状态"
    )
    
    # 关系
    blocks: Mapped[List["Block"]] = relationship(
        "Block",
        back_populates="system",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="Block.priority.desc(), Block.created_at.asc()"
    )
    
    # 索引
    __table_args__ = (
        Index("ix_systems_status_created", "status", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<System(id={self.id}, name='{self.name}', status='{self.status}')>"
    
    @property
    def stats(self) -> Dict[str, Any]:
        """计算系统统计信息"""
        from sqlalchemy import func
        
        # 这里需要在查询时计算，这里只是返回结构
        return {
            "total_blocks": len(self.blocks),
            "completed_blocks": sum(1 for b in self.blocks if b.status == "completed"),
            "total_features": sum(len(b.features) for b in self.blocks),
            "completed_features": sum(
                sum(1 for f in b.features if f.status == "passed") 
                for b in self.blocks
            ),
        }
```

### Block 模型
```python
# src/codemcp/models/block.py
from typing import TYPE_CHECKING, List

from sqlalchemy import ForeignKey, String, Text, Integer, Enum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .system import System
    from .feature import Feature


class Block(Base):
    """功能模块模型"""
    
    __tablename__ = "blocks"
    
    system_id: Mapped[int] = mapped_column(
        ForeignKey("systems.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所属系统ID"
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="模块名称"
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="模块描述"
    )
    priority: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="优先级（数字越小优先级越高）"
    )
    status: Mapped[str] = mapped_column(
        Enum("pending", "in_progress", "completed", "aborted", name="block_status"),
        default="pending",
        nullable=False,
        comment="模块状态"
    )
    
    # 关系
    system: Mapped["System"] = relationship(
        "System",
        back_populates="blocks",
        lazy="joined"
    )
    features: Mapped[List["Feature"]] = relationship(
        "Feature",
        back_populates="block",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="Feature.priority.desc(), Feature.created_at.asc()"
    )
    
    # 索引
    __table_args__ = (
        Index("ix_blocks_system_status", "system_id", "status"),
        Index("ix_blocks_priority_status", "priority", "status"),
        Index("ix_blocks_status_updated", "status", "updated_at"),
    )
    
    def __repr__(self) -> str:
        return f"<Block(id={self.id}, name='{self.name}', status='{self.status}')>"
    
    def update_status_from_features(self) -> None:
        """根据Feature状态更新Block状态"""
        if not self.features:
            return
        
        feature_statuses = [f.status for f in self.features]
        
        if any(status == "aborted" for status in feature_statuses):
            self.status = "aborted"
        elif all(status == "passed" for status in feature_statuses):
            self.status = "completed"
        elif any(status in ["running", "pending"] for status in feature_statuses):
            self.status = "in_progress"
        else:
            self.status = "pending"
```

### Feature 模型
```python
# src/codemcp/models/feature.py
from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import ForeignKey, String, Text, Integer, Float, Enum, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .block import Block
    from .test import Test


class Feature(Base):
    """功能点模型"""
    
    __tablename__ = "features"
    
    block_id: Mapped[int] = mapped_column(
        ForeignKey("blocks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所属模块ID"
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="功能点名称"
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="功能点描述"
    )
    test_command: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="测试命令"
    )
    priority: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="优先级"
    )
    status: Mapped[str] = mapped_column(
        Enum("pending", "running", "passed", "failed", "aborted", name="feature_status"),
        default="pending",
        nullable=False,
        comment="功能点状态"
    )
    retry_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="重试次数"
    )
    max_retries: Mapped[int] = mapped_column(
        Integer,
        default=3,
        nullable=False,
        comment="最大重试次数"
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="开始执行时间"
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="完成时间"
    )
    duration: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="执行时长（秒）"
    )
    
    # 关系
    block: Mapped["Block"] = relationship(
        "Block",
        back_populates="features",
        lazy="joined"
    )
    tests: Mapped[List["Test"]] = relationship(
        "Test",
        back_populates="feature",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="Test.created_at.desc()"
    )
    
    # 索引
    __table_args__ = (
        Index("ix_features_block_status", "block_id", "status"),
        Index("ix_features_status_priority", "status", "priority"),
        Index("ix_features_retry_count", "retry_count"),
        Index("ix_features_started_at", "started_at"),
    )
    
    def __repr__(self) -> str:
        return f"<Feature(id={self.id}, name='{self.name}', status='{self.status}')>"
    
    def mark_as_started(self) -> None:
        """标记为开始执行"""
        self.status = "running"
        self.started_at = datetime.utcnow()
    
    def mark_as_completed(self, success: bool, duration: float = None) -> None:
        """标记为完成"""
        self.status = "passed" if success else "failed"
        self.completed_at = datetime.utcnow()
        if duration is not None:
            self.duration = duration
        
        # 更新所属Block状态
        self.block.update_status_from_features()
    
    def can_retry(self) -> bool:
        """检查是否可以重试"""
        return self.status == "failed" and self.retry_count < self.max_retries
    
    def prepare_for_retry(self) -> None:
        """准备重试"""
        if self.can_retry():
            self.status = "pending"
            self.retry_count += 1
            self.started_at = None
            self.completed_at = None
            self.duration = None
```

### Test 模型
```python
# src/codemcp/models/test.py
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Text, Integer, Float, Enum, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .feature import Feature


class Test(Base):
    """测试单元模型"""
    
    __tablename__ = "tests"
    
    feature_id: Mapped[int] = mapped_column(
        ForeignKey("features.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所属功能点ID"
    )
    command: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="执行的命令"
    )
    exit_code: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="退出码"
    )
    stdout: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="标准输出"
    )
    stderr: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="标准错误"
    )
    duration: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="执行时长（秒）"
    )
    status: Mapped[str] = mapped_column(
        Enum("pending", "running", "passed", "failed", name="test_status"),
        default="pending",
        nullable=False,
        comment="测试状态"
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="开始执行时间"
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="完成时间"
    )
    
    # 关系
    feature: Mapped["Feature"] = relationship(
        "Feature",
        back_populates="tests",
        lazy="joined"
    )
    
    # 索引
    __table_args__ = (
        Index("ix_tests_feature_status", "feature_id", "status"),
        Index("ix_tests_exit_code", "exit_code"),
        Index("ix_tests_started_at", "started_at"),
    )
    
    def __repr__(self) -> str:
        return f"<Test(id={self.id}, feature_id={self.feature_id}, status='{self.status}')>"
    
    def mark_as_started(self) -> None:
        """标记为开始执行"""
        self.status = "running"
        self.started_at = datetime.utcnow()
    
    def mark_as_completed(
        self, 
        exit_code: int, 
        stdout: str = None, 
        stderr: str = None,
        duration: float = None
    ) -> None:
        """标记为完成"""
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.duration = duration
        self.completed_at = datetime.utcnow()
        self.status = "passed" if exit_code == 0 else "failed"
        
        # 如果测试失败，更新所属Feature状态
        if exit_code != 0:
            self.feature.mark_as_completed(success=False, duration=duration)
        else:
            # 检查是否所有测试都通过
            all_passed = all(t.status == "passed" for t in self.feature.tests)
            if all_passed:
                self.feature.mark_as_completed(success=True, duration=duration)
```

## 数据库会话管理

```python
# src/codemcp/database/session.py
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from ..config import settings

# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,
)

# 创建会话工厂
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """获取数据库会话（依赖注入）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def db_session() -> Generator[Session, None, None]:
    """上下文管理器形式的数据库会话"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    """初始化数据库（创建表）"""
    from ..models.base import Base
    
    Base.metadata.create_all(bind=engine)
```

## 数据访问模式

### Repository 模式示例
```python
# src/codemcp/database/repositories/system_repository.py
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from ...models.system import System


class SystemRepository:
    """System 数据访问层"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get(self, system_id: int) -> Optional[System]:
        """根据ID获取系统"""
        return self.db.get(System, system_id)
    
    def get_by_name(self, name: str) -> Optional[System]:
        """根据名称获取系统"""
        stmt = select(System).where(System.name == name)
        return self.db.scalar(stmt)
    
    def list(
        self, 
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[System]:
        """列出系统"""
        stmt = select(System).order_by(desc(System.created_at))
        
        if status:
            stmt = stmt.where(System.status == status)
        
        if skip:
            stmt = stmt.offset(skip)
        if limit:
            stmt = stmt.limit(limit)
        
        return list(self.db.scalars(stmt))
    
    def create(self, name: str, description: str = None) -> System:
        """创建新系统"""
        system = System(name=name, description=description)
        self