"""
日志工具模块

提供统一的日志配置和管理功能。
"""

import logging
import sys
from typing import Optional, Dict, Any
from pathlib import Path

from ..config import settings


def setup_logging(
    name: str = "codemcp",
    level: Optional[str] = None,
    log_file: Optional[str] = None,
    log_format: Optional[str] = None,
) -> logging.Logger:
    """
    配置并返回日志记录器
    
    Args:
        name: 日志记录器名称
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日志文件路径
        log_format: 日志格式 (json, text)
        
    Returns:
        配置好的日志记录器
    """
    # 使用配置中的默认值
    if level is None:
        level = settings.log_level
    if log_file is None:
        log_file = settings.log_file
    if log_format is None:
        log_format = settings.log_format
    
    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # 清除现有的处理器
    logger.handlers.clear()
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    
    # 设置日志格式
    if log_format == "json":
        try:
            import json
            from pythonjsonlogger import jsonlogger
            
            class CustomJsonFormatter(jsonlogger.JsonFormatter):
                def add_fields(self, log_record, record, message_dict):
                    super().add_fields(log_record, record, message_dict)
                    log_record["timestamp"] = record.created
                    log_record["level"] = record.levelname
                    log_record["logger"] = record.name
                    log_record["module"] = record.module
                    log_record["function"] = record.funcName
                    log_record["line"] = record.lineno
            
            formatter = CustomJsonFormatter(
                "%(timestamp)s %(level)s %(logger)s %(module)s %(function)s %(line)s %(message)s"
            )
        except ImportError:
            # 如果 pythonjsonlogger 不可用，回退到文本格式
            logging.warning("pythonjsonlogger not installed, falling back to text format")
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 如果指定了日志文件，添加文件处理器
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = "codemcp") -> logging.Logger:
    """
    获取或创建日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        日志记录器实例
    """
    logger = logging.getLogger(name)
    
    # 如果记录器还没有处理器，则进行配置
    if not logger.handlers:
        setup_logging(name)
    
    return logger


class LoggingMixin:
    """提供日志功能的混入类"""
    
    @property
    def logger(self) -> logging.Logger:
        """获取类特定的日志记录器"""
        if not hasattr(self, "_logger"):
            class_name = self.__class__.__name__
            self._logger = get_logger(f"codemcp.{class_name}")
        return self._logger
    
    def log_debug(self, message: str, **kwargs):
        """记录调试信息"""
        self.logger.debug(message, extra=kwargs)
    
    def log_info(self, message: str, **kwargs):
        """记录信息"""
        self.logger.info(message, extra=kwargs)
    
    def log_warning(self, message: str, **kwargs):
        """记录警告"""
        self.logger.warning(message, extra=kwargs)
    
    def log_error(self, message: str, **kwargs):
        """记录错误"""
        self.logger.error(message, extra=kwargs)
    
    def log_exception(self, message: str, exc_info: bool = True, **kwargs):
        """记录异常"""
        self.logger.exception(message, exc_info=exc_info, extra=kwargs)