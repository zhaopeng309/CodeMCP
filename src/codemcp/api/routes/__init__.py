"""
API 路由层

FastAPI 路由端点定义。
"""

from fastapi import APIRouter

from .systems import router as systems_router
from .blocks import router as blocks_router
from .features import router as features_router
from .tasks import router as tasks_router
from .queue import router as queue_router
from .status import router as status_router
from .events import router as events_router
from .auth import router as auth_router
from ...mcp.server import router as mcp_router

# 创建主路由器
api_router = APIRouter()

# 包含所有子路由
api_router.include_router(systems_router)
api_router.include_router(blocks_router)
api_router.include_router(features_router)
api_router.include_router(tasks_router)
api_router.include_router(queue_router)
api_router.include_router(status_router)
api_router.include_router(events_router)
api_router.include_router(auth_router)
api_router.include_router(mcp_router)

__all__ = [
    "api_router",
    "systems_router",
    "blocks_router",
    "features_router",
    "tasks_router",
    "queue_router",
    "status_router",
    "events_router",
    "auth_router",
    "mcp_router",
]