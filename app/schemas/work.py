from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.schemas.image import UploadedImage, ProcessedImage, ImageOperation, SceneType
from app.schemas.common import Pagination


class Work(BaseModel):
    id: str = Field(..., example="work_123456")
    filename: str = Field(..., example="IMG_2024_processed.jpg")
    thumbnail: Optional[str] = Field(None, format="uri", example="https://cdn.lumina.ai/works/thumb_work_123456.jpg")
    category: Optional[SceneType] = Field(None, example=SceneType.TAOBAO)
    size: int = Field(..., description="文件大小（字节）", example=1536000)
    createdAt: datetime = Field(..., example="2024-01-15T10:30:00Z")


class WorkDetail(Work):
    imageUrl: str = Field(..., format="uri", example="https://cdn.lumina.ai/works/work_123456.jpg")
    beforeImage: UploadedImage
    afterImage: ProcessedImage
    tags: List[str] = Field(default_factory=list, example=["产品图", "白底图"])
    operations: List[ImageOperation] = Field(default_factory=list)


class SaveWorkRequest(BaseModel):
    processedImageId: str = Field(..., description="处理后的图片ID", example="processed_img_xyz789")
    filename: str = Field(..., description="作品文件名", example="IMG_2024_processed.jpg")
    category: Optional[SceneType] = Field(None, description="作品分类", example=SceneType.TAOBAO)
    tags: List[str] = Field(default_factory=list, description="标签", example=["产品图", "白底图"])


class WorksListResponse(BaseModel):
    works: List[Work]
    pagination: Pagination
    totalStorage: float = Field(..., description="总存储使用量（字节）", example=2457600000)


class BatchDeleteRequest(BaseModel):
    workIds: List[str] = Field(..., min_length=1, example=["work_123456", "work_789012"])

