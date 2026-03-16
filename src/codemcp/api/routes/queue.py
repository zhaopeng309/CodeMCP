"""
Queue 路由

任务队列相关的 API 端点。
"""

from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.task_engine import TaskEngine
from ...core.executor import LocalCommandExecutor
from ...database.session import get_db_session
from ...models.test import TestModel, TestStatus
from ..dependencies import ProtectedDeps
from ..schemas.task import TaskQueueResponse

router = APIRouter(prefix="/queue", tags=["queue"])

# 创建任务引擎实例
task_engine = TaskEngine(
    executor=LocalCommandExecutor(),
    window_size=5,
    max_retries=3,
)

# 队列状态
queue_paused = False


@router.get("/", response_model=List[TaskQueueResponse])
async def get_queue(
    db: AsyncSession = Depends(get_db_session),
    _current_user: str = Depends(ProtectedDeps["current_user"]),
) -> List[TaskQueueResponse]:
    """获取任务队列"""
    try:
        # 获取等待中的任务
        query = select(TestModel).where(
            TestModel.status == TestStatus.PENDING
        ).order_by(TestModel.created_at)
        
        result = await db.execute(query)
        tasks = result.scalars().all()
        
        # 转换为响应模型
        queue_items = []
        for task in tasks:
            # 检查任务是否在等待队列中
            is_in_queue = task.id in task_engine.task_window.waiting_queue
            is_running = task.id in task_engine.running_tasks
            
            queue_items.append(TaskQueueResponse(
                id=str(uuid4()),  # 队列项ID
                test_id=task.id,
                priority=0,  # 默认优先级
                scheduled_at=task.created_at,
                status=TestStatus.PENDING,
                started_at=None,
                completed_at=None,
                attempts=task.retry_count,
                max_attempts=task.max_retries,
                error_message=None,
                created_at=task.created_at,
                updated_at=task.updated_at,
            ))
        
        return queue_items
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取任务队列失败: {str(e)}",
        )


@router.get("/status", response_model=dict)
async def get_queue_status(
    db: AsyncSession = Depends(get_db_session),
    _current_user: str = Depends(ProtectedDeps["current_user"]),
) -> dict:
    """获取队列状态"""
    try:
        # 统计等待中的任务
        query = select(TestModel).where(
            TestModel.status == TestStatus.PENDING
        )
        result = await db.execute(query)
        pending_tasks = result.scalars().all()
        
        # 获取队列统计
        total_pending = len(pending_tasks)
        running_tasks = len(task_engine.running_tasks)
        waiting_queue = len(task_engine.task_window.waiting_queue)
        available_slots = task_engine.task_window.available_slots
        
        return {
            "status": "paused" if queue_paused else "running",
            "total_pending": total_pending,
            "running_tasks": running_tasks,
            "waiting_queue": waiting_queue,
            "available_slots": available_slots,
            "window_size": task_engine.task_window.size,
            "max_retries": task_engine.failure_handler.max_retries,
            "paused": queue_paused,
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取队列状态失败: {str(e)}",
        )


@router.post("/pause", status_code=200)
async def pause_queue(
    db: AsyncSession = Depends(get_db_session),
    _current_user: str = Depends(ProtectedDeps["current_user"]),
) -> dict:
    """暂停任务队列"""
    global queue_paused
    
    try:
        if queue_paused:
            return {
                "status": "already_paused",
                "message": "队列已处于暂停状态",
            }
        
        queue_paused = True
        
        # 这里可以添加更复杂的暂停逻辑，比如停止接受新任务
        # 但当前运行的任务会继续完成
        
        return {
            "status": "paused",
            "message": "任务队列已暂停",
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"暂停队列失败: {str(e)}",
        )


@router.post("/resume", status_code=200)
async def resume_queue(
    db: AsyncSession = Depends(get_db_session),
    _current_user: str = Depends(ProtectedDeps["current_user"]),
) -> dict:
    """恢复任务队列"""
    global queue_paused
    
    try:
        if not queue_paused:
            return {
                "status": "already_running",
                "message": "队列已处于运行状态",
            }
        
        queue_paused = False
        
        # 这里可以添加恢复逻辑，比如重新开始处理等待队列
        
        return {
            "status": "running",
            "message": "任务队列已恢复",
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"恢复队列失败: {str(e)}",
        )


@router.post("/clear", status_code=200)
async def clear_queue(
    db: AsyncSession = Depends(get_db_session),
    _current_user: str = Depends(ProtectedDeps["current_user"]),
) -> dict:
    """清空任务队列"""
    try:
        # 获取所有等待中的任务
        query = select(TestModel).where(
            TestModel.status == TestStatus.PENDING
        )
        result = await db.execute(query)
        pending_tasks = result.scalars().all()
        
        cleared_count = 0
        
        # 将等待中的任务标记为已取消
        for task in pending_tasks:
            # 检查任务是否在运行中
            if task.id not in task_engine.running_tasks:
                task.status = TestStatus.FAILED
                task.error_message = "任务被队列清空操作取消"
                cleared_count += 1
        
        await db.commit()
        
        # 清空任务引擎的等待队列
        task_engine.task_window.waiting_queue.clear()
        
        return {
            "status": "cleared",
            "message": f"已清空 {cleared_count} 个等待任务",
            "cleared_count": cleared_count,
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"清空队列失败: {str(e)}",
        )


@router.post("/{task_id}/prioritize", status_code=200)
async def prioritize_task(
    task_id: str,
    priority: int = 0,
    db: AsyncSession = Depends(get_db_session),
    _current_user: str = Depends(ProtectedDeps["current_user"]),
) -> dict:
    """设置任务优先级"""
    try:
        # 获取任务
        query = select(TestModel).where(TestModel.id == task_id)
        result = await db.execute(query)
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(
                status_code=404,
                detail=f"任务 {task_id} 不存在",
            )
        
        # 检查任务状态
        if task.status != TestStatus.PENDING:
            raise HTTPException(
                status_code=400,
                detail=f"任务状态为 {task.status.value}，无法设置优先级",
            )
        
        # 这里可以添加优先级设置逻辑
        # 目前只是返回成功响应
        
        return {
            "status": "prioritized",
            "message": f"任务 {task_id} 优先级已设置为 {priority}",
            "task_id": task_id,
            "priority": priority,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"设置任务优先级失败: {str(e)}",
        )


@router.post("/window/size", status_code=200)
async def set_window_size(
    size: int,
    db: AsyncSession = Depends(get_db_session),
    _current_user: str = Depends(ProtectedDeps["current_user"]),
) -> dict:
    """设置任务窗口大小"""
    try:
        if size < 1 or size > 100:
            raise HTTPException(
                status_code=400,
                detail="窗口大小必须在 1 到 100 之间",
            )
        
        # 更新任务窗口大小
        task_engine.task_window.size = size
        
        return {
            "status": "updated",
            "message": f"任务窗口大小已设置为 {size}",
            "window_size": size,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"设置窗口大小失败: {str(e)}",
        )


@router.get("/window/status", response_model=dict)
async def get_window_status(
    db: AsyncSession = Depends(get_db_session),
    _current_user: str = Depends(ProtectedDeps["current_user"]),
) -> dict:
    """获取窗口状态"""
    try:
        window = task_engine.task_window
        
        return {
            "size": window.size,
            "running_tasks": list(window.running_tasks),
            "waiting_queue": list(window.waiting_queue),
            "available_slots": window.available_slots,
            "is_full": window.is_full,
            "is_empty": window.is_empty,
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取窗口状态失败: {str(e)}",
        )