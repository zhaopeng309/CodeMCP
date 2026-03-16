"""
Executor 客户端

与外部 Executor 通信的 MCP 客户端。
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from uuid import uuid4

from ..exceptions import MCPProtocolError
from ..models.test import TestModel, TestStatus
from .protocol import (
    BaseMessage,
    ErrorMessage,
    MessagePriority,
    MessageType,
    SimpleMCPProtocol,
    TaskFetchMessage,
    TaskResultMessage,
)


class ExecutorClient:
    """Executor 客户端"""

    def __init__(
        self,
        server_url: str = "mcp://localhost:8000",
        client_id: Optional[str] = None,
        capabilities: Optional[List[str]] = None,
    ):
        """初始化 Executor 客户端

        Args:
            server_url: MCP 服务器 URL
            client_id: 客户端标识，如果为 None 则自动生成
            capabilities: 执行器能力列表
        """
        self.server_url = server_url
        self.client_id = client_id or f"executor-{uuid4().hex[:8]}"
        self.capabilities = capabilities or ["python", "pytest", "shell"]
        self.protocol = SimpleMCPProtocol()
        self.logger = logging.getLogger(f"codemcp.mcp.executor.{self.client_id}")
        self._connected = False

    async def connect(self) -> bool:
        """连接到 MCP 服务器

        Returns:
            是否连接成功
        """
        try:
            self.logger.info(f"连接到 MCP 服务器: {self.server_url}")
            self.logger.info(f"执行器能力: {self.capabilities}")
            # 模拟连接过程
            await asyncio.sleep(0.1)
            self._connected = True
            self.logger.info("连接成功")
            return True
        except Exception as e:
            self.logger.error(f"连接失败: {e}")
            return False

    async def disconnect(self) -> None:
        """断开连接"""
        if self._connected:
            self.logger.info("断开 MCP 服务器连接")
            self._connected = False

    async def fetch_tasks(
        self,
        max_tasks: int = 1,
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> List[Dict[str, Any]]:
        """获取待执行任务

        Args:
            max_tasks: 最大任务数
            priority: 消息优先级

        Returns:
            任务列表

        Raises:
            MCPProtocolError: MCP 协议错误
        """
        if not self._connected:
            raise MCPProtocolError("客户端未连接")

        try:
            # 创建消息
            message = TaskFetchMessage(
                source=self.client_id,
                destination="codemcp/gateway",
                priority=priority,
                executor_id=self.client_id,
                capabilities=self.capabilities,
                max_tasks=max_tasks,
            )

            # 发送消息（模拟）
            self.logger.info(f"获取任务 (max={max_tasks})")
            response = await self._send_message(message)

            # 处理响应
            if isinstance(response, ErrorMessage):
                raise MCPProtocolError(
                    f"获取任务失败: {response.error_message}",
                    error_code=response.error_code,
                )

            # 模拟返回任务数据
            tasks = response.metadata.get("tasks", [])
            if not tasks:
                self.logger.info("暂无可用任务")
                return []

            self.logger.info(f"获取到 {len(tasks)} 个任务")
            return tasks

        except Exception as e:
            self.logger.error(f"获取任务时出错: {e}")
            raise MCPProtocolError(f"获取任务失败: {e}")

    async def submit_task_result(
        self,
        task_id: str,
        exit_code: int,
        stdout: str,
        stderr: str,
        duration: float,
        success: bool,
        error_message: Optional[str] = None,
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> Dict[str, Any]:
        """提交任务执行结果

        Args:
            task_id: 任务 ID
            exit_code: 退出码
            stdout: 标准输出
            stderr: 标准错误
            duration: 执行时长（秒）
            success: 是否成功
            error_message: 错误信息
            priority: 消息优先级

        Returns:
            提交结果

        Raises:
            MCPProtocolError: MCP 协议错误
        """
        if not self._connected:
            raise MCPProtocolError("客户端未连接")

        try:
            # 创建消息
            message = TaskResultMessage(
                source=self.client_id,
                destination="codemcp/gateway",
                priority=priority,
                task_id=task_id,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                duration=duration,
                success=success,
                error_message=error_message,
            )

            # 发送消息（模拟）
            self.logger.info(f"提交任务结果: {task_id} (success={success})")
            response = await self._send_message(message)

            # 处理响应
            if isinstance(response, ErrorMessage):
                raise MCPProtocolError(
                    f"提交任务结果失败: {response.error_message}",
                    error_code=response.error_code,
                )

            return {
                "success": True,
                "task_id": task_id,
                "response": response.metadata,
            }

        except Exception as e:
            self.logger.error(f"提交任务结果时出错: {e}")
            raise MCPProtocolError(f"提交任务结果失败: {e}")

    async def get_task_status(
        self,
        task_id: str,
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> Dict[str, Any]:
        """获取任务状态

        Args:
            task_id: 任务 ID
            priority: 消息优先级

        Returns:
            任务状态

        Raises:
            MCPProtocolError: MCP 协议错误
        """
        if not self._connected:
            raise MCPProtocolError("客户端未连接")

        try:
            # 创建消息
            message = BaseMessage(
                message_type=MessageType.TASK_STATUS,
                source=self.client_id,
                destination="codemcp/gateway",
                priority=priority,
                metadata={"task_id": task_id},
            )

            # 发送消息（模拟）
            self.logger.info(f"获取任务状态: {task_id}")
            response = await self._send_message(message)

            # 处理响应
            if isinstance(response, ErrorMessage):
                raise MCPProtocolError(
                    f"获取任务状态失败: {response.error_message}",
                    error_code=response.error_code,
                )

            return {
                "success": True,
                "task_id": task_id,
                "status": response.metadata.get("status", "unknown"),
                "details": response.metadata,
            }

        except Exception as e:
            self.logger.error(f"获取任务状态时出错: {e}")
            raise MCPProtocolError(f"获取任务状态失败: {e}")

    async def ping(self) -> Dict[str, Any]:
        """发送 Ping 消息测试连接

        Returns:
            Ping 结果
        """
        try:
            message = BaseMessage(
                message_type=MessageType.PING,
                source=self.client_id,
                destination="codemcp/gateway",
                priority=MessagePriority.LOW,
            )

            response = await self._send_message(message)
            return {
                "success": True,
                "latency": "模拟 0.1s",
                "response": response.metadata,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    async def execute_and_report(
        self,
        task: Dict[str, Any],
    ) -> Dict[str, Any]:
        """执行任务并自动报告结果

        Args:
            task: 任务数据

        Returns:
            执行结果
        """
        task_id = task.get("id")
        command = task.get("command")

        if not task_id or not command:
            return {
                "success": False,
                "error": "任务数据不完整",
            }

        self.logger.info(f"开始执行任务 {task_id}: {command}")

        try:
            # 模拟任务执行
            await asyncio.sleep(0.5)  # 模拟执行时间

            # 模拟执行结果（成功或失败）
            import random
            success = random.random() > 0.3  # 70% 成功率

            if success:
                exit_code = 0
                stdout = f"任务执行成功: {command}"
                stderr = ""
                error_message = None
            else:
                exit_code = 1
                stdout = ""
                stderr = f"模拟错误: 任务执行失败"
                error_message = "模拟执行错误"

            duration = 0.5

            # 提交结果
            result = await self.submit_task_result(
                task_id=task_id,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                duration=duration,
                success=success,
                error_message=error_message,
            )

            return {
                "success": True,
                "task_id": task_id,
                "execution_success": success,
                "result": result,
            }

        except Exception as e:
            self.logger.error(f"执行任务时出错: {e}")
            return {
                "success": False,
                "task_id": task_id,
                "error": str(e),
            }

    async def _send_message(self, message: BaseMessage) -> BaseMessage:
        """发送消息（模拟实现）

        实际项目中需要实现真正的网络通信

        Args:
            message: 要发送的消息

        Returns:
            响应消息
        """
        # 模拟网络延迟
        await asyncio.sleep(0.1)

        # 验证消息
        if not await self.protocol.validate_message(message):
            return ErrorMessage(
                error_code="INVALID_MESSAGE",
                error_message="消息验证失败",
                source=message.destination,
                destination=message.source,
            )

        # 处理消息（模拟服务器处理）
        response = await self.protocol.handle_message(message)
        return response

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.disconnect()