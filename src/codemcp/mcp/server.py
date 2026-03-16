"""
MCP 协议服务器

处理 Planner 和 Executor 请求的 MCP 协议服务器端点。
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Optional, cast

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.task_engine import TaskEngine
from ..core.executor import LocalCommandExecutor
from ..database.session import get_db_session
from ..models.test import TestModel, TestStatus
from .protocol import (
    BaseMessage,
    ErrorMessage,
    MessageType,
    PlanCreateMessage,
    TaskFetchMessage,
    TaskResultMessage,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mcp", tags=["mcp"])


class MCPServer:
    """MCP 协议服务器"""

    def __init__(self, task_engine: Optional[TaskEngine] = None):
        """初始化 MCP 服务器

        Args:
            task_engine: 任务引擎实例
        """
        self.task_engine = task_engine or TaskEngine(
            executor=LocalCommandExecutor(),
            window_size=5,
            max_retries=3,
        )
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_types: Dict[str, str] = {}  # "planner" 或 "executor"

    async def connect(self, websocket: WebSocket, client_type: str, client_id: str):
        """连接客户端

        Args:
            websocket: WebSocket 连接
            client_type: 客户端类型 ("planner" 或 "executor")
            client_id: 客户端 ID
        """
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.connection_types[client_id] = client_type
        logger.info(f"客户端 {client_id} ({client_type}) 已连接")

    async def disconnect(self, client_id: str):
        """断开客户端连接

        Args:
            client_id: 客户端 ID
        """
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            del self.connection_types[client_id]
            logger.info(f"客户端 {client_id} 已断开连接")

    async def send_message(self, client_id: str, message: BaseMessage):
        """向客户端发送消息

        Args:
            client_id: 客户端 ID
            message: 要发送的消息
        """
        if client_id not in self.active_connections:
            logger.warning(f"客户端 {client_id} 未连接，无法发送消息")
            return

        try:
            await self.active_connections[client_id].send_text(message.to_json())
            logger.debug(f"向客户端 {client_id} 发送消息: {message.message_type}")
        except Exception as e:
            logger.error(f"向客户端 {client_id} 发送消息失败: {e}")

    async def broadcast(self, message: BaseMessage, client_type: Optional[str] = None):
        """广播消息给所有客户端或特定类型的客户端

        Args:
            message: 要广播的消息
            client_type: 客户端类型筛选 (None 表示所有客户端)
        """
        for client_id, websocket in self.active_connections.items():
            if client_type is None or self.connection_types.get(client_id) == client_type:
                try:
                    await websocket.send_text(message.to_json())
                except Exception as e:
                    logger.error(f"向客户端 {client_id} 广播消息失败: {e}")

    async def handle_planner_message(
        self,
        message: BaseMessage,
        session: AsyncSession,
    ) -> Optional[BaseMessage]:
        """处理 Planner 消息

        Args:
            message: 接收到的消息
            session: 数据库会话

        Returns:
            响应消息
        """
        if message.message_type == MessageType.PLAN_CREATE:
            plan_message = cast(PlanCreateMessage, message)
            return await self.handle_plan_create(plan_message, session)
        elif message.message_type == MessageType.PLAN_STATUS:
            return await self.handle_plan_status(message, session)
        elif message.message_type == MessageType.PING:
            return BaseMessage(
                message_type=MessageType.PONG,
                source="server",
                destination=message.source,
            )

        return ErrorMessage(
            error_message=f"不支持的消息类型: {message.message_type}",
            source="server",
            destination=message.source,
        )

    async def handle_executor_message(
        self,
        message: BaseMessage,
        session: AsyncSession,
    ) -> Optional[BaseMessage]:
        """处理 Executor 消息

        Args:
            message: 接收到的消息
            session: 数据库会话

        Returns:
            响应消息
        """
        if message.message_type == MessageType.TASK_FETCH:
            task_fetch_message = cast(TaskFetchMessage, message)
            return await self.handle_task_fetch(task_fetch_message, session)
        elif message.message_type == MessageType.TASK_RESULT:
            task_result_message = cast(TaskResultMessage, message)
            return await self.handle_task_result(task_result_message, session)
        elif message.message_type == MessageType.TASK_STATUS:
            return await self.handle_task_status(message, session)
        elif message.message_type == MessageType.PING:
            return BaseMessage(
                message_type=MessageType.PONG,
                source="server",
                destination=message.source,
            )

        return ErrorMessage(
            error_message=f"不支持的消息类型: {message.message_type}",
            source="server",
            destination=message.source,
        )

    async def handle_plan_create(
        self,
        message: PlanCreateMessage,
        session: AsyncSession,
    ) -> BaseMessage:
        """处理创建计划请求

        Args:
            message: 创建计划消息
            session: 数据库会话

        Returns:
            响应消息
        """
        try:
            # 这里应该实现创建计划的逻辑
            # 目前先返回成功响应
            logger.info(f"收到创建计划请求: {message.system_id} - {message.description}")

            return BaseMessage(
                message_type=MessageType.PLAN_STATUS,
                source="server",
                destination=message.source,
                metadata={
                    "plan_id": "generated_plan_id",
                    "status": "created",
                    "system_id": message.system_id,
                },
            )

        except Exception as e:
            logger.error(f"处理创建计划失败: {e}")
            return ErrorMessage(
                error_message=f"创建计划失败: {str(e)}",
                source="server",
                destination=message.source,
            )

    async def handle_plan_status(
        self,
        message: BaseMessage,
        session: AsyncSession,
    ) -> BaseMessage:
        """处理计划状态查询

        Args:
            message: 计划状态消息
            session: 数据库会话

        Returns:
            响应消息
        """
        plan_id = message.metadata.get("plan_id")
        logger.info(f"查询计划状态: {plan_id}")

        return BaseMessage(
            message_type=MessageType.PLAN_STATUS,
            source="server",
            destination=message.source,
            metadata={
                "plan_id": plan_id,
                "status": "active",
                "progress": 0.5,
            },
        )

    async def handle_task_fetch(
        self,
        message: TaskFetchMessage,
        session: AsyncSession,
    ) -> BaseMessage:
        """处理任务获取请求

        Args:
            message: 任务获取消息
            session: 数据库会话

        Returns:
            响应消息
        """
        try:
            # 获取待处理的任务
            # 这里应该实现任务分配逻辑
            # 目前先返回一个模拟任务
            logger.info(f"收到任务获取请求 from {message.source}")

            # 查询数据库获取待处理任务
            # 使用 SQLAlchemy ORM 查询
            stmt = select(TestModel).where(
                TestModel.status == TestStatus.PENDING
            ).order_by(TestModel.created_at).limit(1)
            
            result = await session.execute(stmt)
            test = result.scalar_one_or_none()

            if test:
                return TaskFetchMessage(
                    source="server",
                    destination=message.source,
                    metadata={
                        "task_id": str(test.id),
                        "command": test.command,
                        "priority": "normal",
                    },
                )
            else:
                # 没有待处理任务
                return BaseMessage(
                    message_type=MessageType.TASK_STATUS,
                    source="server",
                    destination=message.source,
                    metadata={
                        "status": "no_tasks",
                        "message": "没有待处理任务",
                    },
                )

        except Exception as e:
            logger.error(f"处理任务获取失败: {e}")
            return ErrorMessage(
                error_message=f"获取任务失败: {str(e)}",
                source="server",
                destination=message.source,
            )

    async def handle_task_result(
        self,
        message: TaskResultMessage,
        session: AsyncSession,
    ) -> BaseMessage:
        """处理任务结果提交

        Args:
            message: 任务结果消息
            session: 数据库会话

        Returns:
            响应消息
        """
        try:
            task_id = message.metadata.get("task_id")
            exit_code = message.metadata.get("exit_code")
            stdout = message.metadata.get("stdout", "")
            stderr = message.metadata.get("stderr", "")
            duration = message.metadata.get("duration", 0.0)

            logger.info(f"收到任务结果: {task_id}, 退出码: {exit_code}")

            # 更新数据库中的任务状态
            test = await session.get(TestModel, task_id)
            if test:
                test.exit_code = exit_code
                test.stdout = stdout
                test.stderr = stderr
                test.duration = duration
                test.finished_at = asyncio.get_event_loop().time()

                if exit_code == 0:
                    test.status = TestStatus.PASSED
                else:
                    test.status = TestStatus.FAILED

                await session.commit()
                logger.info(f"任务 {task_id} 状态已更新为 {test.status.value}")

            return BaseMessage(
                message_type=MessageType.TASK_STATUS,
                source="server",
                destination=message.source,
                metadata={
                    "task_id": task_id,
                    "status": "processed",
                    "message": "任务结果已接收并处理",
                },
            )

        except Exception as e:
            logger.error(f"处理任务结果失败: {e}")
            return ErrorMessage(
                error_message=f"处理任务结果失败: {str(e)}",
                source="server",
                destination=message.source,
            )

    async def handle_task_status(
        self,
        message: BaseMessage,
        session: AsyncSession,
    ) -> BaseMessage:
        """处理任务状态查询

        Args:
            message: 任务状态消息
            session: 数据库会话

        Returns:
            响应消息
        """
        task_id = message.metadata.get("task_id")
        logger.info(f"查询任务状态: {task_id}")

        if task_id:
            test = await session.get(TestModel, task_id)
            if test:
                return BaseMessage(
                    message_type=MessageType.TASK_STATUS,
                    source="server",
                    destination=message.source,
                    metadata={
                        "task_id": task_id,
                        "status": test.status.value,
                        "exit_code": test.exit_code,
                        "retry_count": test.retry_count,
                    },
                )

        return ErrorMessage(
            error_message=f"任务 {task_id} 不存在",
            source="server",
            destination=message.source,
        )


# 创建全局 MCP 服务器实例
mcp_server = MCPServer()


@router.websocket("/ws/{client_type}")
async def websocket_endpoint(
    websocket: WebSocket,
    client_type: str,
):
    """WebSocket 端点用于 MCP 协议通信

    简化版本，无需API密钥认证，仅验证客户端类型
    
    Args:
        websocket: WebSocket 连接
        client_type: 客户端类型 ("planner" 或 "executor")
    """
    # 验证客户端类型
    if client_type not in ["planner", "executor"]:
        await websocket.close(code=1008, reason="Invalid client type")
        return

    # 生成简单的客户端ID
    import uuid
    client_id = f"{client_type}_{uuid.uuid4().hex[:8]}"

    # 连接客户端
    await mcp_server.connect(websocket, client_type, client_id)
    logger.info(f"新客户端连接: {client_id} ({client_type})")

    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()
            
            # 解析消息
            try:
                message_dict = json.loads(data)
                message = BaseMessage.from_dict(message_dict)
            except json.JSONDecodeError as e:
                logger.error(f"消息 JSON 解析失败: {e}")
                error_msg = ErrorMessage(
                    error_message=f"消息格式错误: {str(e)}",
                    source="server",
                    destination=client_id,
                )
                await websocket.send_text(error_msg.to_json())
                continue

            # 获取数据库会话
            async for session in get_db_session():
                # 根据客户端类型处理消息
                if client_type == "planner":
                    response = await mcp_server.handle_planner_message(message, session)
                else:  # executor
                    response = await mcp_server.handle_executor_message(message, session)

                # 发送响应
                if response:
                    await websocket.send_text(response.to_json())

    except WebSocketDisconnect:
        logger.info(f"客户端 {client_id} 断开连接")
    except Exception as e:
        logger.error(f"处理客户端 {client_id} 消息时发生错误: {e}")
    finally:
        await mcp_server.disconnect(client_id)


@router.post("/planner/plan")
async def create_plan_via_http():
    """通过 HTTP 创建计划（兼容性端点）"""
    # 待实现
    raise HTTPException(
        status_code=501,
        detail="HTTP 端点尚未实现，请使用 WebSocket 接口",
    )


@router.get("/executor/tasks")
async def fetch_tasks_via_http():
    """通过 HTTP 获取任务（兼容性端点）"""
    # 待实现
    raise HTTPException(
        status_code=501,
        detail="HTTP 端点尚未实现，请使用 WebSocket 接口",
    )


@router.post("/executor/tasks/{task_id}/result")
async def submit_task_result_via_http(task_id: str):
    """通过 HTTP 提交任务结果（兼容性端点）"""
    # 待实现
    raise HTTPException(
        status_code=501,
        detail="HTTP 端点尚未实现，请使用 WebSocket 接口",
    )


@router.get("/info")
async def get_mcp_info():
    """获取 MCP 服务器信息
    
    返回当前 MCP 服务器的配置和状态信息
    """
    return {
        "service": "CodeMCP MCP Server",
        "version": "1.0",
        "protocol": "MCP (Model Context Protocol)",
        "authentication": "none (simplified)",
        "endpoints": {
            "websocket": "/mcp/ws/{client_type}",
            "client_types": ["planner", "executor"],
            "info": "/mcp/info",
            "health": "/mcp/health"
        },
        "active_connections": len(mcp_server.active_connections),
        "connection_types": mcp_server.connection_types
    }


@router.get("/health")
async def health_check():
    """MCP 服务器健康检查"""
    return {
        "status": "healthy",
        "service": "mcp-server",
        "timestamp": datetime.now().isoformat()
    }


@router.post("/test/echo")
async def test_echo(message: dict):
    """测试端点：回显消息
    
    用于测试 MCP 服务器的基本功能
    """
    return {
        "echo": message,
        "received_at": datetime.now().isoformat(),
        "server": "codemcp-mcp-server"
    }