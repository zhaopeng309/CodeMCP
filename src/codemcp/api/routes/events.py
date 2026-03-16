"""
Events 路由

WebSocket 事件推送相关的 API 端点。
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from typing import List

router = APIRouter(prefix="/events", tags=["events"])


class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """接受 WebSocket 连接"""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """断开 WebSocket 连接"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """发送个人消息"""
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        """广播消息给所有连接"""
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 事件推送"""
    await manager.connect(websocket)
    try:
        while True:
            # 等待客户端消息（可选）
            data = await websocket.receive_text()
            # 可以处理客户端消息，这里简单回应
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        manager.disconnect(websocket)
        # 记录错误


@router.get("/test")
async def test_event(
    message: str = "Test event message"
) -> dict:
    """测试事件推送（用于调试）"""
    try:
        await manager.broadcast(message)
        return {
            "success": True,
            "message": f"Event broadcast to {len(manager.active_connections)} connections",
            "connections": len(manager.active_connections),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"事件推送失败: {str(e)}",
        )