"""
Task 路由

Task 相关的 API 端点。
"""

from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...core.task_engine import TaskEngine
from ...core.executor import LocalCommandExecutor
from ...database.session import get_db_session
from ...models.test import TestModel, TestStatus
from ..dependencies import ProtectedDeps
from ..schemas.task import (
    TestCreate,
    TestDetailResponse,
    TestExecuteRequest,
    TestExecuteResponse,
    TestListResponse,
    TestResponse,
    TestUpdate,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])

# 创建任务引擎实例
task_engine = TaskEngine(
    executor=LocalCommandExecutor(),
    window_size=5,
    max_retries=3,
)


@router.get("/", response_model=TestListResponse)
async def list_tasks(
    db: AsyncSession = Depends(get_db_session),
    feature_id: str = Query(None, description="按功能点 ID 筛选"),
    status: TestStatus = Query(None, description="按状态筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
) -> TestListResponse:
    """获取任务列表"""
    try:
        # 构建查询
        query = select(TestModel)
        
        # 应用筛选条件
        if feature_id:
            query = query.where(TestModel.feature_id == feature_id)
        if status:
            query = query.where(TestModel.status == status)
        
        # 计算总数
        count_query = query.with_only_columns(TestModel.id)
        count_result = await db.execute(count_query)
        total = len(count_result.fetchall())
        
        # 应用分页
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        # 执行查询
        result = await db.execute(query)
        tasks = result.scalars().all()
        
        # 转换为响应模型
        task_responses = [
            TestResponse.from_orm(task) for task in tasks
        ]
        
        return TestListResponse(
            tests=task_responses,
            total=total,
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取任务列表失败: {str(e)}",
        )


@router.post("/", response_model=TestResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TestCreate,
    db: AsyncSession = Depends(get_db_session),
    _current_user: str = Depends(ProtectedDeps["current_user"]),
) -> TestResponse:
    """创建新任务"""
    try:
        # 创建测试模型实例
        test = TestModel(
            id=str(uuid4()),
            command=task_data.command,
            feature_id=task_data.feature_id,
            description=task_data.description,
            max_retries=task_data.max_retries or 3,
            timeout=task_data.timeout or 3600,
            status=TestStatus.PENDING,
            retry_count=0,
        )
        
        # 保存到数据库
        db.add(test)
        await db.commit()
        await db.refresh(test)
        
        return TestResponse.from_orm(test)
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建任务失败: {str(e)}",
        )


@router.get("/{task_id}", response_model=TestDetailResponse)
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> TestDetailResponse:
    """获取任务详情"""
    try:
        # 查询任务，包含关联的功能点
        query = select(TestModel).where(TestModel.id == task_id).options(
            selectinload(TestModel.feature)
        )
        result = await db.execute(query)
        test = result.scalar_one_or_none()
        
        if not test:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"任务 {task_id} 不存在",
            )
        
        return TestDetailResponse.from_orm(test)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取任务详情失败: {str(e)}",
        )


@router.put("/{task_id}", response_model=TestResponse)
async def update_task(
    task_id: str,
    task_data: TestUpdate,
    db: AsyncSession = Depends(get_db_session),
    _current_user: str = Depends(ProtectedDeps["current_user"]),
) -> TestResponse:
    """更新任务"""
    try:
        # 获取现有任务
        result = await db.execute(
            select(TestModel).where(TestModel.id == task_id)
        )
        test = result.scalar_one_or_none()
        
        if not test:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"任务 {task_id} 不存在",
            )
        
        # 更新字段
        if task_data.command is not None:
            test.command = task_data.command
        if task_data.description is not None:
            test.description = task_data.description
        if task_data.max_retries is not None:
            test.max_retries = task_data.max_retries
        if task_data.timeout is not None:
            test.timeout = task_data.timeout
        if task_data.status is not None:
            test.status = task_data.status
        
        # 保存更改
        await db.commit()
        await db.refresh(test)
        
        return TestResponse.from_orm(test)
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新任务失败: {str(e)}",
        )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    db: AsyncSession = Depends(get_db_session),
    _current_user: str = Depends(ProtectedDeps["current_user"]),
) -> None:
    """删除任务"""
    try:
        # 获取现有任务
        result = await db.execute(
            select(TestModel).where(TestModel.id == task_id)
        )
        test = result.scalar_one_or_none()
        
        if not test:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"任务 {task_id} 不存在",
            )
        
        # 删除任务
        await db.delete(test)
        await db.commit()
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除任务失败: {str(e)}",
        )


@router.post("/{task_id}/execute", response_model=TestExecuteResponse)
async def execute_task(
    task_id: str,
    execute_data: TestExecuteRequest,
    db: AsyncSession = Depends(get_db_session),
    _current_user: str = Depends(ProtectedDeps["current_user"]),
) -> TestExecuteResponse:
    """执行任务"""
    try:
        # 获取任务
        result = await db.execute(
            select(TestModel).where(TestModel.id == task_id)
        )
        test = result.scalar_one_or_none()
        
        if not test:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"任务 {task_id} 不存在",
            )
        
        # 检查任务状态
        if test.status not in [TestStatus.PENDING, TestStatus.FAILED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"任务状态为 {test.status.value}，无法执行",
            )
        
        # 使用任务引擎执行任务
        # 注意：这里我们异步执行，不等待完成
        import asyncio
        asyncio.create_task(task_engine.execute_task(task_id))
        
        return TestExecuteResponse(
            task_id=task_id,
            status="executing",
            message="任务已开始执行",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"执行任务失败: {str(e)}",
        )


@router.get("/next", response_model=TestDetailResponse)
async def get_next_task(
    db: AsyncSession = Depends(get_db_session),
    _current_user: str = Depends(ProtectedDeps["current_user"]),
) -> TestDetailResponse:
    """获取下一个待执行任务"""
    try:
        # 查询下一个待处理的任务
        query = select(TestModel).where(
            TestModel.status == TestStatus.PENDING
        ).order_by(
            TestModel.created_at
        ).limit(1).options(
            selectinload(TestModel.feature)
        )
        
        result = await db.execute(query)
        test = result.scalar_one_or_none()
        
        if not test:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="没有待执行的任务",
            )
        
        return TestDetailResponse.from_orm(test)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取下一个任务失败: {str(e)}",
        )


@router.get("/status/{task_id}", response_model=dict)
async def get_task_status(
    task_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """获取任务状态信息"""
    try:
        # 获取任务状态
        status_info = await task_engine.get_task_status(task_id)
        
        if not status_info:
            # 从数据库获取基本信息
            result = await db.execute(
                select(TestModel).where(TestModel.id == task_id)
            )
            test = result.scalar_one_or_none()
            
            if not test:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"任务 {task_id} 不存在",
                )
            
            status_info = {
                "id": test.id,
                "status": test.status.value,
                "is_running": False,
                "is_in_window": False,
                "is_in_queue": False,
                "retry_count": test.retry_count,
                "max_retries": test.max_retries,
                "error_message": test.error_message,
            }
        
        return status_info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取任务状态失败: {str(e)}",
        )


@router.post("/{task_id}/cancel", response_model=dict)
async def cancel_task(
    task_id: str,
    db: AsyncSession = Depends(get_db_session),
    _current_user: str = Depends(ProtectedDeps["current_user"]),
) -> dict:
    """取消正在执行的任务"""
    try:
        # 尝试取消任务
        cancelled = await task_engine.cancel_task(task_id)
        
        if cancelled:
            # 更新数据库状态
            result = await db.execute(
                select(TestModel).where(TestModel.id == task_id)
            )
            test = result.scalar_one_or_none()
            
            if test:
                test.status = TestStatus.ABORTED
                await db.commit()
            
            return {
                "task_id": task_id,
                "status": "cancelled",
                "message": "任务已取消",
            }
        else:
            # 检查任务是否存在
            result = await db.execute(
                select(TestModel).where(TestModel.id == task_id)
            )
            test = result.scalar_one_or_none()
            
            if not test:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"任务 {task_id} 不存在",
                )
            
            return {
                "task_id": task_id,
                "status": "not_running",
                "message": "任务未在运行中",
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"取消任务失败: {str(e)}",
        )