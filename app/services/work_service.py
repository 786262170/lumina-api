from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.work import Work
from app.models.image import Image
from app.models.user import User
from app.schemas.work import Work as WorkSchema, WorkDetail, SaveWorkRequest, WorksListResponse
from app.schemas.common import Pagination
from app.exceptions import NotFoundException, BadRequestException
import uuid


def generate_work_id() -> str:
    """Generate unique work ID"""
    return f"work_{uuid.uuid4().hex[:12]}"


def get_works(
    user: User,
    page: int,
    page_size: int,
    category: Optional[str],
    db: Session
) -> WorksListResponse:
    """Get works list with pagination"""
    query = db.query(Work).filter(Work.user_id == user.id)
    
    if category and category != "all":
        query = query.filter(Work.category == category)
    
    total = query.count()
    total_pages = (total + page_size - 1) // page_size
    
    works = query.order_by(Work.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    # Get processed images for all works
    processed_image_ids = [work.processed_image_id for work in works]
    processed_images = {
        img.id: img for img in db.query(Image).filter(Image.id.in_(processed_image_ids)).all()
    } if processed_image_ids else {}
    
    work_schemas = [
        WorkSchema(
            id=work.id,
            filename=work.filename,
            thumbnail=processed_images.get(work.processed_image_id).thumbnail if work.processed_image_id in processed_images else None,
            category=work.category,
            size=work.size,
            createdAt=work.created_at
        )
        for work in works
    ]
    
    # Calculate total storage
    total_storage = db.query(func.sum(Work.size)).filter(Work.user_id == user.id).scalar() or 0
    
    return WorksListResponse(
        works=work_schemas,
        pagination=Pagination(
            page=page,
            pageSize=page_size,
            total=total,
            totalPages=total_pages
        ),
        totalStorage=total_storage
    )


def save_work(
    user: User,
    request: SaveWorkRequest,
    db: Session
) -> WorkSchema:
    """Save processed image as work"""
    # Verify processed image exists and belongs to user
    processed_image = db.query(Image).filter(
        Image.id == request.processedImageId,
        Image.user_id == user.id
    ).first()
    
    if not processed_image:
        raise NotFoundException("处理后的图片不存在")
    
    # Create work
    work_id = generate_work_id()
    work = Work(
        id=work_id,
        user_id=user.id,
        processed_image_id=processed_image.id,
        filename=request.filename,
        category=request.category,
        tags=request.tags,
        size=processed_image.size,
        created_at=processed_image.uploaded_at
    )
    db.add(work)
    db.commit()
    db.refresh(work)
    
    return WorkSchema(
        id=work.id,
        filename=work.filename,
        thumbnail=processed_image.thumbnail,
        category=work.category,
        size=work.size,
        createdAt=work.created_at
    )


def get_work_detail(work_id: str, user: User, db: Session) -> WorkDetail:
    """Get work detail"""
    work = db.query(Work).filter(
        Work.id == work_id,
        Work.user_id == user.id
    ).first()
    
    if not work:
        raise NotFoundException("作品不存在")
    
    # Get processed image manually
    processed_image = db.query(Image).filter(Image.id == work.processed_image_id).first()
    if not processed_image:
        raise NotFoundException("处理后的图片不存在")
    
    # Get source image from process task
    from app.models.image import ProcessTask
    process_task = db.query(ProcessTask).filter(
        ProcessTask.result_image_id == processed_image.id,
        ProcessTask.user_id == user.id
    ).first()
    
    source_image = None
    if process_task:
        source_image = db.query(Image).filter(Image.id == process_task.image_id).first()
    
    if not source_image:
        # Fallback to processed image if source not found
        source_image = processed_image
    
    from app.schemas.image import UploadedImage, ProcessedImage, ImageOperation
    
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
    
    after_image = ProcessedImage(
        id=processed_image.id,
        url=processed_image.url,
        thumbnail=processed_image.thumbnail,
        width=processed_image.width,
        height=processed_image.height,
        size=processed_image.size,
        format=processed_image.format.value,
        operations=[ImageOperation(**op) for op in (process_task.operations if process_task else [])] if process_task else []
    )
    
    return WorkDetail(
        id=work.id,
        filename=work.filename,
        thumbnail=processed_image.thumbnail,
        category=work.category,
        size=work.size,
        createdAt=work.created_at,
        imageUrl=processed_image.url,
        beforeImage=before_image,
        afterImage=after_image,
        tags=work.tags or [],
        operations=[ImageOperation(**op) for op in (process_task.operations if process_task else [])]
    )


def delete_work(work_id: str, user: User, db: Session):
    """Delete work"""
    work = db.query(Work).filter(
        Work.id == work_id,
        Work.user_id == user.id
    ).first()
    
    if not work:
        raise NotFoundException("作品不存在")
    
    db.delete(work)
    db.commit()


def batch_delete_works(work_ids: List[str], user: User, db: Session):
    """Batch delete works"""
    works = db.query(Work).filter(
        Work.id.in_(work_ids),
        Work.user_id == user.id
    ).all()
    
    if len(works) != len(work_ids):
        raise BadRequestException("部分作品不存在或无权限")
    
    for work in works:
        db.delete(work)
    db.commit()

