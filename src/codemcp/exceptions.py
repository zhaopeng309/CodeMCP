"""
CodeMCP 自定义异常

项目特定的异常类型定义。
"""

from typing import Optional


class CodeMCPError(Exception):
    """CodeMCP 基础异常"""
    pass


class ConfigurationError(CodeMCPError):
    """配置错误"""
    pass


class DatabaseError(CodeMCPError):
    """数据库错误"""
    pass


class StateTransitionError(CodeMCPError):
    """状态流转错误"""
    pass


class TaskError(CodeMCPError):
    """任务执行错误"""
    pass


class TaskWindowFullError(TaskError):
    """任务窗口已满错误"""
    pass


class TaskNotFoundError(TaskError):
    """任务未找到错误"""
    pass


class MCPProtocolError(CodeMCPError):
    """MCP 协议错误"""

    def __init__(self, message: str, error_code: Optional[str] = None):
        super().__init__(message)
        self.error_code = error_code

    def __str__(self) -> str:
        if self.error_code:
            return f"{self.error_code}: {super().__str__()}"
        return super().__str__()


class ValidationError(CodeMCPError):
    """数据验证错误"""
    pass


class AuthenticationError(CodeMCPError):
    """认证错误"""
    pass


class AuthorizationError(CodeMCPError):
    """授权错误"""
    pass


class RateLimitError(CodeMCPError):
    """速率限制错误"""
    pass


class RetryExhaustedError(TaskError):
    """重试次数用尽错误"""
    pass