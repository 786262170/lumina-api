from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import UserProfile, UpdateUserProfileRequest, UserStats
from app.services.user_service import get_user_profile, update_user_profile, get_user_stats

router = APIRouter()


@router.get("/user/profile", response_model=UserProfile)
async def get_user_profile_endpoint(
    current_user: User = Depends(get_current_user)
):
    """获取用户信息"""
    return get_user_profile(current_user)


@router.put("/user/profile", response_model=UserProfile)
async def update_user_profile_endpoint(
    request: UpdateUserProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用户信息"""
    return update_user_profile(current_user, request, db)


@router.get("/user/stats", response_model=UserStats)
async def get_user_stats_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户统计信息"""
    return get_user_stats(current_user, db)
