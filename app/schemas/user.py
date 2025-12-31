from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from datetime import datetime


class UserProfile(BaseModel):
    id: str = Field(..., example="user_123456")
    phoneNumber: Optional[str] = Field(None, example="138****5678")
    nickname: Optional[str] = Field(None, example="创作者")
    avatar: Optional[HttpUrl] = Field(None, example="https://cdn.lumina.ai/avatars/user_123456.jpg")
    isPro: bool = Field(False, description="是否为专业版会员", example=True)
    membershipType: str = Field("free", example="annual")
    membershipExpiry: Optional[datetime] = Field(None, example="2025-01-28T00:00:00Z")
    createdAt: datetime = Field(..., example="2024-01-01T00:00:00Z")


class UpdateUserProfileRequest(BaseModel):
    nickname: Optional[str] = Field(None, min_length=1, max_length=20, example="新昵称")
    avatar: Optional[HttpUrl] = Field(None, example="https://cdn.lumina.ai/avatars/new_avatar.jpg")


class UserStats(BaseModel):
    processedCount: int = Field(..., description="已处理图片数量", example=1234)
    remainingQuota: int = Field(..., description="剩余配额（-1表示无限）", example=58)
    dailyQuota: int = Field(..., description="每日配额（-1表示无限）", example=-1)
    membershipDaysLeft: Optional[int] = Field(None, description="会员剩余天数", example=28)
    storageUsed: float = Field(..., description="已使用存储空间（GB）", example=2.3)
    storageTotal: float = Field(..., description="总存储空间（GB，-1表示无限）", example=5.0)

