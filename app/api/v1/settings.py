from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.settings import AppSettings, UpdateSettingsRequest
from app.services.settings_service import get_settings, update_settings

router = APIRouter()


@router.get("/settings", response_model=AppSettings)
async def get_settings_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取应用设置"""
    return get_settings(current_user, db)


@router.put("/settings", response_model=AppSettings)
async def update_settings_endpoint(
    request: UpdateSettingsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新应用设置"""
    return update_settings(current_user, request, db)
