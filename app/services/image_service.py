import uuid
import os
from datetime import datetime
from typing import List, Optional, Dict, Tuple
from fastapi import UploadFile
from sqlalchemy.orm import Session
from PIL import Image as PILImage
import io
from app.models.image import Image, ProcessTask, ImageFormat, TaskStatus
from app.models.user import User
from app.schemas.image import (
    UploadedImage,
    ProcessImageRequest,
    ProcessTaskResponse,
    ProcessStatusResponse,
    ProcessResultResponse,
    ProcessedImage,
    ImageOperation
)
from app.services.storage_service import storage_service
from app.utils.ai_processor import process_image
from app.exceptions import NotFoundException, BadRequestException
from app.utils.logger import logger
from fastapi import BackgroundTasks


def generate_image_id() -> str:
    """Generate unique image ID"""
    return f"img_{uuid.uuid4().hex[:12]}"


def generate_task_id() -> str:
    """Generate unique task ID"""
    return f"task_{uuid.uuid4().hex[:12]}"


# Image format mapping: PIL format -> (ImageFormat enum, file extension)
IMAGE_FORMAT_MAP: Dict[str, Tuple[ImageFormat, str]] = {
    "jpeg": (ImageFormat.JPG, "jpg"),
    "jpg": (ImageFormat.JPG, "jpg"),
    "png": (ImageFormat.PNG, "png"),
    "webp": (ImageFormat.WEBP, "webp"),
}

# Content type to format mapping
CONTENT_TYPE_FORMAT_MAP: Dict[str, Tuple[ImageFormat, str]] = {
    "image/jpeg": (ImageFormat.JPG, "jpg"),
    "image/png": (ImageFormat.PNG, "png"),
    "image/webp": (ImageFormat.WEBP, "webp"),
}


def detect_image_format(img: PILImage.Image, content_type: str) -> Tuple[ImageFormat, str]:
    """
    Detect image format from PIL Image and content type
    Returns: (ImageFormat enum, file extension)
    """
    # Try to detect from PIL image format first (most accurate)
    if img.format:
        img_format_str = img.format.lower()
        if img_format_str in IMAGE_FORMAT_MAP:
            return IMAGE_FORMAT_MAP[img_format_str]
    
    # Fallback to content type
    if content_type in CONTENT_TYPE_FORMAT_MAP:
        return CONTENT_TYPE_FORMAT_MAP[content_type]
    
    # Default to JPG if unknown
    logger.warning(f"Unknown image format, defaulting to JPG. PIL format: {img.format}, Content type: {content_type}")
    return (ImageFormat.JPG, "jpg")


async def upload_images(
    files: List[UploadFile],
    user: User,
    scene_type: Optional[str],
    db: Session
) -> List[UploadedImage]:
    """Upload multiple images"""
    if len(files) > 100:
        raise BadRequestException("单次最多上传100张图片")
    
    uploaded_images = []
    
    for file in files:
        # Validate file type
        if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
            raise BadRequestException(f"不支持的图片格式: {file.content_type}")
        
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        # Get image dimensions and verify format
        img_buffer = io.BytesIO(content)
        img = PILImage.open(img_buffer)
        width, height = img.size
        
        # Detect image format
        img_format, file_ext = detect_image_format(img, file.content_type)
        
        # Log image info for verification
        logger.debug(f"Image info - Size: {file_size} bytes, Dimensions: {width}x{height}, Format: {img_format.value}, Extension: {file_ext}")
        
        # Generate file path (without storage root prefix, storage_service will add it)
        image_id = generate_image_id()
        file_path = f"{user.id}/{image_id}.{file_ext}"
        
        # Upload to OSS
        url = storage_service.upload_file(content, file_path, file.content_type)
        
        # Generate thumbnail
        thumbnail_content = storage_service.generate_thumbnail(content)
        thumbnail_path = f"{user.id}/thumb_{image_id}.{file_ext}"
        thumbnail_url = storage_service.upload_file(thumbnail_content, thumbnail_path, file.content_type)
        
        # Save to database
        image = Image(
            id=image_id,
            user_id=user.id,
            filename=file.filename or f"image.{file_ext}",
            url=url,
            thumbnail=thumbnail_url,
            width=width,
            height=height,
            size=file_size,
            format=img_format,
            uploaded_at=datetime.utcnow()
        )
        db.add(image)
        db.commit()
        db.refresh(image)
        
        uploaded_images.append(UploadedImage(
            id=image.id,
            filename=image.filename,
            url=image.url,
            thumbnail=image.thumbnail,
            width=image.width,
            height=image.height,
            size=image.size,
            format=image.format.value,
            uploadedAt=image.uploaded_at
        ))
    
    return uploaded_images


async def process_image_task(
    request: ProcessImageRequest,
    user: User,
    db: Session,
    background_tasks: BackgroundTasks
) -> ProcessTaskResponse:
    """Create image processing task"""
    # Verify image belongs to user
    image = db.query(Image).filter(
        Image.id == request.imageId,
        Image.user_id == user.id
    ).first()
    
    if not image:
        raise NotFoundException("图片不存在")
    
    # Create task
    task_id = generate_task_id()
    task = ProcessTask(
        id=task_id,
        user_id=user.id,
        image_id=image.id,
        status=TaskStatus.PENDING,
        progress=0,
        operations=[op.dict() for op in request.operations],
        output_size=request.outputSize,
        quality=request.quality,
        edge_smoothing=request.edgeSmoothing,
        scene_type=request.sceneType.value if request.sceneType else None,
        created_at=datetime.utcnow()
    )
    db.add(task)
    db.commit()
    
    # Start background processing
    background_tasks.add_task(
        execute_image_processing,
        task_id,
        image.url,
        request.operations,
        request.outputSize,
        request.quality,
        request.edgeSmoothing,
        db
    )
    
    return ProcessTaskResponse(
        taskId=task.id,
        status=task.status.value,
        estimatedTime=5
    )


async def execute_image_processing(
    task_id: str,
    image_url: str,
    operations: List[ImageOperation],
    output_size: Optional[str],
    quality: int,
    edge_smoothing: bool,
    db: Session
):
    """Execute image processing in background"""
    task = db.query(ProcessTask).filter(ProcessTask.id == task_id).first()
    if not task:
        return
    
    try:
        # Update status to processing
        task.status = TaskStatus.PROCESSING
        task.progress = 10
        db.commit()
        
        # Call AI processing service
        result = await process_image(
            image_url,
            operations,
            output_size,
            quality,
            edge_smoothing
        )
        
        if not result:
            task.status = TaskStatus.FAILED
            task.error_message = "AI处理服务返回错误"
            task.completed_at = datetime.utcnow()
            db.commit()
            return
        
        # Save processed image
        processed_image_id = generate_image_id()
        processed_image = Image(
            id=processed_image_id,
            user_id=task.user_id,
            filename=f"processed_{task.image_id}.jpg",
            url=result["processed_url"],
            thumbnail=result.get("thumbnail_url"),
            width=result.get("width", 2000),
            height=result.get("height", 2000),
            size=result.get("size", 0),
            format=ImageFormat.JPG,
            uploaded_at=datetime.utcnow()
        )
        db.add(processed_image)
        
        # Update task
        task.status = TaskStatus.COMPLETED
        task.progress = 100
        task.result_image_id = processed_image_id
        task.completed_at = datetime.utcnow()
        processing_time = (datetime.utcnow() - task.created_at).total_seconds()
        task.processing_time = int(processing_time)
        db.commit()
        
    except Exception as e:
        task.status = TaskStatus.FAILED
        task.error_message = str(e)
        task.completed_at = datetime.utcnow()
        db.commit()


def get_process_status(task_id: str, user: User, db: Session) -> ProcessStatusResponse:
    """Get processing task status"""
    task = db.query(ProcessTask).filter(
        ProcessTask.id == task_id,
        ProcessTask.user_id == user.id
    ).first()
    
    if not task:
        raise NotFoundException("任务不存在")
    
    message = None
    if task.status == TaskStatus.PROCESSING:
        message = "正在处理中..."
    elif task.status == TaskStatus.COMPLETED:
        message = "处理完成"
    elif task.status == TaskStatus.FAILED:
        message = task.error_message or "处理失败"
    
    estimated_time = None
    if task.status == TaskStatus.PROCESSING:
        estimated_time = max(1, 5 - int((datetime.utcnow() - task.created_at).total_seconds()))
    
    return ProcessStatusResponse(
        taskId=task.id,
        status=task.status.value,
        progress=task.progress,
        message=message,
        estimatedTimeRemaining=estimated_time
    )


def get_process_result(task_id: str, user: User, db: Session) -> ProcessResultResponse:
    """Get processing result"""
    task = db.query(ProcessTask).filter(
        ProcessTask.id == task_id,
        ProcessTask.user_id == user.id
    ).first()
    
    if not task:
        raise NotFoundException("任务不存在")
    
    if task.status != TaskStatus.COMPLETED and task.status != TaskStatus.FAILED:
        raise BadRequestException("任务尚未完成")
    
    # Get source image
    source_image = db.query(Image).filter(Image.id == task.image_id).first()
    if not source_image:
        raise NotFoundException("源图片不存在")
    
    before_image = UploadedImage(
        id=source_image.id,
        filename=source_image.filename,
        url=source_image.url,
        thumbnail=source_image.thumbnail,
        width=source_image.width,
        height=source_image.height,
        size=source_image.size,
        format=source_image.format.value,
        uploadedAt=source_image.uploaded_at
    )
    
    if task.status == TaskStatus.FAILED:
        return ProcessResultResponse(
            taskId=task.id,
            status=task.status.value,
            resultImage=ProcessedImage(
                id="",
                url="",
                thumbnail=None,
                width=0,
                height=0,
                size=0,
                format=ImageFormat.JPG,
                operations=[]
            ),
            processingTime=0,
            beforeImage=before_image,
            error=task.error_message
        )
    
    # Get result image
    result_image = db.query(Image).filter(Image.id == task.result_image_id).first()
    if not result_image:
        raise NotFoundException("处理结果图片不存在")
    
    processed_image = ProcessedImage(
        id=result_image.id,
        url=result_image.url,
        thumbnail=result_image.thumbnail,
        width=result_image.width,
        height=result_image.height,
        size=result_image.size,
        format=result_image.format.value,
        operations=[ImageOperation(**op) for op in task.operations]
    )
    
    return ProcessResultResponse(
        taskId=task.id,
        status=task.status.value,
        resultImage=processed_image,
        processingTime=task.processing_time or 0,
        beforeImage=before_image,
        error=None
    )

