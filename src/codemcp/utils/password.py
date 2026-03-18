"""
密码工具模块

密码哈希和验证功能。
"""

from passlib.context import CryptContext

# 创建密码上下文，使用 bcrypt 算法
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码
    
    Args:
        plain_password: 明文密码
        hashed_password: 哈希后的密码
        
    Returns:
        bool: 密码是否匹配
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """获取密码的哈希值
    
    Args:
        password: 明文密码
        
    Returns:
        str: 哈希后的密码
    """
    return pwd_context.hash(password)


def is_password_strong(password: str) -> bool:
    """检查密码强度
    
    Args:
        password: 密码
        
    Returns:
        bool: 密码是否足够强
    """
    # 基本密码强度检查
    if len(password) < 8:
        return False
    
    # 检查是否包含数字
    if not any(char.isdigit() for char in password):
        return False
    
    # 检查是否包含字母
    if not any(char.isalpha() for char in password):
        return False
    
    return True