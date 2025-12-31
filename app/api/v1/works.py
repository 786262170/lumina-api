from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.work import (
    WorksListResponse,
    Work as WorkSchema,
    WorkDetail,
    SaveWorkRequest,
    BatchDeleteRequest
)
from app.schemas.common import SuccessResponse
from app.services.work_service import (
    get_works,
    save_work,
    get_work_detail,
    delete_work,
    batch_delete_works
)

router = APIRouter()


@router.get("/works", response_model=WorksListResponse)
async def get_works_endpoint(
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取作品列表"""
    return get_works(current_user, page, pageSize, category, db)


@router.post("/works", response_model=WorkSchema)
async def save_work_endpoint(
    request: SaveWorkRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """保存作品"""
    return save_work(current_user, request, db)


@router.get("/works/{workId}", response_model=WorkDetail)
async def get_work_detail_endpoint(
    workId: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取作品详情"""
    return get_work_detail(workId, current_user, db)


@router.delete("/works/{workId}", response_model=SuccessResponse)
async def delete_work_endpoint(
    workId: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除作品"""
    delete_work(workId, current_user, db)
    return SuccessResponse(success=True, message="删除成功")


@router.post("/works/batch-delete", response_model=SuccessResponse)
async def batch_delete_works_endpoint(
    request: BatchDeleteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """批量删除作品"""
    batch_delete_works(request.workIds, current_user, db)
    return SuccessResponse(success=True, message="删除成功")
