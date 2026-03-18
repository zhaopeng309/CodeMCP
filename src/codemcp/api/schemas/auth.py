"""
认证相关的 Pydantic 模型
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    """令牌响应模型"""
    
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")


class TokenPayload(BaseModel):
    """令牌 payload 模型"""
    
    sub: Optional[str] = Field(None, description="用户ID")
    username: Optional[str] = Field(None, description="用户名")
    email: Optional[str] = Field(None, description="邮箱")
    is_superuser: Optional[bool] = Field(False, description="是否超级用户")


class UserLogin(BaseModel):
    """用户登录请求模型"""
    
    username: str = Field(..., description="用户名", min_length=3, max_length=50)
    password: str = Field(..., description="密码", min_length=8, max_length=100)


class UserRegister(BaseModel):
    """用户注册请求模型"""
    
    username: str = Field(..., description="用户名", min_length=3, max_length=50)
    email: Optional[EmailStr] = Field(None, description="邮箱地址")
    password: str = Field(..., description="密码", min_length=8, max_length=100)
    confirm_password: str = Field(..., description="确认密码", min_length=8, max_length=100)


class UserResponse(BaseModel):
    """用户响应模型"""
    
    id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: Optional[str] = Field(None, description="邮箱地址")
    is_active: bool = Field(..., description="是否激活")
    is_superuser: bool = Field(..., description="是否超级用户")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")


class UserUpdate(BaseModel):
    """用户更新模型"""
    
    email: Optional[EmailStr] = Field(None, description="邮箱地址")
    password: Optional[str] = Field(None, description="新密码", min_length=8, max_length=100)
    current_password: Optional[str] = Field(None, description="当前密码（修改密码时需要）")


class PasswordResetRequest(BaseModel):
    """密码重置请求模型"""
    
    email: EmailStr = Field(..., description="邮箱地址")


class PasswordResetConfirm(BaseModel):
    """密码重置确认模型"""
    
    token: str = Field(..., description="重置令牌")
    new_password: str = Field(..., description="新密码", min_length=8, max_length=100)


class LogoutRequest(BaseModel):
    """登出请求模型"""
    
    token: Optional[str] = Field(None, description="要撤销的令牌（为空则撤销当前令牌）")