from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.settings import AppSettings, UpdateSettingsRequest
from app.services.settings_service import get_settings, update_settings
from app.utils.logger import cleanup_old_logs, get_log_size_info
from app.config import settings

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


@router.get("/settings/logs/info")
async def get_logs_info(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    获取日志目录信息（管理员接口）

    Returns:
        日志文件数量和总大小信息
    """
    # 可以添加权限检查，只允许管理员访问
    return get_log_size_info()


@router.post("/settings/logs/cleanup")
async def cleanup_logs(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    手动触发日志清理（管理员接口）

    Returns:
        清理结果信息
    """
    # 可以添加权限检查，只允许管理员访问
    try:
        cleanup_old_logs(max_size_mb=settings.log_cleanup_max_size_mb)
        log_info = get_log_size_info()
        return {
            "success": True,
            "message": "日志清理完成",
            "log_info": log_info
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"日志清理失败: {str(e)}"
        }
