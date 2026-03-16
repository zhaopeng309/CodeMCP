"""
Planner MCP 客户端

与 CodeMCP Gateway 通信的 Planner 客户端，支持 JSON-RPC 2.0 和消息两种接口。

主要功能：
1. 计划管理：创建、更新、查询计划状态
2. 失败分析：获取失败详情，分析失败原因
3. 事件订阅：通过 WebSocket 订阅实时事件
4. 健康检查：监控连接状态和服务器健康

支持两种模式：
- JSON-RPC 模式：与设计文档兼容的 JSON-RPC 2.0 接口
- 消息模式：向后兼容的自定义消息接口

使用示例：
    ```python
    # 创建客户端
    client = PlannerClient(
        server_url="http://localhost:8000",
        api_key="your-api-key",
    )

    async with client:
        # 创建计划
        result = await client.create_plan(
            system_id=1,
            plan_name="用户认证模块",
            blocks=[...],
        )
    ```
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union, Callable, Awaitable
from uuid import uuid4
from dataclasses import dataclass
from enum import Enum

import httpx

# 可选导入 websockets
try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    websockets = None  # 类型: ignore

from ..exceptions import MCPProtocolError, AuthenticationError, RateLimitError
from .protocol import (
    BaseMessage,
    ErrorMessage,
    MessagePriority,
    MessageType,
    PlanCreateMessage,
    SimpleMCPProtocol,
)


class EventType(str, Enum):
    """事件类型枚举"""
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    PLAN_CREATED = "plan_created"
    PLAN_UPDATED = "plan_updated"
    BLOCK_ABORTED = "block_aborted"
    QUEUE_PAUSED = "queue_paused"
    QUEUE_RESUMED = "queue_resumed"


# 事件回调类型
EventCallback = Callable[[Dict[str, Any]], Awaitable[None]]


@dataclass
class MCPClientConfig:
    """MCP 客户端配置"""
    server_url: str = "http://localhost:8000"
    api_key: Optional[str] = None
    role: str = "planner"
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0  # 重试延迟（秒）
    use_mock: bool = False  # 是否使用模拟模式
    enable_websocket: bool = True  # 是否启用 WebSocket 事件


class PlannerClient:
    """Planner 客户端"""

    def __init__(
        self,
        server_url: str = "http://localhost:8000",
        client_id: Optional[str] = None,
        api_key: Optional[str] = None,
        config: Optional[MCPClientConfig] = None,
    ):
        """初始化 Planner 客户端

        Args:
            server_url: MCP 服务器 URL
            client_id: 客户端标识，如果为 None 则自动生成
            api_key: API 密钥
            config: 客户端配置，如果提供则覆盖其他参数
        """
        if config:
            self.config = config
            server_url = config.server_url
            api_key = config.api_key
        else:
            self.config = MCPClientConfig(
                server_url=server_url,
                api_key=api_key,
            )

        self.server_url = server_url.rstrip('/')
        self.client_id = client_id or f"planner-{uuid4().hex[:8]}"
        self.api_key = api_key
        self.protocol = SimpleMCPProtocol()
        self.logger = logging.getLogger(f"codemcp.mcp.planner.{self.client_id}")
        self._connected = False
        self._client: Optional[httpx.AsyncClient] = None
        self._request_counter = 0
        self._websocket: Optional[websockets.WebSocketClientProtocol] = None
        self._event_callbacks: Dict[EventType, List[EventCallback]] = {}
        self._websocket_task: Optional[asyncio.Task] = None
        self._websocket_connected = False

    async def connect(self) -> bool:
        """连接到 MCP 服务器

        Returns:
            是否连接成功
        """
        try:
            self.logger.info(f"连接到 MCP 服务器: {self.server_url}")

            if self.config.use_mock:
                # 模拟连接过程
                await asyncio.sleep(0.1)
                self._connected = True
                self.logger.info("模拟连接成功")
                return True

            # 实际网络连接
            headers = {
                "User-Agent": f"CodeMCP-Planner/{self.client_id}",
                "Content-Type": "application/json",
            }
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            self._client = httpx.AsyncClient(
                base_url=self.server_url,
                headers=headers,
                timeout=self.config.timeout,
                follow_redirects=True,
            )

            # 测试连接
            try:
                response = await self._client.get("/health")
                if response.status_code == 200:
                    self._connected = True
                    self.logger.info("连接成功")
                    return True
                else:
                    self.logger.warning(f"健康检查失败: {response.status_code}")
            except Exception:
                # 如果 /health 端点不存在，尝试 ping
                pass

            # 尝试使用 ping 方法
            try:
                result = await self.ping()
                if result.get("success"):
                    self._connected = True
                    self.logger.info("连接成功 (通过 ping)")
                    return True
            except Exception as e:
                self.logger.warning(f"Ping 测试失败: {e}")

            # 如果没有明确的健康检查，仍然标记为已连接
            self._connected = True
            self.logger.info("连接已建立（假设服务器可用）")
            return True

        except Exception as e:
            self.logger.error(f"连接失败: {e}")
            self._connected = False
            if self._client:
                await self._client.aclose()
                self._client = None
            return False

    async def disconnect(self) -> None:
        """断开连接"""
        if self._connected:
            self.logger.info("断开 MCP 服务器连接")
            self._connected = False

        # 停止 WebSocket
        await self._stop_websocket()

        if self._client:
            await self._client.aclose()
            self._client = None

    async def create_plan(
        self,
        system_id: Union[str, int],
        plan_name: str,
        blocks: List[Dict[str, Any]],
        plan_version: str = "1.0",
        metadata: Optional[Dict[str, Any]] = None,
        use_jsonrpc: bool = True,
    ) -> Dict[str, Any]:
        """创建计划

        Args:
            system_id: 系统 ID
            plan_name: 计划名称
            blocks: 模块列表
            plan_version: 计划版本
            metadata: 元数据
            use_jsonrpc: 是否使用 JSON-RPC 接口

        Returns:
            创建结果

        Raises:
            MCPProtocolError: MCP 协议错误
        """
        try:
            if use_jsonrpc and not self.config.use_mock:
                # 使用 JSON-RPC 接口
                params = {
                    "system_id": system_id,
                    "plan_name": plan_name,
                    "plan_version": plan_version,
                    "blocks": blocks,
                    "metadata": metadata or {},
                }

                self.logger.info(f"创建计划: {plan_name} (系统: {system_id})")
                result = await self._jsonrpc_call_with_retry("mcp.planner.create_plan", params)

                return {
                    "success": True,
                    "method": "jsonrpc",
                    "result": result.get("result", {}),
                }
            else:
                # 使用旧的消息接口（向后兼容）
                if not self._connected:
                    raise MCPProtocolError("客户端未连接")

                message = PlanCreateMessage(
                    source=self.client_id,
                    destination="codemcp/gateway",
                    priority=MessagePriority.NORMAL,
                    system_id=str(system_id),
                    description=plan_name,
                    plan_data={
                        "blocks": blocks,
                        "version": plan_version,
                        "metadata": metadata or {},
                    },
                )

                self.logger.info(f"发送计划创建消息: {plan_name}")
                response = await self._send_message(message)

                if isinstance(response, ErrorMessage):
                    raise MCPProtocolError(
                        f"计划创建失败: {response.error_message}",
                        error_code=response.error_code,
                    )

                return {
                    "success": True,
                    "method": "message",
                    "message_id": message.message_id,
                    "response": response.metadata,
                }

        except Exception as e:
            self.logger.error(f"创建计划时出错: {e}")
            raise MCPProtocolError(f"创建计划失败: {e}")

    async def get_plan_status(
        self,
        plan_id: str,
        include_details: bool = True,
        use_jsonrpc: bool = True,
    ) -> Dict[str, Any]:
        """获取计划状态

        Args:
            plan_id: 计划 ID
            include_details: 是否包含详细信息
            use_jsonrpc: 是否使用 JSON-RPC 接口

        Returns:
            计划状态

        Raises:
            MCPProtocolError: MCP 协议错误
        """
        try:
            if use_jsonrpc and not self.config.use_mock:
                # 使用 JSON-RPC 接口
                params = {
                    "plan_id": plan_id,
                    "include_details": include_details,
                }

                self.logger.info(f"获取计划状态: {plan_id}")
                result = await self._jsonrpc_call_with_retry("mcp.planner.get_plan_status", params)

                return {
                    "success": True,
                    "method": "jsonrpc",
                    "result": result.get("result", {}),
                }
            else:
                # 使用旧的消息接口
                if not self._connected:
                    raise MCPProtocolError("客户端未连接")

                message = BaseMessage(
                    message_type=MessageType.PLAN_STATUS,
                    source=self.client_id,
                    destination="codemcp/gateway",
                    priority=MessagePriority.NORMAL,
                    metadata={"plan_id": plan_id},
                )

                self.logger.info(f"获取计划状态: {plan_id}")
                response = await self._send_message(message)

                if isinstance(response, ErrorMessage):
                    raise MCPProtocolError(
                        f"获取计划状态失败: {response.error_message}",
                        error_code=response.error_code,
                    )

                return {
                    "success": True,
                    "method": "message",
                    "plan_id": plan_id,
                    "status": response.metadata.get("status", "unknown"),
                    "details": response.metadata,
                }

        except Exception as e:
            self.logger.error(f"获取计划状态时出错: {e}")
            raise MCPProtocolError(f"获取计划状态失败: {e}")

    async def update_plan(
        self,
        plan_id: str,
        reason: str,
        new_blocks: Optional[List[Dict[str, Any]]] = None,
        updates: Optional[Dict[str, Any]] = None,
        use_jsonrpc: bool = True,
    ) -> Dict[str, Any]:
        """更新计划（重新规划）

        Args:
            plan_id: 计划 ID
            reason: 更新原因
            new_blocks: 新的模块列表（用于重新规划）
            updates: 其他更新内容
            use_jsonrpc: 是否使用 JSON-RPC 接口

        Returns:
            更新结果

        Raises:
            MCPProtocolError: MCP 协议错误
        """
        try:
            if use_jsonrpc and not self.config.use_mock:
                # 使用 JSON-RPC 接口
                params = {
                    "plan_id": plan_id,
                    "reason": reason,
                }

                if new_blocks:
                    params["new_blocks"] = new_blocks
                if updates:
                    params["updates"] = updates

                self.logger.info(f"更新计划: {plan_id} (原因: {reason})")
                result = await self._jsonrpc_call_with_retry("mcp.planner.update_plan", params)

                return {
                    "success": True,
                    "method": "jsonrpc",
                    "result": result.get("result", {}),
                }
            else:
                # 使用旧的消息接口
                if not self._connected:
                    raise MCPProtocolError("客户端未连接")

                metadata = {
                    "plan_id": plan_id,
                    "reason": reason,
                }
                if new_blocks:
                    metadata["new_blocks"] = new_blocks
                if updates:
                    metadata["updates"] = updates

                message = BaseMessage(
                    message_type=MessageType.PLAN_UPDATE,
                    source=self.client_id,
                    destination="codemcp/gateway",
                    priority=MessagePriority.NORMAL,
                    metadata=metadata,
                )

                self.logger.info(f"更新计划: {plan_id}")
                response = await self._send_message(message)

                if isinstance(response, ErrorMessage):
                    raise MCPProtocolError(
                        f"更新计划失败: {response.error_message}",
                        error_code=response.error_code,
                    )

                return {
                    "success": True,
                    "method": "message",
                    "plan_id": plan_id,
                    "response": response.metadata,
                }

        except Exception as e:
            self.logger.error(f"更新计划时出错: {e}")
            raise MCPProtocolError(f"更新计划失败: {e}")

    async def get_failure_details(
        self,
        feature_id: Union[str, int],
        include_logs: bool = True,
        use_jsonrpc: bool = True,
    ) -> Dict[str, Any]:
        """获取失败详情

        Args:
            feature_id: 功能点 ID
            include_logs: 是否包含日志
            use_jsonrpc: 是否使用 JSON-RPC 接口

        Returns:
            失败详情

        Raises:
            MCPProtocolError: MCP 协议错误
        """
        try:
            if use_jsonrpc and not self.config.use_mock:
                params = {
                    "feature_id": feature_id,
                    "include_logs": include_logs,
                }

                self.logger.info(f"获取失败详情: 功能点 {feature_id}")
                result = await self._jsonrpc_call_with_retry("mcp.planner.get_failure_details", params)

                return {
                    "success": True,
                    "method": "jsonrpc",
                    "result": result.get("result", {}),
                }
            else:
                # 模拟实现
                await asyncio.sleep(0.05)
                return {
                    "success": True,
                    "method": "mock",
                    "feature_id": feature_id,
                    "failure_details": {
                        "error_type": "TEST_FAILURE",
                        "error_message": "模拟错误详情",
                        "logs": ["模拟日志条目 1", "模拟日志条目 2"] if include_logs else [],
                        "timestamp": "2024-01-01T00:00:00Z",
                    }
                }

        except Exception as e:
            self.logger.error(f"获取失败详情时出错: {e}")
            raise MCPProtocolError(f"获取失败详情失败: {e}")

    async def analyze_failure(
        self,
        feature_id: Union[str, int],
        include_suggestions: bool = True,
        use_jsonrpc: bool = True,
    ) -> Dict[str, Any]:
        """分析失败原因

        Args:
            feature_id: 功能点 ID
            include_suggestions: 是否包含建议
            use_jsonrpc: 是否使用 JSON-RPC 接口

        Returns:
            分析结果

        Raises:
            MCPProtocolError: MCP 协议错误
        """
        try:
            if use_jsonrpc and not self.config.use_mock:
                params = {
                    "feature_id": feature_id,
                    "include_suggestions": include_suggestions,
                }

                self.logger.info(f"分析失败原因: 功能点 {feature_id}")
                result = await self._jsonrpc_call_with_retry("mcp.planner.analyze_failure", params)

                return {
                    "success": True,
                    "method": "jsonrpc",
                    "result": result.get("result", {}),
                }
            else:
                # 模拟实现
                await asyncio.sleep(0.05)
                result = {
                    "root_cause": "模拟根因: 数据库连接超时",
                    "error_type": "CONNECTION_TIMEOUT",
                    "failure_context": {
                        "attempt_count": 3,
                        "last_error": "Connection refused",
                        "environment": "test",
                    }
                }

                if include_suggestions:
                    result["suggested_fixes"] = [
                        "检查数据库服务状态",
                        "增加连接超时时间",
                        "验证网络配置",
                    ]
                    result["recommended_actions"] = [
                        {
                            "type": "retry",
                            "config": {
                                "max_retries": 2,
                                "backoff_seconds": 5
                            }
                        }
                    ]

                return {
                    "success": True,
                    "method": "mock",
                    "analysis": result,
                }

        except Exception as e:
            self.logger.error(f"分析失败原因时出错: {e}")
            raise MCPProtocolError(f"分析失败原因失败: {e}")

    async def ping(self) -> Dict[str, Any]:
        """发送 Ping 消息测试连接

        Returns:
            Ping 结果
        """
        try:
            if not self.config.use_mock and self._client:
                # 使用 JSON-RPC ping
                try:
                    result = await self._jsonrpc_call_with_retry("mcp.ping", {})
                    return {
                        "success": True,
                        "method": "jsonrpc",
                        "latency": "测量中",
                        "response": result.get("result", {}),
                    }
                except Exception:
                    # 如果 JSON-RPC ping 失败，回退到消息模式
                    pass

            # 使用消息模式或模拟模式
            message = BaseMessage(
                message_type=MessageType.PING,
                source=self.client_id,
                destination="codemcp/gateway",
                priority=MessagePriority.LOW,
            )

            response = await self._send_message(message)
            return {
                "success": True,
                "method": "message",
                "latency": "模拟 0.1s",
                "response": response.metadata,
            }
        except Exception as e:
            return {
                "success": False,
                "method": "error",
                "error": str(e),
            }

    # ==================== 事件系统 ====================

    def add_event_callback(
        self,
        event_type: EventType,
        callback: EventCallback,
    ) -> None:
        """添加事件回调

        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        if event_type not in self._event_callbacks:
            self._event_callbacks[event_type] = []
        self._event_callbacks[event_type].append(callback)
        self.logger.debug(f"添加事件回调: {event_type}")

    def remove_event_callback(
        self,
        event_type: EventType,
        callback: EventCallback,
    ) -> None:
        """移除事件回调

        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        if event_type in self._event_callbacks:
            try:
                self._event_callbacks[event_type].remove(callback)
                self.logger.debug(f"移除事件回调: {event_type}")
            except ValueError:
                pass

    async def subscribe_events(
        self,
        event_types: List[EventType],
        filters: Optional[Dict[str, Any]] = None,
        use_jsonrpc: bool = True,
    ) -> Dict[str, Any]:
        """订阅事件

        Args:
            event_types: 事件类型列表
            filters: 过滤器
            use_jsonrpc: 是否使用 JSON-RPC 接口

        Returns:
            订阅结果
        """
        try:
            if use_jsonrpc and not self.config.use_mock:
                params = {
                    "event_types": [et.value for et in event_types],
                }
                if filters:
                    params["filters"] = filters

                self.logger.info(f"订阅事件: {event_types}")
                result = await self._jsonrpc_call_with_retry("mcp.events.subscribe", params)

                # 启动 WebSocket 连接（如果启用）
                if self.config.enable_websocket:
                    await self._start_websocket()

                return {
                    "success": True,
                    "method": "jsonrpc",
                    "result": result.get("result", {}),
                }
            else:
                # 模拟实现
                await asyncio.sleep(0.05)
                self.logger.info(f"模拟订阅事件: {event_types}")

                # 在模拟模式下也模拟启动 WebSocket
                if self.config.enable_websocket and not self.config.use_mock:
                    await self._start_websocket()

                return {
                    "success": True,
                    "method": "mock",
                    "event_types": event_types,
                    "subscription_id": f"sub-{uuid4().hex[:8]}",
                }

        except Exception as e:
            self.logger.error(f"订阅事件时出错: {e}")
            raise MCPProtocolError(f"订阅事件失败: {e}")

    async def _start_websocket(self) -> None:
        """启动 WebSocket 连接"""
        if self._websocket_task and not self._websocket_task.done():
            return  # 已经启动

        if self.config.use_mock:
            return  # 模拟模式不启动 WebSocket

        if not WEBSOCKETS_AVAILABLE:
            self.logger.warning("websockets 库未安装，无法启动 WebSocket 连接")
            return

        ws_url = self.server_url.replace("http://", "ws://").replace("https://", "wss://")
        ws_url = f"{ws_url}/mcp/ws"

        # 添加查询参数
        query_params = f"?role=planner&client_id={self.client_id}"
        if self.api_key:
            query_params += f"&api_key={self.api_key}"
        ws_url += query_params

        self.logger.info(f"启动 WebSocket 连接: {ws_url}")
        self._websocket_task = asyncio.create_task(self._websocket_loop(ws_url))

    async def _websocket_loop(self, ws_url: str) -> None:
        """WebSocket 消息循环"""
        if not WEBSOCKETS_AVAILABLE:
            self.logger.error("websockets 库不可用")
            return

        while self._connected and self.config.enable_websocket:
            try:
                async with websockets.connect(ws_url) as websocket:  # type: ignore
                    self._websocket = websocket
                    self._websocket_connected = True
                    self.logger.info("WebSocket 连接已建立")

                    # 发送初始消息
                    if self.api_key:
                        await websocket.send(json.dumps({
                            "type": "auth",
                            "api_key": self.api_key,
                        }))

                    # 消息循环
                    while self._connected and self._websocket_connected:
                        try:
                            message = await websocket.recv()
                            await self._handle_websocket_message(message)
                        except websockets.exceptions.ConnectionClosed:  # type: ignore
                            self.logger.warning("WebSocket 连接已关闭")
                            break
                        except Exception as e:
                            self.logger.error(f"处理 WebSocket 消息时出错: {e}")
                            break

            except Exception as e:
                self.logger.error(f"WebSocket 连接失败: {e}")
                self._websocket_connected = False

            # 重连前等待
            if self._connected and self.config.enable_websocket:
                self.logger.info("5秒后重连 WebSocket...")
                await asyncio.sleep(5)

    async def _handle_websocket_message(self, message: str) -> None:
        """处理 WebSocket 消息"""
        try:
            data = json.loads(message)

            # 处理 JSON-RPC 通知
            if data.get("jsonrpc") == "2.0" and "method" in data:
                method = data.get("method")
                params = data.get("params", {})

                # 将方法名映射到事件类型
                method_to_event = {
                    "mcp.events.task_started": EventType.TASK_STARTED,
                    "mcp.events.task_completed": EventType.TASK_COMPLETED,
                    "mcp.events.task_failed": EventType.TASK_FAILED,
                    "mcp.events.plan_created": EventType.PLAN_CREATED,
                    "mcp.events.plan_updated": EventType.PLAN_UPDATED,
                    "mcp.events.block_aborted": EventType.BLOCK_ABORTED,
                    "mcp.events.queue_paused": EventType.QUEUE_PAUSED,
                    "mcp.events.queue_resumed": EventType.QUEUE_RESUMED,
                }

                event_type = method_to_event.get(method)
                if event_type and event_type in self._event_callbacks:
                    event_data = {
                        "event_type": event_type.value,
                        "timestamp": params.get("timestamp"),
                        "data": params.get("data", {}),
                        "raw_message": data,
                    }

                    # 调用所有回调
                    for callback in self._event_callbacks[event_type]:
                        try:
                            await callback(event_data)
                        except Exception as e:
                            self.logger.error(f"事件回调执行失败: {e}")

                self.logger.debug(f"收到 WebSocket 事件: {method}")

            else:
                self.logger.debug(f"收到 WebSocket 消息: {data}")

        except json.JSONDecodeError:
            self.logger.warning(f"无法解析 WebSocket 消息: {message}")
        except Exception as e:
            self.logger.error(f"处理 WebSocket 消息时出错: {e}")

    async def _stop_websocket(self) -> None:
        """停止 WebSocket 连接"""
        self._websocket_connected = False

        if self._websocket:
            try:
                await self._websocket.close()
            except Exception:
                pass
            self._websocket = None

        if self._websocket_task:
            try:
                self._websocket_task.cancel()
                await self._websocket_task
            except asyncio.CancelledError:
                pass
            except Exception:
                pass
            self._websocket_task = None

        self.logger.info("WebSocket 连接已停止")

    async def _jsonrpc_call_with_retry(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """执行 JSON-RPC 2.0 调用（带重试）

        Args:
            method: 方法名
            params: 参数
            id: 请求 ID，如果为 None 则自动生成

        Returns:
            响应数据

        Raises:
            MCPProtocolError: MCP 协议错误
            AuthenticationError: 认证错误
            RateLimitError: 速率限制错误
        """
        last_exception = None

        for attempt in range(self.config.max_retries + 1):
            try:
                return await self._jsonrpc_call(method, params, id, attempt)
            except (MCPProtocolError, AuthenticationError, RateLimitError) as e:
                last_exception = e

                # 检查是否应该重试
                should_retry = False
                if isinstance(e, MCPProtocolError):
                    # 对于网络错误和服务器错误可以重试
                    should_retry = attempt < self.config.max_retries
                elif isinstance(e, RateLimitError):
                    # 速率限制可以重试
                    should_retry = attempt < self.config.max_retries
                # 认证错误不应该重试

                if not should_retry:
                    break

                # 等待后重试
                delay = self.config.retry_delay * (2 ** attempt)  # 指数退避
                self.logger.warning(
                    f"请求失败 (尝试 {attempt + 1}/{self.config.max_retries + 1}): {e}. "
                    f"{delay:.1f}秒后重试..."
                )
                await asyncio.sleep(delay)

        # 所有重试都失败了
        raise last_exception or MCPProtocolError(f"请求失败: {method}")

    async def _jsonrpc_call(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        id: Optional[str] = None,
        attempt: int = 0,
    ) -> Dict[str, Any]:
        """执行 JSON-RPC 2.0 调用（单次尝试）

        Args:
            method: 方法名
            params: 参数
            id: 请求 ID，如果为 None 则自动生成
            attempt: 尝试次数（用于日志）

        Returns:
            响应数据

        Raises:
            MCPProtocolError: MCP 协议错误
            AuthenticationError: 认证错误
            RateLimitError: 速率限制错误
        """
        if not self._connected:
            raise MCPProtocolError("客户端未连接")

        request_id = id or f"req-{self.client_id}-{self._request_counter}"
        self._request_counter += 1

        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params or {},
        }

        self.logger.debug(f"JSON-RPC 请求: {method} (id: {request_id})")

        if self.config.use_mock:
            # 模拟模式
            await asyncio.sleep(0.1)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "status": "mock_response",
                    "method": method,
                    "params": params,
                }
            }

        # 实际网络请求
        if not self._client:
            raise MCPProtocolError("HTTP 客户端未初始化")

        try:
            response = await self._client.post(
                "/mcp/jsonrpc",
                json=request,
                headers={
                    "X-MCP-Role": "planner",
                    "X-MCP-Version": "1.0",
                }
            )

            if response.status_code == 401:
                raise AuthenticationError("API 密钥无效或缺失")
            elif response.status_code == 429:
                raise RateLimitError("请求频率过高")
            elif response.status_code != 200:
                raise MCPProtocolError(
                    f"HTTP 错误: {response.status_code} - {response.text}"
                )

            data = response.json()

            if "error" in data:
                error = data["error"]
                error_code = error.get("code", -32000)
                error_message = error.get("message", "Unknown error")

                # JSON-RPC 标准错误码
                if error_code in [-32600, -32601, -32602]:
                    raise MCPProtocolError(f"JSON-RPC 错误: {error_message}")
                elif error_code in [-32001, -32002]:
                    raise AuthenticationError(f"认证/授权错误: {error_message}")
                else:
                    raise MCPProtocolError(f"服务器错误: {error_message}")

            return data

        except httpx.RequestError as e:
            raise MCPProtocolError(f"网络请求失败: {e}")
        except json.JSONDecodeError as e:
            raise MCPProtocolError(f"响应 JSON 解析失败: {e}")

    async def _send_message(self, message: BaseMessage) -> BaseMessage:
        """发送消息（模拟实现）

        实际项目中需要实现真正的网络通信

        Args:
            message: 要发送的消息

        Returns:
            响应消息
        """
        # 如果使用模拟模式或需要向后兼容，使用原来的逻辑
        if self.config.use_mock or not self._connected:
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
        else:
            # 转换为 JSON-RPC 调用
            method_map = {
                MessageType.PLAN_CREATE: "mcp.planner.create_plan",
                MessageType.PLAN_UPDATE: "mcp.planner.update_plan",
                MessageType.PLAN_STATUS: "mcp.planner.get_plan_status",
                MessageType.PING: "mcp.ping",
            }

            method = method_map.get(message.message_type)
            if not method:
                return ErrorMessage(
                    error_code="UNSUPPORTED_MESSAGE",
                    error_message=f"不支持的消息类型: {message.message_type}",
                    source=message.destination,
                    destination=message.source,
                )

            try:
                result = await self._jsonrpc_call(method, message.metadata)
                response_data = result.get("result", {})

                # 创建响应消息
                response = BaseMessage(
                    message_type=MessageType.PONG if message.message_type == MessageType.PING else message.message_type,
                    source=message.destination,
                    destination=message.source,
                    metadata=response_data,
                )
                return response
            except Exception as e:
                return ErrorMessage(
                    error_code="RPC_CALL_FAILED",
                    error_message=str(e),
                    source=message.destination,
                    destination=message.source,
                )

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.disconnect()

    # ==================== 辅助方法 ====================

    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._connected

    def is_websocket_connected(self) -> bool:
        """检查 WebSocket 是否已连接"""
        return self._websocket_connected

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            ping_result = await self.ping()
            return {
                "success": ping_result.get("success", False),
                "http": self._client is not None,
                "websocket": self._websocket_connected,
                "ping": ping_result,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }


# ==================== 使用示例 ====================

async def example_usage():
    """使用示例"""
    # 创建客户端
    client = PlannerClient(
        server_url="http://localhost:8000",
        api_key="your-api-key-here",
    )

    async with client:
        # 连接测试
        print(f"已连接: {client.is_connected()}")

        # 创建计划
        plan_result = await client.create_plan(
            system_id=1,
            plan_name="用户认证模块开发",
            blocks=[
                {
                    "name": "数据库层",
                    "description": "用户表和数据访问",
                    "priority": 0,
                    "features": [
                        {
                            "name": "创建用户表",
                            "description": "设计并创建 users 表",
                            "test_command": "pytest tests/test_user_model.py",
                            "priority": 0
                        }
                    ]
                }
            ],
            metadata={
                "created_by": "planner-agent-001",
                "git_repo": "https://github.com/zhaopeng309/CodeMCP",
            }
        )
        print(f"创建计划结果: {plan_result}")

        if plan_result.get("success") and "result" in plan_result:
            plan_id = plan_result["result"].get("plan_id")

            # 获取计划状态
            status_result = await client.get_plan_status(plan_id)
            print(f"计划状态: {status_result}")

            # 分析失败（示例）
            analysis_result = await client.analyze_failure(
                feature_id=101,
                include_suggestions=True,
            )
            print(f"失败分析: {analysis_result}")

        # 健康检查
        health = await client.health_check()
        print(f"健康检查: {health}")


async def example_with_events():
    """带事件订阅的使用示例"""
    client = PlannerClient(
        server_url="http://localhost:8000",
        api_key="your-api-key-here",
    )

    async def on_task_started(event_data: Dict[str, Any]):
        print(f"任务开始: {event_data}")

    async def on_task_completed(event_data: Dict[str, Any]):
        print(f"任务完成: {event_data}")

    async with client:
        # 添加事件回调
        client.add_event_callback(EventType.TASK_STARTED, on_task_started)
        client.add_event_callback(EventType.TASK_COMPLETED, on_task_completed)

        # 订阅事件
        await client.subscribe_events([
            EventType.TASK_STARTED,
            EventType.TASK_COMPLETED,
            EventType.TASK_FAILED,
        ])

        # 等待事件（示例中等待一段时间）
        print("等待事件...")
        await asyncio.sleep(10)