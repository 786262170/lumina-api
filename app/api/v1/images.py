from fastapi import APIRouter, Depends, UploadFile, File, Form, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.image import (
    UploadResponse,
    ProcessImageRequest,
    ProcessTaskResponse,
    BatchProcessRequest,
    BatchProcessResponse,
    ProcessStatusResponse,
    ProcessResultResponse,
    ImageAnalysisRequest,
    ImageAnalysisResponse,
    ImageFormat
)
from app.services.image_service import (
    upload_images,
    process_image_task,
    get_process_status,
    get_process_result,
    generate_task_id,
    generate_image_id
)
from app.exceptions import BadRequestException, NotFoundException
from app.services.image_understanding_service import analyze_image
from app.models.image import Image
import httpx
import io

router = APIRouter()


@router.post("/images/upload", response_model=UploadResponse)
async def upload_images_endpoint(
    files: List[UploadFile] = File(...),
    sceneType: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """上传图片"""
    if len(files) == 0:
        raise BadRequestException("至少需要上传一张图片")
    
    uploaded_images = await upload_images(files, current_user, sceneType, db)
    return UploadResponse(images=uploaded_images)


@router.post("/images/process", response_model=ProcessTaskResponse)
async def process_image_endpoint(
    request: ProcessImageRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """处理单张图片"""
    return await process_image_task(request, current_user, db, background_tasks)


@router.post("/images/batch-process", response_model=BatchProcessResponse)
async def batch_process_images_endpoint(
    request: BatchProcessRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """批量处理图片"""
    from app.schemas.image import ProcessImageRequest
    
    batch_task_id = f"batch_{generate_task_id()}"
    tasks = []
    
    for image_id in request.imageIds:
        process_request = ProcessImageRequest(
            imageId=image_id,
            operations=request.operations,
            outputSize=request.outputSize,
            quality=request.quality,
            edgeSmoothing=request.edgeSmoothing,
            sceneType=request.sceneType
        )
        task_response = await process_image_task(process_request, current_user, db, background_tasks)
        tasks.append(task_response)
    
    return BatchProcessResponse(
        batchTaskId=batch_task_id,
        tasks=tasks,
        totalCount=len(tasks)
    )


@router.get("/images/process/{taskId}/status", response_model=ProcessStatusResponse)
async def get_process_status_endpoint(
    taskId: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取处理进度"""
    return get_process_status(taskId, current_user, db)


@router.get("/images/process/{taskId}/result", response_model=ProcessResultResponse)
async def get_process_result_endpoint(
    taskId: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取处理结果"""
    return get_process_result(taskId, current_user, db)


@router.post("/images/analyze", response_model=ImageAnalysisResponse)
async def analyze_image_endpoint(
    request: ImageAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """使用GLM-4.7v分析图片"""
    # Verify image belongs to user
    image = db.query(Image).filter(
        Image.id == request.imageId,
        Image.user_id == current_user.id
    ).first()
    
    if not image:
        raise NotFoundException("图片不存在")
    
    # Analyze image using configured provider (OpenAI, GLM, or LangGraph)
    analysis_result = await analyze_image(
        image.url,
        request.prompt,
        request.maxTokens
    )
    
    if not analysis_result:
        raise BadRequestException("图片分析失败，请稍后重试")
    
    return ImageAnalysisResponse(
        imageId=image.id,
        description=analysis_result.get("description", "无法生成描述"),
        tags=analysis_result.get("tags", []),
        mainSubject=analysis_result.get("main_subject", "未知"),
        style=analysis_result.get("style", "未知"),
        qualityScore=analysis_result.get("quality_score", 0.8),
        suggestions=analysis_result.get("suggestions", [])
    )


@router.get("/images/{imageId}/download")
async def download_image_endpoint(
    imageId: str,
    quality: int = Query(85, ge=60, le=100),
    format: ImageFormat = Query(ImageFormat.JPG),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """下载图片"""
    image = db.query(Image).filter(
        Image.id == imageId,
        Image.user_id == current_user.id
    ).first()
    
    if not image:
        raise NotFoundException("图片不存在")
    
    # Download image from OSS or local storage
    async with httpx.AsyncClient() as client:
        response = await client.get(image.url)
        if response.status_code == 200:
            return StreamingResponse(
                io.BytesIO(response.content),
                media_type=f"image/{format.value}",
                headers={
                    "Content-Disposition": f'attachment; filename="{image.filename}"'
                }
            )
        else:
            raise NotFoundException("无法下载图片")
