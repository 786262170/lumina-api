from fastapi import HTTPException, status
from typing import Optional, Dict, Any
from app.schemas.common import ErrorResponse, ErrorDetail


class LuminaException(HTTPException):
    """Base exception for Lumina API"""
    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=message)
        self.error_code = error_code
        self.details = details or {}


class BadRequestException(LuminaException):
    """400 Bad Request"""
    def __init__(self, message: str = "请求参数错误", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="INVALID_REQUEST",
            message=message,
            details=details
        )


class UnauthorizedException(LuminaException):
    """401 Unauthorized"""
    def __init__(self, message: str = "未授权，需要登录", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="UNAUTHORIZED",
            message=message,
            details=details
        )


class NotFoundException(LuminaException):
    """404 Not Found"""
    def __init__(self, message: str = "资源不存在", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND",
            message=message,
            details=details
        )


class TooManyRequestsException(LuminaException):
    """429 Too Many Requests"""
    def __init__(self, message: str = "请求过于频繁，请稍后再试", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="TOO_MANY_REQUESTS",
            message=message,
            details=details
        )


class InternalServerException(LuminaException):
    """500 Internal Server Error"""
    def __init__(self, message: str = "服务器内部错误", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="INTERNAL_ERROR",
            message=message,
            details=details
        )

