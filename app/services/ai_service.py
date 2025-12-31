from typing import Optional, Dict
from sqlalchemy.orm import Session
import uuid
from app.models.task import QuizSession
from app.models.user import User
from app.schemas.ai import QuizSubmissionRequest, QuizSubmissionResponse, RecommendationsResponse
from app.schemas.scene import Recommendation, Feature, SceneDetail
from app.schemas.image import SceneType


def submit_quiz(
    user: Optional[User],
    request: QuizSubmissionRequest,
    db: Session
) -> QuizSubmissionResponse:
    """Submit quiz answers"""
    session_id = f"quiz_session_{uuid.uuid4().hex[:12]}"
    
    quiz_session = QuizSession(
        id=session_id,
        user_id=user.id if user else None,
        answers=request.answers
    )
    db.add(quiz_session)
    db.commit()
    
    return QuizSubmissionResponse(
        sessionId=session_id,
        message="提交成功"
    )


def get_recommendations(
    user: Optional[User],
    quiz_session_id: Optional[str],
    db: Session
) -> RecommendationsResponse:
    """Get AI recommendations based on quiz or user history"""
    # Simple recommendation logic based on quiz answers
    # In production, this would use ML models
    
    if quiz_session_id:
        quiz_session = db.query(QuizSession).filter(QuizSession.id == quiz_session_id).first()
        if quiz_session:
            answers = quiz_session.answers
            # Simple rule-based recommendation
            if "taobao" in str(answers.values()).lower():
                primary_scene = SceneType.TAOBAO
            elif "douyin" in str(answers.values()).lower():
                primary_scene = SceneType.DOUYIN
            elif "xiaohongshu" in str(answers.values()).lower():
                primary_scene = SceneType.XIAOHONGSHU
            elif "amazon" in str(answers.values()).lower():
                primary_scene = SceneType.AMAZON
            else:
                primary_scene = SceneType.CUSTOM
        else:
            primary_scene = SceneType.TAOBAO
    else:
        # Based on user history
        primary_scene = SceneType.TAOBAO
    
    # Create primary recommendation
    scene_configs = {
        SceneType.TAOBAO: {
            "name": "电商主图",
            "description": "基于您的选择，这个场景最适合您的需求",
            "match": 98
        },
        SceneType.DOUYIN: {
            "name": "抖音视频封面",
            "description": "专为抖音平台优化的图片处理",
            "match": 95
        },
        SceneType.XIAOHONGSHU: {
            "name": "小红书配图",
            "description": "符合小红书平台规范的图片",
            "match": 92
        },
        SceneType.AMAZON: {
            "name": "Amazon产品图",
            "description": "符合Amazon平台要求的产品图片",
            "match": 90
        },
        SceneType.CUSTOM: {
            "name": "自定义场景",
            "description": "根据您的需求定制",
            "match": 85
        }
    }
    
    config = scene_configs[primary_scene]
    primary = Recommendation(
        sceneType=primary_scene,
        sceneName=config["name"],
        matchPercentage=config["match"],
        previewImage=f"https://cdn.lumina.ai/previews/{primary_scene.value}.jpg",
        description=config["description"]
    )
    
    # Alternative recommendations
    alternatives = []
    for scene_type, alt_config in scene_configs.items():
        if scene_type != primary_scene:
            alternatives.append(Recommendation(
                sceneType=scene_type,
                sceneName=alt_config["name"],
                matchPercentage=alt_config["match"] - 10,
                previewImage=f"https://cdn.lumina.ai/previews/{scene_type.value}.jpg",
                description=alt_config["description"]
            ))
    
    # Recommended features
    features = [
        Feature(
            id="smart_cutout",
            name="智能抠图",
            description="AI精准识别主体，一键移除背景",
            icon="sparkles"
        ),
        Feature(
            id="background_replace",
            name="背景替换",
            description="多种背景模板，一键替换",
            icon="image"
        ),
        Feature(
            id="lighting_adjust",
            name="光效调整",
            description="智能调整光线，提升图片质感",
            icon="sun"
        )
    ]
    
    return RecommendationsResponse(
        primaryRecommendation=primary,
        alternatives=alternatives[:3],  # Top 3 alternatives
        recommendedFeatures=features
    )

