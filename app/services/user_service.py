from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from app.models.user import User
from app.models.image import Image, ProcessTask
from app.models.work import Work
from app.models.subscription import Subscription
from app.schemas.user import UserProfile, UpdateUserProfileRequest, UserStats
from app.exceptions import NotFoundException


def get_user_profile(user: User) -> UserProfile:
    """Convert User model to UserProfile schema"""
    return UserProfile(
        id=user.id,
        phoneNumber=user.phone_number,
        nickname=user.nickname,
        avatar=user.avatar,
        isPro=user.is_pro,
        membershipType=user.membership_type.value,
        membershipExpiry=user.membership_expiry,
        createdAt=user.created_at
    )


def update_user_profile(
    user: User,
    request: UpdateUserProfileRequest,
    db: Session
) -> UserProfile:
    """Update user profile"""
    if request.nickname is not None:
        user.nickname = request.nickname
    if request.avatar is not None:
        user.avatar = str(request.avatar)
    
    db.commit()
    db.refresh(user)
    
    return get_user_profile(user)


def get_user_stats(user: User, db: Session) -> UserStats:
    """Get user statistics"""
    # Count processed images
    processed_count = db.query(ProcessTask).filter(
        ProcessTask.user_id == user.id,
        ProcessTask.status == "completed"
    ).count()
    
    # Calculate storage used
    total_size = db.query(func.sum(Work.size)).filter(
        Work.user_id == user.id
    ).scalar() or 0
    
    storage_used_gb = total_size / (1024 ** 3)  # Convert bytes to GB
    
    # Get membership info
    membership_days_left = None
    if user.membership_expiry:
        days_left = (user.membership_expiry - datetime.utcnow()).days
        membership_days_left = max(0, days_left) if days_left > 0 else None
    
    # Determine quotas based on membership
    if user.is_pro or user.membership_type.value != "free":
        remaining_quota = -1  # Unlimited
        daily_quota = -1
        storage_total = -1
    else:
        remaining_quota = max(0, 100 - processed_count)  # Free tier: 100 images
        daily_quota = 10  # Free tier: 10 per day
        storage_total = 1.0  # Free tier: 1GB
    
    return UserStats(
        processedCount=processed_count,
        remainingQuota=remaining_quota,
        dailyQuota=daily_quota,
        membershipDaysLeft=membership_days_left,
        storageUsed=round(storage_used_gb, 2),
        storageTotal=storage_total
    )

