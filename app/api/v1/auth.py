from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user, security
from app.models.user import User
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
from app.utils.jwt import add_token_to_blacklist, revoke_user_tokens, verify_token
from app.utils.logger import logger
from jose import jwt, JWTError
from app.exceptions import BadRequestException, TooManyRequestsException

router = APIRouter()


@router.post("/auth/send-code", response_model=SendCodeResponse)
async def send_verification_code_endpoint(
    request: SendCodeRequest,
    db: Session = Depends(get_db)
):
    """发送验证码"""
    code, expires_in = send_verification_code(request.phoneNumber, db)
    return SendCodeResponse(
        success=True,
        message="验证码已发送",
        expiresIn=expires_in
    )


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
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    登出
    将当前 token 加入黑名单，使其失效
    """
    token = credentials.credentials
    
    # Decode token to get expiration time for blacklist TTL
    # We already verified the token in get_current_user, so we can safely decode it
    try:
        from datetime import datetime
        from app.config import settings
        
        # Decode token to get exp claim (we already verified it in get_current_user)
        payload = jwt.decode(
            token, 
            settings.jwt_secret_key, 
            algorithms=[settings.jwt_algorithm],
            options={"verify_signature": True, "verify_exp": False}  # Skip exp verification, we'll calculate TTL
        )
        
        # Calculate remaining TTL
        exp = payload.get("exp")
        if exp:
            current_time = datetime.utcnow().timestamp()
            expires_in = int(exp - current_time)
            
            if expires_in > 0:
                # Add token to blacklist with remaining TTL
                success = add_token_to_blacklist(token, expires_in)
                if success:
                    logger.info(f"Token blacklisted for user: {current_user.id}, expires in {expires_in}s")
                else:
                    logger.warning(f"Failed to blacklist token for user: {current_user.id}. Redis may not be available.")
            else:
                logger.debug(f"Token already expired (expired {abs(expires_in)}s ago), skipping blacklist")
        else:
            logger.warning("Token has no expiration claim, cannot add to blacklist")
    except JWTError as e:
        logger.error(f"Failed to decode token during logout: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Unexpected error during logout: {e}", exc_info=True)
    
    return SuccessResponse(success=True, message="登出成功")
