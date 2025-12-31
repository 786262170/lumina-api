from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.settings import AppSettings, UpdateSettingsRequest
from app.schemas.image import ImageFormat
# In production, you might want a separate UserSettings table


def get_settings(user: User, db: Session) -> AppSettings:
    """Get user app settings"""
    # For now, return default settings
    # In production, load from UserSettings table
    return AppSettings(
        notifications=True,
        autoSave=True,
        defaultQuality=85,
        defaultFormat=ImageFormat.JPG
    )


def update_settings(
    user: User,
    request: UpdateSettingsRequest,
    db: Session
) -> AppSettings:
    """Update user app settings"""
    # For now, just return updated settings
    # In production, save to UserSettings table
    current = get_settings(user, db)
    
    return AppSettings(
        notifications=request.notifications if request.notifications is not None else current.notifications,
        autoSave=request.autoSave if request.autoSave is not None else current.autoSave,
        defaultQuality=request.defaultQuality if request.defaultQuality is not None else current.defaultQuality,
        defaultFormat=request.defaultFormat if request.defaultFormat is not None else current.defaultFormat
    )

