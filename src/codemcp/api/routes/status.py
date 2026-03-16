"""
Status 路由

系统状态相关的 API 端点。
"""

from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case

from ...database.session import get_db_session
from ..dependencies import PublicDeps, verify_token

router = APIRouter(prefix="/status", tags=["status"])

# 可选的安全方案
optional_security = HTTPBearer(auto_error=False)


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Security(optional_security),
) -> str | None:
    """获取可选的当前用户（如果有认证信息）"""
    if credentials:
        try:
            return await verify_token(credentials)
        except HTTPException:
            return None
    return None


@router.get("/")
async def get_system_status(
    db: AsyncSession = Depends(get_db_session),
    _settings=Depends(PublicDeps["settings"]),
) -> dict:
    """获取系统状态"""
    from datetime import datetime
    
    try:
        # 测试数据库连接 - 使用正确的SQLAlchemy语法
        from sqlalchemy import text
        await db.execute(text("SELECT 1"))
        db_status = "connected"
        
        # 获取基本统计信息（简化版本）
        from ...models.task_queue import TaskQueueModel
        from ...models.system import SystemModel
        
        # 任务统计
        task_count_result = await db.execute(select(func.count(TaskQueueModel.id)))
        task_count = task_count_result.scalar() or 0
        
        # 系统统计
        system_count_result = await db.execute(select(func.count(SystemModel.id)))
        system_count = system_count_result.scalar() or 0
        
        return {
            "status": "operational",
            "service": "codemcp-gateway",
            "database": db_status,
            "statistics": {
                "systems": system_count,
                "tasks": {
                    "total": task_count,
                    "completed": 0,  # 简化版本
                    "failed": 0,
                    "running": 0,
                    "pending": 0,
                    "success_rate": 0
                }
            },
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    except Exception as e:
        # 如果查询失败，返回基本状态
        return {
            "status": "degraded",
            "service": "codemcp-gateway",
            "database": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }


@router.get("/health")
async def health_check() -> dict:
    """健康检查"""
    return {
        "status": "healthy",
        "service": "codemcp-gateway",
        "timestamp": "2026-03-15T16:20:00Z",
    }


@router.get("/metrics")
async def get_metrics(
    db: AsyncSession = Depends(get_db_session),
    _current_user: str | None = Depends(get_optional_user),
) -> dict:
    """获取系统指标"""
    # 待实现 - 返回系统性能指标
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="功能尚未实现",
    )


@router.get("/stats")
async def get_statistics(
    db: AsyncSession = Depends(get_db_session),
    _current_user: str | None = Depends(get_optional_user),
) -> dict:
    """获取系统统计信息"""
    # 待实现 - 返回任务统计、成功率等
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="功能尚未实现",
    )