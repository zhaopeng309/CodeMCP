"""
认证路由

用户认证相关的 API 端点，包括登录、注册、令牌管理等。
"""

from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ...config import settings
from ...database.session import get_db_session
from ...exceptions import AuthenticationError
from ...models.user import User
from ...utils.jwt import create_token, revoke_token, revoke_all_user_tokens
from ...utils.password import get_password_hash
from ..dependencies import authenticate_user, get_current_user, security_scheme
from ..schemas.auth import (
    Token,
    UserLogin,
    UserRegister,
    UserResponse,
    UserUpdate,
    PasswordResetRequest,
    PasswordResetConfirm,
    LogoutRequest,
)
from ..schemas.common import SuccessResponse, ErrorResponse

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=Token)
async def login(
    user_login: UserLogin,
    db: AsyncSession = Depends(get_db_session),
) -> Token:
    """用户登录
    
    Args:
        user_login: 登录信息
        db: 数据库会话
        
    Returns:
        Token: 访问令牌
        
    Raises:
        HTTPException: 认证失败
    """
    # 如果认证被禁用，返回模拟令牌
    if not settings.auth_enabled:
        return Token(
            access_token="auth-disabled-no-token-needed",
            token_type="none"
        )
    
    try:
        # 验证用户凭据
        user = await authenticate_user(user_login.username, user_login.password, db)
        
        # 创建 JWT 令牌
        token = create_token(
            user_id=str(user.id),
            username=user.username,
            email=user.email,
            is_superuser=user.is_superuser
        )
        
        return Token(access_token=token, token_type="bearer")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录失败: {str(e)}",
        )


@router.post("/register", response_model=UserResponse)
async def register(
    user_register: UserRegister,
    db: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    """用户注册
    
    Args:
        user_register: 注册信息
        db: 数据库会话
        
    Returns:
        UserResponse: 注册成功的用户信息
        
    Raises:
        HTTPException: 注册失败
    """
    # 如果认证被禁用，返回错误
    if not settings.auth_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="认证已禁用，无法注册新用户",
        )
    
    # 检查密码是否匹配
    if user_register.password != user_register.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码和确认密码不匹配",
        )
    
    # 检查用户名是否已存在
    from sqlalchemy import select
    result = await db.execute(
        select(User).where(User.username == user_register.username)
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在",
        )
    
    # 检查邮箱是否已存在（如果提供了邮箱）
    if user_register.email:
        result = await db.execute(
            select(User).where(User.email == user_register.email)
        )
        existing_email = result.scalar_one_or_none()
        
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱地址已存在",
            )
    
    try:
        # 创建新用户
        hashed_password = get_password_hash(user_register.password)
        user = User(
            username=user_register.username,
            email=user_register.email,
            hashed_password=hashed_password,
            is_active=True,
            is_superuser=False  # 新用户默认不是超级用户
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        # 返回用户信息
        return UserResponse(
            id=str(user.id),
            username=user.username,
            email=user.email,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            created_at=user.created_at.isoformat() if user.created_at else "",
            updated_at=user.updated_at.isoformat() if user.updated_at else ""
        )
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册失败: {str(e)}",
        )


@router.post("/logout", response_model=SuccessResponse)
async def logout(
    logout_request: LogoutRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db_session),
) -> SuccessResponse:
    """用户登出（撤销令牌）
    
    Args:
        logout_request: 登出请求
        credentials: 认证凭证
        db: 数据库会话
        
    Returns:
        SuccessResponse: 操作结果
        
    Raises:
        HTTPException: 操作失败
    """
    # 如果认证被禁用，直接返回成功
    if not settings.auth_enabled:
        return SuccessResponse(
            success=True,
            message="认证已禁用，无需登出操作"
        )
    
    try:
        token_to_revoke = logout_request.token
        
        # 如果没有指定令牌，则撤销当前令牌
        if not token_to_revoke and credentials:
            token_to_revoke = credentials.credentials
        
        if not token_to_revoke:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="未指定要撤销的令牌",
            )
        
        # 撤销令牌
        success = await revoke_token(token_to_revoke, reason="用户主动登出")
        
        if success:
            return SuccessResponse(
                success=True,
                message="登出成功，令牌已撤销"
            )
        else:
            return SuccessResponse(
                success=False,
                message="令牌无效或已过期"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登出失败: {str(e)}",
        )


@router.post("/logout/all", response_model=SuccessResponse)
async def logout_all(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> SuccessResponse:
    """撤销用户的所有令牌
    
    Args:
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        SuccessResponse: 操作结果
    """
    # 如果认证被禁用，直接返回成功
    if not settings.auth_enabled:
        return SuccessResponse(
            success=True,
            message="认证已禁用，无需撤销令牌操作"
        )
    
    try:
        # 撤销用户的所有令牌
        count = await revoke_all_user_tokens(str(current_user.id), reason="用户撤销所有令牌")
        
        return SuccessResponse(
            success=True,
            message=f"已撤销用户的所有令牌（{count}个）"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"撤销所有令牌失败: {str(e)}",
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """获取当前用户信息
    
    Args:
        current_user: 当前用户
        
    Returns:
        UserResponse: 用户信息
    """
    # 如果认证被禁用，返回匿名用户信息
    if not settings.auth_enabled:
        return UserResponse(
            id="anonymous",
            username="anonymous",
            email="anonymous@example.com",
            is_active=True,
            is_superuser=False,
            created_at="",
            updated_at=""
        )
    
    return UserResponse(
        id=str(current_user.id),
        username=current_user.username,
        email=current_user.email,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
        created_at=current_user.created_at.isoformat() if current_user.created_at else "",
        updated_at=current_user.updated_at.isoformat() if current_user.updated_at else ""
    )


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    """更新当前用户信息
    
    Args:
        user_update: 更新信息
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        UserResponse: 更新后的用户信息
        
    Raises:
        HTTPException: 更新失败
    """
    # 如果认证被禁用，返回错误
    if not settings.auth_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="认证已禁用，无法更新用户信息",
        )
    
    try:
        # 更新邮箱（如果提供了）
        if user_update.email is not None:
            # 检查邮箱是否已被其他用户使用
            from sqlalchemy import select
            result = await db.execute(
                select(User).where(
                    User.email == user_update.email,
                    User.id != current_user.id
                )
            )
            existing_email = result.scalar_one_or_none()
            
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="邮箱地址已被其他用户使用",
                )
            
            current_user.email = user_update.email
        
        # 更新密码（如果提供了）
        if user_update.password:
            # 验证当前密码（如果提供了）
            if not user_update.current_password:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="修改密码需要提供当前密码",
                )
            
            # 验证当前密码
            from ...utils.password import verify_password
            if not verify_password(user_update.current_password, current_user.hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="当前密码错误",
                )
            
            # 更新密码
            current_user.hashed_password = get_password_hash(user_update.password)
        
        await db.commit()
        await db.refresh(current_user)
        
        return UserResponse(
            id=str(current_user.id),
            username=current_user.username,
            email=current_user.email,
            is_active=current_user.is_active,
            is_superuser=current_user.is_superuser,
            created_at=current_user.created_at.isoformat() if current_user.created_at else "",
            updated_at=current_user.updated_at.isoformat() if current_user.updated_at else ""
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新用户信息失败: {str(e)}",
        )


@router.post("/password/reset/request", response_model=SuccessResponse)
async def request_password_reset(
    reset_request: PasswordResetRequest,
    db: AsyncSession = Depends(get_db_session),
) -> SuccessResponse:
    """请求密码重置（发送重置邮件）
    
    Args:
        reset_request: 重置请求
        db: 数据库会话
        
    Returns:
        SuccessResponse: 操作结果
        
    Note:
        这是一个简化实现，实际项目中应该发送重置邮件
    """
    # 如果认证被禁用，返回错误
    if not settings.auth_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="认证已禁用，无法重置密码",
        )
    
    # 查找用户
    from sqlalchemy import select
    result = await db.execute(
        select(User).where(User.email == reset_request.email)
    )
    user = result.scalar_one_or_none()
    
    if user:
        # 实际项目中：生成重置令牌并发送邮件
        # 这里简化实现，只返回成功消息
        return SuccessResponse(
            success=True,
            message="如果邮箱存在，重置链接已发送"
        )
    else:
        # 出于安全考虑，即使邮箱不存在也返回相同消息
        return SuccessResponse(
            success=True,
            message="如果邮箱存在，重置链接已发送"
        )


@router.post("/password/reset/confirm", response_model=SuccessResponse)
async def confirm_password_reset(
    reset_confirm: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db_session),
) -> SuccessResponse:
    """确认密码重置
    
    Args:
        reset_confirm: 重置确认信息
        db: 数据库会话
        
    Returns:
        SuccessResponse: 操作结果
        
    Note:
        这是一个简化实现，实际项目中应该验证重置令牌
    """
    # 如果认证被禁用，返回错误
    if not settings.auth_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="认证已禁用，无法重置密码",
        )
    
    # 实际项目中：验证重置令牌并更新密码
    # 这里简化实现，假设令牌有效
    
    try:
        # 解码令牌获取用户信息（简化）
        from ...utils.jwt import decode_token
        try:
            payload = decode_token(reset_confirm.token)
            user_id = payload.get("sub")
            
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="无效的重置令牌",
                )
            
            # 查找用户
            from sqlalchemy import select
            result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="用户不存在",
                )
            
            # 更新密码
            user.hashed_password = get_password_hash(reset_confirm.new_password)
            await db.commit()
            
            return SuccessResponse(
                success=True,
                message="密码重置成功"
            )
            
        except AuthenticationError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效或过期的重置令牌",
            )
            
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"密码重置失败: {str(e)}",
        )


@router.get("/health", response_model=Dict)
async def auth_health() -> Dict:
    """认证服务健康检查
    
    Returns:
        Dict: 健康状态
    """
    return {
        "status": "healthy",
        "service": "authentication",
        "auth_enabled": settings.auth_enabled,
        "jwt_enabled": settings.auth_enabled,  # 与auth_enabled保持一致
        "algorithm": settings.jwt_algorithm if settings.auth_enabled else "none"
    }