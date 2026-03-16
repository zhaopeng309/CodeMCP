"""
数据库会话管理

异步数据库会话工厂和依赖注入。
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ..config import settings

# 创建异步引擎
engine = create_async_engine(
    settings.database_url.replace("sqlite://", "sqlite+aiosqlite://"),
    echo=settings.debug,
    future=True,
)

# 创建异步会话工厂
AsyncSessionFactory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话的依赖函数

    Yields:
        AsyncSession: 异步数据库会话
    """
    async with AsyncSessionFactory() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """初始化数据库（创建所有表）"""
    from ..models.base import Base

    async with engine.begin() as conn:
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """关闭数据库连接"""
    await engine.dispose()