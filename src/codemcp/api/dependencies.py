"""
FastAPI 依赖项

API 路由的依赖注入函数。
"""

from typing import AsyncGenerator, Dict, Optional

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..config import settings
from ..database.session import get_db_session
from ..exceptions import AuthenticationError
from ..models.user import User
from ..utils.jwt import verify_token as verify_jwt_token
from ..utils.password import verify_password
from sqlalchemy import select
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
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme),
) -> Optional[Dict]:
    """验证访问令牌
    
    根据 auth_enabled 配置决定是否需要认证：
    - 如果 auth_enabled=False: 返回 None，表示不需要认证
    - 如果 auth_enabled=True: 需要有效的 JWT 令牌

    Args:
        credentials: HTTP 认证凭证

    Returns:
        Optional[Dict]: 令牌 payload 信息，如果 auth_enabled=False 则返回 None

    Raises:
        HTTPException: 认证失败（当 auth_enabled=True 时）
    """
    # 如果认证被禁用，直接返回 None
    if not settings.auth_enabled:
        return None

    # 认证启用，但缺少凭证
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证已启用，但缺少认证凭证",
        )

    token = credentials.credentials

    try:
        # 验证 JWT 令牌
        payload = await verify_jwt_token(token)
        return payload
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"无效的认证凭证: {str(e)}",
        )


async def get_current_user(
    payload: Optional[Dict] = Depends(verify_token),
    db: AsyncSession = Depends(get_db_session),
) -> Optional[User]:
    """获取当前用户对象
    
    根据 auth_enabled 配置决定：
    - 如果 auth_enabled=False: 返回 None，表示匿名用户
    - 如果 auth_enabled=True: 返回对应的用户对象

    Args:
        payload: 令牌 payload（可能为 None）
        db: 数据库会话

    Returns:
        Optional[User]: 用户对象，如果 auth_enabled=False 则返回 None

    Raises:
        HTTPException: 用户不存在或未激活（当 auth_enabled=True 时）
    """
    # 如果认证被禁用，返回 None 表示匿名用户
    if not settings.auth_enabled:
        return None

    # 认证启用，但缺少 payload（不应该发生，因为 verify_token 会抛出异常）
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证已启用，但缺少用户信息",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的令牌 payload",
        )

    # 从数据库获取用户
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户未激活",
        )

    return user


async def require_admin(
    user: Optional[User] = Depends(get_current_user),
) -> User:
    """要求管理员权限
    
    根据 auth_enabled 配置决定：
    - 如果 auth_enabled=False: 返回模拟的管理员用户
    - 如果 auth_enabled=True: 检查用户是否为超级用户

    Args:
        user: 当前用户（可能为 None）

    Returns:
        User: 管理员用户

    Raises:
        HTTPException: 权限不足（当 auth_enabled=True 时）
    """
    # 如果认证被禁用，返回模拟的管理员用户
    if not settings.auth_enabled:
        return User(
            id="anonymous-admin",
            username="anonymous",
            email="anonymous@example.com",
            is_active=True,
            is_superuser=True,
            hashed_password=""
        )

    # 认证启用，但缺少用户（不应该发生）
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="需要认证",
        )

    # 检查是否为超级用户
    if not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )
    
    return user


async def authenticate_user(
    username: str,
    password: str,
    db: AsyncSession = Depends(get_db_session)
) -> User:
    """验证用户凭据

    Args:
        username: 用户名
        password: 密码
        db: 数据库会话

    Returns:
        User: 验证通过的用户

    Raises:
        HTTPException: 认证失败
    """
    # 查找用户
    result = await db.execute(
        select(User).where(User.username == username)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户未激活",
        )

    # 验证密码
    if not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    return user


def get_settings():
    """获取配置依赖"""
    return settings


# 公共依赖（不需要认证）
PublicDeps = {
    "db": get_db,
    "settings": get_settings,
}

# 受保护依赖（根据配置决定是否需要认证）
# 注意：这些依赖现在会根据 auth_enabled 配置自动处理认证
ProtectedDeps = {
    **PublicDeps,
    "current_user": get_current_user,
}

# 管理员依赖
AdminDeps = {
    **ProtectedDeps,
    "admin_user": require_admin,
}