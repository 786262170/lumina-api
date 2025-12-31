from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from enum import Enum
import re
from app.schemas.image import ImageOperation, SceneType


class SceneDetail(BaseModel):
    type: SceneType = Field(..., example=SceneType.TAOBAO)
    title: str = Field(..., example="淘宝白底图")
    description: str = Field(..., example="自动生成纯白背景，符合淘宝平台规格")
    presetSizes: List[str] = Field(
        ...,
        example=["2000x2000", "1600x1600", "1000x1000"]
    )
    defaultOperations: List[ImageOperation] = Field(..., description="场景默认处理操作")

    @field_validator("presetSizes")
    @classmethod
    def validate_preset_sizes(cls, v: List[str]) -> List[str]:
        for size in v:
            if not re.match(r"^\d+x\d+$", size):
                raise ValueError(f"预设尺寸格式不正确: {size}")
        return v


class ScenesResponse(BaseModel):
    scenes: List[SceneDetail]


class Recommendation(BaseModel):
    sceneType: SceneType = Field(..., example=SceneType.TAOBAO)
    sceneName: str = Field(..., example="电商主图")
    matchPercentage: int = Field(..., ge=0, le=100, example=98)
    previewImage: Optional[str] = Field(None, format="uri", example="https://cdn.lumina.ai/previews/taobao.jpg")
    description: str = Field(..., example="基于您的选择，这个场景最适合您的需求")


class Feature(BaseModel):
    id: str = Field(..., example="smart_cutout")
    name: str = Field(..., example="智能抠图")
    description: str = Field(..., example="AI精准识别主体，一键移除背景")
    icon: str = Field(..., example="sparkles")

