import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.user import User, MembershipType
from app.utils.jwt import create_access_token, create_refresh_token
from app.utils.sms import send_verification_code, verify_code
from app.utils.wechat import get_wechat_user_info
from app.exceptions import BadRequestException, UnauthorizedException, TooManyRequestsException
from app.schemas.auth import LoginResponse
from app.schemas.user import UserProfile


def create_guest_user(db: Session) -> tuple[User, str, str]:
    """
    Create a guest user account
    Returns: (user, access_token, refresh_token)
    """
    user_id = f"guest_{uuid.uuid4().hex[:12]}"
    user = User(
        id=user_id,
        is_guest=True,
        membership_type=MembershipType.FREE
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Generate tokens
    access_token = create_access_token(data={"sub": user_id})
    refresh_token = create_refresh_token(data={"sub": user_id})
    
    return user, access_token, refresh_token


async def login_with_phone(
    phone_number: str,
    verification_code: str,
    db: Session
) -> LoginResponse:
    """
    Login with phone number and verification code
    """
    # Verify code
    if not verify_code(phone_number, verification_code, db):
        raise UnauthorizedException("验证码错误或已过期")
    
    # Find or create user
    user = db.query(User).filter(User.phone_number == phone_number).first()
    is_new_user = False
    
    if not user:
        is_new_user = True
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        user = User(
            id=user_id,
            phone_number=phone_number,
            membership_type=MembershipType.FREE
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Generate tokens
    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})
    
    return LoginResponse(
        token=access_token,
        refreshToken=refresh_token,
        user=UserProfile(
            id=user.id,
            phoneNumber=user.phone_number,
            nickname=user.nickname,
            avatar=user.avatar,
            isPro=user.is_pro,
            membershipType=user.membership_type.value,
            membershipExpiry=user.membership_expiry,
            createdAt=user.created_at
        ),
        isNewUser=is_new_user,
        expiresIn=7200  # 2 hours
    )


async def login_with_wechat(code: str, db: Session) -> LoginResponse:
    """
    Login with WeChat OAuth code
    """
    wechat_user = await get_wechat_user_info(code)
    if not wechat_user:
        raise UnauthorizedException("微信授权失败")
    
    openid = wechat_user.get("openid")
    if not openid:
        raise UnauthorizedException("无法获取微信用户信息")
    
    # Find or create user
    user = db.query(User).filter(User.wechat_openid == openid).first()
    is_new_user = False
    
    if not user:
        is_new_user = True
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        user = User(
            id=user_id,
            wechat_openid=openid,
            nickname=wechat_user.get("nickname"),
            avatar=wechat_user.get("headimgurl"),
            membership_type=MembershipType.FREE
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Update user info
        if wechat_user.get("nickname"):
            user.nickname = wechat_user.get("nickname")
        if wechat_user.get("headimgurl"):
            user.avatar = wechat_user.get("headimgurl")
        db.commit()
        db.refresh(user)
    
    # Generate tokens
    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})
    
    return LoginResponse(
        token=access_token,
        refreshToken=refresh_token,
        user=UserProfile(
            id=user.id,
            phoneNumber=user.phone_number,
            nickname=user.nickname,
            avatar=user.avatar,
            isPro=user.is_pro,
            membershipType=user.membership_type.value,
            membershipExpiry=user.membership_expiry,
            createdAt=user.created_at
        ),
        isNewUser=is_new_user,
        expiresIn=7200
    )

