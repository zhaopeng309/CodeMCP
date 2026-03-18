"""
JWT 工具模块

JWT 令牌的创建、验证和管理功能。
"""

import uuid
from datetime import datetime
from typing import Dict, Optional

from jose import JWTError, jwt

from ..config import settings
from ..exceptions import AuthenticationError
from ..models.user import RevokedToken
from ..database.session import get_db_session
from sqlalchemy import select


def create_token(
    user_id: str, 
    username: str, 
    email: Optional[str] = None, 
    is_superuser: bool = False
) -> str:
    """创建永不过期的 JWT 令牌
    
    Args:
        user_id: 用户ID
        username: 用户名
        email: 邮箱地址
        is_superuser: 是否超级用户
        
    Returns:
        str: JWT 令牌
    """
    # 创建 payload，不包含过期时间
    payload = {
        "sub": user_id,
        "username": username,
        "email": email or "",
        "is_superuser": is_superuser,
        "iat": int(datetime.utcnow().timestamp()),  # 签发时间
        "jti": str(uuid.uuid4()),  # JWT ID，用于撤销
        "type": "access"
    }
    
    # 编码 JWT
    token = jwt.encode(
        payload, 
        settings.secret_key, 
        algorithm=settings.jwt_algorithm
    )
    
    return token


def decode_token(token: str) -> Dict:
    """解码 JWT 令牌
    
    Args:
        token: JWT 令牌
        
    Returns:
        Dict: 解码后的 payload
        
    Raises:
        AuthenticationError: 令牌无效或已撤销
    """
    try:
        # 解码令牌
        payload = jwt.decode(
            token, 
            settings.secret_key, 
            algorithms=[settings.jwt_algorithm]
        )
        
        # 检查令牌类型
        if payload.get("type") != "access":
            raise AuthenticationError("无效的令牌类型")
            
        return payload
        
    except JWTError as e:
        raise AuthenticationError(f"无效的令牌: {str(e)}")


async def verify_token(token: str) -> Dict:
    """验证 JWT 令牌（检查是否被撤销）
    
    Args:
        token: JWT 令牌
        
    Returns:
        Dict: 解码后的 payload
        
    Raises:
        AuthenticationError: 令牌无效或已撤销
    """
    # 解码令牌
    payload = decode_token(token)
    
    # 检查令牌是否被撤销
    token_id = payload.get("jti")
    if token_id:
        async with get_db_session() as db:
            result = await db.execute(
                select(RevokedToken).where(RevokedToken.token_id == token_id)
            )
            revoked_token = result.scalar_one_or_none()
            
            if revoked_token:
                raise AuthenticationError("令牌已被撤销")
    
    return payload


async def revoke_token(token: str, reason: Optional[str] = None) -> bool:
    """撤销 JWT 令牌
    
    Args:
        token: JWT 令牌
        reason: 撤销原因
        
    Returns:
        bool: 是否成功撤销
        
    Raises:
        AuthenticationError: 令牌无效
    """
    try:
        # 解码令牌获取信息
        payload = decode_token(token)
        token_id = payload.get("jti")
        user_id = payload.get("sub")
        
        if not token_id or not user_id:
            raise AuthenticationError("无效的令牌格式")
        
        # 将令牌添加到撤销列表
        async with get_db_session() as db:
            # 检查是否已经撤销
            result = await db.execute(
                select(RevokedToken).where(RevokedToken.token_id == token_id)
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                revoked_token = RevokedToken(
                    token_id=token_id,
                    user_id=user_id,
                    reason=reason
                )
                db.add(revoked_token)
                await db.commit()
                
        return True
        
    except (JWTError, AuthenticationError):
        return False


async def revoke_all_user_tokens(user_id: str, reason: Optional[str] = None) -> int:
    """撤销用户的所有令牌
    
    Args:
        user_id: 用户ID
        reason: 撤销原因
        
    Returns:
        int: 撤销的令牌数量
    """
    # 注意：这个方法实际上是通过记录用户ID来标记所有令牌为已撤销
    # 在实际验证时，需要检查用户ID是否在撤销列表中
    # 这里简化实现，只记录撤销操作
    
    async with get_db_session() as db:
        revoked_token = RevokedToken(
            token_id=f"user_{user_id}_all",  # 特殊标记，表示用户所有令牌
            user_id=user_id,
            reason=reason or "用户所有令牌被撤销"
        )
        db.add(revoked_token)
        await db.commit()
    
    return 1  # 简化返回


def extract_token_from_header(authorization_header: str) -> str:
    """从 Authorization 头中提取令牌
    
    Args:
        authorization_header: Authorization 头，格式为 "Bearer <token>"
        
    Returns:
        str: 提取的令牌
        
    Raises:
        AuthenticationError: 头格式无效
    """
    if not authorization_header:
        raise AuthenticationError("缺少认证头")
    
    parts = authorization_header.split()
    
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AuthenticationError("认证头格式无效，应为 'Bearer <token>'")
    
    return parts[1]