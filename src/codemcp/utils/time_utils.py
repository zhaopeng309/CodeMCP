"""
时间处理工具模块

提供时间格式化、解析和计算功能。
"""

import time
import datetime
from typing import Optional, Union
from dateutil import parser as date_parser


def format_timestamp(
    timestamp: Optional[Union[float, int, datetime.datetime]] = None,
    format_str: str = "%Y-%m-%d %H:%M:%S"
) -> str:
    """
    格式化时间戳为字符串
    
    Args:
        timestamp: 时间戳（秒），datetime对象，或None（使用当前时间）
        format_str: 格式化字符串
        
    Returns:
        格式化后的时间字符串
    """
    if timestamp is None:
        dt = datetime.datetime.now()
    elif isinstance(timestamp, (float, int)):
        dt = datetime.datetime.fromtimestamp(timestamp)
    elif isinstance(timestamp, datetime.datetime):
        dt = timestamp
    else:
        raise ValueError(f"不支持的时间戳类型: {type(timestamp)}")
    
    return dt.strftime(format_str)


def parse_duration(duration_str: str) -> float:
    """
    解析持续时间字符串为秒数
    
    支持格式:
    - "1h30m15s" -> 1小时30分钟15秒
    - "45m" -> 45分钟
    - "2h" -> 2小时
    - "90s" -> 90秒
    
    Args:
        duration_str: 持续时间字符串
        
    Returns:
        秒数
    """
    import re
    
    # 正则表达式匹配时间单位
    pattern = r"(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?"
    match = re.match(pattern, duration_str)
    
    if not match:
        raise ValueError(f"无效的持续时间格式: {duration_str}")
    
    hours = match.group(1)
    minutes = match.group(2)
    seconds = match.group(3)
    
    total_seconds = 0
    if hours:
        total_seconds += int(hours) * 3600
    if minutes:
        total_seconds += int(minutes) * 60
    if seconds:
        total_seconds += int(seconds)
    
    return total_seconds


def human_readable_duration(seconds: float) -> str:
    """
    将秒数转换为人类可读的持续时间
    
    Args:
        seconds: 秒数
        
    Returns:
        人类可读的持续时间字符串
    """
    if seconds < 0:
        return "0秒"
    
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days}天")
    if hours > 0:
        parts.append(f"{hours}小时")
    if minutes > 0:
        parts.append(f"{minutes}分钟")
    if secs > 0 or not parts:
        parts.append(f"{secs}秒")
    
    return "".join(parts)


def parse_datetime(datetime_str: str) -> datetime.datetime:
    """
    解析日期时间字符串
    
    Args:
        datetime_str: 日期时间字符串
        
    Returns:
        datetime对象
    """
    try:
        return date_parser.parse(datetime_str)
    except Exception as e:
        raise ValueError(f"无法解析日期时间字符串 '{datetime_str}': {e}")


def get_elapsed_time(start_time: float, end_time: Optional[float] = None) -> str:
    """
    计算经过的时间
    
    Args:
        start_time: 开始时间戳（秒）
        end_time: 结束时间戳（秒），None表示当前时间
        
    Returns:
        经过的时间字符串
    """
    if end_time is None:
        end_time = time.time()
    
    elapsed = end_time - start_time
    return human_readable_duration(elapsed)


def is_within_time_window(
    timestamp: Union[float, datetime.datetime],
    window_hours: int = 24
) -> bool:
    """
    检查时间戳是否在指定时间窗口内
    
    Args:
        timestamp: 时间戳
        window_hours: 时间窗口（小时）
        
    Returns:
        是否在时间窗口内
    """
    if isinstance(timestamp, datetime.datetime):
        timestamp = timestamp.timestamp()
    
    current_time = time.time()
    window_seconds = window_hours * 3600
    
    return current_time - timestamp <= window_seconds


def format_relative_time(timestamp: Union[float, datetime.datetime]) -> str:
    """
    格式化相对时间（例如："2小时前"）
    
    Args:
        timestamp: 时间戳
        
    Returns:
        相对时间字符串
    """
    if isinstance(timestamp, datetime.datetime):
        timestamp = timestamp.timestamp()
    
    current_time = time.time()
    diff_seconds = current_time - timestamp
    
    if diff_seconds < 0:
        return "未来"
    elif diff_seconds < 60:
        return "刚刚"
    elif diff_seconds < 3600:
        minutes = int(diff_seconds // 60)
        return f"{minutes}分钟前"
    elif diff_seconds < 86400:
        hours = int(diff_seconds // 3600)
        return f"{hours}小时前"
    elif diff_seconds < 2592000:  # 30天
        days = int(diff_seconds // 86400)
        return f"{days}天前"
    elif diff_seconds < 31536000:  # 365天
        months = int(diff_seconds // 2592000)
        return f"{months}个月前"
    else:
        years = int(diff_seconds // 31536000)
        return f"{years}年前"