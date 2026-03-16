"""
Block 路由

Block 相关的 API 端点。
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...database.session import get_db_session
from ...models.block import BlockModel, BlockStatus
from ..dependencies import ProtectedDeps
from ..schemas.block import (
    BlockCreate,
    BlockDetailResponse,
    BlockListResponse,
    BlockResponse,
    BlockUpdate,
)

router = APIRouter(prefix="/blocks", tags=["blocks"])


@router.get("/", response_model=BlockListResponse)
async def list_blocks(
    db: AsyncSession = Depends(get_db_session),
    system_id: str = Query(None, description="按系统 ID 筛选"),
    status: BlockStatus = Query(None, description="按状态筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
) -> BlockListResponse:
    """获取模块列表"""
    # 待实现
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="功能尚未实现",
    )


@router.post("/", response_model=BlockResponse, status_code=status.HTTP_201_CREATED)
async def create_block(
    block_data: BlockCreate,
    db: AsyncSession = Depends(get_db_session),
    _current_user: str = Depends(ProtectedDeps["current_user"]),
) -> BlockResponse:
    """创建新模块"""
    # 待实现
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="功能尚未实现",
    )


@router.get("/{block_id}", response_model=BlockDetailResponse)
async def get_block(
    block_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> BlockDetailResponse:
    """获取模块详情"""
    # 待实现
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="功能尚未实现",
    )


@router.put("/{block_id}", response_model=BlockResponse)
async def update_block(
    block_id: str,
    block_data: BlockUpdate,
    db: AsyncSession = Depends(get_db_session),
    _current_user: str = Depends(ProtectedDeps["current_user"]),
) -> BlockResponse:
    """更新模块"""
    # 待实现
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="功能尚未实现",
    )


@router.delete("/{block_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_block(
    block_id: str,
    db: AsyncSession = Depends(get_db_session),
    _current_user: str = Depends(ProtectedDeps["current_user"]),
) -> None:
    """删除模块"""
    # 待实现
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="功能尚未实现",
    )