"""
Feature 路由

Feature 相关的 API 端点。
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...database.session import get_db_session
from ...models.feature import FeatureModel, FeatureStatus
from ..dependencies import ProtectedDeps
from ..schemas.feature import (
    FeatureCreate,
    FeatureDetailResponse,
    FeatureListResponse,
    FeatureResponse,
    FeatureUpdate,
)

router = APIRouter(prefix="/features", tags=["features"])


@router.get("/", response_model=FeatureListResponse)
async def list_features(
    db: AsyncSession = Depends(get_db_session),
    block_id: str = Query(None, description="按模块 ID 筛选"),
    status: FeatureStatus = Query(None, description="按状态筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
) -> FeatureListResponse:
    """获取功能点列表"""
    # 待实现
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="功能尚未实现",
    )


@router.post("/", response_model=FeatureResponse, status_code=status.HTTP_201_CREATED)
async def create_feature(
    feature_data: FeatureCreate,
    db: AsyncSession = Depends(get_db_session),
    _current_user: str = Depends(ProtectedDeps["current_user"]),
) -> FeatureResponse:
    """创建新功能点"""
    # 待实现
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="功能尚未实现",
    )


@router.get("/{feature_id}", response_model=FeatureDetailResponse)
async def get_feature(
    feature_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> FeatureDetailResponse:
    """获取功能点详情"""
    # 待实现
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="功能尚未实现",
    )


@router.put("/{feature_id}", response_model=FeatureResponse)
async def update_feature(
    feature_id: str,
    feature_data: FeatureUpdate,
    db: AsyncSession = Depends(get_db_session),
    _current_user: str = Depends(ProtectedDeps["current_user"]),
) -> FeatureResponse:
    """更新功能点"""
    # 待实现
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="功能尚未实现",
    )


@router.delete("/{feature_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_feature(
    feature_id: str,
    db: AsyncSession = Depends(get_db_session),
    _current_user: str = Depends(ProtectedDeps["current_user"]),
) -> None:
    """删除功能点"""
    # 待实现
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="功能尚未实现",
    )