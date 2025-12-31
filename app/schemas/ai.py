from pydantic import BaseModel, Field
from typing import Dict, List
from app.schemas.scene import Recommendation, Feature


class QuizSubmissionRequest(BaseModel):
    answers: Dict[str, str] = Field(
        ...,
        description="问答答案，key为问题序号（1-based），value为选项ID",
        example={"1": "clothing", "2": "taobao", "3": "minimal"}
    )


class QuizSubmissionResponse(BaseModel):
    sessionId: str = Field(..., description="问答会话ID", example="quiz_session_abc123")
    message: str = Field(..., example="提交成功")


class RecommendationsResponse(BaseModel):
    primaryRecommendation: Recommendation
    alternatives: List[Recommendation] = Field(default_factory=list)
    recommendedFeatures: List[Feature] = Field(default_factory=list)

