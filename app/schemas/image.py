from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import re


class ImageFormat(str, Enum):
    JPG = "jpg"
    PNG = "png"
    WEBP = "webp"


class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class OperationType(str, Enum):
    CUTOUT = "cutout"
    BACKGROUND = "background"
    LIGHTING = "lighting"
    FILTER = "filter"
    RESIZE = "resize"


class SceneType(str, Enum):
    TAOBAO = "taobao"
    DOUYIN = "douyin"
    XIAOHONGSHU = "xiaohongshu"
    AMAZON = "amazon"
    CUSTOM = "custom"


class ImageOperation(BaseModel):
    type: OperationType = Field(..., description="操作类型")
    params: Dict[str, Any] = Field(
        default_factory=dict,
        description="操作参数（根据type不同而不同）",
        example={
            "backgroundColor": "#FFFFFF",
            "backgroundTemplateId": "white",
            "brightness": 1.2,
            "contrast": 1.1
        }
    )


class UploadedImage(BaseModel):
    id: str = Field(..., example="img_abc123")
    filename: str = Field(..., example="IMG_2024.jpg")
    url: str = Field(..., format="uri", example="https://cdn.lumina.ai/uploads/img_abc123.jpg")
    thumbnail: Optional[str] = Field(None, format="uri", example="https://cdn.lumina.ai/uploads/thumb_img_abc123.jpg")
    width: int = Field(..., example=1920)
    height: int = Field(..., example=1080)
    size: int = Field(..., description="文件大小（字节）", example=2048000)
    format: ImageFormat = Field(..., example=ImageFormat.JPG)
    uploadedAt: datetime = Field(..., example="2024-01-15T10:30:00Z")


class UploadResponse(BaseModel):
    images: List[UploadedImage]


class ProcessImageRequest(BaseModel):
    imageId: str = Field(..., description="要处理的图片ID", example="img_abc123")
    operations: List[ImageOperation] = Field(..., description="处理操作列表")
    outputSize: Optional[str] = Field(None, description="输出尺寸（如：2000x2000）", example="2000x2000")
    quality: int = Field(85, ge=60, le=100, description="输出质量（60-100）", example=85)
    edgeSmoothing: bool = Field(True, description="是否启用边缘平滑", example=True)
    sceneType: Optional[SceneType] = Field(None, description="场景类型", example=SceneType.TAOBAO)

    @field_validator("outputSize")
    @classmethod
    def validate_output_size(cls, v: Optional[str]) -> Optional[str]:
        if v and not re.match(r"^\d+x\d+$", v):
            raise ValueError("输出尺寸格式不正确，应为 '宽x高'，如 '2000x2000'")
        return v


class ProcessTaskResponse(BaseModel):
    taskId: str = Field(..., description="处理任务ID", example="task_xyz789")
    status: TaskStatus = Field(..., example=TaskStatus.PENDING)
    estimatedTime: int = Field(..., description="预计处理时间（秒）", example=5)


class BatchProcessRequest(BaseModel):
    imageIds: List[str] = Field(
        ...,
        description="要处理的图片ID列表（最多100张）",
        min_length=1,
        max_length=100,
        example=["img_abc123", "img_def456"]
    )
    operations: List[ImageOperation] = Field(..., description="处理操作列表（应用到所有图片）")
    outputSize: Optional[str] = Field(None, example="2000x2000")
    quality: int = Field(85, ge=60, le=100, example=85)
    edgeSmoothing: bool = Field(True, example=True)
    sceneType: Optional[SceneType] = Field(None, example=SceneType.TAOBAO)

    @field_validator("outputSize")
    @classmethod
    def validate_output_size(cls, v: Optional[str]) -> Optional[str]:
        if v and not re.match(r"^\d+x\d+$", v):
            raise ValueError("输出尺寸格式不正确，应为 '宽x高'，如 '2000x2000'")
        return v


class BatchProcessResponse(BaseModel):
    batchTaskId: str = Field(..., description="批量处理任务ID", example="batch_task_abc123")
    tasks: List[ProcessTaskResponse]
    totalCount: int = Field(..., example=2)


class ProcessStatusResponse(BaseModel):
    taskId: str = Field(..., example="task_xyz789")
    status: TaskStatus = Field(..., example=TaskStatus.PROCESSING)
    progress: int = Field(..., ge=0, le=100, description="处理进度（0-100）", example=65)
    message: Optional[str] = Field(None, description="状态消息", example="正在处理中...")
    estimatedTimeRemaining: Optional[int] = Field(None, description="预计剩余时间（秒）", example=2)


class ProcessedImage(BaseModel):
    id: str = Field(..., example="processed_img_xyz789")
    url: str = Field(..., format="uri", example="https://cdn.lumina.ai/processed/processed_img_xyz789.jpg")
    thumbnail: Optional[str] = Field(None, format="uri", example="https://cdn.lumina.ai/processed/thumb_processed_img_xyz789.jpg")
    width: int = Field(..., example=2000)
    height: int = Field(..., example=2000)
    size: int = Field(..., description="文件大小（字节）", example=1536000)
    format: ImageFormat = Field(..., example=ImageFormat.JPG)
    operations: List[ImageOperation] = Field(..., description="应用的处理操作")


class ProcessResultResponse(BaseModel):
    taskId: str = Field(..., example="task_xyz789")
    status: TaskStatus = Field(..., example=TaskStatus.COMPLETED)
    resultImage: ProcessedImage
    processingTime: float = Field(..., description="处理耗时（秒）", example=3.2)
    beforeImage: UploadedImage
    error: Optional[str] = Field(None, description="错误信息（如果失败）")

