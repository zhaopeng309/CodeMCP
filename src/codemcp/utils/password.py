"""
密码工具模块

密码哈希和验证功能。
简化版本，避免 bcrypt 和 passlib 的兼容性问题。
"""

import hashlib

# 直接使用 bcrypt 库，避免 passlib 的 __about__ 属性错误
import bcrypt


def _ensure_password_length(password: str) -> bytes:
    """确保密码字节长度不超过 72 字节（bcrypt 限制）
    
    Args:
        password: 密码字符串
        
    Returns:
        bytes: 处理后的密码字节
    """
    password_bytes = password.encode('utf-8')
    
    # bcrypt 限制为 72 字节
    if len(password_bytes) <= 72:
        return password_bytes
    
    # 对于超过 72 字节的密码，使用 SHA-256 哈希
    # 这样可以在保持安全性的同时避免截断
    hash_obj = hashlib.sha256(password_bytes)
    # 使用十六进制表示（64个字符）
    hashed_hex = hash_obj.hexdigest()
    # 返回字节
    return hashed_hex.encode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码
    
    Args:
        plain_password: 明文密码
        hashed_password: 哈希后的密码
        
    Returns:
        bool: 密码是否匹配
    """
    if not plain_password or not hashed_password:
        return False
    
    try:
        # 处理密码长度限制
        password_bytes = _ensure_password_length(plain_password)
        
        # 确保 hashed_password 是字节
        if isinstance(hashed_password, str):
            hashed_password_bytes = hashed_password.encode('utf-8')
        else:
            hashed_password_bytes = hashed_password
        
        return bcrypt.checkpw(password_bytes, hashed_password_bytes)
    except Exception as e:
        # 如果验证失败，尝试简单的截断
        try:
            # 简单截断到 72 字节
            password_bytes = plain_password.encode('utf-8')[:72]
            if isinstance(hashed_password, str):
                hashed_password_bytes = hashed_password.encode('utf-8')
            else:
                hashed_password_bytes = hashed_password
            return bcrypt.checkpw(password_bytes, hashed_password_bytes)
        except Exception:
            return False


def get_password_hash(password: str) -> str:
    """获取密码的哈希值
    
    Args:
        password: 明文密码
        
    Returns:
        str: 哈希后的密码
    """
    if not password:
        raise ValueError("Password cannot be empty")
    
    # 处理密码长度限制
    password_bytes = _ensure_password_length(password)
    
    # 生成 salt 和哈希
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


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