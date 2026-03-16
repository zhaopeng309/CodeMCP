"""
数据库引擎管理

数据库引擎实例和连接池配置。
"""

from sqlalchemy.ext.asyncio import create_async_engine

from ..config import settings

# 创建异步引擎实例
engine = create_async_engine(
    settings.database_url.replace("sqlite://", "sqlite+aiosqlite://"),
    echo=settings.debug,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600,
    future=True,
)

__all__ = ["engine"]