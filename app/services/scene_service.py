from typing import List
from app.schemas.scene import SceneDetail, ScenesResponse, SceneType
from app.schemas.image import ImageOperation, OperationType


def get_scenes() -> ScenesResponse:
    """Get all available scenes"""
    scenes = [
        SceneDetail(
            type=SceneType.TAOBAO,
            title="淘宝白底图",
            description="自动生成纯白背景，符合淘宝平台规格",
            presetSizes=["2000x2000", "1600x1600", "1000x1000"],
            defaultOperations=[
                ImageOperation(
                    type=OperationType.CUTOUT,
                    params={}
                ),
                ImageOperation(
                    type=OperationType.BACKGROUND,
                    params={"backgroundColor": "#FFFFFF", "backgroundTemplateId": "white"}
                )
            ]
        ),
        SceneDetail(
            type=SceneType.DOUYIN,
            title="抖音视频封面",
            description="专为抖音平台优化的封面图处理",
            presetSizes=["1080x1920", "1080x1440", "1080x1080"],
            defaultOperations=[
                ImageOperation(
                    type=OperationType.CUTOUT,
                    params={}
                ),
                ImageOperation(
                    type=OperationType.LIGHTING,
                    params={"brightness": 1.1, "contrast": 1.05}
                )
            ]
        ),
        SceneDetail(
            type=SceneType.XIAOHONGSHU,
            title="小红书配图",
            description="符合小红书平台规范的图片",
            presetSizes=["1080x1080", "1080x1440", "1080x1920"],
            defaultOperations=[
                ImageOperation(
                    type=OperationType.CUTOUT,
                    params={}
                ),
                ImageOperation(
                    type=OperationType.FILTER,
                    params={"filterType": "warm"}
                )
            ]
        ),
        SceneDetail(
            type=SceneType.AMAZON,
            title="Amazon产品图",
            description="符合Amazon平台要求的产品图片",
            presetSizes=["2000x2000", "1600x1600", "1000x1000"],
            defaultOperations=[
                ImageOperation(
                    type=OperationType.CUTOUT,
                    params={}
                ),
                ImageOperation(
                    type=OperationType.BACKGROUND,
                    params={"backgroundColor": "#FFFFFF"}
                )
            ]
        ),
        SceneDetail(
            type=SceneType.CUSTOM,
            title="自定义场景",
            description="根据您的需求定制处理方案",
            presetSizes=["2000x2000", "1920x1080", "1080x1080"],
            defaultOperations=[
                ImageOperation(
                    type=OperationType.CUTOUT,
                    params={}
                )
            ]
        )
    ]
    
    return ScenesResponse(scenes=scenes)


def get_scene_detail(scene_type: SceneType) -> SceneDetail:
    """Get specific scene detail"""
    scenes_response = get_scenes()
    for scene in scenes_response.scenes:
        if scene.type == scene_type:
            return scene
    
    # Fallback to custom if not found
    return SceneDetail(
        type=SceneType.CUSTOM,
        title="自定义场景",
        description="根据您的需求定制处理方案",
        presetSizes=["2000x2000", "1920x1080", "1080x1080"],
        defaultOperations=[
            ImageOperation(
                type=OperationType.CUTOUT,
                params={}
            )
        ]
    )

