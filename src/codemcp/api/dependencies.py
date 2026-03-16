"""
FastAPI 依赖项

API 路由的依赖注入函数。
"""

from typing import AsyncGenerator

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..config import settings
from ..database.session import get_db_session
from ..exceptions import AuthenticationError, AuthorizationError
from sqlalchemy.ext.asyncio import AsyncSession

security_scheme = HTTPBearer(auto_error=False)


async def get_db(
    session: AsyncSession = Depends(get_db_session),
) -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话依赖

    Args:
        session: 数据库会话

    Yields:
        数据库会话
    """
    yield session


async def verify_token(
    credentials: HTTPAuthorizationCredentials = Security(security_scheme),
) -> str:
    """验证访问令牌

    Args:
        credentials: HTTP 认证凭证

    Returns:
        用户 ID 或标识

    Raises:
        HTTPException: 认证失败
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少认证凭证",
        )

    token = credentials.credentials

    # 简化实现：实际项目需要验证 JWT 或其他令牌
    # 这里仅做示例检查
    if token != "demo-token":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭证",
        )

    return "demo-user"


async def require_admin(
    user_id: str = Depends(verify_token),
) -> str:
    """要求管理员权限

    Args:
        user_id: 用户 ID

    Returns:
        用户 ID

    Raises:
        HTTPException: 权限不足
    """
    # 简化实现：实际项目需要检查用户角色
    if user_id != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )
    return user_id


async def get_current_user(
    user_id: str = Depends(verify_token),
) -> str:
    """获取当前用户

    Args:
        user_id: 用户 ID

    Returns:
        用户 ID
    """
    return user_id


def get_settings():
    """获取配置依赖"""
    return settings


# 公共依赖（不需要认证）
PublicDeps = {
    "db": get_db,
    "settings": get_settings,
}

# 受保护依赖（需要认证）
ProtectedDeps = {
    **PublicDeps,
    "current_user": get_current_user,
}

# 管理员依赖
AdminDeps = {
    **ProtectedDeps,
    "admin_user": require_admin,
}