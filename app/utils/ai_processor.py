import httpx
from typing import Dict, Any, Optional, List
from app.config import settings
from app.schemas.image import ImageOperation


async def process_image(
    image_url: str,
    operations: List[ImageOperation],
    output_size: Optional[str] = None,
    quality: int = 85,
    edge_smoothing: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Process image using external AI service
    Returns processed image URL or None if failed
    """
    if settings.ai_service_mock_mode or not settings.ai_service_url:
        # Mock mode: return mock processed image URL
        return {
            "processed_url": image_url.replace("/uploads/", "/processed/"),
            "thumbnail_url": image_url.replace("/uploads/", "/processed/thumb_"),
            "width": 2000,
            "height": 2000,
            "size": 1536000,
            "format": "jpg"
        }
    
    # Real AI service integration
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
                print(f"AI service error: {response.status_code} - {response.text}")
                return None
    except Exception as e:
        print(f"AI processing error: {e}")
        return None

