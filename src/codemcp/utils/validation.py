"""
数据验证工具模块

提供数据验证和清理功能。
"""

import re
import uuid
from typing import Dict, Any, Optional, List, Tuple
from urllib.parse import urlparse


def validate_task_data(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    验证任务数据
    
    Args:
        data: 任务数据字典
        
    Returns:
        (是否有效, 错误信息)
    """
    required_fields = ["command", "feature_id"]
    
    # 检查必填字段
    for field in required_fields:
        if field not in data:
            return False, f"缺少必填字段: {field}"
    
    # 验证命令
    command = data.get("command", "")
    if not command or not isinstance(command, str):
        return False, "命令必须是非空字符串"
    
    # 验证功能点ID
    feature_id = data.get("feature_id", "")
    if not feature_id or not isinstance(feature_id, str):
        return False, "功能点ID必须是有效字符串"
    
    # 验证最大重试次数
    max_retries = data.get("max_retries", 3)
    if not isinstance(max_retries, int) or max_retries < 0 or max_retries > 10:
        return False, "最大重试次数必须是0-10之间的整数"
    
    # 验证超时时间
    timeout = data.get("timeout", 3600)
    if not isinstance(timeout, (int, float)) or timeout <= 0:
        return False, "超时时间必须是正数"
    
    # 验证优先级
    priority = data.get("priority", 0)
    if not isinstance(priority, int):
        return False, "优先级必须是整数"
    
    return True, None


def validate_feature_data(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    验证功能点数据
    
    Args:
        data: 功能点数据字典
        
    Returns:
        (是否有效, 错误信息)
    """
    required_fields = ["name", "system_id"]
    
    # 检查必填字段
    for field in required_fields:
        if field not in data:
            return False, f"缺少必填字段: {field}"
    
    # 验证名称
    name = data.get("name", "")
    if not name or not isinstance(name, str) or len(name) > 200:
        return False, "名称必须是1-200个字符的字符串"
    
    # 验证系统ID
    system_id = data.get("system_id", "")
    if not system_id or not isinstance(system_id, str):
        return False, "系统ID必须是有效字符串"
    
    # 验证描述
    description = data.get("description", "")
    if description and not isinstance(description, str):
        return False, "描述必须是字符串"
    
    # 验证测试命令模板
    test_command_template = data.get("test_command_template", "")
    if test_command_template and not isinstance(test_command_template, str):
        return False, "测试命令模板必须是字符串"
    
    return True, None


def validate_system_data(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    验证系统数据
    
    Args:
        data: 系统数据字典
        
    Returns:
        (是否有效, 错误信息)
    """
    required_fields = ["name"]
    
    # 检查必填字段
    for field in required_fields:
        if field not in data:
            return False, f"缺少必填字段: {field}"
    
    # 验证名称
    name = data.get("name", "")
    if not name or not isinstance(name, str) or len(name) > 100:
        return False, "名称必须是1-100个字符的字符串"
    
    # 验证描述
    description = data.get("description", "")
    if description and not isinstance(description, str):
        return False, "描述必须是字符串"
    
    # 验证仓库URL
    repo_url = data.get("repo_url", "")
    if repo_url:
        if not isinstance(repo_url, str):
            return False, "仓库URL必须是字符串"
        
        # 基本URL验证
        try:
            result = urlparse(repo_url)
            if not all([result.scheme, result.netloc]):
                return False, "仓库URL格式无效"
        except:
            return False, "仓库URL格式无效"
    
    return True, None


def validate_uuid(uuid_str: str) -> bool:
    """
    验证UUID字符串
    
    Args:
        uuid_str: UUID字符串
        
    Returns:
        是否有效
    """
    try:
        uuid.UUID(uuid_str)
        return True
    except (ValueError, AttributeError):
        return False


def validate_email(email: str) -> bool:
    """
    验证电子邮件地址
    
    Args:
        email: 电子邮件地址
        
    Returns:
        是否有效
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_url(url: str) -> bool:
    """
    验证URL
    
    Args:
        url: URL字符串
        
    Returns:
        是否有效
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


def sanitize_string(input_str: str, max_length: int = 1000) -> str:
    """
    清理字符串，移除危险字符并限制长度
    
    Args:
        input_str: 输入字符串
        max_length: 最大长度
        
    Returns:
        清理后的字符串
    """
    if not input_str:
        return ""
    
    # 移除控制字符
    cleaned = re.sub(r'[\x00-\x1F\x7F]', '', input_str)
    
    # 限制长度
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    
    return cleaned


def validate_and_sanitize_command(command: str) -> Tuple[bool, Optional[str], str]:
    """
    验证并清理命令字符串
    
    Args:
        command: 命令字符串
        
    Returns:
        (是否有效, 错误信息, 清理后的命令)
    """
    if not command or not isinstance(command, str):
        return False, "命令必须是非空字符串", ""
    
    # 清理命令
    sanitized = sanitize_string(command, max_length=5000)
    
    # 检查危险命令模式
    dangerous_patterns = [
        r'rm\s+-rf',
        r':\(\)\{:\|:&\};:',
        r'mkfs',
        r'dd\s+if=/dev/',
        r'>/dev/sd',
        r'chmod\s+[0-7]{3,4}\s+',
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, sanitized, re.IGNORECASE):
            return False, f"命令包含危险模式: {pattern}", sanitized
    
    return True, None, sanitized


def validate_pagination_params(
    page: int,
    page_size: int,
    max_page_size: int = 100
) -> Tuple[bool, Optional[str]]:
    """
    验证分页参数
    
    Args:
        page: 页码
        page_size: 每页大小
        max_page_size: 最大每页大小
        
    Returns:
        (是否有效, 错误信息)
    """
    if not isinstance(page, int) or page < 1:
        return False, "页码必须是大于0的整数"
    
    if not isinstance(page_size, int) or page_size < 1 or page_size > max_page_size:
        return False, f"每页大小必须是1-{max_page_size}之间的整数"
    
    return True, None