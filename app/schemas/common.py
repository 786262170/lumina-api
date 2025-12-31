from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class SuccessResponse(BaseModel):
    success: bool = True
    message: str = "操作成功"


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class Pagination(BaseModel):
    page: int = 1
    pageSize: int = 20
    total: int = 0
    totalPages: int = 0

