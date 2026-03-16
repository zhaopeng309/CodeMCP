"""
System 路由

System 相关的 API 端点。
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...database.session import get_db_session
from ...exceptions import DatabaseError
from ...models.system import SystemModel, SystemStatus
from ..dependencies import ProtectedDeps
from ..schemas.system import (
    SystemCreate,
    SystemDetailResponse,
    SystemListResponse,
    SystemResponse,
    SystemUpdate,
)

router = APIRouter(prefix="/systems", tags=["systems"])


@router.get("/", response_model=SystemListResponse)
async def list_systems(
    db: AsyncSession = Depends(get_db_session),
    status: SystemStatus = Query(None, description="按状态筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
) -> SystemListResponse:
    """获取系统列表"""
    try:
        # 构建查询
        from sqlalchemy import select
        from sqlalchemy.sql import func

        query = select(SystemModel)

        if status:
            query = query.where(SystemModel.status == status)

        # 获取总数
        count_query = select(func.count()).select_from(SystemModel)
        if status:
            count_query = count_query.where(SystemModel.status == status)

        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        # 获取分页数据
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        systems = result.scalars().all()

        # 转换为响应模型
        system_responses = []
        for system in systems:
            # 获取模块数量
            block_count = len(system.blocks) if hasattr(system, "blocks") else 0
            system_responses.append(
                SystemResponse(
                    id=system.id,
                    name=system.name,
                    description=system.description,
                    status=system.status.value,
                    created_at=system.created_at,
                    updated_at=system.updated_at,
                    block_count=block_count,
                )
            )

        return SystemListResponse(
            systems=system_responses,
            total=total,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取系统列表失败: {str(e)}",
        )


@router.post("/", response_model=SystemResponse, status_code=status.HTTP_201_CREATED)
async def create_system(
    system_data: SystemCreate,
    db: AsyncSession = Depends(get_db_session),
    _current_user: str = Depends(ProtectedDeps["current_user"]),
) -> SystemResponse:
    """创建新系统"""
    try:
        # 检查名称是否已存在
        from sqlalchemy import select

        existing_query = select(SystemModel).where(SystemModel.name == system_data.name)
        existing_result = await db.execute(existing_query)
        existing_system = existing_result.scalar_one_or_none()

        if existing_system:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"系统名称 '{system_data.name}' 已存在",
            )

        # 创建新系统
        system = SystemModel(
            name=system_data.name,
            description=system_data.description,
            status=system_data.status,
        )

        db.add(system)
        await db.commit()
        await db.refresh(system)

        return SystemResponse(
            id=system.id,
            name=system.name,
            description=system.description,
            status=system.status.value,
            created_at=system.created_at,
            updated_at=system.updated_at,
            block_count=0,
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建系统失败: {str(e)}",
        )


@router.get("/{system_id}", response_model=SystemDetailResponse)
async def get_system(
    system_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> SystemDetailResponse:
    """获取系统详情"""
    try:
        from sqlalchemy import select

        query = select(SystemModel).where(SystemModel.id == system_id)
        result = await db.execute(query)
        system = result.scalar_one_or_none()

        if not system:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"系统 {system_id} 不存在",
            )

        block_count = len(system.blocks) if hasattr(system, "blocks") else 0

        return SystemDetailResponse(
            id=system.id,
            name=system.name,
            description=system.description,
            status=system.status.value,
            created_at=system.created_at,
            updated_at=system.updated_at,
            block_count=block_count,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取系统详情失败: {str(e)}",
        )


@router.put("/{system_id}", response_model=SystemResponse)
async def update_system(
    system_id: str,
    system_data: SystemUpdate,
    db: AsyncSession = Depends(get_db_session),
    _current_user: str = Depends(ProtectedDeps["current_user"]),
) -> SystemResponse:
    """更新系统"""
    try:
        from sqlalchemy import select

        # 获取现有系统
        query = select(SystemModel).where(SystemModel.id == system_id)
        result = await db.execute(query)
        system = result.scalar_one_or_none()

        if not system:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"系统 {system_id} 不存在",
            )

        # 更新字段
        if system_data.name is not None:
            # 检查名称是否与其他系统冲突
            if system_data.name != system.name:
                existing_query = select(SystemModel).where(
                    SystemModel.name == system_data.name,
                    SystemModel.id != system_id,
                )
                existing_result = await db.execute(existing_query)
                existing_system = existing_result.scalar_one_or_none()

                if existing_system:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"系统名称 '{system_data.name}' 已存在",
                    )
            system.name = system_data.name

        if system_data.description is not None:
            system.description = system_data.description

        if system_data.status is not None:
            system.status = system_data.status

        await db.commit()
        await db.refresh(system)

        block_count = len(system.blocks) if hasattr(system, "blocks") else 0

        return SystemResponse(
            id=system.id,
            name=system.name,
            description=system.description,
            status=system.status.value,
            created_at=system.created_at,
            updated_at=system.updated_at,
            block_count=block_count,
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新系统失败: {str(e)}",
        )


@router.delete("/{system_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_system(
    system_id: str,
    db: AsyncSession = Depends(get_db_session),
    _current_user: str = Depends(ProtectedDeps["current_user"]),
) -> None:
    """删除系统"""
    try:
        from sqlalchemy import select

        # 获取现有系统
        query = select(SystemModel).where(SystemModel.id == system_id)
        result = await db.execute(query)
        system = result.scalar_one_or_none()

        if not system:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"系统 {system_id} 不存在",
            )

        # 检查是否有关联的模块
        if hasattr(system, "blocks") and system.blocks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无法删除有关联模块的系统，请先删除所有模块",
            )

        await db.delete(system)
        await db.commit()

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除系统失败: {str(e)}",
        )