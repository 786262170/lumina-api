from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from app.schemas.image import ImageFormat


class AppSettings(BaseModel):
    notifications: bool = Field(True, description="是否启用通知", example=True)
    autoSave: bool = Field(True, description="是否自动保存", example=True)
    defaultQuality: int = Field(85, ge=60, le=100, description="默认图片质量", example=85)
    defaultFormat: ImageFormat = Field(ImageFormat.JPG, description="默认图片格式", example=ImageFormat.JPG)


class UpdateSettingsRequest(BaseModel):
    notifications: Optional[bool] = None
    autoSave: Optional[bool] = None
    defaultQuality: Optional[int] = Field(None, ge=60, le=100)
    defaultFormat: Optional[ImageFormat] = None

