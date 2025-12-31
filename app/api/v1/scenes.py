from fastapi import APIRouter
from app.schemas.scene import ScenesResponse, SceneDetail, SceneType
from app.services.scene_service import get_scenes, get_scene_detail
from app.exceptions import NotFoundException

router = APIRouter()


@router.get("/scenes", response_model=ScenesResponse)
async def get_scenes_endpoint():
    """获取场景列表"""
    return get_scenes()


@router.get("/scenes/{sceneType}", response_model=SceneDetail)
async def get_scene_detail_endpoint(sceneType: SceneType):
    """获取场景详情"""
    try:
        return get_scene_detail(sceneType)
    except Exception:
        raise NotFoundException("场景不存在")
