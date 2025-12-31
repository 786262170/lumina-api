from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.auth import (
    SendCodeRequest,
    SendCodeResponse,
    LoginRequest,
    LoginResponse,
    WeChatLoginRequest
)
from app.schemas.common import SuccessResponse
from app.services.auth_service import create_guest_user, login_with_phone, login_with_wechat
from app.utils.sms import send_verification_code
from app.exceptions import BadRequestException, TooManyRequestsException

router = APIRouter()


@router.post("/auth/send-code", response_model=SendCodeResponse)
async def send_verification_code_endpoint(
    request: SendCodeRequest,
    db: Session = Depends(get_db)
):
    """发送验证码"""
    try:
        code, expires_in = send_verification_code(request.phoneNumber, db)
        return SendCodeResponse(
            success=True,
            message="验证码已发送",
            expiresIn=expires_in
        )
    except Exception as e:
        # Rate limiting check would go here
        raise TooManyRequestsException("请求过于频繁，请稍后再试")


@router.post("/auth/login", response_model=LoginResponse)
async def login_endpoint(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """手机号登录"""
    return await login_with_phone(request.phoneNumber, request.verificationCode, db)


@router.post("/auth/wechat-login", response_model=LoginResponse)
async def wechat_login_endpoint(
    request: WeChatLoginRequest,
    db: Session = Depends(get_db)
):
    """微信登录"""
    return await login_with_wechat(request.code, db)


@router.post("/auth/guest", response_model=LoginResponse)
async def guest_mode_endpoint(db: Session = Depends(get_db)):
    """游客模式"""
    user, access_token, refresh_token = create_guest_user(db)
    
    from app.schemas.user import UserProfile
    from app.models.user import MembershipType
    
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
        isNewUser=True,
        expiresIn=7200
    )


@router.post("/auth/logout", response_model=SuccessResponse)
async def logout_endpoint(
    # Token would be validated by dependency
    db: Session = Depends(get_db)
):
    """登出"""
    # TODO: Add token to blacklist
    return SuccessResponse(success=True, message="登出成功")
