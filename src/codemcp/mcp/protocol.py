"""
MCP 协议实现

Model Context Protocol 协议消息定义和解析。
"""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4


class MessageType(str, Enum):
    """MCP 消息类型枚举"""
    # 通用消息
    PING = "ping"
    PONG = "pong"
    ERROR = "error"

    # 规划器消息
    PLAN_CREATE = "plan/create"
    PLAN_UPDATE = "plan/update"
    PLAN_STATUS = "plan/status"

    # 执行器消息
    TASK_FETCH = "task/fetch"
    TASK_RESULT = "task/result"
    TASK_STATUS = "task/status"

    # 系统消息
    SYSTEM_STATUS = "system/status"
    SYSTEM_CONFIG = "system/config"


class MessagePriority(str, Enum):
    """消息优先级枚举"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class BaseMessage:
    """基础消息类"""

    message_id: str = field(default_factory=lambda: str(uuid4()))
    message_type: MessageType = MessageType.PING
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: datetime = field(default_factory=datetime.now)
    source: Optional[str] = None
    destination: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "message_id": self.message_id,
            "message_type": self.message_type.value,
            "priority": self.priority.value,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "destination": self.destination,
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseMessage":
        """从字典创建消息"""
        return cls(
            message_id=data.get("message_id", str(uuid4())),
            message_type=MessageType(data.get("message_type", MessageType.PING.value)),
            priority=MessagePriority(data.get("priority", MessagePriority.NORMAL.value)),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())),
            source=data.get("source"),
            destination=data.get("destination"),
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "BaseMessage":
        """从 JSON 字符串创建消息"""
        data = json.loads(json_str)
        return cls.from_dict(data)


@dataclass
class PlanCreateMessage(BaseMessage):
    """创建计划消息"""

    system_id: Optional[str] = None
    description: Optional[str] = None
    plan_data: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        self.message_type = MessageType.PLAN_CREATE

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        base_dict = super().to_dict()
        base_dict.update({
            "system_id": self.system_id,
            "description": self.description,
            "plan_data": self.plan_data,
        })
        return base_dict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlanCreateMessage":
        """从字典创建消息

        支持两种格式：
        1. 直接包含system_id、description、plan_data字段
        2. 包含在data字段中的嵌套格式（兼容旧版）
        """
        # 检查是否有嵌套的data字段
        if "data" in data and isinstance(data["data"], dict):
            nested_data = data["data"]
            # 从嵌套数据中提取字段
            system_id = nested_data.get("system_name") or nested_data.get("system_id")
            description = nested_data.get("description", "")
            plan_data = nested_data.get("plan_data") or nested_data
        else:
            # 直接使用顶层字段
            system_id = data.get("system_id")
            description = data.get("description", "")
            plan_data = data.get("plan_data", {})

        # 调用基类from_dict，然后创建PlanCreateMessage实例
        base_message = super().from_dict(data)

        return cls(
            message_id=base_message.message_id,
            message_type=base_message.message_type,
            priority=base_message.priority,
            timestamp=base_message.timestamp,
            source=base_message.source,
            destination=base_message.destination,
            metadata=base_message.metadata,
            system_id=system_id,
            description=description,
            plan_data=plan_data,
        )


@dataclass
class TaskFetchMessage(BaseMessage):
    """获取任务消息"""

    executor_id: Optional[str] = None
    capabilities: Optional[List[str]] = None
    max_tasks: int = 1

    def __post_init__(self):
        self.message_type = MessageType.TASK_FETCH

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        base_dict = super().to_dict()
        base_dict.update({
            "executor_id": self.executor_id,
            "capabilities": self.capabilities,
            "max_tasks": self.max_tasks,
        })
        return base_dict


@dataclass
class TaskResultMessage(BaseMessage):
    """任务结果消息"""

    task_id: Optional[str] = None
    exit_code: Optional[int] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    duration: Optional[float] = None
    success: bool = False
    error_message: Optional[str] = None

    def __post_init__(self):
        self.message_type = MessageType.TASK_RESULT

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        base_dict = super().to_dict()
        base_dict.update({
            "task_id": self.task_id,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration": self.duration,
            "success": self.success,
            "error_message": self.error_message,
        })
        return base_dict


@dataclass
class ErrorMessage(BaseMessage):
    """错误消息"""

    error_code: Optional[str] = None
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        self.message_type = MessageType.ERROR

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        base_dict = super().to_dict()
        base_dict.update({
            "error_code": self.error_code,
            "error_message": self.error_message,
            "details": self.details,
        })
        return base_dict


class MCPProtocol(ABC):
    """MCP 协议处理器抽象基类"""

    @abstractmethod
    async def handle_message(self, message: BaseMessage) -> BaseMessage:
        """处理消息

        Args:
            message: 接收到的消息

        Returns:
            响应消息
        """
        pass

    @abstractmethod
    async def validate_message(self, message: BaseMessage) -> bool:
        """验证消息

        Args:
            message: 待验证的消息

        Returns:
            是否有效
        """
        pass

    @abstractmethod
    async def create_response(self, request: BaseMessage, **kwargs) -> BaseMessage:
        """创建响应消息

        Args:
            request: 请求消息
            **kwargs: 响应参数

        Returns:
            响应消息
        """
        pass


class SimpleMCPProtocol(MCPProtocol):
    """简单 MCP 协议处理器"""

    async def handle_message(self, message: BaseMessage) -> BaseMessage:
        """处理消息"""
        # 根据消息类型路由到不同的处理方法
        handlers = {
            MessageType.PLAN_CREATE: self._handle_plan_create,
            MessageType.PLAN_UPDATE: self._handle_plan_update,
            MessageType.PLAN_STATUS: self._handle_plan_status,
            MessageType.TASK_FETCH: self._handle_task_fetch,
            MessageType.TASK_RESULT: self._handle_task_result,
            MessageType.PING: self._handle_ping,
        }

        handler = handlers.get(message.message_type)
        if handler:
            return await handler(message)
        else:
            return await self._handle_unknown_message(message)

    async def validate_message(self, message: BaseMessage) -> bool:
        """验证消息"""
        # 基础验证
        if not message.message_id:
            return False
        if not isinstance(message.message_type, MessageType):
            return False
        if message.timestamp > datetime.now():
            return False  # 未来时间戳无效

        return True

    async def create_response(self, request: BaseMessage, **kwargs) -> BaseMessage:
        """创建响应消息"""
        response = BaseMessage(
            message_type=MessageType.PONG if request.message_type == MessageType.PING else request.message_type,
            source=request.destination,
            destination=request.source,
            metadata={"in_response_to": request.message_id},
        )
        response.metadata.update(kwargs)
        return response

    async def _handle_ping(self, message: BaseMessage) -> BaseMessage:
        """处理 Ping 消息"""
        return await self.create_response(message, status="pong")

    async def _handle_plan_update(self, message: BaseMessage) -> BaseMessage:
        """处理计划更新消息"""
        return await self.create_response(
            message,
            status="received",
            message="计划更新请求已接收",
        )

    async def _handle_plan_status(self, message: BaseMessage) -> BaseMessage:
        """处理计划状态查询消息"""
        plan_id = message.metadata.get("plan_id", "unknown")
        return await self.create_response(
            message,
            status="mock_status",
            plan_id=plan_id,
            status_value="in_progress",
            completion_rate=0.5,
            message=f"计划 {plan_id} 状态查询已接收",
        )

    async def _handle_plan_create(self, message: BaseMessage) -> BaseMessage:
        """处理计划创建消息"""
        return await self.create_response(
            message,
            status="received",
            message="计划创建请求已接收",
        )

    async def _handle_task_fetch(self, message: BaseMessage) -> BaseMessage:
        """处理任务获取消息"""
        return await self.create_response(
            message,
            status="no_tasks",
            message="暂无可用任务",
        )

    async def _handle_task_result(self, message: BaseMessage) -> BaseMessage:
        """处理任务结果消息"""
        return await self.create_response(
            message,
            status="received",
            message="任务结果已接收",
        )

    async def _handle_unknown_message(self, message: BaseMessage) -> BaseMessage:
        """处理未知消息"""
        return ErrorMessage(
            error_code="UNKNOWN_MESSAGE_TYPE",
            error_message=f"未知的消息类型: {message.message_type}",
            source=message.destination,
            destination=message.source,
            metadata={"original_message_id": message.message_id},
        )