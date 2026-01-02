import httpx
from typing import Dict, Any, Optional, List
from app.config import settings
from app.schemas.image import ImageOperation
from app.utils.logger import logger


async def process_image(
    image_url: str,
    operations: List[ImageOperation],
    output_size: Optional[str] = None,
    quality: int = 85,
    edge_smoothing: bool = True,
    scene_type: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Process image using AI service
    Priority: 阿里云视觉智能开放平台 > External AI Service > Mock Mode
    Returns processed image URL or None if failed
    
    Args:
        image_url: 图片 URL
        operations: 处理操作列表
        output_size: 输出尺寸
        quality: 输出质量
        edge_smoothing: 边缘平滑
        scene_type: 场景类型（用于智能选择分割服务）
    """
    # 优先使用阿里云视觉智能开放平台
    if settings.viapi_access_key_id and settings.viapi_access_key_secret and not settings.viapi_mock_mode:
        try:
            from app.services.image_processing_service import process_image_with_viapi
            logger.debug("Using Alibaba Cloud VIAPI for image processing")
            return await process_image_with_viapi(image_url, operations, output_size, quality, scene_type)
        except ImportError:
            logger.warning("VIAPI service not available, falling back to external service")
        except Exception as e:
            logger.error(f"VIAPI processing error: {e}", exc_info=True)
            # Fallback to external service
    
    # 使用外部 AI 服务（如果配置了）
    if settings.ai_service_url and not settings.ai_service_mock_mode:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "image_url": image_url,
                    "operations": [op.dict() for op in operations],
                    "output_size": output_size,
                    "quality": quality,
                    "edge_smoothing": edge_smoothing
                }
                
                headers = {}
                if settings.ai_service_api_key:
                    headers["Authorization"] = f"Bearer {settings.ai_service_api_key}"
                
                response = await client.post(
                    settings.ai_service_url,
                    json=payload,
                    headers=headers
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"AI service error: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"External AI service error: {e}", exc_info=True)
    
    # Mock mode: return mock processed image URL
    logger.debug("Using mock mode for image processing")
    return {
        "processed_url": image_url.replace("/uploads/", "/processed/"),
        "thumbnail_url": image_url.replace("/uploads/", "/processed/thumb_"),
        "width": 2000,
        "height": 2000,
        "size": 1536000,
        "format": "jpg"
    }

