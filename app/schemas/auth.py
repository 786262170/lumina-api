from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
import re
from app.schemas.user import UserProfile


class SendCodeRequest(BaseModel):
    phoneNumber: str = Field(..., description="手机号码（11位，以1开头）", example="13812345678")

    @field_validator("phoneNumber")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not re.match(r"^1[3-9]\d{9}$", v):
            raise ValueError("手机号码格式不正确")
        return v


class SendCodeResponse(BaseModel):
    success: bool = True
    message: str = "验证码已发送"
    expiresIn: int = Field(..., description="验证码有效期（秒）", example=300)


class LoginRequest(BaseModel):
    phoneNumber: str = Field(..., description="手机号码", example="13812345678")
    verificationCode: str = Field(..., description="6位验证码", example="123456")

    @field_validator("phoneNumber")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not re.match(r"^1[3-9]\d{9}$", v):
            raise ValueError("手机号码格式不正确")
        return v

    @field_validator("verificationCode")
    @classmethod
    def validate_code(cls, v: str) -> str:
        if not re.match(r"^\d{6}$", v):
            raise ValueError("验证码必须是6位数字")
        return v


class WeChatLoginRequest(BaseModel):
    code: str = Field(..., description="微信授权码", example="081abc123def456")


class LoginResponse(BaseModel):
    token: str = Field(..., description="JWT认证令牌")
    refreshToken: str = Field(..., description="刷新令牌")
    user: UserProfile
    isNewUser: bool = Field(..., description="是否为新用户", example=True)
    expiresIn: int = Field(..., description="Token过期时间（秒）", example=7200)

