from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.dependencies import get_current_user_optional
from fastapi import Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models.user import User
from app.schemas.ai import (
    QuizSubmissionRequest,
    QuizSubmissionResponse,
    RecommendationsResponse
)
from app.services.ai_service import submit_quiz, get_recommendations

router = APIRouter()


@router.post("/ai/quiz", response_model=QuizSubmissionResponse)
async def submit_quiz_endpoint(
    request: QuizSubmissionRequest,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
):
    """提交AI问答答案"""
    current_user = await get_current_user_optional(credentials, db)
    return submit_quiz(current_user, request, db)


@router.get("/ai/recommendations", response_model=RecommendationsResponse)
async def get_recommendations_endpoint(
    quizSessionId: Optional[str] = Query(None, description="问答会话ID（如果提供则基于问答结果，否则基于用户历史）"),
    credentials: Optional[HTTPAuthorizationCredentials] = Security(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
):
    """获取AI推荐"""
    current_user = await get_current_user_optional(credentials, db)
    return get_recommendations(current_user, quizSessionId, db)
